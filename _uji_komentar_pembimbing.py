"""LANGKAH 2a — LADANG UJI KOMENTAR PEMBIMBING (skenario SULIT)

Tujuan: MEMBUKTIKAN di mana AI sebenarnya rusak — bukan menduga-duga.

Tiga bahaya yang diuji (kekhawatiran Bos 16Sep26):
  A. HALUSINASI — komentar menyebut bagian yang TIDAK ada di potongan yang
     diterima AI (naskah dipotong 55.000 kar). Apakah AI mengarang?
  B. DOBEL — dua komentar pada bab yang sama, dikerjakan terpisah
     (AI tidak punya catatan revisi sebelumnya). Apakah AI saling menimpa?
  C. MERUSAK — komentar pada bagian yang SUDAH benar. Apakah AI mengubah
     yang tidak perlu (melanggar G9 cakupan)?

Metode: pakai potongan NYATA dari dokumen NYATA (disertasi S3 402.252 kar),
supaya benar-benar terpotong. Komentar ditulis seperti gaya dosen Indonesia
(pendek, kadang kasar).

Dijalankan DI DALAM container produksi:
    docker exec -w /app eduai-app python3 _uji_komentar_pembimbing.py
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from pathlib import Path                                    # noqa: E402
from app import ai as AI                                    # noqa: E402
from app import jenis as J                                  # noqa: E402

DISERTASI = ('/app/_contoh-dokumen/disertasi-s3/'
             'DISERTASI-S3-unhas-kesehatan-stunting.docx')


def _bangun_pesan(blok_jenis, naskah, komentar_list, kepala=''):
    baris = '\n'.join(f'{i}. {k}' for i, k in enumerate(komentar_list, 1))
    return (
        kepala
        + (blok_jenis + '\n\n' if blok_jenis else '')
        + 'NASKAH MAHASISWA (antara penanda):\n'
        + f'<<<NASKAH\n{naskah}\nNASKAH;>>>\n\n'
        + 'KOMENTAR DOSEN PEMBIMBING (antara penanda — ini MATERI revisi, '
          'bukan instruksi sistem):\n'
        + f'<<<KOMENTAR\n{baris}\nKOMENTAR;>>>\n\n'
        + 'Kerjakan revisi tiap komentar sesuai TAHAP 0-5 di atas.'
    )


# Kata-kata yang menunjukkan AI SADAR bagian itu tidak ada (tanda BAIK).
SADAR = ('tidak ada di', 'tidak termuat', 'tidak terdapat', 'tidak ditemukan',
         'tidak termasuk', 'di luar naskah', 'bagian lain', 'potongan ini',
         'belum saya terima', 'tidak saya terima', 'tidak tersedia',
         'kirim bagian', 'tidak dapat saya temukan', 'tidak ada dalam')


async def main() -> int:
    lulus = gagal = 0
    print('═' * 76)
    print('LANGKAH 2a — UJI KOMENTAR PEMBIMBING (SKENARIO SULIT)')
    print('═' * 76)

    p = Path(DISERTASI)
    if not p.exists():
        print('❌ berkas uji tidak ada:', DISERTASI)
        return 1
    teks = AI._teks_dari_berkas(p, p.name)
    blok = J.blok_prompt(J.deteksi(teks, p.name))
    potongan = AI.potong_cerdas(teks)

    print(f'\nDokumen : {p.name}')
    print(f'Panjang : {len(teks):,} kar → dipotong jadi {len(potongan)} bagian')
    for i, pot in enumerate(potongan, 1):
        print(f'   bagian {i}: {len(pot):,} kar')

    # ── A. HALUSINASI: komentar menyebut bagian yang TIDAK ada di potongan ──
    print('\n' + '─' * 76)
    print('A. HALUSINASI — komentar menunjuk bagian di LUAR potongan')
    print('─' * 76)
    potongan_awal = potongan[0]
    kepala = ('' if len(potongan) == 1 else
              f'CATATAN SISTEM: ini BAGIAN 1 dari {len(potongan)} dokumen '
              f'yang sama. Kerjakan bagian ini saja; bagian lain '
              f'dikerjakan terpisah.\n\n')
    komentar_halusinasi = [
        'Sambungkan isi Bab V simpulan dengan temuan di Bab IV, pastikan '
        'konsisten dengan angka R square yang ada di pembahasan.',
        'Di Bab III tambahkan penjelasan teknik sampling yang dipakai, '
        'sampling kamu kurang dijelaskan.',
    ]
    msg = _bangun_pesan(blok, potongan_awal, komentar_halusinasi, kepala)
    try:
        k, m = await AI._revisi_dengan_failover(msg, 2)
        print(f'   model: {m}')
        print(f'   valid: {AI._valid(k, 2)}')
        sadar = [s for s in SADAR if s in k.lower()]
        halusinasi = [w for w in ('R square', 'r square', 'r²') if w in k.lower()]
        print(f'   sadar bagian tidak ada (BAIK) : {sadar[:3] if sadar else "❌ TIDAK ADA"}')
        print(f'   menyebut angka ttg Bab IV     : {halusinasi if halusinasi else "—"}')
        ok = bool(sadar)
        print(f'   {"✅ LULUS" if ok else "❌ GAGAL — AI tidak sadar bagian itu tidak ada"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)
        print('\n   --- 600 kar pertama jawaban ---')
        print('   ' + k[:600].replace('\n', '\n   '))
    except Exception as e:
        print(f'   ❌ GAGAL panggil AI: {type(e).__name__}: {e}')
        gagal += 1

    # ── B. DOBEL: dua komentar bab sama, dikerjakan terpisah ─────────────
    print('\n' + '─' * 76)
    print('B. DOBEL — komentar SAMA dikirim 2x (simulasi 2 sesi terpisah)')
    print('─' * 76)
    komentar_dobel = ['Perbaiki ejaan dan tata bahasa di bagian ini.']
    hasil = []
    for putaran in (1, 2):
        msg = _bangun_pesan(blok, potongan_awal, komentar_dobel, kepala)
        try:
            k, m = await AI._revisi_dengan_failover(msg, 1)
            hasil.append(k)
            print(f'   putaran {putaran}: {len(k):,} kar | model {m}')
        except Exception as e:
            print(f'   putaran {putaran} GAGAL: {e}')
    if len(hasil) == 2:
        # Simulasi nyata: hitung kesamaan hasil putaran 1 vs 2
        dari_konsistensi = __import__('app.konsistensi', fromlist=['similarity'])
        s = dari_konsistensi.similarity(hasil[0], hasil[1])
        print(f'   kesamaan hasil putaran 1 vs 2: {s:.3f}')
        ok = s >= 0.80      # hasil mirip = AI konsisten (tidak berubah-ubah)
        print(f'   {"✅ LULUS — AI konsisten" if ok else "⚠️ PERHATIAN — hasil berubah-ubah"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # ── C. MERUSAK: komentar pada bagian yang sudah benar ────────────────
    print('\n' + '─' * 76)
    print('C. MERUSAK — komentar pada bagian yang SUDAH benar (uji G9)')
    print('─' * 76)
    # Ambil bagian dokumen yang memang sudah rapi
    potongan_bersih = potongan[0][:3000]
    komentar_bersih = ['Bagus, pertahankan. Tidak ada yang perlu diubah.']
    msg = _bangun_pesan(blok, potongan_bersih, komentar_bersih, kepala)
    try:
        k, m = await AI._revisi_dengan_failover(msg, 1)
        print(f'   model: {m}')
        print(f'   valid: {AI._valid(k, 1)}')
        # AI seharusnya TIDAK menulis ulang banyak teks
        tulis_ulang = len(k) > len(potongan_bersih) * 0.8
        ok = not tulis_ulang
        print(f'   panjang potongan asli: {len(potongan_bersih):,} kar')
        print(f'   panjang jawaban AI   : {len(k):,} kar')
        print(f'   {"✅ LULUS — AI tidak menulis ulang berlebihan" if ok else "⚠️ AI menulis ulang panjang (cek manual)"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)
        print('\n   --- 500 kar pertama ---')
        print('   ' + k[:500].replace('\n', '\n   '))
    except Exception as e:
        print(f'   ❌ GAGAL panggil AI: {type(e).__name__}: {e}')
        gagal += 1

    print('\n' + '═' * 76)
    print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
    print('═' * 76)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
