"""Setelan aplikasi yang bisa diubah ADMIN dari browser (ACC Bos 24Sep26).

═══ MASALAH YANG DIPECAHKAN ═══
`TOKEN_REVISI_PER` hanya bisa diubah lewat `.env` + deploy → butuh Wulan,
butuh restart container (user yang sedang revisi terputus). Bos minta bisa
naik-turun mengikuti pasar dari browser. Modul ini jembatannya.

═══ URUTAN PRIORITAS (PENTING) ═══
    DB (tabel `setelan`)  >  .env  >  default config.py
DB menang supaya admin bisa ubah langsung. Kalau baris DB dihapus, nilai
kembali ke `.env`/default — jadi TIDAK ada nilai yang "terkunci" di DB.

═══ NILAI YANG DIKELOLA ═══
    token_revisi_per : pembagi rumus §4.13 (default 10.000)
    token_revisi_cap : batas maksimum Token Revisi per operasi (default 60)

═══ PAGAR (kenapa ada batas nilai) ═══
Angka ini MENENTUKAN HARGA. Salah ketik (mis. 1.000.000) = harga jadi
nyaris gratis; 100 = harga 100× lipat. Karena itu ada RENTANG aman dan
PERINGATAN — bukan pemblokiran, sesuai aturan Bos "selalu kasih jalan
keluar".
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import TOKEN_REVISI_CAP as _CAP_ENV
from .config import TOKEN_REVISI_PER as _PER_ENV
from .models import Setelan, SetelanRiwayat

log = logging.getLogger(__name__)

#  ── definisi setelan: kunci → (label, default, min, maks, satuan, catatan)
SETELAN = {
    'token_revisi_per': {
        'label': '1 Token Revisi = berapa token',
        'default': _PER_ENV,
        'min': 1_000,
        'maks': 200_000,
        'satuan': 'token',
        'catatan': 'Angka KECIL = mahasiswa kena Token LEBIH BANYAK.',
    },
    'token_revisi_cap': {
        'label': 'Batas maksimum Token Revisi per operasi',
        'default': _CAP_ENV,
        'min': 1,
        'maks': 1_000,
        'satuan': 'Token Revisi',
        'catatan': 'Pagar supaya naskah raksasa tidak menagih ratusan Token.',
    },
}


def baca(db: Session, kunci: str) -> int:
    """Ambil nilai setelan: DB → .env/default. Selalu mengembalikan int."""
    info = SETELAN.get(kunci)
    if not info:
        raise KeyError(f'setelan tidak dikenal: {kunci}')
    baris = db.get(Setelan, kunci)
    if baris and str(baris.nilai).strip():
        try:
            return int(baris.nilai)
        except (TypeError, ValueError):
            log.warning('[setelan] nilai DB %s=%r tidak sah → pakai default',
                        kunci, baris.nilai)
    return int(info['default'])


def baca_semua(db: Session) -> dict[str, int]:
    """Ambil SEMUA setelan sekaligus (dipakai halaman /pengaturan)."""
    return {k: baca(db, k) for k in SETELAN}


def asal(db: Session, kunci: str) -> str:
    """Dari mana nilai ini datang — 'DB' atau 'default'. Untuk ditampilkan."""
    baris = db.get(Setelan, kunci)
    return 'DB' if (baris and str(baris.nilai).strip()) else 'default'


def tulis(db: Session, kunci: str, nilai: int, oleh: str = '') -> tuple[bool, str]:
    """Simpan setelan + catat riwayat. Kembalikan (berhasil, pesan).

    TIDAK memblokir nilai di luar rentang — hanya MEMPERINGATKAN, karena
    admin (Bos) yang memutuskan. Yang diblokir hanya nilai yang MUSTAHIL
    (0 atau negatif) sebab bikin pembagian nol / harga tak terhingga.
    """
    info = SETELAN.get(kunci)
    if not info:
        return False, f'Setelan "{kunci}" tidak dikenal.'
    try:
        nilai = int(nilai)
    except (TypeError, ValueError):
        return False, 'Nilai harus berupa angka bulat.'
    if nilai <= 0:
        return False, 'Nilai harus lebih besar dari 0.'

    lama = baca(db, kunci)
    if nilai == lama:
        return True, 'Nilai tidak berubah.'

    baris = db.get(Setelan, kunci)
    if baris:
        baris.nilai = str(nilai)
        baris.oleh = oleh
    else:
        db.add(Setelan(kunci=kunci, nilai=str(nilai), oleh=oleh))
    db.add(SetelanRiwayat(kunci=kunci, nilai_lama=str(lama),
                          nilai_baru=str(nilai), oleh=oleh))
    db.commit()
    log.info('[setelan] %s: %s → %s (oleh %s)', kunci, lama, nilai, oleh)

    pesan = f'Tersimpan: {info["label"]} = {nilai:,} {info["satuan"]}.'
    if nilai < info['min'] or nilai > info['maks']:
        pesan += (f' ⚠️ Di luar rentang wajar ({info["min"]:,}–'
                  f'{info["maks"]:,}) — pastikan ini memang disengaja.')
    return True, pesan


def riwayat(db: Session, batas: int = 20) -> list[dict]:
    """Perubahan terakhir — ditampilkan di halaman supaya jejaknya kelihatan."""
    baris = db.scalars(
        select(SetelanRiwayat).order_by(SetelanRiwayat.id.desc()).limit(batas)
    ).all()
    return [{'kunci': b.kunci, 'lama': b.nilai_lama, 'baru': b.nilai_baru,
             'oleh': b.oleh, 'kapan': b.dibuat} for b in baris]


def simulasi(per: int, cap: int) -> list[dict]:
    """Tabel contoh: berapa Token Revisi untuk beberapa ukuran naskah.

    KENAPA contoh NYATA (bukan angka karangan): supaya Bos bisa MELIHAT
    akibat perubahan angka sebelum menyimpan. Semua memakai rumus §4.13
    yang sama dengan produksi:
        min( ceil((token_in + token_out) / per) × pengali, cap )
    """
    from math import ceil

    # Ukuran naskah contoh: (nama, token_in, token_out) — dari riwayat
    # proses_ai nyata (rata-rata token_out ~7.577 untuk token_in ~29.811).
    contoh = [
        ('Revisi ringan (1 sub-bab)', 6_000, 1_500),
        ('Skripsi S1 (65.932 kar)', 29_811, 7_577),
        ('Tesis S2 (92.223 kar)', 34_800, 14_200),
        ('Disertasi S3 (374.095 kar)', 351_841, 36_000),
    ]
    hasil = []
    for nama, tin, tout in contoh:
        total = tin + tout
        mentah = ceil(total / per) if per else 0
        nilai = min(mentah, cap)
        hasil.append({'nama': nama, 'total': total,
                      'tanpa_cap': mentah, 'token': nilai,
                      'kena_cap': mentah > cap})
    return hasil
