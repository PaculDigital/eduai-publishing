import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/main.py')
s = f.read_text(encoding='utf-8')

RUTE = '''

# ══════════════════════════════════════════════════════════════════════════
#  UNDUH LoA  (tombol di kartu "Daftar Artikel")
#  Putusan Bos 17 Okt 2026: opsi A — tombol "Unduh LoA" di kartu Daftar Artikel.
#  Syarat (dari mesin loa.periksa_syarat): status DITERIMA + Volume/Nomor ada.
# ══════════════════════════════════════════════════════════════════════════
@_router_kolaborasi.post('/api/ai/v1/loa/terbitkan')
async def api_terbitkan_loa(berkas_id: int = Form(...),
                            db: Session = Depends(get_db),
                            request: Request = None):
    """Terbitkan LoA untuk satu artikel user (PDF)."""
    u = _wajib_login_api_submit(request, db)
    from .models import ProfilDokumen                         # noqa: PLC0415
    from pathlib import Path                                  # noqa: PLC0415

    p = db.query(ProfilDokumen).filter(
        ProfilDokumen.user_id == u.id,
        ProfilDokumen.file_id == berkas_id).first()
    if not p:
        return JSONResponse({'ok': False,
                             'sebab': 'Naskah tidak ditemukan.'}, status_code=404)

    #  data artikel dari catatan EduAi
    from . import submit_jurnal as _sj                          # noqa: PLC0415
    cat = _sj._catatan(p) if hasattr(_sj, '_catatan') else {}
    riwayat = (cat or {}).get('riwayat') or []
    if not riwayat:
        return JSONResponse({'ok': False,
                             'sebab': 'Artikel ini belum pernah dikirim ke Tridarma.'})

    r = riwayat[-1]
    status = {
        'ok': True,
        'status': r.get('status') or '',
        'submission_id': r.get('submission_id') or '',
        'judul': r.get('judul') or p.judul or '',
        'volume': r.get('volume') or '',
        'nomor': r.get('nomor') or '',
        'tanggal_diterima': r.get('tanggal_diterima') or r.get('tanggal') or '',
        'tanggal_terbit': r.get('tanggal_terbit') or '',
        'authors': r.get('penulis') or '',
        'affiliation': r.get('afiliasi') or '',
    }
    artikel = {'judul': p.judul or '', 'penulis': r.get('penulis') or '',
               'afiliasi': r.get('afiliasi') or '', 'id_ojs': r.get('submission_id') or ''}

    folder = Path('/app/data/loa') / str(u.id)
    hasil = _loa.unduh_untuk_user(status, artikel, folder)
    if not hasil.get('ok'):
        return JSONResponse({'ok': False, 'sebab': hasil.get('sebab')}, status_code=400)

    return JSONResponse({'ok': True, 'nomor': hasil.get('nomor'),
                         'nomor_surat': hasil.get('nomor_surat'),
                         'unduh': f'/api/ai/v1/loa/unduh?berkas_id={berkas_id}'})


@_router_kolaborasi.get('/api/ai/v1/loa/unduh')
async def api_unduh_loa(berkas_id: int = 0,
                        db: Session = Depends(get_db),
                        request: Request = None):
    """Kirim berkas PDF LoA yang sudah dibuat."""
    u = _wajib_login_api_submit(request, db)
    from pathlib import Path                                  # noqa: PLC0415
    from fastapi.responses import FileResponse                 # noqa: PLC0415

    folder = Path('/app/data/loa') / str(u.id)
    kandidat = sorted(folder.glob('LoA-*.pdf')) if folder.exists() else []
    if not kandidat:
        return JSONResponse({'ok': False,
                             'sebab': 'LoA belum dibuat. Tekan "Terbitkan LoA" dulu.'},
                            status_code=404)
    pdf = kandidat[-1]
    return FileResponse(str(pdf), media_type='application/pdf',
                        filename=pdf.name)
'''

lama_inc = 'app.include_router(_router_kolaborasi)'
assert lama_inc in s
s = s.replace(lama_inc, RUTE.strip('\n') + '\n\n\n' + lama_inc, 1)
f.write_text(s, encoding='utf-8')
print('✓ 2 rute LoA ditambahkan')
print('cek:', s.count('/api/ai/v1/loa/'))
