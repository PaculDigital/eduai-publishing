import re, pathlib
p = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = p.read_text(encoding='utf-8')
tok = sorted(set(re.findall(r'\{\{\s*([a-zA-Z_]+)\s*\}\}', s)))
print('JUMLAH TOKEN:', len(tok))
for t in tok:
    print('  {{' + t + '}}')
print()
print('JS/script di template?', '<script' in s)
print('baris:', s.count(chr(10)))
