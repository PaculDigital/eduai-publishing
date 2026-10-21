"""UJI GIGI + KEADAAN LENGKAP — jembatan bab kurang.

Gigi: jembatan dimatikan → HARUS ada yang GAGAL.
Lengkap: bab lengkap → kartu konversi MUNCUL, jembatan TIDAK.
"""
import os
import sys

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


KURANG = {"bahan": {"metode": False, "hasil": False, "kesimpulan": False},
          "kurang": ["metode", "hasil", "kesimpulan"],
          "ada_peta": True, "kategori": []}
asli = K.cek_kelengkapan

# ── KEADAAN ②: BAB LENGKAP (apa adanya, naskah 81) ────────────────────
print("\n══ KEADAAN ②: BAB LENGKAP ══")
r = klien.get("/artikel/81/konversi")
t = r.text
cek("B1 status 200", r.status_code == 200, str(r.status_code))
cek("B2 jembatan TIDAK muncul", "Naskah Belum Lengkap" not in t)
cek("B3 kartu 'Identitas Penulis' MUNCUL", "Identitas Penulis" in t)
cek("B4 'Mulai Konversi' MUNCUL", "Mulai Konversi" in t)

# ── KEADAAN ①: BAB KURANG ─────────────────────────────────────────────
print("\n══ KEADAAN ①: BAB KURANG ══")
K.cek_kelengkapan = lambda brief, peta: KURANG
try:
    r2 = klien.get("/artikel/81/konversi")
    t2 = r2.text
    cek("A1 status 200", r2.status_code == 200, str(r2.status_code))
    cek("A2 jembatan MUNCUL", "Naskah Belum Lengkap" in t2)
    cek("A3 label manusia MUNCUL", "BAB III Metode Penelitian" in t2)
    cek("A4 'Perbaiki' MUNCUL", "Perbaiki" in t2)
    cek("A5 'Mulai Konversi' TIDAK muncul", "Mulai Konversi" not in t2)
    cek("A6 'Identitas Penulis' TIDAK muncul (kartu konversi disembunyikan)",
        "Identitas Penulis" not in t2)
    cek("A7 TIDAK ada dua tombol sekaligus",
        not ("Naskah Belum Lengkap" in t2 and "Mulai Konversi" in t2))
finally:
    K.cek_kelengkapan = asli

# ── UJI GIGI: jembatan DIMATIKAN ──────────────────────────────────────
print("\n══ UJI GIGI: template dimatikan (blok dihapus) ══")
p = "/app/app/templates/artikel_konversi.html"
asli_tpl = open(p).read()
open(p, "w").write(asli_tpl.replace("Naskah Belum Lengkap", "XXX-MATI-XXX"))
try:
    M.templates.env.cache.clear()
    K.cek_kelengkapan = lambda brief, peta: KURANG
    r3 = klien.get("/artikel/81/konversi")
    cek("G1 jembatan mati → blok hilang (buktikan uji bergigi)",
        "Naskah Belum Lengkap" not in r3.text)
    #  ⚠️ G2 jangan cari 'Perbaiki' atau '/kolaborasi' sendirian:
    #     'Perbaiki' juga di "Perbaiki Sebagian (Revisi)";
    #     '/kolaborasi' juga ADA DI MENU (_menu.html:29) → GAGAL PALSU.
    #     Paling tepat: cari KALIMAT AJAKAN khas jembatan (hanya ada di sana).
    cek("G2 jembatan mati → kalimat ajakan jembatan hilang",
        "Lengkapi dulu bagian di atas" not in r3.text)
finally:
    open(p, "w").write(asli_tpl)
    M.templates.env.cache.clear()
    K.cek_kelengkapan = asli
    print("     (template asli dipulihkan)")

print()
print("═" * 60)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 60)
sys.exit(1 if gagal else 0)
