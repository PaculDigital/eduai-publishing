"""Siapkan data uji Tahap 2.5 (kelompok catatan per bab).

Dipakai untuk UJI + POTRET. Bukan kode produksi.
Dibuat 24Sep26 atas ACC Bos: "Lanjutkan 2.5".
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/app')
from app.models import (BerkasPembimbingan, CatatanPembimbing, Pembimbingan,
                        SessionLocal, User, VersiDokumen, init_db)
from app import pembimbing as P

init_db()
db = SessionLocal()

# ── bersihkan sisa uji kita sendiri ───────────────────────────────────
lama = db.query(Pembimbingan).filter(Pembimbingan.nama == 'Prof. Uji Bab').all()
for b in lama:
    db.query(CatatanPembimbing).filter(CatatanPembimbing.pembimbingan_id == b.id).delete()
    db.query(BerkasPembimbingan).filter(BerkasPembimbingan.pembimbingan_id == b.id).delete()
    db.delete(b)
db.commit()

u = db.query(User).filter(User.id == 3).one()
FID = 9   # berkas nyata milik user 3 (TESIS_LENGKAP_Goras.docx)
baris, TOK = P.buat_bimbingan(db, u.id, nama='Prof. Uji Bab',
                              wa='081234567890', hari=30)
#  ⚠️ ISI IDENTITAS (bug nyata 24Sep26): tanpa ini halaman menampilkan
#  "halaman sambutan" (minta nama pembimbing) — BUKAN halaman tinjau.
#  Akibatnya uji melaporkan "kepala-bab=0 / select=0" padahal kode BENAR.
baris.identitas = 'Prof. Uji Bab <uji@contoh.id>'
db.commit()

# ── naskah BERBAB (supaya dropdown terisi 4 bab) ───────────────────────
bk = BerkasPembimbingan(pembimbingan_id=baris.id, file_id=FID,
                        judul='Skripsi Uji — Kelompok Bab')
db.add(bk)
db.commit()

teks = ('BAB I\nPENDAHULUAN\nLatar belakang masalah belum luas.\n'
        'BAB II\nTINJAUAN PUSTAKA\nTeori utama belum disebut.\n'
        'BAB III\nMETODE PENELITIAN\nMetode sampling belum jelas.\n'
        'BAB IV\nHASIL DAN PEMBAHASAN\nTabel 4.2 belum ada sumbernya.\n')
db.add(VersiDokumen(user_id=u.id, file_id=FID, bab='BAB I', nomor=99,
                    isi=teks, ukuran=len(teks), sumber='uji'))
db.commit()

# ── catatan di BEBERAPA bab (ejaan sengaja beda: uji penyatuan) ─────────
SEKARANG = datetime(2026, 9, 24, 10, 0)
CONTOH = [
    # (bab, isi, warna, jam-mundur, ronde)
    ('BAB I — PENDAHULUAN', 'Latar belakang belum menunjukkan kesenjangan.', 'kuning', 5, 1),
    ('BAB I — PENDAHULUAN', 'Tambahkan data BPS terbaru.', 'kuning', 4, 1),
    ('BAB II — TINJAUAN PUSTAKA', 'Teori utama belum disebut sama sekali.', 'kuning', 3, 1),
    # ⚠️ ejaan beda-beda untuk bab 3 → HARUS menyatu jadi satu kelompok
    ('BAB III — METODE PENELITIAN', 'Metode sampling belum dijelaskan.', 'kuning', 3, 1),
    ('BAB 3', 'Pakai rujukan ini untuk instrumen.', 'kuning', 2, 1),
    ('bab iii', 'Uji validitas instrumen belum dilaporkan.', 'kuning', 1, 3),
    ('BAB IV — HASIL DAN PEMBAHASAN', 'Tabel 4.2 belum ada sumbernya.', 'hijau', 2, 1),
    # ⚠️ tanpa bab → kelompok terakhir
    ('', 'Mohon perbaiki penulisan daftar pustaka.', 'kuning', 1, 1),
]

for i, (bab, isi, warna, mundur, ronde) in enumerate(CONTOH):
    c = CatatanPembimbing(
        pembimbingan_id=baris.id,
        penulis_id=baris.id,
        dari_pembimbing=True,
        section_id=(bab.split('—')[0].strip() if bab else ''),
        section_judul=bab,
        isi=isi,
        ronde=ronde,
        warna=warna,
        dibuat=SEKARANG - timedelta(hours=mundur),
    )
    db.add(c)
db.commit()

jml = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == baris.id).count()
print('TOKEN:', TOK)
#  ⚠️ TULIS JUGA KE /app/_tok25.json (bug nyata 24Sep26): skrip ini dulu
#  HANYA mencetak token. Akibatnya `_uji_kelompok_bab.py` membaca berkas
#  token yang BASI (bimbingan lama sudah dihapus) → halaman menyambut
#  "halaman sambutan" → uji melaporkan "kepala-bab=0" padahal kode benar.
Path('/app/_tok25.json').write_text(
    json.dumps({'token': TOK}), encoding='utf-8')
print('catatan:', jml, '| berkas: 1 | bab di naskah: 4')
db.close()
