"""SIAPKAN + POTRET halaman pembimbing dengan naskah ASLI (untuk dilihat Bos).

Token disimpan sebagai SIDIK (bukan mentah) — jadi untuk potret kita buat
bimbingan BARU di sini dan pakai token mentahnya sekali saja.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/app')

from app import ai as AI
from app import pembimbing as P
from app.models import (BerkasPembimbingan, CatatanPembimbing, Pembimbingan,
                        SessionLocal, User, VersiDokumen, init_db)

init_db()
db = SessionLocal()

NAMA = 'Prof. Uji Presisi'
#  ⚠️ Bersihkan sisa uji sampai BENAR-BENAR bersih. Dulu hanya catatan &
#  berkas yang dihapus → bimbingan lama masih tertinggal (induk terhapus
#  tapi baris versi menahan) → nomor versi bentrok saat dijalankan ulang.
#  Urutan aman: ANAK dulu (versi & catatan), INDUK belakangan.
for b in db.query(Pembimbingan).filter(Pembimbingan.nama == NAMA).all():
    db.query(VersiDokumen).filter(VersiDokumen.nomor == 100000 + b.id).delete()
    db.query(CatatanPembimbing).filter(
        CatatanPembimbing.pembimbingan_id == b.id).delete()
    db.query(BerkasPembimbingan).filter(
        BerkasPembimbingan.pembimbingan_id == b.id).delete()
    db.delete(b)
db.commit()

u = db.query(User).filter(User.id == 3).one()
FID = 9
teks = AI._teks_dari_berkas(Path('/app/_uji_doc/proposal_v1_original.docx'),
                            'proposal.docx')

baris, TOK = P.buat_bimbingan(db, u.id, nama=NAMA, hari=7)
baris.identitas = 'Prof. Uji Presisi <uji@contoh.id>'
db.add(BerkasPembimbingan(pembimbingan_id=baris.id, file_id=FID,
                          judul='PROPOSAL TESIS'))
#  ⚠️ `nomor` versi uji diambil dari id bimbingan supaya TIDAK bentrok
#  kalau skrip ini dijalankan berkali-kali (constraint unik di SQLite).
db.add(VersiDokumen(user_id=u.id, file_id=FID, bab='__naskah__',
                    nomor=100000 + baris.id, isi=teks, ukuran=len(teks),
                    sumber='uji'))
db.commit()

CONTOH = [
    #  ⚠️ Catatan uji ini SENGAJA dibuat REALISTIS: mengutip kata yang
    #  BENAR-BENAR ada di proposal (data lampiran tesis Bos), supaya
    #  potret memperlihatkan tombol "Lihat di naskah" yang benar-benar
    #  bekerja. Catatan yang tidak mengutip naskah akan berakhir jujur
    #  "Tidak ditemukan bagiannya" — itu juga benar, tapi bukan yang
    #  mau diperlihatkan di potret.
    ('BAB I', 'Latar belakang belum menunjukkan kesenjangan penelitian.', 5),
    ('BAB I', 'Digital self-efficacy belum dijelaskan definisinya.', 4),
    ('BAB II', 'Teori mediasi digital readiness belum dipaparkan.', 3),
    ('BAB III', 'Populasi dan sampel perlu dijelaskan lebih rinci.', 2),
    ('BAB IV', 'Rencana analisis data masih terlalu umum.', 1),
]
for bab, isi, mundur in CONTOH:
    db.add(CatatanPembimbing(
        pembimbingan_id=baris.id, penulis_id=baris.id, dari_pembimbing=True,
        section_id=bab, section_judul=bab, isi=isi, ronde=1, warna='kuning',
        dibuat=datetime(2026, 9, 24, 10) - timedelta(hours=mundur)))
db.commit()

#  ⚠️ SIMPAN TOKEN KE BERKAS — jangan hanya cetak. Skrip ini kadang
#  dijalankan dua kali (pernah kejadian: bimbingan pertama dihapus oleh
#  jalanan kedua, token yang dicetak jalanan pertama jadi 404).
Path('/app/_tok25b.txt').write_text(TOK, encoding='utf-8')
print('TOKEN:', TOK)
db.close()
