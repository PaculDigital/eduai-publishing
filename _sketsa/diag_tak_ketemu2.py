"""Diagnosa tak_ketemu v2 — panggil 9router LANGSUNG dgn prompt revisi yang
sama, lihat bentuk KUTIP-ASLI yang dikirim AI, lalu cocokkan ke naskah.
"""
import json
import os
import re
import urllib.request

from sqlalchemy import text
from app.models import SessionLocal, FileBerkas
from app.pipa import normal
from app.ai import _path_berkas, _teks_dari_berkas

db = SessionLocal()
fb = db.get(FileBerkas, 61)
teks = _baca = None
try:
    from app.ai import _teks_dari_berkas
    teks = _teks_dari_berkas(_path_berkas(fb), fb.nama)
except Exception as e:
    print('baca berkas gagal:', e)
print('naskah:', len(teks or ''))

# kutipan yang dipakai pipa: kita perlu tahu apa yang AI tulis.
# Ambil prompt template revisi & jalankan seperti ai.py — terlalu berat.
# Cara ringkas: ambil 1 paragraf BAB 2 (penelitian terdahulu) dan lihat
# apakah "penelitian terdahulu" bisa ditunjuk.
p = [x for x in (teks or '').split('\n\n') if 'terdahulu' in normal(x)]
print('paragraf berisi "terdahulu":', len(p))
for x in p[:2]:
    print('---', normal(x)[:150])
