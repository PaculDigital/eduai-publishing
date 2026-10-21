#!/usr/bin/env python3
"""BENCHMARK model inferhub — revisi teks akademik Indonesia (parser BENAR).

Dipakai benchmark resmi. Semua respons inferhub formatnya:
    {JSON objek}data: [DONE]\n
Parse: JSONDecoder().raw_decode() di teks setelah buang 'data: [DONE]'.

Ujian:
  K1: perbaiki 1 kalimat PUEBI (10 kesalahan disengaja)
  K2: komentar dosen gaya singkat → jadi instruksi revisi
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


def tanya(model, pesan, max_tokens=2000, timeout=300):
    """Return (content, detik, error). Format {JSON}data:[DONE] ditangani."""
    t0 = time.time()
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': max_tokens}).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers=HDR, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
    except Exception as e:
        return None, round(time.time() - t0, 1), f'{type(e).__name__}: {str(e)[:100]}'
    s = raw.strip()
    if s.endswith('data: [DONE]'):
        s = s[:-len('data: [DONE]')].strip()
    try:
        d, _ = json.JSONDecoder().raw_decode(s)
        c = d['choices'][0]
        msg = c.get('message') or {}
        isi = msg.get('content') or ''
        if not isi and c.get('finish_reason') == 'length':
            return None, round(time.time() - t0, 1), 'token habis (reasoning makan semua)'
        return (isi or '').strip(), round(time.time() - t0, 1), None
    except Exception as e:
        return None, round(time.time() - t0, 1), f'parse: {str(e)[:80]}'


# ── K1: 10 kesalahan PUEBI disengaja ────────────────────────────────────
KALIMAT_K1 = ('Penelitian ini bertujuan untuk menganalisa pengaruh media sosial '
              'terhadap prestasi belajar siswa. Sampel diambil secara acak, '
              'respon yang diperoleh diolah menggunakan teknik analisa data. '
              'Hasil penelitian menunjukkan bahwa variable independen berpengaruh '
              'signifikan terhadap variable dependen, hal tersebut dapat dilihat '
              'dari nilai signifikansi yang lebih kecil dari 0,05.')

KANDA_K1 = {  # kata salah → baku
    'menganalisa': 'menganalisis', 'respon': 'responsi' if False else 'responsi',
    'analisa': 'analisis', 'variable': 'variabel',
}

PESAN_K1 = ('Anda editor akademik. Perbaiki paragraf tesis berikut sesuai PUEBI. '
            'Ganti kata tidak baku menjadi baku. Balas HANYA paragraf hasil:\n\n'
            + KALIMAT_K1)

# ── K2: komentar dosen singkat → revisi ─────────────────────────────────
PESAN_K2 = ('Komentar dosen pembimbing: "Bab ini ngaco banget, methodologi '
            'kamu nggak jelas, pake analisa apa nggak disebut, sampaikan juga '
            'alasan pilih metode itu."\n\n'
            'Paragraf asli mahasiswa:\n'
            '"Data yang sudah terkumpul kemudian diolah. Setelah itu hasilnya '
            'ditampilkan dalam bentuk tabel."\n\n'
            'Tugas Anda: tuliskan ulang paragraf tersebut agar menjawab '
            'keberatan dosen (metode jelas + alasan). Maksimal 3 kalimat. '
            'Balas HANYA paragraf hasil.')

MODEL = ['inferhub/cb/deepseek-v4.1-flash',
         'inferhub/ali/qwen3.8-max',
         'inferhub/ag/gemini-3.8-flash-high',
         'inferhub/ali/glm-5.2',
         'inferhub/ag/claude-sonnet-4-6',
         'inferhub/ali/kimi-k3']

print('═' * 76)
print('K1 — Perbaikan PUEBI (4 kata tak baku disengaja)')
print('═' * 76)
skor = {}
for mo in MODEL:
    jawab, dt, err = tanya(mo, PESAN_K1)
    if err:
        print(f'{mo:<38} ERR {err}')
        skor[mo] = 0
        continue
    benar = sum(1 for salah in KANDA_K1
                if salah not in jawab.lower() and KANDA_K1[salah].lower() not in salah
                and salah not in jawab.lower())
    n_bersih = sum(1 for salah in KANDA_K1 if salah not in jawab.lower())
    utuh = len(jawab) > 100
    print(f'{mo:<38} t={dt:>4}s bersih={n_bersih}/4 utuh={utuh}')
    skor[mo] = n_bersih + (2 if utuh else 0)
    print(f'  ↳ {jawab[:150]}')

print()
print('═' * 76)
print('K2 — Komentar dosen singkat → revisi paragraf')
print('═' * 76)
for mo in MODEL:
    jawab, dt, err = tanya(mo, PESAN_K2)
    if err:
        print(f'{mo:<38} ERR {err}')
        continue
    kunci = ['analisis', 'alasan', 'metode']
    ada = sum(1 for k in kunci if k in jawab.lower())
    print(f'{mo:<38} t={dt:>4}s kunci={ada}/3')
    print(f'  ↳ {jawab[:200]}')

print()
print('═' * 76)
print('RINGKASAN K1 (skor maks 6):', json.dumps(skor, indent=1))
