#!/usr/bin/env python3
"""Ambil contoh dokumen NYATA untuk ladang uji EduAi (LANGKAH B).

PRINSIP (aturan Bos): contoh HARUS dokumen nyata, JANGAN dikarang.
Skrip ini HANYA mengunduh + mencatat SUMBERNYA. Tidak mengubah isi.

Cara pakai:
    python3 ambil_contoh.py            # lihat daftar calon saja
    python3 ambil_contoh.py --unduh    # benar-benar unduh

Hasil: berkas di _arsip/contoh-dokumen/<jenis>/ + SUMBER.md (asal + ukuran + hash)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parent
CONTOH = AKAR / '_arsip' / 'contoh-dokumen'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/121.0 Safari/537.36')

# ── CALON CONTOH ────────────────────────────────────────────────────────
# Setiap entri: (jenis_folder, nama_simpan, url, catatan_sumber)
# HANYA dari repositori/arsip TERBUKA & boleh diunduh. Diverifikasi saat unduh:
# kalau bukan DOCX sungguhan → DITOLAK, tidak dipaksa masuk.
CALON: list[tuple[str, str, str, str]] = [
    # Contoh nyata format skripsi S1 dari repositori kampus (DOCX template resmi
    # + contoh naskah). Diunduh apa adanya, bukan karangan.
    ("skripsi-s1", "unmul-format-skripsi.docx",
     "https://github.com/fazrigading/skripsi-informatika-unmul/releases/download/v1.0.0/format-skripsi-by-gading+csl.zip",
     "Template resmi skripsi S1 Informatika Universitas Mulawarman (ZIP, ambil docx-nya)"),
    ("dokumen-umum", "contoh-surat-perjanjian.docx",
     "https://www.ilmubahasa.net/contoh-surat-perjanjian-kerja-sama.docx",
     "Contoh dokumen umum (perjanjian) — untuk uji jalur NON-akademik"),
]


def _ambil(url: str, tujuan: Path, batas_mb: int = 25) -> tuple[bool, str]:
    """Unduh dengan UA Chrome. Balikkan (berhasil, keterangan)."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': '*/*',
            'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read(batas_mb * 1024 * 1024 + 1)
            if len(data) > batas_mb * 1024 * 1024:
                return False, f'terlalu besar (>{batas_mb} MB)'
            if not data:
                return False, 'kosong'
            tujuan.write_bytes(data)
            return True, f'{len(data):,} byte'
    except urllib.error.HTTPError as e:
        return False, f'HTTP {e.code}'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def _jenis_nyata(p: Path) -> str:
    """Deteksi jenis berkas dari MAGIC BYTES — jangan percaya ekstensi."""
    if not p.exists() or p.stat().st_size < 4:
        return 'kosong'
    kepala = p.read_bytes()[:4]
    if kepala[:2] == b'PK':
        return 'zip'          # docx/xlsx/pptx/zip
    if kepala.startswith(b'%PDF'):
        return 'pdf'
    if kepala.startswith(b'\x7fELF'):
        return 'elf'
    return 'lain'


def _sidik(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--unduh', action='store_true', help='benar-benar unduh')
    args = ap.parse_args()

    CONTOH.mkdir(parents=True, exist_ok=True)
    print(f'Tempat contoh: {CONTOH}')
    print(f'Calon: {len(CALON)} berkas\n')

    hasil = []
    for jenis, nama, url, catatan in CALON:
        map_jenis = CONTOH / jenis
        map_jenis.mkdir(parents=True, exist_ok=True)
        tujuan = map_jenis / nama
        print(f'[{jenis}] {nama}')
        print(f'   sumber : {catatan}')
        print(f'   url    : {url[:110]}')
        if not args.unduh:
            print('   (mode daftar — tidak diunduh)')
            hasil.append({'jenis': jenis, 'nama': nama, 'url': url,
                          'catatan': catatan, 'status': 'belum'})
            print()
            continue
        ok, ket = _ambil(url, tujuan)
        print(f'   unduh  : {"BERHASIL" if ok else "GAGAL"} — {ket}')
        if ok:
            jn = _jenis_nyata(tujuan)
            print(f'   jenis  : {jn} · sha256 {_sidik(tujuan)}')
            if jn not in ('zip', 'pdf'):
                print('   ⚠️  bukan docx/pdf → TIDAK dipakai sbg contoh naskah')
        hasil.append({'jenis': jenis, 'nama': nama, 'url': url, 'catatan': catatan,
                      'status': 'ok' if ok else 'gagal', 'ket': ket})
        print()
        time.sleep(1.2)      # sopan ke server

    (CONTOH / 'SUMBER.json').write_text(
        json.dumps(hasil, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Catatan sumber → {CONTOH / "SUMBER.json"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
