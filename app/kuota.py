"""kuota.py — SISTEM KUOTA & CREDIT AI (MASTER_PLAN §4.10, ACC Bos 13Sep26).

MENGAPA MODUL INI ADA
---------------------
Gerbang AI sebelumnya BINER: `_member_berbayar()` cuma cek "punya ≥1
transaksi sukses". Jadi beli Rp 50.000 = AI **unlimited**, tanpa hitungan.
Itu lubang: makin banyak dipakai, makin besar biaya tanpa batas.

ALUR GERBANG BARU (menggantikan _member_berbayar):
  1. user login?            → tidak: 401
  2. punya paket berbayar?  → tidak: 403 (pesan upgrade)
  3. kuota bulan ini ada?   → tidak: 402 (pesan TAWARKAN ADDON, bukan upgrade)
  4. jalankan AI → potong 1 kuota → catat di pemakaian_ai

STRATEGI BISNIS (JANGAN diubah tanpa ACC Bos):
  • Kuota habis → tawarkan ADDON, JANGAN dorong upgrade paket.
  • AddOn TERKUNCI untuk paket gratis (validasi BACKEND, bukan hanya UI).
  • Reset bulanan tanggal 1, sisa credit HANGUS, implementasi LAZY (tanpa cron).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import (
    ADDON,
    ADMIN_EMAIL,
    KUOTA_PAKET,
    KUOTA_SIMULASI_PAKET,
    PAKET_TANPA_ADDON,
    boleh_beli_addon,
    jatah_folder,          # dipakai _saran_untuk() (ACC Bos 15Sep26)
)
from .models import PemakaianAI, PembelianAddon, User
from . import saldo as _saldo

log = logging.getLogger('eduai.kuota')


def bulan_sekarang() -> str:
    """Kunci bulan 'YYYY-MM' (UTC). Dipakai sebagai kunci reset bulanan."""
    return datetime.now(timezone.utc).strftime('%Y-%m')


def _admin(u: User) -> bool:
    return u.email == ADMIN_EMAIL or u.role == 'admin'


# ══════════════════════════════════════════════════════════════════════════
# PEMAKAIAN BULAN INI (lazy — tidak perlu cron)
# ══════════════════════════════════════════════════════════════════════════
def ambil_pemakaian(db: Session, uid: int, bulan: str | None = None) -> PemakaianAI:
    """Ambil (atau buat) baris pemakaian bulan ini.

    LAZY RESET: kalau bulan berganti, baris bulan lama tetap ada sebagai
    riwayat; baris bulan BARU dibuat dengan hitungan 0 → otomatis "reset".
    Tidak butuh cron: reset terjadi saat diakses.
    """
    bulan = bulan or bulan_sekarang()
    baris = db.execute(
        select(PemakaianAI).where(
            PemakaianAI.user_id == uid, PemakaianAI.bulan == bulan
        )
    ).scalar_one_or_none()
    if baris is None:
        baris = PemakaianAI(user_id=uid, bulan=bulan, jumlah_revisi=0, jumlah_simulasi=0)
        db.add(baris)
        try:
            db.commit()
        except IntegrityError:
            # balapan: baris sudah dibuat request lain → ambil yang ada
            db.rollback()
            baris = db.execute(
                select(PemakaianAI).where(
                    PemakaianAI.user_id == uid, PemakaianAI.bulan == bulan
                )
            ).scalar_one()
    return baris


def sisa_addon(db: Session, uid: int, jenis: str) -> int:
    """Total sisa kuota AddOn jenis tertentu yang masih berlaku."""
    now = datetime.now(timezone.utc)
    baris = db.execute(
        select(PembelianAddon).where(
            PembelianAddon.user_id == uid, PembelianAddon.jenis == jenis
        )
    ).scalars().all()
    total = 0
    for b in baris:
        if b.sisa_kuota <= 0:
            continue
        if b.kedaluwarsa is not None:
            kd = b.kedaluwarsa
            # SQLite bisa kembalikan naive → samakan jadi aware (pelajaran 12Sep26)
            if kd.tzinfo is None:
                kd = kd.replace(tzinfo=timezone.utc)
            if kd < now:
                continue        # kedaluwarsa → tidak dihitung
        total += b.sisa_kuota
    return total


# ══════════════════════════════════════════════════════════════════════════
# GERBANG KUOTA — inti pengganti _member_berbayar()
# ══════════════════════════════════════════════════════════════════════════
def _token_pakai_bulan(db: Session, uid: int, bulan: str | None = None) -> int:
    """Token NET terpakai bulan berjalan — dari buku besar `saldo_token`.

    Satuan SAMA dengan `sisa` (token), bukan 'jumlah revisi', supaya angka
    panel (`dipakai` / `total`) sebanding. Baris `kembali%` ikut dihitung
    sehingga pengembalian token menurunkan pemakaian (jujur dua arah).
    """
    from sqlalchemy import func
    from .models import SaldoToken
    awal_bulan = (bulan or bulan_sekarang()) + '-01'
    n = db.execute(
        select(func.coalesce(func.sum(SaldoToken.jumlah), 0)).where(
            SaldoToken.user_id == uid,
            (SaldoToken.sumber.like('pakai%')
             | SaldoToken.sumber.like('kembali%')),
            #  kolom DateTime SQLite tersimpan sebagai teks ISO → perbandingan
            #  teks aman: '2026-09-28 ...' >= '2026-09-01'
            SaldoToken.dibuat >= awal_bulan,
        )).scalar()
    return int(-(n or 0))


def ringkasan_kuota(db: Session, u: User) -> dict:
    """Ringkasan kuota untuk frontend (endpoint GET /api/ai/kuota).

    ⭐ SATU KANTONG (ACC Bos 26Sep26): angka `revisi` bersumber dari buku
    besar `saldo_token` — SAMA PERSIS dengan gerbang 402 (`cek_dan_potong`
    → `saldo.sisa`). Satu sumber → tampilan dan gerbang mustahil beda.

    ❌ AKAR 28Sep26 (JANGAN dikembalikan): model lama
    `max(jatah_paket + addon − pemakaian_bulanan, 0)` tidak ikut migrasi
    Saldo Permanen. Terukur: user penulis terpakai 38 revisi bulan ini
    (jatah 12) → tampilan bilang sisa 0 padahal saldo ledger 27 → dialog
    izin dokumen besar `cukup=false` MEMATIKAN tombol "Ya, proses" untuk
    mahasiswa, dan uji C7 J1/J2 gagal (sisa0=0, sisa1=0 → pakai=0).
    """
    paket = (u.paket or 'gratis')
    saldo = _saldo.sisa(db, u)                 # kantong tunggal (ledger)
    pakai = ambil_pemakaian(db, u.id)
    dipakai = _token_pakai_bulan(db, u.id)     # token terpakai bulan ini
    total = saldo + dipakai                    # isi kantong bulan berjalan

    sim_paket = KUOTA_SIMULASI_PAKET.get(paket, 0)
    sim_addon = sisa_addon(db, u.id, 'belajar')
    bljr_paket = KUOTA_PAKET.get(paket, {}).get('belajar_naskah', 0)
    konv_paket = KUOTA_PAKET.get(paket, {}).get('konversi', 0)

    return {
        'paket': paket,
        'bulan': pakai.bulan,
        'revisi': {
            'jatah_paket': 0,          # permanen — tidak ada jatah bulanan
            'jatah_addon': 0,          # AddOn sudah menyatu ke saldo
            'total': total,
            'dipakai': dipakai,
            'sisa': saldo,
            'sisa_paket': saldo,       # satu kantong: paket + addon = saldo
            'sisa_addon': 0,           # tidak ada potongan terpisah
            'persen_pakai': round(dipakai / total * 100, 1) if total else 100.0,
        },
        'simulasi': {
            'jatah_paket': sim_paket,
            'jatah_addon': sim_addon,
            'total': sim_paket + sim_addon,
            'dipakai': pakai.jumlah_simulasi,
            'sisa': max(sim_paket + sim_addon - pakai.jumlah_simulasi, 0),
        },
        'belajar_naskah': {'jatah_paket': bljr_paket, 'aktif': _jml_belajar(db, u.id)},
        #  🩹 07Okt26 (tutup R1): dulu cuma kirim jatah_paket → UI tak tahu SISA
        #  (termasuk AddOn yang dibeli). Kini lengkap, SATU bentuk dengan belajar.
        #  ⚠️ `belajar` sengaja TIDAK diubah (di luar lingkup izin) — dicatat di SOT.
        'konversi': {**_j_konversi_ringkas(db, u), 'jatah_paket': konv_paket},
        'boleh_beli_addon': boleh_beli_addon(paket),
        'paket_berbayar': paket != 'gratis',
        'admin': _admin(u),
    }


def _jml_belajar(db: Session, uid: int) -> int:
    from .models import BelajarNaskah
    return len(db.execute(
        select(BelajarNaskah.id).where(
            BelajarNaskah.user_id == uid, BelajarNaskah.status == 'aktif'
        )
    ).all())


# ══════════════════════════════════════════════════════════════════════════
# KONVERSI JURNAL (07 Okt 2026) — SALINAN POLA 'belajar'
# ══════════════════════════════════════════════════════════════════════════
def _jml_konversi(db: Session, uid: int) -> int:
    """Berapa konversi yang SUDAH DIPAKAI user ini.

    Dihitung dari baris `konversi_naskah` yang status != 'gagal'.
    Baris 'gagal' = AI gagal TEKNIS → token dikembalikan, jadi TIDAK dihitung
    (kalau dihitung, user dirugikan karena gagal bukan salah dia).
    """
    from .models import KonversiNaskah
    return len(db.execute(
        select(KonversiNaskah.id).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.status != 'gagal',
        )
    ).all())


def _j_konversi_ringkas(db: Session, u: User) -> dict:
    """Ringkasan konversi untuk `ringkasan_kuota()` — bentuknya sengaja sama
    dengan `belajar_naskah` supaya UI bisa pakai pola tampil yang SAMA."""
    j = jatah_konversi(db, u)
    return {'dipakai': j['dipakai'], 'jatah_addon': j['jatah_addon'], 'sisa': j['sisa']}


def jatah_konversi(db: Session, u: User) -> dict:
    """Jatah konversi user = sisa paket + AddOn terbeli − yang sudah dipakai.

    POLA SAMA dengan `belajar` (jatah_paket + sisa_addon − terpakai), TAPI
    diperbaiki: pola belajar lupa `sisa_addon` di `aktivasi()` → AddOn belajar
    yang dibeli tak pernah terhitung. Di sini `sisa_addon` DIPAKAI sejak awal.

    ⚠️ AddOn 'konversi' sudah ADA di config.py:339 (Rp100.000, kuota 1) —
    tidak ada AddOn baru. `sisa_addon(db, uid, 'konversi')` memakai kolom
    `pembelian_addon.jenis` yang sudah menerima 'konversi' (models.py:463).
    """
    paket = (u.paket or 'gratis')
    jatah_paket = int(KUOTA_PAKET.get(paket, {}).get('konversi', 0) or 0)
    addon = sisa_addon(db, u.id, 'konversi')
    dipakai = _jml_konversi(db, u.id)
    total = jatah_paket + addon
    return {
        'jatah_paket': jatah_paket,
        'jatah_addon': addon,
        'total': total,
        'dipakai': dipakai,
        'sisa': max(total - dipakai, 0),
        'boleh': max(total - dipakai, 0) > 0,
        'boleh_beli_addon': boleh_beli_addon(paket),
    }


def potong_konversi(db: Session, u: User, fid: int) -> tuple[bool, str]:
    """Potong 1 konversi + CATAT baris pelacak. Mengembalikan (ok, pesan).

    Dipanggil SEBELUM proses AI mulai (bukan saat preview). Kalau proses AI
    GAGAL TEKNIS → panggil `kembalikan_konversi()` untuk membatalkan.

    PAGAR (semua di SERVER, bukan tampilan):
      1. naskah WAJIB milik user sendiri
      2. naskah yang SAMA tidak boleh dikonversi dua kali SAAT MASIH ADA baris
         'proses' (mencegah klik dobel / dua tab)
      3. sisa jatah harus > 0 (paket + AddOn)
    """
    from .models import KonversiNaskah, FileBerkas

    uid = int(getattr(u, 'id', 0))

    f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
    if f is None or int(getattr(f, 'user_id', 0)) != uid:
        return False, 'Naskah itu bukan milikmu.'

    sedang = db.execute(
        select(KonversiNaskah).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'proses',
        )
    ).scalars().first()
    if sedang is not None:
        return False, 'Naskah ini sedang dikonversi. Tunggu sampai selesai ya.'

    j = jatah_konversi(db, u)
    if not j['boleh']:
        if j['boleh_beli_addon']:
            return False, ('Kuota konversimu sudah habis. '
                           'Tambah AddOn Konversi Jurnal untuk naskah berikutnya.')
        return False, ('Kuota konversimu sudah habis. '
                       'Naikkan paket untuk membuka konversi.')

    baris = KonversiNaskah(
        file_id=int(fid), user_id=uid, status='proses',
        sumber_kuota=('addon' if j['jatah_addon'] > 0
                      and j['dipakai'] >= j['jatah_paket'] else 'paket'),
    )
    db.add(baris)
    db.commit()
    return True, 'Konversi dimulai.'


def kembalikan_konversi(db: Session, uid: int, fid: int, galat: str = '') -> bool:
    """Tandai konversi GAGAL TEKNIS → jatah kembali (baris tidak dihitung lagi).

    KENAPA bukan hapus baris: jejak tetap ada untuk audit; yang berubah cuma
    status jadi 'gagal' → `_jml_konversi()` tidak menghitungnya.
    """
    from .models import KonversiNaskah
    baris = db.execute(
        select(KonversiNaskah).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'proses',
        ).order_by(KonversiNaskah.id.desc())
    ).scalars().first()
    if baris is None:
        return False
    baris.status = 'gagal'
    baris.galat = (galat or '')[:2000]
    db.commit()
    return True


def selesaikan_konversi(db: Session, uid: int, fid: int, hasil: dict,
                        jenis: str = '', token_dipotong: int = 0) -> bool:
    """Tandai konversi SELESAI + simpan hasil (artikel) ke baris pelacak."""
    import json as _json
    from .models import KonversiNaskah
    baris = db.execute(
        select(KonversiNaskah).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'proses',
        ).order_by(KonversiNaskah.id.desc())
    ).scalars().first()
    if baris is None:
        return False
    baris.status = 'beres'
    baris.jenis = (jenis or '')[:30]
    baris.token_dipotong = int(token_dipotong or 0)
    try:
        baris.hasil_json = _json.dumps(hasil or {}, ensure_ascii=False)
    except (TypeError, ValueError):
        baris.hasil_json = '{}'
    db.commit()
    return True


def daftar_konversi(db: Session, uid: int) -> list:
    """SEMUA baris konversi milik user, terbaru dulu.

    Dipakai halaman /artikel untuk menampilkan status tiap naskah
    (belum · proses · beres · gagal) — SATU query untuk semua naskah,
    bukan satu query per baris.
    """
    from .models import KonversiNaskah
    return list(db.execute(
        select(KonversiNaskah)
        .where(KonversiNaskah.user_id == uid)
        .order_by(KonversiNaskah.id.desc())
    ).scalars().all())


def konversi_terakhir(db: Session, uid: int):
    """Baris konversi TERAKHIR milik user (untuk halaman /artikel).

    Tanpa anotasi tipe supaya kuota.py TIDAK mengimpor models di atas
    (hindari impor melingkar) — sama pola dengan `_jml_belajar`.
    """
    from .models import KonversiNaskah
    return db.execute(
        select(KonversiNaskah)
        .where(KonversiNaskah.user_id == uid)
        .order_by(KonversiNaskah.id.desc())
    ).scalars().first()


def _saran_untuk(u: User, db: Session, sebab: str) -> dict:
    """Tentukan SATU saran utama + diagnosis untuk popup (ACC Bos 15Sep26).

    KENAPA ADA: popup lama = katalog statis. User bingung, risiko salah beli
    (butuh +10 folder malah beli paket Rp 300.000 karena paket lebih menonjol).

    SOLUSI: popup harus TAHU kenapa user dibawa ke sini, lalu taruh SATU
    jawaban paling atas. Diagnosis + saran dihitung di SINI (backend) supaya
    angkanya NYATA dari DB — bukan tebak-tebakan frontend.

    `sebab`: folder | storage | ai | manual
    """
    paket = (u.paket or 'gratis')
    boleh = boleh_beli_addon(paket)

    # ── Kondisi nyata user (angka dari DB, bukan perkiraan) ──────────────
    sisa_mb = max(0.0, (u.kuota_mb or 0) - (u.terpakai_bytes or 0) / 1048576)
    jatah_fd = jatah_folder(paket, u.folder_ekstra or 0)
    from .folder import jumlah_folder
    pakai_fd = jumlah_folder(db, u.id)
    ring = ringkasan_kuota(db, u)
    sisa_ai = ring['revisi']['sisa']

    if sebab == 'folder':
        diagnosis = ('Folder Anda sudah penuh — %d dari %d.'
                     % (pakai_fd, jatah_fd))
        addon = 'storage' if boleh else None
        alasan = ('Sekali beli: +%d folder DAN +%d MB storage. '
                  'Berlaku permanen.' % (ADDON['storage']['tambahan']['folder_ekstra'],
                                         ADDON['storage']['tambahan']['kuota_mb']))
    elif sebab == 'storage':
        diagnosis = ('Storage Anda hampir penuh — sisa %.1f MB.' % sisa_mb)
        addon = 'storage' if boleh else None
        alasan = ('Sekali beli: +%d MB storage DAN +%d folder. '
                  'Berlaku permanen.'
                  % (ADDON['storage']['tambahan']['kuota_mb'],
                     ADDON['storage']['tambahan']['folder_ekstra']))
    elif sebab == 'ai':
        diagnosis = 'Kuota AI bulan ini sudah habis.'
        addon = 'ai' if boleh else None
        alasan = 'AddOn tidak hangus di akhir bulan.'
    else:                                   # manual — user buka sendiri
        diagnosis = 'Anda membuka Tambah Kuota.'
        addon = None
        alasan = 'Pilih yang paling cocok. Kami urutkan dari yang paling murah.'

    saran = None
    if addon:
        v = ADDON[addon]
        saran = {
            'jenis': addon,
            'nama': v['nama'],
            'harga': v['harga'],
            'label': 'Rp {:,}'.format(v['harga']).replace(',', '.'),
            'keterangan': v['keterangan'],
            'alasan': alasan,
            'permanen': bool(v.get('tambahan')),
        }
    return {
        'sebab': sebab,
        'diagnosis': diagnosis,
        'saran': saran,
        'kondisi': {
            'paket': paket,
            'sisa_mb': round(sisa_mb, 1),
            'kuota_mb': u.kuota_mb,
            'folder_pakai': pakai_fd,
            'folder_jatah': jatah_fd,
            'sisa_ai': sisa_ai,
        },
    }


def _pesan_addon_habis(jenis: str = 'ai') -> dict:
    """Susun pesan 402 — TAWARKAN ADDON, jangan upgrade paket.

    Ini inti strategi Bos: AddOn = mesin uang. Saat kuota habis, user
    diarahkan beli AddOn (murah, bisa berulang), BUKAN pindah paket.
    """
    pilihan = []
    for k, v in ADDON.items():
        pilihan.append({
            'jenis': k, 'nama': v['nama'], 'harga': v['harga'],
            'label': f"Rp {v['harga']:,}".replace(',', '.'),
            'keterangan': v['keterangan'],
        })
    return {
        'ok': False,
        'kode': 'KUOTA_HABIS',
        'pesan': 'Kuota AI bulan ini sudah habis. Beli AddOn untuk lanjut ya — '
                 'AddOn tidak hangus di akhir bulan.',
        'tawarkan': 'ADDON',          # penanda tegas untuk frontend
        'addon': pilihan,
    }


def cek_dan_potong(db: Session, u: User, jenis: str = 'revisi') -> dict:
    """Gerbang utama: cek hak + kuota, lalu POTONG 1.

    Raise HTTPException:
      403 → belum berbayar (pesan upgrade)
      402 → kuota habis (pesan TAWARKAN ADDON)

    Kembalikan dict info pemotongan kalau berhasil.
    """
    if _admin(u):
        return {'dipotong': False, 'alasan': 'admin', 'paket': u.paket or 'gratis'}

    paket = u.paket or 'gratis'

    #  ⭐ SALDO PERMANEN (ACC Bos 26Sep26): "Ai mau kerja lihatnya ke Saldo.
    #     Kalo kurang diarahkan ke pembelian AddOn."
    #     Satu kantong — paket & AddOn bernilai SAMA, TIDAK ada urutan
    #     'paket dulu'. Jalur revisi biasa (1 token) ikut memakai saldo yang
    #     SAMA seperti kerangka per bab (potong_banyak), supaya TIDAK ada dua
    #     buku yang bisa dipakai user untuk lolos dari potongan.
    from . import saldo as _saldo
    saldo_kini = _saldo.sisa(db, u)

    # 2) kurang → TOLAK di depan (jangan eksekusi), arahkan dengan benar
    if saldo_kini < 1:
        # GRATIS tak boleh beli AddOn → arahkan UPGRADE PAKET (aturan Bos:
        # "Free wajib upgrade ke penulis untuk bisa isi saldo.")
        if not boleh_beli_addon(paket):
            raise HTTPException(403, detail={
                'ok': False, 'kode': 'BUTUH_UPGRADE',
                'butuh': 1, 'saldo': saldo_kini, 'kurang': 1,
                'tawarkan': 'UPGRADE', 'paket': paket,
                'pesan': ('Saldo Token Revisimu habis. Paket Gratis belum bisa '
                          'menambah saldo — upgrade ke paket Penulis dulu ya. '
                          'Setelah itu token Paket dan AddOn masuk ke saldo '
                          'yang sama.'),
            })
        raise HTTPException(402, detail=_pesan_addon_habis('ai'))

    # 4) potong dari SALDO + catat bulanan (analitik & notifikasi lama)
    _saldo.pakai(db, u, 1, sumber='pakai', catatan='revisi')
    pakai = ambil_pemakaian(db, u.id)
    pakai.jumlah_revisi += 1
    db.commit()
    sisa = _saldo.sisa(db, u, seed=False)
    log.info('[kuota] user=%s revisi (saldo) sisa=%d (paket=%s)',
             u.id, sisa, paket)

    # 5) 🔔 PEMICU NOTIFIKASI (ACC Bos 17Sep26)
    #    ⚠️ KENAPA PAKAI SESI SENDIRI (`_sesi_baru`) — bukan `db` di atas:
    #    `catat()` bisa memanggil `db.rollback()` kalau penulisan notifikasi
    #    gagal. Kalau memakai sesi yang sama, rollback itu akan MEMBATALKAN
    #    potongan kuota yang baru saja di-commit di atas — mahasiswa jadi
    #    dapat notifikasi "kuota menipis" tanpa kuotanya benar-benar
    #    berkurang. Sesi terpisah memastikan pekerjaan utama SELALU utuh.
    #    Anti-spam 24 jam dijaga di app/notifikasi.py supaya mahasiswa tidak
    #    menerima "sisa 1" berulang-ulang (permintaan Bos: jangan mengganggu).
    try:
        from .notifikasi import periksa_dan_catat
        from .models import SessionLocal as _Sesi
        _db2 = _Sesi()
        try:
            sisa_addon_kini = sisa_addon(_db2, u.id, 'ai')
            tercatat = periksa_dan_catat(
                _db2, u.id, sisa_kuota=sisa, sisa_addon=sisa_addon_kini)
            if tercatat:
                _db2.commit()
                log.info('[notifikasi] user=%s tercatat: %s', u.id, tercatat)
        finally:
            _db2.close()
    except Exception as e:                                        # noqa: BLE001
        log.warning('[notifikasi] pemicu kuota gagal (diabaikan): %s', e)

    return {
        'dipotong': True, 'paket': paket,
        'jumlah_revisi': pakai.jumlah_revisi, 'sisa': sisa,
    }


def cek_kuota_simulasi(db: Session, u: User) -> dict:
    """Gerbang khusus simulasi sidang (Mode Belajar L3)."""
    if _admin(u):
        return {'dipotong': False, 'alasan': 'admin'}
    paket = u.paket or 'gratis'
    jatah = KUOTA_SIMULASI_PAKET.get(paket, 0) + sisa_addon(db, u.id, 'belajar')
    pakai = ambil_pemakaian(db, u.id)
    if pakai.jumlah_simulasi >= jatah:
        raise HTTPException(402, detail={
            'ok': False, 'kode': 'KUOTA_SIMULASI_HABIS',
            'pesan': 'Kuota simulasi sidang habis. AddOn Mode Belajar menambah 1 naskah.',
            'tawarkan': 'ADDON',
        })
    pakai.jumlah_simulasi += 1
    db.commit()
    return {'dipotong': True, 'dipakai': pakai.jumlah_simulasi, 'total': jatah}


# ══════════════════════════════════════════════════════════════════════════
# PEMBELIAN ADDON
# ══════════════════════════════════════════════════════════════════════════
def tambah_addon(db: Session, uid: int, jenis: str, order_id: str = '',
                 paket_user: str | None = None) -> PembelianAddon:
    """Tambahkan AddOn setelah pembayaran sukses.

    AddOn TERKUNCI untuk paket gratis — divalidasi di BACKEND (bukan UI),
    sesuai MASTER_PLAN §4.10.
    """
    if jenis not in ADDON:
        raise ValueError(f'AddOn tidak dikenal: {jenis}')
    if paket_user is not None and paket_user in PAKET_TANPA_ADDON:
        raise PermissionError(
            'AddOn hanya tersedia untuk paket berbayar. Upgrade paket dulu.'
        )
    info = ADDON[jenis]
    baris = PembelianAddon(
        user_id=uid, jenis=jenis, sisa_kuota=info.get('kuota', 0),
        harga=info['harga'], order_id=order_id,
    )
    db.add(baris)

    #  ⭐ MASUK SALDO PERMANEN (ACC Bos 26Sep26): "AddOn masuk atau di
    #     tambah ke saldo... berapa kali beli AddOn masuknya ke saldo semua."
    #     AddOn berkuota (mis. AI +30) langsung masuk ke buku besar saldo.
    #     ⚠️ AddOn dengan `tambahan` (storage) BUKAN token → TIDAK masuk sini.
    _kuota_addon = int(info.get('kuota', 0) or 0)
    if _kuota_addon > 0 and jenis == 'ai':
        try:
            u2 = db.get(User, uid)
            if u2 is not None:
                from . import saldo as _sald
                _sald.masuk(db, u2, _kuota_addon, sumber=f'addon:{jenis}',
                            catatan=f'Token dari AddOn {info["nama"]}',
                            order_id=order_id, commit=False)
        except Exception:                                 # noqa: BLE001
            log.exception('[addon] gagal masukkan AddOn %s ke saldo', jenis)

    # ── AddOn dengan EFEK PERMANEN (ACC Bos 15Sep26) ────────────────────
    # AddOn `storage` TIDAK memakai kuota yang dipotong — dia MENAMBAH
    # kapasitas user secara permanen (+50 MB & +10 folder), tanpa kedaluwarsa.
    # ⚠ `kuota_mb` dinaikkan langsung supaya SEMUA pemeriksaan kuota lama
    #   (main.py /unggah, ai.py revisi) otomatis ikut naik.
    efek = info.get('tambahan') or {}
    if efek:
        u = db.get(User, uid)
        if u is None:
            raise ValueError(f'User {uid} tidak ditemukan untuk AddOn {jenis}')
        for kolom, nilai in efek.items():
            if not hasattr(u, kolom):
                # ⚠ Pesan TIDAK menyebut nama internal (config/modul) — itu
                #   bocor ke user kalau AddOn diterapkan dari halaman bayar.
                #   Detail teknis cukup masuk log.
                log.error('[addon] kolom `%s` tidak ada di User (jenis=%s)',
                          kolom, jenis)
                raise ValueError(
                    'AddOn sedang tidak bisa diaktifkan. '
                    'Hubungi admin: eduai@bikinaja.id')
            setattr(u, kolom, (getattr(u, kolom) or 0) + nilai)

    db.commit()
    log.info('[addon] user=%s jenis=%s tambahan=%s order=%s',
             uid, jenis, efek or info.get('kuota'), order_id)
    return baris


# ══════════════════════════════════════════════════════════════════════════
#  🪙 SATU KANTONG SALDO TOKEN (26Sep26) — aturan Bos
#     "Berapapun sisa saldo token baik berasal dari paket atau AddOn itu
#      sama nilainya."
# ══════════════════════════════════════════════════════════════════════════
def saldo_token(db: Session, u: User, jenis_addon: str = 'ai') -> dict:
    """SALDO TOKEN user = sisa jatah paket + sisa AddOn. Satu angka.

    ⚠️ JANGAN pakai `jatah_paket + sisa_addon` lalu bandingkan dengan
    `jumlah_revisi` (cara lama) — itu yang bikin 402 palsu.
    Cara benar: hitung SISA, bukan total.
    """
    paket = u.paket or 'gratis'
    #  ⭐ SALDO PERMANEN (ACC Bos 26Sep26): satu kantong, tidak hangus.
    #     Paket & AddOn sama-sama MASUK ke sini. Tetap ditampilkan
    #     rincian (sisa_paket/addon) supaya layar bisa menjelaskan asalnya.
    saldo_kini = _saldo.sisa(db, u)
    jatah = KUOTA_PAKET.get(paket, {}).get('revisi', 0)
    pakai = ambil_pemakaian(db, u.id).jumlah_revisi
    addon = sisa_addon(db, u.id, jenis_addon)
    return {
        'saldo': saldo_kini,
        'sisa_paket': max(0, jatah - pakai),
        'jatah_paket': jatah,
        'terpakai': pakai,
        'addon': addon,
        'paket': paket,
        'boleh_beli_addon': bool(boleh_beli_addon(paket)),
    }


def potong_banyak(db: Session, u: User, butuh: int,
                  jenis_addon: str = 'ai') -> dict:
    """Potong `butuh` token SEKALIGUS dari SATU KANTONG saldo.

    ATURAN BOS: kalau saldo < butuh → TOLAK (jangan eksekusi), arahkan
    beli AddOn. Admin dikecualikan (tidak dipotong).

    Raise HTTPException 402 + tawaran AddOn kalau kurang.
    Return {'saldo_sebelum', 'saldo_sesudah', 'butuh', 'dipotong'}.
    """
    butuh = int(butuh)
    if butuh <= 0:
        return {'butuh': 0, 'dipotong': 0, 'saldo_sebelum': None,
                'saldo_sesudah': None}

    if _admin(u):
        return {'butuh': butuh, 'dipotong': 0, 'admin': True,
                'saldo_sebelum': None, 'saldo_sesudah': None}

    info = saldo_token(db, u, jenis_addon)
    saldo = info['saldo']

    #  ── GERBANG: saldo kurang → TOLAK di DEPAN (tidak boleh eksekusi) ──
    if saldo < butuh:
        kurang = butuh - saldo
        #  ⭐ ATURAN BOS (26Sep26): "Free wajib upgrade ke penulis untuk
        #     bisa isi saldo." ⇒ GRATIS TIDAK diarahkan ke AddOn (dia tak
        #     boleh beli AddOn selamanya) — diarahkan UPGRADE PAKET.
        if not boleh_beli_addon(u.paket or 'gratis'):
            raise HTTPException(403, detail={
                'ok': False, 'kode': 'BUTUH_UPGRADE',
                'butuh': butuh, 'saldo': saldo, 'kurang': kurang,
                'tawarkan': 'UPGRADE', 'paket': u.paket or 'gratis',
                'pesan': (f'Untuk ini perlu {butuh} Token Revisi, sedangkan '
                          f'saldo kamu {saldo} (kurang {kurang}). Paket Gratis '
                          'belum bisa menambah saldo — upgrade ke paket '
                          'Penulis dulu ya. Setelah itu token Paket dan AddOn '
                          'masuk ke saldo yang sama.'),
            })
        detail = _pesan_addon_habis(jenis_addon)
        if isinstance(detail, dict):
            detail = dict(detail)
            detail['kode'] = 'SALDO_KURANG'
            detail['butuh'] = butuh
            detail['saldo'] = saldo
            detail['kurang'] = kurang
            #  Pesan BARU & UTUH (jangan tempel kalimat lama "kuota habis" —
            #  itu keliru: saldo masih ada, hanya KURANG dari kebutuhan).
            detail['pesan'] = (
                f'Untuk membuat ini perlu {butuh} Token Revisi, sedangkan '
                f'saldo Token Revisimu {saldo} (kurang {kurang}). '
                'Tambah AddOn AI dulu ya — AddOn tidak hangus di akhir bulan.')
        else:
            detail = {'ok': False, 'kode': 'SALDO_KURANG', 'butuh': butuh,
                      'saldo': saldo, 'kurang': kurang,
                      'pesan': (f'Untuk ini perlu {butuh} Token Revisi, '
                                f'sedangkan saldo kamu {saldo}.')}
        raise HTTPException(402, detail=detail)

    #  ── POTONG DARI SALDO PERMANEN (satu kantong, ACC Bos 26Sep26) ──
    #     TIDAK ada urutan 'paket dulu' — semua pemasukan (paket & AddOn)
    #     masuk ke saldo yang SAMA (putusan Bos: "B" = permanen).
    from . import saldo as _saldo
    _saldo.pakai(db, u, butuh, sumber='pakai',
                 catatan=f'pakai:{jenis_addon}')
    sesudah = _saldo.sisa(db, u, seed=False)

    #  catatan bulanan tetap diperbarui (analitik & notifikasi lama)
    pakai = ambil_pemakaian(db, u.id)
    pakai.jumlah_revisi += butuh
    db.commit()

    log.info('[kuota] potong_banyak user=%s butuh=%d saldo %s → %s',
             u.id, butuh, saldo, sesudah)

    #  🔔 notifikasi (pola sama dengan cek_dan_potong)
    try:
        from .notifikasi import periksa_dan_catat
        from .models import SessionLocal as _Sesi
        _db2 = _Sesi()
        try:
            periksa_dan_catat(_db2, u.id, sisa_kuota=sesudah['saldo'],
                              sisa_addon=sesudah['addon'])
        finally:
            _db2.close()
    except Exception:                                     # noqa: BLE001
        pass

    return {'butuh': butuh, 'dipotong': butuh,
            'saldo_sebelum': saldo, 'saldo_sesudah': sesudah}


def kembalikan_banyak(db: Session, u: User, jumlah: int,
                      jenis_addon: str = 'ai') -> dict:
    """Kembalikan `jumlah` token ke SALDO PERMANEN (pagar P2).

    Dipakai kalau fitur gagal SETELAH token dipotong.
    """
    jumlah = int(jumlah)
    if jumlah <= 0 or _admin(u):
        return {'dikembalikan': 0}
    from . import saldo as _saldo
    h = _saldo.kembalikan(db, u, jumlah, sumber='kembali',
                          catatan='fitur gagal -> saldo dikembalikan')
    #  catatan bulanan ikut dikurangi (biar analitik tetap seimbang)
    pakai = ambil_pemakaian(db, u.id)
    pakai.jumlah_revisi = max(0, pakai.jumlah_revisi - jumlah)
    db.commit()
    log.info('[kuota] kembalikan_banyak user=%s jumlah=%d -> sisa %s',
             u.id, jumlah, h['sisa'])
    return h
