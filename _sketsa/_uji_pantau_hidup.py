"""UJI PAPAN PANTAU HIDUP — jalankan AI NYATA, potret modal, periksa mata.

KENAPA ADA: `_uji_tampilan.py` memeriksa elemen ADA, tapi modal pantau baru
muncul saat ADA proses AI jalan. Uji ini MENITIPKAN revisi nyata ke server
lalu memotret halaman → membuktikan modal + tahap nyata benar-benar tampil
ke user (bukan cuma ada di HTML).
"""
import os
import subprocess
import sys
import time

BASE = os.getenv('EDUAI_BASE', 'https://eduai.bikinaja.id')
EMAIL = os.getenv('E2E_EMAIL', 'uji-berbayar-e2e@test.local')
SANDI = os.getenv('E2E_SANDI', 'UjiBayar123!')
FILE_ID = int(os.getenv('E2E_FILE_ID', '30'))
DIR = '/opt/data/services/eduai-publishing/_arsip/uji-tampilan'

sys.path.insert(0, '/opt/data/services/cloakbrowser')
os.makedirs(DIR, exist_ok=True)
from cloakbrowser import launch  # noqa: E402


def main():
    b = launch(headless=True)
    hasil = []
    try:
        ctx = b.new_context(viewport={'width': 1500, 'height': 950},
                            ignore_https_errors=True)
        pg = ctx.new_page()
        pg.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
        pg.wait_for_timeout(2000)
        pg.fill('input[name="email"]', EMAIL)
        pg.fill('input[name="password"]', SANDI)
        pg.click('button[type="submit"]')
        pg.wait_for_timeout(5000)
        print(f'1. login → {pg.url}')

        # ── TITIPKAN revisi (endpoint NYATA = /v1/revisi, TANPA `tunggu`)
        #  ⚠️ AKAR (16Sep26): Wulan menebak nama `/v1/titip` + field `perintah`
        #   → 404. Fakta dari app/ai.py: nama = `/v1/revisi`; field WAJIB =
        #   `komentar` (list, min 1); `tunggu` TIDAK diisi = proses LATAR
        #   BELAKANG (yang justru ingin diuji di sini).
        print(f'2. titipkan revisi (latar belakang) untuk berkas {FILE_ID}')
        r = pg.evaluate("""async (fid) => {
            const r = await fetch('/api/ai/v1/revisi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'same-origin',
                body: JSON.stringify({
                    file_id: fid,
                    bab: '__seluruh__',
                    komentar: ['Perbaiki tata bahasa dan ejaan paragraf ini.']
                })
            });
            let d = {}; try { d = await r.json(); } catch(e) { d = {raw: 'bukan json'}; }
            return {kode: r.status, isi: d};
        }""", FILE_ID)
        print(f'   titip → HTTP {r["kode"]} {str(r["isi"])[:150]}')
        # ⚠️ AKAR 16Sep26: uji ini dulu HIJAU padahal TIDAK ADA proses jalan —
        #  karena HTTP 402 (kuota habis) tidak diperiksa, dan pemeriksaan modal
        #  hanya melihat DOM (yang memang ada di HTML). WAJIB periksa kode HTTP
        #  DULU; kalau bukan 2xx → uji TIDAK SAH (jangan lapor hijau).
        if r['kode'] == 402:
            print('   ❌ KUOTA HABIS (402) — uji tidak sah. Isi ulang kuota dulu.')
            hasil.append(('kuota AI tersedia (bukan 402)', False,
                          f'HTTP {r["kode"]} {str(r["isi"])[:100]}'))
            raise SystemExit(1)
        if r['kode'] not in (200, 201, 202):
            hasil.append(('titip revisi diterima', False,
                          f'HTTP {r["kode"]} {str(r["isi"])[:100]}'))
            raise SystemExit(1)
        hasil.append(('titip revisi diterima', True, f'HTTP {r["kode"]}'))

        # ── buka halaman editor → modal pantau HARUS muncul ──
        pg.goto(f'{BASE}/edit/{FILE_ID}', wait_until='domcontentloaded',
                timeout=60000)
        # ⚠️ AKAR 16Sep26: dulu tunggu 9 detik lalu periksa SEKALI. Saat itu
        #  proses masih 'menunggu antrean' (belum 'jalan') → modal wajar belum
        #  muncul → uji lapor GAGAL padahal tampilannya BENAR.
        #  Perbaikan: TUNGGU sampai proses benar-benar 'jalan' (maks 60 dtk),
        #  baru periksa. Ini juga lebih menyerupai perilaku user sungguhan.
        for _i in range(20):
            pg.wait_for_timeout(3000)
            _st = pg.evaluate("""async () => {
                const r = await fetch('/api/ai/v1/proses',
                                      {credentials:'same-origin'});
                const d = await r.json();
                return (d.jalan || []).map(x => x.status).join(',');
            }""")
            if 'jalan' in (_st or ''):
                print(f'   proses mulai jalan setelah {(_i+1)*3} detik')
                # ⚠️ Beri JS halaman kesempatan menjalankan polling-nya
                #  (JEDA_PANTAU = 2000 ms). Tanpa jeda ini uji memeriksa
                #  LEBIH CEPAT dari polling halaman → positif palsu GAGAL.
                pg.wait_for_timeout(3000)
                break

        keadaan = pg.evaluate("""() => {
            const mp = document.getElementById('pantau');
            const sp = document.getElementById('kunci-spanduk');
            const th = document.getElementById('pantau-tahap');
            const lk = document.getElementById('pantau-langkah');
            return {
                // ⚠️ AKAR 16Sep26: uji ini memeriksa kelas 'tampil', padahal
                //  kode SUDAH memakai 'buka' (sesuai CSS #pantau.buka).
                //  Uji tertinggal dari kode → lapor GAGAL padahal tampilannya
                //  benar (dibuktikan: kelas="buka", display="flex").
                //  Perbaikan: periksa DISPLAY (nyata terlihat), bukan nama kelas.
                modal_tampil: mp ? getComputedStyle(mp).display !== 'none' : null,
                modal_kelas: mp ? mp.className : null,
                spanduk_tampil: sp ? sp.classList.contains('tampil') : null,
                tahap: th ? th.textContent.trim() : null,
                pita: lk ? lk.textContent.trim() : null,
                ada_modal_elemen: mp !== null,
            };
        }""")
        print(f'   keadaan modal: {keadaan}')
        hasil.append(('modal pantau terlihat', bool(keadaan['modal_tampil']),
                      str(keadaan['tahap'])))
        hasil.append(('spanduk kunci terlihat', bool(keadaan['spanduk_tampil']), ''))

        p = f'{DIR}/03-papan-pantau-ai-jalan.png'
        pg.screenshot(path=p, full_page=False)
        print(f'3. potret → {p}')

        # ── batalkan supaya tidak makan kuota panjang ──
        pg.wait_for_timeout(3000)
        p2 = f'{DIR}/04-papan-pantau-detik-ke3.png'
        pg.screenshot(path=p2, full_page=False)
        print(f'4. potret ke-2 → {p2}')

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
