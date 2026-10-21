import pathlib
import re

raw = pathlib.Path('/tmp/g.txt').read_text()
blok = raw[raw.find('HTTP 400: ') + 10:]
for _ in range(6):
    b2 = blok.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
    if b2 == blok:
        break
    blok = b2

print('── potongan mentah (600 kar pertama setelah dibuka) ──')
print(blok[:600])
print()
print('── semua "path" yang disebut ──')
for m in re.finditer(r'"path":\s*\[(.*?)\]', blok, re.S):
    print('   ', ' '.join(m.group(1).split()))
print()
print('── semua "message" yang disebut ──')
for m in re.finditer(r'"message":\s*"([^"]{0,200})', blok):
    print('   ', m.group(1))
