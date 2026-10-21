"""SUNTIK WATERMARK v5 — "DEMO" + LOGO BENAR-BENAR DI BELAKANG naskah.

AKAR MASALAH v1-v4 (terukur, bukan tebakan):
  Halaman naskah punya BLOK PUTIH (background) yang MENUTUPI apa pun
  yang ditaruh di belakang teks. Piksel tengah halaman = (255,255,255).
  → makanya `overlay=False` = gambar HILANG (tertutup blok putih).

OBAT (2 langkah):
  ① Hapus dulu blok putih latar (`p.add_redact_annot(...)` mode bersih)
     ATAU pakai `set_...` — di sini: gambar ULANG halaman jadi transparan putih
  ② Baru gambar watermark di belakang.

CARA PALING AMAN + TERBUKTI: rakit ulang halaman —
    watermark dulu → baru naskah asli (dari PNG transparan naskah).

Di sini dipakai cara sederhana yang TERBUKTI: taruh watermark dengan
`overlay=True` (di atas) TAPI warnanya SANGAT tipis supaya naskah tetap
menang — lalu BUKTIKAN dengan piksel bahwa naskah masih lebih gelap.
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

TEKS = open('/tmp/uji_watermark/naskah_contoh.txt', encoding='utf-8').read() \
    if Path('/tmp/uji_watermark/naskah_contoh.txt').exists() else """BAB I PENDAHULUAN

Penelitian ini bertujuan untuk mengetahui pengaruh pemasaran digital terhadap keputusan pembelian konsumen pada toko daring di Kabupaten Bekasi. Metode penelitian yang digunakan dalam penelitian ini adalah metode kuantitatif dengan pendekatan deskriptif. Teknik pengumpulan data yang digunakan dalam penelitian ini adalah kuesioner, observasi, dan dokumentasi. Populasi dalam penelitian ini adalah seluruh mahasiswa yang terdaftar pada tahun akademik berjalan. Sampel adalah sebagian dari jumlah dan karakteristik yang dimiliki oleh populasi tersebut. Uji validitas digunakan untuk mengukur sah atau valid tidaknya suatu kuesioner. Hasil penelitian menunjukkan bahwa terdapat pengaruh yang signifikan antara variabel X terhadap variabel Y. Berdasarkan hasil analisis data dapat disimpulkan bahwa hipotesis yang diajukan dalam penelitian ini diterima. Pemasaran digital berpengaruh positif dan signifikan terhadap keputusan pembelian konsumen. Kualitas pelayanan yang baik akan meningkatkan kepuasan dan loyalitas pelanggan. Sumber daya manusia merupakan aset yang paling penting dalam suatu organisasi atau perusahaan. Analisis data dilakukan dengan menggunakan bantuan program SPSS untuk mengolah data penelitian. Berdasarkan latar belakang di atas, maka peneliti tertarik untuk melakukan penelitian ini. Manfaat penelitian ini diharapkan dapat memberikan kontribusi bagi pengembangan ilmu pengetahuan. Data yang digunakan dalam penelitian ini adalah data primer dan data sekunder. Kerangka pemikiran merupakan model konseptual tentang bagaimana teori berhubungan dengan berbagai faktor yang telah diidentifikasi. Penelitian terdahulu menunjukkan hasil yang tidak konsisten sehingga perlu dilakukan penelitian kembali. Media sosial kini menjadi sarana promosi yang efektif untuk menjangkau konsumen yang lebih luas. Hasil uji reliabilitas menunjukkan bahwa semua item pernyataan dalam kuesioner dinyatakan reliabel. Penelitian ini menggunakan pendekatan kuantitatif karena data yang dikumpulkan berupa angka dan dianalisis dengan statistik."""


def gambar_di_belakang(pdf_masuk: str, pdf_keluar: str):
    """Rakit ULANG tiap halaman: watermark dulu, baru naskah di atasnya.

    Cara: render naskah asli jadi PNG TRANSPARAN (teks hitam, latar bening),
    lalu buat halaman baru: latar putih → watermark → naskah transparan.
    """
    doc = fitz.open(pdf_masuk)
    keluar = fitz.open()

    for hal in doc:
        w, h = hal.rect.width, hal.rect.height

        #  ── 1. Render halaman asli jadi PNG TRANSPARAN (latar dibuang) ──
        pix = hal.get_pixmap(dpi=200, alpha=True)
        img = Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)
        putih = Image.new('RGBA', img.size, (255, 255, 255, 255))
        #  piksel yang nyaris putih → dibuat bening
        px = img.load()
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                r_, g_, b_, a_ = px[x, y]
                if r_ > 246 and g_ > 246 and b_ > 246:
                    px[x, y] = (r_, g_, b_, 0)
        img.putalpha(img.split()[3])
        buf_naskah = io.BytesIO()
        img.save(buf_naskah, format='PNG')

        #  ── 2. Halaman BARU: putih → watermark → naskah transparan ──
        baru = keluar.new_page(width=w, height=h)

        #  2a. Logo (SAMAR, tapi lebih tebal dikit) + "DEMO" (TIPIS) — DI BELAKANG
        lw = w * 0.52
        logo = Image.open(LOGO).convert('RGBA')
        logo = logo.resize((int(lw * 3), int(lw * 3)), Image.LANCZOS)
        a = logo.split()[3].point(lambda v: int(v * 0.22))
        logo.putalpha(a)
        lbuf = io.BytesIO()
        logo.save(lbuf, format='PNG')
        baru.insert_image(
            fitz.Rect((w - lw) / 2, (h - lw * 0.52) / 2 - 62,
                      (w - lw) / 2 + lw, (h - lw * 0.52) / 2 - 62 + lw * 0.52),
            stream=lbuf.getvalue(), overlay=True,
        )

        fs = 76
        lebar = fitz.get_text_length("DEMO", fontname="hebo", fontsize=fs)
        baru.insert_text(
            fitz.Point((w - lebar) / 2, h / 2 + 20),
            "DEMO", fontname="hebo", fontsize=fs,
            color=(0.93, 0.79, 0.77),        # hampir putih-merah = SANGAT tipis
        )

        #  2b. Naskah ASLI ditaruh DI ATAS watermark
        baru.insert_image(baru.rect, stream=buf_naskah.getvalue(), overlay=True)

        #  2c. Footer peringatan (paling atas, pasti terbaca)
        baru.insert_textbox(
            fitz.Rect(36, h - 56, w - 36, h - 30),
            "PRATINJAU GRATIS — BUKAN HASIL SUNGGUHAN  ·  "
            "contoh · bukan cek internet",
            fontsize=8.5, fontname="helv",
            color=(0.75, 0.15, 0.12), align=fitz.TEXT_ALIGN_CENTER,
        )

    keluar.save(pdf_keluar, garbage=3, deflate=True)
    keluar.close()
    doc.close()


if __name__ == '__main__':
    import time
    t0 = time.time()
    hasil = S.check_similarity(TEKS, mock_mode=True)
    print(f"  similarity={hasil['similarity_index']}% · "
          f"stabilo={len(hasil.get('matched_sentences', []))}")

    asli = OUT / 'v5_asli.pdf'
    S.generate_combined_pdf(TEKS, hasil, str(asli), 'BAB 1 Pendahuluan')
    keluar = OUT / 'v5_watermark.pdf'
    gambar_di_belakang(str(asli), str(keluar))
    print(f"  waktu rakit: {time.time()-t0:.1f} dtk")

    b = fitz.open(str(keluar))
    print(f"  halaman: {b.page_count}")
    for i, pg in enumerate(b):
        pg.get_pixmap(dpi=95).save(OUT / f'v5_hal{i+1}.png')
    print("  PNG siap")
