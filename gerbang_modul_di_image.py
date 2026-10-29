"""GERBANG: setiap modul mesin buku WAJIB bisa diimpor DARI DALAM IMAGE.

🚨 AKAR YANG DITUTUP (20 Okt 2026, TERUKUR — hampir lolos ke produksi):
  `jev_buku_umum.py` dan `diagram_buku.py` TIDAK PERNAH ada di Dockerfile.
  Akibatnya di dalam container:
      ModuleNotFoundError: No module named 'jev_buku_umum'

  TAPI seluruh gerbang HIJAU (142 LULUS) karena dijalankan di HOST lewat
  `docker exec ... python3 /app/gerbang_x.py` yang `sys.path`-nya /app —
  dan saat itu /app masih berisi berkas hasil `docker cp`, BUKAN isi image.

  Inti pelajaran: **gerbang yang mengimpor dari folder kerja tidak
  membuktikan modul ikut ke image.** Yang membuktikan hanya:
      docker exec <container> python3 -c "import <modul>"

  Cacat ini SENYAP: `buku_umum_assembly` menangkap ImportError lalu jatuh
  ke jalur regex lama — buku tetap terbit, hanya tanpa Jev & tanpa 8 bentuk
  diagram. Hasilnya "mirip benar", jadi tidak ada yang curiga.

LULUS = 0 GAGAL.
"""
import os
import subprocess
import sys

APP = 'eduai-app'

#  IMAGE yang akan diuji. Kalau kosong → periksa container hidup.
#  Diisi lewat env `EDUAI_IMAGE_UJI=eduai-app:<tag>` (dipakai periksa_kode.sh
#  bila ada image hasil build; kalau tidak, jatuh ke container hidup).
IMAGE_UJI = os.environ.get('EDUAI_IMAGE_UJI', '').strip()

#  Modul mesin buku yang WAJIB ada di image. Tambahkan bila ada modul baru.
WAJIB = [
    ('jev_buku_umum',      'Jev pembaca BENTUK naskah buku'),
    ('diagram_buku',       'penggambar 8 bentuk diagram'),
    ('tahapan_diagram',    'Jev di depan penggambar diagram'),
    ('buku_umum_assembly', 'perakit 1 buku → 1 .docx'),
    ('buku_umum_pipeline', 'pipa utama buku umum'),
    ('jenis_buku',         'paket jenis + gaya ilustrasi'),
    ('tone_menulis',       'ambang paragraf per tone'),
    ('brief_visual',       'brief ilustrasi + prompt gambar'),
    ('mutu_isi_buku',      'pemeriksa mutu isi'),
    ('label_infografis',   'label infografis'),
    ('larangan_budaya',    'larangan budaya'),
    ('verifikasi_sitasi',  'verifikasi sitasi'),
    ('indeks_referensi',   'indeks referensi'),
    ('outline_buku',       'outline buku'),
    ('penyusun_buku',      'penyusun buku'),
    ('tier_buku',          'tier buku Hemat/Normal/Full'),
]

lulus = 0
gagal = []


def cek_impor(modul):
    """Impor modul DARI DALAM IMAGE, bukan dari host.

    🚨 Urutan penting (20 Okt 2026): bila image hasil build BELUM ada,
    periksa CONTAINER HIDUP. Tapi saat `periksa_kode.sh` jalan SEBELUM
    build, container yang hidup masih IMAGE LAMA — memeriksanya membuat
    gerbang menuduh kode baru padahal yang diperiksa kode lama.
    Karena itu: utamakan `docker run --rm` pada IMAGE yang akan dikirim.
    """
    if IMAGE_UJI:
        #  `-e` kosong: cukup untuk menguji KEBERADAAN modul. Modul yang
        #  menuntut kunci (mis. buku_umum_pipeline → EDUAI_ROUTER_KEY) akan gagal
        #  diuji tanpa env, padahal di produksi env ADA (ditempel jalankan.sh).
        #  Yang diuji di sini = bisa/tidaknya DIimpor, bukan isi konfigurasi.
        argv = ['docker', 'run', '--rm', '--entrypoint', 'python3',
                '-e', 'EDUAI_ROUTER_KEY=uji',
                '-e', 'INFERHUB_KEY=uji', '-e', 'OPENALEX_KEY=uji',
                '-e', 'SCOPUS_KEY=uji', '-e', 'SCITE_KEY=uji',
                IMAGE_UJI, '-c', f"import {modul}; print({modul}.__file__)"]
    else:
        argv = ['docker', 'exec', APP, 'python3', '-c',
                f"import sys; sys.path.insert(0,'/app'); "
                f"import {modul}; print({modul}.__file__)"]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    return r.returncode == 0, (r.stdout or '').strip(), (r.stderr or '')


print('=' * 70)
print('GERBANG MODUL MESIN BUKU — HARUS BISA DIIMPOR DARI DALAM IMAGE')
print('=' * 70)

#  ── 0. Sumber pemeriksaan ─────────────────────────────────────────────
if IMAGE_UJI:
    print(f'  sumber: IMAGE {IMAGE_UJI} (docker run --rm)')
else:
    r = subprocess.run(['docker', 'ps', '--filter', f'name={APP}',
                        '--format', '{{.Status}}'],
                       capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        print(f'  ❌ {APP} tidak hidup — gerbang TIDAK DILEWATI (prasyarat kosong = GAGAL)')
        print('{"lulus": 0, "gagal": 1}')
        sys.exit(1)
    print(f'  sumber: container HIDUP {APP} ({r.stdout.strip()})')
print()

#  ── 1. Setiap modul WAJIB bisa diimpor ───────────────────────────────
for modul, guna in WAJIB:
    ok, jalur, err = cek_impor(modul)
    if ok:
        lulus += 1
        print(f'  ✅ {modul:22s} {jalur}')
    else:
        pesan = err.strip().splitlines()[-1] if err.strip() else 'gagal'
        gagal.append(f'{modul} ({guna}) — {pesan}')
        print(f'  ❌ {modul:22s} TIDAK BISA DIIMPOR — {guna}')

#  ── 2. Bukti silang: modul benar-benar berasal dari IMAGE ─────────────
#  Kalau jalur keluar selain /app/<modul>.py, berkasnya entah dari mana.
print()
for modul, _ in WAJIB[:2]:
    ok, jalur, _ = cek_impor(modul)
    benar = jalur == f'/app/{modul}.py'
    if benar:
        lulus += 1
        print(f'  ✅ {modul}: jalur image benar ({jalur})')
    else:
        gagal.append(f'{modul}: jalur aneh {jalur!r} (harus /app/{modul}.py)')
        print(f'  ❌ {modul}: jalur ANEH {jalur!r}')

#  ── 3. Bukti bahwa Dockerfile MEMANG menyebut kedua berkas rawan ─────
print()
try:
    df = open('/opt/data/services/eduai-publishing/Dockerfile',
              encoding='utf-8').read()
except FileNotFoundError:
    df = ''
for berkas in ('jev_buku_umum.py', 'diagram_buku.py', 'tata_paragraf.py', 'tier_buku.py'):
    if f'COPY {berkas}' in df:
        lulus += 1
        print(f'  ✅ Dockerfile: COPY {berkas}')
    else:
        gagal.append(f'Dockerfile TIDAK meng-COPY {berkas}')
        print(f'  ❌ Dockerfile TIDAK meng-COPY {berkas} ⇒ akan hilang lagi')

print()
for g in gagal:
    print(f'  ❌ {g}')
print('=' * 70)
print(f'{{"lulus": {lulus}, "gagal": {len(gagal)}}}')
print('=' * 70)
sys.exit(1 if gagal else 0)
