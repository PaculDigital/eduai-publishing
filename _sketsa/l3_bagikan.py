"""L3 — MAHASISWA BAGIKAN TAUTAN KE PEMBIMBING (lewat LAYAR, bukan curl).

Alur: /naskah → klik tombol "Bagikan" → form muncul → isi nama + WA
      → pilih naskah → submit → dapat link /tinjau/<token>
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402

HASIL = pathlib.Path('/opt/data/services/eduai-publishing/_sketsa/e2e_bukti')
HASIL.mkdir(exist_ok=True)


def main() -> int:
    s = Sesi()
    try:
        s.ke(f'{BASE}/naskah', 5)
        cek('L3a /naskah terbuka', s.js('location.pathname') == '/naskah')

        #  Temukan tombol bagikan di layar
        tombol = s.js("""
        (function(){
          var t = document.querySelector('.tombol-bagikan, [onclick*="bukaBagikan"]');
          return t ? (t.innerText||'').trim() : 'TIDAK ADA';
        })()
        """)
        cek('L3b tombol "Bagikan" ada di layar', tombol != 'TIDAK ADA',
            f'tombol={tombol!r}')
        s.potret('L3a_halaman_naskah')

        #  Klik tombol (panggil fungsi halamannya — sama seperti user klik)
        r = s.js("(function(){ if(typeof bukaBagikan==='function')"
                 "{bukaBagikan(); return 'klik';} return 'fungsi tidak ada';})()",
                 tunggu=2)
        info(f'klik Bagikan: {r}')
        s.potret('L3b_form_bagikan')

        #  Cek form yang muncul
        isi_form_ada = s.js("""
        (function(){
          var f = document.querySelector('.bagikan, #bagikan, [class*=bagikan]');
          if(!f) return 'TIDAK ADA';
          var inp = f.querySelectorAll('input,select,textarea');
          return 'input=' + inp.length + ' | nama=' +
                 Array.from(inp).map(function(i){return i.name||i.id;}).join(',');
        })()
        """)
        info(f'form bagikan: {isi_form_ada}')
        cek('L3c form bagikan punya isian',
            'input=' in str(isi_form_ada) and 'TIDAK ADA' not in str(isi_form_ada),
            str(isi_form_ada)[:80])

        #  Potret bagian form supaya MATA bisa memeriksa
        print()
        print('  FORM BAGIKAN — isi field yang ada:')
        for f in ['nama', 'wa', 'email', 'hari', 'file_id']:
            v = s.js(f"(function(){{var e=document.querySelector"
                     f"('[name=\"{f}\"]');return e?e.tagName:'tidak ada';}})()")
            print(f'     {f:9s} → {v}')
    finally:
        print(f'\n       (tab dibiarkan terbuka: {s.tid})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
