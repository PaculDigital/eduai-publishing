#!/usr/bin/env python3
"""GATE CEK KEMIRIPAN (barang 11 RENCANA-BANGUN-SSOT).

Cek plagiarisme LOKAL yang terukur — BUKAN Turnitin dan tidak mengaku
setara Turnitin (basis data pembandingnya hanya buku itu sendiri +
korpus lokal yang diberikan). Yang diperiksa:
  K1 paragraf ganda persis di dalam buku (normalisasi kata, >= 30 kata).
  K2 paragraf nyaris sama (irisan 8-gram antar paragraf >= 50%).
  K3 (bila --korpus diberikan) irisan 8-gram buku dengan korpus luar;
     GAGAL bila >= 5% dari seluruh 8-gram buku.

Pakai:
    python3 cek_kemiripan.py buku.docx [--korpus folder/teks]
EXIT 0 = bersih pada batas ukur ini, 1 = ada temuan.
"""
import html
import re
import sys
import zipfile
from pathlib import Path

LULUS = GAGAL = 0
NGRAM = 8


def ok(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  -> {info}' if info else ''))


def teks_para(p):
    return html.unescape(''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p))).strip()


def gaya_para(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else ''


def kata(teks):
    return re.findall(r'[a-z0-9]+', teks.lower())


def ngram(kata_list, n=NGRAM):
    return {' '.join(kata_list[i:i + n]) for i in range(len(kata_list) - n + 1)}


def paragraf_isi(path):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = [(gaya_para(p), teks_para(p))
             for p in re.findall(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', doc, re.S)]
    i_bab = next((i for i, (g, t) in enumerate(paras)
                  if g == 'Heading1' and t.upper().startswith('BAB ')), 0)
    i_dp = next((i for i, (g, t) in enumerate(paras)
                 if g == 'Heading1' and t.upper() == 'DAFTAR PUSTAKA'), len(paras))
    return [t for _, t in paras[i_bab:i_dp] if len(kata(t)) >= 30]


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not arg:
        sys.exit(__doc__)
    path = Path(arg[0])
    paras = paragraf_isi(path)
    print(f'BERKAS: {path}')
    print(f'{len(paras)} paragraf isi (>= 30 kata) diperiksa')

    norm = [' '.join(kata(t)) for t in paras]
    ganda = [(i, j) for i in range(len(norm)) for j in range(i + 1, len(norm))
             if norm[i] == norm[j]]
    ok(f'K1 tidak ada paragraf ganda persis ({len(paras)} paragraf)',
       not ganda, f'pasangan ganda: {ganda[:3]}')

    gram = [ngram(kata(t)) for t in paras]
    nyaris = []
    for i in range(len(paras)):
        for j in range(i + 1, len(paras)):
            if not gram[i] or not gram[j]:
                continue
            irisan = len(gram[i] & gram[j]) / min(len(gram[i]), len(gram[j]))
            if irisan >= 0.5:
                nyaris.append((i, j, round(irisan, 2)))
    ok('K2 tidak ada paragraf nyaris sama (irisan 8-gram >= 50%)',
       not nyaris, f'nyaris sama: {nyaris[:3]}')

    korpus_path = next((a.split('=', 1)[1] for a in sys.argv[1:]
                        if a.startswith('--korpus=')), None)
    if korpus_path:
        sumber = {}
        for berkas in sorted(Path(korpus_path).rglob('*')):
            if berkas.suffix.lower() in ('.txt', '.md'):
                g = ngram(kata(berkas.read_text(encoding='utf-8', errors='ignore')))
            elif berkas.suffix.lower() == '.docx':
                g = set()
                for t in paragraf_isi(berkas):
                    g |= ngram(kata(t))
            else:
                continue
            if g:
                sumber[str(berkas)] = g
        semua_buku = set().union(*gram) if gram else set()
        total = len(semua_buku)
        tertangkap = set()
        for nama, g in sumber.items():
            tertangkap |= (semua_buku & g)
        rasio = (len(tertangkap) / total) if total else 0
        ok(f'K3 irisan korpus {rasio:.1%} < 5% ({len(tertangkap)}/{total} 8-gram, '
           f'{len(sumber)} berkas korpus)', rasio < 0.05,
           f'irisan {rasio:.1%} — periksa sumbernya')

    print(f'\nRINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
