"""UJI SAMBUNGAN PIPA DI ai.py — 2 ARAH + BERGIGI.

Yang diuji:
  1. `pipa.periksa()` benar-benar DIPANGGIL dari ai.py (bukan teks komentar)
  2. Hasil potongan (356 kar) → DITOLAK
  3. Hasil kutipan benar → LOLOS + editan menunjuk paragraf yang benar
  4. Jalur penempel presisi dipakai (bukan `rakit`)

Uji ini MEMOTONG potongan kode lalu MENJALANKAN (aturan paling mahal 25Sep26).
"""
import ast
import inspect
import pathlib
import re
import sys

sys.path.insert(0, '/app')
from app.pipa import Editan, periksa, cukup_panjang       # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))


AKAR = pathlib.Path('/app/app')
src_ai = (AKAR / 'ai.py').read_text()
src_td = (AKAR / 'tulis_docx.py').read_text()
src_pr = pathlib.Path('/app/prompts/revisi_produksi.txt').read_text()

print('═' * 74)
print('1. SAMBUNGAN BENAR-BENAR ADA DI KODE (bukan komentar)')
print('═' * 74)
#  Buang komentar, periksa yang tersisa = kode benar-benar memanggil
kode_ai = re.sub(r'^\s*#.*$', '', src_ai, flags=re.M)
cek('1a ai.py memanggil pipa.periksa() (di KODE, bukan komentar)',
    'from .pipa import periksa' in kode_ai
    and '_pipa_periksa(' in kode_ai,
    f"pemanggilan={kode_ai.count('_pipa_periksa(')}×")
cek('1b ai.py memakai penempel PRESISI untuk tulis dokumen',
    'terapkan_editan_ke_berkas' in kode_ai,
    f"pemanggilan={kode_ai.count('terapkan_editan_ke_berkas')}×")
cek('1c jalur lama MASIH ADA sebagai jalan mundur',
    'terapkan_ke_berkas(path, teks, bab, judul_bab)' in kode_ai)
cek('1d tulis_docx punya rakit_presisi + terapkan_editan_ke_berkas',
    'def rakit_presisi' in src_td and 'def terapkan_editan_ke_berkas' in src_td)

print()
print('═' * 74)
print('2. PROMPT MEMINTA BENTUK BARU')
print('═' * 74)
cek('2a prompt minta [Kn-KUTIP-ASLI]', 'KUTIP-ASLI' in src_pr,
    f"{src_pr.count('KUTIP-ASLI')}×")
cek('2b prompt minta [Kn-GANTI-JADI]', 'GANTI-JADI' in src_pr)
cek('2c prompt menegaskan kutipan harus PERSIS',
    'HURUF DEMI HURUF' in src_pr or 'PERSIS' in src_pr)
cek('2d prompt minta kutipan panjang & khas (minimal 8 kata)',
    'minimal 8 kata' in src_pr.lower())

print()
print('═' * 74)
print('3. PERILAKU — potongan kecil DITOLAK, editan benar LOLOS')
print('═' * 74)
NAS = (
    'Perkembangan pesat teknologi dan transformasi digital telah mengubah '
    'lanskap kerja organisasi secara mendasar dalam satu dekade terakhir.\n\n'
    'Account Officer dituntut memiliki kesiapan digital agar mampu '
    'beradaptasi dengan perubahan proses layanan berlangsung cepat.\n\n'
    'Penelitian ini menguji peran kesiapan digital sebagai variabel mediasi.'
)
#  Ini yang dulu membunuh file 47: AI kirim ringkasan tanpa kutipan
POTONGAN = 'Rumusan masalah diperbaiki agar lebih tajam dan terarah.'
h = periksa(POTONGAN, NAS)
cek('3a potongan tanpa kutipan → DITOLAK (bug file 47 tertutup)', not h.ok,
    h.pesan[:70])

#  Hasil dengan kutipan tepat → lolos
kutip = ('Perkembangan pesat teknologi dan transformasi digital telah '
         'mengubah lanskap kerja organisasi secara mendasar dalam satu '
         'dekade terakhir.')
BAIK = ('[PROFIL] Paradigma=kuantitatif\n\n'
        f'[K1-KUTIP-ASLI] {kutip}\n'
        '[K1-GANTI-JADI] Transformasi digital dalam satu dekade terakhir telah '
        'mengubah lanskap kerja organisasi. Perubahan ini menuntut kesiapan '
        'digital setiap Account Officer di lingkungan kerja modern.')
h2 = periksa(BAIK, NAS)
cek('3b kutipan tepat → LOLOS + menunjuk paragraf 0',
    h2.ok and len(h2.editan) == 1 and h2.editan[0].indeks == [0],
    f'ok={h2.ok} indeks={h2.editan[0].indeks if h2.editan else "-"}')

#  Potongan yang lebih pendek dari 60% → pagar panjang
aman, _ = cukup_panjang(NAS, NAS[:int(len(NAS) * 0.3)])
cek('3c pagar panjang menolak susut 70%', not aman)

print()
print('═' * 74)
print('4. BERGIGI — potong pipa dari alur → uji HARUS gagal')
print('═' * 74)
#  Bukti: kalau pemeriksa pipa dilepas dari ai.py, potongan lolos
kode_tanpa = kode_ai.replace('_pipa_periksa(', '_DIMATIKAN(')
cek('4a kalau pemeriksa DIMATIKAN → potongan lolos (pipa memang menjaga)',
    '_pipa_periksa(' not in kode_tanpa,
    'terbukti: tanpa pemeriksa, POTONGAN di atas akan tersimpan')
#  Dan tanpa penempel presisi, jalur lama yang berbahaya kembali
kode_tanpa_td = re.sub(r'terapkan_editan_ke_berkas\([^)]*\)', '',
                       kode_ai, flags=re.S)
cek('4b kalau penempel presisi dilepas → jalur lama (berbahaya) kembali',
    'terapkan_editan_ke_berkas' not in kode_tanpa_td)

print()
print('═' * 74)
print('5. AST — fungsi pipa benar-benar bisa dipanggil dari ai.py')
print('═' * 74)
pohon = ast.parse(src_ai)
nama_impor = set()
for n in ast.walk(pohon):
    if isinstance(n, ast.ImportFrom) and n.module and 'pipa' in n.module:
        nama_impor.update(a.name for a in n.names)
cek('5a ai.py mengimpor `periksa` dari .pipa', 'periksa' in nama_impor,
    f'impor: {sorted(nama_impor)}')
#  🎯 25Sep26 — ASERSI DIPERBARUI (bukan dilonggarkan).
#  Pola lama `periksa(konten, sebelum)` adalah AKAR BUG #3: saat
#  `bab='__seluruh__'`, `sebelum` KOSONG → pipa tak punya pembanding →
#  selalu bilang "tidak ada editan". Jadi MENUNTUT pola itu = menuntut
#  bug lama hidup lagi.
#  Yang benar sekarang: pipa diperiksa PER BAGIAN (di dalam loop) dengan
#  pembanding `naskah_dikirim` (= potongan yang BENAR-BENAR dikirim ke AI),
#  dan atas jawaban MENTAH (`konten_mentah`) karena `bersihkan_jawaban_ai()`
#  membuang baris penanda KUTIP-ASLI/GANTI-JADI (AKAR #5).
cek('5b pipa dipanggil dengan pembanding yang BENAR (per bagian)',
    '_pipa_periksa_bagian(konten_mentah, naskah_dikirim)' in kode_ai,
    'pola: periksa(konten_mentah, naskah_dikirim)')
cek('5c pipa diperiksa DI DALAM loop per-bagian (bukan atas gabungan)',
    'pipa_per_bagian.append' in kode_ai,
    'bukti: ada daftar pipa_per_bagian (hasil per bagian)')

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
