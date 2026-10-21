import re, zipfile
from pathlib import Path
P = Path('/app/uploads/6/349508cb13697288.docx')
with zipfile.ZipFile(P) as z:
    doc = z.read('word/document.xml').decode('utf-8')
pars = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc, re.S)
print(f'total paragraf: {len(pars)}')
for i in range(170, 180):
    t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', pars[i])).strip()
    print(f'  {i:>3}| {t[:80]!r}')
print()
print('── cari SEMUA judul berpola N.N di paragraf 700-822 ──')
for i in range(700, min(822, len(pars))):
    t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', pars[i])).strip()
    if re.match(r'^\d+\.\d+\s+\S', t) and len(t) < 90:
        print(f'  {i:>3}| {t[:70]!r}')
