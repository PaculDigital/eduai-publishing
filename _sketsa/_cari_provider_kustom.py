"""Cari: apakah 9router punya jalur RESMI menambah provider/model kustom
(tanpa mengubah bundle build)?"""
import re
import subprocess

# salin beberapa chunk inti untuk dibaca
for ck in ('9128', '318', '235', '3193', '9820'):
    subprocess.run(['docker', 'cp', f'9router:/app/.next/server/chunks/{ck}.js',
                    f'/tmp/9router_cek/{ck}.js'], check=False)

# cari endpoint API yang berkaitan dengan provider kustom / user-defined
print('== endpoint /api 9router yang mungkin berkaitan ==')
r = subprocess.run(['docker', 'exec', '9router', 'sh', '-c',
                    'ls -d /app/.next/server/app/api/*/ 2>/dev/null'],
                   capture_output=True, text=True)
print(r.stdout)

print('== cari kata "custom" / "user-defined" / "plugin" di chunk ==')
for ck in ('9128', '318', '235'):
    try:
        src = open(f'/tmp/9router_cek/{ck}.js', encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for kata in ('customProvider', 'userProvider', 'providerTemplate',
                 'custom_provider', 'addProvider', 'createProvider'):
        n = src.count(kata)
        if n:
            print(f'  chunk {ck}: {kata} × {n}')
            m = re.search(re.escape(kata), src)
            print('     ...', src[max(0, m.start() - 150):m.start() + 250].replace('\n', ' ')[:380])
