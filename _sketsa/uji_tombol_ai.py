"""UJI TOMBOL AI — setelah identitas diisi (pembimbing tanpa akun).

Alur nyata:
  1. POST /tinjau/{token}/identitas  (isi nomor HP)
  2. GET  /tinjau/{token}            → HARUS tampil tombol "Periksa dengan AI"
  3. POST /tinjau/{token}/periksa-ai → tanpa akun HARUS 303 /daftar
"""
import sys

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

TOKEN = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'

with TestClient(app) as c:
    print('1. SEBELUM isi identitas:')
    r0 = c.get(f'/tinjau/{TOKEN}', follow_redirects=False)
    print('   HTTP', r0.status_code)
    print('   ada "Undangan Kolaborasi" :', 'Undangan Kolaborasi' in r0.text)
    print('   ada "Periksa dengan AI"  :', 'Periksa dengan AI' in r0.text)
    print()

    print('2. ISI IDENTITAS (POST /identitas):')
    r1 = c.post(f'/tinjau/{TOKEN}/identitas',
                data={'identitas': '081234567890'},
                follow_redirects=False)
    print('   HTTP', r1.status_code, '| location:', r1.headers.get('location'))
    print()

    print('3. SESUDAH isi identitas:')
    r2 = c.get(f'/tinjau/{TOKEN}', follow_redirects=False)
    print('   HTTP', r2.status_code, '| ukuran:', len(r2.text))
    for tanda in ('Periksa dengan AI', 'Buka di editor',
                  'Undangan Kolaborasi', 'Ringkasan hasil masuk'):
        print(f'   {"ADA " if tanda in r2.text else "TIDAK"} — {tanda!r}')
    print()

    print('4. KLIK "Periksa dengan AI" (tanpa akun):')
    r3 = c.post(f'/tinjau/{TOKEN}/periksa-ai',
                data={'berkas_id': '1'}, follow_redirects=False)
    print('   HTTP', r3.status_code, '| location:', r3.headers.get('location'))
    if r3.status_code == 303 and '/daftar' in (r3.headers.get('location') or ''):
        print('   ✅ BENAR: pembimbing tanpa akun diarahkan DAFTAR dulu')
    else:
        print('   ⚠️ TIDAK sesuai harapan')
