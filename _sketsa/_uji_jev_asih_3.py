"""UJI JEV KE-2 — naskah BERANTAKAN & PROPOSAL (kasus yang menipu mesin lama).

Kasus uji (semua dari kejadian NYATA di proyek):
  U1. Bab salah tulis romawi: "BAB IIII"
  U2. Naskah tanpa bab sama sekali (artikel jurnal)
  U3. Proposal (hanya BAB I–III, tidak ada IV/V)
  U4. Daftar isi menggoda (judul bab muncul 2× — daftar isi + asli)
  U5. Bab dengan judul MENEMPEL: "BAB IPENDAHULUAN"

Yang diukur: apakah Jev BENAR di semua kasus, dan apakah confidence-nya
turun jujur ketika naskahnya memang ambigu.
"""
import json
import sqlite3
import time
import urllib.error
import urllib.request

c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
KEY = json.loads(dict(c.execute(
    "select data from providerConnections where provider='openrouter'").fetchone())['data'])['apiKey']


def tanya(state, questions, label, harap=None):
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
            print(f'\n[{label}] ✅ {dt:.2f} dtk · Rp {float(u.get("cost", 0))*15800:.4f}')
            jawab = {}
            for k, v in (d.get('answers') or {}).items():
                print(f'   {k}: {json.dumps(v, ensure_ascii=False)}')
                jawab[k] = v
            if harap:
                print(f'   HARAPAN WULAN: {harap}')
            return jawab
    except urllib.error.HTTPError as e:
        print(f'\n[{label}] ❌ HTTP {e.code}: {e.read().decode()[:300]}')
    except Exception as e:
        print(f'\n[{label}] ❌ {type(e).__name__}: {e}')
    return {}


S_STRUKTUR = {
    'jumlah_bab': {'instructions': 'Berapa bab akademik yang benar-benar ada di naskah ini?',
                   'type': 'choice',
                   'criteria': {'0': 'tidak ada bab', '1': 'satu', '3': 'tiga',
                                '5': 'lima', '7': 'tujuh'},
                   'options': ['0', '1', '3', '5', '7']},
    'semua_romawi_sah': {'instructions':
        'Apakah semua nomor bab memakai angka romawi yang SAH (I, II, III, IV, V)?',
        'type': 'noul'},
    'berurutan': {'instructions': 'Apakah urutan bab tidak melompat?', 'type': 'noul'},
}

print('=' * 72)
print('U1. BAB SALAH TULIS ROMAWI ("BAB IIII") — kasus nyata ditemukan 03Okt26')
print('=' * 72)
tanya('BAB I PENDAHULUAN\nisi...\nBAB II TINJAUAN PUSTAKA\nisi...\n'
      'BAB IIII METODE PENELITIAN\nisi...\nBAB IV HASIL DAN PEMBAHASAN\nisi...\n'
      'BAB V PENUTUP\nisi...', S_STRUKTUR, 'U1: BAB IIII', 'harusnya: 5 bab? / romawi sah = TIDAK')

print()
print('=' * 72)
print('U2. NASKAH TANPA BAB (artikel jurnal)')
print('=' * 72)
tanya('Pengaruh Harga terhadap Keputusan Pembelian\nAbstrak\nPenelitian ini '
      'bertujuan...\nPendahuluan\nHarga adalah...\nMetode\nPopulasi penelitian...\n'
      'Hasil dan Pembahasan\nUji t menunjukkan...\nKesimpulan\nHarga berpengaruh...\n'
      'Daftar Pustaka\nArikunto (2019)...',
      S_STRUKTUR, 'U2: artikel jurnal (tanpa "BAB")',
      'harusnya: 0 bab / tidak ada romawi / -')

print()
print('=' * 72)
print('U3. PROPOSAL (hanya BAB I-III) — kasus nyata: proposal tesis Bos')
print('=' * 72)
tanya('BAB I PENDAHULUAN\n1.1 Latar Belakang\n...\nBAB II TINJAUAN PUSTAKA\n...\n'
      'BAB III METODE PENELITIAN\n...\nSistematika Penulisan\nBAB IV akan berisi hasil.',
      S_STRUKTUR, 'U3: proposal 3 bab',
      'harusnya: 3 bab (jangan tertipu "BAB IV akan berisi")')

print()
print('=' * 72)
print('U4. DAFTAR ISI MENGGODA (judul bab muncul 2×)')
print('=' * 72)
tanya('DAFTAR ISI\nBAB I PENDAHULUAN1\nBAB II TINJAUAN PUSTAKA17\n'
      'BAB III METODE PENELITIAN31\nBAB IV HASIL DAN PEMBAHASAN46\nBAB V PENUTUP58\n'
      'BAB I PENDAHULUAN\nLatar belakang penelitian ini...\nBAB II TINJAUAN PUSTAKA\n'
      'Teori yang digunakan...\nBAB III METODE PENELITIAN\nDesain penelitian...\n'
      'BAB IV HASIL DAN PEMBAHASAN\nHasil pengujian...\nBAB V PENUTUP\nKesimpulan...',
      S_STRUKTUR, 'U4: daftar isi + asli', 'harusnya: 5 bab (bukan 10)')

print()
print('=' * 72)
print('U5. JUDUL MENEMPEL ("BAB IPENDAHULUAN")')
print('=' * 72)
tanya('BAB IPENDAHULUAN\nisi bab satu\nBAB IITINJAUAN PUSTAKA\nisi\n'
      'BAB IIIMETODE PENELITIAN\nisi\nBAB IVHASIL DAN PEMBAHASAN\nisi\n'
      'BAB VPENUTUP\nisi',
      S_STRUKTUR, 'U5: judul menempel', 'harusnya: 5 bab')
