import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

lama = '<div class="qr">[TEMPEL<br>QR CODE<br>VERIFIKASI<br>DI SINI]</div>'
baru = '<div class="qr"><img src="qr-verifikasi.png" alt="QR verifikasi LoA"></div>'
assert lama in s, 'placeholder QR tidak ketemu'
s = s.replace(lama, baru)

# pastikan CSS .qr img pas
if '.qr img' not in s:
    s = s.replace('.verify .qr{', '.verify .qr img{width:100%;height:100%;display:block;border-radius:6px;}\n.verify .qr{')

f.write_text(s, encoding='utf-8')
print('✓ placeholder QR -> gambar QR asli (qr-verifikasi.png)')
print('cek:', 'qr-verifikasi.png' in s, '| .qr img:', '.qr img' in s)
