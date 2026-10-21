"""Bedah /api/provider-nodes & /api/providers — apakah salah satunya
menerima definisi provider BARU dari user (jalur resmi)?"""
import re
import subprocess

untuk = [
    'provider-nodes/route.js',
    'provider-nodes/[id]/route.js',
    'providers/route.js',
]
for p in untuk:
    aman = p.replace('/', '__').replace('[', '').replace(']', '')
    subprocess.run(['docker', 'cp', f'9router:/app/.next/server/app/api/{p}',
                    f'/tmp/9router_cek/pn_{aman}'], check=False)
    try:
        src = open(f'/tmp/9router_cek/pn_{aman}', encoding='utf-8', errors='replace').read()
    except Exception as e:
        print(p, 'GAGAL:', e)
        continue
    print('=' * 72)
    print(f'{p}  ({len(src)} byte)')
    print('=' * 72)
    # cari handler HTTP (GET/POST/PUT/DELETE) dan field yang dibaca
    handlers = re.findall(r'\b(GET|POST|PUT|PATCH|DELETE)\s*[:=]', src)
    print('  handler:', sorted(set(handlers)))
    for nama in ('kind', 'type', 'baseUrl', 'name', 'provider', 'models',
                 'authType', 'headers', 'transport', 'custom', 'template'):
        if f'"{nama}"' in src or f'{nama}:' in src:
            m = re.search(rf'["\']?{nama}["\']?\s*[:=]', src)
            if m:
                print(f'  [{nama}]', src[max(0, m.start() - 80):m.start() + 160]
                      .replace('\n', ' ')[:240])
    print()
