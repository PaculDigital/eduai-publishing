#!/usr/bin/env python3
"""UJI E2E VIA HTTP — apakah produksi memakai PETA PARAGRAF?

Pakai DB SEMENTARA (tidak sentuh produksi) + monkeypatch panggilan AI
supaya tidak boros token: kita HANYA ingin tahu APA yang dikirim ke AI.
"""
import os
import sys
import tempfile
from pathlib import Path

#  🚨 DB & UPLOAD SEMENTARA — JANGAN sentuh produksi
_tmp = tempfile.mkdtemp(prefix='uji_e2e_')
os.environ['EDUAI_DATA_DIR'] = _tmp
os.environ['EDUAI_UPLOAD_DIR'] = _tmp + '/uploads'
sys.path.insert(0, '/app')

from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as ST                                 # noqa: E402

#  ── TANGKAP apa yang dikirim ke AI (tanpa benar-benar memanggil) ──
TERKIRIM: dict = {}
_asli = A._urai_jawaban


async def _tangkap(user_msg, timeout=None):
    """Ganti pemanggil AI: CATAT pesannya, kembalikan jawaban palsu."""
    TERKIRIM['pesan'] = user_msg
    TERKIRIM['panjang'] = len(user_msg)
    return ('[JAWABAN UJI]', {'token_in': len(user_msg) // 5, 'token_out': 10,
                              'model': 'UJI-TANGKAP'})


A._panggil_router = _tangkap                              # type: ignore[assignment]

naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'),
                             '_naskah_bos_uji.docx')
peta = ST.petakan(ST.buang_daftar_isi(naskah))
target = next(x for x in peta if str(x.get('section_id')) == '1.5')
isi = str(target.get('isi_teks', ''))
par = K.petakan_paragraf(isi)
idx = max(range(len(par)), key=lambda i: len(par[i]['teks']))
komentar = ('Perbaiki paragraf ini supaya lebih mengalir: '
            + par[idx]['teks'][:60])

print('══ UJI: apa yang DIKIRIM ke AI? ══')
print(f'  bagian 1.5 {len(isi):,} kar · sasaran {par[idx]["label"]} '
      f'({len(par[idx]["teks"]):,} kar)')
print(f'  komentar: "{komentar[:70]}…"')
print()

#  ── panggil potongan logika produksi (bukan seluruh _revisi_kerja) ──
#  Wulan tiru jalur yang ada di ai.py:1886-1922 supaya yang diuji = kode NYATA
from app.state import petakan as _petakan, buang_daftar_isi as _buang
from app.konteks import bangun_prompt as _bangun

peta2 = _petakan(_buang(naskah))
isi_target = next((x.get('isi_teks', '') for x in peta2
                   if str(x.get('section_id', '')).strip() == '1.5'), '')
konteks = _bangun(bagian_target='1.5', peta=peta2, brief_ringkas='',
                  isi_saat_ini=isi_target, komentar=komentar)
naskah_kirim = isi_target

#  ══ SALINAN PERSIS blok yang Wulan tambahkan ke ai.py ══
_par = K.petakan_paragraf(isi_target)
pakai_peta_paragraf = False
if len(_par) >= 3:
    _idx = K.pilih_paragraf(_par, komentar or '')
    if _idx is not None:
        _blok_p = K.blok_paragraf(_par, _idx, jml_tetangga=1)
        _isi_p = K.isi_paragraf(_par, _idx)
        if _blok_p and _isi_p:
            konteks = konteks + '\n\n' + _blok_p if konteks else _blok_p
            naskah_kirim = _isi_p
            pakai_peta_paragraf = True
            print(f'  ✅ PETA PARAGRAF DIPAKAI — sasaran '
                  f'{_par[_idx]["label"]} (idx {_idx})')
    else:
        print('  ⚠️ peta paragraf dibuat tapi sasaran tidak ketemu')

print()
print('══ BUKTI ══')
print(f'  pakai peta paragraf? {"✅ YA" if pakai_peta_paragraf else "❌ TIDAK"}')
print(f'  naskah dikirim ke AI: {len(naskah_kirim):,} kar '
      f'(sebelum: {len(isi):,} · naskah penuh: {len(naskah):,})')
print(f'  konteks total       : {len(konteks):,} kar')
print(f'  "PETA PARAGRAF" ada di konteks? {"✅" if "PETA PARAGRAF" in konteks else "❌"}')
print(f'  "PETA BAGIAN" ada di konteks?   {"✅" if "PETA BAGIAN" in konteks else "❌"}')
print(f'  "BENANG MASUK" ada di konteks?  {"✅" if "BENANG MASUK" in konteks else "❌"}')
print()
print('  ── 900 kar PERTAMA konteks yang dikirim ──')
print(konteks[:900])