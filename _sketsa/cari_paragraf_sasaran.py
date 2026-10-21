"""Cari paragraf kandidat sasaran komentar 'latar belakang terlalu pendek'
di naskah uji C7 (file 65) — TANPA AI.

Cetak: 15 paragraf TERPANJANG + semua paragraf di sekitar judul
'LATAR BELAKANG' beserta panjangnya, supaya batas pagar dihitung dari
data nyata (bukan tebakan).
"""
from sqlalchemy import text
from app.models import SessionLocal
from app.config import UPLOAD_DIR
from app.ai import _teks_dari_docx
from app import pipa

db = SessionLocal()
m = dict(db.execute(text("SELECT * FROM files WHERE id = 65")).fetchone()
         ._mapping)
p = str(UPLOAD_DIR / str(m['user_id']) / (m['nama_simpan'] or m['nama']))
naskah = _teks_dari_docx(p)
par = pipa.pisah_paragraf(naskah)
print(f"naskah {len(naskah)} kar · {len(par)} paragraf\n")

urut = sorted(range(len(par)), key=lambda i: len(par[i]), reverse=True)
print("== 15 PARAGRAF TERPANJANG ==")
for i in urut[:15]:
    t = par[i].replace('\n', ' ')
    print(f"  [{i:3d}] {len(par[i]):5d} kar · {t[:90]!r}")

print("\n== SEKITAR JUDUL 'LATAR BELAKANG' ==")
for i, t in enumerate(par):
    if 'latar belakang' in t.lower() and len(t) < 200:
        print(f"  judul [{i}] {len(t)} kar: {t[:100]!r}")
        for j in range(max(0, i - 1), min(len(par), i + 8)):
            isi = par[j].replace('\n', ' ')
            print(f"      [{j:3d}] {len(par[j]):5d} kar · {isi[:70]!r}")
        print()

#  Berapa paragraf berada di rentang yang wajar jadi "latar belakang"
print("== SEBARAN (paragraf isi, bukan judul: ≥200 kar) ==")
isi = sorted(len(t) for t in par if len(t) >= 200)
n = len(isi)
if n:
    print(f"  n={n} · min {isi[0]} · median {isi[n // 2]} · "
          f"p90 {isi[int(n * .9)]} · maks {isi[-1]}")
