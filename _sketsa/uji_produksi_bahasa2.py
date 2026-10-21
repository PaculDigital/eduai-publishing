"""UJI PRODUKSI NYATA (end-to-end):
  1. POST /alur/dokumen-baru  -> dapat file_id dokumen BARU
  2. periksa bahasa berkasnya di server (harus id-ID, bukan en-US)
  3. buka /edit/<fid> di browser -> BACA bahasa yang TAMPIL di baris status
  4. potret untuk MATA
"""
import base64, importlib.util, json, os, subprocess, sys, time, urllib.request

BASE = "https://eduai.bikinaja.id"

spec = importlib.util.spec_from_file_location(
    "ph", "/opt/data/skills/creative/bayana-publishing-web/scripts/potret_halaman.py")
ph = importlib.util.module_from_spec(spec); spec.loader.exec_module(ph)


def d(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


T = d(["docker", "exec", "eduai-app", "python3", "-c",
       "from app.auth import buat_token; print(buat_token(7))"])
C = d(["docker", "exec", "eduai-app", "python3", "-c",
       "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)"])

# ── 1. Bikin dokumen baru lewat rute resmi ─────────────────────────
print("=== 1. POST /alur/dokumen-baru ===")
req = urllib.request.Request(
    f"{BASE}/alur/dokumen-baru",
    data=json.dumps({"nama_dokumen": "UJI-BAHASA-02Okt26.docx"}).encode(),
    headers={"Content-Type": "application/json", "Cookie": f"{C}={T}"},
    method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        jawab = json.loads(r.read().decode())
    print("  HTTP", r.status)
    print("  balasan:", json.dumps(jawab)[:300])
except Exception as e:
    print("  GAGAL:", type(e).__name__, str(e)[:200]); sys.exit(1)

fid = (jawab.get("file_id") or jawab.get("dokumen", {}).get("file_id")
       or jawab.get("fid"))
print("  file_id BARU =", fid)
if not fid:
    print("  tidak dapat file_id:", json.dumps(jawab)[:400]); sys.exit(1)

# ── 2. Bahasa berkasnya di server ──────────────────────────────────
print("\n=== 2. bahasa berkas baru di server ===")
r = subprocess.run(["docker", "exec", "eduai-app", "python3", "-c",
  "import sqlite3,zipfile,re,collections,glob,os\n"
  "c=sqlite3.connect('/app/data/eduai.db')\n"
  "row=c.execute('select nama_simpan,user_id from files where id=?',(" + str(fid) + ",)).fetchone()\n"
  "print('nama_simpan:', row)\n"
  "p=glob.glob('/app/uploads/%s/%s' % (row[1], row[0]))\n"
  "p = p[0] if p else None\n"
  "print('berkas:', p)\n"
  "if p and os.path.exists(p):\n"
  "    z=zipfile.ZipFile(p)\n"
  "    dd=z.read('word/styles.xml').decode('utf-8','ignore')\n"
  "    print('BAHASA:', dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', dd))))"],
  capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip()[-300:])
print("FID=" + str(fid))
