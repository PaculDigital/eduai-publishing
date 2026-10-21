"""Periksa: (1) apakah templat baru sudah benar, (2) berapa dokumen LAMA
yang masih berbahasa en-US, (3) apakah OO benar-benar memakai templat ini.
"""
import re, zipfile, collections, subprocess, json, os

print("=== 1. TEMPLAT naskah-baru.docx ===")
p = "/opt/data/services/eduai-publishing/app/templat/naskah-baru.docx"
z = zipfile.ZipFile(p)
d = z.read("word/styles.xml").decode("utf-8", "ignore")
print("  styles.xml w:lang :", dict(collections.Counter(re.findall(r'w:lang w:val="([^"]+)"', d))))

print("\n=== 2. Dokumen LAMA di container (berapa masih en-US?) ===")
out = subprocess.run(
    ["docker", "exec", "eduai-app", "sh", "-c",
     "ls -1 /app/data/files/ 2>/dev/null | head -40"],
    capture_output=True, text=True).stdout.strip()
print("  isi /app/data/files:", out[:300] if out else "(kosong/tidak ada)")

# cari folder dokumen
out2 = subprocess.run(
    ["docker", "exec", "eduai-app", "sh", "-c",
     "find /app -name '*.docx' -not -path '*/node_modules/*' 2>/dev/null | head -30"],
    capture_output=True, text=True).stdout.strip()
print("\n  berkas .docx di container:")
for f in (out2 or "(tidak ada)").splitlines()[:20]:
    print("   ", f)

print("\n=== 3. Bahasanya masing-masing ===")
if out2:
    for f in out2.splitlines()[:12]:
        try:
            cmd = ("python3 -c \"import zipfile,re,collections,sys;"
                   "z=zipfile.ZipFile(sys.argv[1]);"
                   "d=z.read('word/styles.xml').decode('utf-8','ignore');"
                   "print(dict(collections.Counter(re.findall(r'w:lang w:val=.([^\\\"]+).', d))))\"")
            r = subprocess.run(["docker", "exec", "eduai-app", "python3", "-c",
                                "import zipfile,re,collections,sys;"
                                "z=zipfile.ZipFile(sys.argv[1]);"
                                "d=z.read('word/styles.xml').decode('utf-8','ignore');"
                                "print(dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', d))))",
                                f], capture_output=True, text=True)
            print(f"   {f} -> {r.stdout.strip() or r.stderr.strip()[:60]}")
        except Exception as e:
            print(f"   {f} -> gagal: {e}")
