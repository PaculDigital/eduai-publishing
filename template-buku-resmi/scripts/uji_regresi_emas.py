#!/usr/bin/env python3
"""BUKU EMAS + UJI REGRESI (barang 17 RENCANA-BANGUN-SSOT).

Setiap jenis punya buku emas: spec tetap yang hasilnya TIDAK BOLEH
berubah diam-diam. Sidik jari struktural disimpan di emas/<jenis>.json:
hash atas (gaya, teks) semua paragraf + hitungan isi. Paginasi SENGAJA
tidak masuk sidik jari — ia tergantung font mesin render; yang dijaga
di sini adalah ISI & STRUKTUR yang dihasilkan generator.

Pakai:
    python3 uji_regresi_emas.py            # bandingkan dengan emas
    python3 uji_regresi_emas.py --perbarui # tulis ulang emas (sengaja!)
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

SINI = Path(__file__).resolve().parent
EMAS = SINI / 'emas'
KASUS = [
    ('monograf', SINI / 'contoh_monograf.json',
     ['--profil', str(SINI.parent / 'jenis' / 'monograf' / 'profil.json'), '--tanpa-ukur']),
    ('induk', SINI / 'contoh_buku.json', ['--tanpa-gerbang']),
    ('ajar', SINI / 'contoh_ajar.json',
     ['--profil', str(SINI.parent / 'jenis' / 'buku-ajar-obe' / 'profil.json'), '--tanpa-ukur']),
    ('referensi', SINI / 'contoh_referensi.json',
     ['--profil', str(SINI.parent / 'jenis' / 'buku-referensi' / 'profil.json'), '--tanpa-ukur']),
]


def teks_para(p):
    return ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()


def gaya_para(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else ''


def sidik(path):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = [(gaya_para(p), teks_para(p))
             for p in re.findall(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', doc, re.S)]
    bahan = '\n'.join(f'{g}|{t}' for g, t in paras)
    return {
        'hash_paragraf': hashlib.sha256(bahan.encode('utf-8')).hexdigest(),
        'jumlah_paragraf': len(paras),
        'jumlah_kata': sum(len(t.split()) for _, t in paras if t),
        'jumlah_gambar': len(re.findall(r'<a:blip', doc)),
        'jumlah_tabel': len(re.findall(r'<w:tbl>', doc)),
    }


def bangun(nama, spec, ekstra, tmp):
    keluar = tmp / f'{nama}.docx'
    r = subprocess.run([sys.executable, str(SINI / 'buat_buku.py'),
                        str(spec), str(keluar), *ekstra],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  GAGAL bangun {nama}: {(r.stdout + r.stderr).strip().splitlines()[-1:]}')
        return None
    return sidik(keluar)


def main():
    perbarui = '--perbarui' in sys.argv
    EMAS.mkdir(exist_ok=True)
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix='emas-'))
    gagal = 0
    for nama, spec, ekstra in KASUS:
        s = bangun(nama, spec, ekstra, tmp)
        if s is None:
            gagal += 1
            continue
        berkas = EMAS / f'{nama}.json'
        if perbarui:
            berkas.write_text(json.dumps(s, indent=2), encoding='utf-8')
            print(f'  EMAS DITULIS  {nama}: {s["hash_paragraf"][:16]}… '
                  f'({s["jumlah_paragraf"]} paragraf, {s["jumlah_kata"]} kata)')
            continue
        if not berkas.exists():
            print(f'  GAGAL  {nama}: emas belum ada — jalankan --perbarui sekali')
            gagal += 1
            continue
        lama = json.loads(berkas.read_text(encoding='utf-8'))
        if lama == s:
            print(f'  LULUS  {nama}: sidik jari sama dengan emas')
        else:
            gagal += 1
            beda = {k: (lama.get(k), s.get(k)) for k in s if lama.get(k) != s.get(k)}
            print(f'  GAGAL  {nama}: berubah dari emas -> {beda}')
    print(f'\nRINGKAS REGRESI EMAS: {"GAGAL " + str(gagal) if gagal else "SEMUA SAMA"}')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
