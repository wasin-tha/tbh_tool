#!/usr/bin/env python3
"""
fetch_prices.py — ดึงราคา Steam Market (฿) สำหรับ TBH materials + equipment

★ เวอร์ชัน anon (2026-07-12) — ไม่ใช้ login/cookie อีกแล้ว:
  - ยิงผ่าน curl (subprocess) — Steam กรอง TLS fingerprint ของ Python สำหรับ anon
    (Python โดน 429 ทุกนัด, curl ผ่าน — พิสูจน์แล้วทั้ง IP บ้านและ GitHub runner)
  - anon ได้สกุลเงินตาม IP ประเทศ: IP ไทย → ฿ ตรงๆ, IP นอก (GitHub) → $ แล้วแปลงเป็น ฿
    ด้วยเรต USD→THB จาก open.er-api.com (สำรอง frankfurter.app)
    เทียบเรตแฝง Valve แล้วคลาด ≤3% (ของแพง <1%; ทดสอบ same-timestamp 12 items 2026-07-12)
  - ดึงขนานหลายหน้า (default 6 workers) → เร็วกว่าเดิมมาก (เดิม sequential ~3.5 นาที)
  - หน้าไหนพังถาวร → exit 3 (ไม่ commit ของครึ่งๆ — เว็บใช้ราคาเดิม รอรอบหน้า)

ใช้:
  python fetch_prices.py [--mat-only|--gear-only|--reset]
  env: TBH_CONC = จำนวน workers (default 6), TBH_DELAY = วินาทีหน่วงต่อ worker (default 0.3)
exit codes: 2 = หาเรตแปลงไม่ได้, 3 = ราคาไม่ครบ/ไม่ได้เลย — Action ใช้เช็คว่าจะ deploy ไหม
"""
import json, os, random, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

TH_TZ = timezone(timedelta(hours=7))  # เวลาไทย (runner เป็น UTC จึงต้อง fix)
sys.stdout.reconfigure(encoding='utf-8')

# ── Config ────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.abspath(__file__))
APP_ID      = '3678970'
PAGE_SIZE   = 10        # Steam cap หน้าละ 10 ตายตัว (ยืนยันซ้ำ 2026-07-12: count=100 ก็ได้ 10)
CONC        = int(os.environ.get('TBH_CONC', '6'))
DELAY       = float(os.environ.get('TBH_DELAY', '0.3'))  # หน่วงเล็กน้อยต่อ request กัน burst แรงเกิน
COOLDOWN    = 30        # วินาทีฐาน เมื่อโดน 429 (ทวีคูณตามครั้ง)
MAX_RETRIES = 5
UA          = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
# currency=14 (฿): anon ให้ได้เฉพาะ "สกุลตามประเทศของ IP" หรือ USD —
#   IP ไทย → ได้ ฿ ตรงๆ (เป๊ะ ไม่ต้องแปลง), IP นอก (GitHub) → Steam ตอบ $ มาแทน → แปลงเอา
RENDER_URL  = ('https://steamcommunity.com/market/search/render/'
               f'?norender=1&appid={APP_ID}&currency=14&sort_column=popular&sort_dir=desc')
THB         = '฿'  # ฿

PRICES_FILE = os.path.join(BASE, 'data', 'tbh_prices.json')
LEG_PLUS    = {'LEGENDARY','IMMORTAL','ARCANA','BEYOND','CELESTIAL','DIVINE','COSMIC'}

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def curl_get(url, timeout=20):
    """GET ผ่าน curl → (status:int, body:str) — ห้ามใช้ requests/urllib กับ Steam (โดนกรอง fingerprint)"""
    r = subprocess.run(
        ['curl', '-s', '--compressed', '-A', UA, '-m', str(timeout), '-w', '\n%{http_code}', url],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout or ''
    body, _, code = out.rpartition('\n')
    return (int(code) if code.strip().isdigit() else 0), body

# ── Build  market_hash_name → item_id  index ───────────────────────────────────
def build_index(mode='all'):
    """{market_hash_name: [item_id, ...]} — gear หลาย level ใช้ hash เดียวกัน จึง map เป็น list"""
    items_list = load_json(os.path.join(BASE, 'data', 'tbh_items.json'), [])
    idx = {}
    for item in items_list:
        if not item.get('marketable', False):
            continue
        raw_name = item.get('name', {})
        name = raw_name.get('en-US', '') if isinstance(raw_name, dict) else ''
        if not name:
            continue
        itype, grade = item.get('type', ''), item.get('grade', '')
        if itype == 'MATERIAL' and mode in ('all', 'mat-only'):
            idx.setdefault(name, []).append(item['id'])
        elif itype == 'GEAR' and grade in LEG_PLUS and mode in ('all', 'gear-only'):
            idx.setdefault(f'{name} ({grade.capitalize()}) A', []).append(item['id'])  # Steam hash: variant A
    return idx

# ── USD→THB rate ──────────────────────────────────────────────────────────────
def get_usd_thb_rate():
    """เรตตลาด (er-api → frankfurter) — เทียบเรตแฝง Valve แล้วต่างกัน ~1% | None ถ้าล่มทั้งคู่"""
    for url, pick in [
        ('https://open.er-api.com/v6/latest/USD',            lambda d: d['rates']['THB']),
        ('https://api.frankfurter.app/latest?from=USD&to=THB', lambda d: d['rates']['THB']),
    ]:
        try:
            code, body = curl_get(url)
            if code == 200:
                rate = float(pick(json.loads(body)))
                if 20 < rate < 60:   # sanity ช่วงเรต ฿/$ ที่เป็นไปได้
                    return rate
        except Exception as e:
            print(f'  ⚠ rate source ล้ม ({url.split("/")[2]}): {e}', flush=True)
    return None

# ── Fetch one page (มี retry/backoff ในตัว — ปลอดภัยต่อการยิงขนาน) ────────────
def fetch_page(start):
    """คืน (results:list, total_count:int) | None = พังถาวร"""
    url = f'{RENDER_URL}&start={start}&count={PAGE_SIZE}'
    for attempt in range(MAX_RETRIES):
        if DELAY:
            time.sleep(DELAY + random.uniform(0, DELAY))
        code, body = curl_get(url)
        if code == 200:
            try:
                d = json.loads(body)
            except json.JSONDecodeError:
                time.sleep(3); continue
            if not d.get('success'):
                time.sleep(3); continue
            return d.get('results', []), d.get('total_count', 0)
        if code == 429:
            wait = COOLDOWN * (attempt + 1) + random.uniform(0, 10)
            print(f'  ⚠ 429 [start={start}] รอ {wait:.0f}s (ครั้ง {attempt+1}/{MAX_RETRIES})', flush=True)
            time.sleep(wait)
            continue
        time.sleep(5)
    return None

PRICE_RE = re.compile(r'[\d,]+(?:\.\d+)?')

def to_thb(it, rate):
    """แปลง 1 result → ราคา ฿ (string 'lowest') | None ถ้า parse ไม่ได้
    IP ไทย → text เป็น ฿ อยู่แล้ว ใช้ตรงๆ; IP นอก → $ → sell_price(cents)×rate"""
    txt = it.get('sell_price_text', '')
    if THB in txt:
        return txt
    if '$' in txt:
        cents = it.get('sell_price')
        usd = cents / 100.0 if isinstance(cents, (int, float)) and cents else None
        if usd is None:
            m = PRICE_RE.search(txt)
            usd = float(m.group().replace(',', '')) if m else None
        if usd is not None and rate:
            return f'{THB}{usd * rate:,.2f}'
    return None

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    mode = 'mat-only' if '--mat-only' in args else 'gear-only' if '--gear-only' in args else 'all'
    reset = '--reset' in args

    idx    = build_index(mode)
    n_ids  = sum(len(v) for v in idx.values())
    prices = {} if reset else load_json(PRICES_FILE)

    print(f'\n{"─"*55}')
    print(f'  เป้าหมาย : {len(idx):,} ชื่อ ({n_ids:,} items) — {mode}')
    print(f'  วิธี     : search/render anon ผ่าน curl — ขนาน {CONC} workers')
    print(f'{"─"*55}\n')

    start_time = time.time()

    # หน้าแรก: เอา total_count + ดูสกุลเงินที่ Steam เลือกให้ (ตาม IP)
    first = fetch_page(0)
    if first is None:
        print('❌ หน้าแรกดึงไม่ได้เลย — ยกเลิก')
        sys.exit(3)
    results0, total_count = first
    sample = results0[0].get('sell_price_text', '?') if results0 else '?'
    native_thb = THB in sample
    print(f'  สกุลเงินจาก IP นี้: "{sample}" → {"฿ ตรงๆ ไม่ต้องแปลง" if native_thb else "แปลงเป็น ฿ ด้วยเรตตลาด"}')

    rate = None
    if not native_thb:
        rate = get_usd_thb_rate()
        if rate is None:
            print('❌ หาเรต USD→THB ไม่ได้ (ทั้ง er-api และ frankfurter) — ยกเลิก ไม่เขียนราคา')
            sys.exit(2)
        print(f'  เรต: 1 USD = {rate:.4f} THB')

    # ดึงที่เหลือขนานกัน
    pages = list(range(PAGE_SIZE, total_count, PAGE_SIZE))
    page_results = {0: results0}
    failed = []
    done = 1
    total_pages = len(pages) + 1
    with ThreadPoolExecutor(max_workers=CONC) as pool:
        futs = {pool.submit(fetch_page, s): s for s in pages}
        for fut in as_completed(futs):
            s = futs[fut]
            res = fut.result()
            done += 1
            if res is None:
                failed.append(s)
                print(f'  ✗ [start={s}] พังถาวร', flush=True)
            else:
                page_results[s] = res[0]
            if done % 10 == 0 or done == total_pages:
                print(f'  [{done}/{total_pages} หน้า] {done/total_pages*100:.0f}%', flush=True)

    if failed:
        print(f'\n❌ ดึงไม่ครบ {len(failed)} หน้า ({sorted(failed)[:5]}...) — ไม่เขียนราคา (เว็บใช้ราคาเดิม รอรอบหน้า)')
        sys.exit(3)

    # จับคู่ + แปลง
    matched, unparsed = 0, 0
    for s in sorted(page_results):
        for it in page_results[s]:
            ids = idx.get(it.get('hash_name', ''))
            if not ids:
                continue
            lowest = to_thb(it, rate)
            if lowest is None:
                unparsed += 1
                continue
            rec = {'lowest': lowest, 'volume': it.get('sell_listings', ''), 'median': ''}
            for iid in ids:      # gear: ราคาเดียวกันทุก level ที่ใช้ hash นี้
                prices[iid] = rec
            matched += len(ids)

    prices['_fetched_at'] = datetime.now(TH_TZ).isoformat(timespec='seconds')
    if rate:
        prices['_rate'] = round(rate, 4)   # เรตที่ใช้แปลง (ไม่มี key นี้ = ได้ ฿ ตรงจาก Steam)
    elif '_rate' in prices:
        del prices['_rate']
    save_json(PRICES_FILE, prices)

    elapsed = time.time() - start_time
    stored = len([k for k in prices if not str(k).startswith('_')])
    print(f'\n{"─"*55}')
    print(f'✅ จับคู่ราคาได้ {matched:,} จาก {n_ids:,} เป้าหมาย  (ใช้เวลา {int(elapsed)}s)')
    if unparsed:
        print(f'   ⚠ parse ไม่ได้ {unparsed:,} ตัว (สกุลเงินแปลก?)')
    print(f'   ทั้งหมดใน tbh_prices.json: {stored:,} items')
    print(f'\nขั้นต่อไป: python gen_tbh.py  →  rebuild index.html')
    print(f'{"─"*55}')

    if matched == 0:
        sys.exit(3)  # exit code 3 = ไม่ได้ราคาเลย — Action/บั๊ตช์ไม่ต้อง deploy

if __name__ == '__main__':
    main()
