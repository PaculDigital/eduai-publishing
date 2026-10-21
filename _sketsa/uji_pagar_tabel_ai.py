#!/usr/bin/env python3
"""UJI PAGAR TABEL (G7d) — apakah AI SUNGGUHAN menolak menulis ulang tabel?

CARA: ambil bagian 1.5 yang MENGANDUNG [[TABEL-2]] + [[GAMBAR-n]].
Perintah = komentar yang MENYASAR ke kalimat pengantar tabel (bukan tabelnya).
ALAMI: AI HARUS merevisi kalimat pengantar, TAPI membiarkan [[TABEL-2]] utuh.

YANG DINILAI (otomatis + mata):
   · apakah penanda [[TABEL-n]] MASIH ADA di hasil? (harus YA)
   · apakah penanda [[GAMBAR-n]] MASIH ADA? (harus YA)
   · apakah AI menulis ULANG isi tabel jadi teks? (harus TIDAK)
"""
import asyncio
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

import httpx                                                # noqa: E402
from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as ST                                 # noqa: E402
import app.config as C                                      # noqa: E402

naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'),
                             '_naskah_bos_uji.docx')
peta = ST.petakan(ST.buang_daftar_isi(naskah))
target = next(x for x in peta if str(x.get('section_id')) == '1.5')
isi = str(target.get('isi_teks', ''))

print('══ BAHAN ══')
print(f'  bagian 1.5: {len(isi):,} kar')
tab = re.findall(r'\[\[TABEL-\d+[^\]]*\]\]', isi)
gam = re.findall(r'\[\[GAMBAR-\d+[^\]]*\]\]', isi)
print(f'  tabel  di bagian ini: {len(tab)} → {tab[:2]}')
print(f'  gambar di bagian ini: {len(gam)} → {gam[:2]}')

#  perintah: benahi KALIMAT PENGANTAR tabel, jangan tabelnya
KOM = ('Perbaiki kalimat pengantar sebelum tabel ini supaya lebih mengalir, '
       'dan pastikan kalimat tersebut menjelaskan isi tabelnya.')

konteks = K.bangun_prompt(bagian_target='1.5', peta=peta, brief_ringkas='',
                          isi_saat_ini=isi, komentar=KOM)
pesan = (konteks + '\n\n'
         'NASKAH MAHASISWA (antara penanda):\n'
         f'<<<NASKAH\n{isi}\nNASKAH;>>>\n\n'
         'KOMENTAR DOSEN PEMBIMBING (antara penanda — ini MATERI revisi):\n'
         f'<<<KOMENTAR\n{KOM}\nKOMENTAR;>>>\n\n'
         'Kerjakan revisi tiap komentar sesuai TAHAP 0-3 di atas.')

print(f'  prompt total: {len(pesan):,} kar · model {C.AI_MODEL}')


async def utama():
    print('\n── PANGGIL AI ──')
    t0 = time.time()
    body = {'model': C.AI_MODEL,
            'messages': [{'role': 'system', 'content': A.SYSTEM_REVISI},
                         {'role': 'user', 'content': pesan}],
            'temperature': 0.2}
    async with httpx.AsyncClient(timeout=900) as kl:
        r = await kl.post(f'{C.ROUTER_BASE}/chat/completions', json=body,
                          headers={'Authorization': f'Bearer {C.ROUTER_KEY}',
                                   'Content-Type': 'application/json'})
    dtk = time.time() - t0
    if r.status_code != 200:
        print(f'  ❌ HTTP {r.status_code}: {r.text[:200]}'); return
    konten, info = A._urai_jawaban(r.text, C.AI_MODEL)
    print(f'  ✅ {dtk:.0f} dtk · in={info.get("token_in")} '
          f'out={info.get("token_out")} · {len(konten):,} kar')

    out = Path('/app/_uji_pagar_tabel')
    out.mkdir(exist_ok=True)
    (out / 'hasil_mentah.txt').write_text(konten, encoding='utf-8')
    (out / 'naskah_dikirim.txt').write_text(isi, encoding='utf-8')
    (out / 'komentar.txt').write_text(KOM, encoding='utf-8')

    print()
    print('══ PENILAIAN PAGAR TABEL ══')
    t_hasil = re.findall(r'\[\[TABEL-\d+[^\]]*\]\]', konten)
    g_hasil = re.findall(r'\[\[GAMBAR-\d+[^\]]*\]\]', konten)
    tutup = re.findall(r'\[\[/TABEL-\d+\]\]', konten)
    print(f'  penanda TABEL di hasil  : {len(t_hasil)}')
    print(f'  penanda /TABEL di hasil : {len(tutup)}')
    print(f'  penanda GAMBAR di hasil : {len(g_hasil)}')
    print(f'  → AI mempertahankan penanda? '
          f'{"✅ YA" if (t_hasil or g_hasil) else "❌ TIDAK"}')
    print(f'  → AI MENULIS ULANG tabel jadi teks? '
          f'{"⚠️ MUNGKIN" if "kolom" in konten.lower() and not t_hasil else "✅ tidak"}')

    print()
    print('── HASIL (1.600 kar pertama) ──')
    print(konten[:1600])


asyncio.run(utama())