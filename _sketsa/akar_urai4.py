"""AKAR FINAL v2: ambil jawaban NYATA, tulis ke BERKAS, periksa byte demi byte.

Jangan pakai jawaban rekaan — pakai yang benar-benar keluar dari model,
supaya akarnya kelihatan (bukan tebakan).
"""
import asyncio
import json
import sys

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

open('/tmp/jawab_nyata.txt', 'w', encoding='utf-8').write(jawab)
print('jawaban disimpan: /tmp/jawab_nyata.txt', len(jawab), 'kar')
print('model:', (info or {}).get('model'))

#  ── Periksa: berapa banyak '{' dan '}' ?
print()
print("jumlah '{':", jawab.count('{'), " jumlah '}':", jawab.count('}'))
print('ada "```":', '```' in jawab)
print('karakter AWAL:', repr(jawab[:60]))
print('karakter AKHIR:', repr(jawab[-60:]))

#  ── Jalankan urai_catatan SUNGGUHAN
hasil = PAI.urai_catatan(jawab)
print()
print('>>> urai_catatan pada jawaban NYATA →', len(hasil), 'butir')
for h in hasil:
    print('   -', h['bagian'], '|', h['soal'][:70])

#  ── Kalau 0: telusuri TEPAT di langkah mana
if not hasil:
    print()
    print('=== TELUSURI LANGKAH DEMI LANGKAH ===')
    t = jawab.strip()
    if t.startswith('```'):
        print('1. ADA pagar ``` di awal')
        t = t.split('\n', 1)[1] if '\n' in t else t
        if t.rstrip().endswith('```'):
            t = t.rstrip()[:-3]
        print('   setelah buang pagar:', len(t))
    else:
        print('1. TIDAK ada pagar (langsung JSON)')

    m = t.find('{')
    print('2. posisi "{" pertama:', m)
    dalam, akhir = 0, -1
    for i in range(m, len(t)):
        if t[i] == '{':
            dalam += 1
        elif t[i] == '}':
            dalam -= 1
            if dalam == 0:
                akhir = i + 1
                break
    print('3. akhir blok seimbang:', akhir)
    if akhir > 0:
        blok = t[m:akhir]
        print('4. panjang blok:', len(blok))
        try:
            d = json.loads(blok)
            print('5. json.loads BERHASIL, kunci:', list(d.keys()))
            b = d.get('catatan')
            print('6. butir:', type(b).__name__,
                  len(b) if isinstance(b, list) else '')
            if isinstance(b, list):
                for i, c in enumerate(b):
                    print(f'   butir {i}: dict={isinstance(c, dict)} '
                          f'soal={bool(str((c or {}).get("soal") or "").strip())} '
                          f'kunci={list(c.keys()) if isinstance(c, dict) else "?"}')
        except Exception as e:
            print('5. json.loads GAGAL:', type(e).__name__, e)
            print('   blok 300 kar pertama:', repr(blok[:300]))
            print('   blok 300 kar terakhir:', repr(blok[-300:]))
    else:
        print('4. TIDAK seimbang → kurung rusak')
        print('   dari posisi { (400 kar):', repr(t[m:m + 400]))
