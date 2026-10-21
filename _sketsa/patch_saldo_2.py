"""SALDO PERMANEN — MESIN + SAMBUNGAN (tahap 2).

1. app/saldo.py  — mesin: masuk(), pakai(), sisa(), seed sekali per user
2. kuota.saldo_token() → baca dari saldo permanen
3. main.py topup_cek   → bayar paket: naikkan u.paket + saldo masuk
4. kuota.tambah_addon  → AddOn masuk saldo juga (lewat tabel addon yg ada)
"""
import pathlib

BASE = pathlib.Path('/opt/data/services/eduai-publishing')

# ══════════════════════════════════════════════════════════════════════════
#  1. MESIN BARU: app/saldo.py
# ══════════════════════════════════════════════════════════════════════════
MESIN = '''"""MESIN SALDO TOKEN PERMANEN — satu kantong (ACC Bos 26Sep26).

ATURAN BOS: "Apapun upgrade paketnya dan berapa kali beli AddOn masuknya ke
saldo semua. AI mau kerja lihatnya ke Saldo. Kalo kurang diarahkan ke
pembelian AddOn."

PEMASUKAN SALDO:
  · Paket (gratis→penulis→peneliti→penerbit): token paket MASUK SEKALI
  · AddOn (AI +30 dll): token AddOn masuk
PEMAKAIAN: potong dari saldo — TIDAK hangus tiap bulan.

KOMPATIBEL MUNDUR: user lama (yang tokennya sudah terpakai sebagian) tidak
kehilangan — sisa lama di-seed SEKALI ke buku besar saat pertama dibaca.
"""
from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import SaldoToken, User, PemakaianAI, PembelianAddon
from .config import KUOTA_PAKET

log = logging.getLogger(__name__)


def _baris_terakhir(db: Session, uid: int) -> SaldoToken | None:
    return db.execute(
        select(SaldoToken).where(SaldoToken.user_id == uid)
        .order_by(SaldoToken.id.desc()).limit(1)
    ).scalars().first()


def _sisa_lama(db: Session, u: User) -> int:
    """Sisa dari cara LAMA (jatah paket - terpakai + AddOn).

    Hanya dipakai SEKALI saat seed migrasi, supaya user lama tidak rugi.
    Setelah ada baris di `saldo_token`, angka ini TIDAK dipakai lagi.
    """
    paket = u.paket or 'gratis'
    jatah = KUOTA_PAKET.get(paket, {}).get('revisi', 0)
    pakai = db.execute(
        select(PemakaianAI).where(PemakaianAI.user_id == u.id)
    ).scalars().all()
    terpakai = sum(p.jumlah_revisi for p in pakai)
    addon = db.execute(
        select(PembelianAddon).where(PembelianAddon.user_id == u.id,
                                     PembelianAddon.jenis == 'ai')
    ).scalars().all()
    sisa_addon = sum(max(0, b.sisa_kuota) for b in addon)
    return max(0, jatah - terpakai) + sisa_addon


def sisa(db: Session, u: User, seed: bool = True) -> int:
    """SALDO SEKARANG (satu kantong). Seed sekali kalau buku besar kosong."""
    b = _baris_terakhir(db, u.id)
    if b is None:
        if not seed:
            return 0
        awal = _sisa_lama(db, u)
        b = masuk(db, u, awal, sumber='awal:migrasi',
                  catatan='Sisa token sebelum sistem saldo permanen')
        if awal == 0:
            return 0
    return int(b.sisa)


def masuk(db: Session, u: User, jumlah: int, sumber: str,
          catatan: str = '', order_id: str = '', commit: bool = True) -> SaldoToken | None:
    """TAMBAH saldo (paket / AddOn / pengembalian)."""
    jumlah = int(jumlah)
    if jumlah == 0:
        return _baris_terakhir(db, u.id)
    sebelum = 0
    b = _baris_terakhir(db, u.id)
    if b is not None:
        sebelum = int(b.sisa)
    baris = SaldoToken(user_id=u.id, jumlah=jumlah, sisa=sebelum + jumlah,
                       sumber=sumber, catatan=catatan[:200], order_id=order_id)
    db.add(baris)
    if commit:
        db.commit()
    log.info('[saldo] user=%s MASUK %+d (%s) → %d', u.id, jumlah, sumber,
             sebelum + jumlah)
    return baris


def pakai(db: Session, u: User, jumlah: int, sumber: str = 'pakai',
          catatan: str = '', commit: bool = True) -> dict:
    """POTONG saldo. Raise ValueError kalau kurang (pemanggil ubah ke 402)."""
    jumlah = int(jumlah)
    if jumlah <= 0:
        return {'dipotong': 0, 'sisa': sisa(db, u, seed=False)}
    kini = sisa(db, u)
    if kini < jumlah:
        raise ValueError(f'saldo kurang: {kini} < {jumlah}')
    baris = SaldoToken(user_id=u.id, jumlah=-jumlah, sisa=kini - jumlah,
                       sumber=sumber, catatan=catatan[:200])
    db.add(baris)
    if commit:
        db.commit()
    log.info('[saldo] user=%s PAKAI -%d (%s) → %d', u.id, jumlah, sumber,
             kini - jumlah)
    return {'dipotong': jumlah, 'sisa': kini - jumlah, 'sisa_sebelum': kini}


def kembalikan(db: Session, u: User, jumlah: int, sumber: str = 'kembali',
               catatan: str = '', commit: bool = True) -> dict:
    """KEMBALIKAN saldo (pagar P2: fitur gagal → saldo utuh)."""
    masuk(db, u, int(jumlah), sumber=sumber, catatan=catatan, commit=commit)
    return {'dikembalikan': int(jumlah), 'sisa': sisa(db, u, seed=False)}


def rincian(db: Session, u: User, batas: int = 20) -> dict:
    """Riwayat saldo (untuk tampilan 'token saya dari mana')."""
    baris = db.execute(
        select(SaldoToken).where(SaldoToken.user_id == u.id)
        .order_by(SaldoToken.id.desc()).limit(batas)
    ).scalars().all()
    return {'sisa': sisa(db, u), 'riwayat': [
        {'jumlah': b.jumlah, 'sisa': b.sisa, 'sumber': b.sumber,
         'catatan': b.catatan, 'dibuat': b.dibuat.isoformat() if b.dibuat else ''}
        for b in baris]}
'''
(BASE / 'app/saldo.py').write_text(MESIN)
print('✅ app/saldo.py dibuat')

# ══════════════════════════════════════════════════════════════════════════
#  2. kuota.saldo_token() → baca dari saldo permanen
# ══════════════════════════════════════════════════════════════════════════
K = BASE / 'app/kuota.py'
s = K.read_text()
if 'from .saldo import' not in s:
    s = s.replace(
        "from .models import PembelianAddon, PemakaianAI, User",
        "from .models import PemakaianAI, PembelianAddon, User\n"
        "from . import saldo as _saldo", 1)

    lama = '''    paket = u.paket or 'gratis'
    jatah = KUOTA_PAKET.get(paket, {}).get('revisi', 0)
    pakai = ambil_pemakaian(db, u.id).jumlah_revisi
    sisa_paket = max(0, jatah - pakai)
    addon = sisa_addon(db, u.id, jenis_addon)
    return {
        'saldo': sisa_paket + addon,
        'sisa_paket': sisa_paket,
        'jatah_paket': jatah,
        'terpakai': pakai,
        'addon': addon,
        'paket': paket,
        'boleh_beli_addon': bool(boleh_beli_addon(paket)),
    }'''
    baru = '''    paket = u.paket or 'gratis'
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
    }'''
    assert lama in s, 'pola saldo_token tidak ketemu'
    s = s.replace(lama, baru, 1)
    K.write_text(s)
    print('✅ kuota.saldo_token() → baca saldo permanen')
else:
    print('⚠️ kuota sudah pakai saldo permanen')
