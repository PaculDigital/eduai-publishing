"""Ambang perubahan untuk periksa ulang struktur naskah (15 Nov 2026).

Perintah Boss:
  08:37, perubahan sepele (tambah titik/spasi/beberapa kata) DIABAIKAN;
  tombol aktif lagi HANYA bila perubahan berarti melewati ambang.
  08:40, DUAL MODE: manual (tombol) + OTOMATIS (jalan sendiri diam-diam
  bila perubahan melewati ambang BESAR). Ambang otomatis HARUS lebih tinggi
  dari ambang manual, supaya tidak sering jalan dan tidak boros biaya.
  08:41, manual dan otomatis memakai SATU penghitung perubahan yang sama,
  dihitung sejak PEMERIKSAAN TERAKHIR (peta_sidik + peta tersimpan).
  Menekan tombol ATAU jalan otomatis mengatur ulang penghitung yang sama.

CARA UKUR (pakai ulang mesin yang sudah ada, bukan mesin baru):
perbandingan memakai `revisi_hemat.rencanakan`, "bagian" di sini = bagian
hemat (blok BAB/subbab) yang sama dengan yang dipetakan ulang. Sidik
bagian itu mentah (tambah titik saja sudah mengubah sidik), jadi sebuah
bagian baru dihitung "berubah" bila KATA ternormalisasinya berubah:
tambah titik/spasi saja = 0 kata berubah = bukan perubahan. Sisipan
baris baru ikut bagian sebelumnya (aturan `peta_posisi`), jadi bagian
baru selalu tertangkap.
"""
from __future__ import annotations

import difflib
import re
from datetime import datetime, timedelta, timezone

# ── SATU konstanta ambang MANUAL (mudah diubah Boss) ─────────────────────
# Tombol "Periksa Struktur" aktif lagi bila SATU SAJA terpenuhi:
#   · satu bagian berubah isinya secara berarti (> 50 kata berubah), ATAU
#   · total bagian yang berubah kata-katanya mencapai 5% dari seluruh bagian.
AMBANG_PERIKSA_ULANG = {'kata_per_bagian': 50, 'persen_bagian': 0.05}

# ── SATU konstanta ambang OTOMATIS (mudah diubah Boss) ───────────────────
# Pemeriksaan jalan sendiri diam-diam bila bagian yang berubah kata-katanya
# mencapai 20% dari seluruh bagian. HARUS lebih besar dari persen manual
# di atas.
AMBANG_PERIKSA_OTOMATIS = {'persen_bagian': 0.20}

# ── SATU konstanta batas laju OTOMATIS (mudah diubah Boss) ───────────────
# Otomatis paling banyak SEKALI per 24 jam per naskah, dan tidak jalan bila
# pemeriksaan terakhir (manual ATAU otomatis) kurang dari 24 jam lalu.
# Diukur dari `peta_dibuat` (waktu pemeriksaan terakhir — diperbarui tiap
# simpan peta): satu cap menutup kedua ikatan, tanpa kolom baru.
BATAS_OTOMATIS_JAM = 24


def boleh_otomatis_jalan(peta_dibuat, sekarang=None) -> tuple[bool, str]:
    """Batas laju otomatis (15 Nov 2026, perintah Bos 09:15).

    `peta_dibuat`: waktu pemeriksaan terakhir (None = belum pernah).
    True bila sudah >= BATAS_OTOMATIS_JAM sejak pemeriksaan terakhir.
    Murni (tanpa Jev/DB) supaya gampang diuji; dipakai endpoint status
    + otomatis. Waktu naive (dari SQLite) dianggap UTC.
    """
    if peta_dibuat is None:
        return True, 'belum pernah diperiksa'
    kini = sekarang or datetime.now(timezone.utc)

    def _polos(dt):
        return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
    try:
        selisih = _polos(kini) - _polos(peta_dibuat)
    except Exception:                                       # noqa: BLE001
        return True, 'waktu terakhir tidak bisa dibaca (anggap boleh)'
    if selisih < timedelta(hours=BATAS_OTOMATIS_JAM):
        return False, ('pemeriksaan terakhir kurang dari %d jam lalu'
                       % BATAS_OTOMATIS_JAM)
    return True, 'boleh jalan otomatis'

_TANDA_BACA = re.compile(r'[^\w\s]+', re.UNICODE)


def normalisasi_teks(teks: str) -> str:
    """Rapikan teks untuk BANDING (bukan untuk simpan).

    Huruf kecil, tanda baca jadi spasi, spasi dirapikan. Akibatnya:
    tambah titik, tambah spasi, atau ubah kapital saja TIDAK terlihat
    sebagai perubahan.
    """
    t = (teks or '').lower()
    t = _TANDA_BACA.sub(' ', t)
    return ' '.join(t.split())


def _kata_berubah(a: list[str], b: list[str]) -> int:
    """Jumlah kata yang berubah antara dua daftar kata (tambah + hapus)."""
    ubah = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag != 'equal':
            ubah += (i2 - i1) + (j2 - j1)
    return ubah


def _hasil(kata_berubah: int, kata_maks: int, bagian_berubah: int,
           total_bagian: int, persen: float, alasan: str,
           struktural: bool = False, struktural_kecil: bool = False,
           gagal_banding: bool = False) -> dict:
    """Ringkasan ukuran perubahan.

    `berubah_berarti` (tombol aktif): 1 bagian > 50 kata ATAU >= 5%
    bagian berubah ATAU perubahan struktur kecil ATAU perbandingan gagal
    (fail-open manual — perintah di docstring `bandingkan_perubahan`).
    `berubah_besar` (ukuran besar): persen >= 20% (atau 100% bila
    struktural). `otomatis` (boleh jalan sendiri): besar DAN BUKAN
    struktural — otomatis TIDAK PERNAH membaca ulang penuh (perintah Bos
    15 Nov 2026 09:15); baca penuh hanya atas tekanan manual.
    """
    berubah_berarti = (
        gagal_banding or struktural_kecil
        or kata_maks > AMBANG_PERIKSA_ULANG['kata_per_bagian']
        or persen >= AMBANG_PERIKSA_ULANG['persen_bagian'])
    berubah_besar = persen >= AMBANG_PERIKSA_OTOMATIS['persen_bagian']
    otomatis = berubah_besar and not struktural and not struktural_kecil
    return {
        'kata_berubah': kata_berubah,
        'kata_maks_per_bagian': kata_maks,
        'bagian_berubah': bagian_berubah,
        'total_bagian': total_bagian,
        'persen_bagian': persen,
        'berubah_berarti': berubah_berarti,
        'berubah_besar': berubah_besar,
        'otomatis': otomatis,
        'struktural': struktural,
        'struktural_kecil': struktural_kecil,
        'alasan': alasan,
    }


def bandingkan_perubahan(peta_lama, teks_baru: str,
                         fn_susun_teks=None) -> dict:
    """Bandingkan naskah baru dengan peta tersimpan (garis awal tunggal).

    `peta_lama`: dict peta_json tersimpan (atau str JSON-nya).
    `teks_baru`: teks naskah sekarang (mentah).
    `fn_susun_teks`: (teks_bersih) -> dict {'baris': [...]}; bawaan susun
    produksi (deterministik, tanpa Jev). Uji menyuntik palsu.

    Gagal membandingkan apa pun -> fail-open untuk manual (anggap berubah,
    tombol aktif), TETAP tidak memicu otomatis (otomatis butuh ukuran
    perubahan yang terukur).
    """
    if AMBANG_PERIKSA_OTOMATIS['persen_bagian'] <= \
            AMBANG_PERIKSA_ULANG['persen_bagian']:
        raise ValueError(
            'AMBANG_PERIKSA_OTOMATIS harus lebih besar dari '
            'AMBANG_PERIKSA_ULANG (persen_bagian), kalau tidak, mode '
            'otomatis akan jalan lebih sering daripada manual.')
    try:
        from . import revisi_hemat as _rh
        from .state import buang_daftar_isi as _buang
        teks_bersih = _buang(teks_baru or '')
        if fn_susun_teks is None:
            from .peta3_jev import susun_teks as _susun
            fn_susun_teks = _susun
        susun_baru = fn_susun_teks(teks_bersih)
        baris_baru = list((susun_baru or {}).get('baris') or [])
        rencana = _rh.rencanakan(peta_lama, baris_baru)
    except Exception:                                       # noqa: BLE001
        # Gagal menilai apa pun -> fail-open MANUAL (tombol aktif, biar
        # mahasiswa bisa menekan; peta_mulai tetap menggerbang hemat),
        # TETAP tidak memicu otomatis (butuh ukuran yang terukur).
        return _hasil(0, 0, 0, 0, 0.0,
                      'tidak bisa dibandingkan (anggap berubah)',
                      gagal_banding=True)
    if rencana.get('jalan') == 'pakai_ulang':
        return _hasil(0, 0, 0, int(rencana.get('jumlah_bagian') or 0),
                      0.0, 'tidak ada perubahan')
    total = int(rencana.get('jumlah_bagian') or 0)
    if rencana.get('jalan') == 'penuh':
        # Perubahan struktur BESAR -> vonis besar (baca penuh, HANYA
        # lewat tombol manual; otomatis dimatikan untuk struktural —
        # perintah Bos 15 Nov 2026 09:15, lihat kunci 'otomatis').
        return _hasil(0, 0, total, total, 1.0,
                      'perubahan struktur (' +
                      str(rencana.get('alasan', '')) + ')',
                      struktural=True)
    kecil = bool(rencana.get('struktural_kecil'))
    # Hemat: hitung diff kata per bagian yang sidiknya berubah.
    try:
        lama = _rh._normalisasi_peta(peta_lama)
        baris_lama = list(lama['baris'])
        opcodes = _rh.diff_baris(baris_lama, baris_baru)
        bagian_berubah = 0
        kata_berubah = 0
        kata_maks = 0
        for b in (lama['bagian'] or []):
            a_lama, b_lama = int(b['awal']), int(b['akhir'])
            a_baru, b_baru = _rh.petakan_rentang(
                opcodes, len(baris_lama), len(baris_baru), a_lama, b_lama)
            if _rh._sidik_baris(baris_baru, a_baru, b_baru) == b['sidik']:
                continue
            d = _kata_berubah(
                normalisasi_teks('\n'.join(baris_lama[a_lama:b_lama])).split(),
                normalisasi_teks('\n'.join(baris_baru[a_baru:b_baru])).split())
            kata_berubah += d
            kata_maks = max(kata_maks, d)
            if d > 0:
                bagian_berubah += 1
    except Exception:                                       # noqa: BLE001
        return _hasil(0, 0, 0, total, 0.0,
                      'tidak bisa membandingkan per bagian (anggap berubah)',
                      gagal_banding=True)
    persen = (bagian_berubah / total) if total else 0.0
    if kecil:
        alasan = ('perubahan struktur kecil (%s)'
                  % (rencana.get('alasan_struktural') or 'judul berubah'))
    elif kata_berubah == 0 and bagian_berubah == 0:
        alasan = 'perubahan sepele di bawah ambang (0 kata berubah)'
    else:
        alasan = (f'perubahan berarti ({kata_berubah} kata, '
                  f'{bagian_berubah}/{total} bagian = {persen:.0%})')
    return _hasil(kata_berubah, kata_maks, bagian_berubah, total,
                  persen, alasan, struktural_kecil=kecil)


def perlu_periksa_ulang(peta_lama, teks_baru: str,
                        fn_susun_teks=None) -> tuple[bool, dict]:
    """Ambang MANUAL: True bila tombol boleh aktif lagi."""
    d = bandingkan_perubahan(peta_lama, teks_baru, fn_susun_teks)
    return d['berubah_berarti'], d


def perlu_periksa_otomatis(peta_lama, teks_baru: str,
                           fn_susun_teks=None) -> tuple[bool, dict]:
    """Ambang OTOMATIS: True bila pemeriksaan boleh jalan sendiri.

    TIDAK PERNAH True untuk perubahan struktural (baca penuh hanya lewat
    tombol manual, perintah Bos 15 Nov 2026 09:15) — lihat kunci
    'otomatis' di `bandingkan_perubahan`. Batas laju 24 jam TIDAK di sini
    (butuh waktu pemeriksaan terakhir dari DB — dicek endpoint).
    """
    d = bandingkan_perubahan(peta_lama, teks_baru, fn_susun_teks)
    return bool(d.get('otomatis', d['berubah_besar'])), d
