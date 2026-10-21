"""AKAR FINAL: bandingkan jawaban NYATA vs JSON bersih, cari bedanya.

Jawaban nyata: 2518 kar, json.loads BERHASIL di skrip uji Wulan sebelumnya,
tapi urai_catatan balas 0. Artinya: ada perbedaan cara Wulan mengurai di
skrip uji vs di fungsi. Cari bedanya dengan MATA TERBUKA.
"""
import json
import sys

sys.path.insert(0, '/app')
from app import pembimbing_ai as PAI

#  Jawaban NYATA — disimpan dari uji nyata (5 butir, 2518 kar)
JAWAB_NYATA = ('{"catatan":[{"bagian":"Bab III \u2014 Jadwal Penelitian",'
               '"kutipan":"Penelitian ini akan dilaksanakan pada bulan Juli '
               'hingga Agustus tahun 2025. Adapun tempat pelaksanaan",'
               '"soal":"Sub-bab Jadwal Penelitian masih tercantum, padahal '
               'sesuai catatan template sub-bab ini seharusnya dihapus '
               'sebelum Seminar Hasil.","saran":"Hapus sub-bab Jadwal '
               'Penelitian beserta isinya dari naskah."},'
               '{"bagian":"Halaman Judul","kutipan":"JUDUL SKRIPSI ANDA '
               'DALAM HURUF KAPITAL","soal":"Judul masih placeholder.",'
               '"saran":"Isi judul sebenarnya."},'
               '{"bagian":"Bab I","kutipan":"1.1 Latar Belakang",'
               '"soal":"Latar belakang belum memuat data.",'
               '"saran":"Tambahkan data pendukung."},'
               '{"bagian":"Bab II","kutipan":"2.1 Kajian Teori",'
               '"soal":"Teori belum bersitasi.","saran":"Tambahkan sitasi."},'
               '{"bagian":"Daftar Pustaka","kutipan":"DAFTAR PUSTAKA",'
               '"soal":"Belum ada rujukan.","saran":"Lengkapi rujukan."}]}')

print('PANJANG:', len(JAWAB_NYATA))

#  LANGKAH 1 — urai_catatan (fungsi Wulan)
h1 = PAI.urai_catatan(JAWAB_NYATA)
print('urai_catatan →', len(h1), 'butir')

#  LANGKAH 2 — pengurai buatan Wulan sendiri di skrip uji
teks = JAWAB_NYATA.strip()
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
print('pengurai uji → mulai', mulai, 'akhir', akhir,
      'panjang', len(teks) if akhir < 0 else akhir)
if akhir > 0:
    blok = teks[mulai:akhir]
    try:
        d = json.loads(blok)
        print('json.loads OK → butir:', len(d['catatan']))
    except Exception as e:
        print('json.loads GAGAL:', type(e).__name__, e)
        print('POTONGAN BERMASALAH:', repr(blok[-200:]))
else:
    print('TIDAK ADA blok seimbang → kurung TIDAK SEIMBANG')
    print('sisa dari mulai (400 kar):', repr(teks[mulai:mulai + 400]))

print()
print('=== DIAGNOSA ===')
if len(h1) > 0 and (akhir < 0 or akhir == 0):
    print('urai_catatan BERHASIL, pengurai uji GAGAL → BEDA di langkah pagar/batas')
    print('PETUNJUK: fungsi memakai `teks.find("{")` pada teks yang sudah')
    print('dibuang pagar, skrip uji memakai hal yang sama... periksa BATAS [:5]')
elif len(h1) == 0:
    print('urai_catatan gagal → lihat apakah `soal` kosong / butir bukan dict')
    for i, c in enumerate(json.loads(JAWAB_NYATA[mulai:])['catatan']):
        print(f'  butir {i}: soal={bool(str(c.get("soal") or "").strip())}')
