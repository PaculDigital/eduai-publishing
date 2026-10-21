"""UJI TAHAN GEMPA T5.1 — kasus rusak ekstrem (wajib GAGAL dengan anggun,
tidak boleh 500/jebol). Acc Bos 27Sep26 'uji sampai tahan gempa'."""
import urllib.request

BASE = 'http://localhost:8000'
LULUS, GAGAL = 0, []


def cek(nama, kondisi):
    global LULUS
    print(('  ✅ ' if kondisi else '  ❌ ') + nama)
    LULUS += kondisi
    if not kondisi:
        GAGAL.append(nama)


def ambil(jalur, tok=None):
    req = urllib.request.Request(BASE + jalur)
    req.add_header('User-Agent', 'Mozilla/5.0 (uji-gempa)')
    if tok:
        req.add_header('Cookie', f'eduai_session={tok}')
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                  # noqa: BLE001
        return 0, str(e)


from app.auth import buat_token                              # noqa: E402
TOK = buat_token(3)

print('— gempa 1: rute aneh —')
for jalur in (
    '/kolaborasi/buka/0', '/kolaborasi/buka/-1',
    '/kolaborasi/buka/99999999', '/kolaborasi/buka/abc',
    '/kolaborasi/kaitkan?token=', '/kolaborasi/kaitkan?token=' + 'x' * 500,
    '/kolaborasi?kait=' + 'j' * 900,
):
    s, isi = ambil(jalur, TOK)
    cek(f'{jalur[:52]} → {s} (bukan 500)', s in (200, 303, 404, 307, 422))

print('— gempa 2: token PALSU panjang/aneh —')
s, isi = ambil('/kolaborasi/kaitkan?token=' + '%20%00%27%22', TOK, )
s2, isi2 = ambil('/kolaborasi/kaitkan?token=' + 'A' * 200, TOK)
cek('SQL/URL injection ditolak anggun', s in (200, 303) and s2 in (200, 303))

print('— gempa 3: cookie PALSU (sesi ngawur) —')
s, isi = ambil('/kolaborasi', 'sesi-palsu-x9y8z7')
cek('sesi ngawur → tidak 500', s in (200, 303, 307, 401, 404))

print('— gempa 4: tanpa cookie sama sekali —')
s, isi = ambil('/kolaborasi')
cek('tanpa cookie → tidak 500', s in (200, 303, 307, 401, 404))

print('— gempa 5: regesi? jalur lama tetap hidup —')
s, isi = ambil('/tinjau/token-ngawur-xyz')
cek('/tinjau token ngawur → halaman ramah (bukan 500)',
    s == 200 and ('tidak' in isi.lower() or 'maaf' in isi.lower()
                  or 'link' in isi.lower()))
s, isi = ambil('/naskah')
cek('/naskah tanpa login → dialihkan (tidak 500)',
    s in (200, 303, 307, 401, 404))

print('— gempa 6: HTML pita tidak bisa diganti oleh isian user —')
s, isi = ambil('/kolaborasi?kait=<script>alert(1)</script>', TOK)
cek('XSS lewat query tidak lolos mentah',
    '<script>alert' not in isi)

print()
print(f'HASIL GEMPA: {LULUS} LULUS / {len(GAGAL)} GAGAL')
if GAGAL:
    print('GAGAL:', GAGAL)
    raise SystemExit(1)
print('TAHAN GEMPA ✅')
