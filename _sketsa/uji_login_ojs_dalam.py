#!/usr/bin/env python3
"""UJI LOGIN OJS dari DALAM — user (username=email) login pakai sandi default.

Bukti langsung: apakah putusan Bos (username=email, sandi Pass1EduAi) JALAN.
"""
import base64
import subprocess
import textwrap

PY = textwrap.dedent('''
    import re, urllib.request, urllib.parse, http.cookiejar

    EMAIL = "uji-wulan-16okt2026@eduai.test"
    SANDI = "Pass1EduAi"
    BASE = "http://ojs-ojs_web-1"

    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPRedirectHandler())

    print("  1 buka halaman login (ambil CSRF)")
    html = op.open(BASE + "/jemt/en/login", timeout=40).read().decode()
    m = re.search(r'name="csrfToken"[^>]*value="([^"]+)"', html)
    tok = m.group(1) if m else ""
    print("     csrf:", "ADA" if tok else "TIDAK ADA", "| html:", len(html))

    print("  2 kirim form login (username = EMAIL, sandi = default)")
    data = urllib.parse.urlencode({
        "username": EMAIL, "password": SANDI,
        "csrfToken": tok, "source": "", "remember": "1"}).encode()
    r = op.open(urllib.request.Request(BASE + "/jemt/en/login/signIn",
                                       data=data), timeout=40)
    isi = r.read().decode()
    print("     HTTP", r.status, "| url akhir:", r.url)
    print("     ada kata 'Keluar'/Logout?", "logout" in isi.lower()
          or "keluar" in isi.lower())

    print("  3 VERIFIKASI dengan halaman profil owner")
    try:
        r2 = op.open(BASE + "/jemt/en/user/profile", timeout=40)
        p = r2.read().decode()
        print("     profil HTTP", r2.status)
        print("     email user tampil?", EMAIL in p)
        print("     nama user tampil? ", ("Wulan" in p or "Uji" in p))
    except Exception as e:
        print("     profil gagal:", e)
''')

b64 = base64.b64encode(PY.encode()).decode()
inner = ("echo " + b64 + " | base64 -d | docker exec -i ojs-mcp python3 -")
cmd = ("docker run --rm alpine:3.20 sh -c \""
       "apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null; "
       "sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no "
       "-o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 '" + inner + "'\"")
out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(out.stdout[-3000:])
if out.stderr:
    print("STDERR:", out.stderr[-500:])
