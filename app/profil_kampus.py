"""PROFIL KAMPUS — ambang aturan Jev/Hakim dari CONFIG, bukan hardcode.

═══════════════════════════════════════════════════════════════════════════
KENAPA ADA (10 Nov 2026 — tahan ribuan jenis naskah):
  Aturan deterministik (mis. "judul >300 karakter") punya angka. Angka itu
  BUKAN hukum alam — kampus lain bisa punya judul sah yang lebih panjang.
  Supaya tidak hardcode per kampus di kode, angka dibaca dari
  `profil/kampus.json` (JSON murni, tanpa dependensi baru):
      {"aturan": {"judul_maks_kar": 300, "subbab_kode_maks_kar": 120},
       "istilah": {"kuesioner": ["kuesioner", "angket"]},
       "penomoran": {"judul_titik_akhir": false},
       "kampus": {"UPB": {"judul_maks_kar": 300}}}
  · Tidak ada berkas ⇒ bawaan di bawah (aman).
  · Berkas rusak ⇒ bawaan + log peringatan (jangan gagalkan pemetaan).
  · Profil kampus hanya MENIMPA angka/istilah/aturan di atas, tidak
    menambah aturan baru.
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

# ── ISTILAH (v6, 10 Nov 2026) ────────────────────────────────────────────
#    Satu konsep, banyak sebutan per kampus: "kuesioner" di satu kampus =
#    "angket" di kampus lain (temuan 09 Okt 2026). Aturan 3 (judul
#    KUESIONER = lampiran, bukan struktur) memakai daftar ini, bukan
#    hardcode dua kata di kode. Kampus boleh menambah sebutannya sendiri
#    di config ("daftar pertanyaan", ...).
BAWAAN_ISTILAH = {
    'kuesioner': ['kuesioner', 'angket'],
}

# ── PENOMORAN (v6, 10 Nov 2026) ──────────────────────────────────────────
#    Gaya penomoran judul per kampus. `judul_titik_akhir`: True bila judul
#    bernomor di kampus itu BOLEH diakhiri titik ("1.1. Latar Belakang.")
#    dan tetap dibaca kode sebagai sub-bab. False (bawaan) = titik akhir
#    berarti kalimat, bukan judul (perilaku lama). Nomor bertitik
#    ("1.1. Latar Belakang", titik sesudah ANGKA) selalu diterima kode —
#    itu format penomoran, bukan titik akhir kalimat.
BAWAAN_PENOMORAN = {
    'judul_titik_akhir': False,
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


def _bagian_config(isi: dict, nama_bagian: str, nama_kampus: str | None,
                   bawaan: dict) -> dict:
    """Gabung satu bagian config: bawaan ← umum ← profil kampus."""
    keluar = {k: (list(v) if isinstance(v, list) else v)
              for k, v in bawaan.items()}
    umum = isi.get(nama_bagian)
    if isinstance(umum, dict):
        for k, v in umum.items():
            # `v` kosong (list kosong / False) tidak menimpa — KECUALI False
            # yang sah untuk kunci bool (kampus boleh mematikan aturan).
            if k in keluar and type(v) is type(keluar[k]) \
                    and (v or isinstance(v, bool)):
                keluar[k] = list(v) if isinstance(v, list) else v
    if nama_kampus:
        kampus = (isi.get('kampus') or {}).get(nama_kampus)
        if isinstance(kampus, dict):
            bagian = kampus.get(nama_bagian)
            if isinstance(bagian, dict):
                for k, v in bagian.items():
                    if k in keluar and type(v) is type(keluar[k]) \
                            and (v or isinstance(v, bool)):
                        keluar[k] = list(v) if isinstance(v, list) else v
    return keluar


def istilah(nama_kampus: str | None = None) -> dict:
    """Istilah efektif: {'kuesioner': ['kuesioner', 'angket', ...]}."""
    return _bagian_config(muat(), 'istilah', nama_kampus, BAWAAN_ISTILAH)


def penomoran(nama_kampus: str | None = None) -> dict:
    """Aturan penomoran efektif: {'judul_titik_akhir': bool}."""
    return _bagian_config(muat(), 'penomoran', nama_kampus, BAWAAN_PENOMORAN)
