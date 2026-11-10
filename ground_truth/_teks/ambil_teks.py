"""Ambil teks bersih (sesudah buang_daftar_isi) fid=112/115/WULAN-1, BACA SAJA.
Jalan di container eduai-app (bukan hermes — di hermes tidak ada paket app):
  ssh ... ubuntu@100.78.203.64 'docker exec -i eduai-app python3 -' < ambil_teks.py
Keluaran: satu baris JSON ke stdout. DB tidak ditulis.
Untuk WULAN-1, docx harus sudah ada di /tmp/wulan1.docx di eduai-app
(ambil dari hermes dulu: docker cp hermes:/tmp/SKRIPSI_WULAN-1.docx).
"""
import sys, base64, json
sys.path.insert(0, '/app')
from pathlib import Path
from app import ai as _ai, state as _st
from app.models import FileBerkas
from app.ai import _teks_dari_berkas, UPLOAD_DIR, SessionLocal
from sqlalchemy import text as _t

out = {}
s = SessionLocal()
try:
    print('sidik sebelum:', (s.execute(_t('SELECT COUNT(*) FROM files')).scalar(),
                             s.execute(_t('SELECT COUNT(*) FROM proses_ai')).scalar(),
                             s.execute(_t('SELECT MAX(id) FROM proses_ai')).scalar()), file=sys.stderr)
    for fid in (112, 115):
        fb = s.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        teks = _teks_dari_berkas(p, fb.nama or '') or ''
        bersih = _st.buang_daftar_isi(teks)
        out[str(fid)] = {'nama': fb.nama,
                         'baris_mentah': len(teks.split('\n')),
                         'baris_bersih': len(bersih.split('\n')),
                         'b64': base64.b64encode(bersih.encode('utf-8')).decode()}
    p = Path('/tmp/wulan1.docx')
    if p.exists():
        teks = _teks_dari_berkas(p, 'SKRIPSI_WULAN-1.docx') or ''
        bersih = _st.buang_daftar_isi(teks)
        out['WULAN-1'] = {'nama': 'SKRIPSI_WULAN-1.docx',
                          'baris_mentah': len(teks.split('\n')),
                          'baris_bersih': len(bersih.split('\n')),
                          'b64': base64.b64encode(bersih.encode('utf-8')).decode()}
    print('sidik sesudah:', (s.execute(_t('SELECT COUNT(*) FROM files')).scalar(),
                             s.execute(_t('SELECT COUNT(*) FROM proses_ai')).scalar(),
                             s.execute(_t('SELECT MAX(id) FROM proses_ai')).scalar()), file=sys.stderr)
finally:
    s.close()
print(json.dumps(out))
