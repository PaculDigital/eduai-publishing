"""UJI PEMBERSIH JAWABAN AI (bug fatal 16Sep26).

Membuktikan: jawaban AI yang menyalin naskah + penanda sistem TIDAK LAGI
masuk ke dokumen mahasiswa.

Dijalankan DI DALAM container produksi:
    docker exec -w /app eduai-app python3 _uji_pembersih.py
"""
import sys

sys.path.insert(0, '/app')

from app import ai as AI                       # noqa: E402
from app.versi import susun_ulang              # noqa: E402

# ── Jawaban AI ASLI hasil uji komentar pembimbing (yang MENGHANCURKAN) ─────
NASKAH_KIRIM = """DISERTASI
VARIASI SPASIAL DAN DETERMINAN STUNTING PADA BALITA
MINSARNAWATI
P1000316303
PROGRAM STUDI DOKTOR KESEHATAN MASYARAKAT
SEKOLAH PASCASARJANA
UNIVERSITAS HASANUDDIN
2020
Kata Pengantar
Assalamu'alaikum Warahmatullahi Wabarakatuh
Syukur Alhamdulillah penulis sampaikan ke hadirat Allah SWT"""

JAWABAN_RUSAK = """[PROFIL] Paradigma=kuantitatif; Desain=survei

[K1-CAKUPAN: dokumen]
Tidak ada perubahan yang perlu dilakukan berdasarkan catatan pembimbing; seluruh teks pada bagian awal naskah ini dipertahankan sesuai aslinya.

DISERTASI
VARIASI SPASIAL DAN DETERMINAN STUNTING PADA BALITA
MINSARNAWATI
P1000316303
PROGRAM STUDI DOKTOR KESEHATAN MASYARAKAT
SEKOLAH PASCASARJANA
UNIVERSITAS HASANUDDIN
2020
Kata Pengantar
Assalamu'alaikum Warahmatullahi Wabarakatuh
Syukur Alhamdulillah penulis sampaikan ke hadirat Allah SWT"""

# ── Jawaban AI yang BENAR (revisi nyata — HARUS tetap tersimpan) ──────────
JAWABAN_BENAR = """[PROFIL] Paradigma=kuantitatif; Desain=survei

[K1-CAKUPAN: paragraf]
Penelitian sebelumnya menunjukkan bahwa variasi spasial stunting dipengaruhi
oleh faktor lingkungan dan sosial-ekonomi (Rahman, 2021)."""


def main() -> int:
    lulus = gagal = 0
    print('═' * 74)
    print('UJI PEMBERSIH JAWABAN AI')
    print('═' * 74)

    # ── 1. Jawaban RUSAK harus jadi KOSONG (tidak ada revisi nyata) ──────
    print('\n── 1. Jawaban AI menyalin naskah + penanda (HARUS jadi kosong)')
    bersih = AI.bersihkan_jawaban_ai(JAWABAN_RUSAK, NASKAH_KIRIM)
    print(f'   panjang sebelum : {len(JAWABAN_RUSAK):,} kar')
    print(f'   panjang sesudah : {len(bersih):,} kar')
    print(f'   ada [PROFIL]    : {"[PROFIL]" in bersih}')
    print(f'   ada [K1-CAKUPAN]: {"[K1-CAKUPAN" in bersih}')
    print(f'   ada salinan     : {"MINSARNAWATI" in bersih}')
    print(f'   isi sisa        : {bersih[:120]!r}')
    ok = ('[PROFIL]' not in bersih and '[K1-CAKUPAN' not in bersih
          and 'MINSARNAWATI' not in bersih)
    print(f'   {"✅ LULUS" if ok else "❌ GAGAL"}')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # ── 2. Bukti: apa yang masuk dokumen sekarang? ───────────────────────
    print('\n── 2. Bukti nyata: ISI DOKUMEN setelah revisi')
    konten = AI.bersihkan_jawaban_ai(JAWABAN_RUSAK, NASKAH_KIRIM)
    sebelum = 'BAB I\nPendahuluan...\n\n'
    sesudah = '\n\nBAB III\nMetode...'
    hasil = susun_ulang(sebelum, konten or '(tidak ada perubahan)', sesudah)
    print('   ' + hasil.replace('\n', '\n   '))
    ok = ('[PROFIL]' not in hasil and 'MINSARNAWATI' not in hasil)
    print(f'   {"✅ LULUS — dokumen BERSIH" if ok else "❌ GAGAL — masih ada sampah"}')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # ── 3. Jawaban BENAR harus tetap UTUH (jangan kebablasan) ────────────
    print('\n── 3. Jawaban AI revisi NYATA (HARUS tetap tersimpan utuh)')
    bersih2 = AI.bersihkan_jawaban_ai(JAWABAN_BENAR, NASKAH_KIRIM)
    print(f'   isi: {bersih2[:150]!r}')
    print(f'   ada [PROFIL]    : {"[PROFIL]" in bersih2} (harus False)')
    print(f'   ada isi revisi  : {"variasi spasial" in bersih2.lower()}')
    ok = ('[PROFIL]' not in bersih2 and 'variasi spasial' in bersih2.lower()
          and len(bersih2) > 80)
    print(f'   {"✅ LULUS — revisi asli tidak ikut terbuang" if ok else "❌ GAGAL"}')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # ── 4. Salinan sebagian + revisi di dalamnya → simpan yg BARU saja ──
    print('\n── 4. AI salin naskah lalu revisi di dalamnya (ambil yg baru saja)')
    campur = (NASKAH_KIRIM + '\n\nPenambahan baru: variasi spasial stunting '
             'dipengaruhi faktor lingkungan menurut Rahman (2021).')
    bersih3 = AI.bersihkan_jawaban_ai(campur, NASKAH_KIRIM)
    print(f'   isi sisa: {bersih3[:160]!r}')
    ok = ('MINSARNAWATI' not in bersih3 and len(bersih3) > 20)
    print(f'   {"✅ LULUS — hanya bagian BARU yang disimpan" if ok else "❌ GAGAL"}')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # ── 5. Regresi: jawaban normal tanpa masalah harus tetap utuh ───────
    print('\n── 5. Regresi: jawaban normal (tanpa salinan) tetap utuh')
    normal = ('[PROFIL] Paradigma=kualitatif; Desain=fenomenologi\n\n'
              '[K1-CAKUPAN: sub-bab]\nPenelitian ini berfokus pada pemaknaan '
              'pengalaman guru dalam pembelajaran daring di daerah terpencil, '
              'sebagaimana dikemukakan oleh informan utama.')
    bersih4 = AI.bersihkan_jawaban_ai(normal, 'Teks naskah yang sama sekali lain.')
    print(f'   panjang: {len(bersih4)} kar')
    print(f'   isi: {bersih4[:120]!r}')
    ok = len(bersih4) > 100 and '[PROFIL]' not in bersih4
    print(f'   {"✅ LULUS" if ok else "❌ GAGAL"}')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    print('\n' + '═' * 74)
    print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
    print('═' * 74)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
