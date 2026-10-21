"""Reproduksi 3 kosmetik: buktikan cacatnya ADA di layar nyata (bukan dari kode).

Ukur yang bisa diukur:
  #1 bahasa editor ('lang' yang BENAR-BENAR dipakai OO)
  #2 'Cacah kata' ada/tidak (padanan kata Inggrisnya)
  #3 popup 'Multipage view' berbahasa apa
"""
import importlib.util, json, re, subprocess, sys, time

BASE = "https://eduai.bikinaja.id"
FID = sys.argv[1] if len(sys.argv) > 1 else None


def tok():
    out = subprocess.run(
        ["docker", "exec", "eduai-app", "python3", "-c",
         "from app.auth import buat_token; print(buat_token(7))"],
        capture_output=True, text=True)
    return out.stdout.strip()


def ck():
    out = subprocess.run(
        ["docker", "exec", "eduai-app", "python3", "-c",
         "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)"],
        capture_output=True, text=True)
    return out.stdout.strip()


T = tok(); C = ck()
print("token:", "ada" if T else "KOSONG", "| cookie:", C)

# Ambil daftar berkas
r = subprocess.run(["curl", "-s", "--max-time", "20", "-H", f"Cookie: {C}={T}",
                    f"{BASE}/api/files"], capture_output=True, text=True)
print("\n=== daftar berkas (potongan) ===")
print(r.stdout[:400])
