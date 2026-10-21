"""UJI TAHAP 2.5b — KLIK CATATAN → NASKAH MELUNCUR (ACC Bos 24Sep26).

Yang diuji = ATURAN, bukan "tampilan bagus":
  1. Modul pencari menemukan bagian naskah dari isi catatan.
  2. Catatan kabur → TIDAK menemukan (jujur, jangan memaksa).
  3. Kata umum ("Metode") sendirian TIDAK boleh jadi dasar (nyasar).
  4. Halaman mengirim tombol HANYA untuk catatan yang ketemu.
  5. Halaman memberi tahu apa adanya untuk yang tidak ketemu.
  6. Teks asli (sorotan Tahap 3) dipakai DULUAN daripada tebakan.
  7. Naskah >1 berkas → pencarian menyeluruh + tahu berkas ke berapa.
"""
import sys

sys.path.insert(0, '/app')
from app import cari_bagian as CB

LULUS = GAGAL = 0


def cek(nama, syarat, sebab=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ GAGAL: {nama}  ({sebab})')


NASKAH = """BAB I
PENDAHULUAN
Latar belakang masalah penelitian ini belum menunjukkan kesenjangan
yang jelas antara harapan dan kenyataan di lapangan.

BAB III
METODE PENELITIAN
Penelitian ini menggunakan pendekatan kuantitatif. Populasi dalam
penelitian ini adalah seluruh account officer. Teknik sampling yang
digunakan belum dijelaskan secara rinci.

Tabel 3.1 menunjukkan jumlah sampel yang diambil dari setiap cabang.

BAB IV
HASIL DAN PEMBAHASAN
Berdasarkan hasil analisis, hipotesis H3 tidak terbukti secara signifikan.
"""

print('═' * 74)
print('  UJI TAHAP 2.5b — KLIK CATATAN → NASKAH MELUNCUR')
print('═' * 74)

#  ── 1. pencarian menemukan bagian yang benar ──────────────────────────
print('\n  ── 1. PENEMUAN BAGIAN ──')
r1 = CB.cari_bagian(NASKAH, 'Tabel 3.1 belum ada sumbernya.')
cek('1a Tabel 3.1 ketemu', r1 is not None)
cek('1b kutipan memuat Tabel 3.1', r1 and 'Tabel 3.1' in r1['kutipan'],
    f'{r1}')
cek('1c dasar = potongan catatan sendiri', r1 and r1['dasar'] == 'Tabel 3.1',
    f"{r1 and r1['dasar']}")

r2 = CB.cari_bagian(NASKAH, 'Hipotesis H3 tidak terbukti, mohon dicek.')
cek('1d hipotesis H3 ketemu di kalimat yang benar',
    r2 and 'tidak terbukti' in r2['kutipan'], f'{r2}')

#  ── 2. catatan kabur → JUJUR tidak ketemu ─────────────────────────────
print('\n  ── 2. KEJUJURAN (tidak memaksa) ──')
r3 = CB.cari_bagian(NASKAH, 'Paragraf ini kurang jelas maksudnya.')
cek('2a catatan kabur → None (jujur)', r3 is None, f'{r3}')
r4 = CB.cari_bagian(NASKAH, '')
cek('2b catatan kosong → None', r4 is None, f'{r4}')
r5 = CB.cari_bagian('', 'Tabel 3.1 belum ada sumbernya.')
cek('2c naskah kosong → None', r5 is None, f'{r5}')

#  ── 3. kata umum sendirian TIDAK jadi dasar (nyasar) ──────────────────
print('\n  ── 3. KATA UMUM JANGAN NYASAR ──')
r6 = CB.cari_bagian(NASKAH, 'Metode penelitian harus diperbaiki.')
cek('3a dasar BUKAN "Metode" sendirian',
    r6 is None or r6['dasar'].lower() != 'metode', f"{r6 and r6['dasar']}")
#  kata umum di daftar hitam
cek('3b "metode" ada di daftar kata umum', 'metode' in CB._KATA_UMUM)
cek('3c "hasil" ada di daftar kata umum', 'hasil' in CB._KATA_UMUM)
cek('3d "data" ada di daftar kata umum', 'data' in CB._KATA_UMUM)

#  ── 4. teks asli (sorotan Tahap 3) DIPAKAI DULUAN ─────────────────────
print('\n  ── 4. TEKS ASLI DIDAHULUKAN ──')
r7 = CB.cari_bagian(NASKAH, 'ini catatan yang salah arah sama sekali',
                    teks_asli='populasi dalam penelitian ini adalah seluruh account officer')
cek('4a teks asli dipakai', r7 is not None and r7['dasar'] == 'teks asli',
    f'{r7}')
cek('4b kutipan dari teks asli (bukan tebakan)',
    r7 and 'account officer' in r7['kutipan'], f'{r7}')

#  ── 5. toleransi spasi (naskah docx sering beda spasi) ────────────────
print('\n  ── 5. TOLERANSI SPASI/BARIS ──')
NASKAH2 = NASKAH.replace('Tabel 3.1', 'Tabel\n3.1')
r8 = CB.cari_bagian(NASKAH2, 'Tabel 3.1 belum ada sumbernya.')
cek('5a spasi/baris berbeda tetap ketemu', r8 is not None, f'{r8}')

#  ── 6. lebih dari satu berkas naskah ──────────────────────────────────
print('\n  ── 6. NASKAH LEBIH DARI SATU BERKAS ──')
r9 = CB.cari_di_banyak(['naskah A tanpa apa-apa', NASKAH],
                       'Tabel 3.1 belum ada sumbernya.')
cek('6a ketemu di berkas ke-2', r9 is not None and r9.get('berkas_ke') == 1,
    f'{r9}')
cek('6b berkas_ke = 1', r9 and r9.get('berkas_ke') == 1, f'{r9}')
r10 = CB.cari_di_banyak([], 'Tabel 3.1')
cek('6c tidak ada berkas → None', r10 is None, f'{r10}')

#  ── 7. bentuk hasil sesuai kontrak ────────────────────────────────────
print('\n  ── 7. BENTUK HASIL ──')
cek('7a ada kunci kutipan/dasar/ketemu',
    r1 and set(['kutipan', 'dasar', 'ketemu']).issubset(r1.keys()), f'{r1}')
cek('7b kutipan dibatasi panjangnya', r1 and len(r1['kutipan']) <= 300,
    f"{r1 and len(r1['kutipan'])}")

#  ── 8. naskah NYATA (dokumen sungguhan) ───────────────────────────────
print('\n  ── 8. NASKAH NYATA (dokumen sungguhan) ──')
from pathlib import Path
from app import ai as AI
#  ⚠️ DIPERBAIKI 24Sep26 (GAGAL PALSU, bukan bug aplikasi):
#  Versi lama mematok SATU berkas: /app/_uji_doc/proposal_v1_original.docx.
#  Berkas itu TIDAK ADA di image produksi (memang — `_uji_doc` cuma disalin
#  Wulan saat menguji di container uji). Jadi uji ini selalu GAGAL di
#  produksi walau APLIKASINYA BENAR.
#  Sebab kedua (yang lebih penting): uji WAJIB BERDIRI SENDIRI. Uji yang
#  bergantung pada berkas yang cuma ada kalau Wulan menyalinnya lebih dulu
#  itu uji RAPUH — dan pernah bikin Wulan salah lapor "regresi".
#  Sekarang: PAKAI BERKAS APA PUN YANG ADA, dan kalau TIDAK ADA berkas sama
#  sekali → LEWATI dengan jujur (bukan GAGAL).
KANDIDAT = [
    '/app/_uji_doc/proposal_v1_original.docx',
    '/app/_uji_doc/DISERTASI-S3-unhas-kesehatan-stunting.docx',
    '/app/_uji_doc/SKRIPSI-S1-unmul-fazrigading.docx',
    '/app/_uji_doc/TESIS-S2-unhas-sastra-novel.docx',
    '/app/_contoh-dokumen/proposal_v1_original.docx',
]
berkas_nyata = next((Path(p) for p in KANDIDAT if Path(p).is_file()), None)
if berkas_nyata is None:
    print('  ⏭️  LEWAT: tidak ada dokumen nyata di container ini '
          '(bukan kegagalan aplikasi)')
else:
    print(f'  (memakai {berkas_nyata.name})')
    teks = AI._teks_dari_berkas(berkas_nyata, berkas_nyata.name)
    #  Ambang 30.000 kar itu untuk PROPOSAL TESIS. Dokumen nyata bisa
    #  berbeda ukuran, jadi ambangnya disesuaikan ke ukuran NYATA berkasnya:
    #  yang penting teksnya TERBACA (bukan kosong), bukan panjang tertentu.
    cek('8a dokumen asli terbaca (bukan kosong)',
        len(teks) > 500, f'{len(teks)} kar')
    #  Cari istilah yang MEMANG ADA di naskah — diambil dari naskah itu
    #  sendiri, bukan kata yang Wulan karang dari ingatan. Kalau tidak
    #  ketemu, uji 8b dilewati dengan jujur.
    from app import sorotan as SR
    par = [p for p in SR.pecah_paragraf(teks) if len(p) > 80]
    if par:
        kalimat = par[0].strip()[:70]
        rn = CB.cari_bagian(teks, kalimat)
        cek('8b kalimat nyata dari naskah BISA ditemukan kembali',
            rn is not None, f'{kalimat[:40]!r} → {rn is not None}')
    rn2 = CB.cari_bagian(teks, 'xyzxyz tidak ada ini')
    cek('8c istilah karangan → None (jujur)', rn2 is None, f'{rn2}')

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
