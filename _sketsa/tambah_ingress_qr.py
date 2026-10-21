"""Tambah SATU aturan: qr.tridarma.id -> EduAi (localhost:8100).
Jangan sentuh aturan lain. Wildcard *.tridarma.id tetap utuh."""
import json, urllib.request, urllib.error, pathlib, datetime

V = json.loads(pathlib.Path('/opt/data/vault/cloudflare.json').read_text(encoding='utf-8'))
AKUN = V['account_id']
TEROWONGAN = '8ae633d2-4726-47e1-aa5d-1d90fe13ffb1'
H = {'Authorization': f"Bearer {V['api_token']}", 'Content-Type': 'application/json'}
BASE = 'https://api.cloudflare.com/client/v4'
url = f'{BASE}/accounts/{AKUN}/cfd_tunnel/{TEROWONGAN}/configurations'

# ══ 1. BACA yang sekarang ══
req = urllib.request.Request(url, headers=H)
isi = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
cfg = (isi.get('result') or {}).get('config') or {}
ingress = cfg.get('ingress') or []

# simpan cadangan
cap = pathlib.Path(f"/opt/data/services/eduai-publishing/_arsip/ingress-pra-qr-{datetime.datetime.now():%Y%m%d-%H%M%S}.json")
cap.write_text(json.dumps(isi, indent=1, ensure_ascii=False), encoding='utf-8')
print('cadangan :', cap.name)

# ══ 2. sudah ada? ══
ada = [a for a in ingress if (a.get('hostname') or '') == 'qr.tridarma.id']
if ada:
    print('SUDAH ADA:', ada[0])
    raise SystemExit(0)

# ══ 3. sisipkan SEBELUM catch-all, dan SEBELUM wildcard *.tridarma.id ══
baru = {'hostname': 'qr.tridarma.id', 'service': 'http://localhost:8100'}

# cari posisi: sebelum aturan '*.tridarma.id' kalau ada, kalau tidak sebelum catch-all
pos = None
for i, a in enumerate(ingress):
    if (a.get('hostname') or '') == '*.tridarma.id':
        pos = i
        break
if pos is None:
    for i, a in enumerate(ingress):
        if not a.get('hostname'):
            pos = i
            break
if pos is None:
    pos = len(ingress)

ingress2 = ingress[:pos] + [baru] + ingress[pos:]
print(f'disisipkan di posisi {pos} (sebelum aturan ke-{pos})')

# ══ 4. PUT seluruh daftar ══
body = json.dumps({'config': {'ingress': ingress2}}, ensure_ascii=False).encode()
req2 = urllib.request.Request(url, data=body, headers=H, method='PUT')
try:
    hasil = json.loads(urllib.request.urlopen(req2, timeout=30).read().decode())
except urllib.error.HTTPError as e:
    print('GAGAL HTTP', e.code, e.read().decode()[:400]); raise SystemExit(1)

print('success:', hasil.get('success'))
aturan_baru = (hasil.get('result') or {}).get('config', {}).get('ingress', [])
print()
print('=== INGRESS SEKARANG ===')
for i, a in enumerate(aturan_baru):
    print(f'  {i:2}. {a.get("hostname") or "(catch-all)":40} -> {a.get("service")}')
