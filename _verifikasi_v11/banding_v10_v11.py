"""Bandingkan v10 (tahap 1) vs v11 (tahap 5) per naskah uji.

Normalisasi 4 skema hasil_latih_grup1-4.json (v10) lawan
hasil_verifikasi_v11_*.json (v11). Tanpa Jev, tanpa label manusia baru.
Keluaran: tabel per kode + cek deterministik klaim v11.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
from ukur_skor_teks import norm  # noqa: E402


def norm_v10(e):
    """Kembalikan dict seragam dari satu entri v10 (grup 1-4)."""
    lab = e.get('label') or {}
    if isinstance(lab, dict):
        lab = {k: v for k, v in lab.items()}
    bab_label = e.get('bab_label') or e.get('bab_judul_label') or []
    bab_gabung = e.get('bab_gabung') or e.get('bab_judul_gabung') or e.get('bab_judul') or []
    if isinstance(bab_gabung, str):
        bab_gabung = [bab_gabung]
    panggilan = e.get('panggilan_total')
    if panggilan is None:
        panggilan = (e.get('panggilan_petakan_total') or 0) + \
            (e.get('panggilan_hakim_total') or e.get('hakim_panggilan_jev') or 0) + \
            (e.get('panggilan_probe_total') or 0)
    return {
        'kode': e['kode'],
        'panggilan': panggilan,
        'goyang': e.get('goyang_jml'),
        'label': dict(lab),
        'bab_label': list(bab_label),
        'bab_gabung': list(bab_gabung),
        'bab_semua': list(bab_label) + list(bab_gabung),
        'label_penuh': e.get('label_penuh'),
        'baris': e.get('baris'),
        'gabung': e.get('gabung') or e.get('gabung_penuh'),
    }


def muat_v10():
    out = {}
    for g in (1, 2, 3, 4):
        d = json.load(open(ROOT / ('hasil_latih_grup%d.json' % g), encoding='utf-8'))
        for e in d['entri']:
            out[e['kode']] = norm_v10(e)
    return out


def muat_v11():
    out = {}
    for tag in ('A', 'B', 'C', 'D', 'SMOKE2'):
        p = ROOT / '_verifikasi_v11' / ('hasil_verifikasi_v11_%s.json' % tag)
        if not p.exists():
            continue
        d = json.load(open(p, encoding='utf-8'))
        for e in d['entri']:
            out[e['kode']] = e
    return out


GARBAGE = [
    (r'^\s*:', 'awal titik-dua (fragmen daftar isi/kepala)'),
    (r'\?{3,}', 'tanda tanya beruntun (nomor halaman daftar isi)'),
    (r'^BAB\s+[IVX]+\s*$', 'BAB tanpa judul'),
    (r'^BAB\s+\d+\s*$', 'BAB angka tanpa judul'),
    (r'^BABV$', 'BABV tanpa spasi'),
    (r'^\d+$', 'angka saja'),
    (r'^BAB\s+[IVX]+$', 'BAB romawi tanpa judul'),
    (r'Berisi tentang', 'deskripsi sistematika'),
    (r'Pada bab ini dijelaskan', 'deskripsi sistematika'),
    (r'meliputi\s*:', 'deskripsi sistematika'),
    (r'TABLE OF CONTENS', 'daftar isi Inggris (salah eja)'),
    (r'^CHAPTER [IVX]+:', 'duplikat daftar isi CHAPTER'),
]


def klasifikasi_bab(judul):
    for pola, alasan in GARBAGE:
        if re.search(pola, judul):
            return ('sampah', alasan)
    return ('bersih', '')


def cek_baris_v11(e):
    """Cek deterministik pada baris v11: pemisah/BOM/judul sampah."""
    baris = e.get('baris') or []
    label = {int(k): v for k, v in (e.get('label_penuh') or {}).items()}
    pemisah = [i for i, b in enumerate(baris) if b.strip().startswith('=====')]
    pemisah_bab = [i for i in pemisah if label.get(i) == 'bab']
    bom = [i for i, b in enumerate(baris) if '\ufeff' in b]
    bom_bab = [i for i in bom if label.get(i) == 'bab']
    gabung = e.get('gabung_penuh') or {}
    bom_gabung = [k for k, v in gabung.items()
                  if any('\ufeff' in str(x) for x in v)]
    return {
        'pemisah_jml': len(pemisah), 'pemisah_bab_jml': len(pemisah_bab),
        'bom_baris_jml': len(bom), 'bom_bab_jml': len(bom_bab),
        'bom_gabung_jml': len(bom_gabung),
        'pemisah_bab_contoh': [baris[i][:60] for i in pemisah_bab[:3]],
    }


def main():
    v10 = muat_v10()
    v11 = muat_v11()
    kodes = sorted(v11)
    print('naskah v11: %d | v10 tersedia: %d' % (len(kodes), len(v10)))
    print()
    print('%-5s %6s %6s | %6s %6s | %5s %5s %5s | %5s %5s %5s | %4s %4s %4s'
          % ('kode', 'pang10', 'pang11', 'goy10', 'goy11', 'bab10',
             'sub10', 'par10', 'bab11', 'sub11', 'par11', 'bs10', 'bs11',
             'smph'))
    tot10 = tot11 = 0
    for k in kodes:
        a = v10.get(k)
        b = v11[k]
        lab10 = a['label'] if a else {}
        lab11 = b['label']
        bs10 = len(a['bab_semua']) if a else -1
        bs11 = len(b['bab_semua'])
        sampah11 = sum(1 for t in b['bab_semua']
                       if klasifikasi_bab(t)[0] == 'sampah')
        tot10 += a['panggilan'] if a else 0
        tot11 += b['panggilan_total']
        print('%-5s %6s %6d | %6s %6d | %5s %5s %5s | %5s %5s %5s | %4s %4d %4d'
              % (k, a['panggilan'] if a else '?', b['panggilan_total'],
                 a['goyang'] if a else '?', b['goyang_jml'],
                 lab10.get('bab', '?'), lab10.get('subbab', '?'),
                 lab10.get('paragraf', '?'),
                 lab11.get('bab', 0), lab11.get('subbab', 0),
                 lab11.get('paragraf', 0),
                 bs10, bs11, sampah11))
    print('TOTAL panggilan v10=%s v11=%d (hanya kode yang sudah jalan v11)'
          % (tot10, tot11))
    print()
    print('=== KLAIM DETERMINISTIK v11 ===')
    for k in kodes:
        b = v11[k]
        a = v10.get(k)
        cek = cek_baris_v11(b)
        sampah = [(t, klasifikasi_bab(t)[1]) for t in b['bab_semua']
                  if klasifikasi_bab(t)[0] == 'sampah']
        print('%s profil=%s bom=%d pemisah=%d | baris: pemisah=%d (bab:%d) '
              'bom=%d (bab:%d, gabung:%d) | bab_semua=%d sampah=%d %s'
              % (k, b['profil_bentuk']['penomoran_bab'],
                 b['profil_bentuk'].get('bom_jml'),
                 b['profil_bentuk'].get('pemisah_gabung_jml'),
                 cek['pemisah_jml'], cek['pemisah_bab_jml'],
                 cek['bom_baris_jml'], cek['bom_bab_jml'],
                 cek['bom_gabung_jml'], len(b['bab_semua']), len(sampah),
                 sampah[:4]))
        if a:
            sampah10 = [(t, klasifikasi_bab(t)[1]) for t in a['bab_semua']
                        if klasifikasi_bab(t)[0] == 'sampah']
            print('    v10 bab_semua=%d sampah=%d %s'
                  % (len(a['bab_semua']), len(sampah10), sampah10[:6]))
    print()
    print('=== BEDA LABEL PER BARIS v10 vs v11 (hanya grup3, label_penuh ada) ===')
    for k in kodes:
        a = v10.get(k)
        b = v11[k]
        if not a or not a.get('label_penuh') or not b.get('label_penuh'):
            continue
        l10 = {int(i): v for i, v in a['label_penuh'].items()}
        l11 = {int(i): v for i, v in b['label_penuh'].items()}
        beda = Counter()
        for i in sorted(set(l10) | set(l11)):
            x, y = l10.get(i), l11.get(i)
            if x != y:
                beda[(x, y)] += 1
        print('%s: indeks sama %d | beda %d %s'
              % (k, len(set(l10) & set(l11)), sum(beda.values()),
                 dict(beda)))


if __name__ == '__main__':
    main()
