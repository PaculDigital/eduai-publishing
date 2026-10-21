#!/usr/bin/env python3
"""UJI NYATA di VPS Tridarma: daftar user OJS dengan username=EMAIL,
lalu LOGIN pakai email + password default. Bukti langsung, bukan tebakan.

Dijalankan lewat Alpine bridge (SSH). Tidak menyimpan kredensial ke berkas.
"""
import base64
import subprocess
import textwrap

SKRIP = textwrap.dedent('''
    import json, urllib.request, urllib.parse, http.cookiejar

    EMAIL = "uji-wulan-16okt2026@eduai.test"
    SANDI = "Pass1EduAi"
    NAMA_D = "Uji"
    NAMA_B = "Wulan"

    print("  ① daftar ke OJS (username=email, sandi default)")
    payload = {
        "username": EMAIL, "email": EMAIL, "password": SANDI,
        "given_name": NAMA_D, "family_name": NAMA_B,
        "affiliation": "Universitas Uji EduAi", "country": "ID",
        "phone": "6285720505555",
    }
    req = urllib.request.Request(
        "http://ojs-ojs_web-1/mcp/register_user.php",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        print("     HTTP", r.status, r.read()[:400].decode())
    except Exception as e:
        print("     galat:", e)
        try:
            print("     isi:", e.read()[:400].decode())
        except Exception:
            pass

    print("  ② LOGIN pakai EMAIL + sandi default di web OJS")
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    #  ambil halaman login dulu (butuh CSRF token)
    try:
        html = op.open("https://tridarma.id/jemt/en/login", timeout=40).read().decode()
    except Exception as e:
        print("     gagal buka login:", e); raise SystemExit(1)
    import re
    m = re.search(r'name="csrfToken"\\s+value="([^"]+)"', html)
    if not m:
        m = re.search(r'csrfToken[^>]*value="([^"]+)"', html)
    tok = m.group(1) if m else ""
    print("     csrf token:", "ADA" if tok else "TIDAK ADA")
    data = urllib.parse.urlencode({
        "username": EMAIL, "password": SANDI, "csrfToken": tok,
        "source": "", "remember": ""}).encode()
    try:
        r2 = op.open(urllib.request.Request(
            "https://tridarma.id/jemt/en/login/signIn", data=data), timeout=40)
        isi = r2.read().decode()
        print("     HTTP", r2.status)
        print("     login berhasil?", ("Keluar" in isi or "Logout" in isi
                                       or "logout" in isi.lower()))
        print("     ada tulisan gagal?",
              ("tidak benar" in isi.lower() or "invalid" in isi.lower()
               or "salah" in isi.lower()))
    except Exception as e:
        print("     galat login:", e)
        try: print("     isi:", e.read()[:300].decode())
        except Exception: pass
''')

b64 = base64.b64encode(SKRIP.encode()).decode()
cmd = (
    "docker run --rm alpine:3.20 sh -c \""
    "apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null; "
    "sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no "
    "-o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 "
    "'echo " + b64 + " | base64 -d | docker exec -i ojs-mcp python3 -'\""
)
print(subprocess.run(cmd, shell=True, capture_output=True,
                     text=True).stdout[-2500:])
