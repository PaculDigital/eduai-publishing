#!/usr/bin/env python3
"""CARI PDF naskah di repository kampus yang HIDUP (05Okt26).

Menguji beberapa bentuk URL pencarian tiap repo, lalu kumpulkan tautan PDF.
Tidak mengunduh PDF-nya di sini — hanya MENGUMPULKAN KANDIDAT + memeriksa
bahwa tautannya benar-benar PDF (bukan halaman HTML).
"""
import concurrent.futures as cf
import json
import re
import sys
import urllib.parse
import urllib.request

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/151.0.0.0 Safari/537.36')

# (host, bentuk URL pencarian) — bentuk khas eprints: /cgi/search?q=
SEARCH = {
    'repository.unhas.ac.id': 'https://repository.unhas.ac.id/cgi/search?q={q}',
    'repository.unmul.ac.id': ('http://repository.unmul.ac.id/cgi/search?q={q}'),
    'etd.repository.ugm.ac.id': ('https://etd.repository.ugm.ac.id/penelitian/'
                                 'index?judul={q}'),
    'repository.unj.ac.id': 'http://repository.unj.ac.id/cgi/search?q={q}',
    'repository.ipb.ac.id': 'https://repository.ipb.ac.id/cgi/search?q={q}',
    'repository.undip.ac.id': 'https://repository.undip.ac.id/cgi/search?q={q}',
    'repository.uin-suska.ac.id': ('https://repository.uin-suska.ac.id/'
                                   'cgi/search?q={q}'),
    'digilib.uns.ac.id': 'https://digilib.uns.ac.id/search?q={q}',
    'eprints.ums.ac.id': 'https://eprints.ums.ac.id/cgi/search?q={q}',
    'eprints.walisongo.ac.id': 'https://eprints.walisongo.ac.id/cgi/search?q={q}',
    'repository.uinjkt.ac.id': ('https://repository.uinjkt.ac.id/'
                                'cgi/search?q={q}'),
}

q = sys.argv[1] if len(sys.argv) > 1 else 'skripsi'


def ambil(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode('utf-8', 'ignore')
    except Exception as e:                                     # noqa: BLE001
        return f'__GALAT__{getattr(e, "code", type(e).__name__)}'


def periksa(host: str, pola: str) -> dict:
    url = pola.format(q=urllib.parse.quote(q))
    h = ambil(url)
    if h.startswith('__GALAT__'):
        return {'host': host, 'url': url, 'galat': h[9:], 'pdf': [], 'eprint': []}
    pdf = sorted(set(re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)))
    ep = sorted(set(re.findall(
        r'href="(https?://[^"]*/(?:id/eprint|eprints)/\d+[^"]*)"', h, re.I)))
    return {'host': host, 'url': url, 'galat': '',
            'pdf': [urllib.parse.urljoin(url, p) for p in pdf][:40],
            'eprint': ep[:40]}


with cf.ThreadPoolExecutor(max_workers=6) as ex:
    hasil = list(ex.map(lambda kv: periksa(*kv), SEARCH.items()))

ringkas = {}
for r in hasil:
    tanda = '❌' if r['galat'] else ('✅' if (r['pdf'] or r['eprint']) else '⚠️ ')
    print(f"  {tanda} {r['host']:30s} pdf={len(r['pdf']):3d} eprint={len(r['eprint']):3d}"
          f" {('GALAT ' + r['galat']) if r['galat'] else ''}")
    if r['pdf'] or r['eprint']:
        ringkas[r['host']] = r
        for p in r['pdf'][:3]:
            print(f'        PDF  {p[:130]}')
        for p in r['eprint'][:3]:
            print(f'        EP   {p[:130]}')

with open('/tmp/kandidat_pdf.json', 'w') as f:
    json.dump(ringkas, f, ensure_ascii=False)
print(f'\n  repo dengan hasil: {len(ringkas)}  → /tmp/kandidat_pdf.json')
