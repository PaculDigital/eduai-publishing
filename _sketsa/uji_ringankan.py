"""UJI RINGANKAN — buktikan HANYA gambar yang berubah (ACC Bos 03Okt26).

Diuji pada NASKAH NYATA 5,08 MB:
  A. Berapa besar hasilnya?
  B. APAKAH NASKAHNYA UTUH? — document.xml, tabel, paragraf HARUS SAMA PERSIS
  C. APAKAH LAYOUT GAMBAR SAMA? — ukuran (cm) & posisi di naskah tak berubah
  D. Apakah .docx hasil masih SAH dibuka (zip + XML)?
  E. Pagar: berkas kecil / bukan docx → dikembalikan APA ADANYA
"""
import hashlib
import io
import re
import sys
import zipfile

sys.path.insert(0, '/app')
from app.ringankan import ringankan_docx                        # noqa: E402

P = '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'

LULUS = GAGAL = 0


def cek(nama, syarat, tambahan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama} {tambahan}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {tambahan}')


asli = open(P, 'rb').read()
print(f'naskah asli: {len(asli)/1048576:.2f} MB')

print()
print('=== A. HASIL KOMPRES ===')
hasil, lapor = ringankan_docx(asli, 'SKRIPSI.docx')
print(f"   gambar ditemukan : {lapor['gambar']}")
print(f"   dikompres        : {lapor['dikompres']}  (dilewati: {lapor['dilewati']})")
print(f"   sebelum          : {lapor['sebelum']/1048576:.2f} MB")
print(f"   sesudah          : {lapor['sesudah']/1048576:.2f} MB")
turun = 100 - (len(hasil) * 100 // len(asli))
print(f"   TURUN            : {turun}%")
cek('A1 berkas jadi lebih kecil', len(hasil) < len(asli))
cek('A2 turun minimal 20%', turun >= 20)

print()
print('=== B. NASKAH UTUH — document.xml HARUS SAMA PERSIS ===')
za, zh = zipfile.ZipFile(io.BytesIO(asli)), zipfile.ZipFile(io.BytesIO(hasil))
nama_a = set(za.namelist())
nama_h = set(zh.namelist())
cek('B1 daftar berkas dalam docx SAMA',
    nama_a == nama_h,
    f'(beda: {nama_a ^ nama_h or "tidak ada"})')

for berkas in ('word/document.xml', 'word/settings.xml', 'word/styles.xml'):
    if berkas in nama_a:
        ha = hashlib.sha256(za.read(berkas)).hexdigest()
        hh = hashlib.sha256(zh.read(berkas)).hexdigest()
        cek(f'B2 {berkas} TIDAK BERUBAH (sidik sama)', ha == hh)

#  Tabel & paragraf: hitung di KEDUA versi
d_a = za.read('word/document.xml').decode('utf8', 'ignore')
d_h = zh.read('word/document.xml').decode('utf8', 'ignore')
cek('B3 jumlah <w:p> (paragraf) sama',
    len(re.findall(r'<w:p[ >]', d_a)) == len(re.findall(r'<w:p[ >]', d_h)))
cek('B4 jumlah <w:tbl> (tabel) sama',
    len(re.findall(r'<w:tbl[ >]', d_a)) == len(re.findall(r'<w:tbl[ >]', d_h)))
cek('B5 seluruh isi document.xml identik', d_a == d_h)

print()
print('=== C. LAYOUT GAMBAR SAMA — ukuran di naskah (cm) tak berubah ===')
ext_a = re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', d_a)
ext_h = re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', d_h)
cek('C1 jumlah & ukuran <wp:extent> SAMA PERSIS', ext_a == ext_h,
    f'({len(ext_a)} gambar)')
emb_a = re.findall(r'r:embed="(rId\d+)"', d_a)
emb_h = re.findall(r'r:embed="(rId\d+)"', d_h)
cek('C2 rujukan gambar (r:embed) SAMA PERSIS', emb_a == emb_h)

print()
print('=== D. FILE HASIL MASIH SAH ===')
try:
    zt = zipfile.ZipFile(io.BytesIO(hasil))
    bad = zt.testzip()
    cek('D1 arsip zip sehat (testzip)', bad is None, f'(rusak di: {bad})')
    cek('D2 24 gambar masih ada',
        len([n for n in zt.namelist() if 'media/' in n]) == 24)
except Exception as e:                                          # noqa: BLE001
    cek(f'D1 zip sehat — MELEDAK: {e}', False)

print()
print('=== E. PAGAR ===')
kecil = b'x' * 5000
h2, l2 = ringankan_docx(kecil, 'catatan.docx')
cek('E1 berkas bukan-docx → dikembalikan APA ADANYA', h2 is kecil)
h3, l3 = ringankan_docx(b'PK\x03\x04 rusak', 'rusak.docx')
cek('E2 docx rusak → dikembalikan APA ADANYA', h3 == b'PK\x03\x04 rusak')
h4, l4 = ringankan_docx(asli, 'naskah.pdf')
cek('E3 bukan .docx → dikembalikan APA ADANYA', h4 is asli)

print()
print(f'═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
sys.exit(1 if GAGAL else 0)
