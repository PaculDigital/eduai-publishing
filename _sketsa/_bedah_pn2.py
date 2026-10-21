"""Bedah provider-nodes LANJUTAN: apiType apa saja yang didukung + validasi."""
import re
import subprocess

subprocess.run(['docker', 'cp',
                '9router:/app/.next/server/app/api/provider-nodes/route.js',
                '/tmp/9router_cek/pn_route.js'], check=False)
src = open('/tmp/9router_cek/pn_route.js', encoding='utf-8', errors='replace').read()

print('== potongan fungsi j (POST) — LENGKAP ==')
i = src.find('async function j(a)')
print(src[i:i + 1600])
print()

print('== daftar apiType / jenis node yang dikenali ==')
for kata in ('openai-compatible', 'anthropic-compatible', 'openai-content',
             'apiType', 'isOpenAICompatible', 'isAnthropicCompatible'):
    for m in re.finditer(re.escape(kata), src):
        seg = src[max(0, m.start() - 60):m.start() + 140].replace('\n', ' ')
        print(f'  [{kata}] {seg[:200]}')
        break
