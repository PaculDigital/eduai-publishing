"""LANGKAH 1 (ACC Bos 03Okt26) — UJI POLA DETEKSI BAB TANPA MENYENTUH PRODUKSI.

Tujuan: buktikan berapa naskah yang GAGAL dideteksi oleh `versi.deteksi_bab`
(pola \b) vs `state` (pola sudah diperbaiki 16Sep26), pada naskah NYATA.

TIDAK mengubah kode apa pun. Hanya MEMBACA + MENGUKUR.

Naskah diuji (nyata di produksi):
  60  SKRIPSI-S1-unmul-fazrigading   (5,3 MB — yang GAGAL tadi)
  71  TESIS-S2-unhas
  72  DISERTASI-S3-unhas
  70  SKRIPSI-S1-unhas-olahraga
  78  TESIS-S2-unhas (varian lain)
"""
import glob
import html
import os
import re
import sys
import zipfile

sys.path.insert(0, '/app')

from app import versi  # noqa: E402

# ── pola versi.py (SEKARANG, pakai \b) ──────────────────────────────────
POLA_LAMA = re.compile(
    r'^[ \t]*(BAB|Bab|bab)[ \t]+([IVXLCDM]+|\d{1,2})\b[ \t]*[:.]?[ \t]*(.*)$',
    re.MULTILINE)

# ── pola state.py (SUDAH DIPERBAIKI 16Sep26, tanpa \b) ──────────────────
POLA_BARU = re.compile(r'^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5})[ \t]*(.*)$',
                       re.MULTILINE)


def teks_docx(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'replace')
    xml = re.sub(r'</w:p>', '\n', xml)
    xml = re.sub(r'<[^>]+>', '', xml)
    return html.unescape(xml)


def cari(fid: int) -> str | None:
    from app.models import SessionLocal, FileBerkas
    db = SessionLocal()
    f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
    db.close()
    if not f:
        return None
    p = f'/app/uploads/{f.user_id}/{f.nama_simpan}'
    return p if os.path.exists(p) else None


def hitung(pola, teks: str):
    """Hitung bab ditemukan + judul (pakai pola mentah, tanpa penyaring)."""
    out = []
    for m in pola.finditer(teks):
        nomor = m.group(1).strip()
        judul = (m.group(2) or '').strip(' .:-\t')
        out.append((nomor, judul[:44]))
    return out


UJI = [
    (60, 'SKRIPSI S1 unmul 5MB'),
    (71, 'TESIS S2 unhas'),
    (72, 'DISERTASI S3 unhas'),
    (70, 'SKRIPSI S1 unhas olahraga'),
    (78, 'TESIS S2 varian'),
    (9,  'TESIS LENGKAP Goras'),
]

print('╔══════════════════════════════════════════════════════════════════╗')
print('║  BANDINGKAN POLA: versi.py (sekarang)  vs  state.py (diperbaiki) ║')
print('╚══════════════════════════════════════════════════════════════════╝')

ringkas = []
for fid, sebutan in UJI:
    p = cari(fid)
    print(f'\n═══ {sebutan} (id={fid}) ═══')
    if not p:
        print('   ⚠️ berkas tidak ketemu — dilewati')
        continue
    teks = teks_docx(p)
    print(f'   {len(teks):,} kar')

    lama = hitung(POLA_LAMA, teks)
    baru = hitung(POLA_BARU, teks)

    #  mesin ASLI versi.py (dengan penyaring lengkap)
    asli = versi.deteksi_bab(teks)

    print(f'   versi.py SEKARANG → {len(asli)} bab '
          f'({[b["label"] for b in asli]})')
    print(f'   pola versi.py     → {len(lama)} kandidat: '
          f'{[n for n, _ in lama]}')
    print(f'   pola state.py     → {len(baru)} kandidat: '
          f'{[n for n, _ in baru]}')
    if baru:
        print('      contoh judul (pola baru):')
        for n, j in baru[:6]:
            print(f'         · BAB {n} | {j}')
    ringkas.append((sebutan, len(asli), len(lama), len(baru)))

print('\n\n╔═══════════════════ RINGKASAN ═══════════════════╗')
print('  %-28s %8s %8s %8s' % ('naskah', 'versi.py', 'pola', 'state'))
for s, a, l, b in ringkas:
    tanda = '  ← GAGAL' if a == 0 and b > 0 else ''
    print('  %-28s %8d %8d %8d%s' % (s[:28], a, l, b, tanda))
print('\n  versi.py = mesin ASLI produksi (deteksi_bab, sudah pakai penyaring)')
print('  pola     = regex POLA_LAMA mentah (tanpa penyaring)')
print('  state    = regex POLA_BARU (perbaikan 16Sep26, tanpa penyaring)')
