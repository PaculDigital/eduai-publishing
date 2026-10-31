"""Uji ukur_kedalaman (paket sempurna, Gas Bos 31 Okt 2026 malam,
item 3). Jalankan dari root checkout: python3 uji_kedalaman.py
Tidak menyentuh DB produksi, tidak memanggil API, tidak memakai LLM.
Hanya fungsi murni ukur_kedalaman (dimuat langsung dari berkas).
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    'sitasi_anti_gagal',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'app', 'sitasi_anti_gagal.py'))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
ukur = _mod.ukur_kedalaman

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


rows = [
    {'kunci': 'vial', 'alias': [], 'tahun': '2019'},
    {'kunci': 'tidaar', 'alias': [], 'tahun': '2019'},
    {'kunci': 'lungu', 'alias': [], 'tahun': '2022'},
]
bab1 = (
    'Transformasi digital dipahami sebagai perubahan mendasar dalam cara '
    'organisasi menciptakan nilai melalui teknologi informasi yang '
    'terintegrasi dengan proses bisnis dan perilaku pelanggan secara '
    'menyeluruh (Vial, 2019). '
    'Vial (2019) menegaskan bahwa transformasi bukan sekadar adopsi '
    'perangkat lunak, melainkan rekonstruksi model bisnis, struktur '
    'organisasi, dan budaya kerja yang saling berkaitan dalam jangka '
    'panjang. '
    'Implikasi dari kerangka Vial (2019) adalah bahwa kegagalan '
    'transformasi sering berakar pada ketidakcocokan antara ambisi '
    'digital dan kesiapan proses internal organisasi yang bersangkutan. '
    'Usaha kecil adalah pilar ekonomi bangsa (Tidaar, 2019).')
bab2 = (
    'Usaha kecil adalah pilar ekonomi bangsa yang menopang ketahanan '
    'ekonomi nasional di tengah tekanan eksternal yang terus meningkat '
    '(Tidaar, 2019). '
    'Hal lain dibahas di sini tanpa sitasi yang relevan sama sekali '
    'dengan panjang kalimat yang cukup untuk pengujian.')
bab3 = (
    'Usaha kecil adalah pilar ekonomi bangsa yang menopang ketahanan '
    'ekonomi nasional di tengah tekanan eksternal yang terus meningkat '
    '(Tidaar, 2019). '
    'Pembahasan lain yang tidak mengutip siapa pun juga hadir di sini '
    'sebagai pengisi bab ketiga dalam pengujian ini.')
hasil = ukur({1: bab1, 2: bab2, 3: bab3},
             {1: rows, 2: rows, 3: rows})
pb1 = hasil['per_bab']['1']
cek('dalam-hitung-kalimat', pb1['vial-2019']['kalimat'] == 3,
    str(pb1['vial-2019']))
cek('dalam-tidak-dangkal', not pb1['vial-2019']['dangkal'],
    str(pb1['vial-2019']))
cek('dangkal-satu-kalimat-pendek', pb1['tidaar-2019']['dangkal'] is True,
    str(pb1['tidaar-2019']))
cek('tidak-dikutip-dangkal', pb1['lungu-2022']['kalimat'] == 0
    and pb1['lungu-2022']['dangkal'] is True, str(pb1['lungu-2022']))
cek('refrain-tidaar-terdeteksi',
    any(r['artikel'] == 'tidaar-2019' for r in hasil['refrain']),
    str(hasil['refrain']))
cek('refrain-vial-tidak-terdeteksi',
    not any(r['artikel'] == 'vial-2019' for r in hasil['refrain']),
    str(hasil['refrain']))
cek('ringkas-dangkal', hasil['ringkas']['dangkal_total'] >= 1,
    str(hasil['ringkas']))

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
