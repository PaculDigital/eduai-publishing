import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

print('== semua baris yang menyebut WA / contact_wa / footer ==')
for i, baris in enumerate(s.split(chr(10)), 1):
    if 'contact_wa' in baris or 'WA:' in baris or 'class="footer"' in baris or 'footer .right' in baris:
        print(f'  {i}: {baris.strip()[:150]}')

print()
print('== blok FOOTER penuh (cari posisinya) ==')
baris = s.split(chr(10))
for i, b in enumerate(baris, 1):
    if 'class="footer"' in b:
        for j in range(i-1, min(i+9, len(baris))):
            print(f'  {j+1}: {baris[j].strip()[:140]}')
        break
