#!/usr/bin/env python3
"""UJI C — UJUNG KE UJUNG: jawaban AI → tangkap grafik → gambar → .docx.

2 arah: SEHAT harus BERHASIL · DIRUSAK harus GAGAL.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import gambar as G                                 # noqa: E402

OUT = Path('/app/_uji_c')
OUT.mkdir(exist_ok=True)
LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


print('══ 0. PARSER: intent BUAT_TABEL / BUAT_GRAFIK ══')
from app import parser as P                                 # noqa: E402
kasus = [
    ('buatkan tabel perbandingan penelitian terdahulu', 'BUAT_TABEL', 2),
    ('tambahkan tabel distribusi frekuensi', 'BUAT_TABEL', 2),
    ('buatkan tabel ringkasan', 'BUAT_TABEL', 2),
    ('sajikan dalam bentuk tabel', 'BUAT_TABEL', 2),
    ('buatkan grafik pertumbuhan GDP', 'BUAT_GRAFIK', 2),
    ('buat histogram distribusi nilai', 'BUAT_GRAFIK', 2),
    ('buatkan diagram alur penelitian', 'BUAT_GRAFIK', 2),
    ('visualisasikan data ini', 'BUAT_GRAFIK', 2),
    #  TIDAK boleh berubah (regresi)
    ('perbaiki kalimat ini', 'REVISI', 1),
    ('perkaya paragraf ini', 'PERKAYA_NARASI', 1),
    ('ganti metode penelitian', 'GANTI_METODE', 3),
    ('apa itu tabel?', 'PERTANYAAN', 1),
]
for pesan, harap_i, harap_p in kasus:
    u = P.urai(pesan)
    got_i = u.get('intent')
    got_p = P.pilih_pengali(got_i, pesan)
    cek(f'"{pesan[:40]}" → {harap_i} ×{harap_p}',
        got_i == harap_i and got_p == harap_p,
        f'(dapat {got_i} ×{got_p})')

print()
print('  label ramah user:')
for pesan in ('buatkan tabel ringkasan', 'buatkan grafik GDP'):
    u = P.urai(pesan)
    print(f'     "{pesan}" → {P.label_pengguna(u["intent"], P.pilih_pengali(u["intent"], pesan))!r}')

print()
print('══ 1. TANGKAP [DATA-GRAFIK] dari jawaban AI ══')
jawab = (
    'Bagian ini memerlukan satu grafik agar polanya terlihat.\n\n'
    '[DATA-GRAFIK]\n'
    '{"jenis": "garis", "judul": "Pertumbuhan GDP 2015-2024", "satuan": "%",\n'
    ' "data": [{"label": "2015", "nilai": 30}, {"label": "2016", "nilai": 34},\n'
    ' {"label": "2017", "nilai": 38}, {"label": "2018", "nilai": 42}]}\n'
    '[/DATA-GRAFIK]\n\n'
    'Grafik tersebut bersumber dari Tabel 1.2.'
)
blok = G.tangkap_data_grafik(jawab)
print(f'  blok tertangkap: {len(blok)}')
if blok:
    print(f'     jenis={blok[0]["jenis"]} · judul={blok[0]["judul"]!r} · '
          f'{len(blok[0]["data"])} titik')
cek('1 blok tertangkap', len(blok) == 1)
cek('jenis terbaca "garis"', blok and blok[0]['jenis'] == 'garis')
cek('4 titik data', blok and len(blok[0]['data']) == 4)

bersih = G.buang_blok_grafik(jawab)
print(f'  teks bersih: {bersih[:80]!r}…')
cek('blok DIBUANG dari teks', 'DATA-GRAFIK' not in bersih and '{' not in bersih)
cek('kalimat naskah TETAP ada', 'bersumber dari Tabel 1.2' in bersih)

print()
print('══ 2. GAMBAR dari data itu ══')
png = G.gambar_grafik(blok[0]['data'], jenis=blok[0]['jenis'],
                      judul=blok[0]['judul'], satuan=blok[0]['satuan'])
(OUT / 'hasil_grafik.png').write_bytes(png)
print(f'  PNG {len(png):,} byte')
cek('PNG > 5 KB', len(png) > 5000, f'({len(png)})')

print()
print('══ 3. SISIP ke .docx (naskah Bos yang SUDAH ADA) ══')
sumber = Path('/app/_naskah_bos_uji.docx')
kerja = OUT / 'hasil_c.docx'
shutil.copy(sumber, kerja)
ket = G.keterangan_gambar(blok[0]['judul'], 'BPS (Tabel 1.2)')
r = G.sisip_gambar_docx(kerja, png, ket)
print(f'  hasil: {r}')
cek('sisip BERHASIL', r.get('ok') is True, str(r))

if r.get('ok'):
    import zipfile
    with zipfile.ZipFile(kerja) as z:
        d = z.read('word/document.xml').decode()
        print(f'  tabel: {d.count("<w:tbl>")} · drawing: {d.count("<w:drawing>")}')
        cek('7 tabel UTUH', d.count('<w:tbl>') == 7)
        cek('gambar nambah (5)', d.count('<w:drawing>') == 5,
            f'(dapat {d.count("<w:drawing>")})')
        cek('keterangan masuk', 'Sumber: BPS' in d)
        cek('media baru ada', 'word/media/grafik_ai.png' in z.namelist())

    from app import ai as A                                 # noqa: E402
    t = A._teks_dari_berkas(kerja, 'hasil_c.docx')
    print(f'  dibaca ulang: {len(t):,} kar · [[GAMBAR- {t.count("[[GAMBAR-")}')
    cek('terbaca balik (naskah utuh)', len(t) > 60_000, f'({len(t)})')

print()
print('══ 4. DIRUSAK — hal buruk HARUS gagal ══')
cek('gambar kosong → TIDAK disisip',
    G.sisip_gambar_docx(kerja, b'', 'x').get('ok') is False)
cek('berkas tidak ada → TIDAK disisip',
    G.sisip_gambar_docx(OUT / 'tidak-ada.docx', png, 'x').get('ok') is False)
cek('JSON rusak → blok dilewati',
    len(G.tangkap_data_grafik('[DATA-GRAFIK]{rusak[/DATA-GRAFIK]')) == 0)
cek('grafik tanpa angka → dilewati',
    len(G.tangkap_data_grafik(
        '[DATA-GRAFIK]{"jenis":"batang","data":[{"label":"A"}]}'
        '[/DATA-GRAFIK]')) == 0)
#  naskah ASLI tidak boleh berubah
cek('naskah ASLI tidak disentuh (ukuran sama)',
    sumber.stat().st_size == 590_578, f'({sumber.stat().st_size})')

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
print(f'  hasil .docx: {kerja}')
print(f'  hasil PNG  : {OUT / "hasil_grafik.png"}')
sys.exit(1 if GAGAL else 0)