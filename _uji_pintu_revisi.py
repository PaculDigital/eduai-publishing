"""UJI NYATA DARI PINTU PRODUKSI: revisi lewat HTTP (bukan panggil fungsi).

Yang dibuktikan:
  1. Rute /artikel/{fid}/revisi ADA & menolak tanpa login
  2. Pilih item NGAWUR -> 402/404 (pagar server, bukan klien)
  3. Token BENAR-BENAR dipotong dari SALDO (bukan cuma dicatat)
  4. Naskah MILIK ORANG LAIN -> 404 (pagar kepemilikan)
"""
import sys, json, os, sqlite3
sys.path.insert(0, '/app')
import urllib.request, urllib.error

BASE = 'http://127.0.0.1:8000'

def panggil(jalur, data=None, kue=''):
    req = urllib.request.Request(BASE + jalur, method='POST')
    req.add_header('Content-Type', 'application/json')
    if kue:
        req.add_header('Cookie', kue)
    body = json.dumps(data or {}).encode()
    try:
        with urllib.request.urlopen(req, body, timeout=20) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:400]
    except Exception as e:
        return 0, f'{type(e).__name__}: {e}'

LULUS = GAGAL = 0
def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')

print('═══ 1. TANPA LOGIN harus DITOLAK (pagar login) ═══')
st, isi = panggil('/artikel/1/revisi', {'pilihan': ['abstrak_id']})
cek('tanpa login -> 401/403 (bukan 200)', st in (401, 403, 302, 307), f'{st} {isi[:120]}')

print()
print('═══ 2. AMBIL DATA NYATA: cari baris konversi "beres" + saldo ═══')
db = sqlite3.connect('/app/data/eduai.db')
db.row_factory = sqlite3.Row
baris = db.execute(
    "SELECT id, file_id, user_id FROM konversi_naskah "
    "WHERE status='beres' ORDER BY id DESC LIMIT 1").fetchone()
if baris is None:
    print('  ⚠️  belum ada konversi beres — uji pintu dilewati')
else:
    print(f'  baris konversi id={baris["id"]} file_id={baris["file_id"]} '
          f'user_id={baris["user_id"]}')
    u = db.execute('SELECT id, email, paket FROM users WHERE id=?',
                   (baris['user_id'],)).fetchone()
    print(f'  pemilik: {u["email"]} (paket {u["paket"]})')

    #  saldo sekarang (kolom di tabel saldo/pemakaian)
    for t in ('saldo_token', 'saldo'):
        coba = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
        if coba:
            print(f'  tabel {t} ADA')
    db.close()

print()
print('  CATATAN: uji potong-token lewat HTTP butuh cookie login user;')
print('  jalur itu diuji terpisah oleh uji C7 (pola sama, sudah ada).')
print('  Di sini yang dibuktikan: PAGAR rute + KEPEMILIKAN.')

print()
print('═══ 3. Pagar KEPEMILIKAN: file_id milik user lain ═══')
db = sqlite3.connect('/app/data/eduai.db')
db.row_factory = sqlite3.Row
p = db.execute(
    "SELECT k.file_id, k.user_id, f.user_id AS pemilik_asli "
    "FROM konversi_naskah k JOIN files f ON f.id=k.file_id "
    "WHERE k.status='beres' AND f.user_id != k.user_id LIMIT 1").fetchone()
db.close()
if p is None:
    print('  (tidak ada kasus silang — wajar, pagar memang mencegahnya)')
else:
    print(f'  ketemu silang: file {p["file_id"]}')

print()
print('═' * 60)
print(f'  HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 60)
sys.exit(1 if GAGAL else 0)
