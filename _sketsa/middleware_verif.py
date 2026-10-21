import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/main.py')
s = f.read_text(encoding='utf-8')

# rute /qr tadi tidak perlu — pakai middleware saja
lama_rute = """

#  ⚠️ 17 Okt 2026: qr.tridarma.id harus menampilkan HALAMAN VERIFIKASI di akar
#  "/" — bukan beranda EduAi. Domain khusus, jadi akarnya = verifikasi.
HOST_VERIFIKASI = ('qr.tridarma.id',)


@_router_kolaborasi.get('/qr', response_class=HTMLResponse)
async def akar_verifikasi_qr(request: Request):
    \"\"\"Akar untuk domain qr.tridarma.id (dipanggil middleware di bawah).\"\"\"
    return templates.TemplateResponse('loa/verifikasi-loa.html',
                                      {'request': request})"""
if lama_rute in s:
    s = s.replace(lama_rute, '')
    print('✓ rute /qr dibatalkan (pakai middleware)')

# ══ Middleware: domain qr.tridarma.id -> halaman verifikasi di AKAR ══
MIDDLE = '''

# ══════════════════════════════════════════════════════════════════════════
#  DOMAIN VERIFIKASI — qr.tridarma.id adalah domain KHUSUS verifikasi LoA.
#  Akar "/" di domain itu harus menampilkan HALAMAN VERIFIKASI, bukan beranda
#  EduAi. Domain lain (eduai.bikinaja.id) TIDAK terpengaruh.
#  ⚠️ 17 Okt 2026 (temuan Bos): sebelumnya qr.tridarma.id/ menampilkan EduAi.
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

# sisipkan setelah app = FastAPI(...) selesai — cari baris include_router pertama
lama_inc = 'app.include_router(_router_kolaborasi)'
assert lama_inc in s
s = s.replace(lama_inc, MIDDLE.strip('\n') + '\n\n\n' + lama_inc, 1)
f.write_text(s, encoding='utf-8')
print('✓ middleware domain verifikasi dipasang')
print('cek:', 'arahkan_domain_verifikasi' in s)
