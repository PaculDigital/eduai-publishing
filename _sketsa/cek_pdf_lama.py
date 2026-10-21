import fitz, glob, os
print('== semua PDF uji yang masih ada ==')
for p in sorted(glob.glob('/tmp/uji_loa*/loa.pdf')):
    try:
        d = fitz.open(p)
        t = d[0].get_text()
        print(f'  {p}')
        print(f'     hal={d.page_count} | "Chief Editor JEMT," ada? {"Chief Editor JEMT," in t} | WA baru? {"0851-7813-8514" in t} | ttd gambar={len(d[0].get_images())}')
    except Exception as e:
        print(f'  {p} ERR {e}')
