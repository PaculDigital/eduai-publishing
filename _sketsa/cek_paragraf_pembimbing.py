"""PERIKSA paragraf naskah di halaman pembimbing — punya data-berkas/data-nomor?

KENAPA: catatan tersimpan tanpa `teks_asli` & `berkas_id`. JS `pilihParagraf`
    mengisi kedua field itu dari `par.dataset.berkas` dan `par.dataset.nomor`.
    Kalau atributnya TIDAK ADA → field kosong → catatan tanpa tujuan.
    Tapi `ambilKalimat()` harus mengembalikan kalimat; kalau kosong → fungsi
    `pilihParagraf` TIDAK dipanggil (`if(!kalimat) return;`).
"""
import sys

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
import pathlib

from uji_e2e_layar import BASE, Sesi      # noqa: E402

link = pathlib.Path('/tmp/e2e_link.txt').read_text().strip()
s = Sesi()
try:
    s.ke(link, 8)
    print('=== PARAGRAF DI HALAMAN PEMBIMBING ===')
    r = s.js("""
    (function(){
      var ps = document.querySelectorAll('.kertas p');
      var out = [];
      for (var i=0; i<Math.min(ps.length, 8); i++){
        var p = ps[i];
        out.push({
          i: i,
          kelas: p.className,
          berkas: p.dataset.berkas === undefined ? 'TIDAK ADA' : p.dataset.berkas,
          nomor:  p.dataset.nomor === undefined ? 'TIDAK ADA' : p.dataset.nomor,
          panjang: (p.innerText||'').length,
          contoh: (p.innerText||'').slice(0,50)
        });
      }
      return JSON.stringify(out, null, 1);
    })()
    """)
    print(r)

    print()
    print('=== APAKAH data-berkas/nomor ADA di SELURUH elemen .kertas? ===')
    print(s.js("""
    (function(){
      var k = document.querySelector('.kertas');
      var semua = k.querySelectorAll('*');
      var adaBerkas = 0, adaNomor = 0, tag = {};
      semua.forEach(function(e){
        if (e.dataset.berkas !== undefined) adaBerkas++;
        if (e.dataset.nomor  !== undefined) adaNomor++;
        if (e.dataset.berkas !== undefined || e.dataset.nomor !== undefined)
          tag[e.tagName + '.' + String(e.className).slice(0,20)] =
            (tag[e.tagName + '.' + String(e.className).slice(0,20)]||0) + 1;
      });
      return JSON.stringify({adaBerkas: adaBerkas, adaNomor: adaNomor,
                             elemen: tag}, null, 1);
    })()
    """))

    print()
    print('=== UJI: klik paragraf → apakah field terisi? ===')
    print(s.js("""
    (function(){
      var p = document.querySelector('.kertas p');
      if(!p) return 'tidak ada paragraf';
      p.click();
      var ta = document.getElementById('teks-terpilih');
      var bk = document.getElementById('sorot-berkas');
      var np = document.getElementById('sorot-nomor');
      var kt = document.getElementById('kutipan-terpilih');
      return JSON.stringify({
        teks_terpilih: ta ? ta.value.slice(0,60) : 'tidak ada',
        berkas: bk ? bk.value : 'tidak ada',
        nomor: np ? np.value : 'tidak ada',
        kutipan_tampil: kt ? kt.innerText.slice(0,60) : 'tidak ada',
        par_terpilih_ada: !!document.querySelector('.kertas p.par-terpilih')
      }, null, 1);
    })()
    """))
finally:
    s.tutup()
