"""Narasi BAB IV — lahir HANYA dari hasil yang TERKUNCI.

Aturan sumber angka (§13 dokumen induk): semua angka di narasi
diambil dari hasil terkunci (termasuk peta_hipotesis di dalamnya)
dan profil data — AI TIDAK mengarang dan TIDAK membulatkan ulang.
Alur: susun draf deterministik dari angka → poles bahasa dengan AI
lewat pintu tunggal app.ai._panggil_router (system prompt melarang
mengubah angka) → bila AI gagal, draf deterministik tetap dipakai.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from . import bab4
from .models import DataLapanganBab4, HasilBab4, User


def kumpulkan_bahan(db: Session, u: User, file_id: int) -> dict | None:
    """Bahan narasi. None bila belum ada hasil terkunci (gerbang
    Kunci Hasil: narasi tidak lahir dari angka yang masih draf)."""
    terkunci = bab4.hasil_terkunci(db, u.id, file_id, 'olah_data')
    if terkunci is None:
        return None
    hasil = bab4.baca_hasil(terkunci)
    peta_row = (db.query(bab4.PetaBab4)
                .filter_by(user_id=u.id, file_id=file_id)
                .order_by(bab4.PetaBab4.nomor.desc()).first())
    peta = bab4.baca_peta(peta_row) if peta_row else {}
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap='utama').first())
    masuk = len(json.loads(d.baris or '[]')) if d else 0
    target = d.target_responden if d else None
    pra = (db.query(HasilBab4)
           .filter_by(user_id=u.id, file_id=file_id, jenis='pra_survei')
           .order_by(HasilBab4.nomor.desc()).first())
    kartu = (bab4.kartu_kesehatan(bab4.baca_hasil(pra))
             if pra is not None else None)
    return {'hasil': hasil, 'versi_terkunci': terkunci.nomor,
            'mode': terkunci.mode, 'peta': peta,
            'responden_masuk': masuk, 'target': target,
            'pengembalian': bab4.tingkat_pengembalian(masuk, target),
            'kartu_pra': kartu}


def _fmt(x, bawaan='—'):
    return bawaan if x is None else (f'{x:.4f}' if isinstance(x, float)
                                     else str(x))


def susun_draf(b: dict) -> str:
    """Draf 4.1–4.4 deterministik — angka persis dari hasil."""
    h = b['hasil']
    peta_h = h.get('peta_hipotesis') or []
    variabel = (b['peta'] or {}).get('variabel') or []
    daftar_var = '; '.join(
        f"{v.get('nama')} ({ {'X': 'variabel bebas', 'M': 'variabel perantara', 'Z': 'variabel penguat', 'Y': 'variabel terikat'}.get(v.get('peran'), v.get('peran')) })"
        for v in variabel if isinstance(v, dict))
    L = ['# BAB IV', '# HASIL DAN PEMBAHASAN', '']
    L += ['## 4.1 Gambaran Umum Objek Penelitian', '',
          f'Penelitian ini mengkaji {daftar_var}. '
          f'Data yang kembali dan layak diolah berjumlah '
          f"{b['responden_masuk']} responden"
          + (f" dari target {b['target']} "
             f"({b['pengembalian']}%)." if b['target'] else '.')]
    if b.get('kartu_pra'):
        k = b['kartu_pra']
        L.append('Sebelum penyebaran utama, instrumen diuji coba: '
                 + ('seluruh butir dinyatakan sehat.'
                    if k['semua_sehat'] else
                    f"{len(k['butir_lemah'])} butir diperbaiki "
                    'kata-katanya berdasarkan hasil uji coba.'))
    L += ['', '## 4.2 Hasil Penelitian', '']
    if h.get('r2') is not None:
        L.append(f"Koefisien determinasi (R²) model adalah "
                 f"{_fmt(h.get('r2'))}, artinya variabel bebas "
                 'menjelaskan bagian tersebut dari keragaman variabel '
                 'terikat; sisanya dijelaskan faktor lain di luar model.')
    for e in peta_h:
        if e.get('jenis') == 'interaksi':
            L.append(f"- {e.get('hipotesis')} (moderasi): "
                     f"{e.get('ringkas') or 'lihat hasil moderasi.'}")
        else:
            L.append(f"- {e.get('hipotesis')}: pengaruh "
                     f"{e.get('dari')} terhadap {e.get('ke')} "
                     f"sebesar {_fmt(e.get('b'))} dengan nilai "
                     f"signifikansi {_fmt(e.get('p'))} — hipotesis "
                     f"{'diterima' if e.get('signifikan') else 'ditolak'}.")
    L += ['', '## 4.3 Pengujian Hipotesis', '']
    for e in peta_h:
        L.append(f"- {e.get('hipotesis')}: "
                 f"{e.get('ringkas') or 'tidak ditemukan di hasil.'}")
    L += ['', '## 4.4 Pembahasan', '']
    for e in peta_h:
        putusan = ('sejalan dengan hipotesis yang diajukan'
                   if e.get('signifikan') else
                   'tidak mendukung hipotesis yang diajukan')
        L.append(f"Hasil pengujian {e.get('hipotesis')} "
                 f"({e.get('dari')} → {e.get('ke')}) {putusan}. "
                 '(Kaitkan temuan ini dengan teori dan penelitian '
                 'terdahulu di Bab II.)')
    return '\n'.join(L) + '\n'


ATURAN_POLES = (
    'Kamu memoles draf BAB IV skripsi berbahasa Indonesia. ATURAN '
    'KERAS: (1) DILARANG mengubah, menambah, atau membulatkan angka '
    'apa pun — semua angka harus persis seperti draf. (2) DILARANG '
    'menambah klaim, teori, nama ahli, atau sitasi baru. (3) Hanya '
    'perbaiki alur kalimat, pilihan kata akademik, dan transisi antar'
    'kalimat. (4) Pertahankan struktur subbab dan daftar butirnya. '
    'Kembalikan teks utuh hasil polesan, tanpa komentar.')


async def poles_ai(draf: str) -> tuple[str, bool]:
    """Poles lewat pintu AI tunggal. (teks, berhasil?) — gagal →
    kembalikan draf asli; narasi tidak boleh gagal total karena AI."""
    try:
        from .ai import _panggil_router
        teks, _info = await _panggil_router(draf, 120.0, system=ATURAN_POLES)
        teks = (teks or '').strip()
        return (teks, True) if teks else (draf, False)
    except Exception:  # noqa: BLE001
        return draf, False
