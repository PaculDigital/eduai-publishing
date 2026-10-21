"""UJI JEMBATAN BAB KURANG — versi BENAR (16 Okt 2026).

Pelajaran dari uji sebelumnya:
  1. JANGAN mengubah berkas template produksi untuk uji gigi — kalau crash,
     kerusakan TERTINGGAL di container hidup (pernah terjadi: judul jadi XXX).
  2. Uji gigi harus lewat SALINAN template di /tmp, bukan berkas asli.
  3. Asersi harus pakai kalimat yang HANYA ADA di blok itu.
"""
import os
import shutil
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
asli_kel = K.cek_kelengkapan


def paksa_kurang(brief, peta):
    return KURANG


# ══ KEADAAN ②: BAB LENGKAP (naskah 81 apa adanya) ═══════════════════
print("\n══ KEADAAN ②: BAB LENGKAP ══")
r = klien.get("/artikel/81/konversi")
t = r.text
cek("B1 status 200", r.status_code == 200, str(r.status_code))
cek("B2 jembatan TIDAK muncul", "Naskah Belum Lengkap" not in t)
cek("B3 kartu konversi MUNCUL", "Identitas Penulis" in t)
cek("B4 'Mulai Konversi' MUNCUL", "Mulai Konversi" in t)

# ══ KEADAAN ①: BAB KURANG ═══════════════════════════════════════════
print("\n══ KEADAAN ①: BAB KURANG ══")
K.cek_kelengkapan = paksa_kurang
try:
    r2 = klien.get("/artikel/81/konversi")
    t2 = r2.text
finally:
    K.cek_kelengkapan = asli_kel

cek("A1 status 200", r2.status_code == 200, str(r2.status_code))
cek("A2 judul jembatan MUNCUL", "Naskah Belum Lengkap" in t2)
cek("A3 kalimat ajakan MUNCUL", "Lengkapi dulu bagian di atas" in t2)
cek("A4 label manusia 'BAB III Metode Penelitian' MUNCUL",
    "BAB III Metode Penelitian" in t2)
cek("A5 tombol Perbaiki (href /kolaborasi) MUNCUL",
    'href="/kolaborasi"' in t2)
cek("A6 'Mulai Konversi' DISEMBUNYIKAN", "Mulai Konversi" not in t2)
cek("A7 kartu konversi DISEMBUNYIKAN", "Identitas Penulis" not in t2)
cek("A8 tidak ada dua tombol sekaligus",
    not ("Naskah Belum Lengkap" in t2 and "Mulai Konversi" in t2))
cek("A9 nama bab mentah tidak bocor", ">metode<" not in t2)

# ══ UJI GIGI: rusak SALINAN, bukan berkas produksi ═══════════════════
print("\n══ UJI GIGI (lewat SALINAN template, produksi TIDAK disentuh) ══")
ASLI = "/app/app/templates/artikel_konversi.html"
SALIN = "/tmp/uji_gigi_tpl/artikel_konversi.html"
os.makedirs("/tmp/uji_gigi_tpl", exist_ok=True)
shutil.copy2(ASLI, SALIN)

# rusak salinan: buang judul jembatan
s = open(SALIN).read()
open(SALIN, "w").write(s.replace("Naskah Belum Lengkap", "XXX-MATI-XXX"))

# arahkan template loader app ke folder salinan SEMENTARA
dari_sebelum = list(M.templates.env.loader.searchpath)
M.templates.env.loader.searchpath = ["/tmp/uji_gigi_tpl"] + dari_sebelum
M.templates.env.cache.clear()
try:
    K.cek_kelengkapan = paksa_kurang
    r3 = klien.get("/artikel/81/konversi")
    t3 = r3.text
finally:
    K.cek_kelengkapan = asli_kel
    M.templates.env.loader.searchpath = dari_sebelum
    M.templates.env.cache.clear()

cek("G1 rusak → judul jembatan HILANG (buktikan bergigi)",
    "Naskah Belum Lengkap" not in t3, "kalau ADA berarti uji tidak bergigi")
#  ⚠️ G2 DIHAPUS 16 Okt 2026: asersinya cacat rancang — di versi rusak hanya
#     JUDUL yang dimatikan, kalimat ajakannya masih ada ⇒ G2 selalu GAGAL
#     walau kode benar. G1 + G3 sudah cukup membuktikan uji bergigi.
cek("G3 berkas PRODUKSI tetap UTUH (tidak disentuh uji)",
    "Naskah Belum Lengkap" in open(ASLI).read())

print()
print("═" * 60)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 60)
sys.exit(1 if gagal else 0)
