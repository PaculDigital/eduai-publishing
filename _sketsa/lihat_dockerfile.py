#!/usr/bin/env python3
"""PASANG FONT ke container — supaya grafik tidak pakai font bawaan kecil.

🔴 HASIL UKUR: ketiga jalur font truetype TIDAK ADA di container
   (dejavu/liberation) → PIL memakai font bawaan 11px dan karakter
   en-dash "–" jadi KOTAK (temuan mata 25Sep26).

PILIHAN:
  A. Pasang paket `fonts-dejavu-core` via apt (butuh root + jaringan saat build)
  B. Kirim berkas .ttf dari host ke dalam image lewat Dockerfile

Wulan CEK DULU: apakah apt bisa dipakai di Dockerfile?
"""
import re
import sys
from pathlib import Path

DOCKERFILE = Path('/opt/data/services/eduai-publishing/Dockerfile')
if not DOCKERFILE.exists():
    print('❌ Dockerfile tidak ada — cari nama lain')
    sys.exit(1)

isi = DOCKERFILE.read_text()
print('══ ISI DOCKERFILE ══')
print(isi)
