import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/main.py')
s = f.read_text(encoding='utf-8')

# AKAR: qr.tridarma.id -> http://localhost:8100 (root EduAi) => "/" menampilkan
# beranda EduAi. Harusnya "/" = HALAMAN VERIFIKASI (satu halaman).
# Solusi: rute "/" mendeteksi host qr.tridarma.id -> tampilkan verifikasi.

lama = """@_router_kolaborasi.get('/verifikasi-loa', response_class=HTMLResponse)
async def halaman_verifikasi_loa(request: Request):
    \"\"\"Halaman verifikasi LoA (dibuka dari scan QR).\"\"\"
    return templates.TemplateResponse('loa/verifikasi-loa.html',
                                      {'request': request})"""

baru = """@_router_kolaborasi.get('/verifikasi-loa', response_class=HTMLResponse)
async def halaman_verifikasi_loa(request: Request):
    \"\"\"Halaman verifikasi LoA (dibuka dari scan QR).\"\"\"
    return templates.TemplateResponse('loa/verifikasi-loa.html',
                                      {'request': request})


#  ⚠️ 17 Okt 2026: qr.tridarma.id harus menampilkan HALAMAN VERIFIKASI di akar
#  "/" — bukan beranda EduAi. Domain khusus, jadi akarnya = verifikasi.
HOST_VERIFIKASI = ('qr.tridarma.id',)


@_router_kolaborasi.get('/qr', response_class=HTMLResponse)
async def akar_verifikasi_qr(request: Request):
    \"\"\"Akar untuk domain qr.tridarma.id (dipanggil middleware di bawah).\"\"\"
    return templates.TemplateResponse('loa/verifikasi-loa.html',
                                      {'request': request})"""

assert lama in s, 'rute verifikasi tidak ketemu'
s = s.replace(lama, baru)
f.write_text(s, encoding='utf-8')
print('✓ rute /qr ditambahkan (akar domain verifikasi)')
