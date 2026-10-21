"""Lihat HTML MENTAH di sekitar tombol — kenapa cuma 1 dari 3?"""
import re
import urllib.request

TOK = open('/app/_tok25b.txt').read().strip()
h = urllib.request.urlopen(f'http://127.0.0.1:8000/tinjau/{TOK}',
                           timeout=40).read().decode('utf-8', 'replace')

#  ambil blok panel catatan saja
i = h.find('panel-isi')
blok = h[i:i + 14000]

print('  ══ potongan HTML panel catatan ══')
for m in re.finditer(r'(tunjuk|Lihat di naskah|Tidak ditemukan)', blok):
    a = max(0, m.start() - 420)
    print('  ' + '─' * 68)
    print('  ' + blok[a:m.end() + 160].replace('\n', '\n  '))
    print()

print('  ══ berapa baris catatan (div class="baris")? ══')
print('   ', blok.count('class="baris"'))

print()
print('  ══ apakah ada "tunjuk-ada" di HTML (bukan CSS)? ══')
body = h[h.find('<body'):]
print('    tunjuk-ada di body  :', body.count('tunjuk-ada'))
print('    data-kutipan di body:', body.count('data-kutipan'))
print('    tb-tunjuk di body   :', body.count('tb-tunjuk'))
