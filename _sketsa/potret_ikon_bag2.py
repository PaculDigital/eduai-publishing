
#  ── 3. cari & buka bagian Log Revisi ────────────────────────────────
print('kandidat tombol Log:', js("""(() => {
  var out=[];
  [].slice.call(document.querySelectorAll('button,a,[role=button],div'))
    .forEach(function(x){
      var t=(x.textContent||'').trim();
      if(/Log Revisi|Riwayat Revisi/i.test(t) && t.length<60) out.push(t);
    });
  return out.slice(0,5).join(' | ');
})()"""))

print('klik:', js("""(() => {
  var x=[].slice.call(document.querySelectorAll('button,a,[role=button],div'))
    .filter(function(y){
      var t=(y.textContent||'').trim();
      return /Log Revisi|Riwayat Revisi/i.test(t) && t.length<60;
    })[0];
  if(!x) return 'TIDAK KETEMU';
  x.click(); return 'diklik';
})()"""))
time.sleep(5)
print('jumlah ikon .kb-ik :', js("document.querySelectorAll('.kb-ik').length"))
print('lencana            :', js("""[].slice.call(document.querySelectorAll('.kb-log-lencana'))
  .map(function(x){return x.textContent.trim();}).join(' | ')"""))
print('tooltip terpasang  :', js("""[].slice.call(document.querySelectorAll('.kb-ik'))
  .map(function(x){return x.getAttribute('data-tip');}).join(' | ')"""))
print('warna ikon (hitung):', js("""(() => {
  var o={};
  [].slice.call(document.querySelectorAll('.kb-ik')).forEach(function(x){
    var c=getComputedStyle(x).color; o[c]=(o[c]||0)+1;
  });
  return JSON.stringify(o);
})()"""))
print('bentuk ikon (href) :', js("""[].slice.call(document.querySelectorAll('.kb-ik use'))
  .map(function(u){return u.getAttribute('href');}).join(' | ')"""))
potret('06-ikon-sungguhan.png')
