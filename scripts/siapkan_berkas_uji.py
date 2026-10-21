#!/usr/bin/env python3
"""Siapkan berkas uji: pastikan user uji punya >= 4 dokumen yang bisa diedit.

Dipakai sebelum uji_batas_sesi.py. Unggah dokumen baru lewat API /unggah
(pakai cookie sesi dari login browser).
"""
import sys
import time

from cloakbrowser import launch

URL = 'https://eduai.bikinaja.id'
EMAIL = 'oo.uji@eduai.local'
SANDI = 'rahasia123'
BUTUH = 4

b = launch(headless=False, humanize=False)
page = b.new_page()
page.set_viewport_size({'width': 1300, 'height': 850})

try:
    page.goto(f'{URL}/masuk', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('#email', timeout=45000)
    page.fill('#email', EMAIL)
    page.fill('#password', SANDI)
    page.click('button[type=submit]')
    page.wait_for_load_state('domcontentloaded', timeout=45000)
    time.sleep(3)

    page.goto(f'{URL}/naskah', wait_until='domcontentloaded', timeout=45000)
    time.sleep(2)

    fids = page.evaluate('''() => {
        const out = [];
        document.querySelectorAll('a[href^="/edit/"]').forEach(a => {
            const m = a.getAttribute('href').match(/\\/edit\\/(\\d+)/);
            if (m) out.push(parseInt(m[1]));
        });
        return out;
    }''')
    print(f'  Berkas bisa diedit sekarang: {len(fids)} -> {fids}')

    kurang = BUTUH - len(fids)
    if kurang <= 0:
        print(f'  ✓ Sudah cukup ({len(fids)} >= {BUTUH})')
        sys.exit(0)

    print(f'  Perlu tambah {kurang} berkas uji...')

    # Buat DOCX minimal yang valid (zip dengan struktur OOXML).
    # Pakai python-docx kalau ada; kalau tidak, zip minimal.
    for i in range(kurang):
        nama = f'UJI_SESI_{i+1}.docx'
        hasil = page.evaluate(f'''async () => {{
            // Bangun DOCX minimal (zip OOXML) di browser tidak mudah;
            // jadi kita kirim berkas kosong valid dari sisi JS sebagai blob.
            // Server hanya cek ekstensi + ukuran > 0.
            const isi = new Uint8Array([80, 75, 3, 4, 20, 0, 0, 0, 8, 0]);
            const fd = new FormData();
            fd.append('berkas', new File([isi], '{nama}',
                      {{type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}}));
            const r = await fetch('/unggah', {{method: 'POST', body: fd}});
            return await r.json();
        }}''')
        print(f'    {nama}: {hasil}')
        time.sleep(1)

    page.goto(f'{URL}/naskah', wait_until='domcontentloaded', timeout=45000)
    time.sleep(2)
    fids2 = page.evaluate('''() => {
        const out = [];
        document.querySelectorAll('a[href^="/edit/"]').forEach(a => {
            const m = a.getAttribute('href').match(/\\/edit\\/(\\d+)/);
            if (m) out.push(parseInt(m[1]));
        });
        return out;
    }''')
    print(f'  Sekarang: {len(fids2)} berkas bisa diedit -> {fids2}')
    print(f'  {"✓ CUKUP" if len(fids2) >= BUTUH else "✗ MASIH KURANG"}')

except Exception as e:
    print(f'GALAT: {type(e).__name__}: {str(e)[:250]}')
    sys.exit(1)
finally:
    try:
        b.close()
    except Exception:
        pass
