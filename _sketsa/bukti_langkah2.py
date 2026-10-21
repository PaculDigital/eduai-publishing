"""BUKTI AKHIR LANGKAH 2 — catat_revisi menerima naskah UTUH sekarang.

Meniru PERSIS apa yang dilakukan ai.py: ambil `1.2` → ganti isinya dengan
hasil revisi → kirim (naskah_utuh, naskah_sesudah_utuh) ke catat_revisi().
Lalu buktikan ingatan menyimpan '1.2' (BUKAN '__seluruh__').
"""
import sys
sys.path.insert(0, '/app')
import zipfile, re, html, glob
import sqlalchemy as sa
from app.models import SessionLocal, User, FileBerkas
from app.catatan_ai import catat_revisi, ringkasan_untuk_ai
from app.versi import ambil_bab


def teks_docx(p):
    with zipfile.ZipFile(p) as z:
        x = z.read('word/document.xml').decode('utf-8', 'ignore')
    return html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', x)))


db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
naskah_utuh = teks_docx(glob.glob('/app/_contoh-dokumen/**/*manajemen*.docx')[0])
print(f'naskah utuh: {len(naskah_utuh):,} kar · file_id={fb.id}')

# tiru ai.py: ambil 1.2, ganti isinya
_sebelum, _isi_lama, _sesudah = ambil_bab(naskah_utuh, '1.2')
print(f'bagian 1.2 = {len(_isi_lama):,} kar (dari {len(naskah_utuh):,})')
_isi_baru = ('1.2 Rumusan Masalah\n\nRumusan masalah penelitian ini adalah '
             'apakah kualitas layanan berpengaruh terhadap kepuasan pelanggan. '
             '[HASIL REVISI AI — CONTOH]')
_naskah_sesudah_utuh = _sebelum + _isi_baru + _sesudah

print(f'\n[LAMA] naskah_sebelum = potongan saja ({len(_isi_lama):,} kar)')
h1 = catat_revisi(db, user_id=u.id, file_id=fb.id, bab='1.2',
                  komentar='Perbaiki kalimat rumusan masalah.',
                  naskah_sebelum=_isi_lama, naskah_sesudah=_isi_baru,
                  token_in=999, token_out=999, token_revisi=1)
print(f'   → section_id tersimpan: {h1["section_id"]!r} '
      f'{"❌ BUTA" if h1["section_id"] == "__seluruh__" else "✅ BENAR"}')

print(f'\n[BARU] naskah_sebelum = UTUH ({len(naskah_utuh):,} kar)')
h2 = catat_revisi(db, user_id=u.id, file_id=fb.id, bab='1.2',
                  komentar='Perbaiki kalimat rumusan masalah.',
                  naskah_sebelum=naskah_utuh, naskah_sesudah=_naskah_sesudah_utuh,
                  token_in=111, token_out=222, token_revisi=1)
print(f'   → section_id tersimpan: {h2["section_id"]!r} '
      f'{"❌ BUTA" if h2["section_id"] == "__seluruh__" else "✅ BENAR"}')

print('\n--- isi section_state ---')
for r in db.execute(sa.text(
        'SELECT id, section_id, section_title, char_count, jenis_revisi '
        'FROM section_state ORDER BY id')):
    print(f'   [{r[0]}] {r[1]!r} {r[2]!r} {r[3]} kar {r[4]}')

print('\n--- PEMBACA: ringkasan_untuk_ai() (yang masuk ke prompt) ---')
print(ringkasan_untuk_ai(db, fb.id))
db.close()
