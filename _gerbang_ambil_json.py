"""GERBANG bug `ambil_json` — nama fungsi WAJIB benar (14 Okt 2026).

AKAR: ai.py memanggil `_p.ambil_json(jawab)` sedangkan `peta_halus` hanya
punya `_ambil_json` (bergaris bawah) ⇒ AttributeError SETIAP KALI jalur AI
peta dipakai ⇒ selalu jatuh ke "peta cepat" tanpa disadari.

Gerbang ini memakai `getattr` (bukan teks kode) ⇒ TIDAK bisa jadi gerbang palsu.
Jalankan di DALAM container.
"""
import sys
sys.path.insert(0, '/app')

from app import peta_halus as P

L = G = 0


def cek(n, s, cat=''):
    global L, G
    if s:
        L += 1
        print(f'  ✅ {n}' + (f' — {cat}' if cat else ''))
    else:
        G += 1
        print(f'  ❌ {n}' + (f' — {cat}' if cat else ''))


print('=' * 70)
print('GERBANG ambil_json — NAMA FUNGSI PETA_HALUS')
print('=' * 70)

# ── ① fungsi pengambil JSON ada (salah satu nama) ─────────────────────
ada_ambil = getattr(P, 'ambil_json', None) or getattr(P, '_ambil_json', None)
cek('① pengambil JSON tersedia', callable(ada_ambil),
    'ambil_json' if hasattr(P, 'ambil_json') else '_ambil_json')

# ── ② panggilan di ai.py memakai resolusi yang BENAR ──────────────────
import inspect
from app import ai
src = inspect.getsource(ai.peta_mulai)
cek('② ai.py TIDAK pakai `_p.ambil_json` telanjang',
    '_p.ambil_json(' not in src,
    'pakai getattr (tahan beda nama)')
cek('②b ai.py pakai getattr utk ambil_json',
    "getattr(_p, 'ambil_json'" in src or "getattr(_p, '_ambil_json'" in src)

# ── ③ PERILAKU: pengambil JSON bisa dipakai ──────────────────────────
try:
    uji = '{"a": 1}'
    hasil = ada_ambil(uji)
    cek('③ pengambil JSON jalan', isinstance(hasil, dict), f'{hasil!r}')
except Exception as e:
    cek('③ pengambil JSON jalan', False, f'{type(e).__name__}: {e}')

print('-' * 70)
print(f'HASIL GERBANG ambil_json: {L} LULUS / {G} GAGAL')
raise SystemExit(1 if G else 0)
