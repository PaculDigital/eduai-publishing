
#  ── GULUNG ke Log Revisi, lalu potret bagian itu saja ──
print('gulung:', n("""(() => {
  var e = document.getElementById('kb-log');
  if(!e) return 'ELEMEN HILANG';
  e.scrollIntoView({block:'center'});
  return 'top=' + Math.round(e.getBoundingClientRect().top) +
    ' tinggi=' + Math.round(e.getBoundingClientRect().height) +
    ' display=' + getComputedStyle(e).display;
})()"""))
time.sleep(2)
#  Ambil potret elemen Log Revisi langsung (bukan seluruh halaman).
res2 = t.tanya('Page.captureScreenshot', format='png')
d = res2.get('result', {}).get('data')
if d:
    p = f'{OUT}/16-log-ikon-tampak.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res2)[:200])
