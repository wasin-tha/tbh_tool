#!/usr/bin/env python3
"""
fetch_prices.py — ดึงราคา Steam Market (THB) สำหรับ TBH materials + equipment

ใช้ Steam Market "search/render" endpoint ที่คืน JSON ทีละ 10 ตัว/หน้า
→ ดึงครบทั้ง mat + gear ใน ~75 requests (เร็วกว่ายิงทีละ item มาก, โดน ban ยากกว่า)

รัน:
  python fetch_prices.py              # ดึงราคาทุกอย่าง (mat + gear)
  python fetch_prices.py --mat-only   # เก็บเฉพาะ materials
  python fetch_prices.py --gear-only  # เก็บเฉพาะ equipment
  python fetch_prices.py --reset      # ล้าง progress แล้วดึงใหม่ทั้งหมด
"""
import json, time, sys, os
from datetime import datetime, timezone, timedelta
TH_TZ = timezone(timedelta(hours=7))  # เวลาไทย (runner เป็น UTC จึงต้อง fix)
sys.stdout.reconfigure(encoding='utf-8')
try:
    import requests
except ImportError:
    print('ติดตั้ง requests ก่อน: pip install requests')
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.abspath(__file__))
APP_ID      = '3678970'
CURRENCY    = 14        # 14 = บาท (THB) — ห้ามใช้ 40
PAGE_SIZE   = 10        # Steam cap หน้าละ 10 (beta)
DELAY       = 2.0       # วินาที ระหว่างหน้า (~3.5 นาที; ลดได้อีกแต่เสี่ยง 429 มากขึ้น)
COOLDOWN    = 45        # วินาที เมื่อโดน 429
MAX_RETRIES = 3         # retry ต่อหน้า หลัง 429
RENDER_URL  = ('https://steamcommunity.com/market/search/render/'
               f'?norender=1&appid={APP_ID}&currency={CURRENCY}'
               '&sort_column=popular&sort_dir=desc')
HEADERS     = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
THB         = '฿'  # ฿

PRICES_FILE = os.path.join(BASE, 'tbh_prices.json')
COOKIE_FILE = os.path.join(BASE, 'steam_cookie.txt')  # วาง steamLoginSecure ที่นี่ (ห้าม commit!)
LEG_PLUS    = {'LEGENDARY','IMMORTAL','ARCANA','BEYOND','CELESTIAL','DIVINE','COSMIC'}

def load_cookies():
    """อ่าน Steam login cookie → ทำให้ render คืนราคาตามสกุลเงินบัญชี (฿) แทน USD
    รองรับ: ค่า steamLoginSecure ล้วน หรือ cookie header เต็ม ('a=1; b=2')"""
    raw = ''
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, encoding='utf-8') as f:
            raw = f.read().strip()
    raw = raw or os.environ.get('STEAM_COOKIE', '').strip()
    if not raw:
        return None
    if ';' in raw or ('=' in raw and 'steamLoginSecure' in raw):
        jar = {}
        for part in raw.split(';'):
            if '=' in part:
                k, v = part.strip().split('=', 1)
                jar[k] = v
        return jar or None
    return {'steamLoginSecure': raw}

COOKIES = load_cookies()

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Build  market_hash_name → item_id  index ───────────────────────────────────
def build_index(mode='all'):
    """{market_hash_name: [item_id, ...]} — gear หลาย level ใช้ hash เดียวกัน จึง map เป็น list"""
    items_list = load_json(os.path.join(BASE, 'tbh_items.json'), [])
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

# ── Fetch one page ─────────────────────────────────────────────────────────────
def fetch_page(start):
    """คืน (results:list, total_count:int) | 'RATELIMIT' | None"""
    url = f'{RENDER_URL}&start={start}&count={PAGE_SIZE}'
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
            if r.status_code == 200:
                d = r.json()
                if not d.get('success'):
                    return None
                return d.get('results', []), d.get('total_count', 0)
            if r.status_code == 429:
                wait = COOLDOWN + attempt * 20
                print(f'\n  ⚠ Rate limit! รอ {wait}s...', flush=True)
                time.sleep(wait)
                continue
            return None
        except Exception as e:
            print(f'\n  error: {e}', flush=True)
            time.sleep(5)
    return 'RATELIMIT'

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    mode = 'mat-only' if '--mat-only' in args else 'gear-only' if '--gear-only' in args else 'all'
    reset = '--reset' in args

    idx    = build_index(mode)
    n_ids  = sum(len(v) for v in idx.values())
    prices = {} if reset else load_json(PRICES_FILE)

    print(f'\n{"─"*55}')
    print(f'  เป้าหมาย   : {len(idx):,} ชื่อ ({n_ids:,} items) — {mode}')
    print(f'  วิธี       : Steam search/render — หน้าละ {PAGE_SIZE} ตัว')
    print(f'  Login      : {"✅ ใช้ cookie (ราคาตามบัญชี)" if COOKIES else "❌ ไม่มี cookie (อาจได้ USD)"}')
    print(f'  Ctrl+C เพื่อหยุด (ราคาที่ได้จะ save ให้)')
    print(f'{"─"*55}\n')

    matched, noncur, total_count, start = 0, 0, None, 0
    start_time = time.time()

    # ── ยืนยันสกุลเงิน ฿ ก่อนเริ่ม — currency จาก runner (IP US) แกว่ง: บางครั้งคืน $ ทั้งที่ cookie valid
    #    → retry หลายรอบจนกว่าจะได้ ฿ (แทนที่จะ fail ทันทีเหมือนเดิม)
    CUR_RETRIES = 12
    for attempt in range(CUR_RETRIES):
        res = fetch_page(0)
        if res in ('RATELIMIT', None):
            time.sleep(10); continue
        r0, total_count = res
        if r0 and THB in r0[0].get('sell_price_text', ''):
            break   # ได้ ฿ แล้ว — เริ่มดึงจริง (loop จะ fetch หน้า 0 ใหม่)
        ex = (r0[0].get('sell_price_text', '') if r0 else '?')
        print(f'  สกุลเงินยังไม่ใช่ ฿ ("{ex}") — retry {attempt+1}/{CUR_RETRIES}', flush=True)
        time.sleep(12)
    else:
        print('❌ retry ครบแล้วยังไม่ได้ ฿ — cookie หมดอายุ/ไม่ valid')
        print(f'   อัปเดต Secret STEAM_COOKIE (หรือไฟล์ {COOKIE_FILE}) แล้วรันใหม่')
        sys.exit(2)  # exit 2 = cookie/สกุลเงินผิด

    try:
        while total_count is None or start < total_count:
            res = fetch_page(start)
            if res == 'RATELIMIT':
                print('\n⚠ โดน rate limit — หยุดก่อน (ราคาที่ได้ save แล้ว) รอ ~15–30 นาที แล้วรันใหม่')
                break
            if not res:
                print(f'  [start={start}] หน้าว่าง/ผิดพลาด — ข้าม')
                start += PAGE_SIZE
                continue
            results, total_count = res

            for it in results:
                ids = idx.get(it.get('hash_name', ''))
                if not ids:
                    continue
                txt = it.get('sell_price_text', '')
                if THB not in txt:   # กันเก็บราคาผิดสกุล (เช่นบางหน้าเด้งเป็น USD)
                    noncur += 1
                    continue
                rec = {'lowest': txt, 'volume': it.get('sell_listings', ''), 'median': ''}
                for iid in ids:      # gear: ราคาเดียวกันทุก level ที่ใช้ hash นี้
                    prices[iid] = rec
                matched += len(ids)

            pct = (start + len(results)) / total_count * 100 if total_count else 0
            print(f'  [{start+len(results):>4}/{total_count}] {pct:5.1f}%  จับคู่ได้ {matched:,}', flush=True)

            start += PAGE_SIZE
            if start < (total_count or 0):
                time.sleep(DELAY)
    except KeyboardInterrupt:
        print('\n⏸ หยุดแล้ว')

    prices['_fetched_at'] = datetime.now(TH_TZ).isoformat(timespec='seconds')
    save_json(PRICES_FILE, prices)

    elapsed = time.time() - start_time
    stored = len([k for k in prices if k != '_fetched_at'])
    print(f'\n{"─"*55}')
    print(f'✅ จับคู่ราคาได้ {matched:,} จาก {n_ids:,} เป้าหมาย  (ใช้เวลา {int(elapsed)}s)')
    if noncur:
        print(f'   ⚠ ข้าม {noncur:,} ตัวที่ราคาไม่ใช่ THB (อาจเพราะ IP ไม่ใช่ไทย)')
    print(f'   ทั้งหมดใน tbh_prices.json: {stored:,} items')
    print(f'\nขั้นต่อไป: python gen_tbh.py  →  rebuild index.html')
    print(f'{"─"*55}')

    if matched == 0:
        sys.exit(3)  # exit code 3 = ไม่ได้ราคาเลย (rate limit ตั้งแต่แรก) — .bat ไม่ต้อง deploy

if __name__ == '__main__':
    main()
