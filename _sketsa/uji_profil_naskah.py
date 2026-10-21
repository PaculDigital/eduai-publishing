#!/usr/bin/env python3
"""UJI PROFIL NASKAH + UNGGAH PANDUAN lewat HTTP produksi (26Sep26).

Grup:
  N1  sintaks JS modal (ekstrak → node --check / cek pola)
  N2  GET  profil-naskah → 200, blok_ai memuat aturan
  N3  POST unggah panduan (PDF pedoman ASLI) → sumber panduan_user
  N4  GET  lagi → sumber panduan_user + nama_panduan
  N5  POST hapus → kembali bawaan (DB dibersihkan)
Exit 0 = semua lulus. SEMUA lewat HTTP (bukan sentuh DB langsung),
kecuali membaca id berkas user uji (baca-saja).
"""
import json
import os
import re
import sqlite3
import sys
import urllib.request
import urllib.error
from http.cookiejar import CookieJar
from pathlib import Path

BASE = os.environ.get("BASE_UJI", "https://eduai.bikinaja.id")
KUKU = ("eduai_session", os.environ.get("TOKEN_UJI", ""))
FID_UJI = int(os.environ.get("FID_UJI", "0"))
PDF_PEDOMAN = Path("/opt/data/cache/documents") / (
    "doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN "
    "EDISI REVISI 2025.pdf")
DB = "/opt/data/services/eduai-publishing/data/eduai.db"

GAGAL = []


def ok(nama, syarat, detail=""):
    if syarat:
        print(f"  LULUS  {nama}")
    else:
        print(f"  GAGAL  {nama} {detail}")
        GAGAL.append(nama)


_jar = CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))
# Cloudflare Mblokir UA bawaan Python (error 1010) — pakai UA browser.
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
_OPENER.addheaders = [("User-Agent", _UA)]


def _kuki():
    import http.cookiejar as cj
    for nama, nilai in (KUKU,):
        _jar.set_cookie(cj.Cookie(
            version=0, name=nama, value=nilai, port=None,
            port_specified=False, domain="eduai.bikinaja.id",
            domain_specified=True, domain_initial_dot=False, path="/",
            path_specified=True, secure=False, expires=None, discard=True,
            comment=None, comment_url=None, rest={}, rfc2109=False))


def get(jalur):
    try:
        r = _OPENER.open(BASE + jalur, timeout=60)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        teks = e.read().decode()
        try:
            return e.code, json.loads(teks)
        except json.JSONDecodeError:
            return e.code, {"raw": teks[:300]}


def post_multipart(jalur, medan: dict, berkas: tuple | None):
    batas = "----ujiPanduan7x"
    bagian = []
    for k, v in medan.items():
        bagian.append(f"--{batas}\r\nContent-Disposition: form-data; "
                      f'name="{k}"\r\n\r\n{v}\r\n'.encode())
    if berkas:
        nama, isi, jenis = berkas
        bagian.append(f"--{batas}\r\nContent-Disposition: form-data; "
                      f'name="berkas"; filename="{nama}"\r\n'
                      f"Content-Type: {jenis}\r\n\r\n".encode() + isi + b"\r\n")
    bagian.append(f"--{batas}--\r\n".encode())
    badan = b"".join(bagian)
    req = urllib.request.Request(
        BASE + jalur, data=badan, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={batas}",
                 "User-Agent": _UA})
    try:
        r = _OPENER.open(req, timeout=120)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        teks = e.read().decode()
        try:
            return e.code, json.loads(teks)
        except json.JSONDecodeError:
            return e.code, {"raw": teks[:300]}


print("N1 — sintaks JS modal")
html = Path("/opt/data/services/eduai-publishing/app/templates/naskah.html").read_text(encoding="utf-8")
blok = re.search(r"/\* ═══ PROFIL NASKAH.*?</script>", html, re.S)
ok("blok JS ada", blok is not None)
if blok:
    js = blok.group(0).rsplit("</script>", 1)[0]
    import subprocess, shutil, tempfile, os
    if shutil.which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js); jp = f.name
        p = subprocess.run(["node", "--check", jp], capture_output=True, text=True)
        ok("node --check", p.returncode == 0, (p.stderr or "")[:300])
        os.unlink(jp)
    else:
        ok("node --check", False, "node tidak ada")
ok("tidak ada typo 'a.spasi isi'", "a.spasi isi" not in html)

_kuki()

print("N2 — GET profil-naskah")
FID = FID_UJI
ok("ada berkas user uji (env FID_UJI)", FID > 0, f"fid={FID}")

st, d = get(f"/api/ai/v1/profil-naskah?file_id={FID}")
ok("GET 200 + ok", st == 200 and d.get("ok") is True, f"st={st} d={str(d)[:200]}")
if d.get("ok"):
    # UJI IDEMPOTEN: lepaskan sisa panduan uji sebelumnya dulu, supaya
    # titik awal selalu "bawaan" apa pun kondisi DB sebelumnya.
    post_multipart("/api/ai/v1/profil-naskah/panduan/hapus",
                   {"file_id": str(FID)}, None)
    d = get(f"/api/ai/v1/profil-naskah?file_id={FID}")[1]
ok("blok_ai memuat aturan rata tengah", "RATA TENGAH" in (d.get("blok_ai") or ""))
ok("sumber awal = bawaan", d.get("sumber") == "bawaan", str(d.get("sumber")))
ok("aturan punya margin", (d.get("aturan") or {}).get("margin_cm", {}).get("kiri") == 4)
ok("profil ringkas ada (judul)", bool((d.get("profil") or {}).get("judul")))

print("N3 — POST unggah panduan (PDF pedoman ASLI)")
if PDF_PEDOMAN.exists() and FID:
    isi = PDF_PEDOMAN.read_bytes()
    st, d = post_multipart("/api/ai/v1/profil-naskah/panduan",
                           {"file_id": str(FID)},
                           (PDF_PEDOMAN.name, isi, "application/pdf"))
    ok("unggah ok", st == 200 and d.get("ok") is True, f"st={st} d={str(d)[:300]}")
    ok("sumber = panduan_user", d.get("sumber") == "panduan_user")
    ok("nama_panduan = asli", "PEDOMAN PENULISAN" in (d.get("nama_panduan") or ""),
       str(d.get("nama_panduan"))[:60])
    ok("ekstraksi dapat margin 4/3/4/3",
       (d.get("hasil") or {}).get("margin_cm", {}).get("atas") == 4.0,
       str((d.get("hasil") or {}).get("margin_cm")))
    ok("blok_ai ikut berubah (ada 'panduan_user')",
       "panduan penulisan yang diunggah user" in (d.get("blok_ai") or ""))
else:
    ok("PDF pedoman ada", False, str(PDF_PEDOMAN))

print("N4 — GET lagi (panduan tersimpan?)")
st, d = get(f"/api/ai/v1/profil-naskah?file_id={FID}")
ok("GET ok", st == 200 and d.get("ok") is True)
ok("sumber = panduan_user (tersimpan)", d.get("sumber") == "panduan_user",
   str(d.get("sumber")))
ok("nama_panduan tampil", bool(d.get("nama_panduan")))

print("N5 — POST hapus (bersihkan produksi)")
st, d = post_multipart("/api/ai/v1/profil-naskah/panduan/hapus",
                       {"file_id": str(FID)}, None)
ok("hapus ok", st == 200 and d.get("ok") is True, str(d)[:200])
ok("kembali bawaan", d.get("sumber") == "bawaan")

print()
print(f"HASIL: GAGAL={len(GAGAL)} {GAGAL if GAGAL else '— semua lulus'}")
sys.exit(1 if GAGAL else 0)
