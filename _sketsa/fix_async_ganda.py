import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/verifikasi-loa.html')
s = f.read_text(encoding='utf-8')

# AKAR: Wulan menyisipkan "async" dua kali -> "async async function" = sintaks RUSAK
lama = s
s = s.replace('async async function', 'async function')
n = lama.count('async async function')
f.write_text(s, encoding='utf-8')
print(f'✓ diperbaiki: {n} tempat ("async async" -> "async")')

# cek sisa
print('sisa "async async":', s.count('async async'))
for i, b in enumerate(s.split('\n'), 1):
    if 'async function' in b:
        print(f'   {i}: {b.strip()}')
