"""LIHAT: apa yg pipa terima SEKARANG saat bab='__seluruh__'.

Bukti kegagalan: "PIPA: tidak ada editan" padahal pembanding sudah diisi.
⇒ cetak `konten` (jawaban AI) + `naskah_dikirim` yang benar-benar terbentuk.
"""
import asyncio
import os
import pathlib
import sys

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
from app.config import UPLOAD_DIR                                     # noqa: E402
from app.pipa import periksa                                          # noqa: E402

P = pathlib.Path(UPLOAD_DIR) / '6' / '468d8078aa53e471.docx'
naskah = A._teks_dari_berkas(P, 'naskah_bos.docx').strip()
bagian = A.potong_cerdas(naskah)
jml = len(bagian)
print(f'naskah {len(naskah):,} kar → {jml} bagian\n')

KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas dan tambahkan penekanan pada tujuan '
            'penelitian.']
baris_komentar = '- ' + KOMENTAR[0]

for idx, potongan in enumerate(bagian, start=1):
    kepala = ('' if jml == 1 else
              f'CATATAN SISTEM: ini BAGIAN {idx} dari {jml} dokumen yang sama. '
              f'Kerjakan bagian ini saja; bagian lain dikerjakan terpisah.\n\n')
    user_msg = (kepala +
                f'NASKAH MAHASISWA (antara penanda):\n'
                f'<<<NASKAH\n{potongan}\nNASKAH;>>>\n\n'
                f'KOMENTAR DOSEN PEMBIMBING (antara penanda):\n'
                f'<<<KOMENTAR\n{baris_komentar}\nKOMENTAR;>>>\n\n'
                f'Kerjakan revisi tiap komentar sesuai TAHAP 0-3 di atas.')
    konten, model, info = asyncio.run(A._revisi_dengan_failover(
        user_msg, len(KOMENTAR), naskah_banding=potongan))
    print(f'═══ BAGIAN {idx}/{jml} — jawaban AI {len(konten):,} kar ═══')
    print(f'   300 kar pertama:')
    print('   ' + konten[:300].replace('\n', '\n   '))
    print()
    #  ── apa yang pipa lihat? ──
    h = periksa(konten, potongan)
    print(f'   pipa(potongan benar) : ok={h.ok} editan={len(h.editan)} '
          f'cakupan={h.cakupan!r}')
    print(f'      pesan={h.pesan[:130]!r}')
    h2 = periksa(konten, '')
    print(f'   pipa("" kosong)      : ok={h2.ok} editan={len(h2.editan)} '
          f'pesan={h2.pesan[:80]!r}')
    print()
