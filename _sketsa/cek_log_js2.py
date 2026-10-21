
print('5. HTML baris (kg 350 kar):')
print('  ', str(nilai("""(async () => {
  await kbMuatLog();
  var e = document.getElementById('kb-log-baris');
  return e ? e.innerHTML.slice(0,350) : 'KOSONG';})()"""))[:420])
print('6. jumlah .kb-log-baris :', nilai("document.querySelectorAll('.kb-log-baris').length"))
print('7. kbIkonSvg ada? :', nilai("typeof kbIkonSvg"))
print('8. kbBarisCari ada? :', nilai("typeof kbBarisCari"))
