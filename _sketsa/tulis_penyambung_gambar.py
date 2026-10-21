#!/usr/bin/env python3
"""TAMBAH: penangkap [DATA-GRAFIK] + penyisip gambar ke .docx.

DITARUH DI AKHIR app/gambar.py (jangan menyentuh kode lama).
Fungsi:
  · tangkap_data_grafik(jawaban) → list blok {'jenis','judul','satuan','data'}
  · buang_blok_grafik(jawaban)  → jawaban tanpa blok [DATA-GRAFIK]
  · sisip_gambar_docx(path, png, keterangan) → tulis ulang .docx + PNG
"""
from pathlib import Path

p = Path('/opt/data/services/eduai-publishing/app/gambar.py')
s = p.read_text(encoding='utf-8')
assert 'def tangkap_data_grafik' not in s, 'sudah ada — batalkan'

TAMBAHAN = '''

#  ══ PENANGKAP [DATA-GRAFIK] (25Sep26, ACC Bos "C") ════════════════════════
#  ALUR: AI mengeluarkan DATA (bukan gambar) → modul ini MENANGKAP → gambar
#  → sisip ke .docx. AI TIDAK PERNAH menggambar sendiri.
#  Blok mesin [DATA-GRAFIK]…[/DATA-GRAFIK] WAJIB DIBUANG dari teks naskah
#  sebelum disimpan (bahasa mesin, tidak boleh terlihat mahasiswa).

_RE_BLOK_GRAFIK = re.compile(
    r'\\[\\s*DATA-GRAFIK\\s*\\]\\s*(\\{.*?\\})\\s*\\[\\s*/\\s*DATA-GRAFIK\\s*\\]',
    re.I | re.DOTALL)


def tangkap_data_grafik(jawaban: str) -> list[dict[str, Any]]:
    """Ambil semua blok [DATA-GRAFIK] dari jawaban AI.

    Return [{'jenis','judul','satuan','data'}, …]
    Blok yang JSON-nya rusak DILEWATI (jangan menebak isinya).
    """
    import json
    hasil = []
    for m in _RE_BLOK_GRAFIK.finditer(jawaban or ''):
        mentah = m.group(1)
        try:
            d = json.loads(mentah)
        except Exception:                                     # noqa: BLE001
            log.warning('[gambar] JSON grafik rusak → dilewati (%d kar)',
                        len(mentah))
            continue
        if not isinstance(d, dict):
            continue
        seri = normalisasi_data(d.get('data'))
        if not seri:
            log.warning('[gambar] grafik tanpa angka layak → dilewati')
            continue
        jns = str(d.get('jenis') or 'batang').lower().strip()
        if jns not in JENIS:
            jns = 'batang'
        hasil.append({'jenis': jns,
                      'judul': str(d.get('judul') or 'Grafik')[:90],
                      'satuan': str(d.get('satuan') or '')[:8],
                      'data': seri})
    return hasil


def buang_blok_grafik(jawaban: str) -> str:
    """Buang blok [DATA-GRAFIK] dari teks (bahasa mesin).

    Wajib dipanggil SEBELUM menyimpan hasil revisi ke naskah.
    Kalau blok ini lolos, mahasiswa melihat JSON di naskahnya.
    """
    return re.sub(r'\\n{3,}', '\\n\\n',
                  _RE_BLOK_GRAFIK.sub('', jawaban or '')).strip()


#  ══ SISIP GAMBAR KE .DOCX (pola TERBUKTI 25Sep26) ═════════════════════════
#  PELAJARAN dari 3× gagal (jangan diulang):
#   1. [Content_Types].xml ditulis SEKALI saja (kalau dua → ZIP rusak)
#   2. namespace wp/a/pic: BACA dulu yang ADA di dokumen; hanya TAMBAH yang
#      kurang. JANGAN memaku prefix (dokumen asli bisa pakai wp14).
#   3. Baca tag <w:document> dengan regex atribut="…" — JANGAN potong di '>'
#      pertama (ada '>' di dalam URL) → terbaca 0 padahal 17 deklarasi.
_NS_TAMBAH = {
    'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing': 'wp',
    'http://schemas.openxmlformats.org/drawingml/2006/main': 'a',
    'http://schemas.openxmlformats.org/drawingml/2006/picture': 'pic',
}
_RE_TAG_DOC = re.compile(r'<w:document(?:\\s+[\\w:.-]+\\s*=\\s*"[^"]*")*\\s*/?>')


def sisip_gambar_docx(docx_path: str | Path, png: bytes,
                      keterangan: str = '') -> dict[str, Any]:
    """Sisipkan PNG ke AKHIR .docx. Return {'ok':bool,'sebab':str,…}.

    TIDAK mengubah: ukuran font, gaya, tabel, atau isi lama — hanya
    MENAMBAH satu paragraf gambar + (opsional) keterangannya.
    """
    import shutil
    import zipfile

    docx_path = Path(docx_path)
    if not png:
        return {'ok': False, 'sebab': 'gambar kosong'}
    if not docx_path.exists():
        return {'ok': False, 'sebab': f'berkas tidak ada: {docx_path}'}

    #  ── kerja di SALINAN dulu; baru ganti kalau sukses (jangan rusak asli)
    tmp = docx_path.with_suffix('.tmp.docx')
    shutil.copy(docx_path, tmp)
    try:
        with zipfile.ZipFile(tmp) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
            ct = z.read('[Content_Types].xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama
                    if n not in ('word/document.xml',
                                 'word/_rels/document.xml.rels',
                                 '[Content_Types].xml')}

        #  1) namespace: baca yang ADA, tambah yang KURANG
        m_tag = _RE_TAG_DOC.search(doc)
        if not m_tag:
            return {'ok': False, 'sebab': 'tag <w:document> tidak ditemukan'}
        kepala_tag = m_tag.group(0)
        ada = set(re.findall(r'xmlns:\\w+="([^"]+)"', kepala_tag))
        kurang = {}
        for uri, pref in _NS_TAMBAH.items():
            if uri in ada:
                continue
            pakai = pref if f'xmlns:{pref}=' not in kepala_tag else \\
                next(k for k in ('wp2', 'a2', 'pic2', 'a3', 'pic3')
                     if f'xmlns:{k}=' not in kepala_tag)
            kurang[pakai] = uri
        if kurang:
            tambah = ''.join(f' xmlns:{k}="{u}"' for k, u in kurang.items())
            doc = doc.replace(kepala_tag, kepala_tag[:-1] + tambah + '>', 1)

        #  2) ukuran gambar: maksimal selebar halaman A4 dikurangi margin
        EMU = 9525                                    # EMU per piksel
        try:
            from PIL import Image
            px_w, px_h = Image.open(io.BytesIO(png)).size
        except Exception:                                     # noqa: BLE001
            px_w, px_h = 720, 400
        lebar_maks = 6_000_000                        # ±16,5 cm
        cx = min(px_w * EMU, lebar_maks)
        cy = int(cx * px_h / max(px_w, 1))

        no_gbr = len(re.findall(r'<w:drawing>|<w:pict>', doc)) + 1
        rid = f'rIdGbrAi{no_gbr}'
        wp = 'wp' if 'xmlns:wp=' in doc else 'wp14'
        a_pref = next((k for k, u in kurang.items() if 'drawingml/2006/main' in u), 'a')
        pic_pref = next((k for k, u in kurang.items() if 'picture' in u), 'pic')

        gbr = (
            f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<{wp}:inline distT="0" distB="0" distL="0" distR="0">'
            f'<{wp}:extent cx="{cx}" cy="{cy}"/>'
            f'<{wp}:docPr id="{no_gbr}" name="GrafikAi{no_gbr}"/>'
            f'<{a_pref}:graphic><{a_pref}:graphicData '
            f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<{pic_pref}:pic><{pic_pref}:nvPicPr>'
            f'<{pic_pref}:cNvPr id="{no_gbr}" name="grafik_ai.png"/>'
            f'<{pic_pref}:cNvPicPr/></{pic_pref}:nvPicPr>'
            f'<{pic_pref}:blipFill><{a_pref}:blip r:embed="{rid}"/>'
            f'<{a_pref}:stretch><{a_pref}:fillRect/></{a_pref}:stretch>'
            f'</{pic_pref}:blipFill>'
            f'<{pic_pref}:spPr><{a_pref}:xfrm><{a_pref}:off x="0" y="0"/>'
            f'<{a_pref}:ext cx="{cx}" cy="{cy}"/></{a_pref}:xfrm>'
            f'<{a_pref}:prstGeom prst="rect"><{a_pref}:avLst/>'
            f'</{a_pref}:prstGeom></{pic_pref}:spPr>'
            f'</{pic_pref}:pic></{a_pref}:graphicData></{a_pref}:graphic>'
            f'</{wp}:inline></w:drawing></w:r></w:p>')

        if keterangan:
            gbr += (f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
                    f'<w:r><w:t xml:space="preserve">{keterangan}</w:t></w:r>'
                    f'</w:p>')

        i = doc.rfind('</w:body>')
        doc = doc[:i] + gbr + doc[i:]

        rels = rels.replace(
            '</Relationships>',
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/image" '
            f'Target="media/grafik_ai.png"/></Relationships>')
        if 'Extension="png"' not in ct:
            ct = ct.replace('<Default Extension="xml"',
                            '<Default Extension="png" '
                            'ContentType="image/png"/>'
                            '<Default Extension="xml"', 1)

        #  3) tulis ULANG — [Content_Types].xml SEKALI saja
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', ct)
            for n, b in lain.items():
                z.writestr(n, b)
            z.writestr('word/document.xml', doc)
            z.writestr('word/_rels/document.xml.rels', rels)
            z.writestr('word/media/grafik_ai.png', png)

        #  4) VERIFIKASI sebelum menimpa asli — kalau rusak, JANGAN timpa
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(tmp) as z:
            d2 = z.read('word/document.xml').decode('utf-8')
            try:
                ET.fromstring(d2)
            except Exception as e:                            # noqa: BLE001
                tmp.unlink(missing_ok=True)
                return {'ok': False, 'sebab': f'XML rusak: {e}'}
            if 'word/media/grafik_ai.png' not in z.namelist():
                tmp.unlink(missing_ok=True)
                return {'ok': False, 'sebab': 'gambar tidak masuk paket'}

        shutil.move(str(tmp), str(docx_path))
        return {'ok': True, 'sebab': '', 'ukuran': len(png),
                'nomor': no_gbr, 'cx': cx, 'cy': cy}
    except Exception as e:                                    # noqa: BLE001
        tmp.unlink(missing_ok=True)
        log.warning('[gambar] gagal sisip .docx: %s', e)
        return {'ok': False, 'sebab': str(e)}
'''

with p.open('a', encoding='utf-8') as f:
    f.write(TAMBAHAN)
print(f'✅ penangkap + penyisip ditambahkan · gambar.py '
      f'{len(s):,} → {len(s) + len(TAMBAHAN):,} byte')