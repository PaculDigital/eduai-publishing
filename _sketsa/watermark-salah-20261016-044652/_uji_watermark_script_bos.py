"""SUNTIK WATERMARK ke PDF keluaran script Bos (TANPA mengubah script aslinya).

Cara kerja:
  1. Panggil `generate_combined_pdf()` MILIK SCRIPT BOS (persis, tidak diubah)
  2. PDF hasilnya dibuka, lalu watermark ditempel di SETIAP halaman
     pakai PyMuPDF (overlay) — jadi template asli TETAP UTUH.

Kunci sinkron: bentuk PDF = PERSIS keluaran berbayar. Yang beda cuma watermark.
"""
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

import fitz  # pymupdf
import similarity_precheck as S

OUT = Path('/tmp/uji_watermark')
OUT.mkdir(parents=True, exist_ok=True)

LOGO = '/opt/data/services/eduai-publishing/app/static/logo-320.png'

TEKS = """Penelitian ini bertujuan untuk mengetahui pengaruh pemasaran digital terhadap keputusan pembelian konsumen pada toko daring di Kabupaten Bekasi. Metode penelitian yang digunakan dalam penelitian ini adalah metode kuantitatif dengan pendekatan deskriptif. Teknik pengumpulan data yang digunakan dalam penelitian ini adalah kuesioner, observasi, dan dokumentasi. Populasi dalam penelitian ini adalah seluruh mahasiswa yang terdaftar pada tahun akademik berjalan. Hasil penelitian menunjukkan bahwa terdapat pengaruh yang signifikan antara variabel X terhadap variabel Y."""


def tempel_watermark(pdf_masuk: str, pdf_keluar: str, logo: str):
    """Tempel logo EduAi + 'DEMO' di tengah SETIAP halaman."""
    doc = fitz.open(pdf_masuk)
    for hal in doc:
        w, h = hal.rect.width, hal.rect.height

        #  ── LOGO besar transparan di tengah ──
        lebar_logo = w * 0.62
        tinggi_logo = lebar_logo * 0.62      # jaga rasio (logo 1:1 → 0.62 biar aman)
        x0 = (w - lebar_logo) / 2
        y0 = (h - tinggi_logo) / 2 - 60
        hal.insert_image(
            fitz.Rect(x0, y0, x0 + lebar_logo, y0 + tinggi_logo),
            filename=logo, overlay=True, alpha=0.14,
        )

        #  ── "DEMO" besar di tengah ──
        hal.insert_textbox(
            fitz.Rect(0, h / 2 - 10, w, h / 2 + 90),
            "DEMO",
            fontsize=78, fontname="hebo",
            color=(0.75, 0.15, 0.12),       # merah
            align=fitz.TEXT_ALIGN_CENTER,
            fill_opacity=0.30,
        )

        #  ── Satu baris peringatan di FOOTER (tidak menutupi naskah) ──
        hal.insert_textbox(
            fitz.Rect(40, h - 62, w - 40, h - 34),
            "PRATINJAU GRATIS — BUKAN HASIL SUNGGUHAN  ·  "
            "Cek contoh · bukan cek internet  ·  eduaai.bikinaja.id",
            fontsize=8.5, fontname="helv",
            color=(0.75, 0.15, 0.12),
            align=fitz.TEXT_ALIGN_CENTER,
            fill_opacity=0.75,
        )

    doc.save(pdf_keluar, garbage=3, deflate=True)
    doc.close()


if __name__ == '__main__':
    print("1) Jalankan script BOS (mode contoh, persis keluaran berbayar) ...")
    hasil = S.check_similarity(TEKS, mock_mode=True)
    print(f"   similarity_index = {hasil['similarity_index']}% · "
          f"sumber = {len(hasil['sources'])}")

    asli = OUT / 'keluaran_script_asli.pdf'
    S.generate_combined_pdf(TEKS, hasil, str(asli), 'BAB 1 Pendahuluan')
    print(f"   PDF asli script : {asli} ({asli.stat().st_size} byte)")

    print("2) Tempel watermark EduAi ...")
    ada_wm = OUT / 'dengan_watermark.pdf'
    tempel_watermark(str(asli), str(ada_wm), LOGO)
    print(f"   PDF + watermark : {ada_wm} ({ada_wm.stat().st_size} byte)")

    d1 = fitz.open(asli)
    d2 = fitz.open(ada_wm)
    print(f"   halaman asli={d1.page_count} · berwatermark={d2.page_count} "
          f"(HARUS SAMA)")
