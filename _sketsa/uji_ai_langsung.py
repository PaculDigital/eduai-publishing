"""UJI LANGSUNG: panggil AI nyata dgn naskah Bos + komentar pembimbing.

KENAPA: proses 103 gagal "hasil kosong" (token_in=0). Kode berhenti di
    pagar C9 SETELAH `bersihkan_jawaban_ai()`. Jadi pertanyaannya:
      (a) AI benar-benar kembalikan SALINAN naskah (tidak merevisi)?
      (b) AI menjawab BAIK, tapi `bersihkan_jawaban_ai()` MEMBUANG semuanya?
    Uji ini memanggil AI dan mencetak jawaban MENTAH + hasil sesudah pembersih.
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from app.ai import (AI_POTONG_KARAKTER, _revisi_dengan_failover,   # noqa: E402
                    _teks_dari_docx, bersihkan_jawaban_ai, potong_cerdas)
import pathlib                                                     # noqa: E402

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
KOMENTAR = ['Paragraf ini perlu ditajamkan: rumusan masalah belum menyebut '
            'kesenjangan penelitian.']

print('═' * 74)
print('UJI LANGSUNG — AI NYATA')
print('═' * 74)

t = _teks_dari_docx(DOCX)
bagian = potong_cerdas(t)
print(f'naskah   : {len(t):,} kar → {len(bagian)} bagian')
print(f'komentar : {KOMENTAR}')
print()

potongan = bagian[0]
print(f'── bagian 1: {len(potongan):,} kar ─────────────────────────────')

user_msg = (
    'NASKAH MAHASISWA:\n' + potongan + '\n\n'
    'CATATAN PEMBIMBING:\n- ' + '\n- '.join(KOMENTAR) + '\n\n'
    'Perbaiki naskah sesuai catatan. Kembalikan SELURUH naskah hasil '
    'perbaikan (bukan ringkasan, bukan hanya bagian yang diubah).'
)

print('memanggil AI (tunggu…)')
try:
    konten, model, info = asyncio.run(
        _revisi_dengan_failover(user_msg, len(KOMENTAR), naskah_banding=potongan))
except Exception as e:                                             # noqa: BLE001
    print(f'❌ PANGGILAN AI GAGAL: {type(e).__name__}: {e}')
    raise SystemExit(1)

print(f'✅ AI MENJAWAB')
print(f'   model     : {model}')
print(f'   token in  : {info.get("token_in"):,}')
print(f'   token out : {info.get("token_out"):,}')
print(f'   panjang mentah : {len(konten):,} kar')
print()
print('   --- 500 kar PERTAMA jawaban mentah ---')
print('   ' + konten[:500].replace('\n', '\n   '))

bersih = bersihkan_jawaban_ai(konten, potongan)
print()
print(f'   panjang SESUDAH pembersih : {len(bersih):,} kar')
print(f'   kosong?                   : {not bersih.strip()}')
print()
if not bersih.strip():
    print('  🚨 KOSONG SESUDAH PEMBERSIH → inilah yang menggagalkan proses.')
    print('     Berarti `bersihkan_jawaban_ai()` MEMBUANG jawaban yang sah.')
    print()
    print('   --- 800 kar jawaban mentah (untuk memeriksa penanda) ---')
    print('   ' + konten[:800].replace('\n', '\n   '))
else:
    print('  ✅ ADA ISI — pagar C9 tidak seharusnya menggagalkan.')
    print('   --- 400 kar sesudah pembersih ---')
    print('   ' + bersih[:400].replace('\n', '\n   '))
