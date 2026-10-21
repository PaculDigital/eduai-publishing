import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/main.py')
s = f.read_text(encoding='utf-8')

# AKAR: Wulan MENEBAK nama fungsi (_catatan) padahal aslinya catatan(db,user_id,berkas_id)
lama = """    from . import submit_jurnal as _sj                          # noqa: PLC0415
    cat = _sj._catatan(p) if hasattr(_sj, '_catatan') else {}
    riwayat = (cat or {}).get('riwayat') or []"""
baru = """    from . import submit_jurnal as _sj                          # noqa: PLC0415
    cat = _sj.catatan(db, u.id, berkas_id)
    riwayat = (cat or {}).get('riwayat') or []"""
assert lama in s, 'pola tidak ketemu'
s = s.replace(lama, baru)
f.write_text(s, encoding='utf-8')
print('✓ pakai nama BENAR: catatan(db, u.id, berkas_id)')
