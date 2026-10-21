"""AUDIT RECALL PER-ATURAN (langkah 1 Bos) — hitung apa yang DIMAKAN tiap saringan.

Bos: "Audit recall tiap aturan saringan di naskah utuh — hitung apa yang dimakan
     tiap aturan, bukan cuma apakah yang dibuang sudah benar."

Menjalankan tiap saringan SENDIRI-SENDIRI atas seluruh naskah, hitung berapa baris
dimakan, dan tunjukkan contoh. TIDAK memanggil Jev.
"""
import sys, re
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import state

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81
db = SessionLocal()
fb = db.get(FileBerkas, FID)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
mentah = _teks_dari_berkas(p, fb.nama or '') or ''
bersih = state.buang_daftar_isi(mentah)
baris = bersih.split('\n')

# ── aturan-aturan yang DIPAKAI di peta3_jev.py ──
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')
AMBANG_CAPTION = 70

ATURAN = [
    ('1. _PEMBUANG (penanda daftar/sumber)', lambda s: bool(_PEMBUANG.match(s))),
    ('2. _TITIK_ISI (daftar isi ber-titik)', lambda s: bool(_TITIK_ISI.search(s))),
    ('3. POLA_MARKER [[..]]', lambda s: bool(POLA_MARKER.match(s))),
    ('4. POLA_SUMBER', lambda s: bool(POLA_SUMBER.match(s))),
    ('5. POLA_CAPTION pendek (<=70)', lambda s: bool(POLA_CAPTION.match(s) and len(s) <= AMBANG_CAPTION)),
    ('6. _subbab_palsu (dipakai Wulan — SALAH!)', lambda s: bool(state._subbab_palsu('', s, s))),
]

print('=' * 74)
print('AUDIT RECALL PER-ATURAN — %s' % fb.nama)
print('   %d baris sesudah buang_daftar_isi' % len(baris))
print('=' * 74)
total_isi = sum(1 for x in baris if x.strip())
print('   baris berisi: %d\n' % total_isi)

for nama, fn in ATURAN:
    kena = [i for i, x in enumerate(baris) if x.strip() and fn(x.strip())]
    print('%-42s → %4d baris (%.0f%%)' % (nama, len(kena), 100.0 * len(kena) / max(1, total_isi)))
    # tunjukkan 4 contoh + apakah ada yang PANJANG (calon paragraf asli!)
    for i in kena[:4]:
        t = ' '.join(baris[i].split())
        print('      L%06d (%3d kar) %s' % (i, len(t), t[:56]))
    panjang = [i for i in kena if len(' '.join(baris[i].split())) > 100]
    if panjang:
        print('      🚨 %d di antaranya >100 kar (CALON PARAGRAF ASLI!):' % len(panjang))
        for i in panjang[:3]:
            print('         L%06d (%d kar) %s' % (i, len(baris[i].strip()), ' '.join(baris[i].split())[:50]))
    print()

print('=' * 74)
print('GABUNGAN semua aturan (yang benar-benar dibuang di peta3_jev.py):')
def dibuang(s):
    for nama, fn in ATURAN:
        if fn(s):
            return True
    return False
gb = [i for i, x in enumerate(baris) if x.strip() and dibuang(x.strip())]
print('   %d baris dibuang (%.0f%%) · %d tersisa' % (len(gb), 100.0 * len(gb) / max(1, total_isi), total_isi - len(gb)))
# berapa paragraf asli (>80 kar) yang ikut terbuang?
panjang_gb = [i for i in gb if len(' '.join(baris[i].split())) > 80]
print('   🚨 dari itu, %d baris PANJANG (>80 kar) = paragraf asli yang HILANG' % len(panjang_gb))
db.close()
