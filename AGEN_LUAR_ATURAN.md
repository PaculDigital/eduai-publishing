# 🚨 ATURAN WAJIB UNTUK AGEN DI LUAR REPO INI

> **BACA SELURUH BERKAS INI SEBELUM MENJALANKAN PERINTAH GIT APA PUN.**
> Repo ini berisi kode **yang berjalan di produksi**. Satu `push` salah bisa
> mematikan layanan milik banyak pengguna.

---

## 1. ATURAN PALING PENTING

### ⛔ DILARANG `push` KE BRANCH `main`

Branch `main` = **produksi**. Hanya pemilik repo (`PaculDigital`) yang boleh
menulis ke sana.

**Cara kerja yang BENAR:**

```
fork repo → clone FORK sendiri → buat branch sendiri → Pull Request
```

**Cara yang DILARANG:**

```
❌ git push origin main
❌ git push --force
❌ git push origin main --force-with-lease
❌ git reset --hard pada main
❌ git clean -fdx pada main
```

Kalau agen merasa **perlu** menyentuh `main`, itu tanda ada yang salah paham.
**Berhenti, tanya pemilik repo.**

---

## 2. LANGKAH MEMULAI (urut, jangan dilompati)

```bash
# 1. FORK repo lewat GitHub UI (tombol "Fork" kanan atas)
#    Hasil: github.com/<akun-agen>/eduai-publishing

# 2. Clone FORK SENDIRI — BUKAN repo pemilik
git clone https://github.com/<akun-agen>/eduai-publishing.git
cd eduai-publishing

# 3. Tambahkan hulu (repo pemilik) — hanya untuk MENARIK update
git remote add hulu https://github.com/PaculDigital/eduai-publishing.git
git remote -v   # pastikan: origin = fork sendiri, hulu = repo pemilik

# 4. PASTIKAN tidak bisa menulis ke hulu
git remote set-url --push hulu NO_PUSH_KE_HULU

# 5. Buat branch kerja (lihat §3)
git checkout -b agen/<nama-agen>/<tujuan-singkat>
```

**Verifikasi sebelum kerja** — WAJIB lulus semua:

```bash
bash scripts/gerbang_git.sh --periksa
```

Skrip itu akan **menolak** kalau:
- remote `origin` menunjuk ke repo pemilik (bukan fork sendiri)
- sedang di branch `main`
- ada perubahan belum ter-commit yang bisa menyentuh produksi

---

## 3. NAMA BRANCH — WAJIB BERPOLA

```
agen/<nama-agen>/<tujuan-singkat>
```

| Contoh BENAR | Contoh SALAH |
| :- | :- |
| `agen/claude/perbaiki-tata-paragraf` | `fix` |
| `agen/cursor/tambah-uji-konversi` | `patch-1` |
| `agen/gemini/audit-kuota` | `main` |
| `agen/devin/speed-up-pipeline` | `claude/branch-baru` |

**Aturan:**
- Huruf kecil, tanda hubung, **tanpa spasi**
- Nama agen = 1 kata, konsisten selama kerja di repo ini
- Satu branch = satu tujuan. Jangan campur 3 perbaikan dalam 1 branch.

---

## 4. BERKAS YANG TIDAK BOLEH DIUBAH

Berkas berikut **mengatur seluruh proyek**. Perubahan di sini bukan tugas agen:

| Berkas | Kenapa dilarang |
| :- | :- |
| `.gitignore` | Salah ubah = **rahasia bisa bocor** (`.env`, `.jwt_oo_secret`) |
| `Dockerfile` | Menentukan isi image produksi |
| `jalankan.sh` | Jalur deploy resmi + urutan gerbang |
| `SOT_*.md` | Source of Truth — hanya pemilik yang memutuskan status |
| `ATURAN_BATAS_PROYEK_03OKT2026.md` | Batas keras antar-proyek |
| `scripts/periksa_kode.sh` | Gerbang utama — melonggarkan = curang |

**Butuh mengubah salah satunya?** Ajukan **usulan di deskripsi PR**, jangan
ubah sendiri. Pemilik yang memutuskan.

---

## 5. RAHASIA — TIDAK BOLEH MASUK COMMIT

Berkas berikut **tidak ada** di repo ini dan **tidak boleh** ditambahkan:

```
.env                    Kunci API (Scopus, Router, InferHub, dll)
.jwt_oo_secret          Rahasia OnlyOffice
data/*.db               Database user
data/*token*.json       Token layanan pihak ketiga
*.pem, *.key, *.p12     Sertifikat & kunci privat
```

**Sebelum setiap commit**, jalankan:

```bash
git diff --cached --name-only | grep -iE '\.env|secret|credential|\.pem|\.key$'
```

Kalau **ada hasil** → JANGAN commit. Periksa dan keluarkan dulu.

**Kalau sudah terlanjur ter-commit:** jangan `push`. Beritahu pemilik repo
segera — kunci yang bocor harus **diganti**, bukan hanya dihapus.

---

## 6. SEBELUM MENGAJUKAN PULL REQUEST

### 6a. Jalankan gerbang — WAJIB

```bash
bash scripts/periksa_kode.sh
```

**Tempel keluaran terakhirnya di PR.** Bukan "sudah saya jalankan" — tapi
keluaran aslinya. Kalau gerbang tidak bisa jalan di mesin agen, **tulis alasannya**,
jangan diam-diam dilewati.

### 6b. Isi template PR dengan JUJUR

Template akan muncul otomatis. Empat hal wajib:

1. **Apa yang diubah** dan **kenapa**
2. **Apa yang diuji** — perintah + hasil (angka, bukan klaim)
3. **Apa yang BELUM** — batasan yang agen tahu tapi belum dikerjakan
4. **Risiko** — apa yang bisa rusak kalau ini salah

**DILARANG** menulis "sudah dites, aman" tanpa keluaran. Kalau belum diuji,
tulis **"belum diuji"**. Itu lebih berguna daripada klaim kosong.

---

## 7. ATURAN ISI KODE PROYEK INI

Agen yang bekerja di sini **wajib** mengikuti aturan induk proyek:

### 7a. Jev hanya membaca BENTUK/STRUKTUR/KEBERADAAN
Jev **bukan** penilai mutu tulisan. Jangan minta Jev menilai "bagus/tidak",
menghitung, atau membandingkan antar-pertanyaan — tiga hal itu **terbukti gagal**.

### 7b. Satu pintu AI
Semua panggilan model **lewat 9router** (`172.17.0.1:20128`). **Dilarang**
memanggil provider AI langsung — itu jalur kedua yang memecah biaya & pagar.

### 7c. Jangan menambal, cari akar
Kalau ada gejala, cari **penulis nilai yang salah**, bukan menambah pengecekan
di hilir. Tambalan menutupi gejala dan menambah hutang.

### 7d. Gerbang hijau ≠ produksi sehat
Gerbang yang jalan di **host** tidak membuktikan isi **image Docker**.
Bukti produksi hanya `docker exec` / `docker run`.

### 7e. Teks untuk user menyebut "EduAi"
Jangan menyebut "AI", "Wulan", nama agen, atau nama model di teks yang dilihat
pengguna. Satu identitas produk: **EduAi**.

---

## 8. REPO INI TIDAK TERHUBUNG KE PRODUKSI

Penting dipahami: **merge PR ≠ deploy**.

```
Pull Request → merge ke main  →  (BERHENTI DI SINI)
                                   ↓
                          deploy = keputusan pemilik
                          (bash jalankan.sh di VPS)
```

Agen **tidak boleh** menganggap merge = sudah live. Wulan/pemilik yang
menjalankan deploy setelah menilai.

---

## 9. KALAU RAGU

**Berhenti dan tanya.** Tiga hal yang **selalu** layak ditanyakan:

1. "Apakah saya perlu menyentuh `main`?" → **Tidak, jangan pernah.**
2. "Apakah berkas ini termasuk yang dilarang diubah?" → Cek §4.
3. "Apakah perubahan ini menyentuh produksi?" → PR dulu, deploy nanti.

Menanyakan lebih baik daripada menebak — naskah dan data pengguna nyata
ada di balik kode ini.

---

## 10. RINGKASAN SATU LAYAR

```
✅ Fork → clone fork sendiri → branch agen/<nama>/<tujuan> → PR
❌ Jangan push ke main, jangan --force, jangan ubah .gitignore/Dockerfile/jalankan.sh
✅ Jalankan scripts/periksa_kode.sh, tempel hasilnya di PR
❌ Jangan commit .env / secret / DB
✅ Isi PR: apa, kenapa, diuji apa, BELUM apa
✅ Ragu → tanya pemilik repo
```
