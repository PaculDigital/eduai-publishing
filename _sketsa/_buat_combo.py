"""BUAT 2 COMBO DI INFERHUB: tier-1 (deepseek+gemini) dan tier-2 (non-ds/gemini).

POST https://inferhub.dev/api/combos
Body wajib: name, slug, members[] = [{kind:'model', modelId:'<uuid>'}]
modelId diambil dari /api/catalog (BUKAN nama model).

Pilihan Bos (tier 1):
  1. ali/DeepSeek V4.1 Flash    (supply 18.949)
  2. ag/gemini-3.7-flash-high   (633, termurah+tercepat)
  3. cbcn/DeepSeek V4.1 Flash   (6.714)

Tier 2 (juara uji): ali/Kimi K2.7 Code, ali/Qwen 3.8 Max, cbcn/GLM 5.3 Flash.
"""
import json
import urllib.error
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
BASE = 'https://inferhub.dev/api'

peta = json.load(open('/opt/data/services/eduai-publishing/_peta_modelid.json'))
# katalog pakai LABEL (huruf besar + spasi); cari dengan normalisasi
norm = {k.lower().replace(' ', '-'): v['id'] for k, v in peta.items()}


def mid(nama_katalog):
    k = nama_katalog.lower().replace(' ', '-')
    return norm.get(k)


# ── susunan combo ────────────────────────────────────────────────────────
TIER1 = [
    ('ali/DeepSeek V4.1 Flash',   'supply 18.949 · $0,0043 · 4,3s'),
    ('ag/Gemini 3.7 Flash',       'supply 633 · $0,0008 · 3,4s (termurah+tercepat)'),
    ('cbcn/DeepSeek V4.1 Flash',  'supply 6.714 · $0,0051 · mirip 1,000'),
]
TIER2 = [
    ('ali/Kimi K2.7 Code',        'supply 18.949 · $0,0009 · 13,0s'),
    ('ali/Qwen 3.8 Max',          'supply 18.949 · $0,0020 · 8,4s'),
    ('cbcn/GLM 5.3 Flash',        'supply 6.714 · $0,0051 · 2,0s'),
]

print('=' * 100)
print('MEMBUAT COMBO DI INFERHUB')
print('=' * 100)


def buat(nama, slug, daftar, selection='cheapest', sticky=True,
         max_ttft=None, min_tps=None):
    print(f'\n>>> {nama}  (slug={slug}, selection={selection})')
    anggota = []
    for label, catatan in daftar:
        i = mid(label)
        if not i:
            print(f'    ❌ modelId TIDAK DITEMUKAN: {label}')
            return None
        anggota.append({'kind': 'model', 'modelId': i})
        print(f'    + {label:28s} {i}   [{catatan}]')

    body = {'name': nama, 'slug': slug, 'members': anggota,
            'selection': selection, 'sticky': sticky}
    if max_ttft is not None:
        body['maxTtftMs'] = max_ttft
    if min_tps is not None:
        body['minTps'] = min_tps

    req = urllib.request.Request(
        f'{BASE}/combos', data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json', 'User-Agent': UA})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        hasil = json.loads(r.read().decode())
        print(f'    ✅ DIBUAT — HTTP {r.status}')
        print(f'       slug: {hasil.get("slug")} | id: {hasil.get("id")}')
        return hasil
    except urllib.error.HTTPError as e:
        pesan = e.read().decode('utf-8', 'ignore')
        print(f'    ❌ GAGAL — HTTP {e.code}: {pesan[:300]}')
        return None
    except Exception as e:
        print(f'    ❌ ERROR {type(e).__name__}: {e}')
        return None


h1 = buat('EduAi Tier 1', 'eduai-tier-1', TIER1,
          selection='cheapest', sticky=True, max_ttft=4000)
h2 = None  # Tier 2 SUDAH dibuat (16Sep26) - jangan dobel

print('\n' + '=' * 100)
print('VERIFIKASI — daftar combo sekarang')
print('=' * 100)
req = urllib.request.Request(f'{BASE}/combos',
                             headers={'Authorization': f'Bearer {KEY}',
                                      'User-Agent': UA})
for c in json.loads(urllib.request.urlopen(req, timeout=60).read().decode()):
    print(f"  {c['slug']:20s} sel={c.get('selection'):9s} "
          f"sticky={c.get('sticky')} anggota={[m.get('model') for m in c.get('members', [])]}")

open('/opt/data/services/eduai-publishing/_combo_dibuat.json', 'w').write(
    json.dumps({'tier1': h1, 'tier2': h2}, ensure_ascii=False, indent=1))
print('\ndisimpan: _combo_dibuat.json')
