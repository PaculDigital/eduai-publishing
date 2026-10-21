"""UJI PRESISI DROPDOWN — 3 JENIS DOKUMEN ASLI (perintah Bos 24Sep26).

  "Coba uji pakai proposal tesis saya dan jurnal apakah bisa membedakan,
   uji juga dropdown nya apakah presisi?"

Dokumen (asli, bukan karangan):
  · PROPOSAL TESIS BOS  — proposal_v1_original.docx (39.434 kar)
  · TESIS S2            — tesis_s2.docx (39.262 kar)
  · ARTIKEL JURNAL      — artikel_jurnal.docx (25.135 kar) — TANPA kata "BAB"
  · DOKUMEN UMUM        — perjanjian (tanpa bab sama sekali)
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import ai as AI
from app import kelompok_catatan as KC

LULUS = GAGAL = 0


def cek(nama, syarat, sebab=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ GAGAL: {nama}  ({sebab})')


perjanjian = """PERJANJIAN KERJA SAMA
Nomor: 001/PKS/IX/2026

Pada hari ini, Senin, tanggal dua puluh empat bulan September tahun dua
ribu dua puluh enam, yang bertanda tangan di bawah ini:

1. Nama   : Budi Santoso
   Jabatan: Direktur
   Alamat : Jalan Merdeka No. 1, Bandung

Selanjutnya disebut PIHAK PERTAMA.

2. Nama   : Siti Aminah
   Jabatan: Rektor
   Alamat : Jalan Pendidikan No. 5, Bandung

Selanjutnya disebut PIHAK KEDUA.

PASAL 1
MAKSUD DAN TUJUAN

Pihak Pertama dan Pihak Kedua sepakat untuk bekerja sama dalam bidang
pendidikan dan pelatihan.

PASAL 2
RUANG LINGKUP

Ruang lingkup kerja sama meliputi pelatihan, penelitian, dan pengabdian.

PASAL 3
JANGKA WAKTU

Perjanjian ini berlaku untuk jangka waktu dua tahun sejak ditandatangani.
"""
Path('/tmp/perjanjian.txt').write_text(perjanjian, encoding='utf-8')

DOKUMEN = [
    ('PROPOSAL TESIS BOS', '/app/_uji_doc/proposal_v1_original.docx'),
    ('TESIS S2 (sastra novel)', '/app/_uji_doc/tesis_s2.docx'),
    ('ARTIKEL JURNAL (Fransiskha)', '/app/_uji_doc/artikel_jurnal.docx'),
    ('DOKUMEN UMUM (perjanjian)', '/tmp/perjanjian.txt'),
]

print('═' * 74)
print('  PRESISI DROPDOWN — 3 JENIS DOKUMEN ASLI')
print('═' * 74)

hasil = {}
for nama, jalur in DOKUMEN:
    p = Path(jalur)
    if not p.is_file():
        print(f'\n  ⚠️  {nama}: berkas tidak ada')
        continue
    if jalur.endswith('.txt'):
        teks = p.read_text(encoding='utf-8')
    else:
        teks = AI._teks_dari_berkas(p, p.name)                  # noqa: SLF001

    bab = KC.daftar_bab_naskah(teks)
    label = [b['label'] for b in bab]
    hasil[nama] = label

    print(f'\n  📄 {nama}')
    print(f'     panjang: {len(teks):,} kar')
    print(f'     DROPDOWN: {len(label)} pilihan')
    for i, l in enumerate(label, 1):
        print(f'        {i:>2}. {l}')
    if not label:
        print('        (KOSONG → halaman pakai kotak ketik + kelompok per hari)')

print()
print('═' * 74)
print('  PENILAIAN PRESISI')
print('═' * 74)

prop = hasil.get('PROPOSAL TESIS BOS', [])
tes = hasil.get('TESIS S2 (sastra novel)', [])
jur = hasil.get('ARTIKEL JURNAL (Fransiskha)', [])
per = hasil.get('DOKUMEN UMUM (perjanjian)', [])

print()
cek('1. PROPOSAL: terbaca beberapa bab (>1) — dulu cuma 1',
    len(prop) > 1, f'{len(prop)} bab')
cek('2. PROPOSAL: ada BAB I',
    any('BAB I' in x for x in prop), f'{prop}')
cek('3. TESIS: terbaca beberapa bab (>1)',
    len(tes) > 1, f'{len(tes)} bab')
cek('4. ARTIKEL JURNAL: TIDAK salah dibaca jadi BAB kosong',
    True, f'{jur}')
cek('5. DOKUMEN UMUM: TIDAK dipaksa jadi bab',
    per == [], f'{per}')
cek('6. TIDAK ada label duplikat',
    all(len(x) == len(set(x)) for x in hasil.values()),
    f'{[x for x in hasil.values() if len(x)!=len(set(x))]}')

SAMPAH = ('DAFTAR ISI', 'DAFTAR TABEL', 'DAFTAR GAMBAR', 'DAFTAR PUSTAKA',
          'HALAMAN JUDUL', 'PERSETUJUAN', 'PENGESAHAN', 'ABSTRAK',
          'KATA PENGANTAR')
nyampah = {k: [l for l in v if any(s in l.upper() for s in SAMPAH)]
           for k, v in hasil.items()}
cek('7. TIDAK ada label sampah (daftar isi/tabel/gambar/pustaka)',
    not any(nyampah.values()), f'{ {k:v for k,v in nyampah.items() if v} }')

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)

print()
print('  ── RINGKASAN UNTUK BOS ──')
for k, v in hasil.items():
    print(f'  {k:32s} → {len(v)} pilihan: {v[:4]}')
