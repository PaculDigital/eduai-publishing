# ✅ TAHAP 1 LANGKAH 4 — JATAH PENCARIAN MANUAL + TABEL JEJAK (06 Okt 2026)

> Lanjutan izin Bos. Langkah 4 = **pagar uang**: 2× gratis per 7 hari,
> lewat itu 1 Token Revisi.

---

## ✅ SELESAI & TERUJI

### 1. Tabel baru `pencarian_manual` (di `models.py`)
Meniru pola `pembatalan_kuota` (jejak per user + waktu + sebab). **9 kolom**:
`id · user_id · file_id · bab · kata_kunci · jenis · token · hasil_jumlah · dibuat`

⇒ `jenis` = `'gratis'` (pakai jatah) atau `'token'` (sudah dipotong 1 token).
⇒ `dibuat` pada baris PERTAMA = **awal pemakaian** (titik nol siklus).

### 2. Hitungan siklus (di `models.py`, dekat DB)
| Fungsi | Guna |
|---|---|
| `_sadar_naive(t)` | ⭐ **PERBAIKAN BUG** — seragamkan waktu (aware vs naive) |
| `_mulai_siklus_berjalan(db, uid)` | Awal siklus 7-hari yang sedang berjalan |
| `terpakai_gratis(db, uid)` | Berapa jatah gratis terpakai siklus ini |
| `sisa_gratis(db, uid)` | Sisa jatah gratis |
| `kapan_reset(db, uid)` | Kapan jatah kembali |
| `pesan_jatah(sisa, reset)` | Kalimat hangat |
| `ringkas_jatah(db, uid)` | Ringkasan untuk tampilan |

### 3. Modul `app/jatah.py` (pintu keputusan)
| Fungsi | Guna |
|---|---|
| `boleh_cari(db, uid)` | Boleh cari? **gratis** atau **token**? |
| `catat(...)` | Catat pencarian (TIDAK commit) |
| `pesan_tidak_cukup_saldo()` | Pesan hangat saat token kurang |
| `ringkas(db, uid)` | Ringkasan jatah |

⚠️ **Elastisitas diatur di satu tempat** (`models.py`) supaya tidak ada angka
kembar (pelajaran MAXMB 15Sep26: batas di dua tempat = salah satu tak pernah
tersentuh).

---

## 📊 BUKTI (bukan klaim)

| Gerbang | Kode benar | Kode dirusak (bergigi) |
|---|---|---|
| `_gerbang_jurnal.py` (kolom) | ✅ **21 / 0** | ✅ 3 GAGAL |
| `_gerbang_jurnal2.py` (modul) | ✅ **60 / 0** | ✅ 6 GAGAL |
| `_gerbang_jurnal3.py` (jembatan) | ✅ **53 / 0** | ✅ 8 GAGAL |
| `_gerbang_jatah.py` (jatah) | ✅ **42 / 0** | ✅ 15 GAGAL |
| `scripts/periksa_kode.sh` | ✅ **LULUS** | — |

### Bukti aturan inti (kutipan gerbang)
```
LULUS  X1a belum pernah cari → sisa 2
LULUS  X2b setelah 2 gratis → sisa 0
LULUS  X2c jenis sekarang = token
LULUS  X2d harga = 1 token
LULUS  X3a pencarian 8 hari lalu → sisa 2 LAGI (siklus baru)
LULUS  X3c2 dua-duanya dalam 7 hari pertama → sisa 0
LULUS  X4b user2 TIDAK terpengaruh (masih 2)
LULUS  X5a pencarian TOKEN tidak memakan jatah gratis
LULUS  X6b pesan (habis) tanpa kata keras
LULUS  X6c pesan habis memberi JALAN KELUAR
LULUS  X8a jatah.py TIDAK membuat tabel saldo sendiri
LULUS  X8c models.py TIDAK menambah tabel dompet baru
LULUS  X9a tabel pencarian_manual TERBUAT
LULUS  X10a catat() TIDAK commit sendiri
```

---

## 🚨 BUG NYATA YANG WULAN TEMUKAN & PERBAIKI

### Bug: `can't subtract offset-naive and offset-aware datetimes`
**Akar:** `models._now()` mengembalikan waktu **AWARE** (`timezone.utc`),
sedangkan kolom `DateTime` SQLite membaca kembali sebagai **NAIVE**. Kalau
dikurangkan → **TypeError** → seluruh hitungan siklus GAGAL.

**Perbaikan (bukan tambalan):** fungsi `_sadar_naive()` menyeragamkan
keduanya ke NAIVE di **satu tempat**, dengan alasan tertulis di kode.

⇒ Kalau tidak ketahuan, fitur jatah akan **error total** di produksi.

### Pelajaran uji (2 GAGAL PALSU berhasil dibedah)
1. **J10a/J10b** — uji ditulis waktu `jurnal.py` **belum** punya jembatan
   mesin. Sekarang memang **harus** memanggil `pustaka`. Uji diperbarui.
2. **J10d** — kata `"jurnal"` ada di `pustaka.py` sebagai **kata biasa**
   (nama jurnal akademik), bukan pemanggilan modul. Asersi diperbaiki jadi
   presisi: `'from . import jurnal' not in p`.

⇒ **ATURAN:** asersi berbasis **kata** mudah salah tangkap. Periksa **konteks**
(pemanggilan/import), bukan sekadar keberadaan kata.

### Pelajaran ke-3: asumsi uji X3c Wulan SALAH
Wulan menebak "1 lama + 1 baru → sisa 1". Ternyata **sisa 2 = BENAR**:
siklus berjalan dihitung dari pemakaian PERTAMA (8 hari lalu) → siklus
sekarang mulai 1 hari lalu → pencarian "3 hari lalu" jatuh di siklus
SEBELUMNYA. ⇒ **Cek kode dulu sebelum menuduh kode salah.**

---

## ⚠️ CATATAN JUJUR

1. **Belum tersambung ke rute/UI** — fungsi tersedia, belum ada halaman.
2. **Belum deploy ke image produksi** — masih `docker cp`. Menunggu izin Bos.
3. **Dompet token BELUM disambung** — `boleh_cari()` **hanya memberi tahu**
   (gratis/token); pemotongan token lewat `kuota.potong_banyak()` dilakukan
   di langkah berikutnya saat rute dibuat.
4. **Gerbang jurnal-2 diubah** (J10) — bukan menurunkan standar, tapi
   menyesuaikan dengan arsitektur langkah 3 yang **memang** memanggil mesin.

---

## 📋 STATUS
- [x] Langkah 1: kolom + migrasi ✅ (21/0)
- [x] Langkah 2: `app/jurnal.py` ✅ (60/0)
- [x] Langkah 3: jembatan mesin + `bangun_isi` terima kiriman ✅ (53/0)
- [x] **Langkah 4: jatah 2×/7hari + tabel jejak ✅ (42/0)**
- [ ] Langkah 5: rute + sambung dompet token + unduh PDF
- [ ] Langkah 6: UI tab Referensi
- [ ] Deploy (menunggu izin Bos)
