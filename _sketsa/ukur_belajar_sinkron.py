"""UKUR (Rp 0): apakah MODE BELAJAR sudah sinkron dengan sistem baru?

Pertanyaan Bos: "Cek apakah fitur belajar juga sudah sinkron dengan sistem
baru ini?"

Yang disebut "sistem baru" (14 Okt):
  · Surveyor Jev = pintu deteksi bab (`versi._deteksi_bagian`)
  · `rapi_bab()` = menyatukan penulisan bab
  · Peta Jev tersimpan (`peta_json`) dipakai ulang

Diuji dengan data NYATA, bukan bacaan kode.
"""
import sys

sys.path.insert(0, '/app')

OK, TIDAK = [], []


def cek(nama, benar, bukti=''):
    (OK if benar else TIDAK).append(nama)
    print(('  OK  ' if benar else '  X   ') + nama +
          (('  [%s]' % bukti) if bukti else ''))


print('=' * 66)
print('  1. APAKAH belajar.py PAKAI PINTU LAYAR SURVEYOR JEV?')
print('=' * 66)
print('     (deteksi bab = pintu yang dilihat user; sistem baru masuk di sini)')
print()
from app import belajar as B                       # noqa: E402
from app import versi as V                         # noqa: E402

# a) apakah bab_terdeteksi pakai versi.deteksi_bab?
src = open('/app/app/belajar.py', encoding='utf-8').read()
cek('bab_terdeteksi() pakai versi.deteksi_bab',
    'from .versi import deteksi_bab' in src)
cek('teks_bab() pakai _deteksi_bagian (pintu Jev)',
    'versi.ambil_bab, deteksi_bab, _deteksi_bagian' in src or
    '_deteksi_bagian(naskah)' in src)

print()
print('=' * 66)
print('  2. APAKAH deteksi_bab (dipakai belajar) SUDAH jalur Jev?')
print('=' * 66)
import inspect                                     # noqa: E402
sumber = inspect.getsource(V.deteksi_bab)
cek('deteksi_bab memanggil surveyor Jev / _deteksi_bagian?',
    '_deteksi_bagian' in sumber or 'peta3' in sumber or 'surveyor' in sumber,
    'panjang fungsi: %d char' % len(sumber))
print()
print('  ------ isi deteksi_bab (20 baris pertama) ------')
for ln in sumber.splitlines()[:20]:
    print('   ' + ln)

print()
print('=' * 66)
print('  3. APAKAH belajar.py punya PENULIS ROMAWI SENDIRI (kembar)?')
print('=' * 66)
cek('_romawi_ke_angka() ADA di belajar.py',
    hasattr(B, '_romawi_ke_angka'))
cek('_nomor_bab_dari_section() ADA di belajar.py',
    hasattr(B, '_nomor_bab_dari_section'))
cek('_angka_romawi() ADA di belajar.py', hasattr(B, '_angka_romawi'))
print()
print('   ⚠️  PEMBANDING: rapi_bab() BARU ada di pembimbing.py')
from app.pembimbing import rapi_bab                # noqa: E402
print('   rapi_bab("BAB III") = %r' % rapi_bab('BAB III'))
print('   rapi_bab("bab iii") = %r' % rapi_bab('bab iii'))
print()
print('   UJI SILANG — apakah penulis romawi belajar.py sepakat dgn rapi_bab?')
for masuk in ('BAB I', 'BAB II', 'BAB III', 'BAB 3', 'bab iii', 'BAB IV'):
    lama = B._nomor_bab_dari_section(masuk)
    baru = rapi_bab(masuk)
    sama = (str(lama) if lama is not None else '') == baru
    print('     %-10r belajar=%-5s rapi_bab=%-5s %s'
          % (masuk, lama, baru, 'sepakat' if sama else 'BEDA'))

print()
print('=' * 66)
print('  4. UJI NYATA — naskah produksi: berapa bab terbaca?')
print('=' * 66)
import sqlite3                                     # noqa: E402
con = sqlite3.connect('/app/data/eduai.db')
r = con.execute('select peta_json from profil_dokumen where file_id=81'
                ).fetchone()
if r and r[0]:
    import json                                    # noqa: E402
    d = json.loads(r[0])
    bab_peta = sorted({str(x.get('bab') or '') for x in (d.get('daftar') or [])})
    print('   peta Jev fid=81: bab = %s' % bab_peta)
else:
    print('   (peta fid=81 tidak ada)')
con.close()

print()
print('=' * 66)
print('  5. KESIMPULAN')
print('=' * 66)
print('  OK  : %d' % len(OK))
print('  X   : %d' % len(TIDAK))
for t in TIDAK:
    print('     X', t)
