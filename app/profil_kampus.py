"""PROFIL KAMPUS — ambang aturan Jev/Hakim dari CONFIG, bukan hardcode.

═══════════════════════════════════════════════════════════════════════════
KENAPA ADA (10 Nov 2026 — tahan ribuan jenis naskah):
  Aturan deterministik (mis. "judul >300 karakter") punya angka. Angka itu
  BUKAN hukum alam — kampus lain bisa punya judul sah yang lebih panjang.
  Supaya tidak hardcode per kampus di kode, angka dibaca dari
  `profil/kampus.json` (JSON murni, tanpa dependensi baru):
      {"aturan": {"judul_maks_kar": 300, "subbab_kode_maks_kar": 120},
       "kampus": {"UPB": {"judul_maks_kar": 300}}}
  · Tidak ada berkas ⇒ bawaan di bawah (aman).
  · Berkas rusak ⇒ bawaan + log peringatan (jangan gagalkan pemetaan).
  · Profil kampus hanya MENIMPA angka di atas, tidak menambah aturan baru.
  · Nama kampus diambil dari pemanggil bila ada; tanpa nama ⇒ "aturan" umum.
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

BAWAAN = {
    'judul_maks_kar': 300,        # Aturan 2 / hakim: judul lebih panjang ⇒ paragraf/curiga
    'subbab_kode_maks_kar': 120,  # baris bernomor dibaca kode: maks panjang judul
}

_cache: dict = {'jalur': None, 'mtime': None, 'isi': None}


def _jalur_kandidat() -> list[Path]:
    env = (os.getenv('EDUAI_PROFIL_KAMPUS') or '').strip()
    keluar = []
    if env:
        keluar.append(Path(env))
    keluar.append(Path(__file__).resolve().parent.parent / 'profil' / 'kampus.json')
    keluar.append(Path('/app/profil/kampus.json'))
    return keluar


def muat() -> dict:
    """Baca config profil (cache per mtime). Selalu kembalikan dict."""
    for jalur in _jalur_kandidat():
        try:
            if not jalur.is_file():
                continue
            mtime = jalur.stat().st_mtime
            if _cache.get('jalur') == str(jalur) and _cache.get('mtime') == mtime:
                return _cache.get('isi') or {}
            isi = json.loads(jalur.read_text(encoding='utf-8'))
            if not isinstance(isi, dict):
                raise ValueError('profil kampus bukan objek JSON')
            _cache.update({'jalur': str(jalur), 'mtime': mtime, 'isi': isi})
            return isi
        except Exception as e:                                  # jangan gagalkan
            log.warning('[profil_kampus] %s tidak bisa dipakai (%s: %s) — pakai bawaan',
                        jalur, type(e).__name__, e)
            continue
    return {}


def aturan(nama_kampus: str | None = None) -> dict:
    """Ambang efektif: bawaan ← aturan umum ← profil kampus (bila ada)."""
    isi = muat()
    keluar = dict(BAWAAN)
    umum = isi.get('aturan')
    if isinstance(umum, dict):
        for k, v in umum.items():
            if k in keluar and isinstance(v, (int, float)):
                keluar[k] = v
    if nama_kampus:
        kampus = (isi.get('kampus') or {}).get(nama_kampus)
        if isinstance(kampus, dict):
            for k, v in kampus.items():
                if k in keluar and isinstance(v, (int, float)):
                    keluar[k] = v
    return keluar
