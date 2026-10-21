"""UJI JEV vs MESIN LAMA — naskah ASLI (Asih, 5 bab).

Tujuan (perintah Bos): apakah Jev optimal & bisa diandalkan untuk
mengatasi masalah "menebak naskah"? Diukur, bukan diduga.

Yang diuji:
  1. Jev dengan naskah ASLI panjang — apakah benar membaca struktur?
  2. Confidence-nya jujur atau over-confident?
  3. Biaya & waktu sebenarnya untuk naskah penuh.
  4. Apakah Jev MENANGKAP kasus yang mesin lama SALAH
     (naskah Asih = kategori 'bab', bukan 'bab1').
  5. Bandingkan Jev vs mesin regex lama pada naskah yang sama.
"""
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request

# ── kunci OpenRouter (dari salinan DB 9router, tidak dicetak)
c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
row = c.execute("select data from providerConnections where provider='openrouter'").fetchone()
KEY = json.loads(dict(row)['data']).get('apiKey')

# ── ambil teks naskah Asih dari dalam container EduAi (naskah asli, bukan uji)
import subprocess
print('== ambil teks naskah Asih dari container ==')
hasil = subprocess.run([
    'docker', 'exec', '-e', 'PYTHONPATH=/app', '-w', '/app', 'eduai-app',
    'python3', '-c',
    "import sys; sys.path.insert(0,'/app');"
    "from app.models import SessionLocal, FileBerkas;"
    "from app.ai import _teks_dari_berkas;"
    "db=SessionLocal();"
    "b=db.get(FileBerkas, 81);"
    "print('NAMA:', b.nama if b else 'TIDAK ADA');"
    "t=_teks_dari_berkas(b);"
    "print('PANJANG:', len(t));"
    "sys.stdout.write('__TEKS__'+t)"
], capture_output=True, text=True, timeout=180)

out = hasil.stdout or ''
if '__TEKS__' not in out:
    print('GAGAL ambil teks:', hasil.stderr[-600:])
    raise SystemExit(1)

head, teks = out.split('__TEKS__', 1)
print(head.strip())
print('panjang teks:', len(teks), 'karakter')
open('/tmp/naskah_asih.txt', 'w').write(teks)

# ── potongan untuk Jev: ambil baris-baris yang mengandung judul bab +
#     sejumlah isi, supaya state tetap masuk akal tapi tidak 130rb karakter
baris = [b.strip() for b in teks.split('\n') if b.strip()]
print('jumlah baris:', len(baris))

import re
kandidat_bab = [b for b in baris if re.match(r'^BAB\s+[IVXLC]+\b', b, re.I)]
print('baris mirip judul bab:', len(kandidat_bab))
for k in kandidat_bab[:12]:
    print('   ', k[:80])
