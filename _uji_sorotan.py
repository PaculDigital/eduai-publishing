"""UJI TAHAP 3.1 — SOROTAN KALIMAT (ACC Bos 24Sep26).

Yang diuji = ATURAN, bukan "tampilan bagus":

  A. MESIN: 3 keadaan (utuh / bergeser / hilang) + umum
  B. NASKAH TIDAK DISENTUH: sorotan = lapisan baca, tak menulis naskah
  C. URUTAN PARAGRAF: server & layar WAJIB sepakat (kalau tidak, sorotan
     jatuh di paragraf SALAH)
  D. JEJAK DI DB: catatan dengan sorotan menyimpan teks_asli + mulai/akhir
  E. HALAMAN: kotak sorotan ada, form tetap jalan, keadaan tampil
  F. TAHAN GEMPA: naskah kosong · naskah raksasa · kalimat kembar

Jalankan DI DALAM container (eduai-app).
"""
import re
import sys
import time
import urllib.request

sys.path.insert(0, '/app')
from app import sorotan as S
from app.models import (BerkasPembimbingan, CatatanPembimbing, Pembimbingan,
                        SessionLocal, User, VersiDokumen, init_db)

LULUS = GAGAL = 0


def cek(nama, syarat, sebab=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ GAGAL: {nama}  ({sebab})')


NASKAH = """BAB I
PENDAHULUAN

Latar belakang masalah penelitian ini adalah kesenjangan digital yang
semakin melebar. Data BPS menunjukkan 42 persen desa belum terjangkau
internet cepat.

Tabel 1.1 Pra-Survey menunjukkan peran Quality of Work Life dominan.

BAB II
TINJAUAN PUSTAKA

Hipotesis H3 menyatakan kepemimpinan digital berpengaruh positif
terhadap kinerja pegawai.
"""

print('═' * 74)
print('  A. MESIN SOROTAN — 3 KEADAAN')
print('═' * 74)
h = S.cari_sorotan(NASKAH, 'Data BPS menunjukkan 42 persen desa')
cek('A1 teks persis → UTUH', h['keadaan'] == S.UTUH, h['keadaan'])
cek('A1b UTUH punya nomor paragraf', h['nomor'] is not None, str(h['nomor']))
cek('A1c UTUH punya posisi awal/akhir',
    h['awal'] is not None and h['akhir'] is not None,
    '%s:%s' % (h['awal'], h['akhir']))

h2 = S.cari_sorotan(
    NASKAH, 'Data BPS memperlihatkan 42 persen desa belum terhubung '
            'internet cepat')
cek('A2 kalimat diedit sedikit → BERGESER', h2['keadaan'] == S.BERGESER,
    '%s (nomor %s)' % (h2['keadaan'], h2['nomor']))
cek('A2b BERGESER tetap menunjuk paragraf', h2['nomor'] is not None, '')

h3 = S.cari_sorotan(NASKAH, 'Anggaran desa meningkat setiap tahun anggaran')
cek('A3 teks tidak ada → HILANG', h3['keadaan'] == S.HILANG, h3['keadaan'])
cek('A3b HILANG mengembalikan teks asli (untuk "Lihat teks asli")',
    h3['teks'] == 'Anggaran desa meningkat setiap tahun anggaran',
    repr(h3['teks']))

cek('A4 tanpa sorotan → UMUM (BUKAN hilang)',
    S.cari_sorotan(NASKAH, '')['keadaan'] == S.UMUM, '')
cek('A5 naskah kosong + ada sorotan → HILANG',
    S.cari_sorotan('', 'Hipotesis H3')['keadaan'] == S.HILANG, '')

print()
print('═' * 74)
print('  B. NASKAH TIDAK DISENTUH (3 tiang)')
print('═' * 74)
import ast                                                       # noqa: E402
src = open('/app/app/sorotan.py', encoding='utf-8').read()
pohon = ast.parse(src)
#  Cari panggilan yang MENULIS ke DB atau ke disk.
terlarang = []
for simpul in ast.walk(pohon):
    if isinstance(simpul, ast.Attribute) and simpul.attr in (
            'commit', 'add', 'delete', 'flush', 'write_text', 'write_bytes',
            'write'):
        terlarang.append('%s (baris %s)' % (simpul.attr, simpul.lineno))
cek('B1 sorotan.py NOL penyimpanan (tidak menyentuh DB/naskah)',
    not terlarang, str(terlarang))
cek('B2 sorotan.py tidak mengimpor model DB',
    'from .models' not in src and 'from app.models' not in src, '')

print()
print('═' * 74)
print('  C. URUTAN PARAGRAF — SERVER & LAYAR HARUS SEPAKAT')
print('═' * 74)
#  Server: re.split(r'\n{2,}')  →  sorotan.pecah_paragraf()
#  Layar : t.split(/\n{2,}/)    →  baca dari template
layar = open('/app/app/templates/tinjau.html', encoding='utf-8').read()
cek('C1 layar memakai pemecah paragraf yang SAMA',
    't.split(/\\n{2,}/)' in layar, 'pemecah di layar tidak ketemu')
cek('C2 server memakai pemecah yang SAMA',
    r"re.split(r'\n{2,}'" in src, 'pemecah di server tidak ketemu')
#  Bukti nyata: jumlah paragraf sama.
cek('C3 naskah uji → jumlah paragraf sama di dua sisi',
    len(S.pecah_paragraf(NASKAH)) == len(
        [p for p in re.split(r'\n{2,}', NASKAH) if p.strip()]), '')

print()
print('═' * 74)
print('  D. JEJAK DI DB — SOROTAN TERSIMPAN SAAT DIBUAT')
print('═' * 74)
init_db()
db = SessionLocal()
u = db.query(User).filter(User.id == 3).one()
FID = 9
for b in db.query(Pembimbingan).filter(
        Pembimbingan.nama == 'Uji Sorotan 3.1').all():
    db.query(CatatanPembimbing).filter(
        CatatanPembimbing.pembimbingan_id == b.id).delete()
    db.query(BerkasPembimbingan).filter(
        BerkasPembimbingan.pembimbingan_id == b.id).delete()
    db.delete(b)
db.query(VersiDokumen).filter(VersiDokumen.file_id == FID).delete()
db.commit()

from app import pembimbing as P                                   # noqa: E402
baris, TOK = P.buat_bimbingan(db, u.id, nama='Uji Sorotan 3.1', hari=7)
baris.identitas = 'Prof. Uji <uji@contoh.id>'
bk = BerkasPembimbingan(pembimbingan_id=baris.id, file_id=FID,
                        judul='Naskah Uji Sorotan')
db.add(bk)
db.add(VersiDokumen(user_id=u.id, file_id=FID, bab='__naskah__',
                    nomor=901, isi=NASKAH, ukuran=len(NASKAH),
                    sumber='uji'))
db.commit()

#  Kirim catatan lewat HALAMAN (HTTP), seperti pembimbing sungguhan.
KALIMAT = 'Data BPS menunjukkan 42 persen desa belum terjangkau internet cepat'
batas = '----uji3'
potongan = (
    f'--{batas}\r\nContent-Disposition: form-data; name="isi"\r\n\r\n'
    f'Catatan uji sorotan A\r\n'
    f'--{batas}\r\nContent-Disposition: form-data; name="teks_asli"\r\n\r\n'
    f'{KALIMAT}\r\n'
    f'--{batas}\r\nContent-Disposition: form-data; name="berkas_id"\r\n\r\n'
    f'{bk.id}\r\n'
    f'--{batas}\r\nContent-Disposition: form-data; name="section_judul"\r\n\r\n'
    f'BAB I — PENDAHULUAN\r\n'
    f'--{batas}--\r\n').encode()

req = urllib.request.Request(
    f'http://127.0.0.1:8000/tinjau/{TOK}/catatan', data=potongan,
    method='POST',
    headers={'Content-Type': f'multipart/form-data; boundary={batas}'})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        status = r.status
except urllib.error.HTTPError as e:
    status = e.code
cek('D1 kirim catatan ber-sorotan lewat HALAMAN → berhasil',
    status in (200, 303), f'HTTP {status}')

db.expire_all()
c = (db.query(CatatanPembimbing)
     .filter(CatatanPembimbing.pembimbingan_id == baris.id)
     .order_by(CatatanPembimbing.id.desc()).first())
cek('D2 catatan tersimpan', c is not None, '')
if c:
    cek('D3 `teks_asli` terisi (kenangan teks tersimpan)',
        (c.teks_asli or '').startswith('Data BPS'), repr(c.teks_asli[:40]))
    cek('D4 `sidik` terisi (untuk mencocokkan nanti)',
        bool((c.sidik or '').strip()), repr(c.sidik))
    cek('D5 `berkas_id` menunjuk berkas bimbingan ini',
        c.berkas_id == bk.id, '%s vs %s' % (c.berkas_id, bk.id))
    cek('D6 `keadaan` di DB = utuh',
        c.keadaan == 'utuh', repr(c.keadaan))
    #  ⚠️ UJI INI DIPERKUAT 24Sep26. Versi pertama cuma memeriksa
    #  `c.mulai is not None` — dan karena `catat()` SELALU mengisi angka
    #  (default 0), uji itu LULUS walau posisi belum pernah dihitung.
    #  Uji yang tidak bisa gagal = tidak menjaga apa pun (pelajaran Bos).
    #
    #  ⚠️ KOREKSI WULAN (2× salah di sini): `mulai`/`akhir` = POSISI di
    #  dalam paragraf (87 → 154), BUKAN 0 → panjang. Jadi yang benar
    #  dibandingkan = SELISIHNYA, bukan `akhir` itu sendiri.
    panjang_ditandai = (c.akhir or 0) - (c.mulai or 0)
    cek('D7 `mulai`/`akhir` DIHITUNG dari naskah (bukan default 0)',
        (c.akhir or 0) > (c.mulai or 0)
        and panjang_ditandai == len(c.teks_asli or ''),
        'mulai=%s akhir=%s selisih=%s panjang teks_asli=%s'
        % (c.mulai, c.akhir, panjang_ditandai, len(c.teks_asli or '')))

print()
print('═' * 74)
print('  E. HALAMAN — KOTAK SOROTAN & KEADAAN TAMPIL')
print('═' * 74)
with urllib.request.urlopen(f'http://127.0.0.1:8000/tinjau/{TOK}',
                            timeout=30) as r:
    html = r.read().decode('utf-8', 'replace')
cek('E1 kotak sorotan ADA di form', 'id="kotak-sorot"' in html, '')
cek('E2 input `teks_asli` ada', 'name="teks_asli"' in html, '')
cek('E3 input `berkas_id` ada', 'name="berkas_id"' in html, '')
cek('E4 input `nomor_paragraf` ada', 'name="nomor_paragraf"' in html, '')
cek('E5 data sorotan dikirim ke layar', '__SOROTAN__' in html, '')
cek('E6 JS klik-kalimat ada', 'function ambilKalimat' in html, '')
cek('E7 JS batalkan ada', 'function batalkanSorot' in html, '')
cek('E8 keadaan sorotan ditampilkan (utuh)',
    'keadaan-utuh' in html, 'tidak ada label keadaan')
cek('E9 form lama TETAP ada (catatan tanpa sorotan masih bisa)',
    'placeholder="Tulis catatan untuk mahasiswa' in html, '')
cek('E10 kotak sorotan TIDAK menonjol saat kosong (hidden)',
    'id="petunjuk-sorot" class="sorot-kotak" hidden' in html, '')

print()
print('═' * 74)
print('  F. TAHAN GEMPA')
print('═' * 74)
cek('F1 naskah KOSONG → tidak error, keadaan hilang',
    S.cari_sorotan('', 'apa saja')['keadaan'] == S.HILANG, '')
cek('F2 teks_asli kosong → tidak error',
    S.cari_sorotan(NASKAH, '')['keadaan'] == S.UMUM, '')
cek('F3 kalimat HANYA 1 KATA → tidak error',
    S.cari_sorotan(NASKAH, 'Hipotesis')['keadaan'] in
    (S.UTUH, S.BERGESER, S.HILANG), '')
#  F4: naskah raksasa (400 rb kar) — ukur waktu, jangan menggantung.
raksasa = (NASKAH + '\n\n') * 1400
t0 = time.time()
S.cari_sorotan(raksasa, 'Hipotesis H3 menyatakan')
lama = time.time() - t0
cek('F4 naskah 400rb kar diperiksa < 3 detik', lama < 3.0,
    '%.2f detik' % lama)
print('     (naskah uji %s karakter, %.2f detik)' % (f'{len(raksasa):,}', lama))

#  F5: kalimat kembar — harus memilih yang PERTAMA & tidak bingung.
kembar = ('Kalimat ini muncul dua kali di naskah.\n\n'
          'Paragraf lain isinya berbeda sama sekali.\n\n'
          'Kalimat ini muncul dua kali di naskah.')
hasil_kembar = S.cari_sorotan(kembar, 'Kalimat ini muncul dua kali')
cek('F5 kalimat kembar → pilih yang PERTAMA',
    hasil_kembar['keadaan'] == S.UTUH and hasil_kembar['nomor'] == 0,
    'nomor %s' % hasil_kembar['nomor'])

print()
print('═' * 74)
print('  G. KEADAAN HARUS BERUBAH SAAT NASKAH BERUBAH (putusan Bos "segar")')
print('═' * 74)
#  KENAPA INI UJI PALING PENTING: kalau keadaan cuma dipatok saat catatan
#  dibuat, pembimbing akan melihat "Teksnya masih ada" padahal mahasiswa
#  sudah menghapusnya. Itu MENYESATKAN — dan justru itu inti keputusan Bos
#  "diperiksa saat pembimbing buka (selalu segar)".
KALIMAT_G = 'Hipotesis H3 menyatakan kepemimpinan digital'
t1 = S.cari_sorotan(NASKAH, KALIMAT_G)['keadaan']
cek('G1 sebelum diubah → utuh', t1 == S.UTUH, t1)

naskah_edit = NASKAH.replace(KALIMAT_G, 'Dugaan H3 memaparkan kepemimpinan digital')
t2 = S.cari_sorotan(naskah_edit, KALIMAT_G)['keadaan']
cek('G2 mahasiswa edit kalimatnya → keadaan BERUBAH (bukan tetap utuh)',
    t2 != S.UTUH, 'tetap %s padahal naskah sudah diubah' % t2)

naskah_hapus = NASKAH.replace(KALIMAT_G, '')
t3 = S.cari_sorotan(naskah_hapus, KALIMAT_G)['keadaan']
cek('G3 mahasiswa HAPUS kalimatnya → keadaan jadi hilang, catatan tetap ada',
    t3 == S.HILANG, t3)

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
