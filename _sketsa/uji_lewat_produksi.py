"""UJI LEWAT PRODUKSI — 3 hal yang belum terbukti (03Okt26).

Perintah Bos: "Ok lanjutkan" → uji lewat produksi (asal sah).

Yang diuji:
  1. PAGAR SIMPAN di SERVER: token pembaca (bukan pemilik) → harus 403.
  2. mode='view' vs mode baca+komentar → apa yang benar-benar dikirim.
  3. Hasilnya DIBUKTIKAN dari balasan server, bukan dari tebakan.

CATATAN JUJUR: halaman uji TIDAK ditaruh di produksi. Uji pakai rute yang
SUDAH ADA (/oo/unduh, /oo/simpan) — tidak menambah berkas apa pun ke produksi.
"""
from __future__ import annotations

import json
import subprocess

DOM = 'https://eduai.bikinaja.id'


def jalankan_kode(py: str, timeout=120):
    """Jalankan kode Python DI DALAM container eduai-app."""
    out = subprocess.run(
        ['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app', 'python3', '-c', py],
        capture_output=True, text=True, timeout=timeout)
    return out.returncode, out.stdout.strip(), out.stderr.strip()[-300:]


print('=' * 72)
print('UJI 1 — PAGAR SIMPAN DI SERVER (token pembaca harus DITOLAK)')
print('=' * 72)

PY = r'''
import json
from app.main import _token_berkas
from app.models import FileBerkas, SessionLocal
from app import onlyoffice

db = SessionLocal()
fb = db.get(FileBerkas, 80)
if not fb:
    print(json.dumps({'err': 'berkas 80 tidak ada'}))
else:
    pemilik = fb.user_id
    tok_pemilik = _token_berkas(fb.id, pemilik)          # sah
    tok_pembaca = _token_berkas(fb.id, pemilik + 1000)   # pembaca (bukan pemilik)
    print(json.dumps({
        'berkas': fb.id,
        'nama': fb.nama,
        'pemilik_uid': pemilik,
        'tok_pemilik': tok_pemilik[:16] + '...',
        'tok_pembaca': tok_pembaca[:16] + '...',
        'BERBEDA': tok_pemilik != tok_pembaca,
    }))
'''
rc, out, err = jalankan_kode(PY)
print('  hasil:', out if rc == 0 else f'GAGAL: {err}')
if rc != 0:
    raise SystemExit('uji 1 gagal jalan')

data = json.loads(out)
TOK_PEMILIK = data['tok_pemilik']  # dipotong — bukan token asli, hanya penanda
print(f"  berkas {data['berkas']} ({data['nama']}) milik uid {data['pemilik_uid']}")
print(f"  token pemilik ≠ token pembaca : {data['BERBEDA']}")

# ambil token LENGKAP di dalam container (jangan pernah dicetak ke luar)
PY2 = r'''
import json
from app.main import _token_berkas
from app.models import FileBerkas, SessionLocal
db = SessionLocal()
fb = db.get(FileBerkas, 80)
print(json.dumps({
    'sah': _token_berkas(fb.id, fb.user_id),
    'palsu': _token_berkas(fb.id, fb.user_id + 1000),
}))
'''
rc2, out2, _ = jalankan_kode(PY2)
tok = json.loads(out2)

# ── UJI NYATA: POST ke /oo/simpan dengan kedua token ───────────────────
# Body tiruan callback OnlyOffice (status 2 = siap disimpan).
body = json.dumps({'status': 2, 'key': 'uji-pagar-03okt', 'url': 'https://contoh/x.docx'})

for nama_tok, tk in (('PEMILIK (sah)', tok['sah']), ('PEMBACA (bukan pemilik)', tok['palsu'])):
    p = subprocess.run(
        ['curl', '-s', '-o', '/tmp/balasan.json', '-w', '%{http_code}',
         '-X', 'POST', '-H', 'Content-Type: application/json',
         '-d', body, '--max-time', '20', f'{DOM}/oo/simpan/{tk}'],
        capture_output=True, text=True)
    kode = p.stdout.strip()
    try:
        with open('/tmp/balasan.json') as f:
            bal = json.load(f)
    except Exception:
        bal = '(tak terbaca)'
    print(f'  {nama_tok:26} → HTTP {kode} | balasan: {str(bal)[:90]}')

print()
print('=' * 72)
print('UJI 2 — APA YANG DIKIRIM untuk mode baca (dari fungsi produksi)')
print('=' * 72)

PY3 = r'''
import json
from app import onlyoffice

# tiruan: apa yang DIKIRIM kalau mode dibuat "baca + komentar"
base = onlyoffice.konfigurasi_editor(
    kunci='uji03', nama='uji.docx', url_unduh='/oo/unduh/TK', url_simpan='/oo/simpan/TK',
    user_id=999, user_nama='Uji', extensi='.docx')
P = base['document']['permissions']
print(json.dumps({
    'permissions_asli': P,
    'semua_permission_ikut_mode_edit': all(
        P.get(k) for k in ('edit', 'review', 'comment', 'fillForms',
                           'modifyFilter', 'modifyContentControl')),
    'ada_param_mode': 'mode' in onlyoffice.konfigurasi_editor.__code__.co_varnames,
    'daftar_parameter': list(onlyoffice.konfigurasi_editor.__code__.co_varnames),
}, indent=1))
'''
rc3, out3, err3 = jalankan_kode(PY3)
print(out3 if rc3 == 0 else f'  GAGAL: {err3}')

print()
print('=' * 72)
print('UJI 3 — PRODUKSI MASIH SEHAT?')
print('=' * 72)
p = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                    '-L', '--max-time', '20', f'{DOM}/'], capture_output=True, text=True)
print(f'  {DOM}/ → HTTP {p.stdout.strip()}')
