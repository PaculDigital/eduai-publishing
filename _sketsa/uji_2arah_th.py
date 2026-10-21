"""UJI 2 ARAH — buktikan akar `content=0` (output invalid) di tokenharbor.

ARAH SEHAT  : kirim parameter matikan reasoning  → content HARUS utuh.
ARAH DIRUSAK: tanpa parameter (pola app hari ini) → content HARUS kosong
              ATAU finish=length (kalau dua-duanya utuh, dugaan Wulan SALAH
              dan harus ditarik).

Prompt & max_tokens DIPERSAMAKAN persis; hanya parameter yang berbeda.
"""
import json, os, time, urllib.error, urllib.request

BASIS = os.environ.get('EDUAI_FALLBACK_BASE', '')
KEY = os.environ.get('EDUAI_FALLBACK_KEY', '')
URL = BASIS.rstrip('/') + '/chat/completions'
MODEL = os.environ.get('MODEL_UJI', 'glm-5.3-flash')

TUGAS = ('Tulis 6 kalimat saran perbaikan tata bahasa paragraf berikut. '
         'Jawab langsung tanpa basa-basi: "Penelitian ini bertujuan untuk '
         'menguji pengaruh harga terhadap pembelian konsumen dengan sampel '
         '100 responden yang dianalisis menggunakan regresi berganda dan '
         'hasilnya menunjukkan bahwa harga berpengaruh signifikan."')


def kirim(tag, tambahan, max_tok=500):
    p = {'model': MODEL, 'max_tokens': max_tok, 'temperature': 0.2,
         'messages': [{'role': 'user', 'content': TUGAS}]}
    p.update(tambahan)
    req = urllib.request.Request(
        URL, data=json.dumps(p).encode(), method='POST',
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            j = json.loads(r.read().decode('utf-8', 'ignore') or '{}')
    except urllib.error.HTTPError as e:
        out = {'tag': tag, 'ok': False, 'status': e.code,
               'galat': e.read().decode('utf-8', 'ignore')[:300]}
        print(json.dumps(out, ensure_ascii=False), flush=True)
        return out
    dt = time.monotonic() - t0
    ch = (j.get('choices') or [{}])[0]
    pesan = ch.get('message') or {}
    isi = pesan.get('content') or ''
    out = {'tag': tag, 'ok': True, 'dt': round(dt, 1),
           'finish': ch.get('finish_reason'),
           'ada_reasoning': 'reasoning_content' in pesan,
           'panjang_reasoning': len(pesan.get('reasoning_content') or ''),
           'panjang_content': len(isi),
           'compl_tok': (j.get('usage') or {}).get('completion_tokens')}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return out


hasil = {}
print('ARAH DIRUSAK (pola app: tanpa parameter matikan reasoning)', flush=True)
hasil['rusak'] = kirim('RUSAK-tanpa-param', {})
time.sleep(1)
print('ARAH SEHAT (dengan enable_thinking=false)', flush=True)
hasil['sehat'] = kirim('SEHAT-enable_thinking', {'enable_thinking': False})
time.sleep(1)
print('ARAH SEHAT-2 (chat_template_kwargs)', flush=True)
hasil['sehat2'] = kirim('SEHAT-chat_template',
                        {'chat_template_kwargs': {'enable_thinking': False}})

with open('/tmp/uji_2arah_th.json', 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)

r_, s_ = hasil['rusak'], hasil['sehat']
kegagalan_terbukti = (r_['panjang_content'] == 0 or r_['finish'] == 'length')
kesembuhan_terbukti = s_['panjang_content'] > 100 and s_['finish'] == 'stop'
print(f'\nVERDIKT: rusak(content={r_["panjang_content"]},finish={r_["finish"]}) '
      f'sehat(content={s_["panjang_content"]},finish={s_["finish"]})')
print('KESIMPULAN:', 'TERBUKTI 2 ARAH' if (kegagalan_terbukti and
      kesembuhan_terbukti) else 'TIDAK TERBUKTI — dugaan ditarik', flush=True)
