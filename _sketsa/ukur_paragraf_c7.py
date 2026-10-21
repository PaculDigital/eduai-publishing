"""Ukur panjang PARAGRAF naskah uji C7 (file 65) — TANPA AI, GRATIS.

Tujuan: pagar panjang harus diukur dari PARAGRAF UTUH (yang benar-benar
diganti oleh rakit_presisi), bukan dari potongan KUTIP-ASLI. Sebelum
memilih angka batas, ukur dulu sebaran panjang paragraf naskah nyata.
"""
from sqlalchemy import text
from app.models import SessionLocal
from app import pipa

db = SessionLocal()
row = db.execute(text("SELECT * FROM files WHERE id = 65")).fetchone()
kunci = row._mapping.keys() if row else []
print("KOLOM files:", list(kunci))
if row is None:
    raise SystemExit("file 65 tidak ada")
m = dict(row._mapping)
path = m.get('path') or m.get('lokasi') or m.get('file_path') or m.get('nama')
from app.config import UPLOAD_DIR
path = str(UPLOAD_DIR / str(m.get('user_id')) /
           (m.get('nama_simpan') or m.get('nama')))
print("PATH:", path)
from app.ai import _teks_dari_docx
naskah = _teks_dari_docx(path)
par = pipa.pisah_paragraf(naskah)
panj = sorted(len(p) for p in par)
n = len(panj)


def kuartil(q):
    return panj[min(n - 1, int(q * n))]


print(f"naskah {len(naskah)} kar · {n} paragraf")
print(f"min {panj[0]} · p25 {kuartil(.25)} · median {kuartil(.5)} · "
      f"p75 {kuartil(.75)} · p90 {kuartil(.9)} · p99 {kuartil(.99)} · "
      f"maks {panj[-1]}")

#  Sebaran: berapa paragraf yang MUAT jika dibatasi kelipatan tertentu
print("\n-- berapa paragraf lolos bila batas = N× panjang paragraf "
      "(ganti 7.201 kar) --")
for kali in (2, 3, 4, 5, 6, 8, 10):
    lolos = sum(1 for p in panj if 7201 <= max(200, int(p * kali)))
    print(f"  {kali}× → {lolos}/{n} paragraf muat")

#  Sebaran rasio "ganti tipikal" bila AI menulis paragraf 1,5–3×
print("\n-- contoh: paragraf mana yang muat ganti 7.201 kar "
      "pada batas 3× / 4× --")
for kali in (3, 4):
    kena = [p for p in panj if 7201 <= max(200, int(p * kali))]
    print(f"  {kali}×: butuh paragraf ≥ {(7201 / kali):.0f} kar "
          f"→ ada {len(kena)} (contoh {kena[:5]})")

#  Uji arah bawah: potongan KUTIP 163 kar vs paragraf
print("\n-- kutip 163 kar berada di paragraf sepanjang apa? --")
for p in par:
    if len(p) >= 163:
        pass
pendek = [p for p in par if 100 <= len(p) <= 400]
print(f"  paragraf 100–400 kar: {len(pendek)} · contoh panjang "
      f"{sorted(len(p) for p in pendek)[:10]}")
