"""B. A/B OPSI 1 — `enable_thinking: false` di jalur 2 (tokenharbor).

Tugas revisi NYATA mini (format KUTIP-ASLI/GANTI-JADI) dikirim dua kali:
  A = pola app hari ini      (tanpa parameter)          → LAMA
  B = dengan enable_thinking:false                       → BARU

Lolos/tidaknya dinilai oleh PEMERIKSA APP SUNGGUHAN `_valid()` +
`_urai_jawaban()` (bukan penilaian Wulan). Skor: durasi, token, lolos.
"""
import json, os, time, urllib.error, urllib.request

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

TUGAS = (
    'NASKAH:\n' + NASKAH +
    '\nKOMENTAR:\n'
    '[K1] Kalimat "memakai bantuan" terasa bertele-tele.\n'
    '[K2] Singkatkan kalimat populasinya.\n\n'
    'Balas HANYA dengan pasangan penanda:\n'
    '[K1-KUTIP-ASLI] <kalimat asli persis>\n'
    '[K1-GANTI-JADI] <penggantinya>\n'
    '[K2-KUTIP-ASLI] <kalimat asli persis>\n'
    '[K2-GANTI-JADI] <penggantinya>'
)


def kirim(tag, tambahan, max_tok=6000, timeout=300):
    p = {'model': 'glm-5.3-flash', 'max_tokens': max_tok, 'temperature': 0.2,
         'messages': [{'role': 'system', 'content': SYSTEM_REVISI},
                      {'role': 'user', 'content': TUGAS}]}
    p.update(tambahan)
    req = urllib.request.Request(
        URL, data=json.dumps(p).encode(), method='POST',
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            teks = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        out = {'tag': tag, 'ok': False, 'galat': e.read().decode('utf-8', 'ignore')[:300]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out, ''
    except Exception as e:                                   # noqa: BLE001
        out = {'tag': tag, 'ok': False, 'galat': type(e).__name__ + ': ' + str(e)[:200]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out, ''
    dt = time.monotonic() - t0
    #  nilai pakai pemeriksa app SUNGGUHAN
    try:
        konten, info = _urai_jawaban(teks, 'glm-5.3-flash')
        lolos, alasan = True, 'LOLOS _valid'
    except Exception as e:                                   # noqa: BLE001
        konten, info, lolos, alasan = '', {}, False, 'DITOLAK: ' + str(e)[:220]
    out = {'tag': tag, 'ok': True, 'dt': round(dt, 1),
           'finish': info.get('finish'), 'lolos': lolos, 'alasan': alasan,
           'panjang': len(konten),
           'token_in': info.get('token_in'), 'token_out': info.get('token_out'),
           'isi': konten[:400]}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return out, konten


hasil = {}
print('A — pola app LAMA (tanpa parameter)', flush=True)
hasil['lama'], isi_lama = kirim('A-lama', {})
time.sleep(2)
print('B — OPSI 1 (enable_thinking: false)', flush=True)
hasil['baru'], isi_baru = kirim('B-baru', {'enable_thinking': False})

#  kualitas: apakah KUTIP-ASLI di dalamnya benar-benar ada di naskah?
def mutu(teks):
    kena = 0
    for blok in teks.split('['):
        if 'KUTIP-ASLI]' in blok:
            kalimat = blok.split('KUTIP-ASLI]', 1)[1].strip().strip(':').strip()
            kalimat = kalimat.split('\n')[0].strip()
            if kalimat and kalimat in NASKAH:
                kena += 1
    return kena


hasil['mutu'] = {'kutip_sesuai_naskah_lama': mutu(isi_lama),
                 'kutip_sesuai_naskah_baru': mutu(isi_baru)}
print('MUTU (kutip asli cocok dgn naskah):', json.dumps(hasil['mutu']),
      flush=True)

with open('/tmp/uji_ab_th.json', 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)
print('arsip: /tmp/uji_ab_th.json', flush=True)
