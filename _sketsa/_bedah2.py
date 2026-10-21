"""Bedah LANJUTAN: bentuk definisi provider openrouter + daftar semua provider."""
import re

src = open('/tmp/9router_cek/3753.js', encoding='utf-8', errors='replace').read()

# ── 1. blok definisi provider openrouter (cari id:"openrouter")
i = src.find('id:"openrouter"')
print('=' * 72)
print('DEFINISI PROVIDER OPENROUTER (posisi', i, '):')
print('=' * 72)
print(src[i - 60:i + 1500] if i > 0 else '(tidak ketemu id:"openrouter")')

# ── 2. semua id provider
ids = re.findall(r'\{id:"([a-z0-9\-]+)",priority:', src)
print()
print('=' * 72)
print('SEMUA ID PROVIDER:', len(ids))
print(ids)

# ── 3. contoh provider openai-compatible (yang paling dekat dgn kebutuhan kita)
print()
print('=' * 72)
m = re.search(r'openai-compatible', src)
if m:
    print('CONTOH openai-compatible:', src[max(0, m.start() - 900):m.start() + 400])
