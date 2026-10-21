"""UJI APAKAH FALLBACK COMBO BEKERJA — jalur 9router produksi.

CARA UJI YANG JUJUR: kita TIDAK bisa mematikan model di InferHub.
Jadi kita uji 2 hal:

  A. BUKTI TIDAK LANGSUNG (observasi nyata):
     - panggil combo berkali-kali, CATAT model mana yang menjawab.
     - kalau pernah muncul model != slot-1 → fallback memang bekerja.
     - catat juga apakah ada jawaban KOSONG (tanda model reasoning kehabisan).

  B. BUKTI LANGSUNG (uji paksa):
     - panggil 9router DENGAN MODEL YANG DIMINTA = slot terakhir
       (cbcn/glm-5.3-flash, non-reasoning) → buktikan dia HIDUP.
     - panggil model yang kita tahu MATI (ag/gemini-3.8-flash-high)
       → buktikan dia memang mati, jadi alasan fallback itu nyata.

Hasilnya: kita tahu apakah anggota combo benar-benar hidup semua,
dan apakah kombinasi ini aman kalau slot depan tumbang.
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
KEY = os.getenv('EDUAI_ROUTER_KEY', '')

PESAN = ("Balas satu kalimat: apa itu hipotesis penelitian?")
HIDUP = ('balas satu kalimat: apa itu hipotesis penelitian?',
         'kesimpulan')


def panggil(model, max_tokens=8000, timeout=300, paksa=''):
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': PESAN + paksa}],
                       'max_tokens': max_tokens, 'temperature': 0.2}).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode("utf-8","ignore")[:130]}'
    except Exception as e:
        return None, f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    try:
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    except Exception as e:
        return None, f'PARSE {e}'
    u = j.get('usage') or {}
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return {'detik': d, 'model': j.get('model'), 'len': len(c),
            'reasoning': (u.get('completion_tokens_details') or {}).get(
                'reasoning_tokens', 0),
            'finish': ch.get('finish_reason'), 'teks': c}, None


print('=' * 100)
print('A. OBSERVASI — 8 panggilan combo EduAi, catat model yang menjawab')
print('=' * 100)
dipakai = {}
kosong = 0
for n in range(1, 9):
    r, err = panggil('EduAi')
    if err:
        print(f'  #{n}: ❌ {err}')
        continue
    dipakai[r['model']] = dipakai.get(r['model'], 0) + 1
    if r['len'] == 0:
        kosong += 1
    print(f"  #{n}: {r['detik']:6.1f}s | {r['model']:28s} | len={r['len']:4d} "
          f"| reason={r['reasoning']:5d} | {r['finish']}")
print(f'\n  Model yang terpakai: {dipakai}')
print(f'  Jawaban KOSONG     : {kosong}/8')
if len(dipakai) > 1:
    print('  ✅ FALLBACK TERBUKTI BEKERJA (lebih dari 1 model terpakai)')
else:
    print('  ℹ️ hanya 1 model terpakai (slot-1 sehat) — fallback belum terpicu')

print('\n' + '=' * 100)
print('B. UJI LANGSUNG TIAP ANGGOTA COMBO — buktikan mana yang HIDUP / MATI')
print('=' * 100)
ANGGOTA = [
    ('inferhub/ali/deepseek-v4.1-flash', 'slot 1 — utama'),
    ('inferhub/cbcn/deepseek-v4.1-flash', 'slot 2'),
    ('inferhub/ag/gemini-3.7-flash-high', 'slot 3 — pengganti 3.8'),
    ('inferhub/cbcn/deepseek-v4-flash', 'slot 4'),
    ('inferhub/cbcn/glm-5.3-flash', 'slot 5 — NON-REASONING (jaring pengaman)'),
    ('inferhub/ag/gemini-3.8-flash-high', 'yang DIBUANG — cek masih mati?'),
]
for m, ket in ANGGOTA:
    r, err = panggil(m, max_tokens=2000, timeout=120)
    if err:
        print(f'  ❌ {m:34s} [{ket}]')
        print(f'     {err}')
    else:
        tanda = '✅ HIDUP' if r['len'] > 0 else '⚠️ KOSONG'
        print(f"  {tanda} {m:34s} [{ket}]")
        print(f"     {r['detik']:5.1f}s | len={r['len']} | "
              f"reason={r['reasoning']} | {r['finish']}")
