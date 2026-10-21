#!/usr/bin/env python3
"""Uji E2E: batal transaksi + tombol QRIS (12Sep26).

Masalah yang diperbaiki:
  #1 Klik "Batal" -> status di riwayat tetap "Menunggu", harusnya "Dibatalkan".
  #2 Tidak ada tombol Simpan QR / Buka App Bank -> user HP tak bisa bayar.

Uji LIVE via domain produksi:
  1. /api/topup/batal ada & menolak tanpa login (303/401)
  2. Batal transaksi pending NYATA -> status berubah jadi 'batal'
  3. Riwayat menampilkan status 'batal' + bisa_batal=False setelah dibatalkan
  4. Tidak bisa membatalkan transaksi 'sukses' (409)
  5. Tidak bisa membatalkan transaksi milik user LAIN (404, anti-IDOR)
  6. Idempoten: batal 2x tetap ok
  7. HTML memuat tombol Simpan QR + Buka App Bank + petunjuk
  8. Badge CSS 'batal' + tombol rw-batal ada
"""
import io
import json
import re
import sqlite3
import subprocess
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


class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class Sesi:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj), NoRedir())

    def get(self, path):
        r = urllib.request.Request(BASE + path,
                                   headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            resp = self.op.open(r, timeout=20)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def post(self, path, data):
        body = urllib.parse.urlencode(data).encode()
        r = urllib.request.Request(BASE + path, data=body, method="POST",
                                   headers={"Content-Type": "application/x-www-form-urlencoded",
                                            "User-Agent": UA})
        try:
            resp = self.op.open(r, timeout=25)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def post_form(self, path, fields):
        b = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in fields.items())
        r = urllib.request.Request(BASE + path, data=b.encode(), method="POST",
                                   headers={"Content-Type": "application/x-www-form-urlencoded",
                                            "User-Agent": UA})
        try:
            resp = self.op.open(r, timeout=25)
            return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")


def db_query(sql):
    """Query DB langsung di container (read-only)."""
    out = subprocess.run(
        ["docker", "exec", "eduai-app", "python3", "-c",
         f"import sqlite3;c=sqlite3.connect('file:/app/data/eduai.db?mode=ro',uri=True);"
         f"print({sql!r} and c.execute({sql!r}).fetchall())"],
        capture_output=True, text=True, timeout=30)
    try:
        return eval(out.stdout.strip())
    except Exception:
        return None


def main():
    print("=" * 74)
    print("UJI E2E: BATAL TRANSAKSI + TOMBOL QRIS")
    print(f"BASE = {BASE}")
    print("=" * 74)

    # ---- 1. tanpa login ----
    print("\n[1] Guard endpoint /api/topup/batal")
    s0 = Sesi()
    st, _ = s0.post_form("/api/topup/batal", {"order_id": "X"})
    check("tanpa login ditolak (303/401/403)", st in (303, 401, 403), f"status={st}")

    # ---- login user A (pemilik) ----
    s = Sesi()
    st, _ = s.post("/masuk", {"email": EMAIL, "password": PWD})
    print(f"\n[0] Login {EMAIL}: status={st}")

    st, html = s.get("/naskah")
    check("/naskah -> 200", st == 200, f"status={st}")

    # ---- 7. tombol QRIS di HTML ----
    print("\n[7] Elemen tombol QRIS di HTML ter-deploy")
    check("tombol 'Simpan QR' ada", 'id="simpan-qr"' in html)
    check("tombol 'Buka Aplikasi Bank' ada", 'id="buka-bank"' in html)
    check("petunjuk unggah dari galeri ada", "unggah dari galeri" in html)
    check("panduan bank manual ada", 'id="panduan-bank"' in html)
    check("fungsi simpan QR (Web Share/unduh) ada",
          "navigator.canShare" in html or "a.download" in html)

    # ---- 8. badge batal ----
    print("\n[8] Status 'batal' di FE")
    check("CSS .rw-lencana.batal ada", ".rw-lencana.batal" in html)
    check("CSS .rw-batal (tombol batal di riwayat) ada", ".rw-batal" in html)
    check("JS peta status 'batal' -> 'Dibatalkan' ada", "'Dibatalkan'" in html)
    check("JS batalkanDariRiwayat ada", "batalkanDariRiwayat" in html)

    # ---- 2/3. buat transaksi pending NYATA lalu batalkan ----
    print("\n[2] Buat transaksi pending sungguhan (via /api/topup/mulai)")
    st, body = s.post_form("/api/topup/buat", {"paket": "penulis"})
    print(f"    status={st} body={body[:220]}")
    order_id = None
    try:
        j = json.loads(body)
        order_id = j.get("order_id")
    except Exception:
        pass
    check("transaksi dibuat (order_id didapat)", bool(order_id), f"order_id={order_id}")

    if order_id:
        print(f"\n[2b] Cek status awal di DB & riwayat")
        st, rb = s.get("/api/riwayat")
        try:
            rw = json.loads(rb).get("riwayat", [])
            row = next((x for x in rw if x.get("order_id") == order_id), None)
            check("transaksi muncul di riwayat sbg 'pending'",
                  bool(row) and row.get("status") == "pending",
                  f"status={row.get('status') if row else 'tidak ada'}")
            check("bisa_batal=True saat pending",
                  bool(row) and row.get("bisa_batal") is True)
        except Exception as e:
            check("riwayat terbaca", False, str(e))

        print(f"\n[3] KLIK BATAL -> /api/topup/batal")
        st, body = s.post_form("/api/topup/batal", {"order_id": order_id})
        print(f"    status={st} body={body[:220]}")
        try:
            j = json.loads(body)
            check("respons ok=True", j.get("ok") is True)
            check("respons status='batal'", j.get("status") == "batal")
        except Exception as e:
            check("respons JSON valid", False, str(e))

        print("\n[3b] VERIFIKASI: status di DB benar-benar berubah")
        st, rb = s.get("/api/riwayat")
        try:
            rw = json.loads(rb).get("riwayat", [])
            row = next((x for x in rw if x.get("order_id") == order_id), None)
            check("riwayat kini menampilkan 'batal' (BUKAN 'pending')",
                  bool(row) and row.get("status") == "batal",
                  f"status={row.get('status') if row else 'tidak ada'}")
            check("bisa_batal=False setelah dibatalkan",
                  bool(row) and row.get("bisa_batal") is False)
        except Exception as e:
            check("riwayat terbaca ulang", False, str(e))

        # ---- 6. idempoten ----
        print("\n[6] Idempoten: batal 2x")
        st, body = s.post_form("/api/topup/batal", {"order_id": order_id})
        try:
            j = json.loads(body)
            check("batal kedua tetap ok=True", j.get("ok") is True, f"pesan={j.get('pesan')}")
        except Exception as e:
            check("batal kedua tetap ok", False, str(e))

        # ---- 4. transaksi sukses tidak bisa dibatalkan ----
        print("\n[4] Transaksi 'sukses' tidak boleh dibatalkan")
        sukses = db_query("SELECT order_id FROM transaksi WHERE status='sukses' LIMIT 1")
        if sukses:
            oid_ok = sukses[0][0]
            st, body = s.post_form("/api/topup/batal", {"order_id": oid_ok})
            print(f"    order_id(sukses)={oid_ok} status={st} body={body[:160]}")
            check("transaksi sukses ditolak (409)", st == 409, f"status={st}")
        else:
            print("    (tidak ada transaksi sukses untuk diuji)")

        # ---- 5. anti-IDOR: transaksi user lain ----
        print("\n[5] Anti-IDOR: transaksi milik user LAIN harus 404")
        lain = db_query(
            f"SELECT order_id FROM transaksi WHERE user_id != "
            f"(SELECT id FROM users WHERE email='{EMAIL}') LIMIT 1")
        if lain:
            oid_lain = lain[0][0]
            st, body = s.post_form("/api/topup/batal", {"order_id": oid_lain})
            print(f"    order_id(user lain)={oid_lain} status={st}")
            check("transaksi user lain -> 404", st == 404, f"status={st}")
        else:
            print("    (tidak ada transaksi user lain)")

    print("\n" + "=" * 74)
    print(f"HASIL: LULUS {len(PASS)}   GAGAL {len(FAIL)}")
    if FAIL:
        print("GAGAL:")
        for f in FAIL:
            print("  - " + f)
    print("=" * 74)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
