# Kwitansi — Review Rancangan & Branch BAB IV (21 Okt 2026)

Sesi nyata: Bos menyerahkan **Dokumentasi Induk BAB IV** lalu memerintahkan
Wulan menjadi penjaga `main`, lalu meminta cek "Fase I" di repo Statistik Lab.

Repo: `PaculDigital/eduai-publishing` (publik) ·
`PaculDigital/statistik-lab` (**private**)

---

## 1. Peran yang diberikan Bos (verbatim)

> *"Semua kendali main adalah kamu, agen lain hanya buat koding di branch nya
> sendiri dan Kamu cek saja dan cari bug, sebelum bisa diintegrasikan ke main."*

> *"Yang jelas kamu tahu rencana dan maksudnya. Paham. Jangan koding dulu"*

⇒ Ini **menetapkan kelas kerja baru**: Wulan = gerbang integrasi, bukan
pelaksana fitur.

---

## 2. Review dokumen rancangan — 4 dokumen + 1 commit tanggapan

Berkas yang dibaca utuh:

| Berkas | Isi |
|---|---|
| `DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md` (583 baris) | konsolidasi final keputusan |
| `AUDIT_WULAN_BAB4_21OKT2026.md` (147 baris) | audit awal + pagar repo |
| `RANCANGAN_JEMBATAN_BAB4_21OKT2026.md` (159 baris) | kontrak API jembatan |
| `RANGKUMAN_DISKUSI_BAB4_21OKT2026.md` (233 baris) | riwayat keputusan A/B/C |
| `CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md` (315 baris) | putusan lama 08 Okt |

### Klaim [FAKTA] yang DIVERIFIKASI — semua BENAR

| Klaim dokumen | Bukti nyata | Status |
|---|---|---|
| Harga `4`=30, `4:olah_data`=30 | `app/config.py:251,253` | ✅ |
| Kerangka 4.1–4.5 kuantitatif | `app/kerangka_bab.py:125-158` | ✅ |
| Dua layanan BAB IV tampil | `app/kerangka.py:207-212` | ✅ |
| Jembatan ke Statistik Lab BELUM ADA | grep `statistik` di `app/*.py` = teks saja | ✅ |
| Endpoint mesin (§3.2) | `/api/diagnosis/unggah|periksa-peran|periksa`, `/api/buat-data[/jalur]`, `/api/kualitatif/saran|ekspor-qdpx|ekspor-qdc` | ✅ |
| Mesin kualitatif masih di browser | server hanya punya `saran` + ekspor | ✅ |
| Pola `VersiDokumen` sudah ada | `app/models.py:234` | ✅ |
| `cek_dan_potong` + `saldo_token` | `app/kuota.py:472` & `:641` | ✅ |
| `_alpha` hanya dipakai jalur PLS | `app/diagnosis.py:703`, dipakai `:466` | ✅ |

---

## 3. Lima celah yang Wulan temukan (sebelum ada dokumen tanggapan)

| # | Celah | Kelas |
|---|---|---|
| 1 | Commit `f259895` berjudul *"Catat push branch selesai (PAT Bos sesaat)"* → agen lain bisa menyimpulkan "boleh minta PAT" | **preseden berbahaya** |
| 2 | Paket 30 token termasuk 3× generate gratis → berpotensi bocor biaya | **bocor biaya** |
| 3 | "Kunci Hasil" disebut sebagai tombol, tapi tak ada tabel/kolom penampung | **klaim UI tanpa DB** |
| 4 | Pra-survei "alat yang sama" tapi `periksa_spss` selalu keluarkan hasil LENGKAP (tak ada mode berhenti awal) | **"alat sama" butuh perubahan** |
| 5 | Campuran: putaran 2 dibangun dari hasil putaran 1 → tak bisa ditagih 60 di depan | **urutan bayar mustahil** |

### Commit `41c2e92` menanggapi kelimanya (+45 baris, dokumen saja)

| Celah | Jawaban di dokumen | Nilai |
|---|---|---|
| 1 | §14.9 baru: *"PAT BUKAN PROSEDUR… pengecualian satu kali… agen DILARANG minta/simpan PAT"* | ✅ tegas |
| 2 | §10.1: potong **SEKALI di depan**, "implementer DILARANG ubah jadi potongan tersembunyi" | ✅ benar |
| 3 | §10.3: butuh tabel DB; **ikuti pola `VersiDokumen`, jangan bikin pola versioning kedua** | ✅ tepat |
| 4 | §8.2: "alat sama" = satu rumus, BUKAN nol perubahan; masuk paket jembatan §11.2 | ✅ jujur |
| 5 | §10.2 status **USULAN**: bayar per putaran | ⚠️ belum diputuskan — **ditandai benar** |

📌 **Pelajaran:** agen yang **menandai [USULAN] dengan jujur** untuk hal yang
belum diputuskan = tanda kualitas. Jangan menuntutnya jadi keputusan.

---

## 4. Kasus "cek Fase I" — tiga sumber, tiga jawaban berbeda

Bos: *"Saya sudah kerjakan fase I di repo, yaitu di Statistik lap nya. Kamu cek
ke dia repo tersebut apakah sudah ada fase 1"*

| Sumber | Hasil terukur | Arti |
|---|---|---|
| **Remote** `api.github.com/repos/PaculDigital/statistik-lab` | **404** | private |
| **Daftar repo publik** owner | hanya 4: bayana-web, BMAD-METHOD, eduai-publishing, OmniRoute — **statistik-lab TIDAK ada** | private (bukan hilang) |
| **Lokal** `/opt/data/services/statistik-lab` @ `090be17` | grep `api/jembatan` = **KOSONG**; tak ada pintu hitung tanpa sesi | Fase I tidak ada |
| **LIVE** `statistik.bikinaja.id` | `/api/status` → `{"versi":"fase1"}` · `POST /api/jembatan/hitung` → **404** · `POST /api/jembatan/kuantitatif` → **404** | Fase I tidak ada |

⚠️ **Jebakan label:** `versi: "fase1"` di `/api/status` adalah label **web
Fase 1 (17 Sep)** — sama sekali bukan fase jembatan BAB IV.

### Kredensial

`GITHUB_TOKEN` di `/opt/data/services/penelitian-bot/.env` →
`api.github.com/user` balas **"Bad credentials" (401)** = **MATI**.
Tidak ada token GitHub lain di semua `.env`.
⇒ Wulan **berhenti & lapor**, tidak mencoba 5 cara lain.

---

## 5. Yang dikerjakan di sisi repo EduAi

```bash
git fetch --all --prune
# → f259895..41c2e92  agen/wulan/bab4-statistik-backend
git log --oneline f259895..origin/agen/wulan/bab4-statistik-backend
# → 41c2e92  Tanggapi 5 temuan review agen …
git diff --stat f259895 origin/agen/wulan/bab4-statistik-backend
# → DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md | 45 +++++++++++++++++++++
#    1 file changed, 45 insertions(+)          ← DOKUMEN saja, nol kode

git checkout -b agen/wulan/analisa-kolaborasi-bab4 \
  origin/agen/wulan/bab4-statistik-backend
bash scripts/gerbang_git.sh --periksa
# → LULUS — mode PEMILIK · branch berpola · berkas terlarang utuh
```

`origin/main` **tetap** di `c57f5cd` ⇒ **belum ada integrasi**. Jangan laporkan
"sudah masuk main".

---

## 6. Berkas terlarang yang diperiksa ada & utuh

`.gitignore` · `Dockerfile` · `jalankan.sh` · `scripts/periksa_kode.sh` ·
`ATURAN_BATAS_PROYEK_03OKT2026.md` · `SOT_*.md` (5 berkas)

Semua **ADA** dan **tidak tersentuh** oleh branch agen.

---

## 7. REVIEW KODE — Fase 1 jembatan di `statistik-lab`

Bos: *"Saya sudah kerjakan fase I di repo, yaitu di Statistik lap nya"* →
lalu *"sudah saya buat publik"*.

⚠️ **Repo ini sebelumnya PRIVATE**: `GITHUB_TOKEN` di
`/opt/data/services/penelitian-bot/.env` → **"Bad credentials" (401) = MATI**.
Obat satu-satunya: **Bos menjadikan repo publik**, lalu `git clone` biasa
berhasil tanpa kredensial apa pun. Jangan habiskan waktu mencari token.

### Branch yang ditemukan

```
origin/agen/wulan/jembatan-bab4   9548ea7  Fase 1 jembatan BAB IV: pintu hitung
                                            tanpa sesi + mode pra-survei +
                                            kunci antar-layanan (Opsi B)
origin/master                     090be17  (4 commit di DEPAN induk branch)
```

### Yang DIMINTA dokumen §11.2 vs yang ADA

| Butir §11.2 | Status | Bukti |
|---|---|---|
| Pintu hitung kuantitatif tanpa sesi | ✅ ADA | `app/jembatan.py` (194 baris), `POST /api/jembatan/hitung` |
| Mode pra-survei (berhenti awal) | ✅ ADA | `periksa_pra_survei()`, pakai `_alpha` yang sudah ada — rumus tidak diduplikasi |
| Kunci antar-layanan | ✅ ADA | header `X-Kunci-Layanan` vs env `JEMBATAN_KUNCI_LAYANAN`, `compare_digest`, 503 kalau belum dipasang |
| Bungkus fungsi murni `periksa_spss`/`periksa_pls` | ✅ ADA | lewat `gabung_peran` + `hias_hasil` (satu sumber, disuntik dari `main.py`) |
| Tanpa simpan (Opsi B) | ✅ ADA | tak panggil `simpan_sementara`, tak tulis berkas, sesi 0→0 |
| **Dua pintu KUALITATIF** (koding + triangulasi/SWOT) | ❌ **BELUM** | grep `kualitatif` di `app/jembatan.py` = kosong |
| Terpasang di produksi | ❌ **BELUM** | live `POST /api/jembatan/hitung` → 404 |

### Uji milik branch: **21/21 LULUS, EXIT 0**

`uji_jembatan.py` (143 baris): SPSS lama-vs-baru (`r2`, `r2_adj`, `vif_maks`,
`dw`, semua `b`/`p`, `masalah[]`), PLS (CR/alpha per konstruk), kunci
(401 tanpa header · 401 salah · 503 env kosong · status 200), pra-survei
(kelompok otomatis, butir sampah `Kualitas_3` tidak lolos, alpha keluar).

Cara jalan: `uv venv .venv && uv pip install --python .venv/bin/python -q
fastapi httpx numpy pandas scipy python-multipart jinja2` lalu
`.venv/bin/python uji_jembatan.py` **dari dalam direktori repo**.

### 🐛 4 BUG temuan Wulan (dari 28 probe tandingan: 24 lulus, 4 gagal)

| # | Bug | Bukti terukur | Tingkat |
|---|---|---|---|
| 1 | **Branch ketinggalan 4 commit `master`** — bercabang dari `9ca0364`, master di `090be17`. Di diff `master..branch`, SEO + brand **tampak TERHAPUS** (`favicon.svg` −12, `uji_seo.py` −141, rute sitemap/robots). Merge apa adanya = **menghapus fitur produksi** | `git merge-base` = `9ca0364`; `git log 9ca0364..master` = 4 commit | 🔴 KRITIS |
| 2 | **Kunci non-ASCII → HTTP 500** | header `X-Kunci-Layanan: kunci-ê` → `UnicodeEncodeError: 'ascii' codec ... ordinal not in range(128)`. `secrets.compare_digest(str, str)` butuh **bytes** | 🔴 |
| 3 | **Kolom jadi X dan Y sekaligus → 200** | `peran['A_1']='Y1'` sementara `A_1` sudah `X1` → diterima, mesin menghitung data tak sah | 🟠 |
| 4 | **Kolom tanpa akhiran angka** (`Kualitas`, `Harga`, `Minat`) → salah kelompok / 400 | `_kelompok_dari_awalan` regex `^(.*?)[_\s]?\d+$`; nama tanpa digit jatuh 1 butir ⇒ "cuma punya 1 butir" | 🟠 |

### ✅ Yang diuji dan TERBUKTI AMAN (jangan dilaporkan sebagai bug)

Sel kosong (`None`) diterima · NaN literal JSON tidak 500 · kolom bernama angka
aman · payload list / `baris` dict / `baris` kosong → 400/422 rapi · PLS tanpa
konstruk → 422 · tahap typo `pra_survey` → **ditangani, tidak** diam-diam jadi
jalur utama · butir konstan (div/0) tidak 500 · butir terbalik tidak lolos +
alpha **−2,8415** dilaporkan apa adanya · data teks → 400 · 1 baris → 400 ·
5000 baris → 200 dalam **0,23 dtk** · deterministik (dua panggilan identik →
hasil sama) · `.env` **tidak** ter-commit · kunci uji tidak tertulis di dokumen.

### ⚠️ Catatan: 2 uji yang tidak bergigi

1. `uji_jembatan.py` menyetel `os.environ['JEMBATAN_KUNCI_LAYANAN']='kunci-uji-rahasia'`
   di dalam proses uji → uji autentikasi **tidak pernah bisa gagal** kalau kode
   memasang kunci keras.
2. Uji membandingkan 4 kunci pilihan (`r2`, `r2_adj`, `vif_maks`, `dw`) + `koef`
   + `masalah`, bukan seluruh respons.

### Putusan Wulan

**JANGAN merge sekarang.** Urutan: (1) rebase ke `master` — wajib; (2) perbaiki
BUG 2–4; (3) pintu kualitatif = fase berikutnya (dokumen §16 memang bertahap,
jadi belum dibangun **bukan** cacat); (4) cek ulang, baru merge.

### Catatan teknis lain

- Respons pra-survei hanya `{tahap, n, variabel, semua_lolos}` — **tidak ada
  kalimat kesimpulan bahasa manusia**. Dokumen §8.2 bilang AI EduAi yang
  menerjemahkan, jadi ini **sesuai rancangan**, bukan bug — tapi wajib dipastikan
  lapis penerjemahnya benar-benar dibangun di EduAi.
- `app/jembatan.py` sudah terpasang: `main.py:992-993`
  `app.include_router(_buat_router_jembatan(_gabung_peran, _hias_hasil))`.

---

## 8. PUTARAN 2 & 3 — bug diperbaiki, dan satu "perbaikan" yang ternyata buta

Bos: *"Bug sudah di betulkan, cek lagi"* → lalu *"Sudah diperbaiki cek lagi"*.

### Putaran 2 — commit `b8e7f46` + merge `8c1e9cc`

| Bug | Status | Bukti terukur |
|---|---|---|
| 1 master ketinggalan | ✅ **TUNTAS** | `8c1e9cc` merge `origin/master`; `grep -c "favicon\|sitemap\|robots" app/main.py` = **13** |
| 2 kunci non-ASCII | ✅ **TUNTAS** | header raw bytes `kunci-\xea` → **401** (dulu 500); `secrets.compare_digest` dengan **bytes** |
| 4 kolom tanpa nomor | ✅ **TUNTAS** | `Kualitas, Harga, Minat` → **400** + pesan pola butir |
| 3 peran tumpang tindih | ❌ **BELUM** | lihat di bawah |
| uji bawaan | 26/26 LULUS | 5 asersi regresi baru |

⚠️ **BUG 3 versi "perbaikan" ternyata BUTA, dan ujinya hijau.** Pagar
`_cek_tumpang_tindih` membaca **`kolom_x`/`kolom_y`**, sedangkan bentuk yang
dipakai uji dan akan dipakai EduAi adalah **`peran: {kolom: peran}`**:

| Bentuk kiriman | Pagar | Hasil |
|---|---|---|
| `kolom_x`/`kolom_y` | dibaca | ✅ 400 |
| `peran` dict (**bentuk nyata**) | **tidak dibaca** | 🚨 **200 LOLOS** |

Komentar kodenya sendiri: *"Peran (dict kolom→peran) secara bentuk tidak bisa
tumpang tindih"* — **salah**: nilai dict bisa membuat satu kolom berdiri di dua
sisi sesudah `gabung_peran`.

**Uji bergigi Wulan — mutasi pertama TIDAK SAH:**
```python
J._cek_tumpang_tindih = lambda p: None    # ❌ TypeError: unexpected keyword 'efektif'
```
Pagar dipanggil dengan 2 bentuk panggilan → lambda menolak argumen baru →
galat → hasil tampak "pagar tidak menangkap". **Kalau dipercaya, Wulan akan
melaporkan pagar sehat sebagai hiasan.** Obat: `lambda p, efektif=False: None`.

### Putaran 3 — commit `848c0d0`: TUNTAS & BERGIGI

Pagar sekarang memeriksa **payload EFEKTIF** (hasil `gabung_peran`), bukan
payload mentah. Kasus terukur:

| Kasus | Dulu | Sekarang |
|---|---|---|
| `peran`: butir satu variabel terbelah X/Y (`A_1`=Y1, `A_2`,`A_3`=X1) | 🚨 200 | ✅ **400** |
| `kolom_x`/`kolom_y` tumpang tindih | 400 | ✅ 400 |
| Butir di dua konstruk (PLS) | 400 | ✅ 400 |
| Campur `peran` + kolom eksplisit (ambigu) | — | ✅ **400** (baru) |

**Uji 3-keadaan (bukti bergigi, bukan hijau palsu):**

| Keadaan | `peran` terbelah | Arti |
|---|---|---|
| pagar asli | **400** | menolak |
| pagar dimatikan total | **200** | uji memang mengukur pagar |
| pagar **buta untuk `peran`** (persis bug versi 1) | **200** | uji menangkap bolongnya |
| dipulihkan | **400** | pulih bersih |

### Putusan akhir

**Fase 1 LAYAK merge.** 4 bug tuntas, pagar bergigi, tanpa regresi (26/26 + 14/14
probe Wulan). Dua hal tersisa **bukan bug kode**:
1. `JEMBATAN_KUNCI_LAYANAN` belum dipasang di produksi → pintu masih **503** (aman tertutup) — keputusan Bos.
2. Pintu kualitatif (§11.2) belum ada → **fase berikutnya**, dokumen §16 memang bertahap ⇒ **bukan cacat**.

📌 **Pola kelas yang disimpan ke SKILL.md:** bug ini masuk kelas
*"pagar membaca bentuk data yang salah"* (§4e) — hanya tertangkap kalau uji
dijalankan untuk **setiap bentuk kiriman**, bukan satu bentuk saja.

---

## 9. MERGE FASE 1 → `master` (selesai 21 Okt 2026)

Bos: *"Catat dan merge, nanti lanjut fase berikutnya"*.

```bash
git checkout -B master-merge origin/master
git merge --no-ff agen/wulan/review-lulus-jembatan
git push origin agen/wulan/review-lulus-jembatan
git push origin HEAD:master
```

Bukti (bukan klaim — diverifikasi dari **clone baru** `--depth 1`):

| Cek | Hasil |
|---|---|
| `master` di GitHub | `629c4ab` (merge commit) |
| `app/jembatan.py` | 15.174 byte, ada |
| Router terdaftar | `main.py:1057-1058` |
| SEO setelah merge | 13 kemunculan `favicon\|sitemap\|robots` |
| `uji_jembatan.py` dijalankan ULANG pasca-merge | 26/26 LULUS |

📌 **Uji ulang SESUDAH merge, bukan hanya sebelum.** Merge commit bisa
memunculkan konflik logis yang uji pra-merge tidak lihat.

📌 **Kredensial push**: repo EduAi punya
`credential.helper = store --file=/opt/data/vault/.git-credentials-eduai`
(akun `x-access-token`). Cara pakai untuk repo lain di owner yang sama:
```bash
git config credential.helper "store --file=/opt/data/vault/.git-credentials-eduai"
```
Jangan cetak isi berkasnya.

---

## 10. FASE 2 — SALAH REPO (kesalahan Wulan, dan obatnya)

Bos: *"Fase 2 sudah commit, kamu cek"*.

**Yang Wulan lakukan salah:** `git ls-remote` di `statistik-lab` → tidak ada
commit baru → melapor **"Fase 2 belum sampai ke GitHub"** + menebak 4
kemungkinan penyebab. **Salah semua.**

**Kenyataan:** `f561b5c` ada di `eduai-publishing`, branch
`agen/wulan/bab4-statistik-backend`. Bos membetulkan dengan memberi peta branch.

⇒ **Aturan yang lahir dari sini (§1b SKILL.md):** sebelum melapor "tidak ada",
`git ls-remote origin` di **SEMUA** repo project. Ketidakadaan hanya sah kalau
tempatnya benar.

---

## 11. REVIEW FASE 2 EDUAI — `f561b5c` (+641 baris, 5 berkas)

| Berkas | Isi |
|---|---|
| `app/bab4.py` (281) | Layanan Hasil (versi + Kunci Hasil + tarif) + mesin aturan peta |
| `app/jembatan_statistik.py` (128) | Klien HTTP ke mesin; `trust_env=False` (NO_PROXY IPv6 di sebagian lingkungan membuat httpx gagal urai pola proksi) |
| `app/models.py` (+54) | `HasilBab4`, `PetaBab4` — tabel BARU, `create_all()` |
| `app/kunci_layanan.py` (+11) | layanan `statistik` (menumpang pola yang sudah ada, nol tabel baru) |
| `uji_bab4_fase2.py` (167) | 22 asersi |

### ✅ Yang TERBUKTI BENAR

- `uji_bab4_fase2.py` **22/22 LULUS**.
- Tabel terbuat otomatis: `hasil_bab4` & `peta_bab4` = True via `create_all()`.
- Tarif sesuai keputusan Bos: generate 1–4 = **0 token**, ke-5 = **5 token**
  (`JATAH_GENERATE_GRATIS = 4` = 1 paket + 3 ulang).
- `pra_survei` **tidak** memotong jatah `olah_data` (dihitung per `jenis`).
- Generate baru **tidak** membatalkan status terkunci.
- Desain mengikuti pola `VersiDokumen` (tidak bikin pola versioning kedua) —
  sesuai permintaan dokumen §10.3.

### 🐛 6 BUG temuan Wulan

| # | Bug | Bukti | Tingkat |
|---|---|---|---|
| 1 | **Kunci Hasil dipanggil 2× menggeser versi terkunci mundur** — versi 3 terkunci, kunci#2 menurunkan jadi draf lalu mengunci versi 2 ⇒ narasi baca angka lama | `kunci#1 → 2`, `kunci#2 → 1` | 🔴 KRITIS |
| 2 | `periksa_peta([])` → **AttributeError** | `'list' object has no attribute 'get'` | 🟠 |
| 3 | `periksa_peta({'variabel':'x'})` → **AttributeError** | `'str' object has no attribute 'get'` | 🟠 |
| 4 | Jalur ke variabel **hantu** (`GHOST → Y`) → **nol masalah** | diterima diam-diam | 🟠 |
| 5 | Peran tak sah (`Q`) → hanya "tanpa X", pesan menyesatkan | `peran_tidak_sah` tidak ada | 🟡 |
| 6 | **Modul YATIM** — `main.py` tidak impor `bab4`/`jembatan_statistik`, nol rute, **nol pemanggil** | `grep` kosong; `grep -rln jembatan_statistik app/` = kosong | 🟠 (wajar untuk fase fondasi, wajib dilaporkan) |

📌 **BUG 1 tidak tertangkap uji bawaan** karena uji hanya memanggil **sekali**.
Kelas: *fungsi keadaan wajib diuji idempoten* (§4h SKILL.md).

📌 **BUG 6 cara membedakan "cacat" vs "bertahap":** dokumen §16 menyebut urutan
bangun, jadi orkestrasi & rute memang fase berikutnya. **Sebut sebagai
"pemasangan belum", bukan "gagal".**

### ⚠️ Pelanggaran prosedur Wulan sendiri (dicatat supaya tidak terulang)

Untuk menjalankan uji, Wulan `docker cp` ke **container produksi `eduai-app`**:
```
docker cp app/bab4.py       eduai-app:/app/app/bab4.py
docker cp app/jembatan_statistik.py …
docker cp app/models.py     …   ← MENIMPA berkas produksi
docker cp app/kunci_layanan.py …
```
Tidak ada berkas terlarang repo yang tersentuh, **tidak restart**, tapi gambar
produksi jadi beda dari `Dockerfile`. Aturan yang benar → SKILL.md §3c.

### Putusan

**Belum layak merge.** Wajib dulu **BUG 1** (angka narasi salah = kredibilitas).
BUG 2–5 = pagar masukan. BUG 6 = fase berikutnya (orkestrasi + rute + layar).

---

## 12. PUTARAN 4 — `5eeeff0`: 5 bug TUNTAS, vonis LULUS FONDASI

Bos: *"Sudah diperbaiki cek lagi"* → lalu *"Ok catat dan merge"*.

Commit `5eeeff0` (+108/−7, 3 berkas: `app/bab4.py` +58, `uji_bab4_fase2.py` +37,
dokumen +20).

### Status 6 temuan

| # | Temuan | Status | Bukti terukur |
|---|---|---|---|
| 1 | Kunci Hasil mundur ke versi lama | ✅ TUNTAS + BERGIGI | kunci#2 → `None`; bug disuntik balik → `2` (uji menangkap) |
| 2 | `periksa_peta([])` meledak | ✅ TUNTAS | → masalah `bentuk_salah` |
| 3 | `periksa_peta({'variabel':'x'})` meledak | ✅ TUNTAS | → masalah `bentuk_salah` |
| 4 | Jalur ke variabel hantu | ✅ TUNTAS | → masalah `jalur_hantu` |
| 5 | Peran tak dikenal (`Q`) | ✅ TUNTAS | → masalah `peran_tak_dikenal` |
| 6 | Modul belum dipasang | ⚠️ DIAKUI JUJUR di dokumen §15b | verifikasi ulang: `main.py` tetap tidak impor, rute `/bab4` tidak ada — **klaim cocok kenyataan** |

**Nama kode masalah berubah** dari usulan review (`jalur_asing`, `peran_tidak_sah`,
`bentuk_salah` vs `bentuk_salah`) → **jangan cocokkan string usulan**, cocokkan
**perilaku** (ada masalah + pesannya menyebut hal yang benar).

### Perbaikan BUG 1 — bentuk kodenya (pola yang bisa dipakai ulang)

```python
berlaku = query(status='terkunci').order_by(nomor.desc()).first()
batas = berlaku.nomor if berlaku else 0
draf = query(status='draf', nomor > batas).order_by(nomor.desc()).first()
if draf is None:
    return None          # kunci lama TIDAK diganggu
```
Kuncinya: **hitung batas DULU**, baru ambil draf yang **lebih baru** dari batas.
Versi lama menurunkan semua `terkunci`→`draf` **sebelum** memastikan ada draf baru.

### Uji tepi tambahan Wulan (di luar uji bawaan)

| Kasus | Hasil |
|---|---|
| Kunci v3 → generate v4,v5 → kunci lagi | v5 ✅ |
| Kunci v4 → generate v5 → kunci | v5 ✅ (bukan v3) |
| 12 generate berturut-turut | 12 baris, tanpa error |

`uji_bab4_fase2.py`: **22 → 29 asersi, semua LULUS.**

### ⚠️ Catatan kecil yang TIDAK menghalangi merge

`bab4.py` menyimpan **semua** versi draf tanpa batas (12 generate = 12 baris),
sedangkan pola `VersiDokumen` di repo ini menyimpan maks 2 versi lama. Dokumen
tidak mewajibkan pembatasan → **catat untuk fase berikutnya**, bukan syarat merge.

📌 **Inilah alasan laporan vonis wajib punya bagian "catatan kecil (BUKAN bug)".**
Tanpa bagian itu, temuan nyata tapi tidak menghalangi jadi hilang begitu saja.

### Dua kesalahan Wulan SENDIRI saat catat + merge (melahirkan §5b–§5c)

1. Sebelum menyunting dokumen induk, Wulan menyalinnya ke
   `/opt/data/_review_statlab/DOK_EDUAI_merge.md` "biar aman", lalu **menyalin
   balik** sesudah suntingan → **seluruh catatan §15c HILANG**. Ketahuan dari
   `grep -c "15c. VONIS REVIEW KETIGA"` di **clone baru** = **0**.
2. Commit catatan (`d20ebbb`) dibuat di `agen/wulan/review-lulus-fase2`,
   sedangkan merge ke `main` dilakukan dari `origin/main` + branch **kode** →
   commit catatan tidak terbawa. `main` = `c1dc007`, kode masuk, catatan tidak.
   Obat: `git cherry-pick d20ebbb` → `3810854`, push ulang.

Tambahan: `git push origin origin/agen/wulan/review-lulus-fase2:refs/heads/...`
**gagal** (`src refspec does not match any`) — harus pakai sha/nama branch lokal.

### Bukti akhir (dari clone baru `--depth 1`, bukan `git log` lokal)

| Cek | Hasil |
|---|---|
| `main` teratas | `3810854` |
| `grep -c "15c. VONIS REVIEW KETIGA"` | **1** |
| `app/bab4.py` / `app/jembatan_statistik.py` / `uji_bab4_fase2.py` | ada (14.909 / 4.946 / 9.517 byte) |
| `class HasilBab4` + `class PetaBab4` | **2** |
| `'statistik'` di `kunci_layanan.py` | **1** |
| `periksa_kode.sh` | LULUS |
| uji ulang pasca-merge | 29/29 LULUS |

### Vonis

**LULUS SEBAGAI FONDASI** — masuk `main` dengan pesan merge yang dibuka
peringatan `⚠️ INI FONDASI, BUKAN FITUR JADI`. Fitur BAB IV belum bisa dipakai
user sampai Fase 3 (orkestrasi + rute + layar).

---

## 13. FASE 3 — `5eeeff0` → `81ad1d2`: rute terpasang, tapi SPSS MATI

Bos: *"Fase 3 sudah ada, cek"*. Branch sama (`agen/wulan/bab4-statistik-backend`),
commit teratas `81ad1d2` (+782 baris, 6 berkas).

| Berkas | Isi |
|---|---|
| `app/bab4_rute.py` (BARU, 219) | 13 rute: `/peta`, `/peta/sahkan`, `/instrumen`, `/data`, `/pra-survei`, `/olah-data`, `/kunci-hasil`, `/ringkasan` + unduh template |
| `app/bab4.py` (+~180) | `susun_payload_hitung`, `baris_ke_objek`, `tingkat_pengembalian`, `_nama_kolom` |
| `app/models.py` | tabel `DataLapanganBab4` + perbaikan FK |
| `app/main.py` | router terdaftar ⇒ **BUG 6 Fase 2 TUNTAS** (modul bukan yatim lagi) |
| `uji_bab4_fase3.py` (BARU) | 13 asersi ujung-ke-ujung |

### ✅ Terbukti BENAR (diuji sendiri, 10 kelompok probe)

Tanpa login ditolak · **user lain sentuh berkas orang → 404 di 7 rute** ·
instrumen tanpa peta disahkan → 409 · olah-data tanpa peta → 409 · peta tanpa
bukti mau disahkan → 422 · data kosong → 409 · tahap ngawur → 422 · sel kosong
dibuang & angka `0` tetap dikirim · kunci-hasil kedua → 409 (BUG Fase 2 tidak
kambuh) · pra-survei terpisah dari olah_data · alokasi tarif (4 gratis, ke-5 = 5
token) benar.

### 🐛 5 BUG — satu di antaranya mematikan jalur utama

| # | Bug | Bukti terukur | Tingkat |
|---|---|---|---|
| 1 | **`kolom_y` dikirim sebagai LIST** padahal kontrak mesin minta SATU nama kolom ⇒ **seluruh mode SPSS (regresi/mediasi/moderasi) 400 di setiap percobaan** | `['Minat_1','Minat_2']` → `400 Kolom Y "['Minat_1', ...]" tidak ada di berkas`; diganti string → **200, r2 keluar** | 🔴 **KRITIS** |
| 2 | **Token dipotong DULU, mesin dipanggil kemudian** ⇒ mesin gagal = **502 + token hangus** | `potong_banyak` dipanggil 1× (5 token) lalu `hitung` disuntik melempar → 502, token tidak kembali | 🔴 |
| 3 | Nama variabel saling mengandung ⇒ butir Y masuk daftar X | `Harga` (X) + `Harga Diskon` (Y) → `kolom_x` ikut `Harga_Diskon_1/2` | 🟠 |
| 4 | `jumlah_butir = -3` → **0 kolom** tanpa pesan | kuesioner kosong, user tak tahu kenapa | 🟡 |
| 5 | `jumlah_butir = 'abc'` → **ValueError** (500) | `int('abc')` tanpa pagar | 🟡 |

### 🔬 Kenapa uji bawaan hijau 13/13

**Semua kasus uji memakai PLS-SEM.** Jalur SPSS — jalur mayoritas skripsi S1 —
**nol kasus uji**. Mode PLS selamat karena memakai `konstruk`, bukan `kolom_y`.

⇒ Kelas baru: **mode/jalur yang tidak pernah diuji** (§4k SKILL.md).

### 🔌 Lingkungan uji (jebakan yang memakan waktu)

| Percobaan | Hasil |
|---|---|
| uvicorn `--host 127.0.0.1:8799` dari container | ❌ ConnectionRefused |
| gateway `172.17.0.1:8799` | ❌ ConnectionRefused (routing host ini tidak lewat gateway bridge) |
| uvicorn `--host 0.0.0.0` + **IP host di antarmuka docker** (`172.17.0.11`) | ✅ **tersambung**, uji 13/13 LULUS |

Cara menemukan IP-nya: `hostname -I` lalu uji tiap kandidat dengan
`socket.create_connection()` **dari dalam container** sebelum menjalankan uji.
Detail prosedur → §4l SKILL.md.

### Vonis

**BELUM BOLEH MERGE.** BUG 1 saja cukup menolak: fitur utamanya tidak jalan
untuk mayoritas user. Urutan wajib: (1) `kolom_y` satu nama kolom + **tambah uji
mode SPSS**; (2) bungkus potong-token dengan `kembalikan_banyak` (pola `ai.py`);
(3) pencocokan kolom pakai dasar tegas, bukan `startswith`; (4) validasi
`jumlah_butir`.

---

## 14. PUTARAN 5 — `8f2a39e`: 5 bug Fase 3 TUNTAS, tapi muncul 2 bug baru

Bos: *\"Bug sudah di perbaiki\"*.

### Status 5 temuan Fase 3

| # | Temuan | Status | Bukti terukur |
|---|---|---|---|
| 1 | SPSS mati (`kolom_y` list) | ✅ **TUNTAS** | regresi / mediasi / moderasi / 2-X → **semua 200** |
| 2 | Token hangus saat mesin gagal | ✅ **TUNTAS** | mesin disuntik melempar → 502, token **dikembalikan** |
| 3 | `Harga` ⊂ `Harga Diskon` | ✅ TUNTAS | `X: Harga_1,2` / `Y: Harga_Diskon_1,2`, tidak tumpang tindih |
| 4 | `jumlah_butir=-3` | ✅ TUNTAS | jatuh ke 4 |
| 5 | `jumlah_butir='abc'` | ✅ TUNTAS | jatuh ke 4, tidak meledak |

Bentuk perbaikannya benar (bukan tambalan):
- `kolom_y` daftar → **`peran` per butir** (`X1`/`M1`/`Z1`/`Y1`), yaitu kontrak
  mesin yang sebenarnya (sama dengan jalur halaman Diagnosis).
- `startswith(dasar + '_')` → pola tegas `rf'{re.escape(dasar)}_\d+$'`.
- potong token → `try/except` + `kembalikan_banyak`.
- `jumlah_butir` → `try int()` + batas 1–20 + jatuh ke `len(indikator) or 4`.

`uji_bab4_fase3.py`: **13 → 19 asersi** (termasuk uji SPSS yang sebelumnya nol).

⚠️ **Tiga \"BUG\" di skrip probe Wulan sendiri (`kolom_x`/`kolom_y` = `None`)
ternyata BUKAN bug** — Wulan masih memeriksa kunci lama yang sengaja tidak
dipakai lagi. Probe yang memeriksa kunci usang akan selalu \"merah\" setelah
kontrak berubah. **Perbarui probe, jangan tuduh kode.**

---

## 15. PUTARAN 6 — `93ad415`: 3 bug tuntas, 2 lubang baru di pemetaan hipotesis

Bos: *\"Sudah diperbaiki\"*.

Commit `93ad415` (+208/−9, 3 berkas) menambah:
- `label_peran(peta)` — label mesin per variabel (`X1`,`X2`,`M1`,`Z1`,`Y1`)
- `petakan_hasil_ke_hipotesis(peta, hasil)` — sambung hasil mesin → H1..Hn
- pagar `kolom_tabrakan` di `periksa_peta()`
- `hasil['peta_hipotesis'] = …` **sebelum** `simpan_hasil` di rute

### Status 3 temuan putaran 5

| # | Temuan | Status | Bukti |
|---|---|---|---|
| 1 | Jalur hipotesis tidak dikirim | ✅ TUNTAS | `peta_hipotesis` H1–H3 tersimpan bersama hasil |
| 2 | Dua perantara M1/M2 | ✅ TUNTAS | mesin balas **2 entri mediasi terpisah** |
| 3 | Nama kolom bertabrakan | ✅ TUNTAS | `Kualitas Produk` vs `Kualitas_Produk` → `kolom_tabrakan` |

`uji_bab4_fase3.py`: **19 → 26 asersi**, semua LULUS.

### 🐛 2 BUG BARU — hanya ketahuan karena membandingkan ke ANGKA MESIN

Uji bawaan memeriksa `ketemu == True` dan `b is not None` → hijau. Wulan
menguji **lapis 3** (angka harus sama dengan mesin) → bocor:

| # | Bug | Bukti terukur | Tingkat |
|---|---|---|---|
| 1 | **Jalur `interaksi` (moderasi) → `b=None, p=None, signifikan=None`** walau `ketemu=True`. Mesin menyediakan `delta_r2`, `jenis`, `arah`, `kalimat` — **semuanya tidak dipakai**, hanya `r2` | `ringkas="R² dengan interaksi: 0.043762"`; `kunci moderasi mesin = ['boleh','n','x','z','y','tanpa_interaksi','dengan_interaksi','delta_r2','jenis','arah','kalimat']` | 🔴 **semua penelitian moderasi akan punya H kosong** |
| 2 | **Satu besaran dua presisi** dalam satu tabel | H2 `b=-0.0373` vs mesin `-0.037252`; H3 `b=0.0496` vs `cp=0.049598`; H2 `0.1223` vs `0.122253`. Sebabnya: mesin mengirim angka **bulat 4 desimal** di `koef` dan **penuh** di `kaitan`, dan pemetaan ambil sumber berbeda per jalur | 🟠 melanggar aturan \"sumber angka HANYA hasil mesin, jangan dibulatkan\" |

### ✅ Yang terbukti BENAR di putaran ini

| Hal | Bukti |
|---|---|
| H1 (X→M) = jalur `a` mesin | `b=0.108322` == `med[0]['a']['b']` ✅ |
| H3 (tidak langsung) = efek tidak langsung | `b=-0.004035` == `med[0]['tidak_langsung']['b']` ✅ |
| Jalur terbalik (H9 `Minat→Harga`) **tidak dikarang** | `ketemu=False`, `b=None` ✅ |
| `peta_hipotesis` bisa di-JSON-kan (ikut tersimpan) | ✅ |
| Token dikembalikan bila mesin gagal | tetap ✅ |
| 7 rute kebocoran antar-user | 404 semua ✅ |
| Pagar peta (bukti / hantu / peran / tabrakan) | semua jalan ✅ |

### Vonis

**Belum merge.** Wajib: BUG BARU 1 (jalur `interaksi` harus memakai
`delta_r2`/`jenis`/`arah`/`kalimat` + menandai signifikansi). Sebaiknya: BUG
BARU 2 (satu sumber angka, presisi penuh).

📌 **Pelajaran inti putaran ini** (→ SKILL.md §4m/§4n): modul **adapter/penerjemah**
(kosakata mesin ↔ kosakata peneliti) wajib diuji **per cabang jenis**, dan
lulus-buktinya adalah **angka sama dengan mesin**, bukan `ketemu=True`.

📌 **Uji Wulan sendiri sempat salah dua kali di sesi ini** dan keduanya sudah
dikoreksi: (a) memeriksa kunci lama yang sengaja dihapus (putaran 5), (b)
menuduh `pra_survei` bocor ke `olah_data` padahal tabel sudah terpisah per
`jenis` — Wulan salah membaca hasil query-nya sendiri. **Sebelum melaporkan bug,
pastikan probe-nya sendiri tidak salah** (bandingkan dengan skill
`verifikasi-klaim-kapabilitas-alat-baru`).

---

## 16. PUTARAN 7 — `93ad415` + perbaikan: 2 bug tuntas, **0 bug**, vonis LULUS

Bos: *"Sudah di perbaiki bug nya"* → lalu *"Cari bug lagi"*.

### Status 2 temuan putaran 6

| # | Temuan | Status | Bukti terukur |
|---|---|---|---|
| 1 | Jalur `interaksi`/moderasi `b/p/signifikan = None` | ✅ **TUNTAS** | `b=0.176639`, `p=0.449784`, `signifikan=False`, plus `delta_r2`, `jenis_moderasi`, `arah`, `kalimat_mesin`; `ringkas` = *"Z1 TIDAK memoderasi pengaruh X1 terhadap Y1…"* |
| 2 | Presisi bercampur (4 vs 6 desimal) | ✅ **TUNTAS** | H2 = `-0.037252`, H3 = `0.049598` — **sama persis angka mesin** |

`uji_bab4_fase3.py`: **26 → 29 asersi**, semua LULUS.

### Uji BERGIGI putaran 7 (3 keadaan, §4f SKILL.md)

| Keadaan | Hasil |
|---|---|
| Kode asli | moderasi `b` terisi ✅ |
| Bug lama disuntik balik (hanya ambil `r2`) | `b = None` → **tertangkap** |
| Bug presisi disuntik balik (ambil dari `koef`) | `0.0544 ≠ cp` → **tertangkap** |
| Dipulihkan | presisi penuh kembali ✅ |

⇒ Perbaikan ini **bukan hijau palsu**: bug dikembalikan, uji GAGAL.

---

## 17. PENCARIAN BUG TAMBAHAN (Bos: *"Cari bug lagi"*) — 5 bug baru

Setelah 0 bug di putaran 7, Bos tetap minta cari lagi. Wulan gali **area yang
belum pernah disentuh** → 5 bug, 2 di antaranya **500**.

| # | Bug | Bukti terukur | Tingkat |
|---|---|---|---|
| 1 | **`PUT /api/bab4/data` menerima `baris` berbentuk OBJEK → `POST /olah-data` 500** | `baris=[{...},{...}]` → `200 "tersimpan"`, lalu olah → **500**; jejak `app/bab4.py:580 baris_ke_objek … KeyError: 0` | 🔴 **meledak begitu layar disambung** |
| 2 | **`jumlah_hipotesis = 'tiga'` → 500 di `/peta` DAN `/peta/sahkan`** | `ValueError: invalid literal for int()` | 🔴 |
| 3 | Sel `[null, "abc", 3, …]` **diterima 200** saat simpan | data sampah masuk; user lihat "tersimpan" padahal hasil hitung beda | 🟠 |
| 4 | **`kolom_tabrakan` tidak menangkap dasar saling mengawali** | `Harga 1` + `Harga` → kolom `Harga_1_1…` vs `Harga_1…`; `periksa_peta` = `[]`; mesin balas **200** `prediktor: ['X1']` = **gabungan 2 variabel** | 🟠 data tertukar tanpa peringatan |
| 5 | `kartu_kesehatan` meledak pada bentuk hasil lain | `variabel` str / `butir` dict → `AttributeError: 'str' object has no attribute 'get'` | 🟡 rute `pra-survei` → 500 |

### ✅ Yang diuji dan BENAR (jangan dilaporkan sebagai bug)

Versi 1→2→3→4 berurutan tanpa bolong · kunci hasil = versi terakhir, kunci
kedua 409 · tarif 1–4 = 0 dan ke-5+ = 5 token · peta diubah (belum disahkan) →
olah 409 · instrumen sebelum peta sah → 409 · `file_id` `0/-1/'abc'/None/999999`
→ 4xx rapi · mode PLS 200 · data kosong 409 · 3 baris & 1 baris → 400 dengan
pesan jelas · semua jawaban konstan → 200 · `/simulasi/contoh` bertanda CONTOH ·
berkas dihapus → data yatim 404.

### 🔬 Kenapa 5 bug ini lolos 7 putaran review

Semua putaran sebelumnya memeriksa **jalur yang sudah ada ujinya** (peta,
hipotesis, tarif, token). Yang belum pernah disentuh: **pintu masuk koleksi**,
**field `int()` yang datang dari AI**, dan **relasi antar nama** (bukan kesamaan
persis). ⇒ Kelas baru §4o/§4p/§4q + skrip `scripts/probe_rute_koleksi.py`.

### Pelajaran proses (→ §4q SKILL.md)

- Probe Wulan sendiri bisa **basi**: `_c1.py` masih menuntut `kolom_x`/`kolom_y`
  yang sengaja diganti `peran` → menghasilkan "BUG" palsu. **Baca tanda tangan
  fungsi versi sekarang sebelum menuduh.**
- Setiap ronde wajib: **regresi probe lama** + **satu area yang belum disentuh**.
  Kalau semua probe lama hijau dan tidak ada area baru digali, jawabannya
  "belum ketemu bug di area itu" — **bukan** "kode bersih".
- Satu bug 500 yang **tidak bisa direproduksi ulang** (`olah-data` 500 di `_d4`
  lalu 200 di `_d5` dengan data mirip) wajib dilacak dengan
  `TestClient(app, raise_server_exceptions=True)` sampai traceback keluar —
  jangan disimpulkan "bug hilang sendiri". Ternyata pemicunya **bentuk `baris`**,
  bukan datanya.

### Vonis putaran 7

**BELUM MERGE.** BUG 1 & 2 wajib (dua-duanya 500 nyata); BUG 4 sebaiknya
(data penelitian bisa tertukar diam-diam). Catatan: layar/UI **belum ada** sama
sekali — 13 rute API terpasang, tapi belum ada halaman untuk mahasiswa.

