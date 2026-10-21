"""L5 — PEMBIMBING masuk (isi identitas → KLIK ULANG link) → SOROT → KOMENTAR.

⚠️ PELAJARAN (bukan bug aplikasi): halaman undangan MEMANG meminta
    "isi sekali, berikutnya klik ulang link". Wulan hanya submit form
    lalu berhenti → tetap di undangan. Harus: submit → KUNJUNGI ULANG link.
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402

LINK = pathlib.Path('/tmp/e2e_link.txt')


def main() -> int:
    link = LINK.read_text().strip()
    print(f'link: {link}')
    s = Sesi()
    try:
        # ══ L5a. buka + isi identitas (kalau masih diminta) ══════════════
        s.ke(link, 6)
        t = str(s.js('document.body.innerText'))
        if 'Undangan' in t:
            info('halaman undangan → isi identitas')
            s.js("""
            (function(){
              var el = document.querySelector('input[name="identitas"]');
              if(!el) return 'TIDAK ADA';
              el.value = '081234567890';
              el.dispatchEvent(new Event('input',{bubbles:true}));
              el.closest('form').submit();
              return 'kirim';
            })()
            """, tunggu=6)

        # ══ L5b. KLIK ULANG LINK (kunci! sesuai petunjuk halaman) ════════
        print('\n── L5b. KLIK ULANG LINK (seperti petunjuk halaman) ──────')
        s.ke(link, 8)
        t = str(s.js('document.body.innerText'))
        cek('L5b halaman TINJAU terbuka (bukan undangan)',
            'Undangan' not in t, f'{len(t)} kar teks')
        s.potret('L5b_tinjau_masuk')

        #  diag struktur
        info('struktur: ' + str(s.js("""
        (function(){
          return JSON.stringify({
            paragraf: document.querySelectorAll('.kertas p').length,
            bagian: document.querySelectorAll('.kertas .bagian, .kertas .bagian-bab').length,
            teks_panjang: (document.body.innerText||'').length
          });
        })()
        """)))

        # ══ L5c. SOROT paragraf pertama → tulis komentar ═════════════════
        print('\n── L5c. SOROT paragraf + TULIS KOMENTAR ─────────────────')
        d = s.js("""
        (function(){
          var ps = document.querySelectorAll('.kertas p');
          if(!ps.length) return 'TIDAK ADA paragraf';
          var p = ps[0];
          var r = p.getBoundingClientRect();
          return JSON.stringify({x:Math.round(r.x+10), y:Math.round(r.y+r.height/2),
                                 teks:(p.innerText||'').slice(0,60),
                                 nomor:p.dataset.nomor||'-'});
        })()
        """)
        info(f'paragraf-1: {d}')
        if isinstance(d, str) and d.startswith('{'):
            q = json.loads(d)
            for jenis in ('mousePressed', 'mouseReleased'):
                s.tab.cmd('Input.dispatchMouseEvent',
                          {'type': jenis, 'x': q['x'], 'y': q['y'],
                           'button': 'left', 'clickCount': 1})
            time.sleep(3)
            s.potret('L5c_sesudah_sorot')
            #  Apa yang muncul setelah klik?
            muncul = s.js("""
            (function(){
              var semua = [];
              ['.kb','[class*=komentar]','[class*=sorot]','textarea','.pop','.panel']
                .forEach(function(sel){
                  document.querySelectorAll(sel).forEach(function(e){
                    var st = getComputedStyle(e);
                    if(st.display!=='none' && st.visibility!=='hidden' &&
                       e.offsetHeight>0)
                      semua.push(sel + '→' + e.tagName +
                                 (e.id?'#'+e.id:'') + '.' +
                                 String(e.className).slice(0,28));
                  });
                });
              return semua.slice(0,12).join(' | ') || 'tidak ada panel muncul';
            })()
            """)
            info(f'muncul setelah klik: {muncul}')
    finally:
        print(f'\n       (tab: {s.tid})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
