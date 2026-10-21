"""UJI NYATA: bisakah dropdown membedakan PROPOSAL TESIS vs ARTIKEL JURNAL
vs DOKUMEN UMUM? Presisikah isinya?

PERINTAH BOS 24Sep26:
  "Coba uji pakai proposal tesis saya dan jurnal apakah bisa membedakan,
   uji juga dropdown nya apakah presisi?"

DOKUMEN ASLI (bukan karangan):
  · proposal : /opt/data/services/tesis-s2-goras/docs/proposal_v1_original.docx
  · tesis    : _contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx
  · jurnal   : /opt/data/services/penelitian-bot/contoh/Fransiskha artikel.docx
  · artikel  : /opt/data/services/jurnalkit/outputs/slr_recovered/slr_final.docx
"""
import sys

sys.path.insert(0, '/app')

from app import kelompok_catatan as KC
from app import state

BERKAS = [
    ('PROPOSAL TESIS BOS',
     '/app/_uji_doc/proposal_v1_original.docx'),
    ('TESIS S2 (sastra novel)',
     '/app/_uji_doc/tesis_s2.docx'),
    ('ARTIKEL JURNAL (Fransiskha)',
     '/app/_uji_doc/artikel_jurnal.docx'),
    ('ARTIKEL JURNAL (SLR)',
     '/app/_uji_doc/slr_final.docx'),
    ('DOKUMEN UMUM (perjanjian buatan)',
     '/app/_uji_doc/perjanjian.txt'),
]


def baca_docx(jalur: str) -> str:
    """Baca .docx jadi teks — pakai pembaca BAWAAN EduAi.

    ⚠️ JANGAN pakai python-docx: kontainer produksi SENGAJA tidak punya
    library itu (keputusan lama, supaya image ringan). Yang ada:
    `app/ai.py::_teks_dari_berkas` — murni Python (zipfile).
    """
    from app import ai as AI
    from pathlib import Path
    try:
        return AI._teks_dari_berkas(Path(jalur), jalur)   # noqa: SLF001
    except Exception as e:                                     # noqa: BLE001
        print(f'      ⚠️ gagal baca: {type(e).__name__}: {e}')
        return ''


for nama, jalur in BERKAS:
    print('═' * 72)
    print(f'  {nama}')
    print('═' * 72)
    try:
        if jalur.endswith('.txt'):
            with open(jalur, encoding='utf-8') as f:
                teks = f.read()
        else:
            teks = baca_docx(jalur)
    except FileNotFoundError:
        print('   ⚠️  berkas tidak ada — dilewati\n')
        continue
    if not teks.strip():
        print('   ⚠️  teks kosong — dilewati\n')
        continue

    print(f'   panjang teks: {len(teks):,} karakter')

    #  ── Apa yang dilihat mesin revisi (jenis dokumen) ──
    try:
        peta = state.petakan(teks)
        ringkas = state.ringkas_peta(peta)
        print(f'   peta mesin  : {len(peta)} bagian')
    except Exception as e:                                     # noqa: BLE001
        print(f'   peta mesin  : ⚠️ {type(e).__name__}: {e}')

    #  ── Apa yang muncul di DROPDOWN (yang Bos tanyakan) ──
    bab = KC.daftar_bab_naskah(teks)
    print(f'   DROPDOWN    : {len(bab)} pilihan')
    for i, x in enumerate(bab[:12], 1):
        print(f'      {i:>2}. {x["label"]}')
    if len(bab) > 12:
        print(f'      … dan {len(bab) - 12} lagi')
    if not bab:
        print('      (KOSONG → halaman memakai kotak KETIK + kelompok PER HARI)')
    print()
