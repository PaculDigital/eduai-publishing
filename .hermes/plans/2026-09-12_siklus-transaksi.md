# Perbaikan Siklus Hidup Transaksi EduAi — Implementation Plan

**STATUS: ✅ SELESAI & LIVE (12Sep26)** — image `eduai-app:v1-siklus3`

**Hasil uji:**
- E2E `uji_siklus_lengkap.py` → **65 LULUS, 0 GAGAL** (9 bagian)
- Visual CloakBrowser HP `uji_visual_siklus.py` → **SEMUA LULUS**
- DB `integrity_check=ok`; transaksi asli Bos (3 baris) **utuh**

**3 bug nyata ketemu & diperbaiki:** (1) `order_id` bentrok → 500,
(2) tab tidak pindah saat "Lanjutkan Bayar" (QR tak terlihat),
(3) skrip uji salah baca guard redirect (bukan bug app).

---

**Goal:** Menutup 4 celah siklus hidup transaksi QRIS: auto-expire, batas transaksi
pending, lanjutkan pembayaran dari riwayat, dan pagination.

**Architecture:** Semua perubahan di `eduai-app` (FastAPI + SQLite + template Jinja).
Tidak ada cron — auto-expire dijalankan **lazy** saat endpoint riwayat/topup dipanggil
(pola paling sederhana & aman untuk SQLite, tanpa proses latar baru).

**Tech Stack:** FastAPI, SQLAlchemy, SQLite (bind-mount `/app/data`), Jinja2, vanilla JS.

**Status saat ini (hasil audit 12Sep26):**

| # | Celah | Bukti |
|---|---|---|
| 1 | Expired tidak mengubah status | `QRIS_EXPIRE_MENIT=20` hanya konstanta tampilan (`config.py:77`); tidak ada penulis status |
| 2 | Transaksi pending tak dibatasi | `topup_buat` (`main.py:405`) tak ada cek pending sama sekali |
| 3 | Tak bisa lanjutkan bayar dari riwayat | QR tersimpan di `trx.bukti` (`main.py:430`) tapi tak ada endpoint pengambil; kartu riwayat hanya punya tombol "Batalkan" |
| 4 | Tak ada pagination | hard `limit(20)` (`main.py:550`) — transaksi lama hilang tanpa kabar |

---

## Keputusan desain (perlu konfirmasi Bos)

1. **Status `expired`** = status ke-5 (`pending|sukses|gagal|batal|expired`).
   Alasan: `gagal` = Pakasir menolak/mati; `expired` = user tidak bayar dalam 20 menit.
   Beda makna → beda analitik. **Rekomendasi Wulan: status baru.**
2. **Batas pending = 3.** Angka sama dengan `MAX_SESI_EDIT` supaya konsisten dan
   mudah diingat user. Bisa diubah lewat env `EDUAI_MAX_PENDING`.
3. **Lazy expire, bukan cron.** Dijalankan di awal `api_riwayat` + `topup_buat` +
   `topup_cek`. Alasan: tidak menambah proses/container baru di VPS, dan tetap
   akurat karena setiap kali user melihat riwayat, data disegarkan dulu.

---

## Task 1: Status `expired` di DB

**Objective:** Tambah `expired` sebagai status valid + kolom waktu kedaluwarsa.

**Files:**
- Modify: `app/models.py:82-94` (`class Transaksi`)
- Modify: `app/config.py:77` (tambah `MAX_PENDING`)

**Step 1: Tambah kolom `kedaluwarsa` di model**

```python
# app/models.py — class Transaksi
# 12Sep26: simpan batas waktu QR. Dipakai untuk auto-expire LAZY (tanpa cron).
kedaluwarsa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Update juga komentar status:

```python
# pending | sukses | gagal | batal | expired
status: Mapped[str] = mapped_column(String(30), default='pending')
```

**Step 2: Tambah konstanta batas pending di config**

```python
# app/config.py — setelah QRIS_EXPIRE_MENIT
# 12Sep26: batas transaksi pending serentak per user. Tanpa ini, user bisa
# membuat puluhan QRIS di Pakasir -> boros & berisiko kena rate-limit.
MAX_PENDING = int(os.getenv('EDUAI_MAX_PENDING', '3'))
```

**Step 3: Migrasi kolom (SQLite ALTER, idempoten)**

```python
# app/db.py atau di init_db() — TAMBAH, jangan ganti
def _migrasi_kolom():
    """ALTER TABLE idempoten untuk kolom baru (SQLite tak punya IF NOT EXISTS)."""
    from sqlalchemy import text
    with engine.connect() as c:
        kolom = {r[1] for r in c.execute(text('PRAGMA table_info(transaksi)'))}
        if 'kedaluwarsa' not in kolom:
            c.execute(text('ALTER TABLE transaksi ADD COLUMN kedaluwarsa DATETIME'))
            c.commit()
```

**Step 4: Verifikasi**

Run: `docker exec eduai-app python3 -c "import sqlite3;c=sqlite3.connect('file:/app/data/eduai.db?mode=ro',uri=True);print([r[1] for r in c.execute('PRAGMA table_info(transaksi)')])"`
Expected: daftar memuat `kedaluwarsa`

**Step 5: Commit**

```bash
git add app/models.py app/config.py app/db.py
git commit -m "feat(eduai): status expired + kolom kedaluwarsa + MAX_PENDING"
```

---

## Task 2: Helper auto-expire (lazy)

**Objective:** Satu fungsi yang menandai pending kedaluwarsa → `expired`.

**Files:**
- Modify: `app/main.py` (tambah helper di atas `api_riwayat`)

**Step 1: Helper**

```python
def _expire_pending(db: Session, u: User) -> int:
    """Tandai transaksi pending milik user yang sudah lewat batas -> 'expired'.

    KENAPA lazy (dipanggil saat user lihat riwayat), bukan cron:
      - Tidak menambah proses/container di VPS.
      - Selalu akurat saat user membuka riwayat (momen yang dia pedulikan).
    KENAPA pakai kolom `kedaluwarsa` kalau ada, kalau tidak fallback dibuat+20m:
      - Pakasir memberi `expired_at`; lebih tepat daripada menebak.
    """
    sekarang = datetime.now(timezone.utc).replace(tzinfo=None)
    batas_bawah = sekarang - timedelta(minutes=0)   # placeholder, lihat bawah
    rows = db.scalars(select(Transaksi).where(
        Transaksi.user_id == u.id, Transaksi.status == 'pending')).all()
    n = 0
    for t in rows:
        bts = _sadar(t.kedaluwarsa) or (_sadar(t.dibuat) + timedelta(minutes=QRIS_EXPIRE_MENIT))
        if bts and sekarang > bts:
            t.status = 'expired'
            n += 1
    if n:
        db.commit()
    return n
```

⚠️ **WAJIB pakai helper `_sadar()`** (memory: SQLite `DateTime(timezone=True)` tetap
balikan NAIVE → TypeError saat dikurangi `now(utc)`). Kalau `_sadar` belum ada di
`main.py`, tambahkan:

```python
def _sadar(d):
    """SQLite balikan datetime NAIVE walau timezone=True -> tambah UTC."""
    if d is None:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
```

**Step 2: Simpan `kedaluwarsa` saat buat transaksi**

`topup_buat` (`main.py:405`) — parse `expired_at` dari Pakasir:

```python
trx.bukti = hasil.get('payment_number', '')[:2000]
# 12Sep26: simpan batas berlaku (dipakai auto-expire)
trx.kedaluwarsa = _parse_expired(hasil.get('expired_at'))
db.commit()
```

```python
def _parse_expired(s):
    """Parse 'expired_at' Pakasir -> datetime naive UTC. Toleran banyak format."""
    if not s:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
        try:
            return datetime.strptime(str(s)[:26].replace('T', ' '), fmt)
        except ValueError:
            continue
    return None
```

**Step 3: Panggil di `api_riwayat`**

```python
@app.get('/api/riwayat')
def api_riwayat(u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    _expire_pending(db, u)     # <- TAMBAH (baris pertama)
    ...
```

**Step 4: Verifikasi**

```bash
docker exec eduai-app python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
c.execute(\"UPDATE transaksi SET dibuat=datetime('now','-40 minutes') WHERE status='pending'\")
c.commit(); print('dimundurkan 40 menit')"
# lalu buka /api/riwayat dgn sesi login -> status harus jadi 'expired'
```
Expected: pending lama → `expired`

**Step 5: Commit**

```bash
git commit -am "feat(eduai): auto-expire pending transaksi (lazy)"
```

---

## Task 3: Batas transaksi pending

**Objective:** Tolak pembuatan transaksi ke-4 saat masih ada 3 pending.

**Files:**
- Modify: `app/main.py` — di dalam `topup_buat`

**Step 1: Tambah cek setelah validasi paket**

```python
# 12Sep26: expire dulu, biar pending yang sudah mati tidak ikut dihitung.
_expire_pending(db, u)
jml = db.scalar(select(func.count()).select_from(Transaksi).where(
    Transaksi.user_id == u.id, Transaksi.status == 'pending'))
if jml >= MAX_PENDING:
    return JSONResponse(
        {'ok': False, 'kode': 'PENDING_PENUH',
         'pesan': f'Anda masih punya {jml} transaksi menunggu. '
                  f'Bayar atau batalkan dulu salah satunya '
                  f'(maksimal {MAX_PENDING} transaksi menunggu).'},
        status_code=429)
```

Pastikan `func` dan `MAX_PENDING` sudah diimpor/di-import di `main.py`.

**Step 2: FE tangani kode `PENDING_PENUH`**

Di `_topup_popup.html`, di handler pembuatan transaksi (`/api/topup/buat`):

```js
if (d.kode === 'PENDING_PENUH') {
  // Arahkan user ke tab riwayat + beri pesan jelas
  tampilGalat(d.pesan);
  setTimeout(function () { pindahTab('riwayat'); }, 1200);
  return;
}
```

**Step 3: Verifikasi**

```bash
# buat 4 transaksi berturut-turut; yang ke-4 harus 429
for i in 1 2 3 4; do
  curl -s -o /dev/null -w "ke-$i -> %{http_code}\n" -b /tmp/ck \
    -X POST -d 'paket=penulis' https://eduai.bikinaja.id/api/topup/buat
done
```
Expected: `ke-1..3 -> 200`, `ke-4 -> 429`

**Step 4: Commit**

```bash
git commit -am "feat(eduai): batas maksimal transaksi pending per user"
```

---

## Task 4: Lanjutkan pembayaran dari riwayat

**Objective:** Kartu pending bisa dibuka kembali QR-nya.

**Files:**
- Modify: `app/main.py` — endpoint baru
- Modify: `app/templates/_topup_popup.html` — tombol + handler

**Step 1: Endpoint ambil QR transaksi pending**

```python
@app.post('/api/topup/lanjut')
def topup_lanjut(order_id: str = Form(...), u: User = Depends(wajib_login),
                 db: Session = Depends(get_db)):
    """Ambil ulang QR transaksi pending supaya pembayaran bisa dilanjutkan.

    Aman karena: (a) hanya milik user ini, (b) hanya status 'pending'
    (yang sudah sukses/batal/expired tidak ada gunanya ditampilkan).
    """
    _expire_pending(db, u)
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')
    if trx.status != 'pending':
        return JSONResponse(
            {'ok': False, 'status': trx.status,
             'pesan': f'Transaksi berstatus {trx.status}, tidak bisa dilanjutkan.'},
            status_code=409)
    p = PAKET.get(trx.paket, {})
    return {'ok': True, 'order_id': trx.order_id, 'qr': trx.bukti or '',
            'paket': p.get('nama', trx.paket), 'mb': trx.tambahan_mb,
            'jumlah': trx.jumlah, 'total_bayar': trx.jumlah,
            'menit': QRIS_EXPIRE_MENIT, 'sandbox': PAKASIR_SANDBOX,
            'sisa_detik': _sisa_detik(trx)}
```

```python
def _sisa_detik(trx) -> int:
    """Sisa detik sebelum QR kedaluwarsa (>=0)."""
    bts = _sadar(trx.kedaluwarsa) or (_sadar(trx.dibuat) + timedelta(minutes=QRIS_EXPIRE_MENIT))
    if not bts:
        return QRIS_EXPIRE_MENIT * 60
    return max(0, int((bts - datetime.now(timezone.utc)).total_seconds()))
```

**Step 2: FE — tombol "Lanjutkan Bayar" di kartu pending**

Di `muatRiwayat()`, di samping tombol `Batalkan`:

```js
if (t.bisa_batal) {          // = status pending
  var lanjut = document.createElement('button');
  lanjut.type = 'button';
  lanjut.className = 'rw-lanjut';
  lanjut.textContent = 'Lanjutkan Bayar';
  lanjut.onclick = function () { lanjutkanBayar(t.order_id); };
  kartu.appendChild(lanjut);
}
```

**Step 3: FE — handler `lanjutkanBayar`**

```js
async function lanjutkanBayar(orderId) {
  try {
    var fd = new FormData(); fd.append('order_id', orderId);
    var r = await fetch('/api/topup/lanjut', { method: 'POST', body: fd });
    var d = await r.json();
    if (!d.ok) { alert(d.pesan || 'Tidak bisa melanjutkan.'); muatRiwayat(); return; }
    orderAktif = d.order_id;
    document.getElementById('rp-paket').textContent = d.paket + ' · +' + d.mb + ' MB';
    document.getElementById('rp-jumlah').textContent = rupiah(d.total_bayar);
    document.getElementById('kode-order').textContent = d.order_id;
    gambarQR(d.qr);                  // pakai fungsi yang sudah ada
    mulaiHitungMundur(d.sisa_detik / 60);
    tampilLangkah(2);                // langsung ke langkah QRIS
    mulaiPolling();
  } catch (e) {
    alert('Gagal memuat QR. Periksa koneksi lalu coba lagi.');
  }
}
```

**Step 4: CSS tombol**

```css
.rw-lanjut{margin-top:8px;width:100%;padding:9px 12px;border-radius:40px;cursor:pointer;
           font-family:inherit;font-size:12.5px;font-weight:700;transition:.2s;
           border:1.5px solid var(--hijau);background:var(--hijau);color:#fff}
.rw-lanjut:hover{background:#16712F}
```

**Step 5: Verifikasi**

```bash
# 1. buat transaksi -> catat order_id
# 2. POST /api/topup/lanjut dengan order_id -> harus ok=True + ada 'qr'
# 3. batalkan -> POST lanjut lagi -> harus 409
```
Expected: QR lama tampil kembali; transaksi non-pending ditolak

**Step 6: Commit**

```bash
git commit -am "feat(eduai): lanjutkan pembayaran dari riwayat"
```

---

## Task 5: Pagination riwayat

**Objective:** Riwayat bisa dimuat bertahap + info total.

**Files:**
- Modify: `app/main.py` — `api_riwayat`
- Modify: `app/templates/_topup_popup.html` — tombol "Muat lebih banyak"

**Step 1: `/api/riwayat` ber-paginasi**

```python
@app.get('/api/riwayat')
def api_riwayat(hal: int = 1, per: int = 10,
                u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    """Riwayat ber-paginasi (12Sep26). `hal` mulai dari 1."""
    _expire_pending(db, u)
    hal = max(1, hal)
    per = min(max(1, per), 50)          # batasi supaya tidak dijadikan DoS
    dasar = select(Transaksi).where(Transaksi.user_id == u.id)
    total = db.scalar(select(func.count()).select_from(Transaksi)
                      .where(Transaksi.user_id == u.id))
    rows = db.scalars(dasar.order_by(Transaksi.dibuat.desc())
                      .offset((hal - 1) * per).limit(per)).all()
    return {'riwayat': [...], 'total': total, 'halaman': hal, 'per': per,
            'ada_lagi': hal * per < total}
```

**Step 2: FE — tombol "Muat lebih banyak"**

Simpan daftar di memori FE; tambah tombol di bawah daftar kalau `ada_lagi`:

```js
var _rwHal = 1, _rwSemua = [];
function muatRiwayat(lanjut) {
  if (!lanjut) { _rwHal = 1; _rwSemua = []; }
  fetch('/api/riwayat?hal=' + _rwHal + '&per=10')
    .then(r => r.json())
    .then(function (d) {
      _rwSemua = _rwSemua.concat(d.riwayat || []);
      gambarDaftar(_rwSemua, d.total);
      if (d.ada_lagi) { /* tampilkan tombol "Muat lebih banyak" */ }
    });
}
```

**Step 3: Verifikasi**

```bash
docker exec eduai-app python3 -c "
import sqlite3
c=sqlite3.connect('file:/app/data/eduai.db?mode=ro',uri=True)
print('total:', c.execute('SELECT COUNT(*) FROM transaksi').fetchone()[0])"
# buka /api/riwayat?hal=1&per=2 dan ?hal=2&per=2 -> tidak boleh ada baris kembar
```
Expected: `total` benar, halaman berurutan tanpa duplikat

**Step 4: Commit**

```bash
git commit -am "feat(eduai): pagination riwayat transaksi"
```

---

## Task 6: Deploy & verifikasi menyeluruh

**Objective:** Naikkan ke produksi dengan bukti, bukan klaim.

**Step 1: Uji lokal dulu (tanpa deploy)**

```bash
cd /opt/data/services/eduai-publishing && python3 -m py_compile app/main.py app/models.py app/config.py
node --check /tmp/popup.js   # ekstrak dulu dari template
```

**Step 2: Backup DB (WAJIB sebelum sentuh produksi)**

```bash
BK="_arsip/pre-siklus-$(date +%Y%m%d-%H%M%S)" && mkdir -p "$BK"
docker exec eduai-app python3 -c "
import sqlite3;c=sqlite3.connect('/app/data/eduai.db')
print(c.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
print(c.execute('PRAGMA integrity_check').fetchone()[0]);c.close()"
docker cp eduai-app:/app/data/eduai.db "$BK/eduai.db"
python3 -c "
import sqlite3;c=sqlite3.connect('$BK/eduai.db')
print('VERIFY:', c.execute('SELECT COUNT(*) FROM transaksi').fetchone()[0])"
```

**Step 3: Build + deploy**

```bash
docker build -t eduai-app:v1-siklus .
sed -i 's|eduai-app:.*$|eduai-app:v1-siklus|' scripts/jalankan.sh
bash scripts/jalankan.sh
```

**Step 4: Uji E2E nyata (HTTP, lewat domain)**

Cek minimal:
- Auto-expire: mundurkan `dibuat` 40 menit → riwayat harus `expired`
- Batas pending: transaksi ke-4 → **429**
- Lanjut bayar: transaksi pending → `qr` ada; transaksi batal → **409**
- Pagination: `hal=1&per=2` + `hal=2&per=2` → total & tidak duplikat
- Anti-IDOR: lanjut dengan order_id user lain → **404**

**Step 5: Uji visual (CloakBrowser, mode HP)**

- Kartu pending tampil tombol **"Lanjutkan Bayar"**
- Klik → kembali ke layar QR dengan QR sama
- Badge **"Kedaluwarsa"** tampil untuk transaksi expired

**Step 6: Bersihkan data uji**

Hapus transaksi milik user uji (`qris.uji@eduai.local`) setelah verifikasi —
**minta ACC Bos dulu**, jangan hapus transaksi milik Bos.

---

## Risks & Tradeoffs

| Risiko | Mitigasi |
|---|---|
| ALTER TABLE di DB produksi | Kolom baru nullable → aman & cepat di SQLite. Backup dulu. |
| Lazy expire tidak jalan kalau user tak buka app | Dapat diterima: status hanya relevan saat user melihatnya. (Opsi lanjut: cron harian.) |
| Batas 3 pending bisa mengganggu user yang sah | Pesan jelas + arahkan ke riwayat. Angka via env, mudah diubah. |
| `expired_at` Pakasir formatnya bisa berubah | `_parse_expired` toleran + fallback `dibuat + 20 menit`. |
| QR lama sudah mati di Pakasir walau sisa waktu belum habis | Saat "Lanjutkan Bayar", kalau Pakasir bilang `canceled` → langsung set `expired`. |

## Keputusan FINAL Bos (12Sep26)

1. **Status `expired`** = status ke-5 ✅ (`pending|sukses|gagal|batal|expired`)
2. **Batas pending = 3** ✅ (`EDUAI_MAX_PENDING=3`)
3. **Pagination = 10 per halaman** ✅
4. **QR lama mati → buat QR BARU, tapi `order_id` DIPAKAI TERUS** ✅
   **+** kalau pending sudah **≥3 → TOLAK** (pesan: batalkan dulu salah satu)

### Aturan `/api/topup/lanjut` (FINAL — revisi dari draf awal)

⚠️ **BEDA DENGAN DRAF AWAL:** draf awal Wulan bikin `order_id` BARU → riwayat
jadi penuh baris sampah (1 transaksi bisa jadi 2-3 baris). Bos koreksi:
**1 baris tetap 1 baris.** QR baru dibuat dengan `order_id` **yang SAMA**,
lalu `bukti` + `kedaluwarsa` di-**UPDATE** di baris itu.

```python
@app.post('/api/topup/lanjut')
def topup_lanjut(order_id: str = Form(...), u=Depends(wajib_login), db=Depends(get_db)):
    _expire_pending(db, u)
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')
    if trx.status == 'sukses':
        return JSONResponse({'ok': False, 'status': 'sukses',
                             'pesan': 'Transaksi sudah lunas.'}, status_code=409)
    if trx.status == 'batal':
        return JSONResponse({'ok': False, 'status': 'batal',
                             'pesan': 'Transaksi sudah dibatalkan.'}, status_code=409)

    # ── BATAS PENDING (keputusan Bos #4) ─────────────────────────────
    # Dihitung SETELAH _expire_pending, jadi transaksi yang sudah mati
    # tidak ikut membebani kuota.
    jml = db.scalar(select(func.count()).select_from(Transaksi).where(
        Transaksi.user_id == u.id, Transaksi.status == 'pending'))
    if jml >= MAX_PENDING:
        return JSONResponse(
            {'ok': False, 'kode': 'PENDING_PENUH',
             'pesan': f'Anda masih punya {jml} transaksi menunggu '
                      f'(maksimal {MAX_PENDING}). Bayar atau batalkan dulu '
                      f'salah satunya, lalu coba lagi.'},
            status_code=429)

    # ── Masih pending: cek dulu apakah QR-nya benar-benar sudah mati ──
    perlu_qr_baru = (trx.status == 'expired')
    if not perlu_qr_baru:
        try:
            detail = _cek_status_sync(order_id, trx.jumlah)
            st = (detail or {}).get('status', 'pending')
        except pakasir.PakasirError:
            st = 'pending'          # ragu -> pakai QR lama, jangan bikin duplikat
        if st == 'completed':       # ternyata sudah dibayar
            trx.status = 'sukses'
            trx.dibayar = datetime.now(timezone.utc)
            _tambah_kuota(db, u, trx)
            db.commit()
            return {'ok': True, 'status': 'sukses',
                    'pesan': 'Pembayaran sudah diterima, kuota ditambahkan.'}
        if st == 'canceled':
            trx.status = 'expired'
            db.commit()
            perlu_qr_baru = True

    if perlu_qr_baru:
        # QR BARU dengan order_id YANG SAMA (keputusan Bos: 1 baris tetap 1 baris).
        # Pakasir mengizinkan create ulang untuk order_id yang sama selama
        # transaksi sebelumnya tidak 'completed'.
        try:
            hasil = pakasir.buat_transaksi_sync(order_id=trx.order_id,
                                                amount=trx.jumlah)
        except pakasir.PakasirError as e:
            return JSONResponse(
                {'ok': False, 'pesan': f'Gagal membuat QR baru: {e}'}, status_code=502)
        trx.bukti = (hasil.get('payment_number') or '')[:2000]
        trx.kedaluwarsa = _parse_expired(hasil.get('expired_at')) or \
                          (datetime.now(timezone.utc).replace(tzinfo=None)
                           + timedelta(minutes=QRIS_EXPIRE_MENIT))
        trx.status = 'pending'
        db.commit()

    p = PAKET.get(trx.paket, {})
    return {'ok': True, 'pakai_baru': perlu_qr_baru, 'order_id': trx.order_id,
            'qr': trx.bukti or '', 'paket': p.get('nama', trx.paket),
            'mb': trx.tambahan_mb, 'jumlah': trx.jumlah, 'total_bayar': trx.jumlah,
            'sisa_detik': _sisa_detik(trx), 'menit': QRIS_EXPIRE_MENIT,
            'sandbox': PAKASIR_SANDBOX}
```

Catatan: butuh `pakasir.buat_transaksi_sync` (wrapper `asyncio.run`, pola sama
dengan `_cek_status_sync`). Kalau create untuk `order_id` yang sama ditolak
Pakasir, fallback: **UPDATE order_id di baris itu** (`trx.order_id = <baru>`) —
tetap 1 baris, riwayat tetap bersih.

---

## Open Questions — SUDAH TERJAWAB

Lihat "Keputusan FINAL Bos" di atas.

## Risiko tambahan dari keputusan #4

| Risiko | Mitigasi |
|---|---|
| Pakasir menolak create ulang `order_id` yang sama | Fallback: UPDATE `trx.order_id` di baris yang sama (masih 1 baris) |
| User frustrasi karena ditolak saat pending penuh | Pesan jelas + arahkan ke riwayat agar bisa batalkan salah satu |


