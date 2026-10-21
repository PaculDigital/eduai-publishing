#!/usr/bin/env python3
"""UNDUH 20-30 NASKAH NYATA untuk uji kedalaman peta halus (05Okt26).

Strategi: ambil dari repo yang TERBUKTI memberi hasil (unhas, unj,
uin-suska, walisongo) + cari juga kata kunci tesis/disertasi.
Setiap PDF diperiksa: benar-benar PDF & punya teks (bukan scan).
Hasil disimpan ke _contoh-dokumen/uji-kedalaman/ + SUMBER.json.
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent
KELUAR = AKAR / '_contoh-dokumen' / 'uji-kedalaman'
KELUAR.mkdir(parents=True, exist_ok=True)

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/151.0.0.0 Safari/537.36')

# repo + bentuk pencarian yang TERBUKTI jalan
PENCARIAN = [
    ('unhas', 'https://repository.unhas.ac.id/cgi/search?q={q}'),
    ('unj', 'http://repository.unj.ac.id/cgi/search?q={q}'),
    ('uin-suska', 'https://repository.uin-suska.ac.id/cgi/search?q={q}'),
    ('walisongo', 'https://eprints.walisongo.ac.id/cgi/search?q={q}'),
]
KATA = ['skripsi', 'tesis', 'disertasi', 'penelitian kuantitatif']


def ambil(url: str, biner: bool = False, timeout: int = 60):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read() if biner else r.read().decode('utf-8', 'ignore')
    except Exception as e:                                     # noqa: BLE001
        return f'__GALAT__{getattr(e, "code", type(e).__name__)}'


def cari_pdf(nama: str, pola: str, q: str) -> list[dict]:
    url = pola.format(q=urllib.parse.quote(q))
    h = ambil(url, timeout=45)
    if isinstance(h, str) and h.startswith('__GALAT__'):
        return []
    pdf = sorted(set(re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)))
    keluar = []
    for p in pdf:
        p2 = urllib.parse.urljoin(url, p)
        # skip sampul/cover/lampiran — cari yang ada teks isi
        if re.search(r'(cover|sampul|lampiran|halaman-judul)\.pdf', p2, re.I):
            continue
        keluar.append({'repo': nama, 'url': p2, 'dari': url, 'kata': q})
    return keluar


kandidat: list[dict] = []
for nama, pola in PENCARIAN:
    for q in KATA:
        r = cari_pdf(nama, pola, q)
        print(f'  {nama:12s} q="{q}" → {len(r)} pdf')
        kandidat += r
        time.sleep(0.4)

print(f'\n  kandidat mentah: {len(kandidat)}')

# buang duplikat URL
lihat, unik = set(), []
for k in kandidat:
    if k['url'] not in lihat:
        lihat.add(k['url'])
        unik.append(k)
print(f'  unik: {len(unik)}')


def unduh(k: dict) -> dict:
    data = ambil(k['url'], biner=True, timeout=120)
    if isinstance(data, str):
        return {**k, 'ok': False, 'sebab': data[9:]}
    if not data.startswith(b'%PDF'):
        return {**k, 'ok': False, 'sebab': f'bukan PDF ({data[:8]!r})'}
    if len(data) < 20_000:
        return {**k, 'ok': False, 'sebab': f'terlalu kecil ({len(data)} B)'}
    sid = hashlib.md5(data).hexdigest()[:10]
    nm = f"{k['repo']}-{k['kata'].replace(' ', '_')}-{sid}.pdf"
    (KELUAR / nm).write_bytes(data)
    return {**k, 'ok': True, 'berkas': nm, 'byte': len(data), 'md5': sid}


print('\n  ── mengunduh (paralel 5) ──')
with cf.ThreadPoolExecutor(max_workers=5) as ex:
    hasil = list(ex.map(unduh, unik[:120]))

ok = [h for h in hasil if h.get('ok')]
gagal = [h for h in hasil if not h.get('ok')]
print(f'  BERHASIL: {len(ok)}   gagal: {len(gagal)}')

# buang duplikat isi (md5 sama)
per_md5, bersih = {}, []
for h in ok:
    if h['md5'] not in per_md5:
        per_md5[h['md5']] = h
        bersih.append(h)
print(f'  unik isi : {len(bersih)}')

sudah = {s.get('md5') for s in json.loads(
    (KELUAR / 'SUMBER.json').read_text())} if (KELUAR / 'SUMBER.json').exists() else set()
catat = json.loads((KELUAR / 'SUMBER.json').read_text()) \
    if (KELUAR / 'SUMBER.json').exists() else []
for h in bersih:
    if h['md5'] in sudah:
        continue
    catat.append({'berkas': h['berkas'], 'url': h['url'], 'repo': h['repo'],
                  'kata': h['kata'], 'byte': h['byte'], 'md5': h['md5'],
                  'diunduh': time.strftime('%Y-%m-%d %H:%M:%S')})
(KELUAR / 'SUMBER.json').write_text(
    json.dumps(catat, ensure_ascii=False, indent=1))
print(f'  tercatat di SUMBER.json: {len(catat)}')
print(f'  folder: {KELUAR}')
