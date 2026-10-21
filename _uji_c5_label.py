"""UJI C5 — label rujukan MASTER_PLAN harus MENUNJUK KE BAGIAN YANG BENAR.

KENAPA ADA (ACC Bos 24Sep26 "C5"):
    Rujukan `§4.10` dan `§4.13` gampang tertukar. Salah rujuk = orang berikutnya
    membaca aturan yang SALAH (harga/kuota vs Token Revisi) → bisa merusak
    rumus yang sudah dikunci Bos.

FAKTA (dibaca dari MASTER_PLAN.md, bukan tebakan):
    §4.10 = SISTEM KUOTA & CREDIT AI   (komponen #6 = endpoint GET /api/ai/kuota)
    §4.13 = SISTEM TOKEN REVISI        (KUNCI HARGA & MESIN UANG)

ATURAN YANG DIUJI:
    • Rujukan soal  "potong per bagian / Token Revisi / rumus ÷10.000"  → §4.13
    • Rujukan soal  "kuota / AddOn / paket / sisa revisi-simulasi"      → §4.10
    • Label "langkah #2" TIDAK BOLEH ada (bagian itu tidak ada di MASTER_PLAN)

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


# ── 0. Fakta §4.10 vs §4.13 ──────────────────────────────────────────────
#  ⚠️ MASTER_PLAN.md TIDAK ikut ke dalam image Docker (Dockerfile hanya
#  COPY app ./app). Jadi uji ini TIDAK boleh bergantung padanya — kalau
#  dipaksakan, ujinya gagal karena berkasnya tidak ada, bukan karena bug.
#  Gantinya: periksa JUDUL bagian dari sumber (host) bila ada; kalau tidak
#  ada, tetap lanjut dan cukup andalkan pemeriksaan isi komentar kode.
MP_LOKAL = '/opt/data/services/eduai-publishing/MASTER_PLAN.md'
import os

print('═' * 60)
print('UJI C5 — label rujukan MASTER_PLAN')
print('═' * 60)

if os.path.exists(MP_LOKAL):
    mp = baca(MP_LOKAL)
    judul_410 = re.search(r'^#{2,4}\s*4\.10\s+(.+)$', mp, re.M)
    judul_413 = re.search(r'^#{2,4}\s*4\.13\s+(.+)$', mp, re.M)
    j410 = judul_410.group(1).strip() if judul_410 else '(TIDAK ADA)'
    j413 = judul_413.group(1).strip() if judul_413 else '(TIDAK ADA)'
    print(f'\n[0] §4.10 = {j410}')
    print(f'    §4.13 = {j413}')
    cek('§4.10 memang tentang KUOTA (bukan Token Revisi)',
        'KUOTA' in j410.upper(), f'judul={j410}')
    cek('§4.13 memang tentang TOKEN REVISI',
        'TOKEN REVISI' in j413.upper(), f'judul={j413}')
else:
    print('\n[0] MASTER_PLAN.md tidak ada (di luar container) — bagian [0] dilewati.')
    print('     Isi MASTER_PLAN TIDAK ikut ke image Docker: Dockerfile hanya')
    print('     COPY app ./app. Jadi cukup periksa ISI KOMENTAR kode (bagian A-D).')

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
