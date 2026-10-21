import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/main.py')
s = f.read_text(encoding='utf-8')

# ══ 1. Import loa ══
lama_imp = 'from . import submit_jurnal as _submit_jurnal  # Submit Artikel Jurnal (16Okt26)'
baru_imp = (lama_imp + '\n'
            'from . import loa as _loa  # Mesin LoA JEMT + verifikasi QR (16Okt26)')
assert lama_imp in s
s = s.replace(lama_imp, baru_imp, 1)
print('✓ import loa')

# ══ 2. 3 rute baru — disisipkan SEBELUM include_router(_router_kolaborasi) ══
RUTE = '''

# ══════════════════════════════════════════════════════════════════════════
#  VERIFIKASI LoA  (halaman qr.tridarma.id)
#  QR di surat LoA menunjuk ke sini: /verifikasi-loa?no=1.001
#  Halaman ini PUBLIK (tanpa login) — memang untuk diperiksa pihak lain.
# ══════════════════════════════════════════════════════════════════════════
@_router_kolaborasi.get('/verifikasi-loa', response_class=HTMLResponse)
async def halaman_verifikasi_loa(request: Request):
    """Halaman verifikasi LoA (dibuka dari scan QR)."""
    return templates.TemplateResponse('loa/verifikasi-loa.html',
                                      {'request': request})


@_router_kolaborasi.get('/api/loa/cek')
async def api_cek_loa(no: str = ''):
    """Cek nomor LoA → data LoA kalau asli, kosong kalau tidak.

    Dipanggil halaman verifikasi lewat fetch('/api/loa/cek?no=...').
    Publik dengan sengaja (QR dipindai orang luar).
    """
    try:
        d = _loa.cek_nomor(no)
    except Exception:
        d = {}
    if not d:
        return JSONResponse({'ok': False, 'sebab': 'Nomor LoA tidak ditemukan.'})
    return JSONResponse({'ok': True, 'data': d})
'''

lama_inc = 'app.include_router(_router_kolaborasi)'
assert lama_inc in s
s = s.replace(lama_inc, RUTE.strip('\n') + '\n\n\n' + lama_inc, 1)
print('✓ 2 rute ditambahkan sebelum include_router')

# pastikan JSONResponse ada
if 'JSONResponse' not in s.split('def ')[0]:
    print('!! JSONResponse mungkin belum diimpor — cek')
    import re
    m = re.search(r'from fastapi.*?import.*', s)
    print('   import fastapi:', m.group(0) if m else 'TIDAK ADA')

f.write_text(s, encoding='utf-8')
print('tersimpan')
