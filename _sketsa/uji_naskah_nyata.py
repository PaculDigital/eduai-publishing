#!/usr/bin/env python3
"""UJI DI NASKAH NYATA BOS — mesin konteks + grafik, pada naskah 22 tabel.

Yang diuji (AI SUNGGUHAN, jalur produksi sama):
   1. petakan() membaca struktur bab naskah NYATA
   2. bangun_prompt() mengirim BENANG MASUK/KELUAR + tetangga UTUH
   3. AI menyelesaikan permintaan grafik dengan 3 lapis
   4. Gambar disisipkan ke .docx → tabel lama TETAP UTUH
   5. Dua arah: permintaan TANPA angka → AI menolak jujur
"""
import asyncio
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_nyata_')
sys.path.insert(0, '/app')

from app import ai as A                                        # noqa: E402
from app import gambar as G                                    # noqa: E402
from app import konteks as K                                   # noqa: E402
from app import state as S                                     # noqa: E402

L, GA = 0, 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')


SUMBER = Path('/app/uploads/6/349508cb13697288.docx')  # naskah JADI 44.782 kar
print('══ UJI DI NASKAH NYATA BOS ══')
print(f'  berkas: {SUMBER.name} · {SUMBER.stat().st_size:,} byte')

#  ── 1. baca teks naskah ──
teks_utuh = A._teks_dari_berkas(SUMBER, SUMBER.name)   # fungsi nyata produksi
print(f'  teks terbaca: {len(teks_utuh):,} karakter')
cek('1. naskah terbaca', len(teks_utuh) > 5000, f'{len(teks_utuh):,} kar')

#  ── 2. petakan struktur ──
peta = S.petakan(S.buang_daftar_isi(teks_utuh))
print(f'  petakan() → {len(peta)} bagian')
for x in peta[:12]:
    print(f'      · {str(x.get("section_id"))[:14]:<14} '
          f'{str(x.get("section_title"))[:44]}')
cek('2. struktur terpetakan (≥5 bagian)', len(peta) >= 5, f'{len(peta)}')

#  ── 3. pilih bagian TENGAH (punya tetangga 2 sisi) ──
idx_t = len(peta) // 2
target = str(peta[idx_t].get('section_id')).strip()
komentar = ('Tambahkan grafik pertumbuhan jumlah unit usaha per tahun '
            'berikut: 2019=1.200, 2020=1.450, 2021=1.700, 2022=2.100, '
            '2023=2.600.')
print(f'  target uji: bagian {target} (ke-{idx_t + 1} dari {len(peta)})')

teks_prompt = K.bangun_prompt(
    bagian_target=target,
    peta=peta,
    isi_saat_ini=peta[idx_t].get('isi_teks', ''),
    komentar=komentar,
)
cek('3. prompt punya BENANG MASUK', 'BENANG MASUK' in teks_prompt)
cek('3. prompt punya BENANG KELUAR', 'BENANG KELUAR' in teks_prompt)
cek('3. prompt punya BAGIAN SEBELUMNYA', 'BAGIAN SEBELUMNYA' in teks_prompt)
cek('3. prompt punya BAGIAN SESUDAHNYA', 'BAGIAN SESUDAHNYA' in teks_prompt)
print(f'      panjang prompt: {len(teks_prompt):,} kar')

#  ── 4. panggil AI (jalur produksi sama) ──
print()
print('  ── memanggil AI (bisa 30-90 dtk) ──')
user = (teks_prompt + '\n\n=== PERMINTAAN USER ===\n' + komentar +
        '\n\n(Tulis jawaban revisi untuk bagian tersebut.)')
msg, info = asyncio.run(A._panggil_9router(user, 900))
print(f'      model={info.get("model")} · jawaban {len(msg):,} kar')
blok = G.tangkap_data_grafik(msg)
kel = G.nilai_kelayakan_grafik(msg)
cek('4. AI membuat grafik', len(blok) >= 1, f'{len(blok)} blok')
cek('4. LAPIS 1 pengantar', kel['ada_kalimat_pengantar'])
cek('4. LAPIS 3 penafsiran', kel['ada_kalimat_penafsiran'])
cek('4. layak (3 lapis lengkap)', kel['layak'] is True, kel.get('sebab', ''))
if blok:
    print(f'      jenis={blok[0]["jenis"]} · judul={blok[0]["judul"][:52]}')
    cek('4. angka user dipakai persis',
        all(a in msg.replace('.', '') for a in ('1200', '2600')))

#  ── 5. sisip ke .docx, tabel lama HARUS utuh ──
print()
print('  ── sisip gambar ke .docx asli ──')
with zipfile.ZipFile(SUMBER) as z:
    tabel_awal = z.read('word/document.xml').decode('utf-8', 'ignore').count('<w:tbl>')
    gambar_awal = len([n for n in z.namelist() if n.startswith('word/media/')])
print(f'      sebelum: {tabel_awal} tabel · {gambar_awal} gambar')

salin = Path('/app/_uji_nyata_hasil.docx')
shutil.copy(SUMBER, salin)
png = G.gambar_grafik(blok[0]['data'], jenis=blok[0]['jenis'],
                      judul=blok[0]['judul'], satuan=blok[0]['satuan']) if blok else b''
png_path = Path('/app/grafik_nyata.png')
png_path.write_bytes(png)
if png:
    G.sisip_gambar_docx(salin, png, keterangan=blok[0]['judul'])

with zipfile.ZipFile(salin) as z:
    doc2 = z.read('word/document.xml').decode('utf-8', 'ignore')
    tabel_akhir = doc2.count('<w:tbl>')
    gambar_akhir = len([n for n in z.namelist() if n.startswith('word/media/')])
print(f'      sesudah: {tabel_akhir} tabel · {gambar_akhir} gambar')

cek('5. TABEL LAMA TETAP UTUH (jumlah sama)', tabel_akhir == tabel_awal,
    f'{tabel_awal} → {tabel_akhir}')
cek('5. ada gambar BARU masuk', gambar_akhir == gambar_awal + 1,
    f'{gambar_awal} → {gambar_akhir}')
cek('5. XML masih sah (punya w:document)',
    re.search(r'<w:document(?:\s+[\w:.-]+\s*=\s*"[^"]*")*\s*/?>', doc2) is not None)

#  ── 6. DIRUSAK: tanpa angka → harus menolak ──
print()
print('  ── DIRUSAK: permintaan tanpa angka ──')
komentar2 = 'Tambahkan grafik pertumbuhan jumlah unit usaha per tahun.'
teks2 = K.bangun_prompt(bagian_target=target, peta=peta,
                        isi_saat_ini=peta[idx_t].get('isi_teks', ''),
                        komentar=komentar2)
msg2, _ = asyncio.run(A._panggil_9router(
    teks2 + '\n\n=== PERMINTAAN USER ===\n' + komentar2, 900))
cek('6. TIDAK menggambar (tidak mengarang)',
    len(G.tangkap_data_grafik(msg2)) == 0)

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
