"""UJI PRODUKSI NYATA: buat dokumen baru lewat rute resmi, lalu buka editor
dan BACA bahasa dokumen yang terlihat di baris status.

Bukti: dropdown bahasa harus jadi "Indonesian" (bukan "English - United States").
"""
import base64, importlib.util, json, os, subprocess, sys, time

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
print("cookie:", C, "| token:", "ada" if T else "KOSONG")

# Cari rute bikin dokumen baru
r = subprocess.run(["docker", "exec", "eduai-app", "sh", "-c",
                    "grep -rn 'dokumen-baru\\|dokumen_baru' /app/app/main.py | head -6"],
                   capture_output=True, text=True)
print("\n=== rute dokumen baru ===")
print(r.stdout.strip() or "(tidak ketemu)")

# Cari FID terbaru milik user 7 (yang sudah ada) -> buat dok baru via UI lebih rumit,
# jadi cukup: pakai dokumen BARU yang dibuat lewat API, lalu buka editornya
print("\n=== cari FID milik user 7 ===")
r2 = subprocess.run(["docker", "exec", "eduai-app", "python3", "-c",
  "import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
  "print([(x[0],x[1]) for x in c.execute(\"select id,nama from files where user_id=7 order by id desc limit 6\")])"],
  capture_output=True, text=True)
print(r2.stdout.strip()[:400])
