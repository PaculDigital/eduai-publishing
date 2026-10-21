"""UJI BERGIGI: jev MELAPOR, pagar aritmatika yang MEMUTUSKAN (putusan Bos "B").

Yang dibuktikan (4 asersi, harus BISA GAGAL):
  1. jev tak bisa lagi MENGhentikan potongan sah → `keputusan` = 'lapor'
  2. pagar aritmatika TETAP menolak yang sungguh ngawur (rasio > batas)
     — dibuktikan dengan MEMANGGIL pipa.periksa() SUNGGUHAN
  3. pagar aritmatika TETAP meloloskan yang wajar (rasio <= batas)
  4. jev MATI/gagal → pagar tetap bekerja (tidak ada penolakan palsu)

⚠️ jev DIPALSUKAN pada asersi 2-4 supaya cepat & deterministik; asersi 1
   memakai jawaban jev NYATA yang sudah TERCATAT (0,99 ya_ngawur).
"""
import sys
import types

sys.path.insert(0, '/app')

lulus = gagal = 0


def cek(nama, syarat, info=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  OK    {nama}')
    else:
        gagal += 1
        print(f'  GAGAL {nama}  {info}')


from app import pipa  # noqa: E402
from app import satpam  # noqa: E402

print('═' * 88)
print('  UJI BERGIGI — jev MELAPOR, pagar aritmatika MEMUTUSKAN')
print('═' * 88)

# ── 1. jev tidak lagi memutuskan lolos/tolak ────────────────────────────
print('\n── 1. jev tidak lagi memutuskan ──')
n = satpam.nilai_balasan('Pendidikan penting.', 'Pendidikan penting.',
                         'Pendidikan penting sekali dan sangat berarti.',
                         'perbaiki ejaan', 1.2, 200)
cek('1a jev balas keputusan=lapor (bukan tolak/lolos)',
    n.get('keputusan') == 'lapor', n)
cek('1b jev tetap MELAPOR apa yang dilihat (kunci laporan ada)',
    isinstance(n.get('laporan'), dict) and 'ngawur' in (n.get('laporan') or {}),
    n.get('laporan'))

# ── 2-4. pagar aritmatika tetap memutuskan (jev dipalsukan) ─────────────
par = ('Pendidikan memiliki peran yang sangat penting dalam membentuk '
       'karakter generasi muda. Proses pendidikan tidak hanya terjadi di '
       'dalam kelas, tetapi juga di lingkungan keluarga dan masyarakat.')
wajar = par.replace('sangat penting', 'penting')
ngawur = ('BAB I PENDAHULUAN\n\nPendidikan merupakan fondasi utama. ' * 40)

naskah = par
jawab_wajar = f'[K1-KUTIP-ASLI] {par}\n[K1-GANTI-JADI] {wajar}'
jawab_ngawur = f'[K1-KUTIP-ASLI] {par}\n[K1-GANTI-JADI] {ngawur}'

#  jev dipalsukan: SELALU bilang ya_ngawur dengan keyakinan 1,0
_PALSU = {'ok': True, 'keputusan': 'lapor', 'confidence': 1.0,
          'alasan': 'jev menduga balasan mengarang',
          'laporan': {'ngawur': 'ya_ngawur', 'confidence': 1.0}}
_asli = satpam.nilai_balasan
satpam.nilai_balasan = lambda *a, **k: dict(_PALSU)

print('\n── 2. jev bilang "NGAWUR" tapi panjangnya WAJAR → tetap LOLOS ──')
h = pipa.periksa(jawab_wajar, naskah, 'perbaiki ejaan')
cek('2a balasan wajar TIDAK ditolak walau jev bilang ngawur',
    h.ok and len(h.editan) >= 1, {'ok': h.ok, 'editan': len(h.editan),
                                  'ditolak': h.ditolak})
cek('2b tidak ada yang masuk daftar ditolak',
    len(h.ditolak) == 0, h.ditolak)

print('\n── 3. panjang NGAWUR (rasio jauh > batas) → DITOLAK aritmatika ──')
h3 = pipa.periksa(jawab_ngawur, naskah, 'perbaiki ejaan')
cek('3a balasan ngawur DITOLAK', not h3.ok, {'ok': h3.ok, 'pesan': h3.pesan[:80]})
cek('3b sebabnya aritmatika (ganti_terlalu_panjang)',
    any(d.get('sebab') == 'ganti_terlalu_panjang' for d in h3.ditolak),
    h3.ditolak)
cek('3c laporan jev IKUT TERCATAT di daftar ditolak (untuk audit)',
    any(isinstance(d.get('jev'), dict) for d in h3.ditolak),
    [d.get('jev') for d in h3.ditolak])

print('\n── 4. jev MATI total → pagar tetap bekerja (tak ada tolak palsu) ──')


def _jev_mati(*a, **k):
    raise RuntimeError('jev mati (tiruan)')


satpam.nilai_balasan = _jev_mati
h4 = pipa.periksa(jawab_wajar, naskah, 'perbaiki ejaan')
cek('4a balasan wajar tetap LOLOS walau jev mati',
    h4.ok and len(h4.editan) >= 1, {'ok': h4.ok, 'ditolak': h4.ditolak})
h5 = pipa.periksa(jawab_ngawur, naskah, 'perbaiki ejaan')
cek('4b balasan ngawur tetap DITOLAK walau jev mati', not h5.ok, h5.pesan[:80])

satpam.nilai_balasan = _asli

print()
print('═' * 88)
print(f'  HASIL: {lulus} LULUS / {gagal} GAGAL')
print('═' * 88)
sys.exit(1 if gagal else 0)
