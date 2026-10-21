"""SUNTIK WATERMARK v2 — logo SAMAR + "DEMO" benar-benar muncul.

Perbaikan dari v1:
  · "DEMO" pakai insert_text (BUKAN textbox+opacity yang diabaikan)
    + warna dicampur ke latar putih dulu => tampak transparan
  · Logo diturunkan opacity-nya lewat pixmap PIL (PyMuPDF tak bisa alpha di PNG)
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

import fitz
import similarity_precheck as S
from PIL import Image

OUT = Path('/tmp/uji_watermark')
LOGO = '/opt/data/services/eduai-publishing/app/static/logo-320.png'

TEKS = """Penelitian ini bertujuan untuk mengetahui pengaruh pemasaran digital terhadap keputusan pembelian konsumen pada toko daring di Kabupaten Bekasi. Metode penelitian yang digunakan dalam penelitian ini adalah metode kuantitatif dengan pendekatan deskriptif. Teknik pengumpulan data yang digunakan dalam penelitian ini adalah kuesioner, observasi, dan dokumentasi. Populasi dalam penelitian ini adalah seluruh mahasiswa yang terdaftar pada tahun akademik berjalan. Hasil penelitian menunjukkan bahwa terdapat pengaruh yang signifikan antara variabel X terhadap variabel Y."""


def logo_samar(path: str, alpha: float = 0.10) -> bytes:
    """Buat versi logo yang SAMAR (alpha rendah), kembalikan PNG bytes."""
    im = Image.open(path).convert('RGBA')
    a = im.split()[3]
    a = a.point(lambda v: int(v * alpha))
    im.putalpha(a)
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()


def campur(hex_warna, latar=(1, 1, 1), alpha=0.30):
    """Campur warna ke putih → tampak transparan (PyMuPDF tak punya alpha teks)."""
    r, g, b = (int(hex_warna[i:i+2], 16) / 255 for i in (0, 2, 4))
    return tuple(c * alpha + l * (1 - alpha) for c, l in zip((r, g, b), latar))


def tempel(pdf_masuk, pdf_keluar):
    doc = fitz.open(pdf_masuk)
    png = logo_samar(LOGO, alpha=0.10)          # logo SAMAR
    merah = campur('c0261d', alpha=0.34)         # "DEMO" tampak transparan
    merah_kecil = campur('c0261d', alpha=0.80)   # footer (harus jelas)

    for hal in doc:
        w, h = hal.rect.width, hal.rect.height

        #  ── 1. LOGO besar SAMAR di tengah ──
        lw = w * 0.58
        hal.insert_image(
            fitz.Rect((w - lw) / 2, (h - lw * 0.58) / 2 - 70,
                      (w - lw) / 2 + lw, (h - lw * 0.58) / 2 - 70 + lw * 0.58),
            stream=png, overlay=True,
        )

        #  ── 2. "DEMO" besar (insert_text — pasti muncul) ──
        fs = 86
        lebar_teks = fitz.get_text_length("DEMO", fontname="hebo", fontsize=fs)
        hal.insert_text(
            fitz.Point((w - lebar_teks) / 2, h / 2 + 22),
            "DEMO", fontname="hebo", fontsize=fs, color=merah,
        )

        #  ── 3. Peringatan FOOTER (jelas, tidak menutupi) ──
        hal.insert_textbox(
            fitz.Rect(36, h - 58, w - 36, h - 30),
            "PRATINJAU GRATIS — BUKAN HASIL SUNGGUHAN  ·  "
            "contoh · bukan cek internet  ·  eduaai.bikinaja.id",
            fontsize=8.5, fontname="helv", color=merah_kecil,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    doc.save(pdf_keluar, garbage=3, deflate=True)
    doc.close()


if __name__ == '__main__':
    hasil = S.check_similarity(TEKS, mock_mode=True)
    asli = OUT / 'v2_asli.pdf'
    S.generate_combined_pdf(TEKS, hasil, str(asli), 'BAB 1 Pendahuluan')
    keluar = OUT / 'v2_watermark.pdf'
    tempel(str(asli), str(keluar))

    a = fitz.open(str(asli))
    b = fitz.open(str(keluar))
    print(f"  asli  : {a.page_count} hlm, {asli.stat().st_size} byte")
    print(f"  +wm   : {b.page_count} hlm, {keluar.stat().st_size} byte")
    p = b[2]
    t = p.get_text()
    print(f"  'DEMO' muncul sebagai teks? {'DEMO' in t}")
    print(f"  'PRATINJAU' ada? {'PRATINJAU' in t}")
    print(f"  isi asli utuh? {'researchsquare' in t and 'SIMILARITY' in t}")
    for i, pg in enumerate(b):
        pg.get_pixmap(dpi=90).save(OUT / f'v2_hal{i+1}.png')
    print("  PNG siap")
