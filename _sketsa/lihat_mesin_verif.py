import pathlib, re
f = pathlib.Path('/tmp/loa2_x/tridarma-loa/verifikasi-loa.html')
s = f.read_text(encoding='utf-8')
print('=== BARIS SCRIPT / DATA (mesin halaman verifikasi) ===')
baris = s.split('\n')
for i, b in enumerate(baris, 1):
    if any(k in b for k in ['DATABASE_CONTOH', 'function', 'fetch(', 'const ', 'let ', '=>', 'return ', 'TODO', '{{']):
        print(f'{i:4}: {b.strip()[:135]}')
