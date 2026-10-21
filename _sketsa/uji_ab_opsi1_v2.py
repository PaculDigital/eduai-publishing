"""A/B OPSI 1 v2 — PENGHAMBAT CACHE: tiap kiriman memakai prompt UNIK.

Pelajaran dari v1: A & B dengan prompt identik → provider mengembalikan
cache (0,9 dtk, token_out identik) → perbandingan TIDAK sah.

v2: teks komentar diacak per pasang supaya tak ada yang bisa cache.
    A = pola app (tanpa parameter)   — LAMA
    B = enable_thinking: false       — BARU
Dinilai oleh pemeriksa app sungguhan `_urai_jawaban()` (finish + _valid).
"""
import json, os, time, urllib.error, urllib.request, random

BASE = os.environ.get('EDUAI_FALLBACK_BASE', '')
KEY = os.environ.get('EDUAI_FALLBACK_KEY', '')
URL = BASE.rstrip('/') + '/chat/completions'

import sys
sys.path.insert(0, '.')
from app.ai import SYSTEM_REVISI, _urai_jawaban  # noqa: E402

NASKAH = (
    'Metode penelitian ini menggunakan pendekatan kuantitatif. '
    'Populasi dalam penelitian ini adalah seluruh mahasiswa semester akhir '
    'yang berjumlah 1.200 orang. Sampel diambil dengan teknik proportionate '
    'stratified random sampling sehingga setiap program studi terwakili. '
    'Data dikumpulkan menggunakan kuesioner daring yang telah diuji '
    'validitas dan reliabilitasnya dengan Cronbach alpha sebesar 0,91. '
    'Analisis data memakai regresi linear berganda memakai bantuan '
    'program SPSS versi 26.\n'
)

#  variasi unik per pasang (mengubah prompt → menembus cache)
VARIASI = [
    ('Kalimat "memakai bantuan" terasa bertele-tele.',
     'Singkatkan kalimat populasinya.'),
    ('Frasa "memakai bantuan" terlalu berbelit.',
     'Perjelas kalimat populasi supaya ringkas.'),
    ('Cara menyusun kata "memakai bantuan" kurang tepat.',
     'Padatkan kalimat tentang populasi penelitian.'),
]


def tugas(v):
    return (
        'NASKAH:\n' + NASKAH +
        '\nKOMENTAR:\n[K1] ' + v[0] + '\n[K2] ' + v[1] + '\n\n'
        'Balas HANYA dengan pasangan penanda:\n'
        '[K1-KUTIP-ASLI] <kalimat asli persis>\n'
        '[K1-GANTI-JADI] <penggantinya>\n'
        '[K2-KUTIP-ASLI] <kalimat asli persis>\n'
        '[K2-GANTI-JADI] <penggantinya>'
    )


def kirim(tag, tambahan, tgs, max_tok=8000, timeout=300):
    p = {'model': 'glm-5.3-flash', 'max_tokens': max_tok, 'temperature': 0.2,
         'messages': [{'role': 'system', 'content': SYSTEM_REVISI},
                      {'role': 'user', 'content': tgs}]}
    p.update(tambahan)
    req = urllib.request.Request(
        URL, data=json.dumps(p).encode(), method='POST',
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            teks = r.read().decode('utf-8', 'ignore')
    except Exception as e:                                   # noqa: BLE001
        out = {'tag': tag, 'ok': False, 'galat': type(e).__name__ + ': ' + str(e)[:250]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out, ''
    dt = time.monotonic() - t0
    try:
        konten, info = _urai_jawaban(teks, 'glm-5.3-flash')
        lolos, alasan = True, 'LOLOS'
    except Exception as e:                                   # noqa: BLE001
        konten, info, lolos, alasan = '', {}, False, 'DITOLAK: ' + str(e)[:200]
    out = {'tag': tag, 'ok': True, 'dt': round(dt, 1),
           'finish': info.get('finish'), 'lolos': lolos, 'alasan': alasan,
           'panjang': len(konten),
           'token_in': info.get('token_in'), 'token_out': info.get('token_out')}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return out, konten


def mutu(teks):
    kena = 0
    for blok in teks.split('['):
        if 'KUTIP-ASLI]' in blok:
            kal = blok.split('KUTIP-ASLI]', 1)[1].strip().strip(':').strip()
            kal = kal.split('\n')[0].strip()
            if kal and kal in NASKAH:
                kena += 1
    return kena


hasil = {'lama': [], 'baru': [], 'mutu_lama': [], 'mutu_baru': []}
for i, v in enumerate(VARIASI, 1):
    tgs = tugas(v)
    print(f'\n── pasang {i} ──', flush=True)
    a, isi_a = kirim(f'A{i}-lama', {}, tgs)
    hasil['lama'].append(a)
    hasil['mutu_lama'].append(mutu(isi_a))
    time.sleep(2)
    #  prompt B = pasangan berbeda tapi setara (anti-cache)
    v2 = VARIASI[i % len(VARIASI)]
    b, isi_b = kirim(f'B{i}-baru', {'enable_thinking': False}, tugas(v2))
    hasil['baru'].append(b)
    hasil['mutu_baru'].append(mutu(isi_b))
    time.sleep(2)

def ringkas(kunci):
    oke = [x for x in hasil[kunci] if x.get('ok')]
    if not oke:
        return '0 sukses'
    dts = [x['dt'] for x in oke]
    lolos = sum(1 for x in oke if x.get('lolos'))
    return (f'{lolos}/{len(oke)} lolos · durasi '
            f'min/avg/max = {min(dts):.1f}/{sum(dts)/len(dts):.1f}/{max(dts):.1f} dtk'
            f' · token_out = {[x.get("token_out") for x in oke]}')

print('\nRINGKAS LAMA :', ringkas('lama'), flush=True)
print('RINGKAS BARU :', ringkas('baru'), flush=True)
print('MUTU kutip   : lama', hasil['mutu_lama'], '· baru',
      hasil['mutu_baru'], flush=True)

with open('/tmp/uji_ab_v2.json', 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)
print('arsip: /tmp/uji_ab_v2.json', flush=True)
