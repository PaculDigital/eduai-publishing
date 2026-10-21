"""AUDIT RECALL v2 — pakai `buang_daftar_isi()` RESMI dari app/state.py (yang SUDAH ADA).
Bos pilih A: "pakai buang_daftar_isi() yang SUDAH ADA di app/state.py (jangan bikin baru)".

Tujuan: ukur apakah baris halaman-awal + daftar isi NEMPEL (L000052-L000276) tertutup.
"""
import sys, re, difflib
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import state

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81
db = SessionLocal()
fb = db.get(FileBerkas, FID)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
mentah = _teks_dari_berkas(p, fb.nama or '') or ''
baris = mentah.split('\n')

# ── jalankan FUNGSI RESMI ──
hasil = state.buang_daftar_isi(mentah)
baris_hasil = hasil.split('\n')

print('═' * 72)
print('🔍 AUDIT RECALL v2 — buang_daftar_isi() RESMI (app/state.py:478)')
print('   %s · masukan %d baris / %d kar' % (fb.nama, len(baris), len(mentah)))
print('   keluaran %d baris / %d kar  (buang %d baris / %d kar = %.1f%%)'
      % (len(baris_hasil), len(hasil), len(baris) - len(baris_hasil),
         len(mentah) - len(hasil), 100.0 * (len(mentah) - len(hasil)) / max(1, len(mentah))))
print('═' * 72)

# ── baris mana yang HILANG (dibuang)? ──
himp_hasil = set(' '.join(x.split()) for x in baris_hasil if x.strip())
dibuang = [(i, ' '.join(baris[i].split())) for i in range(len(baris))
           if baris[i].strip() and ' '.join(baris[i].split()) not in himp_hasil]
print('\n📊 BARIS DIBUANG: %d' % len(dibuang))
print('\n   Cek 26 baris yang tadi BOCOR (L000052-L000276):')
bocor = [52, 56, 62, 66, 70, 74, 78, 106, 108, 112, 114, 122, 124, 134, 136,
         138, 140, 142, 144, 146, 148, 150, 154, 156, 160, 172, 174, 176, 180,
         184, 196, 198, 200, 210, 212, 226, 228, 230, 234, 238, 276]
kena, lolos = 0, []
for i in bocor:
    if i >= len(baris):
        continue
    s = ' '.join(baris[i].split())
    if not s:
        continue
    if s not in himp_hasil:
        kena += 1
    else:
        lolos.append((i, s[:60]))
print('      ✅ DIBUANG sekarang : %d' % kena)
print('      ⚠️ MASIH LOLOS       : %d' % len(lolos))
for i, s in lolos:
    print('         L%06d %s' % (i, s))

# ── hitung BAB I asli masih ada? ──
idx = [i for i, x in enumerate(baris) if x.strip() == 'BAB I']
idx_h = [i for i, x in enumerate(baris_hasil) if x.strip() == 'BAB I']
print('\n   BAB I: asli %d tempat %s · sesudah buang %d tempat %s'
      % (len(idx), idx[:6], len(idx_h), idx_h[:6]))
db.close()
