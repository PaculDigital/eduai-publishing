"""B: uji pemisah — apakah jalur 1 lambat karena INPUT besar atau OUTPUT besar?

Tiga tembakan (semua pakai naskah asli 65.826 kar):
  U1  input besar + output KECIL  (max_tokens=60)  → kalau cepat = input BUKAN masalah
  U2  input sedang + output sedang (max_tokens=2000, suhu 0.2) → lihat throughput nyata
Catat SEMUA waktu; jangan tampilkan key.
"""
import json
import os
import time
import urllib.request

BASE = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
KEY = os.getenv('EDUAI_ROUTER_KEY', '')
MODEL = os.getenv('EDUAI_AI_MODEL', 'EduAi')
TEKS = open('/app/_contoh-dokumen/skripsi-s1/NASKAH-ASLI-file47-65826kar.txt',
            encoding='utf-8', errors='replace').read()


def tembak(label, pesan, max_tokens):
    body = json.dumps({
        'model': MODEL,
        'messages': [{'role': 'user', 'content': pesan}],
        'max_tokens': max_tokens, 'temperature': 0.2,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=300) as h:
            mentah = h.read().decode('utf-8', 'replace')
        dta = time.monotonic() - t0
        try:
            isi = json.loads(mentah.strip().split('\n')[0])
        except Exception:
            isi = json.loads(mentah)
        isi_txt = isi['choices'][0]['message'].get('content') or ''
        up = isi.get('usage', {})
        print(f'{label}: {dta:.1f} dtk · balas {len(isi_txt)} kar · '
              f'model_asli={isi.get("model", "?")} · '
              f'tok_in={up.get("prompt_tokens", "?")} out={up.get("completion_tokens", "?")}')
    except Exception as e:
        print(f'{label}: GAGAL {time.monotonic() - t0:.1f} dtk · {type(e).__name__}: {e}')


tembak('U1 input 65rb kar + out max 60  ', TEKS[:65000] + '\n\nBalas satu kata: OK', 60)
tembak('U2 input 65rb kar + out max 2000',
       'Perbaiki paragraf pertama bagian latar belakang naskah berikut, '
       'singkat 30% tanpa mengubah arti:\n\n' + TEKS[:65000], 2000)
