import json, re
from urllib.parse import quote

# ── Load data ────────────────────────────────────────────────────────────────
import os as _os
BASE = _os.path.dirname(_os.path.abspath(__file__))

with open(f'{BASE}/tbh_items.json', encoding='utf-8') as f:
    items_list = json.load(f)
with open(f'{BASE}/tbh_materials.json', encoding='utf-8') as f:
    mats_raw = json.load(f)
with open(f'{BASE}/tbh_stat_mod_groups.json', encoding='utf-8') as f:
    groups_raw = json.load(f)
with open(f'{BASE}/tbh_stat_mods.json', encoding='utf-8') as f:
    mods_raw = json.load(f)
with open(f'{BASE}/tbh_stat_strings.json', encoding='utf-8') as f:
    stat_strings = json.load(f)
with open(f'{BASE}/tbh_prices.json', encoding='utf-8') as f:
    prices_raw = json.load(f)
with open(f'{BASE}/tbh_items_detail.json', encoding='utf-8') as f:
    items_detail = json.load(f)
with open(f'{BASE}/tbh_gear_types.json', encoding='utf-8') as f:
    gear_types_raw = json.load(f)
with open(f'{BASE}/tbh_heroes.json', encoding='utf-8') as f:
    heroes_raw = json.load(f)
with open(f'{BASE}/tbh_skills.json', encoding='utf-8') as f:
    skills_raw = json.load(f)
with open(f'{BASE}/tbh_passive_skills.json', encoding='utf-8') as f:
    passives_raw = json.load(f)
with open(f'{BASE}/tbh_stages.json', encoding='utf-8') as f:
    stages_raw = json.load(f)
with open(f'{BASE}/tbh_stage_details.json', encoding='utf-8') as f:
    stage_details_raw = json.load(f)
# (tbh_portal_map.json ไม่ได้ใช้แล้ว — เปลี่ยนเป็นตาราง stage จึงไม่ load)
with open(f'{BASE}/tbh_pets.json', encoding='utf-8') as f:
    pets_raw = json.load(f)
with open(f'{BASE}/tbh_monsters.json', encoding='utf-8') as f:
    monsters_raw = json.load(f)
with open(f'{BASE}/tbh_unique_mods_desc.json', encoding='utf-8') as f:
    unique_mods_desc = json.load(f)
with open(f'{BASE}/tbh_recipes.json', encoding='utf-8') as f:
    recipes_raw = json.load(f)
with open(f'{BASE}/tbh_rune_tree.json', encoding='utf-8') as f:
    rune_tree_raw = json.load(f)
with open(f'{BASE}/tbh_runes.json', encoding='utf-8') as f:
    runes_raw = json.load(f)
with open(f'{BASE}/tbh_skill_maxlevel.json', encoding='utf-8') as f:
    _ml = json.load(f)
skill_maxlevel   = {int(k): v for k, v in _ml.get('skills', {}).items()}
passive_maxlevel = {int(k): v for k, v in _ml.get('passives', {}).items()}

prices = {int(k): v for k, v in prices_raw.items() if k != '_fetched_at'}

_THAI_MON = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']
def _fmt_price_date(iso):
    if not iso: return ''
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso)
        return f'{dt.day} {_THAI_MON[dt.month-1]} {str(dt.year+543)[-2:]} {dt.hour:02d}:{dt.minute:02d}'
    except: return ''
PRICE_DATE = _fmt_price_date(prices_raw.get('_fetched_at', ''))
PRICE_DATE_HTML = (f'<span style="margin-left:auto;font-size:11px;color:var(--muted)">'
                   f'ราคา • อัพเดท {PRICE_DATE}</span>') if PRICE_DATE else ''
items_by_id = {i['id']: i for i in items_list}
mods_by_key = {}
for m in mods_raw:
    mods_by_key.setdefault(m['StatModKey'], []).append(m)
groups_by_group_key = {}
for g in groups_raw:
    groups_by_group_key.setdefault(g['StatModGroupKey'], []).append(g)

D_SET = {'CooldownReduction','CriticalChance','CriticalDamage','DodgeChance','BlockChance',
         'ElementalBlockChance','ElementalDodgeChance','HpLeech','IncreaseExpAmount',
         'IncreaseGoldAmount','SkillRangeExpansion','DamageReduction','PhysicalDamageReduction',
         'FireDamageReduction','ColdDamageReduction','LightningDamageReduction','ChaosDamageReduction'}

def get_fmt(stat, mod):
    if stat.endswith('Resistance') or stat in ('MaxBlockChance','MaxDodgeChance'): return 'rawpct'
    if stat.endswith('Percent') or mod in ('ADDITIVE','MULTIPLICATIVE') or stat in D_SET: return 'div10'
    return 'flat'

def scale(val, fmt):
    if fmt == 'div10':
        v = val / 10
        return int(v) if v == int(v) else round(v, 1)
    return val

import html as _html

def _esc_min(s):
    return _html.escape(str(s or ''), quote=True)

def bi(d):
    """i18n dict (en-US/th-TH), {en,th}, {e,t}, or str → dual-span HTML."""
    if isinstance(d, dict):
        en = d.get('en-US') or d.get('en') or d.get('e') or ''
        th = d.get('th-TH') or d.get('th') or d.get('t') or en
    else:
        en = th = str(d or '')
    return f'<span class="en">{_esc_min(en)}</span><span class="th">{_esc_min(th)}</span>'

def biobj(d):
    """i18n dict → {'e':en,'t':th} for embedding in JS data."""
    if isinstance(d, dict):
        en = d.get('en-US', d.get('en', '')) or ''
        th = d.get('th-TH', d.get('th', '')) or en
    else:
        en = th = str(d or '')
    return {'e': en, 't': th}

def get_stat_name(stat_type, lang='en-US'):
    ss = stat_strings.get(stat_type, {})
    n = (ss.get('name') or {}).get(lang, '') if ss else ''
    if not n and lang != 'en-US':
        n = (ss.get('name') or {}).get('en-US', '') if ss else ''
    if n: return n
    line = (ss.get('line') or {}).get(lang, '') or (ss.get('line') or {}).get('en-US', '') if ss else ''
    if line:
        return re.sub(r'\s*\+\{0\}.*$', '', line).strip()
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', stat_type)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s).replace('_', ' ')
    return s.title()

def get_stat_name_bi(stat_type):
    return {'e': get_stat_name(stat_type, 'en-US'), 't': get_stat_name(stat_type, 'th-TH')}

def fmt_range(stat, mod, lo, hi):
    if stat == 'AttackSpeed' and mod in ('FLAT', None):
        a, b = f'{lo/100:.2f}', f'{hi/100:.2f}'
        return f'+{a}/s' if a == b else f'+{a}~{b}/s'
    fmt = get_fmt(stat, mod)
    sfx = '' if fmt == 'flat' else '%'
    a, b = scale(lo, fmt), scale(hi, fmt)
    return f'+{a}{sfx}' if a == b else f'+{a}~{b}{sfx}'

GRADE_ORDER = ['COMMON','UNCOMMON','RARE','LEGENDARY','IMMORTAL','ARCANA','BEYOND','CELESTIAL','DIVINE','COSMIC']
GRADE_COLORS = {
    'COMMON':'#c8cad6','UNCOMMON':'#54fc0c','RARE':'#4d9eff','LEGENDARY':'#fc9c0c',
    'IMMORTAL':'#fc2424','ARCANA':'#c84dff','BEYOND':'#ff4d8f','CELESTIAL':'#6ccce4',
    'DIVINE':'#fce454','COSMIC':'#fcfcfc'
}
SLOT_ORDER = ['WEAPON','ARMOR','ACCESSORY','COMMON']
APP_ID = '3678970'
WIKI_BASE = 'https://taskbarhero.wiki'

# ── Official Thai terms (Steam Market / in-game, cross-checked w/ drop data) ──
GRADE_TH = {
    'COMMON':'ธรรมดา','UNCOMMON':'ไม่ธรรมดา','RARE':'หายาก','LEGENDARY':'ตำนาน',
    'IMMORTAL':'อมตะ','ARCANA':'อาร์คานา','BEYOND':'เหนือขีดจำกัด','CELESTIAL':'สวรรค์',
    'DIVINE':'ศักดิ์สิทธิ์','COSMIC':'จักรวาล',
}
# gear type → Thai (from drop data + Steam); 6 missing (no official source)
GEARTYPE_TH = {
    'SWORD':'ดาบ','AXE':'ขวาน','HATCHET':'ขวานมือ','CROSSBOW':'หน้าไม้',
    'SHIELD':'โล่','BOLT':'ลูกธนูหน้าไม้',
    'HELMET':'หมวก','ARMOR':'เกราะ','GLOVES':'ถุงมือ','BOOTS':'รองเท้า',
    'AMULET':'สร้อยคอ','EARING':'ต่างหู','RING':'แหวน','BRACER':'สายรัดข้อมือ',
}
SLOT_GROUP_TH = {'Weapon':'อาวุธหลัก','Offhand':'อาวุธรอง','Armor':'เกราะ','Accessory':'เครื่องประดับ'}
CLASS_TH = {'Knight':'อัศวิน','Ranger':'เรนเจอร์','Sorcerer':'จอมเวท','Priest':'นักบวช','Hunter':'นักล่า','Slayer':'สเลเยอร์'}

def gb(en, th):
    """dual-span from explicit en/th strings."""
    return f'<span class="en">{_esc_min(en)}</span><span class="th">{_esc_min(th)}</span>'

# ── Build material data ───────────────────────────────────────────────────────
materials = []
for mat in mats_raw:
    item = items_by_id.get(mat['ItemKey'])
    if not item or item.get('type') != 'MATERIAL': continue
    raw_name = item.get('name')
    if not raw_name or not isinstance(raw_name, dict): continue
    name = raw_name.get('en-US', '')
    if not name: continue

    grade = item.get('grade', 'COMMON')
    slots = []
    group_key = mat.get('StatModGroupKey')
    if group_key and group_key in groups_by_group_key:
        slot_dict = {}
        for g in groups_by_group_key[group_key]:
            gear = g['GearGroup']
            tmods = [m for m in mods_by_key.get(g['StatModKey'], [])
                     if g['MinTier'] <= m['Tier'] <= g['MaxTier']]
            if not tmods: continue
            first = tmods[0]
            st, mt = first['STATTYPE'], first['MODTYPE']
            lo = min(m['MinValue'] for m in tmods)
            hi = max(m['MaxValue'] for m in tmods)
            tier = f"T{g['MinTier']}" if g['MinTier'] == g['MaxTier'] else f"T{g['MinTier']}-{g['MaxTier']}"
            slot_dict.setdefault(gear, []).append(
                {'stat': get_stat_name(st), 'stat_bi': get_stat_name_bi(st),
                 'value': fmt_range(st, mt, lo, hi), 'tier': tier}
            )
        for s in SLOT_ORDER:
            if s in slot_dict:
                slots.append({'slot': s.capitalize(), 'stats': slot_dict[s]})

    p = prices.get(item['id'])
    price_str  = (p.get('lowest', '')  if isinstance(p, dict) else '')
    volume_str = (p.get('volume', '')  if isinstance(p, dict) else '')

    materials.append({
        'id': item['id'],
        'name': name,
        'name_bi': biobj(raw_name),
        'grade': grade,
        'grade_order': GRADE_ORDER.index(grade) if grade in GRADE_ORDER else 99,
        'mat_type': mat.get('MATERIALTYPE', '').capitalize(),
        'icon_url': f"{WIKI_BASE}{item['icon']}" if item.get('icon') else '',
        'marketable': item.get('marketable', False),
        'steam_url': f"https://steamcommunity.com/market/listings/{APP_ID}/{quote(name)}",
        'slots': slots,
        'slot_names': ','.join(s['slot'] for s in slots),  # unique per slot group
        'stat_names': sorted({st['stat'] for s in slots for st in s['stats']}),
        'stats_by_slot': {s['slot']: [st['stat'] for st in s['stats']] for s in slots},
        'color': GRADE_COLORS.get(grade, '#8b94a7'),
        'price': price_str,
        'volume': volume_str,
    })

materials.sort(key=lambda x: (x['grade_order'], x['id']))
COUNT = len(materials)
ALL_STATS = sorted({s for m in materials for s in m['stat_names']})
# en→th map for effect dropdown labels
_stat_th = {}
for m in materials:
    for s in m['slots']:
        for st in s['stats']:
            _stat_th[st['stat_bi']['e']] = st['stat_bi']['t']
print(f'Processed {COUNT} materials')

# ── Build gear data ───────────────────────────────────────────────────────────
gt_map = {g['GearType']: g for g in gear_types_raw}  # gear type -> base stat info

SLOT_GROUP = {}
for gt in ['SWORD','BOW','STAFF','SCEPTER','CROSSBOW','AXE']:
    SLOT_GROUP[gt] = 'Weapon'
for gt in ['SHIELD','ARROW','ORB','TOME','BOLT','HATCHET']:
    SLOT_GROUP[gt] = 'Offhand'
for gt in ['HELMET','ARMOR','GLOVES','BOOTS']:
    SLOT_GROUP[gt] = 'Armor'
for gt in ['AMULET','EARING','RING','BRACER']:
    SLOT_GROUP[gt] = 'Accessory'

LEG_PLUS = {'LEGENDARY','IMMORTAL','ARCANA','BEYOND','CELESTIAL','DIVINE','COSMIC'}

def fmt_single(stat, mod, val):
    """Format a single stat value for display."""
    if val is None or val == 0:
        return None
    if stat == 'AttackSpeed' and mod in ('FLAT', None):
        return f'+{val/100:.2f}/s'
    fmt = get_fmt(stat, mod)
    sfx = '' if fmt == 'flat' else '%'
    v = scale(val, fmt)
    return f'+{v}{sfx}'

def item_stats(iid):
    """base + inherent stats (bilingual) for any gear item id — for crafting possible-items."""
    item = items_by_id.get(iid, {})
    det = items_detail.get(str(iid), {})
    sraw = det.get('stats') or {}
    gtype = item.get('gear', '')
    bs = []
    if gtype in gt_map:
        gi = gt_map[gtype]
        for n in (1, 2):
            st = gi.get(f'BaseStat{n}_STATTYPE', '')
            md = gi.get(f'BaseStat{n}_MODTYPE', 'FLAT')
            vl = sraw.get(f'BaseStat{n}_Value')
            if st and st != 'NONE' and vl:
                disp = fmt_single(st, md, vl)
                if disp: bs.append({'label': get_stat_name_bi(st), 'value': disp})
    ih = []
    for n in (1, 2, 3):
        st = sraw.get(f'InherentStat{n}_STATTYPE', 'NONE')
        md = sraw.get(f'InherentStat{n}_MODTYPE', 'FLAT')
        vl = sraw.get(f'InherentStat{n}_Value', 0)
        if st and st != 'NONE' and vl:
            disp = fmt_single(st, md, vl)
            if disp: ih.append({'label': get_stat_name_bi(st), 'value': disp})
    return bs, ih

gear_data = []
for item in items_list:
    if item.get('type') != 'GEAR': continue
    if item.get('grade') not in LEG_PLUS: continue
    raw_name = item.get('name')
    if not raw_name or not isinstance(raw_name, dict): continue
    name = raw_name.get('en-US', '')
    if not name: continue

    gear_type = item.get('gear', '')
    grade     = item.get('grade', '')
    level     = item.get('level', 0)
    icon_url  = f"{WIKI_BASE}{item['icon']}" if item.get('icon') else ''
    slot      = SLOT_GROUP.get(gear_type, 'Other')
    steam_url = f"https://steamcommunity.com/market/listings/{APP_ID}/{quote(f'{name} ({grade.capitalize()}) A')}"

    det  = items_detail.get(str(item['id']), {})
    stats_raw = det.get('stats') or {}
    _um_key = det.get('uniqueMod') or ''
    # full description from Steam (matches in-game); fallback to spaced key
    unique_mod = unique_mods_desc.get(_um_key) or (re.sub(r'([A-Z])', r' \1', _um_key).strip() if _um_key else '')

    # Base stats (weapon/armor gear types have defined base stat types)
    base_stats = []
    if gear_type in gt_map:
        gt_info = gt_map[gear_type]
        for n in (1, 2):
            st   = gt_info.get(f'BaseStat{n}_STATTYPE', '')
            mod  = gt_info.get(f'BaseStat{n}_MODTYPE', 'FLAT')
            val  = stats_raw.get(f'BaseStat{n}_Value')
            if st and st != 'NONE' and val:
                disp  = fmt_single(st, mod, val)
                if disp:
                    base_stats.append({'label': get_stat_name_bi(st), 'value': disp})

    # Inherent stats (up to 3)
    inherent = []
    for n in (1, 2, 3):
        st  = stats_raw.get(f'InherentStat{n}_STATTYPE', 'NONE')
        mod = stats_raw.get(f'InherentStat{n}_MODTYPE', 'FLAT')
        val = stats_raw.get(f'InherentStat{n}_Value', 0)
        if st and st != 'NONE' and val:
            disp  = fmt_single(st, mod, val)
            if disp:
                inherent.append({'label': get_stat_name_bi(st), 'value': disp})

    gear_data.append({
        'id':         item['id'],
        'name':       name,
        'name_bi':    biobj(raw_name),
        'grade':      grade,
        'grade_order': GRADE_ORDER.index(grade) if grade in GRADE_ORDER else 99,
        'gear_type':  gear_type,
        'slot':       slot,
        'level':      level,
        'icon_url':   icon_url,
        'steam_url':  steam_url,
        'color':      GRADE_COLORS.get(grade, '#8b94a7'),
        'base_stats': base_stats,
        'inherent':   inherent,
        'unique_mod': unique_mod,
        'unique_key': _um_key,
    })

# Deduplicate: keep first variant per (name, grade, gear_type, level)
seen_keys = set()
gear_deduped = []
for g in gear_data:
    key = (g['name'], g['grade'], g['gear_type'], g['level'])
    if key not in seen_keys:
        seen_keys.add(key)
        gear_deduped.append(g)
gear_data = gear_deduped

gear_data.sort(key=lambda x: (x['grade_order'], x['gear_type'], x['level']))
GEAR_COUNT = len(gear_data)
print(f'Processed {GEAR_COUNT} gear items (Legendary+, deduped)')

# Serialize gear data as compact JSON for embedding in JS
import json as _json
GEAR_JSON = _json.dumps([{
    'id':   g['id'],
    'n':    g['name'],
    'nb':   g['name_bi'],
    'gr':   g['grade'],
    'go':   g['grade_order'],
    'gt':   g['gear_type'],
    'sl':   g['slot'],
    'lv':   g['level'],
    'ic':   g['icon_url'],
    'su':   g['steam_url'],
    'co':   g['color'],
    'pr':   prices.get(g['id'], {}).get('lowest', '') if isinstance(prices.get(g['id']), dict) else '',
    'pv':   prices.get(g['id'], {}).get('volume', '')  if isinstance(prices.get(g['id']), dict) else '',
    'bs':   g['base_stats'],
    'ih':   g['inherent'],
    'um':   g['unique_mod'],
    'uk':   g['unique_key'],
} for g in gear_data], ensure_ascii=False, separators=(',', ':'))

# ── Build skills data ────────────────────────────────────────────────────────
HERO_COLORS = {
    'Knight':'#60a5fa','Ranger':'#4ade80','Sorcerer':'#a78bfa',
    'Priest':'#fcd34d','Hunter':'#f97316','Slayer':'#f87171',
}
ACTIVATION_LABEL = {
    'BASEATTACK_COUNT': lambda v: {'e': f'Every {v} attacks', 't': f'ทุก {v} การโจมตี'},
    'BASEATTACK':       lambda v: {'e': 'On attack', 't': 'เมื่อโจมตี'},
    'PASSIVE':          lambda v: {'e': 'Passive', 't': 'พาสซีฟ'},
}

passives_by_key = {p['PassiveSkillKey']: p for p in passives_raw}

heroes_skills_data = []
for h in heroes_raw:
    hero_key = h['HeroKey']
    prefix   = hero_key // 100  # 101→1, 201→2 ...
    cls      = h.get('ClassType', '')
    name_en  = h['HeroNameKey_i18n']['en-US']
    name_bi  = biobj(h.get('HeroNameKey_i18n'))
    _dd = h.get('DescriptionKey_i18n', {})
    desc_bi  = {'e': (_dd.get('en-US','') or '').replace('\n',' '),
                't': (_dd.get('th-TH') or _dd.get('en-US','') or '').replace('\n',' ')}

    active = []
    for s in skills_raw:
        if s.get('SLOTTYPE') != 'SKILL': continue
        if s['SkillKey'] // 10000 != prefix: continue
        sname = biobj(s.get('SkillNameKey_i18n'))
        sdesc = biobj(s.get('SkillDescriptionKey_i18n'))
        lvls  = s.get('levels', [])
        lv1   = lvls[0]['value']  if lvls else None
        lv10  = lvls[-1]['value'] if lvls else None  # ค่าสูงสุดใน database (cap ที่ Lv10)
        _mx   = skill_maxlevel.get(s['SkillKey'], len(lvls))  # max level ที่เล่นได้จริงในเกม (=5)
        lvmax = lvls[_mx-1]['value'] if lvls and 0 < _mx <= len(lvls) else lv10  # ค่าที่ Lv ตันจริง
        atype = s.get('ACTIVATIONTYPE', '')
        aval  = s.get('ActivationValue', 0)
        trigger = ACTIVATION_LABEL.get(atype, lambda v: {'e':atype,'t':atype})(aval)
        active.append({
            'key': s['SkillKey'], 'name': sname, 'desc': sdesc,
            'trigger': trigger, 'dmg_type': s.get('DamageType',''),
            'delivery': s.get('DamageDeliveryType',''),
            'lv1': lv1, 'lv10': lv10, 'lvmax': lvmax,
            'max_lv': _mx,
            'levels': [{'lv': l['level'], 'val': l['value']} for l in lvls],
            'icon': f"{WIKI_BASE}{s['icon']}" if s.get('icon') else '',
        })
    active.sort(key=lambda x: x['key'])

    passive = []
    for pk in h.get('attribute_keys', []):
        p = passives_by_key.get(pk)
        if not p: continue
        pname = biobj(p.get('SkillNameKey_i18n'))
        stat = p.get('STATTYPE', '')
        mod  = p.get('MODTYPE', '')
        val  = p.get('Value', 0)
        sl_bi = get_stat_name_bi(stat) if stat else {'e':'','t':''}
        val_str    = fmt_single(stat, mod, val) or f'+{val}'
        pdesc = {'e': f'Increases {sl_bi["e"]} by {val_str} per level.' if sl_bi['e'] else '',
                 't': f'เพิ่ม {sl_bi["t"]} {val_str} ต่อเลเวล' if sl_bi['t'] else ''}
        passive.append({
            'key': pk, 'name': pname,
            'stat': stat, 'mod': mod, 'value': val, 'desc': pdesc,
            'max_lv': passive_maxlevel.get(pk, 10),
            'icon': f"{WIKI_BASE}{p['icon']}" if p.get('icon') else '',
        })

    heroes_skills_data.append({
        'key': hero_key, 'name': name_en, 'name_bi': name_bi, 'class': cls,
        'desc': desc_bi,
        'icon': f"{WIKI_BASE}{h['icon']}" if h.get('icon') else '',
        'color': HERO_COLORS.get(cls, '#8b94a7'),
        'active': active, 'passive': passive,
    })

import json as _json2
HEROES_JSON = _json2.dumps(heroes_skills_data, ensure_ascii=False, separators=(',',':'))

# ── Build stages data ─────────────────────────────────────────────────────────
stages_by_key = {}
for s in stages_raw:
    base_key = 1000 + s['act']*100 + s['no']  # Normal key for monster lookup
    detail = stage_details_raw.get(str(base_key), {})
    monsters = [{
        'name': biobj(m['name']),
        'portrait': m['portrait'],
        'spawn': m['spawn'],
    } for m in detail.get('monsters', []) if (m.get('name') or {}).get('en') and m.get('portrait')]

    def _box_bi(box):
        if not box: return None
        return {
            'box_name': biobj(box.get('box_name')),
            'grade': box.get('grade',''),
            'icon': box.get('icon',''),
            'entries': [{'name': biobj(e['name']), 'pct': e['pct'],
                         'icon': e.get('icon',''), 'grade': e.get('grade','')}
                        for e in box.get('entries', [])],
        }

    stages_by_key[s['key']] = {
        'key':   s['key'],
        'act':   s['act'],
        'no':    s['no'],
        'level': s['level'],
        'type':  s['type'],
        'diff':  s['difficulty'],
        'name':    (s.get('name') or {}).get('en-US', f"Stage {s['no']}"),
        'name_bi': biobj(s.get('name')),
        'waves':   s.get('waves'),
        'perWave': detail.get('perWave') or None,
        'mobs':    s.get('monsterCount') or None,
        'kills':   s.get('kills') or None,
        'gold':  s.get('goldPerClear', 0),
        'exp':   s.get('expPerClear', 0),
        'boss_name':    ((s.get('boss') or {}).get('name') or {}).get('en-US', ''),
        'boss_bi':      biobj((s.get('boss') or {}).get('name')),
        'boss_portrait': f"{WIKI_BASE}{s['boss']['portrait']}" if s.get('boss') and s['boss'].get('portrait') else '',
        'monsters': monsters,
        'monsterBox': _box_bi(detail.get('monsterBox')),
        'bossBox':    _box_bi(detail.get('bossBox')),
    }

stages_json     = _json2.dumps(list(stages_by_key.values()), ensure_ascii=False, separators=(',',':'))
print(f'Processed {len(stages_by_key)} stages')

# ── Build crafting data ───────────────────────────────────────────────────────
CRAFT_TYPE_TH = {
    'MainWeapon':'อาวุธหลัก','SubWeapon':'อาวุธรอง','Helmet':'หมวก','Armor':'เกราะ',
    'Gloves':'ถุงมือ','Boots':'รองเท้า','Accessory':'เครื่องประดับ',
}
CRAFT_TYPE_EN = {
    'MainWeapon':'Main Weapon','SubWeapon':'Sub Weapon','Helmet':'Helmet','Armor':'Armor',
    'Gloves':'Gloves','Boots':'Boots','Accessory':'Accessory',
}

def _price_num(idv):
    p = prices.get(idv)
    if not isinstance(p, dict): return 0.0
    s = (p.get('lowest') or '').replace('฿', '').replace(',', '').strip()
    try: return float(s)
    except: return 0.0

craft_data = []
for r in recipes_raw.get('crafting', []):
    mats = []
    for m in r['materials']:
        mid = m['id']
        item = items_by_id.get(mid, {})
        nm_en = (m.get('name') or {}).get('en-US', '')
        mats.append({
            'name':  biobj(m.get('name')),
            'icon':  f"{WIKI_BASE}{m['icon']}" if m.get('icon') else '',
            'count': m.get('count', 1),
            'grade': m.get('grade', ''),
            'price': _price_num(mid),
            'su':    f"https://steamcommunity.com/market/listings/{APP_ID}/{quote(nm_en)}" if nm_en else '',
        })
    res = r.get('result', {})
    # possible result items — group by English name; collect per-grade prices (craft gives random grade)
    by_name = {}
    for grade_k, ids in res.get('itemsByGrade', {}).items():
        for iid in ids:
            it = items_by_id.get(iid)
            if not it or not isinstance(it.get('name'), dict): continue
            en = it['name'].get('en-US', '')
            if not en: continue
            entry = by_name.get(en)
            if entry is None:
                _bs, _ih = item_stats(iid)
                entry = {'n': biobj(it['name']),
                         'ic': f"{WIKI_BASE}{it['icon']}" if it.get('icon') else '',
                         'bs': _bs, 'ih': _ih, 'pr': []}
                by_name[en] = entry
            # price for this grade (if marketable + priced)
            p = prices.get(iid)
            if it.get('marketable') and isinstance(p, dict) and p.get('lowest'):
                entry['pr'].append({
                    'g': grade_k, 'p': p['lowest'],
                    'su': f"https://steamcommunity.com/market/listings/{APP_ID}/{quote(f'{en} ({grade_k.capitalize()}) A')}",
                })
    for e in by_name.values():
        e['pr'].sort(key=lambda x: GRADE_ORDER.index(x['g']) if x['g'] in GRADE_ORDER else 99)
    poss = sorted(by_name.values(), key=lambda x: x['n']['e'])
    craft_data.append({
        'type':  r['type'],
        'type_bi': {'e': CRAFT_TYPE_EN.get(r['type'], r['type']), 't': CRAFT_TYPE_TH.get(r['type'], r['type'])},
        'tier':  r['tier'],
        'lvMin': res.get('levelMin', 0),
        'lvMax': res.get('levelMax', 0),
        'odds':  [{'g': o['grade'], 'pct': o['pct']} for o in res.get('gradeOdds', [])],
        'mats':  mats,
        'poss':  poss,
    })
craft_json = _json2.dumps(craft_data, ensure_ascii=False, separators=(',',':'))
print(f'Processed {len(craft_data)} crafting recipes')

# ── Pet Thai names (en → th) ──────────────────────────────────────────────────
pet_th = {}
for p in pets_raw:
    i = p.get('NameKey_i18n') or {}
    en = i.get('en-US', '')
    if en:
        pet_th[en] = i.get('th-TH') or en
PET_TH_JSON = _json2.dumps(pet_th, ensure_ascii=False, separators=(',',':'))

# en→th maps for monster names (pet unlock) and stage names (farm locations)
monster_th = {}
for x in monsters_raw:
    i = x.get('MonsterNameStringKey_i18n') or {}
    en = i.get('en-US', '')
    if en:
        monster_th[en] = i.get('th-TH') or en
MONSTER_TH_JSON = _json2.dumps(monster_th, ensure_ascii=False, separators=(',',':'))

stage_name_th = {}
for s in stages_raw:
    nm = s.get('name') or {}
    en = nm.get('en-US', '')
    if en:
        stage_name_th[en] = nm.get('th-TH') or en
STAGE_NAME_TH_JSON = _json2.dumps(stage_name_th, ensure_ascii=False, separators=(',',':'))
GRADE_TH_JSON    = _json2.dumps(GRADE_TH, ensure_ascii=False, separators=(',',':'))
GEARTYPE_TH_JSON = _json2.dumps(GEARTYPE_TH, ensure_ascii=False, separators=(',',':'))
CLASS_TH_JSON    = _json2.dumps(CLASS_TH, ensure_ascii=False, separators=(',',':'))

# gear type → ไอคอนตัวแทน (item id ต่ำสุด = ของฐานธรรมดา รูปเรียบสุด) สำหรับปุ่ม filter เกราะ/เครื่องประดับ
geartype_icon = {}
for it in items_list:
    if it.get('type') != 'GEAR' or not it.get('icon'): continue
    g = it.get('gear')
    if not g: continue
    if g not in geartype_icon or it['id'] < geartype_icon[g][0]:
        geartype_icon[g] = (it['id'], f"{WIKI_BASE}{it['icon']}")
GEARTYPE_ICON_JSON = _json2.dumps({g: v[1] for g, v in geartype_icon.items()},
                                  ensure_ascii=False, separators=(',',':'))

# ── Build rune data ───────────────────────────────────────────────────────────
def _rune_color(stat):
    if any(k in stat for k in ['AttackDamage','Crit','PhysicalDamage','Elemental','DamagePercent','SkillDamage']): return '#f87171'
    if any(k in stat for k in ['MaxHp','Armor','DamageReduction','Block','Dodge','Resistance']): return '#60a5fa'
    if any(k in stat for k in ['Gold','Chest','Inventory','Drop','AutoOpen','Amount']): return '#fcd34d'
    if any(k in stat for k in ['Speed','Cooldown','CastSpeed','AttackSpeed','Range']): return '#4ade80'
    if any(k in stat for k in ['Exp','Experience','IncreaseExp']): return '#c084fc'
    return '#94a3b8'

_rnodes = rune_tree_raw['nodes']
_redges = rune_tree_raw['edges']
_bounds = rune_tree_raw['bounds']
MIN_X, MIN_Y = _bounds['minX'], _bounds['minY']

rune_nodes_json = _json2.dumps([{
    'key':      n['key'],
    'x':        n['x'] - MIN_X,
    'y':        n['y'] - MIN_Y,
    'name':     (n.get('name') or {}).get('en-US', ''),
    'name_bi':  biobj(n.get('name')),
    'icon':     f"{WIKI_BASE}{n['icon']}" if n.get('icon') else '',
    'effect':   (n.get('effect') or {}).get('en-US', ''),
    'effect_bi': biobj(n.get('effect')),
    'maxLevel': n.get('maxLevel', 1),
    'cost':     n['levels'][0]['costValue'] if n.get('levels') else 0,
    'costItem': n['levels'][0]['costItem']  if n.get('levels') else 0,
    'lv1val':   n['levels'][0]['value']     if n.get('levels') else 0,
    'color':    _rune_color(n.get('stat', '')),
} for n in _rnodes], ensure_ascii=False, separators=(',',':'))

rune_edges_json = _json2.dumps(_redges, ensure_ascii=False, separators=(',',':'))
RUNE_W = int(_bounds['maxX'] - MIN_X)
RUNE_H = int(_bounds['maxY'] - MIN_Y)
print(f'Processed {len(_rnodes)} rune nodes, {len(_redges)} edges')
print(f'Processed {len(heroes_skills_data)} heroes with skills')

# ── Generate material cards HTML ──────────────────────────────────────────────
STEAM_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V9c0-2.08 1.67-3.77 3.75-3.77 2.08 0 3.77 1.69 3.77 3.77s-1.69 3.77-3.77 3.77h-.087l-4.08 2.905c0 .052.004.103.004.154 0 1.56-1.258 2.826-2.818 2.826-1.364 0-2.504-.97-2.774-2.252L.189 14.4C1.179 19.836 6.016 24 11.979 24c6.627 0 12-5.373 12-12S18.606 0 11.979 0z"/></svg>'
VOL_ICON   = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'

def card_html(m):
    slots_html = ''
    for slot_group in m['slots']:
        stat_rows = ''.join(
            f'<div class="slot-row"><span class="stat-name">{bi(stat["stat_bi"])}</span>'
            f'<span class="stat-right"><span class="stat-val">{stat["value"]}</span>'
            f'<span class="tier">{stat["tier"]}</span></span></div>'
            for stat in slot_group['stats']
        )
        slots_html += (
            f'<div class="slot-sec" data-slot="{slot_group["slot"]}">'
            f'<span class="slot-lbl">{gb(slot_group["slot"], SLOT_GROUP_TH.get(slot_group["slot"], slot_group["slot"]))}</span>'
            f'{stat_rows}</div>'
        )
    price_html = ''
    if m['price']:
        vol = f'<span class="price-vol">{VOL_ICON} {m["volume"]} sold</span>' if m['volume'] else ''
        price_html = f'<div class="price-row"><span class="price-val">{m["price"]}</span>{vol}</div>'
    steam = (f'<a class="steam-btn" href="{m["steam_url"]}" target="_blank" rel="noopener" title="Steam Market">'
             f'{STEAM_ICON}</a>') if m['marketable'] else ''
    return (
        f'<article class="card" data-type="{m["mat_type"]}" data-grade="{m["grade"]}"'
        f' data-slots="{m["slot_names"]}" data-stats="{json.dumps(m["stats_by_slot"], ensure_ascii=False).replace(chr(34), "&quot;")}" data-name="{m["name"].lower()}|{m["name_bi"]["t"].lower()}" style="border-left:3px solid {m["color"]}">'
        f'<div class="card-hd">'
        f'<div class="icon-wrap"><img class="item-icon" src="{m["icon_url"]}" alt="{m["name"]}"'
        f' loading="lazy" onerror="this.style.visibility=\'hidden\'"></div>'
        f'<div class="card-meta"><span class="item-name" style="color:{m["color"]}">{bi(m["name_bi"])}</span>'
        f'<div class="card-tags">'
        f'<span class="tag-grade" style="color:{m["color"]};border-color:{m["color"]}55;background:{m["color"]}30">'
        f'{gb(m["grade"].capitalize(), GRADE_TH.get(m["grade"], m["grade"].capitalize()))}</span>'
        f'<span class="tag-type">{m["mat_type"]}</span></div>'
        f'{price_html}</div>{steam}</div>'
        f'<div class="card-stats">{slots_html}</div></article>'
    )

CARDS_HTML = '\n'.join(card_html(m) for m in materials)

# ── HTML (regular strings to avoid f-string conflict with JS template literals) ──

HEAD = """\
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TBH Tools</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');

:root {
  --bg:       #020617;
  --surf:     #0f172a;
  --surf2:    #1e293b;
  --border:   #1e2d45;
  --border2:  #2a3d56;
  --gold:     #e8c84a;
  --gold-dim: #b89a2e;
  --text:     #e2e8f0;
  --muted:    #64748b;
  --muted2:   #475569;
  --green:    #4ade80;
  --amber:    #fcd34d;
  --blue:     #60a5fa;
  --purple:   #a78bfa;
  --red:      #f87171;
  --r:        10px;
  --r-sm:     7px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg); color: var(--text);
  font-family: 'Noto Sans Thai', system-ui, sans-serif;
  font-size: 14px; line-height: 1.6; min-height: 100vh;
}
.num { font-family: 'Fira Code', 'Courier New', monospace !important; }

/* ── i18n dual-span toggle ── */
.th { display: none; }
body.lang-th .en { display: none; }
body.lang-th .th { display: inline; }
.lang-toggle {
  position: relative; display: inline-flex; align-items: center;
  border: 1px solid var(--border2); background: var(--surf2);
  border-radius: 100px; padding: 3px; cursor: pointer; user-select: none;
}
.lang-toggle .lang-opt {
  position: relative; z-index: 1; width: 42px; text-align: center;
  font-size: 12px; font-weight: 700; padding: 3px 0;
  color: var(--muted); transition: color .2s;
}
.lang-toggle .lang-knob {
  position: absolute; top: 3px; left: 3px; width: 42px; height: calc(100% - 6px);
  background: var(--gold); border-radius: 100px; transition: transform .2s;
}
/* EN active (default lang) → knob left; TH active → knob right */
body.lang-th .lang-toggle .lang-knob { transform: translateX(42px); }
.lang-toggle .opt-en { color: #0a0a0a; }              /* EN selected by default */
body.lang-th .lang-toggle .opt-en { color: var(--muted); }
body.lang-th .lang-toggle .opt-th { color: #0a0a0a; }

/* ── Top Tab Bar ── */
.topbar {
  position: sticky; top: 0; z-index: 200;
  display: flex; align-items: center; gap: 0;
  height: 52px; padding: 0 20px;
  background: rgba(2,6,23,.95); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
.topbar-logo {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 800; color: var(--gold);
  text-decoration: none; letter-spacing: -.02em;
  margin-right: 24px; white-space: nowrap; cursor: default;
}
.tab-nav { display: flex; gap: 2px; flex: 1; }
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 16px; border-radius: 8px; border: none;
  background: transparent; color: var(--muted);
  font-size: 13px; font-weight: 600; font-family: inherit;
  cursor: pointer; transition: all .15s; white-space: nowrap;
}
.tab-btn:hover { color: var(--text); background: var(--surf2); }
.tab-btn.active { color: var(--gold); background: rgba(232,200,74,.1); }
.topbar-actions { display: none; align-items: center; gap: 8px; margin-left: auto; }
.topbar-actions.visible { display: flex; }

/* ── Buttons ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: var(--r-sm); border: none;
  font-size: 12px; font-weight: 600; font-family: inherit;
  cursor: pointer; transition: all .15s; white-space: nowrap;
}
.btn-ghost   { background: var(--surf2); color: var(--muted2); border: 1px solid var(--border); }
.btn-ghost:hover { color: var(--text); border-color: var(--border2); }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-primary:hover { background: #4338ca; }
.btn-green   { background: rgba(74,222,128,.1); color: var(--green); border: 1px solid rgba(74,222,128,.25); }
.btn-green:hover { background: rgba(74,222,128,.2); }

/* ── Tab panes ── */
.tab-pane { display: none; }
.tab-pane.active { display: block; }

/* ════════════════════════════
   TAB 1 — MATERIAL EFFECTS
════════════════════════════ */
.mat-wrap { max-width: 1600px; margin: 0 auto; padding: 24px 20px 60px; }
.page-title { font-size: clamp(1.5rem,3vw,2rem); font-weight: 700; color: var(--gold); letter-spacing: -.02em; }
.page-sub { color: var(--muted); font-size: 13px; margin-top: 4px; margin-bottom: 20px; }
.controls {
  background: var(--surf); border: 1px solid var(--border);
  border-radius: var(--r); padding: 14px 18px; margin-bottom: 18px;
  display: flex; flex-direction: column; gap: 12px;
}
.search-row { position: relative; }
.search-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--muted); pointer-events: none; display: flex; }
.search-input {
  width: 100%; background: var(--surf2); border: 1px solid var(--border);
  color: var(--text); padding: 8px 13px 8px 36px;
  border-radius: var(--r-sm); font-size: 14px; font-family: inherit; outline: none;
  transition: border-color .15s;
}
.search-input::placeholder { color: var(--muted); }
.search-input:focus { border-color: var(--gold); }
.filter-rows { display: flex; flex-wrap: wrap; gap: 10px 20px; align-items: flex-start; }
.filter-group { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.filter-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: #94a3b8; white-space: nowrap; min-width: 40px; }
.pill {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--surf2); border: 1px solid var(--border); color: #94a3b8;
  padding: 4px 13px; border-radius: 100px; cursor: pointer;
  font-size: 12px; font-weight: 600; font-family: inherit; transition: all .15s;
}
.pill:hover { border-color: var(--gold-dim); color: var(--gold); }
.pill.active { background: var(--gold); border-color: var(--gold); color: #0a0a0a; font-weight: 700; }
.grade-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; vertical-align:middle; flex-shrink:0; }

/* ── custom Effect dropdown ── */
.eff-dd { position:relative; }
.eff-trigger {
  display:flex; align-items:center; gap:8px; min-width:180px;
  background:var(--surf2); border:1px solid var(--border2); color:var(--text);
  padding:6px 11px; border-radius:var(--r-sm); font-size:12px; font-weight:600;
  font-family:inherit; cursor:pointer; transition:border-color .15s;
}
.eff-trigger:hover { border-color:var(--gold-dim); }
.eff-dd.open .eff-trigger { border-color:var(--gold); }
.eff-cur { flex:1; text-align:left; white-space:nowrap; }
.eff-trigger svg { color:var(--muted); transition:transform .15s; flex-shrink:0; }
.eff-dd.open .eff-trigger svg { transform:rotate(180deg); color:var(--gold); }
.eff-panel {
  position:absolute; top:calc(100% + 4px); left:0; z-index:300;
  width:260px; max-width:80vw; background:var(--surf); border:1px solid var(--border2);
  border-radius:var(--r); box-shadow:0 12px 32px rgba(0,0,0,.6);
  display:none; overflow:hidden;
}
.eff-dd.open .eff-panel { display:block; }
.eff-search-wrap { padding:8px; border-bottom:1px solid var(--border); }
.eff-search {
  width:100%; background:var(--surf2); border:1px solid var(--border); color:var(--text);
  padding:7px 10px; border-radius:var(--r-sm); font-size:13px; font-family:inherit; outline:none;
}
.eff-search:focus { border-color:var(--gold); }
.eff-list { max-height:280px; overflow-y:auto; padding:4px; }
.eff-opt {
  padding:7px 10px; border-radius:var(--r-sm); font-size:12.5px; color:#cbd5e1;
  cursor:pointer; transition:background .1s; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.eff-opt:hover { background:var(--surf2); color:var(--text); }
.eff-opt.active { background:rgba(232,200,74,.15); color:var(--gold); font-weight:700; }
.eff-opt.hide { display:none; }
.eff-empty { padding:14px; text-align:center; font-size:12px; color:var(--muted); display:none; }
.result-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; font-size: 13px; color: var(--muted); }
.result-count { color: var(--gold); font-weight: 700; font-size: 15px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px,1fr)); gap: 13px; }
/* material card */
.card {
  background: var(--surf); border: 1px solid var(--border);
  border-radius: var(--r); overflow: hidden; cursor: default;
  transition: border-color .2s, box-shadow .2s, transform .2s;
}
.card:hover { border-color: var(--border2); box-shadow: 0 8px 28px rgba(0,0,0,.5); transform: translateY(-2px); }
.card-hd { display: flex; align-items: flex-start; gap: 11px; padding: 13px 13px 11px; border-bottom: 1px solid var(--border); }
.icon-wrap { flex-shrink: 0; width: 50px; height: 50px; background: #0a101e; border: 1px solid var(--border2); border-radius: 7px; display: flex; align-items: center; justify-content: center; }
.item-icon { width: 46px; height: 46px; object-fit: contain; image-rendering: pixelated; }
.card-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.item-name { font-size: .95rem; font-weight: 700; color: #f1f5f9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-tags { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.tag-grade { font-size: 11px; font-weight: 700; padding: 1px 7px; border-radius: 4px; border: 1px solid; }
.tag-type  { font-size: 11px; color: var(--muted); background: var(--surf2); padding: 1px 7px; border-radius: 4px; border: 1px solid var(--border); }
.price-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 1px; }
.price-val { display: flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 700; color: #4ade80; }
.price-vol { display: flex; align-items: center; gap: 3px; font-size: 11px; color: var(--muted); }
.steam-btn {
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  background: #1b2838; border: 1px solid #2a4158; color: #66c0f4;
  width: 30px; height: 30px; border-radius: var(--r-sm); text-decoration: none;
  cursor: pointer; transition: all .15s; align-self: flex-start;
}
.steam-btn:hover { background: #2a475e; border-color: #66c0f4; color: #fff; }
.card-stats { padding: 9px 13px 12px; display: flex; flex-direction: column; gap: 8px; }
.slot-sec   { display: flex; flex-direction: column; gap: 3px; }
.slot-lbl   { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); }
.slot-row   { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.stat-name  { color: #cbd5e1; font-size: 13px; }
.stat-right { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.stat-val   { color: var(--gold); font-weight: 700; font-size: 13px; }
.tier       { background: var(--surf2); border: 1px solid var(--border); color: var(--muted); padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }
.empty-state { grid-column: 1/-1; text-align: center; padding: 80px 20px; color: var(--muted); }

/* ════════════════════════════
   TAB 2 — STAGE CALCULATOR
════════════════════════════ */
.calc-wrap { max-width: 980px; margin: 0 auto; padding: 24px 20px 60px; }
.ctrl {
  display: block; width: 100%; height: 34px; padding: 0 10px;
  border: 1px solid var(--border2); border-radius: var(--r-sm);
  background: var(--surf2); color: var(--text); font-size: 13px;
  font-family: inherit; outline: none; transition: border-color .15s, box-shadow .15s;
}
.ctrl:focus { border-color: var(--gold); box-shadow: 0 0 0 2px rgba(232,200,74,.15); }
select.ctrl {
  appearance: none; -webkit-appearance: none; cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center; padding-right: 30px;
}
input[type="number"].ctrl { -moz-appearance: textfield; }
input[type="number"].ctrl::-webkit-outer-spin-button,
input[type="number"].ctrl::-webkit-inner-spin-button { -webkit-appearance: none; }
.default-strip {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: var(--surf); border: 1px solid var(--border);
  border-radius: var(--r); padding: 10px 16px; margin-bottom: 20px;
  font-size: 12px; color: var(--muted);
}
.card-stage {
  background: var(--surf); border: 1px solid var(--border);
  border-radius: var(--r); padding: 18px; box-shadow: 0 2px 12px rgba(0,0,0,.3);
  transition: border-color .2s;
}
.card-stage.drag-over { border-color: var(--gold); }
.card-stage.dragging  { opacity: .5; }
.card-run { background: var(--bg); border: 1px solid var(--border); border-radius: var(--r-sm); padding: 13px; margin-bottom: 8px; }
.grp { border-radius: var(--r-sm); padding: 10px 11px; }
.grp-exp  { background: #071a0f; border: 1px solid #166534; }
.grp-gold { background: #1c1000; border: 1px solid #7c3200; }
.grp-time { background: #07102a; border: 1px solid #1e3a8a; }
.grp-comp { background: #120825; border: 1px solid #5b21b6; }
.grp-title { font-size: 10px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; display: block; margin-bottom: 7px; }
.grp-exp  .grp-title { color: var(--green); }
.grp-gold .grp-title { color: var(--amber); }
.grp-time .grp-title { color: var(--blue); }
.grp-comp .grp-title { color: var(--purple); }
.grp-lbl  { font-size: 11px; font-weight: 600; color: var(--muted); display: block; margin-bottom: 4px; }
.grp-exp  .ctrl { background: #0a2018; border-color: #166534; }
.grp-exp  .ctrl:focus { border-color: #22c55e; box-shadow: 0 0 0 2px rgba(34,197,94,.15); }
.grp-gold .ctrl { background: #1a0e00; border-color: #7c3200; }
.grp-gold .ctrl:focus { border-color: #f59e0b; box-shadow: 0 0 0 2px rgba(245,158,11,.15); }
.grp-time .ctrl { background: #060d24; border-color: #1e3a8a; }
.grp-time .ctrl:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,.15); }
.grp-comp .ctrl { background: #0e0520; border-color: #5b21b6; }
.grp-comp .ctrl:focus { border-color: #8b5cf6; box-shadow: 0 0 0 2px rgba(139,92,246,.15); }
.diff-badge { font-size: 11px; font-weight: 700; padding: 2px 9px; border-radius: 20px; white-space: nowrap; }
.d-normal    { background: rgba(29,78,216,.2);  color: #93c5fd; border: 1px solid rgba(29,78,216,.4); }
.d-nightmare { background: rgba(109,40,217,.2); color: #c4b5fd; border: 1px solid rgba(109,40,217,.4); }
.d-hell      { background: rgba(194,65,12,.2);  color: #fdba74; border: 1px solid rgba(194,65,12,.4); }
.d-torment   { background: rgba(190,18,60,.2);  color: #fda4af; border: 1px solid rgba(190,18,60,.4); }
.pill-e { display: inline-flex; align-items: center; gap: 5px; background: #071a0f; color: var(--green); border: 1px solid #166534; border-radius: var(--r-sm); padding: 4px 11px; font-size: 12px; }
.pill-g { display: inline-flex; align-items: center; gap: 5px; background: #1c1000; color: var(--amber); border: 1px solid #7c3200; border-radius: var(--r-sm); padding: 4px 11px; font-size: 12px; }
.chip { background: var(--surf2); border-radius: var(--r-sm); padding: 4px 11px; font-size: 13px; border: 1px solid var(--border); }
.comp-badge { font-size: 11px; font-weight: 600; background: #120825; color: var(--purple); border-radius: 5px; padding: 2px 8px; border: 1px solid #5b21b6; white-space: nowrap; }
.ts-label { font-family: 'Fira Code', monospace; font-size: 11px; color: var(--muted); }
.drag-handle { cursor: grab; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 5px; color: var(--muted); transition: all .15s; }
.drag-handle:hover { background: var(--surf2); color: var(--text); }
.del { cursor: pointer; width: 28px; height: 28px; border-radius: 50%; background: rgba(239,68,68,.12); color: var(--red); border: none; display: flex; align-items: center; justify-content: center; transition: all .15s; flex-shrink: 0; }
.del:hover { background: #ef4444; color: #fff; }
.del svg { width: 13px; height: 13px; pointer-events: none; }
.del.del-lg { width: 32px; height: 32px; }
.del.del-lg svg { width: 14px; height: 14px; }
.cmp-section { margin-top: 36px; }
.cmp-table { width: 100%; border-collapse: collapse; }
.cmp-th { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; padding: 10px 13px; white-space: nowrap; text-align: left; border-bottom: 1px solid var(--border); }
.cmp-td { padding: 11px 13px; border-top: 1px solid var(--border); font-size: 13px; }
.row-worth { background: rgba(99,102,241,.08); }
.row-exp   { background: rgba(74,222,128,.06); }
.row-gold  { background: rgba(252,211,77,.06); }
.row-nodata { opacity: .4; }
.sort-btn { cursor: pointer; border-radius: 20px; padding: 4px 13px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--surf2); color: var(--muted); font-family: inherit; transition: all .15s; }
.sort-btn.active { background: var(--gold); color: #0a0a0a; border-color: var(--gold); }
.worth-bg { background: var(--surf2); border-radius: 3px; height: 5px; width: 56px; overflow: hidden; display: inline-block; vertical-align: middle; margin-left: 6px; }
.worth-fill { background: #818cf8; height: 100%; border-radius: 3px; }
.stage-empty { text-align: center; padding: 60px 20px; color: var(--muted); display: none; }

/* ════════════════════════════
   TAB 3 — PET
════════════════════════════ */
.pet-wrap { max-width: 1200px; margin: 0 auto; padding: 24px 20px 60px; }
.pet-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px,1fr)); gap: 13px; }
.pet-card { background: var(--surf); border: 1px solid var(--border); border-radius: var(--r); padding: 16px; transition: border-color .2s, box-shadow .2s, transform .2s; }
.pet-card:hover { border-color: var(--border2); box-shadow: 0 6px 24px rgba(0,0,0,.4); transform: translateY(-1px); }
.pet-name { font-size: 1rem; font-weight: 700; color: #f1f5f9; }
.farm-box { margin-top: 12px; padding-top: 11px; border-top: 1px solid var(--border); }
.farm-box-header { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 8px; }
.farm-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; }
.farm-row + .farm-row { border-top: 1px solid var(--border); }
.pet-unlock { display:flex; align-items:center; gap:6px; margin-top:6px; font-size:11px; color:#94a3b8; flex-wrap:wrap; }
.unlock-lbl { font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; background:var(--surf2); border:1px solid var(--border); border-radius:4px; padding:1px 6px; color:var(--muted); white-space:nowrap; flex-shrink:0; }
.unlock-count { color:var(--gold); font-weight:700; }
.badge { font-size:10px; font-weight:700; padding:2px 8px; border-radius:20px; white-space:nowrap; }
.badge-priority { background:#312e81; color:#a5b4fc; border:1px solid #4338ca; }
.badge-free     { background:#052e16; color:#4ade80; border:1px solid #166534; }
.badge-supporter{ background:#2d1900; color:#fcd34d; border:1px solid #92400e; }
.pet-grid { grid-template-columns: repeat(auto-fill, minmax(340px,1fr)) !important; }

/* ════════════════════════════
   TAB 4 — EQUIPMENT
════════════════════════════ */
.gear-wrap { max-width: 1600px; margin: 0 auto; padding: 24px 20px 60px; }
.gear-card-base { display: flex; flex-direction: column; gap: 3px; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.gear-card-base:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
.gear-section-lbl { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 3px; }
.gear-stat-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.gear-stat-name { font-size: 12px; color: #cbd5e1; }
.gear-stat-val  { font-size: 12px; font-weight: 700; color: var(--gold); flex-shrink: 0; }
.gear-stat-val.green { color: var(--green); }
.type-slot-lbl { color: #64748b !important; font-size: 10px !important; min-width: 70px !important; }
.pill.type-pill { flex-direction: column; gap: 0; padding: 5px 13px; }
.pill.type-pill.with-portrait { flex-direction: row; align-items: center; gap: 7px; padding: 4px 12px 4px 5px; }
.type-portrait { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; flex-shrink: 0; background: #0a101e; }
.type-portrait.type-portrait-sq { border-radius: 6px; object-fit: contain; image-rendering: pixelated; padding: 2px; }
.type-txt { display: flex; flex-direction: column; align-items: flex-start; line-height: 1.15; }
.type-class { font-size: 9px; font-weight: 500; color: #60a5fa; line-height: 1.2; }
.pill.active .type-class { color: rgba(0,0,0,.55); }
.unique-badge {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(129,140,248,.12); color: #a5b4fc;
  border: 1px solid rgba(129,140,248,.3);
  border-radius: 6px; padding: 3px 9px; font-size: 11px; font-weight: 600;
  margin-top: 4px;
}

/* ════════════════════════════
   TAB 5 — SKILLS
════════════════════════════ */
.skills-wrap { max-width: 1400px; margin: 0 auto; padding: 24px 20px 60px; }
.hero-nav { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
.hero-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 18px; border-radius: var(--r); border: 2px solid var(--border);
  background: var(--surf); color: var(--muted); font-size: 13px; font-weight: 700;
  font-family: inherit; cursor: pointer; transition: all .15s;
}
.hero-btn:hover { color: var(--text); border-color: var(--border2); }
.hero-btn.active { color: var(--bg); border-color: transparent; }
.hero-portrait { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; }
.skills-section-lbl {
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em;
  color: #94a3b8; margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.skill-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px,1fr)); gap: 12px; margin-bottom: 28px; }
.skill-card {
  background: var(--surf); border: 1px solid var(--border);
  border-radius: var(--r); padding: 14px; transition: border-color .2s;
}
.skill-card:hover { border-color: var(--border2); }
.skill-hd { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.skill-icon { width: 46px; height: 46px; border-radius: 8px; background: #0a101e; border: 1px solid var(--border2); flex-shrink: 0; object-fit: contain; image-rendering: pixelated; }
.skill-name { font-size: .9rem; font-weight: 700; color: #f1f5f9; margin-bottom: 4px; }
.skill-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.skill-tag { font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 4px; border: 1px solid; }
.skill-desc { font-size: 12px; color: #94a3b8; line-height: 1.6; margin-bottom: 8px; }
.skill-dmg { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; background: var(--bg); border-radius: var(--r-sm); border: 1px solid var(--border); font-size: 12px; }
.skill-dmg-val { font-weight: 700; font-family: 'Fira Code', monospace; }
.passive-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px,1fr)); gap: 8px; }
.passive-card {
  display: flex; align-items: center; gap: 10px;
  background: var(--surf); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 10px 12px;
}
.passive-icon { width: 32px; height: 32px; border-radius: 6px; background: #0a101e; border: 1px solid var(--border2); flex-shrink: 0; object-fit: contain; }
.passive-name { font-size: 12px; font-weight: 600; color: #e2e8f0; }
.passive-val  { font-size: 11px; color: var(--gold); font-weight: 700; margin-top: 2px; }
.skill-card { cursor: pointer; }
.skill-detail-ov { position:fixed; inset:0; background:rgba(0,0,0,.7); backdrop-filter:blur(8px); display:flex; align-items:center; justify-content:center; z-index:9999; opacity:0; pointer-events:none; transition:opacity .18s; }
.skill-detail-ov.show { opacity:1; pointer-events:all; }
.skill-detail-box { background:var(--surf); border:1px solid var(--border2); border-radius:14px; padding:24px; max-width:480px; width:calc(100% - 32px); max-height:85vh; overflow-y:auto; box-shadow:0 24px 64px rgba(0,0,0,.7); transform:scale(.95); transition:transform .2s; }
.skill-detail-ov.show .skill-detail-box { transform:scale(1); }
.sd-hd { display:flex; align-items:flex-start; gap:12px; margin-bottom:16px; }
.sd-icon { width:56px; height:56px; border-radius:10px; background:#0a101e; border:1px solid var(--border2); object-fit:contain; flex-shrink:0; }
.sd-title { font-size:1.1rem; font-weight:800; color:#f1f5f9; margin-bottom:6px; }
.sd-desc { font-size:13px; color:#94a3b8; line-height:1.7; margin-bottom:16px; padding-bottom:16px; border-bottom:1px solid var(--border); }
.sd-section-lbl { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); margin-bottom:10px; }
.sd-levels { display:grid; grid-template-columns:repeat(5,1fr); gap:6px; margin-bottom:16px; }
.sd-lv { background:var(--surf2); border:1px solid var(--border); border-radius:6px; padding:6px 4px; text-align:center; }
.sd-lv-n { font-size:9px; color:var(--muted); font-weight:700; }
.sd-lv-v { font-size:12px; font-weight:700; margin-top:2px; }
.sd-lv.max { border-color:var(--gold); background:rgba(232,200,74,.08); }
.sd-lv.max .sd-lv-v { color:var(--gold); }
.sd-lv.locked { opacity:.35; }
.sd-stats { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.sd-stat { background:var(--surf2); border:1px solid var(--border); border-radius:8px; padding:8px 12px; }
.sd-stat-lbl { font-size:10px; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.06em; }
.sd-stat-val { font-size:13px; font-weight:700; color:var(--text); margin-top:2px; }

/* ════════════════════════════
   TAB — CRAFTING
════════════════════════════ */
.craft-wrap { max-width:1600px; margin:0 auto; padding:24px 20px 60px; }
.craft-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(360px,1fr)); gap:13px; }
.craft-card { background:var(--surf); border:1px solid var(--border); border-radius:var(--r); overflow:hidden; }
.craft-poss-btn { width:100%; display:flex; align-items:center; justify-content:center; gap:6px; padding:9px; border:none; border-top:1px solid var(--border); background:var(--surf2); color:#a5b4fc; font-size:12px; font-weight:700; font-family:inherit; cursor:pointer; transition:background .15s; }
.craft-poss-btn:hover { background:var(--border2); color:#c7d2fe; }
.cposs-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:7px; align-items:start; }
.cposs-item { background:var(--surf2); border:1px solid var(--border); border-radius:var(--r-sm); padding:6px 8px; }
.cposs-item.has-stat { cursor:pointer; }
.cposs-row { display:flex; align-items:center; gap:8px; }
.cposs-icon { width:30px; height:30px; flex-shrink:0; object-fit:contain; image-rendering:pixelated; background:#0a101e; border-radius:5px; }
.cposs-name { flex:1; min-width:0; font-size:12px; color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cposs-caret { color:var(--muted); font-size:10px; transition:transform .15s; }
.cposs-item.open .cposs-caret { transform:rotate(180deg); }
.cposs-stats { display:none; margin-top:6px; padding-top:6px; border-top:1px solid var(--border); flex-direction:column; gap:3px; }
.cposs-item.open .cposs-stats { display:flex; }
.cposs-stat { display:flex; justify-content:space-between; gap:8px; font-size:11px; color:var(--muted2); }
.cposs-stat-v { font-weight:700; color:var(--gold); }
.cposs-stat-v.green { color:var(--green); }
.cposs-price { font-size:11px; font-weight:700; color:#4ade80; font-family:'Fira Code',monospace; flex-shrink:0; }
.cposs-prlbl { font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-top:4px; }
.cposs-pr { display:flex; align-items:center; font-size:11px; text-decoration:none; padding:2px 0; }
.cposs-pr:hover .cposs-pr-v { color:#fff; }
.cposs-pr-v { font-weight:700; color:#4ade80; font-family:'Fira Code',monospace; }
.craft-hd { display:flex; align-items:center; justify-content:space-between; gap:8px; padding:12px 14px; border-bottom:1px solid var(--border); }
.craft-title { font-size:.95rem; font-weight:700; color:#f1f5f9; }
.craft-sub { font-size:11px; color:var(--muted); margin-top:2px; }
.craft-tier { font-size:11px; font-weight:700; color:var(--gold); background:rgba(232,200,74,.12); border:1px solid rgba(232,200,74,.3); border-radius:6px; padding:2px 9px; white-space:nowrap; }
.craft-mats { padding:8px 14px; display:flex; flex-direction:column; gap:6px; }
.craft-mat { display:flex; align-items:center; gap:9px; }
.craft-mat-icon { width:30px; height:30px; flex-shrink:0; border-radius:6px; background:#0a101e; border:1px solid var(--border2); object-fit:contain; image-rendering:pixelated; }
.craft-mat-name { flex:1; min-width:0; font-size:12px; color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.craft-mat-x { font-size:11px; color:var(--muted); font-weight:700; }
.craft-mat-price { font-size:12px; font-weight:700; color:#4ade80; white-space:nowrap; font-family:'Fira Code',monospace; min-width:62px; text-align:right; }
.craft-mat-buy { flex-shrink:0; display:flex; align-items:center; color:#66c0f4; text-decoration:none; opacity:.7; transition:opacity .15s; }
.craft-mat-buy:hover { opacity:1; }
.craft-total { display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-top:1px solid var(--border); background:var(--bg); }
.craft-total-lbl { font-size:12px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }
.craft-total-val { font-size:15px; font-weight:800; color:#4ade80; font-family:'Fira Code',monospace; }
.craft-odds { padding:10px 14px; border-top:1px solid var(--border); }
.craft-odds-lbl { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:7px; }
.craft-odds-bar { display:flex; height:8px; border-radius:4px; overflow:hidden; margin-bottom:6px; }
.craft-odds-list { display:flex; flex-wrap:wrap; gap:4px 10px; }
.craft-odd { display:flex; align-items:center; gap:4px; font-size:11px; }
.craft-odd-dot { width:8px; height:8px; border-radius:50%; }
.craft-odd-pct { font-weight:700; font-family:'Fira Code',monospace; }

/* ════════════════════════════
   TAB — STAGES
════════════════════════════ */
.stages-wrap { max-width:1400px; margin:0 auto; padding:24px 20px 60px; }
.stages-layout { display:flex; gap:28px; align-items:flex-start; flex-wrap:wrap; }
.stages-left { flex-shrink:0; }
.stages-right { flex:1; min-width:280px; }

/* Act / Diff selectors */
.stage-act-nav { display:flex; gap:6px; margin-bottom:14px; }
.stage-act-btn {
  padding:7px 20px; border-radius:var(--r-sm); border:2px solid var(--border);
  background:var(--surf); color:var(--muted); font-size:13px; font-weight:700;
  font-family:inherit; cursor:pointer; transition:all .15s;
}
.stage-act-btn:hover { border-color:var(--border2); color:var(--text); }
.stage-act-btn.active { border-color:var(--gold); color:var(--gold); background:rgba(232,200,74,.1); }
.stage-diff-nav { display:flex; gap:5px; margin-bottom:16px; flex-wrap:wrap; }
.stage-diff-btn {
  padding:4px 14px; border-radius:100px; border:1px solid var(--border);
  background:var(--surf2); color:var(--muted); font-size:12px; font-weight:600;
  font-family:inherit; cursor:pointer; transition:all .15s;
}
.stage-diff-btn.active { color:#0a0a0a; font-weight:700; }

/* Stage table */
.stage-acts-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:16px; }
.stage-act-col { background:var(--surf); border:1px solid var(--border); border-radius:var(--r); overflow:hidden; }
.stage-act-hd { padding:10px 14px; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; background:var(--surf2); border-bottom:1px solid var(--border); color:#94a3b8; }
.stage-row {
  display:grid; grid-template-columns:38px 1fr auto;
  align-items:center; gap:8px;
  padding:7px 12px; border-bottom:1px solid var(--border);
  cursor:pointer; transition:background .12s;
}
.stage-row:last-child { border-bottom:none; }
.stage-row:hover { background:var(--surf2); }
.stage-row.boss-row { background:rgba(248,113,113,.04); }
.stage-row.boss-row:hover { background:rgba(248,113,113,.1); }
.sr-id { font-size:11px; font-weight:800; color:#64748b; }
.sr-name { font-size:12px; color:#e2e8f0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sr-name.boss { color:#fda4af; }
.sr-levels { display:flex; gap:4px; flex-shrink:0; }
.sr-lv-badge { font-size:10px; font-weight:700; padding:1px 5px; border-radius:4px; white-space:nowrap; }

/* Monsters in detail */
.monster-grid { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.monster-card { display:flex; flex-direction:column; align-items:center; gap:4px; width:60px; }
.monster-portrait { width:52px; height:52px; object-fit:contain; border-radius:6px; background:#0a101e; border:1px solid var(--border2); image-rendering:pixelated; }
.monster-name { font-size:9px; color:var(--muted); text-align:center; line-height:1.2; }

/* Loot boxes */
.loot-box { padding:14px 18px; border-top:1px solid var(--border); }
.loot-hd { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.loot-icon { width:38px; height:38px; object-fit:contain; border-radius:7px; background:#0a101e; border:1px solid var(--border2); image-rendering:pixelated; }
.loot-box-name { font-size:13px; font-weight:700; color:#f1f5f9; }
.loot-grade { font-size:10px; font-weight:700; padding:1px 7px; border-radius:4px; border:1px solid; }
.loot-list { display:flex; flex-direction:column; gap:6px; }
.loot-row { display:flex; align-items:center; gap:8px; font-size:12px; }
.loot-item-icon { width:26px; height:26px; flex-shrink:0; border-radius:5px; background:#0a101e; border:1px solid var(--border2); object-fit:contain; image-rendering:pixelated; }
.loot-item-ph { width:26px; height:26px; flex-shrink:0; border-radius:5px; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:800; border:1px solid; }
.loot-row-name { color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; }
.loot-pct { font-weight:700; font-family:'Fira Code',monospace; flex-shrink:0; }
.loot-bar { flex:1; height:4px; background:var(--surf2); border-radius:3px; overflow:hidden; margin:0 8px; min-width:30px; }
.loot-bar-fill { height:100%; border-radius:3px; }
.loot-more { font-size:11px; color:var(--gold); cursor:pointer; margin-top:6px; font-weight:600; }
.loot-more:hover { text-decoration:underline; }

/* Stage detail panel */
.stage-detail-empty { color:var(--muted); font-size:13px; padding:20px 0; }
.stage-detail-card {
  background:var(--surf); border:1px solid var(--border2);
  border-radius:var(--r); overflow:hidden;
}
.stage-detail-hd { padding:16px 18px 14px; border-bottom:1px solid var(--border); }
.stage-detail-tag { display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap; }
.stage-detail-name { font-size:1.2rem; font-weight:800; color:#f1f5f9; margin-bottom:4px; }
.stage-detail-sub { font-size:12px; color:var(--muted); }
.stage-stats-grid { display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--border); }
.stage-stat { background:var(--surf); padding:12px 16px; }
.stage-stat-lbl { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:4px; }
.stage-stat-val { font-size:18px; font-weight:800; }
.boss-section { padding:14px 18px; border-top:1px solid var(--border); display:flex; align-items:center; gap:14px; }
.boss-portrait { width:64px; height:64px; object-fit:contain; border-radius:8px; background:#0a101e; border:1px solid var(--border2); image-rendering:pixelated; }
.boss-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }
.boss-name { font-size:15px; font-weight:700; color:#f1f5f9; margin-top:4px; }

/* ════════════════════════════
   TAB 6 — RUNES
════════════════════════════ */
.runes-wrap { max-width:1600px; margin:0 auto; padding:24px 20px 60px; }
.rune-viewport {
  width:100%; height:calc(100vh - 220px); min-height:500px; overflow:hidden; position:relative;
  background:#060d1a; border:1px solid var(--border); border-radius:var(--r);
  cursor:grab; user-select:none;
}
.rune-viewport.dragging { cursor:grabbing; }
.rune-world { position:absolute; transform-origin:0 0; }
.rune-edges { position:absolute; top:0; left:0; pointer-events:none; overflow:visible; }
.rune-edges line { stroke:#2d5a8e; stroke-width:3; stroke-linecap:round; }
.rune-node {
  position:absolute; width:36px; height:36px;
  transform:translate(-18px,-18px);
  border-radius:6px; border:2px solid;
  background:#0a1628; overflow:hidden;
  transition:filter .15s, transform .1s;
  cursor:pointer;
}
.rune-node:hover { filter:brightness(1.4); transform:translate(-18px,-18px) scale(1.25); z-index:10; }
.rune-node.dimmed { opacity:.12; filter:grayscale(1); }
.rune-node.hit { box-shadow:0 0 0 3px var(--gold), 0 0 14px 2px rgba(232,200,74,.6); z-index:5; }
.rune-node img { width:100%; height:100%; object-fit:contain; image-rendering:pixelated; }
.rune-controls {
  position:absolute; bottom:12px; right:12px; display:flex; gap:6px; z-index:20;
}
.rune-ctrl-btn {
  width:32px; height:32px; border-radius:6px; border:1px solid var(--border2);
  background:rgba(15,23,42,.9); color:var(--text); font-size:16px; font-weight:700;
  cursor:pointer; display:flex; align-items:center; justify-content:center;
  transition:background .15s;
}
.rune-ctrl-btn:hover { background:var(--surf2); }
.rune-hint { position:absolute; bottom:12px; left:12px; font-size:11px; color:var(--muted); pointer-events:none; }
.rune-tooltip {
  position:fixed; z-index:9999; pointer-events:none;
  background:var(--surf); border:1px solid var(--border2);
  border-radius:8px; padding:10px 13px; max-width:240px;
  box-shadow:0 8px 24px rgba(0,0,0,.6); opacity:0; transition:opacity .1s;
}
.rune-tooltip.show { opacity:1; }
.rtt-name { font-size:13px; font-weight:700; color:#f1f5f9; margin-bottom:4px; }
.rtt-effect { font-size:12px; color:#94a3b8; line-height:1.5; margin-bottom:6px; }
.rtt-cost { font-size:11px; color:var(--gold); }

/* ── Modal ── */
.modal-ov { position: fixed; inset: 0; background: rgba(0,0,0,.65); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; z-index: 9999; opacity: 0; pointer-events: none; transition: opacity .18s; }
.modal-ov.show { opacity: 1; pointer-events: all; }
.modal-box { background: var(--surf); border: 1px solid var(--border2); border-radius: 14px; padding: 26px 26px 20px; max-width: 340px; width: calc(100% - 32px); box-shadow: 0 20px 60px rgba(0,0,0,.6); transform: scale(.95); transition: transform .2s; }
.modal-ov.show .modal-box { transform: scale(1); }
.mi  { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }
.mi svg { width: 20px; height: 20px; }
.mt  { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 5px; }
.mm  { font-size: 13px; color: var(--muted); line-height: 1.7; margin-bottom: 18px; }
.ma  { display: flex; gap: 8px; justify-content: flex-end; }
.mb  { cursor: pointer; border-radius: var(--r-sm); padding: 7px 16px; font-size: 13px; font-weight: 600; border: none; font-family: inherit; transition: all .15s; }
.mb-cancel { background: var(--surf2); color: var(--muted2); }
.mb-cancel:hover { background: var(--border2); }
.mb-danger { background: #ef4444; color: #fff; }
.mb-danger:hover { background: #dc2626; }
.mb-ok { background: #6366f1; color: #fff; }
.mb-ok:hover { background: #4f46e5; }

@media (max-width: 600px) {
  .topbar { padding: 0 12px; }
  .topbar-logo span { display: none; }
  .tab-btn { padding: 5px 10px; font-size: 12px; }
  .tab-btn svg { display: none; }
  .grid, .pet-grid { grid-template-columns: 1fr; }
  .run-groups { grid-template-columns: 1fr 1fr !important; }
  .mat-wrap, .calc-wrap, .pet-wrap { padding: 16px 12px 40px; }
}
@media (prefers-reduced-motion: reduce) {
  .card, .pet-card, .tab-btn, .pill, .btn { transition: none; }
  .card:hover, .pet-card:hover { transform: none; }
}
</style>
</head>
<body class="lang-th">"""

TOPBAR = """
<nav class="topbar">
  <div class="topbar-logo">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
    <span>TBH Tools</span>
  </div>
  <div class="tab-nav">
    <button class="tab-btn active" data-tab="materials" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M2 12h3m14 0h3M12 2v3m0 14v3"/></svg>
      Material Effects
    </button>
    <button class="tab-btn" data-tab="gear" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
      Equipment
    </button>
    <button class="tab-btn" data-tab="craft" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
      <span class="en">Crafting</span><span class="th">คราฟต์</span>
    </button>
    <button class="tab-btn" data-tab="pets" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 7h-3a2 2 0 0 1-2-2V2"/><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/></svg>
      Pet
    </button>
    <button class="tab-btn" data-tab="stages" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M3 3h18v18H3z"/><path d="M3 9h18M3 15h18M9 3v18"/></svg>
      Stages
    </button>
    <button class="tab-btn" data-tab="runes" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      Runes
    </button>
    <button class="tab-btn" data-tab="skills" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
      Skills
    </button>
    <button class="tab-btn" data-tab="calc" onclick="switchTab(this)">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 17v-6m3 6V7m3 10v-4M3 21h18"/></svg>
      Stage Calculator
    </button>
  </div>
  <div class="topbar-actions" id="calc-actions">
    <button class="btn btn-ghost" onclick="importData()">Import</button>
    <button class="btn btn-ghost" onclick="exportData()">Export</button>
    <button class="btn btn-primary" onclick="addStage()">+ เพิ่มด่าน</button>
  </div>
  <div class="lang-toggle" id="lang-toggle" onclick="toggleLang()" style="margin-left:12px" title="สลับภาษา / Switch language">
    <span class="lang-knob"></span>
    <span class="lang-opt opt-en">EN</span>
    <span class="lang-opt opt-th">ไทย</span>
  </div>
</nav>
<input type="file" id="import-file" accept=".json" style="display:none" onchange="handleImport(event)">"""

TAB1_START = """
<div id="tab-materials" class="tab-pane active">
<div class="mat-wrap">
  <h1 class="page-title">Material Effects</h1>
  <p class="page-sub">ข้อมูล stat ทุก slot พร้อมราคา Steam Market</p>
  <div class="controls">
    <div class="search-row">
      <span class="search-icon"><svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></span>
      <input class="search-input" id="mat-search" type="search" placeholder="ค้นหาชื่อ material..." autocomplete="off">
    </div>
    <div class="filter-rows">
      <div class="filter-group">
        <span class="filter-label">Type</span>
        <button class="pill active" data-filter="type" data-value="">""" + gb('All','ทั้งหมด') + """</button>
        <button class="pill" data-filter="type" data-value="Decoration">Decoration</button>
        <button class="pill" data-filter="type" data-value="Engraving">Engraving</button>
        <button class="pill" data-filter="type" data-value="Inscription">Inscription</button>
      </div>
      <div class="filter-group">
        <span class="filter-label">""" + gb('Slot','ส่วน') + """</span>
        <button class="pill active" data-filter="slot" data-value="">""" + gb('All','ทั้งหมด') + """</button>
        <button class="pill" data-filter="slot" data-value="Weapon">""" + gb('Weapon','อาวุธหลัก') + """</button>
        <button class="pill" data-filter="slot" data-value="Armor">""" + gb('Armor','เกราะ') + """</button>
        <button class="pill" data-filter="slot" data-value="Accessory">""" + gb('Accessory','เครื่องประดับ') + """</button>
      </div>
      <div class="filter-group">
        <span class="filter-label">""" + gb('Grade','ระดับ') + """</span>
        <button class="pill active" data-filter="grade" data-value="">""" + gb('All','ทั้งหมด') + """</button>
        <button class="pill" data-filter="grade" data-value="COMMON"><span class="grade-dot" style="background:""" + GRADE_COLORS['COMMON'] + """"></span>""" + gb('Common',GRADE_TH['COMMON']) + """</button>
        <button class="pill" data-filter="grade" data-value="UNCOMMON"><span class="grade-dot" style="background:""" + GRADE_COLORS['UNCOMMON'] + """"></span>""" + gb('Uncommon',GRADE_TH['UNCOMMON']) + """</button>
        <button class="pill" data-filter="grade" data-value="RARE"><span class="grade-dot" style="background:""" + GRADE_COLORS['RARE'] + """"></span>""" + gb('Rare',GRADE_TH['RARE']) + """</button>
        <button class="pill" data-filter="grade" data-value="LEGENDARY"><span class="grade-dot" style="background:""" + GRADE_COLORS['LEGENDARY'] + """"></span>""" + gb('Legendary',GRADE_TH['LEGENDARY']) + """</button>
        <button class="pill" data-filter="grade" data-value="IMMORTAL"><span class="grade-dot" style="background:""" + GRADE_COLORS['IMMORTAL'] + """"></span>""" + gb('Immortal',GRADE_TH['IMMORTAL']) + """</button>
        <button class="pill" data-filter="grade" data-value="ARCANA"><span class="grade-dot" style="background:""" + GRADE_COLORS['ARCANA'] + """"></span>""" + gb('Arcana',GRADE_TH['ARCANA']) + """</button>
        <button class="pill" data-filter="grade" data-value="BEYOND"><span class="grade-dot" style="background:""" + GRADE_COLORS['BEYOND'] + """"></span>""" + gb('Beyond',GRADE_TH['BEYOND']) + """</button>
      </div>
      <div class="filter-group">
        <span class="filter-label">""" + gb('Effect','เอฟเฟกต์') + """</span>
        <div class="eff-dd" id="eff-dd">
          <button type="button" class="eff-trigger" id="eff-trigger" onclick="toggleEffDD(event)">
            <span class="eff-cur" id="eff-cur">""" + gb('All effects','ทุกเอฟเฟกต์') + """</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <div class="eff-panel" id="eff-panel">
            <div class="eff-search-wrap">
              <input type="search" class="eff-search" id="eff-search" placeholder="" autocomplete="off" oninput="filterEffOpts(this.value)">
            </div>
            <div class="eff-list" id="eff-list">
              <div class="eff-opt active" data-v="" onclick="pickEff(this)">""" + gb('All effects','ทุกเอฟเฟกต์') + """</div>
              __EFFECT_OPTIONS__
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="result-bar"><span class="result-count" id="mat-count">"""

TAB1_MID = """</span><span>materials</span>""" + PRICE_DATE_HTML + """</div>
  <div class="grid" id="mat-grid">
"""

TAB1_END = """
    <div class="empty-state" id="mat-empty" style="display:none">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:.3;margin-bottom:10px"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <p>ไม่พบ material ที่ตรงกัน</p>
    </div>
  </div>
</div></div>"""

TAB2 = """
<div id="tab-calc" class="tab-pane">
<div class="calc-wrap">
  <h1 class="page-title">Stage Calculator</h1>
  <p class="page-sub">คำนวณ EXP/s และ Gold/s ต่อด่าน — เพิ่มหลายด่านเพื่อเปรียบเทียบ</p>
  <div class="controls" style="margin-bottom:20px;flex-direction:row;align-items:center;flex-wrap:wrap;gap:10px">
    <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="flex-shrink:0;color:var(--muted)"><path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0"/></svg>
    <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);white-space:nowrap">Default ทีม</span>
    <input type="text" class="ctrl" list="comp-list" id="default-comp-input" placeholder="เช่น Tank+Mage" style="max-width:200px;font-size:13px;height:34px" oninput="updateDefaultComp(this.value)">
    <span style="color:var(--muted);font-size:12px">รันใหม่ใช้ทีมนี้อัตโนมัติ</span>
    <button class="btn btn-ghost" onclick="clearDefaultComp()" style="margin-left:auto">ล้าง</button>
  </div>
  <datalist id="comp-list"></datalist>
  <div id="stages-container" style="display:flex;flex-direction:column;gap:16px"></div>
  <div class="stage-empty" id="stage-empty">
    <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" style="opacity:.3;margin-bottom:10px"><path d="M9 17v-6m3 6V7m3 10v-4M3 21h18"/></svg>
    <p>ยังไม่มีด่าน กด <strong style="color:var(--gold)">+ เพิ่มด่าน</strong> เพื่อเริ่มต้น</p>
  </div>
  <div id="comparison-section" class="cmp-section" style="display:none">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:14px">
      <h2 id="cmp-title" style="font-size:16px;font-weight:700;color:var(--text)">สรุปผลด่าน</h2>
      <div id="cmp-sort-btns" style="display:none;gap:6px;flex-wrap:wrap">
        <button class="sort-btn active" data-sort="worth" onclick="setSort(this)">Worth</button>
        <button class="sort-btn" data-sort="exp"   onclick="setSort(this)">EXP/s</button>
        <button class="sort-btn" data-sort="gold"  onclick="setSort(this)">Gold/s</button>
      </div>
    </div>
    <div style="overflow-x:auto;border-radius:var(--r);border:1px solid var(--border)">
      <table class="cmp-table">
        <thead><tr>
          <th class="cmp-th">ด่าน</th><th class="cmp-th">Difficulty</th>
          <th class="cmp-th">ทีม</th>
          <th class="cmp-th" id="cmp-th-worth" style="display:none;text-align:right">Worth</th>
          <th class="cmp-th" style="text-align:right">EXP/s</th>
          <th class="cmp-th" style="text-align:right">Gold/s</th>
          <th class="cmp-th" style="text-align:right">รัน</th>
          <th class="cmp-th" style="text-align:right">เฉลี่ย</th>
        </tr></thead>
        <tbody id="comparison-body"></tbody>
      </table>
    </div>
  </div>
</div></div>"""

TAB3 = """
<div id="tab-pets" class="tab-pane">
<div class="pet-wrap">
  <h1 class="page-title" style="margin-bottom:4px">Pet</h1>
  <p class="page-sub">Pets ทั้งหมดพร้อมโบนัสและแหล่งฟาร์ม</p>
  <div class="controls" style="margin-bottom:16px;flex-direction:row;align-items:center;flex-wrap:wrap;gap:10px">
    <div class="search-row" style="flex:1;min-width:200px">
      <span class="search-icon"><svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></span>
      <input class="search-input" id="pet-search" type="search" placeholder="ค้นหา pet หรือ bonus..." oninput="renderPets()">
    </div>
    <div style="display:flex;gap:6px">
      <button class="pill active pet-filter-btn" data-rarity="all"       onclick="setPetFilter(this)">ทั้งหมด</button>
      <button class="pill pet-filter-btn" data-rarity="free"             onclick="setPetFilter(this)">ฟาร์มได้</button>
      <button class="pill pet-filter-btn" data-rarity="supporter"        onclick="setPetFilter(this)">Supporter</button>
    </div>
  </div>
  <div class="result-bar"><span class="result-count" id="pet-count">0</span><span>pets</span></div>
  <div class="pet-grid" id="pet-grid"></div>
</div></div>"""

TAB4 = """
<div id="tab-gear" class="tab-pane">
<div class="gear-wrap">
  <h1 class="page-title" style="margin-bottom:4px">Equipment</h1>
  <p class="page-sub">Gear ทั้งหมด พร้อม base stats, inherent stats และ unique mods</p>
  <div class="controls" style="margin-bottom:16px">
    <div class="search-row" style="margin-bottom:10px">
      <span class="search-icon"><svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></span>
      <input class="search-input" id="gear-search" type="search" placeholder="ค้นหาชื่อ gear หรือ unique mod..." oninput="applyGearFilter()">
    </div>
    <div class="filter-rows">
      <div class="filter-group">
        <span class="filter-label">""" + gb('Slot','ส่วน') + """</span>
        <button class="pill active" data-gf="slot" data-gv="">""" + gb('All','ทั้งหมด') + """</button>
        <button class="pill" data-gf="slot" data-gv="Weapon">""" + gb('Weapon','อาวุธหลัก') + """</button>
        <button class="pill" data-gf="slot" data-gv="Offhand">""" + gb('Offhand','อาวุธรอง') + """</button>
        <button class="pill" data-gf="slot" data-gv="Armor">""" + gb('Armor','เกราะ') + """</button>
        <button class="pill" data-gf="slot" data-gv="Accessory">""" + gb('Accessory','เครื่องประดับ') + """</button>
      </div>
      <div class="filter-group">
        <span class="filter-label">""" + gb('Grade','ระดับ') + """</span>
        <button class="pill active" data-gf="grade" data-gv="">""" + gb('Legendary+','ตำนาน+') + """</button>
        <button class="pill" data-gf="grade" data-gv="LEGENDARY"><span class="grade-dot" style="background:""" + GRADE_COLORS['LEGENDARY'] + """"></span>""" + gb('Legendary',GRADE_TH['LEGENDARY']) + """</button>
        <button class="pill" data-gf="grade" data-gv="IMMORTAL"><span class="grade-dot" style="background:""" + GRADE_COLORS['IMMORTAL'] + """"></span>""" + gb('Immortal',GRADE_TH['IMMORTAL']) + """</button>
        <button class="pill" data-gf="grade" data-gv="ARCANA"><span class="grade-dot" style="background:""" + GRADE_COLORS['ARCANA'] + """"></span>""" + gb('Arcana',GRADE_TH['ARCANA']) + """</button>
        <button class="pill" data-gf="grade" data-gv="BEYOND"><span class="grade-dot" style="background:""" + GRADE_COLORS['BEYOND'] + """"></span>""" + gb('Beyond',GRADE_TH['BEYOND']) + """</button>
        <button class="pill" data-gf="grade" data-gv="CELESTIAL"><span class="grade-dot" style="background:""" + GRADE_COLORS['CELESTIAL'] + """"></span>""" + gb('Celestial',GRADE_TH['CELESTIAL']) + """</button>
        <button class="pill" data-gf="grade" data-gv="DIVINE"><span class="grade-dot" style="background:""" + GRADE_COLORS['DIVINE'] + """"></span>""" + gb('Divine',GRADE_TH['DIVINE']) + """</button>
        <button class="pill" data-gf="grade" data-gv="COSMIC"><span class="grade-dot" style="background:""" + GRADE_COLORS['COSMIC'] + """"></span>""" + gb('Cosmic',GRADE_TH['COSMIC']) + """</button>
      </div>
      <div class="filter-group" style="flex-wrap:wrap">
        <span class="filter-label">Level</span>
        <button class="pill active" data-gf="level" data-gv="0">""" + gb('All','ทั้งหมด') + """</button>
        <button class="pill" data-gf="level" data-gv="1">1</button>
        <button class="pill" data-gf="level" data-gv="5">5</button>
        <button class="pill" data-gf="level" data-gv="10">10</button>
        <button class="pill" data-gf="level" data-gv="15">15</button>
        <button class="pill" data-gf="level" data-gv="20">20</button>
        <button class="pill" data-gf="level" data-gv="25">25</button>
        <button class="pill" data-gf="level" data-gv="30">30</button>
        <button class="pill" data-gf="level" data-gv="35">35</button>
        <button class="pill" data-gf="level" data-gv="40">40</button>
        <button class="pill" data-gf="level" data-gv="45">45</button>
        <button class="pill" data-gf="level" data-gv="50">50</button>
        <button class="pill" data-gf="level" data-gv="55">55</button>
        <button class="pill" data-gf="level" data-gv="60">60</button>
        <button class="pill" data-gf="level" data-gv="65">65</button>
        <button class="pill" data-gf="level" data-gv="70">70</button>
        <button class="pill" data-gf="level" data-gv="75">75</button>
        <button class="pill" data-gf="level" data-gv="80">80</button>
        <button class="pill" data-gf="level" data-gv="85">85</button>
        <button class="pill" data-gf="level" data-gv="90">90</button>
      </div>
      <div id="gear-type-group" style="display:flex;flex-direction:column;gap:6px"></div>
      <div class="filter-group">
        <span class="filter-label">""" + gb('Unique','ยูนีค') + """</span>
        <button class="pill" id="gear-unique-btn" onclick="toggleGearUnique()">&#10022; """ + gb('Has unique mod','มี unique mod') + """</button>
      </div>
    </div>
  </div>
  <div class="result-bar"><span class="result-count" id="gear-count">0</span><span>items</span>""" + PRICE_DATE_HTML + """</div>
  <div class="grid" id="gear-grid"></div>
</div></div>"""

TAB_CRAFT = """
<div id="tab-craft" class="tab-pane">
<div class="craft-wrap">
  <h1 class="page-title"><span class="en">Crafting</span><span class="th">คราฟต์</span></h1>
  <p class="page-sub"><span class="en">Recipes with material cost from Steam Market — click an item to buy</span><span class="th">สูตรคราฟต์ พร้อมราคาวัตถุดิบจาก Steam Market — กดที่ของเพื่อไปซื้อ</span></p>
  <div class="controls" style="margin-bottom:16px">
    <div class="filter-rows">
      <div class="filter-group">
        <span class="filter-label">""" + gb('Type','ประเภท') + """</span>
        <button class="pill active" data-cf="" onclick="setCraftFilter(this)">""" + gb('All','ทั้งหมด') + """</button>
        <button class="pill" data-cf="MainWeapon" onclick="setCraftFilter(this)">""" + gb('Main Weapon','อาวุธหลัก') + """</button>
        <button class="pill" data-cf="SubWeapon" onclick="setCraftFilter(this)">""" + gb('Sub Weapon','อาวุธรอง') + """</button>
        <button class="pill" data-cf="Helmet" onclick="setCraftFilter(this)">""" + gb('Helmet','หมวก') + """</button>
        <button class="pill" data-cf="Armor" onclick="setCraftFilter(this)">""" + gb('Armor','เกราะ') + """</button>
        <button class="pill" data-cf="Gloves" onclick="setCraftFilter(this)">""" + gb('Gloves','ถุงมือ') + """</button>
        <button class="pill" data-cf="Boots" onclick="setCraftFilter(this)">""" + gb('Boots','รองเท้า') + """</button>
        <button class="pill" data-cf="Accessory" onclick="setCraftFilter(this)">""" + gb('Accessory','เครื่องประดับ') + """</button>
      </div>
    </div>
  </div>
  <div class="result-bar"><span class="result-count" id="craft-count">0</span><span>""" + gb('recipes','สูตร') + """</span>""" + PRICE_DATE_HTML + """</div>
  <div class="craft-grid" id="craft-grid"></div>
</div></div>"""

TAB_STAGES = """
<div id="tab-stages" class="tab-pane">
<div class="stages-wrap">
  <h1 class="page-title">Stages</h1>
  <p class="page-sub">3 Acts · 4 Difficulties · 30 stages each — คลิกแถวเพื่อดู detail</p>
  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:16px;font-size:12px;color:var(--muted)">
    <span><span class="en">Level needed:</span><span class="th">เลเวลที่ต้องใช้:</span></span>
    <span style="color:#93c5fd;background:#93c5fd18;border:1px solid #93c5fd44;padding:1px 7px;border-radius:4px;font-weight:700">N = <span class="en">Normal</span><span class="th">ปกติ</span></span>
    <span style="color:#c4b5fd;background:#c4b5fd18;border:1px solid #c4b5fd44;padding:1px 7px;border-radius:4px;font-weight:700">NM = <span class="en">Nightmare</span><span class="th">ฝันร้าย</span></span>
    <span style="color:#fdba74;background:#fdba7418;border:1px solid #fdba7444;padding:1px 7px;border-radius:4px;font-weight:700">H = <span class="en">Hell</span><span class="th">นรก</span></span>
    <span style="color:#fda4af;background:#fda4af18;border:1px solid #fda4af44;padding:1px 7px;border-radius:4px;font-weight:700">T = <span class="en">Torment</span><span class="th">ทรมาน</span></span>
  </div>
  <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap">
    <div style="flex:1;min-width:320px">
      <div class="stage-acts-grid" id="stage-acts-grid"></div>
    </div>
    <div style="flex:0 0 300px">
      <div id="stage-detail-panel"></div>
    </div>
  </div>
</div></div>"""

TAB6_RUNES = f"""
<div id="tab-runes" class="tab-pane">
<div class="runes-wrap">
  <h1 class="page-title">Rune Tree</h1>
  <p class="page-sub">{len(_rnodes)} rune nodes · {len(_redges)} connections — ลากเพื่อเลื่อน, scroll เพื่อซูม, คลิก node เพื่อดู detail</p>
  <div class="search-row" style="margin-bottom:12px;max-width:420px">
    <span class="search-icon"><svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></span>
    <input class="search-input" id="rune-search" type="search" placeholder="ค้นหา rune เช่น Offline Reward EXP, Gold, Chest..." autocomplete="off" oninput="filterRunes(this.value)">
    <span id="rune-match-count" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);font-size:12px;color:var(--muted);pointer-events:none"></span>
  </div>
  <div class="rune-viewport" id="rune-vp">
    <div class="rune-world" id="rune-world">
      <svg class="rune-edges" id="rune-edges" width="{RUNE_W}" height="{RUNE_H}"></svg>
    </div>
    <div class="rune-controls">
      <button class="rune-ctrl-btn" onclick="runeZoom(1.2)">+</button>
      <button class="rune-ctrl-btn" onclick="runeZoom(0.8)">−</button>
      <button class="rune-ctrl-btn" style="font-size:11px;width:auto;padding:0 10px" onclick="runeReset()">Reset</button>
    </div>
    <div class="rune-hint">Drag to pan · Scroll to zoom · Click node for details</div>
  </div>
  <div class="rune-tooltip" id="rune-tt"></div>
</div></div>"""

TAB5 = """
<div id="tab-skills" class="tab-pane">
<div class="skills-wrap">
  <h1 class="page-title">Skills</h1>
  <p class="page-sub">Active skills และ Passive skills ของแต่ละ class — กดที่ skill เพื่อดู detail</p>
  <div class="hero-nav" id="hero-nav"></div>
  <div id="skills-content"></div>
</div></div>
<div class="skill-detail-ov" id="skill-detail-ov" onclick="closeSkillDetail(event)">
  <div class="skill-detail-box" id="skill-detail-box"></div>
</div>"""

MODAL = """
<div class="modal-ov" id="modal-ov" onclick="modalBg(event)">
  <div class="modal-box">
    <div class="mi" id="mi"></div>
    <div class="mt" id="mt"></div>
    <div class="mm" id="mm"></div>
    <div class="ma" id="ma"></div>
  </div>
</div>"""

# JS is a plain string — NO f-string, so JS template literals ${} are safe
JS = r"""
<script>
// ── Language toggle ───────────────────────────────────────────────────────────
function toggleLang() {
  const th = document.body.classList.toggle('lang-th');
  try { localStorage.setItem('tbh_lang', th ? 'th' : 'en'); } catch {}
  applyLangToSelects(th);
}
function applyLangToSelects(th) {
  document.querySelectorAll('#stages-container option[data-en]').forEach(o => {
    o.textContent = th ? o.dataset.th : o.dataset.en;
  });
}
function jbi(o) {
  if (o == null) return '';
  if (typeof o === 'string') return esc(o);
  return '<span class="en">' + esc(o.e) + '</span><span class="th">' + esc(o.t) + '</span>';
}
// ── custom Effect dropdown ──
window.matEffectVal = '';
function toggleEffDD(e) {
  e.stopPropagation();
  const dd = document.getElementById('eff-dd');
  const open = dd.classList.toggle('open');
  if (open) { const s = document.getElementById('eff-search'); s.value=''; filterEffOpts(''); setTimeout(()=>s.focus(),0); }
}
function pickEff(el) {
  window.matEffectVal = el.dataset.v;
  document.querySelectorAll('#eff-list .eff-opt').forEach(o => o.classList.toggle('active', o===el));
  document.getElementById('eff-cur').innerHTML = el.innerHTML;
  document.getElementById('eff-dd').classList.remove('open');
  window.applyMatFilter && window.applyMatFilter();
}
function filterEffOpts(q) {
  q = (q||'').trim().toLowerCase();
  let n = 0;
  document.querySelectorAll('#eff-list .eff-opt').forEach(o => {
    const hit = !q || o.textContent.toLowerCase().includes(q);
    o.classList.toggle('hide', !hit);
    if (hit) n++;
  });
}
document.addEventListener('click', e => {
  const dd = document.getElementById('eff-dd');
  if (dd && !dd.contains(e.target)) dd.classList.remove('open');
});

// bilingual with a per-side transform (e.g. {0} replacement). fn must return HTML-safe string.
function jbiR(o, fn) {
  if (o == null) return '';
  if (typeof o === 'string') return fn(o);
  return '<span class="en">' + fn(o.e) + '</span><span class="th">' + fn(o.t) + '</span>';
}
// Difficulty Thai (in-game): Normal/Nightmare/Hell/Torment + UPPERCASE variants
const DIFF_TH = {Normal:'ปกติ',Nightmare:'ฝันร้าย',Hell:'นรก',Torment:'ทรมาน',
                 NORMAL:'ปกติ',NIGHTMARE:'ฝันร้าย',HELL:'นรก',TORMENT:'ทรมาน'};
function jdiff(d) { return jbi({e: d, t: (DIFF_TH[d] || d)}); }
// default Thai (body starts with lang-th); switch to EN only if saved
(function(){ try {
  if (localStorage.getItem('tbh_lang') === 'en') document.body.classList.remove('lang-th');
  else document.addEventListener('DOMContentLoaded', () => applyLangToSelects(true));
} catch {} })();

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(btn) {
  const tab = btn.dataset.tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === 'tab-' + tab));
  document.getElementById('calc-actions').classList.toggle('visible', tab === 'calc');
  if (tab === 'pets') renderPets();
  if (tab === 'skills') initSkills();
  if (tab === 'runes')  initRuneTree();
  if (tab === 'stages') initStages();
  if (tab === 'craft')  initCraft();
}

// ── Material Effects filter ───────────────────────────────────────────────────
(function() {
  const grid    = document.getElementById('mat-grid');
  const countEl = document.getElementById('mat-count');
  const emptyEl = document.getElementById('mat-empty');
  const searchEl = document.getElementById('mat-search');
  const allCards = Array.from(grid.querySelectorAll('.card'));
  let typeSet = new Set(), slotSet = new Set(), gradeSet = new Set(), q = '', effect = '';

  function apply() {
    let n = 0;
    allCards.forEach(c => {
      c.querySelectorAll('.slot-sec').forEach(s => {
        s.style.display = (!slotSet.size || slotSet.has(s.dataset.slot) || s.dataset.slot === 'Common') ? '' : 'none';
      });
      const slots = c.dataset.slots ? c.dataset.slots.split(',') : [];
      let effectOk = !effect;
      if (effect) {
        const bySlot = JSON.parse(c.dataset.stats || '{}');
        // match effect only within slots currently visible (respects slot filter)
        for (const [sl, sts] of Object.entries(bySlot)) {
          const slotVisible = !slotSet.size || slotSet.has(sl) || sl === 'Common';
          if (slotVisible && sts.includes(effect)) { effectOk = true; break; }
        }
      }
      const ok = (!slotSet.size  || slots.some(sv => slotSet.has(sv)) || slots.includes('Common'))
              && (!typeSet.size  || typeSet.has(c.dataset.type))
              && (!gradeSet.size || gradeSet.has(c.dataset.grade))
              && effectOk
              && (!q             || c.dataset.name.includes(q));
      c.style.display = ok ? '' : 'none';
      if (ok) n++;
    });
    countEl.textContent = n;
    emptyEl.style.display = n === 0 ? '' : 'none';
  }
  window.applyMatFilter = function() { effect = window.matEffectVal || ''; apply(); };

  document.querySelectorAll('.pill[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      const f = btn.dataset.filter;
      const v = btn.dataset.value;
      const s = f === 'type' ? typeSet : f === 'slot' ? slotSet : gradeSet;
      if (!v) { s.clear(); }
      else { if (s.has(v)) s.delete(v); else s.add(v); }
      document.querySelectorAll(`.pill[data-filter="${f}"]`).forEach(b => {
        const bv = b.dataset.value;
        b.classList.toggle('active', !bv ? s.size === 0 : s.has(bv));
      });
      apply();
    });
  });

  let timer;
  searchEl.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { q = searchEl.value.trim().toLowerCase(); apply(); }, 120);
  });
})();

// ── Pet data ──────────────────────────────────────────────────────────────────
const PETS = [
  { name:'Bat', type:'free', img:'img/Bat.png', priority:true,
    bonus:['10% Increased Common Chest Drop Chance Multiplier','15% Increased Exp Gain'],
    unlock:'Defeat 5,000 × Bat',
    bestFarm:[
      {stage:'A1-7',name:'City Outskirts',diff:'Torment',perRun:'~204'},
      {stage:'A1-8',name:'Cemetery',diff:'Torment',perRun:'~172'},
      {stage:'A1-7',name:'City Outskirts',diff:'Hell',perRun:'~148'},
    ]},
  { name:'Watcher', type:'free', img:'img/Watcher.png', priority:true,
    bonus:['15% Increased Gold Per Kill'],
    unlock:'Defeat 5,000 × Giant Fly',
    bestFarm:[
      {stage:'A2-5',name:'Scorching Dunes',diff:'Torment',perRun:'~228'},
      {stage:'A2-5',name:'Scorching Dunes',diff:'Hell',perRun:'~160'},
      {stage:'A2-5',name:'Scorching Dunes',diff:'Nightmare',perRun:'~114'},
    ]},
  { name:'Burning Skeleton', type:'free', img:'img/Burning Skeleton.png',
    bonus:['10% Increased Stage Boss Chest Drop Chance Multiplier'],
    unlock:'Defeat 5,000 × Fire Elemental',
    bestFarm:[
      {stage:'A2-8',name:'Sacred Tomb',diff:'Torment',perRun:'~120'},
      {stage:'A2-9',name:"Pharaoh's Crypt",diff:'Torment',perRun:'~109'},
      {stage:'A2-9',name:"Pharaoh's Crypt",diff:'Hell',perRun:'~80'},
    ]},
  { name:'Blue Golem', type:'free', img:'img/Blue Golem.png',
    bonus:['15% Increased Common Chest Drop Chance Multiplier'],
    unlock:'Defeat 5,000 × Hell Golem',
    bestFarm:[
      {stage:'A3-6',name:'Burning Ravine',diff:'Torment',perRun:'~138'},
      {stage:'A3-6',name:'Burning Ravine',diff:'Hell',perRun:'~131'},
      {stage:'A3-6',name:'Burning Ravine',diff:'Nightmare',perRun:'~85'},
    ]},
  { name:'Dark Spirit', type:'free', img:'img/Dark Spirit.png',
    bonus:['15% Increased Stage Boss Chest Drop Chance Multiplier'],
    unlock:'Defeat 5,000 × Ghost',
    bestFarm:[
      {stage:'A3-4',name:'Frozen Glacier Cavern',diff:'Torment',perRun:'~135'},
      {stage:'A3-4',name:'Frozen Glacier Cavern',diff:'Hell',perRun:'~100'},
      {stage:'A3-9',name:'Core of the Abyss',diff:'Torment',perRun:'~88'},
    ]},
  { name:'Sword', type:'supporter', img:'img/Sword.png',
    bonus:['15% Increased Exp Gain'],
    unlock:'Purchase the Supporter Pack on Steam', bestFarm:[]},
  { name:'Butterfly', type:'supporter', img:'img/Butterfly.png',
    bonus:['10% Increased Gold Per Kill'],
    unlock:'Purchase the Supporter Pack on Steam', bestFarm:[]},
  { name:'Dragon', type:'supporter', img:'img/Dragon.png',
    bonus:['20% Increased Common Chest Drop Chance Multiplier','15% Increased Gold Per Kill','20% Increased Exp Gain'],
    unlock:'Purchase the Supporter Pack on Steam', bestFarm:[]},
];

const DIFF_COLOR = {Torment:'#fda4af',Hell:'#fdba74',Nightmare:'#c4b5fd',Normal:'#93c5fd'};
const DIFF_BG    = {Torment:'rgba(190,18,60,.2)',Hell:'rgba(194,65,12,.2)',Nightmare:'rgba(109,40,217,.2)',Normal:'rgba(29,78,216,.2)'};
const PET_BONUS_TH = {
  'Increased Common Chest Drop Chance Multiplier':'เพิ่มอัตราดรอปหีบทั่วไป',
  'Increased Stage Boss Chest Drop Chance Multiplier':'เพิ่มอัตราดรอปหีบบอสด่าน',
  'Increased Exp Gain':'เพิ่ม EXP ที่ได้รับ',
  'Increased Gold Per Kill':'เพิ่มทองต่อการสังหาร',
};
let petFilter = 'all';

function setPetFilter(btn) {
  petFilter = btn.dataset.rarity;
  document.querySelectorAll('.pet-filter-btn').forEach(b => b.classList.toggle('active', b === btn));
  renderPets();
}

function renderPets() {
  const q = (document.getElementById('pet-search')?.value || '').toLowerCase();
  const grid = document.getElementById('pet-grid');
  const countEl = document.getElementById('pet-count');
  if (!grid) return;

  const list = PETS.filter(p => {
    if (petFilter === 'free' && p.type !== 'free') return false;
    if (petFilter === 'supporter' && p.type !== 'supporter') return false;
    if (q && !p.name.toLowerCase().includes(q) && !p.bonus.join(' ').toLowerCase().includes(q)) return false;
    return true;
  });

  if (countEl) countEl.textContent = list.length;

  if (!list.length) {
    grid.innerHTML = '<div class="empty-state"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:.3;margin-bottom:10px"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><p>ไม่พบ pet</p></div>';
    return;
  }

  grid.innerHTML = list.map(p => {
    const isSupporter = p.type === 'supporter';
    const borderColor = p.priority ? '#4338ca' : isSupporter ? '#92400e' : 'var(--border2)';

    const badges = [
      p.priority ? '<span class="badge badge-priority">★ Priority</span>' : '',
      isSupporter ? '<span class="badge badge-supporter">Supporter</span>'
                  : '<span class="badge badge-free">ฟาร์มได้</span>',
    ].filter(Boolean).join('');

    const bonusRows = p.bonus.map(b => {
      const pct = b.match(/\d+%/)?.[0] || '';
      const col = b.includes('Exp') ? '#4ade80' : b.includes('Gold') ? '#fcd34d' : '#a78bfa';
      const stem = b.replace(pct,'').trim();
      return `<div class="slot-row">
        <span class="stat-name">${jbi({e:stem, t:(PET_BONUS_TH[stem]||stem)})}</span>
        <span class="stat-right"><span class="stat-val" style="color:${col}">${pct}</span></span>
      </div>`;
    }).join('');

    const farmSection = p.bestFarm.length ? `
      <div class="farm-box">
        <div class="farm-box-header">${jbi({e:'Best Farm Locations',t:'จุดฟาร์มที่ดีที่สุด'})}</div>
        ${p.bestFarm.map(f => `
          <div class="farm-row">
            <span class="num" style="font-size:12px;font-weight:700;color:var(--text);min-width:38px">${esc(f.stage)}</span>
            <span style="font-size:11px;color:var(--muted);flex:1">${jbi({e:f.name,t:(STAGE_NAME_TH[f.name]||f.name)})}</span>
            <span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;background:${DIFF_BG[f.diff]||''};color:${DIFF_COLOR[f.diff]||'var(--muted)'};white-space:nowrap">${jdiff(f.diff)}</span>
            <span class="num" style="font-size:11px;font-weight:700;color:#818cf8;min-width:54px;text-align:right">${esc(f.perRun)}/run</span>
          </div>`).join('')}
      </div>` : `
      <div style="padding-top:10px;border-top:1px solid var(--border);font-size:12px;color:var(--muted)">
        ซื้อได้จาก <a href="https://store.steampowered.com" target="_blank" style="color:#60a5fa;text-decoration:none">Steam Supporter Pack</a>
      </div>`;

    return `<article class="card" style="border-left:3px solid ${borderColor}">
      <div class="card-hd">
        <div class="icon-wrap" style="width:60px;height:60px;flex-shrink:0">
          <img style="width:54px;height:54px;object-fit:contain;image-rendering:pixelated" src="${esc(p.img)}" alt="${esc(p.name)}" onerror="this.style.opacity='.3'">
        </div>
        <div class="card-meta">
          <span class="item-name">${jbi({e:p.name, t:(PET_TH[p.name]||p.name)})}</span>
          <div class="card-tags">${badges}</div>
          ${(()=>{const m=p.unlock.match(/^Defeat ([\d,]+) × (.+)$/);return m?`<div class="pet-unlock"><span class="unlock-lbl">Unlock</span>${jbi({e:'Defeat',t:'กำจัด'})} <span class="unlock-count">${m[1]}</span> × ${jbi({e:m[2],t:(MONSTER_TH[m[2]]||m[2])})}</div>`:`<div class="pet-unlock"><span class="unlock-lbl">Unlock</span><a href="https://store.steampowered.com/app/3678970" target="_blank" style="color:#60a5fa;text-decoration:none">Steam Supporter Pack</a></div>`;})()}
        </div>
      </div>
      <div class="card-stats">
        <div class="slot-sec">
          <span class="slot-lbl">${jbi({e:'Bonus',t:'โบนัส'})}</span>
          ${bonusRows}
        </div>
        ${farmSection}
      </div>
    </article>`;
  }).join('');
}

// ── Stage Calculator ──────────────────────────────────────────────────────────
const DIFF_CLS  = {Normal:'d-normal',Nightmare:'d-nightmare',Hell:'d-hell',Torment:'d-torment'};
const DIFFICULTIES = ['Normal','Nightmare','Hell','Torment'];
const STORAGE_KEY  = 'tbh_v4';
let stages = [], stageIdCounter = 0, sortKey = 'worth', modalCb = null;
let defaultComp = localStorage.getItem('tbh_defaultComp') || '';

function updateDefaultComp(v) { defaultComp=v; localStorage.setItem('tbh_defaultComp',v); }
function clearDefaultComp() {
  defaultComp=''; localStorage.removeItem('tbh_defaultComp');
  const el=document.getElementById('default-comp-input'); if(el)el.value='';
}
document.addEventListener('DOMContentLoaded',()=>{ const el=document.getElementById('default-comp-input'); if(el&&defaultComp)el.value=defaultComp; });

function stageSelectHtml(selected) {
  let h='';
  for(let w=1;w<=3;w++){
    h+=`<optgroup label="Act ${w}">`;
    for(let s=1;s<=10;s++){const v=`${w}-${s}`;h+=`<option value="${v}" ${selected===v?'selected':''}>${v}</option>`;}
    h+='</optgroup>';
  }
  return h;
}

const ICO_WARN=`<svg style="color:#f87171" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>`;
const ICO_INFO=`<svg style="color:#818cf8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path stroke-linecap="round" d="M12 8v4m0 4h.01"/></svg>`;

function showConfirm({title,msg,confirmLabel='ยืนยัน',danger=true},cb){
  document.getElementById('mi').innerHTML=danger?ICO_WARN:ICO_INFO;
  document.getElementById('mi').style.background=danger?'rgba(239,68,68,.2)':'rgba(129,140,248,.2)';
  document.getElementById('mt').textContent=title;
  document.getElementById('mm').textContent=msg;
  document.getElementById('ma').innerHTML=`<button class="mb mb-cancel" onclick="closeModal()">ยกเลิก</button><button class="mb ${danger?'mb-danger':'mb-ok'}" onclick="confirmModal()">${esc(confirmLabel)}</button>`;
  modalCb=cb; document.getElementById('modal-ov').classList.add('show');
}
function showAlert({title,msg}){
  document.getElementById('mi').innerHTML=ICO_INFO;
  document.getElementById('mi').style.background='rgba(129,140,248,.2)';
  document.getElementById('mt').textContent=title; document.getElementById('mm').textContent=msg;
  document.getElementById('ma').innerHTML=`<button class="mb mb-ok" onclick="closeModal()">ตกลง</button>`;
  modalCb=null; document.getElementById('modal-ov').classList.add('show');
}
function confirmModal(){closeModal();modalCb?.();}
function closeModal(){document.getElementById('modal-ov').classList.remove('show');}
function modalBg(e){if(e.target===document.getElementById('modal-ov'))closeModal();}

function save(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify({stages,stageIdCounter}));}catch{}}
function load(){
  try{
    const d=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');
    if(!d?.stages)return false;
    stages=d.stages; stageIdCounter=d.stageIdCounter||stages.reduce((m,s)=>Math.max(m,s.id),0);
    return true;
  }catch{return false;}
}
function updateCompList(){
  const vals=[...new Set(stages.flatMap(s=>s.runs.map(r=>r.comp?.trim()).filter(Boolean)))].sort();
  document.getElementById('comp-list').innerHTML=vals.map(v=>`<option value="${esc(v)}"></option>`).join('');
}
function setSort(btn){
  sortKey=btn.dataset.sort;
  document.querySelectorAll('.sort-btn').forEach(b=>b.classList.toggle('active',b===btn));
  renderComparison();
}
function addStage(){const id=++stageIdCounter;stages.push({id,name:'1-1',difficulty:'Normal',runs:[]});renderAll();save();addRun(id);}
function removeStage(id){
  const s=stages.find(x=>x.id===id);
  showConfirm({title:'ลบด่านนี้?',msg:`"${s?.name}" และรันทั้งหมดจะถูกลบถาวร`,confirmLabel:'ลบด่าน'},
    ()=>{stages=stages.filter(x=>x.id!==id);renderAll();save();});
}
function addRun(sid){
  const s=stages.find(x=>x.id===sid);if(!s)return;
  s.runs.push({id:Date.now()+Math.random(),comp:defaultComp,startExp:'',endExp:'',startGold:'',endGold:'',time:'',recordedAt:new Date().toISOString()});
  renderAll();save();
}
function removeRun(sid,rid){
  const s=stages.find(x=>x.id===sid);if(!s)return;
  const idx=s.runs.findIndex(r=>r.id===rid);
  showConfirm({title:'ลบรันนี้?',msg:`รัน #${idx+1} จะถูกลบถาวร`,confirmLabel:'ลบรัน'},
    ()=>{s.runs=s.runs.filter(r=>r.id!==rid);renderAll();save();});
}
function updateField(sid,rid,field,value){
  const s=stages.find(x=>x.id===sid);if(!s)return;
  const r=s.runs.find(x=>x.id===rid);if(!r)return;
  r[field]=value;save();
  const res=calcRun(r);
  const pillsEl=document.getElementById(`pills-${rid}`);
  if(pillsEl)pillsEl.innerHTML=res
    ?`<div class="pill-e">EXP <strong class="num">${fmtInt(res.gainedExp)}</strong> &rarr; <strong class="num">${fmt(res.expPerSec)}/s</strong></div>
      <div class="pill-g">Gold <strong class="num">${fmtInt(res.gainedGold)}</strong> &rarr; <strong class="num">${fmt(res.goldPerSec)}/s</strong></div>`:'';
  const avg=calcStageAvg(s);
  const avgEl=document.getElementById(`stage-avg-${sid}`);
  if(avgEl)avgEl.innerHTML=avg
    ?`<span class="chip" style="color:#4ade80">EXP <strong class="num">${fmt(avg.avgExpPerSec)}/s</strong></span>
      <span class="chip" style="color:#fcd34d">Gold <strong class="num">${fmt(avg.avgGoldPerSec)}/s</strong></span>
      <span class="chip" style="color:var(--muted)">${avg.count} รัน</span>`:'';
  if(field==='time'){const el=document.getElementById(`time-fmt-${rid}`);if(el)el.textContent=fmtSec(+value);}
  if(field==='comp'){
    const el=document.getElementById(`comp-badge-${rid}`);
    if(el)el.innerHTML=value.trim()?`<span class="comp-badge">${esc(value.trim())}</span>`:'';
    updateCompList();
  }
  renderComparison();
}
function updateStageName(sid,v){const s=stages.find(x=>x.id===sid);if(s){s.name=v;renderAll();save();}}
function updateDifficulty(sid,v){const s=stages.find(x=>x.id===sid);if(s){s.difficulty=v;renderAll();save();}}

function calcRun(r){
  if(!r.startExp||!r.endExp||!r.startGold||!r.endGold||!r.time)return null;
  const se=+r.startExp,ee=+r.endExp,sg=+r.startGold,eg=+r.endGold,t=+r.time;
  if([se,ee,sg,eg,t].some(isNaN)||t<=0)return null;
  if(ee<se||eg<sg)return null;  // จบ < เริ่ม = พิมพ์ผิด ไม่นับ
  return{gainedExp:ee-se,gainedGold:eg-sg,expPerSec:(ee-se)/t,goldPerSec:(eg-sg)/t,time:t};
}
function calcStageAvg(s){
  const rs=s.runs.map(calcRun).filter(Boolean);if(!rs.length)return null;
  const comps=[...new Set(s.runs.filter(r=>r.comp?.trim()).map(r=>r.comp.trim()))];
  return{avgExpPerSec:rs.reduce((a,r)=>a+r.expPerSec,0)/rs.length,avgGoldPerSec:rs.reduce((a,r)=>a+r.goldPerSec,0)/rs.length,avgTime:rs.reduce((a,r)=>a+r.time,0)/rs.length,count:rs.length,comps};
}
function fmt(n,d=2){if(n==null||isNaN(n))return'—';return n.toLocaleString('en',{minimumFractionDigits:d,maximumFractionDigits:d});}
function fmtInt(n){if(n==null||isNaN(n))return'—';return Math.round(n).toLocaleString('en');}
function fmtSec(s){if(!s||isNaN(s)||s<=0)return'';const m=Math.floor(s/60),sec=Math.round(s%60);return m>0?`${m}:${String(sec).padStart(2,'0')} นาที`:`${sec} วิ`;}
function fmtTs(iso){if(!iso)return'';try{const d=new Date(iso);return`${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;}catch{return'';}}
function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

let dragSrcId=null;
function onDragStart(e,sid){if(!e.target.closest('.drag-handle')){e.preventDefault();return;}dragSrcId=sid;e.dataTransfer.effectAllowed='move';setTimeout(()=>e.target.closest('.card-stage')?.classList.add('dragging'),0);}
function onDragEnd(e){e.target.closest('.card-stage')?.classList.remove('dragging');document.querySelectorAll('.card-stage').forEach(c=>c.classList.remove('drag-over'));}
function onDragOver(e,sid){e.preventDefault();if(dragSrcId===sid)return;document.querySelectorAll('.card-stage').forEach(c=>c.classList.remove('drag-over'));e.currentTarget.classList.add('drag-over');}
function onDragLeave(e){e.currentTarget.classList.remove('drag-over');}
function onDrop(e,sid){
  e.preventDefault();document.querySelectorAll('.card-stage').forEach(c=>c.classList.remove('drag-over'));
  if(!dragSrcId||dragSrcId===sid)return;
  const si=stages.findIndex(s=>s.id===dragSrcId),di=stages.findIndex(s=>s.id===sid);
  if(si<0||di<0)return;
  const[moved]=stages.splice(si,1);stages.splice(di,0,moved);
  dragSrcId=null;renderAll();save();
}

function renderAll(){
  const fEl=document.activeElement,fKey=fEl?.getAttribute('data-fk');
  let selS,selE;try{selS=fEl?.selectionStart;selE=fEl?.selectionEnd;}catch{}
  const container=document.getElementById('stages-container');
  const empty=document.getElementById('stage-empty');
  if(!stages.length){container.innerHTML='';empty.style.display='block';document.getElementById('comparison-section').style.display='none';return;}
  empty.style.display='none';
  container.innerHTML=stages.map(renderStage).join('');
  updateCompList();renderComparison();
  if(fKey){const el=document.querySelector(`[data-fk="${fKey}"]`);if(el){el.focus();try{if(typeof selS==='number')el.setSelectionRange(selS,selE);}catch{}}}
}

function renderComparison(){
  const sec=document.getElementById('comparison-section');
  if(!stages.length){sec.style.display='none';return;}
  sec.style.display='block';
  const isMulti=stages.length>=2;
  document.getElementById('cmp-title').textContent=isMulti?'สรุปเปรียบเทียบด่าน':'สรุปผลด่าน';
  document.getElementById('cmp-sort-btns').style.display=isMulti?'flex':'none';
  document.getElementById('cmp-th-worth').style.display=isMulti?'':'none';
  const entries=stages.map(s=>({stage:s,avg:calcStageAvg(s),worthScore:null}));
  const withData=entries.filter(x=>x.avg);
  if(withData.length>=2){
    const eV=withData.map(x=>x.avg.avgExpPerSec),gV=withData.map(x=>x.avg.avgGoldPerSec);
    const minE=Math.min(...eV),maxE=Math.max(...eV),minG=Math.min(...gV),maxG=Math.max(...gV);
    const norm=(v,lo,hi)=>hi===lo?100:Math.round((v-lo)/(hi-lo)*100);
    withData.forEach(x=>{x.worthScore=Math.round((norm(x.avg.avgExpPerSec,minE,maxE)+norm(x.avg.avgGoldPerSec,minG,maxG))/2);});
  }else if(withData.length===1){withData[0].worthScore=100;}
  const score=x=>{if(!x.avg)return-Infinity;if(sortKey==='exp')return x.avg.avgExpPerSec;if(sortKey==='gold')return x.avg.avgGoldPerSec;return x.worthScore??-Infinity;};
  entries.sort((a,b)=>score(b)-score(a));
  const topE=Math.max(...withData.map(x=>x.avg.avgExpPerSec),0);
  const topG=Math.max(...withData.map(x=>x.avg.avgGoldPerSec),0);
  document.getElementById('comparison-body').innerHTML=entries.map(({stage,avg,worthScore},i)=>{
    const dc=DIFF_CLS[stage.difficulty]||'d-normal';
    if(!avg)return`<tr class="row-nodata"><td class="cmp-td" style="font-weight:700">${esc(stage.name)}</td><td class="cmp-td"><span class="diff-badge ${dc}">${jdiff(stage.difficulty)}</span></td><td class="cmp-td" colspan="6" style="color:var(--muted);font-size:12px">ยังไม่มีข้อมูลรัน</td></tr>`;
    const bE=avg.avgExpPerSec===topE,bG=avg.avgGoldPerSec===topG;
    const rc=i===0&&sortKey==='worth'?'row-worth':i===0&&sortKey==='exp'?'row-exp':i===0&&sortKey==='gold'?'row-gold':'';
    const ch=avg.comps?.length?avg.comps.map(c=>`<span class="comp-badge">${esc(c)}</span>`).join(' '):'<span style="color:var(--muted)">—</span>';
    const ws=worthScore??'—';
    const wb=typeof ws==='number'?`<span class="worth-bg"><span class="worth-fill" style="width:${ws}%"></span></span>`:'';
    return`<tr class="${rc}">
      <td class="cmp-td" style="font-weight:700">${esc(stage.name)}</td>
      <td class="cmp-td"><span class="diff-badge ${dc}">${jdiff(stage.difficulty)}</span></td>
      <td class="cmp-td">${ch}</td>
      <td class="cmp-td" style="text-align:right;white-space:nowrap;${isMulti?'':'display:none'}"><span class="num" style="font-weight:700;color:#818cf8">${ws}</span>${wb}</td>
      <td class="cmp-td num" style="text-align:right;font-weight:${bE?700:400};color:#4ade80">${fmt(avg.avgExpPerSec)}</td>
      <td class="cmp-td num" style="text-align:right;font-weight:${bG?700:400};color:#fcd34d">${fmt(avg.avgGoldPerSec)}</td>
      <td class="cmp-td num" style="text-align:right;color:var(--muted)">${avg.count}</td>
      <td class="cmp-td num" style="text-align:right;color:var(--muted)">${fmt(avg.avgTime,1)}s</td>
    </tr>`;
  }).join('');
}

function renderStage(stage){
  const avg=calcStageAvg(stage),dc=DIFF_CLS[stage.difficulty]||'d-normal';
  const _th=document.body.classList.contains('lang-th');
  const opts=DIFFICULTIES.map(d=>`<option value="${d}" data-en="${d}" data-th="${DIFF_TH[d]||d}" ${stage.difficulty===d?'selected':''}>${_th?(DIFF_TH[d]||d):d}</option>`).join('');
  const runs=stage.runs.map((run,idx)=>{
    const res=calcRun(run),ts=fmtTs(run.recordedAt),sid=stage.id,rid=run.id;
    return`<div class="card-run">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:11px">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span style="font-size:12px;font-weight:700;color:var(--purple)">รัน #${idx+1}</span>
          <span id="comp-badge-${rid}">${run.comp?`<span class="comp-badge">${esc(run.comp)}</span>`:''}</span>
          ${ts?`<span class="ts-label">${ts}</span>`:''}
        </div>
        <button class="del" title="ลบรัน" onclick="removeRun(${sid},${rid})">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="run-groups" style="display:grid;grid-template-columns:5fr 5fr 3fr 3fr;gap:8px;align-items:start">
        <div class="grp grp-exp"><span class="grp-title">EXP</span>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
            <div><label class="grp-lbl">เริ่ม</label><input type="number" class="ctrl" placeholder="0" value="${esc(run.startExp)}" data-fk="s${sid}r${rid}fstartExp" oninput="updateField(${sid},${rid},'startExp',this.value)"></div>
            <div><label class="grp-lbl">จบ</label><input type="number" class="ctrl" placeholder="0" value="${esc(run.endExp)}" data-fk="s${sid}r${rid}fendExp" oninput="updateField(${sid},${rid},'endExp',this.value)"></div>
          </div></div>
        <div class="grp grp-gold"><span class="grp-title">Gold</span>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
            <div><label class="grp-lbl">เริ่ม</label><input type="number" class="ctrl" placeholder="0" value="${esc(run.startGold)}" data-fk="s${sid}r${rid}fstartGold" oninput="updateField(${sid},${rid},'startGold',this.value)"></div>
            <div><label class="grp-lbl">จบ</label><input type="number" class="ctrl" placeholder="0" value="${esc(run.endGold)}" data-fk="s${sid}r${rid}fendGold" oninput="updateField(${sid},${rid},'endGold',this.value)"></div>
          </div></div>
        <div class="grp grp-time"><span class="grp-title">เวลา</span>
          <label class="grp-lbl">วินาที (s)</label>
          <input type="number" class="ctrl" placeholder="0" value="${esc(run.time)}" data-fk="s${sid}r${rid}ftime" oninput="updateField(${sid},${rid},'time',this.value)">
          <div id="time-fmt-${rid}" class="num" style="font-size:11px;color:var(--blue);margin-top:4px;min-height:14px">${run.time?fmtSec(+run.time):''}</div>
        </div>
        <div class="grp grp-comp"><span class="grp-title">ทีม</span>
          <label class="grp-lbl">Composition</label>
          <input type="text" class="ctrl" placeholder="Tank+Mage" value="${esc(run.comp)}" list="comp-list" data-fk="s${sid}r${rid}fcomp" oninput="updateField(${sid},${rid},'comp',this.value)">
        </div>
      </div>
      <div id="pills-${rid}" style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
        ${res?`<div class="pill-e">EXP <strong class="num">${fmtInt(res.gainedExp)}</strong> &rarr; <strong class="num">${fmt(res.expPerSec)}/s</strong></div>
               <div class="pill-g">Gold <strong class="num">${fmtInt(res.gainedGold)}</strong> &rarr; <strong class="num">${fmt(res.goldPerSec)}/s</strong></div>`:''}
      </div>
    </div>`;
  }).join('');

  return`<div class="card-stage" draggable="true"
    ondragstart="onDragStart(event,${stage.id})" ondragend="onDragEnd(event)"
    ondragover="onDragOver(event,${stage.id})" ondragleave="onDragLeave(event)" ondrop="onDrop(event,${stage.id})">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:14px">
      <div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;flex:1;min-width:0">
        <div class="drag-handle" title="ลากเพื่อสลับตำแหน่ง">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="9" cy="6" r="1.5"/><circle cx="15" cy="6" r="1.5"/><circle cx="9" cy="12" r="1.5"/><circle cx="15" cy="12" r="1.5"/><circle cx="9" cy="18" r="1.5"/><circle cx="15" cy="18" r="1.5"/></svg>
        </div>
        <select class="ctrl" style="width:110px;font-weight:700;font-size:14px" onchange="updateStageName(${stage.id},this.value)">${stageSelectHtml(stage.name)}</select>
        <select class="ctrl" style="width:130px" onchange="updateDifficulty(${stage.id},this.value)">${opts}</select>
        <span class="diff-badge ${dc}">${jdiff(stage.difficulty)}</span>
        <div id="stage-avg-${stage.id}" style="display:flex;gap:7px;flex-wrap:wrap">
          ${avg?`<span class="chip" style="color:#4ade80">EXP <strong class="num">${fmt(avg.avgExpPerSec)}/s</strong></span>
                 <span class="chip" style="color:#fcd34d">Gold <strong class="num">${fmt(avg.avgGoldPerSec)}/s</strong></span>
                 <span class="chip" style="color:var(--muted)">${avg.count} รัน</span>`:''}
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
        <button class="btn btn-green" onclick="addRun(${stage.id})">+ เพิ่มรัน</button>
        <button class="del del-lg" title="ลบด่าน" onclick="removeStage(${stage.id})">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>
    ${runs}
  </div>`;
}

function exportData(){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({stages,stageIdCounter},null,2)],{type:'application/json'}));a.download='tbh-stages.json';a.click();}
function importData(){document.getElementById('import-file').click();}
function handleImport(e){
  const file=e.target.files[0];if(!file)return;
  const r=new FileReader();
  r.onload=ev=>{try{const d=JSON.parse(ev.target.result);if(!d?.stages)throw 0;stages=d.stages;stageIdCounter=d.stageIdCounter||stages.reduce((m,s)=>Math.max(m,s.id),0);renderAll();save();}catch{showAlert({title:'นำเข้าไม่สำเร็จ',msg:'ไฟล์ JSON ไม่ถูกต้อง'});}};
  r.readAsText(file);e.target.value='';
}

// ── Equipment ─────────────────────────────────────────────────────────────────
const CLASS_MAP = {
  SWORD:'Knight', SHIELD:'Knight',
  BOW:'Ranger',   ARROW:'Ranger',
  STAFF:'Sorcerer', ORB:'Sorcerer',
  SCEPTER:'Priest', TOME:'Priest',
  CROSSBOW:'Hunter', BOLT:'Hunter',
  AXE:'Slayer',   HATCHET:'Slayer',
};
const GEAR_TYPES_BY_SLOT = {
  Weapon:['SWORD','BOW','STAFF','SCEPTER','CROSSBOW','AXE'],
  Offhand:['SHIELD','ARROW','ORB','TOME','BOLT','HATCHET'],
  Armor:['HELMET','ARMOR','GLOVES','BOOTS'],
  Accessory:['AMULET','EARING','RING','BRACER'],
};
let gearSlotSet=new Set(), gearGradeSet=new Set(), gearFilterLevel=0, gearTypeSet=new Set(), gearFilterQ='';

// Populate gear type buttons based on selected slot — grouped when showing all
function updateGearTypeButtons() {
  const group = document.getElementById('gear-type-group');
  const singleSlot = gearSlotSet.size === 1 ? [...gearSlotSet][0] : null;
  // lazy build class → portrait icon map (HEROES_DATA ประกาศทีหลังในไฟล์ จึงสร้างตอนเรียกครั้งแรก)
  if(!window.CLASS_ICON){ window.CLASS_ICON={}; (typeof HEROES_DATA!=='undefined'?HEROES_DATA:[]).forEach(h=>{ window.CLASS_ICON[h.class]=h.icon; }); }

  if (singleSlot) {
    const slotTypes = GEAR_TYPES_BY_SLOT[singleSlot] || [];
    for(const t of [...gearTypeSet]) { if(!slotTypes.includes(t)) gearTypeSet.delete(t); }
    const btns = [`<button class="pill${gearTypeSet.size===0?' active':''}" data-gf="type" data-gv="" onclick="setGearFilter(this)">${jbi({e:'All',t:'ทั้งหมด'})}</button>`];
    slotTypes.forEach(t => btns.push(gearTypeBtn(t)));
    group.innerHTML = `<div class="filter-group" style="flex-wrap:wrap">
      <span class="filter-label">Type</span>${btns.join('')}
    </div>`;
  } else {
    const allTypes = Object.values(GEAR_TYPES_BY_SLOT).flat();
    for(const t of [...gearTypeSet]) { if(!allTypes.includes(t)) gearTypeSet.delete(t); }
    const allBtn = `<button class="pill${gearTypeSet.size===0?' active':''}" data-gf="type" data-gv="" onclick="setGearFilter(this)">${jbi({e:'All',t:'ทั้งหมด'})}</button>`;
    const SLOT_LABELS = {
      Weapon:'⚔ '+jbi({e:'Weapon',t:'อาวุธหลัก'}),
      Offhand:'🛡 '+jbi({e:'Offhand',t:'อาวุธรอง'}),
      Armor:'🧥 '+jbi({e:'Armor',t:'เกราะ'}),
      Accessory:'💍 '+jbi({e:'Accessory',t:'เครื่องประดับ'}),
    };
    const groups = Object.entries(GEAR_TYPES_BY_SLOT).map(([slot, types]) => {
      const typeBtns = types.map(gearTypeBtn).join('');
      return `<div class="filter-group" style="flex-wrap:wrap">
        <span class="filter-label type-slot-lbl">${SLOT_LABELS[slot]||slot}</span>${typeBtns}
      </div>`;
    }).join('');
    group.innerHTML = `<div class="filter-group"><span class="filter-label">Type</span>${allBtn}</div>${groups}`;
  }
}

// ปุ่ม filter ตาม gear type — อาวุธหลัก/รอง แสดงชื่ออาชีพ + รูปอาชีพ (จากหน้า Skills); ที่เหลือแสดงแค่ชนิด
function gearTypeBtn(t) {
  const active = gearTypeSet.has(t) ? ' active' : '';
  const cls = CLASS_MAP[t];
  if (cls) {
    const icon = (window.CLASS_ICON||{})[cls];
    const img = icon ? `<img class="type-portrait" src="${esc(icon)}" alt="" onerror="this.style.display='none'">` : '';
    return `<button class="pill type-pill with-portrait${active}" data-gf="type" data-gv="${t}" onclick="setGearFilter(this)">${img}<span class="type-txt">${jbi({e:cls,t:(CLASS_TH[cls]||cls)})}<span class="type-class">${jbi({e:t,t:(GEARTYPE_TH[t]||t)})}</span></span></button>`;
  }
  // เกราะ/เครื่องประดับ: ใช้ไอคอนชนิด gear (item ฐาน) เป็นรูปตัวแทน
  const tIcon = (typeof GEARTYPE_ICON!=='undefined' ? GEARTYPE_ICON[t] : '');
  const tImg = tIcon ? `<img class="type-portrait type-portrait-sq" src="${esc(tIcon)}" alt="" onerror="this.style.display='none'">` : '';
  return `<button class="pill type-pill with-portrait${active}" data-gf="type" data-gv="${t}" onclick="setGearFilter(this)">${tImg}<span class="type-txt">${jbi({e:t,t:(GEARTYPE_TH[t]||t)})}</span></button>`;
}

function setGearFilter(btn) {
  const f=btn.dataset.gf, v=btn.dataset.gv;
  if(f==='level') {
    document.querySelectorAll('[data-gf="level"]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    gearFilterLevel=+v;
  } else {
    const s = f==='slot' ? gearSlotSet : f==='grade' ? gearGradeSet : gearTypeSet;
    if(!v) { s.clear(); }
    else { if(s.has(v)) s.delete(v); else s.add(v); }
    document.querySelectorAll(`[data-gf="${f}"]`).forEach(b => {
      const bv=b.dataset.gv;
      b.classList.toggle('active', !bv ? s.size===0 : s.has(bv));
    });
    if(f==='slot') updateGearTypeButtons();
  }
  applyGearFilter();
}

document.querySelectorAll('[data-gf]').forEach(btn => {
  btn.addEventListener('click', () => setGearFilter(btn));
});

let gearUniqueOnly = false;
function toggleGearUnique() {
  gearUniqueOnly = !gearUniqueOnly;
  document.getElementById('gear-unique-btn').classList.toggle('active', gearUniqueOnly);
  applyGearFilter();
}

function applyGearFilter() {
  gearFilterQ = (document.getElementById('gear-search')?.value||'').toLowerCase();
  const LEG_PLUS = ['LEGENDARY','IMMORTAL','ARCANA','BEYOND','CELESTIAL','DIVINE','COSMIC'];
  const filtered = GEAR_DATA.filter(g => {
    if(gearSlotSet.size  && !gearSlotSet.has(g.sl))  return false;
    if(gearGradeSet.size) { if(!gearGradeSet.has(g.gr)) return false; }
    else { if(!LEG_PLUS.includes(g.gr)) return false; }
    if(gearFilterLevel && g.lv !== gearFilterLevel)  return false;
    if(gearTypeSet.size  && !gearTypeSet.has(g.gt))   return false;
    if(gearUniqueOnly && !g.uk) return false;
    if(gearFilterQ && !(g.n+' '+(g.nb?g.nb.t:'')).toLowerCase().includes(gearFilterQ) && !(g.um||'').toLowerCase().includes(gearFilterQ)) return false;
    return true;
  });
  renderGearItems(filtered);
}

function renderGearItems(list) {
  const grid = document.getElementById('gear-grid');
  const countEl = document.getElementById('gear-count');
  countEl.textContent = list.length;
  if(!list.length) {
    grid.innerHTML = '<div class="empty-state"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:.3;margin-bottom:10px"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><p>ไม่พบ gear ที่ตรงกัน</p></div>';
    return;
  }

  grid.innerHTML = list.map(g => {
    const baseHtml = g.bs.length ? `
      <div class="gear-card-base">
        <div class="gear-section-lbl">Base Stats</div>
        ${g.bs.map(s=>`<div class="gear-stat-row"><span class="gear-stat-name">${jbi(s.label)}</span><span class="gear-stat-val">${esc(s.value)}</span></div>`).join('')}
      </div>` : '';

    const inhHtml = g.ih.length ? `
      <div class="gear-card-base">
        <div class="gear-section-lbl">Inherent</div>
        ${g.ih.map(s=>`<div class="gear-stat-row"><span class="gear-stat-name">${jbi(s.label)}</span><span class="gear-stat-val green">${esc(s.value)}</span></div>`).join('')}
      </div>` : '';

    const umHtml = g.um ? `<div class="unique-badge">&#10022; ${esc(g.um)}</div>` : '';

    return `<article class="card" style="cursor:default;border-left:3px solid ${g.co}">
      <div class="card-hd">
        <div class="icon-wrap"><img class="item-icon" src="${esc(g.ic)}" alt="${esc(g.n)}" loading="lazy" onerror="this.style.visibility='hidden'"></div>
        <div class="card-meta">
          <span class="item-name" style="color:${g.co}">${jbi(g.nb||g.n)}</span>
          <div class="card-tags">
            <span class="tag-grade" style="color:${g.co};border-color:${g.co}55;background:${g.co}30">${jbi({e:g.gr.charAt(0)+g.gr.slice(1).toLowerCase(), t:(GRADE_TH[g.gr]||g.gr)})}</span>
            <span class="tag-type">${jbi({e:g.gt, t:(GEARTYPE_TH[g.gt]||g.gt)})}</span>
            <span class="tag-type">Lv.${g.lv}</span>
          </div>
          ${g.pr ? `<div class="price-row"><span class="price-val">${esc(g.pr)}</span>${g.pv?`<span class="price-vol"><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> ${esc(g.pv)} sold</span>`:''}</div>` : ''}
        </div>
        <a class="steam-btn" href="${esc(g.su)}" target="_blank" rel="noopener" title="Steam Market">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V9c0-2.08 1.67-3.77 3.75-3.77 2.08 0 3.77 1.69 3.77 3.77s-1.69 3.77-3.77 3.77h-.087l-4.08 2.905c0 .052.004.103.004.154 0 1.56-1.258 2.826-2.818 2.826-1.364 0-2.504-.97-2.774-2.252L.189 14.4C1.179 19.836 6.016 24 11.979 24c6.627 0 12-5.373 12-12S18.606 0 11.979 0z"/></svg>
        </a>
      </div>
      <div class="card-stats">${baseHtml}${inhHtml}${umHtml}</div>
    </article>`;
  }).join('');
}

// ── Crafting ──────────────────────────────────────────────────────────────────
// ── Crafting data ──
let craftInitDone = false, craftFilter = '';

function initCraft() {
  if (craftInitDone) return;
  craftInitDone = true;
  renderCraft();
}
function setCraftFilter(btn) {
  craftFilter = btn.dataset.cf;
  document.querySelectorAll('[data-cf]').forEach(b => b.classList.toggle('active', b === btn));
  renderCraft();
}
function renderCraft() {
  const grid = document.getElementById('craft-grid');
  const list = CRAFT_DATA.filter(r => !craftFilter || r.type === craftFilter);
  document.getElementById('craft-count').textContent = list.length;
  grid.innerHTML = list.map(r => {
    const i = CRAFT_DATA.indexOf(r);
    const total = r.mats.reduce((s,m) => s + m.price * m.count, 0);
    const anyMissing = r.mats.some(m => !m.price);
    const matRows = r.mats.map(m => {
      const line = m.price * m.count;
      const gc = GRADE_HEX[m.grade] || '#94a3b8';
      const priceTxt = m.price ? '฿' + line.toFixed(2) : '—';
      return `<div class="craft-mat">
        <img class="craft-mat-icon" src="${esc(m.icon)}" alt="" style="border-color:${gc}55" onerror="this.style.opacity='.2'">
        <span class="craft-mat-name">${jbi(m.name)}</span>
        <span class="craft-mat-x">×${m.count}</span>
        <span class="craft-mat-price">${priceTxt}</span>
        ${m.su ? `<a class="craft-mat-buy" href="${esc(m.su)}" target="_blank" rel="noopener" title="Steam Market"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V9c0-2.08 1.67-3.77 3.75-3.77 2.08 0 3.77 1.69 3.77 3.77s-1.69 3.77-3.77 3.77h-.087l-4.08 2.905c0 .052.004.103.004.154 0 1.56-1.258 2.826-2.818 2.826-1.364 0-2.504-.97-2.774-2.252L.189 14.4C1.179 19.836 6.016 24 11.979 24c6.627 0 12-5.373 12-12S18.606 0 11.979 0z"/></svg></a>` : ''}
      </div>`;
    }).join('');
    const oddsBar = r.odds.map(o => `<div style="flex:${o.pct};background:${GRADE_HEX[o.g]||'#94a3b8'}"></div>`).join('');
    const oddsList = r.odds.map(o => `<span class="craft-odd"><span class="craft-odd-dot" style="background:${GRADE_HEX[o.g]||'#94a3b8'}"></span>${jbi({e:o.g.charAt(0)+o.g.slice(1).toLowerCase(), t:(GRADE_TH[o.g]||o.g)})} <span class="craft-odd-pct" style="color:${GRADE_HEX[o.g]||'#94a3b8'}">${o.pct}%</span></span>`).join('');
    return `<div class="craft-card">
      <div class="craft-hd">
        <div>
          <div class="craft-title">${jbi(r.type_bi)} <span style="color:var(--muted);font-weight:400">Lv.${r.lvMin}${r.lvMax!==r.lvMin?'-'+r.lvMax:''}</span></div>
          <div class="craft-sub">${jbi({e:'Tier',t:'เทียร์'})} ${r.tier} · ${r.mats.length} <span class="en">materials</span><span class="th">วัตถุดิบ</span></div>
        </div>
        <span class="craft-tier">T${r.tier}</span>
      </div>
      <div class="craft-mats">${matRows}</div>
      <div class="craft-total">
        <span class="craft-total-lbl">${jbi({e:'Total',t:'รวม'})}</span>
        <span class="craft-total-val">${total>0?'฿'+total.toFixed(2):'—'}${anyMissing&&total>0?'<span style="font-size:10px;color:var(--muted)"> +?</span>':''}</span>
      </div>
      <div class="craft-odds">
        <div class="craft-odds-lbl">${jbi({e:'Result chance',t:'โอกาสได้'})}</div>
        <div class="craft-odds-bar">${oddsBar}</div>
        <div class="craft-odds-list">${oddsList}</div>
      </div>
      ${r.poss && r.poss.length ? `<button class="craft-poss-btn" onclick="openCraftPossible(${i})">&#128230; ${jbi({e:'Possible items',t:'ของที่อาจได้'})} (${r.poss.length})</button>` : ''}
    </div>`;
  }).join('');
}

function openCraftPossible(i) {
  const r = CRAFT_DATA[i];
  if (!r) return;
  const grid = r.poss.map(it => {
    const stats = [...(it.bs||[]).map(s=>['',s]), ...(it.ih||[]).map(s=>['green',s])];
    const statRows = stats.map(([cls,s]) => `<div class="cposs-stat"><span>${jbi(s.label)}</span><span class="cposs-stat-v ${cls}">${esc(s.value)}</span></div>`).join('');
    const pr = it.pr || [];
    // cheapest price as a chip on the collapsed row
    const cheapest = pr.length ? pr.reduce((a,b) => parseFloat(b.p.replace(/[^\d.]/g,''))<parseFloat(a.p.replace(/[^\d.]/g,''))?b:a) : null;
    const priceChip = cheapest ? `<span class="cposs-price">${esc(cheapest.p)}+</span>` : '';
    const priceRows = pr.map(x => `<a class="cposs-pr" href="${esc(x.su)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">
      <span class="grade-dot" style="background:${GRADE_HEX[x.g]||'#94a3b8'};margin-right:5px"></span>
      <span style="flex:1;color:${GRADE_HEX[x.g]||'#94a3b8'}">${jbi({e:x.g.charAt(0)+x.g.slice(1).toLowerCase(), t:(GRADE_TH[x.g]||x.g)})}</span>
      <span class="cposs-pr-v">${esc(x.p)}</span>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="#66c0f4" style="margin-left:5px;flex-shrink:0"><path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V9c0-2.08 1.67-3.77 3.75-3.77 2.08 0 3.77 1.69 3.77 3.77s-1.69 3.77-3.77 3.77h-.087l-4.08 2.905c0 .052.004.103.004.154 0 1.56-1.258 2.826-2.818 2.826-1.364 0-2.504-.97-2.774-2.252L.189 14.4C1.179 19.836 6.016 24 11.979 24c6.627 0 12-5.373 12-12S18.606 0 11.979 0z"/></svg>
    </a>`).join('');
    const hasDetail = statRows || priceRows;
    return `<div class="cposs-item${hasDetail?' has-stat':''}" onclick="this.classList.toggle('open')">
      <div class="cposs-row">
        <img class="cposs-icon" src="${esc(it.ic)}" alt="" onerror="this.style.opacity='.2'">
        <span class="cposs-name">${jbi(it.n)}</span>
        ${priceChip}
        ${hasDetail?'<span class="cposs-caret">▾</span>':''}
      </div>
      ${hasDetail?`<div class="cposs-stats">${statRows}${priceRows?`<div class="cposs-prlbl">${jbi({e:'Market price',t:'ราคาตลาด'})}</div>${priceRows}`:''}</div>`:''}
    </div>`;
  }).join('');
  document.getElementById('skill-detail-box').innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
      <div>
        <div style="font-size:1.05rem;font-weight:800;color:#f1f5f9">${jbi(r.type_bi)} <span style="color:var(--muted);font-weight:400">Lv.${r.lvMin}${r.lvMax!==r.lvMin?'-'+r.lvMax:''}</span></div>
        <div style="font-size:11px;color:var(--muted);margin-top:3px">${jbi({e:'Possible items',t:'ของที่อาจได้'})} · ${r.poss.length} ${jbi({e:'(grade by chance above)',t:'(เกรดสุ่มตามโอกาส)'})}</div>
      </div>
      <button onclick="document.getElementById('skill-detail-ov').classList.remove('show')"
        style="background:var(--surf2);border:1px solid var(--border);color:var(--muted);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0">✕</button>
    </div>
    <div class="cposs-grid">${grid}</div>`;
  document.getElementById('skill-detail-ov').classList.add('show');
}

// ── Stages ────────────────────────────────────────────────────────────────────
// ── Stages data ──
let stagesInitDone = false;
let curAct = 1, curDiff = 'NORMAL';

const DIFF_META = {
  NORMAL:    {label:'Normal',    color:'#93c5fd'},
  NIGHTMARE: {label:'Nightmare', color:'#c4b5fd'},
  HELL:      {label:'Hell',      color:'#fdba74'},
  TORMENT:   {label:'Torment',   color:'#fda4af'},
};
const ACT_BG = {
  1: 'https://taskbarhero.wiki/game/ui/Act1_Bg.png',
  2: 'https://taskbarhero.wiki/game/ui/Act2_Bg.png',
  3: 'https://taskbarhero.wiki/game/ui/Act3_Bg.png',
};
const DIFF_PREFIX = {NORMAL:1, NIGHTMARE:2, HELL:3, TORMENT:4};

function initStages() {
  if (stagesInitDone) return;
  stagesInitDone = true;

  // Build stage lookup {key: stage}
  window.STAGE_MAP = {};
  STAGES_DATA.forEach(s => { STAGE_MAP[s.key] = s; });

  renderStageTable();
}

const DIFF_ABBR = {NORMAL:'N', NIGHTMARE:'NM', HELL:'H', TORMENT:'T'};

function renderStageTable() {
  const grid = document.getElementById('stage-acts-grid');
  grid.innerHTML = '';

  [1,2,3].forEach(act => {
    const col = document.createElement('div');
    col.className = 'stage-act-col';
    col.innerHTML = `<div class="stage-act-hd">ACT ${act}</div>`;

    for (let no = 1; no <= 10; no++) {
      const normalKey = 1000 + act * 100 + no;
      const s = STAGE_MAP[normalKey];
      if (!s) continue;
      const isBoss = s.type === 'ACTBOSS';

      const lvBadges = Object.entries(DIFF_META).map(([diff, meta]) => {
        const key = DIFF_PREFIX[diff] * 1000 + act * 100 + no;
        const st = STAGE_MAP[key];
        return st ? `<span class="sr-lv-badge" style="color:${meta.color};background:${meta.color}18;border:1px solid ${meta.color}44">${DIFF_ABBR[diff]}·${st.level}</span>` : '';
      }).join('');

      const row = document.createElement('div');
      row.className = 'stage-row' + (isBoss ? ' boss-row' : '');
      row.innerHTML = `
        <span class="sr-id">${act}-${no}</span>
        <span class="sr-name${isBoss?' boss':''}">${isBoss?'★ ':''}${jbi(s.name_bi||s.name)}</span>
        <span class="sr-levels">${lvBadges}</span>`;
      row.onclick = () => showStageDetail(s, DIFF_META.NORMAL.color);
      col.appendChild(row);
    }
    grid.appendChild(col);
  });

  document.getElementById('stage-detail-panel').innerHTML = '';
}

function showStageDetail(s, color) {
  const isBoss = s.type === 'ACTBOSS';
  document.getElementById('stage-detail-panel').innerHTML = `
    <div class="stage-detail-card" style="border-left:3px solid ${color}">
      <div class="stage-detail-hd">
        <div class="stage-detail-tag">
          <span class="badge" style="background:${color}22;color:${color};border:1px solid ${color}44">
            Act ${s.act}-${s.no}
          </span>
          ${isBoss ? '<span class="badge badge-supporter">Boss Stage</span>' : ''}
          <span class="badge" style="background:var(--surf2);color:var(--muted);border:1px solid var(--border)">
            Lv.${s.level}+
          </span>
        </div>
        <div class="stage-detail-name">${jbi(s.name_bi||s.name)}</div>
        <div class="stage-detail-sub">${s.waves!=null?`${s.waves} waves${s.perWave?` · ${s.perWave}/wave`:''} · `:''}${s.monsters?s.monsters.length:s.mobs||0} monster types</div>
      </div>
      ${diffTableHtml(s)}
      ${s.monsters && s.monsters.length ? `
      <div class="boss-section" style="flex-direction:column;align-items:flex-start;gap:8px">
        <div class="boss-label">Monsters (${s.monsters.length} types · ${s.perWave||'?'}/wave)</div>
        <div class="monster-grid">
          ${s.monsters.map(m => `
            <div class="monster-card">
              <img class="monster-portrait" src="${esc(m.portrait)}" alt="${esc(m.name.e)}" onerror="this.style.opacity='.2'">
              <div class="monster-name">${jbi(m.name)}</div>
            </div>`).join('')}
        </div>
      </div>` : ''}
      ${s.boss_name ? `
      <div class="boss-section">
        ${s.boss_portrait ? `<img class="boss-portrait" src="${esc(s.boss_portrait)}" alt="${esc(s.boss_name)}" onerror="this.style.opacity='.2'">` : ''}
        <div>
          <div class="boss-label">Stage Boss</div>
          <div class="boss-name">${jbi(s.boss_bi||s.boss_name)}</div>
        </div>
      </div>` : ''}
      ${lootBoxHtml(s.monsterBox, 'Monster Drops')}
      ${lootBoxHtml(s.bossBox, 'Boss Drops')}
    </div>`;
}

function fmtNum(n) {
  if (n == null) return '—';
  if (n >= 1e6) return (n/1e6).toFixed(n>=1e7?0:1)+'M';
  if (n >= 1e3) return (n/1e3).toFixed(n>=1e4?0:1)+'K';
  return n.toLocaleString('en');
}

function diffTableHtml(s) {
  // s = Normal stage; look up all difficulties by act/no
  const rows = Object.entries(DIFF_META).map(([diff, meta]) => {
    const key = DIFF_PREFIX[diff] * 1000 + s.act * 100 + s.no;
    const st = STAGE_MAP[key];
    if (!st) return '';
    return `<tr>
      <td style="padding:7px 10px;font-weight:700;color:${meta.color}">${jdiff(meta.label)}</td>
      <td style="padding:7px 10px;text-align:right;color:#cbd5e1" class="num">Lv.${st.level}</td>
      <td style="padding:7px 10px;text-align:right;color:#94a3b8" class="num">${st.kills!=null?fmtNum(st.kills):'—'}</td>
      <td style="padding:7px 10px;text-align:right;color:#4ade80;font-weight:700" class="num">${fmtNum(st.exp)}</td>
      <td style="padding:7px 10px;text-align:right;color:#fcd34d;font-weight:700" class="num">${fmtNum(st.gold)}</td>
    </tr>`;
  }).join('');
  return `<div style="padding:14px 18px;border-top:1px solid var(--border)">
    <div class="boss-label" style="margin-bottom:8px">EXP / Gold ต่อ clear (ตามระดับ)</div>
    <table style="width:100%;border-collapse:collapse;font-size:12px">
      <thead><tr style="border-bottom:1px solid var(--border)">
        <th style="padding:6px 10px;text-align:left;font-size:10px;color:var(--muted);font-weight:700">DIFFICULTY</th>
        <th style="padding:6px 10px;text-align:right;font-size:10px;color:var(--muted);font-weight:700">LEVEL</th>
        <th style="padding:6px 10px;text-align:right;font-size:10px;color:var(--muted);font-weight:700">KILLS</th>
        <th style="padding:6px 10px;text-align:right;font-size:10px;color:var(--muted);font-weight:700">EXP</th>
        <th style="padding:6px 10px;text-align:right;font-size:10px;color:var(--muted);font-weight:700">GOLD</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`;
}

const GRADE_HEX = {
  COMMON:'#c8cad6', UNCOMMON:'#54fc0c', RARE:'#4d9eff', LEGENDARY:'#fc9c0c',
  IMMORTAL:'#fc2424', ARCANA:'#c84dff', BEYOND:'#ff4d8f', CELESTIAL:'#6ccce4',
  DIVINE:'#fce454', COSMIC:'#fcfcfc',
};

function lootBoxHtml(box, label) {
  if (!box || !box.entries || !box.entries.length) return '';
  const color = GRADE_HEX[box.grade] || '#94a3b8';
  const maxPct = Math.max(...box.entries.map(e => e.pct), 1);
  const SHOW = 5;
  const rows = box.entries.map((e, i) => {
    const gc = GRADE_HEX[e.grade] || '#94a3b8';
    const thumb = e.icon
      ? `<img class="loot-item-icon" src="${esc(e.icon)}" alt="" onerror="this.style.opacity='.2'">`
      : `<span class="loot-item-ph" style="color:${gc};border-color:${gc}55;background:${gc}18">${e.grade?e.grade.charAt(0):'?'}</span>`;
    return `<div class="loot-row" data-extra="${i >= SHOW ? 1 : 0}" ${i >= SHOW ? 'style="display:none"' : ''}>
      ${thumb}
      <span class="loot-row-name">${jbi(e.name)}</span>
      <span class="loot-bar"><span class="loot-bar-fill" style="width:${(e.pct/maxPct*100).toFixed(0)}%;background:${color}"></span></span>
      <span class="loot-pct" style="color:${color}">${e.pct}%</span>
    </div>`;
  }).join('');
  const more = box.entries.length > SHOW
    ? `<div class="loot-more" onclick="toggleLoot(this)">+ ดูทั้งหมด (${box.entries.length})</div>` : '';
  return `<div class="loot-box">
    <div class="loot-hd">
      ${box.icon ? `<img class="loot-icon" src="${esc(box.icon)}" alt="" onerror="this.style.opacity='.2'">` : ''}
      <div>
        <div class="boss-label">${esc(label)}</div>
        <div style="display:flex;align-items:center;gap:6px;margin-top:3px">
          <span class="loot-box-name">${jbi(box.box_name)}</span>
          <span class="loot-grade" style="color:${color};border-color:${color}55;background:${color}22">${box.grade.charAt(0)+box.grade.slice(1).toLowerCase()}</span>
        </div>
      </div>
    </div>
    <div class="loot-list">${rows}</div>
    ${more}
  </div>`;
}

function toggleLoot(el) {
  const box = el.closest('.loot-box');
  const hidden = box.querySelectorAll('.loot-row[data-extra="1"]');
  const isHidden = hidden[0].style.display === 'none';
  hidden.forEach(r => r.style.display = isHidden ? '' : 'none');
  el.textContent = isHidden ? '− ย่อ' : `+ ดูทั้งหมด (${box.querySelectorAll('.loot-row').length})`;
}

// ── Rune Tree ─────────────────────────────────────────────────────────────────
// ── Rune data ──
let runeInitDone = false;

function initRuneTree() {
  if (runeInitDone) return;
  runeInitDone = true;

  const vp    = document.getElementById('rune-vp');
  const world = document.getElementById('rune-world');
  const svg   = document.getElementById('rune-edges');
  const tt    = document.getElementById('rune-tt');
  if (!vp || !world) return;

  const NODE_SIZE = 36;
  let scale = 0.48, ox = 40, oy = 40;

  // Build node lookup
  const nodeMap = {};
  RUNE_NODES.forEach(n => nodeMap[n.key] = n);

  // Draw SVG edges
  svg.innerHTML = RUNE_EDGES.map(e => {
    const a = nodeMap[e.from], b = nodeMap[e.to];
    if (!a || !b) return '';
    return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>`;
  }).join('');

  // Create node divs
  window.runeNodeDivs = [];
  RUNE_NODES.forEach(n => {
    const div = document.createElement('div');
    div.className = 'rune-node';
    div.style.left  = n.x + 'px';
    div.style.top   = n.y + 'px';
    div.style.borderColor = n.color;
    div.dataset.search = (n.name + ' ' + (n.effect||'') + ' ' + (n.name_bi?n.name_bi.t:'') + ' ' + (n.effect_bi?n.effect_bi.t:'')).toLowerCase();
    window.runeNodeDivs.push(div);
    if (n.icon) {
      const img = document.createElement('img');
      img.src = n.icon;
      img.alt = n.name;
      div.appendChild(img);
    }
    div.addEventListener('mouseenter', ev => showRuneTT(ev, n));
    div.addEventListener('mouseleave', () => { tt.classList.remove('show'); });
    div.addEventListener('click', () => openRuneDetail(n));
    world.appendChild(div);
  });

  applyRuneTransform();

  // Pan
  let drag = false, lx = 0, ly = 0;
  vp.addEventListener('mousedown', e => { drag=true; lx=e.clientX; ly=e.clientY; vp.classList.add('dragging'); });
  window.addEventListener('mousemove', e => {
    if (!drag) return;
    ox += e.clientX - lx; oy += e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    applyRuneTransform();
  });
  window.addEventListener('mouseup', () => { drag=false; vp.classList.remove('dragging'); });

  // Touch pan
  let touch0 = null;
  vp.addEventListener('touchstart', e => { if(e.touches.length===1){ touch0={x:e.touches[0].clientX,y:e.touches[0].clientY}; } }, {passive:true});
  vp.addEventListener('touchmove', e => {
    if(e.touches.length===1 && touch0){
      ox+=e.touches[0].clientX-touch0.x; oy+=e.touches[0].clientY-touch0.y;
      touch0={x:e.touches[0].clientX,y:e.touches[0].clientY};
      applyRuneTransform();
    }
  }, {passive:true});

  // Zoom
  vp.addEventListener('wheel', e => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    const rect = vp.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    ox = mx - (mx - ox) * factor;
    oy = my - (my - oy) * factor;
    scale = Math.max(0.2, Math.min(3, scale * factor));
    applyRuneTransform();
  }, {passive:false});

  function applyRuneTransform() {
    world.style.transform = `translate(${ox}px,${oy}px) scale(${scale})`;
  }

  window.runeZoom = function(f) {
    const rect = vp.getBoundingClientRect();
    const cx = rect.width/2, cy = rect.height/2;
    ox = cx - (cx - ox) * f; oy = cy - (cy - oy) * f;
    scale = Math.max(0.2, Math.min(3, scale * f));
    applyRuneTransform();
  };
  window.runeReset = function() {
    scale = 0.48; ox = 40; oy = 40; applyRuneTransform();
  };
}

function filterRunes(q) {
  q = (q || '').trim().toLowerCase();
  const divs = window.runeNodeDivs || [];
  const countEl = document.getElementById('rune-match-count');
  if (!q) {
    divs.forEach(d => { d.classList.remove('dimmed', 'hit'); });
    if (countEl) countEl.textContent = '';
    return;
  }
  let n = 0;
  divs.forEach(d => {
    const match = d.dataset.search.includes(q);
    d.classList.toggle('dimmed', !match);
    d.classList.toggle('hit', match);
    if (match) n++;
  });
  if (countEl) countEl.textContent = n ? `เจอ ${n}` : 'ไม่พบ';
}

function showRuneTT(ev, n) {
  const tt = document.getElementById('rune-tt');
  const val = n.lv1val || '';
  const effect = jbiR(n.effect_bi || n.effect, txt => esc((txt||'').replace(/\{0\}/g, val)));
  const costFull = (n.cost||0).toLocaleString('en');
  tt.innerHTML = `<div class="rtt-name" style="color:${n.color}">${jbi(n.name_bi||n.name)}</div>
    ${effect ? `<div class="rtt-effect">${effect}</div>` : ''}
    ${n.cost ? `<div class="rtt-cost"><span class="en">Cost: ${costFull} coins</span><span class="th">ราคา: ${costFull} เหรียญ</span></div>` : ''}`;
  tt.style.left = (ev.clientX + 14) + 'px';
  tt.style.top  = (ev.clientY - 10) + 'px';
  tt.classList.add('show');
}

function openRuneDetail(n) {
  const val = n.lv1val || '';
  const effect = jbiR(n.effect_bi || n.effect, txt => esc(txt||'').replace(/\{0\}/g, `<strong style="color:${n.color}">${val}</strong>`));
  const costFull = (n.cost||0).toLocaleString('en');
  document.getElementById('skill-detail-box').innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:56px;height:56px;border-radius:10px;background:#0a101e;border:2px solid ${n.color};overflow:hidden;flex-shrink:0">
          ${n.icon ? `<img src="${esc(n.icon)}" style="width:100%;height:100%;object-fit:contain;image-rendering:pixelated">` : ''}
        </div>
        <div>
          <div style="font-size:1.1rem;font-weight:800;color:${n.color};margin-bottom:4px">${jbi(n.name_bi||n.name)}</div>
          <span class="badge" style="background:${n.color}22;color:${n.color};border:1px solid ${n.color}44">Lv ${n.maxLevel} max</span>
        </div>
      </div>
      <button onclick="document.getElementById('skill-detail-ov').classList.remove('show')"
        style="background:var(--surf2);border:1px solid var(--border);color:var(--muted);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0">✕</button>
    </div>
    ${effect ? `<div class="sd-desc">${effect}</div>` : ''}
    ${n.cost ? `<div class="sd-stats"><div class="sd-stat"><div class="sd-stat-lbl"><span class="en">Unlock Cost</span><span class="th">ราคาปลดล็อก</span></div><div class="sd-stat-val" style="color:var(--gold)"><span class="en">${costFull} coins</span><span class="th">${costFull} เหรียญ</span></div></div><div class="sd-stat"><div class="sd-stat-lbl"><span class="en">Max Level</span><span class="th">เลเวลสูงสุด</span></div><div class="sd-stat-val">${n.maxLevel}</div></div></div>` : ''}
  `;
  document.getElementById('skill-detail-ov').classList.add('show');
}

// ── Skills ────────────────────────────────────────────────────────────────────
// ── Skills data ──
let activeHeroKey = null;

function initSkills() {
  const nav = document.getElementById('hero-nav');
  if (!nav || nav.children.length) return;
  HEROES_DATA.forEach((h, i) => {
    const btn = document.createElement('button');
    btn.className = 'hero-btn' + (i === 0 ? ' active' : '');
    btn.dataset.hkey = h.key;
    btn.style.setProperty('--hc', h.color);
    if (i === 0) { btn.style.background = h.color; btn.style.color = '#0a0a0a'; btn.style.borderColor = h.color; }
    btn.innerHTML = `<img class="hero-portrait" src="${esc(h.icon)}" alt="${esc(h.name)}" onerror="this.style.display='none'">${jbi(h.name_bi)}`;
    btn.onclick = () => switchHero(h.key);
    nav.appendChild(btn);
  });
  switchHero(HEROES_DATA[0].key);
}

function switchHero(key) {
  activeHeroKey = key;
  document.querySelectorAll('.hero-btn').forEach(b => {
    const h = HEROES_DATA.find(x => x.key === +b.dataset.hkey);
    const on = +b.dataset.hkey === key;
    b.classList.toggle('active', on);
    b.style.background    = on ? h.color : '';
    b.style.color         = on ? '#0a0a0a' : '';
    b.style.borderColor   = on ? h.color : '';
  });
  renderHeroSkills(key);
}

function fmtDmg(v) { if (!v) return '—'; const n = v / 100; return Number.isInteger(n) ? n + '%' : n.toFixed(1) + '%'; }

function renderHeroSkills(key) {
  const h = HEROES_DATA.find(x => x.key === key);
  if (!h) return;
  const el = document.getElementById('skills-content');
  if (!el) return;

  const dmgColors = { Physical:'#f87171', Fire:'#fb923c', Cold:'#67e8f9', Lightning:'#fde68a', Magic:'#c4b5fd', Heal:'#4ade80' };

  const activeCards = h.active.map(s => {
    const dmgCol = dmgColors[s.dmg_type] || '#94a3b8';
    const range = `${fmtDmg(s.lv1)}~${fmtDmg(s.lvmax)}`;  // Lv1→max ที่เล่นได้จริง
    const desc = jbiR(s.desc, txt => esc((txt||'').replace(/\{0\}/g, range)));
    const tags = [
      s.dmg_type ? `<span class="skill-tag" style="color:${dmgCol};border-color:${dmgCol}44;background:${dmgCol}18">${esc(s.dmg_type)}</span>` : '',
      s.delivery ? `<span class="skill-tag" style="color:var(--muted);border-color:var(--border)">${esc(s.delivery)}</span>` : '',
    ].filter(Boolean).join('');
    return `<div class="skill-card" style="border-left:3px solid ${h.color}" onclick="openSkillDetail(${s.key},${h.key})">
      <div class="skill-hd">
        <img class="skill-icon" src="${esc(s.icon)}" alt="${esc(s.name.e)}" onerror="this.style.opacity='.2'">
        <div>
          <div class="skill-name">${jbi(s.name)}</div>
          <div class="skill-tags">${tags}</div>
        </div>
      </div>
      ${desc ? `<div class="skill-desc">${desc}</div>` : ''}
      <div class="skill-dmg">
        <span style="font-size:11px;color:var(--muted);font-weight:600">${jbi(s.trigger)}</span>
        <span style="font-size:10px;color:var(--muted);font-style:italic">กดเพื่อดู detail</span>
      </div>
    </div>`;
  }).join('');

  const passiveCards = h.passive.map(p => {
    const valStr = p.mod === 'FLAT' ? `+${p.value}` : `+${p.value / 10}%`;
    return `<div class="passive-card" style="cursor:pointer" onclick="openPassiveDetail(${p.key},${h.key})">
      <img class="passive-icon" src="${esc(p.icon)}" alt="${esc(p.name.e)}" onerror="this.style.opacity='.2'">
      <div>
        <div class="passive-name">${jbi(p.name)}</div>
        <div class="passive-val">${valStr} <span class="en">per level</span><span class="th">ต่อเลเวล</span></div>
        ${p.desc ? `<div style="font-size:11px;color:var(--muted);margin-top:3px;line-height:1.5">${jbi(p.desc)}</div>` : ''}
      </div>
    </div>`;
  }).join('');

  el.innerHTML = `
    <div class="skills-section-lbl">Active Skills</div>
    <div class="skill-grid">${activeCards || '<p style="color:var(--muted)">ไม่มีข้อมูล</p>'}</div>
    <div class="skills-section-lbl">Passive Skills</div>
    <div class="passive-grid">${passiveCards || '<p style="color:var(--muted)">ไม่มีข้อมูล</p>'}</div>
  `;
}

function openSkillDetail(skillKey, heroKey) {
  const h = HEROES_DATA.find(x => x.key === heroKey);
  const s = h?.active.find(x => x.key === skillKey);
  if (!s) return;
  const dmgColors = {Physical:'#f87171',Fire:'#fb923c',Cold:'#67e8f9',Lightning:'#fde68a',Magic:'#c4b5fd',Heal:'#4ade80'};
  const dmgCol = dmgColors[s.dmg_type] || '#94a3b8';

  const range = `<strong style="color:${dmgCol}">${fmtDmg(s.lv1)}~${fmtDmg(s.lvmax)}</strong>`;  // Lv1→max ที่เล่นได้จริง
  const desc = jbiR(s.desc, txt => esc(txt||'').replace(/\{0\}/g, range));

  const tags = [
    s.dmg_type ? `<span class="skill-tag" style="color:${dmgCol};border-color:${dmgCol}44;background:${dmgCol}18">${esc(s.dmg_type)}</span>` : '',
    s.delivery ? `<span class="skill-tag" style="color:var(--muted);border-color:var(--border)">${esc(s.delivery)}</span>` : '',
  ].filter(Boolean).join('');

  const levelCells = (s.levels||[]).map(l => {
    const isCurMax = l.lv === s.max_lv;
    const isLocked = l.lv > s.max_lv;
    return `<div class="sd-lv${isCurMax?' max':''}${isLocked?' locked':''}">
      <div class="sd-lv-n">${isCurMax?'★':('Lv'+l.lv)}</div>
      <div class="sd-lv-v" style="${isLocked?'color:var(--muted)':isCurMax?'':('color:'+dmgCol)}">${fmtDmg(l.val)}</div>
    </div>`;
  }).join('');

  document.getElementById('skill-detail-box').innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div class="sd-hd" style="margin-bottom:0">
        <img class="sd-icon" src="${esc(s.icon)}" alt="${esc(s.name.e)}" onerror="this.style.opacity='.2'">
        <div>
          <div class="sd-title">${jbi(s.name)}</div>
          <div class="skill-tags">${tags}</div>
        </div>
      </div>
      <button onclick="document.getElementById('skill-detail-ov').classList.remove('show')"
        style="background:var(--surf2);border:1px solid var(--border);color:var(--muted);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0">✕</button>
    </div>
    ${desc ? `<div class="sd-desc">${desc}</div>` : ''}
    ${levelCells ? `<div class="sd-section-lbl"><span class="en">Damage per Level</span><span class="th">ดาเมจต่อเลเวล</span></div><div class="sd-levels">${levelCells}</div>` : ''}
    <div class="sd-section-lbl">Details</div>
    <div class="sd-stats">
      <div class="sd-stat"><div class="sd-stat-lbl">Trigger</div><div class="sd-stat-val">${jbi(s.trigger)}</div></div>
      <div class="sd-stat"><div class="sd-stat-lbl">Damage Type</div><div class="sd-stat-val" style="color:${dmgCol}">${esc(s.dmg_type||'—')}</div></div>
      <div class="sd-stat"><div class="sd-stat-lbl">Delivery</div><div class="sd-stat-val">${esc(s.delivery||'—')}</div></div>
      <div class="sd-stat"><div class="sd-stat-lbl">Class</div><div class="sd-stat-val" style="color:${h.color}">${jbi(h.name_bi)}</div></div>
    </div>
  `;
  document.getElementById('skill-detail-ov').classList.add('show');
}

function closeSkillDetail(e) {
  if (e.target === document.getElementById('skill-detail-ov'))
    document.getElementById('skill-detail-ov').classList.remove('show');
}

function openPassiveDetail(passiveKey, heroKey) {
  const h = HEROES_DATA.find(x => x.key === heroKey);
  const p = h?.passive.find(x => x.key === passiveKey);
  if (!p) return;
  const valStr = p.mod === 'FLAT' ? `+${p.value}` : `+${p.value/10}%`;
  const MAX_LV = p.max_lv || 10;
  const levelCells = Array.from({length: MAX_LV}, (_,i) => {
    const lv = i + 1;
    const total = p.mod === 'FLAT' ? `+${p.value * lv}` : `+${(p.value/10 * lv).toFixed(1)}%`;
    const isMax = lv === MAX_LV;
    return `<div class="sd-lv${isMax?' max':''}">
      <div class="sd-lv-n">Lv${lv}</div>
      <div class="sd-lv-v" style="${isMax?'':('color:var(--green)')}">${total}</div>
    </div>`;
  }).join('');

  document.getElementById('skill-detail-box').innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div class="sd-hd" style="margin-bottom:0">
        <img class="sd-icon" src="${esc(p.icon)}" alt="${esc(p.name.e)}" onerror="this.style.opacity='.2'">
        <div>
          <div class="sd-title">${jbi(p.name)}</div>
          <span class="badge badge-free" style="font-size:10px">Passive</span>
        </div>
      </div>
      <button onclick="document.getElementById('skill-detail-ov').classList.remove('show')"
        style="background:var(--surf2);border:1px solid var(--border);color:var(--muted);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0">✕</button>
    </div>
    ${p.desc ? `<div class="sd-desc">${jbi(p.desc)}</div>` : ''}
    <div class="sd-section-lbl"><span class="en">Bonus per Level</span><span class="th">โบนัสต่อเลเวล</span></div>
    <div class="sd-levels">${levelCells}</div>
    <div class="sd-section-lbl">Details</div>
    <div class="sd-stats">
      <div class="sd-stat"><div class="sd-stat-lbl">Stat</div><div class="sd-stat-val">${esc(p.stat||'—')}</div></div>
      <div class="sd-stat"><div class="sd-stat-lbl"><span class="en">Per Level</span><span class="th">ต่อเลเวล</span></div><div class="sd-stat-val" style="color:var(--green)">${valStr}</div></div>
      <div class="sd-stat"><div class="sd-stat-lbl">Type</div><div class="sd-stat-val">${esc(p.mod||'—')}</div></div>
      <div class="sd-stat"><div class="sd-stat-lbl">Class</div><div class="sd-stat-val" style="color:${h.color}">${esc(h.name)}</div></div>
    </div>
  `;
  document.getElementById('skill-detail-ov').classList.add('show');
}

// Init gear tab on first switch
let gearInitDone = false;
const _origSwitchTab = switchTab;
switchTab = function(btn) {
  _origSwitchTab(btn);
  if(btn.dataset.tab === 'gear' && !gearInitDone) {
    gearInitDone = true;
    updateGearTypeButtons();
    applyGearFilter();
  }
};

if(!load()){
  const now=new Date().toISOString();
  stages.push({id:++stageIdCounter,name:'3-9',difficulty:'Normal',runs:[{id:1,comp:'',startExp:'1660367',endExp:'2074913',startGold:'182584',endGold:'214582',time:'366',recordedAt:now}]});
  stages.push({id:++stageIdCounter,name:'3-8',difficulty:'Normal',runs:[{id:2,comp:'',startExp:'',endExp:'',startGold:'',endGold:'',time:'',recordedAt:now}]});
  stages.push({id:++stageIdCounter,name:'3-7',difficulty:'Normal',runs:[{id:3,comp:'',startExp:'1154186',endExp:'1458272',startGold:'153557',endGold:'172432',time:'319',recordedAt:now}]});
  save();
}
renderAll();
</script>
</body>
</html>"""

# ── Inject GEAR_DATA into JS (must be after JS raw string is defined) ─────────
JS_WITH_GEAR = JS.replace(
    '// ── Equipment ──',
    f'const GEAR_DATA={GEAR_JSON};\n// ── Equipment ──'
).replace(
    '// ── Skills data ──',
    f'const HEROES_DATA={HEROES_JSON};\n// ── Skills data ──'
).replace(
    '// ── Rune data ──',
    f'const RUNE_NODES={rune_nodes_json};\nconst RUNE_EDGES={rune_edges_json};\n// ── Rune data ──'
).replace(
    '// ── Stages data ──',
    f'const STAGES_DATA={stages_json};\n// ── Stages data ──'
).replace(
    '// ── Crafting data ──',
    f'const CRAFT_DATA={craft_json};\n// ── Crafting data ──'
).replace(
    '// ── Pet data ──',
    f'const PET_TH={PET_TH_JSON};\nconst MONSTER_TH={MONSTER_TH_JSON};\nconst STAGE_NAME_TH={STAGE_NAME_TH_JSON};\nconst GRADE_TH={GRADE_TH_JSON};\nconst GEARTYPE_TH={GEARTYPE_TH_JSON};\nconst GEARTYPE_ICON={GEARTYPE_ICON_JSON};\nconst CLASS_TH={CLASS_TH_JSON};\n// ── Pet data ──'
)

# ── Assemble & write ──────────────────────────────────────────────────────────
EFFECT_OPTIONS = ''.join(
    f'<div class="eff-opt" data-v="{_esc_min(s)}" onclick="pickEff(this)">{gb(s, _stat_th.get(s, s))}</div>'
    for s in ALL_STATS
)
TAB1_START_FILLED = TAB1_START.replace('__EFFECT_OPTIONS__', EFFECT_OPTIONS)
html = (HEAD + TOPBAR
        + TAB1_START_FILLED + str(COUNT) + TAB1_MID + CARDS_HTML + TAB1_END
        + TAB4 + TAB_CRAFT + TAB3 + TAB_STAGES + TAB6_RUNES + TAB5 + TAB2 + MODAL + JS_WITH_GEAR)

out = f'{BASE}/index.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Saved: {out} ({len(html)//1024}KB)')
