"""ADU PETA MESIN vs JEV — pertanyaan Bos (08 Okt 2026).

Bos: "Apakah sekarang jev sudah bisa memetakan naskah dan lebih baik dari peta
     kasar dan halus mesin."

Mesin (app/state.py):   deteksi_bab_besar() = KASAR · deteksi_subbab() = HALUS
Jev  (peta3_jev.py):    peta 3 tingkat (bab + sub-bab + paragraf)

Naskah: Asih fid=81. Cetak bab & sub-bab dari KETIGA cara berdampingan.
TIDAK memanggil Jev — pakai hasil yang sudah disimpan (HASIL_PETA3_ASIH.json).
"""
import sys, json
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import state

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81
db = SessionLocal()
fb = db.get(FileBerkas, FID)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
mentah = _teks_dari_berkas(p, fb.nama or '') or ''

print('=' * 78)
print('NASKAH: %s — %d kar' % (fb.nama, len(mentah)))
print('=' * 78)

# ── 1. MESIN KASAR: deteksi_bab_besar() ──
try:
    bab_mesin = state.deteksi_bab_besar(mentah)
except Exception as e:
    bab_mesin = []
    print('deteksi_bab_besar ERROR:', e)
print('\n── 1. MESIN KASAR: deteksi_bab_besar() → %d bab' % len(bab_mesin))
for b in bab_mesin[:12]:
    print('   %-28s kar=%-7s asal=%s' % (str(b.get('judul', b.get('title', '?')))[:28],
                                          b.get('char_count', b.get('panjang', '?')), b.get('asal', '-')))

# ── 2. MESIN HALUS: deteksi_subbab() ──
try:
    sub_mesin = state.deteksi_subbab(buang := state.buang_daftar_isi(mentah))
except Exception as e:
    sub_mesin = []
    print('deteksi_subbab ERROR:', e)
print('\n── 2. MESIN HALUS: deteksi_subbab() → %d sub-bab' % len(sub_mesin))
for s in sub_mesin[:14]:
    print('   %-40s kar=%s' % (str(s.get('judul', s.get('title', '?')))[:40], s.get('char_count', '?')))

# ── 3. JEV: peta3 (dari hasil tersimpan) ──
try:
    dj = json.load(open('/app/HASIL_PETA3_ASIH.json'))
    lab = dj['label']
    from app.ai import _teks_dari_berkas as _t
    baris_asli = state.buang_daftar_isi(mentah).split('\n')
    bar = {i: (' '.join(baris_asli[int(i)].split()) if int(i) < len(baris_asli) else '') for i in lab}
    print('\n── 3. JEV peta3_jev.py → bab & sub-bab')
    n_bab = n_sub = n_par = 0
    for i, s in sorted(lab.items(), key=lambda x: int(x[0])):
        if s in ('bab', 'subbab'):
            if s == 'bab': n_bab += 1
            else: n_sub += 1
            print('   [%-6s] L%06d %s' % (s.upper(), int(i), str(bar.get(i, ''))[:56]))
        elif s == 'paragraf':
            n_par += 1
    print('   ⇒ JEV: %d bab · %d sub-bab · %d paragraf' % (n_bab, n_sub, n_par))
except Exception as e:
    print('JEV json ERROR:', e)

# ── 4. BANDING ──
print('\n' + '=' * 78)
print('BANDING JUMLAH')
print('=' * 78)
print('   %-24s bab=%-4s sub-bab=%s' % ('MESIN KASAR (regex)', len(bab_mesin), '-'))
print('   %-24s bab=%-4s sub-bab=%s' % ('MESIN HALUS (regex)', '-', len(sub_mesin)))
print('   %-24s bab=%-4s sub-bab=%s' % ('JEV (peta3)', n_bab if 'n_bab' in dir() else '?', n_sub if 'n_sub' in dir() else '?'))
db.close()
