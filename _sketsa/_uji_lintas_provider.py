"""UJI OPTIMAL LINTAS PROVIDER — prompt PENDEK (arahan Bos: biar cepat).

Arahan Bos 16Sep26: "jangan pernah mengandalkan satu provider saja... ambil
yang rata-rata supply banyak, cari paling murah, cari paling cepat dan
reasoning atau tidak. Kemudian kombinasikan secara optimal."

Indikator yang dipakai:
  1. JUMLAH PENAWARAN (len(pricePointsIn)) = berapa banyak penyedia menjual
     model ini → MAKIN BANYAK = makin tahan gangguan (indikator track record)
  2. SUPPLY provider (activeProviders)
  3. HARGA (officialIn/officialOut)
  4. KECEPATAN (detik, prompt pendek)
  5. REASONING atau tidak (reasoning_tokens)
  6. LOLOS = benar-benar menjawab (len > 0, finish=stop)

Hasil ditulis ke _hasil_uji_lintas_provider.json
"""
import json
import time
import urllib.error
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
BASE = 'https://inferhub.dev/v1'
UA = {'User-Agent': 'Mozilla/5.0', 'Authorization': f'Bearer {KEY}',
      'Content-Type': 'application/json'}


def get(u):
    r = urllib.request.Request(u, headers=UA)
    return json.load(urllib.request.urlopen(r, timeout=60))


cat = get('https://inferhub.dev/api/catalog')

# ── kumpulkan model kandidat: provider supply besar, harga wajar ───────────
kandidat = []
for p in cat:
    aktif = p.get('activeProviders') or 0
    if aktif < 400:                       # supply kecil → rapuh, lewati
        continue
    for m in (p.get('models') or []):
        um = str(m.get('upstreamModelId') or '')
        try:
            hin = float(m.get('officialIn') or 0)
            hout = float(m.get('officialOut') or 0)
        except (TypeError, ValueError):
            continue
        if hin <= 0 or hin > 2.0:          # mahal → tidak masuk hitungan
            continue
        tawaran = len(m.get('pricePointsIn') or [])
        kandidat.append({
            'model': f"{p.get('prefix')}/{um}",
            'provider': p.get('prefix'),
            'supply': aktif,
            'tawaran': tawaran,
            'in': hin, 'out': hout,
        })

# dedupe & urutkan: tawaran terbanyak + supply terbesar + termurah
seen = set()
unik = []
for k in kandidat:
    if k['model'] in seen:
        continue
    seen.add(k['model'])
    unik.append(k)
unik.sort(key=lambda k: (-k['tawaran'], -k['supply'], k['in']))

PESAN = ('Balas persis satu baris: "SIAP".')


def ukur(model):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': PESAN}],
        'max_tokens': 2000,           # pendek saja — uji cepat
        'temperature': 0.2,
    }).encode()
    req = urllib.request.Request(f'{BASE}/chat/completions', data=body,
                                 headers=UA)
    t0 = time.monotonic()
    try:
        raw = urllib.request.urlopen(req, timeout=120).read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return {'ok': False, 'galat': f'HTTP {e.code}', 'pesan':
                e.read().decode('utf-8', 'ignore')[:110]}
    except Exception as e:
        return {'ok': False, 'galat': type(e).__name__, 'pesan': str(e)[:110]}
    detik = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    try:
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    except Exception as e:
        return {'ok': False, 'galat': 'PARSE', 'pesan': str(e)[:110]}
    ch = j['choices'][0]
    u = j.get('usage') or {}
    rt = (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    isi = ch['message'].get('content') or ''
    return {'ok': bool(isi) and ch.get('finish_reason') == 'stop',
            'detik': detik, 'dipakai': j.get('model'), 'len': len(isi),
            'reasoning': rt, 'finish': ch.get('finish_reason')}


print('=' * 108)
print('UJI LINTAS PROVIDER — prompt PENDEK (arahan Bos). Urut: tawaran terbanyak')
print('=' * 108)
print(f"{'#':>3} {'model':34s} {'prov':5s} {'tawaran':>7s} {'supply':>7s} "
      f"{'$in':>6s} {'detik':>6s} {'reas':>6s}  hasil")

hasil = []
for n, k in enumerate(unik[:14], start=1):
    r = ukur(k['model'])
    k.update(r)
    hasil.append(k)
    if r['ok']:
        print(f"{n:>3} {k['model']:34s} {k['provider']:5s} {k['tawaran']:>7d} "
              f"{k['supply']:>7d} {k['in']:>6.3f} {r['detik']:>6.1f} "
              f"{r['reasoning']:>6d}  LULUS ({r['len']} kar)")
    else:
        print(f"{n:>3} {k['model']:34s} {k['provider']:5s} {k['tawaran']:>7d} "
              f"{k['supply']:>7d} {k['in']:>6.3f} {'-':>6s} {'-':>6s}  "
              f"GAGAL {r.get('galat')} {str(r.get('pesan'))[:60]}")
    time.sleep(1.5)

with open('/tmp/_hasil_uji_lintas_provider.json', 'w') as f:
    json.dump(hasil, f, indent=1)
print('\n(hasil disimpan: /tmp/_hasil_uji_lintas_provider.json)')