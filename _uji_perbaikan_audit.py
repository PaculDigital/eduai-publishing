"""VERIFIKASI PERBAIKAN audit konsistensi — BUKTIKAN bug tertutup.
Jalankan: docker exec -w /app eduai-app python3 _uji_perbaikan_audit.py
"""
import sys
sys.path.insert(0, '/app')
from app import konsistensi as KS

lolos = gagal = 0


def t(nama, syarat, bukti=''):
    global lolos, gagal
    if syarat:
        lolos += 1
        print(f'  ✅ {nama}')
    else:
        gagal += 1
        print(f'   {nama}  ← {bukti}')


def S(sid, judul, isi):
    return {'section_id': sid, 'title': judul, 'isi_teks': isi}


print('=' * 96)
print('VERIFIKASI PERBAIKAN — BUG 1: JUDUL WAJIB PERSIS')
print('=' * 96)
jb = ('PENGARUH MOTIVASI KERJA TERHADAP KINERJA KARYAWAN '
      'DENGAN KEPUASAN KERJA SEBAGAI VARIABEL MEDIASI')
js = jb.replace('KARYAWAN', 'PEGAWAI')

# 1a. judul PERSIS → tidak ada catatan
r = KS.check_judul_consistency({'judul': jb}, [S('1.1', 'LB', f'Judul: {jb}. ' + 'x ' * 300)])
t('judul PERSIS = tidak ada catatan', len(r['issues']) == 0, f'catatan={len(r["issues"])}')

# 1b. judul beda 1 kata → HARUS ada catatan (dulu lolos!)
r = KS.check_judul_consistency({'judul': jb}, [S('1.1', 'LB', f'{js} penting. ' + 'x ' * 300)])
t('judul beda 1 kata (KARYAWAN→PEGAWAI) MUNCUL catatan',
  len(r['issues']) == 1 and r['issues'][0]['type'] == 'judul_hampir_persis',
  f'catatan={len(r["issues"])}')

# 1c. judul sama sekali beda → tidak ada catatan (bukan tugas section itu)
r = KS.check_judul_consistency({'judul': jb}, [S('1.1', 'LB', 'Pembahasan lain. ' + 'x ' * 300)])
t('section tanpa judul = tidak dipaksa (jangan ganggu user)', len(r['issues']) == 0,
  f'catatan={len(r["issues"])}')

# 1d. typo ringan (spasi ganda) → warning, bukan lolos
r = KS.check_judul_consistency({'judul': jb}, [S('1.1', 'LB', f'Judul : {jb} . ' + 'x ' * 300)])
t('spasi/tanda baca ringan tetap dianggap PERSIS', len(r['issues']) == 0,
  f'catatan={len(r["issues"])}')

print()
print('=' * 96)
print('VERIFIKASI PERBAIKAN — BUG 3: VARIABEL FRASA UTUH')
print('=' * 96)
b = {'variabel': ['motivasi intrinsik', 'motivasi ekstrinsik']}

# 3a. naskah cuma "motivasi" → HARUS 2 catatan (dulu 0!)
r = KS.check_variable_consistency(b, [S('2.1', 'TP', 'Motivasi itu penting. ' + 'z ' * 300)])
t('naskah cuma menyebut "motivasi" → 2 catatan muncul', len(r['issues']) == 2,
  f'catatan={len(r["issues"])}')

# 3b. variabel disebut UTUH → tidak ada catatan
r = KS.check_variable_consistency(
    b, [S('2.1', 'TP', 'Motivasi intrinsik dan motivasi ekstrinsik itu penting. ' + 'z ' * 300)])
t('variabel disebut UTUH = tidak ada catatan', len(r['issues']) == 0,
  f'catatan={len(r["issues"])}')

# 3c. variabel 1 kata tetap jalan
r = KS.check_variable_consistency({'variabel': ['kepuasan']},
                                  [S('2.1', 'TP', 'Kepuasan kerja penting. ' + 'z ' * 300)])
t('variabel 1 kata = tidak ada catatan (perilaku lama aman)', len(r['issues']) == 0,
  f'catatan={len(r["issues"])}')

# 3d. variabel 1 kata hilang → ada catatan
r = KS.check_variable_consistency({'variabel': ['kompensasi']},
                                  [S('2.1', 'TP', 'Motivasi itu penting. ' + 'z ' * 300)])
t('variabel 1 kata hilang = ada catatan', len(r['issues']) == 1, f'catatan={len(r["issues"])}')

print()
print('=' * 96)
print('VERIFIKASI PERBAIKAN — ALAT UKUR BARU (makna & persis)')
print('=' * 96)
t('sama_persis(): judul PERSIS terdeteksi', KS.sama_persis(f'awal {jb} akhir', jb))
t('sama_persis(): judul beda 1 kata TIDAK dianggap persis',
  not KS.sama_persis(js, jb))
t('sama_teks_akademik(): beda kata penting TIDAK lolos (toleransi 0,97)',
  not KS.sama_teks_akademik(js, jb))
t('sama_teks_akademik(): sama persis → True', KS.sama_teks_akademik(jb, jb))

lama = ('Kinerja karyawan dipengaruhi motivasi kerja (β=0,432; p<0,05) sebesar 12% '
        'menurut Sari (2022). Metode kuantitatif dengan regresi.')
baru = ('Motivasi kerja memengaruhi kinerja karyawan (β=0,441; p<0,05) sekitar 12% '
        'menurut Sari (2022). Pendekatan kuantitatif memakai regresi.')
m = KS.makna_terjaga(lama, baru)
print(f'  makna: kemiripan={m["kemiripan"]} terjaga={m["terjaga"]} '
      f'hilang={m["penanda_hilang"]} baru={m["penanda_baru"]}')
t('makna paragraf (kata beda, makna sama) TERJAGA ≥0,80', m['terjaga'],
  f'kemiripan={m["kemiripan"]}')

rusak = 'Penelitian ini memakai wawancara mendalam secara kualitatif.'
m2 = KS.makna_terjaga(lama, rusak)
t('makna BERUBAH total terdeteksi TIDAK terjaga', not m2['terjaga'],
  f'kemiripan={m2["kemiripan"]}')

print()
print('=' * 96)
print('REGRESI — pastikan yang lama TIDAK rusak')
print('=' * 96)
r = KS.check_hipotesis_consistency(
    {'hipotesis': ['H1', 'H2']},
    [S('2.4', 'Hipo', 'H1 dan H2 berpengaruh. ' + 'v ' * 200),
     S('4.4', 'Uji', 'H1 dan H2 diuji. ' + 'u ' * 200),
     S('5.1', 'Kes', 'H1 dan H2 terbukti. ' + 't ' * 200)])
t('hipotesis sinkron = 0 catatan', len(r['issues']) == 0, f'catatan={len(r["issues"])}')

r = KS.check_hipotesis_consistency(
    {'hipotesis': ['H1', 'H2']},
    [S('2.4', 'Hipo', 'H1 dan H2 berpengaruh. ' + 'v ' * 200),
     S('4.4', 'Uji', 'H1 saja diuji. ' + 'u ' * 200)])
t('hipotesis TIDAK sinkron 2.4 vs 4.4 = ada catatan', len(r['issues']) >= 1,
  f'catatan={len(r["issues"])}')

r = KS.check_consistency({}, [])
t('brief kosong tidak error (prinsip jangan halangi user)', isinstance(r, dict))

r = KS.check_ov_consistency({}, [S('3.1', 'Metode', 'Tabel OV: X1, X2. ' + 'w ' * 200)])
t('OV dengan penanda = tidak ada catatan', len(r['issues']) == 0, f'catatan={len(r["issues"])}')

print()
print('=' * 96)
print(f'HASIL: {lolos} LOLOS / {gagal} GAGAL')
print('=' * 96)