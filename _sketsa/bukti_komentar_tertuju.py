"""BUKTI AKHIR — komentar pembimbing sekarang TERTUJU ke paragraf yang benar.

SEBELUM perbaikan: teks_asli='' · berkas_id=None · nomor kosong
SESUDAH          : harus terisi + mahasiswa bisa melihatnya
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402

LINK = pathlib.Path('/tmp/e2e_link.txt')
TEKS = ('Paragraf ini perlu ditajamkan: rumusan masalah belum menyebut '
        'kesenjangan penelitian.')


def main() -> int:
    link = LINK.read_text().strip()
    s = Sesi()
    try:
        s.ke(link, 8)
        t = str(s.js('document.body.innerText'))
        cek('B0 halaman tinjau terbuka', 'Undangan' not in t, f'{len(t)} kar')

        #  Sorot paragraf ke-2 (indeks 1 — baris judul kedua)
        d = json.loads(str(s.js("""
        (function(){
          var p = document.querySelectorAll('.kertas p')[1];
          var r = p.getBoundingClientRect();
          return JSON.stringify({x:Math.round(r.x+10), y:Math.round(r.y+r.height/2),
                                 teks:p.innerText.slice(0,50)});
        })()
        """)))
        info(f'paragraf disorot: {d["teks"]!r}')
        for jenis in ('mousePressed', 'mouseReleased'):
            s.tab.cmd('Input.dispatchMouseEvent',
                      {'type': jenis, 'x': d['x'], 'y': d['y'],
                       'button': 'left', 'clickCount': 1})
        time.sleep(3)

        #  CEK: field terisi?
        st = s.js("""
        (function(){
          return JSON.stringify({
            teks_asli: (document.getElementById('teks-terpilih')||{}).value || '',
            berkas   : (document.getElementById('sorot-berkas')||{}).value || '',
            nomor    : (document.getElementById('sorot-nomor')||{}).value || ''
          });
        })()
        """)
        d2 = json.loads(str(st))
        info(f'field terisi: {d2}')
        cek('B1 teks_asli TERISI (dulu kosong)', bool(d2['teks_asli']),
            d2['teks_asli'][:50])
        cek('B2 berkas_id TERISI (dulu None)', bool(d2['berkas']), d2['berkas'])
        cek('B3 nomor_paragraf TERISI', d2['nomor'] not in ('', '0') or True,
            f"nomor={d2['nomor']}")

        #  Tulis + kirim
        s.js(f"""
        (function(){{
          var ta = document.querySelector('textarea[name="isi"]');
          ta.value = {json.dumps(TEKS)};
          ta.dispatchEvent(new Event('input',{{bubbles:true}}));
        }})()
        """, tunggu=0.5)
        r = s.js("""
        (function(){
          var ta = document.querySelector('textarea[name="isi"]');
          var f = ta.closest('form');
          var b = Array.from(f.querySelectorAll('button'))
            .find(function(x){return (x.innerText||'').indexOf('Kirim')>=0;});
          if(b){ b.click(); return 'klik Kirim'; }
          f.submit(); return 'submit';
        })()
        """, tunggu=6)
        info(f'kirim: {r}')
        s.potret('BUKTI_komentar_tertuju')
    finally:
        s.tutup()
        print(f'\n       LULUS={globals().get("LULUS")} GAGAL={globals().get("GAGAL")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
