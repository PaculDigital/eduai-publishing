import pathlib, re
tpl = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html').read_text(encoding='utf-8')
print('== di mana {{contact_wa}} dipakai? ==')
for i, baris in enumerate(tpl.split(chr(10)), 1):
    if 'contact_wa' in baris or 'contact_email' in baris:
        print(f'  {i}: {baris.strip()[:150]}')
print()
print('== blok tanda tangan / footer template ==')
for i, baris in enumerate(tpl.split(chr(10)), 1):
    if any(k in baris for k in ['sign', 'jabatan', 'nama', 'Chief Editor', 'footer', 'ttd', 'editor_name']):
        print(f'  {i}: {baris.strip()[:130]}')
