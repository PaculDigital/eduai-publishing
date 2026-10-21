#!/usr/bin/env python3
"""PROBE RUTE GATEWAY `EduAi` di 9router — apa model di baliknya + fallback.

Bos (13Sep26): "Llm 9router Model: EduAi — pertahankan jalur khusus".
Tes: (1) panggil model `EduAi` langsung, (2) lihat respons apakah menyebut
model & fallback, (3) tes skenario revisi mini 2x utk konsistensi model.
"""
import json
import re
import time
import urllib.request

BASE = 'http://172.17.0.1:20128/v1'
KEY = 'sk-dc042321c94f2e3e-0x5kj6-d8b38a02'  # key khusus EduAi (Bos)


def chat(model, pesan, max_tokens=4000):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': pesan}],
        'max_tokens': max_tokens,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode()
    detik = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    konten = j['choices'][0]['message']['content']
    return konten, raw, j, detik


# ── Tes 1: panggil gateway EduAi, lihat metadata model ──────────────────
print('═══ TES 1: model gateway `EduAi` (2x utk konsistensi) ═══')
for n in (1, 2):
    try:
        konten, raw, j, detik = chat('EduAi', 'Balas SATU kata: PONG')
        m = re.search(r'"model":\s*"([^"]+)"', raw)
        print(f'run {n}: {detik:.1f}s  jawab={konten[:40]!r}  '
              f'model-respons={m.group(1) if m else "?"}')
    except Exception as e:
        print(f'run {n}: GAGAL {type(e).__name__}: {e}')

# ── Tes 2: skenario revisi mini (guardrail nyata) ───────────────────────
print()
print('═══ TES 2: revisi mini via gateway EduAi ═══')
naskah = ('BAB III METODE PENELITIAN\nPenelitian ini menggunakan pendekatan '
          'kuantitatif dengan desain survei. Populasi 180 siswa, sampel 120 siswa, '
          '75 perempuan dan 45 laki-laki.')
komentar = 'Perbaiki kata "praktek" menjadi baku.'
pesan = (f'NASKAH:\n{naskah}\n\nKOMENTAR DOSEN:\n1. {komentar}\n\n'
         'Balas format: [K1] kalimat revisi')
try:
    konten, raw, j, detik = chat('EduAi', pesan)
    m = re.search(r'"model":\s*"([^"]+)"', raw)
    print(f'{detik:.1f}s  model-respons={m.group(1) if m else "?"}')
    print(f'jawab: {konten[:300]}')
except Exception as e:
    print(f'GAGAL {type(e).__name__}: {e}')
