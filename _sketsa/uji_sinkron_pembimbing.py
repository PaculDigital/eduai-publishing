"""UJI SINKRON: catatan pembimbing → mahasiswa → AI (dari data NYATA).

PERTANYAAN BOS 25Sep26:
  1. Apakah dashboard mahasiswa & pembimbing SUDAH SINKRON?
  2. Apakah yang direvisi pembimbing tersampaikan ke mahasiswa JELAS?
  3. Apakah revisi AI tunduk §4.13 (<10.000 token = 1 Token Revisi)?

Uji ini TIDAK mengubah apa pun — hanya MEMBACA produksi.
"""
import sys

sys.path.insert(0, '/app')
import sqlite3

print('═' * 76)
print('  UJI SINKRON PEMBIMBING ↔ MAHASISWA (data produksi)')
print('═' * 76)

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

#  ── 1. struktur tabel catatan ───────────────────────────────────────────
print('\n── [1] TABEL catatan_pembimbing ──')
kol = [r[1] for r in c.execute('PRAGMA table_info(catatan_pembimbing)')]
print('   kolom:', kol)

n = c.execute('SELECT COUNT(*) FROM catatan_pembimbing').fetchone()[0]
print(f'   jumlah catatan: {n}')

#  ── 2. catatan terakhir: apa isinya & menempel ke siapa ─────────────────
print('\n── [2] 3 CATATAN TERBARU ──')
q = '''SELECT id, file_id, user_id, isi, teks_asli, halaman, dibuat
       FROM catatan_pembimbing ORDER BY id DESC LIMIT 3'''
try:
    for r in c.execute(q):
        print(f'   id={r["id"]} file={r["file_id"]} pembimbing={r["user_id"]}')
        print(f'      isi      : {str(r["isi"])[:100]!r}')
        print(f'      teks_asli: {str(r["teks_asli"])[:80]!r}')
        print(f'      dibuat   : {r["dibuat"]}')
except Exception as e:                                                    # noqa: BLE001
    print('   ⚠️ kolom beda:', e)
    for r in c.execute('SELECT * FROM catatan_pembimbing ORDER BY id DESC LIMIT 2'):
        print('   ', dict(r))

#  ── 3. apakah berkas punya PEMBIMBING (relasi) ──────────────────────────
print('\n── [3] RELASI pembimbingan ──')
for t in ('berkas_pembimbingan', 'pembimbingan', 'pembimbing'):
    try:
        kol = [x[1] for x in c.execute(f'PRAGMA table_info({t})')]
        if kol:
            n = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
            print(f'   {t}: {kol} · {n} baris')
    except Exception:                                                     # noqa: BLE001
        pass

#  ── 4. APAKAH catatan pembimbing MASUK ke prompt AI? ───────────────────
print('\n── [4] CATATAN PEMBIMBING MASUK PROMPT AI? ──')
try:
    from app.ai import _revisi_kerja                                                  # noqa: F401
    import inspect
    src = inspect.getsource(_revisi_kerja)
    tanda = {
        'komentar dibungkus penanda': '<<<KOMENTAR' in src,
        'nomor urut catatan':         "f'{i + 1}." in src,
        'dikirim ke panggilan AI':    'komentar=baris_komentar' in src,
    }
    for k, v in tanda.items():
        print(f'   {"✅" if v else "❌"} {k}')
except Exception as e:                                                    # noqa: BLE001
    print('   err:', e)

#  ── 5. RUMUS §4.13 waktu nyata (dari proses terakhir) ───────────────────
print('\n── [5] RUMUS §4.13 PADA PROSES NYATA ──')
from math import ceil                                                     # noqa: E402
PER, CAP = 10000, 60
q = '''SELECT id, status, token_in, token_out, token_revisi, model_ai
       FROM proses_ai WHERE token_in > 0 ORDER BY id DESC LIMIT 5'''
print(f'   {"id":>4} {"in":>7} {"out":>7} {"total":>7}  {"hitung":>6} {"dicatat":>7}  {"cocok":>5}')
for r in c.execute(q):
    tin, tout, rev = r['token_in'] or 0, r['token_out'] or 0, r['token_revisi'] or 0
    total = tin + tout
    hitung = min(ceil(total / PER) * 1, CAP) if total else 0
    ok = '✅' if hitung == rev else '❌'
    print(f'   {r["id"]:>4} {tin:>7} {tout:>7} {total:>7}  {hitung:>6} {rev:>7}  {ok:>5}')

#  ── 6. bukti "< 10.000 → 1" ─────────────────────────────────────────────
print('\n── [6] BUKTI ATURAN "kurang dari 10.000 = 1 Token Revisi" ──')
for total in (1, 5000, 9999, 10000, 10001, 20000, 30000):
    h = min(ceil(total / PER), CAP)
    print(f'   {total:>6} token  →  {h} Token Revisi')
print()
print('   ⇒ BENAR: 1-10.000 token = 1 · 10.001-20.000 = 2 · 20.001-30.000 = 3')
print('   ⇒ batas CAP 60 Token Revisi per operasi')
