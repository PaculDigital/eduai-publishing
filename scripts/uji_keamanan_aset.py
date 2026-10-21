#!/usr/bin/env python3
"""UJI KEAMANAN guard kondisional /oo/aset (WAJIB LULUS sebelum Cache Rule).

Diuji TANPA login sama sekali:
  1. aset mesin (sdkjs, web-apps)     -> HARUS 200 (boleh publik, untuk CF cache)
  2. dokumen mahasiswa (cache/files)  -> HARUS 303 /masuk (JANGAN bocor)
  3. kanal socket.io (doc/)           -> HARUS 303 /masuk
  4. path aneh (../)                  -> HARUS 400

Jalankan di container:
  docker cp scripts/uji_keamanan_aset.py eduai-app:/tmp/
  docker exec eduai-app python3 /tmp/uji_keamanan_aset.py
"""
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
V = "/9.4.0-3b37c3e6815d56e6b4740c638c7907f8"

HASIL = []


def ok(label, lulus, info=''):
    HASIL.append((label, lulus, info))
    print(f"  [{'LULUS' if lulus else 'GAGAL'}] {label} {info}")


class TanpaRedirect(urllib.request.HTTPRedirectHandler):
    """Blokir redirect otomatis: kita mau LIHAT 303, bukan mengikutinya."""

    def redirect_request(self, *a, **k):
        return None


opener = urllib.request.build_opener(TanpaRedirect)


def cek(path):
    """Ambil tanpa cookie. Kembalikan (kode, lokasi)."""
    rq = urllib.request.Request(BASE + path,
                                headers={'Accept-Encoding': 'gzip'})
    try:
        r = opener.open(rq, timeout=60)
        return r.status, r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Location', '')


print("=" * 74)
print("UJI KEAMANAN — TANPA LOGIN SAMA SEKALI")
print("=" * 74)

print("\n── 1. ASET MESIN EDITOR (boleh publik, ini tujuan OOpsi B) ──")
for p, nama in [
    (f"/oo/aset{V}/sdkjs/word/sdk-all.js", "sdk-all.js (4,5 MB)"),
    (f"/oo/aset{V}/web-apps/apps/api/documents/api.js", "api.js"),
    (f"/oo/aset{V}/sdkjs/common/AllFonts.js", "AllFonts.js"),
    ("/oo/aset/web-apps/apps/api/documents/api.js", "api.js (tanpa versi)"),
    (f"/oo/aset{V}/themes.json", "themes.json"),
]:
    kode, lok = cek(p)
    ok(f"aset publik: {nama}", kode == 200, f"(HTTP {kode})")

print("\n── 2. DOKUMEN MAHASISWA (WAJIB 303, jangan bocor!) ──")
for p in [
    "/oo/aset/cache/files/data/uji123/Editor.bin/Editor.bin",
    "/oo/aset/cache/files/data/uji123/origin.docx/origin.docx",
    "/oo/aset/cache/files/1/output.docx/output.docx",
]:
    kode, lok = cek(p)
    ok(f"dokumen ditolak: {p.split('/')[-1]}",
       kode in (303, 302, 401, 403), f"(HTTP {kode} -> {lok or '-'})")

print("\n── 3. KANAL SOCKET.IO (wajib login juga) ──")
kode, lok = cek(f"/oo/aset{V}/doc/uji123/c/?shardkey=uji123&EIO=4&transport=polling")
ok("socket.io ditolak tanpa login", kode in (303, 302, 401, 403),
   f"(HTTP {kode} -> {lok or '-'})")

print("\n── 4. PATH TIDAK SAH ──")
kode, _ = cek("/oo/aset/../../etc/passwd")
ok("path traversal ditolak", kode in (400, 404), f"(HTTP {kode})")

print("\n" + "=" * 74)
lulus = sum(1 for _, l, _ in HASIL if l)
print(f"HASIL: {lulus} LULUS, {len(HASIL)-lulus} GAGAL")
print("=" * 74)
