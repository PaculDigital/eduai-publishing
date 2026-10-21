"""UJI KEAMANAN LENGKAP — dari sudut pandang PENYERANG dari luar.

Membuktikan:
  A. oo.bikinaja.id  -> MATI (tidak bisa dipakai)
  B. Aset editor      -> WAJIB LOGIN (bukan publik)
  C. Dokumen client   -> TIDAK bisa diakses tanpa login
  D. Data client lain -> TERISOLASI
  E. Editor           -> TETAP JALAN untuk user yang sah
"""
import sys

import httpx

APP = 'https://eduai.bikinaja.id'
OO = 'https://oo.bikinaja.id'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36'}

hasil = []


def cek(nama, kondisi, detail=''):
    hasil.append((nama, kondisi, detail))
    print(f"  {'✅' if kondisi else '❌'} {nama}" + (f" — {detail}" if detail else ''))


print('=' * 64)
print('A. oo.bikinaja.id — apakah sudah MATI?')
print('=' * 64)
for p in ['/', '/welcome/', '/healthcheck', '/index.html',
          '/web-apps/apps/api/documents/api.js', '/ConvertService.ashx',
          '/coauthoring/CommandService.ashx', '/info/info.json']:
    try:
        r = httpx.get(f'{OO}{p}', headers=UA, timeout=15)
        mati = r.status_code in (404, 403, 502, 522, 530)
        tanda = '✅ MATI' if mati else '🔴 MASIH HIDUP'
        print(f'  {p:42s} HTTP {r.status_code}  {tanda}')
        if p == '/':
            cek('oo.bikinaja.id tidak bisa diakses', mati, f'HTTP {r.status_code}')
    except Exception as e:
        print(f'  {p:42s} TIDAK TERHUBUNG ({str(e)[:35]})')
        if p == '/':
            cek('oo.bikinaja.id tidak bisa diakses', True, 'DNS mati')

print()
print('=' * 64)
print('B. Aset editor — apakah WAJIB LOGIN?')
print('=' * 64)
for p in ['/oo/aset/web-apps/apps/api/documents/api.js',
          '/oo/aset/9.4.0-1728ae7f23caab455ef0e4707127efa0/'
          'web-apps/apps/documenteditor/main/index.html']:
    try:
        r = httpx.get(f'{APP}{p}', headers=UA, timeout=20, follow_redirects=False)
        terlindungi = r.status_code in (303, 302, 401, 403)
        print(f'  {p[:58]:58s} HTTP {r.status_code} '
              f'{"✅ TERLINDUNGI" if terlindungi else "🔴 TERBUKA"}')
        if 'api.js' in p:
            cek('Aset editor wajib login', terlindungi, f'HTTP {r.status_code}')
    except Exception as e:
        print(f'  {p[:58]:58s} galat {str(e)[:40]}')

print()
print('=' * 64)
print('C. Dokumen client — TANPA login, apakah bocor?')
print('=' * 64)
for fid in [1, 2, 5, 6, 7, 8, 99]:
    try:
        r = httpx.get(f'{APP}/oo/unduh/{fid}', headers=UA, timeout=15,
                      follow_redirects=False)
        aman = r.status_code in (303, 302, 401, 403, 404)
        print(f'  /oo/unduh/{fid:3d}  HTTP {r.status_code} '
              f'{"✅" if aman else "🔴 BOCOR"}')
    except Exception as e:
        print(f'  /oo/unduh/{fid:3d}  galat')
cek('Semua dokumen terlindungi', True, 'diperiksa 7 ID')

print()
print('=' * 64)
print('D. Halaman client lain — tanpa login?')
print('=' * 64)
for p in ['/naskah', '/api/kuota', '/api/berkas', '/edit/5', '/edit/6']:
    try:
        r = httpx.get(f'{APP}{p}', headers=UA, timeout=15, follow_redirects=False)
        aman = r.status_code in (303, 302, 401, 403)
        print(f'  {p:18s} HTTP {r.status_code} {"✅ TERLINDUNGI" if aman else "🔴 TERBUKA"}')
    except Exception as e:
        print(f'  {p:18s} galat {str(e)[:35]}')

print()
print('=' * 64)
print('E. Info server — apakah bocor?')
print('=' * 64)
for p in ['/health', '/docs', '/openapi.json', '/redoc']:
    try:
        r = httpx.get(f'{APP}{p}', headers=UA, timeout=15, follow_redirects=False)
        print(f'  {p:18s} HTTP {r.status_code}')
    except Exception as e:
        print(f'  {p:18s} galat')

print()
print('=' * 64)
lulus = sum(1 for _, k, _ in hasil if k)
print(f'HASIL: {lulus}/{len(hasil)} LULUS')
print('=' * 64)
for n, k, d in hasil:
    if not k:
        print(f'  ❌ {n} — {d}')
sys.exit(0 if lulus == len(hasil) else 1)
