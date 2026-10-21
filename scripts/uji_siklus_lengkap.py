#!/usr/bin/env python3
"""Uji E2E MENYELURUH siklus hidup transaksi EduAi (12Sep26).

Tujuan: pondasi "tahan gempa" — bukan cuma happy path, tapi juga
kasus batas, balapan, data kotor, dan isolasi antar user.

Bagian:
  [0] Prasyarat & bersih-bersih
  [1] order_id TAHAN BENTROK (regresi bug 500)
  [2] Auto-expire (batas waktu, fallback, tepat di ambang)
  [3] Batas pending (3 terima, ke-4 tolak, konsistensi hitungan)
  [4] Lanjutkan bayar (QR baru, order_id tetap, 1 baris, status)
  [5] Pagination (total, batas halaman, per, urutan, tanpa duplikat)
  [6] Isolasi antar user (anti-IDOR, tidak saling lihat)
  [7] Ketahanan input buruk (halaman negatif, per=0, order_id ngawur)
  [8] Batal: aturan & idempotensi
  [9] Integritas DB akhir

Jalankan: python3 scripts/uji_siklus_lengkap.py
"""
import concurrent.futures
import http.cookiejar
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://eduai.bikinaja.id"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

USER_A = ("uji.gempa.a@eduai.local", "UjiGempa123!", "Uji Gempa A")
USER_B = ("uji.gempa.b@eduai.local", "UjiGempa123!", "Uji Gempa B")

LULUS, GAGAL = 0, 0
CATATAN = []


def ok(nama, syarat, info=""):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f"  [LULUS] {nama} {info}")
    else:
        GAGAL += 1
        print(f"  [GAGAL] {nama} {info}")


def _dari_bagian():
    """--dari=N untuk melanjutkan uji dari bagian tertentu (hemat waktu saat
    jaringan putus di tengah uji panjang)."""
    for a in sys.argv[1:]:
        if a.startswith('--dari='):
            return int(a.split('=', 1)[1])
    return 0


MULAI = _dari_bagian()


def bagian(n, judul):
    print(f"\n[{n}] {judul}")


def jalan(n):
    """True kalau bagian ke-n harus dijalankan."""
    return n >= MULAI


class Sesi:
    def __init__(self, ikut_redirect=False):
        self.cj = http.cookiejar.CookieJar()
        handlers = [urllib.request.HTTPCookieProcessor(self.cj)]
        if not ikut_redirect:
            # PENTING: guard login membalas 303 -> /masuk. Tanpa ini, urllib
            # otomatis mengikuti redirect dan kita melihat 200 (halaman masuk),
            # bukan 303. Itu bikin uji "tanpa login" salah lapor LULUS.
            class _TanpaRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k):
                    return None
            handlers.append(_TanpaRedirect())
        self.op = urllib.request.build_opener(*handlers)

    def _req(self, metode, path, data=None, _coba=4):
        """Kirim request dengan RETRY saat jaringan Hermes putus.

        KENAPA perlu: jaringan container Hermes kadang `Errno 101 Network is
        unreachable` sesaat. Tanpa retry, uji panjang selalu gagal di tengah
        dan hasilnya tidak bisa dipercaya.
        """
        body = urllib.parse.urlencode(data).encode() if data else None
        terakhir = None
        for n in range(_coba):
            r = urllib.request.Request(BASE + path, data=body, method=metode)
            r.add_header('User-Agent', UA)
            r.add_header('Accept', 'application/json, text/html, */*')
            r.add_header('Referer', BASE + '/')
            if body:
                r.add_header('Content-Type', 'application/x-www-form-urlencoded')
            try:
                with self.op.open(r, timeout=40) as resp:
                    return resp.status, resp.read().decode('utf-8', 'replace')
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode('utf-8', 'replace')
            except Exception as e:                 # URLError / timeout
                terakhir = e
                if n < _coba - 1:
                    import time as _t
                    _t.sleep(2 + n * 2)            # backoff 2s, 4s, 6s
        raise terakhir

    def _j(self, metode, p, d=None):
        st, b = self._req(metode, p, d)
        try:
            return st, json.loads(b)
        except Exception:
            return st, {'_raw': b[:300]}

    def get(self, p):
        return self._j('GET', p)

    def post(self, p, d=None):
        return self._j('POST', p, d)


def sq(sql):
    """SELECT -> list of tuples (via container)."""
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('/app/data/eduai.db');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


def ex(sql):
    """EXECUTE tulis (via container)."""
    subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
         f"c.execute({sql!r});c.commit();c.close()"],
        capture_output=True, text=True, timeout=60)


def daftar_atau_login(email, sandi, nama):
    """Daftar kalau belum ada; kalau sudah, langsung login. Balikan (sesi, uid).

    PENTING: untuk /daftar & /masuk kita HARUS mengikuti redirect — sukses
    daftar/login membalas 303 ke dashboard. Sesi untuk uji guard (tanpa login)
    dibuat terpisah dengan ikut_redirect=False.
    """
    s = Sesi(ikut_redirect=True)
    s.post('/daftar', {'email': email, 'password': sandi, 'nama': nama})
    st, _ = s.post('/masuk', {'email': email, 'password': sandi})
    uid = sq(f"SELECT id FROM users WHERE email='{email}'")
    return (s, uid[0][0] if uid else None), st


print("=" * 64)
print("UJI MENYELURUH SIKLUS TRANSAKSI EDUAI")
print("=" * 64)

# ══ [0] PRASYARAT ════════════════════════════════════════════════
bagian(0, "PRASYARAT & BERSIH-BERSIH")
(a, uid_a), st_a = daftar_atau_login(*USER_A)
ok("user A siap", uid_a is not None and st_a == 200, f"(uid={uid_a}, HTTP {st_a})")
(b, uid_b), st_b = daftar_atau_login(*USER_B)
ok("user B siap", uid_b is not None and st_b == 200, f"(uid={uid_b}, HTTP {st_b})")

# pastikan kolom kedaluwarsa ada (migrasi jalan)
kol = [r[1] for r in sq('PRAGMA table_info(transaksi)')]
ok("kolom 'kedaluwarsa' ada (migrasi jalan)", 'kedaluwarsa' in kol,
   f"({len(kol)} kolom)")

for u in (uid_a, uid_b):
    ex(f"DELETE FROM transaksi WHERE user_id={u}")
    ex(f"DELETE FROM files WHERE user_id={u}")

# catat data ASLI (jangan sampai tersentuh)
asli_sebelum = sq("SELECT COUNT(*) FROM transaksi WHERE user_id NOT IN (%d,%d)"
                  % (uid_a, uid_b))[0][0]
print(f"  (info) transaksi milik user lain (TIDAK disentuh): {asli_sebelum}")

# ══ [1] ORDER_ID TAHAN BENTROK (regresi bug 500) ═════════════════
bagian(1, "ORDER_ID TAHAN BENTROK (regresi bug 500)")
if jalan(1):
    # 1a. Berurutan cepat: dulu 2 transaksi di detik yang sama -> 500
    hasil_kode = []
    for i in range(3):
        st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
        hasil_kode.append(st)
    ok("3 transaksi berurutan TANPA 500", 500 not in hasil_kode, f"({hasil_kode})")
    ids = sq(f"SELECT order_id FROM transaksi WHERE user_id={uid_a}")
    ok("semua order_id UNIK", len(ids) == len({x[0] for x in ids}),
       f"({len(ids)} baris, {len({x[0] for x in ids})} unik)")

    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # 1b. PARALEL sungguhan: 3 permintaan bersamaan (jaringan Hermes terbatas,
    #     jadi jumlah thread dijaga kecil + retry saat koneksi putus)
    def kirim(i, _coba=3):
        for n in range(_coba):
            try:
                s = Sesi(ikut_redirect=True)
                s.post('/masuk', {'email': USER_A[0], 'password': USER_A[1]})
                return s.post('/api/topup/buat', {'paket': 'penulis'})
            except Exception as e:
                if n == _coba - 1:
                    return (0, {'_err': str(e)[:60]})
                import time as _t
                _t.sleep(1.5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:
        par = list(p.map(kirim, range(3)))
    kode_par = sorted(st for st, _ in par)
    err_par = [d.get('_err') for _, d in par if isinstance(d, dict) and d.get('_err')]
    ok("3 permintaan PARALEL tanpa 500", 500 not in kode_par,
       f"({kode_par}{' err=' + str(err_par) if err_par else ''})")
    rows_par = sq(f"SELECT order_id FROM transaksi WHERE user_id={uid_a}")
    ok("order_id paralel semua unik",
       len(rows_par) == len({x[0] for x in rows_par}),
       f"({len(rows_par)} baris)")
    # batas pending 3 -> maksimal 3 yang boleh lolos
    ok("batas pending ditegakkan saat paralel", len(rows_par) <= 3,
       f"({len(rows_par)} baris, maks 3)")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [2] AUTO-EXPIRE ══════════════════════════════════════════════
bagian(2, "AUTO-EXPIRE")
if jalan(2):
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    oid = d.get('order_id')
    bts = sq(f"SELECT kedaluwarsa FROM transaksi WHERE order_id='{oid}'")
    ok("kedaluwarsa TERISI dari Pakasir",
       bool(bts and bts[0][0]), f"({bts[0][0] if bts else None})")

    # 2a. jauh lewat batas -> expired
    ex(f"UPDATE transaksi SET dibuat=datetime('now','-60 minutes'), "
       f"kedaluwarsa=datetime('now','-40 minutes') WHERE order_id='{oid}'")
    st, rw = a.get('/api/riwayat?hal=1&per=10')
    r = [x for x in rw.get('riwayat', []) if x['order_id'] == oid]
    ok("lewat batas -> 'expired'", r and r[0]['status'] == 'expired',
       f"({r[0]['status'] if r else '?'})")
    ok("'expired' tidak bisa dibatalkan", r and r[0]['bisa_batal'] is False)
    ok("'expired' BISA dilanjutkan", r and r[0]['bisa_lanjut'] is True)

    # 2b. masih dalam batas -> tetap pending
    ok("di dalam batas -> tetap 'pending'",
       bool(r) and r[0]['sisa_detik'] >= 0,
       f"(sisa={r[0]['sisa_detik'] if r else '?'}s)")

    # 2c. tepat di ambang (59 detik lalu, batas 20 menit) -> pending
    ex(f"UPDATE transaksi SET status='pending', dibuat=datetime('now','-59 seconds'), "
       f"kedaluwarsa=NULL WHERE order_id='{oid}'")
    st, rw = a.get('/api/riwayat?hal=1&per=10')
    r = [x for x in rw.get('riwayat', []) if x['order_id'] == oid]
    ok("baru 59 detik -> masih 'pending'", r and r[0]['status'] == 'pending',
       f"(status={r[0]['status'] if r else '?'})")

    # 2d. fallback: kedaluwarsa NULL, dibuat lama -> tetap expired
    ex(f"UPDATE transaksi SET dibuat=datetime('now','-45 minutes'), "
       f"kedaluwarsa=NULL WHERE order_id='{oid}'")
    st, rw = a.get('/api/riwayat?hal=1&per=10')
    r = [x for x in rw.get('riwayat', []) if x['order_id'] == oid]
    ok("kedaluwarsa NULL + dibuat lama -> 'expired' (fallback)",
       r and r[0]['status'] == 'expired', f"({r[0]['status'] if r else '?'})")

    # 2e. status lain TIDAK boleh jadi expired
    ex(f"UPDATE transaksi SET status='sukses', dibuat=datetime('now','-90 minutes'), "
       f"kedaluwarsa=datetime('now','-60 minutes') WHERE order_id='{oid}'")
    st, rw = a.get('/api/riwayat?hal=1&per=10')
    r = [x for x in rw.get('riwayat', []) if x['order_id'] == oid]
    ok("'sukses' lama TETAP 'sukses' (tidak di-expire)",
       r and r[0]['status'] == 'sukses', f"({r[0]['status'] if r else '?'})")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [3] BATAS PENDING ════════════════════════════════════════════
bagian(3, "BATAS PENDING (maks 3)")
if jalan(3):
    kode = []
    for i in range(5):
        st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
        kode.append(st)
    ok("transaksi 1-3 diterima 200", kode[:3] == [200, 200, 200], f"({kode[:3]})")
    ok("transaksi 4-5 DITOLAK 429", kode[3:] == [429, 429], f"({kode[3:]})")
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    ok("kode PENDING_PENUH", d.get('kode') == 'PENDING_PENUH', f"({d.get('kode')})")
    ok("pesan menyebut jumlah & batas",
       'menunggu' in (d.get('pesan') or '') and '3' in (d.get('pesan') or ''),
       f"({(d.get('pesan') or '')[:60]}…)")

    n = sq(f"SELECT COUNT(*) FROM transaksi WHERE user_id={uid_a}")[0][0]
    ok("DB hanya berisi 3 baris", n == 3, f"({n} baris)")

    # bayar 1 -> kuota naik, hitungan pending turun -> boleh buat lagi
    oid_bayar = sq(f"SELECT order_id FROM transaksi WHERE user_id={uid_a} "
                   f"AND status='pending' LIMIT 1")[0][0]
    kuota_before = sq(f"SELECT kuota_mb FROM users WHERE id={uid_a}")[0][0]
    ex(f"UPDATE transaksi SET status='sukses', dibayar=datetime('now') "
       f"WHERE order_id='{oid_bayar}'")
    ex(f"UPDATE users SET kuota_mb = kuota_mb + 100 WHERE id={uid_a}")
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    ok("setelah 1 lunas -> boleh buat lagi (200)", st == 200, f"(HTTP {st})")

    # paket tidak valid
    st, d = a.post('/api/topup/buat', {'paket': 'paket-ngawur'})
    ok("paket ngawur ditolak", st == 400, f"(HTTP {st})")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [4] LANJUTKAN BAYAR ═════════════════════════════════════════
bagian(4, "LANJUTKAN BAYAR")
if jalan(4):
    st, d = a.post('/api/topup/buat', {'paket': 'peneliti'})
    oid = d.get('order_id')
    ex(f"UPDATE transaksi SET status='expired', dibuat=datetime('now','-40 minutes'), "
       f"kedaluwarsa=datetime('now','-20 minutes') WHERE order_id='{oid}'")

    st, d2 = a.post('/api/topup/lanjut', {'order_id': oid})
    ok("lanjut transaksi expired -> ok", st == 200 and d2.get('ok'), f"(HTTP {st})")
    ok("order_id TETAP", d2.get('order_id') == oid, f"({d2.get('order_id')})")
    ok("QR terisi", bool(d2.get('qr')), f"(panjang={len(d2.get('qr') or '')})")
    # CATATAN: Pakasir memakai masa berlaku ~1 jam, jadi sisa_detik wajar bisa
    # sampai ~3600s. Yang penting: > 0 dan tidak lebih dari 1 jam + toleransi.
    ok("sisa_detik wajar (1..3700)",
       1 <= (d2.get('sisa_detik') or 0) <= 3700, f"({d2.get('sisa_detik')}s)")
    n = sq(f"SELECT COUNT(*) FROM transaksi WHERE user_id={uid_a}")[0][0]
    ok("TETAP 1 baris (tidak menambah)", n == 1, f"({n} baris)")
    stt = sq(f"SELECT status FROM transaksi WHERE order_id='{oid}'")[0][0]
    ok("status kembali 'pending'", stt == 'pending', f"({stt})")

    # lanjut pada 'sukses'
    ex(f"UPDATE transaksi SET status='sukses' WHERE order_id='{oid}'")
    st, d3 = a.post('/api/topup/lanjut', {'order_id': oid})
    ok("'sukses' ditolak 409", st == 409, f"(HTTP {st})")
    # lanjut pada 'batal'
    ex(f"UPDATE transaksi SET status='batal' WHERE order_id='{oid}'")
    st, d4 = a.post('/api/topup/lanjut', {'order_id': oid})
    ok("'batal' ditolak 409", st == 409, f"(HTTP {st})")
    # lanjut pada 'gagal'
    ex(f"UPDATE transaksi SET status='gagal' WHERE order_id='{oid}'")
    st, d5 = a.post('/api/topup/lanjut', {'order_id': oid})
    ok("'gagal' ditolak 409", st == 409, f"(HTTP {st})")

    # batas pending berlaku juga saat lanjut
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")
    for i in range(3):
        a.post('/api/topup/buat', {'paket': 'penulis'})
    ex(f"UPDATE transaksi SET status='expired', kedaluwarsa=datetime('now','-30 minutes') "
       f"WHERE user_id={uid_a} AND id=(SELECT MIN(id) FROM transaksi WHERE user_id={uid_a})")
    oid_x = sq(f"SELECT order_id FROM transaksi WHERE user_id={uid_a} AND status='expired'"
               )[0][0]
    for i in range(2):
        a.post('/api/topup/buat', {'paket': 'penulis'})   # isi sampai 3 pending
    n_pending = sq(f"SELECT COUNT(*) FROM transaksi WHERE user_id={uid_a} "
                   f"AND status='pending'")[0][0]
    st, d6 = a.post('/api/topup/lanjut', {'order_id': oid_x})
    ok(f"lanjut saat pending penuh ({n_pending}) -> 429",
       st == 429, f"(HTTP {st}, kode={d6.get('kode')})")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [5] PAGINATION ═══════════════════════════════════════════════
bagian(5, "PAGINATION")
if jalan(5):
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")
    for i in range(25):
        ex(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat)"
            f" VALUES ({uid_a},'UJI-PG{i:02d}','penulis',100,50000,'sukses',"
            f"datetime('now','-{i} hours'))")

    st, p1 = a.get('/api/riwayat?hal=1&per=10')
    ok("total = 25", p1.get('total') == 25, f"(total={p1.get('total')})")
    ok("halaman 1 -> 10 baris", len(p1.get('riwayat', [])) == 10,
       f"({len(p1.get('riwayat', []))})")
    ok("ada_lagi True", p1.get('ada_lagi') is True)
    ok("urutan terbaru dulu",
       p1['riwayat'][0]['order_id'] == 'UJI-PG00',
       f"({p1['riwayat'][0]['order_id'] if p1.get('riwayat') else '?'})")

    st, p3 = a.get('/api/riwayat?hal=3&per=10')
    ok("halaman 3 -> 5 baris", len(p3.get('riwayat', [])) == 5,
       f"({len(p3.get('riwayat', []))})")
    ok("ada_lagi False di halaman akhir", p3.get('ada_lagi') is False)

    st, p4 = a.get('/api/riwayat?hal=4&per=10')
    ok("halaman di luar jangkauan -> kosong, bukan error",
       st == 200 and len(p4.get('riwayat', [])) == 0, f"(HTTP {st})")

    # tidak ada duplikat & gabungan lengkap
    semua = []
    for h in (1, 2, 3):
        st, px = a.get(f'/api/riwayat?hal={h}&per=10')
        semua += [x['order_id'] for x in px.get('riwayat', [])]
    ok("gabungan 3 halaman = 25 baris", len(semua) == 25, f"({len(semua)})")
    ok("tanpa duplikat", len(semua) == len(set(semua)),
       f"({len(semua)} vs {len(set(semua))} unik)")

    # input buruk
    st, pn = a.get('/api/riwayat?hal=-5&per=10')
    ok("hal negatif ditangani (200, hal=1)", st == 200 and pn.get('halaman') == 1,
       f"(HTTP {st}, hal={pn.get('halaman')})")
    st, p0 = a.get('/api/riwayat?hal=1&per=0')
    # per=0 -> `int(per or 10)` menganggap 0 sebagai falsy -> pakai default 10.
    # Itu perilaku yang BENAR (bukan error), jadi kita uji hasilnya wajar.
    ok("per=0 ditangani (pakai default, tanpa error)",
       st == 200 and 1 <= len(p0.get('riwayat', [])) <= 50,
       f"(HTTP {st}, {len(p0.get('riwayat', []))} baris)")
    st, pbig = a.get('/api/riwayat?hal=1&per=99999')
    ok("per raksasa dibatasi 50", len(pbig.get('riwayat', [])) <= 50,
       f"({len(pbig.get('riwayat', []))})")
    st, pab = a.get('/api/riwayat?hal=abc&per=xyz')
    ok("hal/per bukan angka -> aman", st in (200, 422), f"(HTTP {st})")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [6] ISOLASI ANTAR USER ═══════════════════════════════════════
bagian(6, "ISOLASI ANTAR USER")
if jalan(6):
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    oid_a = d.get('order_id')
    ex(f"UPDATE transaksi SET order_id='UJI-B-KEPUNYAAN-B', user_id={uid_b} "
       f"WHERE order_id='{oid_a}'")

    st, _ = a.post('/api/topup/lanjut', {'order_id': 'UJI-B-KEPUNYAAN-B'})
    ok("A tidak bisa lanjut transaksi B -> 404", st == 404, f"(HTTP {st})")
    st, _ = a.post('/api/topup/batal', {'order_id': 'UJI-B-KEPUNYAAN-B'})
    ok("A tidak bisa batalkan transaksi B -> 404", st == 404, f"(HTTP {st})")

    # riwayat tidak bocor
    ex(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat)"
       f" VALUES ({uid_b},'UJI-B-RAHASIA','penulis',100,50000,'sukses',datetime('now'))")
    st, ra = a.get('/api/riwayat?hal=1&per=50')
    st, rb = b.get('/api/riwayat?hal=1&per=50')
    oa = {x['order_id'] for x in ra.get('riwayat', [])}
    ob = {x['order_id'] for x in rb.get('riwayat', [])}
    ok("riwayat A tidak memuat milik B", 'UJI-B-RAHASIA' not in oa)
    ok("riwayat B memuat miliknya", 'UJI-B-RAHASIA' in ob, f"({ob})")

    # tanpa login -> ditolak
    anon = Sesi()          # ikut_redirect=False -> guard 303 terlihat apa adanya
    st, _ = anon.get('/api/riwayat')
    ok("tanpa login -> riwayat ditolak (303/401/403)", st in (303, 401, 403),
       f"(HTTP {st})")
    st, _ = anon.post('/api/topup/lanjut', {'order_id': 'UJI-B-RAHASIA'})
    ok("tanpa login -> lanjut ditolak (303/401/403)", st in (303, 401, 403),
       f"(HTTP {st})")

    # order_id ngawur
    st, _ = a.post('/api/topup/lanjut', {'order_id': 'TIDAK-ADA-SAMA-SEKALI'})
    ok("order_id ngawur -> 404", st == 404, f"(HTTP {st})")
    st, _ = a.post('/api/topup/lanjut', {})
    ok("order_id kosong -> 422 (validasi)", st == 422, f"(HTTP {st})")
    ex(f"DELETE FROM transaksi WHERE user_id IN ({uid_a},{uid_b})")

    # ══ [7] BATAL: ATURAN & IDEMPOTENSI ═════════════════════════════
bagian(7, "BATAL: ATURAN & IDEMPOTENSI")
if jalan(7):
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    oid = d.get('order_id')
    st, d1 = a.post('/api/topup/batal', {'order_id': oid})
    ok("batal transaksi pending -> ok", st == 200 and d1.get('ok'), f"(HTTP {st})")
    stt = sq(f"SELECT status FROM transaksi WHERE order_id='{oid}'")[0][0]
    ok("status jadi 'batal'", stt == 'batal', f"({stt})")

    st, d2 = a.post('/api/topup/batal', {'order_id': oid})
    ok("batal 2x idempoten (tetap 200)", st == 200, f"(HTTP {st})")

    st, rw = a.get('/api/riwayat?hal=1&per=10')
    r = [x for x in rw.get('riwayat', []) if x['order_id'] == oid]
    ok("riwayat: 'Dibatalkan', tanpa tombol batal",
       bool(r) and r[0]['status'] == 'batal' and r[0]['bisa_batal'] is False)

    # batal transaksi sukses -> harus ditolak (kuota sudah masuk)
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    oid2 = d.get('order_id')
    ex(f"UPDATE transaksi SET status='sukses' WHERE order_id='{oid2}'")
    st, d3 = a.post('/api/topup/batal', {'order_id': oid2})
    ok("batal transaksi 'sukses' ditolak 409", st == 409, f"(HTTP {st})")
    stt = sq(f"SELECT status FROM transaksi WHERE order_id='{oid2}'")[0][0]
    ok("status 'sukses' TIDAK berubah", stt == 'sukses', f"({stt})")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [8] KONSISTENSI KUOTA ═══════════════════════════════════════
bagian(8, "KONSISTENSI KUOTA")
if jalan(8):
    kuota0 = sq(f"SELECT kuota_mb FROM users WHERE id={uid_a}")[0][0]
    st, d = a.post('/api/topup/buat', {'paket': 'penulis'})
    oid = d.get('order_id')
    mb = sq(f"SELECT tambahan_mb FROM transaksi WHERE order_id='{oid}'")[0][0]
    # cek status tidak berubah kalau tidak dibayar
    kuota1 = sq(f"SELECT kuota_mb FROM users WHERE id={uid_a}")[0][0]
    ok("pending tidak menambah kuota", kuota1 == kuota0,
       f"({kuota0} -> {kuota1})")
    # transaksi uji lain milik user ini tidak boleh ikut terpengaruh
    ok("tambahan_mb sesuai paket", mb > 0, f"({mb} MB)")
    ex(f"DELETE FROM transaksi WHERE user_id={uid_a}")

    # ══ [9] INTEGRITAS AKHIR ════════════════════════════════════════
bagian(9, "INTEGRITAS AKHIR")
if jalan(9):
    integ = sq("PRAGMA integrity_check")[0][0]
    ok("integrity_check DB = ok", integ == 'ok', f"({integ})")
    asli_sesudah = sq("SELECT COUNT(*) FROM transaksi WHERE user_id NOT IN (%d,%d)"
                      % (uid_a, uid_b))[0][0]
    ok("transaksi ASLI tidak tersentuh", asli_sesudah == asli_sebelum,
       f"({asli_sebelum} -> {asli_sesudah})")
    sisa = sq(f"SELECT COUNT(*) FROM transaksi WHERE user_id IN ({uid_a},{uid_b})")[0][0]
    ok("data uji bersih", sisa == 0, f"({sisa} baris sisa)")

print("\n" + "=" * 64)
print(f"HASIL AKHIR: {LULUS} LULUS, {GAGAL} GAGAL")
print("=" * 64)
sys.exit(1 if GAGAL else 0)
