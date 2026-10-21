"""UJI JEJAK NYATA: bentuk balasan jev dari 9router lewat fungsi SUNGGUHAN.

Tujuan: (a) lihat BENTUK balasan jev yang sebenarnya, (b) buktikan apakah
satpam lama BUTA terhadap salah satu bentuk.

PENTING: ini memanggil 9router SUNGGUHAN (model SATPAM/typesafe/jev-1.13).
"""
import json
import sys

sys.path.insert(0, '/app')
from app import satpam  # noqa: E402

naskah = (
    'BAB I PENDAHULUAN\n\nLatar belakang penelitian ini membahas pengaruh harga '
    'terhadap keputusan pembelian. Data dikumpulkan dari 200 responden.\n\n'
    'BAB II TINJAUAN PUSTAKA\n\nTeori harga menurut Kotler adalah nilai yang '
    'ditukarkan konsumen.\n\n'
    'BAB III METODE PENELITIAN\n\nPenelitian ini menggunakan pendekatan kuantitatif '
    'dengan regresi linear.\n\n'
    'BAB IV HASIL DAN PEMBAHASAN\n\nHasil menunjukkan harga berpengaruh signifikan.\n\n'
    'BAB V KESIMPULAN\n\nKesimpulan: harga berpengaruh positif terhadap keputusan.'
)

peta = [{'section_id': f'BAB {i}', 'section_title': t}
        for i, t in enumerate(
            ['PENDAHULUAN', 'TINJAUAN PUSTAKA', 'METODE PENELITIAN',
             'HASIL DAN PEMBAHASAN', 'KESIMPULAN'], 1)]

print('═' * 96)
print('  UJI JEJAK NYATA — panggil jev lewat fungsi satpam.periksa()')
print('═' * 96)

# ── Ambil balasan MENTAH dengan memanggil sendiri (supaya bisa lihat bentuknya) ──
import urllib.request  # noqa: E402

body = {'model': satpam.MODEL,
        'messages': [{'role': 'user',
                      'content': json.dumps({'state': satpam._susun_state(naskah, peta),
                                             'questions': satpam.TANYA})}]}
req = urllib.request.Request(
    satpam.BASE, data=json.dumps(body).encode(),
    headers={'Authorization': f'Bearer {satpam.KUNCI}',
             'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=90) as r:
    mentah = r.read().decode()

print(f'panjang balasan mentah: {len(mentah)} byte')
print(f'10 karakter pertama  : {mentah[:10]!r}')
print(f'apakah ada "data:"   : {"data:" in mentah}')
print(f'apakah ada "[DONE]"  : {"[DONE]" in mentah}')
print()

u = satpam._urai_balasan(mentah)
kunci = list(u.keys()) if isinstance(u, dict) else None
print(f'kunci hasil urai     : {kunci}')
print()

# ── Apakah satpam bisa membacanya? ──────────────────────────────────────
h = satpam.periksa(naskah, peta)
print('HASIL satpam.periksa():')
print(f'  keputusan   : {h.get("keputusan")}')
print(f'  keyakinan   : {h.get("confidence")}')
print(f'  jumlah_bab  : {h.get("jumlah_bab")}  (mesin: {h.get("jumlah_bab_mesin")})')
print(f'  alasan      : {h.get("alasan")}')
print()

# ── Lakmus: apakah hasil urai punya lapis 'answers'? ────────────────────
if isinstance(u, dict) and 'answers' in u:
    print('🚨 BENTUK BERLAPIS: hasil urai = {"answers": {...}}')
    print('   → satpam LAMA baca jawab["jumlah_bab"] = None ⇒ BUTA')
    bb = (u.get('answers') or {}).get('jumlah_bab') or {}
    print(f'   → kalau dibuka satu lapis: jumlah_bab={bb.get("choice")} '
          f'keyakinan={bb.get("confidence")}')
else:
    print('✅ BENTUK AKAR: hasil urai langsung {jumlah_bab: ...}')
    print('   → satpam lama BISA membacanya')
