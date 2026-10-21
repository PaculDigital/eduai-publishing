import pathlib
D = pathlib.Path('/opt/data/services/eduai-publishing')
f = D / 'app/templates/loa/loa-jemt.html'
s = f.read_text(encoding='utf-8')

print('== tampilkan baris di sekitar "Chief Editor JEMT," ==')
for i, baris in enumerate(s.split(chr(10)), 1):
    if 'Chief Editor JEMT' in baris:
        print(f'  {i}: {repr(baris)}')

# hapus baris itu (apa pun spasinya)
s2 = '\n'.join(l for l in s.split('\n') if 'Chief Editor JEMT,' not in l)
f.write_text(s2, encoding='utf-8')
print()
print('sesudah hapus -> masih ada?', 'Chief Editor JEMT,' in s2)

print()
print('== blok tanda tangan sesudahnya ==')
for i, baris in enumerate(s2.split('\n'), 1):
    if any(k in baris for k in ['class="sign"', 'class="nama"', 'class="jabatan"', 'class="ttd"', 'editor_name']):
        print(f'  {i}: {baris.strip()[:120]}')
