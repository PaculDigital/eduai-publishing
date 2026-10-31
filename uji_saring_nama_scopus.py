"""Uji saring nama KHUSUS Scopus di panen.

Memuat app/pustaka.py langsung lewat spec, tanpa paket app, supaya
bisa jalan di hermes tanpa sqlalchemy. Tidak ada jaringan: httpx
di-mock untuk uji cari_scopus.
"""
import importlib.util
import os
import sys

LULUS = 0
GAGAL = 0


def cek(nama, kondisi, detail=""):
    global LULUS, GAGAL
    if kondisi:
        LULUS += 1
        print("LULUS: %s" % nama)
    else:
        GAGAL += 1
        print("GAGAL: %s %s" % (nama, detail))


def muat_pustaka():
    kandidat = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "app", "pustaka.py"),
        "/opt/data/services/eduai-publishing/app/pustaka.py",
        "/app/app/pustaka.py",
    ]
    jalan = None
    for k in kandidat:
        if os.path.exists(k):
            jalan = k
            break
    assert jalan, "pustaka.py tidak ditemukan"
    spec = importlib.util.spec_from_file_location("pustaka_saring", jalan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, jalan


P, JALAN = muat_pustaka()
os.environ["EDUAI_SCOPUS_KEY"] = "dummy-uji"

# 1. Scopus dipertahankan, nama belakang benar.
PERTAHAN = [
    ("Masina N.P.S.", "Masina"),
    ("Ebrahim A.Q.", "Ebrahim"),
    ("Sáenz-Royo C.", "Sáenz-Royo"),
    ("Daškevič D.", "Daškevič"),
    ("Kankanamge A.K.S.U.", "Kankanamge"),
    ("Shi J.", "Shi"),
    ("Yu Z.", "Yu"),
    ("Xu J.", "Xu"),
    ("Masina, N.P.S.", "Masina"),
    ("Sáenz-Royo, C.", "Sáenz-Royo"),
]
for creator, harap in PERTAHAN:
    cek("scopus-pertahankan-%s" % creator,
        P.nama_belakang_scopus(creator) == harap,
        "dapat %r harap %r" % (P.nama_belakang_scopus(creator), harap))

# 2. Scopus dibuang, nama belakang tidak bisa ditentukan.
BUANG = ["", "   ", "N.P.S.", "A.K.S.U.", "123", ".,", None, ".,;"]
for creator in BUANG:
    cek("scopus-buang-%r" % (creator,),
        P.nama_belakang_scopus(creator) == "",
        "dapat %r" % (P.nama_belakang_scopus(creator),))

# 3. Saring campuran: hanya Scopus rusak yang dibuang.
campur = [
    {"source": "Scopus", "authors": "Masina N.P.S.", "title": "A"},
    {"source": "Scopus", "authors": "N.P.S.", "title": "B"},
    {"source": "Scopus", "authors": "", "title": "C"},
    {"source": "Scopus", "authors": "Shi J.", "title": "D"},
    {"source": "OpenAlex", "authors": "Wan Laura Hardilawati", "title": "E"},
    {"source": "CrossRef", "authors": "Chege Samwel Macharia", "title": "F"},
    {"source": "CrossRef", "authors": "Prasanna RPIR", "title": "G"},
    {"source": "Garuda", "authors": "Bambang Arianto", "title": "H"},
    {"source": "OpenAlex", "authors": "N.P.S.", "title": "I"},
    {"source": "CrossRef", "authors": "N.P.S.", "title": "J"},
    {"source": "Garuda", "authors": "N.P.S.", "title": "K"},
]
hasil = P.saring_scopus(campur)
cek("saring-campur-judul",
    [r["title"] for r in hasil] == ["A", "D", "E", "F", "G", "H", "I", "J", "K"],
    "dapat %r" % ([r["title"] for r in hasil],))
cek("saring-tidak-ubah-daftar-asli",
    len(campur) == 11 and campur[1]["title"] == "B",
    "daftar asli berubah")
cek("saring-tidak-dedup-tidak-karang",
    len(hasil) == 9, "dapat %s" % len(hasil))

# 4. cari_scopus end-to-end dengan httpx di-mock.
class RespPalsu:
    status_code = 200

    def __init__(self, entri):
        self._entri = entri

    def json(self):
        return {"search-results": {"entry": self._entri}}


def entri(creator, judul):
    return {
        "prism:doi": "10.1/" + judul.lower(),
        "prism:coverDate": "2024-01-01",
        "dc:title": judul,
        "dc:creator": creator,
        "citedby-count": "5",
        "dc:description": "",
        "prism:publicationName": "Jurnal Uji",
        "prism:issn": "",
    }


entri_list = [
    entri("Masina N.P.S.", "JudulA"),
    entri("N.P.S.", "JudulB"),
    entri("Sáenz-Royo C.", "JudulC"),
    entri("", "JudulD"),
    entri("Xu J.", "JudulE"),
]
asli_get = P.httpx.get
P.httpx.get = lambda *a, **k: RespPalsu(entri_list)
try:
    keluar = P.cari_scopus(["SME"], maks=15, query_siap="TITLE-ABS-KEY(SME)")
finally:
    P.httpx.get = asli_get
cek("cari-scopus-mock-judul",
    [r["title"] for r in keluar] == ["JudulA", "JudulC", "JudulE"],
    "dapat %r" % ([r["title"] for r in keluar],))
cek("cari-scopus-mock-sumber",
    all(r["source"] == "Scopus" for r in keluar),
    "sumber berubah")

# 5. Sumber lain tidak kena: helper hanya dipakai di cari_scopus.
with open(JALAN, encoding="utf-8") as f:
    sumber = f.read()
for nama_fungsi in ("def cari_openalex", "def cari_garuda",
                    "def cari_crossref"):
    mulai = sumber.index(nama_fungsi)
    # potong sampai fungsi berikutnya di level atas
    sisa = sumber[mulai + len(nama_fungsi):]
    potong = len(sisa)
    for penanda in ("\ndef ",):
        pos = sisa.find(penanda)
        if pos != -1:
            potong = min(potong, pos)
    badan = sisa[:potong]
    cek("lain-tidak-kena-%s" % nama_fungsi,
        "nama_belakang_scopus" not in badan
        and "saring_scopus" not in badan,
        "helper ditemukan di fungsi lain")

print("TOTAL: LULUS %s GAGAL %s" % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
