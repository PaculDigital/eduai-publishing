"""BACA aturan ingress yang ada — pakai account_id DARI VAULT."""
import json, urllib.request, urllib.error, pathlib

V = json.loads(pathlib.Path('/opt/data/vault/cloudflare.json').read_text(encoding='utf-8'))
AKUN = V['account_id']
TEROWONGAN = '8ae633d2-4726-47e1-aa5d-1d90fe13ffb1'
H = {'Authorization': f"Bearer {V['api_token']}", 'Content-Type': 'application/json'}
BASE = 'https://api.cloudflare.com/client/v4'

print('account_id (dari vault):', AKUN)
print()

url = f'{BASE}/accounts/{AKUN}/cfd_tunnel/{TEROWONGAN}/configurations'
try:
    req = urllib.request.Request(url, headers=H)
    isi = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:300]); raise SystemExit(1)

aturan = (isi.get('result') or {}).get('config', {}).get('ingress', [])
print('JUMLAH aturan ingress:', len(aturan))
print()
for i, a in enumerate(aturan):
    print(f'  {i:2}. {a.get("hostname") or "(catch-all)":40} -> {a.get("service")}')

cadangan = pathlib.Path('/opt/data/services/eduai-publishing/_arsip/ingress-sebelum-qr-tridarma.json')
cadangan.parent.mkdir(parents=True, exist_ok=True)
cadangan.write_text(json.dumps(isi, indent=1, ensure_ascii=False), encoding='utf-8')
print()
print('CADANGAN:', cadangan)
print()
print('=== aturan tridarma / qr ===')
for i, a in enumerate(aturan):
    h = a.get('hostname') or ''
    if 'tridarma' in h or h.startswith('qr.'):
        print(f'  {i:2}. {h:40} -> {a.get("service")}')
print()
print('=== catch-all ===')
for i, a in enumerate(aturan):
    if not a.get('hostname'):
        print(f'  {i:2}. (catch-all) -> {a.get("service")}')
