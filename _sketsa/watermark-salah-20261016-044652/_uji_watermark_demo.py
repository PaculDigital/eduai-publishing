"""UJI WATERMARK 'DEMO' + LOGO EduAi pada PDF (WeasyPrint).

Membuktikan: PDF gaya Turnitin BISA diberi
  · logo EduAi transparan besar di tengah
  · tulisan "DEMO" besar di tengah naskah
  · berulang di SETIAP halaman
tanpa merusak teks (teks tetap bisa dipilih/dibaca).
"""
import subprocess
import sys
from pathlib import Path

OUT = Path('/tmp/uji_watermark')
OUT.mkdir(parents=True, exist_ok=True)

LOGO = Path('/opt/data/services/eduai-publishing/app/static/logo-320.png')

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @page {{
    size: A4; margin: 2cm;
    /* ── WATERMARK: berulang di SETIAP halaman, di BELAKANG teks ── */
    @bottom-center {{
      content: "";
    }}
  }}
  body {{ font-family: Georgia, serif; font-size: 16pt; line-height: 1.8; }}

  /*  Wadah watermark: menutupi SELURUH halaman, TIDAK mengganggu teks  */
  .wm {{
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: -1;              /* di BELAKANG teks */
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    pointer-events: none;
  }}
  .wm img {{
    width: 13cm; opacity: 0.13;    /* LOGO BESAR, transparan */
  }}
  .wm .demo {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 82pt; font-weight: bold;
    color: #c0392b; opacity: 0.30;  /* "DEMO" besar di tengah */
    letter-spacing: 0.25em; margin-top: -1.2cm;
  }}
  .wm .ket {{
    font-family: Arial, sans-serif; font-size: 14pt;
    color: #c0392b; opacity: 0.55; margin-top: 6px;
    text-align: center;
  }}
  h1 {{ font-size: 22pt; margin: 0 0 6pt; }}
  .meta {{ font-size: 9pt; color: #7a7a7a; }}
  hr {{ border: 0; border-top: 1px solid #000; margin: 8pt 0; }}
</style></head><body>

<!-- ── WATERMARK (fixed = muncul di semua halaman) ── -->
<div class="wm">
  <img src="file://{LOGO}" alt="EduAi">
  <div class="demo">DEMO</div>
  <div class="ket">PRATINJAU GRATIS — BUKAN HASIL SUNGGUHAN<br>
  Bank 30 kalimat contoh · bukan cek internet</div>
</div>

<h1>BAB-KGBp-4-1-1</h1>
<div class="meta">ORIGINALITY REPORT</div>
<hr>
<div style="font-size:36pt">31%</div>
<div class="meta">SIMILARITY INDEX</div>
<hr>
<div class="meta">PRIMARY SOURCES</div>
<p>Penelitian ini bertujuan untuk mengetahui pengaruh variabel independen
terhadap variabel dependen. Metode penelitian yang digunakan dalam penelitian
ini adalah metode kuantitatif dengan pendekatan deskriptif. Teknik pengumpulan
data yang digunakan dalam penelitian ini adalah kuesioner, observasi, dan
dokumentasi.</p>
<p>Populasi dalam penelitian ini adalah seluruh mahasiswa yang terdaftar pada
tahun akademik berjalan. Hasil penelitian menunjukkan bahwa terdapat pengaruh
yang signifikan antara variabel X terhadap variabel Y. Berdasarkan hasil
analisis data dapat disimpulkan bahwa hipotesis yang diajukan dalam penelitian
ini diterima.</p>
</body></html>"""

html_path = OUT / 'demo.html'
html_path.write_text(HTML, encoding='utf-8')
pdf_path = OUT / 'demo.pdf'

subprocess.run(
    ['/opt/data/.venv/bin/python3', '-m', 'weasyprint',
     str(html_path), str(pdf_path)],
    check=True, capture_output=True, timeout=180,
)

print(f"  PDF jadi : {pdf_path}  ({pdf_path.stat().st_size} byte)")

#  ── Verifikasi: gambar tertanam? teks "DEMO" hilang dari lapisan teks?
import fitz  # pymupdf
doc = fitz.open(pdf_path)
print(f"  Halaman  : {doc.page_count}")
p0 = doc[0]
print(f"  Gambar   : {len(p0.get_images(full=True))} tertanam")
ekstrak = p0.get_text()
print(f"  Teks bisa dibaca: {len(ekstrak)} karakter")
print(f"  'DEMO' ikut jadi teks? {'DEMO' in ekstrak}  "
      f"(True = masih bisa di-copy, itu wajar untuk watermark)")
