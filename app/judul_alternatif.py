"""Judul alternatif (tombol di siapkan, 30 Okt 2026).

Satu panggilan LLM baru per judul (cache per user+judul+jenis+bidang),
maks 3 panggilan baru per user per hari. Cache dan batas dihitung dari
tabel judul_alternatif_log (dibuat create_all, tanpa migrasi manual).
"""

import json
import re

from .models import JudulAlternatifLog, _now

BATAS_HARIAN = 3
MIN_JUDUL = 10
MAKS_JUDUL = 180
MAKS_ALTERNATIF = 3

ATURAN_JENIS = {
    'buku-referensi': (
        'Judul BUKU REFERENSI ilmiah: baku, menyebut bidang ilmu, '
        'menyebut topik, dan menarik agar laku dibeli. Bukan judul '
        'buku umum, bukan judul komik.'),
}
ATURAN_UMUM = (
    'Judul buku yang menarik, menyebut topik, dan mudah dipahami '
    'calon pembeli.')


def prompt_alternatif(judul, jenis, bidang):
    aturan = ATURAN_JENIS.get(jenis or '', ATURAN_UMUM)
    return (
        'Buatkan 3 alternatif judul buku.\n'
        f'Jenis buku: {jenis or "(tidak disebut)"}\n'
        f'Judul awal user: {judul}\n'
        f'Bidang: {bidang or "(sesuai judul)"}\n\n'
        f'Aturan: {aturan}\n'
        'Syarat: tiap judul satu baris, tanpa nomor, tanpa penjelasan, '
        'tanpa karakter U+2014, tiap judul maks 120 huruf.')


def saring_alternatif(teks, judul_asal):
    """Bersihkan keluaran LLM jadi maks 3 judul (tanpa duplikat, tanpa
    judul asal, tanpa U+2014). Tidak pernah raise."""
    if not teks:
        return []
    asal = (judul_asal or '').strip().lower()
    hasil = []
    for baris in str(teks).splitlines():
        s = baris.strip()
        s = re.sub(r'^[0-9]+[\.)\-]\s*', '', s)
        s = re.sub(r'^[-*\u2022]\s*', '', s)
        s = s.replace('\u2014', ',').strip().strip('"').strip()
        if not s or len(s) > 120:
            continue
        if s.lower() == asal or s.lower() in [h.lower() for h in hasil]:
            continue
        hasil.append(s)
        if len(hasil) >= MAKS_ALTERNATIF:
            break
    return hasil


def _normalisasi(judul):
    return (judul or '').strip().lower()


def ambil_alternatif(db, user_id, judul, jenis, bidang):
    """Kembalikan (daftar, dari_cache, galat). Galat None = sukses."""
    judul_bersih = (judul or '').strip()
    if len(judul_bersih) < MIN_JUDUL:
        return None, False, 'Judul minimal 10 huruf dulu, baru Wulan carikan alternatif.'
    if len(judul_bersih) > MAKS_JUDUL:
        return None, False, 'Judul terlalu panjang (maks 180 huruf).'
    jenis = (jenis or '').strip()
    bidang = (bidang or '').strip()
    kunci = _normalisasi(judul_bersih)
    lama = (db.query(JudulAlternatifLog)
            .filter(JudulAlternatifLog.user_id == user_id,
                    JudulAlternatifLog.judul == kunci,
                    JudulAlternatifLog.jenis == jenis,
                    JudulAlternatifLog.bidang == bidang)
            .order_by(JudulAlternatifLog.id.desc()).first())
    if lama is not None:
        try:
            return json.loads(lama.alternatif), True, None
        except (ValueError, TypeError):
            pass
    hari_ini = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    hitung = (db.query(JudulAlternatifLog)
              .filter(JudulAlternatifLog.user_id == user_id,
                      JudulAlternatifLog.dibuat >= hari_ini).count())
    if hitung >= BATAS_HARIAN:
        return None, False, (
            'Batas harian tercapai (3x). Alternatif muncul lagi besok, '
            'atau lanjut ke kerangka.')
    import buku_umum_pipeline as P
    teks = P.call_llm(prompt_alternatif(judul_bersih, jenis, bidang),
                      max_tokens=800, timeout=60)
    daftar = saring_alternatif(teks, judul_bersih)
    if not daftar:
        return None, False, 'Gagal memuat alternatif, coba lagi.'
    db.add(JudulAlternatifLog(user_id=user_id, judul=kunci, jenis=jenis,
                              bidang=bidang,
                              alternatif=json.dumps(daftar, ensure_ascii=False)))
    db.commit()
    return daftar, False, None
