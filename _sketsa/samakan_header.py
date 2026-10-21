"""Samakan HEADER halaman verifikasi dengan KOP LoA (persis).

AKAR: header verifikasi-loa.html dibuat terpisah -> logo 56px, brand 19px,
E-ISSN numpang di sub, TIDAK ada 'Tridarma Journal Publishing', TIDAK ada
baris meta (E-ISSN•Terbit•Web•Email), TIDAK ada accent-bar.
TARGET: persis kop LoA (loa-jemt.html) — logo 64px, brand 30px, sub 15px,
pub 13px tengah, meta 11.5px satu baris tengah, accent-bar 4px.
"""
import pathlib, re

D = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa')
loa = (D / 'loa-jemt.html').read_text(encoding='utf-8')
ver = (D / 'verifikasi-loa.html').read_text(encoding='utf-8')

# ══ 1. Ambil URL logo dari LoA (base64 sama) ══
m = re.search(r'<img src="(data:image/png;base64,[^"]+)"', loa)
assert m, 'logo base64 LoA tidak ketemu'
LOGO = m.group(1)
print('✓ logo LoA diambil, panjang', len(LOGO))

# ══ 2. CSS: ganti blok header verifikasi dengan CSS kop LoA ══
CSS_LAMA = re.search(
    r"  /\* ── header ── \*/.*?header \.home:hover\{[^}]*\}\n", ver, re.S)
assert CSS_LAMA, 'CSS header verifikasi tidak ketemu'
CSS_BARU = """  /* ── header — KOP SAMA PERSIS dengan LoA (17 Okt 2026) ── */
  .top-strip{height:10px;background:linear-gradient(90deg,var(--navy) 0%,var(--navy2) 55%,var(--orange) 100%);}
  .kop{background:#fff;padding:16px 20px 10px;}
  .kop-row{display:flex;align-items:center;gap:24px;max-width:960px;margin:0 auto;}
  .kop .logo img{height:64px;width:auto;}
  .kop .ident{flex:1;}
  .kop .ident .brand{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:30px;color:var(--navy);letter-spacing:.5px;line-height:1.1;}
  .kop .ident .brand span{color:var(--orange);}
  .kop .ident .sub{font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;font-size:15px;color:var(--navy2);margin-top:3px;}
  .kop .home{margin-left:auto;font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:13px;
    color:var(--navy2);text-decoration:none;border:1px solid var(--line);padding:8px 16px;border-radius:10px;background:#fff;transition:.2s;white-space:nowrap;}
  .kop .home:hover{border-color:var(--orange);color:var(--orange2);}
  .kop-detail{max-width:960px;margin:9px auto 0;text-align:center;}
  .kop-detail .pub{font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:13px;color:var(--navy);}
  .kop-detail .meta{font-size:11.5px;color:var(--muted);line-height:1.6;}
  .kop-detail .meta b{color:var(--navy);}
  .accent-bar{height:4px;margin:8px auto 0;max-width:888px;
    background:linear-gradient(90deg,var(--orange),var(--gold) 60%,var(--navy2));border-radius:2px;}
"""
ver = ver.replace(CSS_LAMA.group(0), CSS_BARU)
print('✓ CSS header -> kop LoA')

# top-strip lama (8px) dihapus karena sudah ada di CSS baru
ver = ver.replace(
    '  .top-strip{height:8px;background:linear-gradient(90deg,var(--navy) 0%,var(--navy2) 55%,var(--orange) 100%);}\n', '')
print('✓ top-strip lama dibuang (dobel)')

# ══ 3. HTML: ganti <header>...</header> dengan kop LoA ══
HTML_LAMA = re.search(r'<header>.*?</header>\n', ver, re.S)
assert HTML_LAMA, 'HTML header tidak ketemu'
HTML_BARU = f'''<div class="top-strip"></div>

<div class="kop">
  <div class="kop-row">
    <div class="logo"><img src="{LOGO}" alt="Logo Tridarma"></div>
    <div class="ident">
      <div class="brand">TRIDARMA<span>.ID</span></div>
      <div class="sub">Jurnal Ekonomi dan Manajemen Tridarma (JEMT)</div>
    </div>
    <a class="home" href="https://tridarma.id/jemt">← Beranda Jurnal</a>
  </div>
  <div class="kop-detail">
    <div class="pub">Tridarma Journal Publishing</div>
    <div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun &nbsp;•&nbsp; <b>Web:</b> https://tridarma.id/jemt &nbsp;•&nbsp; <b>Email:</b> admin@tridarma.id</div>
  </div>
</div>
<div class="accent-bar"></div>
'''
ver = ver.replace(HTML_LAMA.group(0), HTML_BARU)
# hapus top-strip lama yang berdiri sendiri sebelum header lama (kalau ada)
ver = ver.replace('<body>\n\n<div class="top-strip"></div>\n\n<div class="top-strip"></div>',
                  '<body>\n\n<div class="top-strip"></div>')
print('✓ HTML header -> kop LoA')

(D / 'verifikasi-loa.html').write_text(ver, encoding='utf-8')
print('tersimpan')

# lapor
for i, b in enumerate(ver.split('\n'), 1):
    if 'top-strip' in b or 'class="kop' in b or 'accent-bar' in b:
        print(f'  {i}: {b.strip()[:80]}')
