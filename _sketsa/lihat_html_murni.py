"""Cari tombol di BAGIAN HTML saja (bukan blok CSS di <head>)."""
import re
import urllib.request

TOK = open('/app/_tok25b.txt').read().strip()
h = urllib.request.urlopen(f'http://127.0.0.1:8000/tinjau/{TOK}',
                           timeout=40).read().decode('utf-8', 'replace')

#  buang <style>...</style> supaya yang tersisa HTML murni
tanpa_css = re.sub(r'<style.*?</style>', '', h, flags=re.S)
tanpa_css = re.sub(r'<script.*?</script>', '', tanpa_css, flags=re.S)

print('  ══ DI HTML MURNI (tanpa CSS/JS) ══')
for x in ['tunjuk-ada', 'tb-tunjuk', 'data-kutipan', 'Lihat di naskah',
          'tunjuk-tidak', 'Tidak ditemukan bagiannya', 'tunjuk-kutipan']:
    print('   %-28s %d' % (x, tanpa_css.count(x)))

print()
print('  ══ jumlah baris catatan ══')
print('    class="baris"  :', tanpa_css.count('class="baris"'))
print('    class="detail" :', tanpa_css.count('class="detail"'))

print()
i = tanpa_css.find('tunjuk-ada')
if i >= 0:
    print('  ══ HTML di sekitar tunjuk-ada ══')
    print(tanpa_css[max(0, i - 700):i + 400])
else:
    print('  ⚠️ tunjuk-ada TIDAK ADA di HTML!')
