#!/usr/bin/env python3
"""UJI BANDING MUTU (VERSI BENAR) — mengikuti cara PRODUKSI app/ai.py:1880-1915.

Bedanya dengan versi pertama Wulan (yang SALAH):
   ❌ versi 1: isi_saat_ini = SELURUH naskah → hasil selalu sebesar naskah
   ✅ versi 2: isi_saat_ini = HANYA bagian target (seperti produksi)

Ukuran:
   · panjang yang BENAR-BENAR dikirim AI (penuh vs potong)
   · apakah tetangga (sebelum/sesudah) ikut terbawa
   · Token Revisi masing-masing (rumus §4.13)
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as ST                                 # noqa: E402


def peta_dari(naskah):
    """peta bab seperti produksi: petakan(buang_daftar_isi(naskah))."""
    return ST.petakan(ST.buang_daftar_isi(naskah))


KANDIDAT = ['/app/_naskah_bos_uji.docx',
            '/app/_uji_doc/BAB1_drive_terbaru.docx']

naskah, path = '', ''
for p in KANDIDAT:
    if os.path.exists(p):
        naskah = A._teks_dari_berkas(Path(p), Path(p).name)
        if naskah and len(naskah) > 5000:
            path = p
            break
        naskah = ''

print('══ 0. NASKAH ══')
if not naskah:
    print('  ❌ TIDAK ADA → LEWATI'); sys.exit(77)
print(f'  {path} · {len(naskah):,} karakter')

#  peta bab
peta = peta_dari(naskah)
print(f'  peta bab: {len(peta)} bagian')
for x in peta[:8]:
    print(f"    · {x.get('section_id','?'):<12} {str(x.get('judul',''))[:45]} "
          f"({len(str(x.get('isi_teks','')))} kar)")

#  pilih bagian TENGAH (paling menantang)
if len(peta) < 3:
    print('  ❌ peta bab kurang dari 3 → LEWATI'); sys.exit(77)
tengah = len(peta) // 2
bag = peta[tengah]
sid = str(bag.get('section_id', ''))
isi_target = str(bag.get('isi_teks', ''))
print()
print(f'══ 1. BAGIAN TARGET: {sid} — {str(bag.get("judul",""))[:50]} ══')
print(f'  panjang bagian: {len(isi_target):,} karakter')
print(f'  tetangga: {peta[tengah-1].get("section_id","")} (sebelum) · '
      f'{peta[tengah+1].get("section_id","")} (sesudah)')

KOM = 'Perbaiki bagian ini supaya lebih jelas dan mengalir.'

#  ── JALAN A: SELURUH NASKAH ──────────────────────────────────────────
print()
print('══ 2. JALAN A — SELURUH NASKAH (cara lama) ══')
tok_a = len(naskah) // 5
print(f'  yang dikirim: {len(naskah):,} kar ≈ {tok_a:,} token_in')
print(f'  Token Revisi: {-(-tok_a // 10000)}')

#  ── JALAN B: PRODUKSI (potong + tetangga), isi_saat_ini = HANYA target ──
print()
print('══ 3. JALAN B — POTONG + KONTEKS TETANGGA (cara produksi) ══')
blok = K.bangun_prompt(
    bagian_target=sid,
    peta=peta,
    brief_ringkas='',
    isi_saat_ini=isi_target,          # ← HANYA bagian target (spt produksi)
    komentar=KOM,
)
tok_b = len(blok) // 5
print(f'  blok konteks : {len(blok):,} karakter')
print(f'  naskah dikirim: {len(isi_target):,} karakter (hanya target)')
print(f'  TOTAL ke AI   : {len(blok):,} kar ≈ {tok_b:,} token_in')
print(f'  Token Revisi  : {-(-tok_b // 10000)}')

#  ── UJI NYAMBUNG ─────────────────────────────────────────────────────
print()
print('══ 4. UJI NYAMBUNG — tetangga ikut terbawa? ══')
ada_target = isi_target[:60] in blok
seb = str(peta[tengah - 1].get('isi_teks', ''))[:60]
ses = str(peta[tengah + 1].get('isi_teks', ''))[:60]
print(f'  target  ikut? {"✅" if ada_target else "❌"}')
print(f'  sebelum ikut? {"✅ YA" if (seb and seb in blok) else "⚠️ TIDAK"}')
print(f'  sesudah ikut? {"✅ YA" if (ses and ses in blok) else "⚠️ TIDAK"}')
print()
print(f'  apakah blok menyebut struktur (peta bab)? '
      f'{"✅ YA" if (str(peta[tengah-1].get("section_id","")) in blok) else "⚠️ TIDAK"}')

#  ── RINGKASAN ────────────────────────────────────────────────────────
print()
print('══ 5. RINGKASAN (angka apa adanya) ══')
rasio = len(blok) / max(len(naskah), 1)
print(f'  penuh  : {len(naskah):>8,} kar ≈ {tok_a:>7,} tok  '
      f'{-(-tok_a // 10000)} Token Revisi')
print(f'  potong : {len(blok):>8,} kar ≈ {tok_b:>7,} tok  '
      f'{-(-tok_b // 10000)} Token Revisi')
print(f'  rasio  : {rasio:.2f}× → {"HEMAT" if rasio < 0.9 else "TIDAK HEMAT"}')
print(f'  hemat  : {100 - round(rasio * 100)}%')
