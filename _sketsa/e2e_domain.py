"""E2E LEWAT DOMAIN PRODUKSI — bukti terakhir sesudah deploy.

Menjawab: sesudah deploy, apakah revisi mahasiswa lewat
https://eduai.bikinaja.id selesai (bukan 420-460 dtk gagal)?

JALAN DI HOST (bukan dalam container) supaya benar-benar lewat jalur publik.
"""
import json
import sys
import time

import httpx

BASE = 'https://eduai.bikinaja.id'
COOKIE = 'eduai_session'

print('═' * 76)
print('  E2E LEWAT DOMAIN PRODUKSI (sesudah deploy)')
print('═' * 76)

#  ── 1. health ──────────────────────────────────────────────────────────
r = httpx.get(f'{BASE}/health', timeout=30)
print(f'health : {r.status_code}')

#  ── 2. token dibuat DI DALAM container (kunci ada di sana) ─────────────
#     (dijalankan terpisah oleh pemanggil lewat docker exec)
TOKEN = sys.argv[1] if len(sys.argv) > 1 else ''
if not TOKEN:
    print('❗ token tidak diberikan')
    sys.exit(2)

FILE_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 9
KOMENTAR = sys.argv[3] if len(sys.argv) > 3 else 'Perbaiki kalimat pembuka.'

print(f'token  : {len(TOKEN)} kar')
print(f'file_id: {FILE_ID}')

hd = {COOKIE: TOKEN}
ck = httpx.Cookies()
ck.set(COOKIE, TOKEN, domain='eduai.bikinaja.id')

#  ── 3. kuota sebelum ───────────────────────────────────────────────────
r = httpx.get(f'{BASE}/api/ai/v1/kuota', cookies=ck, timeout=30)
print(f'\nkuota SEBELUM : {r.status_code} · {r.text[:180]}')

#  ── 4. tekan tombol ────────────────────────────────────────────────────
body = {'file_id': FILE_ID, 'bab': '__seluruh__',
        'komentar': [KOMENTAR], 'setuju_bagian': True}
t0 = time.time()
r = httpx.post(f'{BASE}/api/ai/v1/revisi', json=body, cookies=ck, timeout=60)
print(f'\nTEKAN TOMBOL  : {r.status_code} dalam {time.time()-t0:.2f} dtk')
print(f'   body: {r.text[:260]}')
try:
    hasil = r.json()
except Exception:                                                         # noqa: BLE001
    hasil = {}
kode = hasil.get('kode', '')
print(f'   kode = {kode!r}')

if not kode:
    print('\n❗ tidak dapat kode proses — periksa kuota/izin')
    sys.exit(1)

#  ── 5. pantau lewat domain ─────────────────────────────────────────────
print('\n── PANTAU (lewat domain publik) ──')
akhir = None
for i in range(1, 40):
    time.sleep(10)
    r = httpx.get(f'{BASE}/api/ai/v1/proses/{kode}', cookies=ck, timeout=30)
    try:
        d = r.json()
    except Exception:                                                     # noqa: BLE001
        d = {}
    st = d.get('status', '?')
    th = d.get('tahap', '?')
    print(f'   t+{time.time()-t0:6.1f}s · status={st:<9} · tahap={th[:44]}')
    if st in ('selesai', 'gagal'):
        akhir = d
        break

print('\n══ HASIL AKHIR LEWAT DOMAIN ══')
if akhir is None:
    print('❌ MASIH MENGGANTUNG — perbaikan TIDAK berhasil')
    sys.exit(1)
print(f'status   : {akhir.get("status")}')
print(f'tahap    : {akhir.get("tahap")}')
print(f'durasi   : {time.time()-t0:.1f} dtk')
for k in ('model_ai', 'token_in', 'token_out', 'token_revisi', 'galat'):
    if k in akhir:
        print(f'{k:9s}: {str(akhir[k])[:150]}')

#  ── 6. kuota sesudah ───────────────────────────────────────────────────
r = httpx.get(f'{BASE}/api/ai/v1/kuota', cookies=ck, timeout=30)
print(f'\nkuota SESUDAH : {r.status_code} · {r.text[:180]}')

print('\n' + '═' * 76)
if akhir.get('status') == 'selesai':
    print('  ✅ LULUS — revisi lewat DOMAIN selesai, tidak menggantung lagi')
    sys.exit(0)
print('  ❌ status bukan selesai')
sys.exit(1)
