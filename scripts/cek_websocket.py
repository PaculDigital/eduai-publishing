"""Cek apakah koneksi socket.io editor BENAR-BENAR tersambung."""
import time

from cloakbrowser import launch

BASE = 'https://eduai.bikinaja.id'
EMAIL, SANDI = 'oo.uji@eduai.local', 'rahasia123'

b = launch(headless=True, humanize=False)
p = b.new_page()
p.set_viewport_size({'width': 1500, 'height': 950})

ws_ok = []
ws_gagal = []
p.on('websocket', lambda ws: ws_ok.append(ws.url[:110]))
http_405 = []
p.on('response', lambda r: r.status == 405 and http_405.append(r.url[:110]))
gagal = []
p.on('response', lambda r: r.status >= 400 and gagal.append((r.status, r.url[:100])))

p.goto(f'{BASE}/masuk', wait_until='domcontentloaded')
time.sleep(2)
p.fill('#email', EMAIL)
p.fill('#password', SANDI)
p.query_selector('button[type=submit]').click()
time.sleep(4)

data = p.evaluate("""() => Array.from(document.querySelectorAll('.berkas'))
    .map(e => e.querySelector('a.edit')?.getAttribute('href') || '').filter(Boolean)""")
p.goto(f'{BASE}{data[0]}', wait_until='domcontentloaded')
p.wait_for_selector("iframe[src*='documenteditor']", timeout=100000)

print('menunggu 40 detik (biar socket.io sempat connect)...')
time.sleep(40)

print('\n=== WEBSOCKET YANG BERHASIL TERSAMBUNG ===')
for w in ws_ok[:6]:
    print('  ✅', w)
if not ws_ok:
    print('  (tidak ada WebSocket)')

print('\n=== HTTP 405 ===')
for u in http_405[:6]:
    print('  ⚠️', u)
if not http_405:
    print('  (tidak ada 405)')

print('\n=== SEMUA REQUEST >=400 ===')
unik = []
for st, u in gagal:
    if (st, u) not in unik:
        unik.append((st, u))
for st, u in unik[:10]:
    print(f'  {st} {u}')
if not unik:
    print('  (BERSIH — tidak ada request gagal)')

# cek editor benar-benar bisa edit (ada status koneksi)
fr_el = None
for f in p.query_selector_all('iframe'):
    if 'editor' in (f.get_attribute('src') or '').lower():
        fr_el = f
        break
if fr_el:
    fr = fr_el.content_frame()
    st = fr.evaluate("""() => {
        const A = window.Asc && window.Asc.editor;
        return {judul: document.title,
                ada_editor: !!A,
                isViewMode: A ? A.isViewMode : null,
                terhubung: !!(A && A.CoAuthoringApi),
                pengguna: document.querySelectorAll('.asc-username').length};
    }""")
    print('\n=== STATUS EDITOR ===')
    for k, v in st.items():
        print(f'  {k}: {v}')

p.screenshot(path='shots/oo-ws.png')
b.close()

print('\n' + '=' * 58)
print(f"WebSocket tersambung : {len(ws_ok)}")
print(f"HTTP 405            : {len(http_405)}")
print(f"Request gagal       : {len(unik)}")
print('=' * 58)
