"""ดึง drop/มอนสเตอร์ต่อด่านจาก wiki ครบทั้ง 120 ด่าน (key จริงตามระดับ)
แก้บั๊กเดิมที่ใช้ key Normal ดึง drop ให้ทุกระดับ → Nightmare/Hell/Torment เลยโชว์ของ Lv1 หมด
endpoint: /data/stages/<key>.json  (key = prefix*1000+act*100+no; NORMAL=1 NIGHTMARE=2 HELL=3 TORMENT=4)
"""
import json, time, urllib.request, pathlib

BASE = pathlib.Path(__file__).parent
WIKI = 'https://taskbarhero.wiki'
HDR = {'User-Agent': 'Mozilla/5.0'}


def bi(d):
    """i18n dict → {'en','th'} (fallback th→en)"""
    d = d or {}
    en = d.get('en-US') or d.get('en') or ''
    th = d.get('th-TH') or d.get('th') or en
    return {'en': en, 'th': th}


def _entry_name(e):
    src = e.get('group') or e.get('item') or {}
    return src.get('name_i18n') or src.get('name') or {}


def _box(b):
    if not b:
        return None
    bx = b.get('box') or {}
    icon = bx.get('icon') or ''
    entries = []
    for e in (b.get('table') or {}).get('entries', []):
        src = e.get('group') or e.get('item') or {}
        eicon = (e.get('item') or {}).get('icon') or ''
        entries.append({
            'name': bi(_entry_name(e)),
            'pct': e.get('pct'),
            'icon': (WIKI + eicon) if eicon else '',
            'grade': src.get('grade', ''),
        })
    return {
        'box_name': bi(bx.get('name')),
        'grade': bx.get('grade', ''),
        'icon': (WIKI + icon) if icon else '',
        'entries': entries,
    }


def fetch(key):
    req = urllib.request.Request(f'{WIKI}/data/stages/{key}.json', headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    stages = json.load(open(BASE / 'tbh_stages.json', encoding='utf-8'))
    keys = [s['key'] for s in stages]
    out = {}
    for i, key in enumerate(keys, 1):
        for attempt in range(3):
            try:
                d = fetch(key)
                break
            except Exception as ex:
                print(f'  retry {key}: {ex}')
                time.sleep(2)
        else:
            print(f'  FAILED {key}')
            continue
        drops = d.get('drops') or {}
        monsters = [{
            'name': bi(m.get('name')),
            'portrait': WIKI + m['portrait'],
            'spawn': m.get('spawnPct'),
        } for m in d.get('monsters', []) if m.get('portrait') and (m.get('name') or {}).get('en-US')]
        out[str(key)] = {
            'monsters': monsters,
            'perWave': d.get('perWave'),
            'monsterBox': _box(drops.get('monster')),
            'bossBox': _box(drops.get('boss')),
        }
        print(f'[{i}/{len(keys)}] {key}  monsters={len(monsters)}  mBox={"y" if out[str(key)]["monsterBox"] else "-"}  bBox={"y" if out[str(key)]["bossBox"] else "-"}')
        time.sleep(0.3)
    json.dump(out, open(BASE / 'tbh_stage_details.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'Saved {len(out)} stages → tbh_stage_details.json')


if __name__ == '__main__':
    main()
