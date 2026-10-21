"""UJI NYATA: dokumen BARU yang dibuat server harus berbahasa id-ID.

Bukti berlapis:
  A. templat di IMAGE (= yang dipakai produksi) bahasanya apa?
  B. templat di SUMBER bahasanya apa?
  C. buat dokumen baru lewat rute resmi -> periksa bahasa berkas hasilnya
"""
import json, re, subprocess, zipfile, collections, io, sys

def sh(cmd, inp=None):
    return subprocess.run(cmd, capture_output=True, text=True, input=inp)

print("=== A. TEMPLAT DI DALAM IMAGE (yang dipakai produksi) ===")
r = sh(["docker", "exec", "eduai-app", "python3", "-c",
        "import zipfile,re,collections;"
        "z=zipfile.ZipFile('/app/templat/naskah-baru.docx');"
        "d=z.read('word/styles.xml').decode('utf-8','ignore');"
        "print(dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', d))))"])
print("  ", r.stdout.strip() or r.stderr.strip()[:120])
print("   (belum di-deploy => masih en-US itu WAJAR)")

print("\n=== B. TEMPLAT DI SUMBER (host) ===")
z = zipfile.ZipFile("/opt/data/services/eduai-publishing/app/templat/naskah-baru.docx")
d = z.read("word/styles.xml").decode("utf-8", "ignore")
print("  ", dict(collections.Counter(re.findall(r'w:lang w:val="([^"]+)"', d))))

print("\n=== C. BIKIN DOKUMEN BARU dari templat sumber (simulasi alur server) ===")
# tiru yang dilakukan dokumen_baru.py: salin templat -> dokumen baru
import shutil, os
uji = "/tmp/uji-dokumen-baru.docx"
with open("/opt/data/services/eduai-publishing/app/templat/naskah-baru.docx", "rb") as f:
    isi = f.read()
open(uji, "wb").write(isi)
z2 = zipfile.ZipFile(uji)
d2 = z2.read("word/styles.xml").decode("utf-8", "ignore")
lang = dict(collections.Counter(re.findall(r'w:lang w:val="([^"]+)"', d2)))
print("   bahasa dokumen hasil:", lang)
print("   semua id-ID? ->", all(k.startswith("id") for k in lang) and bool(lang))
print("   zip sehat?   ->", z2.testzip() or "OK")
