"""LAPIS 2 — JALUR SURVEYOR di rute /v1/peta/mulai.

DISIPLIN (aturan Bos & pelajaran hari ini):
  · JANGAN ganti bentuk balasan  → 5 pemakai lama TIDAK rusak.
  · SURVEYOR = jalur PERTAMA; gagal/miskin ⇒ FALLBACK peta_halus (berjejak).
  · `peta_halus` TIDAK dibuang (putusan Bos #4).

FUNGSI MURNI supaya bisa diuji tanpa HTTP & tanpa Jev:
    putuskan_jalur(peta_surveyor) -> ('jev'|'fallback', alasan:str)
"""
from __future__ import annotations

from typing import Any

# ── ambang minimal supaya surveyor dianggap LAYAK dipakai ──────────────
#    Alasan: peta kosong / tanpa bab = tidak lebih baik dari cara lama.
MIN_BAB = 1


def putuskan_jalur(peta_surveyor: dict[str, Any] | None) -> tuple[str, str]:
    """Putuskan pakai JEV atau FALLBACK — hanya dari ISI peta.

    Kembalikan (jalur, alasan):
        ('jev',      'bab=N sub=N')   peta surveyor layak dipakai
        ('fallback', '<sebab>')       kembali ke cara lama (peta_halus)

    ⚠️ "MATI" ≠ "RAGU". Ragu sebagian BUKAN alasan fallback — itu urusan
    hakim/goyang. Fallback HANYA untuk: None · bukan dict · tanpa label ·
    tanpa bab sama sekali.
    """
    if peta_surveyor is None:
        return 'fallback', 'surveyor mati/tidak tersedia'
    if not isinstance(peta_surveyor, dict):
        return 'fallback', f'bentuk tidak sah: {type(peta_surveyor).__name__}'

    label = peta_surveyor.get('label')
    if not isinstance(label, dict) or not label:
        return 'fallback', 'peta tanpa label'

    bab = sum(1 for v in label.values() if v == 'bab')
    sub = sum(1 for v in label.values() if v == 'subbab')
    if bab < MIN_BAB:
        #  Bab dari `gabung` (kode, STABIL) juga dihitung — lihat catatan
        #  CATATAN_KEPUTUSAN_PETA3: "BAB = len(gabung) + label bab non-sistematika".
        try:
            gabung = peta_surveyor.get('gabung') or {}
            bab += len(gabung)
        except Exception:
            pass
        if bab < MIN_BAB:
            return 'fallback', f'surveyor tidak menemukan bab (sub={sub})'

    return 'jev', f'bab={bab} sub={sub}'
