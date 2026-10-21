"""TAHAP 1: Jev memeta WILAYAH. Denah = baris ber-ID (pangkas 64 kar).
Jev dikasih pertanyaan choice: baris ini termasuk wilayah apa?
Uji pada WINDOW yang berbeda-beda supaya hemat tapi tetap bukti.
"""
import sys, time, json
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
baris = [' '.join(b.split()) for b in t.split('\n')]

# Denah: TANPA pangkas isi kosong, beri ID. Pangkas 64 kar.
denah = '\n'.join(f'{i:04d}|{b[:64]}' for i, b in enumerate(baris))
print(f'denah: {len(denah):,} kar (~{len(denah)//4:,} token)')

# Uji: apakah Jev bisa menandai wilayah pada BEBERAPA titik acak?
TITIK = [5, 100, 145, 200, 240, 300, 355, 380, 400, 500, 545, 600, 700,
         740, 900, 960, 1100, 1190, 1300, 1500, 1800, 2000, 2220]
q = {}
for i in TITIK:
    q[f'w{i:04d}'] = {
        'instructions': f'Wilayah apa baris {i:04d} pada denah naskah di atas?',
        'type': 'choice',
        'criteria': {
            'cover': 'halaman muka/sampul, judul skripsi, nama penulis, logo',
            'abstrak': 'abstrak atau kata pengantar/prakata',
            'daftar': 'daftar isi, daftar tabel, daftar gambar, daftar lampiran',
            'sistematika': 'blok penjelasan ringkas isi tiap bab (sistematika penulisan)',
            'bab': 'isi bab akademik yang sebenarnya (uraian panjang)',
            'pustaka': 'daftar pustaka / referensi',
            'lampiran': 'lampiran, kuesioner, tabulasi, dokumentasi, riwayat hidup',
        },
    }
print(f'\npertanyaan: {len(q)}')
t0 = time.time()
jawab = satpam.tanya_bebas_mutu(denah, q) or {}
print(f'Jev: {time.time()-t0:.2f} dtk\n')
for i in TITIK:
    a = jawab.get(f'w{i:04d}') or {}
    print(f'  {i:05d} {str(a.get("choice")):12} conf={a.get("confidence")}  {baris[i][:48]}')
