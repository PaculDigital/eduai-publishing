#!/usr/bin/env python3
"""PERIKSA FONT: apakah font yang dituntut template terpasang?

Template hanya menyebut NAMA font; berkasnya hidup di mesin pembuka.
Script ini memeriksa 9 font wajib template di mesin ini (lewat fontconfig
`fc-list` bila ada + pindai folder font umum), atau di folder tertentu
lewat --folder (mis. folder font privat di server — TIDAK disalin ke repo).

Pakai:
    python3 periksa_font.py
    python3 periksa_font.py --folder /path/folder/font

EXIT 0 = semua ada, EXIT 1 = ada yang hilang.
Stdlib murni; fc-list dipakai bila tersedia (Linux/macOS fontconfig).
"""
import re
import subprocess
import sys
from pathlib import Path

FONT_WAJIB = {
    'Trajan Pro': 'judul bab & judul bagian (Heading1)',
    'Palatino Linotype': 'ISI BUKU (paling kritis)',
    'Adobe Garamond Pro': 'sampul',
    'Elephant': 'sampul / judul besar',
    'Digory Doodles': 'hiasan judul sampul',
    'Nyala': 'style Pa2/Pa5',
    'Calibri': 'eastAsia pendamping',
    'Times New Roman': 'style Normal (dasar)',
    'Roboto': 'elemen lain-lain',
}

FOLDER_UMUM = [Path.home() / '.fonts', Path.home() / '.local/share/fonts',
               Path('/usr/share/fonts'), Path('/usr/local/share/fonts'),
               Path('/Library/Fonts'), Path.home() / 'Library/Fonts',
               Path('C:/Windows/Fonts')]


def dari_fc_list(target=None):
    """Kembalikan {family_lower: contoh_path} dari fc-list."""
    hasil = {}
    cmd = ['fc-list']
    if target:
        cmd.append(str(target))
    cmd += [':', 'family', 'file']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return hasil
    for ln in r.stdout.splitlines():
        if ':' not in ln:
            continue
        berkas, fam = ln.split(':', 1)
        for nama in fam.split(','):
            hasil.setdefault(nama.strip().lower(), berkas.strip())
    return hasil


def dari_nama_berkas(folder):
    """Cadangan bila fc-list tidak ada: cocokkan nama berkas font."""
    hasil = {}
    if not folder or not Path(folder).exists():
        return hasil
    for b in Path(folder).rglob('*'):
        if b.suffix.lower() not in ('.ttf', '.otf', '.ttc'):
            continue
        slug = re.sub(r'[^a-z]', '', b.stem.lower())
        for nama in FONT_WAJIB:
            kunci = re.sub(r'[^a-z]', '', nama.lower())
            if kunci and kunci in slug:
                hasil.setdefault(nama.lower(), str(b))
    return hasil


def main():
    folder = None
    if '--folder' in sys.argv:
        i = sys.argv.index('--folder')
        folder = Path(sys.argv[i + 1])

    # --profil (barang 8): font wajib diambil dari profil jenis —
    # gerbang yang sama memeriksa font yang sungguh dipakai buku itu.
    font_wajib = FONT_WAJIB
    if '--profil' in sys.argv:
        import json
        i = sys.argv.index('--profil')
        profil = json.loads(Path(sys.argv[i + 1]).read_text(encoding='utf-8'))
        f = profil['format']
        font_wajib = {f['font_isi']['nama']: 'font isi (profil)'}
        if f.get('font_judul'):
            font_wajib[f['font_judul']['nama']] = 'font judul (profil)'
        print(f"PROFIL: {profil['id']}")

    terpasang = dari_fc_list(folder) if folder else dari_fc_list()
    if not folder:
        for f in FOLDER_UMUM:
            for k, v in dari_nama_berkas(f).items():
                terpasang.setdefault(k, v)
    if folder:
        for k, v in dari_nama_berkas(folder).items():
            terpasang.setdefault(k, v)

    print(f"SUMBER: {'folder ' + str(folder) if folder else 'mesin ini'}")
    hilang = []
    for nama, peran in font_wajib.items():
        lokasi = terpasang.get(nama.lower())
        if lokasi:
            print(f'  ADA     {nama:20s} {peran}  [{lokasi}]')
        else:
            hilang.append(nama)
            print(f'  HILANG  {nama:20s} {peran}')
    print(f'\nRINGKAS: {len(font_wajib) - len(hilang)}/{len(font_wajib)} font ada')
    if hilang:
        print('Yang hilang:', ', '.join(hilang))
        print('Cara memperoleh yang sah: lihat fonts/README.md')
    return 1 if hilang else 0


if __name__ == '__main__':
    sys.exit(main())
