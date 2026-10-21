"""Cari bentuk `questions` yang DITERIMA jev — coba satu-satu, laporkan galat asli.

Jev memakai "discriminator type" → tiap pertanyaan WAJIB punya `type`
bernilai salah satu dari 'noul' | 'choice' | 'score'.
"""
import json
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, '/app')
from app import satpam  # noqa: E402


def kirim(questions, nama):
    body = {'model': satpam.MODEL,
            'messages': [{'role': 'user',
                          'content': json.dumps({'state': {'naskah': 'BAB I ...'},
                                                 'questions': questions})}]}
    req = urllib.request.Request(
        satpam.BASE, data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {satpam.KUNCI}',
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            isi = r.read().decode()
        print(f'  ✅ {nama}')
        print(f'     balasan: {isi[:260]}')
        return True
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        blok = raw[raw.find('HTTP 400: ') + 10:] if 'HTTP 400: ' in raw else raw
        for _ in range(6):
            b2 = blok.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
            if b2 == blok:
                break
            blok = b2
        p = re.search(r'"path":\s*\[(.*?)\]', blok, re.S)
        m = re.search(r'"message":\s*"(Invalid[^"]{0,120})', blok)
        print(f'  ❌ {nama}: HTTP {e.code}')
        if p:
            print(f'     path : {" ".join(p.group(1).split())}')
        if m:
            print(f'     pesan: {m.group(1)}')
        return False


print('═' * 88)
print('  CARI BENTUK questions YANG DITERIMA JEV')
print('═' * 88)

# 1. bentuk asli satpam (limit 6 pilihan)
kirim({'jumlah_bab': {
    'instructions': 'Berapa bab yang ada?',
    'type': 'choice',
    'criteria': {k: v for k, v in list(satpam.TANYA['jumlah_bab']['criteria'].items())},
}}, '1. bentuk ASLI satpam (jumlah_bab, 8 pilihan)')

# 2. noul saja (tanpa criteria)
kirim({'sesuai': {'instructions': 'Apakah balasan menjawab tugas?', 'type': 'noul'}},
      '2. hanya noul (1 pertanyaan)')

# 3. choice dengan 2 pilihan
kirim({'ngawur': {'instructions': 'Apakah balasan ini ngawur?',
                  'type': 'choice',
                  'criteria': {'ya': 'ngawur', 'tidak': 'wajar'}}},
      '3. choice 2 pilihan')

# 4. gabungan noul + choice
kirim({'ngawur': {'instructions': 'Apakah balasan ini ngawur?',
                  'type': 'choice',
                  'criteria': {'ya': 'ngawur', 'tidak': 'wajar'}},
       'sesuai': {'instructions': 'Apakah menjawab tugas?', 'type': 'noul'}},
      '4. choice + noul (dua pertanyaan)')
