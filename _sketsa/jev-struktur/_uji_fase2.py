"""UJI FASE 2 — brief.py + konteks.py (jalankan DI DALAM container)."""
import json
import sys
sys.path.insert(0, '/app')

from app import brief, konteks

print('=' * 66)
print('UJI 1 — brief.py : template & siklus dasar')
print('=' * 66)
b0 = brief.brief_kosong()
print(f'  brief_kosong() -> {len(b0)} kunci')
wajib = ['jenis', 'kategori', 'paradigma', 'alur', 'judul', 'variabel',
         'hipotesis', 'metodologi', 'istilah', 'catatan', 'struktur', 'sidik_jari']
missing = [k for k in wajib if k not in b0]
print(f'  kunci wajib hilang: {missing or "TIDAK ADA ✅"}')

print()
print('=' * 66)
print('UJI 2 — brief.py : tahan data rusak (NULL/kosong/JSON rusak/bukan objek)')
print('=' * 66)
for nama, masukan in [
    ('None', None),
    ('string kosong', ''),
    ('spasi saja', '   '),
    ('JSON rusak', '{rusak banget'),
    ('JSON bukan objek', '[1,2,3]'),
    ('JSON null', 'null'),
]:
    hasil = brief.muat(masukan)
    ok = isinstance(hasil, dict) and 'judul' in hasil
    print(f'  {nama:20s} -> {"AMAN ✅" if ok else "GAGAL ❌"} ({len(hasil) if isinstance(hasil, dict) else "?"} kunci)')

print()
print('=' * 66)
print('UJI 3 — brief.py : perbarui() + kunci sistem dilindungi')
print('=' * 66)
j = brief.simpan(brief.brief_kosong())
j = brief.perbarui(j, judul='Pengaruh QWL terhadap Kinerja',
                   paradigma='kuantitatif',
                   variabel=[{'nama': 'X1', 'jenis': 'independen'},
                             {'nama': 'Y', 'jenis': 'dependen'}],
                   hipotesis=['H1', 'H2'])
b = brief.muat(j)
print(f'  judul      : {b["judul"]}')
print(f'  paradigma  : {b["paradigma"]}')
print(f'  variabel   : {[v["nama"] for v in b["variabel"]]}')
print(f'  hipotesis  : {b["hipotesis"]}')

# kunci sistem HANYA boleh diisi sistem, bukan AI/user
j2 = brief.perbarui(j, alur='kuantitatif_deduktif')      # pertama: boleh
print(f'  alur diset : {brief.muat(j2)["alur"]}')
j3 = brief.perbarui(j2, alur='kualitatif_induktif')      # kedua: HARUS ditolak
alur_akhir = brief.muat(j3)['alur']
print(f'  coba timpa : {"DITOLAK ✅" if alur_akhir == "kuantitatif_deduktif" else "TERTIMPA ❌"} (masih {alur_akhir})')

print()
print('=' * 66)
print('UJI 4 — brief.py : catatan + ringkas')
print('=' * 66)
j4 = brief.tambah_catatan(j3, 'Dosen minta tambah data 2024')
b4 = brief.muat(j4)
print(f'  jumlah catatan: {len(b4["catatan"])}')
print(f'  catatan[0].text: {b4["catatan"][0]["text"]}')
print()
print('  --- ringkas() ---')
for ln in brief.ringkas(b4).split('\n'):
    print('    ' + ln)

print()
print('=' * 66)
print('UJI 5 — konteks.py : potong() di batas kata')
print('=' * 66)
panjang = 'kata ' * 5000       # 25.000 karakter
hasil = konteks.potong(panjang, 2000)
print(f'  asal {len(panjang)} kar -> potong {len(hasil)} kar')
print(f'  berakhir "[dipotong]": {"YA ✅" if hasil.endswith("[dipotong]") else "TIDAK ❌"}')
print(f'  ekor: ...{hasil[-60:]!r}')

pendek = 'Teks pendek saja.'
print(f'  teks pendek -> {"TIDAK dipotong ✅" if konteks.potong(pendek, 2000) == pendek else "dipotong ❌"}')

print()
print('=' * 66)
print('UJI 6 — konteks.py : dari_struktur() ambil BAB I + tetangga')
print('=' * 66)
struktur = [
    {'nomor': 'BAB I',   'judul': 'PENDAHULUAN',  'isi': 'Latar belakang penelitian ini adalah QWL.'},
    {'nomor': 'BAB II',  'judul': 'TINJAUAN',     'isi': 'Teori COR dan SCT digunakan.'},
    {'nomor': 'BAB III', 'judul': 'METODE',       'isi': 'Penelitian memakai desain survei.'},
    {'nomor': 'BAB IV',  'judul': 'HASIL',        'isi': 'Hasil regresi menunjukkan pengaruh positif.'},
]
t = konteks.dari_struktur(struktur, 'BAB III')
print(f'  target BAB III ->')
print(f'    bab1   : {t["bab1"][:50]!r}')
print(f'    sebelum: {t["sebelum"][:50]!r}')
print(f'    sesudah: {t["sesudah"][:50]!r}')
benar = ('QWL' in t['bab1']) and ('COR' in t['sebelum']) and ('regresi' in t['sesudah'])
print(f'  isi BENAR: {"YA ✅" if benar else "TIDAK ❌"}')

print()
print('=' * 66)
print('UJI 7 — konteks.py : tahan data kosong/aneh')
print('=' * 66)
for nama, st, tgt in [
    ('struktur None', None, 'BAB I'),
    ('struktur kosong', [], 'BAB I'),
    ('target tak ada', struktur, 'BAB X'),
    ('target string kosong', struktur, ''),
    ('blok string', [{'nomor': 'BAB I', 'isi': 'teks langsung'}], 'BAB I'),
]:
    try:
        h = konteks.dari_struktur(st, tgt)
        print(f'  {nama:22s} -> AMAN ✅ (bab1={len(h["bab1"])} kar)')
    except Exception as e:
        print(f'  {nama:22s} -> GAGAL ❌ {type(e).__name__}: {e}')

print()
print('=' * 66)
print('UJI 8 — konteks.py : bangun_prompt() utuh')
print('=' * 66)
prompt = konteks.bangun_prompt(
    bagian_target='BAB III',
    struktur=struktur,
    brief_ringkas=brief.ringkas(b4),
    isi_saat_ini='Penelitian ini menggunakan metode kuantitatif.',
    komentar='Dosen: tambahkan justifikasi pemilihan desain.',
)
print(f'  panjang prompt : {len(prompt)} karakter')
for penanda in ['KEBENARAN TUNGGAL', 'BAB I (konteks)', 'BAGIAN SEBELUMNYA',
                'BAGIAN SESUDAHNYA', 'ISI BAGIAN YANG DIREVISI',
                'KOMENTAR/MASUKAN', 'TUGAS SAAT INI']:
    ada = penanda in prompt
    print(f'  {"✅" if ada else "❌"} {penanda}')
