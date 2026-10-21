"""UJI halaman verifikasi di HP — MANDIRI: bikin data uji sendiri, lalu hapus lagi.

AKAR alat lama: bergantung pada nomor 1.001 yang SUDAH dibersihkan dari produksi
=> 4 GAGAL palsu (VALID tidak muncul karena datanya memang tidak ada lagi).
OBAT: alat ini MENANAM data uji sementara di awal dan MENGHAPUSNYA di akhir,
sehingga bisa dijalankan kapan saja tanpa mengotori produksi.

11 asersi:
  ① nomor uji  -> LoA VALID + data lengkap + bukan undefined
  ② nomor palsu -> TIDAK DITEMUKAN + WA baru
  ③ tata letak HP 390px: lebar, scrollWidth, overflow, galat JS
"""
import pathlib, os, json, subprocess, datetime
OUT = pathlib.Path('/tmp/potret_hp'); OUT.mkdir(parents=True, exist_ok=True)
from playwright.sync_api import sync_playwright

CHROME = '/opt/data/home/.cloakbrowser/chromium-151.0.7922.108.6-pro/chrome'
EP = CHROME if os.path.exists(CHROME) else None
HASIL = []
NOMOR = '9.999.1'          # sengaja aneh supaya tidak bentrok nomor asli
NOMOR_PALSU = '8.888.8'

def cek(nama, lulus, ket=''):
    HASIL.append((nama, bool(lulus), ket))
    print(f"  {'✅' if lulus else '❌'} {nama}" + (f" — {ket}" if ket else ''))

def masuk(nama, isi):
    subprocess.run(['docker', 'exec', '-i', 'eduai-app', 'sh', '-c',
                    f'cat > {nama}'], input=isi, capture_output=True, text=True)

def baca(nama):
    return subprocess.run(['docker', 'exec', 'eduai-app', 'cat', nama],
                          capture_output=True, text=True).stdout

# ══ TANAM data uji ══
print('══ menanam data uji sementara ══')
ASLI = baca('/app/data/loa-terbit.json')
json.dump({NOMOR: {
    'nomor': NOMOR, 'nomor_surat': f'{NOMOR}/LOA/JEMT/X/2026',
    'judul': 'UJI MANDIRI VERIFIKASI LoA (data sementara)',
    'penulis': 'Wulan (uji otomatis)', 'afiliasi': 'Tridarma Journal Publishing',
    'id_ojs': 'UJI-MANDIRI-01', 'tanggal_diterima': '17 Oktober 2026',
    'terbit': 'Volume 1, Nomor 2 — Desember 2026',
    'editor': 'Jizenji Tyas Wirastomo', 'diterbitkan_pada': '17 Oktober 2026'}},
    open('/tmp/loa_uji.json', 'w'), indent=1, ensure_ascii=False)
masuk('/app/data/loa-terbit.json', pathlib.Path('/tmp/loa_uji.json').read_text())
print('  data uji ditanam, nomor =', NOMOR)

try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--no-sandbox', '--disable-gpu'], executable_path=EP)
        pg = b.new_page(viewport={'width': 390, 'height': 844},
                        device_scale_factor=2, is_mobile=True, has_touch=True)
        galat = []
        pg.on('console', lambda m: galat.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: galat.append(str(e)))

        pg.goto('https://qr.tridarma.id/', wait_until='networkidle', timeout=45000)
        pg.wait_for_timeout(1200)

        # ① nomor uji
        print('\n══ ① nomor uji', NOMOR, '══')
        pg.fill('#nomor', NOMOR)
        pg.click('button:has-text("Verifikasi")')
        pg.wait_for_timeout(3500)
        t = pg.inner_text('body')
        pg.screenshot(path=str(OUT / 'hp_valid.png'), full_page=True)
        cek('kotak VALID muncul', 'VALID' in t.upper(),
            [l for l in t.split('\n') if 'VALID' in l.upper()][:1])
        cek('judul artikel uji muncul', 'UJI MANDIRI' in t.upper())
        cek('penulis muncul', 'WULAN' in t.upper())
        cek('ID Submission terisi', 'UJI-MANDIRI-01' in t,
            [l for l in t.split('\n') if 'UJI-MANDIRI-01' in l][:1])
        cek('BUKAN undefined', 'undefined' not in t.lower())

        # ② nomor palsu
        print('\n══ ② nomor palsu', NOMOR_PALSU, '══')
        pg.fill('#nomor', NOMOR_PALSU)
        pg.click('button:has-text("Verifikasi")')
        pg.wait_for_timeout(3500)
        t2 = pg.inner_text('body')
        pg.screenshot(path=str(OUT / 'hp_palsu.png'), full_page=True)
        cek('ditolak (TIDAK DITEMUKAN)', 'TIDAK DITEMUKAN' in t2.upper(),
            [l for l in t2.split('\n') if 'TIDAK' in l.upper()][:1])
        cek('WA baru tampil', '0851-7813-8514' in t2 or '0851‑7813‑8514' in t2)

        # ③ tata letak HP
        print('\n══ ③ tata letak HP ══')
        cek('lebar = 390', pg.evaluate('window.innerWidth') == 390,
            pg.evaluate('window.innerWidth'))
        sw = pg.evaluate('document.documentElement.scrollWidth')
        cek('tidak bisa digeser samping', sw <= 390, f'scrollWidth={sw}')
        luber = pg.evaluate('''() => {let n=0;document.querySelectorAll('*').forEach(e=>{
            const r=e.getBoundingClientRect();
            if(r.width>0&&(r.right>391||r.left<-1))n++;});return n;}''')
        cek('tidak ada elemen meluber', luber == 0, f'{luber} elemen')
        cek('tanpa galat JavaScript', not galat, galat[:2])

        b.close()
finally:
    # ══ KEMBALIKAN data asli ══
    print('\n══ membersihkan data uji ══')
    masuk('/app/data/loa-terbit.json', ASLI if ASLI.strip() else '{}')
    sisa = baca('/app/data/loa-terbit.json')
    print('  loa-terbit.json sekarang:', sisa.strip()[:80] or '{}')

print('\n════ HASIL ════')
lulus = sum(1 for _, l, _ in HASIL if l)
print(f'{lulus} LULUS / {len(HASIL)-lulus} GAGAL')
for n, l, k in HASIL:
    if not l:
        print(f'  ❌ {n} — {k}')
