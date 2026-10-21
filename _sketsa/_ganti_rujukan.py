import re
import pathlib

p = pathlib.Path('/opt/data/services/eduai-publishing/_sketsa/uji_3_kasus_sulit.py')
s = p.read_text()
ganti = [
    ("h = cari_paragraf(naskah, asli)",
     "h = cari_paragraf(naskah_kembar, paras_kembar[0])"),
    ("h2 = cari_paragraf(naskah, paras[1])",
     "h2 = cari_paragraf(naskah_kembar, paras_kembar[1])"),
    ("bag1 = '\\n\\n'.join(paras[0:2])",
     "bag1 = '\\n\\n'.join(paras_unik[0:2])"),
    ("bag2 = '\\n\\n'.join(paras[2:4])",
     "bag2 = '\\n\\n'.join(paras_unik[2:4])"),
    ("kutip_b2 = paras[2]", "kutip_b2 = paras_unik[2]"),
    ("kutip_b1 = paras[0]", "kutip_b1 = paras_unik[0]"),
    ("asli = paras[0]", "asli = paras_unik[0]"),
]
for a, b in ganti:
    if a not in s:
        print(f'  ! TIDAK KETEMU: {a[:55]}')
    s = s.replace(a, b)
p.write_text(s)
print('sisa rujukan paras[ yang belum diganti:', re.findall(r'\bparas\[\d', s))
print('ok')
