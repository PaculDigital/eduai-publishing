#!/usr/bin/env python3
"""UJI GERBANG BESAR + 4 LANGKAH (26Sep26) — 2 ARAH.

Arah 1 (SEHAT)  : alur normal harus jalan & hasilnya masuk akal.
Arah 2 (DIRUSAK): kirim data ngawur / tidak lengkap → mesin HARUS
                  menolak ramah (tanya) — BUKAN meledak & BUKAN salah tebak.
"""
import os
import sys

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/uji_alur')

from app import alur_awal as A                                          # noqa: E402

L = GA = 0


def cek(nama, ok, bukti=''):
    global L, GA
    if ok:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


print('══ A. SEHAT — GERBANG BESAR ══')
# A1. belum pilih apa-apa → tampilkan pintu
r = A.petakan_jalur(None)
cek('A1. belum pilih → tanya pintu', r['tanya'] == 'pintu', str(r)[:110])

# A2. pilih "mulai baru" tanpa berkas → jalur baru
r = A.petakan_jalur('baru')
cek('A2. mulai baru → jalur baru', r['jalur'] == 'baru', str(r)[:110])

# A3. pilih "lanjut" TANPA berkas → P1 TANYA (jangan diamkan)
r = A.petakan_jalur('lanjut')
cek('A3. P1: lanjut tanpa berkas → TANYA', r['tanya'] == 'unggah',
    str(r)[:110])
cek('A3b. P1: jalur BELUM ditetapkan', r['jalur'] is None, str(r['jalur']))

# A4. ada berkas + naskah nyata + pilih lanjut → P3 tampilkan deteksi
naskah = '''BAB I PENDAHULUAN
Latar belakang masalah penelitian ini adalah rendahnya hasil belajar.
Rumusan masalah: apakah media pembelajaran berpengaruh signifikan
terhadap hasil belajar siswa? Hipotesis penelitian ini diuji dengan
regresi linear. Responden berjumlah 120 orang dengan kuesioner.
BAB II TINJAUAN PUSTAKA
Penelitian terdahulu menunjukkan hasil yang beragam.
BAB III METODE PENELITIAN
Penelitian ini memakai pendekatan kuantitatif dengan sampel 120 siswa.
BAB IV HASIL DAN PEMBAHASAN
BAB V KESIMPULAN
'''
r = A.petakan_jalur('lanjut', ada_berkas=True, teks=naskah)
cek('A4. P3: ada ISI → tanya konfirmasi', r['tanya'] == 'konfirmasi',
    str(r)[:130])
cek('A4b. deteksi jenis dokumen ketemu',
    bool(r['deteksi'] and r['deteksi'].get('jenis')), str(r['deteksi'])[:130])
cek('A4c. bab terdeteksi I-V',
    r['deteksi']['bab_ada'] == ['I', 'II', 'III', 'IV', 'V'],
    str(r['deteksi']['bab_ada']))
cek('A4d. jenis penelitian = kuantitatif',
    r['deteksi']['jenis_penelitian'] == 'kuantitatif',
    str(r['deteksi']['jenis_penelitian']))
cek('A4e. sudah_lengkap = True', r['deteksi']['sudah_lengkap'] is True,
    str(r['deteksi']['sudah_lengkap']))
cek('A4f. kalimat ramah dibentuk',
    'Sepertinya' in (r['deteksi'].get('ringkas') or ''),
    str(r['deteksi'].get('ringkas'))[:130])

# A5. user konfirmasi "Benar" → lanjut
r = A.petakan_jalur('lanjut', ada_berkas=True, teks=naskah, konfirmasi=True)
cek('A5. konfirmasi Benar → jalur lanjut', r['jalur'] == 'lanjut', str(r)[:110])

# A6. user bilang "Ubah" → jalur baru, naskah tetap tersimpan
r = A.petakan_jalur('lanjut', ada_berkas=True, teks=naskah, konfirmasi=False)
cek('A6. konfirmasi Salah → jalur baru', r['jalur'] == 'baru', str(r)[:110])

print('\n══ B. DIRUSAK — PAGAR (jangan salah tebak) ══')
# B1. P2: ada berkas TAPI bilang "mulai baru" → TANYA niatnya
r = A.petakan_jalur('baru', ada_berkas=True, teks=naskah)
cek('B1. P2: berkas + "mulai baru" → TANYA',
    r['tanya'] == 'maksud_berkas' and r['jalur'] is None, str(r)[:130])

# B2. pilihan ngawur (bukan baru/lanjut) → tanya pintu (tidak meledak)
r = A.petakan_jalur('xyz123')
cek('B2. pilihan ngawur → tanya pintu (tidak meledak)',
    r['tanya'] == 'pintu', str(r)[:110])

# B3. teks None / kosong → tidak meledak
try:
    r = A.petakan_jalur('lanjut', ada_berkas=False, teks=None)
    cek('B3. teks None → tidak meledak', r['tanya'] == 'unggah', str(r)[:90])
except Exception as e:
    cek('B3. teks None → tidak meledak', False, repr(e)[:100])

# B4. naskah isi ngawur → deteksi ragu, TIDAK memaksa
r = A.deteksi_isi('asdf qwer zxcv 12345')
cek('B4. naskah ngawur → bab kosong (jujur)', r['bab_ada'] == [],
    str(r['bab_ada']))
cek('B4b. naskah ngawur → jenis penelitian kosong (tidak menebak)',
    r['jenis_penelitian'] == '', str(r['jenis_penelitian']))

# B5. jenis dokumen tidak dikenal → tidak meledak
try:
    r = A.deteksi_isi('')
    cek('B5. teks kosong → tidak meledak', isinstance(r, dict), str(r)[:80])
except Exception as e:
    cek('B5. teks kosong → tidak meledak', False, repr(e)[:100])

print('\n══ C. 4 LANGKAH ══')
# C1. belum ada apa-apa → langkah 1 (jenjang)
r = A.langkah_berikut({})
cek('C1. kosong → langkah 1 jenjang', r['langkah'] == 'jenjang', str(r)[:110])

# C2. jenjang terisi → langkah 2 (bidang) + 8 pilihan
r = A.langkah_berikut({'jenjang': 'skripsi'})
cek('C2. jenjang → langkah 2 bidang', r['langkah'] == 'bidang', str(r)[:110])
cek('C2b. ada 8 bidang + Lainnya = 9 pilihan', len(r.get('pilihan') or []) == 9,
    str(len(r.get('pilihan') or [])))

# C3. bidang terisi → langkah 3 (jenis) + 2 pilihan
r = A.langkah_berikut({'jenjang': 'skripsi', 'bidang': 'pendidikan'})
cek('C3. bidang → langkah 3 jenis', r['langkah'] == 'jenis', str(r)[:110])
cek('C3b. kuantitatif siap, kualitatif belum',
    [x['siap'] for x in r['pilihan']] == [True, False], str(r['pilihan'])[:120])

# C4. jenis terisi → langkah 4 (judul) + 3-5 contoh
r = A.langkah_berikut({'jenjang': 'skripsi', 'bidang': 'pendidikan',
                       'mode_penelitian': 'kuantitatif'})
cek('C4. jenis → langkah 4 judul', r['langkah'] == 'judul', str(r)[:110])
cek('C4b. contoh judul 3-5 buah', 3 <= len(r.get('contoh') or []) <= 5,
    str(len(r.get('contoh') or [])))

# C5. judul terisi → selesai
r = A.langkah_berikut({'jenjang': 'skripsi', 'bidang': 'pendidikan',
                       'mode_penelitian': 'kuantitatif',
                       'judul': 'Pengaruh X terhadap Y'})
cek('C5. judul → selesai', r['selesai'] is True, str(r)[:110])

# C6. data ngawur (bukan dict) → tidak meledak
try:
    r = A.langkah_berikut(None)
    cek('C6. data None → langkah 1 (tidak meledak)',
        r['langkah'] == 'jenjang', str(r)[:90])
except Exception as e:
    cek('C6. data None → tidak meledak', False, repr(e)[:100])

# C7. bidang tidak dikenal → contoh judul kosong (layar sembunyikan, sistem jalan)
cek('C7. bidang tak dikenal → contoh kosong (tidak menebak)',
    A.contoh_judul('bidang_ngawur') == [], str(A.contoh_judul('bidang_ngawur')))

print('\n══ D. IDENTITAS COVER (logo boleh dilewati) ══')
# D1. kosong → kurang 3 wajib
r = A.periksa_identitas({})
cek('D1. kosong → kurang Nama+NIM+Kampus', len(r['kurang']) == 3, str(r['kurang']))
cek('D1b. boleh_lanjut = False', r['boleh_lanjut'] is False, str(r['boleh_lanjut']))

# D2. wajib terisi, logo BELUM → BOLEH LANJUT (aturan Bos)
r = A.periksa_identitas({'nama_lengkap': 'Budi Santoso', 'nim': '12345',
                         'nama_kampus': 'Universitas Negeri'})
cek('D2. wajib terisi tanpa logo → boleh_lanjut = True',
    r['boleh_lanjut'] is True, str(r)[:130])
cek('D2b. logo disebut boleh nanti',
    'berkas_logo_id' in r['belum_opsional'], str(r['belum_opsional']))
cek('D2c. pesan menyebut "boleh diisi nanti"',
    'boleh diisi nanti' in r['pesan'], r['pesan'][:130])

# D3. lengkap semua → pesan lengkap
r = A.periksa_identitas({'nama_lengkap': 'Budi', 'nim': '1',
                         'nama_kampus': 'UN', 'kota_kampus': 'Malang',
                         'fakultas': 'FEB', 'program_studi': 'Manajemen',
                         'berkas_logo_id': 7})
cek('D3. lengkap → "sudah lengkap"',
    'sudah lengkap' in r['pesan'].lower(), r['pesan'][:100])

# D4. nama diisi spasi saja → dianggap KOSONG (jangan lolos)
r = A.periksa_identitas({'nama_lengkap': '   ', 'nim': '1',
                         'nama_kampus': 'UN'})
cek('D4. nama spasi saja → tetap kurang (tidak lolos)',
    'nama_lengkap' in r['kurang'], str(r['kurang']))

# D5. None → tidak meledak
try:
    r = A.periksa_identitas(None)
    cek('D5. None → tidak meledak', r['boleh_lanjut'] is False, str(r)[:80])
except Exception as e:
    cek('D5. None → tidak meledak', False, repr(e)[:100])

print('\n══ E. PAKAI MESIN YANG SUDAH ADA (jangan duplikat) ══')
cek('E1. daftar_jenjang dari app/jenis.py (6 jenis)',
    len(A.daftar_jenjang()) == 6, str(len(A.daftar_jenjang())))
cek('E2. daftar_bidang = 9 (8 + Lainnya)', len(A.daftar_bidang()) == 9,
    str(len(A.daftar_bidang())))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
