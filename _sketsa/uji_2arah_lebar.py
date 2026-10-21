"""Uji 2 ARAH lebar dokumen /tinjau di HP 390px (27Sep26).

Arah SEHAT : keadaan biasa harus 390px.
Arah DIRUSAK: suntik teks TANPA SPASI (URL panjang / istilah tanpa spasi)
             ke .kertas — kalau scrollWidth melebar, itu AKAR 539px.

Dijalankan dari HOST (Chrome CDP :9333).
"""
import json
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                        # noqa: E402

LEBAR = 390


def token_tinjau():
    src = '/opt/data/services/eduai-publishing/_sketsa/ambil_token_tinjau.py'
    subprocess.run(['docker', 'cp', src, 'eduai-app:/tmp/ambil_token.py'],
                   check=True, timeout=30)
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'sh', '-c',
         'cd /app && PYTHONPATH=/app python /tmp/ambil_token.py'],
        capture_output=True, text=True, timeout=60)
    for b in out.stdout.splitlines():
        if b.startswith('TOKEN='):
            return b.split('=', 1)[1].strip()
    raise SystemExit(f'token gagal: {out.stderr[-300:]!r}')


def dasar():
    """Alamat app yang bisa dijangkau Chrome di HOST.

    Jebakan (terukur 27Sep): `172.17.0.1:8100` → ERR_CONNECTION_REFUSED
    (port sudah tidak terbit / container pindah jaringan 172.20.x) →
    halaman error 390px terbaca "bersih" = UJI PALSU.
    Kini: IP container (172.20.0.2:8000), fallback domain publik.
    """
    ip = subprocess.run(
        ['docker', 'inspect', '-f',
         '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
         'eduai-app'],
        capture_output=True, text=True, timeout=20).stdout.strip()
    return f'http://{ip}:8000'


def js(tab, e):
    r = tab.cmd('Runtime.evaluate', {'expression': e, 'returnByValue': True})
    return r['result']['result'].get('value')


def ukur(tab, label):
    eksp = r'''
(() => {
  const lebar = document.documentElement.scrollWidth;
  const b = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.right > window.innerWidth + 1 || r.width > window.innerWidth + 1) {
      b.push(`${el.tagName.toLowerCase()}.${String(el.className||'').slice(0,40)} w=${Math.round(r.width)} right=${Math.round(r.right)} txt="${(el.textContent||'').trim().slice(0,50)}"`);
    }
  }
  return JSON.stringify({lebar, inner: window.innerWidth, n: b.length, b: b.slice(0,12)});
})()
'''
    h = json.loads(js(tab, eksp))
    print(f'{label}: {h["lebar"]}px (layar {h["inner"]}) | melebar={h["n"]}')
    for x in h['b']:
        print('   ', x)
    return h


def isi_identitas(url):
    """Isi kartu sambutan via HTTP SEBELUM buka tab.

    ⚠️ JEBAK TERUKUR (27Sep): form.submit() DI DALAM TAB membuat
    Emulation.setDeviceMetricsOverride MATI total (set ulang pun tak
    mempan) → innerWidth balik 539 (lebar jendela asli) dan "539px"
    terbaca sebagai layout HP rusak. Kini navigasi hanya sekali (GET).
    """
    import urllib.parse
    dasar_, _, jalur = url.rpartition('/tinjau/')
    tujuan = f'{dasar_}/tinjau/{jalur}/identitas'
    data = urllib.parse.urlencode(
        {'identitas': '081234567890'}).encode()
    req = urllib.request.Request(tujuan, data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    url = f'{dasar()}/tinjau/{token_tinjau()}'
    st = isi_identitas(url)
    print(f'identitas diisi via HTTP: {st}')
    tab, tid = tab_baru('about:blank')
    try:
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.enable')
        tab.cmd('Page.navigate', {'url': url})
        for _ in range(60):
            time.sleep(0.5)
            if js(tab, 'document.readyState') == 'complete':
                break
        time.sleep(2)

        #  Kartu sambutan sudah diisi lewat HTTP di isi_identitas() —
        #  JANGAN form.submit() di dalam tab (merusak emulasi, terukur).
        ada_kertas = js(tab, "!!document.querySelector('.kertas')")
        print(f'.kertas tampil: {ada_kertas} | layar={js(tab, "window.innerWidth")}px')
        if not ada_kertas:
            print('STOP: tanpa .kertas semua ukuran di bawah = PALSU')
            return

        #  ⚠️ mobile:true terbukti GAMPANG LEPAS di tab ini (set ulang pun
        #  tak mempan → innerWidth 539 = lebar jendela). Pakai jalur yang
        #  terbukti mempan (cek_emulasi set#3): mobile:false width 390.
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 1,
                 'mobile': False})
        time.sleep(0.5)
        layar = js(tab, 'window.innerWidth')
        print(f'lebar layar sesudah set ulang: {layar}')
        if layar != LEBAR:
            print('STOP: emulasi tidak mempan → ukuran di bawah PALSU')
            return
        ukur(tab, 'A) SEHAT (keadaan asli)')

        #  DIRUSAK: teks naskah tanpa spasi (mirip temuan "placeholder panjang")
        js(tab, r"""
(() => {
  const k = document.querySelector('.kertas');
  if (!k) return 'tidak ada .kertas';
  const p = document.createElement('p');
  p.textContent = 'https://eduai.bikinaja.id/tinjau/'
    + 'AbCdEfGhIjKlMnOpQrStUvWxYz0123456789/daftar-istilah-'
    + 'multikolinearitasheteroskedastisitasnormalitas-linearitas';
  k.appendChild(p);
  return 'disuntik';
})()
""")
        time.sleep(0.5)
        ukur(tab, 'B) DIRUSAK (teks tanpa spasi)')

        #  DIRUSAK 2: placeholder/input panjang di kartu identitas
        js(tab, r"""
(() => {
  const i = document.querySelector('.sambut input');
  if (i) { i.placeholder = 'Masukkan nomor WhatsApp aktif Anda dengan format '
    + 'negara contoh +6281234567890 atau 081234567890 supaya dapat kiriman '
    + 'notifikasi penting dari kami'; return 'placeholder dipanjangkan'; }
  return 'tidak ada input sambut';
})()
""")
        time.sleep(0.5)
        ukur(tab, 'C) DIRUSAK (placeholder panjang)')
    finally:
        try:
            urllib.request.urlopen(
                f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
        except Exception:                          # noqa: BLE001
            pass
        tab.tutup()


if __name__ == '__main__':
    main()
