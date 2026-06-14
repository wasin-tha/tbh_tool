#!/usr/bin/env python3
"""steam_login.py — ล็อกอิน Steam ด้วย user/pass (บัญชีไม่เปิด 2FA) → คืน steamLoginSecure สด
เขียนลง steam_cookie.txt ให้ fetch_prices.py ใช้ต่อ (และ print ค่าออกมา)

ต้องมี lib:  pip install steam
ใช้:
  STEAM_USER=xxx STEAM_PASS=yyy python steam_login.py
  python steam_login.py <user> <pass>

⚠ บัญชีต้องปิด Steam Guard ทั้งหมด (ทั้ง mobile + email) ไม่งั้น login จะค้างรอ code
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE        = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(BASE, 'steam_cookie.txt')


API = 'https://api.steampowered.com/IAuthenticationService'

def get_cookie(user, password):
    """login ผ่าน flow ใหม่ (IAuthenticationService) → คืนค่า steamLoginSecure
    (= steamid%7C%7Caccess_token ตามที่ steamcommunity ใช้). บัญชีไม่มี Steam Guard"""
    import base64, time as _t
    import requests
    from steam.core.crypto import rsa_publickey, pkcs1v15_encrypt   # reuse แค่ตัวเข้ารหัส
    s = requests.Session()
    s.headers['User-Agent'] = 'Mozilla/5.0'

    # 1) RSA public key ของบัญชี → เข้ารหัสรหัสผ่าน
    rk = s.get(f'{API}/GetPasswordRSAPublicKey/v1/',
               params={'account_name': user}, timeout=15).json().get('response') or {}
    if not rk.get('publickey_mod'):
        raise RuntimeError('ขอ RSA key ไม่ได้ (ชื่อบัญชีผิด?)')
    key = rsa_publickey(int(rk['publickey_mod'], 16), int(rk['publickey_exp'], 16))
    enc = base64.b64encode(pkcs1v15_encrypt(key, password.encode('ascii'))).decode()

    # 2) เริ่ม session ด้วย user/รหัส
    begin = s.post(f'{API}/BeginAuthSessionViaCredentials/v1/', timeout=15, data={
        'account_name': user, 'encrypted_password': enc,
        'encryption_timestamp': rk['timestamp'], 'remember_login': 'true',
        'platform_type': 2, 'persistence': 1, 'website_id': 'Community',
    }).json().get('response') or {}
    if not begin.get('client_id'):
        raise RuntimeError('begin auth ล้มเหลว — รหัสผ่านผิด')
    confs = [c.get('confirmation_type') for c in begin.get('allowed_confirmations', [])]
    if any(t not in (1, None) for t in confs):   # 1 = ไม่ต้องยืนยัน; อื่น = ติด Steam Guard
        raise RuntimeError(f'บัญชีติด Steam Guard (confirmation {confs}) — ต้องปิด guard ให้หมด')

    # 3) poll จน Steam ออก access_token
    steamid = begin['steamid']
    for _ in range(10):
        poll = s.post(f'{API}/PollAuthSessionStatus/v1/', timeout=15, data={
            'client_id': begin['client_id'], 'request_id': begin['request_id'],
        }).json().get('response') or {}
        if poll.get('access_token'):
            return f"{steamid}%7C%7C{poll['access_token']}"
        _t.sleep(2)
    raise RuntimeError('poll ไม่ได้ access_token (timeout / ติด guard)')


def refresh():
    """อ่าน creds → login → เขียน steam_cookie.txt → คืนค่า cookie"""
    user = os.environ.get('STEAM_USER', '').strip()
    pw   = os.environ.get('STEAM_PASS', '').strip()
    if len(sys.argv) >= 3:
        user, pw = sys.argv[1].strip(), sys.argv[2].strip()
    if not user or not pw:
        raise RuntimeError('ต้องมี STEAM_USER + STEAM_PASS (env หรือ args)')
    val = get_cookie(user, pw)
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        f.write(val)
    return val


if __name__ == '__main__':
    try:
        v = refresh()
        print(f'✅ เขียน steamLoginSecure สดลง {COOKIE_FILE} แล้ว ({len(v)} ตัวอักษร)')
    except Exception as e:
        print(f'❌ login ล้มเหลว: {e}')
        sys.exit(1)
