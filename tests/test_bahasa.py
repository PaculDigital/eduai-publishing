"""Cek Bahasa Pedoman: pemeriksa deterministik di standar_penulisan.py (20 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB. Fixture .docx kecil dibuat dengan
python-docx (pola fid 81: penanda telanjang BAB I..II, paragraf isi panjang).
Satu berkas benar + satu pelanggaran per kasus.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import standar_penulisan as SP

# Paragraf isi yang benar semua: tiap kalimat memakai kata pasif (di-/ter-),
# tanpa saya/dimana/di- menempel/desimal titik/sehingga di awal kalimat.
ISI_PASIF_1 = ('Variabel penelitian ini dianalisis dengan metode kuantitatif '
               'yang dilakukan secara sistematis dan terencana oleh peneliti.')
ISI_PASIF_2 = ('Data yang dikumpulkan dari responden diolah menggunakan '
               'perangkat lunak statistik yang dipilih secara cermat dan teliti.')
ISI_PASIF_3 = ('Hasil penelitian ini disajikan dalam bentuk tabel dan gambar '
               'yang disusun berdasarkan urutan variabel yang diteliti.')


def cek(nama, benar):
    print(("  LULUS  " if benar else "  GAGAL  ") + nama)
    return benar


def _bab(doc, nomor):
    """Judul bab telanjang (Heading 1, tengah, tebal dari gaya)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    gaya = doc.styles['Heading 1']
    gaya.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    gaya.font.bold = True
    p = doc.add_paragraph(style='Heading 1')
    p.add_run(f'BAB {nomor}')
    return p


def _isi(doc, teks):
    """Satu paragraf isi (Normal, panjang >= 80 karakter)."""
    p = doc.add_paragraph(style='Normal')
    p.add_run(teks)
    return p


def docx_benar(tmp):
    """Docx yang bahasanya benar semua (6/6 lulus)."""
    from docx import Document
    doc = Document()
    _isi(doc, 'Kata pengantar isi naskah yang cukup panjang supaya masuk ambang '
              'paragraf isi dan dibaca sebagai bagian awal naskah skripsi ini.')
    _bab(doc, 'I')
    _isi(doc, ISI_PASIF_1)
    _isi(doc, ISI_PASIF_2)
    _bab(doc, 'II')
    _isi(doc, ISI_PASIF_3)
    p = doc.add_paragraph(style='Heading 1')
    p.add_run('DAFTAR PUSTAKA')
    jalur = tmp / 'benar.docx'
    doc.save(str(jalur))
    return jalur


def docx_ubah(tmp, ubah):
    """Docx benar lalu diubah satu hal (nama ubah -> fungsi)."""
    from docx import Document
    jalur = docx_benar(tmp)
    doc = Document(str(jalur))
    ubah(doc)
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


def _paragraf_isi(doc):
    """Paragraf isi (Normal, panjang >= 80) di antara BAB I dan pustaka.

    Kata pengantar (sebelum BAB I) TIDAK termasuk, karena pemeriksa hanya
    menilai isi (pola _teks_isi_bahasa di standar_penulisan.py).
    """
    paras = list(doc.paragraphs)
    awal = 0
    akhir = len(paras)
    for i, p in enumerate(paras):
        if (p.style.name == 'Heading 1'
                and (p.text or '').strip().upper().startswith('BAB ')):
            awal = i + 1
            break
    for i in range(awal, len(paras)):
        if (paras[i].style.name == 'Heading 1'
                and (paras[i].text or '').strip().upper()
                == 'DAFTAR PUSTAKA'):
            akhir = i
            break
    return [p for p in paras[awal:akhir]
            if p.style.name == 'Normal' and len((p.text or '')) >= 80]


def main():
    lulus = 0
    total = 0

    def t(nama, benar):
        nonlocal lulus, total
        total += 1
        if cek(nama, benar):
            lulus += 1

    tmp = Path(tempfile.mkdtemp())

    # --- Berkas benar: 6/6 lulus ---
    h = SP.periksa_bahasa(docx_benar(tmp))
    t('benar: 6 temuan', len(h['temuan']) == 6)
    t('benar: ringkasan 6 lulus',
      h['ringkasan'] == {'lulus': 6, 'tidak': 0, 'ragu': 0})
    t('benar: sidik berkas terisi', bool(h.get('sidik_berkas')))
    t('benar: langkah berikut = semua sesuai',
      h['langkah_berikut'] == 'Semua bahasa sudah sesuai pedoman.')
    t('benar: tidak ada kata salah di alasan',
      all('salah' not in (x['alasan'] or '').lower()
          for x in h['temuan']))

    # --- Kata 'Kita' di isi ---
    def ubah_saya(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = p.text + ' Kita sepakat bahwa hasil ini penting.'
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_saya))
    t('saya: vonis tidak', _vonis(h, 'saya') == 'tidak')
    t('saya: alasan menyebut jumlah dan contoh',
      '1 kali' in _alasan(h, 'saya') and 'Kita' in _alasan(h, 'saya'))

    # --- 'Sehingga' di awal kalimat ---
    def ubah_hubung(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = p.text + ' Sehingga hasil penelitian ini penting.'
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_hubung))
    t('hubung_awal: vonis tidak', _vonis(h, 'hubung_awal') == 'tidak')

    # --- Kata 'dimana' ---
    def ubah_dimana(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = (p.text + ' Tempat dimana penelitian ini '
                           'dilakukan adalah Kabupaten Bekasi.')
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_dimana))
    t('dimana: vonis tidak', _vonis(h, 'dimana') == 'tidak')
    t('dimana: alasan menyebut contoh',
      'dimana' in _alasan(h, 'dimana'))

    # --- 'diatas' menempel ---
    def ubah_dike(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = (p.text + ' Data diatas menunjukkan peningkatan '
                           'yang diukur secara berkala.')
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_dike))
    t('dike_tempat: vonis tidak', _vonis(h, 'dike_tempat') == 'tidak')
    t('dike_tempat: alasan menyebut contoh',
      'diatas' in _alasan(h, 'dike_tempat'))

    # --- 'di atas' terpisah TIDAK ditandai ---
    def ubah_dipisah(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = (p.text + ' Data di atas menunjukkan peningkatan '
                           'yang diukur secara berkala.')
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_dipisah))
    t('di atas terpisah: dike_tempat lulus',
      _vonis(h, 'dike_tempat') == 'lulus')

    # --- Desimal pakai titik (50.5) ---
    def ubah_desimal(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = p.text + ' Nilai rata-rata yang diperoleh adalah 50.5.'
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_desimal))
    t('desimal: vonis tidak', _vonis(h, 'desimal') == 'tidak')
    t('desimal: alasan menyebut koma',
      'koma' in _alasan(h, 'desimal'))

    # --- Pemisah ribuan (293.753) TIDAK ditandai ---
    def ubah_ribuan(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = (p.text + ' Jumlah usaha yang tercatat adalah '
                           '293.753 unit di seluruh wilayah.')
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_ribuan))
    t('ribuan 293.753: desimal lulus', _vonis(h, 'desimal') == 'lulus')

    # --- Rujukan 'Tabel 4.1' TIDAK ditandai sebagai desimal ---
    def ubah_rujukan(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = (p.text + ' Hasil pada Tabel 4.1 menunjukkan '
                           'peningkatan yang diukur secara berkala.')
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_rujukan))
    t('Tabel 4.1: desimal lulus', _vonis(h, 'desimal') == 'lulus')

    # --- Kalimat aktif: vonis ragu, TIDAK PERNAH tidak ---
    def ubah_aktif(doc):
        p = _paragraf_isi(doc)[0]
        p.runs[0].text = ('Penelitian ini menunjukkan bahwa UMKM kuliner '
                          'ayam bakar memiliki peran penting dalam '
                          'perekonomian daerah dan membuka lapangan kerja.')
    h = SP.periksa_bahasa(docx_ubah(tmp, ubah_aktif))
    t('aktif: vonis ragu (bukan tidak)', _vonis(h, 'aktif') == 'ragu')
    t('aktif: alasan menyebut "perlu diperiksa"',
      'perlu diperiksa' in _alasan(h, 'aktif').lower())
    t('aktif: alasan menyebut contoh pola aktif',
      'menunjukkan' in _alasan(h, 'aktif'))

    # --- Aturan lama tidak berubah ---
    t('aturan lama: ringkas_untuk_ai masih ada',
      callable(getattr(SP, 'ringkas_untuk_ai', None)))
    t('aturan lama: ATURAN_BAKU bahasa masih ada',
      'pasif' in (SP.ATURAN_BAKU.get('bahasa') or {}))
    t('aturan lama: periksa_format masih ada',
      callable(getattr(SP, 'periksa_format', None)))

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    sys.exit(main())
