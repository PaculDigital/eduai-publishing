"""UJI C5 — label rujukan harga/kuota harus MENUNJUK KE TOPIK YANG BENAR.

KENAPA ADA (ACC Bos 24Sep26 "C5"):
    Rujukan `§4.10` dan `§4.13` gampang tertukar. Salah rujuk = orang berikutnya
    membaca aturan yang SALAH (harga/kuota vs Token Revisi) → bisa merusak
    rumus yang sudah dikunci Bos.

FAKTA (sumber kebenaran kini: app/config.py + docs/sot/04-harga-dan-kuota.md,
BUKAN berkas arsip):
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


# ── 0. Fakta harga/kuota dari SUMBER YANG ADA DI IMAGE ───────────────────
#  BERGIGI (26 Okt 2026, temuan agen Boss C): bagian ini DULU membaca berkas
#  arsip dari path host dan MELEWATI 2 cek begitu saja kalau berkasnya tidak
#  ada — cek hilang tanpa gagal. Sekarang sumbernya adalah app/config.py,
#  yang ADA di dalam image (Dockerfile COPY app ./app), sehingga cek ini
#  TIDAK PERNAH dilewati. Kalau config.py hilang/rusak, cek ini GAGAL keras.
#  docs/sot/04 hanya dicek tambahan bila ada di host; tidak adanya di
#  container bukan kegagalan, karena cek inti sudah ada di config.py.
import os

print('═' * 60)
print('UJI C5 — label rujukan harga/kuota (sumber: config.py + docs/sot/04)')
print('═' * 60)

CONFIG = '/app/app/config.py'
print('\n[0] Sumber nilai: app/config.py (di image) + docs/sot/04 (host, bila ada)')
if os.path.exists(CONFIG):
    cfg = baca(CONFIG)
    cek('config.py memuat KUOTA_PAKET (paket & revisi/bulan)',
        'KUOTA_PAKET' in cfg)
    cek('config.py: Peneliti Rp100.000 / Penerbit Rp300.000 (sesuai docs/sot/04)',
        '100_000' in cfg and '300_000' in cfg)
    cek('config.py: rumus Token Revisi ÷10.000, cap 60 (TOKEN_REVISI_PER/CAP)',
        'TOKEN_REVISI_PER' in cfg and '10000' in cfg
        and 'TOKEN_REVISI_CAP' in cfg and '60' in cfg)
else:
    cek('config.py ADA di image (sumber nilai tidak boleh hilang)',
        False, f'path={CONFIG} tidak ditemukan')
SOT04 = '/opt/data/services/eduai-publishing/docs/sot/04-harga-dan-kuota.md'
if os.path.exists(SOT04):
    s04 = baca(SOT04)
    cek('docs/sot/04 menyebut config.py sebagai sumber tunggal angka',
        'app/config.py' in s04)
    cek('docs/sot/04: Peneliti Rp100.000 / Penerbit Rp300.000',
        'Rp 100.000' in s04 and 'Rp 300.000' in s04)
else:
    print('     (catatan: docs/sot/04 tidak ada di container — bukan kegagalan, '
          'cek inti di config.py sudah di atas)')

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
