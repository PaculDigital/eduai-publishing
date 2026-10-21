"""Uji PENUTUP tokenharbor — 3 pertanyaan app:

U1. Apakah `max_tokens` dihormati? (anomali: minta 4000 → usage 8000)
U2. Bisakah REASONING dimatikan? (akar 'output invalid' = reasoning memakan
    jatah → content kosong/pendek). Coba 4 gaya param yang umum.
U3. Uji PERSIS seperti app: SYSTEM_REVISI + naskah 55rb kar +
    max_tokens=32000 (AI_MAX_TOKENS) → selesai utuh atau terpotong?
"""
import json
import os
import time
import urllib.error
import urllib.request

# Di container: kunci datang dari env (docker run --env-file) — BUKAN berkas.
# Di host: fallback ke .env. Tidak pernah dicetak.
BASIS = os.environ.get('EDUAI_FALLBACK_BASE', '')
KEY = os.environ.get('EDUAI_FALLBACK_KEY', '')
if not BASIS:
    for _b in open(os.environ.get('ENV_BERKAS', '.env')):
        if _b.startswith('EDUAI_FALLBACK_BASE='):
            BASIS = _b.split('=', 1)[1].strip().strip('"').strip("'")
        elif _b.startswith('EDUAI_FALLBACK_KEY='):
            KEY = _b.split('=', 1)[1].strip().strip('"').strip("'")
assert BASIS and KEY, 'BASE/KEY tidak ditemukan'
URL = BASIS.rstrip('/') + '/chat/completions'

# SYSTEM_REVISI asli dari app (dibaca dari sumber, jangan diketik ulang)
# Harus dijalankan DI DALAM container (httpx ada di sana).
import sys
sys.path.insert(0, '.')
from app.ai import SYSTEM_REVISI                        # noqa: E402
from app.config import AI_MAX_TOKENS                    # noqa: E402
print(f'AI_MAX_TOKENS app = {AI_MAX_TOKENS} · SYSTEM_REVISI = '
      f'{len(SYSTEM_REVISI)} kar', flush=True)

KATA = ('metode regresi berganda bertujuan menguji pengaruh variabel '
        'independen terhadap dependen sekaligus mengendalikan variabel '
        'lainnya dalam kerangka model penelitian yang telah ditetapkan. ').split()
par, n = [], 0
while sum(len(p) for p in par) < 55000:
    par.append(' '.join(KATA[(n * 7 + i) % len(KATA)]
                        for i in range(60, 130)) + '\n\n')
    n += 1
NAASKAH = ''.join(par)


def kirim(tag, payload, timeout=600):
    badan = json.dumps(payload).encode()
    req = urllib.request.Request(
        URL, data=badan, method='POST',
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode('utf-8', 'ignore') or '{}')
    except urllib.error.HTTPError as e:
        out = {'tag': tag, 'ok': False, 'status': e.code,
               'galat': e.read().decode('utf-8', 'ignore')[:300]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out
    except Exception as e:                                  # noqa: BLE001
        out = {'tag': tag, 'ok': False, 'status': 0,
               'galat': type(e).__name__ + ': ' + str(e)[:200]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out
    dt = time.monotonic() - t0
    ch = (j.get('choices') or [{}])[0]
    pesan = ch.get('message') or {}
    u = j.get('usage') or {}
    isi = pesan.get('content') or ''
    out = {'tag': tag, 'ok': True, 'dt': round(dt, 1),
           'finish': ch.get('finish_reason'),
           'kunci': sorted(pesan.keys()),
           'panjang_content': len(isi),
           'ada_reasoning': 'reasoning_content' in pesan,
           'panjang_reasoning': len(pesan.get('reasoning_content') or ''),
           'prompt_tok': u.get('prompt_tokens'),
           'compl_tok': u.get('completion_tokens'),
           'detil': u.get('completion_tokens_details')}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return out


hasil = {}

# ── U1: apakah max_tokens dihormati? ────────────────────────────────────
print('\nU1 — max_tokens=500, tugas kecil', flush=True)
hasil['u1'] = kirim('U1-max500', {
    'model': 'glm-5.3-flash', 'max_tokens': 500, 'temperature': 0.2,
    'messages': [{'role': 'user', 'content': 'Tulis 3 kalimat saran '
                  'perbaikan paragraf: "Penelitian ini bertujuan untuk '
                  'menguji pengaruh harga terhadap pembelian."'}]})

# ── U2: bisakah reasoning dimatikan? ────────────────────────────────────
PESAN2 = [{'role': 'user', 'content': 'Tulis 2 kalimat saran perbaikan '
           'tata bahasa paragraf berikut: "Penelitian ini bertujuan untuk '
           'menguji pengaruh harga terhadap pembelian dengan sampel 100."'}]
print('\nU2 — coba 4 gaya mematikan reasoning (glm-5.3-flash)', flush=True)
for gaya, tambahan in (
        ('A enable_thinking:false', {'enable_thinking': False}),
        ('B chat_template_kwargs', {'chat_template_kwargs':
                                     {'enable_thinking': False}}),
        ('C reasoning.effort:none', {'reasoning': {'effort': 'none'}}),
        ('D reasoning_effort:min', {'reasoning_effort': 'minimal'})):
    p = {'model': 'glm-5.3-flash', 'max_tokens': 1500, 'temperature': 0.2,
         'messages': PESAN2}
    p.update(tambahan)
    hasil['u2_' + gaya[0]] = kirim('U2-' + gaya[0], p)
    time.sleep(1)

# ── U3: uji PERSIS seperti app ─────────────────────────────────────────
print('\nU3 — pola persis app: SYSTEM_REVISI + 55rb kar + '
      f'max_tokens={AI_MAX_TOKENS}', flush=True)
TUGAS = ('NASKAH:\n' + NAASKAH +
         '\n\nTUGAS: Perbaiki tata bahasa dan ejaan seluruh naskah. '
         'Pertahankan isi dan struktur. Kembalikan naskah lengkap yang '
         'sudah diperbaiki tanpa memotong bagian mana pun.')
hasil['u3_glm'] = kirim('U3-glm-pola-app', {
    'model': 'glm-5.3-flash', 'max_tokens': AI_MAX_TOKENS,
    'temperature': 0.2,
    'messages': [{'role': 'system', 'content': SYSTEM_REVISI},
                 {'role': 'user', 'content': TUGAS}]})
time.sleep(2)
hasil['u3_deepseek'] = kirim('U3-deepseek-pola-app', {
    'model': 'deepseek-v4.1-flash', 'max_tokens': AI_MAX_TOKENS,
    'temperature': 0.2,
    'messages': [{'role': 'system', 'content': SYSTEM_REVISI},
                 {'role': 'user', 'content': TUGAS}]})

with open('/tmp/uji_penutup_th.json', 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)
print('\narsip: /tmp/uji_penutup_th.json')
