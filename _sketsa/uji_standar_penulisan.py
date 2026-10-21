#!/usr/bin/env python3
"""UJI STANDAR PENULISAN (26Sep26) — jalankan dari luar container.

Grup:
  S1 sintaks (ast.parse) 3 berkas diubah
  S2 modul terimpor + ATURAN_BAKU lengkap
  S3 ringkas_untuk_ai → blok terbentuk (baku & panduan user)
  S4 baca_panduan_berkas → baca PEDOMAN ASLI (PDF 105 halaman)
  S5 muat_panduan → JSON rusak tidak meledak
  S6 gerbang teks: catatan_format tersuntik di user_msg ai.py
Exit 0 = semua lulus.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GAGAL = []
def ok(nama, syarat, detail=""):
    if syarat:
        print(f"  LULUS  {nama}")
    else:
        print(f"  GAGAL  {nama} {detail}")
        GAGAL.append(nama)

# ── S1 sintaks ──
print("S1 — sintaks")
for f in ("app/standar_penulisan.py", "app/models.py", "app/ai.py"):
    try:
        ast.parse((ROOT / f).read_text(encoding="utf-8"))
        ok(f, True)
    except SyntaxError as e:
        ok(f, False, f"-> {e}")

# ── S2 modul ──
print("S2 — modul standar_penulisan")
try:
    from app.standar_penulisan import (ATURAN_BAKU, baca_panduan_berkas,
                                       muat_panduan, ringkas_untuk_ai)
    ok("impor", True)
    wajib = ["kertas", "margin_cm", "huruf", "spasi", "paragraf",
             "penomoran_halaman", "judul_bab", "tabel", "gambar",
             "bahasa", "sitasi", "sistematika", "jumlah_halaman"]
    kurang = [k for k in wajib if k not in ATURAN_BAKU]
    ok("13 bagian aturan lengkap", not kurang, f"kurang={kurang}")
    m = ATURAN_BAKU["margin_cm"]
    ok("margin 4/3/4/3 persis pedoman",
       m == {"atas": 4, "bawah": 3, "kiri": 4, "kanan": 3}, str(m))
except Exception as e:                                       # noqa: BLE001
    ok("impor", False, f"-> {e!r}")
    print("GAGAL BERANTAI — berhenti")
    sys.exit(1)

# ── S3 ringkas ──
print("S3 — ringkas_untuk_ai")
baku = ringkas_untuk_ai(None)
ok("blok baku terbentuk", baku.startswith("[STANDAR PENULISAN"), baku[:60])
ok("memuat rata tengah (putusan Bos)", "RATA TENGAH" in baku)
ok("memuat margin", "A4" in baku and "4 / bawah 3" in baku)
ok("hemat token (<1600 kar)", len(baku) < 1600, f"{len(baku)} kar")
pil = ringkas_untuk_ai({"margin_cm": {"kiri": 5}, "sumber": "Panduan Kampus X"})
ok("panduan user menang (kiri=5)", "kiri': 5" in pil or "kiri\": 5" in pil,
   pil[:200])
ok("blok user beda dari baku", pil != baku)
kosong = ringkas_untuk_ai({})
ok("dict kosong → jatuh ke baku", kosong == baku)

# ── S4 baca pedoman ASLI ──
print("S4 — baca_panduan_berkas(PDF pedoman asli)")
PDF = Path("/opt/data/cache/documents") / (
    "doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN "
    "EDISI REVISI 2025.pdf")
if PDF.exists():
    h = baca_panduan_berkas(PDF)
    print(f"    hasil: {json.dumps(h, ensure_ascii=False)[:300]}")
    ok("teks terbaca (>50000 kar)", h.get("panjang_teks", 0) > 50000,
       str(h.get("panjang_teks")))
    ok("kertas A4 terdeteksi", h.get("kertas", {}).get("ukuran") == "A4",
       str(h.get("kertas")))
    ok("margin terdeteksi", bool(h.get("margin_cm")), str(h.get("margin_cm")))
    ok("jumlah halaman 50 terdeteksi",
       h.get("jumlah_halaman", {}).get("total_minimal") == 50,
       str(h.get("jumlah_halaman")))
else:
    ok("PDF pedoman ada", False, str(PDF))
# berkas tak terbaca → jangan mengarang
h2 = baca_panduan_berkas(ROOT / "app/standar_penulisan.py")  # .py = tak didukung
ok("format tak didukung → catatan jujur", "tidak terbaca" in h2.get("catatan", ""),
   str(h2)[:120])

# ── S5 muat_panduan ──
print("S5 — muat_panduan")
ok("None → None", muat_panduan(None) is None)
ok("'' → None", muat_panduan("") is None)
ok("JSON rusak → None (tak meledak)", muat_panduan("{tidak valid") is None)
ok("JSON sah → dict", muat_panduan('{"margin_cm":{"kiri":5}}')
   == {"margin_cm": {"kiri": 5}})
ok("JSON '[]' → None", muat_panduan("[]") is None)

# ── S6 gerbang teks ai.py ──
print("S6 — gerbang teks ai.py")
src = (ROOT / "app/ai.py").read_text(encoding="utf-8")
ok("import standar_penulisan",
   "from .standar_penulisan import muat_panduan, ringkas_untuk_ai" in src)
ok("blok catatan_format dibentuk", "catatan_format = ringkas_untuk_ai(panduan_user)" in src)
ok("tersuntik di user_msg", "(catatan_format + '\\n\\n' if catatan_format else '') +" in src)
ok("tersuntik SETELAH etika & sebelum NASKAH",
   src.find("catatan_format +") < src.find("NASKAH MAHASISWA (antara penanda)"))
ok("model punya panduan_json", "panduan_json" in (ROOT / "app/models.py").read_text(encoding="utf-8"))
ok("migrasi punya panduan_json",
   "'panduan_json': 'TEXT'" in (ROOT / "app/models.py").read_text(encoding="utf-8"))

print()
print(f"HASIL: GAGAL={len(GAGAL)} {GAGAL if GAGAL else '— semua lulus'}")
sys.exit(1 if GAGAL else 0)
