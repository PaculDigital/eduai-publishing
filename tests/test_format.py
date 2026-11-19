"""Cek Format Pedoman: pemeriksa deterministik di standar_penulisan.py (19 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB. Fixture .docx kecil dibuat dengan
python-docx (pola fid 81: penanda telanjang BAB I..V, keterangan Tabel/Gambar,
gambar SPSS sebagai gambar). Satu berkas benar + satu pelanggaran per kasus.
"""
import base64
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import standar_penulisan as SP

# PNG 1x1 transparan (untuk gambar/drawing di fixture).
PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')

ISI_PANJANG = ('Paragraf isi yang cukup panjang supaya masuk ambang paragraf isi, '
               'lebih dari delapan puluh karakter, dan membahas variabel penelitian.')


def cek(nama, benar):
    print(("  LULUS  " if benar else "  GAGAL  ") + nama)
    return benar


def _png_jalur(tmp):
    p = tmp / 'titik.png'
    p.write_bytes(PNG_1X1)
    return str(p)


def _atur_pgnum(section, fmt):
    """Set format nomor halaman seksi (lowerRoman/decimal) lewat XML.

    Ganti yang sudah ada (bukan tambah) — satu sectPr hanya boleh punya
    satu pgNumType; add_section() menyalin pgNumType seksi sebelumnya.
    """
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    sectPr = section._sectPr
    for lama in sectPr.findall(qn('w:pgNumType')):
        sectPr.remove(lama)
    el = OxmlElement('w:pgNumType')
    el.set(qn('w:fmt'), fmt)
    sectPr.append(el)


def _atur_default_dokumen(doc, huruf='Times New Roman', ukuran_pt=12.0):
    """Set default dokumen (docDefaults): huruf + ukuran (pola fid 81)."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    styles_el = doc.styles.element
    defaults = styles_el.find(qn('w:docDefaults'))
    if defaults is None:
        defaults = OxmlElement('w:docDefaults')
        styles_el.insert(0, defaults)
    rpr_default = defaults.find(qn('w:rPrDefault'))
    if rpr_default is None:
        rpr_default = OxmlElement('w:rPrDefault')
        defaults.append(rpr_default)
    rpr = rpr_default.find(qn('w:rPr'))
    if rpr is None:
        rpr = OxmlElement('w:rPr')
        rpr_default.append(rpr)
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        rpr.append(fonts)
    fonts.set(qn('w:ascii'), huruf)
    fonts.set(qn('w:hAnsi'), huruf)
    sz = rpr.find(qn('w:sz'))
    if sz is None:
        sz = OxmlElement('w:sz')
        rpr.append(sz)
    sz.set(qn('w:val'), str(int(ukuran_pt * 2)))


def _isi(doc, teks, spasi=1.5, rata='JUSTIFY', tebal=False):
    """Satu paragraf isi (Normal, panjang, spasi + rata diatur)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph(style='Normal')
    r = p.add_run(teks)
    r.bold = tebal
    p.paragraph_format.line_spacing = spasi
    p.paragraph_format.alignment = getattr(WD_ALIGN_PARAGRAPH, rata)
    return p


def _bab(doc, nomor):
    """Judul bab telanjang (Heading 1, tengah, tebal dari gaya)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    gaya = doc.styles['Heading 1']
    gaya.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    gaya.font.bold = True
    p = doc.add_paragraph(style='Heading 1')
    p.add_run(f'BAB {nomor}')
    return p


def _keterangan_tabel(doc, nomor, judul, rata='LEFT', tebal=False):
    """Keterangan tabel (DI ATAS tabel)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph()
    r = p.add_run(f'Tabel {nomor} {judul}')
    r.bold = tebal
    p.paragraph_format.alignment = getattr(WD_ALIGN_PARAGRAPH, rata)
    return p


def _keterangan_gambar(doc, nomor, judul, rata='CENTER', tebal=False):
    """Keterangan gambar (DI BAWAH gambar)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph()
    r = p.add_run(f'Gambar {nomor} {judul}')
    r.bold = tebal
    p.paragraph_format.alignment = getattr(WD_ALIGN_PARAGRAPH, rata)
    return p


def docx_benar(tmp, png):
    """Docx yang formatnya benar semua (8/8 lulus)."""
    from docx import Document
    from docx.shared import Cm
    doc = Document()
    _atur_default_dokumen(doc)
    s0 = doc.sections[0]
    s0.top_margin = Cm(4)
    s0.bottom_margin = Cm(3)
    s0.left_margin = Cm(4)
    s0.right_margin = Cm(3)
    _atur_pgnum(s0, 'lowerRoman')
    _isi(doc, 'Kata pengantar isi naskah yang cukup panjang supaya masuk ambang paragraf isi dan dibaca.')
    _bab(doc, 'I')
    _isi(doc, ISI_PANJANG + ' Bab satu membahas latar belakang masalah penelitian ini.')
    _isi(doc, ISI_PANJANG + ' Bab satu juga merumuskan masalah dan tujuan penelitian ini.')
    _keterangan_tabel(doc, '1.1', 'Gap research')
    doc.add_table(rows=2, cols=2)
    _isi(doc, ISI_PANJANG + ' Pembahasan hasil tabel di atas menunjukkan kesenjangan penelitian.')
    doc.add_picture(png, width=Cm(5))
    _keterangan_gambar(doc, '1.1', 'Perkembangan UMKM')
    _isi(doc, ISI_PANJANG + ' Gambar di atas menunjukkan perkembangan UMKM di Kabupaten Bekasi.')
    _bab(doc, 'II')
    _isi(doc, ISI_PANJANG + ' Bab dua membahas tinjauan pustaka dan hipotesis penelitian.')
    s1 = doc.add_section()
    s1.top_margin = Cm(4)
    s1.bottom_margin = Cm(3)
    s1.left_margin = Cm(4)
    s1.right_margin = Cm(3)
    _atur_pgnum(s1, 'decimal')
    p = doc.add_paragraph(style='Heading 1')
    p.add_run('DAFTAR PUSTAKA')
    jalur = tmp / 'benar.docx'
    doc.save(str(jalur))
    return jalur


def docx_ubah(tmp, png, ubah):
    """Docx benar lalu diubah satu hal (nama ubah -> fungsi)."""
    from docx import Document
    from docx.shared import Cm
    jalur = docx_benar(tmp, png)
    doc = Document(str(jalur))
    ubah(doc, tmp, png)
    jalur2 = tmp / 'ubah.docx'
    doc.save(str(jalur2))
    return jalur2


def _vonis(hasil, cek_id):
    for t in hasil['temuan']:
        if t['id'] == cek_id:
            return t['vonis']
    return None


def _alasan(hasil, cek_id):
    for t in hasil['temuan']:
        if t['id'] == cek_id:
            return t['alasan']
    return ''


def main():
    lulus = 0
    total = 0

    def t(nama, benar):
        nonlocal lulus, total
        total += 1
        if cek(nama, benar):
            lulus += 1

    tmp = Path(tempfile.mkdtemp())
    png = _png_jalur(tmp)

    # --- Berkas benar: 8/8 lulus ---
    h = SP.periksa_format(docx_benar(tmp, png))
    t('benar: 8 temuan', len(h['temuan']) == 8)
    t('benar: ringkasan 8 lulus',
      h['ringkasan'] == {'lulus': 8, 'tidak': 0, 'ragu': 0})
    t('benar: sidik berkas terisi', bool(h.get('sidik_berkas')))
    t('benar: langkah berikut = semua sesuai',
      h['langkah_berikut'] == 'Semua format sudah sesuai pedoman.')
    t('benar: tidak ada kata salah di alasan',
      all('salah' not in (x['alasan'] or '').lower()
          for x in h['temuan']))

    # --- Margin salah (atas 2 cm) ---
    def ubah_margin(doc, tmp, png):
        from docx.shared import Cm
        doc.sections[0].top_margin = Cm(2)
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_margin))
    t('margin salah: vonis tidak', _vonis(h, 'margin') == 'tidak')
    t('margin salah: alasan menyebut 2 cm dan 4 cm',
      '2' in _alasan(h, 'margin') and '4' in _alasan(h, 'margin'))

    # --- Huruf salah (Arial 11) ---
    def ubah_huruf(doc, tmp, png):
        _atur_default_dokumen(doc, huruf='Arial', ukuran_pt=11.0)
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_huruf))
    t('huruf salah: vonis tidak', _vonis(h, 'huruf') == 'tidak')
    t('huruf salah: alasan menyebut Arial',
      'arial' in _alasan(h, 'huruf').lower())

    # --- Spasi salah (1,0) ---
    def ubah_spasi(doc, tmp, png):
        for p in doc.paragraphs:
            if p.style.name == 'Normal' and len((p.text or '')) >= 80:
                p.paragraph_format.line_spacing = 1.0
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_spasi))
    t('spasi salah: vonis tidak', _vonis(h, 'spasi') == 'tidak')

    # --- Perataan salah (rata kiri) ---
    def ubah_rata(doc, tmp, png):
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        for p in doc.paragraphs:
            if p.style.name == 'Normal' and len((p.text or '')) >= 80:
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_rata))
    t('perataan salah: vonis tidak', _vonis(h, 'perataan') == 'tidak')

    # --- Judul bab tidak tengah ---
    def ubah_judul(doc, tmp, png):
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        doc.styles['Heading 1'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for p in doc.paragraphs:
            if p.style.name == 'Heading 1':
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_judul))
    t('judul bab rata kiri: vonis tidak', _vonis(h, 'judul_bab') == 'tidak')
    t('judul bab rata kiri: alasan menyebut Bab I',
      'Bab I' in _alasan(h, 'judul_bab'))

    # --- Keterangan tabel rata tengah (bukan kiri) ---
    def ubah_ket_tabel(doc, tmp, png):
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        for p in doc.paragraphs:
            if (p.text or '').startswith('Tabel '):
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_ket_tabel))
    t('keterangan tabel tengah: vonis tidak', _vonis(h, 'tabel') == 'tidak')
    t('keterangan tabel tengah: alasan menyebut Tabel 1.1',
      'Tabel 1.1' in _alasan(h, 'tabel'))

    # --- Keterangan gambar rata kiri (bukan tengah) ---
    def ubah_ket_gambar(doc, tmp, png):
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        for p in doc.paragraphs:
            if (p.text or '').startswith('Gambar '):
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_ket_gambar))
    t('keterangan gambar kiri: vonis tidak', _vonis(h, 'gambar') == 'tidak')
    t('keterangan gambar kiri: alasan menyebut Gambar 1.1',
      'Gambar 1.1' in _alasan(h, 'gambar'))

    # --- Nomor halaman: semua desimal (bagian awal bukan romawi) ---
    def ubah_pgnum(doc, tmp, png):
        _atur_pgnum(doc.sections[0], 'decimal')
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_pgnum))
    t('nomor halaman desimal semua: vonis tidak',
      _vonis(h, 'nomor_halaman') == 'tidak')

    # --- Kalimat rujukan bukan keterangan (pola fid 81) ---
    def ubah_rujukan(doc, tmp, png):
        p = doc.add_paragraph()
        p.add_run('Tabel 1.1 menunjukkan bahwa seluruh item pernyataan valid.')
    h = SP.periksa_format(docx_ubah(tmp, png, ubah_rujukan))
    t('rujukan Tabel 1.1 menunjukkan: tabel tetap lulus',
      _vonis(h, 'tabel') == 'lulus')

    # --- Gambar SPSS sebagai tabel (pola fid 81) ---
    from docx import Document
    from docx.shared import Cm
    doc = Document()
    _atur_default_dokumen(doc)
    s0 = doc.sections[0]
    s0.top_margin = Cm(4)
    s0.bottom_margin = Cm(3)
    s0.left_margin = Cm(4)
    s0.right_margin = Cm(3)
    _atur_pgnum(s0, 'lowerRoman')
    _bab(doc, 'I')
    _isi(doc, ISI_PANJANG + ' Bab satu membahas latar belakang masalah penelitian ini.')
    _keterangan_tabel(doc, '4.1', 'Hasil Uji Validitas')
    doc.add_picture(png, width=Cm(5))
    _isi(doc, 'Sumber: Data diolah penulis, 2026')
    _isi(doc, ISI_PANJANG + ' Tabel 4.1 menunjukkan bahwa seluruh item valid.')
    _bab(doc, 'II')
    _isi(doc, ISI_PANJANG + ' Bab dua membahas tinjauan pustaka penelitian ini.')
    s1 = doc.add_section()
    s1.top_margin = Cm(4)
    s1.bottom_margin = Cm(3)
    s1.left_margin = Cm(4)
    s1.right_margin = Cm(3)
    _atur_pgnum(s1, 'decimal')
    p = doc.add_paragraph(style='Heading 1')
    p.add_run('DAFTAR PUSTAKA')
    jalur = tmp / 'spss.docx'
    doc.save(str(jalur))
    h = SP.periksa_format(jalur)
    t('gambar SPSS sebagai tabel: tabel lulus', _vonis(h, 'tabel') == 'lulus')
    t('gambar SPSS sebagai tabel: gambar lulus (tidak ada gambar isi)',
      _vonis(h, 'gambar') == 'lulus')

    # --- Aturan lama tidak berubah (ringkas_untuk_ai + baca_panduan) ---
    t('aturan lama: ringkas_untuk_ai masih ada',
      'Times New Roman' in SP.ringkas_untuk_ai(None) or
      'TNR' in SP.ringkas_untuk_ai(None))
    t('aturan lama: ATURAN_BAKU margin 4/3/4/3',
      SP.ATURAN_BAKU['margin_cm'] == {'atas': 4, 'bawah': 3, 'kiri': 4, 'kanan': 3})

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    raise SystemExit(main())
