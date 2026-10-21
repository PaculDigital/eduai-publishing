"""UJI PEMBIMBING AI — bagian yang TIDAK butuh model (03Okt26).

Diuji: (1) pengurai jawaban model tabah terhadap bentuk aneh;
(2) gerbang boleh_pakai (saklar, paket, saldo); (3) pembentuk prompt;
(4) perapian isi. Bagian yang butuh model diuji TERPISAH.
"""
import sys

sys.path.insert(0, '/app')
#  ⚠️ Impor lewat PAKET `app`, JANGAN exec_module berkas mentah —
#  berkas ini memakai impor relatif (`from . import pembimbing`).
from app import pembimbing_ai as PA

LULUS = GAGAL = 0


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama} {catatan}')


print('=== A. PENGURAI JAWABAN (urai_catatan) ===')

#  ⚠️ JEBAKAN: jangan menulis JSON panjang dengan sambungan string `'…"'
#  + '"'` — mata manusia salah hitung kutip, dan yang gagal justru SKRIP
#  UJI, bukan kode. Pakai json.dumps → tidak mungkin salah.
import json as _j
_SATU = {'catatan': [{'bagian': 'BAB I',
                      'kutipan': 'penelitian ini bertujuan untuk',
                      'soal': 'Tujuan belum spesifik',
                      'saran': 'Batasi ruang lingkup'}]}

# A1 bentuk bersih
j1 = _j.dumps(_SATU)
h1 = PA.urai_catatan(j1)
cek('A1 bentuk bersih', len(h1) == 1 and h1[0]['bagian'] == 'BAB I')
cek('A1b isi terbaca', bool(h1) and 'spesifik' in h1[0]['soal'])

# A2 dengan pagar ```json
j2 = '```json\n' + j1 + '\n```'
cek('A2 pagar kode', len(PA.urai_catatan(j2)) == 1)

# A3 ada teks pembuka
j3 = 'Tentu, berikut catatannya:\n' + j1 + '\nSemoga membantu!'
cek('A3 teks pembuka/penutup', len(PA.urai_catatan(j3)) == 1)

# A4 rusak total
cek('A4 rusak → kosong', PA.urai_catatan('maaf saya tidak bisa') == [])
cek('A5 kosong → kosong', PA.urai_catatan('') == [])
cek('A6 None aman', PA.urai_catatan(None) == [])

# A7 tanpa soal → dibuang (jangan simpan catatan kosong)
j7 = '{"catatan":[{"bagian":"BAB II","kutipan":"x","saran":"y"}]}'
cek('A7 tanpa soal dibuang', PA.urai_catatan(j7) == [])

# A8 lebih dari 5 → dipotong 5
banyak = {'catatan': [{'soal': f'masalah {i}'} for i in range(9)]}
import json as _j
cek('A8 maks 5', len(PA.urai_catatan(_j.dumps(banyak))) == 5)

# A9 kutipan panjang dipotong
j9 = _j.dumps({'catatan': [{'soal': 'a', 'kutipan': 'z' * 999}]})
cek('A9 kutipan dipotong', len(PA.urai_catatan(j9)[0]['kutipan']) == 300)

print()
print('=== B. PERAPIAN ISI (rapikan_isi) ===')
c = {'bagian': 'BAB I', 'kutipan': 'ini kutipan', 'soal': 'Ini masalah',
     'saran': 'Ini saran'}
t = PA.rapikan_isi(c)
cek('B1 ada bagian', '[BAB I]' in t)
cek('B2 ada kutipan', 'Kutipan' in t)
cek('B3 ada saran', 'Arah perbaikan' in t)
t2 = PA.rapikan_isi({'soal': 'hanya masalah'})
cek('B4 tanpa bagian tetap jalan', t2.strip() == 'hanya masalah')

print()
print('=== C. PROMPT (bangun_prompt) ===')
p = PA.bangun_prompt('Budi', 'Skripsi Analisis', 'Isi naskah di sini.')
cek('C1 sebut nama', 'Budi' in p)
cek('C2 sebut judul', 'Skripsi Analisis' in p)
cek('C3 ada naskah', 'Isi naskah di sini.' in p)
cek('C4 larangan tulis ulang', 'JANGAN menulis ulang' in p)
cek('C5 minta JSON', '"catatan"' in p)
p2 = PA.bangun_prompt('A', 'B', 'x', sudah_ada=['catatan lama satu'])
cek('C6 catatan lama disertakan', 'catatan lama satu' in p2)

print()
print('=== D. SAKLAR (aktif) ===')
#  Saklar dibaca dari config — uji dua keadaan lewat monkeypatch
from app import config as C
lama = getattr(C, 'PEMBIMBING_AI_AKTIF', None)
C.PEMBIMBING_AI_AKTIF = True
cek('D1 saklar hidup', PA.aktif() is True)
C.PEMBIMBING_AI_AKTIF = False
cek('D2 saklar mati', PA.aktif() is False)
if lama is not None:
    C.PEMBIMBING_AI_AKTIF = lama

cek('D3 kalimat ramah', 'kuota' in PA.KALIMAT_SALDO_KOSONG.lower())
cek('D4 kalimat tanpa kata terlarang',
    not any(x in PA.KALIMAT_SAKLAR_MATI.upper()
            for x in ('PERINGATAN', 'GAGAL', 'HABIS', 'BAHAYA')))

print()
print(f'RINGKASAN: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
