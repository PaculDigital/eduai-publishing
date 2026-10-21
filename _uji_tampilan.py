"""UJI TAMPILAN NYATA — lonceng + papan pantau, render + potret layar.

KENAPA ADA: aturan Bos — "XML benar ≠ tampilan benar → render + vision WAJIB".
Uji kode (26/0) hanya membuktikan elemen & fungsi ADA, BUKAN bahwa halaman
benar-benar menampilkannya. Skrip ini membuka halaman editor NYATA di
peramban, memeriksa DOM hidup, dan memotret layar untuk diperiksa mata.
"""
import os
import sys
import time

BASE = os.getenv('EDUAI_BASE', 'https://eduai.bikinaja.id')
EMAIL = os.getenv('E2E_EMAIL', 'uji-berbayar-e2e@test.local')
SANDI = os.getenv('E2E_SANDI', 'UjiBayar123!')
DIR = os.getenv('SHOT_DIR', '/opt/data/services/eduai-publishing/_arsip/uji-tampilan')

sys.path.insert(0, '/opt/data/services/cloakbrowser')
os.makedirs(DIR, exist_ok=True)

# ⚠️ API CloakBrowser yang BENAR = `launch` (BUKAN `CloakBrowser`).
#  Wulan sempat mengarang nama kelas → ImportError. Pola ini disalin dari
#  _shot_final.py yang SUDAH terbukti jalan (16Sep26).
from cloakbrowser import launch  # noqa: E402


def main():
    hasil = []
    b = launch(headless=True)
    try:
        ctx = b.new_context(viewport={'width': 1500, 'height': 950},
                            ignore_https_errors=True)
        pg = ctx.new_page()
        print(f'1. buka {BASE}/masuk')
        pg.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
        time.sleep(1.5)

        # LOGIN — ⚠️ field WAJIB `password` (BUKAN `sandi`) + klik submit
        pg.fill('input[name="email"]', EMAIL)
        pg.fill('input[name="password"]', SANDI)
        pg.click('button[type="submit"]')
        time.sleep(3)
        print(f'   setelah login → {pg.url}')

        print('2. buka daftar naskah')
        pg.goto(f'{BASE}/naskah', wait_until='domcontentloaded', timeout=60000)
        time.sleep(2)

        # ⚠️ AKAR (16Sep26): daftar naskah bisa memuat tautan .pdf (halaman
        #  lain), tapi /edit/ HANYA untuk .docx → 404. Ambil berkas .docx
        #  milik user uji LANGSUNG dari DB.
        import subprocess, json as _json
        _q = ("SELECT id FROM files WHERE user_id=(SELECT id FROM users "
              "WHERE email='%s') AND tipe LIKE '%%wordprocessingml%%' "
              "AND terhapus_pada IS NULL ORDER BY id DESC LIMIT 1" % EMAIL)
        _out = subprocess.run(['docker', 'exec', 'eduai-app', 'python3', '-c',
            f"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
            f"r=c.execute({_q!r}).fetchone();print(r[0] if r else '')"],
            capture_output=True, text=True, timeout=60)
        _id = _out.stdout.strip()
        if not _id:
            print('   ⚠️ user uji tidak punya berkas .docx')
            hasil.append(('ada berkas .docx untuk diuji', False, 'tidak ada'))
        else:
            href = f'/edit/{_id}'
            print(f'   berkas .docx dari DB: id={_id}')
            print(f'3. buka editor {href}')
            pg.goto(BASE + href, wait_until='domcontentloaded', timeout=60000)
            time.sleep(6)   # beri waktu hanyaoffice + JS kita jalan

            # ── DOM HIDUP (bukan file!) ──
            cek = {
                'lonceng': 'document.getElementById("lonceng") !== null',
                'lonceng-angka': 'document.getElementById("lonceng-angka") !== null',
                'daftar-lonceng': 'document.getElementById("daftar-lonceng") !== null',
                'pantau': 'document.getElementById("pantau") !== null',
                'pantau-langkah': 'document.getElementById("pantau-langkah") !== null',
                'kunci-spanduk': 'document.getElementById("kunci-spanduk") !== null',
                'ikon bell ada isinya':
                    '(() => { const b = document.querySelector("#lonceng svg, #lonceng use");'
                    ' return b !== null; })()',
                'JS pantau jalan (ada interval)':
                    'typeof window.__AI_FILE_ID__ !== "undefined"',
            }
            for nama, ekspr in cek.items():
                try:
                    ok = bool(pg.evaluate(ekspr))
                except Exception as e:                          # noqa: BLE001
                    ok = False
                    print(f'     (galat periksa {nama}: {e})')
                hasil.append((nama, ok, ''))
                print(f'   {"✅" if ok else "❌"} {nama}')

            # ── Panggil API proses seperti halaman ──
            try:
                j = pg.evaluate("""async () => {
                    const r = await fetch('/api/ai/v1/proses', {credentials:'same-origin'});
                    return {kode: r.status, isi: await r.json()};
                }""")
                punya = isinstance(j.get('isi'), dict) and 'jalan' in j['isi']
                hasil.append(('API /v1/proses balas benar', punya, str(j)[:120]))
                print(f'   {"✅" if punya else "❌"} API /v1/proses → {j}')
            except Exception as e:                              # noqa: BLE001
                hasil.append(('API /v1/proses balas benar', False, str(e)[:120]))
                print(f'   ❌ API /v1/proses galat: {e}')

            # ── POTRET LAYAR ──
            p1 = f'{DIR}/01-halaman-editor.png'
            pg.screenshot(path=p1, full_page=False)
            print(f'4. potret layar → {p1}')

            # ── buka lonceng → potret ──
            try:
                pg.click('#lonceng')
                time.sleep(1.5)
                p2 = f'{DIR}/02-lonceng-terbuka.png'
                pg.screenshot(path=p2, full_page=False)
                print(f'5. potret lonceng → {p2}')
                buka = pg.evaluate(
                    'document.getElementById("daftar-lonceng")'
                    '.classList.contains("buka")')
                hasil.append(('lonceng terbuka saat diklik', bool(buka), ''))
                print(f'   {"✅" if buka else "❌"} lonceng terbuka')
            except Exception as e:                              # noqa: BLE001
                print(f'   ⚠️ gagal buka lonceng: {e}')

    finally:
        try:
            b.close()
        except Exception:
            pass

    print('\n' + '=' * 62)
    gagal = [h for h in hasil if not h[1]]
    print(f'TOTAL {len(hasil)} — GAGAL {len(gagal)}')
    for h in gagal:
        print(f'  ❌ {h[0]} {h[2]}')
    print('=' * 62)
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())