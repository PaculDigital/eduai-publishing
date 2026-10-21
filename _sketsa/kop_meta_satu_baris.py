import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

# ---- HTML: jadikan SATU baris panjang ----
lama_html = '''      <div class="meta-baris">
        <div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun</div>
        <div class="meta"><b>Web:</b> https://tridarma.id/jemt</div>
        <div class="meta"><b>Email:</b> {{contact_email}}</div>
      </div>'''
baru_html = '''      <div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun &nbsp;•&nbsp; <b>Web:</b> https://tridarma.id/jemt &nbsp;•&nbsp; <b>Email:</b> {{contact_email}}</div>'''
assert lama_html in s, 'HTML tidak ketemu'
s = s.replace(lama_html, baru_html)

# ---- CSS: satu baris rata TENGAH ----
lama_css = '  .kop-detail{margin-top:9px;text-align:justify;}'
baru_css = '  .kop-detail{margin-top:9px;text-align:center;}'
if lama_css not in s:
    lama_css = '  .kop-detail{margin-top:14px;text-align:justify;}'
assert lama_css in s, 'CSS kop-detail tidak ketemu'
s = s.replace(lama_css, baru_css)

# hapus CSS .meta-baris (tidak dipakai lagi)
s = s.replace('  .kop-detail .meta-baris{display:flex;flex-wrap:wrap;gap:6px 30px;margin-top:3px;}\n', '')

f.write_text(s, encoding='utf-8')
print('✓ kop: E-ISSN • Terbit • Web • Email = SATU baris, RATA TENGAH')
