#!/usr/bin/env python3
"""UJI MIGRASI KOLOM di DB SALINAN (26Sep26) — JANGAN sentuh produksi.

Arah 1 (SEHAT) : migrasi menambah kolom yang kurang, data lama TETAP utuh.
Arah 2 (DIRUSAK): jalankan 2x → idempoten (tidak dobel, tidak error).
"""
import os
import sys
import shutil
import sqlite3
import tempfile

L = GA = 0


def cek(nama, ok, bukti=''):
    global L, GA
    if ok:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


# ── siapkan DB salinan (JANGAN produksi) ────────────────────────────────
asal = '/app/data/eduai.db'
tmp = tempfile.mkdtemp(prefix='uji_migrasi_')
salin = os.path.join(tmp, 'eduai.db')
shutil.copy2(asal, salin)
os.environ['EDUAI_DATA_DIR'] = tmp

# hitung data lama sebelum migrasi
c0 = sqlite3.connect(salin)
jml_user0 = c0.execute('SELECT COUNT(*) FROM users').fetchone()[0]
kol0 = {r[1] for r in c0.execute('PRAGMA table_info(users)')}
print(f'DB salinan: {jml_user0} user · {len(kol0)} kolom users')
cek('0. kolom baru BELUM ada (prasyarat uji)', 'nama_lengkap' not in kol0,
    str(sorted(kol0)))

# ── jalankan migrasi (dari models.py yang BARU) ─────────────────────────
sys.path.insert(0, '/app')
from app import models                                               # noqa: E402

models.init_db()

c1 = sqlite3.connect(salin)
kol1 = {r[1] for r in c1.execute('PRAGMA table_info(users)')}
jml_user1 = c1.execute('SELECT COUNT(*) FROM users').fetchone()[0]
kol_pd = {r[1] for r in c1.execute('PRAGMA table_info(profil_dokumen)')}

print('\n── A. MIGRASI BERHASIL ──')
for k in ('nama_lengkap', 'nim', 'nama_kampus', 'kota_kampus', 'fakultas',
          'program_studi', 'berkas_logo_id', 'pembimbing_1', 'pembimbing_2'):
    cek(f'A. users.{k} ADA', k in kol1, str(sorted(kol0)))
cek('A. jumlah user TIDAK berubah (data aman)', jml_user0 == jml_user1,
    f'{jml_user0} -> {jml_user1}')
for k in ('peta_json', 'peta_sidik', 'peta_dibuat', 'asal_naskah',
          'berkas_logo_id'):
    cek(f'A. profil_dokumen.{k} ADA', k in kol_pd, str(sorted(kol_pd)))

print('\n── B. IDEMPOTEN (jalankan 2x) ──')
try:
    models.init_db()
    kol2 = {r[1] for r in c1.execute('PRAGMA table_info(users)')}
    jml2 = c1.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    cek('B1. tidak error saat dijalankan ulang', True)
    cek('B2. jumlah kolom SAMA (tidak dobel)', kol1 == kol2,
        f'{len(kol1)} vs {len(kol2)}')
    cek('B3. jumlah user SAMA', jml_user1 == jml2, f'{jml_user1} vs {jml2}')
except Exception as e:
    cek('B1-B3. idempoten', False, repr(e)[:120])

print('\n── C. DATA LAMA UTUH ──')
try:
    u0 = c1.execute('SELECT email FROM users ORDER BY id LIMIT 1').fetchone()
    cek('C1. user lama bisa dibaca (email ada)', u0 is not None, str(u0))
    # baca dengan ORM (cara aplikasi) — ini yang tadi meledak
    ses = models.SessionLocal()
    try:
        ada = ses.query(models.User).order_by(models.User.id).first()
        cek('C2. ORM BISA baca User (bug tadi HILANG)', ada is not None,
            str(ada))
        if ada:
            cek('C3. kolom baru terbaca kosong (bukan error)',
                hasattr(ada, 'nama_lengkap'), 'tanpa atribut')
    finally:
        ses.close()
except Exception as e:
    cek('C1-C3. ORM baca User', False, repr(e)[:200])

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
print(f'DB salinan di {tmp} (produksi TIDAK disentuh)')
sys.exit(1 if GA else 0)
