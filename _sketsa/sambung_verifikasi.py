import pathlib, re, json

D = pathlib.Path('/opt/data/services/eduai-publishing')
Z = pathlib.Path('/tmp/loa2_x/tridarma-loa')

# ══ 1. Ambil JSON contoh (untuk tahu bentuk data) ══
contoh = json.loads((Z / 'agent/contoh-data-loa.json').read_text(encoding='utf-8'))
print('bentuk data contoh:')
for k, v in contoh.items():
    print(f'   {k} = {str(v)[:55]}')

# ══ 2. Halaman verifikasi: ganti DATABASE_CONTOH -> fetch API ══
s = (Z / 'verifikasi-loa.html').read_text(encoding='utf-8')

# cari blok DATABASE_CONTOH ... sampai sebelum function esc
m = re.search(r'const DATABASE_CONTOH = \{.*?\n\};\n', s, re.S)
print()
print('blok DATABASE_CONTOH ditemukan:', bool(m), '| panjang:', len(m.group(0)) if m else 0)
if m:
    s = s[:m.start()] + '// data diambil dari server EduAi (bukan contoh lagi)\n' + s[m.end():]

# ganti fungsi cariLoA
lama = '''function cariLoA(nomor) {
      // TODO: ganti dengan fetch ke API/database OJS
      return DATABASE_CONTOH[nomor.trim()] || null;'''
baru = '''async function cariLoA(nomor) {
      // data LoA diambil dari server EduAi (jembatan /api/loa/cek)
      try {
        const r = await fetch('/api/loa/cek?no=' + encodeURIComponent(nomor.trim()));
        const j = await r.json();
        return j && j.ok ? j.data : null;
      } catch (e) {
        return null;
      }'''
if lama in s:
    s = s.replace(lama, baru)
    print('cariLoA: diganti ke fetch API')
else:
    print('!! pola cariLoA TIDAK ketemu — perlu lihat manual')

# verifikasi() harus async
s = s.replace('function verifikasi(){', 'async function verifikasi(){')
s = s.replace('const d = cariLoA(nomor);', 'const d = await cariLoA(nomor);')
# panggilan lain (dari ?no=) juga
s = re.sub(r'(\bd = )cariLoA\(', r'\1await cariLoA(', s)
if 'async function show(){' not in s and 'function show(){' in s:
    s = s.replace('function show(){', 'async function show(){')

(D / 'app/templates/loa/verifikasi-loa.html').write_text(s, encoding='utf-8')
print('halaman verifikasi tersimpan ke EduAi')

# cek sisa
print()
print('sisa DATABASE_CONTOH:', 'DATABASE_CONTOH' in s)
print('fetch dipakai     :', "fetch('/api/loa/cek" in s)
print('baris             :', s.count(chr(10)))
