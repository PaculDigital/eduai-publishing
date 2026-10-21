"""Diagnosa: posisi judul BAB asli di dokumen uji (baca .docx mentah, Rp 0)."""
import glob
import re
import zipfile

p = glob.glob('/app/uploads/7/f04505099df1f0a8.docx')[0]
z = zipfile.ZipFile(p)
xml = z.read('word/document.xml').decode('utf-8', 'replace')
z.close()
par = re.findall(r'<w:p[ >].*?</w:p>', xml, re.S)
baris = []
for b in par:
    t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', b, re.S))
    baris.append(t)
teks = '\n'.join(baris)
print('panjang teks:', len(teks))
for m in re.finditer(r'(?i)bab\s+(?:[ivxlcdm]+|\d{1,2})\b', teks):
    print(f'  pos={m.start():6d}  {teks[m.start():m.start()+70]!r}')
print('--- kemunculan "DAFTAR" ---')
for m in re.finditer(r'(?i)daftar\s+\w+', teks[:16000]):
    print(f'  pos={m.start():6d}  {m.group(0)!r}')
