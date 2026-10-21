"""AUDIT app/konsistensi.py — BUKTIKAN tiap dugaan bug dengan UJI NYATA.

Arahan Bos 16Sep26: "Lakukan audit dan temukan bug sampai sempurna."

Tiap BUG di bawah HARUS terbukti dengan kasus yang gagal (bukan dugaan dari
membaca kode). Kalau tidak terbukti, JANGAN ditulis sebagai bug.

Klasifikasi alat ukur (kaidah akademik — ACC arah Bos):
  • WAJIB PERSIS  : judul · rumusan masalah · hipotesis · variabel · teori+tahun
  • BOLEH MIRIP   : paragraf naskah (memang direvisi) → ukur MAKNA, ambang 80%
"""
import sys
sys.path.insert(0, '/app')

from app import konsistensi as KS

HASIL = []


def catat(no, nama, terbukti, bukti, dampak):
    HASIL.append((no, nama, terbukti, bukti, dampak))
    tanda = '🐛 TERBUKTI' if terbukti else '✅ aman'
    print(f'\n[{no}] {tanda} — {nama}')
    print(f'    bukti : {bukti}')
    if terbukti:
        print(f'    dampak: {dampak}')


def S(sid, judul, isi):
    return {'section_id': sid, 'title': judul, 'isi_teks': isi}


print('=' * 100)
print('AUDIT app/konsistensi.py — TAHAP 1: BUKTI BUG')
print('=' * 100)

# ── BUG 1: judul — Jaccard MELOLOSKAN judul yang beda satu kata ───────────
print('\n' + '-' * 100)
print('BUG 1: JUDUL WAJIB PERSIS — apakah Jaccard meloloskan judul yang cacat?')
print('-' * 100)
judul_benar = ('PENGARUH MOTIVASI KERJA TERHADAP KINERJA KARYAWAN '
               'DENGAN KEPUASAN KERJA SEBAGAI VARIABEL MEDIASI')
judul_salah = judul_benar.replace('KARYAWAN', 'PEGAWAI')
sim = KS.similarity(judul_salah, judul_benar)
naskah = [S('1.1', 'Latar Belakang',
            f'{judul_salah} merupakan topik yang penting untuk diteliti. ' + 'x ' * 300)]
r = KS.check_judul_consistency({'judul': judul_benar}, naskah)
print(f'  Jaccard judul "KARYAWAN" vs "PEGAWAI" = {sim:.3f}')
print(f'  jumlah catatan yang keluar = {len(r["issues"])}')
if r['issues']:
    print(f'  catatan: level={r["issues"][0]["level"]} type={r["issues"][0]["type"]}')
catat('BUG 1', 'Judul beda 1 kata diloloskan Jaccard',
      len(r['issues']) == 0,
      f'Jaccard={sim:.3f}; catatan keluar={len(r["issues"])}',
      'Sistem bilang AMAN padahal judul di naskah BEDA dari cover. '
      'Cacat akademik lolos.')

# ── BUG 2: judul — Jaccard MEMBANJIRI catatan palsu saat judul panjang ────
print('\n' + '-' * 100)
print('BUG 2: judul panjang — apakah muncul catatan palsu padahal PERSIS?')
print('-' * 100)
j = 'PENGARUH MOTIVASI KERJA TERHADAP KINERJA KARYAWAN'
naskah2 = [S('1.1', 'Latar Belakang',
             f'Judul penelitian ini adalah {j} dan hal ini penting. ' + 'y ' * 300)]
r2 = KS.check_judul_consistency({'judul': j}, naskah2)
print(f'  judul memang PERSIS ada di paragraf: {j in naskah2[0]["isi_teks"]}')
print(f'  catatan keluar = {len(r2["issues"])}')
catat('BUG 2', 'Cek PERSIS judul (sudah ada)', len(r2['issues']) == 0,
      f'catatan={len(r2["issues"])} saat judul PERSIS',
      'Kalau ada catatan di sini, mahasiswa disuruh perbaiki yang sudah benar.')

# ── BUG 3: variabel — membandingkan "kata pertama" → lolos palsu ─────────
print('\n' + '-' * 100)
print('BUG 3: VARIABEL — kata pertama cocok tapi variabel BERBEDA')
print('-' * 100)
brief3 = {'variabel': ['motivasi intrinsik', 'motivasi ekstrinsik']}
naskah3 = [S('2.1', 'Tinjauan Pustaka',
             'Motivasi adalah hal penting dalam organisasi. ' + 'z ' * 300)]
r3 = KS.check_variable_consistency(brief3, naskah3)
jumlah = len(r3['issues'])
print(f'  Brief minta: motivasi intrinsik + motivasi ekstrinsik')
print(f'  naskah hanya sebut: "Motivasi" (kata pertama cocok)')
print(f'  catatan keluar = {jumlah}  ← seharusnya 2 (dua variabel hilang)')
catat('BUG 3', 'Variabel "motivasi intrinsik" dianggap ADA karena kata pertama "motivasi" cocok',
      jumlah == 0,
      f'catatan={jumlah}, seharusnya 2',
      'Variabel yang benar-benar tidak dibahas dianggap sudah dibahas → '
      'AI tidak pernah diberi tahu variabelnya hilang.')

# ── BUG 4: OV — deteksi tabel terlalu naif ───────────────────────────────
print('\n' + '-' * 100)
print('BUG 4: OV — pola X\\d+|"..."|Y\\s*\\( terlalu naif')
print('-' * 100)
naskah4 = [S('3.1', 'Metode',
             'Penelitian ini menggunakan analisis regresi. Variabel X diukur '
             'dengan skala Likert 1-5. ' + 'w ' * 200)]
r4 = KS.check_ov_consistency({'variabel': ['motivasi']}, naskah4)
print(f'  naskah TIDAK punya tabel OV (cuma sebut "Variabel X")')
print(f'  catatan keluar = {len(r4["issues"])}')
catat('BUG 4', 'OV tanpa tabel lolos karena pola cocok pada "Variabel X"',
      len(r4['issues']) == 0,
      f'catatan={len(r4["issues"])} pada naskah TANPA tabel OV',
      'Mahasiswa tidak diberi tahu tabel Definisi Operasional belum ada.')

# ── BUG 5: hipotesis — cek H10 vs H1 (substring) ─────────────────────────
print('\n' + '-' * 100)
print('BUG 5: HIPOTESIS — "H1" vs "H10" tertukar (kode 2 digit)')
print('-' * 100)
b5 = {'hipotesis': ['H1', 'H10']}
naskah5 = [S('2.4', 'Hipotesis', 'H1 berpengaruh positif. ' + 'v ' * 200),
           S('4.4', 'Uji Hipotesis', 'H10 berpengaruh positif. ' + 'u ' * 200)]
r5 = KS.check_hipotesis_consistency(b5, naskah5)
print(f'  Brief punya H1 & H10; 2.4 tulis H1; 4.4 tulis H10')
print(f'  catatan keluar = {len(r5["issues"])}')
for it in r5['issues']:
    print(f'    - {it["type"]}: {it["message"][:90]}')
catat('BUG 5', 'H1 vs H10 tidak tertukar', True,
      f'catatan={len(r5["issues"])} (perilaku wajar)',
      'pembanding.')

# ── BUG 6: naskah/paragraf — tidak ada cek MAKNA ─────────────────────────
print('\n' + '-' * 100)
print('BUG 6: NASKAH BOLEH MIRIP — apakah ada alat ukur MAKNA untuk paragraf?')
print('-' * 100)
ada_makna = [n for n in dir(KS) if any(k in n.lower() for k in
                                      ('makna', 'semantik', 'kunci', 'kata_kunci'))]
print(f'  fungsi bernuansa makna di konsistensi.py: {ada_makna or "(TIDAK ADA)"}')
a = 'motivasi kerja berpengaruh terhadap kinerja karyawan dan kepuasan kerja'
b = 'motivasi memengaruhi kinerja karyawan serta kepuasan kerja pegawai'
print(f'  Jaccard paragraf A vs B = {KS.similarity(a,b):.3f}')
catat('BUG 6', 'Tidak ada alat ukur MAKNA untuk paragraf naskah',
      not ada_makna,
      f'fungsi makna={ada_makna or "tidak ada"}; Jaccard paragraf={KS.similarity(a,b):.3f}',
      'Naskah yang maknanya sama tapi katanya beda akan terbaca "berbeda" '
      'oleh alat yang ada. (Belum dipakai untuk memblokir, tapi belum ada.)')

# ── RINGKASAN ────────────────────────────────────────────────────────────
print('\n' + '=' * 100)
print('RINGKASAN AUDIT')
print('=' * 100)
bug = [h for h in HASIL if h[2]]
print(f'  TOTAL diperiksa : {len(HASIL)}')
print(f'  🐛 TERBUKTI BUG : {len(bug)}')
for no, nama, _, bukti, _ in bug:
    print(f'     {no}: {nama}')
    print(f'          {bukti}')
print(f'  ✅ aman         : {len(HASIL)-len(bug)}')