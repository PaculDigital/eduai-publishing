"""TAMBAH fungsi `sisip_gambar_setelah_bagian()` ke AKHIR app/gambar.py.

🔴 MENGAPA (permintaan Bos "A" 26Sep26):
   Gambar sekarang selalu ditaruh SEBELUM </w:body> = AKHIR dokumen.
   Mahasiswa harus menggulung ke ujung naskah untuk melihatnya.
   ⇒ WAJIB ditaruh TEPAT di akhir bagian yang direvisi (mis. setelah
     paragraf terakhir sub-bab 2.3, sebelum judul 2.4).

CARA KERJA (dari bentuk nyata .docx 822 paragraf):
   1. Cari paragraf yang TEKSNYA cocok judul bagian target ("2.3 ...").
   2. Cari paragraf judul bagian BERIKUTNYA ("2.4 ...").
   3. Sisipkan gambar + keterangan TEPAT SEBELUM judul berikutnya.
   4. Kalau tidak ketemu → JANGAN mengarang: kembalikan ok=False supaya
      pemanggil pakai cara lama (akhir dokumen).
"""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/gambar.py')
s = P.read_text()

assert 'def sisip_gambar_setelah_bagian' not in s, 'fungsi sudah ada'

FUNGSI = '''

#  ══════════════════════════════════════════════════════════════════════════
#  SISIP GAMBAR DI POSISI BAGIAN (26Sep26, permintaan Bos)
#  Gambar ditaruh TEPAT setelah bagian yang direvisi, BUKAN di akhir dokumen.
#  ══════════════════════════════════════════════════════════════════════════
_RE_P = re.compile(r'<w:p\\b.*?</w:p>|<w:p\\b[^>]*/>', re.S)
_RE_T = re.compile(r'<w:t[^>]*>([^<]*)</w:t>')


def _teks_par(p: str) -> str:
    """Ambil teks sebuah <w:p> (tanpa tag)."""
    return ''.join(_RE_T.findall(p)).strip()


def _cocok_judul(teks: str, bagian: str) -> bool:
    """True kalau teks paragraf ini JUDUL bagian yang dimaksud.

    Bentuk yang diterima: "2.3 Judul", "2.3.  Judul", "2.3  Judul".
    DILARANG cocok dengan "2.30 ..." (bagian lain yang kebetulan berawalan).
    """
    b = str(bagian).strip()
    if not b or not teks:
        return False
    t = teks.strip()
    if not t.startswith(b):
        return False
    sisa = t[len(b):]
    #  setelah nomor HARUS titik/spasi (bukan angka lain)
    if not sisa or (sisa[0] not in '. \\t'):
        return False
    sisa = sisa.lstrip('. \\t')
    #  judul tidak boleh kepanjangan (itu paragraf isi, bukan judul)
    return 0 < len(sisa) <= 120


def sisip_gambar_setelah_bagian(docx_path, png: bytes, bagian: str,
                                bagian_berikut: str = '',
                                keterangan: str = '') -> dict:
    """Sisipkan gambar TEPAT di akhir bagian `bagian` (sebelum bagian berikutnya).

    Kalau tidak bisa dipastikan posisinya → ok=False (jangan menebak;
    pemanggil boleh pakai sisip_gambar_docx() = akhir dokumen).
    """
    docx_path = Path(docx_path)
    if not png:
        return {'ok': False, 'sebab': 'gambar kosong'}
    if not docx_path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada'}

    with zipfile.ZipFile(docx_path) as z:
        nama = set(z.namelist())
        doc = z.read('word/document.xml').decode('utf-8')
        tipe = z.read('[Content_Types].xml').decode('utf-8')
        rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
        isi_lain = {n: z.read(n) for n in nama
                    if n not in ('word/document.xml', '[Content_Types].xml',
                                 'word/_rels/document.xml.rels')}

    par_list = [m.group(0) for m in _RE_P.finditer(doc)]
    if not par_list:
        return {'ok': False, 'sebab': 'paragraf tidak terbaca'}

    #  ── 1. cari paragraf judul bagian target ──
    idx_target = None
    for i, p in enumerate(par_list):
        if _cocok_judul(_teks_par(p), bagian):
            idx_target = i
            break
    if idx_target is None:
        return {'ok': False, 'sebab': f'judul bagian {bagian!r} tidak ditemukan'}

    #  ── 2. cari paragraf judul bagian BERIKUTNYA (batas akhir bagian) ──
    idx_akhir = None
    if bagian_berikut:
        for i in range(idx_target + 1, len(par_list)):
            if _cocok_judul(_teks_par(par_list[i]), bagian_berikut):
                idx_akhir = i
                break
    #  kalau bagian berikut tidak diketahui/ditemukan → pakai paragraf isi
    #  terakhir sebelum paragraf yang SEOLAH judul (pola "N.N Judul")
    if idx_akhir is None:
        for i in range(idx_target + 1, len(par_list)):
            t = _teks_par(par_list[i])
            if re.match(r'^\\d+\\.\\d+\\s+\\S', t) and len(t) < 90:
                idx_akhir = i
                break
    if idx_akhir is None:
        idx_akhir = len(par_list)          # taruh sebelum akhir badan

    #  ── 3. bangun paragraf gambar + keterangan (pola sama dgn fungsi lama) ──
    idx_media = 1
    while f'word/media/grafik_ai{idx_media if idx_media > 1 else ""}.png' in nama:
        idx_media += 1
    nama_media = ('word/media/grafik_ai.png' if idx_media == 1
                  else f'word/media/grafik_ai{idx_media}.png')

    dipakai = [int(m) for m in re.findall(r'Id="rId(\\d+)"', rels)]
    rid = f'rId{max(dipakai) + 1 if dipakai else 1}'

    m_tag = re.search(r'<w:document(?:\\s+[\\w:.-]+\\s*=\\s*"[^"]*")*\\s*/?>', doc)
    if not m_tag:
        return {'ok': False, 'sebab': 'tag <w:document> tidak terbaca'}
    tag = m_tag.group(0)
    ada = dict(re.findall(r'xmlns:([\\w.-]+)\\s*=\\s*"([^"]*)"', tag))
    tambah = []
    if 'wp' not in ada:
        tambah.append(f'xmlns:wp="{_NS_WP}"')
    if 'a' not in ada:
        tambah.append(f'xmlns:a="{_NS_A}"')
    if 'pic' not in ada:
        tambah.append(f'xmlns:pic="{_NS_PIC}"')
    if tambah:
        tag_baru = tag[:-1] + ' ' + ' '.join(tambah) + ('/>' if tag.endswith('/>')
                                                        else '>')
        doc = doc.replace(tag, tag_baru, 1)

    cx, cy = 5_486_400, 3_200_400
    pid = 900_000 + idx_media
    par = (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pid}" name="Grafik{idx_media}"/>'
        '<a:graphic><a:graphicData '
        f'uri="{_NS_PIC}"><pic:pic>'
        f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="{nama_media}"/>'
        '<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
        '<a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing></w:r></w:p>'
    )
    par_cap = ''
    if keterangan:
        par_cap = (
            '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
            '<w:r><w:rPr><w:i/><w:sz w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{keterangan}</w:t></w:r></w:p>'
        )

    #  ── 4. tulis ulang doc: sisipkan SEBELUM paragraf judul berikutnya ──
    par_akhir = par_list[idx_akhir]
    pos = doc.find(par_akhir, doc.find(par_list[idx_target]))
    if pos < 0:
        pos = doc.find(par_akhir)
    if pos < 0:
        return {'ok': False, 'sebab': 'titik sisip tidak ditemukan'}
    doc = doc[:pos] + par + par_cap + doc[pos:]

    #  ── 5. content-types + rels ──
    if 'png' not in tipe:
        tipe = tipe.replace(
            '</Types>',
            '<Default Extension="png" ContentType="image/png"/></Types>')
    rels = rels.replace(
        '</Relationships>',
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/relationships/image" Target="media/'
        f'{nama_media.split("/")[-1]}"/></Relationships>')

    tmp = docx_path.with_suffix('.tmp.docx')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', tipe)
        z.writestr('word/document.xml', doc)
        z.writestr('word/_rels/document.xml.rels', rels)
        z.writestr(nama_media, png)
        for n, b in isi_lain.items():
            if n == '[Content_Types].xml':
                continue
            z.writestr(n, b)
    shutil.move(str(tmp), str(docx_path))

    return {'ok': True, 'ukuran': len(png), 'media': nama_media, 'rid': rid,
            'paragraf_judul': idx_target, 'paragraf_akhir_bagian': idx_akhir}
'''

s = s.rstrip('\n') + '\n' + FUNGSI
P.write_text(s)
print('✅ fungsi sisip_gambar_setelah_bagian() ditambahkan di AKHIR gambar.py')
print(f'   panjang berkas: {len(s):,} byte')
