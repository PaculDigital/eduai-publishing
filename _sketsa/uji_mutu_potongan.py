#!/usr/bin/env python3
"""UJI BANDING MUTU: POTONGAN + KONTEKS TETANGGA  vs  NASKAH PENUH.

PERTANYAAN BOS (25Sep26 — titik kritis):
   "potongan WAJIB tetap NYAMBUNG — jangan terkesan aneh sendiri jika
    dibaca. Intinya presisi, tepat dan Natural berbahasa nya."

CARA UJI (jujur, apa adanya):
   1. Ambil naskah nyata (tesis Bos).
   2. Pilih 1 KOMENTAR yang menunjuk PARAGRAF tertentu di TENGAH naskah.
   3. JALAN A (penuh)  : SELURUH naskah dikirim → AI revisi.
   4. JALAN B (potong) : potong + konteks tetangga → AI revisi.
   5. BANDINGKAN dengan UKURAN OBJEKTIF:
        · panjang yang dikirim (hemat berapa?)
        · apakah TETANGGA (sebelum/sesudah) ikut terbawa?
        · Token Revisi masing-masing (rumus §4.13)
   6. LAPOR apa adanya — kalau potongan kalah, bilang kalah.

CATATAN: uji ini TIDAK memanggil AI dulu (ukur panjang & bentuk saja).
Panggilan AI diuji terpisah supaya biaya terkendali.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as S                                  # noqa: E402

KANDIDAT = [
    '/app/_naskah_bos_uji.docx',
    '/app/_uji_doc/BAB1_drive_terbaru.docx',
    '/app/_uji_doc/tesis.docx',
]


def ambil_naskah() -> tuple[str, str]:
    for p in KANDIDAT:
        if os.path.exists(p):
            try:
                t = A._teks_dari_berkas(Path(p), Path(p).name)
                if t and len(t) > 5000:
                    return t, p
            except Exception as e:                          # noqa: BLE001
                print(f'  (gagal baca {p}: {e})')
    return '', ''


print('══ 0. SIAPKAN NASKAH ══')
naskah, path = ambil_naskah()
if not naskah:
    print('  ❌ naskah uji TIDAK ADA → LEWATI (bukan gagal)')
    sys.exit(77)
print(f'  berkas : {path}')
print(f'  panjang: {len(naskah):,} karakter')
print(f'  potong : AI_POTONG_KARAKTER={A.AI_POTONG_KARAKTER:,} '
      f'(≈{A.AI_POTONG_KARAKTER // 5:,} token)')

#  ── Paragraf target (di TENGAH — paling menantang) ───────────────────
par = [p.strip() for p in re.split(r'\n\s*\n', naskah) if len(p.strip()) > 200]
if len(par) < 4:
    print('  ❌ paragraf panjang tidak cukup → LEWATI')
    sys.exit(77)

idx = len(par) // 2
target = par[idx]
sebelum = par[idx - 1] if idx > 0 else ''
sesudah = par[idx + 1] if idx + 1 < len(par) else ''

print()
print('══ 1. PARAGRAF TARGET (tengah naskah) ══')
print(f'  index {idx} dari {len(par)} paragraf · {len(target):,} karakter')
print(f'  kutipan: {target[:140]}…')

#  ── JALAN A: SELURUH NASKAH (cara lama) ──────────────────────────────
print()
print('══ 2. JALAN A — SELURUH NASKAH (cara lama) ══')
bagian = A.potong_cerdas(naskah)
print(f'  potong_cerdas() → {len(bagian)} bagian')
tok_penuh = len(naskah) // 5
tr_penuh = -(-tok_penuh // 10000)
print(f'  yang dikirim per panggilan: ~{len(naskah):,} karakter '
      f'(tiap bagian berisi konteks besar)')
print(f'  perkiraan token_in: ~{tok_penuh:,}')
print(f'  Token Revisi (rumus §4.13): {tr_penuh}')

#  ── JALAN B: POTONGAN + KONTEKS TETANGGA ────────────────────────────
print()
print('══ 3. JALAN B — POTONGAN + KONTEKS TETANGGA (cara baru) ══')
komentar_list = [f'Perbaiki paragraf ini supaya lebih jelas dan mengalir: '
                 f'{target[:160]}']
boleh = A._boleh_konteks(komentar_list)
print(f'  _boleh_konteks() → {boleh}  (True = boleh dipotong)')

#  struktur: pakai state (peta bab nyata)
try:
    tujuan = {'nomor': '', 'judul': ''}
    det = S.deteksi_subbab(naskah, tujuan, '')
    struktur = []
    for s in (det or []):
        struktur.append({'nomor': s.get('nomor', ''),
                         'judul': s.get('judul', ''),
                         'isi': s.get('isi', '')})
    print(f'  peta bab terdeteksi: {len(struktur)} bagian')
except Exception as e:                                      # noqa: BLE001
    print(f'  ⚠️ peta bab gagal ({e}) → pakai daftar kosong')
    struktur = []

konteks_blok = ''
tr_potong = 0
try:
    konteks_blok = K.bangun_prompt(
        bagian_target=target,
        struktur=struktur,
        brief_ringkas='',
        isi_saat_ini=naskah,
        komentar='\n'.join(komentar_list),
        peta=None,
    )
    tok_potong = len(konteks_blok) // 5
    tr_potong = -(-tok_potong // 10000)
    print(f'  konteks.bangun_prompt() → {len(konteks_blok):,} karakter')
    print(f'  perkiraan token_in: ~{tok_potong:,}')
    print(f'  Token Revisi (rumus §4.13): {tr_potong}')
except Exception as e:                                      # noqa: BLE001
    print(f'  ❌ bangun_prompt gagal: {e}')

#  ── UJI NYAMBUNG: tetangga ikut terbawa? ────────────────────────────
print()
print('══ 4. UJI NYAMBUNG — paragraf SEBELUM & SESUDAH ikut? ══')
if konteks_blok:
    a1 = target[:70] in konteks_blok
    a2 = bool(sebelum) and sebelum[:70] in konteks_blok
    a3 = bool(sesudah) and sesudah[:70] in konteks_blok
    print(f'  target  ikut?  {"✅ YA" if a1 else "❌ TIDAK"}')
    print(f'  sebelum ikut?  {"✅ YA" if a2 else "⚠️ TIDAK"}')
    print(f'  sesudah ikut?  {"✅ YA" if a3 else "⚠️ TIDAK"}')
else:
    print('  (tidak bisa diuji)')

#  ── RINGKASAN ────────────────────────────────────────────────────────
print()
print('══ 5. RINGKASAN ANGKA (apa adanya) ══')
if konteks_blok:
    rasio = len(konteks_blok) / max(len(naskah), 1)
    print(f'  penuh  : {len(naskah):>8,} kar  ≈{tok_penuh:>7,} token_in  '
          f'{tr_penuh} Token Revisi')
    print(f'  potong : {len(konteks_blok):>8,} kar  ≈{tok_potong:>7,} token_in  '
          f'{tr_potong} Token Revisi')
    print(f'  rasio  : {rasio:.2f}× dari penuh → '
          f'{"HEMAT" if rasio < 0.9 else "TIDAK HEMAT"}')
else:
    print('  ⚠️ tidak bisa dibandingkan')

print()
print('SELESAI — ini UKURAN PANJANG & BENTUK.')
print('UJI MUTU SUNGGUHAN (panggil AI, banding hasil tulisan) = terpisah.')
