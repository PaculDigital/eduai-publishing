#!/usr/bin/env python3
"""UJI E2E BATAS SESI EDIT — bukti nyata, bukan klaim.

Skenario:
  0. Bersihkan sesi sisa (uji harus mulai dari 0)
  1. Login
  2. Buka dokumen #1, #2, #3 -> harus SEMUA BOLEH
  3. Cek /api/sesi -> sesi aktif = 3
  4. Buka dokumen KE-4 -> HARUS DITOLAK (halaman batas_sesi)
  5. Buka ULANG dokumen #1 -> harus BOLEH (sama, bukan sesi baru)
  6. Tutup dokumen #2 via API -> sesi jadi 2
  7. Buka dokumen KE-4 -> sekarang harus BOLEH
  8. Bersihkan

PENTING: skrip ini membersihkan sesi di awal, karena sesi hantu dari uji
sebelumnya membuat hasil uji jadi palsu-gagal.

Jalankan: DISPLAY=:99 /opt/data/services/cloakbrowser/.venv/bin/python3 \
            scripts/uji_batas_sesi.py
"""
import json
import subprocess
import sys
import time

from cloakbrowser import launch

URL = 'https://eduai.bikinaja.id'
EMAIL = 'oo.uji@eduai.local'
SANDI = 'rahasia123'
BATAS = 3
DIR = '/opt/data/services/eduai-publishing'

lulus, gagal = [], []


def cek(nama, kondisi, detail=''):
    if kondisi:
        lulus.append(nama)
        print(f'  ✓ {nama}' + (f' — {detail}' if detail else ''))
    else:
        gagal.append(nama)
        print(f'  ✗ {nama}' + (f' — {detail}' if detail else ''))


def reset_sesi():
    r = subprocess.run(['bash', 'scripts/bersihkan_sesi.sh'],
                       capture_output=True, text=True, cwd=DIR)
    return (r.stdout or r.stderr).strip()


def ambil_json(page, js):
    return page.evaluate('''async (kode) => {
        const r = await fetch(kode);
        const t = await r.text();
        try { return JSON.parse(t); }
        catch (e) { return {__bukan_json: true, status: r.status, isi: t.slice(0, 300)}; }
    }''', js)


def status_editor(page):
    return page.evaluate('''() => {
        const t = document.body.innerText || '';
        return {
            ada_iframe: !!document.querySelector("iframe[src*='documenteditor']"),
            batas: t.includes('dokumen bersamaan'),
        };
    }''')


b = launch(headless=False, humanize=False)
page = b.new_page()
page.set_viewport_size({'width': 1400, 'height': 900})

try:
    print('\n=== 0. Reset sesi (mulai dari 0) ===')
    print('  ' + reset_sesi().replace('\n', '\n  '))

    page.goto(f'{URL}/masuk', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('#email', timeout=45000)
    page.fill('#email', EMAIL)
    page.fill('#password', SANDI)
    page.click('button[type=submit]')
    page.wait_for_load_state('domcontentloaded', timeout=45000)
    time.sleep(3)
    print(f'\n  Login OK -> {page.url}')

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
    print(f'  Berkas bisa diedit: {fids}')

    if len(fids) < 4:
        print(f'  ⚠ Hanya {len(fids)} berkas bisa diedit — uji butuh >= 4.')
        print('    Jalankan dulu: python3 scripts/siapkan_berkas_uji.py')
        sys.exit(2)

    print(f'\n=== Buka {BATAS} dokumen pertama (harus BOLEH) ===')
    for i in range(BATAS):
        fid = fids[i]
        page.goto(f'{URL}/edit/{fid}', wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)
        st = status_editor(page)
        cek(f'buka #{i+1} (fid={fid}) BOLEH', st['ada_iframe'] and not st['batas'],
            f"iframe={st['ada_iframe']} halaman_batas={st['batas']}")

    s = ambil_json(page, '/api/sesi')
    if s.get('__bukan_json'):
        cek('GET /api/sesi balas JSON', False, f"HTTP {s.get('status')} -> {s.get('isi')}")
    else:
        cek('GET /api/sesi balas JSON', True)
        cek(f'sesi aktif = {BATAS}', s.get('sesi_aktif') == BATAS,
            f"dapat {s.get('sesi_aktif')} / batas {s.get('batas')}")
        print(f"    dokumen terbuka: {[x['nama'] for x in s.get('sesi', [])]}")

    print(f'\n=== Buka dokumen ke-{BATAS+1} (harus DITOLAK) ===')
    fid4 = fids[BATAS]
    page.goto(f'{URL}/edit/{fid4}', wait_until='domcontentloaded', timeout=60000)
    time.sleep(3)
    tolak = page.evaluate('''() => {
        const t = document.body.innerText || '';
        return {
            batas: t.includes('dokumen bersamaan'),
            ada_iframe: !!document.querySelector("iframe[src*='documenteditor']"),
            judul: document.title,
            cuplikan: t.slice(0, 200),
        };
    }''')
    cek('dokumen ke-4 DITOLAK (halaman batas sesi)',
        tolak['batas'] and not tolak['ada_iframe'],
        f"halaman_batas={tolak['batas']} iframe={tolak['ada_iframe']}")
    print(f"    judul: {tolak['judul']}")
    print(f"    cuplikan: {tolak['cuplikan'][:160].replace(chr(10), ' | ')}")

    print('\n=== Buka ULANG dokumen #1 (harus BOLEH — bukan sesi baru) ===')
    page.goto(f'{URL}/edit/{fids[0]}', wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)
    ulang = status_editor(page)
    cek('buka ulang dokumen #1 BOLEH', ulang['ada_iframe'] and not ulang['batas'])

    s2 = ambil_json(page, '/api/sesi')
    cek('sesi tetap 3 (refresh bukan sesi baru)', s2.get('sesi_aktif') == BATAS,
        f"dapat {s2.get('sesi_aktif')}")

    print('\n=== Tutup dokumen #2 via API (forcesave + close) ===')
    t0 = time.time()
    hasil = page.evaluate(f'''async () => {{
        const r = await fetch('/api/sesi/tutup', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{file_id: {fids[1]}}})
        }});
        const t = await r.text();
        try {{ return JSON.parse(t); }}
        catch (e) {{ return {{__bukan_json: true, status: r.status, isi: t.slice(0,300)}}; }}
    }}''')
    print(f"    hasil: {json.dumps(hasil)[:200]}  ({time.time()-t0:.1f} detik)")
    cek('tutup dokumen #2 BERHASIL', hasil.get('ok') is True,
        f"sesi_aktif={hasil.get('sesi_aktif')}")

    print(f'\n=== Buka dokumen ke-{BATAS+1} lagi (sekarang harus BOLEH) ===')
    page.goto(f'{URL}/edit/{fid4}', wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)
    akhir = status_editor(page)
    cek(f'dokumen ke-{BATAS+1} sekarang BOLEH',
        akhir['ada_iframe'] and not akhir['batas'])

    print('\n=== Bersihkan ===')
    print('  ' + reset_sesi().replace('\n', '\n  '))

except Exception as e:
    print(f'\nGALAT: {type(e).__name__}: {str(e)[:250]}')
    gagal.append('eksekusi tanpa galat')
finally:
    try:
        b.close()
    except Exception:
        pass

print()
print('═' * 62)
print(f'  LULUS: {len(lulus)}   GAGAL: {len(gagal)}')
if gagal:
    for g in gagal:
        print(f'    ✗ {g}')
else:
    print('  ✅ SEMUA LULUS — batas sesi bekerja!')
print('═' * 62)
sys.exit(1 if gagal else 0)
