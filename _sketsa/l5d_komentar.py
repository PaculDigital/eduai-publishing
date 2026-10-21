"""L5d — PEMBIMBING TULIS KOMENTAR pada paragraf yang disorot → KIRIM.

Field (dari template tinjau.html):
    textarea[name=isi]           → catatan untuk mahasiswa
    hidden[name=teks_asli]       → kutipan paragraf (diisi otomatis saat sorot)
    hidden[name=berkas_id]
    hidden[name=nomor_paragraf]
    form action = /tinjau/<token>/catatan
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402

LINK = pathlib.Path('/tmp/e2e_link.txt')
TEKS = ('Paragraf pembuka ini perlu ditajamkan: rumusan masalah belum '
        'menyebut kesenjangan penelitian. Mohon tambahkan kalimat yang '
        'menjelaskan mengapa penelitian ini penting dan apa yang belum '
        'dijawab penelitian sebelumnya.')


def main() -> int:
    link = LINK.read_text().strip()
    s = Sesi()
    try:
        s.ke(link, 8)
        t = str(s.js('document.body.innerText'))
        cek('L5d0 halaman tinjau terbuka', 'Undangan' not in t, f'{len(t)} kar')

        #  Sorot paragraf 0
        d = json.loads(str(s.js("""
        (function(){
          var p = document.querySelectorAll('.kertas p')[0];
          var r = p.getBoundingClientRect();
          return JSON.stringify({x:Math.round(r.x+10),
                                 y:Math.round(r.y+r.height/2)});
        })()
        """)))
        for jenis in ('mousePressed', 'mouseReleased'):
            s.tab.cmd('Input.dispatchMouseEvent',
                      {'type': jenis, 'x': d['x'], 'y': d['y'],
                       'button': 'left', 'clickCount': 1})
        time.sleep(3)
        info('kutipan terpilih: ' + str(s.js(
            "document.getElementById('kutipan-terpilih')?.innerText?.slice(0,90)")))
        info('teks_asli (hidden): ' + str(s.js(
            "document.getElementById('teks-terpilih')?.value?.slice(0,90)")))
        info('berkas_id: ' + str(s.js(
            "document.getElementById('sorot-berkas')?.value")))

        #  Tulis catatan
        r = s.js(f"""
        (function(){{
          var ta = document.querySelector('#kotak-sorot textarea[name="isi"]')
                || document.querySelector('textarea[name="isi"]');
          if(!ta) return 'TIDAK ADA textarea';
          ta.focus(); ta.value = {json.dumps(TEKS)};
          ta.dispatchEvent(new Event('input',{{bubbles:true}}));
          ta.dispatchEvent(new Event('change',{{bubbles:true}}));
          return 'ok:' + ta.value.length + ' kar';
        }})()
        """, tunggu=0.5)
        info(f'tulis catatan: {r}')
        s.potret('L5d_komentar_tertulis')

        #  Tombol kirim di dalam panel sorot
        info('tombol di panel: ' + str(s.js("""
        Array.from(document.querySelectorAll('#kotak-sorot button, form button'))
          .map(function(b){return (b.id||'-') + ':' + (b.innerText||'').trim().slice(0,18);})
          .join(' | ')
        """)))

        #  Kirim form catatan
        r = s.js("""
        (function(){
          var ta = document.querySelector('textarea[name="isi"]');
          var f = ta.closest('form');
          if(!f) return 'form tidak ketemu';
          var b = f.querySelector('button[type="submit"], button:not([type])');
          if(b){ b.click(); return 'klik tombol: ' + (b.innerText||'').trim(); }
          f.submit(); return 'submit form langsung';
        })()
        """, tunggu=5)
        info(f'kirim catatan: {r}')
        s.potret('L5d2_sesudah_kirim')
        t2 = str(s.js('document.body.innerText'))
        info(f'halaman sesudah kirim: {len(t2)} kar')
    finally:
        print(f'\n       (tab: {s.tid})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
