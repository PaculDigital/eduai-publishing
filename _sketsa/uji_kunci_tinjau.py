"""UJI KUNCI TINJAU — 03Okt26. Buktikan BERGIGI, bukan cuma "bisa dibuat".

Diuji: (1) kunci sah dibaca benar; (2) kunci PALSU ditolak; (3) kunci
kedaluwarsa ditolak; (4) kunci naskah A TIDAK membuka naskah B (scoped);
(5) bentuk ngawur tidak bikin meledak; (6) batas_exp tidak melebihi token.
"""
import sys

sys.path.insert(0, '/app')
from app import kunci_tinjau as K                                  # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}')


print('=== A. KUNCI SAH ===')
exp = int(__import__('time').time()) + 3600
k = K.kunci_untuk(7, 60, exp)
print('   contoh kunci:', k[:40], '...')
cek('A1 kunci sah → (7, 60)', K.baca_kunci(k) == (7, 60))

print('=== B. KUNCI PALSU DITOLAK ===')
#  Ganti sidik jadi ngawur
bagian = k.split('.')
palsu = '.'.join(bagian[:3] + ['0' * 64])
cek('B1 sidik dipalsukan → None', K.baca_kunci(palsu) is None)
cek('B2 ubah berkas_id (tanpa sidik baru) → None',
    K.baca_kunci(f'7.99.{exp}.{bagian[3]}') is None)
cek('B3 ubah bimbingan_id → None',
    K.baca_kunci(f'99.60.{exp}.{bagian[3]}') is None)

print('=== C. KEDALUWARSA DITOLAK ===')
k_lama = K.kunci_untuk(7, 60, int(__import__('time').time()) - 10)
cek('C1 kunci lewat masa berlaku → None', K.baca_kunci(k_lama) is None)

print('=== D. SCOPED KE SATU NASKAH ===')
k_a = K.kunci_untuk(7, 60, exp)
k_b = K.kunci_untuk(7, 61, exp)
cek('D1 kunci naskah 60 ≠ kunci naskah 61', k_a != k_b)
cek('D2 kunci 60 dibaca (7,60)', K.baca_kunci(k_a) == (7, 60))
cek('D3 kunci 61 dibaca (7,61)', K.baca_kunci(k_b) == (7, 61))

print('=== E. BENTUK NGAWUR — TIDAK MELEDAK ===')
for bentuk in (None, '', 'a', 'a.b', 'a.b.c', 'a.b.c.d.e', '7.60.abc.sig',
               '7.60.99999999999999.' + 'x' * 64, 12345):
    try:
        hasil = K.baca_kunci(bentuk)
        cek(f'E1 bentuk {bentuk!r:.30} → {hasil!r} (tidak meledak)', True)
    except Exception as e:                                    # noqa: BLE001
        cek(f'E1 bentuk {bentuk!r:.30} MELEDAK: {e}', False)

print('=== F. BATAS EXP TIDAK MELEBIHI TOKEN TINJAU ===')
from datetime import datetime, timedelta, timezone                # noqa: E402
kini = datetime.now(timezone.utc)
exp_pendek = K.batas_exp(kini + timedelta(hours=2))
exp_panjang = K.batas_exp(kini + timedelta(days=30))
cek('F1 token 2 jam → cookie ≤ ~2 jam',
    exp_pendek - int(kini.timestamp()) <= 2 * 3600 + 5)
cek('F2 token 30 hari → cookie dibatasi ≤ 7 hari',
    exp_panjang - int(kini.timestamp()) <= 7 * 24 * 3600 + 5)
cek('F3 token sudah lewat → minimal 60 detik (tidak nol/negatif)',
    K.batas_exp(kini - timedelta(hours=1)) - int(kini.timestamp()) >= 60)

print()
print(f'═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
sys.exit(1 if GAGAL else 0)
