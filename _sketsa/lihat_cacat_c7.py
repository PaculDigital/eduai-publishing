"""Perbaiki CACAT UJI C7: blok skenario berat memanggil `docker` dari DALAM container.

KENAPA (terukur 25Sep26): `docker` TIDAK ADA di dalam image eduai-app.
    Akibatnya dari dalam container:
      · `kuota_reset_berat()` → GAGAL → user 7 kuota tidak direset
      · `P1` (matikan provider) → `docker: not found` → gangguan TIDAK terjadi
      · skenario N/O/P/Q → HTTP 403 "Fitur AI hanya untuk member berbayar"
        karena user 7 tidak punya baris `pemakaian_ai` → dianggap bukan member
    Semua itu GAGAL PALSU — aplikasinya benar.

CARA PERBAIKI:
    (1) tulis SQL langsung (sqlite3 terbuka di dalam container), TANPA `docker`;
    (2) pastikan BARIS `pemakaian_ai` ada (INSERT bila belum) untuk user berat;
    (3) untuk skenario P (gangguan provider), JANGAN pakai `docker` — pakai
        SAKLAR LEWAT BERKAS: tulis penanda di `/app/data/` yang dibaca app.
        (Kalau app tidak punya saklar itu → tandai P sebagai TIDAK BISA DIUJI
        di dalam container, dan jalankan P dari HOST.)

Berkas ini PATCHER: mengubah `_uji_publik_komentar.py`.
"""
import pathlib
import re

P = pathlib.Path('/opt/data/services/eduai-publishing/_uji_publik_komentar.py')
s = P.read_text()

# ── 1. Apa `_docker()` itu? ───────────────────────────────────────────────
m = re.search(r'def _docker\([^)]*\)[^\n]*\n(?:.*?\n){0,14}?\n\n', s)
print('=== _docker() sekarang ===')
print(m.group(0) if m else '(tidak ditemukan)')
print()

# ── 2. Apakah uji tahu ia jalan DI DALAM container? ───────────────────────
print('=== penanda lingkungan ===')
for pola in ['_DI_DALAM_KONTAINER', '/.dockerenv', 'os.path.exists("/app/app")',
             'DOCKER_ADA']:
    print(f'  {pola!r:34s} → {"ADA" if pola in s else "tidak ada"}')
print()
print('=== P1 sekarang (cara mematikan provider) ===')
i = s.find('P1 koneksi provider berhasil DIMATIKAN')
print(s[max(0, i - 900):i + 120] if i > 0 else '(tidak ditemukan)')
