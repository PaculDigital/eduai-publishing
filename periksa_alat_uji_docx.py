"""PERIKSA ALAT UJI — apakah yang dilaporkan "5 paragraf >7 kalimat" itu NYATA?

Sebelum menyalahkan kode, periksa ALAT UKUR (pelajaran 15 Okt 2026:
"PRODUKSI SEHAT, yang rusak ALAT UJI").

Yang dipertanyakan: `nkal()` di `uji_docx_jev_buku.py` menghitung kalimat
dengan `split('.')`. Itu MENGHITUNG SALAH untuk:
  · singkatan       "et al.", "dkk.", "No.", "Gbr."
  · inisial         "R. A. Kartini"
  · desimal         "11.5", "1.234"
  · URL/DOI         "https://www.bmkg.go.id"
  · elipsis         "…"

Skrip ini membandingkan TIGA penghitung pada paragraf yang SAMA:
  1. nkal_uji    — split('.') seperti alat uji sekarang
  2. nkal_tata   — tata_paragraf.pecah_kalimat() = yang dipakai produksi
  3. nkal_mata   — hitung manual tiap kalimat, cetak untuk diperiksa manusia
"""
import json
import sys

sys.path.insert(0, '/app')
import tata_paragraf as T                 # noqa: E402
from docx import Document                  # noqa: E402

DOCX = '/tmp/uji_buku_jev/UJI_JEV_BUKU.docx'
d = Document(DOCX)


def nkal_uji(t):
    """Cara alat uji sekarang (split titik) — DIDUGA SALAH."""
    return len([k for k in t.replace('!', '.').replace('?', '.').split('.')
                if k.strip()])


def nkal_tata(t):
    """Cara produksi (tata_paragraf.pecah_kalimat)."""
    return len(T.pecah_kalimat(t))


print(f"{'split':>6} | {'tata':>5} | {'beda':>5} | AWAL TEKS")
print('-' * 100)

beda = []
for p in d.paragraphs:
    t = p.text.strip()
    if p.style.name == 'List Bullet' or len(t) < 40:
        continue
    a, b = nkal_uji(t), nkal_tata(t)
    if a > 7 or b > 7:
        tanda = '  <<< BEDA' if a != b else ''
        print(f'{a:>6} | {b:>5} | {a - b:>5} | {t[:62]}{tanda}')
        if a != b:
            beda.append({'split': a, 'tata': b, 'teks': t[:200]})

print()
print('=== PARAGRAF YANG DIANGGAP SALAH OLEH ALAT UJI, TAPI BENAR MENURUT PRODUKSI ===')
for b in beda:
    if b['split'] > 7 >= b['tata']:
        print(json.dumps(b, ensure_ascii=False, indent=1))

print()
print(json.dumps({
    'alat_uji_salah_hitung': len(beda),
    'masih_lewat_setelah_koreksi': sum(1 for p in d.paragraphs
                                       if p.style.name != 'List Bullet'
                                       and len(p.text.strip()) >= 40
                                       and nkal_tata(p.text.strip()) > 7),
}, ensure_ascii=False))
