import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

ganti = [
    #  baris "Demikian..." + catatan keaslian → lebih rapat
    ('.body{padding:12px 46px;font-size:13px;line-height:1.62;text-align:justify;}',
     '.body{padding:10px 46px;font-size:12.5px;line-height:1.5;text-align:justify;}'),
    #  kop lebih rapat
    ('.kop{padding:16px 36px 10px;}', '.kop{padding:12px 36px 8px;}'),
    ('.doc-title{text-align:center;padding:14px 40px 4px;}', '.doc-title{text-align:center;padding:10px 40px 3px;}'),
    ('.doc-title h1{font-family:\'Plus Jakarta Sans\',sans-serif;font-weight:800;font-size:23px;color:var(--navy);margin-top:14px;letter-spacing:.3px;}',
     '.doc-title h1{font-family:\'Plus Jakarta Sans\',sans-serif;font-weight:800;font-size:21px;color:var(--navy);margin-top:9px;letter-spacing:.3px;}'),
    #  kotak verifikasi lebih rapat
    ('.verify{margin:11px 46px 0;background:linear-gradient(135deg,var(--navy),var(--navy2));border-radius:12px;padding:12px 18px;display:flex;gap:16px;alig',
     '.verify{margin:8px 46px 0;background:linear-gradient(135deg,var(--navy),var(--navy2));border-radius:12px;padding:10px 16px;display:flex;gap:14px;alig'),
    ('.verify .qr{width:78px;height:78px;flex:0 0 78px;', '.verify .qr{width:68px;height:68px;flex:0 0 68px;'),
    #  tanda tangan lebih rapat
    ('.sign{display:flex;justify-content:flex-end;padding:14px 56px 0;font-size:12.5px;line-height:1.55;}',
     '.sign{display:flex;justify-content:flex-end;padding:9px 56px 0;font-size:12px;line-height:1.45;}'),
    ('.sign .ttd{display:block;height:58px;', '.sign .ttd{display:block;height:50px;'),
    #  footer lebih rapat
    ('.footer{margin-top:12px;background:var(--cream);border-top:3px solid var(--orange);padding:9px 36px;',
     '.footer{margin-top:8px;background:var(--cream);border-top:3px solid var(--orange);padding:7px 36px;'),
]
n = 0
for lama, baru in ganti:
    if lama in s:
        s = s.replace(lama, baru); n += 1
    else:
        print('LEWAT:', lama[:55])
f.write_text(s, encoding='utf-8')
print(f'padatkan lagi: {n}/{len(ganti)}')
