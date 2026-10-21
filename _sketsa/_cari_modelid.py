"""KUMPULKAN modelId (UUID) untuk semua model yang dibutuhkan combo.
Endpoint /api/combos butuh modelId, bukan nama model.
"""
import json
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
req = urllib.request.Request('https://inferhub.dev/api/catalog',
                             headers={'Authorization': f'Bearer {KEY}',
                                      'User-Agent': UA})
cat = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())

# prefix -> {label model: uuid}
peta = {}
for p in cat:
    pfx = p.get('prefix')
    for m in p.get('models', []):
        label = m.get('label') or ''
        full = f'{pfx}/{label}' if pfx else label
        peta[full] = {'id': m.get('id'),
                      'label': label,
                      'upstream': m.get('upstreamModelId'),
                      'aktif': p.get('activeProviders'),
                      'status': p.get('status')}

print('total model di katalog:', len(peta))
open('/opt/data/services/eduai-publishing/_peta_modelid.json', 'w').write(
    json.dumps(peta, ensure_ascii=False, indent=1))

CARILIST = [
    'ali/deepseek-v4.1-flash',
    'ag/gemini-3.7-flash-high',
    'cbcn/deepseek-v4.1-flash',
    # kandidat tier 2 (bukan deepseek / gemini)
    'ali/kimi-k2.7-code', 'ali/kimi-k2.6', 'ali/kimi-k3',
    'ali/qwen3.8-max', 'ali/glm-5.3', 'ali/glm-5.2', 'ali/glm-5.3-flash',
    'cbcn/kimi-k2.7', 'cbcn/kimi-k2.6', 'cbcn/kimi-k3',
    'cbcn/minimax-m3', 'cbcn/minimax-m2.7', 'cbcn/glm-5.3-flash',
    'cb/glm-5.3', 'cb/minimax-m3', 'cb/gpt-5.6-luna', 'cb/kimi-k3',
    'cx/gpt-5.6-luna',
]
print()
for c in CARILIST:
    v = peta.get(c)
    print(f'{c:32s} -> ' + (v['id'] if v else '*** TIDAK ADA DI KATALOG ***'))

print()
print('=== semua model kimi ===')
for k in sorted(peta):
    if 'kimi' in k.lower():
        print(f'  {k:34s} {peta[k]["id"]}')
print('=== semua model glm ===')
for k in sorted(peta):
    if 'glm' in k.lower():
        print(f'  {k:34s} {peta[k]["id"]}')
print('=== semua model qwen ===')
for k in sorted(peta):
    if 'qwen' in k.lower():
        print(f'  {k:34s} {peta[k]["id"]}')
print('=== semua model minimax ===')
for k in sorted(peta):
    if 'minimax' in k.lower():
        print(f'  {k:34s} {peta[k]["id"]}')
