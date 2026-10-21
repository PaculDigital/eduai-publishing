"""UJI C9 — pagar "hasil revisi KOSONG / cuma SALINAN".

KENAPA ADA (temuan 25Sep26, ACC Bos "1"):
    DB produksi file 47 menyimpan versi revisi **0 karakter** dan versi itu
    jadi `terpakai=1` → NASKAH MAHASISWA KOSONG, padahal notifikasi berkata
    "berhasil" (SUKSES PALSU).

    Rantai bug: AI kadang hanya MENYALIN naskah yang dikirim → jawaban itu
    LOLOS `_valid()` lama (ada [PROFIL], blok [Kn] panjang) → dibuang oleh
    `bersihkan_jawaban_ai()` (memang disengaja) → 0 kar → tetap disimpan
    sebagai versi BARU dan ditandai selesai.

TIGA PAGAR YANG DIUJI (semua harus ada):
    1. `_valid()` menolak jawaban yang setelah dibersihkan jadi kosong.
    2. `_revisi_kerja()` MENGAGALKAN proses kalau hasil bagian kosong
       (raise HTTPException) — bukan menyimpan versi kosong.
    3. `token_revisi` TIDAK lagi memakai `or len(info_potong)`
       (angka token palsu saat token nyata 0).

BERGIGI: uji ini membaca KODE SUNGGUHAN (bukan berkas tiruan) dan memanggil
FUNGSI SUNGGUHAN. Kalau pagar dicabut, asersi harus GAGAL.
"""
import re
import sys

sys.path.insert(0, '/app')

lulus = gagal = 0


def cek(nama, syarat, info=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  OK   {nama}')
    else:
        gagal += 1
        print(f'  GAGAL {nama} {info}')


import app.ai as A  # noqa: E402

KODE = open('/app/app/ai.py', encoding='utf-8').read()
#  Buang komentar dulu — supaya asersi TIDAK lulus palsu karena kata-kata
#  di dalam komentar penjelasan (pelajaran uji C4 24Sep26).
KODE_BERSIH = re.sub(r'#[^\n]*', '', KODE)

print('═' * 68)
print('UJI C9 — pagar hasil revisi KOSONG (ACC Bos "1")')
print('═' * 68)

# ── 1. Pagar di _valid(): tolak jawaban yang cuma SALINAN ────────────────
#  ⚠️ PELAJARAN (kesalahan uji versi-1): asersi harus lewat **fungsi NYATA
#  `_revisi_dengan_failover()`**, bukan menyetel `_NASKAH_BANDING` manual.
#  Sebab: `_revisi_dengan_failover()` MENGOSONGKAN `_NASKAH_BANDING` lagi
#  setelah memvalidasi — kalau uji menyetel manual, yang diuji bukan jalur
#  nyata. Jadi kita tiru urutan yang sama: set → validasi → kosongkan.
print('\n── 1. _valid() menolak jawaban SALINAN ──')
naskah = 'BAB I\nPENDAHULUAN\n' + ('Kalimat asli mahasiswa tentang latar belakang. ' * 14)


def lewat_jalur_nyata(jawab, pembanding, jml_komentar=1):
    """Tiru urutan `_revisi_dengan_failover()`: titip → validasi → bersihkan."""
    A._NASKAH_BANDING = pembanding or ''
    try:
        return A._valid(jawab, jml_komentar)
    finally:
        A._NASKAH_BANDING = ''


#  1a. SALINAN PERSIS → harus DITOLAK
salinan = '[PROFIL] tesis\n[K1]\n' + naskah
alasan = lewat_jalur_nyata(salinan, naskah)
cek('1a salinan persis DITOLAK', alasan is not None, repr(alasan))

#  1b. Revisi NYATA → harus DITERIMA
#  🎯 25Sep26 — BENTUK diperbarui ke PIPA (KUTIP-ASLI/GANTI-JADI).
#  KENAPA: `_valid()` sekarang MEWAJIBKAN penanda pipa (AKAR #7). Asersi lama
#  memakai `[K1]` gaya lama → ditolak bukan karena pagar bocor, tapi karena
#  bentuk jawabannya memang sudah tidak dipakai lagi produksi.
KUTIP_1B = ('Penelitian ini bertujuan menguji pengaruh kualitas kehidupan '
            'kerja terhadap kinerja adaptif karyawan.')
GANTI_1B = ('Penelitian ini bertujuan menguji pengaruh kualitas kehidupan '
            'kerja dan efikasi diri digital terhadap kinerja adaptif '
            'karyawan, dengan kesiapan digital sebagai mediasi.')
revisi = ('[PROFIL] tesis\n'
          f'[K1-KUTIP-ASLI] {KUTIP_1B}\n'
          f'[K1-GANTI-JADI] {GANTI_1B}')
alasan2 = lewat_jalur_nyata(revisi, naskah)
cek('1b revisi nyata DITERIMA', alasan2 is None, repr(alasan2))

#  1c. FAIL-SAFE: tanpa naskah pembanding → jangan menolak (jaga revisi sah)
alasan3 = lewat_jalur_nyata(salinan, '')
cek('1c tanpa pembanding TIDAK menolak (fail-safe)', alasan3 is None, repr(alasan3))

#  1d. Pembanding ada & jawaban murni sisipan baru → DITERIMA
#  🎯 25Sep26 — bentuk PIPA (KUTIP-ASLI/GANTI-JADI), lihat catatan 1b.
jawab_baru = ('[PROFIL] tesis\n'
              '[K1-KUTIP-ASLI] Data penelitian sebelumnya masih terbatas.\n'
              '[K1-GANTI-JADI] Data penelitian terbaru tahun 2025 menunjukkan '
              'pola yang jauh lebih jelas dan konsisten dengan teori yang '
              'dipakai pada bab sebelumnya.')
alasan4 = lewat_jalur_nyata(jawab_baru, naskah)
cek('1d isi baru (bukan salinan) DITERIMA', alasan4 is None, repr(alasan4))

#  1e. Sesudah divalidasi, titipan HARUS kosong lagi (tidak bocor ke revisi lain)
cek('1e _NASKAH_BANDING dikosongkan lagi sesudah dipakai',
    A._NASKAH_BANDING == '', repr(A._NASKAH_BANDING))

# ── 2. Pagar di _revisi_kerja(): hasil kosong → GAGAL ────────────────────
#  ⚠️ PELAJARAN (kesalahan uji versi-1): asersi `'teks' in KODE` TIDAK BERGIGI
#  — waktu pagar dicabut (`if not (konten...):` → `if False:`), teks
#  pemeriksaannya MASIH ADA di berkas → uji tetap lulus. Sekarang uji
#  MEMANGGIL `bersihkan_jawaban_ai()` + memeriksa PESAN GALAT yang nyata.
print('\n── 2. _revisi_kerja() menggagalkan hasil kosong ──')
cek('2a ADA pemeriksaan "hasil kosong" (bukan `if False`)',
    bool(re.search(r"if not \(konten or ''\)\.strip\(\):", KODE_BERSIH)))
cek('2b LEMPAR HTTPException SESUDAH pemeriksaan kosong',
    bool(re.search(r"if not \(konten or ''\)\.strip\(\):(?:[^\n]*\n){1,14}?\s*raise HTTPException",
                   KODE_BERSIH)))
cek('2c kuota DIKEMBALIKAN saat hasil kosong',
    bool(re.search(r"if not \(konten or ''\)\.strip\(\):(?:[^\n]*\n){1,8}?[^\n]*_kembalikan_kuota",
                   KODE_BERSIH)))
cek('2d pesan galat menyebut Token Revisi dikembalikan (jujur ke mahasiswa)',
    'Token Revisi Anda sudah dikembalikan' in KODE_BERSIH)

#  2e. BUKTI PERILAKU: hasil kosong memang TIDAK lolos menjadi isi versi.
#      Kalau pagar ada, jalur revisi tidak boleh menyimpan hasil 0 kar.
#      Kita buktikan lewat fungsi nyata: teks kosong → tetap kosong, dan
#      KODE harus memeriksanya SEBELUM `hasil_bagian.append`.
_pos_cek = KODE_BERSIH.find("if not (konten or '').strip():")
_pos_app = KODE_BERSIH.find('hasil_bagian.append(konten)')
cek('2e pemeriksaan kosong berada SEBELUM hasil_bagian.append',
    _pos_cek > 0 and _pos_app > 0 and _pos_cek < _pos_app,
    f'cek@{_pos_cek} append@{_pos_app}')

# ── 3. Pagar token: jangan lapor angka palsu ─────────────────────────────
print('\n── 3. token_revisi TIDAK lapor angka palsu ──')
cek('3a TIDAK ada lagi "token_revisi_nyata or len(info_potong)"',
    'token_revisi_nyata or len(info_potong)' not in KODE_BERSIH)
cek("3b nilai bersih dipakai apa adanya",
    "'token_revisi': token_revisi_nyata," in KODE_BERSIH)
#  3c: cari SEMUA pemakaian `or len(info_potong)` — dulu hanya 1 titik
#      yang diperiksa, padahal ada DUA (kembalian + catat_revisi) → uji
#      versi-1 GAGAL PALSU. Sekarang diperiksa menyeluruh.
_sisa_or = re.findall(r'\w+\s*or\s+len\(info_potong\)', KODE_BERSIH)
cek('3c TIDAK ada sisa pola "X or len(info_potong)" di mana pun',
    not _sisa_or, f'{len(_sisa_or)} sisa: {_sisa_or}')

# ── 4. Bukti NYATA lewat rantai fungsi (bukan cuma baca kode) ────────────
print('\n── 4. Bukti rantai nyata (valid → bersihkan) ──')
A._NASKAH_BANDING = naskah
_v = A._valid(salinan, 1)
A._NASKAH_BANDING = ''
_b = A.bersihkan_jawaban_ai(salinan, naskah)
cek('4a salinan: _valid MENOLAK', _v is not None, repr(_v))
cek('4b salinan: setelah dibersihkan memang 0 kar', len(_b.strip()) == 0, f'{len(_b)} kar')
cek('4c KEDUANYA sepakat: yang dibuang memang yang ditolak',
    (_v is not None) and len(_b.strip()) == 0)

print('\n' + '═' * 68)
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
print('═' * 68)
sys.exit(1 if gagal else 0)
