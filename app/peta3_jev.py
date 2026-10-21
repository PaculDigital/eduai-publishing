"""MODUL PETA 3 TINGKAT (SURVEYOR JEV) — pembungkus resmi untuk produksi.

═══════════════════════════════════════════════════════════════════════════
KENAPA BERKAS INI ADA (14 Okt 2026)

`peta3_jev.py` di root proyek = SKRIP CLI. Ia punya:
    · `sys.path.insert(0, '/app')`  (baris 14)
    · impor level-atas `from app.ai import SessionLocal, ...` (baris 15)
    · `def main()` + `if __name__ == '__main__'` (baris 346/383)

⇒ TIDAK boleh diimpor langsung dari rute produksi: impor level-atasnya
  menarik `app.ai` (putaran impor) dan `sys.path.insert` merebut jalur.

PUTUSAN BOS 14 Okt 2026:
    "Peta3_jev mengganti peta halus, sesuai uji dan keputusan 08/09 okt."
    "Peta halus dan kasar yang sebelumnya jangan di buang dan jadikan
     fallback jika jev dan hakim mati."

CARA KERJA BERKAS INI = **PEMBUNGKUS**, bukan salinan:
    · memuat `peta3_jev.py` sebagai modul lewat `importlib` (jalur eksplisit)
    · TIDAK menyalin satu baris logika pun dari `peta3_jev.py`
      ⇒ "satu sumber kebenaran" tetap dipertahankan (aturan induk Bos)
    · impor `app.ai` terjadi DI DALAM fungsi ⇒ tidak ada putaran impor

URUTAN RESMI (TERKUNCI 09 Okt) — jangan diubah:
    JEV SURVEYOR (berkas ini) → JEV HAKIM → MESIN (`peta_jembatan`) → AI

PAGAR:
    P1  JANGAN menyalin logika peta3_jev ke sini. Kalau peta3_jev diubah,
        modul ini OTOMATIS ikut — itu tujuan pembungkus.
    P2  Kalau surveyor gagal/mati ⇒ kembalikan None ⇒ pemanggil KEMBALI ke
        cara lama (`peta_halus`/`state.petakan`). Jev mati TIDAK BOLEH
        menghentikan produksi.
    P3  JANGAN pakai berkas ini di jalur biaya secara diam-diam. Pembungkus
        TIDAK menyentuh satpam; panggilan Jev tetap lewat peta3_jev apa adanya.
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import importlib.util
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# ── lokasi skrip asli (JANGAN disalin ke sini) ─────────────────────────────
_DIR_APP = os.path.dirname(os.path.abspath(__file__))          # .../app
_DIR_PROYEK = os.path.dirname(_DIR_APP)                        # .../eduai-publishing
_KANDIDAT_JALUR = (
    os.path.join(_DIR_PROYEK, 'peta3_jev.py'),                 # host: root proyek
    '/app/peta3_jev.py',                                       # container (COPY)
)

_mod = None          # cache modul (dimuat sekali per proses)
_gagal_muat = None   # simpan pesan gagal supaya tidak dicoba berulang


def _muat() -> Any | None:
    """Muat `peta3_jev.py` sebagai modul. None kalau tidak bisa (pagar P2)."""
    global _mod, _gagal_muat
    if _mod is not None:
        return _mod
    if _gagal_muat is not None:
        return None

    jalur = next((p for p in _KANDIDAT_JALUR if os.path.exists(p)), None)
    if not jalur:
        _gagal_muat = f'peta3_jev.py tidak ditemukan di: {_KANDIDAT_JALUR}'
        log.warning('[peta3_jev] %s', _gagal_muat)
        return None

    #  ⚠️ `peta3_jev.py` melakukan `sys.path.insert(0,'/app')` + impor
    #     `app.ai` saat dimuat. Impor itu AMAN di sini karena kita SUDAH
    #     berada di dalam proses app (app.* sudah termuat lebih dulu).
    try:
        spec = importlib.util.spec_from_file_location('_peta3_jev_root', jalur)
        if spec is None or spec.loader is None:
            _gagal_muat = f'spec tidak bisa dibentuk untuk {jalur}'
            log.warning('[peta3_jev] %s', _gagal_muat)
            return None
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _mod = m
        log.info('[peta3_jev] modul surveyor dimuat dari %s', jalur)
        return _mod
    except Exception as e:                                   # pagar P2
        _gagal_muat = f'{type(e).__name__}: {e}'
        log.warning('[peta3_jev] gagal muat modul surveyor: %s', _gagal_muat)
        return None


def tersedia() -> bool:
    """Apakah surveyor bisa dipakai? (untuk pemanggil memutuskan fallback)."""
    return _muat() is not None


def alasan_gagal() -> str | None:
    """Pesan kenapa surveyor tidak bisa dipakai (None = tidak ada masalah)."""
    _muat()
    return _gagal_muat


def petakan(fid: int, awal: int | None = None,
            akhir: int | None = None, putaran: int | None = None) -> dict | None:
    """PETA 3 TINGKAT dari surveyor. Format SAMA dengan `peta3_jev.petakan()`.

    Kembalikan **None** kalau surveyor tidak bisa dipakai (pagar P2) —
    pemanggil WAJIB menyiapkan fallback ke `peta_halus`/`state.petakan`.

    Bentuk: {'baris','kand','label','p','gabung','sistematika',
             'boleh_dipakai_fitur','...'} — lihat `peta3_jev.petakan()`.

    ⚠️ `putaran=None` (14 Okt 2026) ⇒ biarkan skrip asli yang memutuskan
    (baca `EDUAI_JEVI_PUTARAN`, bawaan 1). DULU di sini `=3` EKSPLISIT
    sehingga env apa pun DIABAIKAN — jebakan nyata, sudah terukur.
    """
    m = _muat()
    if m is None:
        return None
    try:
        return m.petakan(fid, awal, akhir, putaran)
    except Exception as e:                                   # pagar P2
        log.warning('[peta3_jev] surveyor gagal memetakan fid=%s: %s: %s',
                    fid, type(e).__name__, e)
        return None


def petakan_teks(teks: str, awal: int | None = None,
                 akhir: int | None = None, putaran: int | None = None) -> dict | None:
    """PETA dari TEKS LANGSUNG (tanpa fid) — untuk pemakai yang sudah punya teks.

    Dipakai pintu LAYAR (Lapis 5): `versi._deteksi_bagian(teks)` sudah memegang
    teks naskah dan TIDAK boleh menebak fid. Skrip asli tetap satu sumber
    kebenaran — kita hanya MENYIAPKAN `susun`-nya, bukan menyalin logikanya.

    ⚠️ `peta3_jev.susun(fid)` bekerja dari fid; untuk teks kita tiru bahan
    masukan `petakan()` dengan menyuntik teks yang sudah dibersihkan.
    Kembalikan **None** kalau tidak bisa (pagar P2).

    ⚠️ `putaran=None` (14 Okt 2026) ⇒ skrip asli yang memutuskan
    (`EDUAI_JEVI_PUTARAN`, bawaan 1). DULU `=3` eksplisit ⇒ env diabaikan.
    """
    m = _muat()
    if m is None:
        return None
    try:
        return m.petakan_dari_teks(teks, awal, akhir, putaran)
    except AttributeError:
        #  skrip asli belum punya jalur teks ⇒ jangan mengarang: None saja,
        #  pemanggil memakai fallback (perilaku lama).
        log.info('[peta3_jev] skrip asli belum punya petakan_dari_teks')
        return None
    except Exception as e:                                   # pagar P2
        log.warning('[peta3_jev] surveyor gagal memetakan teks: %s: %s',
                    type(e).__name__, e)
        return None
