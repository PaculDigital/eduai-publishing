import pathlib, re

D = pathlib.Path('/opt/data/services/eduai-publishing')
Z = pathlib.Path('/tmp/loa2_x/tridarma-loa')

# ---- 1. Ambil versi BOS (ZIP-2, 15 token) sebagai dasar ----
s = (Z / 'agent/template-loa-jemt-agent.html').read_text(encoding='utf-8')
print('dasar: ZIP-2 agent (15 token) | baris:', s.count(chr(10)))

# ---- 2. PERBAIKAN 1: hapus baris "Chief Editor JEMT," yang berlebih ----
sebelum = s
s = s.replace('        Chief Editor JEMT,\n', '')
print('P1 hapus "Chief Editor JEMT," :', s != sebelum)

# ---- 3. PERBAIKAN 2: blok tanda tangan -> RATA KANAN ----
ganti = [
    # blok .sign: rata kanan + lebar cukup
    ('.sign .box{text-align:center;min-width:250px;}',
     '.sign .box{text-align:right;min-width:265px;}'),
    # nama: margin-top dikecilkan (biar muat 1 halaman) + warna navy
    ('.sign .nama{font-family:\'Plus Jakarta Sans\',sans-serif;font-weight:800;color:var(--navy);font-size:14px;margin-top:64px;border-bottom:2px solid var(--orange);padding-bottom:4px;display:inline-block;min-width:220px;}',
     '.sign .nama{font-family:\'Plus Jakarta Sans\',sans-serif;font-weight:800;color:var(--navy);font-size:14px;margin-top:8px;border-bottom:1.5px solid var(--navy);padding-bottom:2px;display:inline-block;min-width:220px;}'),
    ('.sign .jabatan{font-size:12px;color:var(--muted);margin-top:4px;}',
     '.sign .jabatan{font-size:11.5px;color:var(--muted);margin-top:4px;max-width:265px;margin-left:auto;}'),
]
for lama, baru in ganti:
    if lama in s:
        s = s.replace(lama, baru)
        print('P2 ok:', lama[:45])
    else:
        print('P2 LEWAT (tidak ketemu):', lama[:45])

# ---- 4. PERBAIKAN 3: pasang GAMBAR tanda tangan (di atas nama) ----
# cari baris nama, sisipkan <img> tepat SEBELUMnya
pola = '<div class="nama">{{editor_name}}</div>'
if pola in s:
    s = s.replace(pola, '<img class="ttd" src="tanda-tangan.png" alt="">\n      ' + pola)
    print('P3 gambar tanda tangan dipasang')
else:
    print('P3 LEWAT: pola nama tidak ketemu')

# CSS gambar tanda tangan
if '.sign .ttd{' not in s:
    s = s.replace('.sign .jabatan{', '.sign .ttd{display:block;height:68px;width:auto;margin:2px 0 -10px auto;margin-left:auto;margin-right:0;}\n.sign .jabatan{')
    print('P3 CSS .ttd ditambahkan')

# ---- 5. nomor WA baru ----
s = s.replace('0857-2050-5555', '0851-7813-8514')

# ---- 6. simpan ----
out = D / 'app/templates/loa/loa-jemt.html'
out.write_text(s, encoding='utf-8')

tok = sorted(set(re.findall(r'\{\{\s*([a-zA-Z_]+)\s*\}\}', s)))
print()
print('HASIL: token =', len(tok))
print('   "Chief Editor JEMT," ada?', 'Chief Editor JEMT,' in s, '(harus False)')
print('   gambar ttd ada?', 'tanda-tangan.png' in s)
print('   rata kanan?', 'text-align:right;min-width:265px' in s)
print('   WA lama ada?', '0857-2050-5555' in s, '(harus False)')
