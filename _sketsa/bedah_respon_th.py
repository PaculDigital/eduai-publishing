"""Bedah struktur respon MENTAH tokenharbor — kenapa `keluar_kar=0`?

Dua panggilan berat (55rb kar, max_tokens 4000) tiap model, simpan
STRUKTUR responsnya: kunci `message`, ada `reasoning_content`?, isi
`content` berapa, `finish_reason`, dan rincian `usage` (reasoning tokens).
Itu yang menjelaskan 'output invalid (blok komentar kosong)' di M2.
"""
import json
import time
import urllib.request

BASIS = KEY = ''
for _b in open('.env'):
    if _b.startswith('EDUAI_FALLBACK_BASE='):
        BASIS = _b.split('=', 1)[1].strip().strip('"').strip("'")
    elif _b.startswith('EDUAI_FALLBACK_KEY='):
        KEY = _b.split('=', 1)[1].strip().strip('"').strip("'")
URL = BASIS.rstrip('/') + '/chat/completions'

KATA = ('metode regresi berganda bertujuan menguji pengaruh variabel '
        'independen terhadap dependen sekaligus mengendalikan variabel '
        'lainnya dalam kerangka model penelitian yang telah ditetapkan. ').split()
par, n = [], 0
while sum(len(p) for p in par) < 55000:
    par.append(' '.join(KATA[(n * 7 + i) % len(KATA)]
                        for i in range(60, 130)) + '\n\n')
    n += 1
NAASKAH = ''.join(par)
TUGAS = ('NASKAH:\n' + NAASKAH +
         '\n\nTUGAS: Perbaiki tata bahasa dan ejaan seluruh naskah. '
         'Kembalikan naskah lengkap yang sudah diperbaiki.')


def bedah(model, max_tok):
    badan = json.dumps({'model': model,
                        'messages': [{'role': 'user', 'content': TUGAS}],
                        'max_tokens': max_tok, 'temperature': 0.2}).encode()
    req = urllib.request.Request(
        URL, data=badan, method='POST',
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=600) as r:
        mentah = r.read().decode('utf-8', 'ignore')
    dt = time.monotonic() - t0
    j = json.loads(mentah)
    pesan = j['choices'][0].get('message') or {}
    isi = pesan.get('content') or ''
    bingkas = {
        'model': model, 'max_tokens': max_tok, 'dt': round(dt, 1),
        'kunci_message': sorted(pesan.keys()),
        'finish': j['choices'][0].get('finish_reason'),
        'panjang_content': len(isi),
        'ada_reasoning_content': 'reasoning_content' in pesan,
        'panjang_reasoning': len(pesan.get('reasoning_content') or ''),
        'usage': j.get('usage'),
        'isi_awal_content': isi[:200].replace('\n', ' '),
        'isi_akhir_content': isi[-200:].replace('\n', ' '),
    }
    print(json.dumps(bingkas, ensure_ascii=False, indent=1), flush=True)
    return bingkas


keluar = {}
for model in ('glm-5.3-flash', 'deepseek-v4.1-flash'):
    print('=' * 60, flush=True)
    keluar[model] = bedah(model, 4000)
    time.sleep(2)

with open('_arsip/bedah_respon_th_28sep.json', 'w') as fh:
    json.dump(keluar, fh, ensure_ascii=False, indent=1)
print('arsip: _arsip/bedah_respon_th_28sep.json')
