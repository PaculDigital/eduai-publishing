#!/usr/bin/env python3
"""UJI TAHAP 1: apakah browser benar-benar menerima judul 'EduAi INOVASI - Editor'?

Diuji dari DALAM container (network berbeda dari host) via domain publik.
PENTING: kirim Accept-Encoding: gzip supaya nginx menyajikan berkas .gz —
itu yang akan diterima browser sungguhan.
"""
import gzip
import urllib.request

BASE = 'https://eduai.bikinaja.id'
FILES = [
    '/oo/aset/9.4.0-3b37c3e6815d56e6b4740c638c7907f8/web-apps/apps/api/documents/preload.html',
    '/oo/aset/9.4.0-3b37c3e6815d56e6b4740c638c7907f8/web-apps/apps/api/documents/cache-scripts.html',
]


def ambil(url, gzip_ok=True):
    h = {'User-Agent': 'Mozilla/5.0 (Chrome/151)'}
    if gzip_ok:
        h['Accept-Encoding'] = 'gzip, deflate'
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            jml = r.read()
            enc = r.headers.get('Content-Encoding', '-')
            if enc == 'gzip':
                try:
                    jml = gzip.decompress(jml)
                except Exception:
                    pass
            return r.status, enc, jml.decode('utf-8', 'replace')
    except Exception as e:
        return None, str(e), ''


print("=" * 76)
print("UJI TAHAP 1 — JUDUL TAB (dari dalam container, via domain publik)")
print("=" * 76)

lulus = gagal = 0
for f in FILES:
    nama = f.split('/')[-1]
    for mode, gz in (('gzip (seperti browser)', True), ('tanpa gzip', False)):
        st, enc, isi = ambil(f'{BASE}{f}', gz)
        judul = '-'
        if '<title>' in isi:
            judul = isi.split('<title>')[1].split('</title>')[0]
        masih_oo = 'ONLYOFFICE' in judul.upper()
        ok = (judul == 'EduAi INOVASI - Editor')
        print(f"\n── {nama}  [{mode}]")
        print(f"   HTTP {st} | enc={enc}")
        print(f"   judul: '{judul}'")
        if ok:
            print(f"   ✅ BENAR")
            lulus += 1
        elif masih_oo:
            print(f"   ❌ MASIH 'ONLYOFFICE'")
            gagal += 1
        else:
            print(f"   ⚠️ judul tidak dikenal")
            gagal += 1

print("\n" + "=" * 76)
print(f"HASIL: {lulus} LULUS, {gagal} GAGAL")
print("=" * 76)
