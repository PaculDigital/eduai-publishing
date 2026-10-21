#!/usr/bin/env python3
"""Uji E2E: siklus hidup transaksi EduAi (12Sep26).

Menguji 4 perbaikan:
  A. Auto-expire  : pending yang lewat batas -> status 'expired'
  B. Batas pending: transaksi ke-4 -> 429 PENDING_PENUH
  C. Lanjut bayar : ambil/buat ulang QR, order_id TETAP, 1 baris tetap 1 baris
  D. Pagination   : hal/per jalan, total benar, tidak ada baris kembar

Jalankan: python3 scripts/uji_siklus_transaksi.py
"""
import http.cookiejar
import json
import re
import sqlite3
import subprocess
import sys
import urllib.parse
import urllib.request

BASE = "https://eduai.bikinaja.id"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

# user uji
EMAIL = "uji.siklus@eduai.local"
PASSWORD = "UjiSiklus123!"

LULUS, GAGAL = 0, 0


def ok(nama, syarat, info=""):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f"  [LULUS] {nama} {info}")
    else:
        GAGAL += 1
        print(f"  [GAGAL] {nama} {info}")


class Sesi:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj))

    def _req(self, metode, path, data=None):
        url = BASE + path
        body = None
        if data:
            body = urllib.parse.urlencode(data).encode()
        r = urllib.request.Request(url, data=body, method=metode)
        r.add_header('User-Agent', UA)
        r.add_header('Accept', 'application/json, text/html, */*')
        r.add_header('Referer', BASE + '/')
        if body:
            r.add_header('Content-Type', 'application/x-www-form-urlencoded')
        try:
            with self.op.open(r, timeout=30) as resp:
                return resp.status, resp.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')

    def get(self, p):
        return self._req('GET', p)

    def post(self, p, d):
        st, b = self._req('POST', p, d)
        try:
            return st, json.loads(b)
        except Exception:
            return st, {'_raw': b[:300]}

    def jget(self, p):
        st, b = self.get(p)
        try:
            return st, json.loads(b)
        except Exception:
            return st, {}


def db(q):
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('/app/data/eduai.db');"
         f"print(json.dumps(c.execute({q!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


def dbe(sql):
    subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
         f"c.execute({sql!r});c.commit();c.close()"],
        capture_output=True, text=True, timeout=60)


print("=" * 62)
print("UJI SIKLUS HIDUP TRANSAKSI EDUAI")
print("=" * 62)

s = Sesi()
st, _b = s.post('/masuk', {'email': EMAIL, 'password': PASSWORD})
ok('login user uji', st in (200, 303), f'(HTTP {st})')

if st not in (200, 303):
    print("\n  !! LOGIN GAGAL - cek kredensial user uji. Berhenti.")
    sys.exit(1)

# ── bersihkan sisa uji sebelumnya ──────────────────────────────
uid = db("SELECT id FROM users WHERE email='%s'" % EMAIL)
uid = uid[0][0] if uid else None
ok("user uji ditemukan", uid is not None, f"(id={uid})")
dbe(f"DELETE FROM transaksi WHERE user_id={uid} AND order_id LIKE 'UJI-%'")
dbe(f"DELETE FROM transaksi WHERE user_id={uid}")

# ══ A. AUTO-EXPIRE ══════════════════════════════════════════════
print("\n[A] AUTO-EXPIRE transaksi pending")
st, d = s.post('/api/topup/buat', {'paket': 'penulis'})
ok("buat transaksi", st == 200 and d.get('ok'), f"(HTTP {st})")
oid = d.get('order_id')
ok("dapat order_id", bool(oid), f"({oid})")

# pastikan kolom kedaluwarsa terisi
bts = db(f"SELECT kedaluwarsa FROM transaksi WHERE order_id='{oid}'")
ok("kolom kedaluwarsa terisi", bool(bts and bts[0][0]), f"({bts[0][0] if bts else None})")

# mundurkan waktu -> harus jadi expired saat riwayat dibuka
dbe(f"UPDATE transaksi SET dibuat=datetime('now','-40 minutes'), "
    f"kedaluwarsa=datetime('now','-20 minutes') WHERE order_id='{oid}'")
st, rw = s.jget('/api/riwayat?hal=1&per=10')
baris = [x for x in rw.get('riwayat', []) if x['order_id'] == oid]
ok("transaksi lama -> status 'expired'",
   bool(baris) and baris[0]['status'] == 'expired',
   f"(status={baris[0]['status'] if baris else '?'})")

# ══ B. BATAS PENDING ════════════════════════════════════════════
print("\n[B] BATAS 3 TRANSAKSI MENUNGGU")
dbe(f"DELETE FROM transaksi WHERE user_id={uid}")
codes = []
for i in range(1, 5):
    st, d = s.post('/api/topup/buat', {'paket': 'penulis'})
    codes.append(st)
ok("transaksi 1-3 diterima", codes[:3] == [200, 200, 200], f"({codes[:3]})")
ok("transaksi ke-4 DITOLAK 429", codes[3] == 429, f"({codes[3]})")

# pesan harus informatif
st, d = s.post('/api/topup/buat', {'paket': 'penulis'})
ok("kode PENDING_PENUH + pesan jelas",
   d.get('kode') == 'PENDING_PENUH' and 'menunggu' in (d.get('pesan') or ''),
   f"({d.get('kode')})")

# ══ C. LANJUTKAN BAYAR ══════════════════════════════════════════
print("\n[C] LANJUTKAN BAYAR dari riwayat")
# hapus semua, buat 1, lalu expire-kan
dbe(f"DELETE FROM transaksi WHERE user_id={uid}")
st, d = s.post('/api/topup/buat', {'paket': 'peneliti'})
oid2 = d.get('order_id')
qr_lama = d.get('qr')
dbe(f"UPDATE transaksi SET status='expired', dibuat=datetime('now','-40 minutes'), "
    f"kedaluwarsa=datetime('now','-20 minutes') WHERE order_id='{oid2}'")

# lanjutkan -> harus dapat QR (baru atau lama) dengan ORDER_ID TETAP
st, d2 = s.post('/api/topup/lanjut', {'order_id': oid2})
ok("lanjut bayar berhasil", st == 200 and d2.get('ok'), f"(HTTP {st})")
ok("order_id TETAP (1 baris tetap 1 baris)",
   d2.get('order_id') == oid2, f"({d2.get('order_id')})")
ok("dapat QR", bool(d2.get('qr')), f"(panjang={len(d2.get('qr') or '')})")
ok("sisa_detik > 0", (d2.get('sisa_detik') or 0) > 0, f"({d2.get('sisa_detik')})")

n_rows = db(f"SELECT COUNT(*) FROM transaksi WHERE user_id={uid}")
ok("TIDAK menambah baris baru", n_rows[0][0] == 1, f"({n_rows[0][0]} baris)")

st_st = db(f"SELECT status FROM transaksi WHERE order_id='{oid2}'")
ok("status kembali 'pending'", st_st[0][0] == 'pending', f"({st_st[0][0]})")

# transaksi non-pending harus ditolak
dbe(f"UPDATE transaksi SET status='batal' WHERE order_id='{oid2}'")
st, d3 = s.post('/api/topup/lanjut', {'order_id': oid2})
ok("transaksi 'batal' ditolak 409", st == 409, f"(HTTP {st})")

# anti-IDOR: order_id milik user lain
lain = db("SELECT order_id FROM transaksi WHERE user_id != %d LIMIT 1" % uid)
if lain:
    st, _ = s.post('/api/topup/lanjut', {'order_id': lain[0][0]})
    ok("order_id user lain -> 404 (anti-IDOR)", st == 404, f"(HTTP {st})")

# ══ D. PAGINATION ═══════════════════════════════════════════════
print("\n[D] PAGINATION riwayat")
dbe(f"DELETE FROM transaksi WHERE user_id={uid}")
for i in range(7):
    dbe(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat)"
        f" VALUES ({uid},'UJI-P{i}',{chr(39)}penulis{chr(39)},100,50000,'sukses',"
        f"datetime('now','-{i} hours'))")

st, p1 = s.jget('/api/riwayat?hal=1&per=3')
ok("total benar", p1.get('total') == 7, f"(total={p1.get('total')})")
ok("halaman 1 berisi 3", len(p1.get('riwayat', [])) == 3,
   f"({len(p1.get('riwayat', []))})")
ok("ada_lagi True", p1.get('ada_lagi') is True)

st, p3 = s.jget('/api/riwayat?hal=3&per=3')
ok("halaman terakhir berisi 1", len(p3.get('riwayat', [])) == 1,
   f"({len(p3.get('riwayat', []))})")
ok("ada_lagi False di akhir", p3.get('ada_lagi') is False)

# tidak ada order_id kembar antar halaman
id1 = {x['order_id'] for x in p1.get('riwayat', [])}
st, p2 = s.jget('/api/riwayat?hal=2&per=3')
id2 = {x['order_id'] for x in p2.get('riwayat', [])}
ok("tidak ada baris kembar", not (id1 & id2), f"({id1 & id2 or 'kosong'})")

# per dibatasi
st, pbig = s.jget('/api/riwayat?hal=1&per=9999')
ok("per dibatasi maks 50", len(pbig.get('riwayat', [])) <= 50,
   f"({len(pbig.get('riwayat', []))})")

# ══ bersihkan ═══════════════════════════════════════════════════
dbe(f"DELETE FROM transaksi WHERE user_id={uid}")
print("\n(bersih) transaksi uji user %d dihapus" % uid)

print("\n" + "=" * 62)
print(f"HASIL: {LULUS} LULUS, {GAGAL} GAGAL")
print("=" * 62)
sys.exit(1 if GAGAL else 0)
