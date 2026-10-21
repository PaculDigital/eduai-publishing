"""UJI KLIK SUNGGUHAN dari DALAM container (lewat form HTTP + cookie).
Meniru persis apa yang browser lakukan: isi form → submit → ikuti 303 → baca HTML.
"""
import json, re, time, urllib.request, urllib.parse, http.cookiejar

BASE = 'http://127.0.0.1:8002'
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def get(u):
    r = op.open(u, timeout=90); return r.status, r.read().decode('utf-8', 'replace')

def post(u, data):
    d = urllib.parse.urlencode(data).encode()
    r = op.open(u, d, timeout=180); return r.status, r.geturl(), r.read().decode('utf-8','replace')

#  1. LOGIN lewat form sungguhan
st, html = get(BASE + '/masuk')
print('  1. halaman masuk     :', st, len(html), 'byte')
st, url, html = post(BASE + '/masuk', {'email':'uji-belajar@eduai.test','password':'UjiBelajar123'})
print('  2. login             :', st, '->', url.replace(BASE,''))

#  2. buka halaman bab
st, html = get(BASE + '/belajar/insight/9?bab=1')
jml_form = html.count('name="jawaban"')
print('  3. halaman belajar   :', st, '| form jawab:', jml_form)
print('     panel kesiapan    :', 'Kesiapan Sidang kamu' in html)

#  3. JAWAB soal 1
jawab = ('Digital readiness adalah kesiapan karyawan memakai teknologi baru, mencakup '
         'kemampuan sekaligus kemauan mengadopsinya, sebagai prasyarat agar kinerja '
         'terjaga saat pekerjaan berubah.')
t0 = time.time()
st, url, html = post(BASE + '/belajar/uji/9', {'bab':'1','soal_ke':'0','jawaban':jawab})
dt = time.time() - t0
print(f'  4. kirim jawaban     : {st} ({dt:.1f} dtk) -> {url.split("?")[0].replace(BASE,"")}')

#  4. ikuti halaman hasil & BACA LAYAR
href = url if url.startswith('http') else BASE + url
st, html = get(href)
kartu = html.count('class="nilai-kartu"')
bulat = re.search(r'class="bulat[^"]*">\s*(\d+)\s*<', html)
kecil = re.search(r'class="nilai-kecil">\s*([\d]+/100)\s*<', html)
panel = re.search(r'class="siap-angka">\s*<b>(\d+)</b>', html)
tepat = re.search(r'<b>Yang sudah tepat:</b>\s*([^<]{5,200})', html)
tambah = re.search(r'<b>Yang bisa ditambah:</b>\s*([^<]{5,200})', html)
lv = re.findall(r'class="siap-lv">\s*([a-z]+ \d+)\s*<', html)

print()
print('  ══ BACA LAYAR (bukti MATA) ══')
print('  kartu nilai muncul   :', kartu)
print('  lingkaran nilai      :', bulat.group(1) if bulat else None)
print('  lencana per soal     :', kecil.group(1) if kecil else None)
print('  panel Kesiapan Sidang:', (panel.group(1) + '/100') if panel else None)
print('  per level            :', lv)
if tepat:  print('  "Yang sudah tepat"   :', tepat.group(1).strip()[:110])
if tambah: print('  "Yang bisa ditambah" :', tambah.group(1).strip()[:110])
print('  form tersisa (belum dijawab):', html.count('name="jawaban"'))

ok = bool(kartu >= 1 and bulat and panel)
print()
print('  ' + ('✅ ALUR KLIK SUNGGUHAN BERHASIL' if ok else '❌ ALUR GAGAL'))
