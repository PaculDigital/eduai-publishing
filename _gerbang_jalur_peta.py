"""GERBANG JALUR PETA — fungsi murni `putuskan_jalur()` (Lapis 2).

BERGIGI: suntikan (buang cek None / buang cek label) ⇒ HARUS GAGAL.
Jalankan DI DALAM container.
"""
import sys
sys.path.insert(0, '/app')

from app.peta_jalur import putuskan_jalur

L, G = 0, 0


def cek(nama, dapat, harus):
    global L, G
    ok = dapat == harus
    print(f'  {"✅" if ok else "❌"} {nama}: dapat {dapat!r} · harus {harus!r}')
    L, G = (L + 1, G) if ok else (L, G + 1)


print('=' * 70)
print('GERBANG JALUR PETA (Lapis 2)')
print('=' * 70)

# ── A. MATI ⇒ fallback ────────────────────────────────────────────────
cek('A1 None ⇒ fallback', putuskan_jalur(None)[0], 'fallback')
cek('A2 bukan dict ⇒ fallback', putuskan_jalur('teks')[0], 'fallback')
cek('A3 dict tanpa label ⇒ fallback', putuskan_jalur({})[0], 'fallback')
cek('A4 label kosong ⇒ fallback', putuskan_jalur({'label': {}})[0], 'fallback')
cek('A5 label bukan dict ⇒ fallback', putuskan_jalur({'label': []})[0], 'fallback')

# ── B. HIDUP ⇒ jev ────────────────────────────────────────────────────
peta_ok = {'label': {10: 'bab', 20: 'subbab', 30: 'subbab'}, 'gabung': {0: 'BAB I'}}
cek('B1 ada bab ⇒ jev', putuskan_jalur(peta_ok)[0], 'jev')
cek('B2 ada subbab saja + gabung ⇒ jev',
    putuskan_jalur({'label': {20: 'subbab'}, 'gabung': {0: 'BAB I'}})[0], 'jev')

# ── C. PAGAR: ragu sebagian BUKAN alasan fallback ─────────────────────
peta_ragu = {'label': {10: 'bab', 20: 'biasa', 30: 'biasa'}, 'goyang': [(20, 30)]}
cek('C1 ragu sebagian ⇒ tetap jev', putuskan_jalur(peta_ragu)[0], 'jev')

# ── D. TANPA bab sama sekali ⇒ fallback ───────────────────────────────
cek('D1 hanya paragraf ⇒ fallback',
    putuskan_jalur({'label': {10: 'paragraf', 20: 'paragraf'}})[0], 'fallback')

# ── E. pesan jelas (untuk JEJAK) ──────────────────────────────────────
j, alasan = putuskan_jalur(peta_ok)
cek('E1 alasan menyebut angkanya', ('bab=' in alasan and 'sub=' in alasan), True)
j2, alasan2 = putuskan_jalur(None)
cek('E2 alasan fallback jelas', len(alasan2) > 5, True)

print('-' * 70)
print(f'HASIL GERBANG JALUR: {L} LULUS / {G} GAGAL')
raise SystemExit(1 if G else 0)
