"""UKUR BEBAN BERAT tokenharbor — pola PERSIS yang dipakai app EduAi.

App memotong naskah per 55.000 karakter (AI_POTONG_KARAKTER=55000) per
panggilan, minta output panjang (revisi paragraf), dan boleh 8 bersamaan
(EDUAI_AI_KONKUREN=8). Fase A-D tadi memakai prompt KECIL — ukuran di sini
memakai beban NYATA supaya ketahuan: berapa lama keluar, dan apakah tahan
bersamaan. Itu yang menentukan batas sabar app (jalur1 180 dtk / fb 240 dtk).
"""
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASIS = KEY = ''
for _b in open('.env'):
    if _b.startswith('EDUAI_FALLBACK_BASE='):
        BASIS = _b.split('=', 1)[1].strip().strip('"').strip("'")
    elif _b.startswith('EDUAI_FALLBACK_KEY='):
        KEY = _b.split('=', 1)[1].strip().strip('"').strip("'")
URL = BASIS.rstrip('/') + '/chat/completions'
MODEL = 'glm-5.3-flash'
MODEL2 = 'deepseek-v4.1-flash'
ARSIP = '_arsip/ukur_tokenharbor_berat_28sep.json'

#  naskah tiruan 55.000 karakter (paragraf bervariasi, bukan kalimat dobel
#  supaya mendekati naskah skripsi sungguhan)
KATA = ('metode regresi berganda bertujuan menguji pengaruh variabel '
        'independen terhadap dependen sekaligus mengendalikan variabel '
        'lainnya dalam kerangka model penelitian yang telah ditetapkan. ').split()
awal = time.time()
par = []
n = 0
while sum(len(p) for p in par) < 55000:
    par.append(' '.join(KATA[(n * 7 + i) % len(KATA)]
                        for i in range(60, 130)) + '\n\n')
    n += 1
NAASKAH = ''.join(par)
print(f'naskah tiruan: {len(NAASKAH):,} karakter (≈'
      f'{len(NAASKAH)//4:,} token masuk) — dibuat {time.time()-awal:.1f} dtk',
      flush=True)

TUGAS = ('NASKAH:\n' + NAASKAH +
         '\n\nTUGAS: Perbaiki tata bahasa dan ejaan seluruh naskah. '
         'Pertahankan isi, gaya penulisan ilmiah, dan struktur paragraf. '
         'Kembalikan naskah lengkap yang sudah diperbaiki.')
TUGAS2 = ('NASKAH:\n' + NAASKAH +
          '\n\nTUGAS: Rapikan kalimat yang terlalu panjang dan perbaiki '
          'ejaan. Kembalikan seluruh naskah hasil perbaikan tanpa '
          'memotong bagian mana pun.')


def kirim(model, isi, max_keluar=4000, timeout=600):
    badan = json.dumps({'model': model,
                        'messages': [{'role': 'user', 'content': isi}],
                        'max_tokens': max_keluar, 'temperature': 0.2}).encode()
    req = urllib.request.Request(
        URL, data=badan, method='POST',
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json',
                 'HTTP-Referer': 'https://eduai.bikinaja.id',
                 'X-Title': 'EduAi-ukur'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode('utf-8', 'ignore') or '{}')
        dt = time.monotonic() - t0
        u = j.get('usage') or {}
        try:
            teks = j['choices'][0]['message'].get('content') or ''
        except Exception:
            teks = ''
        return {'ok': True, 'dt': round(dt, 1), 'status': 200,
                'token_in': u.get('prompt_tokens'),
                'token_out': u.get('completion_tokens'),
                'keluar_kar': len(teks),
                'finish': (j.get('choices') or [{}])[0].get('finish_reason')}
    except urllib.error.HTTPError as e:
        return {'ok': False, 'dt': round(time.monotonic() - t0, 1),
                'status': e.code,
                'galat': e.read().decode('utf-8', 'ignore')[:300]}
    except Exception as e:                                  # noqa: BLE001
        return {'ok': False, 'dt': round(time.monotonic() - t0, 1),
                'status': 0, 'galat': type(e).__name__ + ': ' + str(e)[:200]}


hasil = {}
print('\nH1 — SATU panggilan berat (55rb kar masuk → output panjang):',
      flush=True)
r = kirim(MODEL, TUGAS, max_keluar=4000, timeout=600)
hasil['h1_tunggal'] = r
print(f'  {MODEL}: {r}', flush=True)

print('\nH2 — SATU panggilan berat model cadangan:', flush=True)
r2 = kirim(MODEL2, TUGAS2, max_keluar=4000, timeout=600)
hasil['h2_tunggal'] = r2
print(f'  {MODEL2}: {r2}', flush=True)

print('\nH3 — EMPAT berat BERSAMAAN (sampel dari 8 konkurensi app):',
      flush=True)
t0 = time.monotonic()
with ThreadPoolExecutor(max_workers=4) as pool:
    daftar = list(pool.map(lambda i: kirim(MODEL if i % 2 == 0 else MODEL2,
                                           TUGAS if i % 2 == 0 else TUGAS2,
                                           max_keluar=4000, timeout=600),
                           range(4)))
wall = time.monotonic() - t0
for i, x in enumerate(daftar):
    print(f'  [{i}] {x}', flush=True)
hasil['h3_empat_bersamaan'] = {'daftar': daftar,
                               'wall_clock': round(wall, 1)}
print(f'  → total {wall:.1f} dtk untuk 4 panggilan 55rb kar bersamaan',
      flush=True)

with open(ARSIP, 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)
print(f'\narsip: {ARSIP}')
