"""REKAM: header skema apa yang masuk ke /oo/aset dari browser?

Tempel jejak ke /tmp/oo_aset_jejak.log lalu buka editor.
Jalankan di container: python3 /tmp/rekam_aset.py
"""
p = '/app/app/main.py'
s = open(p).read()

# titik masuk rute /oo/aset
anchor = "async def oo_aset(sisa: str, req: Request):"
if anchor not in s:
    # cari nama fungsi rute aset yang sebenarnya
    import re
    m = re.search(r"async def (oo_aset\w*)\(sisa: str, req: Request\)", s)
    if not m:
        print('FUNGSI RUTE ASET TIDAK KETEMU')
        raise SystemExit(1)
    anchor = m.group(0)

sisip = anchor + """
    try:
        import json as _j, datetime as _d
        open('/tmp/oo_aset_jejak.log', 'a').write(_j.dumps({
            'jam': _d.datetime.now().strftime('%H:%M:%S'),
            'path': str(req.url.path)[:80],
            'xfp': req.headers.get('x-forwarded-proto'),
            'host': req.headers.get('host'),
            'scheme': req.url.scheme,
            'ref': (req.headers.get('referer') or '')[:70],
        }) + chr(10))
    except Exception:
        pass"""

assert anchor in s
open(p, 'w').write(s.replace(anchor, sisip, 1))
print('REKAM DIPASANG di:', anchor[:60])
