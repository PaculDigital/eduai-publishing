"""UJI DAMPAK PERBAIKAN — 3 berkas diperbaiki, sekarang buktikan.

Membandingkan hasil SEBELUM vs SESUDAH pada 6 naskah NYATA.
Tidak mengubah apa pun — hanya memanggil fungsi produksi.

Yang diuji:
  app.versi.deteksi_bab()          (berkas diperbaiki)
  app.cari_bagian (pola)           (berkas diperbaiki)
  app.tulis_docx._mirip_judul()    (berkas diperbaiki)
  app.state.deteksi_bab_besar()    (acuan, sudah benar)
"""
import html
import os
import re
import sys
import zipfile

sys.path.insert(0, '/app')

from app import versi, state, tulis_docx  # noqa: E402
from app import cari_bagian as cb  # noqa: E402

UJI = [
    (60, 'SKRIPSI S1 unmul 5MB', 5),
    (71, 'TESIS S2 unhas', 7),
    (72, 'DISERTASI S3 unhas', 5),
    (70, 'SKRIPSI S1 unhas', 5),
    (78, 'TESIS S2 varian', 7),
    (9,  'TESIS Goras', 5),
]


def teks_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'replace')
    xml = re.sub(r'</w:p>', '\n', xml)
    xml = re.sub(r'<[^>]+>', '', xml)
    return html.unescape(xml)


def cari(fid):
    from app.models import SessionLocal, FileBerkas
    db = SessionLocal()
    f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
    db.close()
    if not f:
        return None
    p = f'/app/uploads/{f.user_id}/{f.nama_simpan}'
    return p if os.path.exists(p) else None


print('╔══════════════════════════════════════════════════════════════════════╗')
print('║  UJI DAMPAK PERBAIKAN — 6 NASKAH NYATA                              ║')
print('╚══════════════════════════════════════════════════════════════════════╝')

hasil = []
for fid, sebutan, harap in UJI:
    p = cari(fid)
    print(f'\n═══ {sebutan} (id={fid}) ═══')
    if not p:
        print('   ⚠️ berkas tidak ketemu — dilewati')
        continue
    teks = teks_docx(p)

    #  fungsi produksi (diperbaiki)
    bab = versi.deteksi_bab(teks)
    nomor = sorted({str(b['nomor']) for b in bab})

    #  mesin acuan state.py
    bab_state = state.deteksi_bab_besar(teks)
    nomor_state = sorted({str(b.get('nomor')) for b in bab_state})

    print(f'   versi.deteksi_bab  → {len(bab)} bab {nomor}')
    for b in bab[:8]:
        print(f'      · {b["label"]:9s} | {str(b["judul"])[:46]}')
    print(f'   state.deteksi_bab_besar → {len(bab_state)} bab {nomor_state}')

    jumlah = len(bab)
    tanda = '✅' if jumlah >= harap else '❌'
    hasil.append((sebutan, harap, jumlah, tanda))

#  uji _mirip_judul
print('\n\n═══ UJI tulis_docx._mirip_judul ═══')
for t, harap in [('BAB IPENDAHULUAN', True), ('BAB I PENDAHULUAN', True),
                 ('BAB IIIMETODOLOGI PENELITIAN', True),
                 ('Bab II Kajian Pustaka', True),
                 ('bab ini menjelaskan metode', False),
                 ('Tabel bab 3 menyajikan', False),
                 ('ini kalimat biasa saja', False)]:
    got = tulis_docx._mirip_judul(t, '')
    print(f'  {"✅" if got == harap else "❌"} {t!r:36s} → {got}')

#  uji pola cari_bagian
print('\n═══ UJI pola cari_bagian ═══')
pola_bab = [p for p in cb._POLA_KHAS if 'BAB' in p.pattern]
if pola_bab:
    P = pola_bab[0]
    print(f'  pola: {P.pattern}')
    for t in ['BAB IPENDAHULUAN', 'BAB III METODE PENELITIAN',
              'Tabel bab 3 menyajikan', 'bab ini menjelaskan',
              'lihat BAB IV hasil']:
        m = P.search(t)
        print(f'  {"✅ cocok" if m else "⬜ tidak"} {t!r:34s} '
              f'{"→ " + repr(m.group(0)) if m else ""}')

print('\n\n╔════════════════════ RINGKASAN ════════════════════╗')
print('  %-26s %6s %8s %6s' % ('naskah', 'harap', 'hasil', ''))
for s, h, j, t in hasil:
    print('  %-26s %6d %8d   %s' % (s[:26], h, j, t))
