import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

# lihat CSS yang mengatur jarak vertikal
print('== CSS pengatur jarak (padding/margin/min-height) ==')
for i, b in enumerate(s.split(chr(10)), 1):
    if any(k in b for k in ['.page{', 'min-height', 'padding:', 'margin-top', '@page', '.body{', '.sign{', '.footer{', '.verifikasi', '.catatan', '.artikel{']):
        print(f'  {i}: {b.strip()[:150]}')
