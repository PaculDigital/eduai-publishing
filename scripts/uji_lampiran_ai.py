"""Gerbang uji 2 ARAH — lampiran pembimbing → AI mahasiswa (27Sep26).

SEHAT  : lampiran PDF + gambar sah → teks & data URL keluar.
DIRUSAK: nama disk palsu/berkas rusak → '' / [] (revisi TIDAK ikut gagal).

JALAN DI CONTAINER: docker exec eduai-app sh -c 'cd /app && python '
                    'scripts/uji_lampiran_ai.py'
"""
import io
import sys

sys.path.insert(0, '/app')

from app import lampiran_ai as LA          # noqa: E402
from app.lampiran_pembimbing import LAMPIRAN_DIR   # noqa: E402

GAGAL: list[str] = []


def cek(nama: str, syarat: bool, detail: str = '') -> None:
    tanda = '✅' if syarat else '❌'
    print(f'{tanda} {nama}' + (f' — {detail}' if detail else ''))
    if not syarat:
        GAGAL.append(nama)


# ══ SEHAT ══════════════════════════════════════════════════════════════
# 1. PDF asli (pypdf) — buat PDF minimal lewat pypdf? Pembuat PDF minimal
#    tanpa teks sulit; pakai docx text + PDF dari fixture jika ada.
#    Sederhana & jujur: uji TEKS via docx (zip XML) buatan.
import zipfile                                    # noqa: E402

docx_buf = io.BytesIO()
with zipfile.ZipFile(docx_buf, 'w') as z:
    z.writestr('word/document.xml',
               '<?xml version="1.0"?><w:document '
               'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               '<w:body><w:p><w:r><w:t>Kata'
               'KunciUjiGanoderma</w:t></w:r></w:p></w:body></w:document>')
docx_nama = 'uji_lampiran_a1b2c3d4e5f6a7b8c9d0e1f2.docx'
LAMPIRAN_DIR.mkdir(parents=True, exist_ok=True)
(LAMPIRAN_DIR / docx_nama).write_bytes(docx_buf.getvalue())
teks = LA.baca_teks(docx_nama)
cek('docx sah → teks terbaca', 'KataKunciUjiGanoderma' in teks,
    f'{len(teks)} kar')

# 2. Gambar sah → data URL
from PIL import Image                             # noqa: E402
img = Image.new('RGB', (240, 60), 'white')
Image.Image.save(img, '/tmp/gbr_uji.png')
png_nama = 'uji_lampiran_b2c3d4e5f6a7b8c9d0e1f2a.png'
(LAMPIRAN_DIR / png_nama).write_bytes(open('/tmp/gbr_uji.png', 'rb').read())
du = LA.data_url_gambar(png_nama)
cek('gambar sah → data URL', du.startswith('data:image/jpeg;base64,')
    and len(du) > 500, f'{len(du)} byte')

# 3. jenis()
cek('jenis teks', LA.jenis(docx_nama) == 'teks')
cek('jenis gambar', LA.jenis(png_nama) == 'gambar')
cek('jenis asing → kosong', LA.jenis('x.exe') == '')

# ══ DIRUSAK (wajib GAGAL DENGAN JALAN KELUAR, bukan raise) ═══════════
cek('nama disk PALSU → teks ""', LA.baca_teks('palsu999999999999999999999.docx') == '')
cek('nama disk PALSU → gambar ""', LA.data_url_gambar('palsu99999999999999999999.png') == '')
cek('nama DISERANG ../ → ""', LA.baca_teks('../../etc/passwd') == '')

rusak = 'uji_lampiran_c3d4e5f6a7b8c9d0e1f2a1b2.docx'
(LAMPIRAN_DIR / rusak).write_bytes(b'bukan docx')
cek('docx RUSAK → teks ""', LA.baca_teks(rusak) == '')

rusak_g = 'uji_lampiran_d4e5f6a7b8c9d0e1f2a1b2c3.png'
(LAMPIRAN_DIR / rusak_g).write_bytes(b'bukan png')
cek('gambar RUSAK → data URL ""', LA.data_url_gambar(rusak_g) == '')

# ══ bereskan berkas uji ═══════════════════════════════════════════════
for n in (docx_nama, png_nama, rusak, rusak_g):
    try:
        (LAMPIRAN_DIR / n).unlink()
    except OSError:
        pass

print(f'\nRINGKAS: {4 + 6 - len(GAGAL)} LULUS / {len(GAGAL)} GAGAL')
sys.exit(1 if GAGAL else 0)
