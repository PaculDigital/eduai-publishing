import pathlib, re, fitz
D = pathlib.Path('/opt/data/services/eduai-publishing')
Z = pathlib.Path('/tmp/loa2_x/tridarma-loa')

print('=== 1. TEMPLATE ASLI ZIP-2: struktur kop ===')
s = (Z / 'agent/template-loa-jemt-agent.html').read_text(encoding='utf-8')
for i, b in enumerate(s.split('\n'), 1):
    if any(k in b for k in ['kop-detail', 'E-ISSN', 'Web:', 'Email:', 'class="meta"', 'class="pub"']):
        print(f'  {i}: {b.strip()[:135]}')

print()
print('=== 2. Kontoh JADI di ZIP (LoA-001) — struktur kop ===')
s2 = (Z / 'agent/LoA-001-LOA-JEMT-X-2026.html').read_text(encoding='utf-8')
for i, b in enumerate(s2.split('\n'), 1):
    if any(k in b for k in ['kop-detail', 'E-ISSN', 'Web:', 'Email:', 'class="meta"']):
        print(f'  {i}: {b.strip()[:135]}')
