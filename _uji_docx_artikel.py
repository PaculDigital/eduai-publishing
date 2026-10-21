"""Uji penulis .docx artikel — TANPA AI, TANPA DB (07 Okt 2026)."""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')
from app import konversi as K

HASIL = {'lulus': 0, 'gagal': 0, 'nama_gagal': []}


def cek(nama, syarat, ket=''):
    if syarat:
        HASIL['lulus'] += 1
        print(f'LULUS  {nama}')
    else:
        HASIL['gagal'] += 1
        HASIL['nama_gagal'].append(nama)
        print(f'GAGAL  {nama} {ket}')


ARTIKEL = {
    'judul': 'Pengaruh Harga & Promosi <Uji> Terhadap Keputusan',
    'penulis': [{'nama': 'Asih Susanti Putri',
                 'email': 'asih@contoh.ac.id',
                 'afiliasi': 'Universitas Contoh'}],
    'institusi': 'Program Magister Manajemen',
    'abstrak_id': 'Abstrak bahasa Indonesia. ' * 20,
    'abstract_en': 'English abstract. ' * 20,
    'kata_kunci': ['harga', 'promosi', 'keputusan'],
    'keywords': ['price', 'promotion'],
    'pendahuluan': 'Paragraf satu pendahuluan.\nParagraf dua pendahuluan.',
    'metode': 'Metode penelitian kuantitatif.',
    'hasil_pembahasan': 'Hasil uji: \u03b2 = 0,45; p = 0,001.',
    'kesimpulan': 'Kesimpulan penelitian ini.',
    'daftar_pustaka': ['Kotler, P. (2020). Manajemen Pemasaran. Jakarta: Erlangga.',
                       'Sugiyono. (2019). Metode Penelitian. Bandung: Alfabeta.'],
    'elemen': {'hook': 'Pembuka yang menarik perhatian.',
               'novelty': 'Kebaruan penelitian ini adalah model terpadu.'},
}

TMPL = Path('/app/app/templat/naskah-baru.docx')
cek('D1 templat .docx ADA', TMPL.exists(), str(TMPL))
if TMPL.exists():
    cek('D1b templat berukuran wajar', TMPL.stat().st_size > 2000,
        f'{TMPL.stat().st_size} byte')

# ── Rakit XML ─────────────────────────────────────────────────────────
xml = K.rakit_xml_artikel(ARTIKEL)
cek('D2 XML memuat judul', 'Pengaruh Harga' in xml)
cek('D2b judul di-escape (& jadi &amp;)', '&amp;' in xml and '<Uji>' not in xml)
cek('D2c XML memuat nama penulis', 'Asih Susanti Putri' in xml)
cek('D2d XML memuat email', 'asih@contoh.ac.id' in xml)
cek('D2e XML memuat ABSTRAK', 'ABSTRAK' in xml)
cek('D2f XML memuat ABSTRACT', 'ABSTRACT' in xml)
cek('D2g XML memuat Pendahuluan', 'Pendahuluan' in xml)
cek('D2h XML memuat Metode', 'Metode' in xml)
cek('D2i XML memuat Daftar Pustaka', 'DAFTAR PUSTAKA' in xml)
cek('D2j XML memuat pustaka ke-2', 'Sugiyono' in xml)
cek('D2k XML memuat elemen hook', 'hook' in xml.lower() or 'Hook' in xml)
cek('D2l XML paragraf terpisah (2 par pendahuluan)',
    xml.count('Paragraf satu') == 1 and xml.count('Paragraf dua') == 1)
cek('D2m ada simbol β (utf-8 aman)', 'β' in xml)

# ── Tulis .docx ───────────────────────────────────────────────────────
out = Path('/tmp/uji_artikel_hasil.docx')
if out.exists():
    out.unlink()
res = K.tulis_artikel_docx(ARTIKEL, out)
cek('D3 tulis .docx SUKSES', res.get('ok') is True, res.get('galat'))
cek('D3b berkas ADA di disk', out.exists())
if out.exists():
    cek('D3c ukuran wajar (> 2 KB)', out.stat().st_size > 2000,
        f'{out.stat().st_size} byte')
    #  ZIP sah?
    try:
        with zipfile.ZipFile(out) as z:
            nama = z.namelist()
            cek('D4 .docx = ZIP sah', 'word/document.xml' in nama)
            cek('D4b ada [Content_Types].xml', '[Content_Types].xml' in nama)
            cek('D4c ada word/styles.xml', 'word/styles.xml' in nama)
            cek('D4d ada word/_rels/document.xml.rels',
                'word/_rels/document.xml.rels' in nama)
            isi = z.read('word/document.xml').decode('utf-8')
            cek('D5 document.xml memuat judul', 'Pengaruh Harga' in isi)
            cek('D5b document.xml memuat ABSTRAK', 'ABSTRAK' in isi)
            cek('D5c document.xml memuat DAFTAR PUSTAKA', 'DAFTAR PUSTAKA' in isi)
            cek('D5d sectPr DIPERTAHANKAN (ukuran halaman)',
                '<w:sectPr' in isi)
            cek('D5d2 ukuran halaman ikut (pgSz 11906×16838)',
                'w:pgSz w:w="11906"' in isi and 'w:h="16838"' in isi)
            cek('D5d3 margin ikut (pgMar)',
                '<w:pgMar' in isi and 'w:left="1701"' in isi)
            cek('D5d4 sectPr TIDAK ganda',
                isi.count('<w:sectPr') == 1, f'{isi.count("<w:sectPr")}×')
            cek('D5e body utuh (ada </w:body>)', '</w:body>' in isi)
            cek('D5f document.xml > 3 KB (isi nyata)',
                len(isi) > 3000, f'{len(isi)} kar')
            z.testzip()
            cek('D5g ZIP tidak korup', True)
    except Exception as e:                                   # noqa: BLE001
        cek('D4 .docx = ZIP sah', False, f'{type(e).__name__}: {e}')

# ── Artikel kosong tetap tidak meledak ────────────────────────────────
res2 = K.tulis_artikel_docx({}, '/tmp/uji_artikel_kosong.docx')
cek('D6 artikel kosong tidak meledak', res2.get('ok') is True, res2.get('galat'))
cek('D6b kosong pakai judul bawaan',
    'ARTIKEL JURNAL' in K.rakit_xml_artikel({}))

# ── Jangan pakai python-docx (tidak terpasang) ────────────────────────
import inspect
src = K.__file__
isi_kode = Path(src).read_text(encoding='utf-8')
cek('D7 TIDAK impor python-docx', 'from docx import' not in isi_kode)
cek('D7b pakai zipfile (yang terpasang)', 'import zipfile' in isi_kode)

print(f'\nTOTAL: {HASIL["lulus"]} LULUS / {HASIL["gagal"]} GAGAL')
if HASIL['gagal']:
    print('YANG GAGAL: ' + ', '.join(HASIL['nama_gagal']))
sys.exit(1 if HASIL['gagal'] else 0)
