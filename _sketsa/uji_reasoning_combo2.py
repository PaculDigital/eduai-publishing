"""Eksperimen batch 2 (lanjutan): isolasi penyebab combo gagal di prompt panjang.

  G qwen langsung, prompt panjang, enable_thinking:false, stream:false
  H qwen langsung, prompt panjang, tanpa field thinking, stream:false
  F2 combo 'pong' pendek, enable_thinking:false, stream:false (ulang F bersih)
  I combo prompt panjang, model 'EduAi(none)', enable_thinking:false, stream:false

Dijalankan DI DALAM container eduai-app. TIDAK mengubah DB/kode produksi.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import sys

sys.path.insert(0, '/app')
from app.config import ROUTER_BASE, ROUTER_KEY, AI_MODEL
from app.agen_kedua import _prompt, _urai_jawaban, MAKS_TOKEN_JAWAB

masuk = json.load(open('/tmp/ukur_masuk.json', encoding='utf-8'))
baris = masuk['baris'] if isinstance(masuk, dict) else masuk
t = next(b for b in baris if b.get('ditandai_hakim'))
prompt = _prompt(t.get('teks_baris'), t.get('konteks'))
print('BARIS:', t.get('naskah'), t.get('no'), '| prompt_chars:', len(prompt),
      flush=True)


def panggil(nama, model, extra, pr=None, timeout=90):
    body = {'model': model,
            'messages': [{'role': 'user',
                          'content': pr if pr is not None else prompt}],
            'max_tokens': MAKS_TOKEN_JAWAB, 'temperature': 0.2,
            'stream': False}
    body.update(extra)
    req = urllib.request.Request(
        ROUTER_BASE.rstrip('/') + '/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {ROUTER_KEY}'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            mentah = r.read().decode()
        dt = time.time() - t0
        j = json.loads(mentah)
        ch = (j.get('choices') or [{}])[0]
        konten = (ch.get('message') or {}).get('content') or ''
        u = j.get('usage') or {}
        det = (u.get('completion_tokens_details') or {})
        jawab = _urai_jawaban(konten) if konten else None
        print(f"{nama}: dt={dt:.1f}s model={j.get('model')} "
              f"finish={ch.get('finish_reason')} "
              f"in={u.get('prompt_tokens')} out={u.get('completion_tokens')} "
              f"reasoning_tokens={det.get('reasoning_tokens')} "
              f"terurai={'YA ' + str(jawab) if jawab else 'TIDAK'} "
              f"konten={konten[:120]!r}", flush=True)
        return {'nama': nama, 'dt': round(dt, 1), 'model': j.get('model'),
                'finish': ch.get('finish_reason'), 'usage': u,
                'terurai': bool(jawab), 'konten': konten[:300]}
    except Exception as e:
        dt = time.time() - t0
        print(f"{nama}: dt={dt:.1f}s GALAT {type(e).__name__}: {e}",
              flush=True)
        return {'nama': nama, 'dt': round(dt, 1),
                'galat': f'{type(e).__name__}: {e}'}


QWEN = 'inferhub/ali/qwen3.8-max'
hasil = []
hasil.append(panggil('G-qwen-langsung-panjang(enable_thinking:false)',
                     QWEN, {'enable_thinking': False}))
hasil.append(panggil('H-qwen-langsung-panjang(tanpa-field)',
                     QWEN, {}))
hasil.append(panggil('F2-combo-pong(enable_thinking:false)',
                     AI_MODEL, {'enable_thinking': False},
                     pr='Jawab dengan satu kata saja: pong'))
hasil.append(panggil('I-combo-panjang-model-EduAi(none)',
                     'EduAi(none)', {'enable_thinking': False}))
json.dump({'baris': {'naskah': t.get('naskah'), 'no': t.get('no')},
           'prompt_chars': len(prompt), 'hasil': hasil},
          open('/tmp/hasil_uji_reasoning_combo2.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('SELESAI, tersimpan /tmp/hasil_uji_reasoning_combo2.json', flush=True)
