"""L3d-L4 — ISI FORM BAGIKAN (selektor BENAR: #kb-*) lalu buka halaman pembimbing.

⚠️ PELAJARAN: selektor awal Wulan pakai `[name="wa"]` → TIDAK ADA.
    Form asli memakai ID: #kb-nama #kb-wa #kb-naskah #kb-hari, tombol #kb-lanjut.
    (Bukan bug aplikasi — Wulan salah baca.)

Alur 2 TAHAP (karena ada konfirmasi):
    isi → #kb-lanjut (kbKeKonfirmasi) → tahap konfirmasi → tombol buat tautan
"""
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402


def isi_id(s, dom_id, nilai):
    expr = f"""
    (function(){{
      var el = document.getElementById({json.dumps(dom_id)});
      if(!el) return 'TIDAK ADA';
      el.focus();
      el.value = {json.dumps(nilai)};
      el.dispatchEvent(new Event('input',{{bubbles:true}}));
      el.dispatchEvent(new Event('change',{{bubbles:true}}));
      return 'ok(' + el.value + ')';
    }})()
    """
    return s.js(expr, tunggu=0.4)


def main() -> int:
    s = Sesi()
    try:
        s.ke(f'{BASE}/naskah', 5)
        s.js("(function(){ if(typeof bukaBagikan==='function')"
             "bukaBagikan(); })()", tunggu=2)

        print('── L3d. ISI FORM (selektor #kb-*) ────────────────────────')
        info('nama  : ' + str(isi_id(s, 'kb-nama', 'Prof. Uji Pembimbing')))
        info('wa    : ' + str(isi_id(s, 'kb-wa', '081234567890')))

        #  pilih naskah_bos.docx
        r = s.js("""
        (function(){
          var sel = document.getElementById('kb-naskah');
          if(!sel) return 'select TIDAK ADA';
          var t = Array.from(sel.options).find(function(o){
            return o.text.indexOf('naskah_bos') >= 0; });
          if(!t) return 'opsi naskah_bos tidak ada: ' +
                 Array.from(sel.options).map(function(o){return o.text.slice(0,20);}).join(' ; ');
          sel.value = t.value;
          sel.dispatchEvent(new Event('change',{bubbles:true}));
          return 'dipilih file_id=' + t.value + ' (' + t.text + ')';
        })()
        """, tunggu=0.5)
        info(f'naskah: {r}')
        s.potret('L3d2_form_terisi')

        print('\n── L3e. KLIK "Lanjut" → TAHAP KONFIRMASI ────────────────')
        r = s.js("(function(){var b=document.getElementById('kb-lanjut');"
                 "if(!b) return 'TIDAK ADA'; b.click(); return 'klik';})()",
                 tunggu=2)
        info(f'klik Lanjut: {r}')
        #  Periksa tahap konfirmasi muncul
        st = s.js("""
        (function(){
          var k = document.getElementById('kb-tahap-konfirmasi');
          var i = document.getElementById('kb-tahap-isi');
          return 'isi=' + (i?getComputedStyle(i).display:'-') +
                 ' konfirmasi=' + (k?getComputedStyle(k).display:'-') +
                 ' | ringkas=' + (document.getElementById('kb-r-nama')||{}).innerText;
        })()
        """)
        info(f'tahap: {st}')
        cek('L3e tahap KONFIRMASI muncul', 'konfirmasi: block' in str(st) or
            'konfirmasi: flex' in str(st), str(st)[:90])
        s.potret('L3e2_konfirmasi')

        #  Cari tombol pembuat tautan (bukan "Lanjut")
        btns = s.js("""
        Array.from(document.querySelectorAll('#kb-tahap-konfirmasi button'))
          .map(function(b){return b.id + ':' + (b.innerText||'').trim();}).join(' | ')
        """)
        info(f'tombol konfirmasi: {btns}')

        print('\n── L3f. KLIK tombol BUAT TAUTAN ─────────────────────────')
        r = s.js("""
        (function(){
          var btns = Array.from(document.querySelectorAll('#kb-tahap-konfirmasi button'));
          var b = btns.find(function(x){
            var t=(x.innerText||'').trim().toLowerCase();
            return t.indexOf('buat')>=0 || t.indexOf('ya')>=0 || t.indexOf('kirim')>=0; });
          if(!b) return 'TIDAK ADA';
          b.click(); return 'klik:' + b.id;
        })()
        """, tunggu=5)
        info(f'klik buat tautan: {r}')
        s.potret('L3f_hasil_tautan')

        teks = str(s.js('document.body.innerText'))
        m = re.search(r'(https?://[^\s\)]*?/tinjau/[A-Za-z0-9_\-]+)', teks) or \
            re.search(r'/tinjau/([A-Za-z0-9_\-]{6,})', teks)
        link = m.group(0) if m else ''
        if link and link.startswith('/'):
            link = BASE + link
        cek('L3f link /tinjau/<token> didapat', bool(link), (link or teks[:120])[:90])
        if link:
            pathlib.Path('/tmp/e2e_link.txt').write_text(link)
            info(f'LINK: {link}')

        print('\n── L4. BUKA SEBAGAI PEMBIMBING (TANPA login) ────────────')
        if not link:
            return 1
        s.ke(link, 7)
        t = str(s.js('document.body.innerText'))
        s.potret('L4_halaman_pembimbing')
        cek('L4a halaman pembimbing terbuka', len(t) > 300, f'{len(t)} kar')
        cek('L4b nama pembimbing tampil', 'Prof. Uji' in t,
            [ln for ln in t.split('\n') if 'Prof' in ln][:2])
        cek('L4c naskah tampil', 'GORAS' in t.upper() or 'KUALITAS' in t.upper(),
            [ln for ln in t.split('\n') if 'GORAS' in ln.upper()][:2])
        n = s.js("document.querySelectorAll('.kertas p, [data-nomor]').length")
        info(f'paragraf naskah di layar: {n}')
        pathlib.Path('/tmp/e2e_teks_pembimbing.txt').write_text(t)
    finally:
        print(f'\n       (tab: {s.tid})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
