"""UJI AKAR: apakah `_teks_dari_berkas` (mesin EduAi sendiri) bisa membaca
berkas asli mahasiswa (.docx/.pdf) dari disk?

JANGAN pasang library baru. Yang diuji = mesin yang SUDAH dipakai EduAi.
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import ai as AI

UJI = [
    ('/app/_uji_doc/proposal_v1_original.docx', 'PROPOSAL TESIS BOS'),
    ('/app/_uji_doc/tesis_s2.docx', 'TESIS S2 (sastra novel)'),
    ('/app/_uji_doc/artikel_jurnal.docx', 'ARTIKEL JURNAL (Fransiskha)'),
    ('/app/_uji_doc/slr_final.docx', 'ARTIKEL JURNAL (SLR)'),
]

for jalur, nama in UJI:
    p = Path(jalur)
    print('═' * 70)
    print(f'  {nama}')
    print('═' * 70)
    if not p.is_file():
        print('   ⚠️  berkas tidak ada\n')
        continue
    try:
        teks = AI._teks_dari_berkas(p, p.name)                  # noqa: SLF001
    except Exception as e:                                     # noqa: BLE001
        print(f'   ❌ GAGAL: {type(e).__name__}: {e}\n')
        continue
    print(f'   panjang teks: {len(teks or ""):,} karakter')
    print('   200 karakter pertama:')
    print('   ' + repr((teks or '')[:200]))
    print()

#  ── uji ke disk: apakah berkas asli mahasiswa ADA di UPLOAD_DIR? ──────
print('═' * 70)
print('  BERKAS ASLI MAHASISWA DI DISK (UPLOAD_DIR)')
print('═' * 70)
try:
    from app.main import UPLOAD_DIR
    print(f'   UPLOAD_DIR = {UPLOAD_DIR}')
    d = Path(UPLOAD_DIR)
    if d.is_dir():
        n = 0
        for anak in sorted(d.iterdir())[:6]:
            if anak.is_dir():
                isi = list(anak.iterdir())[:3]
                print(f'   📁 {anak.name}/ → {len(list(anak.iterdir()))} berkas')
                for x in isi:
                    n += 1
                    print(f'        {x.name}  ({x.stat().st_size:,} byte)')
        print(f'   total berkas contoh: {n}')
    else:
        print('   ⚠️ UPLOAD_DIR tidak ada di kontainer ini')
except Exception as e:                                         # noqa: BLE001
    print(f'   ⚠️ {type(e).__name__}: {e}')
