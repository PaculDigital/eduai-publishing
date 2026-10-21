"""UJI E2E NYATA — batas unggah 15 MB lewat jalur USER ASLI.

WAJIB: pakai input[type=file] + dispatchEvent('change') — BUKAN fetch()
(Pelajaran 15Sep26: uji fetch MELEWATI pemeriksaan JS browser = MENIPU).

Skenario:
  A. uji12mb.txt (12,59 MB) -> HARUS DITERIMA user (di antara 5-15 MB)
  B. uji16mb.txt (16,94 MB) -> HARUS DITOLAK di sisi browser (JS)
"""
import sys
import time

from cloakbrowser import launch

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji-gratis-render@test.local'


def main(sandi: str):
    b = launch(headless=True)
    p = b.new_page() if hasattr(b, 'new_page') else b

    print('[1] Buka halaman login', flush=True)
    p.goto(f'{BASE}/masuk', timeout=60000)
    time.sleep(2)

    print('[2] Login (field: email + password)', flush=True)
    p.fill('input[name=email]', EMAIL)
    p.fill('input[name=password]', sandi)
    p.click('button[type=submit]')
    time.sleep(4)

    print(f'    URL setelah login: {p.url}', flush=True)
    if '/masuk' in p.url:
        print('    GAGAL — masih di halaman login', flush=True)
        return

    print('[3] Buka halaman naskah', flush=True)
    p.goto(f'{BASE}/naskah', timeout=60000)
    time.sleep(3)

    max_mb = p.evaluate('window.MAX_MB')
    print(f'    window.MAX_MB = {max_mb}   (harus 15)', flush=True)

    ada = p.evaluate("!!document.querySelector('input[type=file]')")
    print(f'    input[type=file] ada: {ada}', flush=True)
    if not ada:
        print('    input file tidak ketemu', flush=True)
        return

    def cek_pesan():
        """Ambil HANYA pesan galat dinamis (toast), BUKAN teks statis dropzone.

        PELAJARAN 15Sep26: teks statis "maks 15 MB per berkas" di dropzone
        BUKAN pesan galat. Kalau ikut dihitung, skrip uji salah lapor.
        Ambil dari elemen toast/alert; kalau tak ketemu, cari kalimat yang
        mengandung angka ukuran + kata 'besar'.
        """
        return p.evaluate("""
            (() => {
              // 1) cari elemen toast/alert/galat yang muncul
              const sel = ['.toast', '[class*=toast]', '[class*=alert]',
                           '[class*=galat]', '[class*=error]', '[role=alert]'];
              for (const s of sel) {
                const el = document.querySelector(s);
                if (el && el.innerText && el.innerText.trim()) {
                  return el.innerText.trim().slice(0, 300);
                }
              }
              // 2) cari kalimat galat dinamis di seluruh body
              const t = document.body.innerText || '';
              const m = t.split('\\n').filter(l =>
                /terlalu besar|tidak boleh diunggah|gagal diunggah|melebihi/i.test(l));
              return m.slice(0, 3).join(' | ');
            })()
        """)

    # ── SKENARIO A: 12,59 MB ──
    print('', flush=True)
    print('[4] SKENARIO A: unggah 12,59 MB (harus DITERIMA)', flush=True)
    p.set_input_files('input[type=file]', '/tmp/uji12mb.txt')
    p.evaluate("""
        document.querySelector('input[type=file]')
          .dispatchEvent(new Event('change', {bubbles:true}))
    """)
    time.sleep(3)
    pesan_a = cek_pesan() or ''
    print(f'    pesan: {pesan_a[:280] or "(tidak ada pesan)"}', flush=True)
    tolak_a = any(k in pesan_a.lower() for k in
                  ['terlalu besar', 'maksimal 15', 'maks 15', 'tidak boleh'])
    print(f'    HASIL A: {"DITOLAK (seharusnya DITERIMA!)" if tolak_a else "DITERIMA"}', flush=True)

    # ── SKENARIO B: 16,94 MB ──
    print('', flush=True)
    print('[5] SKENARIO B: unggah 16,94 MB (harus DITOLAK)', flush=True)
    p.set_input_files('input[type=file]', '/tmp/uji16mb.txt')
    p.evaluate("""
        document.querySelector('input[type=file]')
          .dispatchEvent(new Event('change', {bubbles:true}))
    """)
    time.sleep(4)
    pesan_b = cek_pesan() or ''
    print(f'    pesan: {pesan_b[:280] or "(tidak ada pesan)"}', flush=True)
    tolak_b = any(k in pesan_b.lower() for k in
                  ['terlalu besar', 'maksimal', 'maks ', 'tidak boleh'])
    print(f'    HASIL B: {"DITOLAK" if tolak_b else "DITERIMA (seharusnya DITOLAK!)"}', flush=True)

    # simpan layar untuk bukti
    p.screenshot(path='/tmp/uji_batas15.png', full_page=True)
    print('    screenshot: /tmp/uji_batas15.png', flush=True)

    print('', flush=True)
    print('=' * 58, flush=True)
    print('RINGKASAN', flush=True)
    print('=' * 58, flush=True)
    print(f'  window.MAX_MB           : {max_mb}', flush=True)
    print(f'  A. 12,59 MB diterima    : {"YA" if not tolak_a else "TIDAK"}', flush=True)
    print(f'  B. 16,94 MB ditolak     : {"YA" if tolak_b else "TIDAK"}', flush=True)

    try:
        b.close()
    except Exception:
        pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('pakai: python3 _uji_batas15.py <SANDI>')
        sys.exit(1)
    main(sys.argv[1])
