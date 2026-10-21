"""KATALOG HARGA + SUPPLY INFERHUB.
Sumber:
  - https://api.inferhub.dev/v1/models?detail=1  -> pricing.asks_in (daftar harga
    dari tiap penyedia) + official_in/out
  - https://inferhub.dev/api/catalog               -> activeProviders per prefix
Tujuan: cari model PALING MURAH yang PUNYA BANYAK SUPPLY.
"""
import json
import statistics
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')


def ambil(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {KEY}',
                                               'User-Agent': UA})
    return json.loads(urllib.request.urlopen(req, timeout=90)
                      .read().decode('utf-8', 'ignore'))


print('mengambil /v1/models?detail=1 ...')
m = ambil('https://api.inferhub.dev/v1/models?detail=1')
models = m['data']
print('total entri:', len(models))

print('mengambil /api/catalog ...')
cat = ambil('https://inferhub.dev/api/catalog')

# prefix -> activeProviders
prov = {}
for p in cat:
    prov[p.get('prefix')] = p.get('activeProviders', 0)
print('prefix dengan supply:', len(prov))

# ── Susun tabel ──────────────────────────────────────────────────────────
baris = []
for x in models:
    mid = x.get('id') or ''
    if mid.endswith('/'):            # entri prefix saja
        continue
    pr = x.get('pricing') or {}
    asks = pr.get('asks_in') or []
    if not asks:
        continue
    pfx = mid.split('/')[0] if '/' in mid else ''
    baris.append({
        'id': mid,
        'prefix': pfx,
        'supply': prov.get(pfx, 0),
        'harga_min': min(asks),
        'harga_med': statistics.median(asks),
        'harga_max': max(asks),
        'n_ask': len(asks),
        'official_in': pr.get('official_in'),
        'official_out': pr.get('official_out'),
    })

print('model dengan harga:', len(baris))

# simpan mentah
open('/opt/data/services/eduai-publishing/_katalog_inferhub.json', 'w').write(
    json.dumps({'providers': prov, 'model': baris}, ensure_ascii=False, indent=1))
print('disimpan: _katalog_inferhub.json')


def tampil(judul, data, n=25):
    print('\n' + '=' * 112)
    print(judul)
    print('=' * 112)
    print(f"{'model':40s} {'supply':>7s} {'min':>8s} {'med':>8s} {'max':>8s} "
          f"{'n':>3s} {'off_in':>7s}")
    for r in data[:n]:
        print(f"{r['id']:40s} {r['supply']:7d} {r['harga_min']:8.4f} "
              f"{r['harga_med']:8.4f} {r['harga_max']:8.4f} {r['n_ask']:3d} "
              f"{(r['official_in'] or 0):7.2f}")


# 1) Termurah keseluruhan
tampil('A. 25 MODEL TERMURAH (harga_min terkecil)',
       sorted(baris, key=lambda r: r['harga_min']))

# 2) Termurah tapi supply >= 50 (banyak supply)
banyak = [r for r in baris if r['supply'] >= 50]
tampil('B. TERMURAH dengan SUPPLY >= 50 penyedia',
       sorted(banyak, key=lambda r: r['harga_min']))

# 3) SEMUA GEMINI
gem = [r for r in baris if 'gemini' in r['id'].lower()]
tampil('C. SEMUA MODEL GEMINI (urut supply terbanyak)',
       sorted(gem, key=lambda r: -r['supply']), n=40)

# 4) SEMUA DEEPSEEK
ds = [r for r in baris if 'deepseek' in r['id'].lower()]
tampil('D. SEMUA MODEL DEEPSEEK (urut supply terbanyak)',
       sorted(ds, key=lambda r: -r['supply']), n=40)

# 5) Supply terbanyak keseluruhan
tampil('E. SUPPLY TERBANYAK (semua model)', sorted(baris, key=lambda r: -r['supply']))

# 6) Rasio: murah DAN banyak supply
print('\n' + '=' * 112)
print('F. PALING MURAH x SUPPLY BANYAK (supply>=100, urut harga)')
print('=' * 112)
sangat = [r for r in baris if r['supply'] >= 100]
print(f"{'model':40s} {'supply':>7s} {'min':>8s} {'med':>8s} {'off_in':>7s}")
for r in sorted(sangat, key=lambda r: r['harga_min'])[:30]:
    print(f"{r['id']:40s} {r['supply']:7d} {r['harga_min']:8.4f} "
          f"{r['harga_med']:8.4f} {(r['official_in'] or 0):7.2f}")
