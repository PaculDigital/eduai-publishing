import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = f.read_text(encoding='utf-8')

ganti = [
    # AKAR 1: jangan paksa tinggi halaman (biar isi mengalir wajar)
    ('.page{width:210mm;min-height:297mm;background:#fff;display:flex;flex-direction:column;margin:0 auto;}',
     '.page{width:210mm;background:#fff;display:flex;flex-direction:column;margin:0 auto;}'),
    # AKAR 2: footer jangan ditarik ke dasar halaman
    ('.footer{margin-top:auto;', '.footer{margin-top:18px;'),
    # padatkan kop
    ('.kop{padding:24px 36px 16px;}', '.kop{padding:16px 36px 10px;}'),
    ('.kop-detail{margin-top:14px;text-align:justify;}', '.kop-detail{margin-top:9px;text-align:justify;}'),
    # padatkan judul
    ('.doc-title{text-align:center;padding:26px 40px 6px;}', '.doc-title{text-align:center;padding:14px 40px 4px;}'),
    # padatkan badan
    ('.body{padding:20px 46px;font-size:13.5px;line-height:1.85;text-align:justify;}',
     '.body{padding:12px 46px;font-size:13px;line-height:1.62;text-align:justify;}'),
    # padatkan kotak artikel
    ('border-radius:0 10px 10px 0;padding:16px 20px;margin', 'border-radius:0 10px 10px 0;padding:11px 18px;margin'),
    # padatkan tutup
    ('.tutup{background:#fffbeF;border:1px dashed var(--gold);border-radius:10px;padding:14px 18px;margin-top:16px;font-size:12.5px;color:var(--ink);}',
     '.tutup{background:#fffbeF;border:1px dashed var(--gold);border-radius:10px;padding:9px 16px;margin-top:10px;font-size:12px;color:var(--ink);}'),
    # padatkan kotak verifikasi
    ('.verify{margin:18px 46px 0;background:linear-gradient(135deg,var(--navy),var(--navy2));border-radius:12px;padding:18px 22px;display:flex;gap:20px;alig',
     '.verify{margin:11px 46px 0;background:linear-gradient(135deg,var(--navy),var(--navy2));border-radius:12px;padding:12px 18px;display:flex;gap:16px;alig'),
    ('.verify .qr{width:92px;height:92px;flex:0 0 92px;', '.verify .qr{width:78px;height:78px;flex:0 0 78px;'),
    # tanda tangan
    ('.sign{display:flex;justify-content:flex-end;padding:26px 56px 0;font-size:13px;line-height:1.8;}',
     '.sign{display:flex;justify-content:flex-end;padding:14px 56px 0;font-size:12.5px;line-height:1.55;}'),
    ('.sign .ttd{display:block;height:68px;', '.sign .ttd{display:block;height:58px;'),
    # footer
    ('.footer{margin-top:18px;background:var(--cream);border-top:3px solid var(--orange);padding:14px 36px;',
     '.footer{margin-top:12px;background:var(--cream);border-top:3px solid var(--orange);padding:9px 36px;'),
]
n = 0
for lama, baru in ganti:
    if lama in s:
        s = s.replace(lama, baru); n += 1
    else:
        print('LEWAT:', lama[:60])
f.write_text(s, encoding='utf-8')
print(f'berhasil: {n}/{len(ganti)} aturan dipadatkan')
