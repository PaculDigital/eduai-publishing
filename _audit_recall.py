"""AUDIT RECALL — saringan KODE di SELURUH naskah Asih.
Tampilkan baris yang LOLOS tapi MENCURIGAKAN (calon yang seharusnya dibuang).
Bos: "Wulan bisa bantu audit sisanya yang lolos" (mis. 'Kata Kunci:', nama penulis).

TIDAK memanggil Jev — murni kode. Cepat.
"""
import sys, re
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas

POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')
AMBANG = 70

# ── calon yang MENCURIGAKAN kalau LOLOS (celah recall) ──
_CURIGA = [
    (re.compile(r'^(kata\s+kunci|keywords?|abstrak|abstract)\s*[:.]', re.I), 'PENANDA ABSTRAK/KATA KUNCI'),
    (re.compile(r'^(universitas|sekolah\s+tinggi|program\s+studi|fakultas)\b', re.I), 'NAMA INSTITUSI'),
    (re.compile(r'^\d{6,}\b|\bnim\b|\bnpm\b|\bnidn\b', re.I), 'ANGKA ID MAHASISWA'),
    (re.compile(r'@|\bhttps?://|\bwww\.', re.I), 'EMAIL/URL'),
    (re.compile(r'^daftar\b', re.I), 'PENANDA DAFTAR'),
    (re.compile(r'^(riwayat\s+hidup|biodata|lembar\s+persetujuan|surat\s+pernyataan)\b', re.I), 'HALAMAN AWAL/BIODATA'),
    (re.compile(r'^(tabel|gambar|grafik|bagan)\s*\.?\s*\d', re.I), 'CAPTION (lolos karena panjang?)'),
    (re.compile(r'^(bab\s+[ivx]+)\s*\S', re.I), 'BAB MENEMPEL JUDUL'),
    (re.compile(r'^(dp\s*\d|\d+\s*$)', re.I), 'NOMOR HALAMAN'),
]
_MIN_KAR_PANJANG = 200


def dibuang(s):
    if _PEMBUANG.match(s) or _TITIK_ISI.search(s) or POLA_MARKER.match(s):
        return True
    if POLA_SUMBER.match(s):
        return True
    if POLA_CAPTION.match(s) and len(s) <= AMBANG:
        return True
    return False


FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81
db = SessionLocal()
fb = db.get(FileBerkas, FID)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
print('═' * 72)
print('🔍 AUDIT RECALL — saringan KODE di SELURUH naskah (%s, %d baris)' % (fb.nama, len(baris)))
print('   Mencari baris yang LOLOS tapi MENCURIGAKAN (celah recall)')
print('═' * 72)

lolos_lolos = []
for i, raw in enumerate(baris):
    s = raw.strip()
    if not s:
        continue
    if dibuang(s):
        continue
    for pola, sebut in _CURIGA:
        if pola.search(s):
            lolos_lolos.append((i, sebut, s[:72]))
            break
    else:
        # baris PENDEK (<25 kar) yang lolos juga mencurigakan (calon judul/penanda)
        if len(s) < 25 and not s.endswith('.'):
            lolos_lolos.append((i, 'PENDEK LOLOS', s[:72]))

print('\n📊 JUMLAH LOLOS-MENCURIGAKAN: %d dari %d baris' % (len(lolos_lolos), len(baris)))
dari = {}
for _i, sebut, _s in lolos_lolos:
    dari[sebut] = dari.get(sebut, 0) + 1
print('\n   PER KATEGORI:')
for k, v in sorted(dari.items(), key=lambda x: -x[1]):
    print('      %-28s %d' % (k, v))

print('\n   DAFTAR (maks 60):')
for i, sebut, s in lolos_lolos[:60]:
    print('      L%06d [%s] %s' % (i, sebut, s))
db.close()
