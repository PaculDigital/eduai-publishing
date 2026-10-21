"""UJI 2 KEADAAN — halaman konversi EduAi (produksi, DB SALINAN).

Buktikan jembatan bab kurang BEKERJA di layar nyata:
  Keadaan A: BAB KURANG   → blok "Naskah Belum Lengkap" MUNCUL + tombol Perbaiki
  Keadaan B: BAB LENGKAP  → blok itu TIDAK muncul + tombol Konversi MUNCUL

Dipakai TestClient + DB SALINAN (aturan: jangan sentuh DB produksi).
"""
import os
import shutil
import sys

SALIN = "/tmp/uji2/eduai.db"
os.makedirs("/tmp/uji2", exist_ok=True)

# ambil DB dari produksi lalu SALIN (jangan pakai aslinya)
import subprocess
subprocess.run(["cp", "/app/data/eduai.db", SALIN], check=False)

os.environ["EDUAI_DATA_DIR"] = "/tmp/uji2"
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient          # noqa: E402
from app import main as M                          # noqa: E402
from app import konversi as K                      # noqa: E402

klien = TestClient(M.app, follow_redirects=False)

# ── login ──────────────────────────────────────────────────────────────
r = klien.post("/masuk", data={"email": "asih.susanti@eduai.test",
                               "password": "uji12345"})
print(f"login: {r.status_code}")

lulus, gagal = [], []


def cek(nama, syarat, bukti=""):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


# ── KEADAAN A: BAB KURANG ──────────────────────────────────────────────
print("\n══ KEADAAN A: BAB KURANG (dipaksa di template) ══")
# Baca template & render dengan data palsu (langsung, tanpa naskah)
#  ⚠️ Pakai LINGKUNGAN JINJA MILIK APLIKASI (`M.templates`) — jangan bikin
#     Environment sendiri: app mendaftarkan global/filter (ikon, ikon_sprite,
#     label_bagian) di sana. Environment buatan sendiri = MissingError palsu.
tpl = M.templates.get_template("artikel_konversi.html")
html_kurang = tpl.render(
    berkas={"id": 999, "nama": "uji.docx"},
    naskah_ada=True, artikel_ada=False, siap={
        "boleh": False, "pesan": "", "kurang": [],
        "kelengkapan": {"kurang": ["hasil", "kesimpulan"]}},
    daftar_revisi=[], saldo_revisi=1, token_per_revisi=2,
    jenis_tebakan="kuantitatif", pesan_galat="",
    user={"nama": "Asih", "email": "asih.susanti@eduai.test"},
)
cek("A1 blok 'Naskah Belum Lengkap' muncul",
    "Naskah Belum Lengkap" in html_kurang)
cek("A2 label manusia 'BAB IV Hasil' muncul",
    "BAB IV Hasil" in html_kurang)
cek("A3 label manusia 'BAB V Kesimpulan' muncul",
    "BAB V Kesimpulan" in html_kurang)
cek("A4 tombol 'Perbaiki' muncul", "Perbaiki" in html_kurang)
cek("A5 tombol 'Mulai Konversi' TIDAK muncul",
    "Mulai Konversi" not in html_kurang)
cek("A6 kata mesin 'kelengkapan' TIDAK bocor",
    "kelengkapan" not in html_kurang)

# ── KEADAAN B: BAB LENGKAP ─────────────────────────────────────────────
print("\n══ KEADAAN B: BAB LENGKAP ══")
html_lengkap = tpl.render(
    berkas={"id": 999, "nama": "uji.docx"},
    naskah_ada=True, artikel_ada=False, siap={
        "boleh": True, "pesan": "", "kurang": [],
        "kelengkapan": {"kurang": []},
        "identitas": {"nama": "Asih Susanti", "email": "asih.susanti@eduai.test"},
        "jenis": {"yakin": True, "jenis": "kuantitatif"},
    },
    mutu=None, mutu_pesan="", jatah={"sisa": 1},
    daftar_revisi=[], saldo_revisi=1, token_per_revisi=2,
    jenis_tebakan="kuantitatif", pesan_galat="",
    user={"nama": "Asih", "email": "asih.susanti@eduai.test"},
)
cek("B1 blok 'Naskah Belum Lengkap' TIDAK muncul",
    "Naskah Belum Lengkap" not in html_lengkap)
cek("B2 tombol 'Mulai Konversi' MUNCUL",
    "Mulai Konversi" in html_lengkap)

# ── PENGUJIAN HALAMAN NYATA (HTTP) ─────────────────────────────────────
print("\n══ PENGUJIAN HALAMAN NYATA (TestClient + DB salinan) ══")
r = klien.get("/artikel/81/konversi")
cek("C1 halaman konversi balas 200", r.status_code == 200,
    str(r.status_code))
if r.status_code == 200:
    t = r.text
    cek("C2 halaman render tanpa galat Jinja",
        "Mulai Konversi" in t or "Naskah Belum Lengkap" in t)
    cek("C3 tidak ada jejak galat 500", "Traceback" not in t)

# ── HASIL ──────────────────────────────────────────────────────────────
print()
print("═" * 60)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 60)
sys.exit(1 if gagal else 0)
