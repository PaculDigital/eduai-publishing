import pathlib
D = pathlib.Path('/opt/data/services/eduai-publishing')
f = D / 'app/templates/loa/verifikasi-loa.html'
s = f.read_text(encoding='utf-8')

lama = '''function cariLoA(nomor) {
  // TODO: ganti dengan fetch ke API/database OJS
  return DATABASE_CONTOH[nomor.trim()] || null;
}'''
baru = '''async function cariLoA(nomor) {
  // data LoA diambil dari server EduAi (jembatan /api/loa/cek)
  try {
    const r = await fetch('/api/loa/cek?no=' + encodeURIComponent(nomor.trim()));
    const j = await r.json();
    return (j && j.ok) ? j.data : null;
  } catch (e) {
    return null;
  }
}'''
assert lama in s, 'pola cariLoA tidak ketemu'
s = s.replace(lama, baru)
print('✓ cariLoA -> fetch /api/loa/cek')

# semua pemanggil cariLoA jadi await
n = s.count('cariLoA(')
s = s.replace('= cariLoA(', '= await cariLoA(')

# fungsi pemanggilnya harus async
for fn in ['function verifikasi(){', 'function show(){']:
    if fn in s:
        s = s.replace(fn, 'async ' + fn)
        print('✓', fn, '-> async')

f.write_text(s, encoding='utf-8')
print()
print('sisa DATABASE_CONTOH :', 'DATABASE_CONTOH' in s)
print('fetch dipakai        :', "fetch('/api/loa/cek" in s)
print('async verifikasi     :', 'async function verifikasi(){' in s)
print('await cariLoA        :', 'await cariLoA(' in s)
