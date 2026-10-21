"""TAHAP 1 — rakit_presisi mampu menaruh paragraf GAMBAR di antara baris.

Menambahkan:
  · parameter `gambar_di` = {nomor: png_bytes}
  · pengubah baris penanda `[[GAMBAR-PNG-<n>]]` menjadi paragraf gambar Word
  · helper `_par_gambar_word()` (MEMAKAI ULANG pola yang sudah terbukti di
    app/gambar.py — jangan menulis pola OOXML baru)
"""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/tulis_docx.py')
s = P.read_text()

assert 'gambar_di' not in s, 'sepertinya sudah dipatch'

#  ── A. helper paragraf gambar (ditaruh sebelum rakit_presisi) ──
HELPER = '''
def _par_gambar_word(png: bytes, rid: str = '',
                     cx: int = 5_486_400, cy: int = 3_200_400,
                     idx: int = 1) -> str:
    """Paragraf Word berisi 1 gambar (PNG bytes) — dipakai rakit_presisi().

    🔴 MEMAKAI ULANG pola OOXML yang SUDAH TERBUKTI di app/gambar.py
       (`sisip_gambar_docx`). JANGAN menulis pola baru — sudah 3 bug
       ditutup di sana (Content_Types dobel, namespace, tag w:document).
    """
    if not png or not rid:
        return ''
    pid = 910_000 + int(idx)
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pid}" name="Grafik{idx}"/>'
        '<a:graphic><a:graphicData '
        'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic>'
        f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="grafik_{idx}.png"/>'
        '<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
        '<a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing></w:r></w:p>'
    )


'''
s = s.replace('def rakit_presisi(', HELPER + 'def rakit_presisi(', 1)

#  ── B. tanda tangan terima gambar_di ──
s = s.replace("""def rakit_presisi(
    xml: str,
    editan: list,
    semua_paragraf: list[str],
) -> tuple[str, dict]:""",
"""def rakit_presisi(
    xml: str,
    editan: list,
    semua_paragraf: list[str],
    gambar_di: dict | None = None,
) -> tuple[str, dict]:""", 1)

#  ── C. baris penanda → paragraf gambar ──
lama = """        isi_baru = ''.join(
            _par_baru(b.strip(), pPr, rPr) for b in baris if b.strip())
        if not isi_baru:
            tak_ketemu.append(e.nomor)
            continue"""
baru = """        #  🆕 26Sep26 (arahan Bos): baris `[[GAMBAR-PNG-n]]` BUKAN teks —
        #     diganti paragraf GAMBAR Word, supaya urutannya tetap
        #     pembuka → GRAFIK → keterangan DI DALAM bagian yang diganti.
        _peta_gambar = gambar_di or {}
        _potong: list[str] = []
        for b in baris:
            _m = re.match(r'^\\s*\\[\\[GAMBAR-PNG-(\\d+)\\]\\]\\s*$', b)
            if _m:
                _nomor_g = int(_m.group(1))
                _png_g = _peta_gambar.get(_nomor_g)
                _rid_g = _peta_gambar.get(f'_rid{_nomor_g}', '')
                _par_g = _par_gambar_word(_png_g, _rid_g, idx=_nomor_g) \\
                    if _png_g else ''
                if _par_g:
                    _potong.append(_par_g)
                continue                       # penanda JANGAN jadi teks
            if b.strip():
                _potong.append(_par_baru(b.strip(), pPr, rPr))
        isi_baru = ''.join(_potong)
        if not isi_baru:
            tak_ketemu.append(e.nomor)
            continue"""
assert lama in s, 'blok baris tak ketemu'
s = s.replace(lama, baru, 1)

#  ── D. terapkan_editan_ke_berkas teruskan gambar_di + tulis media/rel ──
P.write_text(s)
print('✅ TAHAP 1 selesai: rakit_presisi(gambar_di=...) + _par_gambar_word()')
