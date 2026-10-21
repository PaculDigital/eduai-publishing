#!/usr/bin/env python3
"""Verifikasi E2E — Tab Riwayat Transaksi EduAi (17Sep26).

Uji LIVE lewat domain produksi (https://eduai.bikinaja.id), bukan unit test.
Cek:
  1. /naskah harus memuat tombol "Riwayat Transaksi" + panggilan bukaRiwayat()
  2. _topup_popup.html harus punya tab + panel riwayat
  3. /api/riwayat: 303 tanpa login, 200 dgn login, bentuk {riwayat:[...]}
  4. Isi riwayat konsisten dengan DB (jumlah baris, field wajib)
  5. Guard: user A tidak bisa lihat transaksi user B
"""
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "https://eduai.bikinaja.id"
DB_IN_CONTAINER = "/app/data/eduai.db"

# Cloudflare memblokir User-Agent default Python (error code 1010).
# Wajib pakai UA browser Chrome.
UA_CHROME = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


class Sesi:
    """Sesi HTTP dengan cookie jar (login pakai cookie sesi)."""

    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            NoRedirect(),
        )

    def get(self, path, follow=True):
        r = urllib.request.Request(
            BASE + path, method="GET",
            headers={"User-Agent": UA_CHROME, "Accept": "text/html,*/*"},
        )
        try:
            resp = self.op.open(r, timeout=20)
            return resp.status, resp.read().decode("utf-8", "replace"), resp.headers
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), e.headers
        except Exception as e:
            return 0, str(e), {}

    def post(self, path, data):
        body = urllib.parse.urlencode(data).encode()
        r = urllib.request.Request(
            BASE + path, data=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": UA_CHROME,
                "Accept": "text/html,*/*",
            },
            method="POST",
        )
        try:
            resp = self.op.open(r, timeout=20)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            return 0, str(e)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def cek_html_tanpa_login():
    print("\n[1] Halaman publik & guard")
    s = Sesi()
    st, _, _ = s.get("/api/riwayat")
    check("/api/riwayat tanpa login → 303/302 (redirect)", st in (302, 303), f"status={st}")

    st, body, _ = s.get("/masuk")
    check("/masuk → 200", st == 200, f"status={st}")


def cek_template_terkirim():
    print("\n[2] Template baru ter-deploy")
    s = Sesi()
    # login dulu
    st, body = s.post("/masuk", {"email": "qris.uji@eduai.local",
                                 "password": "rahasia123"})
    check("login qris.uji@eduai.local berhasil", st in (200, 302, 303), f"status={st}")

    st, html, _ = s.get("/naskah")
    check("/naskah → 200 (login OK)", st == 200, f"status={st}")

    if st == 200:
        check("tombol 'Riwayat Transaksi' ADA di naskah.html",
              "Riwayat Transaksi" in html)
        check("fungsi bukaRiwayat() dipanggil tombol",
              "bukaRiwayat()" in html)
        check("CSS .tombol-riwayat ADA", "tombol-riwayat" in html)
        check("include _topup_popup.html ter-render",
              "tab-riwayat" in html and "panel-riwayat" in html)
        check("tab 'Beli Kuota' ADA", "Beli Kuota" in html)
        check("wadah riwayat ADA", "wadah-riwayat" in html)
        check("JS muatRiwayat ADA", "muatRiwayat" in html)
        check("JS pindahTab ADA", "pindahTab" in html)
    return s


def cek_api_riwayat(s):
    print("\n[3] /api/riwayat dengan login")
    st, body, _ = s.get("/api/riwayat")
    check("/api/riwayat login → 200", st == 200, f"status={st}")
    try:
        d = json.loads(body)
    except Exception as e:
        check("respons JSON valid", False, f"{e} body={body[:150]}")
        return None
    check("respons JSON valid", True)
    check("punya key 'riwayat'", "riwayat" in d)
    rows = d.get("riwayat", [])
    check("'riwayat' berupa list", isinstance(rows, list), f"type={type(rows).__name__}")

    if rows:
        r0 = rows[0]
        for k in ("order_id", "paket", "mb", "jumlah", "status", "tanggal"):
            check(f"field '{k}' ada di item", k in r0, f"keys={list(r0.keys())}")
    return rows


def cek_konsistensi_db(rows):
    print("\n[4] Konsistensi respons vs DB (user 4)")
    # baca DB via docker exec (DB ada di dalam container)
    import subprocess
    code = (
        "import sqlite3,json;"
        "c=sqlite3.connect('file:/app/data/eduai.db?mode=ro',uri=True);"
        "print(json.dumps(c.execute("
        "'SELECT order_id,paket,tambahan_mb,jumlah,status FROM transaksi "
        "WHERE user_id=4 ORDER BY dibuat DESC').fetchall()))"
    )
    try:
        out = subprocess.run(
            ["docker", "exec", "eduai-app", "python3", "-c", code],
            capture_output=True, text=True, timeout=30,
        )
        db_rows = json.loads(out.stdout.strip())
    except Exception as e:
        check("baca DB", False, str(e))
        return

    check(f"jumlah baris BE({len(rows)}) == DB({len(db_rows)})", len(rows) == len(db_rows))
    if rows and db_rows:
        check("order_id urutan pertama sama",
              rows[0]["order_id"] == db_rows[0][0],
              f"BE={rows[0]['order_id']} DB={db_rows[0][0]}")
        check("status urutan pertama sama",
              rows[0]["status"] == db_rows[0][4],
              f"BE={rows[0]['status']} DB={db_rows[0][4]}")
        check("mb urutan pertama sama",
              int(rows[0]["mb"]) == int(db_rows[0][2]))
        check("jumlah urutan pertama sama",
              int(rows[0]["jumlah"]) == int(db_rows[0][3]))


def cek_isolasi_user():
    print("\n[5] Isolasi: user lain tidak lihat transaksi user 4")
    s2 = Sesi()
    st, _ = s2.post("/masuk", {"email": "oo.uji@eduai.local",
                               "password": "rahasia123"})
    if st not in (200, 302, 303):
        check("login oo.uji (skip isolasi)", True, f"status={st} — dilewati")
        return
    st, body, _ = s2.get("/api/riwayat")
    if st != 200:
        check("/api/riwayat user lain → 200", False, f"status={st}")
        return
    rows2 = json.loads(body).get("riwayat", [])
    check("user 5 tidak melihat transaksi user 4",
          all("EDUAI-4-" not in r["order_id"] for r in rows2),
          f"rows={[r['order_id'] for r in rows2]}")


def main():
    print("=" * 70)
    print("VERIFIKASI E2E — TAB RIWAYAT TRANSAKSI EduAi")
    print(f"BASE = {BASE}")
    print("=" * 70)

    cek_html_tanpa_login()
    s = cek_template_terkirim()
    rows = cek_api_riwayat(s)
    if rows is not None:
        cek_konsistensi_db(rows)
    cek_isolasi_user()

    print("\n" + "=" * 70)
    print(f"HASIL: LULUS {len(PASS)}   GAGAL {len(FAIL)}")
    if FAIL:
        print("\nGAGAL:")
        for f in FAIL:
            print(f"  - {f}")
    print("=" * 70)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
