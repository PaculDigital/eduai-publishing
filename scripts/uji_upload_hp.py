#!/usr/bin/env python3
"""Verifikasi FIX upload dokumen di HP (12Sep26).

Masalah: di HP, klik area upload -> muncul KAMERA/GALERI, bukan File Manager.
Sebab: (1) accept cuma ekstensi tanpa MIME type, (2) double-trigger label+JS,
(3) input display:none.

Uji live via domain produksi:
  1. HTML ter-deploy memuat accept dengan MIME type
  2. Tidak ada double-trigger (preventDefault ada)
  3. Input tidak display:none
  4. ACCEPT vs EKSTENSI_DIIZINKAN BE sinkron
  5. /unggah benar-benar menerima file .docx (uji unggah nyata)
  6. /unggah menolak ekstensi terlarang
"""
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "https://eduai.bikinaja.id"
UA = ("Mozilla/5.0 (Linux; Android 13; SM-A536E) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36")
EMAIL = "qris.uji@eduai.local"
PWD = "rahasia123"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class Sesi:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj), NoRedirect())

    def get(self, path):
        r = urllib.request.Request(BASE + path,
                                   headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        try:
            resp = self.op.open(r, timeout=20)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def post(self, path, data):
        body = urllib.parse.urlencode(data).encode()
        r = urllib.request.Request(BASE + path, data=body,
                                   headers={"Content-Type": "application/x-www-form-urlencoded",
                                            "User-Agent": UA}, method="POST")
        try:
            resp = self.op.open(r, timeout=20)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def post_multipart(self, path, field, filename, content):
        """Unggah multipart/form-data manual."""
        boundary = "----WulanBoundary" + str(abs(hash(filename)) % 10**12)
        body = io.BytesIO()
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{field}"; '
                   f'filename="{filename}"\r\n'.encode())
        body.write(b"Content-Type: application/octet-stream\r\n\r\n")
        body.write(content)
        body.write(f"\r\n--{boundary}--\r\n".encode())
        r = urllib.request.Request(
            BASE + path, data=body.getvalue(),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                     "User-Agent": UA}, method="POST")
        try:
            resp = self.op.open(r, timeout=30)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")


def main():
    print("=" * 72)
    print("VERIFIKASI FIX UPLOAD DOKUMEN DI HP")
    print(f"BASE = {BASE}")
    print(f"UA   = Android Chrome (mensimulasikan HP)")
    print("=" * 72)

    # ---- login ----
    s = Sesi()
    st, _ = s.post("/masuk", {"email": EMAIL, "password": PWD})
    print(f"\n[0] Login: status={st}")

    st, html = s.get("/naskah")
    check("/naskah -> 200", st == 200, f"status={st}")
    if st != 200:
        print("STOP — tidak bisa ambil halaman")
        sys.exit(1)

    # ---- 1. accept pakai MIME type ----
    print("\n[1] accept attribute")
    m = re.search(r'<input[^>]*type="file"[^>]*accept="([^"]+)"', html, re.S)
    check("tag input file ditemukan", bool(m))
    acc = m.group(1) if m else ""
    check("ada MIME application/pdf", "application/pdf" in acc)
    check("ada MIME docx",
          "wordprocessingml.document" in acc)
    check("ada MIME xlsx", "spreadsheetml.sheet" in acc)
    check("ada MIME pptx", "presentationml.presentation" in acc)
    check("ada image/* (gambar tetap didukung)", "image/*" in acc)
    print(f"    accept = {acc[:110]}...")

    # ---- 2. tidak double-trigger ----
    print("\n[2] Perbaikan double-trigger")
    check("preventDefault() ada di handler zon",
          "e.preventDefault();      // cegah label memicu input kedua kali" in html
          or "cegah label memicu input kedua kali" in html)

    # ---- 3. input tidak display:none ----
    print("\n[3] Input tidak display:none")
    check("rule '.zon input{display:none}' SUDAH HILANG",
          ".zon input{display:none}" not in html.replace(" ", ""))
    check("pakai teknik visually-hidden", "clip:rect(0 0 0 0)" in html or "clip: rect(0 0 0 0)" in html)

    # ---- 4. validasi klien ----
    print("\n[4] Validasi sisi klien")
    check("validasi ekstensi klien ada", "const IZIN = [" in html)
    check("validasi ukuran klien ada", "const MAXMB = 25" in html)

    # ---- 5. UJI UNGGUH NYATA: docx ----
    print("\n[5] UJI NYATA: unggah .docx")
    # docx minimal (zip valid)
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/content-types"><Default Extension="xml" '
                   'ContentType="application/xml"/></Types>')
    st, body = s.post_multipart("/unggah", "berkas", "uji_dokumen.docx", buf.getvalue())
    print(f"    status={st} body={body[:160]}")
    try:
        j = json.loads(body)
        check(".docx DITERIMA server", j.get("ok") is True,
              f"pesan={j.get('pesan')}")
    except Exception as e:
        check(".docx DITERIMA server", False, f"respons bukan JSON: {e}")

    # ---- 6. tolak ekstensi terlarang ----
    print("\n[6] UJI NYATA: tolak ekstensi terlarang (.exe)")
    st, body = s.post_multipart("/unggah", "berkas", "jahat.exe", b"MZ\x90\x00")
    print(f"    status={st} body={body[:160]}")
    try:
        j = json.loads(body)
        check(".exe DITOLAK server", j.get("ok") is False, f"pesan={j.get('pesan')}")
    except Exception as e:
        check(".exe DITOLAK server", False, f"{e}")

    # ---- 7. sinkron FE vs BE ----
    print("\n[7] Sinkronisasi ACCEPT (FE) vs EKSTENSI_DIIZINKAN (BE)")
    eks_f = set(re.findall(r'\.([a-z0-9]{2,5})(?=[,>])', acc))
    eks_f |= set(re.findall(r',\.([a-z0-9]{2,5})', acc))
    eks_f = {e for e in eks_f if e not in ("com", "org", "xml", "openxmlformats")}
    be = {'docx','doc','pdf','xlsx','xls','pptx','ppt','txt','rtf','odt','ods','odp','csv','png','jpg','jpeg','zip'}
    hilang = be - eks_f
    check("semua ekstensi BE ada di ACCEPT FE", not hilang,
          f"hilang={sorted(hilang)}" if hilang else f"{len(eks_f)} ekstensi cocok")

    print("\n" + "=" * 72)
    print(f"HASIL: LULUS {len(PASS)}   GAGAL {len(FAIL)}")
    if FAIL:
        print("GAGAL:")
        for f in FAIL:
            print(f"  - {f}")
    print("=" * 72)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
