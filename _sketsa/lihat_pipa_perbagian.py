"""CETAK: apa yg pipa per bagian TERIMA di jalur nyata.

Karena jalur nyata bilang "tidak ada blok KUTIP-ASLI/GANTI-JADI", padahal
bagian 1 jawabannya ADA blok itu → ada yg salah di `konten` / `naskah_dikirim`.
"""
import sys

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
from app.pipa import periksa                                          # noqa: E402

#  ── Bungkus pipa supaya terlihat argumennya ──
_asli = periksa
import app.pipa as _P                                                 # noqa: E402


def pipa_wrap(konten, naskah=None):
    print(f'   [PIPA] konten={len(konten or ""):,} kar · '
          f'naskah={len(naskah or ""):,} kar')
    print(f'        konten 120: {(konten or "")[:120]!r}')
    r = _asli(konten, naskah)
    print(f'        → ok={r.ok} editan={len(r.editan)} pesan={r.pesan[:80]!r}')
    return r


_P.periksa = pipa_wrap
A._pipa_periksa_bagian = pipa_wrap

#  ── Jalankan tiruan loop (sama spt _revisi_kerja) ──
import asyncio                                                        # noqa: E402
import pathlib                                                        # noqa: E402
from app.config import UPLOAD_DIR                                     # noqa: E402

naskah = A._teks_dari_berkas(
    pathlib.Path(UPLOAD_DIR) / '6' / '468d8078aa53e471.docx', 'x.docx').strip()
bagian = A.potong_cerdas(naskah)
jml = len(bagian)

KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas dan tambahkan penekanan pada tujuan '
            'penelitian.']
baris_komentar = '- ' + KOMENTAR[0]

print(f'naskah {len(naskah):,} kar → {jml} bagian\n')
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
    print(f'═══ BAGIAN {idx} ═══ jawaban {len(konten):,} kar')
    bersih = A.bersihkan_jawaban_ai(konten, potongan)
    print(f'   bersih {len(bersih):,} kar · 90 kar: {bersih[:90]!r}')
    print('   → pipa:')
    r = periksa(bersih, potongan)
    print(f'   hasil: ok={r.ok} editan={len(r.editan)}')
    print()
