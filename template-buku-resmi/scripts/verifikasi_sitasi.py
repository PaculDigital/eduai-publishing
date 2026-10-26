#!/usr/bin/env python3
"""VERIFIKASI SITASI 3 LAPIS (barang 12 RENCANA-BANGUN-SSOT).

Mengikuti aturan skill buku-referensi (verifikasi anti-halusinasi):
  LAPIS 1 EKSISTENSI  — referensi benar ada? Diperiksa ke Crossref:
            DOI persis bila entri memuat DOI; selain itu pencarian
            bibliografis (judul + penulis + tahun).
  LAPIS 2 ATRIBUSI    — penulis pertama & tahun di Crossref COCOK
            dengan entri? Beda = entri tertukar / dikarang.
  LAPIS 3 MAKNA       — TIDAK bisa dimesinkan. Skrip menyiapkan bahan
            peninjau: kalimat-kalimat di buku yang memakai tiap sitasi,
            supaya peninjau memeriksa makna tanpa berburu dari nol.

Status per entri: TERBUKTI / TIDAK-DITEMUKAN / PERLU-MANUAL.
EXIT 1 hanya bila ada DOI persis yang Crossref nyatakan TIDAK ADA
(bukti kuat karangan). Hasil pencarian judul yang nihil = peringatan.

Pakai:
    python3 verifikasi_sitasi.py buku.docx
"""
import json
import html
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def teks_para(p):
    return html.unescape(''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p))).strip()


def gaya_para(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else ''


def ambil_bagian(path):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = [(gaya_para(p), teks_para(p))
             for p in re.findall(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', doc, re.S)]
    i_dp = next((i for i, (g, t) in enumerate(paras)
                 if g == 'Heading1' and t.upper() == 'DAFTAR PUSTAKA'), None)
    i_pen = next((i for i, (g, t) in enumerate(paras)
                  if g == 'Heading1' and t.upper().startswith('TENTANG PENULIS')), len(paras))
    i_bab = next((i for i, (g, t) in enumerate(paras)
                  if g == 'Heading1' and t.upper().startswith('BAB ')), 0)
    entri = [t for _, t in paras[i_dp + 1:i_pen] if t] if i_dp is not None else []
    isi = ' '.join(t for _, t in paras[i_bab:i_dp]) if i_dp is not None else ''
    return entri, isi


def parse_entri(e):
    m = re.search(r'\((\d{4})[a-z]?\)', e)
    tahun = m.group(1) if m else ''
    judul = ''
    if m:
        sisa = e[m.end():].strip().lstrip('.').strip()
        judul = sisa.split('.')[0].strip()
    nama = re.findall(r"[A-Z][a-zA-Z'\-]{2,}", e[:m.start()] if m else e)
    doi = re.search(r'10\.\d{4,}/[^\s]+', e)
    return {'nama': nama[0].lower() if nama else '', 'tahun': tahun,
            'judul': judul, 'doi': doi.group(0).rstrip('.') if doi else ''}


def crossref(url):
    req = urllib.request.Request(
        url, headers={'User-Agent': 'EduAiVerifikasiSitasi/1.0 (mailto:admin@bikinaja.id)'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def kemiripan_judul(a, b):
    ka = set(re.findall(r'[a-z0-9]+', a.lower()))
    kb = set(re.findall(r'[a-z0-9]+', b.lower()))
    return len(ka & kb) / max(1, len(ka | kb))


def periksa_entri(e):
    info = parse_entri(e)
    if info['doi']:
        try:
            d = crossref(f"https://api.crossref.org/works/{urllib.parse.quote(info['doi'], safe='')}")
            msg = d['message']
            tahun_cr = str(((msg.get('issued') or {}).get('date-parts') or [['']])[0][0])
            penulis_cr = ((msg.get('author') or [{}])[0].get('family') or '').lower()
            cocok = (tahun_cr == info['tahun'] and penulis_cr == info['nama'])
            return ('TERBUKTI' if cocok else 'TERBUKTI-ADA-ATRIBUSI-BEDA',
                    f"DOI {info['doi']} ada di Crossref; tahun {tahun_cr}, penulis {penulis_cr}")
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                return ('TIDAK-DITEMUKAN', f"DOI {info['doi']} TIDAK ADA di Crossref (404)")
            return ('PERLU-MANUAL', f'Crossref menjawab HTTP {ex.code}')
        except Exception as ex:
            return ('PERLU-MANUAL', f'jaringan: {ex}')
    if info['judul'] and info['nama']:
        q = urllib.parse.urlencode({
            'query.bibliographic': f"{info['judul']} {info['nama']}",
            'rows': 1})
        try:
            d = crossref(f'https://api.crossref.org/works?{q}')
            items = d['message']['items']
            if not items:
                return ('PERLU-MANUAL', 'pencarian Crossref nihil — periksa manual')
            it = items[0]
            judul_cr = (it.get('title') or [''])[0]
            skor = kemiripan_judul(info['judul'], judul_cr)
            tahun_cr = str(((it.get('issued') or {}).get('date-parts') or [['']])[0][0])
            penulis_cr = ((it.get('author') or [{}])[0].get('family') or '').lower()
            if skor >= 0.5 and tahun_cr == info['tahun'] and penulis_cr == info['nama']:
                return ('TERBUKTI', f'judul mirip {skor:.0%}, tahun & penulis cocok')
            return ('PERLU-MANUAL',
                    f'calon teratas mirip {skor:.0%}, tahun {tahun_cr}, penulis {penulis_cr} — vonis manual')
        except Exception as ex:
            return ('PERLU-MANUAL', f'jaringan: {ex}')
    return ('PERLU-MANUAL', 'entri tanpa DOI & judul tak terbaca — periksa manual')


def kalimat_pemakai(isi, info):
    if not info['nama'] or not info['tahun']:
        return []
    pola = re.compile(rf"[^.]*(?:{re.escape(info['nama'])}[^.]{{0,60}}?{info['tahun']}|"
                      rf"\([^)]*{re.escape(info['nama'])}[^)]*{info['tahun']})[^.]*\.",
                      re.I)
    return [m.group(0).strip()[:220] for m in pola.finditer(isi)][:2]


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not arg:
        sys.exit(__doc__)
    entri, isi = ambil_bagian(Path(arg[0]))
    print(f'BERKAS: {arg[0]}')
    print(f'{len(entri)} entri pustaka diperiksa (Crossref)\n')
    gagal_keras = 0
    for e in entri:
        status, ket = periksa_entri(e)
        if status == 'TIDAK-DITEMUKAN':
            gagal_keras += 1
        print(f'  [{status}] {e[:72]}')
        print(f'      lapis 1-2: {ket}')
        info = parse_entri(e)
        for k in kalimat_pemakai(isi, info):
            print(f'      lapis 3 (makna, untuk peninjau): "{k}..."')
    print(f'\nRINGKAS: {len(entri)} entri | TIDAK-DITEMUKAN: {gagal_keras}')
    return 1 if gagal_keras else 0


if __name__ == '__main__':
    sys.exit(main())
