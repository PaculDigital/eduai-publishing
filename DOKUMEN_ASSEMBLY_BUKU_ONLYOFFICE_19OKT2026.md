# 📖 ASSEMBLY BUKU → SATU .docx → ONLYOFFICE — 19 OKT 2026

<!-- 📌 SOT: Assembly buku (1 buku = 1 .docx). Status HITUNG dari kode:
     `_gerbang_assembly_buku.py` (30/0) + `_uji_sambung_assembly.py`.
     Sumber resmi tetap SOT.md -->

> **ACC Bos 19 Okt 2026 — pilihan B:** assembly DOCX disambung dulu, sebelum
> percepatan paralel. Alasan Bos: user harus bisa **edit sendiri** dan
> **simpan seperti dokumen biasa**, tanpa Jev/Hakim yang memang bukan alatnya.

**STATUS: ✅ LIVE — image `eduai-app:20261019_082734-sot` (deploy 19 Okt 2026, izin Bos)**

| Gerbang | Hasil | Bergigi |
|---|---|---|
| `_gerbang_porsi_alat.py` | 138 / 0 | 3/3 |
| `_uji_id_buku_ke_alat.py` | 55 / 0 | 3/3 |
| `_gerbang_assembly_buku.py` | 30 / 0 | 3/3 |
| `_uji_daftar_berkas_buku.py` | **28 / 0** | 3/3 |
| `_gerbang_salinan_mesin.py` | 25 / 0 | 1/1 |
| `scripts/periksa_kode.sh` | **LULUS** | — |

### Bukti DI PRODUKSI (bukan host)

```
PORSI ALAT buku_umum  → {'jev': False, 'hakim': False, 'mutu_buku': True}
PORSI ALAT skripsi    → {'jev': True,  'hakim': True,  'mutu_buku': False}
PORSI ALAT ngawur     → semua False
python-docx di image  → OK · rakit()/siapkan() ada
Rakit "Awan dan Hujan" → AWAN_DAN_HUJAN_FINAL.docx 38.696 byte
  judul baru  : ADA
  bocor EKONOMI DIGITAL : TIDAK
  bocor Syahrul Alim    : TIDAK
Daftar ke files → FILE_ID=1 · nama "Awan dan Hujan.docx" · bisa_dibuka=True
DB produksi setelah uji: files=23 · users=6 (TIDAK bertambah)
```

Titik mundur: `eduai-app:cadangan-pra-sot` · backup DB `_arsip/pra-sot/20261019_082734-sot`

---

## 1. INI PEMASANGAN, BUKAN MESIN BARU

Mesin `buku_umum_assembly.py` (701 baris) **SUDAH ADA** sejak awal dan sudah
lengkap: cover, ISBN, kata pengantar, daftar isi, bab, glosarium, indeks,
daftar pustaka, bio, B5, footer nomor halaman. **Nol fungsi assembly baru.**

Yang ditambal = **3 hal yang membuat mesin itu tidak bisa dipakai buku lain:**

| # | Akar masalah (terukur) | Akibat | Obat |
|---|---|---|---|
| 1 | `OUT_DIR`/`DOCX_OUT`/`BUKU` **hardcode** buku Ekonomi Digital | Buku user lain dirakit dengan nama berkas & identitas buku orang lain | `siapkan()` + `rakit()` setel global per buku, pulihkan di `finally` |
| 2 | `add_kata_pengantar()` **menulis mati** cerita ekonomi digital | Buku "Petualangan di Laut" keluar pengantar ekonomi digital | Pengantar mengikuti `judul` |
| 3 | `add_bio()` **menulis mati** biografi "Syahrul Alim" | Buku user lain keluar biografi orang lain | Bio mengikuti `BUKU['penulis']`/`institusi`; kalau kosong → **tidak mengarang nama** |

Kebocoran #2 dan #3 **ditemukan gerbang**, bukan dari membaca kode.

---

## 2. TEMUAN PALING BERBAHAYA: `python-docx` TIDAK ADA DI IMAGE

`buku_umum_assembly.py` mengimpor `docx`, sedangkan **EduAi selalu memakai
WeasyPrint (PDF)** — jadi `python-docx` **belum pernah** masuk `requirements.txt`.

Konsekuensi kalau tidak ketahuan: di host assembly jalan, di dalam container
**"No module named 'docx'"** ⇒ user hanya dapat berkas bab terpisah dan
mengira fiturnya rusak. Sudah ditambahkan `python-docx==1.2.0` (versi sama
dengan host yang terbukti).

---

## 3. YANG DIPASANG

| Berkas | Perubahan |
|---|---|
| `buku_umum_assembly.py` (host `/opt/data`) | `siapkan()` · `rakit()` · kata pengantar dinamis · bio dinamis · `_ASLI` dipulihkan di `finally` |
| `app/penyusunan_buku.py` | setelah bab jadi → panggil `rakit()`; gagal rakit **tidak** membatalkan buku (`docx=None` + alasan) |
| `app/main.py` | `/buku/susun` meneruskan `docx` & `docx_alasan`; `/buku/selesai` **memeriksa berkasnya ADA** sebelum ditampilkan |
| `app/templates/buku_selesai.html` | kartu "Dokumen buku" (nama, ukuran, catatan) + tombol **Edit dokumen** |
| `Dockerfile` | `COPY buku_umum_assembly.py` + `COPY indeks_referensi.py` |
| `requirements.txt` | `python-docx==1.2.0` |

### Kenapa gagal rakit TIDAK menggagalkan buku
Bab sudah ditulis dan **sudah dipotong tokennya**. Kalau rakit gagal lalu
seluruh proses dianggap gagal, user kehilangan token padahal babnya jadi.
Karena itu: bab tetap disimpan, dokumen bisa dirakit ulang, dan alasannya
ditampilkan apa adanya.

### Kenapa halaman hasil memeriksa berkas
Parameter URL bisa diubah siapa saja (`?docx=/etc/passwd`). Halaman **wajib**
memeriksa `os.path.exists` dan hanya menampilkan `basename` — bukan path penuh.

---

## 4. GERBANG

```bash
cd /opt/data
.venv/bin/python _gerbang_assembly_buku.py        # 30/0

cd /opt/data/services/eduai-publishing
PYTHONPATH=$PWD EDUAI_APP_DIR=$PWD /opt/data/.venv/bin/python _uji_sambung_assembly.py
```

**TERBUKTI BERGIGI (3 suntikan, semua tertangkap):**

| Suntikan | Hasil |
|---|---|
| judul di-hardcode lagi jadi "EKONOMI DIGITAL" | ❌ 2 GAGAL |
| pemulihan global (`pulih()`) dihapus | ❌ 4 GAGAL |
| bab hilang dilewati diam-diam | ❌ 1 GAGAL |

Yang diuji gerbang assembly: judul baru masuk · judul lama **tidak** bocor ·
nama berkas dari judul · bab hilang **dilaporkan** · daftar isi hanya bab yang
ada · global pulih (termasuk setelah galat) · B5 + Times New Roman + footer
nomor halaman · daftar pustaka ikut · **zip docx utuh & `word/document.xml` ada**
(syarat OnlyOffice) · folder tanpa bab / outline kosong → galat jelas.

---

## 5. JEBAKAN YANG SUDAH MENGGIGIT

| # | Jebakan | Akibat terukur | Obat |
|---|---|---|---|
| 1 | `_ASLI` diletakkan sebelum `BUKU` didefinisikan | `NameError: BUKU` saat import | Isi `_ASLI` **setelah** `BUKU` |
| 2 | Kata pengantar & bio **ditulis mati** | Buku lain keluar identitas buku contoh | Ikut `judul`/`penulis`; kosong → jangan karang nama |
| 3 | `python-docx` tidak ada di image | Rakit gagal di produksi walau host jalan | Tambah ke `requirements.txt` |
| 4 | Assembly tidak ikut `COPY` di Dockerfile | Sama: rute jalan, rakit gagal | `COPY` kedua berkas |

---

## 6. PENDAFTARAN KE TABEL `files` — KABEL TERAKHIR (SUDAH DIPASANG)

Tanpa langkah ini: dokumen ADA di disk tetapi `/edit/{fid}` **tidak bisa**
membukanya, karena rute itu mencari baris `FileBerkas`.

| Yang dipasang | Berkas |
|---|---|
| `_daftarkan_berkas()` — salin ke `UPLOAD_DIR/<user_id>/` + baris `FileBerkas` | `app/penyusunan_buku.py` |
| `susun()` memanggilnya setelah rakit + lapor `file_alasan` kalau gagal | `app/penyusunan_buku.py` |
| `/buku/selesai` meneruskan `fid` dan **memeriksa pemilik + bukan sampah** | `app/main.py` |
| Tombol **Edit dokumen** → `/edit/{fid}` | `buku_selesai.html` |

Pola SAMA dengan `app/dokumen_baru.py:87` — **nol mesin baru**.

**3 penjaga yang dipasang:**
1. `?fid=` hanya dipakai kalau baris `files` **milik user login** dan **tidak di
   sampah**. Tanpa ini, `?fid=1` membuka dokumen orang lain.
2. Pendaftaran gagal → berkas yang sudah disalin **dihapus** (tidak ada berkas
   yatim di folder upload).
3. Panjang nama dijaga di kode (`<=255`), tidak bergantung pada DB.

---

## 7. JEBAKAN (lanjutan)

| # | Jebakan | Akibat terukur | Obat |
|---|---|---|---|
| 5 | `peta3_jev.py` dimasukkan ke daftar "salinan mesin" | Gagal palsu — berkas itu **milik proyek**, bukan salinan | Dikeluarkan dari daftar, dengan alasan tertulis |
| 6 | Uji yatim memakai judul 400 karakter | Kode **memotong** jadi 120 ⇒ uji tidak pernah bisa gagal (PALSU) | Uji diganti: `user_id` tak ada → FK gagal |
| 7 | SQLite **tidak menegakkan** panjang kolom | Nama 400 karakter masuk tanpa galat (MySQL akan menolak) | Panjang nama dijaga **di kode** |
| 8 | Uji hanya cek "fungsi ada", bukan "dipanggil" | Mematikan pendaftaran **tidak tertangkap** | Uji perilaku: `hasil['file_id'] = _daftarkan_berkas(` setelah komentar/docstring dibuang |
| 9 | Berkas uji tertinggal di `/tmp` | Gerbang `ANTI-BIKIN-BARU` **menolak deploy** | Bersihkan `/tmp` sebelum `periksa_kode.sh` |

---

## 8. BELUM (jujur)

- ✅ **SUDAH DEPLOY** 19 Okt 2026 — `eduai-app:20261019_082734-sot`, `/health` 200,
  gerbang editor LULUS.
- **Belum uji buku 6 bab sungguhan** (butuh token & ±36 menit). Yang diuji:
  rakit 1 bab + daftar `files` DI DALAM container produksi.
- **Belum menekan `/edit/{fid}` lewat BROWSER ber-login** ke OnlyOffice hidup.
  Yang diuji: semua syarat rute terpenuhi di produksi (baris `files`, pemilik,
  tidak sampah, berkas ada, `bisa_dibuka=True`) + gerbang editor LULUS.
- `render_html_to_png()` untuk diagram **masih stub**.
- **Percepatan paralel + orkestrator belum disentuh sama sekali.**

---

## 9. LANGKAH BERIKUTNYA

1. **Deploy** (`bash jalankan.sh` setelah `periksa_kode.sh` LULUS) — izin Bos.
2. Setelah deploy: susun 1 buku 3 bab sungguhan → ukur waktu, buka `/edit/{fid}`,
   simpan, pastikan tidak hilang.
3. Percepatan paralel + orkestrator + pemeriksa mutu (rencana terpisah).
