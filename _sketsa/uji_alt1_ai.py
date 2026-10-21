#!/usr/bin/env python3
"""UJI ALTERNATIF 1 DENGAN AI — bagian utuh vs 3 paragraf berlabel.

PERTANYAAN: apakah "3 paragraf berlabel" benar-benar lebih PRESISI
(AI tidak meleset) dibanding "bagian utuh"?

CARA ADIL (model SAMA, komentar SAMA, target SAMA):
   JALAN A = bagian 1.5 utuh (1.861 kar)   ← cara sekarang (konteks tetangga)
   JALAN B = 3 paragraf berlabel (659 kar) ← Alternatif 1

PENILAIAN (otomatis, jujur):
   · apakah hasil menyentuh PARAGRAF SASARAN? (cari kata khas paragraf itu)
   · apakah hasil MENYENTUH paragraf lain? (tanda meleset)
   · ukuran & token.
"""
import asyncio
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
isi_bagian = str(target.get('isi_teks', ''))

par = K.petakan_paragraf(isi_bagian)
#  pilih paragraf SASARAN yang berisi (bukan judul): cari yang paling panjang
idx_sasar = max(range(len(par)), key=lambda i: len(par[i]['teks']))
sasar = par[idx_sasar]
print('══ SITUASI ══')
print(f'  bagian {sid}: {len(isi_bagian):,} kar · {len(par)} paragraf')
print(f'  SASARAN: {sasar["label"]} ({len(sasar["teks"]):,} kar)')
print(f'  isi: {sasar["teks"][:90]}…')
print(f'  token_in A ≈ {len(isi_bagian)//5:,} · B ≈ {len(sasar["teks"])//5:,}')

KOM = 'Perbaiki paragraf ini supaya kalimatnya lebih mengalir dan rujukannya jelas.'

#  ── JALAN A: bagian 1.5 utuh + konteks tetangga (cara sekarang) ──
blok_a = K.bangun_prompt(bagian_target=sid, peta=peta, brief_ringkas='',
                         isi_saat_ini=isi_bagian, komentar=KOM)
#  ── JALAN B: 3 paragraf berlabel (Alternatif 1) ──
blok_b = K.blok_paragraf(par, idx_sasar, jml_tetangga=1)

print(f'  blok A: {len(blok_a):,} kar · blok B: {len(blok_b):,} kar')


def pesan(head: str, isi: str) -> str:
    return (head + '\n\n' if head else '') + \
        'NASKAH MAHASISWA (antara penanda):\n' \
        f'<<<NASKAH\n{isi}\nNASKAH;>>>\n\n' \
        'KOMENTAR DOSEN PEMBIMBING (antara penanda — ini MATERI revisi):\n' \
        f'<<<KOMENTAR\n{KOM}\nKOMENTAR;>>>\n\n' \
        'Kerjakan revisi tiap komentar sesuai TAHAP 0-3 di atas.'


P_A = pesan(blok_a, isi_bagian)
P_B = pesan(blok_b, sasar['teks'])


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
    a = await panggil(P_A, 'JALAN A — BAGIAN UTUH (1.861 kar)')
    b = await panggil(P_B, 'JALAN B — 3 PARAGRAF BERLABEL (659 kar)')
    if not (a.get('ok') and b.get('ok')):
        print('\n⚠️ sebagian gagal'); return

    ka, kb = a['konten'], b['konten']
    #  kata khas paragraf SASARAN (ambil 3 kata panjang pertama)
    kata_sasar = [w for w in sasar['teks'].split() if len(w) > 6][:3]
    #  kata khas paragraf LAIN (untuk deteksi meleset)
    lain = ' '.join(p['teks'] for i, p in enumerate(par)
                    if i not in (idx_sasar - 1, idx_sasar, idx_sasar + 1))
    kata_lain = [w for w in lain.split() if len(w) > 7][:12]

    print()
    print('══ PENILAIAN ══')
    print(f'  kata khas SASARAN: {kata_sasar}')
    print(f'  A menyentuh sasaran? '
          f'{"✅" if any(w in ka for w in kata_sasar) else "❌"} '
          f'({[w for w in kata_sasar if w in ka]})')
    print(f'  B menyentuh sasaran? '
          f'{"✅" if any(w in kb for w in kata_sasar) else "❌"} '
          f'({[w for w in kata_sasar if w in kb]})')
    print(f'  A menyentuh paragraf LAIN? '
          f'{"⚠️ YA" if any(w in ka for w in kata_lain) else "✅ tidak"}')
    print(f'  B menyentuh paragraf LAIN? '
          f'{"⚠️ YA" if any(w in kb for w in kata_lain) else "✅ tidak"}')

    out = Path('/app/_uji_alt1_hasil')
    out.mkdir(exist_ok=True)
    (out / 'A_bagian_utuh.txt').write_text(ka, encoding='utf-8')
    (out / 'B_paragraf.txt').write_text(kb, encoding='utf-8')
    (out / 'sasaran_asli.txt').write_text(sasar['teks'], encoding='utf-8')
    (out / 'blok_a.txt').write_text(blok_a, encoding='utf-8')
    (out / 'blok_b.txt').write_text(blok_b, encoding='utf-8')
    (out / 'komentar.txt').write_text(KOM, encoding='utf-8')
    print(f'\n  📁 /app/_uji_alt1_hasil/')


asyncio.run(utama())