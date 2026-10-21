"""PETA SEMUA PROVIDER INFERHUB + SUPPLY NYATA (bukan hanya yang terdaftar).

Arahan Bos 16Sep26: "jangan pernah mengandalkan satu provider saja... lihat ada
berapa provider di Inferhub, ambil yang rata-rata supply banyak, cari paling
murah, cari paling cepat dan reasoning atau tidak. Kemudian kombinasikan
secara optimal."

Ukur:
  1. BERAPA PROVIDER & BERAPA MODEL per provider (bukan cuma activeProviders)
  2. SUPPLY NYATA: activeProviders rata-rata per model di provider itu
  3. HARGA: officialIn/officialOut
  4. Coba API publik yang mungkin menyingkap "track record / populer":
     /v1/models?detail=1 (pricePoints = jumlah offer?) · /api/catalog
"""
import json
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
UA = {'User-Agent': 'Mozilla/5.0', 'Authorization': f'Bearer {KEY}'}


def get(u):
    r = urllib.request.Request(u, headers=UA)
    return json.load(urllib.request.urlopen(r, timeout=60))


cat = get('https://inferhub.dev/api/catalog')

print('=' * 104)
print('SEMUA PROVIDER INFERHUB — jumlah model, supply, harga')
print('=' * 104)
print(f"{'pref':6s} {'label':22s} {'active':>8s} {'#model':>7s} "
      f"{'supply/model':>13s} {'murahIn':>9s} {'murahOut':>9s}")
print('-' * 104)

rekap = []
for p in sorted(cat, key=lambda x: -(x.get('activeProviders') or 0)):
    models = p.get('models') or []
    aktif = p.get('activeProviders') or 0
    # harga termurah yang punya supply
    hargas = []
    for m in models:
        try:
            i = float(m.get('officialIn') or 0)
            o = float(m.get('officialOut') or 0)
            if i > 0:
                hargas.append((i, o, str(m.get('upstreamModelId') or '')))
        except (TypeError, ValueError):
            pass
    hargas.sort()
    mi = hargas[0][0] if hargas else 0
    mo = hargas[0][1] if hargas else 0
    sm = aktif / len(models) if models else 0
    rekap.append((p.get('prefix'), p.get('label'), aktif, len(models), sm,
                  mi, mo, p.get('status'), p.get('enabled')))
    print(f"{str(p.get('prefix')):6s} {str(p.get('label'))[:22]:22s} "
          f"{aktif:>8d} {len(models):>7d} {sm:>13.0f} {mi:>9.4f} {mo:>9.4f}")

print()
print('=' * 104)
print('PROVIDER DENGAN SUPPLY BANYAK *DAN* BANYAK MODEL (kandidat andalan)')
print('=' * 104)
kand = [r for r in rekap if r[2] >= 400 and r[3] >= 3]
kand.sort(key=lambda r: -r[4])
for pre, lab, aktif, nm, sm, mi, mo, st, en in kand:
    print(f'  {pre:6s} {str(lab)[:24]:26s} active={aktif:>6d} model={nm:>3d} '
          f'supply/model={sm:>7.0f} murah=${mi:.4f}/${mo:.4f} {st}')

print()
print('=' * 104)
print('ATRIBUT LAIN YANG MUNGKIN BERGUNA (cek 1 model penuh)')
print('=' * 104)
p0 = cat[0]
m0 = (p0.get('models') or [{}])[0]
print(json.dumps(m0, indent=1)[:1800])