# ✅ TAHAP 1 LANGKAH 1 — KOLOM JURNAL (06 Okt 2026)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Izin Bos: *"Cek dulu, pokoknya jangan buat baru tapi lebih optimal kan yang
> sudah ada"* → lalu memilih **Opsi A** (tambah 1 kolom JSON ikut pola `peta_json`).

---

## ✅ SELESAI & TERUJI

### Yang ditambahkan (mengikuti pola `peta_json` yang sudah terbukti)
Di `app/models.py`, tabel **`profil_dokumen`**:
```python
jurnal_json:  Mapped[str] = mapped_column(Text, default='')
jurnal_sidik: Mapped[str] = mapped_column(String(64), default='')
```

**Bentuk `jurnal_json`:**
```json
{
  "BAB II": [
    {"title":"...", "authors":"...", "year":2020, "journal":"...",
     "doi":"10.29040/...", "garuda_id":1662547,
     "doi_status":"verified", "asal":"ai"}
  ],
  "_manual_terpakai": {"BAB II": 1}
}
```
⇒ Tiap artikel **bentuknya SAMA** dengan `app/pustaka.py` (tidak bikin bentuk baru).
⇒ Kunci `asal` = `"ai"` atau `"manual"` → penanda asal + dasar hitung batas 8.

**`jurnal_sidik`** = SHA-256 dari `judul|kata kunci` →
kalau judul/kk berubah, hasil lama **tidak dipakai ulang** (anti data basi).
Persis pola `peta_sidik`.

### Bukti (bukan klaim)
| Bukti | Hasil |
|---|---|
| Gerbang uji | **21 LULUS / 0 GAGAL** (EXIT 0) |
| Gerbang **BERGIGI** | disuntik kerusakan → **3 GAGAL** (terbukti bisa gagal) |
| Kolom di DB produksi | `jurnal_json` **ADA** · `jurnal_sidik` **ADA** |
| Migrasi otomatis | ✅ lewat restart container (`ALTER TABLE ... ADD COLUMN`) |
| `/health` | ✅ 200 |
| **Nol tabel baru** | ✅ sesuai perintah Bos |

**Berkas:**
- `app/models.py` — 2 kolom + 2 entri migrasi (md5 **f70425e5ea7e547b579a99c2f0d47eea**)
- `_gerbang_jurnal.py` (5.945 byte) — uji bergigi, di ROOT proyek
- Backup: `_arsip/pre-jurnal-kolom-20261006-124436/` + `MD5.txt`

### Cara migrasi bekerja (tanpa sentuh data lama)
`models.py::_migrasi_kolom()` jalan otomatis saat app start:
```python
if nama not in ada:
    ALTER TABLE profil_dokumen ADD COLUMN jurnal_json TEXT
```
⇒ **Idempoten** — jalankan berapa kali pun aman. Data lama tidak tersentuh.

---

## ⚠️ CATATAN JUJUR

1. **Log migrasi tidak muncul** di `docker logs` walau kolomnya **terbukti
   terpasang** — kemungkinan level log `migrasi` tidak tercetak. **Kolomnya ADA**
   (dibuktikan langsung ke DB), jadi tidak masalah; hanya mencatat agar tidak
   bingung nanti.
2. **Kode ini BELUM di-deploy ke image produksi** (`bash jalankan.sh`) — baru
   dipasang lewat `docker cp` + restart untuk uji. **Deploy produksi menunggu
   izin Bos** (aturan Bos: deploy = izin dulu).
3. **Belum ada isi** yang menulis/membaca kolom ini — baru **wadah**. Pengisian
   dikerjakan di langkah berikutnya.

---

## 🎯 LANGKAH BERIKUTNYA (usulan Wulan)

**Langkah 2: fungsi simpan/baca daftar artikel per bab.**
- `simpan_jurnal(prof, bab, artikel, asal)` — tulis ke `jurnal_json`
- `baca_jurnal(prof, bab)` — baca kembali
- `boleh_tambah_manual(prof, bab)` — pagar **batas 8 per bab**
- `sidik_jurnal(judul, kk)` — untuk `jurnal_sidik` (anti data basi)

⇒ Semua **fungsi kecil**, ditaruh di modul yang **sudah ada** (`pustaka.py` atau
modul baru tipis). **Belum dikerjakan** — menunggu izin Bos.

---

## 📋 STATUS
- [x] Backup dulu ✅
- [x] Cari yang sudah ada (nol tabel baru) ✅
- [x] Kolom + migrasi terpasang & terbukti ✅
- [x] Gerbang bergigi terbukti ✅
- [x] **21 LULUS / 0 GAGAL** ✅
- [ ] Belum deploy ke image produksi (menunggu izin Bos)
- [ ] Langkah 2: fungsi simpan/baca/hitung
