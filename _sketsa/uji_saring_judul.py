#!/usr/bin/env python3
"""UJI PENYARING JUDUL (ACC Bos "1. A") — 2 arah: SEHAT lulus, DIRUSAK gagal."""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as ST                                 # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


print('══ 1. KLASIFIKASI JENIS PARAGRAF ══')
kasus = [
    ('1.6  Kesenjangan Penelitian (Research Gap)', 'judul'),
    ('1.6.1  Kesenjangan Konteks (Contextual Gap)', 'judul'),
    ('1.7  Kerangka Pemikiran dan Pengembangan Hipotesis', 'judul'),
    ('BAB I  PENDAHULUAN', 'judul'),
    ('Gambar 1.1.  Nilai PDB Pergudangan, Jasa Penunjang Angkutan', 'judul'),
    ('Tabel 1.2. Distribusi Responden', 'judul'),
    ('Sumber: Badan Pusat Statistik (BPS), dipublikasikan Techinasia', 'keterangan'),
    ('Catatan: data diolah penulis', 'keterangan'),
    ('[[TABEL-6: 5 baris × 3 kolom — JANGAN diubah, ini konteks]]', 'penanda'),
    ('[[GAMBAR-2: di sini — JANGAN diubah, ini konteks]]', 'penanda'),
    ('[[/TABEL-6]]', 'penanda'),
    #  ISI — harus tetap 'isi'
    ('Perkembangan pesat teknologi digital telah mengubah lanskap industri logistik di Indonesia secara mendasar, sehingga perusahaan dituntut untuk beradaptasi dengan cepat dan tepat.', 'isi'),
    ('QWL terbukti meningkatkan kinerja melalui keterlibatan kerja dan menurunkan niat keluar karyawan.', 'isi'),
    ('Kebaruan (novelty) penelitian ini terletak pada tiga hal, yaitu konteks, variabel, dan metode yang dipakai untuk menganalisis kesiapan digital pada sektor pergudangan nasional.', 'isi'),
]
for teks, harap in kasus:
    dapat = K.jenis_paragraf(teks)
    cek(f'"{teks[:46]}…" → {harap}', dapat == harap, f'(dapat {dapat})')

print()
print('══ 2. UJI KE NASKAH SUNGGUHAN ══')
naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'), 'x.docx')
bersih = ST.buang_daftar_isi(naskah)
peta = ST.petakan(bersih)

total = 0
non_isi = 0
for b in peta:
    isi = str(b.get('isi_teks', ''))
    if not isi:
        continue
    for p in K.petakan_paragraf(isi):
        total += 1
        if p['jenis'] != 'isi':
            non_isi += 1
print(f'  {total} paragraf · {non_isi} non-isi ({100*non_isi/max(total,1):.0f}%)')
cek('non-isi terdeteksi (harus > 10%)', non_isi > total * 0.10)

#  TIDAK boleh berlebihan — kalau semua dianggap judul, mesin mati
cek('TIDAK semua dianggap non-isi (< 45%)', non_isi < total * 0.45,
    f'({100*non_isi/total:.0f}%)')

print()
print('══ 3. PARAGRAF ISI MASIH ADA (tidak ikut terbuang) ══')
for b in peta[:3]:
    sid = str(b.get('section_id'))
    isi = str(b.get('isi_teks', ''))
    par = K.petakan_paragraf(isi)
    jml_isi = sum(1 for p in par if p['jenis'] == 'isi')
    print(f'  bagian {sid}: {len(par)} paragraf · {jml_isi} ISI')
    cek(f'bagian {sid} punya paragraf ISI', jml_isi >= 1, f'({jml_isi})')

print()
print('══ 4. GESER DARI JUDUL KE ISI (fungsi _geser_ke_isi) ══')
#  bagian 1.6: P-01 = judul "1.6 …", P-02 = isi
b16 = next((x for x in peta if str(x.get('section_id')) == '1.6'), None)
if b16:
    par16 = K.petakan_paragraf(str(b16.get('isi_teks', '')))
    for i, p in enumerate(par16[:5]):
        print(f'     [{i}] {p["jenis"]:11} {p["teks"][:52]}…')
    nol = next((i for i, p in enumerate(par16) if p['jenis'] != 'isi'), None)
    if nol is not None:
        geser = K._geser_ke_isi(par16, nol)
        print(f'  geser dari idx {nol} (judul) → {geser} '
              f'({par16[geser]["jenis"]})')
        cek('geser berhenti di paragraf ISI', par16[geser]['jenis'] == 'isi')

print()
print('══ 5. DIRUSAK — judul yang mirip ISI jangan lolos ══')
#  kalau judul pendek TANPA pola tapi Kapital → harus tetap dikenali judul
cek('"Metode Penelitian" → judul', K.jenis_paragraf('Metode Penelitian') == 'judul')
cek('kalimat panjang → isi',
    K.jenis_paragraf('Metode penelitian ini memakai pendekatan kuantitatif '
                     'dengan pengumpulan data melalui kuesioner daring.') == 'isi')
cek('kosong → penanda', K.jenis_paragraf('') == 'penanda')
cek('paragraf_boleh_direvisi(judul) = False',
    K.paragraf_boleh_direvisi({'jenis': 'judul'}) is False)
cek('paragraf_boleh_direvisi(isi) = True',
    K.paragraf_boleh_direvisi({'jenis': 'isi'}) is True)

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)