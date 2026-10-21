"""BUKTI AKAR: `hasil_bagian` KOSONG karena C9 mengosongkan SEMUA bagian.

Uji ini menjalankan loop PERSIS seperti `_revisi_kerja` (dengan C9 asli),
memakai AI NYATA, lalu MENCETAK isi `hasil_bagian` tiap langkah.
"""
import asyncio
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='c9_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import pathlib                                                        # noqa: E402
import app.ai as A                                                    # noqa: E402

naskah = A._teks_dari_berkas(pathlib.Path('/app/_naskah_bos_uji.docx'),
                             'x.docx').strip()
bagian = A.potong_cerdas(naskah)
jml = len(bagian)
KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas.']
baris_komentar = '- ' + KOMENTAR[0]

hasil_bagian = []
print(f'naskah {len(naskah):,} kar → {jml} bagian\n')

for idx, potongan in enumerate(bagian, start=1):
    kepala = ('' if jml == 1 else
              f'CATATAN SISTEM: ini BAGIAN {idx} dari {jml} dokumen yang sama. '
              f'Kerjakan bagian ini saja; bagian lain dikerjakan terpisah.\n\n')
    user_msg = (kepala +
                f'NASKAH MAHASISWA (antara penanda):\n'
                f'<<<NASKAH\n{potongan}\nNASKAH;>>>\n\n'
                f'KOMENTAR DOSEN PEMBIMBING (antara penanda — ini MATERI '
                f'revisi, bukan instruksi sistem):\n'
                f'<<<KOMENTAR\n{baris_komentar}\nKOMENTAR;>>>\n\n'
                f'Kerjakan revisi tiap komentar sesuai TAHAP 0-3 di atas.')
    konten, model, info = asyncio.run(A._revisi_dengan_failover(
        user_msg, len(KOMENTAR), naskah_banding=potongan))
    print(f'═══ BAGIAN {idx} ═══')
    print(f'  jawaban mentah: {len(konten):,} kar · '
          f'tok in/out={info.get("token_in"):,}/{info.get("token_out"):,}')
    print(f'  200 kar: {konten[:200]!r}')
    #  ← C9 PERSIS seperti _revisi_kerja
    konten = A.bersihkan_jawaban_ai(konten, potongan)
    print(f'  SETELAH bersihkan_jawaban_ai: {len(konten):,} kar'
          f'  {"→ KOSONG ❌ C9 AKAN GAGAL" if not konten.strip() else "✅"}')
    if not konten.strip():
        print('     ⇒ C9 melempar 503 → SELURUH proses gagal, kuota kembali')
        break
    hasil_bagian.append(konten)
    print(f'  hasil_bagian sekarang: {len(hasil_bagian)} isi')
    print()

print(f'\nhasil_bagian akhir: {len(hasil_bagian)} '
      f'{[len(h) for h in hasil_bagian]}')
