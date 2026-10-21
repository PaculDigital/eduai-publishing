"""UJI TAHAP 1 — SURVEYOR vs HAKIM pada naskah Asih (fid=81).

TUJUAN (putusan Bos 09 Okt, OPSI A): ukur APAKAH hakim (satpam.periksa)
menambah nilai di atas surveyor (peta3_jev). TIDAK mengubah kode produksi.

Cara: jalankan kedua fungsi pada naskah YANG SAMA, cetak berdampingan.
  · SURVEYOR  = peta3_jev.petakan(fid) → bab/sub-bab/paragraf + sistematika
  · HAKIM     = satpam.periksa(teks, peta_mesin) → jumlah_bab, confidence

PAGAR: naskah dibaca lewat app.ai._teks_dari_berkas (jalur RESMI).
JALAN: docker exec -w /app eduai-app python3 _uji_adu_surveyor_hakim.py 81
"""
import json
import sys

sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import state, satpam

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81

# ── 0. BACA NASKAH (JALUR RESMI) ───────────────────────────────────────────
db = SessionLocal()
fb = db.get(FileBerkas, FID)
if not fb:
    print('BERKAS TIDAK DITEMUKAN:', FID)
    sys.exit(1)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
mentah = _teks_dari_berkas(p, fb.nama or '') or ''
bersih = state.buang_daftar_isi(mentah)

print('=' * 78)
print('NASKAH : %s (fid=%d)' % (fb.nama, FID))
print('PANJANG: %d kar · %d baris' % (len(mentah), mentah.count(chr(10)) + 1))
print('=' * 78)

# ── 1. SURVEYOR: peta3_jev ─────────────────────────────────────────────────
print('\n>>> 1. SURVEYOR (peta3_jev.py) — TIDAK panggil Jev, hasil tersimpan')
bab_sv = sub_sv = par_sv = 0
sis_sv = []
gab_sv = 0
sumber = 'HASIL_PETA3_ASIH.json'
try:
    dj = json.load(open('/app/HASIL_PETA3_ASIH.json'))
    lab = dj.get('label') or {}
    gab_sv = len(dj.get('gabung') or [])
    sis_sv = [int(x) for x in (dj.get('sistematika') or [])]
    baris_asli = bersih.split('\n')
    for i, s in sorted(lab.items(), key=lambda x: int(x[0])):
        if s == 'bab':
            bab_sv += 1
        elif s == 'subbab':
            sub_sv += 1
        elif s == 'paragraf':
            par_sv += 1
except Exception as e:
    print('   json ERROR:', e)
    sumber = 'GAGAL'

bab_asli = gab_sv + len([1 for i, s in (lab or {}).items()
                         if s == 'bab' and int(i) not in sis_sv])
print('   sumber    :', sumber)
print('   gabung    : %d  (baris "BAB x" polos)' % gab_sv)
print('   label bab : %d  (kandidat non-sistematika)' % (bab_sv - len(
    [1 for i, s in (lab or {}).items() if s == 'bab' and int(i) in sis_sv])))
print('   sistematika: %s' % sis_sv)
print('   ⇒ BAB ASLI : %d' % bab_asli)
print('   ⇒ sub-bab  : %d' % sub_sv)
print('   ⇒ paragraf : %d' % par_sv)

# ── 2. HAKIM: satpam.periksa (peta MESIN lama, seperti di produksi) ────────
print('\n>>> 2. HAKIM (satpam.periksa) — PANGGIL JEV LEBIH DULU')
peta_mesin = state.petakan(bersih)
print('   peta mesin yang diperiksa: %d bagian' % len(peta_mesin))
for b in peta_mesin[:8]:
    print('      %-8s %-34s %s kar' % (b.get('section_id'), 
          str(b.get('section_title'))[:34], b.get('char_count')))
h = satpam.periksa(bersih, peta_mesin)
print('   keputusan     :', h.get('keputusan'))
print('   confidence    :', h.get('confidence'))
print('   jumlah_bab(Jev):', h.get('jumlah_bab'))
print('   jumlah_bab(mesin):', h.get('jumlah_bab_mesin'))
print('   romawi_sah    :', h.get('romawi_sah'))
print('   berurutan     :', h.get('berurutan'))
print('   kedalaman     :', h.get('kedalaman_subbab'))
print('   detik         :', h.get('detik'))
print('   alasan        :', h.get('alasan'))

# ── 3. BANDING ─────────────────────────────────────────────────────────────
print('\n' + '=' * 78)
print('BANDING — APAKAH HAKIM MENAMBAH NILAI?')
print('=' * 78)
print('   SURVEYOR (peta3_jev)  : BAB=%d · sub-bab=%d · paragraf=%d' % (
    bab_asli, sub_sv, par_sv))
print('   HAKIM (satpam→Jev)    : BAB=%s (conf %s) — periksa peta MESIN (%d bagian)' % (
    h.get('jumlah_bab'), h.get('confidence'), len(peta_mesin)))
print('   MESIN LAMA (petakan)  : %d bagian' % len(peta_mesin))
print()
if h.get('jumlah_bab') is not None:
    if int(h['jumlah_bab']) == bab_asli:
        print('   ⇒ SEPAKAT: Jev(hakim)=%s vs surveyor=%d → hakim TIDAK menambah info baru'
              % (h['jumlah_bab'], bab_asli))
    else:
        print('   ⇒ BEDA: Jev(hakim)=%s vs surveyor=%d → perlu dicek siapa benar'
              % (h['jumlah_bab'], bab_asli))
else:
    print('   ⇒ Hakim tidak menjawab jumlah_bab (mati/ragu)')
db.close()
