#!/usr/bin/env python3
"""TULIS fungsi ALTERNATIF 1 (Peta Paragraf) ke app/konteks.py — tambah di AKHIR.

RANCANGAN (usul Wulan, ACC Bos "Opsi A, 5 - 1 - 2"):

MASALAH YANG DIPECAHKAN: dengan naskah penuh, AI tidak tahu bagian mana yang
dimaksud → dia memilih sendiri → MELESET (terbukti 25Sep26: 2 uji).

CARA KERJA:
  1. `petakan_paragraf(teks)` — pecah teks jadi paragraf bernomor:
       [P-01] paragraf pertama…
       [P-02] paragraf kedua…
     Nomor ini HANYA untuk konteks internal (tidak ditampilkan ke user).
  2. `pilih_paragraf(peta_par, komentar, teks_asli)` — cari paragraf yang
     paling cocok dengan komentar. Pakai `app/cari_bagian.py` yang SUDAH ADA
     (cari_bagian) — JANGAN bikin mesin pencari baru.
  3. `blok_paragraf(peta_par, idx, tetangga=1)` — susun blok:
       === PARAGRAF SASARAN ===
       [P-88] …
       === PARAGRAF SEBELUMNYA ===
       [P-87] …
       === PARAGRAF SESUDAHNYA ===
       [P-89] …
       → perintah: "kerjakan HANYA [P-88]"

HASIL YANG DIHARAPKAN: AI hanya melihat ±3 paragraf → MUSTAHIL meleset.
Keamanan: kalau paragraf tidak ketemu / terlalu sedikit → kembalikan ''
           (jalur lama tetap jalan, tidak error).
"""
from __future__ import annotations

import re
from typing import Any

KODE = r'''

#  ═══════════════════════════════════════════════════════════════════════════
#  ALTERNATIF 1 (25Sep26) — PETA PARAGRAF BERLABEL
#  ACC Bos: "Opsi A, 5 - 1 - 2" · langkah ke-2.
#
#  MASALAH: dengan naskah penuh AI tidak tahu bagian mana yang dimaksud →
#  memilih sendiri → MELESET. Dengan paragraf berlabel + tetangga paragraf,
#  AI hanya melihat 3 paragraf → tidak ada ruang untuk meleset.
#
#  KEAMANAN: semua fungsi di bawah HANYA MEMBACA & MENAMBAH teks. Tidak
#  mengubah cara potong kuota, tidak menyentuh ai.py. Gagal → '' (jujur).
#  ═══════════════════════════════════════════════════════════════════════════

_BATAS_PAR_PENDEK = 40      # paragraf lebih pendek dari ini dianggap sampah/daftar
_BATAS_PAR_TAMPIL = 1400    # batas tampil 1 paragraf di blok konteks
MAKS_PARAGRAF = 400         # pengaman: naskah raksasa jangan bikin lambat


def petakan_paragraf(teks: str) -> list[dict[str, Any]]:
    """Pecah teks jadi daftar paragraf BERLABEL.

    Return daftar butir:
        {'label': 'P-01', 'posisi': 1, 'teks': '…isi paragraf…',
         'awal': 1200, 'akhir': 1560}
    Label dipakai HANYA di dalam prompt (tidak pernah ditampilkan ke user).
    """
    t = teks or ''
    if not t.strip():
        return []
    #  pisah per baris kosong (pola naskah Word hasil ekstraksi)
    mentah = re.split(r'\n\s*\n', t)
    hasil: list[dict[str, Any]] = []
    ofs = 0
    for m in mentah:
        isi = m.strip()
        panjang_asli = len(m)
        if len(isi) >= _BATAS_PAR_PENDEK:
            hasil.append({
                'label': f'P-{len(hasil) + 1:02d}',
                'posisi': len(hasil) + 1,
                'teks': isi,
                'awal': ofs,
                'akhir': ofs + panjang_asli,
            })
            if len(hasil) >= MAKS_PARAGRAF:
                break
        ofs += panjang_asli + 1
    return hasil


def pilih_paragraf(par_list: list[dict[str, Any]], komentar: str,
                   teks_asli: str = '') -> int | None:
    """Cari INDEKS paragraf yang paling cocok dengan komentar.

    Pakai `app/cari_bagian.py` yang SUDAH ADA (jangan bikin mesin baru).
    Return None kalau tidak ketemu (jujur — jangan menebak).
    """
    if not par_list or not (komentar or '').strip():
        return None
    try:
        from .cari_bagian import cari_bagian
        gabung = '\n\n'.join(p['teks'] for p in par_list)
        hasil = cari_bagian(gabung, komentar, teks_asli or '')
        if not hasil or not hasil.get('ketemu'):
            return None
        #  cari paragraf mana yang memuat kutipan itu
        kutipan = (hasil.get('kutipan') or '').strip()[:60]
        if not kutipan:
            return None
        for i, p in enumerate(par_list):
            if kutipan in p['teks']:
                return i
        #  kutipan mungkin terpotong — coba potongan lebih pendek
        pendek = kutipan[:30]
        for i, p in enumerate(par_list):
            if pendek and pendek in p['teks']:
                return i
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konteks] pilih paragraf gagal (%s) → dilewati', e)
    return None


def blok_paragraf(par_list: list[dict[str, Any]], idx: int,
                  jml_tetangga: int = 1) -> str:
    """Susun blok PARAGRAF SASARAN + tetangga (sebelum & sesudah).

    Return '' kalau idx di luar batas / data tidak cukup.
    """
    if not par_list or not isinstance(idx, int):
        return ''
    if idx < 0 or idx >= len(par_list):
        return ''
    try:
        baris: list[str] = ['=== PETA PARAGRAF (sasaran jelas) ===']
        baris.append(f'Paragraf SASARAN: {par_list[idx]["label"]} '
                     f'(ke-{par_list[idx]["posisi"]} dari {len(par_list)})')

        for j in range(max(0, idx - jml_tetangga), idx):
            p = par_list[j]
            baris.append(f'\n--- {p["label"]} (SEBELUMNYA, jangan diubah) ---\n'
                         f'{potong(p["teks"], _BATAS_PAR_TAMPIL)}')

        p = par_list[idx]
        baris.append(f'\n--- {p["label"]} (SASARAN — kerjakan HANYA ini) ---\n'
                     f'{potong(p["teks"], _BATAS_PAR_TAMPIL)}')

        for j in range(idx + 1, min(len(par_list), idx + 1 + jml_tetangga)):
            p = par_list[j]
            baris.append(f'\n--- {p["label"]} (SESUDAHNYA, jangan diubah) ---\n'
                         f'{potong(p["teks"], _BATAS_PAR_TAMPIL)}')

        baris.append(f'\n⇒ KERJAKAN HANYA {par_list[idx]["label"]}. '
                     f'Paragraf berlabel lain HANYA konteks — JANGAN diubah, '
                     f'JANGAN diulang isinya.')
        return '\n'.join(baris)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konteks] blok paragraf gagal (%s) → dilewati', e)
        return ''


def isi_paragraf(par_list: list[dict[str, Any]], idx: int) -> str:
    """Isi teks paragraf sasaran (untuk `isi_saat_ini`)."""
    if not par_list or idx is None or idx < 0 or idx >= len(par_list):
        return ''
    return str(par_list[idx].get('teks') or '')
'''

with open('/opt/data/services/eduai-publishing/app/konteks.py', 'a',
          encoding='utf-8') as f:
    f.write(KODE)

import ast
src = open('/opt/data/services/eduai-publishing/app/konteks.py',
           encoding='utf-8').read()
ast.parse(src)
print(f'✅ KODE ditambahkan & sintaks OK · konteks.py = {len(src):,} byte')