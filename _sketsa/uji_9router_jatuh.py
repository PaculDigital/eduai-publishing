"""A. UJI 9ROUTER — kenapa jalur 1 LAMBAT 180 dtk / gagal → jatuh jalur 2.

Panggil combo `EduAi` lewat payload YANG PERSIS sama dengan app
(_panggil_9router): SYSTEM_REVISI + naskah 55rb kar, max_tokens=32000,
temperature 0.2. Ukur durasi + model yang benar-benar dipakai 9router.

Dijalankan: docker exec -i -w /app eduai-app python3 - < skrip ini
"""
import json, os, time, urllib.error, urllib.request

BASE = os.environ.get('EDUAI_ROUTER_BASE', 'http://9router:20128/v1')
KEY = os.environ.get('EDUAI_ROUTER_KEY', '')
MODEL = os.environ.get('EDUAI_AI_MODEL', 'EduAi')
MAXTOK = int(os.environ.get('EDUAI_AI_MAX_TOKENS', '32000'))
URL = BASE.rstrip('/') + '/chat/completions'

import sys
sys.path.insert(0, '.')
from app.ai import SYSTEM_REVISI  # noqa: E402

KATA = ('metode regresi berganda bertujuan menguji pengaruh variabel '
        'independen terhadap dependen sekaligus mengendalikan variabel '
        'lainnya dalam kerangka model penelitian yang telah ditetapkan. ').split()
par, n = [], 0
while sum(len(p) for p in par) < 55000:
    par.append(' '.join(KATA[(n * 7 + i) % len(KATA)]
                        for i in range(60, 130)) + '\n\n')
    n += 1
NAASKAH = ''.join(par)


def panggil(tag, system, tugas, timeout=420):
    payload = {
        'model': MODEL,
        'messages': [{'role': 'system', 'content': system},
                     {'role': 'user', 'content': tugas}],
        'max_tokens': MAXTOK, 'temperature': 0.2,
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(), method='POST',
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            mentah = r.read().decode('utf-8', 'ignore')
        #  9router membalas bentuk STREAM: {json}data: [DONE]
        #  (jejak _sketsa/intip_balasan_9r.py) → ambil segmen JSON pertama
        import json as _json
        j, _ = _json.JSONDecoder().raw_decode(mentah.lstrip())
    except urllib.error.HTTPError as e:
        out = {'tag': tag, 'ok': False, 'status': e.code,
               'galat': e.read().decode('utf-8', 'ignore')[:400]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out
    except Exception as e:                                   # noqa: BLE001
        out = {'tag': tag, 'ok': False, 'status': 0,
               'galat': type(e).__name__ + ': ' + str(e)[:300]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out
    dt = time.monotonic() - t0
    ch = (j.get('choices') or [{}])[0]
    pesan = ch.get('message') or {}
    u = j.get('usage') or {}
    isi = pesan.get('content') or ''
    out = {'tag': tag, 'ok': True, 'dt': round(dt, 1),
           'model_balik': j.get('model'),
           'finish': ch.get('finish_reason'),
           'panjang_content': len(isi),
           'reasoning': len(pesan.get('reasoning_content') or ''),
           'prompt_tok': u.get('prompt_tokens'),
           'compl_tok': u.get('completion_tokens')}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return out


hasil = {}

# ── A1: pola PERSIS app (55rb kar + SYSTEM_REVISI) ──────────────────
print('A1 — combo EduAi, pola persis app (naskah 55rb kar)', flush=True)
tugas = ('NASKAH:\n' + NAASKAH +
         '\n\nADA 1 KOMENTAR PEMBIMBING:\n'
         '[K1] Kalimat pembuka paragraf 1 terlalu umum.\n\n'
         'Balas HANYA dengan:\n[K1-KUTIP-ASLI] <kalimat asli>\n'
         '[K1-GANTI-JADI] <kalimat perbaikan>')
hasil['a1'] = panggil('A1-pola-app', SYSTEM_REVISI, tugas, timeout=420)
time.sleep(2)

# ── A2: ringkas (tanpa naskah besar) — biar ketahuan modelnya sehat ──
print('A2 — combo EduAi, tugas ringkas (cek model aktif)', flush=True)
hasil['a2'] = panggil('A2-ringkas', SYSTEM_REVISI,
                      'Balas satu kata: siap', timeout=120)

# ── A3: ulang A1 — konsistensi / antrean ────────────────────────────
time.sleep(2)
print('A3 — ulang A1 (uji konsistensi)', flush=True)
hasil['a3'] = panggil('A3-ulang', SYSTEM_REVISI, tugas, timeout=420)

with open('/tmp/uji_9router.json', 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)
print('\narsip: /tmp/uji_9router.json', flush=True)
