#!/usr/bin/env python3
"""UJI JEV terhadap ARTIKEL HASIL KONVERSI (07 Okt 2026).

Memakai hasil nyata /tmp/hasil_konversi_nyata.json.
Pertanyaan: apakah Jev benar-benar memeriksa hasilnya?
"""
import json
import sys
import time

sys.path.insert(0, '/app')
from app import konversi as K                                      # noqa: E402
from app.models import SessionLocal                               # noqa: E402
from app import satpam                                             # noqa: E402

with open('/tmp/hasil_konversi_nyata.json', encoding='utf-8') as f:
    d = json.load(f)

a = d.get('artikel') or {}
teks = d.get('teks') or K.artikel_ke_teks(a)

print('═' * 66)
print('UJI JEV PERIKSA ARTIKEL HASIL')
print('═' * 66)
print(f'panjang teks artikel : {len(teks):,} kar')
print()

db = SessionLocal()
try:
    print('─' * 66)
    print('① JEV PERIKSA MUTU (18 poin: 11 elemen + 7 bagian)')
    print('─' * 66)
    t0 = time.time()
    mutu = K.periksa_mutu(db, 81, teks)
    detik = time.time() - t0
    print(f'  ok        : {mutu.get("ok")}')
    print(f'  keputusan : {mutu.get("keputusan")}')
    print(f'  skor      : {mutu.get("skor")}')
    print(f'  detik     : {detik:.2f}')
    print(f'  model     : {mutu.get("model")}')
    print(f'  alasan    : {mutu.get("alasan")}')
    print()
    ada = mutu.get('ada') or {}
    print(f'  ADA ({len(ada)}):')
    for k, v in ada.items():
        print(f'    ✅ {k}: {v}')
    kurang = mutu.get('kurang') or []
    ragu = mutu.get('ragu') or []
    print(f'  KURANG ({len(kurang)}): {kurang}')
    print(f'  RAGU   ({len(ragu)}): {ragu}')
    print()
    print('─' * 66)
    print('② PESAN KE USER (rangkum_mutu)')
    print('─' * 66)
    print(K.rangkum_mutu(mutu))
    print()
    print('─' * 66)
    print('③ BAHAN YANG DIKIRIM KE JEV (potongan 600 kar)')
    print('─' * 66)
    bahan = K._bahan_mutu(teks)
    print(f'  panjang bahan: {len(bahan):,} kar')
    print(f'  AWAL : {bahan[:200]!r}')
    print(f'  AKHIR: {bahan[-200:]!r}')
finally:
    db.close()
print('═' * 66)
