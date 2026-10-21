"""UJI 3: bentuk CHOICE & SCORE yang benar di Jev (+ ukur biaya nyata)."""
import json
import sqlite3
import time
import urllib.error
import urllib.request

c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
row = c.execute("select data from providerConnections where provider='openrouter'").fetchone()
key = json.loads(dict(row)['data']).get('apiKey')

STATE = ("BAB I PENDAHULUAN\nLatar belakang masalah penelitian.\n"
         "BAB II TINJAUAN PUSTAKA\nTeori-teori pendukung.\n"
         "BAB III METODE PENELITIAN\nCara penelitian dilakukan.")


def kirim(body, label):
    t0 = time.time()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/systemone',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                 'HTTP-Referer': 'https://eduai.local', 'X-Title': 'EduAi Satpam Test'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            isi = json.loads(r.read().decode())
            print(f'[{label}] HTTP 200 ✅  ({time.time()-t0:.2f} dtk)')
            print('   answers:', json.dumps(isi.get('answers'), ensure_ascii=False))
            u = isi.get('usage', {})
            print(f"   token in={u.get('input_tokens')} out={u.get('output_tokens')} "
                  f"biaya=${u.get('cost')} = Rp {float(u.get('cost', 0))*15800:.4f}")
    except urllib.error.HTTPError as e:
        print(f'[{label}] HTTP {e.code} ❌')
        print('  ', e.read().decode()[:500])
    except Exception as e:
        print(f'[{label}] GAGAL {type(e).__name__}: {e}')
    print()


# CHOICE dengan criteria (bentuk yang diminta)
kirim({'model': 'typesafe/jev-1.13', 'state': STATE, 'questions': {
    'kategori_bab': {
        'instructions': 'Bagian ini termasuk kategori apa?',
        'type': 'choice',
        'criteria': {'pendahuluan': 'Membahas latar belakang dan rumusan masalah',
                     'tinjauan': 'Membahas teori dan penelitian terdahulu',
                     'metode': 'Membahas cara/desain penelitian'},
        'options': ['pendahuluan', 'tinjauan', 'metode'],
    }}}, 'CHOICE (kategori bab)')

# SCORE dengan criteria
kirim({'model': 'typesafe/jev-1.13', 'state': STATE, 'questions': {
    'kualitas_struktur': {
        'instructions': 'Seberapa rapi struktur bab ini?',
        'type': 'score',
        'criteria': {'0': 'struktur kacau', '1': 'cukup', '2': 'sangat rapi'},
        'options': [0, 1, 2],
    }}}, 'SCORE (kualitas struktur)')

# NOUL jamak sekaligus (uji "satpam" banyak pertanyaan)
kirim({'model': 'typesafe/jev-1.13', 'state': STATE, 'questions': {
    'bab_berurutan': {'instructions': 'Apakah bab berurutan I, II, III?', 'type': 'noul'},
    'ada_bab_hasil': {'instructions': 'Apakah ada bab HASIL atau PEMBAHASAN?', 'type': 'noul'},
    'ada_daftar_pustaka': {'instructions': 'Apakah ada DAFTAR PUSTAKA?', 'type': 'noul'},
}}, '3 NOUL sekaligus (satpam penuh)')
