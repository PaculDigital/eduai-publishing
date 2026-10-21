"""UJI VISION 9router — combo `EduAi` bisa baca gambar? (pertanyaan Bos 27Sep26)

Kirim gambar PNG berisi teks (dibuat PIL di host) sebagai image_url
(base64 data URL) → lihat apakah model di balik combo membaca teksnya.
"""
import base64
import io
import json
import time
import urllib.request

KEY = [l.split('=', 1)[1].strip()
       for l in open('/opt/data/services/eduai-publishing/.env')
       if l.startswith('EDUAI_ROUTER_KEY=')][0]

from PIL import Image, ImageDraw

img = Image.new('RGB', (240, 60), 'white')
d = ImageDraw.Draw(img)
d.text((10, 20), 'GANODERMA 42 SAWIT', fill='black')
buf = io.BytesIO()
img.save(buf, 'PNG')
b64 = base64.b64encode(buf.getvalue()).decode()

for model in ('EduAi', 'EduAi Tier 2'):
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text',
             'text': 'Baca teks pada gambar ini. Jawab HANYA isi teksnya.'},
            {'type': 'image_url',
             'image_url': {'url': f'data:image/png;base64,{b64}'}},
        ]}],
    }
    req = urllib.request.Request(
        'http://172.17.0.1:20128/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=180)
        mentah = r.read().decode()
        # 9router kadang mengirim streaming/SSE atau data menempel — coba
        # SSE dulu, lalu raw_decode jangkar '{'
        if mentah.startswith('data:'):
            isi_txt = ''
            for baris in mentah.splitlines():
                if baris.startswith('data:') and '[DONE]' not in baris:
                    try:
                        chunk = json.loads(baris[5:].strip())
                        delta = (chunk.get('choices') or [{}])[0].get(
                            'delta', {}).get('content')
                        if delta:
                            isi_txt += delta
                        m = chunk.get('model')
                    except Exception:                     # noqa: BLE001
                        pass
            print(f'✅(sse) {model}: {time.time()-t0:.1f}s · jawaban: '
                  f'{isi_txt.strip()[:120]!r}')
            continue
        resp, _ = json.JSONDecoder().raw_decode(mentah.lstrip())
        msg = resp['choices'][0]['message']
        isi = msg.get('content') or ''
        if isinstance(isi, list):
            isi = ' '.join(x.get('text', '') for x in isi if isinstance(x, dict))
        print(f'✅ {model}: {time.time()-t0:.1f}s · model_asli='
              f'{resp.get("model")} · jawaban: {isi.strip()[:120]!r}')
    except Exception as e:                                   # noqa: BLE001
        bad = getattr(e, 'read', lambda: b'')()
        print(f'❌ {model}: {time.time()-t0:.1f}s · {e} · {bad[:160]}')
