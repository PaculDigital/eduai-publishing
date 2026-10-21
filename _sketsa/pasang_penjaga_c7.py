"""TANDAI uji C7 agar TIDAK dijalankan sembarangan (permintaan Wulan, disetujui Bos).

KENAPA: `_uji_publik_komentar.py` MENEMBAK endpoint nyata di produksi:
    · memanggil AI (memakai kuota akun uji)
    · MENULIS ke DB produksi (versi_dokumen/proses_ai)
    Sebelum C10 tayang, tiap jalan = 1 naskah hilang. Sekarang pagar C10
    mencegah naskah rusak, TAPI kuota tetap terpakai & DB tetap tertulis.
    ⇒ WAJIB ada penanda di kepala berkas + penjaga yang menolak jalan
      tanpa setuju (E2E_SAYA_SETUJU=1).
"""
import pathlib
import re

P = pathlib.Path('/opt/data/services/eduai-publishing/_uji_publik_komentar.py')
s = P.read_text()

# ── 1. Sisipkan PENJAGA setelah impor (sebelum kerja apa pun) ────────────
PENJAGA = '''
# ═══════════════════════════════════════════════════════════════════════════
#  🛑 PENJAGA PRODUKSI — uji ini MENULIS ke data NYATA.
#  WAJIB setuju dulu:  E2E_SAYA_SETUJU=1 python3 _uji_publik_komentar.py
#  Alasan: memanggil AI (memakai kuota akun uji) + menulis DB produksi.
#  Wajib pula: BACKUP DB dulu (`_arsip/pra-sot/<image>/eduai.db`).
# ═══════════════════════════════════════════════════════════════════════════
if os.getenv('E2E_SAYA_SETUJU', '') != '1':
    print('🛑 UJI INI MENYENTUH PRODUKSI (memakai kuota + menulis DB nyata).')
    print('   Wajib setuju + backup DB dulu, lalu jalankan:')
    print('     E2E_SAYA_SETUJU=1 python3 _uji_publik_komentar.py')
    print('   Untuk skenario berat: tambah E2E_BERAT=1')
    sys.exit(77)          # 77 = KODE_LEWAT (dilewati, bukan gagal)
'''

#  Sisipkan SETELAH blok impor pertama (baris 'import sys' atau sejenisnya).
m = re.search(r'^(import .*\n)+', s, re.M)
if m:
    pos = m.end()
    s = s[:pos] + PENJAGA + s[pos:]
    print('✅ penjaga disisipkan')
else:
    print('❌ gagal menemukan blok impor')

P.write_text(s)
print(f'  berkas: {P} ({len(s):,} byte)')
