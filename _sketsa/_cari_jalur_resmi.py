"""Cari jalur RESMI: 9router punya endpoint provider-nodes & providers.
Cek apakah salah satunya menerima definisi provider BARU dari user."""
import json
import re
import subprocess

# endpoint yang menarik: provider-nodes, providers, translator
for nama in ('provider-nodes', 'providers', 'translator'):
    print('=' * 70)
    print('ENDPOINT /api/' + nama)
    print('=' * 70)
    r = subprocess.run(
        ['docker', 'exec', '9router', 'sh', '-c',
         f'find /app/.next/server/app/api/{nama} -name "*.js" 2>/dev/null | head -6'],
        capture_output=True, text=True)
    print(r.stdout)

# cari kata kunci di chunk soal provider kustom / translator
src_semua = {}
for ck in ('9128', '318', '235', '3193', '9820'):
    try:
        src_semua[ck] = open(f'/tmp/9router_cek/{ck}.js', encoding='utf-8', errors='replace').read()
    except Exception:
        pass

print('=' * 70)
print('CARI istilah penerjemah / format khusus')
print('=' * 70)
for kata in ('translator', 'buildRequest', 'transformRequest', 'bodyTemplate',
             'requestTemplate', 'responsesApi', 'customEndpoint'):
    for ck, src in src_semua.items():
        n = src.count(kata)
        if n:
            print(f'  {kata:20s} chunk {ck}: {n}×')
            break
