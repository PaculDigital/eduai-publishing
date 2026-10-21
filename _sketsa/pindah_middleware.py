import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/main.py')
s = f.read_text(encoding='utf-8')

BARIS_MIDDLE = '''
# ══════════════════════════════════════════════════════════════════════════
#  DOMAIN VERIFIKASI — qr.tridarma.id = domain KHUSUS verifikasi LoA.
#  Akar "/" di domain itu menampilkan halaman verifikasi, BUKAN beranda EduAi.
#  Domain lain (eduai.bikinaja.id) TIDAK terpengaruh.
#  ⚠️ 17 Okt 2026 (temuan Bos): sebelumnya qr.tridarma.id/ menampilkan EduAi.
#  ⚠️ WAJIB dipasang TEPAT setelah `app = FastAPI(...)` — FastAPI menolak
#     middleware yang didaftarkan setelah aplikasi mulai melayani permintaan.
# ══════════════════════════════════════════════════════════════════════════
HOST_VERIFIKASI = {'qr.tridarma.id'}


@app.middleware('http')
async def arahkan_domain_verifikasi(request: Request, call_next):
    host = (request.headers.get('host') or '').split(':')[0].lower()
    if host in HOST_VERIFIKASI and request.url.path in ('/', ''):
        return templates.TemplateResponse('loa/verifikasi-loa.html',
                                          {'request': request})
    return await call_next(request)
'''

# ── 1. hapus blok yang salah posisi ──
mulai = s.find('# ══════════════════════════════════════════════════════════════════════════\n#  DOMAIN VERIFIKASI — qr.tridarma.id adalah domain KHUSUS')
if mulai >= 0:
    akhir = s.find('    return await call_next(request)', mulai)
    akhir = s.find('\n', akhir + 30) + 1
    s = s[:mulai] + s[akhir:]
    # rapikan baris kosong berlebih
    s = s.replace('\n\n\n\napp.include_router(_router_kolaborasi)', '\n\napp.include_router(_router_kolaborasi)')
    print('✓ blok lama (posisi salah) dihapus')

# ── 2. sisipkan setelah app = FastAPI(...) ──
import re
m = re.search(r"app = FastAPI\([^)]*\)\n", s, re.S)
assert m, 'pola app = FastAPI tidak ketemu'
pos = m.end()
s = s[:pos] + BARIS_MIDDLE.lstrip('\n') + '\n' + s[pos:]
print('✓ middleware dipasang setelah app = FastAPI(...)')

f.write_text(s, encoding='utf-8')

# lapor posisi
for i, b in enumerate(s.split('\n'), 1):
    if 'app = FastAPI' in b or 'arahkan_domain_verifikasi' in b or 'HOST_VERIFIKASI =' in b:
        print(f'   {i}: {b.strip()[:70]}')
