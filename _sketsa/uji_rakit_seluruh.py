"""BUKTI 2 ARAH: rakit(BAB_SELURUH) benar-benar mengganti SELURUH naskah.

SEHAT (dugaan benar): teks hasil G4 11.843 kar -> naskah jadi pendek, susut 87%.
DIRUSAK: kalau rakit TIDAK mengganti seluruh (mis. cuma tambah paragraf),
         uji ini harus GAGAL (keluar exit 1).

Murni di MEMORI — tidak menulis berkas apa pun.
  docker cp _sketsa/uji_rakit_seluruh.py eduai-app:/tmp/
  docker exec eduai-app python3 /tmp/uji_rakit_seluruh.py
"""
import sqlite3
import sys
import zipfile

sys.path.insert(0, "/app")

from app import tulis_docx  # noqa: E402
from app.models import SessionLocal, FileBerkas  # noqa: E402
from app.config import UPLOAD_DIR  # noqa: E402

LULUS, GAGAL = 0, []


def cek(nama, syarat):
    global LULUS
    print(("  OK   " if syarat else "  GAGAL") + " " + nama)
    LULUS += syarat
    if not syarat:
        GAGAL.append(nama)


with SessionLocal() as db:
    fb = db.get(FileBerkas, 78)
path = UPLOAD_DIR / "7" / fb.nama_simpan

with zipfile.ZipFile(path) as z:
    xml_lama = z.read("word/document.xml").decode("utf-8", "ignore")

c = sqlite3.connect("/app/data/eduai.db")
teks_hasil = c.execute(
    "SELECT isi FROM versi_dokumen WHERE file_id=78 ORDER BY id DESC LIMIT 1"
).fetchone()[0]

par_lama = tulis_docx.peta_paragraf(xml_lama)
print(f"paragraf naskah asli : {len(par_lama)}")
print(f"teks hasil (terapkan): {len(teks_hasil)} kar")

xml_baru, info = tulis_docx.rakit(xml_lama, teks_hasil, "__seluruh__", "")
print("info rakit           :", info)
print()

cek("rakit dilaporkan ok", info.get("ok") is True)

par_baru = tulis_docx.peta_paragraf(xml_baru)
print(f"paragraf sesudah rakit: {len(par_baru)}")
cek("jumlah paragraf BERUBAH (diganti seluruhnya)", len(par_baru) != len(par_lama))

# teks naskah sesudah rakit
teks_baru = "\n".join(p["teks"] for p in par_baru)
print(f"panjang teks sesudah : {len(teks_baru)} kar (asli "
      f"{sum(len(p['teks']) for p in par_lama)} kar)")
susut = 1 - len(teks_baru) / max(1, sum(len(p["teks"]) for p in par_lama))
print(f"susut                : {susut * 100:.1f}%")
cek("SUSUT MASIF terkonfirmasi (>80% isi hilang)", susut > 0.80)

# isi penanda AI ikut tertulis
cek("penanda 'BAGIAN 1 dari 2' ikut masuk naskah",
    "BAGIAN 1 dari 2" in teks_baru)
cek("catatan AI 'Catatan untuk Anda' ikut masuk naskah",
    "Catatan untuk Anda" in teks_baru)
cek("'TIDAK ADA PERUBAHAN' ikut masuk naskah",
    "TIDAK ADA PERUBAHAN" in teks_baru)

# isi lama HILANG
cek("isi lama naskah (Bab V) hilang dari hasil",
    "terhadap keputusan pembelian melalui pendekatan Relationship Marketing"
    not in teks_baru)

print()
print(f"HASIL: {LULUS} LULUS / {len(GAGAL)} GAGAL")
if GAGAL:
    print("GAGAL:", GAGAL)
    raise SystemExit(1)
print("TERBUKTI: rakit BAB_SELURUH mengganti seluruh naskah (cacat aktif).")
