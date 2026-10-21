"""Bedah fitur TRANSLATOR 9router — bentuk aturannya seperti apa?"""
import re
import subprocess

for p in ('translate', 'save', 'load'):
    subprocess.run(['docker', 'cp', f'9router:/app/.next/server/app/api/translator/{p}/route.js',
                    f'/tmp/9router_cek/translator_{p}.js'], check=False)

for p in ('translate', 'save', 'load'):
    try:
        src = open(f'/tmp/9router_cek/translator_{p}.js', encoding='utf-8', errors='replace').read()
    except Exception as e:
        print(p, 'GAGAL:', e)
        continue
    print('=' * 72)
    print(f'ROUTE translator/{p}  ({len(src)} byte)')
    print('=' * 72)
    # cari field yang diharapkan
    for pola in (r'body\.(\w+)', r'json\(\)\.(\w+)', r'searchParams\.get\("(\w+)"\)',
                 r'request\.json\(\)'):
        for m in re.finditer(pola, src):
            pass
    fields = sorted(set(re.findall(r'(?:body|payload|data)\.([a-zA-Z_]{3,24})', src)))
    print('  field yang dibaca:', fields[:25])

    # cari kata kunci penting
    for kata in ('providerId', 'modelId', 'template', 'transform', 'rules',
                 'requestTransform', 'responseTransform', 'prompt', 'systemPrompt',
                 'isCustom', 'modelAlias'):
        if kata in src:
            m = re.search(re.escape(kata), src)
            print(f'  [{kata}]', src[max(0, m.start() - 100):m.start() + 180].replace('\n', ' ')[:270])
    print()
