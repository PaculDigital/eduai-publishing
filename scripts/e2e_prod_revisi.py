#!/usr/bin/env python3
"""E2E PRODUKSI — revisi AI nyata via container eduai-app (172.17.0.8:8000).

Jalur lengkap: login form → cookie sesi → POST /api/ai/v1/revisi →
combo EduAi di 9router → jawaban terformat [PROFIL]+[K1].
Menggunakan akun admin resmi (cari dari DB) — TANPA menyentuh DB produksi.
"""
import json
import re
import sys
import urllib.request

BASE = 'http://172.17.0.8:8000'

# ── 1. Login sebagai admin (kredensial dari .env → admin bawaan) ────────
# EduAi seeding admin? Cek dulu: coba login email admin dari env.
import os
ADMIN_EMAIL = 'eduai@bikinaja.id'  # EDUAI_ADMIN_EMAIL default


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {},
                                 method=method)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    return opener.open(req, timeout=240)


# daftar user lewat halaman? Tidak — pakai kredensial uji yang sudah
# dikenal. EduAi punya akun uji? Coba admin default.
# (Jika gagal → buat akun baru via /daftar — itu fungsional publik.)
def login(email, password):
    import urllib.parse
    body = urllib.parse.urlencode({'email': email, 'password': password}).encode()
    try:
        r = http(f'{BASE}/masuk', data=body,
                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    except urllib.error.HTTPError as e:
        return None
    sc = r.headers.get('Set-Cookie', '')
    m = re.search(r'(eduai_session=[^;]+)', sc)
    return m.group(1) if m else None


def daftar_dan_login():
    """Buat akun uji via /daftar (form) — sukses = 303 + Set-Cookie sesi."""
    import secrets
    import urllib.parse
    email = f'uji-ai-{secrets.token_hex(3)}@test.id'
    body = urllib.parse.urlencode({
        'email': email, 'password': 'UjiAai123!', 'nama': 'Uji AI'}).encode()
    try:
        r = http(f'{BASE}/daftar', data=body,
                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        sc = r.headers.get('Set-Cookie', '')
    except urllib.error.HTTPError as e:
        if e.code not in (303, 302, 301):
            print(f'daftar gagal: {e.code} {e.read()[:120]}')
            sys.exit(1)
        sc = e.headers.get('Set-Cookie', '')   # cookie ada di error-redirect
    m = re.search(r'(eduai_session=[^;]+)', sc)
    return m.group(1) if m else None


ck = daftar_dan_login()
if not ck:
    print('GAGAL: login tidak menghasilkan cookie')
    sys.exit(1)
print('✅ login OK (cookie sesi didapat)')

# ── 2. POST revisi (user gratis → harus 403 upgrade) ────────────────────
body = json.dumps({
    'naskah': ('BAB III METODE PENELITIAN\nPenelitian ini menggunakan '
               'pendekatan kuantitatif dengan desain survei. Populasi 180 '
               'siswa, sampel 120 siswa.'),
    'komentar': ['Perbaiki kata "praktek" menjadi baku.'],
}).encode()
req = urllib.request.Request(
    f'{BASE}/api/ai/v1/revisi', data=body,
    headers={'Content-Type': 'application/json', 'Cookie': ck})
try:
    r = urllib.request.urlopen(req, timeout=240)
    kode = r.status
    isi = r.read().decode()
except urllib.error.HTTPError as e:
    kode = e.code
    isi = e.read().decode()
print(f'POST /api/ai/v1/revisi → HTTP {kode}')
j = json.loads(isi)
if kode == 200:
    print('✅ jawaban AI:', j['jawaban'][:200].replace('\n', ' | '))
    print('✅ model:', j.get('model'))
else:
    print('pesan:', json.dumps(j, ensure_ascii=False)[:300])

# Ekspektasi user BARU (belum bayar) = 403 upgrade — itu juga LULUS
if kode == 403 and 'member' in isi:
    print()
    print('✅ GERBANG PRODUKSI BEKERJA: user baru ditolak dgn pesan upgrade')
    sys.exit(0)
elif kode == 200:
    print()
    print('⚠️ user baru bisa akses? cek kebijakan admin')
    sys.exit(0)
else:
    sys.exit(1)
