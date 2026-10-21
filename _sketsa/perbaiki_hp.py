"""Perbaikan TAMPILAN HP halaman verifikasi.

AKAR TERUKUR (CDP 390px):
  .kop-row butuh 697px -> meluber 307px; brand & tombol 'Beranda Jurnal' terpotong.
SEBAB:
  ① tidak ada @media(max-width:...) untuk kop (hanya .card & footer)
  ② CSS kop disalin dari LoA (kertas A4 210mm) tanpa penyesuaian layar
OBAT (bukan tambalan):
  · HP: .kop-row jadi flex-wrap + logo/brand/tombol bertumpuk rapi
  · brand 30px -> 24px, sub 15px -> 13px
  · meta: potong 'Terbit 6 kali...' ke baris sendiri, font 10.5px
  · accent-bar margin 16px
  · cegah overflow horizontal: html,body{overflow-x:hidden}
"""
import pathlib, re

f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/verifikasi-loa.html')
s = f.read_text(encoding='utf-8')

# ══ 1. CSS HP untuk kop — sisipkan SEBELUM @media print ══
MEDIA_HP = """
  /* ── KOP di layar HP (17 Okt 2026) ─────────────────────────────────────
     AKAR: .kop-row butuh 697px pada layar 390px -> brand & tombol terpotong.
     Kop LoA dibuat untuk kertas A4, jadi di HP harus BERTUMPUK ke bawah. */
  @media(max-width:640px){
    .kop{padding:12px 14px 8px;}
    .kop-row{flex-wrap:wrap;gap:10px;min-height:0;}
    .kop .logo img{height:52px;}
    .kop .logo{flex:0 0 auto;}
    .kop .ident{flex:1 1 100%;order:3;}
    .kop .ident .brand{font-size:24px;}
    .kop .ident .sub{font-size:12.5px;line-height:1.4;}
    .kop .home{margin-left:auto;align-self:center;font-size:11.5px;padding:7px 12px;order:2;}
    .kop-detail{margin-top:8px;}
    .kop-detail .pub{font-size:12px;}
    .kop-detail .meta{font-size:10px;line-height:1.75;}
    .kop-detail .meta .pisah{display:block;height:0;}
    .accent-bar{margin:7px 14px 0;max-width:none;}
  }
  @media(max-width:380px){
    .kop .ident .brand{font-size:21px;}
    .kop .logo img{height:44px;}
  }

"""
lama_print = '  @media print{.hero,.card .card-body .field,.hint,header .home{display:none;}}'
assert lama_print in s, 'penanda @media print tidak ketemu'
s = s.replace(lama_print, MEDIA_HP + lama_print)
print('✓ CSS HP kop disisipkan')

# ══ 2. cegah geser ke samping ══
s = s.replace("body{font-family:'Inter',Arial,sans-serif;color:var(--ink);background:var(--cream);line-height:1.7;}",
              "body{font-family:'Inter',Arial,sans-serif;color:var(--ink);background:var(--cream);line-height:1.7;overflow-x:hidden;}")
print('✓ overflow-x:hidden')

# ══ 3. meta: beri titik potong agar tidak jadi satu baris panjang di HP ══
lama_meta = '<div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun &nbsp;•&nbsp; <b>Web:</b> https://tridarma.id/jemt &nbsp;•&nbsp; <b>Email:</b> admin@tridarma.id</div>'
baru_meta = ('<div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun'
             '<span class="pisah"></span> &nbsp;•&nbsp; <b>Web:</b> https://tridarma.id/jemt &nbsp;•&nbsp; '
             '<b>Email:</b> admin@tridarma.id</div>')
assert lama_meta in s, 'baris meta tidak ketemu'
s = s.replace(lama_meta, baru_meta)
print('✓ titik potong meta HP')

f.write_text(s, encoding='utf-8')
print('tersimpan')
