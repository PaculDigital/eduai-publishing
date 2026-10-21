"""ALUR LENGKAP: buka Belajar → minta insight & soal → jawab → dapat skor."""
import http.cookiejar, json, re, time, urllib.error, urllib.parse, urllib.request

BASE = 'http://127.0.0.1:8000'
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
d = urllib.parse.urlencode({'email': 'asih.susanti@eduai.test',
                            'password': 'AsihPutri2026'}).encode()
op.open(BASE + '/masuk', d, timeout=60)
print('  1. masuk ✅')

h = op.open(BASE + '/belajar?naskah=81', timeout=180).read().decode('utf-8', 'replace')
tombol = sorted(set(re.findall(r'href="(/belajar/insight/\d+[^"]*)"', h)))
print('  2. tombol Mulai Belajar:', tombol[:3])
if not tombol:
    print('  ❌ tidak ada tombol'); raise SystemExit(1)

url = tombol[0]
h2 = op.open(BASE + url, timeout=240).read().decode('utf-8', 'replace')
print('  3. halaman belajar →', len(h2), 'byte')
print('     panel Kesiapan :', 'Kesiapan' in h2)
print('     Bank Soal      :', 'Bank Soal' in h2)
print('     tombol Minta   :', h2.count('Minta'))
print('     form jawab     :', h2.count('Kirim Jawaban'))

#  minta insight + bank soal lewat rute yang ada
fid = re.search(r'/belajar/insight/(\d+)', url).group(1)
bab = re.search(r'bab=(\d+)', url)
bab = bab.group(1) if bab else '1'
for minta in ('insight', 'soal'):
    body = urllib.parse.urlencode({'minta': minta, 'bab': bab}).encode()
    try:
        r = op.open(BASE + '/belajar/insight/%s' % fid, body, timeout=600)
        print('  4. minta %-8s → %s %s' % (minta, r.status,
              r.geturl().replace(BASE, '')[:40]))
    except urllib.error.HTTPError as e:
        print('  4. minta %-8s → HTTP %s' % (minta, e.code))

time.sleep(1)
h3 = op.open(BASE + url, timeout=240).read().decode('utf-8', 'replace')
print()
print('  5. SETELAH MINTA:')
print('     kartu soal    :', len(re.findall(r'class="soal lv-', h3)))
print('     tombol jawab  :', h3.count('Kirim Jawaban'))
print('     lencana level :', re.findall(r'class="lencana">([^<]+)', h3))

#  jawab satu soal
if h3.count('Kirim Jawaban'):
    body = urllib.parse.urlencode({
        'minta': 'nilai', 'bab': bab, 'soal_ke': '0',
        'jawaban': ('Faktor yang membuat UMKM kuliner bertahan adalah kemampuan '
                    'beradaptasi dengan perubahan perilaku konsumen dan '
                    'memanfaatkan pemasaran digital untuk memperluas jangkauan.'),
    }).encode()
    t0 = time.time()
    try:
        r = op.open(BASE + '/belajar/uji/%s' % fid, body, timeout=600)
        print()
        print('  6. KIRIM JAWABAN → %s (%.1f dtk)' % (r.status, time.time() - t0))
    except urllib.error.HTTPError as e:
        print('  6. KIRIM JAWABAN → HTTP %s' % e.code)
    h4 = op.open(BASE + url, timeout=240).read().decode('utf-8', 'replace')
    nilai = re.findall(r'class="bulat">\s*(\d+)', h4)
    print('     lingkaran nilai:', nilai[:3])
    print('     panel Kesiapan :', re.findall(r'Kesiapan[^<]*</[^>]+>\s*<[^>]*>\s*(\d+)', h4)[:2])
