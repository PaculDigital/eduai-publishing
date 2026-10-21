# ✅ TAHAP 1 LANGKAH 2 — MODUL INGATAN `app/jurnal.py` (06 Okt 2026)

> Lanjutan izin Bos. Langkah 1 = kolom `jurnal_json` + `jurnal_sidik`.
> Langkah 2 = **fungsi simpan/baca/hitung**.

---

## ✅ SELESAI & TERUJI

### Berkas baru: `app/jurnal.py` (11.699 byte)
**Pemisahan tugas yang sengaja:**
| Modul | Tugas |
|---|---|
| `app/pustaka.py` | **MESIN PENCARI** (murni hitung, tidak simpan) — **TIDAK diubah** |
| `app/jurnal.py` | **INGATAN** (simpan/baca/hitung) ← baru |

⇒ Sesuai perintah Bos: **tidak bikin mesin baru, tidak ganggu yang ada.**

### Fungsi yang dibuat (semua kecil & jelas)

| Fungsi | Guna |
|---|---|
| `baca(prof)` | Baca `jurnal_json` → dict. **Tahan JSON rusak / kolom kosong** |
| `tulis(prof, data, sidik)` | Tulis ke kolom (tidak commit — pemanggil yang commit) |
| `sidik(judul, kk)` | SHA-256 → anti **pakai data basi** (pola `peta_sidik`) |
| `sidik_cocok(prof, judul, kk)` | Hasil tersimpan masih sekukuh judul+kk? |
| `kunci(a)` | Kunci unik artikel: DOI → Garuda → judul+tahun |
| `tambah(data, bab, artikel, asal)` | Tambah + **dedup otomatis** + **pagar batas 8** |
| `hapus(data, bab, kunci)` | Buang 1 artikel |
| `jumlah_manual(data, bab)` | Hitung artikel manual **per bab** |
| `boleh_tambah_manual(data, bab)` | **Pagar Bos: maks 8 per bab** |
| `sisa_slot_manual(data, bab)` | Sisa slot (untuk ditampilkan ke user) |
| `pakai_di(data, dari, ke, kunci)` | **Pakai ulang antar bab** tanpa hitung dobel |
| `sudah_dipakai_di(data, kunci)` | Info: artikel ini dipakai di bab mana saja |
| `layak_sitasi(data)` | **Hanya terverifikasi** (pagar P3 dipertahankan) |
| `tidak_layak(data)` | Yang belum terverifikasi (ditampilkan jujur) |
| `semua_artikel(data)` | Semua bab, sudah dibuang kembar |

---

## 📊 BUKTI (bukan klaim)

| Bukti | Hasil |
|---|---|
| Gerbang `_gerbang_jurnal2.py` | ✅ **59 LULUS / 0 GAGAL** (EXIT 0) |
| Gerbang **BERGIGI** | ✅ disuntik 2 kerusakan (batas 8→30, dedup hilang) → **8 GAGAL** |
| `/health` | ✅ 200 |

### Cakupan uji (10 kelompok, 59 asersi)
| Kelompok | Isi |
|---|---|
| J1 (6) | Kunci artikel: DOI / Garuda / judul+tahun, normalisasi, prioritas |
| J2 (5) | Sidik: sama→sama, kk beda→beda, judul beda→beda |
| J3 (4) | **Dedup** — artikel kembar tidak dobel |
| **J4 (10)** | **PAGAR BATAS 8** — inti putusan Bos (manual ke-9 DITOLAK) |
| J5 (5) | **Hitungan PER BAB** (BAB II penuh ≠ BAB IV kena) |
| J6 (3) | Hapus |
| J7 (6) | **Pakai ulang antar bab** tanpa hitung dobel |
| J8 (6) | **Pagar P3** — hanya terverifikasi yang layak sitasi |
| J9 (10) | Tahan data aneh: JSON rusak, list, `None`, round-trip |
| J10 (4) | **Pemisahan tugas** — jurnal.py tidak menyentuh pustaka.py/DB |

### Bukti pagar batas 8 bekerja (kutipan hasil uji)
```
LULUS  J4d artikel ke-8 masuk
LULUS  J4e setelah 8 → TIDAK boleh
LULUS  J4f artikel ke-9 DITOLAK (tetap 8)
LULUS  J4g artikel ke-9 tidak ada di daftar
LULUS  J4h 30 artikel AI → manual tetap 0
LULUS  J4i AI tidak makan slot manual
LULUS  J5e BAB II tetap 8 (per bab, bukan global)
```

---

## ⚠️ CATATAN JUJUR

1. **Belum tersambung ke rute/UI** — modul ini masih **berdiri sendiri**.
   Pemakaian dari halaman (tab Referensi) = langkah berikutnya.
2. **Belum deploy ke image produksi** — masih lewat `docker cp` untuk uji.
   Deploy (`bash jalankan.sh`) **menunggu izin Bos**.
3. **`tulis()` tidak commit** — sengaja, supaya pemanggil bisa menggabung
   beberapa perubahan dalam 1 transaksi (meniru pola `peta_json`).
4. **`pakai_di()` tidak menambah hitungan manual di bab tujuan** — ini
   **putusan Bos** ("pakai ulang tanpa hitung dobel") yang Wulan pegang, tapi
   perlu dicatat karena artinya: user bisa memakai 1 artikel manual di banyak bab
   tanpa kena batas 8. Wulan anggap ini **memang yang dikehendaki** Bos.

---

## 🎯 LANGKAH BERIKUTNYA (usulan)

**Langkah 3: sambungkan ke mesin pencarian.**
- Fungsi `cari_dan_simpan(prof, bab, judul, kk, tipe)` → panggil
  `pustaka.cari_semua()` → simpan ke `jurnal_json` via `jurnal.tambah()`.
- **Titik sambung** ke `bangun_isi()` (`kerangka.py:354`) — perbaikan kecil
  yang sudah dicatat (terima artikel kiriman).

---

## 📋 STATUS
- [x] Langkah 1: kolom + migrasi ✅ (21/0)
- [x] **Langkah 2: modul `app/jurnal.py` ✅ (59/0, bergigi terbukti)**
- [x] Backup tetap ada: `_arsip/pre-jurnal-kolom-20261006-124436/`
- [ ] Belum deploy ke image produksi (menunggu izin Bos)
- [ ] Langkah 3: sambung ke `pustaka.cari_semua()` + `bangun_isi()`
