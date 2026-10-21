"""Ukur 9router (jalur 1) menurut UKURAN prompt — 28Sep26.

Pertanyaan: kenapa revisi naskah besar (≈58rb kar) selalu `LAMBAT 180 dtk`
padahal teks kecil 1,1 dtk? Diukur dari DALAM container eduai-app,
endpoint SAMA dengan yang dipakai aplikasi (ROUTER_BASE + ROUTER_KEY).
Keluaran: tabel ukuran → durasi → hasil.
"""
import json
import time
import urllib.request

from app.config import ROUTER_BASE, ROUTER_KEY, AI_MODEL

DASAR = ('Penelitian ini membahas pengaruh kualitas produk dan harga '
         'terhadap keputusan pembelian konsumen di Kota Padang menggunakan '
         'regresi linear berganda. ')

print(f'BASE={ROUTER_BASE} MODEL={AI_MODEL}')
print(f'{"ukuran":>8} {"durasi":>8} {"hasil":>6}  catatan')
for ukur in (2_000, 10_000, 30_000, 60_000):
    teks = (DASAR * (ukur // len(DASAR) + 1))[:ukur]
    isi = json.dumps({'model': AI_MODEL,
                      'messages': [{'role': 'user',
                                    'content': teks +
                                    '\n\nBalas HANYA: OK'}],
                      'max_tokens': 64}).encode()
    t = time.time()
    try:
        req = urllib.request.Request(
            ROUTER_BASE + '/chat/completions', data=isi,
            headers={'Authorization': f'Bearer {ROUTER_KEY}',
                     'Content-Type': 'application/json'})
        r = urllib.request.urlopen(req, timeout=150)
        badan = r.read().decode()
        dt = time.time() - t
        catat = badan[:110].replace('\n', ' ')
        print(f'{ukur:>8} {dt:>7.1f}s {r.status:>6}  {catat}')
    except Exception as e:                                     # noqa: BLE001
        dt = time.time() - t
        print(f'{ukur:>8} {dt:>7.1f}s {"GAGAL":>6}  '
              f'{type(e).__name__}: {str(e)[:90]}')
