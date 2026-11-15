"""Antrean admin pemeriksaan struktur (15 Nov 2026, alur pilot Jev/Hakim).

Mahasiswa TIDAK PERNAH ditanya apa pun. Baris yang Hakim tandai ragu /
curiga masuk antrean ini; yang memutuskan hanya admin (Boss) lewat pilihan
ganda BAB / SUB-BAB / PARAGRAF / BIASA + "Lewati", satu ketuk, tanpa mengetik.

Keputusan admin DIREKAM sebagai ground truth baru (loop belajar): baris +
tetangga + label Jev + label akhir + pilihan admin tersimpan di baris ini.
Bila keputusan bukan "Lewati", label baris itu di peta tersimpan ikut
diperbarui supaya mahasiswa melihat hasil putusan (bukan lagi
"sedang diperiksa").

Pembuat baris (`bangun_baris_antrean`) MURNI supaya gampang diuji; fungsi DB
(`isi_antrean`, `putuskan`) mengimpor model secara malas.
"""
from __future__ import annotations

import json

KEPUTUSAN_SAH = ('bab', 'subbab', 'paragraf', 'biasa', 'lewati')
STATUS_MENUNGGU = 'menunggu'


def _ringkas(teks: str, maks: int = 500) -> str:
    t = ' '.join(str(teks or '').split()).strip()
    return t[:maks]


def bangun_baris_antrean(*, audit_bagian, baris, label_akhir,
                         file_id: int, user_id: int,
                         peta_sidik: str) -> list[dict]:
    """Bangun baris antrean dari jejak Hakim (murni).

    `audit_bagian`: list dict Hakim `{i, label, status, alasan}`.
    `baris`: daftar baris surveyor (teks lengkap per baris).
    `label_akhir`: label final per baris di peta (sesudah agen kedua +
    aturan), dict {int: str}.
    Hanya status 'ragu' / 'curiga' yang masuk antrean.
    """
    keluar = []
    baris = list(baris or [])
    for b in (audit_bagian or []):
        if not isinstance(b, dict):
            continue
        if b.get('status') not in ('ragu', 'curiga'):
            continue
        try:
            i = int(b.get('i'))
        except (TypeError, ValueError):
            continue
        if i < 0 or i >= len(baris):
            continue
        tetangga = {
            'atas': _ringkas(baris[i - 1]) if i > 0 else '',
            'bawah': _ringkas(baris[i + 1]) if i + 1 < len(baris) else '',
        }
        keluar.append({
            'file_id': int(file_id), 'user_id': int(user_id),
            'peta_sidik': str(peta_sidik or ''),
            'baris_idx': i,
            'teks': _ringkas(baris[i], 1000),
            'tetangga': tetangga,
            'label_jev': str(b.get('label') or ''),
            'label_akhir': str((label_akhir or {}).get(i)
                               or (label_akhir or {}).get(str(i)) or ''),
            'status_hakim': str(b.get('status') or ''),
            'alasan': list(b.get('alasan') or []),
        })
    return keluar


def isi_antrean(db, *, file_id: int, user_id: int, peta_sidik: str,
                simpan: dict) -> int:
    """Isi antrean dari peta tersimpan yang diperkaya (idempoten).

    `simpan`: dict hasil `siapkan_simpan` (membawa `peta_surveyor` +
    `hakim_bagian`). Baris yang sudah ada untuk (file_id, peta_sidik,
    baris_idx) tidak diduplikasi. Kembalikan jumlah baris BARU.
    Gagal apa pun -> 0 (jangan pernah menggagalkan pemeriksaan).
    """
    try:
        from .models import AntreanPeta
        surveyor = (simpan or {}).get('peta_surveyor') or {}
        baris = surveyor.get('baris') or []
        label = surveyor.get('label') or {}
        audit = (simpan or {}).get('hakim_bagian') or []
        calon = bangun_baris_antrean(
            audit_bagian=audit, baris=baris, label_akhir=label,
            file_id=file_id, user_id=user_id, peta_sidik=peta_sidik)
        baru = 0
        for c in calon:
            ada = db.query(AntreanPeta).filter(
                AntreanPeta.file_id == c['file_id'],
                AntreanPeta.peta_sidik == c['peta_sidik'],
                AntreanPeta.baris_idx == c['baris_idx']).first()
            if ada is not None:
                continue
            db.add(AntreanPeta(
                file_id=c['file_id'], user_id=c['user_id'],
                peta_sidik=c['peta_sidik'], baris_idx=c['baris_idx'],
                teks=c['teks'],
                tetangga=json.dumps(c['tetangga'], ensure_ascii=False),
                label_jev=c['label_jev'], label_akhir=c['label_akhir'],
                status_hakim=c['status_hakim'],
                alasan=json.dumps(c['alasan'], ensure_ascii=False),
                status=STATUS_MENUNGGU, keputusan=''))
            baru += 1
        if baru:
            db.commit()
        return baru
    except Exception:                                           # noqa: BLE001
        try:
            db.rollback()
        except Exception:                                       # noqa: BLE001
            pass
        return 0


def putuskan(db, *, antrean_id: int, keputusan: str,
             admin_id: int) -> dict:
    """Rekam keputusan admin atas satu baris antrean.

    `keputusan`: 'bab' | 'subbab' | 'paragraf' | 'biasa' | 'lewati'.
    'lewati' = status 'dilewati', tanpa label (bisa diputuskan nanti).
    Selain itu status 'diputuskan' + label baris di peta tersimpan ikut
    diperbarui ke pilihan admin (satu-satunya penulisan ke peta di sini).
    """
    from .models import AntreanPeta, ProfilDokumen, _now
    keputusan = str(keputusan or '').strip().lower()
    if keputusan not in KEPUTUSAN_SAH:
        return {'ok': False, 'pesan': 'Pilihan tidak dikenal.'}
    row = db.get(AntreanPeta, int(antrean_id))
    if row is None:
        return {'ok': False, 'pesan': 'Butir antrean tidak ditemukan.'}
    row.keputusan = keputusan
    row.status = 'dilewati' if keputusan == 'lewati' else 'diputuskan'
    row.diputuskan_oleh = int(admin_id)
    row.diputuskan_pada = _now()
    if keputusan != 'lewati':
        try:
            prof = db.query(ProfilDokumen).filter(
                ProfilDokumen.file_id == row.file_id).first()
            if prof is not None and prof.peta_json:
                simpan = json.loads(prof.peta_json)
                surveyor = simpan.get('peta_surveyor') or {}
                label = surveyor.get('label') or {}
                label[str(row.baris_idx)] = keputusan
                surveyor['label'] = label
                simpan['peta_surveyor'] = surveyor
                prof.peta_json = json.dumps(simpan, ensure_ascii=False)
        except Exception:                                       # noqa: BLE001
            pass
    db.commit()
    return {'ok': True, 'pesan': 'Keputusan tersimpan.',
            'status': row.status, 'keputusan': row.keputusan}
