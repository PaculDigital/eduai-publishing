import pathlib

p = pathlib.Path('/opt/data/services/eduai-publishing/app/gambar.py')
s = p.read_text()

#  GARIS/SEBAR: judul pakai _font_muat
s = s.replace("""    f_judul = _font(40, True)
    f_kecil = _font(19)
    f_angka = _font(20, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 108), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    bawah = min(min(nilai), 0)""",
"""    f_kecil = _font(19)
    f_angka = _font(20, True)

    f_judul, uk = _font_muat(judul, X1 - X0, 40)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 14), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    bawah = min(min(nilai), 0)""")

#  HISTOGRAM
s = s.replace("""    f_judul = _font(40, True)
    f_kecil = _font(18)
    f_angka = _font(18, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 108), f'Satuan: {satuan}', font=f_kecil, fill=ABU)""",
"""    f_kecil = _font(18)
    f_angka = _font(18, True)

    f_judul, uk = _font_muat(judul, X1 - X0, 40)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 14), f'Satuan: {satuan}', font=f_kecil, fill=ABU)""")

#  PAI
s = s.replace("""    f_judul = _font(38, True)
    f_kecil = _font(20)
    f_isian = _font(19, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 106), f'Satuan: {satuan}', font=f_kecil, fill=ABU)""",
"""    f_kecil = _font(20)
    f_isian = _font(19, True)

    f_judul, uk = _font_muat(judul, X1 - X0, 38)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 12), f'Satuan: {satuan}', font=f_kecil, fill=ABU)""")

p.write_text(s)
print('✅ judul pakai _font_muat di batang/garis/histogram/pai')
