"""AKAR: uji urai_catatan dengan jawaban NYATA, satu langkah demi satu.

Jawaban nyata: 2518 karakter, JSON sah, 5 butir, kunci: bagian/kutipan/soal/saran.
Kalau JSON sah tapi urai balas 0 → akarnya di DALAM urai_catatan.
"""
import json
import sys

sys.path.insert(0, '/app')
from app import pembimbing_ai as PAI

#  Jawaban NYATA dari model (disimpan apa adanya, ini bukan karangan)
JAWAB = json.dumps({
    "catatan": [
        {"bagian": "Bab III — Jadwal Penelitian",
         "kutipan": "Penelitian ini akan dilaksanakan pada bulan Juli",
         "soal": "Sub-bab Jadwal Penelitian masih tercantum padahal "
                 "seharusnya dihapus sebelum seminar.",
         "saran": "Hapus sub-bab Jadwal Penelitian dari naskah."},
        {"bagian": "Halaman Judul",
         "kutipan": "JUDUL SKRIPSI ANDA DALAM HURUF KAPITAL",
         "soal": "Judul masih placeholder.", "saran": "Isi judul sebenarnya."},
    ]
}, ensure_ascii=False)

print('=== JSON uji panjang:', len(JAWAB))
hasil = PAI.urai_catatan(JAWAB)
print('urai_catatan →', len(hasil), 'butir')
for h in hasil:
    print('   -', h['bagian'], '|', h['soal'][:60])
print()

print('=== Uji potongan satu per satu (cari langkah yang memutus) ===')
teks = JAWAB.strip()
mulai = teks.find('{')
dalam, akhir = 0, -1
for i in range(mulai, len(teks)):
    if teks[i] == '{':
        dalam += 1
    elif teks[i] == '}':
        dalam -= 1
        if dalam == 0:
            akhir = i + 1
            break
print('mulai', mulai, 'akhir', akhir, 'panjang', len(teks))
data = json.loads(teks[mulai:akhir])
print('json.loads OK, kunci:', list(data.keys()))
butir = data.get('catatan')
print('butir:', type(butir).__name__, len(butir) if isinstance(butir, list) else '')
for i, c in enumerate(butir if isinstance(butir, list) else []):
    soal = str(c.get('soal') or '').strip()
    print(f'  butir {i}: soal kosong={not soal} panjang={len(soal)}')

print()
print('=== KESIMPULAN ===')
if len(hasil) > 0:
    print('urai_catatan BEKERJA dengan JSON bersih → akarnya di jawaban NYATA,')
    print('bukan di fungsi ini. Perlu lihat jawaban nyata karakter demi karakter.')
else:
    print('urai_catatan GAGAL walau JSON bersih → akarnya DI DALAM fungsi.')
