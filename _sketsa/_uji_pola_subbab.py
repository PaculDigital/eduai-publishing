"""UJI OPSI A — _POLA_SUBBAB kenali "1.1." (titik kedua) — 24Sep26.

Bukti yang diminta: SEBELUM vs SESUDAH pada 5 dokumen nyata + naskah tesis Bos.
Menguji FUNGSI ASLI app.state.petakan() / deteksi_subbab() — bukan salinan.
"""
import sys, zipfile, re, os, importlib
sys.path.insert(0, '/opt/data/services/eduai-publishing')

def baca(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', xml))

DOK = [
    ('tesis S2 manajemen', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx'),
    ('tesis S2 pend.bahasa', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx'),
    ('tesis S2 sastra', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx'),
    ('skripsi S1 UNMUL', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
    ('skripsi S1 olahraga', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx'),
]

def ukur(mod, teks):
    from app.state import petakan
    p = petakan(teks)
    return {
        'sub': len(mod.deteksi_subbab(teks)),
        'peta': len(p),
        'pertama': p[0]['section_id'] if p else '-',
        'kiriman': sum(max(1, -(-len(x['isi_teks']) // 55000)) for x in p),
    }

import app.state as st

print('=' * 100)
print('UJI OPSI A — pola "1.1." (titik kedua)  ·  SEBELUM vs SESUDAH')
print('=' * 100)
print(f'\nPola LAMA    : {r"^\s*([1-9]|[12]\d)\.(\d{1,2})\s+"}')
print(f'Pola BARU    : {r"^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+"}')
print(f'Pola di berkas: {st._POLA_SUBBAB.pattern}')

# ── BANDINGKAN dengan pola lama (dihitung manual, tanpa mengubah berkas) ──
POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\s+([A-Z][^\n]{2,110})$', re.M)
POLA_BARU = st._POLA_SUBBAB

print(f'\n{"=" * 100}')
print(f'{"dokumen":<22}{"pola lama":>12}{"pola baru":>12}   keterangan')
print('=' * 100)
for nama, path in DOK:
    if not os.path.exists(path):
        print(f'{nama:<22} (berkas tidak ada)'); continue
    from app.state import buang_daftar_isi
    bersih = buang_daftar_isi(baca(path))
    n_lama = len(POLA_LAMA.findall(bersih))
    n_baru = len(POLA_BARU.findall(bersih))
    tanda = '⭐ PERBAIKAN' if n_baru > n_lama else ('= tetap' if n_baru == n_lama else '⚠️ RUSAK')
    print(f'{nama:<22}{n_lama:>12}{n_baru:>12}   {tanda}')

# ── UJI PENUH: peta & harga sebelum vs sesudah (pakai FUNGSI ASLI) ──
print(f'\n{"=" * 100}')
print('DAMPAK KE PETA & KIRIMAN KE AI (fungsi asli app.state.petakan)')
print('=' * 100)
for nama, path in DOK:
    if not os.path.exists(path):
        continue
    from app.state import buang_daftar_isi
    bersih = buang_daftar_isi(baca(path))
    sub = st.deteksi_subbab(bersih)
    peta = st.petakan(bersih)
    kiriman = sum(max(1, -(-len(x['isi_teks']) // 55000)) for x in peta)
    print(f'\n### {nama}  ({len(bersih):,} kar)')
    print(f'    sub-bab terdeteksi: {len(sub)}   peta: {len(peta)} bagian   '
          f'kiriman ke AI: {kiriman}')
    for x in peta[:10]:
        print(f'       {x["section_id"]:<10} {x["section_title"][:40]:<40} {x["char_count"]:>9,} kar')
    if len(peta) > 10:
        print(f'       … dan {len(peta)-10} bagian lagi')

print()
print('=' * 100)
print('GERBANG: apakah ada dokumen yang RUSAK (sub-bab berkurang)?')
print('=' * 100)
rusak = 0
for nama, path in DOK:
    if not os.path.exists(path):
        continue
    from app.state import buang_daftar_isi
    bersih = buang_daftar_isi(baca(path))
    if len(POLA_BARU.findall(bersih)) < len(POLA_LAMA.findall(bersih)):
        print(f'  ❌ RUSAK: {nama}'); rusak += 1
print(f'  {"✅ tidak ada yang rusak" if rusak == 0 else f"❌ {rusak} dokumen rusak"}')
sys.exit(0 if rusak == 0 else 1)
