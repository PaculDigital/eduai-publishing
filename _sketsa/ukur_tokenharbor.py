"""UKUR NYATA tokenharbor.ai — kapasitas, latensi, jeda, konkurensi.

Dipakai Wulan untuk menjawab Bos: "kapasitas yang bisa diterima tokenharbor
dan jeda antar request, agar project ini berhasil dengan tokenharbor".

4 FASE (murah → mahal, berhenti sendiri kalau diblokir):
  A. JEDA ANTAR REQUEST — kirim berurutan dgn jeda 0 / 0,25 / 0,5 / 1 / 2 dtk
  B. KONKURENSI — 1 / 2 / 4 / 8 / 16 request BERSAMAAN
  C. LATENSI + THROUGHPUT — request kecil, lalu minta ~1.000 token keluar
  D. KAPASITAS KONTEKS — prompt besar → kalau DITOLAK, baca angka context
     limit dari pesan galat provider (hemat: tolak = gratis)

API key TIDAK PERNAH dicetak. Keluaran: tabel ringkas + JSON di _arsip/.
"""
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASIS = ''
KEY = ''
for _b in open('.env'):
    if _b.startswith('EDUAI_FALLBACK_BASE='):
        BASIS = _b.split('=', 1)[1].strip().strip('"').strip("'")
    elif _b.startswith('EDUAI_FALLBACK_KEY='):
        KEY = _b.split('=', 1)[1].strip().strip('"').strip("'")
if not BASIS or not KEY:
    raise SystemExit('BASE/KEY kosong di .env — berhenti')
URL = BASIS.rstrip('/') + '/chat/completions'
MODEL = 'glm-5.3-flash'
MODEL2 = 'deepseek-v4.1-flash'
ARSIP = '_arsip/ukur_tokenharbor_28sep.json'
HASIL = {'fase': {}, 'meta': {'url': BASIS, 'mulai': time.strftime('%H:%M:%S')}}


def kirim(model, isi, max_keluar=16, timeout=120, rujuk=''):
    """Satu request ChatCompletion → dict jujur (tanpa key)."""
    badan = json.dumps({'model': model, 'messages': [{'role': 'user',
                                                      'content': isi}],
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
        teks = ''
        try:
            teks = j['choices'][0]['message'].get('content') or ''
        except Exception:
            pass
        return {'ok': True, 'dt': round(dt, 2), 'status': 200,
                'keluar': len(teks), 'token_in': u.get('prompt_tokens'),
                'token_out': u.get('completion_tokens'), 'rujuk': rujuk}
    except urllib.error.HTTPError as e:
        dt = time.monotonic() - t0
        bad = e.read().decode('utf-8', 'ignore')[:400]
        return {'ok': False, 'dt': round(dt, 2), 'status': e.code,
                'galat': bad, 'rujuk': rujuk}
    except Exception as e:                                  # noqa: BLE001
        dt = time.monotonic() - t0
        return {'ok': False, 'dt': round(dt, 2), 'status': 0,
                'galat': type(e).__name__ + ': ' + str(e)[:200],
                'rujuk': rujuk}


def catat(fase, kunci, daftar):
    ok = [x for x in daftar if x['ok']]
    dtk = [x['dt'] for x in daftar]
    galat = sorted({str(x.get('status')) + ' ' + (x.get('galat') or '')[:60]
                    for x in daftar if not x['ok']})
    baris = (f'{len(ok)}/{len(daftar)} sukses · '
             f'latensi min/avg/max = {min(dtk):.1f}/{sum(dtk)/len(dtk):.1f}/'
             f'{max(dtk):.1f} dtk')
    if galat:
        baris += ' · GALAT: ' + ' || '.join(galat[:3])
    print(f'  [{fase}] {kunci}: {baris}', flush=True)
    HASIL['fase'].setdefault(fase, {})[kunci] = {'daftar': daftar,
                                                 'ringkas': baris}


print('=' * 66)
print(f'UKUR tokenharbor · model {MODEL} · {time.strftime("%H:%M:%S")}')
print('=' * 66)

# ── FASE A: JEDA ANTAR REQUEST ──────────────────────────────────────────
print('\nFASE A — JEDA ANTAR REQUEST (6 request berurutan tiap jeda)')
for jeda in (0.0, 0.25, 0.5, 1.0, 2.0):
    hasil = []
    for i in range(6):
        hasil.append(kirim(MODEL, f'Balas satu kata: siap {i}',
                           max_keluar=8, timeout=60, rujuk=f'jeda{jeda}'))
        if jeda:
            time.sleep(jeda)
    catat('A-jeda', f'jeda {jeda} dtk', hasil)
    if any(x['status'] == 429 for x in hasil):
        print('  ⛔ kena 429 → hentikan fase A (batas terkecil terlalu ketat)')
        break

# ── FASE B: KONKURENSI ─────────────────────────────────────────────────
print('\nFASE B — KONKURENSI (request BERSAMAAN)')
for n in (1, 2, 4, 8, 16):
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=n) as pool:
        hasil = list(pool.map(
            lambda i: kirim(MODEL, f'Balas satu kata: siap {i}',
                            max_keluar=8, timeout=90, rujuk=f'konk{n}'),
            range(n)))
    waktu = time.monotonic() - t0
    catat('B-konkuren', f'{n} bersamaan', hasil)
    print(f'         → total {waktu:.1f} dtk untuk {n} request', flush=True)
    if any(x['status'] == 429 for x in hasil):
        print('  ⛔ kena 429 → hentikan fase B')
        break
    time.sleep(2)

# ── FASE C: LATENSI + THROUGHPUT ────────────────────────────────────────
print('\nFASE C — LATENSI & KECEPATAN KELUAR')
print('  (C1) 5 request kecil', flush=True)
h = [kirim(MODEL, 'Balas satu kalimat: semangat belajar', max_keluar=32,
           timeout=90, rujuk='C1') for _ in range(5)]
catat('C-latensi', 'request kecil', h)

print('  (C2) minta ±1.000 token keluar (kecepatan)', flush=True)
h2 = [kirim(MODEL, 'Tulis penjelasan metode regresi berganda yang lengkap, '
            'minimal 900 kata, dalam bahasa Indonesia akademik.',
            max_keluar=1400, timeout=180, rujuk='C2')]
h2 += [kirim(MODEL2, 'Tulis penjelasan uji asumsi klasik yang lengkap, '
             'minimal 900 kata, dalam bahasa Indonesia akademik.',
             max_keluar=1400, timeout=180, rujuk='C2b')]
catat('C-throughput', 'mintai ±1.000 token keluar', h2)
for x in h2:
    if x['ok'] and x['dt']:
        laju = (x['keluar'] / 4) / x['dt']
        print(f"         → {x['rujuk']}: ~{x['keluar']} kar ≈ "
              f"{x['token_out'] or 0} token dalam {x['dt']} dtk "
              f"= {laju:.0f} token/detik", flush=True)

# ── FASE D: KAPASITAS KONTEKS ──────────────────────────────────────────
print('\nFASE D — KAPASITAS KONTEKS PER REQUEST (naik dari 64k token)')
#  1 token ≈ 4 karakter Indonesia-ish → 64k token ≈ 256rb karakter
for ribu in (64, 128, 256, 512):
    isi = ('Abstrak penelitian berikut. ' + 'kalimat uji ukur konteks. '
           * (ribu * 1000 // 24))
    print(f'  (D) ±{ribu}.000 token ({len(isi):,} karakter) …', flush=True)
    r = kirim(MODEL, isi, max_keluar=1, timeout=180, rujuk=f'D{ribu}')
    catat('D-konteks', f'±{ribu}k token', [r])
    if r['ok']:
        print(f'         ✅ DITERIMA ({ribu}k token)', flush=True)
        continue
    if r['status'] in (400, 413, 422):
        print(f'         ⛔ DITOLAK {r["status"]}: {r.get("galat","")[:220]}',
              flush=True)
        break
    print(f'         ? status {r["status"]} — coba ukuran berikut', flush=True)
    time.sleep(3)

HASIL['meta']['selesai'] = time.strftime('%H:%M:%S')
with open(ARSIP, 'w') as fh:
    json.dump(HASIL, fh, ensure_ascii=False, indent=1)
print('\n' + '=' * 66)
print(f'RINGKASAN AKHIR — arsip: {ARSIP}')
for fase, isi in HASIL['fase'].items():
    for kunci, v in isi.items():
        print(f'  {fase} · {kunci}: {v["ringkas"]}')
print('=' * 66)
