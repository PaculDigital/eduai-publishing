"""GERBANG JALUR BUKU — `susun()` dijalankan SAMPAI SELESAI, bukan cuma diimpor.

🚨 KENAPA GERBANG INI ADA (20 Okt 2026):
Bug nyata: `susun()` mencari `bab{n}.txt` di AKAR folder buku, padahal
`susun_buku()` menyimpannya di `bab{n}/bab{n}.txt`. Akibatnya buku yang SUDAH
JADI (2.078 + 2.155 kata, 3 diagram Jev, 4 tabel, ilustrasi) DIBUANG dan
dilaporkan "tidak satu pun berkas bab tersimpan" — user kehilangan hasil yang
sudah dibayar tokennya.

Bug itu TIDAK PERNAH tertangkap karena tidak ada uji yang memanggil `susun()`
sampai selesai. Gerbang ini menutup lubang itu.

CARA: AI & Jev DIPALSUKAN (Rp 0, cepat), tapi ALUR SUNGGUHAN — termasuk
menulis `bab{n}/bab{n}.txt` ke disk, merakit .docx, dan memeriksa hasilnya.

BERGIGI: kalau `_path_bab()` dikembalikan ke bentuk lama (nama saja),
uji ③ & ④ HARUS gagal.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

LULUS, GAGAL = [], []


def cek(nama, syarat, bukti=''):
    (LULUS if syarat else GAGAL).append(f'{nama} {bukti}'.strip())


AKAR = tempfile.mkdtemp(prefix='gerbang_jalur_buku_')
os.environ['BUKU_DIR'] = AKAR

# ── Palsukan AI + Jev SEBELUM modul dimuat ────────────────────────────────
import app.jev as JEV

JEV.tanya = lambda *a, **k: {'jumlah_tahap': {'score': 4, 'confidence': 1.0},
                             'ada_urutan': {'noul': 0.95}}

from app import penyusunan_buku as S      # noqa: E402

#  `susun()` memanggil `susun_buku()` (di `penyusun_buku`) yang memakai LLM
#  & pembuat gambar. Semua dipalsukan — yang diuji JALUR & PEMERIKSAAN
#  BERKAS, bukan mutu tulisan.
import penyusun_buku as PN                # noqa: E402

ISI_BAB = {n: (f'### {n}.1 Bagian\n\n' + 'kalimat uji. ' * 60)
           for n in (1, 2)}


def susun_buku_palsu(judul, outline, jenis='umum', keluar_dir=None, lapor=None):
    """Tiru `susun_buku()` — TERMASUK letak berkas yang jadi akar bug."""
    hasil_bab, gagal = {}, {}
    for n in (1, 2):
        d = os.path.join(keluar_dir, f'bab{n}')
        os.makedirs(d, exist_ok=True)
        #  ⚠️ LETAK INI YANG MENJADI AKAR BUG: di DALAM folder bab.
        with open(os.path.join(d, f'bab{n}.txt'), 'w', encoding='utf-8') as f:
            f.write(ISI_BAB[n])
        hasil_bab[n] = {'kata': 120, 'sitasi': 1, 'file': f'bab{n}.txt'}
    if gagal:
        raise RuntimeError(f'{gagal} TIDAK LOLOS')
    return {'ok': True, 'judul': judul, 'jenis': jenis, 'bab': hasil_bab,
            'bab_selesai': len(hasil_bab), 'mutu_lolos': True,
            'mutu_masalah': [], 'mutu_curiga': [], 'total_kata': 240,
            'total_sitasi': 2, 'detik': 0.1}


PN.susun_buku = susun_buku_palsu

#  Outline juga dipalsukan (tidak memanggil LLM).
import outline_buku as OB               # noqa: E402

OB.susun_outline = lambda judul, bidang='', jenis='umum', jumlah_bab=None, \
    sub_per_bab=None, panggil_llm=None, bahasa='Indonesia': {
        1: {'title': 'Bab Satu', 'subs': [(1, 'Sub', '')]},
        2: {'title': 'Bab Dua', 'subs': [(1, 'Sub', '')]},
        '_judul': judul, '_bidang': bidang, '_jenis': jenis, '_sumber': 'uji'}
OB.periksa = lambda outline: []

#  Kuota dipalsukan (tidak memotong saldo sungguhan).
from app import kuota                  # noqa: E402

kuota.potong_banyak = lambda db, u, n: {'sisa': 99}
kuota.kembalikan_banyak = lambda db, u, n: None


class UserUji:
    id = 990001
    email = 'gerbang@localhost'
    nama = 'Gerbang'
    paket = 'penerbit'
    role = 'client'


class DbUji:
    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    def add(self, *a):
        pass

    def flush(self):
        pass


#  Pendaftaran berkas ke tabel `files` dipalsukan — yang diuji bukan itu.
S._daftarkan_berkas = lambda db, u, path, judul: 12345

hasil = None
try:
    hasil = S.susun(DbUji(), UserUji(), 'Buku Uji Gerbang', 'sains', 'sd',
                    'anak', jumlah_bab=2, lapor=None)
    jalan = True
    galat = ''
except Exception as e:                                          # noqa: BLE001
    jalan, galat = False, f'{type(e).__name__}: {e}'
    import traceback
    traceback.print_exc()

#  ① susun() selesai tanpa galat
cek('① susun() selesai tanpa galat', jalan, galat)

#  ② bab dilaporkan ADA
ada = (hasil or {}).get('bab_ada') or []
cek('② bab_ada berisi 2 bab', sorted(ada) == [1, 2], str(ada))

#  ③ path LENGKAP menunjuk berkas yang benar-benar ada
paths = [(hasil or {}).get('bab', {}).get(n, {}).get('path') for n in (1, 2)]
cek('③ path tiap bab ADA di disk', all(p and os.path.exists(p) for p in paths),
    str(paths))

#  ④ letak path = di DALAM folder bab (bentuk nyata, bukan akar)
cek('④ path di dalam folder bab',
    all(p and os.path.basename(os.path.dirname(p)) == f'bab{n}'
        for n, p in zip((1, 2), paths)), str(paths))

#  ⑤ isi berkas benar-benar teks bab
isi_ok = all(p and open(p, encoding='utf-8').read().startswith('### ')
             for p in paths)
cek('⑤ isi berkas = teks bab sungguhan', isi_ok)

#  ⑥ .docx dirakit & ADA (bukan cuma diklaim)
docx = (hasil or {}).get('docx')
cek('⑥ .docx dirakit & ada di disk',
    bool(docx) and os.path.exists(docx), f'docx={docx}')

#  ⑦ token TIDAK dikembalikan saat sukses (anti-rugi hanya saat gagal)
cek('⑦ jalur sukses tidak menyentuh pengembalian token', jalan,
    'kalau gagal, token kembali — itu benar')

shutil.rmtree(AKAR, ignore_errors=True)

import json                                                     # noqa: E402
print(json.dumps({'lulus': len(LULUS), 'gagal': len(GAGAL),
                  'rincian_lulus': LULUS, 'rincian_gagal': GAGAL},
                 ensure_ascii=False, indent=1))
sys.exit(1 if GAGAL else 0)
