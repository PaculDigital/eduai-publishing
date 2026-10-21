"""UJI JEMBATAN BAB KURANG lewat HALAMAN NYATA (TestClient + DB SALINAN).

Cara ini LEBIH KUAT dari memaksa template: yang diuji benar-benar jalur
produksi (rute → periksa_sebelum_konversi → layar).

Trik: paksa `cek_kelengkapan` mengembalikan bab kurang, lalu lihat layar.
"""
import os
import sys

os.makedirs("/tmp/uji3", exist_ok=True)
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient      # noqa: E402
from app import main as M                      # noqa: E402
from app import konversi as K                  # noqa: E402

klien = TestClient(M.app, follow_redirects=False)
r = klien.post("/masuk", data={"email": "asih.susanti@eduai.test",
                               "password": "uji12345"})
print(f"login: {r.status_code}")

lulus, gagal = [], []


def cek(nama, syarat, bukti=""):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


# ── KEADAAN B DULU: apa adanya (tanpa dipaksa) ────────────────────────
print("\n══ KEADAAN B: NASKAH APA ADANYA (naskah 81) ══")
r = klien.get("/artikel/81/konversi")
cek("B1 halaman balas 200", r.status_code == 200, str(r.status_code))
t_b = r.text
if r.status_code == 200:
    ada_jembatan = "Naskah Belum Lengkap" in t_b
    ada_konversi = "Mulai Konversi" in t_b
    print(f"     (jembatan={ada_jembatan} · tombol konversi={ada_konversi})")
    cek("B2 TIDAK ada dua tombol sekaligus",
        not (ada_jembatan and ada_konversi))
    cek("B3 tidak ada galat 500", "Traceback" not in t_b)
    cek("B4 kata mesin 'kelengkapan' tidak bocor ke layar",
        "kelengkapan" not in t_b)

# ── KEADAAN A: PAKSA bab kurang (bajakan fungsi asli, dipulihkan) ─────
print("\n══ KEADAAN A: BAB KURANG (dipaksa di fungsi asli) ══")
asli = K.cek_kelengkapan


def kurang_palsu(brief, peta):
    hasil = asli(brief, peta)
    hasil = dict(hasil)
    hasil["kurang"] = ["hasil", "kesimpulan"]
    return hasil


K.cek_kelengkapan = kurang_palsu
try:
    r2 = klien.get("/artikel/81/konversi")
    t_a = r2.text
    print(f"     status={r2.status_code} ({len(t_a)} karakter)")
    cek("A1 halaman balas 200", r2.status_code == 200, str(r2.status_code))
    cek("A2 blok 'Naskah Belum Lengkap' MUNCUL",
        "Naskah Belum Lengkap" in t_a)
    cek("A3 label manusia 'BAB IV Hasil' MUNCUL", "BAB IV Hasil" in t_a)
    cek("A4 label manusia 'BAB V Kesimpulan' MUNCUL",
        "BAB V Kesimpulan" in t_a)
    cek("A5 tombol 'Perbaiki' MUNCUL", "Perbaiki" in t_a)
    cek("A6 tombol 'Mulai Konversi' DISEMBUNYIKAN",
        "Mulai Konversi" not in t_a)
    cek("A7 kata mesin 'hasil' tidak tampil mentah",
        '>hasil<' not in t_a)
    with open("/tmp/potret_A.html", "w") as f:
        f.write(t_a)
finally:
    K.cek_kelengkapan = asli
    print("     (fungsi asli dipulihkan)")

# ── BUKTI BERGIGI: JEMBATAN DIMATIKAN HARUS GAGAL ────────────────────
print("\n══ UJI GIGI: jembatan dimatikan (blok dihapus) ══")
tpl_path = "/app/app/templates/artikel_konversi.html"
palsu = open(tpl_path).read()
terpotong = palsu.replace("Naskah Belum Lengkap", "XXX-DIMATIKAN-XXX")
with open(tpl_path, "w") as f:
    f.write(terpotong)
try:
    M.templates.env.cache.clear()
    K.cek_kelengkapan = kurang_palsu
    r3 = klien.get("/artikel/81/konversi")
    cek("G1 jembatan mati → blok TIDAK muncul (harus GAGAL di A2)",
        "Naskah Belum Lengkap" not in r3.text)
    cek("G2 jembatan mati → tombol Perbaiki TIDAK muncul",
        "Perbaiki" not in r3.text)
finally:
    with open(tpl_path, "w") as f:
        f.write(palsu)
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
