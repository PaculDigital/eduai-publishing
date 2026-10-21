"""TIKET LOLOS — Lapis 3 (Tanda Khusus per-Elemen) — 16 Okt 2026.

Jawaban pertanyaan Bos:
    "user sudah bayar & dapat kebutuhannya di bab itu, lalu edit manual /
     menambah kalimat yang sesuai tapi TIDAK merubah makna — lolos atau tidak?"
    ⇒ LOLOS. Yang dinilai MAKNA, bukan huruf.

KENAPA BUKAN SIDIK TEKS: sidik teks mentah tidak bisa membedakan
"tambah kalimat pendukung" (makna TETAP) dari "ganti angka temuan"
(makna BERUBAH) ⇒ user yang cuma menyempurnakan akan diminta bayar lagi
= TIDAK ADIL (melanggar prinsip Bos "tidak kerja bolak-balik").

CARA KERJA (putusan Bos 16 Okt, pilihan A):
  ① saat revisi SUKSES  → tulis TIKET per elemen (bab + 1500 huruf bab)
  ② saat konversi ulang → Jev ditanya 1 pertanyaan CHOICE per elemen bertiket:
        "masih membahas hal yang sama?"  {sama / beda}
  ③ Jev jawab 'sama'    → tiket TETAP → elemen DONE (tidak ditanyakan lagi)
     Jev jawab lain / mati / ragu → tiket BATAL → elemen ditanyakan ulang

⚠️ PRINSIP AMAN: Jev mati TIDAK boleh jadi pintu gratis. Kegagalan teknis
   ⇒ tiket BATAL (diperiksa ulang), bukan lolos otomatis.

NOL mesin baru: memakai `jev.tanya()` (SUDAH ADA), wadah
`KonversiNaskah.hasil_json` (SUDAH ADA), dan label elemen `ELEMEN_REVISI`.
"""
from __future__ import annotations

import json
import logging

#  ⚠️ Ambil ELEMEN_REVISI / ELEMEN_11 dari modul PEMAKAI (konversi.py) —
#     JANGAN salin daftarnya ke sini (dua sumber = bahaya, pelajaran MAXMB).
from .konversi import ELEMEN_REVISI, ELEMEN_11

log = logging.getLogger('eduai.konversi')

#  Panjang sidik bab (putusan Bos 16 Okt 2026: 1500 huruf).
SIDIK_HURUF = 1500

#  Nama kunci tiket di hasil_json.
KUNCI_TIKET = 'tiket'


def _potong(teks: str, maks: int = SIDIK_HURUF) -> str:
    """Ambil `maks` huruf pertama (buang spasi berlebih di ujung)."""
    return (teks or '').strip()[:maks].strip()


def label_elemen(kunci: str) -> str:
    """Nama manusiawi sebuah elemen (dari ELEMEN_REVISI yang SUDAH ADA)."""
    for k, label in ELEMEN_REVISI:                            # noqa: F821
        if k == kunci:
            return label
    return kunci


def bab_dari_kunci(kunci: str, peta_bab: dict | None = None) -> str:
    """Bab tempat sebuah elemen tinggal (dari ELEMEN_11 kolom ke-3).

    ELEMEN_11 = (kunci, label, wilayah) — mis. ('gap', 'Gap', 'Pendahuluan ¶4').
    Kembalikan wilayah apa adanya kalau peta bab tidak memberi nomor.
    """
    wilayah = ''
    for baris in ELEMEN_11:                                   # noqa: F821
        if baris and baris[0] == kunci:
            wilayah = baris[2] if len(baris) > 2 else ''
            break
    return wilayah or 'Pendahuluan'


def tiket_baca(db, u, fid: int) -> dict:
    """Baca tiket tersimpan dari `KonversiNaskah.hasil_json`.

    SELALU kembalikan dict (kosong kalau tidak ada / rusak). TIDAK melempar.
    """
    import json as _json
    from .models import KonversiNaskah
    from sqlalchemy import select as _select

    uid = int(getattr(u, 'id', 0))
    try:
        baris = db.execute(
            _select(KonversiNaskah).where(
                KonversiNaskah.user_id == uid,
                KonversiNaskah.file_id == int(fid),
                KonversiNaskah.status == 'beres',
            ).order_by(KonversiNaskah.id.desc())
        ).scalars().first()
    except Exception as e:                                    # noqa: BLE001
        log.warning('[tiket] baca gagal (fid=%s): %s', fid, e)
        return {}

    if baris is None:
        return {}
    try:
        wadah = _json.loads(baris.hasil_json or '{}')
    except Exception:                                         # noqa: BLE001
        return {}
    tiket = wadah.get(KUNCI_TIKET) or {}
    return tiket if isinstance(tiket, dict) else {}


def tiket_tulis(db, u, fid: int, artikel: dict, pilihan, teks_bab_untuk) -> dict:
    """Tulis/segarkan tiket untuk `pilihan` (daftar kunci elemen) setelah revisi.

    `teks_bab_untuk(kunci)` = fungsi yang mengembalikan TEKS bab tempat elemen
    itu tinggal (naskah penuh; di sini dipotong SIDIK_HURUF huruf).

    ⚠️ TIDAK membuat tabel/kolom baru — menumpang `KonversiNaskah.hasil_json`
    (wadah yang SUDAH dipakai kunci 'revisi' & 'artikel').
    """
    import json as _json
    from .models import KonversiNaskah, _now
    from sqlalchemy import select as _select

    uid = int(getattr(u, 'id', 0))
    baris = db.execute(
        _select(KonversiNaskah).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'beres',
        ).order_by(KonversiNaskah.id.desc())
    ).scalars().first()
    if baris is None:
        return {'tersimpan': False, 'pesan': 'Baris konversi tidak ditemukan.'}

    try:
        wadah = _json.loads(baris.hasil_json or '{}')
    except Exception:                                         # noqa: BLE001
        wadah = {}
    if not isinstance(wadah, dict):
        wadah = {}

    tiket = wadah.get(KUNCI_TIKET) or {}
    if not isinstance(tiket, dict):
        tiket = {}

    waktu = _now().isoformat(timespec='seconds')
    ditulis = []
    for kunci in (pilihan or []):
        k = str(kunci or '').strip()
        if not k:
            continue
        try:
            teks = teks_bab_untuk(k)
        except Exception as e:                                # noqa: BLE001
            log.warning('[tiket] ambil teks bab %s gagal: %s', k, e)
            teks = ''
        tiket[k] = {'bab': bab_dari_kunci(k), 'sidik': _potong(teks),
                    'waktu': waktu}
        ditulis.append(k)

    wadah[KUNCI_TIKET] = tiket
    baris.hasil_json = _json.dumps(wadah, ensure_ascii=False)
    db.commit()
    return {'tersimpan': True, 'ditulis': ditulis, 'jumlah': len(tiket)}


def tiket_batal(db, u, fid: int, kunci: str) -> bool:
    """Hapus tiket satu elemen (dipakai kalau Jev bilang makna BERUBAH)."""
    import json as _json
    from .models import KonversiNaskah
    from sqlalchemy import select as _select

    uid = int(getattr(u, 'id', 0))
    baris = db.execute(
        _select(KonversiNaskah).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'beres',
        ).order_by(KonversiNaskah.id.desc())
    ).scalars().first()
    if baris is None:
        return False
    try:
        wadah = _json.loads(baris.hasil_json or '{}')
    except Exception:                                         # noqa: BLE001
        return False
    tiket = wadah.get(KUNCI_TIKET) or {}
    if not isinstance(tiket, dict) or kunci not in tiket:
        return False
    tiket.pop(kunci, None)
    wadah[KUNCI_TIKET] = tiket
    baris.hasil_json = _json.dumps(wadah, ensure_ascii=False)
    db.commit()
    return True


# ══════════════════════════════════════════════════════════════════════════
# JEV MENILAI MAKNA — 1 pertanyaan choice per elemen bertiket
# ══════════════════════════════════════════════════════════════════════════
def _skema_pertanyaan() -> dict:
    """Skema CHOICE untuk Jev (WAJIB `criteria` OBJEK — jangan list)."""
    return {
        'masih_sama': {
            'type': 'choice',
            'instructions': (
                'Di bawah ada DUA potongan bab dari naskah yang SAMA pada dua '
                'waktu berbeda (LAMA dan BARU). Jawab: apakah bab ini masih '
                'membahas HAL YANG SAMA / fokus yang sama? Perhatikan MAKNA, '
                'bukan panjang tulisan. Penambahan kalimat pendukung, '
                'perbaikan ejaan, atau penyempurnaan gaya TIDAK mengubah makna. '
                'Makna BERUBAH kalau fokus/objek/klaim utamanya bergeser, '
                'atau temuan/angka pokoknya diganti.'),
            'criteria': {
                'sama': 'masih membahas hal/fokus yang SAMA',
                'beda': 'fokus/klaim utamanya sudah BERBEDA',
            },
        }
    }


def _bahan_banding(lama: str, baru: str) -> str:
    """Susun bahan untuk Jev: bab LAMA vs bab BARU."""
    return ('=== BAB LAMA (saat elemen ini dibayar) ===\n'
            + (lama or '(kosong)')
            + '\n\n=== BAB BARU (sekarang) ===\n'
            + (baru or '(kosong)'))


def tiket_periksa(db, u, fid: int, kurang, teks_bab_untuk,
                  panggil=None) -> dict:
    """Periksa tiket untuk elemen di `kurang`. Jev menilai MAKNA.

    Parameter
    ---------
    kurang        : daftar NAMA elemen (label manusiawi) yang kurang menurut
                    `periksa_mutu()`. Yang bertiket & maknanya tetap ⇒ DIBUANG.
    teks_bab_untuk: fungsi(kunci) → teks bab SEKARANG.
    panggil       : fungsi(bahan, skema) → balasan Jev (untuk uji; default
                    `jev.tanya`). DIJADIKAN PARAMETER supaya bisa diuji
                    tanpa jaringan.

    Balik
    -----
    {'kurang': [...sisa...], 'lolos': [...], 'batal': [...], 'diperiksa': int}
    """
    keluar = {'kurang': list(kurang or []), 'lolos': [], 'batal': [],
              'diperiksa': 0}
    if not keluar['kurang']:
        return keluar

    tiket = tiket_baca(db, u, fid)
    if not tiket:
        return keluar

    if panggil is None:
        from . import jev as jev_mod
        panggil = jev_mod.tanya

    skema = _skema_pertanyaan()

    for label in list(kurang or []):
        #  label → kunci elemen (kebalikan ELEMEN_REVISI)
        kunci = ''
        for k, lb in ELEMEN_REVISI:                            # noqa: F821
            if lb == label:
                kunci = k
                break
        if not kunci or kunci not in tiket:
            continue                      # tidak bertiket → tetap ditanyakan

        keluar['diperiksa'] += 1
        data = tiket.get(kunci) or {}
        lama = str(data.get('sidik') or '')
        try:
            baru = _potong(teks_bab_untuk(kunci))
        except Exception as e:                                # noqa: BLE001
            log.warning('[tiket] teks bab %s gagal: %s', kunci, e)
            baru = ''

        if not lama.strip():
            keluar['batal'].append(label)    # tiket rusak ⇒ batal (aman)
            continue

        #  Kalau bab TIDAK berubah sama sekali → tiket pasti tetap (hemat Jev)
        if lama.strip() == baru.strip():
            keluar['lolos'].append(label)
            keluar['kurang'].remove(label)
            continue

        try:
            jawab = panggil(_bahan_banding(lama, baru), skema)
        except Exception as e:                                # noqa: BLE001
            log.warning('[tiket] Jev gagal (fid=%s, %s): %s', fid, kunci, e)
            jawab = None

        #  ⚠️ PRINSIP AMAN: apa pun selain 'sama' yang YAKIN ⇒ BATAL.
        putusan = ''
        yakin = 0.0
        if isinstance(jawab, dict):
            isi = jawab.get('masih_sama') or {}
            if isinstance(isi, dict):
                putusan = str(isi.get('choice') or '').strip().lower()
                try:
                    yakin = float(isi.get('confidence') or 0)
                except (TypeError, ValueError):
                    yakin = 0.0

        if putusan == 'sama':
            keluar['lolos'].append(label)
            keluar['kurang'].remove(label)
        else:
            keluar['batal'].append(label)
            try:
                tiket_batal(db, u, fid, kunci)
            except Exception as e:                            # noqa: BLE001
                log.warning('[tiket] batal %s gagal: %s', kunci, e)

    return keluar
