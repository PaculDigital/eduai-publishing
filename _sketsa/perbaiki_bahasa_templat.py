"""Perbaiki bahasa templat: en-US -> id-ID (di styles.xml + document.xml).

Akar (terukur 02Okt26): app/templat/naskah-baru.docx punya
  styles.xml -> w:lang w:val="en-US"
sehingga setiap dokumen BARU lahir berbahasa Inggris (dropdown
"English - United States"), dan itu memengaruhi pemeriksa ejaan.

OnlyOffice: bahasa DOKUMEN = properti berkas, TIDAK bisa lewat Docs API.
Jalan resmi = templat yang bahasanya sudah benar.

AMAN: hanya mengubah atribut bahasa; isi/tata letak tidak disentuh.
"""
import re
import shutil
import sys
import zipfile

SRC = "/opt/data/services/eduai-publishing/app/templat/naskah-baru.docx"
BAK = "_arsip/pre-kosmetik-20261002-1051/naskah-baru-TEMPLAT-ASLI.docx"

shutil.copy(SRC, BAK)
print("backup ->", BAK)

zin = zipfile.ZipFile(SRC)
items = zin.infolist()
isi = {}
ubah_total = 0

for it in items:
    data = zin.read(it.filename)
    if it.filename.endswith(".xml"):
        teks = data.decode("utf-8")
        asli = teks
        # 1) w:lang w:val="en-XX" -> id-ID
        teks = re.sub(r'(w:val=")en-[A-Z]{2}(")', r"\1id-ID\2", teks)
        # 2) eastAsia / bidi juga
        teks = teks.replace('w:eastAsia="en-US"', 'w:eastAsia="id-ID"')
        if teks != asli:
            n = len(re.findall(r'"id-ID"', teks))
            ubah_total += n
            print(f"  diubah: {it.filename} ({n} titik)")
        data = teks.encode("utf-8")
    isi[it.filename] = data
zin.close()

if ubah_total == 0:
    print("\nTIDAK ADA yang diubah — periksa polanya.")
    sys.exit(2)

# Tulis ulang (pertahankan kompresi)
with zipfile.ZipFile(SRC, "w", zipfile.ZIP_DEFLATED) as zout:
    for it in items:
        zout.writestr(it, isi[it.filename])

print(f"\nSELESAI — {ubah_total} titik bahasa diubah ke id-ID")
print("ukuran baru:", __import__("os").path.getsize(SRC), "byte")
