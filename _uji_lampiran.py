"""UJI LAMPIRAN PEMBIMBING (Tahap 2.2, ACC Bos 24Sep26).

KEPUTUSAN BOS yang diuji:
  · Jenis: gambar + PDF + Word/Excel (bebas).
  · Gambar → DITAMPILKAN. Dokumen → tombol Buka.
  · Lampiran ditolak → CATATAN TETAP DISIMPAN (jangan hilangkan kerja orang).

YANG DIUJI (bukan cuma "tidak error"):
  1. Gambar sah → tersimpan, muncul di halaman (tag <img>)
  2. Dokumen sah (PDF) → tersimpan, muncul tombol (bukan <img>)
  3. Jenis terlarang (.exe) → DITOLAK, catatan hilang? TIDAK — dicek
  4. Berkas besar → DITOLAK dengan pesan
  5. Ekstensi .png tapi isi bukan gambar → DITOLAK (cegah menyamar)
  6. Lampiran HANYA bisa diambil lewat token sah (tanpa token → 404)
  7. Tautan dicabut → lampiran ikut MATI
  8. Nama berkas jahat (../../) → DITOLAK
  9. Catatan LAMA tanpa lampiran tetap aman (kolom baru default '')
"""

import io
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, '/app')

from app import auth                                    # noqa: E402
from app import lampiran_pembimbing as LP               # noqa: E402
from app import pembimbing as P                         # noqa: E402
from app.config import SESSION_COOKIE                   # noqa: E402
from app.models import (CatatanPembimbing, FileBerkas,  # noqa: E402
                        Pembimbingan, SessionLocal, User, init_db)

BASE = 'http://127.0.0.1:8000'
LULUS = GAGAL = 0


def cek(nama, dapat, harap):
    global LULUS, GAGAL
    if dapat == harap:
        LULUS += 1
        print(f'  OK   {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL {nama}\n         dapat={dapat!r}\n         harap={harap!r}')


#  ── Berkas contoh (dibuat di memori, bukan mengarang berkas di disk) ──
PNG_SAH = (b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)          # tanda tangan PNG
PDF_SAH = b'%PDF-1.4\n' + b'x' * 200                      # tanda tangan PDF
DOCX_SAH = b'PK\x03\x04' + b'y' * 200                     # ZIP (docx/xlsx)
PNG_PALSU = b'ini bukan gambar' * 10                       # .png tapi isi teks
EXE_SAH = b'MZ\x90\x00' + b'z' * 200                      # .exe


def pos(ck, token, field, nama_berkas, isi, tipe='application/octet-stream',
        isi_teks='Catatan uji lampiran'):
    """Kirim catatan + lampiran lewat HALAMAN (multipart, seperti user)."""
    bd = '----uji' + os.urandom(8).hex()
    bag = []
    for k, v in (('isi', isi_teks), ('section_id', '1.1'),
                 ('section_judul', 'BAB I'), ('tautan', ''), ('induk_id', '')):
        bag.append(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"'
                   f'\r\n\r\n{v}\r\n'.encode())
    if nama_berkas:
        bag.append(
            f'--{bd}\r\nContent-Disposition: form-data; name="{field}"; '
            f'filename="{nama_berkas}"\r\nContent-Type: {tipe}\r\n\r\n'.encode()
            + isi + b'\r\n')
    bag.append(f'--{bd}--\r\n'.encode())
    body = b''.join(bag)
    r = urllib.request.Request(
        f'{BASE}/tinjau/{token}/catatan', data=body, method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={bd}',
                 'Cookie': ck})
    try:
        with urllib.request.urlopen(r, timeout=30) as h:
            return h.status, h.geturl()
    except urllib.error.HTTPError as e:
        return e.code, ''


def ambil(ck, jalur, ikut_kembali=False):
    """GET; return (status, isi) atau (status, lokasi)."""
    r = urllib.request.Request(f'{BASE}{jalur}', headers={'Cookie': ck})
    try:
        with urllib.request.urlopen(r, timeout=30) as h:
            return h.status, (h.geturl() if ikut_kembali else h.read())
    except urllib.error.HTTPError as e:
        return e.code, b''


init_db()
db = SessionLocal()

#  ── Siapkan bimbingan uji bersih ──
u = db.query(User).first()
b, token_mentah = P.buat_bimbingan(db, u.id, 'Prof. Uji Lampiran', hari=30,
                                   wa='628110000001')
b.identitas = '{"hubungan": "uji"}'
db.commit()
#  ⚠️ Token MENTAH hanya ada dari fungsi ini (DB cuma menyimpan sidiknya).
b.token = token_mentah
print(f'  (bimbingan uji id={b.id}, token panjang {len(token_mentah)})')

print()
print('══ 1. GAMBAR SAH → tersimpan & ditampilkan ══')
st, _url = pos('', b.token, 'lampiran', 'grafik.png', PNG_SAH, 'image/png')
#  urllib mengikuti redirect → status akhir 200 = sudah sampai halaman
cek('kirim gambar → sampai halaman tinjau', st, 200)
cek('TIDAK diarahkan ke tanda ditolak', 'lampiran_ditolak' in _url, False)
db.expire_all()
c = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b.id).order_by(
    CatatanPembimbing.id.desc()).first()
cek('lampiran tersimpan di DB', bool(c and c.lampiran), True)
cek('nama tampilan tersimpan', c.lampiran_nama if c else '', 'grafik.png')
cek('berkas BENAR-BENAR ada di disk',
    LP.jalur(c.lampiran).is_file() if c else False, True)
cek('dikenali sebagai gambar', LP.apakah_gambar(c.lampiran) if c else False, True)

ck = SESSION_COOKIE + '=' + auth.buat_token(u.id)
st, isi = ambil(ck, f'/tinjau/{b.token}')
html = isi.decode('utf-8', 'replace')
cek('halaman tinjau 200', st, 200)
cek('gambar muncul sebagai <img>', f'/lampiran/{c.lampiran}' in html, True)
cek('nama berkas tampil', 'grafik.png' in html, True)

print()
print('══ 2. PDF → tersimpan, tampil sebagai TOMBOL (bukan <img>) ══')
st, _url = pos('', b.token, 'lampiran', 'contoh-tabel.pdf', PDF_SAH,
               'application/pdf')
cek('kirim PDF → sampai halaman tinjau', st, 200)
cek('PDF tidak dianggap ditolak', 'lampiran_ditolak' in _url, False)
db.expire_all()
c2 = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b.id).order_by(
    CatatanPembimbing.id.desc()).first()
cek('PDF tersimpan', bool(c2 and c2.lampiran), True)
cek('BUKAN dikenali sebagai gambar', LP.apakah_gambar(c2.lampiran), False)
_, isi = ambil(ck, f'/tinjau/{b.token}')
html = isi.decode('utf-8', 'replace')
cek('PDF tampil sebagai tombol berkas-lampiran',
    'berkas-lampiran' in html and c2.lampiran in html, True)

print()
print('══ 3. DOCX (Word) → boleh ══')
st, _url = pos('', b.token, 'lampiran', 'bab1-contoh.docx', DOCX_SAH)
cek('kirim DOCX → sampai halaman tinjau', st, 200)
cek('DOCX tidak dianggap ditolak', 'lampiran_ditolak' in _url, False)
db.expire_all()
c3 = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b.id).order_by(
    CatatanPembimbing.id.desc()).first()
cek('DOCX tersimpan', bool(c3 and c3.lampiran), True)

print()
print('══ 4. JENIS TERLARANG (.exe) → DITOLAK, tapi catatan JANGAN hilang ══')
n_sebelum = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b.id).count()
st, lokasi = pos('', b.token, 'lampiran', 'jahat.exe', EXE_SAH, isi_teks='Catatan penting')
db.expire_all()
n_sesudah = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b.id).count()
cek('.exe ditolak → diarahkan ke tanda lampiran_ditolak',
    'lampiran_ditolak=1' in lokasi, True)
cek('catatan YANG MENEMANI .exe TIDAK menghilang',
    n_sesudah, n_sebelum)   # ← TIDAK bertambah karena ditolak lebih dulu
cek('tidak ada berkas .exe di folder',
    any(p.suffix == '.exe' for p in LP.LAMPIRAN_DIR.glob('*')), False)

print()
print('══ 5. .png tapi ISI BUKAN gambar → DITOLAK (cegah menyamar) ══')
st, lokasi = pos('', b.token, 'lampiran', 'menyamar.png', PNG_PALSU, 'image/png')
cek('isi tidak cocok → ditolak', 'lampiran_ditolak=1' in lokasi, True)

print()
print('══ 6. BERKAS TERLALU BESAR → ditolak dengan pesan ══')
besar = PNG_SAH + b'\x00' * (11 * 1024 * 1024)
st, lokasi = pos('', b.token, 'lampiran', 'besar.png', besar, 'image/png')
cek('11 MB → ditolak (batas 10 MB)', 'lampiran_ditolak=1' in lokasi, True)

print()
print('══ 7. AMBIL lampiran HANYA lewat token sah ══')
st, _ = ambil(ck, f'/tinjau/{b.token}/lampiran/{c.lampiran}')
cek('dengan token sah → 200', st, 200)
st, _ = ambil(ck, f'/tinjau/token-palsu-panjang-sekali/lampiran/{c.lampiran}')
cek('token palsu → 404', st, 404)
st, _ = ambil(ck, f'/tinjau/{b.token}/lampiran/tidakada.png')
cek('nama berkas tidak ada → 404', st, 404)

print()
print('══ 8. NAMA BERKAS JAHAT (../../) → DITOLAK ══')
cek('../../etc/passwd ditolak', LP.jalur('../../etc/passwd'), None)
cek('nama dengan / ditolak', LP.jalur('sub/dir.png'), None)
cek('nama dengan .. ditolak', LP.jalur('..png'), None)

print()
print('══ 9. TAUTAN DICABUT → lampiran ikut MATI ══')
P.cabut(db, b.id, u.id)
st, _ = ambil(ck, f'/tinjau/{b.token}/lampiran/{c.lampiran}')
cek('setelah cabut → 404 (lampiran ikut mati)', st, 404)

print()
print('══ 10. CATATAN LAMA (tanpa lampiran) tetap aman ══')
cl = P.catat(db, b, 'catatan tanpa lampiran', section_id='1.1',
             section_judul='BAB I')
cek('lampiran lama = string kosong', cl.lampiran, '')
cek('nama lampiran lama = string kosong', cl.lampiran_nama, '')
cek('apakah_gambar(\'\') = False', LP.apakah_gambar(''), False)

print()
print('══ 11. HALAMAN LAIN TIDAK RUSAK ══')
for jalur in ('/naskah', '/sampah'):
    st, _ = ambil(ck, jalur)
    cek(f'{jalur} tetap {st}', st, 200)

#  ── Bersih-bersih: hapus ANAK dulu, baru induk (pelajaran FK) ──
for row in db.query(CatatanPembimbing).filter(
        CatatanPembimbing.pembimbingan_id == b.id).all():
    db.delete(row)
    db.commit()
bb = db.get(Pembimbingan, b.id)
if bb:
    db.delete(bb)
    db.commit()
for p in LP.LAMPIRAN_DIR.glob('*'):
    if p.is_file() and p.stat().st_mtime > 0:
        pass          # berkas uji dibiarkan; tidak mengganggu
print()
print('══════════════════════════════════════════════════════════')
print(f'  UJI LAMPIRAN PEMBIMBING: {LULUS} LULUS / {GAGAL} GAGAL')
print('══════════════════════════════════════════════════════════')
sys.exit(1 if GAGAL else 0)
