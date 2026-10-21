"""UJI E2E editor OnlyOffice LEWAT PROXY (aset lewat domain kita sendiri).

Perubahan besar: oo.bikinaja.id akan DITUTUP. Semua aset editor
(api.js, sdkjs, web-apps) kini diambil lewat /oo/aset/... yang
dilindungi login kita.
"""
import sys
import time

from cloakbrowser import launch

BASE = 'https://eduai.bikinaja.id'
EMAIL, SANDI = 'oo.uji@eduai.local', 'rahasia123'
hasil = []


def cek(n, l, d=''):
    hasil.append((n, l, d))
    print(f"  {'✅' if l else '❌'} {n}" + (f" — {d}" if d else ''))


b = launch(headless=True, humanize=False)
p = b.new_page()
p.set_viewport_size({'width': 1500, 'height': 950})
gagal = []
p.on('response', lambda r: r.status >= 400 and gagal.append((r.status, r.url[:150])))
konsol = []
p.on('console', lambda m: m.type == 'error' and konsol.append(m.text[:200]))

print('1. Login')
p.goto(f'{BASE}/masuk', wait_until='domcontentloaded')
time.sleep(2)
p.fill('#email', EMAIL)
p.fill('#password', SANDI)
p.query_selector('button[type=submit]').click()
time.sleep(4)
cek('Masuk', '/naskah' in p.url, p.url)

print('\n2. Buka editor')
data = p.evaluate("""() => Array.from(document.querySelectorAll('.berkas'))
    .map(e => e.querySelector('a.edit')?.getAttribute('href') || '').filter(Boolean)""")
p.goto(f'{BASE}{data[0]}', wait_until='domcontentloaded')
time.sleep(3)

print('\n3. Cek aset dimuat LEWAT PROXY kita (bukan oo.bikinaja.id)')
aset = p.evaluate("""() => {
    const s = Array.from(document.scripts).map(x => x.src).filter(Boolean);
    return {api_js: s.find(x => x.includes('api.js')) || '(tidak ada)',
            pakai_proxy: !!(s.find(x => x.includes('api.js')) || '').includes('/oo/aset/'),
            ke_oo_langsung: s.some(x => x.includes('oo.bikinaja.id'))};
}""")
print('   api.js:', aset['api_js'][:100])
cek('api.js lewat /oo/aset/ (proxy kita)', aset['pakai_proxy'], aset['api_js'][:80])
cek('TIDAK ada script ke oo.bikinaja.id langsung', not aset['ke_oo_langsung'])

print('\n4. Tunggu iframe editor')
fr_el = None
try:
    p.wait_for_selector("iframe[src*='documenteditor']", timeout=100000)
    for f in p.query_selector_all('iframe'):
        src = f.get_attribute('src') or ''
        if 'editor' in src.lower():
            fr_el = f
            print('   iframe:', src[:120])
            break
except Exception as e:
    print('   tunggu:', str(e)[:130])
cek('Iframe editor muncul', fr_el is not None)

if fr_el:
    time.sleep(25)
    fr = fr_el.content_frame()
    isi = {}
    if fr:
        try:
            isi = fr.evaluate("""() => ({judul: document.title,
                toolbar: !!document.querySelector('#toolbar, .toolbar, #id-toolbar'),
                kanvas: !!document.querySelector('#id-viewer, canvas, #viewport')})""")
        except Exception as e:
            isi = {'galat': str(e)[:100]}
    print('   isi:', isi)
    cek('Editor termuat', bool(isi.get('toolbar') or isi.get('kanvas')), str(isi)[:120])
    cek('Judul dokumen benar', 'ONLYOFFICE' in str(isi.get('judul', '')), str(isi.get('judul'))[:70])

p.screenshot(path='shots/oo-proxy.png')

print('\n5. Request gagal?')
unik = []
seen = set()
for st, u in gagal:
    if (st, u) in seen:
        continue
    seen.add((st, u))
    unik.append((st, u))
for st, u in unik[:8]:
    print(f'   {st} {u}')
cek('Tanpa request gagal', len(unik) == 0, f'{len(unik)} gagal' if unik else 'bersih')

b.close()
print('\n' + '=' * 60)
lulus = sum(1 for _, l, _ in hasil if l)
print(f'HASIL: {lulus}/{len(hasil)} LULUS')
for n, l, d in hasil:
    if not l:
        print(f'  ❌ {n} — {d}')
sys.exit(0 if lulus == len(hasil) else 1)
