"""UJI MIRIP / UJI PLAGIARISME EduAi — modul resmi.

TUGAS: dari naskah → **SATU file PDF** berisi:
    cover (doc ID)  +  naskah + stabilo  +  laporan similarity
    (persis template Turnitin)  +  watermark (logo + DEMO + PRATINJAU)

NOL MESIN BARU — modul ini hanya MERAKIT yang SUDAH ADA:
  · `scripts/similarity_precheck.py` (script Bos) → check_similarity()
    + generate_combined_pdf()  [sudah diperbaiki bug stabilonya]
  · `app/static/watermark-uji-mirip.png` (gambar menyatu, sudah jadi)

CARA PAKAI:
    from app import uji_mirip
    pdf = uji_mirip.buat_laporan(teks, judul="BAB II ...", keluar="/tmp/x.pdf")
"""
from __future__ import annotations

import sys
from pathlib import Path

#  ── Lokasi script Bos (di luar proyek: /opt/data/scripts) ─────────────
_SCRIPTS = Path('/opt/data/scripts')
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_WM = Path(__file__).resolve().parent / 'static' / 'watermark-uji-mirip.png'

#  Kalimat footer (putusan Bos: keterangan di FOOTER, warna brand)
_FOOTER = ('PRATINJAU GRATIS  ·  BUKAN HASIL SUNGGUHAN  ·  '
           'contoh  ·  bukan cek internet')

#  Warna footer = merah peringatan (putusan Bos ① A · ② C = brand)
_WARNA_FOOTER = (0.73, 0.13, 0.11)


def _watermark():
    """Ambil gambar watermark menyatu (logo + DEMO + PRATINJAU)."""
    if not _WM.exists():
        raise FileNotFoundError(
            f'Gambar watermark belum ada: {_WM}\n'
            f'Buat dulu: python3 _buat_watermark_menyatu.py')
    return str(_WM)


def tempel_watermark(pdf_masuk: str, pdf_keluar: str, skala: float = 0.86) -> str:
    """Tempel watermark (1 gambar menyatu) + footer ke SETIAP halaman PDF."""
    import fitz

    wm = _watermark()
    doc = fitz.open(pdf_masuk)

    from PIL import Image
    im = Image.open(wm)

    for hal in doc:
        w, h = hal.rect.width, hal.rect.height
        lebar = w * skala
        tinggi = lebar * im.height / im.width
        x0 = (w - lebar) / 2
        y0 = (h - tinggi) / 2
        hal.insert_image(fitz.Rect(x0, y0, x0 + lebar, y0 + tinggi),
                         filename=wm, overlay=True)
        hal.insert_textbox(
            fitz.Rect(36, h - 56, w - 36, h - 30),
            _FOOTER, fontsize=8.5, fontname='helv',
            color=_WARNA_FOOTER, align=fitz.TEXT_ALIGN_CENTER)

    doc.save(pdf_keluar, garbage=3, deflate=True)
    doc.close()
    return pdf_keluar


def buat_laporan(teks: str, judul: str, keluar: str,
                 mock: bool = True, gratis: bool = None) -> dict:
    """Buat SATU file PDF laporan uji mirip.

    teks   : naskah (teks biasa)
    judul  : judul dokumen (tampil di cover + laporan)
    keluar : path PDF hasil
    mock   : True = pakai mode contoh (11 sumber, TANPA cek internet)
             False = cek sungguhan ke 11 domain (butuh mesin pencari)
    gratis : None = ikut `mock`; True/False menimpa (dipakai pemanggil app)

    Kembalikan dict: {'pdf': path, 'indeks': %, 'jumlah_sumber': n,
                      'stabilo': n, 'halaman': n}
    """
    import tempfile

    import similarity_precheck as S

    if gratis is not None:
        mock = bool(gratis)
    if not teks or not teks.strip():
        raise ValueError('Naskah kosong — tidak ada yang bisa diuji.')

    #  ① mesin script Bos (persis, tidak diubah)
    hasil = S.check_similarity(teks, mock_mode=mock)

    #  ② PDF gaya Turnitin (script Bos) — ke berkas sementara
    with tempfile.TemporaryDirectory() as td:
        asli = str(Path(td) / 'asli.pdf')
        S.generate_combined_pdf(teks, hasil, asli, judul)
        #  ③ tempel watermark → SATU berkas hasil
        tempel_watermark(asli, keluar)

    import fitz
    d = fitz.open(keluar)
    jml_hal = d.page_count
    d.close()

    return {
        'pdf': keluar,
        'indeks': hasil.get('similarity_index', 0),
        'jumlah_sumber': len(hasil.get('sources', [])),
        'stabilo': len(hasil.get('matched_sentences', [])),
        'halaman': jml_hal,
    }
