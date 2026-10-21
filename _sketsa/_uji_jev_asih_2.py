"""UJI JEV vs MESIN LAMA — naskah ASLI Asih (159.909 karakter).

Pertanyaan Bos: (1) Jev optimal? (2) andal, bukan kosmetik? (3) bisa
dipakai di fungsi lain?
"""
import json
import re
import sqlite3
import time
import urllib.error
import urllib.request

# kunci
c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
KEY = json.loads(dict(c.execute(
    "select data from providerConnections where provider='openrouter'").fetchone())['data'])['apiKey']

teks = open('/opt/data/services/eduai-publishing/_naskah_asih.txt', encoding='utf-8').read()
baris = [b.strip() for b in teks.split('\n') if b.strip()]
print(f'naskah: {len(teks)} karakter, {len(baris)} baris')

# ── MESIN LAMA: cari bab dengan regex yang sama dengan produksi
POLA = re.compile(r'^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5})[ \t]*(.*)$')
lama = []
for i, b in enumerate(baris):
    m = POLA.match(b)
    if m:
        lama.append((i, m.group(1).upper(), m.group(2)[:40]))
print(f'\n== MESIN LAMA (regex) menemukan {len(lama)} judul bab ==')
for i, nomor, judul in lama[:12]:
    print(f'   baris {i:5d}  BAB {nomor:5s}  {judul}')

# ── SUSUN STATE untuk Jev: judul bab + sekeliling (isi tiap bab ringkas)
def ringkas_bab(maks_per_bab=600):
    """Ambil tiap bab + beberapa kalimat isinya."""
    pos = [i for i, n, j in lama]
    keluar = []
    for k, idx in enumerate(pos):
        akhir = pos[k + 1] if k + 1 < len(pos) else len(baris)
        isi = ' '.join(baris[idx:min(idx + 6, akhir)])
        keluar.append(isi[:maks_per_bab])
    return '\n\n'.join(keluar)

judul_bab = [f'BAB {n} {j}'.strip() for _, n, j in lama]
state_judul = '\n'.join(judul_bab)
print(f'\n== STATE (judul bab saja) — {len(state_judul)} karakter ==')
print(state_judul[:700])


def tanya(state, questions, label):
    t0 = time.time()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/systemone',
        data=json.dumps({'model': 'typesafe/jev-1.13', 'state': state,
                         'questions': questions}).encode(),
        headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json',
                 'HTTP-Referer': 'https://eduai.local', 'X-Title': 'EduAi Satpam'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode())
            dt = time.time() - t0
            u = d.get('usage', {})
            print(f'\n[{label}] ✅ {dt:.2f} dtk · in={u.get("input_tokens")} '
                  f'out={u.get("output_tokens")} · biaya=${u.get("cost")} '
                  f'= Rp {float(u.get("cost", 0)) * 15800:.4f}')
            for k, v in (d.get('answers') or {}).items():
                print(f'   {k}: {json.dumps(v, ensure_ascii=False)}')
            return d
    except urllib.error.HTTPError as e:
        print(f'\n[{label}] ❌ HTTP {e.code}: {e.read().decode()[:400]}')
    except Exception as e:
        print(f'\n[{label}] ❌ {type(e).__name__}: {e}')
    return None


print('\n' + '=' * 70)
print('PERTANYAAN 1: apakah Jev membaca 5 bab dengan benar?')
print('=' * 70)
tanya(state_judul, {
    'jumlah_bab': {'instructions': 'Ada berapa bab akademik dalam naskah ini?',
                   'type': 'choice',
                   'criteria': {'3': 'tiga bab', '5': 'lima bab',
                                '1': 'satu bab', '7': 'tujuh bab'},
                   'options': ['1', '3', '5', '7']},
    'berurutan': {'instructions': 'Apakah nomor bab berurutan tanpa lompatan?',
                  'type': 'noul'},
    'ada_metode': {'instructions': 'Apakah ada bab METODE PENELITIAN?',
                   'type': 'noul'},
    'ada_hasil': {'instructions': 'Apakah ada bab HASIL dan PEMBAHASAN?',
                  'type': 'noul'},
}, 'A: struktur 5 bab (state = judul bab saja)')
