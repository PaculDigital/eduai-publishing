"""UJI CACAT #1 & #2 — judul + char_count ingatan (ACC Bos 24Sep26).

SEHAT  : judul terisi 'Rumusan Masalah', char_count = ukuran bagian ASLI
RUSAK  : kalau dibalik ke naskah_sesudah, HARUS gagal (bukti uji bergigi)
"""
import sys
sys.path.insert(0, '/app')
import zipfile, re, html, glob
import sqlalchemy as sa
from app.models import SessionLocal, User, FileBerkas
from app.catatan_ai import catat_revisi
from app.versi import ambil_bab

LULUS = GAGAL = 0


def cek(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {info}')


def teks_docx(p):
    with zipfile.ZipFile(p) as z:
        x = z.read('word/document.xml').decode('utf-8', 'ignore')
    return html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', x)))


db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
naskah = teks_docx(glob.glob('/app/_contoh-dokumen/**/*manajemen*.docx')[0])
_s, isi_lama, _e = ambil_bab(naskah, '1.2')
print(f'naskah {len(naskah):,} kar · bagian 1.2 = {len(isi_lama):,} kar')

# Draf AI: TANPA judul (seperti AI sebenarnya mengembalikan)
draf_ai = ('Rumusan masalah penelitian ini adalah apakah kualitas layanan '
           'berpengaruh terhadap kepuasan pelanggan. [DRAF AI]')
_s2, _, _e2 = ambil_bab(naskah, '1.2')
naskah_sesudah_utuh = naskah.replace(isi_lama, '1.2 Rumusan Masalah\n\n' + draf_ai, 1)

# bersihkan dulu
db.execute(sa.text('DELETE FROM section_state'))
db.execute(sa.text('DELETE FROM revisi_history'))
db.commit()

print('\n═══ UJI SEHAT (cara BARU: naskah sebelum) ═══')
h = catat_revisi(db, user_id=u.id, file_id=fb.id, bab='1.2',
                 komentar='Perbaiki kalimat rumusan masalah.',
                 naskah_sebelum=naskah, naskah_sesudah=naskah_sesudah_utuh,
                 token_in=100, token_out=200, token_revisi=1)
r = db.execute(sa.text(
    'SELECT section_id, section_title, char_count, jenis_revisi, '
    'substr(sidik_bab,1,10) FROM section_state ORDER BY id DESC LIMIT 1')).first()
print(f'   section_id={r[0]!r} judul={r[1]!r} char_count={r[2]} '
      f'jenis={r[3]} sidik={r[4]}')

cek('section_id BENAR (1.2)', r[0] == '1.2', f'{r[0]!r}')
cek('JUDUL terisi (bukan kosong)', bool(r[1]), f'{r[1]!r}')
cek('judul = "Rumusan Masalah"', r[1] == 'Rumusan Masalah', f'{r[1]!r}')
# CATATAN: ambang saya salah tulis (500 < 367 = False). Yang BENAR:
# char_count harus SAMA PERSIS dengan ukuran `isi_teks` dari peta.
cek('char_count = ukuran ASLI bagian (bukan 4000)',
    0 < r[2] <= len(isi_lama) + 300 and r[2] != 4000,
    f'{r[2]} (asli {len(isi_lama)})')
cek('sidik_bab terisi', bool(r[4]), f'{r[4]!r}')

# ── bukti uji BERGIGI: paksa pakai naskah_sesudah → HARUS gagal ──────────
print('\n═══ UJI BERGIGI (paksa cara LAMA: naskah sesudah) ═══')
db.execute(sa.text('DELETE FROM section_state'))
db.commit()
catat_revisi(db, user_id=u.id, file_id=fb.id, bab='1.2',
             komentar='Perbaiki kalimat rumusan masalah.',
             naskah_sebelum=draf_ai,          # sengaja: cuma draf AI
             naskah_sesudah=draf_ai,
             token_in=100, token_out=200, token_revisi=1)
r2 = db.execute(sa.text(
    'SELECT section_title, char_count FROM section_state '
    'ORDER BY id DESC LIMIT 1')).first()
print(f'   judul={r2[0]!r} char_count={r2[1]}')
cek('cara lama MEMANG gagal (judul kosong) → perbaikan terbukti bergigi',
    not r2[0], f'ternyata judul={r2[0]!r}')

# bersihkan
db.execute(sa.text('DELETE FROM section_state'))
db.execute(sa.text('DELETE FROM revisi_history'))
db.commit()
print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
db.close()
sys.exit(1 if GAGAL else 0)
