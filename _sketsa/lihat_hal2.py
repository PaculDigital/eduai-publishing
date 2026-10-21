import fitz
d = fitz.open('/tmp/uji_loa22/loa.pdf')
print('HALAMAN:', d.page_count)
for i in range(d.page_count):
    t = d[i].get_text()
    print(f'--- hal {i+1}: {len(t)} kar ---')
    print('  akhir:', repr(t[-200:]))
    print('  ada WA?', '0851-7813-8514' in t, '| ada footer?', 'Tridarma Journal Publishing' in t)
