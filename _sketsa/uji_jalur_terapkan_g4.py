"""UJI OFFLINE (tanpa AI, tanpa tulis berkas) — menentukan jalur penerapan G4.

Pertanyaan: kalau user file78 menekan "Terapkan" dengan versi terpakai
(11.843 kar), jalur mana yang diambil?
  · pipa.periksa OK + ada editan -> jalur PRESISI (aman: hanya paragraf terbukti)
  · pipa gagal                   -> JALAN MUNDUR rakit(BAB_SELURUH)
                                    = seluruh naskah 93.818 kar DIGANTI 11.843 kar

Dijalankan di container:
  docker cp _sketsa/uji_jalur_terapkan_g4.py eduai-app:/tmp/
  docker exec eduai-app python3 /tmp/uji_jalur_terapkan_g4.py
"""
import sys

sys.path.insert(0, "/app")

from app import pipa  # noqa: E402
from app import ai as A  # noqa: E402
from app.models import SessionLocal, FileBerkas  # noqa: E402
from app.config import UPLOAD_DIR  # noqa: E402
import sqlite3  # noqa: E402

DB = "/app/data/eduai.db"
c = sqlite3.connect(DB)
vd = c.execute(
    "SELECT isi FROM versi_dokumen WHERE file_id=78 ORDER BY id DESC LIMIT 1"
).fetchone()[0] or ""

with SessionLocal() as db:
    fb = db.get(FileBerkas, 78)
teks_docx = A._teks_dari_berkas(UPLOAD_DIR / "7" / fb.nama_simpan, fb.nama)

print("naskah .docx  :", len(teks_docx), "kar")
print("teks terapkan :", len(vd), "kar (versi terpakai G4)")
print("susut bila rakit BAB_SELURUH:", f"{100 - 100 * len(vd) / len(teks_docx):.1f}%", "isi hilang")
print()

h = pipa.periksa(vd, teks_docx)
print("pipa.periksa  ->")
print("  ok      :", h.ok)
print("  pesan   :", h.pesan[:200])
print("  editan  :", len(h.editan) if h.editan else 0)
print("  ditolak :", len(h.ditolak) if h.ditolak else 0)
if h.editan:
    for e in h.editan[:6]:
        print("    +", repr((e.kutip or "")[:70]), "=>", repr((e.ganti or "")[:60]))
if h.ditolak:
    for d in h.ditolak[:8]:
        print("    x ditolak:", repr(str(d)[:100]))

print()
print("KESIMPULAN JALUR:")
if h.ok and h.editan:
    print("  -> JALUR PRESISI (aman, hanya paragraf terbukti diganti)")
else:
    print("  -> ❗ JALAN MUNDUR rakit(BAB_SELURUH): SELURUH naskah diganti teks terapkan")
    print("     Artinya: klik Terapkan -> naskah 93.818 kar JADI 11.843 kar +")
    print("     berisi penanda 'BAGIAN x dari 2' + catatan AI + 'TIDAK ADA PERUBAHAN'")
