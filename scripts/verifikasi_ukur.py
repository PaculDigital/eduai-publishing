#!/usr/bin/env python3
"""VERIFIKASI — cek 2 kecurigaan bug pengukuran (bukan bug model):

1. K1 'respon' → substring bug: 'respons' mengandung 'respon'.
   Cek benar: regex word-boundary \\brespon\\b (tanpa 's') vs \\brespons\\b.
2. K2 'alasan' → jawaban model pakai kata 'karena' (alasan = because).
   Cek benar: hadirnya 'karena' ATAU 'alasan' ATAU 'pertimbangan'.
"""
import json
import re
import time
import urllib.request

teks = open('/opt/data/config.yaml').read()
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}


def tanya(model, pesan, max_tokens=4000, timeout=300):
    t0 = time.time()
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': max_tokens}).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers=HDR, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
    s = raw.strip()
    if s.endswith('data: [DONE]'):
        s = s[:-len('data: [DONE]')].strip()
    d, _ = json.JSONDecoder().raw_decode(s)
    return (d['choices'][0]['message'].get('content') or '').strip(), \
        round(time.time() - t0, 1)


KALIMAT_K1 = ('Penelitian ini bertujuan untuk menganalisa pengaruh media sosial '
              'terhadap prestasi belajar siswa. Sampel diambil secara acak, '
              'respon yang diperoleh diolah menggunakan teknik analisa data. '
              'Hasil penelitian menunjukkan bahwa variable independen berpengaruh '
              'signifikan terhadap variable dependen, hal tersebut dapat dilihat '
              'dari nilai signifikansi yang lebih kecil dari 0,05.')
PESAN_K1 = ('Anda editor akademik. Perbaiki paragraf tesis berikut sesuai PUEBI. '
            'Ganti kata tidak baku menjadi baku. Balas HANYA paragraf hasil:\n\n'
            + KALIMAT_K1)

PESAN_K2 = ('Komentar dosen pembimbing: "Bab ini ngaco banget, methodologi '
            'kamu nggak jelas, pake analisa apa nggak disebut, sampaikan juga '
            'alasan pilih metode itu."\n\n'
            'Paragraf asli mahasiswa:\n'
            '"Data yang sudah terkumpul kemudian diolah. Setelah itu hasilnya '
            'ditampilkan dalam bentuk tabel."\n\n'
            'Tugas Anda: tuliskan ulang paragraf tersebut agar menjawab '
            'keberatan dosen. Maksimal 3 kalimat. Balas HANYA paragraf hasil.')

print('── K1 verifikasi word-boundary (2 model tercepat) ──')
for mo in ['inferhub/ag/claude-sonnet-4-6', 'inferhub/cb/deepseek-v4.1-flash']:
    jawab, dt = tanya(mo, PESAN_K1)
    cek = {
        'menganalisa hilang': not re.search(r'\bmenganalisa\b', jawab, re.I),
        'analisa hilang': not re.search(r'\banalisa\b', jawab, re.I),
        'variable→variabel': not re.search(r'\bvariable\b', jawab, re.I),
        'respon→respons (WB)': not re.search(r'\brespon\b(?!s)', jawab, re.I),
        'respons benar ada': bool(re.search(r'\brespons\b', jawab, re.I)),
    }
    print(f'\n{mo} ({dt}s)')
    for k, v in cek.items():
        print(f'   {"✓" if v else "✗"} {k}')
    print('   jawab:', jawab[:200])

print()
print('── K2 verifikasi kata alasan ──')
for mo in ['inferhub/ag/claude-sonnet-4-6', 'inferhub/ali/qwen3.8-max']:
    jawab, dt = tanya(mo, PESAN_K2)
    ada_alasan = any(w in jawab.lower() for w in ('alasan', 'karena', 'pertimbangan'))
    print(f'{mo} ({dt}s) alasan/karena ada: {ada_alasan}')
    print('   jawab:', jawab[:250])
