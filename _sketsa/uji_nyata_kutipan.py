"""UJI NYATA: cari_semua() — apakah kartu ikut membawa daftar kutipan?"""
import sys
sys.path.insert(0, '/app')
from app.pustaka import cari_semua

hasil = cari_semua('kepuasan kerja kinerja karyawan')
art = hasil.get('artikel') or []
print('artikel:', len(art))
_punya_scite = [a for a in art if a.get('scite')]
_punya_kt = [a for a in art if a.get('kutipan')]
print('punya angka scite :', len(_punya_scite))
print('punya DAFTAR kutipan:', len(_punya_kt))
print()
for a in _punya_kt[:3]:
    sc = a.get('scite') or {}
    kt = a.get('kutipan') or []
    print('•', (a.get('title') or '')[:58])
    print('   angka: Dikutip %s · Didukung %s · Dibantah %s'
          % (sc.get('total'), sc.get('didukung'), sc.get('dibantah')))
    for k in kt[:3]:
        print('     - [%s] %s | %s'
              % (k['jenis'], (k.get('doi') or '')[:40], (k.get('bagian') or '')[:30]))
    print()
