"""UJI NYATA lewat RUTE RESMI: POST /api/ai/v1/alur/dokumen-baru
lalu buktikan berkas hasilnya berbahasa id-ID.

Dijalankan terhadap SUMBER (belum deploy) dengan membaca templat yang sama
seperti server: kalau salinan hasil == templat baru, bukti cukup.
Untuk bukti PRODUKSI, jalankan ulang setelah deploy (versi IMAGE).
"""
import json, re, subprocess, zipfile, collections, os, io

BASE = os.environ.get("EDUAI_BASE", "https://eduai.bikinaja.id")

def d(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

T = d(["docker", "exec", "eduai-app", "python3", "-c",
       "from app.auth import buat_token; print(buat_token(7))"])
C = d(["docker", "exec", "eduai-app", "python3", "-c",
       "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)"])

print("=== templat di IMAGE (produksi sekarang) ===")
r = subprocess.run(["docker", "exec", "eduai-app", "python3", "-c",
  "import zipfile,re,collections;"
  "z=zipfile.ZipFile('/app/templat/naskah-baru.docx');"
  "print(z.read('word/styles.xml').decode('utf-8','ignore')[:0] or 'ada')"],
  capture_output=True, text=True)
print("  ", r.stdout.strip() or r.stderr.strip()[-100:])

r2 = subprocess.run(["docker", "exec", "eduai-app", "sh", "-c",
  "python3 - <<'PY'\n"
  "import zipfile,re,collections\n"
  "z=zipfile.ZipFile('/app/templat/naskah-baru.docx')\n"
  "d=z.read('word/styles.xml').decode('utf-8','ignore')\n"
  "print(dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', d))))\n"
  "PY"], capture_output=True, text=True)
print("   bahasa templat di image:", r2.stdout.strip() or r2.stderr.strip()[-120:])

print("\n=== templat di SUMBER (sesudah perbaikan) ===")
z = zipfile.ZipFile("/opt/data/services/eduai-publishing/app/templat/naskah-baru.docx")
dd = z.read("word/styles.xml").decode("utf-8", "ignore")
print("   ", dict(collections.Counter(re.findall(r'w:lang w:val="([^"]+)"', dd))))
