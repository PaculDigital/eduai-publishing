
#  ── Log Revisi berada di dalam OVERLAY tertutup (tinggi=0). Untuk uji MATA,
#  pindahkan elemennya ke wadah terlihat, pakai CSS yang SAMA, data SAMA.
print('pindah & potret:', n("""(() => {
  var e = document.getElementById('kb-log');
  if(!e) return 'ELEMEN HILANG';
  //  tutup overlay, lalu tempelkan log ke body supaya benar-benar terlihat
  var l = document.getElementById('latar-bagikan');
  if (l) l.classList.remove('buka');
  var wadah = document.createElement('div');
  wadah.id = '__panggung';
  wadah.style.cssText = 'background:#F6F7F5;padding:20px;max-width:900px';
  document.body.insertBefore(wadah, document.body.firstChild);
  wadah.appendChild(e);
  e.style.display = 'block';
  e.style.marginTop = '0';
  var r = e.getBoundingClientRect();
  return 'tinggi=' + Math.round(r.height) + ' ikon=' +
    document.querySelectorAll('.kb-ik').length;
})()"""))
time.sleep(2)
res3 = t.tanya('Page.captureScreenshot', format='png')
d3 = res3.get('result', {}).get('data')
if d3:
    p3 = f'{OUT}/17-log-ikon-terlihat.png'
    open(p3, 'wb').write(base64.b64decode(d3))
    print(f'✅ {p3} ({os.path.getsize(p3)} byte)')
else:
    print('potret gagal:', json.dumps(res3)[:200])
