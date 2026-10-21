"""UKUR CAKUPAN (baca-saja, offline): berapa versi_dokumen sumber=ai yang
menghasilkan pipa.editan == 0 saat dipasangkan ke berkasnya sendiri?

Kalau editan=0 -> klik "Tulis hasil ke dokumen" jatuh ke JALAN MUNDUR rakit
BAB_SELURUH (ganti seluruh naskah).

  docker cp _sketsa/ukur_cakupan_editan0.py eduai-app:/tmp/
  docker exec eduai-app python3 /tmp/ukur_cakupan_editan0.py
"""
import sqlite3
import sys

sys.path.insert(0, "/app")

from app import pipa  # noqa: E402
from app import ai as A  # noqa: E402
from app.models import SessionLocal, FileBerkas  # noqa: E402
from app.config import UPLOAD_DIR  # noqa: E402

c = sqlite3.connect("/app/data/eduai.db")
c.row_factory = sqlite3.Row

baris = list(c.execute(
    "SELECT v.id, v.file_id, v.bab, v.nomor, v.ukuran, v.dibuat, "
    "v.isi AS isi, LENGTH(COALESCE(v.isi,'')) panjang "
    "FROM versi_dokumen v WHERE v.sumber='ai' AND LENGTH(COALESCE(v.isi,''))>0 "
    "ORDER BY v.id DESC LIMIT 25"
))
print(f"total versi sumber=ai dicek: {len(baris)}")
print()

n0 = n1 = nt = 0
for b in baris:
    with SessionLocal() as db:
        fb = db.get(FileBerkas, b["file_id"])
    if not fb:
        continue
    p = UPLOAD_DIR / "7" / fb.nama_simpan
    if not p.exists() or not str(p).endswith(".docx"):
        continue
    try:
        teks_docx = A._teks_dari_berkas(p, fb.nama)
        if not teks_docx:
            continue
        h = pipa.periksa(b["isi"] or "", teks_docx)
        ne = len(h.editan) if h.editan else 0
    except Exception as e:                                    # noqa: BLE001
        print(f"  id{b['id']} file{b['file_id']} bab={b['bab'][:18]:18} "
              f"GALAT {e}")
        continue
    if ne == 0:
        n0 += 1
    else:
        n1 += 1
    jml = f"{ne:3d}"
    tanda = "EDITAN=0 -> JALAN MUNDUR" if ne == 0 else "jalur presisi"
    print(f"  id{b['id']:3d} file{b['file_id']:3d} bab={b['bab'][:18]:18} "
          f"isi={b['panjang']:6d}kar  editan={jml}  {tanda}")
    nt += 1

print()
print(f"REKAP: {nt} versi diperiksa | editan=0: {n0} | editan>0: {n1}")
if nt:
    print(f"CAKUPAN JALAN MUNDUR: {100 * n0 / nt:.0f}% dari versi sumber=ai")
