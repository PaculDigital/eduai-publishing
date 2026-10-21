import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

# ---- HTML: 3 baris meta -> 3 KOLOM sejajar ----
lama_html = '''      <div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun</div>
      <div class="meta"><b>Web:</b> https://tridarma.id/jemt &nbsp;•&nbsp; <b>Email:</b> {{contact_email}}</div>'''
baru_html = '''      <div class="meta-baris">
        <div class="meta"><b>E-ISSN:</b> 3163-608X &nbsp;•&nbsp; Terbit 6 kali dalam setahun</div>
        <div class="meta"><b>Web:</b> https://tridarma.id/jemt</div>
        <div class="meta"><b>Email:</b> {{contact_email}}</div>
      </div>'''
assert lama_html in s, 'HTML meta tidak ketemu'
s = s.replace(lama_html, baru_html)
print('✓ HTML: 3 kolom meta')

# ---- CSS: baris meta jadi 3 kolom sejajar ----
lama_css = '  .kop-detail .meta{font-size:11.5px;color:var(--muted);margin-top:3px;line-height:1.6;}'
baru_css = ('  .kop-detail .meta-baris{display:flex;flex-wrap:wrap;gap:6px 30px;margin-top:3px;}\n'
            '  .kop-detail .meta{font-size:11.5px;color:var(--muted);line-height:1.6;}')
assert lama_css in s, 'CSS meta tidak ketemu'
s = s.replace(lama_css, baru_css)
print('✓ CSS: meta-baris flex (sejajar)')

f.write_text(s, encoding='utf-8')
print('selesai')
