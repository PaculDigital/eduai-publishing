"""UJI BATAS NYATA: apakah 503 = RATE LIMIT / 504 / provider naik-turun?

Cara ukur yang benar (aturan lama): JANGAN vonis dari 1x gagal.
Yang diukur:
  A. 20 panggilan BERUNTUN TANPA JEDA   -> kalau rate limit, mulai gagal
  B. 20 panggilan BERUNTUN DENGAN JEDA 1 dtk -> kalau lolos, berarti rate limit
  C. Panjang state naik (5rb, 20rb, 40rb, 80rb kar) -> cari TITIK PUTUS
  D. Isi pesan galat MENTAH (bukan yang dipotong 9router)
"""
import sys, time, json, urllib.request, urllib.error
sys.path.insert(0, '/app')
from app import satpam

print('MODEL     :', satpam.MODEL)
print('BASE      :', getattr(satpam, 'BASE', '?')[:60])
print()

def panggil(state, q, timeout=60):
    """Panggil LANGSUNG satpam (jangan lewat pembungkus) + tangkap galat mentah."""
    t0 = time.time()
    try:
        j = satpam.tanya_bebas_mutu(state, q)
        return ('OK' if j else 'KOSONG'), time.time() - t0, ''
    except urllib.error.HTTPError as e:
        try:
            isi = e.read().decode('utf-8', 'replace')[:300]
        except Exception:
            isi = '?'
        return f'HTTP {e.code}', time.time() - t0, isi
    except Exception as e:
        return f'{type(e).__name__}', time.time() - t0, str(e)[:300]

def state_n(n):
    """State berisi n karakter (baris pendek), + 1 pertanyaan noul."""
    baris = [f'L{i:04d}| Baris contoh nomor {i} untuk uji ukuran state jev.' 
             for i in range(n // 50)]
    s = '\n'.join(baris)
    return s[:n], {'t0000': {'instructions': 'Does line L0000 pick up mid-sentence?',
                             'type': 'noul'}}

print('═══ A. 20 panggilan BERUNTUN TANPA JEDA (rate limit?) ═══')
st, q = state_n(2000)
ok = gagal = 0
for i in range(20):
    hasil, dt, pesan = panggil(st, q)
    if hasil == 'OK':
        ok += 1
    else:
        gagal += 1
        print(f'   #{i+1:2d} {hasil:10} {dt:6.2f} dtk  {pesan[:120]}')
print(f'   HASIL: {ok}/20 OK, {gagal} gagal')
print()

print('═══ B. 10 panggilan BERUNTUN DENGAN JEDA 1 dtk ═══')
ok = gagal = 0
for i in range(10):
    hasil, dt, pesan = panggil(st, q)
    if hasil == 'OK':
        ok += 1
    else:
        gagal += 1
        print(f'   #{i+1:2d} {hasil:10} {dt:6.2f} dtk  {pesan[:120]}')
    time.sleep(1)
print(f'   HASIL: {ok}/10 OK, {gagal} gagal')
print()

print('═══ C. CARI TITIK PUTUS: state makin besar ═══')
for n in (5000, 20000, 40000, 80000, 120000):
    st, q = state_n(n)
    hasil, dt, pesan = panggil(st, q)
    print(f'   state {n:7,} kar -> {hasil:10} {dt:6.2f} dtk  {pesan[:150]}')
    time.sleep(1)
