#!/usr/bin/env python3
"""
update_data.py — ดึง game data ใหม่จาก taskbarhero.wiki แล้ว rebuild

รัน:
  python update_data.py          # ดึง data + rebuild
  python update_data.py --dry    # แค่เช็คว่า URL ใช้ได้ไหม ไม่ save
"""
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
try:
    import requests
except ImportError:
    print('ติดตั้ง requests ก่อน: pip install requests')
    sys.exit(1)

BASE    = os.path.dirname(os.path.abspath(__file__))
WIKI    = 'https://taskbarhero.wiki'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
DRY     = '--dry' in sys.argv

FILES = [
    (f'{WIKI}/data/items.json',             'tbh_items.json',           'Items (ชื่อ/icon/grade/type)'),
    (f'{WIKI}/data/items_detail.json',      'tbh_items_detail.json',    'Items detail (base/inherent stats)'),
    (f'{WIKI}/data/t/materials.json',       'tbh_materials.json',       'Materials'),
    (f'{WIKI}/data/t/stat_mod_groups.json', 'tbh_stat_mod_groups.json', 'Stat mod groups'),
    (f'{WIKI}/data/t/stat_mods.json',       'tbh_stat_mods.json',       'Stat mods (min/max per tier)'),
    (f'{WIKI}/data/stat_strings.json',      'tbh_stat_strings.json',    'Stat display names'),
    (f'{WIKI}/data/t/gear_type_scales',     'tbh_gear_types.json',      'Gear type base stats'),
    (f'{WIKI}/data/grades.json',            'tbh_grades.json',          'Grades'),
    (f'{WIKI}/data/t/levels.json',          'tbh_levels.json',          'Levels (ExpForLevelUp ต่อเลเวล)'),
    (f'{WIKI}/data/rune_tree.json',         'tbh_rune_tree.json',       'Rune tree (nodes/effect/levels/cost)'),
    (f'{WIKI}/data/runes.json',             'tbh_runes.json',           'Runes (i18n names)'),
]

def download(url, dest_path, label):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if not DRY:
                with open(dest_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            count = len(data) if isinstance(data, list) else len(data) if isinstance(data, dict) else '?'
            print(f'  ✅ {label:<35} {count} items{"  (dry)" if DRY else ""}')
            return True
        else:
            if os.path.exists(dest_path):
                print(f'  ⚠ {label:<35} HTTP {r.status_code} (kept existing file)')
                return True
            print(f'  ❌ {label:<35} HTTP {r.status_code}')
            return False
    except Exception as e:
        print(f'  ❌ {label:<35} {e}')
        return False

def main():
    print(f'\n{"─"*55}')
    print(f'  TBH Data Updater{"  [DRY RUN]" if DRY else ""}')
    print('-'*55)
    print('ดาวน์โหลด game data จาก wiki...\n')

    ok = 0
    for url, filename, label in FILES:
        dest = os.path.join(BASE, filename)
        if download(url, dest, label):
            ok += 1

    print(f'\n{ok}/{len(FILES)} ไฟล์สำเร็จ')

    if ok < len(FILES):
        print('\n⚠ บางไฟล์ดาวน์โหลดไม่ได้ — ตรวจสอบ internet หรือ wiki อาจ down')
        if ok == 0:
            sys.exit(1)

    if DRY:
        print('\n[DRY RUN] ไม่ได้ save หรือ rebuild')
        return

    # Rebuild index.html
    print(f'\n{"─"*55}')
    print('Rebuild index.html...')
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, 'gen_tbh.py')],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout.strip())
        print('\n✅ เสร็จ! index.html อัพเดทแล้ว')
        print('-'*55)
        print('\nขั้นต่อไป (ถ้าต้องการ):')
        print('  python fetch_prices.py --reset   ← ดึงราคาใหม่ทั้งหมด')
        print('  python fetch_prices.py            ← ดึงเฉพาะ item ใหม่ที่ยังไม่มีราคา')
    else:
        print('❌ gen_tbh.py error:')
        print(result.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
