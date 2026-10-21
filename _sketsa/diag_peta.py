"""Diagnosa 5: reproduksi peta paragraf persis alur produk utk S7 blok 3.1."""
import os, sys
sys.path.insert(0, '/tmp/rg')
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/rg_data')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/rg_up')

from app.ai import _teks_dari_body
from app.versi import ambil_bab, deteksi_bab, _deteksi_bagian
from app.state import petakan, buang_daftar_isi
from app.konteks import (petakan_paragraf, pilih_paragraf, blok_paragraf,
                         isi_paragraf)
from app.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

KUTIP = 'hipotesis yaitu hipotesis komparatif yang berarti potensi untuk memberikan jawaban'
KOM = '1. perbaiki paragraf di bagian ini'

_db = sessionmaker(bind=create_engine('sqlite:////tmp/rg_data/eduai.db'))()
_u = _db.query(User).filter(User.id == 7).first()
NASKAH, _, _err = _teks_dari_body(_db, _u, {'file_id': 78})

#  1) _isi_target versi produk: petakan(seluruh) → section_id '3.1'
_utuh = NASKAH
_peta2 = petakan(buang_daftar_isi(_utuh))
_isi_target = next((x.get('isi_teks', '') for x in _peta2
                    if str(x.get('section_id', '')).strip() == '3.1'), '')
print('peta2 jumlah entri =', len(_peta2))
print('_isi_target len =', len(_isi_target), '| kutip ∈?', KUTIP in _isi_target)

#  2) bandingkan dengan ambil_bab region
_, region31, _ = ambil_bab(NASKAH, '3.1')
print('ambil_bab region len =', len(region31), '| sama?', region31 == _isi_target)

#  3) peta paragraf di atas _isi_target
par = petakan_paragraf(_isi_target)
print('petakan_paragraf → jumlah =', len(par))
if par:
    print('  tipe entri[0] =', type(par[0]), repr(par[0])[:100]
          if not isinstance(par[0], dict) else list(par[0].keys()))
    idx = pilih_paragraf(par, KOM)
    print('  pilih_paragraf idx =', idx)
    if idx is not None:
        p = isi_paragraf(par, idx)
        print('  isi_paragraf len =', len(p or ''), '| kutip ∈?', KUTIP in (p or ''))
        bp = blok_paragraf(par, idx, jml_tetangga=1)
        print('  blok_paragraf len =', len(bp or ''), '| kutip ∈?', KUTIP in (bp or ''))
