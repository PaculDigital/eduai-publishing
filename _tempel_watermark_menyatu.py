"""TEMPEL watermark MENYATU ke PDF — tinggal 1 langkah (insert_image).

Pakai gambar jadi: app/static/watermark-uji-mirip.png
  (sudah berisi LOGO + DEMO + PRATINJAU menyatu, transparan)

Tidak perlu lagi menyusun 2 lapis (logo + teks) — tinggal tempel gambarnya.
"""
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

import fitz
import similarity_precheck as S

WM = '/opt/data/services/eduai-publishing/app/static/watermark-uji-mirip.png'
OUT = Path('/tmp/uji_watermark')


def tempel_menyatu(pdf_masuk: str, pdf_keluar: str, skala: float = 0.86):
    doc = fitz.open(pdf_masuk)
    for hal in doc:
        w, h = hal.rect.width, hal.rect.height
        lebar = w * skala
        from PIL import Image as _I
        im = _I.open(WM)
        tinggi = lebar * im.height / im.width
        x0 = (w - lebar) / 2
        y0 = (h - tinggi) / 2
        hal.insert_image(fitz.Rect(x0, y0, x0 + lebar, y0 + tinggi),
                         filename=WM, overlay=True)
        #  footer peringatan
        hal.insert_textbox(
            fitz.Rect(36, h - 56, w - 36, h - 30),
            "PRATINJAU GRATIS — BUKAN HASIL SUNGGUHAN  ·  contoh · bukan cek internet",
            fontsize=8.5, fontname="helv", color=(0.75, 0.15, 0.12),
            align=fitz.TEXT_ALIGN_CENTER,
        )
    doc.save(pdf_keluar, garbage=3, deflate=True)
    doc.close()


if __name__ == '__main__':
    teks = open('/tmp/uji_watermark/naskah_turnitin.txt', encoding='utf-8').read()
    hasil = S.check_similarity(teks, mock_mode=True)
    print(f"  similarity={hasil['similarity_index']}% · stabilo={len(hasil['matched_sentences'])}")

    asli = OUT / 'menyatu_asli.pdf'
    S.generate_combined_pdf(teks, hasil, str(asli),
        'BAB 2 Identifikasi Masalah, Tujuan, dan Perumusan Riset Pemasaran')

    keluar = OUT / 'menyatu_watermark.pdf'
    tempel_menyatu(str(asli), str(keluar))

    a, b = fitz.open(str(asli)), fitz.open(str(keluar))
    print(f"  asli {a.page_count} hlm → +wm {b.page_count} hlm")
    for i in [0, 1, 12]:
        if i < b.page_count:
            b[i].get_pixmap(dpi=90).save(OUT / f'menyatu_hal{i+1}.png')
    print("  PNG siap")
