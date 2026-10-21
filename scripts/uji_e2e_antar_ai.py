"""UJI E2E ANTAR-AI (pertanyaan Bos 27Sep26): komentar telaahan AI PEMBIMBING
dibaca AI MAHASISWA untuk revisi?

Alur yang diuji (persis produksi):
  1. Ambil catatan telaahan ASLI yang dibuat AI T5.2 (DB, bimbingan uji 3)
  2. Kirim sebagai KOMENTAR ke /api/ai/v1/revisi (jalur mahasiswa, domain)
  3. Pantau proses latar → ambil hasil
  4. Asersi: hasil menyebut ISI catatan (AI mahasiswa MEMAHAMI komentar AI
     pembimbing), token nyata, tanpa penanda internal.

JALANKAN: python3 scripts/uji_e2e_antar_ai.py  (dari host; butuh E2E env)
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

sys.path.insert(0, '/opt/data/services/eduai-publishing')
BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
LULUS, GAGAL = 0, []


def cek(nama, ok, ket=''):
    global LULUS
    if ok:
        LULUS += 1
        print(f'  ✅ {nama}  {ket}')
    else:
        GAGAL.append(nama)
        print(f'  ❌ {nama}  {ket}')


cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
TOK_SESI = ''          # diisi manual setelah ambil token (CookieJar tidak andal)


def buka(path, data=None, metode=None, timeout=120):
    h = {'User-Agent': UA}
    if TOK_SESI:
        h['Cookie'] = f'eduai_session={TOK_SESI}'
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode()
        h['Content-Type'] = 'application/json'
    try:
        r = OP.open(urllib.request.Request(BASE + path, data=data, headers=h,
                                           method=metode), timeout=timeout)
        return r.status, r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')


EMAIL = os.getenv('E2E_EMAIL', 'uji-asing-t52@eduai.test')
SANDI = os.getenv('E2E_SANDI', 'UjiT52123!')

# ── 1. AMBIL KOMENTAR AI PEMBIMBING DARI DB (produksi, read-only) ──────
print('── 1. Catatan telaahan AI pembimbing (dari DB) ──────────')
r = os.popen(
    "docker exec eduai-app sh -c 'cd /app && python /app/baca_catatan.py'"
).read()
for baris in r.strip().splitlines():
    if baris.startswith('HASILJSON='):
        try:
            komentar_ai = json.loads(baris.split('=', 1)[1])
        except Exception:
            komentar_ai = []
cek('komentar telaahan AI pembimbing ada di DB', len(komentar_ai) >= 1,
    f'{len(komentar_ai)} catatan')
if not komentar_ai:
    print('  jalankan dulu tombol Minta telaahan (E2E T5.2) → lalu ulangi')
    sys.exit(1)
for k in komentar_ai[:3]:
    print('   ·', k[:100])

# ── 2. LOGIN mahasiswa (pemilik naskah = user 3) ────────────────────────
print('── 2. Login mahasiswa ────────────────────────────────────')
#  user uji 4 bukan pemilik file → pakai sesi token user 3 langsung (uji)
tok = os.popen("docker exec eduai-app sh -c 'cd /app && python -c \""
               "from app.auth import buat_token; print(buat_token(3))\"'"
               ).read().strip()
TOK_SESI = tok.strip().splitlines()[-1] if tok.strip() else ''
cj.clear()
req = urllib.request.Request(BASE + '/naskah', headers={
    'User-Agent': UA, 'Cookie': f'eduai_session={TOK_SESI}'})
try:
    resp = OP.open(req, timeout=60)
    s, isi = resp.status, resp.read().decode('utf-8', 'ignore')
except urllib.error.HTTPError as e:
    s, isi = e.code, e.read().decode('utf-8', 'ignore')
cek('login (sesi token user 3) → halaman naskah', s == 200, f'HTTP {s}')
fid = None
m = re.findall(r'/edit/(\d+)', isi)
if m:
    fid = int(max(m, key=int))
cek('file_id naskah ditemukan', fid is not None, f'file_id={fid}')

# ── 3. KIRIM KOMENTAR AI PEMBIMBING KE AI MAHASISWA ─────────────────────
print('── 3. Kirim komentar (AI pembimbing) → AI mahasiswa ─────')
body = {'komentar': komentar_ai[:2]}
if fid:
    body['file_id'] = fid
s, b = buka('/api/ai/v1/revisi', data=body, metode='POST', timeout=180)
print('   HTTP', s, b[:160])
kode = ''
try:
    j = json.loads(b)
    kode = j.get('kode') or ''
except Exception:
    j = {}
cek('revisi diterima (200 + kode proses)', s == 200 and bool(kode),
    f'HTTP {s} kode={kode}')
if s == 409:
    body['setuju_bagian'] = True
    s, b = buka('/api/ai/v1/revisi', data=body, metode='POST', timeout=180)
    try:
        j = json.loads(b)
        kode = j.get('kode') or ''
    except Exception:
        j = {}
    cek('gerbang izin → setuju → diterima', s == 200 and bool(kode),
        f'HTTP {s}')
if not kode:
    sys.exit(1)

# ── 4. PANTAU ────────────────────────────────────────────────────────────
print('── 4. Pantau proses ──────────────────────────────────────')
status, ring, hasil = '', {}, ''
t0 = time.monotonic()
for _ in range(60):
    time.sleep(10)
    s, b = buka(f'/api/ai/v1/proses/{kode}', timeout=60)
    try:
        ring = json.loads(b) or {}
    except Exception:
        ring = {}
    status = ring.get('status') or ''
    if status in ('selesai', 'gagal'):
        break
detik = time.monotonic() - t0
cek('proses SELESAI', status == 'selesai',
    f'{status} · {detik:.0f}s · galat={ring.get("galat") or "-"}')
cek('token_in nyata (AI benar dipanggil)', (ring.get('token_in') or 0) > 0,
    f'in={ring.get("token_in")} out={ring.get("token_out")}')

s, b = buka(f'/api/ai/v1/proses/{kode}/hasil', timeout=120)
try:
    hasil = (json.loads(b) or {}).get('jawaban') or ''
except Exception:
    hasil = ''
cek('hasil revisi terisi', len(hasil) > 50, f'{len(hasil):,} kar')

# ── 5. BUKTI "ANTAR-AI SALING PAHAM" ────────────────────────────────────
print('── 5. AI mahasiswa memahami komentar AI pembimbing? ──────')
kunci_kata = set()
for k in komentar_ai[:2]:
    for w in re.findall(r'[a-z]{6,}', k.lower()):
        kunci_kata.add(w)
potong_hasil = hasil.lower()
t_ep = sum(1 for w in kunci_kata if w in potong_hasil)
print(f'   kata kunci komentar: {sorted(kunci_kata)[:12]}')
print(f'   kata kunci muncul di hasil: {t_ep}/{len(kunci_kata)}')
cek('hasil RELEVAN dgn isi komentar (≥30% kata kunci)',
    len(kunci_kata) > 0 and t_ep / len(kunci_kata) >= 0.3,
    f'{t_ep}/{len(kunci_kata)}')
terlarang = ['[PROFIL]', 'Guardrail', 'K1-CAKUPAN', 'Paradigma=']
buruk = [t for t in terlarang if t in hasil]
cek('bebas penanda internal', not buruk, str(buruk))
print()
print('   --- cuplikan hasil revisi ---')
for baris in hasil[:600].splitlines()[:8]:
    print('   ', baris[:110])

print()
print(f'HASIL: {LULUS} LULUS / {len(GAGAL)} GAGAL')
sys.exit(0 if not GAGAL else 1)
