#!/usr/bin/env python3
"""PROBE JALUR EDUAI DI 9ROUTER — key khusus (ACC Bos opsi 2, 13Sep26).

Tugas: cek lewat key EduAi ada berapa model + tes 1 panggilan nyata.
Key TIDAK di-print ke output.
"""
import json
import re
import sys
import urllib.request

BASE = 'http://172.17.0.1:20128/v1'

# Key khusus EduAi (diberikan Bos langsung di chat, 13Sep26)
KEY_EDUAI = 'sk-dc042321c94f2e3e-0x5kj6-d8b38a02'

# Key utama Hermes (dari config.yaml) — hanya untuk perbandingan jumlah model
_t = open('/opt/data/config.yaml').read()
_m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*'
               r'(http://172\.17\.0\.1:20128/v1)', _t)
KEY_HERMES = _m.group(1).strip('\'"')


def models(key):
    req = urllib.request.Request(
        f'{BASE}/models',
        headers={'Authorization': f'Bearer {key}'},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def chat(key, model, pesan):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': pesan}],
        'max_tokens': 4000,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {key}',
                 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode()
    i = raw.find('data: [DONE]')
    j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    return j['choices'][0]['message']['content']


# ── 1. Daftar model jalur EduAi vs jalur Hermes ─────────────────────────
ed = models(KEY_EDUAI)
hermes = models(KEY_HERMES)
m_ed = sorted(x['id'] for x in ed['data'])
m_he = sorted(x['id'] for x in hermes['data'])
print(f'Model lewat key EduAi  : {len(m_ed)}')
print(f'Model lewat key Hermes : {len(m_he)}')
print()
print('=== DAFTAR MODEL JALUR EDUAI ===')
for m in m_ed:
    tanda = '' if m in m_he else '  ← BARU/di luar jalur Hermes'
    print(f'  {m}{tanda}')
print()

# ── 2. Tes 1 panggilan nyata lewat jalur EduAi ─────────────────────────
kandidat = [m for m in m_ed if 'gemini' in m.lower()] or m_ed[:1]
tes = kandidat[0]
print(f'=== TES PANGGILAN via jalur EduAi: {tes} ===')
try:
    jawab = chat(KEY_EDUAI, tes,
                 'Balas dengan SATU kata saja: PONG')
    print(f'jawab: {jawab[:80]!r}')
    print('STATUS: JALUR EDUAI JALAN ✅')
except Exception as e:
    print(f'GAGAL: {type(e).__name__}: {e}')
    sys.exit(1)
