"""Ekstrak bentuk definisi provider dari chunk 9router (baca SALINAN, tidak ubah)."""
import re
import subprocess

# salin chunk ke sisi Wulan
subprocess.run(['docker', 'cp', '9router:/app/.next/server/chunks/3753.js',
                '/tmp/9router_cek/3753.js'], check=False)
src = open('/tmp/9router_cek/3753.js', encoding='utf-8', errors='replace').read()
print('ukuran:', len(src))

# --- 1. cari blok sekitar "openrouter" pada peta provider ---
for m in re.finditer(r'openrouter', src):
    a = max(0, m.start() - 700)
    b = min(len(src), m.start() + 900)
    blok = src[a:b]
    if 'chat/completions' in blok or 'api/v1' in blok:
        print('=' * 70)
        print(blok)
        print()
        break

# --- 2. cari daftar jenis provider (kunci-kunci seperti 'openai-compatible-chat-xxx')
jenis = sorted(set(re.findall(r'"(openai-compatible-chat-[a-z0-9]+)"', src)))
print('JENIS PROVIDER ditemukan:', len(jenis))
print(jenis[:30])

# --- 3. cari definisi yang punya "baseUrl" atau "endpoint"
for m in re.finditer(r'(baseUrl|endpoint|apiBase)\s*:', src):
    print('  ...', src[max(0, m.start()-120):m.start()+180].replace('\n', ' ')[:300])
    break
