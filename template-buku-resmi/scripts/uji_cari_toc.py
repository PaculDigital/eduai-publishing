#!/usr/bin/env python3
"""Uji regresi cari TOC (ukur_halaman di buat_buku.py).

Latar: daftar isi yang melintasi 2 halaman membuat BAB III
terpetakan ke halaman lanjutan TOC, bukan ke judul aslinya.
Perbaikan pertama (saring baris bertitik 4+) hanya bekerja
untuk judul pendek: rumus sisip_titik memberi minimum 3 titik
(n = max(3, ...)), jadi judul panjang hanya bertitik 3 dan
lolos saringan (temuan review agen 27 Okt 2026, terbukti
reproduksi: BAB III 'METODE PENELITIAN DAN PENGEMBANGAN'
terpetakan ke hlm 5, padahal judul asli di hlm 8).

Uji ini mengunci perbaikan kedua (saring baris bertitik 2+):
  1. judul pendek  -> BAB III = 8 (kasus asal)
  2. judul panjang -> BAB III = 8, BUKAN 5 (kasus agen)

Jalankan dari direktori scripts, dengan perender WordCraft
tersedia (WORDCRAFT_CLI / wordcraft-cli di PATH / docker
hermes). Bila perender atau pdftotext tidak tersedia, uji
SKIP (bukan gagal) — sama seperti gerbang chapter yang
melaporkan 'tidak terukur' tanpa crash.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

DIREKTORI = Path(__file__).resolve().parent
sys.path.insert(0, str(DIREKTORI))

PROFIL = DIREKTORI.parent / 'jenis' / 'monograf' / 'profil.json'


def bangun_docx(spec_path, keluar):
    """Bangun docx TANPA ukur (ukur diuji terpisah di bawah)."""
    r = subprocess.run(
        [sys.executable, str(DIREKTORI / 'buat_buku.py'),
         str(spec_path), str(keluar),
         '--profil', str(PROFIL), '--tanpa-ukur'],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'gagal membangun docx: {r.stderr[-800:]}')


def main():
    spec_awal = json.loads((DIREKTORI / 'contoh_monograf.json').read_text())
    kasus = [
        # (nama, judul BAB III baru atau None, kunci peta yang dicek)
        ('judul pendek', None, 'BAB III HASIL DAN PEMBAHASAN'),
        ('judul panjang', 'Metode Penelitian dan Pengembangan',
         'BAB III METODE PENELITIAN DAN PENGEMBANGAN'),
    ]
    lulus = 0
    gagal = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for nama, judul_baru, kunci_bab3 in kasus:
            spec = json.loads(json.dumps(spec_awal))
            if judul_baru:
                for b in spec['bab']:
                    if b['romawi'] == 'III':
                        b['judul'] = judul_baru
            spec_path = td / f'spec-{nama.replace(" ", "-")}.json'
            spec_path.write_text(json.dumps(spec, ensure_ascii=False))
            docx = td / f'buku-{nama.replace(" ", "-")}.docx'
            bangun_docx(spec_path, docx)
            try:
                import buat_buku
                peta, hilang, total = buat_buku.ukur_halaman(str(docx), spec)
            except (RuntimeError, FileNotFoundError, OSError) as e:
                print(f'SKIP: perender/pembaca PDF tidak tersedia ({e})')
                return 0
            harap = {'BAB I PENDAHULUAN': 6, 'BAB II TINJAUAN PUSTAKA': 7,
                     kunci_bab3: 8, '3.1 Pembahasan': 8}
            salah = [(k, harap[k], peta.get(k))
                     for k in harap if peta.get(k) != harap[k]]
            if salah:
                gagal.append((nama, salah))
                print(f'GAGAL [{nama}]: {salah} (total {total} hlm)')
            else:
                lulus += 1
                print(f'LULUS [{nama}]: BAB III = {peta[kunci_bab3]} '
                      f'(bukan halaman lanjutan TOC)')
    print(f'RINGKAS UJI CARI TOC: {lulus} LULUS / {len(gagal)} GAGAL')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
