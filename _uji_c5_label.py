"""UJI C5 — label rujukan harga/kuota harus MENUNJUK KE TOPIK YANG BENAR.

KENAPA ADA (ACC Bos 24Sep26 "C5"):
    Rujukan `§4.10` dan `§4.13` gampang tertukar. Salah rujuk = orang berikutnya
    membaca aturan yang SALAH (harga/kuota vs Token Revisi) → bisa merusak
    rumus yang sudah dikunci Bos.

FAKTA (sumber kebenaran uji ini: app/config.py di image, BUKAN berkas
arsip dan BUKAN path host; cek docs-vs-config ada di sot.py periksa_harga):
    §4.10 (nomor bagian historis) = SISTEM KUOTA & CREDIT AI
    §4.13 (nomor bagian historis) = SISTEM TOKEN REVISI (KUNCI HARGA & MESIN UANG)
    Nomor §4.10/§4.13 dipertahankan di komentar kode sebagai label historis;
    NILAINYA dicek dari config.py, bukan dari berkas arsip.

ATURAN YANG DIUJI:
    • Rujukan soal  "potong per bagian / Token Revisi / rumus ÷10.000"  → §4.13
    • Rujukan soal  "kuota / AddOn / paket / sisa revisi-simulasi"      → §4.10
    • Label "langkah #2" TIDAK BOLEH ada

DUA ARAH:
    SEHAT   → wajib LULUS
    BERGIGI → kalau salah satu rujukan dikembalikan ke §4.10 yang salah,
              uji ini WAJIB GAGAL (dibuktikan dalam skrip: lihat BAGIAN B).

JALAN: docker cp _uji_c5_label.py eduai-app:/app/ \
       && docker exec -w /app eduai-app python3 _uji_c5_label.py
"""
import re
import sys

sys.path.insert(0, '/app')

LULUS = 0
GAGAL = 0


def cek(nama, syarat, detail=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {detail}')


def baca(p):
    return open(p, encoding='utf-8').read()


# ── 0. Fakta harga/kuota HANYA dari SUMBER YANG ADA DI IMAGE ─────────────
#  BERGIGI (26 Okt 2026, temuan agen Boss C, lalu ronde 2 butir 1):
#  Bagian ini DULU membaca berkas arsip dari path host dan MELEWATI cek
#  begitu saja kalau berkasnya tidak ada. Perbaikan ronde 1 memindahkan
#  sumber ke config.py, TAPI masih menyisakan 2 cek docs/sot/04 dari path
#  host /opt/... yang di container TIDAK ADA — jadi 2 cek itu tetap
#  dilewati diam-diam dengan alasan "bukan kegagalan". Itu pola yang SAMA,
#  cuma pindah tempat — belum dicabut akarnya.
#  AKAR YANG DICABUT DI SINI: uji container ini TIDAK BOLEH membaca path
#  host sama sekali. Semua cek [0] di bawah hanya memakai /app/app/config.py
#  (ADA di image, Dockerfile COPY app ./app) — tanpa cabang opsional,
#  tidak ada cek yang dilewati. Kalau config hilang, cek GAGAL keras.
#  Cek docs-vs-config TIDAK HILANG: ia pindah ke tempat yang benar, yaitu
#  sot.py periksa_harga(), di mana dokumen memang tersedia (host maupun
#  salinan sot-dok di container). Uji ini tidak lagi berpura-pura
#  memeriksanya dari container.
import os

print('═' * 60)
print('UJI C5 — label rujukan harga/kuota (sumber: config.py di image saja)')
print('═' * 60)

CONFIG = '/app/app/config.py'
print('\n[0] Sumber nilai: app/config.py (di image saja, tanpa path host)')
if os.path.exists(CONFIG):
    cfg = baca(CONFIG)
    cek('config.py memuat KUOTA_PAKET (paket & revisi/bulan)',
        'KUOTA_PAKET' in cfg)
    cek('config.py: Peneliti Rp100.000 / Penerbit Rp300.000',
        '100_000' in cfg and '300_000' in cfg)
    cek('config.py: rumus Token Revisi ÷10.000, cap 60 (TOKEN_REVISI_PER/CAP)',
        'TOKEN_REVISI_PER' in cfg and '10000' in cfg
        and 'TOKEN_REVISI_CAP' in cfg and '60' in cfg)
    cek('config.py: KUOTA_PAKET peneliti & penerbit lengkap (nama, mb, harga)',
        "'peneliti'" in cfg and "'penerbit'" in cfg
        and "'nama'" in cfg and "'mb'" in cfg and "'harga'" in cfg)
    cek('config.py: label harga Rp 100.000 / Rp 300.000',
        'Rp 100.000' in cfg and 'Rp 300.000' in cfg)
else:
    cek('config.py ADA di image (sumber nilai tidak boleh hilang)',
        False, f'path={CONFIG} tidak ditemukan')

# ── A. Kode: rujukan HARUS cocok dengan isi komentarnya ───────────────────
#  Kata kunci yang menandakan TOPIK "Token Revisi" (harus §4.13)
KATA_TOKEN = ('potong', 'token revisi', '÷10.000', '/10.000', '10.000',
              'pengali', 'bagian')


def periksa_baris(path, no_baris, teks):
    """Kembalikan (ok, alasan) untuk satu baris rujukan."""
    if '§4.13' in teks:
        return True, 'menunjuk §4.13'
    if '§4.10' in teks:
        dasar = teks.split('§4.10')[1].lower()
        if any(k in dasar for k in KATA_TOKEN):
            return False, ('menunjuk §4.10 padahal membahas Token Revisi '
                           f'(harus §4.13): "{teks.strip()[:90]}"')
        return True, 'menunjuk §4.10 (topik kuota)'
    return True, 'tidak ada rujukan §'


print('\n[A] Rujukan di app/ai.py')
ai = baca('/app/app/ai.py')
salah = []
for i, baris in enumerate(ai.splitlines(), 1):
    if '§4.1' in baris:
        ok, alasan = periksa_baris('ai.py', i, baris)
        if not ok:
            salah.append(f'ai.py:{i} — {alasan}')

cek('tidak ada rujukan §4.10 yang sebenarnya soal Token Revisi (ai.py)',
    not salah, '; '.join(salah))

print('\n[B] Label "langkah #2" tidak ada lagi')
cek('tidak ada label "langkah #2" di ai.py',
    'langkah #2' not in ai)
cek('tidak ada label "langkah #2" di main.py',
    'langkah #2' not in baca('/app/app/main.py'))

# ── C. Rumus §4.13 benar-benar yang dipakai di kode ──────────────────────
print('\n[C] Rumus Token Revisi = §4.13 (bukan §4.10)')
rumus = [l for l in ai.splitlines()
         if re.search(r'(TOKEN_REVISI|_total_tok|token_revisi)', l)]
cek('kode memakai TOKEN_REVISI (berarti §4.13)',
    any('TOKEN_REVISI' in l for l in rumus),
    f'baris={len(rumus)}')

# ── D. BERGIGI: buktikan uji ini BISA gagal ──────────────────────────────
#  Uji MENYUNTIK sendiri baris yang salah → periksa_baris HARUS bilang TIDAK ok.
print('\n[D] Uji bergigi (memasukkan rujukan yang SALAH ke pemeriksa)')
ok_buruk, alasan_buruk = periksa_baris(
    'x', 0, '# ── KUOTA (MASTER_PLAN §4.10) — potong SEBANYAK BAGIAN, sebelum LLM ──')
cek('pemeriksa MENOLAK "§4.10 … potong SEBAYAK BAGIAN" (yang salah)',
    not ok_buruk, f'pemeriksa bilang ok={ok_buruk}')

ok_baik, _ = periksa_baris(
    'x', 0, '# ── KUOTA (MASTER_PLAN §4.13) — potong SEBANYAK BAGIAN, sebelum LLM ──')
cek('pemeriksa MENERIMA "§4.13 … potong SEBANYAK BAGIAN" (yang benar)',
    ok_baik)

ok_kuota, _ = periksa_baris(
    'x', 0, '# KUOTA AI untuk panel editor (MASTER_PLAN §4.10 — sistem kuota AI)')
cek('pemeriksa MENERIMA "§4.10 — sistem kuota AI" (topik kuota)', ok_kuota)

print('\n' + '═' * 60)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 60)
sys.exit(0 if GAGAL == 0 else 1)
