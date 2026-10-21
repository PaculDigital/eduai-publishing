#!/usr/bin/env python3
"""UJI TERPISAH — rakit_presisi menaruh paragraf GAMBAR di antara baris.

Bentuk yang diuji (arahan Bos 26Sep26):
   paragraf pembuka → GRAFIK (paragraf Word berisi PNG) → paragraf keterangan

2 ARAH:
   A. penanda [[GAMBAR-PNG-1]] + png  → 3 paragraf (teks·gambar·teks)
   B. TANPA gambar_di (perilaku lama) → penanda jangan jadi teks,
      dan JANGAN ada paragraf gambar (tetap 2 paragraf teks)
"""
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_rakit_gbr_')
sys.path.insert(0, '/app')

from app import gambar as G                                    # noqa: E402
from app import tulis_docx as T                                # noqa: E402

L, GA = 0, 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')


SUMBER = Path('/app/uploads/6/349508cb13697288.docx')
PNG = G.gambar_grafik([{'label': '2020', 'nilai': 120},
                       {'label': '2021', 'nilai': 180}],
                      jenis='batang', judul='Uji Sisip Tengah', satuan='orang')

PEMBUKA = ('Pertumbuhan peserta latihan kriket digambarkan sebagai diagram '
           'batang agar arah perubahan setiap tahun mudah dibaca, '
           'sebagaimana disajikan pada grafik berikut.')
KETERANGAN = ('Berdasarkan grafik tersebut, jumlah peserta meningkat dari '
              '120 orang pada 2020 menjadi 180 orang pada 2021.')


class E:
    """Editan tiruan (sama bentuk dengan pipa.Editan)."""

    def __init__(self, nomor, kutip, ganti):
        self.nomor = nomor
        self.kutip = kutip
        self.ganti = ganti


print('══ UJI TERPISAH: rakit_presisi + gambar di tengah ══')
print()

#  ── A. DENGAN gambar_di ──
print('── A. dengan gambar_di (PNG di tengah) ──')
salin = Path('/app/_uji_rakit_A.docx')
shutil.copy(SUMBER, salin)
#  kutipan = paragraf nyata dari naskah (supaya cocok)
with zipfile.ZipFile(SUMBER) as z:
    xml = z.read('word/document.xml').decode('utf-8')
par = T.peta_paragraf(xml)
kutip = next(p['teks'] for p in par
             if p['teks'].startswith('Batting (memukul)'))
print(f'   kutip: {kutip[:60]!r}')

ed = [E(1, kutip,
        PEMBUKA + '\n[[GAMBAR-PNG-1]]\n' + KETERANGAN)]
hasil = T.terapkan_editan_ke_berkas(salin, ed, [p['teks'] for p in par],
                                    gambar_di={1: PNG})
print(f'   hasil: ok={hasil.get("ok")} · paragraf_diganti='
      f'{hasil.get("paragraf_diganti")}')
cek('A. ok=True', hasil.get('ok') is True, str(hasil.get('pesan'))[:90])

with zipfile.ZipFile(salin) as z:
    doc2 = z.read('word/document.xml').decode('utf-8')
    media = [n for n in z.namelist() if 'grafik_ai' in n]
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
    tipe = z.read('[Content_Types].xml').decode('utf-8')

par2 = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc2, re.S)
i_gbr = next((i for i, p in enumerate(par2) if 'grafik_ai' in p), None)
print(f'   paragraf gambar di indeks: {i_gbr}')
cek('A. ada paragraf GAMBAR', i_gbr is not None)
cek('A. ada berkas media PNG baru', len(media) >= 1, str(media))
cek('A. penanda TIDAK jadi teks', 'GAMBAR-PNG' not in doc2)
cek('A. XML tetap sah', '<w:document' in doc2)
cek('A. rel image ditambahkan', 'relationships/image' in rels)
cek('A. content-types punya png', 'png' in tipe)

#  urutan: pembuka < gambar < keterangan
if i_gbr is not None:
    def teks_par(p):
        return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).strip()
    sebelum = [teks_par(par2[i]) for i in range(max(0, i_gbr - 3), i_gbr)]
    sesudah = [teks_par(par2[i]) for i in range(i_gbr + 1,
                                               min(len(par2), i_gbr + 4))]
    print(f'   3 paragraf sebelum: {[x[:44] for x in sebelum]}')
    print(f'   3 paragraf sesudah: {[x[:44] for x in sesudah]}')
    cek('A. sebelum gambar = PEMBUKA',
        any('grafik berikut' in x for x in sebelum), str(sebelum)[:80])
    cek('A. sesudah gambar = KETERANGAN',
        any('Berdasarkan grafik tersebut' in x for x in sesudah),
        str(sesudah)[:80])

#  ── B. TANPA gambar_di (perilaku lama) ──
print()
print('── B. DIRUSAK: tanpa gambar_di (harus tetap jalan, tanpa gambar) ──')
salin2 = Path('/app/_uji_rakit_B.docx')
shutil.copy(SUMBER, salin2)
ed2 = [E(1, kutip, PEMBUKA + '\n[[GAMBAR-PNG-1]]\n' + KETERANGAN)]
hasil2 = T.terapkan_editan_ke_berkas(salin2, ed2, [p['teks'] for p in par])
print(f'   hasil: ok={hasil2.get("ok")}')
cek('B. ok=True', hasil2.get('ok') is True, str(hasil2.get('pesan'))[:90])
with zipfile.ZipFile(salin2) as z:
    doc3 = z.read('word/document.xml').decode('utf-8')
    media3 = [n for n in z.namelist() if 'grafik_ai' in n]
cek('B. TIDAK ada berkas gambar', len(media3) == 0, str(media3))
cek('B. penanda TIDAK jadi teks', 'GAMBAR-PNG' not in doc3)
cek('B. 2 paragraf teks tetap masuk',
    'grafik berikut' in doc3 and 'Berdasarkan grafik tersebut' in doc3)

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
