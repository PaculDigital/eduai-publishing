"""SELIDIK temuan 29Sep: 'file78 IDENTIK file77 — naskah tak berubah tapi 10 TR terpotong'.

HANYA BACA. Dijalankan di dalam container eduai-app:
    docker cp _sketsa/selidik_g4_file78.py eduai-app:/tmp/ && docker exec eduai-app python3 /tmp/selidik_g4_file78.py

Pertanyaan yang dijawab:
1. Apa isi proses_ai kode G4 (status, hasil, panjang)?
2. Apakah file78 punya versi_dokumen? Isinya berisi teks revisi G4 atau sama dgn isi berkas?
3. Apakah revisi_history file78 tercatat (token, model)?
4. Hash isi berkas 77 vs 78 (apakah benar identik?)
5. Apakah teks hasil G4 ADA di versi_dokumen terakhir? (kalau YA -> desain snapshot, BUKAN bug)
"""
import hashlib
import sqlite3
import sys

sys.path.insert(0, "/app")
from app.models import SessionLocal, FileBerkas  # noqa: E402
from app.config import UPLOAD_DIR  # noqa: E402

DB = "/app/data/eduai.db"
KODE_G4 = "gRQFCEy457dJadbX0ZG_Uw"
P1 = "Pesatnya perkembangan teknologi informasi pada era digital sekarang ini"
P2 = "mengharuskan pelaku usaha menyesuaikan diri agar mampu bersaing"

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=" * 70)
print("1. proses_ai kode G4")
print("=" * 70)
baris = c.execute(
    "SELECT id, kode, status, file_id, user_id, dibuat, selesai, "
    "LENGTH(COALESCE(hasil,'')) AS len_hasil "
    "FROM proses_ai WHERE kode=? OR id IN (SELECT id FROM proses_ai WHERE kode=?)",
    (KODE_G4, KODE_G4),
).fetchall()
for b in baris:
    print(dict(b))
if not baris:
    # cari terbaru milik user 7
    print("(kode G4 tak ketemu — cari terbaru user 7)")
    for b in c.execute(
        "SELECT id, kode, status, file_id, dibuat, selesai, "
        "LENGTH(COALESCE(hasil,'')) AS len_hasil FROM proses_ai "
        "WHERE user_id=7 ORDER BY id DESC LIMIT 8"
    ):
        print(dict(b))

print()
print("=" * 70)
print("2. versi_dokumen file78 & file77")
print("=" * 70)
try:
    for b in c.execute(
        "SELECT id, file_id, versi, sumber, LENGTH(COALESCE(isi,'')) AS len_isi, dibuat "
        "FROM versi_dokumen WHERE file_id IN (77,78) ORDER BY file_id, id"
    ):
        print(dict(b))
except sqlite3.Error as e:
    print("gagal baca versi_dokumen:", e)

print()
print("=" * 70)
print("3. revisi_history file78 & file77")
print("=" * 70)
for tbl in ("revisi_history",):
    try:
        kol = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
        print("kolom:", kol)
        for b in c.execute(
            f"SELECT * FROM {tbl} WHERE file_id IN (77,78) ORDER BY id DESC LIMIT 6"
        ):
            d = dict(b)
            for k in list(d):
                if isinstance(d[k], str) and len(d[k]) > 90:
                    d[k] = d[k][:90] + f"...({len(dict(b)[k])} kar)"
            print(d)
    except sqlite3.Error as e:
        print("gagal baca", tbl, ":", e)

print()
print("=" * 70)
print("4. hash berkas 77 vs 78 (dari disk)")
print("=" * 70)
isi = {}
for fid in (77, 78):
    fb = None
    with SessionLocal() as db:
        fb = db.get(FileBerkas, fid)
    if not fb:
        print(fid, "TIDAK ADA di DB")
        continue
    p = UPLOAD_DIR / "7" / fb.nama_simpan
    if not p.exists():
        print(fid, "berkas hilang:", p)
        continue
    teks = p.read_bytes()
    isi[fid] = hashlib.md5(teks).hexdigest()
    print(fid, "|", (fb.nama or "")[:44], "|", isi[fid], "|", len(teks), "byte")

print()
print("=" * 70)
print("5. PERTANYAAN KUNCI: teks hasil G4 ada di versi_dokumen file78?")
print("=" * 70)
h = c.execute("SELECT hasil FROM proses_ai WHERE kode=?", (KODE_G4,)).fetchone()
h = (h[0] or "") if h else ""
print("hasil G4:", len(h), "kar")
# teks ganti AI = bagian setelah penanda
g = h.split("[K1-GANTI-JADI]")[-1] if "[K1-GANTI-JADI]" in h else h
kata = " ".join(g.split()[:12])
print("12 kata pertama hasil G4:", kata[:120])

vd = c.execute(
    "SELECT id, versi, sumber, LENGTH(COALESCE(isi,'')) len, isi FROM versi_dokumen "
    "WHERE file_id=78 ORDER BY id DESC LIMIT 1"
).fetchone()
if vd:
    isi_vd = vd["isi"] or ""
    fl_vd = " ".join(isi_vd.split())
    print("versi_dokumen terakhir file78: id", vd["id"], "v", vd["versi"],
          "sumber", vd["sumber"], vd["len"], "kar")
    print("  teks hasil G4 ADA di versi_dokumen?", bool(kata) and kata in fl_vd)
    print("  paragraf LAMA masih ada di versi_dokumen?", P1[:60] in fl_vd)
    print("  teks BARU ada di versi_dokumen?", P2[:50] in fl_vd)
else:
    print("❌ file78 TIDAK PUNYA versi_dokumen sama sekali!")

# pembanding: isi berkas mentah
print()
print("--- isi berkas mentah file78 ---")
with SessionLocal() as db:
    fb = db.get(FileBerkas, 78)
p = UPLOAD_DIR / "7" / fb.nama_simpan
from app import ai as A  # noqa: E402
t = A._teks_dari_berkas(p, fb.nama)
ft = " ".join(t.split())
print("panjang:", len(t))
print("  teks hasil G4 ADA di berkas?", bool(kata) and kata in ft)
print("  paragraf LAMA masih ada?", P1[:60] in ft)
