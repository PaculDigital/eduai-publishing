"""UJI DROPDOWN PAKAI NASKAH NYATA (isi DB — cara OnlyOffice/EduAi menyimpan).

PERINTAH BOS 24Sep26:
  "Ya kamu uji pakai onlyoffice, kemudian di section Pembimbing,
   presisi tidak dropdownnya"

CARA UJI YANG BENAR:
  JANGAN baca berkas .docx sendiri (itu di luar jalur EduAi).
  Pakai NASKAH yang SUDAH tersimpan di DB (`versi_dokumen.isi`) — itu yang
  dibaca halaman tinjau lewat `_isi_naskah()`. Jadi yang diuji = JALUR NYATA.

Yang diukur untuk setiap naskah nyata:
  (1) berapa pilihan DROPDOWN yang muncul
  (2) apa labelnya (persis)
  (3) apakah ADA duplikat (tidak presisi)
  (4) apakah ada label sampah (daftar isi, tabel, gambar, daftar pustaka)
"""
import sys

sys.path.insert(0, '/app')

from app import kelompok_catatan as KC
from app.models import FileBerkas, SessionLocal, VersiDokumen, init_db

init_db()
db = SessionLocal()

#  ambil versi TERPANJANG per berkas (paling lengkap)
terbaik: dict[int, object] = {}
for v in db.query(VersiDokumen).all():
    isi = (v.isi or '').strip()
    if not isi:
        continue
    lama = terbaik.get(v.file_id)
    if lama is None or len(isi) > len(lama.isi or ''):
        terbaik[v.file_id] = v

print('═' * 74)
print('  UJI PRESISI DROPDOWN — NASKAH NYATA DARI DB (jalur EduAi/OnlyOffice)')
print('═' * 74)

total_masalah = 0
for fid, v in sorted(terbaik.items(), key=lambda x: -len(x[1].isi or '')):
    f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
    nama = (f.nama if f else f'file-{fid}')
    teks = v.isi or ''

    bab = KC.daftar_bab_naskah(teks)
    label = [b['label'] for b in bab]

    print(f'\n  📄 {nama}')
    print(f'     panjang: {len(teks):,} kar · versi: v{v.id}')
    print(f'     DROPDOWN: {len(label)} pilihan')
    for i, l in enumerate(label, 1):
        print(f'        {i:>2}. {l}')

    #  ── PRESISI: ada duplikat? ──
    duplikat = len(label) - len(set(label))
    if not label:
        print('     → TANPA bab (halaman pakai kotak ketik + kelompok per hari)')

    #  ── SAMPAH: label yang bukan bab isi ──
    SAMPAH = ('DAFTAR ISI', 'DAFTAR TABEL', 'DAFTAR GAMBAR', 'DAFTAR PUSTAKA',
              'HALAMAN JUDUL', 'PERSETUJUAN', 'PENGESAHAN', 'ABSTRACT',
              'ABSTRAK', 'KATA PENGANTAR', 'RIWAYAT HIDUP', 'LAMPIRAN')
    nyampah = [l for l in label if any(s in l.upper() for s in SAMPAH)]

    if duplikat:
        print(f'     ⚠️  DUPLIKAT: {duplikat}')
        total_masalah += 1
    if nyampah:
        print(f'     ⚠️  BUKAN BAB ISI: {nyampah}')
        total_masalah += 1
    if label and not duplikat and not nyampah:
        print('     ✅ presisi: tanpa duplikat, tanpa label sampah')

print()
print('═' * 74)
print(f'  NASKAH DIUJI: {len(terbaik)} · TEMUAN MASALAH: {total_masalah}')
print('═' * 74)
db.close()
