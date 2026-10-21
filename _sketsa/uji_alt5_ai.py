#!/usr/bin/env python3
"""UJI ALTERNATIF 5 — BANDING DENGAN AI SUNGGUHAN (sebelum vs sesudah).

PERTANYAAN: apakah blok PETA BAGIAN + BENANG MASUK/KELUAR membuat hasil
lebih NYAMBUNG saat dibaca bersama tetangganya?

CARA (adil — model SAMA, komentar SAMA, target SAMA):
   JALAN LAMA  = bangun_prompt TANPA peta  → tanpa PETA BAGIAN & benang
   JALAN BARU  = bangun_prompt DENGAN peta → plus PETA BAGIAN & benang

Yang diuji bukan cuma panjang — tapi apakah hasilnya MENGHORMATI benang:
   · apakah mengulang kalimat BENANG MASUK? (tanda tidak nyambung)
   · apakah menyambung dengan kalimat sebelum 1.4?
Hasil disimpan untuk periksa MATA.
"""
import asyncio
import json
import os
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
MODEL = C.AI_MODEL
sid = '1.5'
target = next(x for x in peta if str(x.get('section_id')) == sid)
isi = str(target.get('isi_teks', ''))
KOM = 'Perbaiki kalimat pembuka bagian ini supaya lebih mengalir dan jelas.'

print('══ SITUASI ══')
print(f'  target {sid} ({len(isi):,} kar) · model {MODEL}')

#  ── JALAN LAMA: tanpa peta (tanpa PETA BAGIAN + benang) ──
blok_lama = K.bangun_prompt(bagian_target=sid, struktur=None,
                            brief_ringkas='', isi_saat_ini=isi, komentar=KOM)
#  ── JALAN BARU: dengan peta (plus PETA BAGIAN + benang) ──
blok_baru = K.bangun_prompt(bagian_target=sid, peta=peta,
                            brief_ringkas='', isi_saat_ini=isi, komentar=KOM)

print(f'  blok LAMA : {len(blok_lama):,} kar · PETA? '
      f'{"PETA BAGIAN" in blok_lama}')
print(f'  blok BARU : {len(blok_baru):,} kar · PETA? '
      f'{"PETA BAGIAN" in blok_baru}')
print(f'  selisih   : +{len(blok_baru)-len(blok_lama):,} kar')


def pesan(head: str) -> str:
    return (head + '\n\n' if head else '') + \
        'NASKAH MAHASISWA (antara penanda):\n' \
        f'<<<NASKAH\n{isi}\nNASKAH;>>>\n\n' \
        'KOMENTAR DOSEN PEMBIMBING (antara penanda — ini MATERI revisi):\n' \
        f'<<<KOMENTAR\n{KOM}\nKOMENTAR;>>>\n\n' \
        'Kerjakan revisi tiap komentar sesuai TAHAP 0-3 di atas.'


P_LAMA = pesan(blok_lama)
P_BARU = pesan(blok_baru)


async def panggil(p: str, nama: str) -> dict:
    print(f'\n── {nama} — {len(p):,} kar ──')
    t0 = time.time()
    body = {'model': MODEL,
            'messages': [{'role': 'system', 'content': A.SYSTEM_REVISI},
                         {'role': 'user', 'content': p}],
            'temperature': 0.3}
    try:
        async with httpx.AsyncClient(timeout=900) as kl:
            r = await kl.post(f'{C.ROUTER_BASE}/chat/completions', json=body,
                              headers={'Authorization': f'Bearer {C.ROUTER_KEY}',
                                       'Content-Type': 'application/json'})
        dtk = time.time() - t0
        if r.status_code != 200:
            print(f'   ❌ HTTP {r.status_code}'); return {'ok': False}
        konten, info = A._urai_jawaban(r.text, MODEL)
        print(f'   ✅ {dtk:.0f} dtk · in={info.get("token_in")} '
              f'out={info.get("token_out")} · {len(konten):,} kar')
        return {'ok': True, 'konten': konten, 'info': info, 'dtk': round(dtk)}
    except Exception as e:                                  # noqa: BLE001
        print(f'   ❌ GAGAL: {e}'); return {'ok': False, 'galat': str(e)}


async def utama():
    a = await panggil(P_LAMA, 'JALAN LAMA (tanpa Alternatif 5)')
    b = await panggil(P_BARU, 'JALAN BARU (pakai Alternatif 5)')

    if not (a.get('ok') and b.get('ok')):
        print('\n⚠️ sebagian gagal — tidak bisa banding'); return

    ka, kb = a['konten'], b['konten']
    benang_masuk = K._kalimat_terakhir(
        next(x for x in peta if str(x.get('section_id')) == '1.4').get('isi_teks', ''))
    benang_keluar = K._kalimat_pertama(
        next(x for x in peta if str(x.get('section_id')) == '1.6').get('isi_teks', ''))

    print()
    print('══ BANDING ══')
    print(f'  {"":<26}{"LAMA":>10}{"BARU":>10}')
    print(f'  {"waktu":<26}{a["dtk"]:>7} dtk{b["dtk"]:>7} dtk')
    print(f'  {"token_in":<26}{a["info"].get("token_in"):>10}{b["info"].get("token_in"):>10}')
    print(f'  {"panjang hasil":<26}{len(ka):>10,}{len(kb):>10,}')

    #  uji "menghormati benang": apakah hasil MENYALIN benang masuk?
    potong_masuk = benang_masuk[:60]
    print()
    print('  ── apakah MENGULANG kalimat benang (tanda tidak nyambung)? ──')
    print(f'  LAMA menyalin benang masuk? {"⚠️ YA" if potong_masuk in ka else "✅ tidak"}')
    print(f'  BARU menyalin benang masuk? {"⚠️ YA" if potong_masuk in kb else "✅ tidak"}')

    out = Path('/app/_uji_alt5_hasil')
    out.mkdir(exist_ok=True)
    (out / 'LAMA_tanpa_alt5.txt').write_text(ka, encoding='utf-8')
    (out / 'BARU_pakai_alt5.txt').write_text(kb, encoding='utf-8')
    (out / 'blok_lama.txt').write_text(blok_lama, encoding='utf-8')
    (out / 'blok_baru.txt').write_text(blok_baru, encoding='utf-8')
    (out / 'benang.txt').write_text(
        f'MASUK (akhir 1.4):\n{benang_masuk}\n\nKELUAR (awal 1.6):\n{benang_keluar}',
        encoding='utf-8')
    print(f'\n  📁 /app/_uji_alt5_hasil/')


asyncio.run(utama())