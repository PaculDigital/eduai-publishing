"""BACA dulu — jangan ubah apa pun. Simpan aturan ingress yang ada."""
import json, urllib.request, pathlib, datetime

AKUN = '6e8bfb7ac4ba0cb10c1c9e5eba7bee41'
TEROWONGAN = '8ae633d2-4726-47e1-aa5d-1d90fe13ffb1'
VAULT = json.loads(pathlib.Path('/opt/data/vault/cloudflare.json').read_text(encoding='utf-8'))
H = {'Authorization': f"Bearer {VAULT['api_token']}",
     'Content-Type': 'application/json'}
BASE = 'https://api.cloudflare.com/client/v4'

# ══ 1. BACA aturan ingress SEKARANG ══
url = f'{BASE}/accounts/{AKUN}/cfd_tunnel/{TEROWONGAN}/configurations'
req = urllib.request.Request(url, headers=H)
isi = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())

aturan = (isi.get('result') or {}).get('config', {}).get('ingress', [])
print('JUMLAH aturan ingress:', len(aturan))
print()
for i, a in enumerate(aturan):
    print(f'  {i:2}. {a.get("hostname") or "(catch-all)":38} -> {a.get("service")}')

# ══ 2. SIMPAN salinan (titik mundur) ══
cadangan = pathlib.Path('/opt/data/services/eduai-publishing/_arsip/ingress-sebelum-qr-tridarma.json')
cadangan.parent.mkdir(parents=True, exist_ok=True)
cadangan.write_text(json.dumps(isi, indent=1, ensure_ascii=False), encoding='utf-8')
print()
print('CADANGAN disimpan:', cadangan)

# ══ 3. Cari aturan tridarma yang ada ══
print()
print('=== aturan bertema tridarma ===')
for i, a in enumerate(aturan):
    h = a.get('hostname') or ''
    if 'tridarma' in h or 'qr' in h:
        print(f'  {i:2}. {h:38} -> {a.get("service")}')

print()
print('=== catch-all (HARUS tetap di akhir) ===')
for i, a in enumerate(aturan):
    if not a.get('hostname'):
        print(f'  {i:2}. (tanpa hostname) -> {a.get("service")}')
