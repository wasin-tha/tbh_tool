# TBH Tools — Task Bar Hero ข้อมูลเกม (Thai/EN)

เว็บ single-page รวมเครื่องมือสำหรับเกม **Task Bar Hero (TBH)** บน Steam (appid `3678970`)
Deploy ที่ GitHub Pages: https://wasin-tha.github.io/tbh_tool/
Repo: https://github.com/wasin-tha/tbh_tool.git

## ⚠️ กฎสำคัญ
- **ห้าม `git commit`/`push` เองเด็ดขาด** จนกว่าผู้ใช้สั่ง (rebuild gen_tbh.py ได้เลย แต่หยุดรอสั่ง commit)
- **แปลภาษาไทยต้องอิงแหล่งจาก wiki/Steam เท่านั้น ห้ามแปลเอง** — ถ้าอันไหนไม่มีแหล่ง ให้ถามผู้ใช้ก่อน
- ตอบผู้ใช้เป็นภาษาไทย, font Noto Sans Thai

## โครงสร้าง / Build pipeline
**Source of truth คือ `gen_tbh.py`** — generate `index.html` ทั้งไฟล์ (~3000 บรรทัด, output ~3.5MB)
**ห้ามแก้ `index.html` ตรงๆ** — ต้องแก้ `gen_tbh.py` แล้ว rebuild

```
tbh_march/
  gen_tbh.py                  ← แก้ที่นี่เท่านั้น
  fetch_prices.py             ← ดึงราคา Steam Market (resume ได้, มี % + ETA)
  update_data.py              ← ดึง game data ใหม่จาก wiki + rebuild อัตโนมัติ
  tbh_*.json                  ← raw data (ดู Data sources)
  img/                        ← รูป pet (Bat.png, ...)
  index.html                  ← OUTPUT (generated — อย่าแก้มือ)
```

Build: `cd D:/Coding/other/tbh_march && python gen_tbh.py`

### Deploy (เมื่อผู้ใช้สั่งเท่านั้น)
git repo root คือ `D:/Coding/other` — ตอนนี้ **track ทั้ง source แล้ว** (gen_tbh.py, fetch_prices.py, tbh_*.json, .github/) เพื่อให้ GitHub Actions รันได้ (ยกเว้น `steam_cookie.txt` — .gitignore กันไว้)
```bash
cd D:/Coding/other
git pull origin main          # ★ ดึง auto-commit ราคาจาก Action ก่อนเสมอ ไม่งั้น push ชน
cp tbh_march/index.html index.html
git add index.html tbh_march/gen_tbh.py   # + ไฟล์ที่แก้ (★ อย่า add prices.json จากเครื่อง!)
git commit -m "..." && git push origin main
```
Co-Authored-By line: `Claude Opus 4.8 <noreply@anthropic.com>`

### ★ ราคาแยกออกจาก index.html (decoupled — กันราคาเก่าทับ)
- **`index.html` ไม่มีราคาอบอยู่** — โหลด `prices.json` ตอน runtime (fetch) แล้ว JS เติมราคา
- `gen_tbh.py` เขียน 2 ไฟล์: `index.html` (code) + `prices.json` (id → `{l,v}` + `_at`)
- **เครื่องเรา commit แค่ `index.html`** (code) — ห้าม add `prices.json` (จะพ่นราคาเก่าทับ)
- **Action เป็นเจ้าของ `prices.json`** คนเดียว (อัปเดตทุก ชม.) → ไม่มีทางชนกัน
- `root/prices.json` = ไฟล์ที่ serve (track ใน git); `tbh_march/prices.json` + `tbh_march/tbh_prices.json` = gitignore
- ⚠️ เปิด `file://` ตรงๆ ราคาไม่ขึ้น (browser บล็อก fetch local) — ต้องผ่าน http/Pages หรือ `python -m http.server`
- JS: `PRICES{}`, `priceNum(id)`, `priceRowInner(id)`, `fillPrices()`, `fmtPriceDate()` (เวลาไทยจาก `_at`)
- **★ auto-refresh ราคาในหน้าที่เปิดค้าง** (`loadPrices(announce)`): poll `prices.json` ทุก 10 นาที (เฉพาะ `visibilityState==='visible'`) + ดึงใหม่ตอน `visibilitychange` (กลับมาที่แท็บ) → อัปเฉพาะเมื่อ `_at` เปลี่ยน (ไม่งั้นไม่แตะ DOM) + toast เล็ก "ราคาอัปเดตแล้ว" (`showPriceToast`)

### GitHub Actions — อัปเดตราคาอัตโนมัติ (`.github/workflows/update-prices.yml`)
- trigger = **`workflow_dispatch`** ยิงจาก **cron-job.org ทุก 30 นาที** (ตรงเวลากว่า GitHub cron) + กด Run เองได้ (GitHub schedule comment ไว้ เปิดกลับได้)
- ทำ: fetch_prices.py → gen_tbh.py → cp `index.html`+`prices.json` ไป root → commit
- **Secrets ที่ต้องตั้งในหน้า GitHub** (ผมตั้งให้ไม่ได้): `STEAM_COOKIE` (steamLoginSecure), `DISCORD_WEBHOOK`
- ถ้า fail → **ยิง Discord เฉพาะเมื่อ fail 4 ครั้งติด** (เช็ค 3 run ก่อนหน้าผ่าน `gh api`, ต้องมี `permissions: actions:read`) — รอบเดียว/สองพังชั่วคราว (rate limit) ไม่เตือน
- Public repo = Actions ฟรีไม่จำกัด
- มี `update_prices.bat` (local, double-click) ทำงานเดียวกันบนเครื่อง — ใช้ **full path python** (เลี่ยง Store stub) + ต้องเป็น **CRLF**

## Data sources (taskbarhero.wiki)
WebFetch โดน 403 — ใช้ `curl -A "Mozilla/5.0"` หรือ `update_data.py`:
```
/data/items.json            → tbh_items.json (ชื่อ i18n/icon/grade/type/gear/level/marketable)
/data/items_detail.json     → tbh_items_detail.json (base/inherent stats, uniqueMod key)
/data/t/materials.json      → tbh_materials.json
/data/t/stat_mod_groups.json→ tbh_stat_mod_groups.json
/data/t/stat_mods.json      → tbh_stat_mods.json
/data/stat_strings.json     → tbh_stat_strings.json (ชื่อ stat หลายภาษา — มี th-TH)
/data/t/gear_type_scales    → tbh_gear_types.json  (URL จริงไม่ลงท้าย .json; update_data.py keep ไฟล์เดิมถ้า 404)
/data/grades.json           → tbh_grades.json (ไม่มีชื่อแปล มีแต่ weights)
/data/t/levels.json         → tbh_levels.json (ExpForLevelUp ต่อเลเวล 1-100 → LEVEL_EXP ใน JS, ใช้คำนวณ "EXP ถึงเลเวลถัดไป" ใน Farm)
/data/heroes.json           → tbh_heroes.json (6 class, main/sub weapon, stats, attribute_keys, i18n)
/data/skills.json           → tbh_skills.json (active skills — ⚠️ SkillNameKey=null, levels[].value ว่าง; ใช้ tree+skill_th แทน)
/data/passive_skills.json   → tbh_passive_skills.json (มี SkillNameKey_i18n th-TH → ชื่อ passive ไทย)
(wiki /heroes SSR)          → tbh_hero_trees.json (★ skill tree เรียงตาม levelGate 0/10/../70 ต่อ class + active levelValues/activation/cooldown/range/element + passive perPoint/total)
(wiki /skills SSR)          → tbh_skill_th.json ({names,descs} ชื่อ+คำอธิบาย active เป็นไทย — /heroes ไม่มีไทย, /skills มี name_i18n + desc i18n)
/data/rune_tree.json        → tbh_rune_tree.json (nodes x/y, edges, bounds)
/data/runes.json            → tbh_runes.json
/data/stages.json           → tbh_stages.json (120 = 3 act × 10 × 4 diff; level/waves/kills/expPerClear/goldPerClear/i18n)
/data/portal_map.json       → tbh_portal_map.json (ไม่ได้ใช้แล้ว)
/data/stages/<key>.json     → tbh_stage_details.json (monsters + drops, i18n) — ★ครบ 120 ด่าน key จริงตามระดับ (1/2/3/4 xxx) ผ่าน fetch_stage_details.py (อย่าใช้ key Normal ดึงให้ทุกระดับ! drop/กล่องต่างกันตามระดับ: N=Box1.., NM=Lv30, H=Lv50, T=Lv65/80)
(taskbarherowiki.com/farm) → tbh_stage_hp.json (totalHP ต่อด่าน 108 ด่าน farmable; ★ดึงจาก wiki farm page เพราะ stages.json ไม่มี HP — ใช้ใน Farm calculator; ACTBOSS ไม่มี HP)
/data/t/pets.json           → tbh_pets.json (ชื่อ pet i18n)
/data/monsters.json         → tbh_monsters.json (ชื่อ monster i18n — ใช้กับ pet unlock)
/data/t/unique_mods.json    → มีแค่ key+param ไม่มี description
/data/recipes.json          → tbh_recipes.json (crafting: 56 สูตร = 7 หมวด × 8 tier; materials + result gradeOdds + itemsByGrade)
```
**maxLevel ของ skill/passive** ฝังใน HTML ของ `/skills` (SSR `body` JSON) → `tbh_skill_maxlevel.json`
(active skills cap ที่ Lv5 ปัจจุบัน; data มีถึง Lv10)

### ราคา Steam Market (THB) — `fetch_prices.py`
- ใช้ endpoint **`/market/search/render/`** ไล่ดู listing ทั้งเกมทีละหน้า แล้ว match hash_name กับ item เรา
  (เร็วกว่ายิงทีละ item — ~75 หน้า; **Steam cap หน้าละ 10 ตายตัว** ขอ count เกินก็ได้ 10)
- **ต้องมี cookie** (steamLoginSecure) ราคาถึงเป็น ฿ (THB) ตามบัญชี — อ่านจาก `steam_cookie.txt` หรือ env `STEAM_COOKIE`
  ถ้าไม่มี/หมดอายุ → ได้ USD → exit code 2 (ให้ bat/Action หยุด)
- `DELAY=2.0s` ระหว่างหน้า (~3.5 นาที); cooldown 45s เมื่อ 429
- `_fetched_at` บันทึกเป็น **เวลาไทย (UTC+7)** เสมอ (runner เป็น UTC) → gen ใส่เป็น `_at` ใน prices.json → JS แสดง "ราคา • อัพเดท"
- exit codes: 2 = cookie/สกุลเงินผิด, 3 = ไม่ได้ราคาเลย (rate limit) — Action ใช้เช็คว่าจะ deploy ไหม
- ใช้: `python fetch_prices.py [--mat-only|--gear-only|--reset]`

### Unique mod descriptions — `tbh_unique_mods_desc.json`
- wiki มีแค่ key (เช่น `ExplosiveBoltHalf`) ไม่มี description
- description เต็มอยู่บน **Steam listing page เท่านั้น** (เป็นอังกฤษ, ไม่มีไทย) — scrape จาก `bbcode-text` block ที่ยาวสุด
- ดึงไว้ 15/18 (อีก 3 ตัวไม่มี listing ขายเลย → fallback เป็นชื่อ key เว้นวรรค)
- gen_tbh.py map key → desc, fallback `re.sub(r'([A-Z])',' \\1', key)`

## สถาปัตยกรรม index.html
Single HTML, ไม่มี framework, dark theme, gold `#e8c84a`
**Responsive**: `@media(max-width:600px)` คุมมือถือ — แถบเมนู `.tab-nav` เลื่อนแนวนอน (overflow-x, ซ่อน scrollbar), grid→1col, ตารางกว้าง (Farm/Skills/Stage) ห่อด้วย `.farm-table-wrap`/overflow-x scroll, tooltip/dropdown clamp ในจอ. เทสด้วย Playwright viewport 360/390px (เช็ค scrollWidth ไม่เกิน innerWidth)
**7 tabs** (ลำดับ): Material → Equipment → Crafting → Pet → **Farm** → Runes → Skills
(แท็บ "Stages" + "Stage Calculator" เดิม **ถูกยุบรวมเป็นแท็บ Farm** — ดูข้อ 5)

### gen_tbh.py — gotcha
- HTML ประกอบจาก string ต่อกัน เพื่อเลี่ยง f-string ชนกับ `{}` ใน JS/CSS
- **`JS` เป็น raw string** → template literal `${...}` ใช้ได้
- ฝังข้อมูลเข้า JS ด้วย `.replace('// ── marker ──', 'const X=...')`: GEAR_DATA, HEROES_DATA, RUNE_NODES/EDGES, STAGES_DATA, PORTAL_MAP, PET_TH/MONSTER_TH/STAGE_NAME_TH/GRADE_TH/GEARTYPE_TH/CLASS_TH
- TAB string เป็น plain string (concat `gb()` ได้); `__EFFECT_OPTIONS__` replace ตอน assemble
- Materials render เป็น **static HTML** ตอน build (filter JS show/hide); Gear/Pet/Skill/Rune/Stage/Craft render ด้วย JS
- **ราคาไม่ baked** — material card มี `<div class="price-row" data-pid="{id}">` ว่าง, gear/craft ใช้ `PRICES[id]` ตอน render; gen เขียน `prices.json` (served) คู่กับ index.html

### ระบบภาษา (i18n) — dual-span + CSS toggle
- ทุก string ที่แปลได้ render เป็น `<span class="en">EN</span><span class="th">TH</span>`
- toggle ด้วย body class: `body.lang-th .en{display:none}` — **ไม่ต้อง re-render** ทำงานกับ modal/tooltip ที่ render ทีหลัง
- **default = ไทย** (`<body class="lang-th">`, สลับเป็น en เมื่อ localStorage `tbh_lang==='en'`)
- ปุ่ม toggle slider (EN ◐ ไทย) มุมขวาบน topbar
- helper: Python `bi(i18n_dict)` / `gb(en,th)` / `biobj()`→{e,t}; JS `jbi({e,t})` / `jbiR(o,fn)` (มี {0} replace) / `jdiff(d)`
- `<option>`/placeholder ใส่ span ไม่ได้ → render เป็น plain text ตามภาษาปัจจุบัน (เช็ค `body.lang-th`); `applyLangToSelects()` re-render farm dropdown ตอนสลับภาษา
- **gotcha**: ห้ามใส่ `&amp;` ในข้อความที่ส่งเข้า `jbi()`/`gb()` (มัน esc ซ้ำ → โชว์ `&amp;`) — ใช้ `&` ปกติ หรือเลี่ยงเป็น "และ"
- search index เก็บทั้ง 2 ภาษา (data-name="en|th", rune dataset.search, gear g.n+g.nb.t)

### คำแปลไทย (อิงแหล่งทางการ — ไม่แปลเอง)
- item/stat names: items.json + stat_strings.json (th-TH)
- skills/runes/stages/monsters/pets: ไฟล์ JSON มี `_i18n`/i18n dict
- **GRADE_TH / GEARTYPE_TH / CLASS_TH** (gen_tbh.py): จาก Steam Market category + cross-check drop item names + heroes.json
  - grade ครบ 10 (ธรรมดา/ไม่ธรรมดา/หายาก/ตำนาน/อมตะ/อาร์คานา/เหนือขีดจำกัด/สวรรค์/ศักดิ์สิทธิ์/จักรวาล)
  - gear type 14/20 (เหลือ BOW/STAFF/SCEPTER/ARROW/ORB/TOME ไม่มีแหล่ง — Steam รวมเป็นอาวุธหลัก/รอง)
  - class 6: อัศวิน/เรนเจอร์/จอมเวท/นักบวช/นักล่า/สเลเยอร์
- difficulty: ปกติ/ฝันร้าย/นรก/ทรมาน (จากภาพในเกม — `DIFF_TH` ใน JS)
- pet bonus: `PET_BONUS_TH` (map 4 แบบ); "per level"→ต่อเลเวล
- **ไม่มีไทย (คงอังกฤษ):** unique mod desc, material type (Decoration/Engraving/Inscription), Base Stats/Inherent/Market labels, weapon type 6 ตัว

### แต่ละ tab
1. **Material Effects** — 115 mats, static HTML, filter Type/Slot/Grade (multi-select) + Effect (**custom searchable dropdown** `#eff-dd` พิมพ์กรองได้ EN/TH) + search, ราคา THB, sold ใส่ลูกน้ำ
2. **Equipment** — gear Legendary+ (~1960 หลัง dedup), filter Slot/Grade/Level/Type (multi-select) + "มี unique mod" toggle + search, base/inherent stats + unique mod desc, ราคา, grade dot สี, type pill มีรูป (class portrait / GEARTYPE_ICON)
3. **Crafting** — 56 สูตร (`CRAFT_DATA`), filter ตามหมวด (type pill มีรูป), แต่ละสูตร: วัตถุดิบ + ราคา/ชิ้น + ราคารวม + ปุ่มซื้อ Steam + gradeOdds bar; ปุ่ม "ของที่อาจได้" → modal โชว์ item (dedup ชื่อ) + base/inherent stat + ราคาต่อเกรด + Steam link
4. **Pet** — 8 pets (hardcode `PETS` ใน JS), filter free/supporter + search; การ์ดดีไซน์ใหม่ (`.petc*`): แถบสีตามชนิด (priority ม่วง/free เขียว/supporter เหลือง), portrait บนไทล์ gradient, โบนัสเป็น chip, จุดฟาร์มอันดับ 1 ติด ★
5. **Farm** ⭐ (แท็บใหม่ แทน Stages+Calculator) — เครื่องคิดฟาร์ม **EXP/Gold ต่อชั่วโมง** + ตารางข้อมูลด่าน + panel มอนสเตอร์/ดรอป — ดู "Farm tab" ด้านล่าง
6. **Runes** — node tree (SVG edges + absolute div), pan/zoom/reset, search (หรี่ node ไม่ตรง)
   - **★ % ต้อง scale ตามกฎ stat เดียวกับ gear** (`get_fmt`/`scale`): stat ลงท้าย `Percent`/อยู่ใน `D_SET` → หาร 10 (raw 30 → 3%); เคสพิเศษ `AllHeroMoveSpeed`/`AllHeroAttackSpeed` (effect มี % แต่ stat ไม่เข้ากฎ) → ถ้า `flat` แต่ effect มี `%` ให้ div10 (raw 20 → 2%) — `_rune_scale()` ใน gen
   - **★ เก็บทุก level** (`_rune_levels` → `n.levels=[{lv,val(scaled),cost}]`, ไม่ใช่แค่ lv1) → แสดง **ตาราง effect+cost ต่อ level**: `runeLvTableHtml(n)` + `runeEffOf(n,v)` (helper ใช้ร่วม hover tooltip + click detail)
   - **hover (`showRuneTT`) โชว์ตารางเต็มเลย** (desktop) + กันล้นจอ (วัด offsetW/H แล้ว clamp/flip); **มือถือ** ไม่มี hover → แตะ `openRuneDetail` panel ที่มีตารางเหมือนกัน
   - drag กันรูปติดเมาส์: `img.draggable=false` + ดัก `dragstart`; มือถือกันจอเลื่อน/pull-to-refresh: CSS `touch-action:none`+`overscroll-behavior:contain` ที่ `.rune-viewport` + touch handler `passive:false`+`preventDefault`
7. **Skills** — เลือก class (hero-nav) → **การ์ดข้อมูลตัวละคร** (portrait + full-body art `taskbarherowiki.com/icons/HeroArt_{key}.png` + คำอธิบาย + มือหลัก/รอง/ปลดล็อก + ค่าพื้นฐาน 9 ค่า: CritChance/CritDamage หาร 10, CastSpeed/CDR ใส่ %) + **ต้นไม้สกิลตามเลเวล** (LV 0-70 จาก `HERO_TREES`/tbh_hero_trees.json), tile = active/passive (`data-kind`), **ชี้เมาส์→tooltip** (`showNodeTip`/`nodeDetailHtml`, ไม่ใช่ modal แล้ว), filter All/Skills/Passives = **หรี่ที่ไม่เลือก** (`.ntile-dim`, ไม่ซ่อน). ชื่อ/desc active ไทยจาก tbh_skill_th, passive ไทยจากข้อมูล, ธาตุไทยจาก ELEMENT_TH
   - ⚠️ desc template มี `{0}%` แล้ว → เติม `{0}` ด้วยช่วงตัวเลขล้วน (ไม่ใส่ %) กัน % ซ้ำ
   - HERO_TREES key = HeroKey (101/201/.../601) ตรงกับ HEROES_DATA; gen เติม URL ไอคอน + name_bi/desc_bi (active) ตอน build

### Farm tab (★ logic ถอด/ตรวจตรงกับ taskbarherowiki.com/farm 100%)
- **โมเดล**: กรอกเวลาเคลียร์ → fit `clearTime = a·totalHP + k·waves` (least-squares 2 ตัวแปร, `a`=วิ/HP=1/DPS, `k`=overhead/wave) → จัดอันดับทุกด่าน `value × penalty × (1+bonus) / T × 3600`
  - EXP mode: `expPerClear × over-level-penalty × (1+expBonus)`; Gold mode: `goldPerClear × (1+goldBonus)` (**gold ไม่มี penalty**)
  - **over-level penalty** `farmPenalty(heroLv,stageLv)`: ถอดจาก code เกม (ตรวจ 14,400 คู่ตรง wiki เป๊ะ) — gold/no-hero → 1
- **input**: โหมด EXP/Gold (แถบคาดบนกล่อง), เลเวลฮีโร่ (default 1, ซ่อนตอน gold), โบนัส (แยก exp/gold), **EXP ปัจจุบัน** (ซ่อนตอน gold), เวลาเคลียร์ — แถวแรก **ล็อค Normal 1-1** (วัด overhead), แถวถัดไปเลือกด่าน (ceiling, default ว่าง) + ระดับเลือกใน dropdown ด่านเลย (tab sticky บนเมนู), กรอกเป็น **วินาที**
  - **หัวข้อ 3 แยกด่านเสริม**: row i===0=หัวข้อ1 (floor), i===1=หัวข้อ2 (ด่านยากสุดด่านเดียว), i===2=หัวข้อ3 ("เพิ่มด่านอื่นๆ ไม่บังคับ" — ด่าน sample ให้ fit แม่นขึ้น)
  - **ปุ่ม ล้าง/แชร์ลิงก์**: `resetFarm()` (custom modal `showConfirm`, ไม่ใช่ native confirm), `farmShare()` encode state → URL hash `#farm=` + copy (toast "คัดลอกแล้ว"); `loadFarmFromHash()` โหลดจากลิงก์ก่อน localStorage
  - **★ "EXP ถึงเลเวลถัดไป"** (`renderFarmResults`): user กรอก **EXP ปัจจุบัน** ช่องเดียว (`farm-expcur`, โชว์ลูกน้ำ `onExpCurInput` คง caret), เต็มเลเวลรู้เองจาก `LEVEL_EXP[heroLv]` (tbh_levels.json) → `remaining = LEVEL_EXP[lv] − cur` → การ์ดโชว์ "≈ X รัน · Y ชม. ถึงเลเวลถัดไป"
  - **badge "ด่านที่ผ่านสูงสุด"** = ด่านเดียวที่ level สูงสุดในบรรดา sample (`ceilRow`/`ceilKey`) — ไม่ใช่ทุก sample
  - **เพดาน pool = `level <= ceilLv`** (ด่านเลเวลต่ำกว่า = เคยผ่าน ฟาร์มได้; HP เยอะแค่ช้าลง ไม่ใช่ตีไม่ผ่าน — **อย่าเปลี่ยนเป็น HP**)
  - ★ **ระดับแยกต่อแถว**: แต่ละ sample เก็บ `diff` ของตัวเอง (`pickDiffInline` เซ็ต `farmSamples[i].diff`); `FARM_DIFF` เหลือเป็นแค่ค่าตั้งต้นของแถวที่เพิ่มใหม่ — loadFarm migrate ค่าเก่าที่ไม่มี diff ต่อแถว
  - **NEXT card** (`renderFarmNext`, ถอดจาก wiki/farm) — แนะนำด่านถัดไปให้จับเวลาเพื่อให้ fit แม่นขึ้น: ≤2 ด่าน=ด่านคุ้มสุดที่ยังไม่กรอก, 3-5=ด่าน HP ห่างจากที่กรอกมากสุด (log-HP gap), ≥6=ขึ้น "ข้อมูลแน่นพอแล้ว"; ปุ่ม "+ เพิ่ม" → `addRecommended(key)` เติมแถวว่าง/เพิ่มแถวพร้อม diff; การ์ดโชว์ระดับ+Lv ของด่านแนะนำ
- **layout 2 คอลัมน์**: ซ้าย=กล่องกรอก, ขวา=การ์ด "ฟาร์มคุ้มสุด" (chips เคลียร์/per-run/penalty + "ดีกว่าด่านสูงสุด X%" + รองลงมา 2-4) — ว่าง = placeholder
- **ตารางผลลัพธ์** (เต็มกว้าง): #, ด่าน (badge คุ้มสุด/ด่านที่ผ่านสูงสุด), ระดับ, Lv, เคลียร์(s), ได้ EXP%, EXP/รัน, EXP/ชม, % เทียบ (bar); "แสดงสูงสุด" custom dropdown (default 15)
- **การ์ด over-level penalty** (จาก wiki): ตาราง EXP-kept ปรับตามเลเวลฮีโร่ + บอก free-gap
- **ตารางข้อมูลด่าน** (`renderStageTable`): farm-table ตาม **`REF_DIFF`** (ตัวเลือกระดับ pills แยกจากเครื่องคิด!) — ด่าน/ชื่อ/Lv/HP/EXP/Gold, คลิกแถว → `showStageDetail()` panel (มอนสเตอร์+ธาตุ+drop boxes เหมือน Stages เดิม)
- **fns**: `initFarm/computeFarm/renderFarmResults/renderFarmNext/addRecommended/renderFarmSamples/farmFit/farmPenalty/renderPenaltyInfo/renderStageTable/showStageDetail`; custom dropdown ด่าน = `fdd*` (toggleFdd/pickFdd/pickDiffInline)
- **localStorage `tbh_farm`** (saveFarm/loadFarm): mode/diff/refDiff/hero/**expcur**/bonus/samples/maxShow — แยกตามเบราว์เซอร์ (รวมใน share-link ด้วย)

### Gear
- dedup เหลือ variant แรกต่อ (name, grade, type, level) → 1960 (ดิบ 3920 มี A/B stat ต่างกัน)
- Steam hash name: **`{name} ({Grade title-case}) A`** เช่น `Mystic Bow (Legendary) A` (ใช้ variant A เสมอ)
- **HATCHET = Offhand** (Slayer sub-weapon), AXE = Weapon; SLOT_GROUP (Python) + GEAR_TYPES_BY_SLOT (JS) ต้องตรงกัน
- type pill แสดง class ไทย (อัศวิน) + gear type ไทย (ดาบ) เป็น subtitle

## Stat formatting (ถอดจาก JS ของ wiki — `get_fmt`/`scale`/`fmt_single`)
- ลงท้าย `Resistance` / MaxBlock/MaxDodge → ตรงๆ + `%` (rawpct)
- ลงท้าย `Percent` / MODTYPE ADDITIVE,MULTIPLICATIVE / อยู่ใน D_SET → **หาร 10** + `%` (div10)
- `AttackSpeed` FLAT → `val/100` + `/s`; อื่นๆ → flat
- stat name แปลไทยผ่าน `get_stat_name(type,'th-TH')` / `get_stat_name_bi()`

## เทสต์
Playwright (Python, headless Chromium) เปิด `file://` ของ index.html, คลิก tab/filter/toggle, เช็ค text + console errors
```python
from playwright.sync_api import sync_playwright
# goto(pathlib.Path('index.html').resolve().as_uri()); pg.on('pageerror', ...)
# คลิก .tab-btn[data-tab="gear"], #lang-toggle, เช็ค eval_on_selector
```

## วิธีอัปเดตเมื่อเกม patch ใหม่
1. `python update_data.py` (ดึง wiki data + rebuild) — ถ้ามี skill/rune/stage/recipe ใหม่ อาจต้องดึง maxLevel/stage_details/recipes เพิ่มเอง
2. ราคา item: ปล่อย GitHub Action รันเอง (ทุก ชม.) หรือ `python fetch_prices.py` เอง
3. ถ้ามี unique mod ใหม่ → re-scrape `tbh_unique_mods_desc.json`
3b. ถ้า stage/HP เปลี่ยน → ดึง `tbh_stage_hp.json` ใหม่จาก `taskbarherowiki.com/farm` (parse `__next_f` `stages[]` → key→totalHP) เพราะ stages.json ไม่มี HP
4. ขอ confirm แล้ว commit (อย่าลืม `git pull` ก่อน — Action push ราคาเรื่อยๆ)

## เกร็ดเพิ่ม
- `gen_tbh.py` `BASE` = โฟลเดอร์ของไฟล์เอง (relative) — รันได้ทั้ง Windows + Linux runner
- `GEARTYPE_ICON` (item id ต่ำสุดต่อ gear type) + `CLASS_ICON` = รูปในปุ่ม filter type; crafting ใช้ `_craft_icon(category)` map หมวด→gear type ตัวแทน
- ตัวเลข "sold"/volume ใส่ลูกน้ำ: Python `f'{int(v):,}'` (material) / JS `Number(v).toLocaleString('en')` (gear)
