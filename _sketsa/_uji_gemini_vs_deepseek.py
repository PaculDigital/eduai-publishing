"""UJI MODEL UNGGULAN: GEMINI vs DEEPSEEK berdasarkan HARGA + SUPPLY.
Sumber harga/supply: /v1/models?detail=1 + /api/catalog (diukur 16Sep26).

Kriteria uji: apakah menjawab (tidak kosong), kecepatan, dan kemiripan
2 putaran (kestabilan). max_tokens=8000 seperti produksi EduAi.
"""
import json
import time
import urllib.error
import urllib.request
from difflib import SequenceMatcher

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
BASE = 'https://api.inferhub.dev/v1'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

PESAN = ("Perbaiki ejaan dan tata bahasa paragraf akademik berikut, "
         "jangan ubah makna. Kembalikan HANYA paragraf hasil perbaikan.\n\n"
         "Penelitian ini bertujuan untuk menganalisis pengaruh kualitas kehidupan "
         "kerja terhadap kinerja adaptif pegawai. Kesiapan digital dipakai sebagai "
         "variabel mediasi. Data dikumpulkan memakai kuesioner lima skala likert "
         "yang telah diuji validitas dan reliabilitasnya.")


def panggil(model, max_tokens=8000, temperature=0.0, timeout=300):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': PESAN}],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json',
                 'User-Agent': UA})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode("utf-8","ignore")[:100]}'
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
    return {
        'detik': d,
        'model': j.get('model'),
        'teks': ch['message'].get('content') or '',
        'panjang': len(ch['message'].get('content') or ''),
        'reasoning': (u.get('completion_tokens_details') or {}).get(
            'reasoning_tokens', 0),
        'tok_in': u.get('prompt_tokens', 0),
        'tok_out': u.get('completion_tokens', 0),
        'finish': ch.get('finish_reason'),
    }, None


# (model, supply, harga_min_usd_per_Mtok_in, catatan)
KANDIDAT = [
    # GEMINI
    ('ag/gemini-3.8-flash-high', 633, 0.0008, 'gemini - tercepat kemarin'),
    ('ag/gemini-3.7-flash-high', 633, 0.0008, 'gemini - termurah'),
    ('cb/gemini-3.1-pro', 861, 0.0960, 'gemini - supply terbanyak'),
    ('ag/gemini-3.6-flash-high', 633, 0.0037, 'gemini - lama'),
    # DEEPSEEK
    ('ali/deepseek-v4.1-flash', 18949, 0.0043, 'deepseek - SUPPLY TERBANYAK'),
    ('ali/deepseek-v4-flash-0731', 18949, 0.0064, 'deepseek - supply 18949'),
    ('cbcn/deepseek-v4.1-flash', 6714, 0.0051, 'deepseek - median termurah'),
    ('cb/deepseek-v4.1-flash', 861, 0.0029, 'deepseek - min termurah'),
    # PEMBANDING MURAH
    ('ali/kimi-k2.7-code', 18949, 0.0009, 'kimi - supply 18949'),
    ('zai/glm-4.7', 26, 0.0006, 'termurah absolut (supply kecil)'),
]

print('=' * 108)
print('UJI GEMINI vs DEEPSEEK vs MURAH - langsung InferHub, max_tokens=8000, temp=0')
print('=' * 108)

hasil_semua = []
for m, supply, harga, catatan in KANDIDAT:
    print(f'\n>>> {m}   [supply={supply} | min=${harga}/Mtok | {catatan}]')
    hs = []
    for ulang in (1, 2):
        h, err = panggil(m)
        if err:
            print(f'    #{ulang}: {err}')
            continue
        print(f"    #{ulang}: {h['detik']:6.1f}s | len={h['panjang']:5d} | "
              f"reason={h['reasoning']:5d} | in={h['tok_in']:5d} "
              f"out={h['tok_out']:5d} | {h['finish']}")
        if h['panjang'] > 0:
            hs.append(h)
    if hs:
        rata = sum(x['detik'] for x in hs) / len(hs)
        mirip = (SequenceMatcher(None, hs[0]['teks'], hs[1]['teks']).ratio()
                 if len(hs) == 2 else 0.0)
        hasil_semua.append({
            'model': m, 'supply': supply, 'harga': harga, 'catatan': catatan,
            'ok': len(hs), 'detik': rata,
            'panjang': sum(x['panjang'] for x in hs) // len(hs),
            'mirip': mirip,
            'tok_in': hs[0]['tok_in'], 'tok_out': hs[0]['tok_out'],
        })
        print(f'    rata {rata:.1f}s | kemiripan 2 putaran: {mirip:.3f}')
        print(f"    contoh: {hs[0]['teks'][:130]!r}")
    else:
        hasil_semua.append({'model': m, 'supply': supply, 'harga': harga,
                            'catatan': catatan, 'ok': 0, 'detik': 0,
                            'panjang': 0, 'mirip': 0.0, 'tok_in': 0, 'tok_out': 0})
        print('    TIDAK menghasilkan jawaban')

print('\n' + '=' * 108)
print('RINGKASAN (urut: berhasil, lalu termurah)')
print('=' * 108)
print(f"{'model':30s} {'ok':>3s} {'supply':>7s} {'min$/M':>8s} {'detik':>7s} "
      f"{'len':>5s} {'mirip':>6s}")
for r in sorted(hasil_semua, key=lambda x: (-x['ok'], x['harga'])):
    print(f"{r['model']:30s} {r['ok']:3d} {r['supply']:7d} {r['harga']:8.4f} "
          f"{r['detik']:6.1f}s {r['panjang']:5d} {r['mirip']:6.3f}")

open('/opt/data/services/eduai-publishing/_hasil_uji_model.json', 'w').write(
    json.dumps(hasil_semua, ensure_ascii=False, indent=1))
print('\ndisimpan: _hasil_uji_model.json')
