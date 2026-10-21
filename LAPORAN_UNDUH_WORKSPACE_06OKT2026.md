# 🔧 LAPORAN — UNDUH PDF → WORKSPACE + 2 BUG NYATA DICABUT (06 Okt 2026)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **Image TERBARU:** `eduai-app:20261006_213049-sot` (21:30) — lihat bagian 8
> di bawah (lanjutan: cegah unduh dobel, syarat Bos).
> **Image sebelumnya:** `eduai-app:20261006_210738-sot` (21:07)
> **Titik mundur:** `eduai-app:cadangan-pra-sot`
> **Backup DB:** `_arsip/pra-sot/20261006_213049-sot`
> **Backup dokumen pra-sesi:** `_arsip/pre-dok-workspace-20261006-211324/`
> **Perintah Bos:** "Lanjutkan workspace" → (Opsi A) "Sambungkan hasil
> pencarian jurnal ke workspace" → "Deploy jalankan.sh" → (Opsi A) "Rapikan
> dokumentasi/skill/memori".
> **Hasil:** `/health` produksi **200** · **13 gerbang = 502 LULUS / 0 GAGAL**.

---

## 1. APA YANG DIMINTA BOS

Wulan **cek kode dulu** sebelum mengerjakan (aturan Bos: "cari yang sudah ada").
Temuan: **tampilan workspace/folder SUDAH ADA & LIVE** sejak 15Sep26
(`folders` + 4 rute `/folder/*` + jatah per paket + kartu folder di `/naskah`).
⇒ Wulan **bertanya** (bukan menebak); Bos pilih **Opsi A** = sambungkan hasil
pencarian jurnal ke workspace.

---

## 2. 🐞 BUG #1 — `/unduh` SELALU GAGAL (akar, dicabut)

**Gejala:** tombol unduh artikel selalu bilang *"belum bisa kami ambil"*,
walau artikelnya **terbuka** dan tautannya ada.

**Akar (terukur, bukan tebakan):**
```python
# app/pustaka.py — mesin mengembalikan kunci 'isi' (byte):
return {'ok': True, 'isi': isi, 'ukuran': len(isi), 'url': url}

# app/rute_jurnal.py — KODE LAMA memeriksa kunci 'berkas' (TIDAK PERNAH ADA):
if not hasil or not hasil.get('berkas'):     # ← SELALU True
    return {'ok': False, 'kode': 'tidak_terbuka', ...}
```
⇒ `hasil.get('berkas')` **selalu None** → **artikel terbuka pun masuk cabang
"tidak terbuka"**. Unduhan **tidak pernah berhasil** sejak fitur dibuat.

**Bukti akar:** `docker exec eduai-app python3 -c "..."` →
`pdf_terbuka` balas `{'ok','isi','ukuran','url'}` — **tidak ada** kunci `'berkas'`.

**FIX:** `if not hasil or not hasil.get('ok') or not hasil.get('isi'):`

**Bukti sembuh:** `_gerbang_pdf_nyata_workspace.py` — ambil PDF **asli dari
internet** (13.264 byte) → tersimpan ke disk + tabel `files` → **10 LULUS / 0**.

---

## 3. 🐞 BUG #2 — HALAMAN REFERENSI MATI UNTUK SEMUA AKUN (akar, dicabut)

**Gejala:** `/referensi` selalu bilang **"Belum ada naskah"** dan daftar
artikel kosong, **walau akun punya naskah**. Fitur Referensi **tidak bisa
dipakai siapa pun**.

**Akar:**
```js
// app/templates/referensi.html:207  ← BENAR (diisi server)
let NASKAH = {{ (daftar_naskah or [])|tojson }};

// app/templates/referensi.html:391  ← AKAR BUG (fungsi mulai())
NASKAH = (window.DAFTAR_NASKAH || []);   // ← variabel TIDAK PERNAH ADA
                                          //   di halaman ini ⇒ jadi []
```
`window.DAFTAR_NASKAH` hanya ada di `/naskah`, **bukan** di `/referensi`.
Baris itu **MENIMPA** daftar naskah dari server menjadi array kosong.

**FIX:** hapus penimpaan → pakai `NASKAH` dari server.
**Bukti:** render `/referensi` (CDP) → dropdown terisi
`SKRIPSI-Asih-Susanti-Putri.docx`, teks `Belum ada naskah` **HILANG**.

---

## 4. ✅ FITUR BARU — UNDUH PDF → WORKSPACE

**Prinsip Bos dipegang:** *"jangan buat baru tapi lebih optimal kan yang sudah
ada"* ⇒ **TIDAK ada tabel/kolom/dompet/halaman baru.** Titip di yang ADA.

| Berkas | Perubahan |
|---|---|
| `app/rute_jurnal.py` | `/unduh` terima `folder_id` + helper `_simpan_pdf()` + `_nama_pdf()` |
| `app/rute_jurnal.py` | Rute BARU `GET /api/ai/v1/jurnal/folder-pilihan` |
| `app/templates/referensi.html` | dropdown "Simpan PDF ke workspace" + tombol "unduh ke workspace" + `muatWorkspace()` + CSS `.baris-simpan` |

**Pola penyimpanan** = SAMA dengan `app/dokumen_baru.py:87`:
tulis berkas ke disk **DULU** → daftar di tabel `files` → `db.commit()`;
kalau commit gagal → **berkas di disk DIBUANG** (jangan tinggalkan sampah yatim).

**Pagar (backend, BUKAN UI):** folder milik user LAIN → `folder_id` jadi `None`
(lewat `folder.ambil(db, u.id, folder_id)`). Gerbang bergigi membuktikannya:
validasi dicabut → **K6a GAGAL (EXIT 1)**.

**Pemisahan tugas dijaga:** `pustaka` (mesin) tetap **murni** — tidak menyentuh
DB. Penyimpanan = tugas **pemanggil** (rute). Gerbang K7a memeriksa ini.

---

## 5. 🧪 GERBANG BARU (dijalankan DI DALAM container)

| Gerbang | Uji | Bergigi? |
|---|---|---|
| `_gerbang_unduh_workspace.py` | **20 LULUS / 0** | ✅ validasi folder dicabut → **19/1 (EXIT 1)** |
| `_gerbang_e2e_unduh_http.py` | **6 LULUS / 0** | HTTP nyata: 401 tanpa login · 404 kunci palsu · 404 pagar |
| `_gerbang_pdf_nyata_workspace.py` | **10 LULUS / 0** | PDF asli 13.264 byte dari internet |
| `_sketsa/gerbang_naskah_isi.py` | **4 LULUS / 0** | ✅ penimpaan daftar naskah dilarang |
| `_sketsa/jalankan_semua_gerbang.sh` | 13 gerbang | **502 LULUS / 0 GAGAL** |

⚠️ **Jebakan yang kena & diperbaiki:** gerbang K1c sempat **GAGAL PALSU** karena
memeriksa teks di **komentar** (komentar memang menjelaskan bug lama). FIX:
buang komentar/docstring dulu, baru periksa. Pelajaran: **gerbang harus
memeriksa KODE, bukan komentar.**

---

## 6. ⚠️ KEJADIAN DEPLOY — DITAHAN GERBANG (bukti gerbang berguna)

**Deploy PERTAMA DIBATALKAN:**
```
── ANTI-BIKIN-BARU ──
  ✗ ada alat/skrip BARU padahal padanannya SUDAH ADA:
        GAGAL  B5 tidak ada alat/skrip Wulan menetap di /tmp → ['gerbang_naskah_isi.py']
⛔ DEPLOY DIBATALKAN — Tidak ada yang diubah: image lama masih jalan, DB tidak disentuh.
```
Wulan meninggalkan `gerbang_naskah_isi.py` di `/tmp`. ⇒ dipindah ke `_sketsa/`
(tempat resmi) → verifikasi `_gerbang_anti_bikin_baru.py` **7/0 (EXIT 0)** →
deploy ulang **BERHASIL**.

**Pelajaran (fact_store #205):** aturan tertulis saja **tidak menahan** Wulan —
hanya **gerbang yang BISA GAGAL** yang menahan.

---

## 7. VERIFIKASI PRODUKSI (bukan klaim)

```
/health (https://eduai.bikinaja.id)          → 200
Image live                                    → eduai-app:20261006_210738-sot
60 file .py image == source                   → IDENTIK
Gerbang editor OnlyOffice                     → LULUS
DB                                            → 25 tabel · users=8 · files=54
Render /referensi dari DOMAIN PUBLIK (CDP):
  dropdown naskah                             → SKRIPSI-Asih-Susanti-Putri.docx ✅
  teks "Belum ada naskah"                     → HILANG ✅
  tombol "unduh ke workspace"                 → ADA ✅
  dropdown "Simpan PDF ke workspace"          → ADA ✅
  2 artikel (Kualitas Produk, Analisis Harga) → TAMPIL ✅
```

**Potret MATA (vision, diverifikasi):** baris "Simpan PDF ke workspace" +
dropdown **ADA**; 2 kartu artikel **ADA**; tombol `unduh ke workspace` di
**KEDUA** kartu **ADA**; lencana `saya cari`/`terverifikasi`/`pilihan EduAi`/
`belum terverifikasi`/`isi terbatas` **ADA**; **tidak ada** tampilan rusak.
⚠️ Catatan: percobaan vision pertama **SALAH** menyebut halaman itu "halaman
login" → sudah **diverifikasi ke sumber** (render CDP + sidik gambar), bukan
dipercaya begitu saja.

---

## 8. 🆕 LANJUTAN 21:30 — CEGAH UNDUH DOBEL (syarat Bos) · LIVE

> **Image:** `eduai-app:20261006_213049-sot` · `/health` produksi **200** ·
> **15 gerbang = 526 LULUS / 0 GAGAL**.

**Syarat Bos (verbatim):** *"kalo sudah download tidak bisa download atau
double, kecuali telah dihapus dan download lagi."*

**Cara jalan (NOL tabel/kolom baru):** penanda `berkas_id` ditulis balik ke
artikel di kolom `profil_dokumen.jurnal_json` yang **SUDAH ADA**.

| Berkas | Perubahan |
|---|---|
| `app/rute_jurnal.py` | +`_berkas_hidup`, `_sudah_diunduh`, `_tandai_terunduh` · `/unduh` **menolak** (`kode=sudah_diunduh`) · `/lihat` lapor `sudah_diunduh` per artikel |
| `app/templates/referensi.html` | tombol → **"sudah diunduh"** (mati) · muat ulang setelah unduh/tertolak |
| `_gerbang_unduh_dobel.py` | **BARU** — 12 LULUS / 0 GAGAL (periksa KODE, bukan komentar) |
| `_gerbang_unduh_dobel_e2e.py` | **BARU** — 12/0, alur LENGKAP: unduh → dobel ditolak → hapus → boleh lagi |
| `_sketsa/potret_kolaborasi_login.py` | +no-cache +`EDUAI_TINGGI` (perbaikan nyata, alat LAMA) |

**TERBUKTI:** alur lengkap 12/0 — setelah hapus, berkas baru **108 → 109**.
Gerbang **BERGIGI**: dirusak → 10/2 EXIT 1; pulih → 12/0 EXIT 0.
Produksi `eduai.bikinaja.id/referensi`: `'sudah diunduh': 1` · `'unduh ke workspace': 1`.

**⚠️ 4 JEBAKAN TERUKUR (jangan terulang):**
1. **`docker cp` WAJIB `docker restart`** — lupa sekali ⇒ `sudah_diunduh = None`.
2. **BROWSER CACHE** menyajikan halaman LAMA ⇒ potret sidik **IDENTIK 3×** walau
   kode baru jalan. Alat potret resmi kini matikan cache (`Network.setCacheDisabled`).
3. **VISION SALAH 2×** bilang "halaman login" ⇒ WAJIB buktikan ke SUMBER
   (teks layar: `'Masuk': 0` ⇒ bukan login).
4. **GERBANG GAGAL PALSU** — `_gerbang_anti_bikin_baru.py` B2 pakai **mtime** ⇒
   alat LAMA yang **diperbaiki** dituduh "baru". Jalan: pulihkan mtime ke tanggal
   lahir alat. **JANGAN melemahkan gerbang.**

**Cara memotret halaman panjang:** `EDUAI_TINGGI=2200` (tinggi tetap 1700
memotong daftar artikel).

---

## 9. 📌 SISA (jujur — BELUM dikerjakan)

1. **Belum ada workspace di akun Asih** ⇒ dropdown masih `— tanpa workspace —`.
   Uji simpan-ke-workspace **LULUS lewat gerbang**, tapi belum dipotret dari
   akun nyata.
2. **Belum uji artikel Garuda SUNGGUHAN** (baru PDF contoh dari internet).
3. **Uji PDF berbayar (paywall)** belum diputar lewat UI.
4. Berkas **"Link Jurnal.txt"** (IDE 06Okt) — masih menunggu putusan Bos.
5. Potret tanda ⚠️ "isi terbatas" belum dipotret (gerbang 32/0 sudah lulus).
