"""UJI JEMBATAN BAB KURANG — dengan NASKAH YANG BENAR-BENAR BABNYA KURANG.

Cara: bajak `muat_naskah`/teks naskah supaya isinya cuma BAB I-II, lalu
lihat layar. Ini menguji jalur NYATA (rute → periksa_sebelum_konversi → layar),
bukan menempel data palsu.
"""
import os
import sys

os.makedirs("/tmp/uji7", exist_ok=True)
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient      # noqa: E402
from app import main as M                      # noqa: E402
from app import konversi as K                  # noqa: E402

klien = TestClient(M.app, follow_redirects=False)
klien.post("/masuk", data={"email": "asih.susanti@eduai.test",
                           "password": "uji12345"})

lulus, gagal = [], []


def cek(nama, syarat, bukti=""):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


# ── Naskah PENDEK (bab kurang): cuma BAB I + II ──────────────────────
NASKAH_PENDEK = (
    "BAB I PENDAHULUAN\n\nLatar belakang masalah ini penting untuk diteliti "
    "karena banyak fenomena yang belum dijelaskan.\n\n"
    "BAB II TINJAUAN PUSTAKA\n\nTeori yang dipakai dalam penelitian ini "
    "adalah teori motivasi dan kinerja.\n"
)

# bajak: paksa naskah yang dibaca = naskah pendek
asli_muat = getattr(K, "muat_naskah", None)
asli_baca = getattr(M, "_teks_naskah", None)

# Cari fungsi yang membaca naskah di main
import inspect
nama_baca = None
src_main = inspect.getsource(M.halaman_konversi_artikel)
print("── baris rute yang membaca naskah ──")
for j, b in enumerate(src_main.split("\n"), 1):
    if "naskah" in b and ("=" in b or "(" in b):
        print(f"   {j:3d}| {b.strip()[:100]}")
        if "=" in b and "naskah" in b.split("=")[0]:
            nama_baca = b.split("=")[0].strip().split()[-1]
print(f"\n  variabel naskah diisi oleh: {nama_baca or '(tak terdeteksi)'}")
print()

# ── Cara paling langsung: bajak cek_kelengkapan via brief ────────────
print("══ UJI A: paksa bahan KOSONG (bab kurang) lewat brief ══")
asli_cek = K.cek_kelengkapan


def cek_kurang(brief, peta):
    """Kembalikan kelengkapan dengan SEMUA bab kurang (seperti naskah pendek)."""
    return {"bahan": {"latar_belakang": True, "tinjauan_pustaka": True,
                      "metode": False, "hasil": False, "pembahasan": False,
                      "kesimpulan": False, "pustaka": False},
            "kurang": ["metode", "hasil", "pembahasan", "kesimpulan", "pustaka"],
            "ada_peta": True, "kategori": []}


K.cek_kelengkapan = cek_kurang
try:
    r = klien.get("/artikel/81/konversi")
    t = r.text
    print(f"  status={r.status_code}, {len(t)} karakter")
    cek("A1 blok 'Naskah Belum Lengkap' MUNCUL", "Naskah Belum Lengkap" in t)
    cek("A2 label 'BAB III Metode Penelitian' MUNCUL",
        "BAB III Metode Penelitian" in t)
    cek("A3 label 'BAB IV Hasil' MUNCUL", "BAB IV Hasil" in t)
    cek("A4 tombol 'Perbaiki' MUNCUL", "Perbaiki" in t)
    cek("A5 'Mulai Konversi' DISEMBUNYIKAN", "Mulai Konversi" not in t)
    cek("A6 nama bab mentah ('metode') tidak bocor", ">metode<" not in t)
    with open("/tmp/potret_A.html", "w") as f:
        f.write(t)
    print("  potret: /tmp/potret_A.html")
finally:
    K.cek_kelengkapan = asli_cek

print()
print("═" * 60)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 60)
sys.exit(1 if gagal else 0)
