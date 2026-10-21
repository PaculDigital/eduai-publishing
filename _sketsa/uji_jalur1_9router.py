"""UJI JALUR 1 (9router) — jatah token vs isi jawaban.

Tujuan: buktikan apakah notif "jalur 1 AI sedang bermasalah" itu AKAR NYATA
(jalur 1 benar-benar mati) atau SALAH HITUNG di aplikasi.

⚠️ 9router mengirim DATA BERLAPIS (extra data) → json.loads gagal.
   Harus dibaca baris demi baris / ambil objek pertama.
"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '/app')
from app import config as C  # noqa: E402

url = C.ROUTER_BASE.rstrip('/') + '/chat/completions'


def tanya(mtok: int, pesan: str = 'Balas hanya: OK'):
    body = json.dumps({'model': C.AI_MODEL,
                       'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': mtok}).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + C.ROUTER_KEY})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=120)
        raw = r.read().decode('utf-8', 'replace')
    except Exception as e:                                        # noqa: BLE001
        return f'GAGAL {type(e).__name__}: {e}', 0
    dtk = time.time() - t
    # 9router bisa kirim lebih dari satu objek JSON berurutan → ambil yang pertama
    dec = json.JSONDecoder()
    try:
        d, _ = dec.raw_decode(raw)
    except Exception as e:                                        # noqa: BLE001
        return f'TAK BISA DIBACA: {e} | raw[0:200]={raw[:200]}', dtk
    ch = (d.get('choices') or [{}])[0]
    m = ch.get('message') or {}
    u = d.get('usage') or {}
    isi = m.get('content') or ''
    return (f"finish={ch.get('finish_reason')} model={d.get('model')} "
            f"content={len(isi)}kar thinking={u.get('completion_thinking_tokens', 0)}tok "
            f"out={u.get('completion_tokens', 0)}tok | isi={isi[:60]!r}"), dtk


print('═' * 100)
print('  UJI JALUR 1 — 9router  |  model:', C.AI_MODEL, '| base:', C.ROUTER_BASE)
print('═' * 100)
for mtok, pesan in [(20, 'Balas hanya: OK'), (300, 'Balas hanya: OK'),
                    (2000, 'Balas hanya: OK')]:
    hasil, dtk = tanya(mtok, pesan)
    print(f'  max_tokens={mtok:<5} {dtk:5.1f}dtk  {hasil}')

print()
print('  ── dengan tugas lebih berat (mirip revisi naskah) ──')
hasil, dtk = tanya(2000, 'Tulis 3 kalimat tentang pentingnya latar belakang penelitian.')
print(f'  max_tokens=2000  {dtk:5.1f}dtk  {hasil}')
