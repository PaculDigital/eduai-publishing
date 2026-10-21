"""CARI AKAR: mengapa urai_catatan balas 0 padahal model jawab JSON?

Jangan menambal — telusuri langkah demi langkah dengan jawaban NYATA.
"""
import asyncio
import json
import sys
import time

sys.path.insert(0, '/app')

from app import pembimbing_ai as PAI
from app import ai as AI
from app.models import SessionLocal, BerkasPembimbingan

db = SessionLocal()
bk = db.query(BerkasPembimbingan).first()
teks = PAI._teks_naskah(db, bk)
prompt = PAI.bangun_prompt('Mhs', bk.judul or '', teks)
jawab, info = asyncio.run(AI._panggil_router(prompt, 240.0,
                                             system=PAI.SYSTEM_PEMBIMBING))
db.close()

print('PANJANG JAWABAN:', len(jawab))
print()
print('=== 300 karakter PERTAMA (repr, supaya terlihat apa adanya) ===')
print(repr(jawab[:300]))
print()
print('=== 200 karakter TERAKHIR ===')
print(repr(jawab[-200:]))
print()

#  Langkah 1: apakah ada '{' ?
print('ada "{" pada posisi:', jawab.find('{'))
print('ada "```" ?', '```' in jawab)
print()

#  Langkah 2: cari blok JSON seimbang (meniru urai_catatan)
teks2 = jawab.strip()
if teks2.startswith('```'):
    teks2 = teks2.split('\n', 1)[1] if '\n' in teks2 else teks2
    if teks2.rstrip().endswith('```'):
        teks2 = teks2.rstrip()[:-3]
mulai = teks2.find('{')
print('posisi "{" setelah buang pagar:', mulai)
dalam, akhir = 0, -1
for i in range(mulai, len(teks2)):
    if teks2[i] == '{':
        dalam += 1
    elif teks2[i] == '}':
        dalam -= 1
        if dalam == 0:
            akhir = i + 1
            break
print('posisi akhir blok JSON:', akhir, '| panjang teks:', len(teks2))
if akhir > 0:
    blok = teks2[mulai:akhir]
    print('panjang blok:', len(blok))
    try:
        data = json.loads(blok)
        print('JSON PARSING: BERHASIL ✅')
        print('kunci:', list(data.keys()) if isinstance(data, dict) else type(data))
        butir = data.get('catatan') if isinstance(data, dict) else None
        print('jumlah butir:', len(butir) if isinstance(butir, list) else 'BUKAN LIST')
        if isinstance(butir, list) and butir:
            print('butir[0] kunci:', list(butir[0].keys()))
            print('butir[0]:', json.dumps(butir[0], ensure_ascii=False)[:250])
    except Exception as e:
        print('JSON PARSING GAGAL ❌ :', type(e).__name__, e)
        print('blok (300 kar):', repr(blok[:300]))
        print('blok (200 kar TERAKHIR):', repr(blok[-200:]))
else:
    print('TIDAK ADA blok JSON seimbang → akar: kurung tidak seimbang')
    print('sisa 400 kar:', repr(teks2[mulai:mulai + 400]))
