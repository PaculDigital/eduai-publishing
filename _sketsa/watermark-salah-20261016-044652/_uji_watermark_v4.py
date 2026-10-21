"""SUNTIK WATERMARK v4 — sesuai koreksi Bos:
  · "DEMO" + LOGO ditaruh DI BELAKANG naskah (overlay=False)
  · "DEMO" lebih TIPIS · logo lebih TEBAL
  · URL eduaai.bikinaja.id DIHAPUS
  · naskah + stabilo ikut tampil

CATATAN URUTAN LAPIS (jawaban pertanyaan Bos):
  overlay=False → gambar DITARUH DI BAWAH (di belakang naskah)  ← dipakai sekarang
  overlay=True  → gambar DITARUH DI ATAS (menimpa naskah)       ← v1-v3, SALAH
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

TEKS = """BAB I PENDAHULUAN

Penelitian ini bertujuan untuk mengetahui pengaruh pemasaran digital terhadap keputusan pembelian konsumen pada toko daring di Kabupaten Bekasi. Metode penelitian yang digunakan dalam penelitian ini adalah metode kuantitatif dengan pendekatan deskriptif. Teknik pengumpulan data yang digunakan dalam penelitian ini adalah kuesioner, observasi, dan dokumentasi. Populasi dalam penelitian ini adalah seluruh mahasiswa yang terdaftar pada tahun akademik berjalan. Sampel adalah sebagian dari jumlah dan karakteristik yang dimiliki oleh populasi tersebut. Uji validitas digunakan untuk mengukur sah atau valid tidaknya suatu kuesioner. Hasil penelitian menunjukkan bahwa terdapat pengaruh yang signifikan antara variabel X terhadap variabel Y. Berdasarkan hasil analisis data dapat disimpulkan bahwa hipotesis yang diajukan dalam penelitian ini diterima. Pemasaran digital berpengaruh positif dan signifikan terhadap keputusan pembelian konsumen. Kualitas pelayanan yang baik akan meningkatkan kepuasan dan loyalitas pelanggan. Sumber daya manusia merupakan aset yang paling penting dalam suatu organisasi atau perusahaan. Analisis data dilakukan dengan menggunakan bantuan program SPSS untuk mengolah data penelitian. Berdasarkan latar belakang di atas, maka peneliti tertarik untuk melakukan penelitian ini. Manfaat penelitian ini diharapkan dapat memberikan kontribusi bagi pengembangan ilmu pengetahuan. Data yang digunakan dalam penelitian ini adalah data primer dan data sekunder. Kerangka pemikiran merupakan model konseptual tentang bagaimana teori berhubungan dengan berbagai faktor yang telah diidentifikasi. Penelitian terdahulu menunjukkan hasil yang tidak konsisten sehingga perlu dilakukan penelitian kembali. Media sosial kini menjadi sarana promosi yang efektif untuk menjangkau konsumen yang lebih luas. Hasil uji reliabilitas menunjukkan bahwa semua item pernyataan dalam kuesioner dinyatakan reliabel. Penelitian ini menggunakan pendekatan kuantitatif karena data yang dikumpulkan berupa angka dan dianalisis dengan statistik."""


def logo_bytes(path: str, alpha: float) -> bytes:
    im = Image.open(path).convert('RGBA')
    a = im.split()[3].point(lambda v: int(v * alpha))
    im.putalpha(a)
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()


def campur(hex_warna, alpha, latar=(1, 1, 1)):
    r, g, b = (int(hex_warna[i:i+2], 16) / 255 for i in (0, 2, 4))
    return tuple(c * alpha + l * (1 - alpha) for c, l in zip((r, g, b), latar))


def tempel(pdf_masuk, pdf_keluar):
    doc = fitz.open(pdf_masuk)
    png = logo_bytes(LOGO, alpha=0.22)
    demo = campur('c0261d', alpha=0.18)
    footer = campur('c0261d', alpha=0.80)

    for hal in doc:
        w, h = hal.rect.width, hal.rect.height

        #  ── LOGO + "DEMO" DI BELAKANG NASKAH (overlay=False) ──
        lw = w * 0.52
        hal.insert_image(
            fitz.Rect((w - lw) / 2, (h - lw * 0.52) / 2 - 62,
                      (w - lw) / 2 + lw, (h - lw * 0.52) / 2 - 62 + lw * 0.52),
            stream=png, overlay=False,          # ← DI BELAKANG
        )

        fs = 76
        lebar = fitz.get_text_length("DEMO", fontname="hebo", fontsize=fs)
        hal.insert_text(
            fitz.Point((w - lebar) / 2, h / 2 + 20),
            "DEMO", fontname="hebo", fontsize=fs, color=demo,
            overlay=False,                       # ← DI BELAKANG
        )

        #  ── Footer: DI ATAS (harus terbaca) ──
        hal.insert_textbox(
            fitz.Rect(36, h - 56, w - 36, h - 30),
            "PRATINJAU GRATIS — BUKAN HASIL SUNGGUHAN  ·  "
            "contoh · bukan cek internet",
            fontsize=8.5, fontname="helv", color=footer,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    doc.save(pdf_keluar, garbage=3, deflate=True)
    doc.close()


if __name__ == '__main__':
    hasil = S.check_similarity(TEKS, mock_mode=True)
    print(f"  similarity={hasil['similarity_index']}% · "
          f"stabilo={len(hasil.get('matched_sentences', []))} kalimat")

    asli = OUT / 'v4_asli.pdf'
    S.generate_combined_pdf(TEKS, hasil, str(asli), 'BAB 1 Pendahuluan')
    keluar = OUT / 'v4_watermark.pdf'
    tempel(str(asli), str(keluar))

    a, b = fitz.open(str(asli)), fitz.open(str(keluar))
    print(f"  asli {a.page_count} hlm → +wm {b.page_count} hlm")
    for i, pg in enumerate(b):
        pg.get_pixmap(dpi=95).save(OUT / f'v4_hal{i+1}.png')
    print("  PNG siap")
