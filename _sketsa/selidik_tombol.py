import re
import urllib.request

TOK = open('/app/_tok25b.txt').read().strip()
h = urllib.request.urlopen(f'http://127.0.0.1:8000/tinjau/{TOK}',
                           timeout=30).read().decode('utf-8', 'replace')

body = h[h.find('<div class="panel-isi">'):]
d = body.find('class="detail"')
t = body.find('tunjuk-ada')
print('   posisi .detail pertama :', d)
print('   posisi tunjuk-ada      :', t)
print('   tunjuk-ada SETELAH .detail?', t > d)

#  hitung kedalaman div untuk tahu apakah tombol berada DI DALAM .detail
i = body.find('<div class="detail"')
if i >= 0:
    depth = 0
    j = i
    akhir = None
    while j < len(body):
        k = body.find('<div', j + 1)
        l = body.find('</div>', j + 1)
        if l < 0:
            break
        if k >= 0 and k < l:
            depth += 1
            j = k
        else:
            depth -= 1
            j = l
            if depth == 0:
                akhir = l
                break
    print('   .detail berakhir di   :', akhir)
    print('   tombol DI DALAM .detail?', i < t < (akhir or len(body)))

print()
print('   ── CSS yang menyembunyikan ──')
for baris in h.splitlines():
    if 'detail{display' in baris or 'buka .detail' in baris:
        print('  ', baris.strip()[:100])
