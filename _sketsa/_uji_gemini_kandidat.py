"""UJI KANDIDAT MODEL GEMINI - LANGSUNG ke InferHub.
Tujuan: cari model Gemini mana yang PALING SESUAI untuk EduAi (revisi naskah).
Kriteria: (1) menghasilkan jawaban (tidak kosong), (2) cepat, (3) stabil.
Semua diuji dengan max_tokens=8000 (seperti produksi EduAi).
"""
import json
import time
import urllib.error
import urllib.request
from difflib import SequenceMatcher

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
BASE = 'https://api.inferhub.dev/v1'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

# Prompt meniru tugas nyata EduAi: revisi ejaan + gaya akademik.
PESAN = ("Perbaiki ejaan dan tata bahasa paragraf akademik berikut, "
         "jangan ubah makna. Kembalikan HANYA paragraf hasil perbaikan.\n\n"
         "Penelitian ini bertujuan untuk menganalisis pengaruh kualitas kehidupan "
         "kerja terhadap kinerja adaptif pegawai. Kesiapan digital dipakai sebagai "
         "variabel mediasi. Data dikumpulkan memakai kuesioner lima skala likert "
         "yang telah diuji validitas dan reliabilitasnya.")


def panggil(model, max_tokens=8000, temperature=0.0, timeout=300):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': PESAN}],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json',
                 'User-Agent': UA})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode("utf-8", "ignore")[:120]}'
    except Exception as e:
        return None, f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0

    i = raw.find('data: [DONE]')
    body2 = raw[:i] if i > 0 else raw
    try:
        j = json.JSONDecoder().raw_decode(body2)[0]
    except Exception as e:
        return None, f'PARSE ERROR {e}'
    u = j.get('usage') or {}
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return {
        'detik': d,
        'model': j.get('model'),
        'teks': c,
        'panjang': len(c),
        'reasoning': (u.get('completion_tokens_details') or {}).get(
            'reasoning_tokens', 0),
        'completion': u.get('completion_tokens'),
        'finish': ch.get('finish_reason'),
    }, None


# Semua kandidat gemini "teks" (bukan image) dari list /v1/models
KANDIDAT = [
    'ag/gemini-3.8-flash-high',
    'ag/gemini-3.7-flash-high',
    'ag/gemini-3.6-flash-high',
    'ag/gemini-pro-agent',
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-3.1-pro',
    'gemini-3.1-pro-high',
    'cb/gemini-3.1-pro',
    'gemini-omni-flash',
]

print('=' * 104)
print('UJI KANDIDAT MODEL GEMINI (langsung InferHub, max_tokens=8000, temperature=0)')
print('=' * 104)

ringkas = []
for m in KANDIDAT:
    print(f'\n>>> {m}')
    hasil = []
    for ulang in (1, 2):
        h, err = panggil(m)
        if err:
            print(f'    #{ulang}: {err}')
            continue
        print(f"    #{ulang}: {h['detik']:6.1f}s | len={h['panjang']:5d} | "
              f"reasoning={h['reasoning']:5d} | finish={h['finish']}")
        if h['panjang'] > 0:
            hasil.append(h)
    if len(hasil) == 2:
        mirip = SequenceMatcher(None, hasil[0]['teks'], hasil[1]['teks']).ratio()
        rata = sum(x['detik'] for x in hasil) / 2
        ringkas.append({
            'model': m,
            'ok': True,
            'detik': rata,
            'panjang': sum(x['panjang'] for x in hasil) // 2,
            'mirip': mirip,
        })
        print(f'    kemiripan 2 putaran: {mirip:.3f} | rata-rata {rata:.1f}s')
        print(f"    contoh: {hasil[0]['teks'][:150]!r}")
    elif len(hasil) == 1:
        ringkas.append({'model': m, 'ok': False, 'detik': hasil[0]['detik'],
                        'panjang': hasil[0]['panjang'], 'mirip': 0.0})
        print('    ⚠️ hanya 1 dari 2 berhasil')
    else:
        ringkas.append({'model': m, 'ok': False, 'detik': 0, 'panjang': 0,
                        'mirip': 0.0})
        print('    ❌ TIDAK menghasilkan jawaban')

print('\n' + '=' * 104)
print('RINGKASAN — DIURUTKAN (yang menjawab 2/2, lalu tercepat)')
print('=' * 104)
print(f"{'model':32s} {'2/2':4s} {'rata2':>7s} {'len':>6s} {'mirip':>6s}")
for r in sorted(ringkas, key=lambda x: (not x['ok'], x['detik'])):
    print(f"{r['model']:32s} {('YA' if r['ok'] else 'TIDAK'):4s} "
          f"{r['detik']:6.1f}s {r['panjang']:6d} {r['mirip']:6.3f}")
