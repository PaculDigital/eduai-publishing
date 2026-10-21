"""Uji FASE 5 revisi-2: gaya penulisan hipotesis + anti-catatan-palsu."""
import sys
sys.path.insert(0, '/app')
from app import konsistensi as K

lulus = gagal = 0
def cek(n, k, info=''):
    global lulus, gagal
    if k: lulus += 1; print(f"  OK   {n}")
    else: gagal += 1; print(f"  GAGAL {n} {info}")

def peta(h24, h44, h51, panjang=900):
    return [
        {"section_id": "2.4", "section_title": "Kerangka", "isi_teks": h24 + (" isi "*panjang)},
        {"section_id": "4.4", "section_title": "Uji",      "isi_teks": h44 + (" isi "*panjang)},
        {"section_id": "5.1", "section_title": "Kesimpulan","isi_teks": h51 + (" isi "*panjang)},
    ]

brief = {"hipotesis": ["H1", "H2"]}

print("=== GAYA PENULISAN HIPOTESIS HARUS DIAKUI SAMA (tanpa catatan palsu) ===")
gaya = [
    ("H1, H2 (baku)",            "H1 dan H2",   "H1 dan H2",   "H1 dan H2"),
    ("Hipotesis 1/2",            "Hipotesis 1 dan Hipotesis 2", "Hipotesis 1, Hipotesis 2", "Hipotesis 1 dan 2"),
    ("Hipotesis ke-1/ke-2",      "Hipotesis ke-1, ke-2", "Hipotesis ke-1 dan ke-2", "hipotesis ke-1, ke-2"),
    ("H 1 / H 2 (spasi)",        "H 1 dan H 2", "H 1, H 2",    "H 1 dan H 2"),
    ("H.1 / H-2 (titik/strip)",  "H.1 dan H-2", "H.1, H-2",    "H.1 dan H-2"),
    ("HURUF BESAR semua",        "HIPOTESIS 1 DAN 2", "H1 DAN H2", "HIPOTESIS 1, 2"),
]
for nama, a, b, c in gaya:
    r = K.check_consistency(brief, peta(a, b, c))
    cek(f"{nama}: 0 catatan", len(r["issues"]) == 0, r["issues"])

print("\n=== CAMPUR GAYA (naskah asli beda dari hasil revisi) ===")
r = K.check_consistency(brief, peta("Hipotesis 1 dan Hipotesis 2", "H1 dan H2", "H1, H2"))
cek("asli 'Hipotesis N' vs revisi 'HN' -> SAMA", len(r["issues"]) == 0, r["issues"])

print("\n=== HARUS TETAP MENANGKAP YANG MEMANG BEDA ===")
r = K.check_consistency(brief, peta("Hipotesis 1 dan Hipotesis 2", "H1 dan H3", "H1, H2"))
cek("H3 di 4.4 tapi brief H2 -> ERROR", any(i["type"] == "hipotesis_mismatch_2.4_4.4" for i in r["issues"]), r["issues"])
r = K.check_consistency(brief, peta("Hipotesis 1", "H1 dan H2", "H1"))
cek("2.4 kurang 1 hipotesis -> ERROR", any(i["type"] == "hipotesis_mismatch_2.4_4.4" for i in r["issues"]), r["issues"])

print("\n=== TANPA SECTION 2.4/4.4/5.1 (proposal) -> cari ke seluruh teks ===")
p_ada = [{"section_id": "1.7", "section_title": "Kerangka", "isi_teks": "Hipotesis 1 dan Hipotesis 2 diajukan." + (" isi "*500)}]
r = K.check_consistency(brief, p_ada)
cek("proposal menulis 'Hipotesis 1/2' -> TIDAK ada catatan", len(r["issues"]) == 0, r["issues"])
r = K.check_consistency({"hipotesis": ["H9"]}, p_ada)
cek("proposal tanpa H9 -> ADA catatan", any(i["type"].startswith("hipotesis_") for i in r["issues"]), r["issues"])

print("\n=== URUTAN KODE HARUS RAPI (H1..H12 tesis mediasi ganda) ===")
b12 = {"hipotesis": [f"H{i}" for i in range(1, 13)]}
teks12 = ", ".join(f"Hipotesis {i}" for i in range(1, 13))
r = K.check_consistency(b12, peta(teks12, teks12, teks12))
cek("12 hipotesis gaya 'Hipotesis N' sinkron", len(r["issues"]) == 0, r["issues"])
r = K.check_consistency({"hipotesis": ["H1", "H2", "H10"]}, peta("H10, H2, H1", "H1, H2, H10", "H2, H10, H1"))
cek("urutan acak tetap dianggap sinkron", len(r["issues"]) == 0, r["issues"])

print("\n=== CATATAN UNTUK AI MEMUAT PERINTAH PERBAIKAN ===")
r = K.check_consistency({"hipotesis": ["H9"]}, peta("H1", "H1", "H1"))
c = K.catatan_untuk_ai(r)
cek("catatan ada", len(c) > 100)
cek("ada perintah baku H1/H2/H3", "H1, H2, H3" in c)
cek("ada larangan ubah jumlah hipotesis", "JANGAN menambah" in c)
cek("tidak bocorkan kata terlarang", not any(t in c.lower() for t in ("kuota", "rupiah", "rp ")))

print(f"\n{'='*50}\n{lulus} OK / {gagal} GAGAL\n{'='*50}")
sys.exit(1 if gagal else 0)
