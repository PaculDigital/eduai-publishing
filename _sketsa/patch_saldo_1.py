"""SALDO TOKEN PERMANEN — SATU KANTONG (putusan Bos 26Sep26).

📌 ATURAN BOS (verbatim):
   "Free wajib upgrade ke penulis untuk bisa isi saldo.
    Penulis token masuk atau ditambah saldo.
    Upgrade ke peneliti token masuk atau ditambah ke saldo.
    Upgrade ke penerbit token masuk atau di tambah ke saldo.
    AddOn masuk atau di tambah ke saldo.
    Apapun upgrade paketnya dan berapa kali beli AddOn masukknya ke saldo
    semua. Ai mau kerja lihatnya ke Saldo. Kalo kurang diarahkan ke
    pembelian AddOn"
   + PUTUSAN: "B — Saldo PERMANEN: bayar paket → token masuk saldo SEKALI,
     tidak hangus, dipakai kapan saja"

⇒ RANCANGAN:
   · Tabel BARU `saldo_token` = BUKU BESAR (ledger) satu kantong.
     Tiap baris = 1 pemasukan/pemakaian token. `sisa` = jumlah berjalan.
   · MASUK saldo: paket (gratis→penulis→peneliti→penerbit) + AddOn.
   · Pemakaian MENGURANGI saldo — TIDAK HANGUS tiap bulan.
   · AI kerja → lihat saldo. Kurang → arahkan beli AddOn.

⚠️ KOMPATIBEL MUNDUR (penting — ada uang di sistem berjalan):
   `saldo_token()` dihitung = sisa lama (jatah paket - terpakai + AddOn)
   DITAMBAH saldo permanen baru. Jadi user yang tokennya sudah dipakai
   TIDAK kehilangan. Sekali saja per user di-seed ke tabel baru.
"""
import pathlib

M = pathlib.Path('/opt/data/services/eduai-publishing/app/models.py')
s = M.read_text()

if 'class SaldoToken' in s:
    print('⚠️ SaldoToken SUDAH ADA')
    raise SystemExit(0)

#  ── 1. TABEL BARU ──
TABEL = '''

class SaldoToken(Base):
    """BUKU BESAR (ledger) SALDO TOKEN — SATU KANTONG (ACC Bos 26Sep26).

    KENAPA LEDGER, bukan satu kolom angka:
      Bos minta "apapun upgrade paketnya dan berapa kali beli AddOn masuknya
      ke saldo semua" — jadi setiap PEMASUKAN harus punya asal-usul yang bisa
      diaudit (dari paket mana / AddOn mana / tanggal berapa). Satu kolom
      angka tidak bisa menjawab "token saya dari mana?" saat user bertanya.

    `sisa` = saldo berjalan SETELAH baris ini (memudahkan tampilan & audit).

    jumlah > 0 = pemasukan · jumlah < 0 = pemakaian.
    """
    __tablename__ = 'saldo_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True,
                                         nullable=False)
    jumlah: Mapped[int] = mapped_column(Integer, default=0)   # +masuk / -pakai
    sisa: Mapped[int] = mapped_column(Integer, default=0)     # saldo sesudah
    sumber: Mapped[str] = mapped_column(String(40), default='', index=True)
    #  ↑ 'paket:penulis' | 'upgrade:penulis|peneliti' | 'addon:ai' |
    #    'pakai:kerangka' | 'kembali:kerangka' | 'awal:migrasi'
    catatan: Mapped[str] = mapped_column(String(200), default='')
    order_id: Mapped[str] = mapped_column(String(100), default='', index=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
'''
s = s.rstrip() + '\n' + TABEL

#  ── 2. daftarkan tabel baru di migrasi otomatis (kalau perlu) ──
#     create_all() sudah membuat tabel BARU otomatis → tidak perlu ALTER.
M.write_text(s)
print('✅ class SaldoToken ditambahkan di app/models.py')
