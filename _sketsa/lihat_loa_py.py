import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/loa.py')
s = f.read_text(encoding='utf-8')
print('== fungsi susun_data & isi contact_wa ==')
mulai = False
for i, baris in enumerate(s.split(chr(10)), 1):
    if 'def susun_data' in baris or 'contact_wa' in baris or 'def isi_template' in baris or 'def setelan' in baris:
        print(f'  {i}: {baris}')
