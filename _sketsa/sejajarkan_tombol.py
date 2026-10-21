"""Perbaiki: tombol 'Beranda Jurnal' belum sejajar vertikal dengan logo.
AKAR: .kop-row pakai align-items:center tapi tombol punya margin-left:auto dan
align-self default -> mengikuti baseline blok .ident yang lebih tinggi.
FIX: align-self:center eksplisit pada .kop .home.
"""
import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/verifikasi-loa.html')
s = f.read_text(encoding='utf-8')

lama = "padding:8px 16px;border-radius:10px;background:#fff;transition:.2s;white-space:nowrap;}"
baru = "padding:8px 16px;border-radius:10px;background:#fff;transition:.2s;white-space:nowrap;align-self:center;}"
assert lama in s
s = s.replace(lama, baru)

# pastikan .kop-row benar-benar center
s = s.replace('.kop-row{display:flex;align-items:center;gap:24px;max-width:960px;margin:0 auto;}',
              '.kop-row{display:flex;align-items:center;gap:24px;max-width:960px;margin:0 auto;min-height:64px;}')
f.write_text(s, encoding='utf-8')
print('✓ .home align-self:center + .kop-row min-height:64px')
