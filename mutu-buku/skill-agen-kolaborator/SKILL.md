---
name: agen-kolaborator-review-gate
description: Use when reviewing agen lain's branch before main, lalu catat vonis + merge.
version: 1.0.0
author: Wulan
license: proprietary
metadata:
  hermes:
    tags: [kolaborasi, code-review, integration-gate, git-branch, multi-agen, audit-klaim, main-guard, merge, vonis]
    related_skills: [requesting-code-review, github-repo-research, eduai-publishing,
                    verifikasi-klaim-kapabilitas-alat-baru, akar-bukan-tambalan]
---

# 🚦 WULAN = PENJAGA `main` — review branch agen lain sebelum integrasi

## When to Use

Pakai kapan pun pekerjaannya berbentuk **"agen lain koding di branch sendiri,
Wulan yang periksa lalu putuskan boleh masuk `main` atau tidak."** Pemicu nyata:

- Bos bilang *"agen lain akan kolaborasi di github kita"*
- *"Kamu cek di repo ada update"* / *"ada branch baru"*
- *"Kamu yang kendalikan main, agen lain cuma koding di branch-nya"*
- *"Cek apakah sudah ada fase N di repo itu"* (klaim pihak lain soal progres)
- Sebelum **merge / PR / integrasi** apa pun ke branch produksi

**Peran yang DIBERIKAN Bos (verbatim 21 Okt 2026):**
> *"Semua kendali main adalah kamu, agen lain hanya buat koding di branch nya
> sendiri dan Kamu cek saja dan cari bug, sebelum bisa diintegrasikan ke main."*

⇒ Wulan **bukan** pelaksana fitur. Wulan = **gerbang**. Tugas: **cek, cari bug,
putuskan**. Bukan memperbaiki diam-diam di branch orang.

---

## 0. 🚨 ATURAN NOMOR SATU — JANGAN KODING SAAT MENERIMA RANCANGAN

Sesi 21 Okt 2026: Bos menyerahkan **dokumen rancangan induk** BAB IV.
Dokumennya sendiri berisi larangan: *"BAHAS DULU, JANGAN KODING DULU"*.

**Yang BENAR saat menerima dokumen rancangan:**
```
□ BACA seluruh dokumen (bukan potongan)
□ VERIFIKASI setiap klaim [FAKTA] ke KODE — bukan ke dokumen lain
□ Laporkan: yang BENAR · yang SALAH · yang BELUM ADA
□ TUNGGU perintah mulai
```

**Yang HARAM:** membaca 5 baris lalu mulai menulis modul, atau "sekalian
menyiapkan kerangka" karena terasa efisien. Bos tidak meminta itu.

⚠️ **Jangan menambah dokumen tata cara baru tanpa diminta.** Bos pernah marah
untuk ini (*"Kamu saya bayar pakai token, harusnya ikut perintah dan taat
aturan!!!"*). Kalau butuh kontrak kolaborasi, **tanya dulu**.

---

## 1. 🔍 ALUR REVIEW (urutan ini, jangan dibalik)

```
[0] CEK INDUK BRANCH    → merge-base vs main (ketinggalan? = bug paling bahaya)
[1] FETCH + BANDINGKAN  → apa yang BENAR-BENAR baru (commit, diffstat, author)
[2] BACA KLAIM          → dokumen/commit message-nya bilang apa
[3] VERIFIKASI KE KODE  → tiap klaim [FAKTA] → grep/baca sumbernya
[4] CARI BUG (dokumen)  → 5 kelas bug rancangan (§4)
[4b] CARI BUG (kode)    → JALANKAN ujinya, lalu tulis uji tandingan (§4b–4d)
[5] CEK PAGAR           → harga, istilah, larangan, modul terpisah
[6] PUTUSKAN + LAPOR    → terima / tolak / minta perbaikan (tertulis)
```

⚠️ **Ada dua jenis review, dan lapis keduanya wajib:**
- **Dokumen saja** (diff nol kode) → cukup [1]–[5]. Jangan mengklaim "sudah diuji".
- **Ada kode** → WAJIB sampai [4b]. Membaca kode saja **tidak cukup** untuk
  menyatakan bug atau lulus. Buktikan dengan eksekusi.

### [1] Fetch & bandingkan — buktikan "ada update" itu APA

```bash
cd <repo>
git fetch --all --prune
git ls-remote origin                      # SEMUA ref yang benar-benar ada di remote
git log --oneline <lama>..origin/<branch> # commit baru saja
git diff --stat <lama> origin/<branch>    # berapa baris, berkas apa
git log --format="%h | %an <%ae> | %ad | %s" <lama>..origin/<branch>  # SIAPA
```

**Yang WAJIB dicatat dari langkah ini:**
- **Berkas apa** yang disentuh → dokumen saja, atau kode?
- **Berapa baris** → +45 baris dokumen ≠ +450 baris kode
- **Author** → commit dari agen mana

⚠️ **Branch produksi (`main`) sering TIDAK berubah walau branch agen berubah.**
Cek `main` terpisah: kalau `main` masih di commit lama, berarti **belum ada
integrasi** — jangan laporkan "sudah masuk main".

#### 🚨 [1b] REPO BISA SALAH — JANGAN simpulkan "belum di-commit" dari SATU repo

**Kesalahan Wulan terukur 21 Okt 2026.** Bos bilang *"Fase 2 sudah commit,
kamu cek"*. Wulan menjalankan `git ls-remote` di **`statistik-lab`**, tidak
menemukan commit baru, lalu melapor **"Fase 2 belum sampai ke GitHub"** —
padahal commit `f561b5c` sudah ada, rapi, di **`eduai-publishing`**.

Penyebabnya bukan kredensial, bukan branch utama: **Wulan berdiri di repo yang
salah.** Satu project Bos sering terbelah ≥2 repo (EduAi = `eduai-publishing`,
mesin = `statistik-lab`), dan fase baru bisa mendarat di repo yang **tidak**
diduga.

**Wajib SEBELUM melapor "tidak ada":**
```bash
for R in <semua repo project Bos>; do
  cd /opt/data/services/$R
  git fetch -q origin
  echo "== $R =="
  git ls-remote origin | grep -v 'refs/pull'      # semua branch + sha di remote
  git log --oneline origin/main -1 2>/dev/null
  git log --oneline origin/master -1 2>/dev/null
  cd - >/dev/null
done
```
- Cara paling murah menemukannya: `git ls-remote origin` di **setiap** repo,
  cari sha/commit message yang Bos maksud.
- Kalau nama branch tidak diberikan, **tanya nama branch/repo** — jangan
  menebak, dan jangan menyimpulkan "belum di-push".

📍 **Kelas kesalahan yang sama berulang:** *"saya cek X, kosong"* lalu
menyimpulkan *"tidak ada"*, padahal yang diperiksa bukan tempatnya. Sama seperti
menyimpulkan repo hilang dari 404 (jebakan #3). **Ketidakadaan hanya sah kalau
tempatnya benar.**

#### 📍 [1c] LAPOR PETA BRANCH, JANGAN CUMA "TIDAK ADA"

Bos menyimpan kerja di **branch khusus yang sengaja tidak masuk branch utama**.
Jadi jawaban yang berguna bukan *"tidak ada"*, tapi **peta**:

```
Repo            Branch                              Commit teratas
eduai-publishing  agen/wulan/bab4-statistik-backend  f561b5c  ← Fase 2
statistik-lab     agen/wulan/jembatan-bab4           848c0d0  ← Fase 1
statistik-lab     master                             629c4ab  ← hasil merge Fase 1
eduai-publishing  main                                c57f5cd  ← belum berubah
```
Sebutkan juga URL `.../tree/<branch>` supaya Bos/agen lain bisa langsung buka.
Branch utama yang belum berubah **bukan** tanda kerjaan hilang.

### [2] Baca klaim — commit message & dokumen adalah KLAIM, bukan bukti

Commit message yang berbunyi *"Tanggapi 5 temuan review"* atau
*"Catat push branch selesai"* = **klaim**. Wulan wajib membaca isi diff-nya
(`git show <sha> -- <berkas>`), bukan mempercayai judulnya.

### [3] Verifikasi ke KODE — inti pekerjaan ini

Untuk **setiap** klaim bertanda [FAKTA] di dokumen, cari buktinya di kode:

```bash
grep -n "nama_fungsi\|nama_kelas\|nama_rute" app/*.py         # fungsi/kelas benar ada?
grep -c "^def " app/modul.py                                  # tanda tangan ada?
ls app/modul_yang_diklaim.py || echo "TIDAK ADA"
grep -rn "api/jembatan\|nama_endpoint" app/*.py               # endpoint benar ada?
```

**Tabel verifikasi adalah bentuk laporan yang diterima Bos:**

| Klaim dokumen | Bukti di kode | Status |
|---|---|---|
| Pola `VersiDokumen` sudah ada | `app/models.py:234` | ✅ BENAR |
| `_alpha` hanya di jalur PLS | `app/diagnosis.py:703`, dipakai `:466` | ✅ BENAR |
| Endpoint jembatan sudah ada | grep `api/jembatan` = kosong | ❌ BELUM ADA |

📌 **"Ada nama fungsinya" ≠ "fungsinya dipakai".** Cek juga pemanggilnya
(kelas bug *modul ada tapi tak disambung* — lihat skill
`architecture-discussion-and-planning`).

#### 🕳️ [3b] MESIN ADA TAPI MODUL YATIM — celah paling sering dilaporkan "selesai"

Fase fondasi hampir selalu berbentuk: **modul + tabel + uji hijau, tapi belum
disambung ke aplikasi.** Terukur 21 Okt 2026 (Fase 2 BAB IV):

| Cek | Hasil |
|---|---|
| `app/bab4.py` + `app/jembatan_statistik.py` + 2 tabel + `uji_*.py` 22/22 LULUS | ✅ mesinnya nyata & benar |
| `main.py` impor `bab4` / `jembatan_statistik` | ❌ **tidak ada** |
| rute HTTP `/bab4`, `kunci_hasil` | ❌ **tidak ada** |
| ada yang memanggil `jembatan_statistik` | ❌ **nol pemanggil** |

⇒ Modul **yatim**: tidak bisa dijangkau dari aplikasi. Ini **wajar** untuk fase
fondasi (dokumen §16 memang bertahap) — tapi **wajib dilaporkan jujur** supaya
tidak dikira sudah jalan.

**Perintah wajib tiap review ada-kode-baru:**
```bash
# 1. Apakah modul baru diimpor & didaftarkan?
grep -n "bab4\|jembatan_statistik" app/main.py || echo "TIDAK DISAMBUNG"
# 2. Apakah ada RUTE yang memakainya?
grep -rn "nama_modul\|nama_fungsi_kunci\|NamaKelasBaru" app/main.py | head
# 3. Apakah ada PEMANGGIL di luar berkasnya sendiri?
grep -rln "jembatan_statistik" app/ | grep -v "jembatan_statistik.py" || echo "NOL PEMANGGIL"
# 4. Apakah layanan baru muncul di LAYAR admin (kalau dokumen bilang bisa diatur admin)?
grep -n "statistik" app/kunci_layanan.py app/templates/pengaturan.html
```
📌 Laporkan sebagai **dua baris terpisah**: *"mesin ✅ / pemasangan ❌"* — jangan
digabung jadi satu kata "selesai" atau "gagal".

#### 🧨 [3c] JANGAN SUNTIK BERKAS KE CONTAINER PRODUKSI UNTUK UJI

Uji Fase 2 butuh `app.models` versi baru (ada `HasilBab4`). Wulan sempat
`docker cp app/models.py eduai-app:/app/app/models.py` — itu **menimpa berkas
produksi**. Berkas TIDAK terlarang menurut repo, tapi **tetap salah**: gambar
produksi jadi tidak sama dengan `Dockerfile`.

**Urutan yang benar:**
```
1. Coba .venv lokal dulu (uv venv + uv pip install …)
2. Kalau dependensi proyek terlalu berat → `docker exec` pada container UJI,
   atau bangun image sementara
3. Menyalin berkas ke container produksi untuk uji = PILIHAN TERAKHIR, dan
   WAJIB dicatat di laporan sebagai "container tersentuh"
```
⚠️ `docker cp` ke `/app/**` **berbeda** dari deploy resmi (`bash jalankan.sh`).
Kalau terlanjur, katakan — jangan sembunyikan, dan jangan restart container
tanpa izin.

### [4] Cari BUG — 5 kelas yang paling sering lolos

| # | Kelas bug | Cara menemukan |
|---|---|---|
| 1 | **Preseden berbahaya** — catatan lama menormalkan hal terlarang (mis. "PAT Bos dipakai", "docker cp boleh") | grep dokumen untuk kata kredensial/prosedur; tanya: *"kalau agen baru baca ini, apa yang ia simpulkan BOLEH?"* |
| 2 | **Bocor biaya** — harga tetap tapi pekerjaan berulang gratis tanpa batas | hitung: paket X token vs N× pekerjaan berulang |
| 3 | **Klaim UI tanpa tempat di DB** — "tombol/mekanisme" disebut, padahal tak ada tabel/kolom penampung | grep nama tabel di `models.py`; kalau tak ada → ini kerja DB nyata, bukan tempelan |
| 4 | **"Alat sama" yang sebenarnya butuh perubahan** — dokumen bilang nol perubahan, kenyataannya fungsi belum punya mode yang diminta | baca tanda tangan fungsi; ada parameter mode/tahap? |
| 5 | **Urutan/aliran yang mustahil dibayar di depan** — tahap B dibangun dari hasil tahap A, tapi ditagih bersamaan | petakan dependensi antar tahap vs waktu tagih |

### [4b] CARI BUG DI KODE — jalankan ujinya, lalu lawan ujinya

Review dokumen berhenti di "klaim vs kode". Review **kode** butuh lapis kedua:
**buktikan dengan eksekusi.** Dua langkah, dan langkah kedua yang menemukan bug.

**Langkah 1 — jalankan uji milik branch itu sendiri (kalau ada).**
```bash
cd <repo-branch>
uv venv .venv && uv pip install --python .venv/bin/python -q \
  fastapi httpx numpy pandas scipy python-multipart jinja2
.venv/bin/python uji_<fitur>.py ; echo "EXIT=$?"
```
⚠️ Berkas uji yang ada di ROOT repo (bukan `tests/`) biasanya dijalankan langsung
dan mengimpor `app.main` — jalankan **dari dalam direktori repo**, jangan dari
`/tmp` (kalau disalin ke `/tmp`, `import app` gagal: *No module named 'app'*).

**Langkah 2 — tulis uji TANDINGAN sendiri di luar uji mereka.**
Uji milik penulis membuktikan "yang saya bangun jalan". Yang dicari Wulan:
"apa yang **tidak** mereka uji". Kuak 4 kelas ini:

| Kelas lawan | Contoh probe | Bug nyata yang ketemu (21 Okt 2026) |
|---|---|---|
| **Autentikasi aneh** | header dengan karakter non-ASCII, panjang beda, string kosong | `secrets.compare_digest(str, str)` → `UnicodeEncodeError` → **HTTP 500**, bukan 401 |
| **Bentuk data menyimpang** | sel kosong `None`, `NaN` literal JSON, kolom bernama angka, `baris` = dict bukan list, payload = list | semua tertangani rapi (400/422) — bagus, catat sebagai lulus |
| **Data mustahil** | butir konstan (div/0), butir terbalik, teks di kolom angka, 1 baris, 1 butir | tertangani (400 atau alpha negatif jujur) |
| **Kebocoran peran** | satu kolom ditandai **X dan Y sekaligus** | **diterima 200** — mesin menghitung data tak sah tanpa menolak |

**Cara menulis probe-nya:** satu berkas `_bug<N>.py` di dalam repo salinan,
satu blok per kelas, cetak `✓`/`✗ BUG` + detail. Jangan pakai `assert` — kalau
satu probe meledak, sisa probe tidak jalan. Bungkus tiap probe yang mungkin
melempar exception dengan `try/except` supaya bisa **melaporkan crash sebagai
temuan**, bukan mati di tengah.

```python
def cek(nama, ok, detail=''):
    print(('  ✓ ' if ok else '  ✗ BUG ') + nama + ('' if ok else f'  → {detail}'))
```
📌 Untuk probe yang MEMANG harus melempar (mis. kunci non-ASCII), `try/except`
di sekeliling panggilan HTTP — itu yang mengubah "server mati" jadi temuan
tertulis.

**Langkah 3 — periksa ruang lingkup: apakah yang diminta dokumen benar-benar lengkap?**
Cocokkan isi modul baru dengan daftar di dokumen keputusan, **butir per butir**:

```
dokumen §11.2 minta TIGA: (1) pintu kuantitatif ✅  (2) DUA pintu kualitatif ❌  (3) kunci ✅
```
Menemukan yang **belum** dibangun sama pentingnya dengan menemukan yang salah.
Jangan menuntut semuanya sekaligus — cek apakah dokumen memang **bertahap**
(§16 "urutan bangun") sebelum menyebutnya cacat.

### [4c] 🚨 BUG PALING BERBAHAYA: branch ketinggalan `main`

**Periksa ini PALING AWAL, sebelum membaca satu baris kode.** Sesi 21 Okt 2026:
`agen/wulan/jembatan-bab4` bercabang dari `9ca0364`, sedangkan `master` sudah
di `090be17` — **4 commit di depan**, termasuk **SEO (favicon/sitemap/robots)**
dan brand footer. Di diff `master..branch`, berkas-berkas itu tampak
**TERHAPUS** (`app/static/favicon.svg` −12, `uji_seo.py` −141, blok rute
sitemap/robots di `main.py`).

⇒ **Merge apa adanya = MENGHAPUS fitur produksi.** Tidak ada satu pun uji
fitur yang akan menangkap ini, karena uji fitur tidak menguji fitur orang lain.

```bash
git merge-base origin/master HEAD | xargs git log --oneline -1   # induk sebenarnya
git log --oneline $(git merge-base origin/master HEAD)..origin/master  # yang KETINGGALAN
git diff --diff-filter=D --name-only master HEAD               # berkas yg "terhapus"
```

**Membaca hasilnya dengan benar:**
- `--diff-filter=D` menampilkan berkas yang **hilang di branch**. Dua kemungkinan:
  (a) branch memang sengaja menghapusnya, atau (b) **branch cuma ketinggalan**.
  Bedakan dengan `git log --oneline <base>..origin/master` — kalau penghapusnya
  adalah commit di `master` yang tidak ada di branch, jawabannya **(b)**.
- Berkas yang "terhapus" tapi **penghapusnya tidak ada di riwayat branch** =
  pasti ketinggalan, bukan keputusan.
- Verdict: **wajib `rebase`/`merge master` dulu**, baru review fiturnya.
  Jangan pernah merge branch yang ketinggalan commit `main`.

### [4d] Uji yang TIDAK BERGIGI — hijau tapi tak membuktikan apa pun

Uji milik penulis bisa lulus karena **tidak pernah diberi kesempatan gagal**:

| Gejala | Kenapa tak bergigi | Obat |
|---|---|---|
| Uji autentikasi menyetel kunci **di dalam proses uji** (`os.environ[...] = 'kunci-uji-rahasia'`) | Kunci selalu cocok; kalau kode memasang kunci keras, uji tetap hijau | Uji harus **memaksa** kondisi gagal: hapus env → wajib 503; kunci salah → wajib 401 |
| Uji cuma membandingkan `r2`, `koef` | Bagian lain respons (mis. bentuk `masalah[]`, tipe angka) tak diperiksa | Bandingkan **seluruh** respons, bukan 4 kunci pilihan |
| Uji "ada endpoint" | Endpoint ada tapi **tidak tersambung** ke router | Cek juga `app.include_router(...)` benar dipanggil |

📌 Prinsipnya sama dengan `test-gate-design`: **gerbang yang tak bisa gagal =
hiasan.** Saat melapor, sebut uji mana yang tak bergigi — itu temuan, bukan pujian.

### [4e] 🚨 PAGAR YANG MEMBACA BENTUK DATA YANG SALAH — kelas bug yang LOLOS review

**Ini bug yang paling sering lolos, dan urutannya penting: periksa ini SEBELUM
menerima klaim "bug sudah diperbaiki".** Terukur 21 Okt 2026: pagar tumpang-tindih
peran ditambahkan, uji hijau, commit bilang *"Perbaiki bug peran tumpang tindih"* —
**tapi pagarnya buta untuk bentuk yang justru dipakai**.

**Bentuk bug-nya:** ada ≥2 **bentuk kiriman** untuk hal yang sama, dan pagar hanya
membaca satu di antaranya.

```
Bentuk A: {"peran": {"A_1": "X1", ...}}              ← dipakai uji & akan dipakai EduAi
Bentuk B: {"kolom_x": [...], "kolom_y": "..."}        ← dipakai alur lama & DIBACA pagar
```

Pagar membaca B → untuk A ia **tidak pernah menyala**:

| Bentuk kiriman | Pagar | Hasil |
|---|---|---|
| `kolom_x`/`kolom_y` (dibaca pagar) | menyala | ✅ 400 |
| `peran` dict (bentuk NYATA) | **buta** | 🚨 200 — data tak sah tetap dihitung |

Bahkan komentar di kodenya sendiri menyatakan *"Peran (dict kolom→peran) secara
bentuk tidak bisa tumpang tindih"* — **itu salah**: satu dict memang tak bisa
punya kunci kembar, tapi **nilainya** bisa membuat satu kolom berdiri di dua sisi
persamaan **sesudah penggabungan peran**.

**Cara menemukannya (langkah wajib saat review pagar baru):**
```bash
# 1. Baca pagar: FIELD apa yang ia periksa?
sed -n '/def _cek_.*tumpang\|def _pagar/,/^def /p' app/modul.py
# 2. Bandingkan dengan field yang BENAR-BENAR dikirim pemanggil
grep -n "payload.get(" app/modul.py | sort -u     # apa yang dibaca
grep -n "json={'\|json=payload\|'peran'\|\"peran\"" uji_*.py main.py   # apa yang dikirim
# 3. UJI KEDUA BENTUK dengan isi kerusakan yang SAMA — hasilnya harus sama-sama ditolak
```
📌 **Aturan:** pagar yang memeriksa ≥2 bentuk kiriman wajib punya **satu uji per
bentuk**. Uji hanya-bentuk-B + klaim "bug tertutup" = **hijau palsu**.

📌 **Kelas yang lebih luas: "kunci yang sama punya dua penulis/dua pembaca".**
Sama seperti `akar-bukan-tambalan`: cari **pembaca lain** dari field yang sama,
lalu pastikan semuanya melihat bentuk yang sama. Perbaikan yang benar biasanya
bukan menambah cabang di pagar, melainkan **memeriksa payload EFEKTIF** (hasil
penggabungan) — sekali lagi, di titik yang sama mesin menghitung.

### [4f] MUTASI UJI YANG TIDAK SAH — jangan simpulkan "pagar hiasan" dari sini

**Jebakan yang menimpa Wulan sendiri 21 Okt 2026.** Untuk membuktikan pagar
bergigi, pagar dimatikan dengan lambda:

```python
J._cek_tumpang_tindih = lambda p: None      # ❌ TypeError: got unexpected keyword 'efektif'
```

Pagar dipanggil dengan **dua** bentuk panggilan (payload mentah + payload efektif),
sehingga suntikan melempar galat → uji tidak menyelesaikan apa pun → **hasilnya
tampak seperti "pagar tidak menangkap"**. Kalau dipercaya, Wulan akan melaporkan
pagar itu hiasan padahal pagarnya sehat.

**Obat — tiru tanda tangan aslinya:**
```python
asli = J._cek_tumpang_tindih
J._cek_tumpang_tindih = lambda p, efektif=False: None    # ✅ terima SEMUA argumen
...
J._cek_tumpang_tindih = asli                             # pulihkan
```
Atau lebih aman, pakai `unittest.mock.patch` / `functools.wraps` dari fungsi asli.

**Uji 3-keadaan yang WAJIB dijalankan (bukan 2):**

| Keadaan | Harus | Artinya kalau salah |
|---|---|---|
| Pagar asli | 400 | pagar memang menolak |
| Pagar dimatikan total | **200** | kalau tetap 400 → uji mengukur hal lain, bukan pagar |
| Pagar ada tapi **buta untuk bentuk tertentu** (bug versi pertama) | **200** | kalau tetap 400 → uji tidak menguji bentuk itu |

Keadaan ke-3 inilah yang membuktikan uji menangkap bug **spesifik**, bukan cuma
"ada penolakan". Terukur: `pagar-buta` → `peran-terbelah = 200` ⇒ uji memang
menangkap bolongnya.

### [4g] 🔁 BUG YANG DIPERBAIKI BERULANG — periksa apakah perbaikannya DI TITIK YANG SAMA

Kalau agen melaporkan "sudah diperbaiki" untuk bug yang **sama persis** seperti
putaran sebelumnya, curigai **perbaikan yang ditempel di tempat berbeda dari
tempat bug terjadi**. Urutannya:

```
1. Cari TITIK bug semula: bentuk data apa yang MASUK ke fungsi itu di jalur nyata?
2. Cari TITIK perbaikan: field apa yang dibaca pagar/perbaikan baru?
3. Sama?  → uji ulang, boleh diterima
   Beda?  → itu sebabnya berulang. Lapor: "perbaikan ada di jalur X, bug terjadi di jalur Y"
```

📌 **Jangan tawarkan "tambal lagi di jalur X"** — tawarkan **memeriksa payload
efektif** (hasil normalisasi/gabung) supaya satu pagar menutup semua bentuk masuk.
Itu pola yang akhirnya dipakai dan **terbukti** (3-keadaan mutasi hijau).

📌 **Pujian yang tepat sasaran saat perbaikan benar:** sebut **apa** yang benar
(mis. *"sekarang pagar BELAH VARIABEL, bukan cuma tumpang tindih persis"*), bukan
"bagus". Bos menolak pujian tanpa bukti.

### [4h] 🔒 FUNGSI KEADAAN (state) — uji IDEMPOTEN, bukan sekali panggil

**Kelas bug yang uji bawaannya hampir selalu buta.** Terukur 21 Okt 2026
(Fase 2 BAB IV, `app/bab4.py::kunci_hasil`): uji bawaan menguji **sekali**
panggil → 22/22 hijau. Wulan memanggil **dua kali** → ketemu bug fatal:

```
Versi 3 = terkunci          (kunci #1)
Kunci #2 dipanggil lagi   → versi 3 diturunkan jadi 'draf'
                          → versi 2 DIKUNCI  ← narasi membaca ANGKA LAMA
```

Kode menurunkan semua versi `terkunci` jadi `draf` **sebelum** memastikan ada
draf baru. Tidak ada draf → `draf is None` seharusnya berhenti, tapi barisnya
sudah terlanjur diambil dari query yang salah urut.

**Uji wajib untuk SETIAP fungsi yang mengubah keadaan (bekukan/kunci/arsipkan/
tandai-terpakai/hapus-lunak):**

```python
# 1. Panggil saat memang ada kandidat → harus berhasil
k1 = mod.kunci_hasil(db, u, f);  assert k1 is not None
# 2. Panggil LAGI tanpa kandidat baru → WAJIB None / tidak berubah
k2 = mod.kunci_hasil(db, u, f);  assert k2 is None, 'kunci#2 menggeser versi terkunci!'
# 3. Hitung baris berstatus khusus → harus TEPAT 1
assert db.query(M).filter_by(status='terkunci').count() == 1
# 4. Setelah generate baru → status terkunci LAMA harus TETAP
```

| Yang diuji | Kenapa penting |
|---|---|
| Panggil 2× / 3× | Tombol di UI gampang ditekan 2× (dobel klik, kiriman ulang) |
| Jumlah baris berstatus khusus | "Hanya satu yang berlaku" adalah **janji** dokumen |
| Keadaan sesudah aksi lain | Generate baru **tidak boleh** membatalkan pembekuan |

📌 **Cari juga urutan yang salah:** `.order_by(X.nomor.desc()).first()` pada
query yang **tidak** memfilter status benar = mengambil baris yang salah.
Baca `filter_by` dan `order_by` berdampingan, bukan terpisah.

### [4i] 🧪 PAGAR MASUKAN — bentuk data salah harus jadi PESAN, bukan 500

Fungsi murni yang menerima dict dari luar (JSON) wajib tahan bentuk menyimpang.
Terukur 21 Okt 2026, `periksa_peta()`:

| Masukan | Hasil | Seharusnya |
|---|---|---|
| `{}` / `None` | 2 masalah rapi | ✅ |
| `[]` (list) | **AttributeError** | 400 / pesan |
| `{'variabel': 'x'}` (str, bukan list) | **AttributeError** | 400 / pesan |
| jalur menunjuk variabel **hantu** (`GHOST → Y`) | **nol masalah** ← diterima diam-diam | masalah `jalur_asing` |
| peran tidak sah (`Q`) | hanya "tanpa X" (pesan menyesatkan) | masalah `peran_tidak_sah` |

**Probe minimal (3 baris, selalu dijalankan):**
```python
for nama, p in [('kosong', {}), ('list', []), ('str', {'variabel': 'x'}),
                ('jalur hantu', {...}), ('peran aneh', {...})]:
    try: r = mod.periksa(p); print(nama, len(r), 'masalah')
    except Exception as e: print('BUG', nama, type(e).__name__)
```
📌 **Pagar yang memeriksa RELASI wajib memeriksa keberadaan kedua ujungnya.**
Jalur `dari`/`ke` yang tidak ada di daftar variabel = data mustahil, bukan
"variabel tanpa bukti".

### [4j] 💸 URUTAN POTONG-TOKEN vs KERJA — kelas "user bayar, dapat kosong"

**Wajib diperiksa pada SETIAP rute yang memotong token/kuota.** Terukur 21 Okt
2026 (Fase 3 BAB IV, `bab4_rute.py`): urutannya **potong token dulu → baru
panggil mesin**. Mesin mati/timeout ⇒ **502, token sudah terpotong, hasil tidak
ada.** Terbukti dengan menyuntik `js.hitung()` agar melempar:

```
potong_banyak dipanggil 1× (5 token) → mesin gagal → 502 → TOKEN HANGUS
```

Ini persis yang Bos tolak (*"jangan sampai user sudah bayar tapi tidak dapat
apa-apa"*). **Dan pola obatnya SUDAH ADA di repo** — jadi ini kelalaian, bukan
keputusan:

```bash
grep -rn "kembalikan_banyak" app/*.py     # 8 pemakaian di ai.py = pola resmi repo
```

Bentuk yang benar:
```python
info = potong_banyak(db, u, tarif, jenis_addon='ai')   # tolak di DEPAN (402/403)
try:
    hasil = jembatan.hitung(payload)
except GagalJembatan as e:
    kembalikan_banyak(db, u, tarif)      # PAGAR: token kembali
    raise HTTPException(e.status or 502, ...)
except Exception:
    kembalikan_banyak(db, u, tarif)
    raise
```

**Probe minimal (selalu jalankan):**
```python
# 1. Apakah potong dipanggil SEBELUM kerja?
asli = kuota.potong_banyak
kuota.potong_banyak = lambda *a, **k: (_ for _ in ()).throw(Exception('402 simulasi'))
r = klien.post('/rute', json=payload)
# 2. Apakah token DIKEMBALIKAN saat mesin gagal?
js.hitung = lambda *a, **k: (_ for _ in ()).throw(js.GagalJembatan('mati', 'jaringan'))
r = klien.post('/rute', json=payload)     # harus 502 DAN pemanggilan potong-nya tidak 'mengendap'
```

📌 **Bedakan dua hal saat melapor:** (a) *token hangus karena kerja gagal* =
**BUG wajib**, (b) *tarif 0 karena jatah paket* = **benar**. Jangan campur.

📌 Pola kelas yang sama sudah tercatat di memori Bos: *"AI GAGAL TEKNIS → kuota
dikembalikan UTUH; user tekan back setelah hasil jadi → token tetap terpakai,
hasil aman"*. Rute baru yang tidak mengikuti itu = menyimpang dari keputusan.

### [4k] 🧪 MODE/JALUR YANG TIDAK PERNAH DIUJI — hijau karena cuma jalur gampang

**Kelas bug paling berbahaya yang ditemukan 21 Okt 2026** (Fase 3 BAB IV):
modul punya **dua jalur** (`spss` regresi vs `pls`), dan **seluruh uji hanya
memakai PLS**. Jalur SPSS — yang justru mayoritas skripsi S1 — **tidak pernah
bisa jalan sama sekali** (kiriman `kolom_y` berbentuk list, padahal kontrak
meminta satu nama kolom ⇒ mesin balas **400** di setiap percobaan).

Cara menemukannya:
```bash
# 1. Berapa jalur/mode yang modul dukung?
grep -n "if .*mode\|== 'pls'\|== 'spss'\|elif .*metode" app/modul.py
# 2. Bandingkan dengan jalur yang benar-benar dipakai uji
grep -n "mode\|metode" uji_*.py | sort -u
# 3. Jalur yang muncul di kode tapi TIDAK di uji = WAJIB dicoba sendiri, satu kasus nyata
```
📌 **Aturan lapor:** *"mode A tidak diuji sama sekali, dan setelah dicoba ia
GAGAL"* — bukan *"uji hijau 13/13"*. Selalu sebut **mode mana** yang diuji.

📌 Untuk modul penghubung antar-repo, buka **berkas pembaca** (repo sebelah) dan
samakan **tipe tiap field**; jangan menebak dari nama field. Detail pola &
kwitansi: skill `defensive-data-shape-parsing` bagian *"SEBELUM MENULIS KODE
BARU: BACA PEMBACA NYATA"*.

### [4l] 🔌 MENGUJI MODUL YANG BUTUH SERVER SEBELAH (lokal, jangan produksi)

Kalau modul baru memanggil layanan lain, uji bawaan akan gagal dengan pesan
menyesatkan (*"Statistik Lab tidak bisa dihubungi"*) — itu **bukan bug kode**,
itu lingkungan uji. Urutan benar:

```bash
# 1. Nyalakan server mesin dari repo sebelah, di venv repo itu
cd /tmp/<repo-mesin> && JEMBATAN_KUNCI_LAYANAN=<uji> \
  .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8799 &

# 2. Cari IP yang BISA dijangkau container uji (JANGAN asal 127.0.0.1)
hostname -I                       # IP host yang sebenarnya
docker exec <c> python3 -c "
import socket
for h in ('172.17.0.1','172.17.0.11','172.20.0.4'):
    try: socket.create_connection((h,8799),timeout=3); print(h,'OK')
    except Exception as e: print(h,'GAGAL',type(e).__name__)"
```
⚠️ **Jebakan terukur:** `--host 127.0.0.1` membuat container **tidak bisa**
menjangkau (ConnectionRefused), dan gateway `172.17.0.1` **tidak selalu** bisa
(routing host ini tidak melewati gateway bridge). Yang berhasil: **IP host di
antarmuka docker** (mis. `172.17.0.11`) + uvicorn `--host 0.0.0.0`.

```bash
# 3. Jalankan uji dengan env menunjuk IP yang terbukti OK
docker exec -w /app -e <SVC>_URL=http://172.17.0.11:8799 -e <SVC>_KUNCI=<uji> \
  <c> python3 uji_<fitur>.py
```

📌 **Jangan melaporkan uji gagal sebagai bug kode sebelum memastikan jalur
jaringan uji hidup** — tapi **JANGAN** juga diam-diam melewati uji yang tak bisa
jalan. Kalau server sebelah tidak bisa dinyalakan, laporkan **"belum teruji
ujung-ke-ujung"**, bukan "lulus".



```
□ Harga TIDAK diubah/diimprovisasi (bandingkan ke config)
□ Istilah terlarang tidak dipakai
□ Larangan yang sudah diputuskan tidak dibangun ulang (fitur yang DITOLAK)
□ Modul BARU terpisah — tidak menumpuk di main.py / berkas raksasa
□ Berkas terlarang tidak tersentuh (.gitignore, Dockerfile, jalankan.sh,
  SOT_*.md, aturan batas proyek, scripts/periksa_kode.sh)
□ Tidak ada kredensial/token tertulis di repo
□ Jalankan gerbang repo: bash scripts/gerbang_git.sh --periksa
```

### [4m] 🧩 PEMETAAN HASIL → HIPOTESIS — "ketemu" ≠ "angkanya BENAR"

**Wajib untuk modul yang menyambungkan hasil mesin ke istilah peneliti**
(hipotesis H1..Hn, jalur, indikator). Terukur 21 Okt 2026 (Fase 3 BAB IV,
`petakan_hasil_ke_hipotesis`): uji bawaan hanya memeriksa `ketemu == True`
dan `b is not None` → **26/26 hijau**. Wulan menguji **angkanya** → 2 lubang.

**Tiga lapis uji, dan lapis ketiga yang menemukan bug:**

| Lapis | Pertanyaan | Cukup? |
|---|---|---|
| 1 | `ketemu` True/False | ❌ hampir tak berguna |
| 2 | `b`/`p` tidak `None` | ❌ hanya menangkap cabang kosong |
| 3 | **`b` SAMA PERSIS dengan angka mesin untuk jalur itu** | ✅ ini yang menemukan bug |

```python
# lapis 3 — bandingkan ke angka MESIN, bukan ke angka pemetaan
med = (hasil['kaitan'] or {}).get('mediasi') or [{}]
cek('H1 (X→M) b = mesin jalur a', pm[0]['b'] == med[0]['a']['b'])
cek('H3 (X→Y langsung) b = mesin cp', pm[2]['b'] == med[0]['cp']['b'])
```

**Bug yang hanya ketahuan dari lapis 3:**

1. **Cabang jenis jalur punya kelengkapan berbeda.** Jalur `langsung` dan
   `tidak_langsung` mengambil `b`/`p` dengan benar, tapi jalur **`interaksi`
   (moderasi)** mengembalikan `b=None, p=None, signifikan=None` — hanya
   `ringkas="R² dengan interaksi: 0.0438"`. Padahal mesin menyediakan
   `delta_r2`, `jenis`, `arah`, `kalimat`. ⇒ **setiap penelitian moderasi akan
   punya hipotesis kosong di BAB IV**, walau `ketemu=True` dan uji hijau.

2. **Satu besaran, dua presisi.** Mesin mengirim angka **dibulatkan 4 desimal**
   di satu kunci (`koef`) dan **penuh** di kunci lain (`kaitan`). Pemetaan
   mengambil dari sumber berbeda per jalur ⇒ satu tabel memuat `b=0.0496` dan
   `b=0.049598`. Bukan "salah hitung", tapi **melanggar aturan "sumber angka
   HANYA hasil mesin, jangan dibulatkan"** dan bikin tabel tidak konsisten.

**Cara menemukannya (jalankan tiap review modul pemetaan):**
```bash
# 1. Kunci apa yang BENAR-BENAR dikirim mesin untuk cabang itu?
#    cetak SEMUA kunci + contoh isi, jangan cuma yang dipakai kode
python3 -c "print(sorted(hasil.keys()))"
# 2. Cabang/case apa saja yang ada di pemetaan?
grep -n "jenis.*==\|elif j.get('jenis')" app/<modul>.py
# 3. Untuk SETIAP cabang, uji satu kasus nyata + bandingkan ke angka mesin
```
📌 **Aturan lapor:** sebut cabang mana yang kosong (*"jalur interaksi `b/p`
kosong padahal mesin punya `delta_r2`"*), bukan *"pemetaan hipotesis sudah
jalan"*.

📌 **Jangan tertipu `ketemu=True`.** `ketemu` cuma berarti *"ada entri"* —
bukan *"entrinya berisi angka yang benar"*. Sama seperti §4d: hijau tanpa
kesempatan gagal.

📌 **Kelas umum:** setiap kali ada **adapter/penerjemah** antara dua kosakata
(mesin ↔ peneliti, kode ↔ label, ID ↔ nama), adapter itu wajib diuji
**per cabang**, bukan per fungsi.

### [4n] 📐 KOLOM YANG DIBANGUN DARI NAMA — uji tabrakan, bukan cuma pemisahan

Nama variabel manusia → nama kolom mesin adalah **pemetaan yang bisa tidak
injektif**. Terukur 21 Okt 2026:

| Nama variabel | Dasar kolom | Bahaya |
|---|---|---|
| `Kualitas Produk` | `Kualitas_Produk` | — |
| `Kualitas_Produk` | `Kualitas_Produk` | **SAMA** ⇒ data dua variabel tertukar diam-diam |
| `Harga` vs `Harga Diskon` | `Harga` ⊂ `Harga_Diskon` | `startswith` menelan butir Y (§7 #23) |

Dua bug berbeda dari akar yang sama: **pemetaan nama→kolom tidak dijaga**.
Perbaikan yang benar bukan menambal `startswith`, tapi:
1. **Batas tegas** saat memisahkan butir: pola `<dasar>_<angka>$`, bukan `startswith`.
2. **Pagar tabrakan** saat menyusun peta: kalau dua nama menghasilkan dasar yang
   sama → tolak (`kolom_tabrakan`), jangan diam-diam digabung.

```python
dasar_kolom = {}
for v in variabel:
    dasar = _nama_kolom(v['nama'])
    if dasar in dasar_kolom and dasar_kolom[dasar] != v['nama']:
        tambah('kolom_tabrakan', f'{v["nama"]} dan {dasar_kolom[dasar]} → kolom sama')
    dasar_kolom.setdefault(dasar, v['nama'])
```
📌 Uji wajib: **dua nama berbeda secara ejaan** (`Kualitas Produk` vs
`Kualitas_Produk`) dan **dua nama saling mengandung** (`Harga` vs `Harga
Diskon`) — keduanya harus lolos tanpa tertukar.

⚠️ **Pagar `kolom_tabrakan` yang hanya membandingkan dasar SAMA PERSIS masih
BOLONG.** Terukur 21 Okt 2026 (ronde 5): nama `Harga 1` dan `Harga` menghasilkan
kolom `Harga_1_1 …` dan `Harga_1 …`. Dasarnya (`Harga_1` vs `Harga`) **tidak
sama**, jadi pagar diam — tapi mesin membaca nama sebelum `_` **terakhir**
sebagai variabel, sehingga `Harga_1_1` → variabel `Harga_1` dan `Harga_1` →
variabel `Harga`. Hasil: **mesin balas 200** dengan `prediktor: ['X1']` yang
merupakan **gabungan dua variabel berbeda**, tanpa peringatan.

⇒ Pagar tabrakan wajib memeriksa **tiga** relasi, bukan satu:

| Relasi | Contoh | Wajib ditolak |
|---|---|---|
| dasar sama persis | `Kualitas Produk` ≡ `Kualitas_Produk` | ✅ |
| dasar **saling mengawali** | `Harga` ⊂ `Harga Diskon` | ✅ |
| dasar + nomor **bertabrakan** | `Harga 1` (butir `Harga_1_1`) vs `Harga` (butir `Harga_1`) | ✅ |

Cara murah & tuntas: bandingkan **daftar kolom hasil `buat_instrumen()`**, bukan
daftar nama variabel — kolomlah yang dibaca mesin. Kalau ada kolom yang menjadi
milik ≥2 variabel (atau satu kolom muncul di dua peran), tolak.

### [4o] 🌐 RUTE PENERIMA DATA — bentuk `baris` wajib diperiksa di PINTU MASUK

**Kelas bug yang meledak justru SETELAH layar disambung.** Terukur 21 Okt 2026
(Fase 3 BAB IV, `PUT /api/bab4/data` + `baris_ke_objek`):

```
PUT /api/bab4/data   baris = [{"Harga_1":4,"Minat_1":2,...}, ...]   → 200 "tersimpan"
POST /api/bab4/olah-data                                            → 500
File "app/bab4.py", line 580, in baris_ke_objek
    if i < len(b) and b[i] not in (None, ''):
KeyError: 0
```

Penyebab: rute menerima `baris` **apa pun** tanpa memeriksa bentuk, lalu fungsi
pembaca mengindeks `b[i]` (menganggap daftar). Objek dict → `KeyError` → 500.

Kenapa ini pasti kejadian: `GET /data` mengembalikan baris apa adanya, jadi layar
JavaScript akan mengirim balik **bentuk yang sama** — kalau pernah tersimpan
sebagai objek, selamanya 500.

**Aturan:** setiap rute yang menerima koleksi (`baris`, `kolom`, `items`, `rows`)
wajib memeriksa **bentuk tiap elemen**, bukan cuma `isinstance(x, list)`:

```python
if not all(isinstance(b, (list, tuple)) for b in baris):
    raise HTTPException(422, 'Baris harus daftar nilai per kolom, bukan objek.')
if not all(isinstance(c, (int, float, str)) or c is None for b in baris for c in b):
    raise HTTPException(422, 'Sel harus angka/kosong — periksa baris ke-N.')
```

📌 **Validasi di pintu masuk, bukan dibiarkan ke mesin.** Kalau data sampah
diterima "tersimpan", user melihat datanya masuk padahal hasil hitungnya beda
dari yang ia kira. Laporkan sebagai *"diterima 200 padahal seharusnya 422"*.

### [4p] 🔢 `int()` TANPA PENJAGA = 500 DI RUTE PETA/DOKUMEN

Nilai yang datang dari AI/parsing naskah sering **bukan angka**. Terukur:

```
peta['jumlah_hipotesis'] = 'tiga'
POST /api/bab4/peta         → 500
POST /api/bab4/peta/sahkan  → 500        (ValueError: invalid literal for int())
```

**Probe wajib untuk setiap field yang di-`int()` dari masukan luar:**
```python
for v in ['abc', None, -3, 3.7, '', [], {}]:
    try: r = klien.post('/rute', json={'field': v}); cek(f'{v!r} -> 4xx', r.status_code < 500)
    except Exception as e: cek(f'{v!r} tidak meledak', False, type(e).__name__)
```
📌 Nilai aneh harus jadi **422 dengan pesan**, bukan 500. `jumlah_butir`
sempat diperbaiki jadi "jatuh ke bawaan" — tapi `jumlah_hipotesis` terlewat.
**Perbaikan validasi harus disapu ke SEMUA field sejenis di modul itu**, bukan
satu per satu saat dilaporkan (pola `akar-bukan-tambalan`: cari kembarannya).

### [4q] 🧪 `ketemu=True` BUKAN BUKTI — dan uji ronde-lalu TIDAK melindungi ronde-ini

Dua pelajaran proses, terukur 21 Okt 2026:

1. **Probe Wulan sendiri bisa basi.** Skrip `_c1.py` masih memeriksa kunci
   `kolom_x`/`kolom_y` yang **sengaja sudah tidak dipakai** setelah kontrak
   berubah ke `peran`. Hasilnya Wulan sempat melaporkan *"kolom_x = None → BUG"*
   padahal kodenya benar. **Sebelum menuduh, pastikan kontrak yang diperiksa
   masih kontrak yang berlaku** — baca `susun_payload_hitung()` versi sekarang,
   jangan pakai ingatan ronde lalu.
2. **Perbaikan ronde N tidak otomatis menutup kelas bug yang sama.** Tiap ronde
   wajib: jalankan **skrip probe ronde-ronde sebelumnya** (regresi) **plus**
   gali **satu area yang belum pernah disentuh**. Daftar area yang terbukti
   produktif: pagar masukan fungsi murni · rute penerima koleksi · field
   `int()` dari AI · relasi antar nama (tabrakan) · urutan salah (data sebelum
   peta) · `id` aneh (0/-1/str/None) · entitas dihapus tapi anaknya masih ada.

📌 **Lapor jujur kalau probe sendiri yang salah.** Kalimat yang diterima Bos:
*"3 'BUG' di skrip lama Wulan bukan bug — Wulan masih memeriksa kunci lama.
Skrip ujinya yang perlu diperbarui, bukan kodenya. Wulan akui."*

### [4r] 🔍 AUDIT GLOBAL LINTAS FASE — bug yang bukan crash: "mesin ada, JALANNYA tidak"

Saat Bos bilang *"cari bug lagi, termasuk fase-fase sebelumnya"*, jangan ulangi
probe ronde lalu saja. Terukur 21 Okt 2026 (Fase 3 BAB IV setelah 5 bug tuntas,
semua 500 hilang): audit global menemukan **4 lubang PEMASANGAN** yang tak akan
pernah muncul sebagai crash dan tak akan pernah ditangkap uji mana pun.

**Tiga sudut yang paling produktif — periksa dalam urutan ini:**

| # | Sudut | Perintah | Yang ketemu (terukur) |
|---|---|---|---|
| 1 | **Rute TULIS ada, rute BACA tidak** | `grep -n "@router\." app/<modul>_rute.py` lalu kelompokkan GET vs POST | `POST /olah-data` + `POST /pra-survei` + `POST /kunci-hasil` ada, **`GET /hasil` TIDAK ADA** ⇒ hasil masuk DB, **tak ada jalan membacanya** ⇒ narasi/langkah berikutnya mustahil |
| 2 | **Data bisa DITULIS ke nilai yang tak pernah DIBACA kode** | cari setiap `body.get('<field>')` yang disimpan, lalu `grep` apakah field itu dipakai selain saat menyimpan | rute simpan 3 `tahap` (`pra`/`utama`/`simulasi`) tapi `olah-data` **hardcode `utama`** ⇒ data simulasi 409 selamanya ("tersimpan sia-sia") |
| 3 | **Fungsi ada, NOL pemanggil** | untuk tiap fungsi publik modul: `grep -rn <fn> app/ \| grep -v "def <fn>"` | `frekuensi_kolom` & `tingkat_pengembalian` (isi BAB IV 4.1) **0 pemanggil** — mesin ditulis, tak disambung |

**Probe minimal (tulis sekali, pakai tiap audit):**
```python
import re, subprocess
src = open('app/<modul>_rute.py', encoding='utf-8').read()
rutes = re.findall(r"@router\.(get|post|put|delete)\('([^']+)'\)", src)
tulis = [p for m, p in rutes if m in ('post', 'put')]
baca  = [p for m, p in rutes if m == 'get']
print('TULIS:', tulis); print('BACA:', baca)
# setiap hasil yang ditulis harus punya pembaca
for kata in ('hasil', 'pra', 'kunci'):
    print(kata, '-> baca?', [p for p in baca if kata in p] or 'TIDAK ADA')
# fungsi mati
for fn in ('frekuensi_kolom', 'tingkat_pengembalian'):
    g = subprocess.run(['grep', '-rn', fn, 'app/'], capture_output=True, text=True)
    pakai = [b for b in g.stdout.split('\n') if b and f'def {fn}' not in b]
    print(f'{fn}: {len(pakai)} pemanggil')
```

📌 **Jangan sertakan "nol layar/template" sebagai bug kode** kalau dokumen memang
bertahap — tapi **wajib disebut** (`grep -rln <modul> app/templates/` = kosong ⇒
*"12 rute berdiri tanpa satu halaman"*). Itu batas fase, bukan cacat.

📌 **Sebut fase asal tiap bug, jangan bilang \"bug BAB IV keseluruhan\".** Bos
bertanya persis itu. Jawab dengan `git log -S "def <fungsi>" --reverse` per
fungsi → tabel *fungsi bermasalah → commit kelahiran*. Terukur: 5 dari 6 bug
lahir di commit Fase 3 (`81ad1d2`), 1 akar desainnya Fase 2 ⇒ *"ini utang Fase 3,
bukan regresi, dan `main` belum punya berkasnya jadi produksi tidak terpengaruh"*.

⚠️ **Fuzz "semua fungsi publik" menghasilkan 213 \"meledak\" — itu SALAH SARING.**
Fungsi yang butuh `db`/argumen internal memang tak tahan `None`; itu bukan bug
karena pemanggilnya selalu benar. **Saring dulu:** hanya fungsi **murni** yang
dipanggil **rute** dengan **data user**. Setelah disaring, hasilnya bersih — dan
Wulan harus mengaku salah ukur itu di laporan.

### [4s] 🔐 FUNGSI KEADAAN BER-`jenis` — filter wajib IKUT, bukan cuma jadi parameter

**Kelas bug yang lolos SEMUA uji karena hanya muncul di satu urutan pemakaian.**
Terukur 21 Okt 2026 (Fase 3 BAB IV, `kunci_hasil(db, user_id, file_id, jenis='olah_data')`):

Fungsi sudah punya parameter `jenis`, tapi **query di dalamnya tidak memakainya**
— dan rute memanggilnya **tanpa** meneruskan `jenis`. Akibatnya satu tabel
menampung `jenis='olah_data'` dan `jenis='simulasi'` dengan penomoran
**terpisah** (`nomor` 1 di keduanya), lalu pagar "versi terkunci" membandingkan
`nomor` lintas jenis.

| Urutan pemakaian | Hasil |
|---|---|
| olah ASLI → kunci → simulasi → kunci | ✅ olah_data v1 terkunci, simulasi v1 draf |
| **simulasi → kunci → olah ASLI → kunci** | 🚨 **simulasi TERKUNCI**, lalu kunci data asli → **409 "tidak ada hasil baru"** |

Akibat nyata: peneliti yang **latihan dulu** (urutan paling wajar) mengunci
hasil latihan, dan **hasil penelitiannya tidak pernah bisa dikunci**. Narasi
BAB IV membaca angka latihan.

**Probe wajib untuk SETIAP fungsi keadaan yang punya kolom pembeda
(`jenis`/`mode`/`tahap`/`kategori`):**

```python
# 1. baca fungsi: apakah kolom pembeda muncul di filter_by/query, atau cuma di tanda tangan?
src = inspect.getsource(mod.kunci_hasil)
assert 'jenis=' in src.split('"""', 2)[-1], 'jenis hanya jadi parameter, tidak dipakai!'
# 2. urutan TERBALIK: isi jenis B dulu, kunci, baru jenis A, kunci
mod.simpan(jenis='simulasi'); assert mod.kunci(...) is None      # wajib TOLAK
mod.simpan(jenis='olah_data'); assert mod.kunci(...) is not None # wajib BERHASIL
# 3. hitung baris per jenis
assert db.query(M).filter_by(jenis='simulasi', status='terkunci').count() == 0
```

📌 **Uji urutan TERBALIK, bukan cuma urutan "enak".** Semua uji bawaan memakai
urutan `utama` dulu → hijau. Bug hanya muncul kalau jenis "latihan" masuk lebih
awal. Aturan umum: **kalau ada >1 nilai sah untuk sebuah kolom pembeda, uji
setiap nilai sebagai yang PERTAMA**, bukan hanya yang pertama secara intuitif.

📌 **Periksa juga rute:** parameter yang ada di fungsi tapi **tidak diteruskan
rute** = parameter hiasan. `grep "kunci_hasil(db" app/*_rute.py` — kalau
`jenis` tidak muncul di pemanggilan, fitur "kunci per jenis" tidak ada.

### [4t] 🖥️ LAYAR MEMANGGIL ENDPOINT YANG TIDAK ADA — 3 tombol inti 404

**Kelas bug fase terakhir, dan uji Python tidak akan pernah menangkapnya.**
Terukur 21 Okt 2026: `app/templates/bab4.html` memanggil **11 endpoint**, tiga
di antaranya **tidak terdaftar di router**:

| Dipanggil layar | Rute sebenarnya | Hasil |
|---|---|---|
| `/api/bab4/kunci` | `/api/bab4/kunci-hasil` | ❌ 404 |
| `/api/bab4/olah` | `/api/bab4/olah-data` | ❌ 404 |
| `/api/bab4/pra` | `/api/bab4/pra-survei` | ❌ 404 |

Dan sebaliknya: **rute yang ada tapi tidak pernah dipanggil layar** —
`GET /hasil`, `GET /profil` ⇒ mesinnya jalan, angkanya **tidak pernah tampil**.

**Perintah wajib tiap ada layar/template baru (murah, 10 detik):**
```bash
# 1. endpoint yang DIPANGGIL layar
grep -o "/api/<modul>/[a-z0-9/_-]*" app/templates/<layar>.html | sort -u > /tmp/dipanggil.txt
# 2. endpoint yang BENAR-BENAR terdaftar
grep -o "@router\.[a-z]*('/[^']*')" app/<modul>_rute.py | sed "s/.*('\/\?/\/api\/<modul>\//;s/')//" | sort -u > /tmp/terdaftar.txt
# 3. selisih dua arah — keduanya bug
comm -23 /tmp/dipanggil.txt /tmp/terdaftar.txt   # layar minta, server tak punya  → 404
comm -13 /tmp/dipanggil.txt /tmp/terdaftar.txt   # server punya, layar tak pakai  → fitur tak tampil
```

📌 **Dua arah sama pentingnya.** Arah pertama = tombol mati (user klik → 404).
Arah kedua = fitur tak terlihat (server benar, user tak pernah tahu ada).

📌 **Jangan percaya "layar sudah ada" sebagai tanda "fitur jalan".** Layar di
fase ini adalah **klaim visual**; yang membuktikan hanya pasangan
`grep endpoint` ↔ `grep @router`. Sama seperti §3b: mesin ✅ / pemasangan ❌.

📌 Idealnya ini jadi **gerbang otomatis** di repo (gagal build kalau ada
endpoint layar tanpa rute). Usulkan ke agen penulis, jangan tulis sendiri di
branch orang.

#### [4t-1] 🧾 KONTRAK LAYAR↔RUTE — cek yang dipanggil **BENAR-BENAR terdaftar**

Perbaikan yang benar atas §4t bukan cuma mengganti 3 nama endpoint, tapi
**menambahkan gerbang** yang membuat kesalahan itu mustahil terulang. Bentuk
yang terbukti (dipakai agen, 21 Okt 2026):

```python
# 1. ambil semua URL /api/<modul>/... dari template
# 2. ambil semua path dari router (INGAT: r.path sudah memuat prefix)
# 3. selisih dua arah = temuan; EXIT 1
```

⚠️ **Jebakan waktu memeriksanya sendiri:** `r.path` pada router Starlette
**sudah memuat prefix** (`/api/bab4/...`). Probe yang menempelkan prefix lagi
akan melihat **semua endpoint "yatim"** — itulah yang membuat Wulan sempat
melapor *"13 endpoint yatim"* padahal sehat. Bandingkan apa adanya, atau pakai
`u == t or u.startswith(t) or t.startswith(u)`.

📌 Saat gerbang begini ditambahkan oleh agen, **nilai plus** — sebut di vonis
(*"bukan cuma dibetulkan, tapi dijaga"*), jangan dianggap basa-basi.

⚠️ **PROSA YANG SALAH TETAP `200`.** Sama seperti §4d: uji status HTTP tidak
pernah membaca kalimatnya. Untuk modul penghasil teks, probe teks (§4u) wajib,
dan idealnya juga jadi gerbang repo supaya tiap perbaikan prosa menambah
asersi — bukan cuma mengganti string.

#### [4t-2] 🔧 PERBAIKAN `<kunci> <spasi> <kata>` — spasi harus MASUK ke dalam

Kelas cacat halus yang muncul setelah perbaikan prosa, dan **mudah diperbaiki
salah**:

```python
f"{'tidak' if signifikan else ''} melewati nol"    # ❌ 'tidak'=None → "  melewati" (spasi dobel)
f"{'tidak ' if signifikan else ''}melewati nol"     # ✅ spasi ikut ke dalam string
```

⇒ Taruh spasi di **dalam** potongan bersyarat, bukan di luar. Pola ini berlaku
untuk semua f-string bersyarat di prosa (narasi, laporan, ringkasan).

📌 Uji yang benar: **dua keadaan**, bukan satu —
`'] melewati nol' in teks` **dan** `']  melewati' not in teks`, plus satu kasus
dengan nilai kebalikannya (`'] tidak melewati nol'`). Satu keadaan saja bisa
lolos karena cabang yang salah.

### [4u] 📝 UJI TEKS NARASI/LAPORAN — hijau karena hanya dicek `200` + satu kata kunci

**Kelas bug paling akhir fase, dan paling merusak kredibilitas.** Terukur 21 Okt
2026 (Fase 3 BAB IV, `bab4_narasi.susun_draf`): uji bawaan memeriksa
`r.status_code == 200` dan `'signifikan' in teks` → **LULUS**. Wulan membaca
teks yang benar-benar keluar → **4 cacat**:

```
- H3: pengaruh Harga terhadap Keputusan sebesar 0.0065 dengan nilai
  signifikansi — — hipotesis ditolak.
- H3: H3: b=0.006458, p=None → tidak signifikan
```

| # | Cacat | Penyebab |
|---|---|---|
| 1 | **label dobel** `H1: H1:` | penyusun menambah label padahal `ringkas` dari mesin sudah memuatnya |
| 2 | **`— —` dobel** | nilai kosong di-format dua kali (satu per lapis) |
| 3 | 🚨 **vonis \"ditolak\" untuk `p` yang TIDAK ADA** | efek tidak langsung (bootstrap) tak punya `p`; kode memperlakukan `None` sebagai \"tidak signifikan\" lalu menulis **\"hipotesis ditolak\"** — **salah secara statistik** |
| 4 | **`p=None` bocor ke teks** | `str(None)` ikut tercetak |

⚠️ **Cacat 3 = tingkat kredibilitas.** Skripsi yang memuat \"hipotesis ditolak\"
tanpa p-value akan langsung dipatahkan pembimbing. `None` **bukan** nol, **bukan**
tidak signifikan — ia \"tidak diukur dengan cara itu\".

**Aturan umum:** setiap modul yang **menghasilkan prosa** (narasi bab, laporan
audit, ringkasan, surat) wajib diuji **teksnya**, bukan status HTTP-nya:

```python
teks = j['teks']
cek('tanpa label dobel',   not re.search(r'H\d+:\s*H\d+:', teks))
cek('tanpa separator dobel', '— —' not in teks)
cek('tanpa None tercetak',  'None' not in teks and 'nan' not in teks.lower())
# angka desimal di teks HARUS ada di hasil mesin (bukan dikarang)
angka_teks  = {round(float(x), 4) for x in re.findall(r'-?\d+\.\d{3,4}', teks)}
angka_mesin = {round(float(v), 4) for v in _semua_float(hasil)}
cek('semua angka dari mesin', angka_teks <= angka_mesin, angka_teks - angka_mesin)
# nilai yang TIDAK ADA tidak boleh divonis
for e in hasil.get('peta_hipotesis', []):
    if e.get('p') is None:
        cek(f"{e['hipotesis']} p kosong → tidak divonis 'ditolak'",
            'ditolak' not in _kalimat_untuk(teks, e['hipotesis']))
```

📌 **Sertakan `R²`, `r2_adj`, koefisien mentah ke himpunan `angka_mesin`.**
Terukur: Wulan sempat menuduh `0.0119` \"bukan dari mesin\" — ternyata itu **R²**.
Sebelum menuduh angka karangan, sisir **seluruh** `hasil` secara rekursif.

📌 **Jangan vonis dari status.** Prosa yang salah tetap `200`. Sama seperti §4d:
hijau tanpa kesempatan gagal.

#### [4t-3] 🧷 BRANCH FASE BARU KETINGGALAN `main` → MERGE = MENGHAPUS CATATAN VONIS

**Kejadian nyata 21 Okt 2026 (Fase 4).** Branch `bab4-statistik-backend`
bercabang dari `cb36678` (akhir Fase 3) — **sebelum** `3ca2f2d` (merge Fase 3) dan
`ef402e2` (vonis Fase 3) masuk `main`. Diff `main..branch` untuk dokumen induk:
**−118 baris**, isinya persis **§15c (vonis Fase 2) + §15d (vonis Fase 3)**.

⇒ Merge apa adanya = **jejak review 9 ronde hilang dari `main`**. Ini bosan §4c
tapi dengan korban berbeda: bukan fitur produksi, melainkan **dokumen vonis** —
dan tidak ada uji yang menangkapnya.

**Deteksi (10 detik, sebelum baca kode):**
```bash
BASE=$(git merge-base origin/main origin/<branch-agen>)
git log --oneline "$BASE" -1                       # induk sebenarnya
git log --oneline "$BASE"..origin/main             # isi = branch KETINGGALAN
git diff --stat origin/main origin/<branch-agen> -- '*.md'
git diff origin/main origin/<branch-agen> -- '*.md' | grep '^-' | grep -i 'vonis\|15c\|15d'
```
📌 **Diff dokumen dengan baris `-` yang menghapus bagian VONIS = tanda bahaya**,
bukan penyuntingan wajar. Vonis HANYA boleh bertambah, tidak pernah berkurang.

**Obat (urutan yang terbukti):**
```bash
git checkout -B <branch>-rapi origin/<branch-agen>
git merge origin/main --no-commit          # biasanya auto-merge BERSIH
grep -c "15c. VONIS REVIEW" <DOKUMEN>.md   # WAJIB ≥1
grep -c "15d. VONIS REVIEW" <DOKUMEN>.md   # WAJIB ≥1
grep -c "Pembaruan Fase 4"  <DOKUMEN>.md   # tambahan baru harus TETAP ada
bash scripts/periksa_kode.sh && bash scripts/gerbang_git.sh --periksa
git commit -m "Rapikan dokumen: branch ketinggalan main — kembalikan vonis ..."
git push origin <branch>-rapi
```

📌 **Sekalian perbarui status yang basi.** Terukur: §15b masih menulis *"SISA Fase
3: simulasi, narasi, layar"* padahal ketiganya sudah selesai dan sudah di `main`.
Ganti jadi status benar + jumlah rute terbaru, dan **tandai blok lama sebagai
`⚠️ RIWAYAT (bukan status sekarang)`** — jangan dihapus (aturan Bos: arsip
ditandai, bukan dibuang).

📌 **Jangan minta agen lain memperbaiki ini lalu menunggu.** Bos sudah memberi
peran *"kendali `main` = kamu"*; merapikan branch sebelum review masih di dalam
peran itu. Tapi **tetap minta izin dulu** kalau menyentuh branch orang (§0).

#### [4v] 🧪 GAGAL PALSU DARI PROBE SENDIRI — kelas paling sering, sudah dipindah
**Semua "BUG" di bawah ternyata SALAH WULAN, bukan kode** (21 Okt 2026, Fase 4
kualitatif). Kelas lengkap: probe BLIND `exceptionDetails`, patch `%s`, bug
middleware-cookie → `references/jebakan-probe-http-cdp-dan-bug-cookie-22okt2026.md`.

| # | Gejala | Sebab sebenarnya | Obat |
|---|---|---|---|
| 1 | `POST /peta/sahkan` → **422 `fokus_kosong`** padahal peta "sudah benar" | Bentuk peta **kualitatif** memakai `fokus`/`informan` di **akar**; Wulan mengirim `variabel` seperti peta kuantitatif | Baca bentuk peta dari **uji bawaan** (`grep "peta_k = "`), jangan mengarang |
| 2 | `PUT /kualitatif/segmen` → **422 "Segmen ke-1 tidak punya teks"** | Segmen butuh `teks`+`informan`+`teknik`+`jenis` **per potongan**; Wulan mengirim `tema`/`kutipan` | Salin bentuk segmen dari uji bawaan, bukan dari nama field di DB |
| 3 | Rute token → **500 `AttributeError: no attribute 'email'`** | `dependency_overrides[wajib_login_api] = lambda: types.SimpleNamespace(id=1)` — fungsi saldo memanggil `u.email`/`u.role` | Override dengan **objek User ASLI dari DB** (`ss.get(User, 1)`), bukan SimpleNamespace |
| 4 | Narasi → **403 BUTUH_UPGRADE** padahal mau uji isi teks | Saldo uji kurang 30 token | Isi saldo lewat jalur RESMI: `kuota._saldo.masuk(db, u, 500, 'uji', '...')`. **Jangan** mengarang kolom (`u.token_saldo = 500`) — kolom itu tak ada di `User`, dan `except: pass` menyembunyikannya |

**Aturan induk:** sebelum melaporkan 4xx/500 sebagai bug, tanya **"apakah kiriman
SAYA yang salah bentuk?"** Periksa bertiga: (a) bentuk di uji bawaan, (b) signature
fungsi, (c) objek yang di-inject ke `dependency_overrides`. Kalau ketiganya tidak
diperiksa, laporan pertama hampir pasti palsu.

📌 **Kolom saldo token TIDAK ada di tabel `User`.** `saldo_token()` membaca buku
besar `SaldoToken` lewat `kuota._saldo.sisa()`. Probe yang menyetel atribut user
akan "berhasil" secara Python lalu tetap 403 — kegagalan senyap yang bikin Wulan
mengira pagar token rusak.

📌 **Suntingan `str.replace` pada probe bisa TIDAK MENDARAT** (pola lama tak
cocok). Setelah mengedit skrip probe, **cetak ulang isi berkasnya** atau tulis
ulang dari nol. Terukur: Wulan 2× mengira sudah memperbaiki probe padahal berkas
di container masih versi lama.

### [4w] 🏷️ ISTILAH TERTUKAR DI PROSA KUALITATIF — "informan" vs "teknik"

**Kelas bug yang tidak akan ditangkap uji status dan merusak metodologi.**
Terukur 21 Okt 2026 (`bab4_narasi`, bagian 4.3 Triangulasi). Data: tema didukung
**3 informan** tapi hanya **1 teknik** pengumpulan data.

Mesin bilang (benar): `kuat: true, tertriangulasi: false, jumlah_teknik: 1`

Narasi menulis: *"…tergolong kuat; namun, tema tersebut baru didukung oleh
**satu jenis informan**."* ⇒ **dua kesalahan sekaligus**: (a) menyebut "satu"
padahal 3 informan, (b) memakai kata **informan** untuk hal yang sebenarnya
**teknik**.

Di penelitian kualitatif **informan ≠ teknik**: informan = orang (I1, I2, I3),
teknik = cara ambil data (wawancara, observasi, dokumentasi). Menukarnya = BAB IV
salah metodologi, dan pembimbing langsung menangkapnya.

**Probe wajib untuk modul prosa kualitatif** — bandingkan **kalimat** ke **angka
mesin**, per medan:
```python
tri = hasil['triangulasi']['tema'][0]
cek('kuat=true → tidak bilang "perlu diperkuat"',
    not (tri['kuat'] and 'perlu diperkuat' in blok))
cek('jumlah_informan=3 → tidak bilang "satu informan"',
    not (tri['jumlah_informan'] > 1 and 'satu informan' in blok))
cek('jumlah_teknik=1 → kalimat menyebut TEKNIK, bukan informan',
    'satu teknik' in blok or 'satu jenis teknik' in blok)
```
📌 **Kelas umum:** setiap prosa yang menerjemahkan **angka** jadi **kalimat**
wajib diuji dengan **pasangan (angka, kata)** — bukan sekadar "kata itu muncul".
Sama seperti §4u, tapi korban di sini **istilah**, bukan format.

### [5] Putuskan + laporkan — bentuk yang diterima Bos

```
## 📥 Update yang masuk
<commit sha> — "<judul>" (+N baris, M berkas)

## ✅ Verifikasi ke kode — <BENAR>/<SALAH>
| Klaim | Bukti | Status |

## 🎯 Kesimpulan
<Terima / Tolak / Minta perbaikan> — <1 kalimat alasan>

## ⚠️ Masih menggantung
<yang belum diputuskan Bos>
```

**Kalau ditolak → tolak dengan ALASAN TERTULIS.** Jangan perbaiki sendiri di
branch orang (dua penulis = dua sumber kebenaran).

---

## 2. 🖥️ "CEK REPO ITU" — TIGA SUMBER, JANGAN TERTUKAR

Saat Bos bilang *"cek apakah sudah ada fase N di repo X"*, ada **tiga** tempat
berbeda yang sering dianggap satu. **Ukur ketiganya, laporkan terpisah.**

| Sumber | Artinya | Cara cek |
|---|---|---|
| **Remote** | apa yang sudah di-push | `git ls-remote` / `git fetch` |
| **Lokal** | salinan di mesin ini (BISA KETINGGALAN) | `git log`, `grep` di disk |
| **LIVE** | apa yang benar-benar jalan untuk user | `curl` endpoint nyata |

**Kwitansi 21 Okt 2026 (Bos: *"cek ke repo tersebut apakah sudah ada fase 1"*):**
- Remote: **tidak terbaca** (repo private + token mati)
- Lokal `@090be17`: `grep api/jembatan` = **KOSONG**
- LIVE: `POST /api/jembatan/hitung` → **404**; `/api/status` → `versi: "fase1"`
  ⚠️ label `"fase1"` itu **versi web lama (17 Sep)**, BUKAN fase yang dimaksud

⇒ **Jangan tertipu label versi.** `versi: "fase1"` di `/api/status` bisa berarti
tahap produk yang sama sekali lain. Yang menentukan: **endpoint-nya ada atau
tidak**.

📌 **Kalau salinan lokal bersih tapi Bos yakin sudah dikerjakan** → salinan lokal
**ketinggalan branch**, atau kerjaan belum di-push. Sebut kemungkinan itu,
jangan menyimpulkan "Bos salah".

---

## 4x. 🔎 BOS LAPOR GEJALA DI PRODUKSI ("kok muncul HTTP 502") — LACAK LINTAS LAPIS, JANGAN TUDUH KODE

**Jenis tugas berbeda dari review branch**, tapi sering muncul di sesi yang sama
dan paling gampang salah jawab. Terukur 21 Okt 2026: Bos lapor
*"di https://statistik.bikinaja.id/kualitatif klik Minta saran AI muncul
`Belum bisa memakai AI: HTTP 502`"*.

**JANGAN langsung bilang "bug kode".** 502 di produksi punya **≥4 lapis** asal,
dan pesan yang dilihat user hampir selalu **bukan** pesan aplikasi.

### Urutan pelacakan (murah → mahal, berhenti begitu ketemu)

```bash
# L1. Kode di repo: baca rute + bagaimana ia menjawab galat
grep -n "@app.post('/api/<rute>')" -A 60 app/main.py
#    catat SEMUA cabang: kunci absen · saklar mati · balasan kosong · exception

# L2. Environment container (bukan kode) — kunci API & saklar
docker exec <c> printenv | grep -iE "API_KEY|_BASE|MODEL" | sed 's/\(KEY=\).*/\1<ADA>/'
docker exec <c> cat /app/data/ai_aktif.txt

# L3. Provider dari DALAM container (lewati aplikasi)
docker exec <c> python -c "<urlopen langsung ke base>/chat/completions ..."

# L4. Rute dari DALAM container (lewati jaringan/Cloudflare)
docker exec <c> python -c "<urlopen 127.0.0.1:8000/api/...>"

# L5. Rute dari DOMAIN PUBLIK (semua lapis ikut: CF + nginx + container)
curl -s -m 180 -w "HTTP %{http_code} | %{time_total}s\n" -X POST https://<domain>/api/<rute> ...

# L6. LOG — inilah bukti sebenarnya
docker logs --since 4h --timestamps <c> | grep "<rute>"
docker logs --since 4h <router> | sed -n '1,40p'
```

### Membaca hasilnya (peta sebab → vonis)

| L3 | L4 | L5 | Artinya |
|---|---|---|---|
| ✅ | ✅ | ✅ | Bukan kode, bukan jaringan — **gangguan sesaat provider**. Uji ulang beberapa kali, laporkan apa adanya |
| ✅ | ✅ | ❌ | Lapisan luar (Cloudflare/nginx/timeout), **bukan** kode aplikasi |
| ✅ | ❌ | ❌ | Antara container & rute — cek log aplikasi |
| ❌ | — | — | Provider/kunci — cek `printenv` + log router |

⚠️ **Log router bisa menipu.** Terukur: model membalas **`succeeded`** di log
router, tapi `DONE … IN 0 · OUT 0` — **isi kosong**. Aplikasi melihat balasan
kosong → menjawab `502` dengan pesan *"AI menjawab tapi isinya kosong"*. Jadi
"succeeded" ≠ "ada isinya"; **selalu baca `IN`/`OUT`**, bukan cuma status.

⚠️ **`max_tokens` kecil + model reasoning = jawaban KOSONG.** 14,6 detik menunggu
lalu `OUT 0` = jatah token habis untuk "mikir" sebelum sempat menulis. Untuk
saran pendek, naikkan `max_tokens` atau pilih model non-reasoning. Ini **kelas
bug konfigurasi**, bukan bug logika.

### 🐛 Temuan yang tetap SAH walau kodenya sehat: PESAN GALAT MENYEMBUNYIKAN SEBAB

Ini yang paling sering jadi keluhan Bos, dan **benar** bahwa itu cacat. Terukur:
server sudah punya **4 pesan bagus** (kunci absen · AI dimatikan · balasan
kosong · exception), tapi layar menampilkan **"HTTP 502"** saja.

```js
const d = await r.json().catch(() => ({}));
if (!r.ok || !d.boleh) throw new Error(d.sebab || ('HTTP ' + r.status));
```

`d.sebab` **ada isinya** kalau yang menjawab aplikasi. Kalau yang menjawab
**Cloudflare** (balasan HTML, bukan JSON), `r.json()` gagal → `{}` → jatuh ke
`'HTTP ' + r.status` ⇒ **user kehilangan seluruh informasi sebabnya**.

**Aturan lapor:** bedakan tegas —
*"rutenya SEHAT (3× 200 saat diuji ulang); yang cacat adalah **pesan galatnya**
tidak pernah sampai ke user"*.
Jangan gabung jadi "AI rusak" (menakutkan, salah) atau "tidak ada bug" (menyembunyikan
cacat nyata).

📌 **Bentuk perbaikan yang diminta:** layar wajib membedakan (a) balasan JSON
aplikasi → tampilkan `d.sebab`; (b) balasan non-JSON / `502` tanpa `sebab` →
*"Server tidak menjawab dalam waktu lama — coba lagi sebentar lagi"*.
Jangan pernah menampilkan kode status mentah sebagai satu-satunya pesan.

📌 **Ini juga berlaku saat reviewer melihat `Balasan kosong`/`502` di uji sendiri:**
sebelum melaporkan bug, jalankan L3–L6 — bisa jadi provider sedang gangguan, dan
melaporkannya sebagai bug kode akan membuat agen lain "memperbaiki" kode sehat.

### [4x-1] ✅ PENUTUP: akar `OUT 0` = `enable_thinking`, dan pesan galat yang menyembunyikan sebab

Bagian di atas menulis **dugaan** (`max_tokens` kecil + model reasoning). Sesi yang
sama menuntaskannya — **inilah jawabannya, jangan mengulang penyelidikan dari nol.**

**Akar (terukur, 2 arah, `max_tokens=200`):**

| | Tanpa param | `enable_thinking: False` |
|---|---|---|
| `content` | **KOSONG** · `finish_reason=length` · pikir 652 | **terisi** 87 kar · `finish=stop` · pikir 0 |

⇒ Model `cb/deepseek-v4.1-flash` membuang token untuk `reasoning_content` **lebih
dulu**. Jatah habis ⇒ `content` tak pernah ditulis ⇒ HTTP **200** tapi kosong ⇒
aplikasi balas 502. **Menaikkan `max_tokens` hanya memperbesar peluang — bukan obat.**

**Perbaikan yang terbukti (3 lapis, semuanya perlu):**
1. `'enable_thinking': False` di **payload utama DAN payload coba-ulang**.
   Kalau hanya yang pertama diberi, coba-ulang tidak menolong sama sekali.
2. `_sebab_kosong(mentah)` membaca `finish_reason` + `reasoning_content` ⇒
   sebab ditulis sebagai **kalimat manusia**, bukan `HTTP 502`.
3. Layar memeriksa `content-type` sebelum `r.json()`. Galat Cloudflare berbentuk
   **HTML**; `r.json()` gagal ⇒ `d={}` ⇒ user hanya melihat `'HTTP '+status`.

**Verifikasi akhir yang sah** (bukan "gerbang hijau"):
```
HTTP 200 ×3 lewat DOMAIN PUBLIK, isi benar, 3,6–4,6 dtk
```

⚠️ **Dua gagal palsu Wulan di babak ini — kenali polanya:**
- Probe melapor **8/8 KOSONG** padahal semua 200. Sebab: `json.loads(mentah)` utuh
  pada balasan berekor `data: [DONE]` ⇒ `JSONDecodeError` ⇒ dicatat "kosong".
  **Tanda pengenal: `finish=None` di SEMUA percobaan = alat ukurnya salah.**
  Obat: `json.JSONDecoder().raw_decode()` dari `{` pertama.
- Menyimpulkan **"mount Docker tidak sinkron"** karena berkas dibaca beda antara
  host (`1`) dan container (`0`). Ternyata nilainya memang berbeda pada jam itu
  (saklar AI dimatikan gerbang uji lain). **Jangan menyimpulkan kerusakan
  prasarana sebelum memastikan nilai yang dibandingkan memang seharusnya sama.**

📌 **Gerbang `gerbang_baca_judul.py` MEMATIKAN saklar AI saat diuji** (`POST /api/ai
{'aktif': False}`) lalu menyalakannya lagi. Kalau gerbang itu gagal di tengah,
saklar bisa tertinggal mati ⇒ user melihat *"AI sedang dimatikan"* padahal bukan
disengaja. Periksa ini **sebelum** menuduh konfigurasi.

📌 **Pelajaran proses:** Bos menyelesaikan ini dengan **satu perintah** —
*"reasoning = false aja"* — setelah Wulan menghabiskan beberapa putaran menaikkan
`max_tokens`. Saat akarnya berupa **parameter model**, tanyakan dulu *"bisakah
modelnya diminta berhenti berpikir?"* sebelum menyetel angka. Detail lengkap:
skill `akar-bukan-tambalan` Hukum 16.

---

## 5. 📝 LAPOR, CATAT, MERGE — setelah vonis keluar

Vonnis "LULUS" belum selesai sampai **jejaknya tertulis** dan **commit-nya
benar-benar mendarat di branch produksi**. Bagian ini berisi 3 kesalahan Wulan
sendiri (21 Okt 2026) yang semuanya terjadi **setelah** review selesai dengan
benar.

### [5a] Tulis vonis ke dokumen induk, bukan cuma ke chat

Bos menerima vonis dalam bentuk **bagian dokumen** yang bisa dibaca agen lain
berikutnya. Bentuk yang dipakai (terbukti diterima):

```markdown
## 15c. VONIS REVIEW KETIGA — <FASE> LULUS SEBAGAI <SIFAT> (<tanggal>)

Reviewer: Wulan (pemegang kendali `main`). Branch: `<branch>` @ **<sha>**.
Metode: baca diff baris-per-baris + uji bawaan + **uji bug independen** +
**uji mutasi** (perbaikan dicabut untuk membuktikan uji bisa GAGAL).

### Status <N> temuan review sebelumnya
| # | Temuan | Status | Bukti |
### Uji mutasi (bukti uji tidak hijau palsu)
| Keadaan | Hasil |
### Uji tepi tambahan reviewer (di luar uji bawaan)
### Catatan kecil (BUKAN bug, tidak menghalangi merge)
**VONIS: <LULUS / TOLAK> — <satu kalimat tegas>**
```

📌 **WAJIB ada baris "Uji mutasi".** Tanpa itu, "semua hijau" tidak bisa
dibedakan dari "uji tak bergigi" (§4d/§4f).

📌 **WAJIB ada bagian "catatan kecil (BUKAN bug)"** supaya hal seperti *"semua
versi draf disimpan tanpa batas, 12 generate = 12 baris"* tercatat untuk fase
berikutnya tanpa menghalangi merge.

### [5b] 🚨 JANGAN menyimpan "salinan" dokumen SEBELUM diedit

**Kesalahan Wulan 21 Okt 2026.** Sebelum menyunting dokumen induk, Wulan
menyalinnya ke `/opt/data/_review_statlab/DOK_EDUAI_merge.md` dengan komentar
"biar aman", **lalu** mengedit berkas aslinya. Sesudahnya menyalin balik
"supaya sama" → **catatan vonis hilang total**, dan baru ketahuan dari
`grep` di clone baru.

**Aturan:** berkas cadangan hanya boleh dibuat **SEBELUM** suntingan pertama,
dinamai jelas `*.bak-<tujuan>`, dan **TIDAK PERNAH disalin balik**. Kalau butuh
membandingkan, pakai `git diff` — repo sudah jadi cadangan.

### [5c] 🚨 COMMIT CATATAN HARUS IKUT MASUK `main` — jangan cuma di branch review

**Kesalahan Wulan 21 Okt 2026 (kedua, di sesi yang sama).** Commit vonis
(`d20ebbb`) dibuat di branch `agen/wulan/review-lulus-fase2`, sementara merge ke
`main` dilakukan dari `origin/main` + merge **branch kode** — jadi commit catatan
**tidak terbawa**. `main` naik, kode masuk, catatan **tidak**.

Obat: `git cherry-pick <sha-catatan>` di branch merge, lalu push lagi.

**Verifikasi wajib SEBELUM melapor "sudah merge":**
```bash
cd /tmp && rm -rf _verif && git clone -q --depth 1 <url-remote> _verif && cd _verif
echo "== HEAD ==";        git log --oneline -2
echo "== catatan ==";     grep -c "VONIS REVIEW" <DOKUMEN>.md     # harus ≥1
echo "== berkas kode =="; ls <modul_baru>.py <uji_baru>.py
echo "== tabel ==";       grep -c "class <TabelBaru>" app/models.py
echo "== pemasangan ==";  grep -c "<nama_modul>" app/main.py
```
📌 **Clone baru dari remote = satu-satunya bukti sah.** `git log` di repo kerja
bisa menipu: ia menampilkan commit **lokal** yang belum di-push.

### [5d] Pesan merge harus menyebut SIFAT commit, bukan hanya isinya

Kalau yang masuk adalah **fondasi** (mesin ada, pemasangan belum), pesan merge
WAJIB dibuka dengan peringatan, bukan daftar fitur:

```
Merge Fase 2 BAB IV EduAi: FONDASI (belum bisa dipakai user)

⚠️ INI FONDASI, BUKAN FITUR JADI. app/bab4.py + app/jembatan_statistik.py
BELUM diimpor main.py, belum ada rute HTTP, belum ada layar. Fitur BAB IV
belum bisa dipakai user sampai Fase 3 (orkestrasi + rute + UI).
```

Alasannya: pesan merge adalah satu-satunya dokumen yang dibaca orang saat
`git log`. Tanpa peringatan ini, "Fase 2 merge" terbaca sebagai "fitur jalan".

### [5e] Urutan merge yang benar (jangan dibalik)

```bash
cd <repo>
git fetch -q origin
# 1. Catat vonis di branch review, COMMIT
git checkout -B agen/wulan/review-lulus-<fase> origin/<branch-agen>
#    (sunting dokumen induk) ; git add ; git commit
# 2. Gerbang repo WAJIB lulus sebelum merge
bash scripts/gerbang_git.sh --periksa
bash scripts/periksa_kode.sh            # untuk repo EduAi
# 3. Merge dari induk bersih (bukan dari branch agen)
git checkout -B main-merge origin/main
git log --oneline origin/main..origin/<branch-agen> | wc -l   # commit baru
git log --oneline origin/<branch-agen>..origin/main | wc -l   # 0 = tidak ketinggalan
git merge --no-ff origin/<branch-agen> -m "<pesan §5d>"
# 4. Kalau commit catatan belum terbawa:
git cherry-pick <sha-catatan>
# 5. Uji ULANG pasca-merge (bukan cuma pra-merge)
# 6. Push, lalu VERIFIKASI dari clone baru (§5c)
git push origin HEAD:main
git push origin <sha-catatan>:refs/heads/agen/wulan/review-lulus-<fase>
```

⚠️ `git push origin origin/<branch>:...` **gagal** (`src refspec ... does not
match any`) — pakai **sha atau nama branch lokal**, bukan `origin/...`.

#### [5e-2] 🚧 PUSH DITOLAK `fetch first` — artinya ORANG LAIN SUDAH MENAMBAH, bukan repo rusak

**Terukur 21 Okt 2026.** Bos bertanya *"sudah kamu push ke repo Statistik lab?"*
Jawabannya **belum** — 3 commit perbaikan hanya ada di VPS. Saat push:

```
! [rejected]  master -> master (fetch first)
hint: Updates were rejected because the remote contains work that you do
      not have locally.
```

⇒ **Bukan** kredensial mati, **bukan** repo rusak: **remote lebih baru**. Dan yang
lebih baru itu ternyata **isi fase lain** (Fase 1 jembatan BAB IV, 7 commit) yang
belum pernah dilihat. Perlakukan sebagai review branch — bukan `pull` refleks.

**Urutan yang benar (jangan `git pull` dulu):**

```bash
# 1. fetch TANPA merge, lalu petakan DUA arah
git fetch origin
git log --oneline HEAD..origin/master        # yang ADA di remote, TIDAK di sini
git log --oneline origin/master..HEAD        # milik Wulan yang belum naik

# 2. Cek tabrakan SEBELUM merge: baris siapa di berkas mana
git diff HEAD...origin/master --stat
git diff HEAD...origin/master -- app/main.py | grep '^@@'    # hunk kedua sisi

# 3. Bandingkan letak perubahan — kalau berjauhan, merge PASTI bersih
grep -n "<penanda_kode_Wulan>" app/main.py                   # baris Wulan
#    vs nomor hunk di langkah 2 → tidak beririsan = aman

# 4. CADANGAN branch dulu (murah, 1 detik)
git branch cadangan-pra-merge-$(date +%H%M)

# 5. merge (bukan rebase — branch bersama, jangan tulis ulang riwayat)
git merge origin/master -m "Merge <isi remote> dari remote"

# 6. VERIFIKASI KEDUA SISI setelah merge — ini langkah yang wajib
grep -c "<penanda_kode_Wulan>" app/main.py      # perbaikan sendiri masih ADA
ls app/<modul_dari_remote>.py                   # kode remote masuk
python -c "import ast; ast.parse(open('app/main.py').read()); print('SAH')"
```

📌 **Verifikasi DUA ARAH, bukan satu.** Setelah merge, yang biasa diperiksa hanya
*"kode remote masuk?"* — padahal risiko sebenarnya adalah **perbaikan sendiri
hilang diam-diam**. Cetak hitungan penanda kode sendiri (`grep -c`), jangan cuma
melihat `git status` bersih.

📌 **Push sukses ≠ commit mendarat.** Buktikan dengan cek per-commit:
```bash
git fetch origin
for c in <sha1> <sha2> <sha3>; do
  git branch -r --contains "$c" | grep -q 'origin/master' \
    && echo "✅ $c ADA" || echo "❌ $c HILANG"
done
```
Terukur: pesan `629c4ab..cf9a98e  master -> master` saja **tidak cukup** —
Bos menanyakan hal ini, dan jawabannya harus per-commit.

📌 **Kredensial: cari helper repo yang SUDAH jalan, jangan bikin token baru.**
`git push` gagal `could not read Username for 'https://github.com'` = repo itu
belum punya `credential.helper`. Repo lain di project yang sama biasanya sudah:
```bash
git -C <repo-lain> config --local --list | grep credential
# → credential.helper=store --file=/opt/data/vault/.git-credentials-<nama>
git -c credential.helper="store --file=/opt/data/vault/.git-credentials-<nama>" push origin master
```
Pakai **hanya kalau owner repo sama** (`PaculDigital/*`). Jangan menyimpan token
baru ke repo; jangan mencetak isi berkas vault.

📌 **Kalau gerbang repo menolak karena dokumen baru belum terdaftar** (mis.
`sot.py` → *"belum didaftarkan di peta dokumen STATUS.md"*), itu **gerbangnya
bekerja**, bukan halangan. Daftarkan 1 baris di tabel peta dokumen, jangan
melewati gerbang. Terukur: merge kode remote sukses, tapi `sot.py` merah sampai
`CATATAN_*.md` didaftarkan.

#### [5e-1] 🧷 KONFLIK DOKUMEN SAAT CHERRY-PICK — DUA vonis, BUKAN dua salinan

**Kejadian nyata 21 Okt 2026 (Fase 3).** `cherry-pick` commit vonis bentrok
karena `main` sudah punya **§15c (vonis Fase 2)**, sedangkan commit baru juga
menulis **§15c (vonis Fase 3)** — penulis memakai nomor yang sama.

Hasil kalau ditangani buru-buru: penanda `<<<<<<<` tertinggal di dokumen repo,
atau salah satu vonis **hilang**. Dua-duanya merusak jejak review.

**Aturan:** kedua vonis WAJIB disimpan — nomori ulang yang lebih baru.

```bash
# 1. Lihat penanda + posisi kedua judul
grep -n '<<<<<<<\|=======\|>>>>>>>\|VONIS REVIEW' <DOKUMEN>.md
# 2. Simpan versi HEAD (§lama) apa adanya; naikkan nomor versi yang baru
python3 - <<'PY'
import re
p='<DOKUMEN>.md'; s=open(p,encoding='utf-8').read()
s=s.replace('=======\n## 15c. VONIS ... FASE 3',
            '---\n\n## 15d. VONIS ... FASE 3')
s=re.sub(r'>>>>>>> [0-9a-f]+[^\n]*\n','',s)
open(p,'w',encoding='utf-8').write(s)
print('penanda sisa:', s.count('<<<<<<<'), s.count('======='), s.count('>>>>>>>'))
PY
```

Verifikasi WAJIB sebelum `--continue`:
```bash
grep -c '<<<<<<<\|=======\|>>>>>>>' <DOKUMEN>.md      # harus 0
grep -n 'VONIS REVIEW' <DOKUMEN>.md                    # harus 2 baris (lama + baru)
bash scripts/periksa_kode.sh && bash scripts/gerbang_git.sh --periksa
git add <DOKUMEN>.md && git cherry-pick --continue
```

⚠️ **Jangan pakai `git checkout --ours/--theirs`** untuk dokumen seperti ini —
itu membuang salah satu vonis, dan jejak review lama ikut lenyap tanpa jejak.

⚠️ **`=======` juga dipakai markdown biasa** (`===` di bawah judul tabel/pemisah).
Setelah membersihkan penanda, hitung ulang dengan pola persis 7 karakter;
kalau gerbang/preview mengeluh, cari `^=======$` (baris tunggal).

### [5f] Susun laporan akhir dalam 3 blok, jujur soal kesalahan sendiri

Bentuk yang diterima Bos:

```
## ✅ CATAT + MERGE — SELESAI        (1 baris status)
## 🔍 Terbukti di GitHub              (tabel: dicek | hasil, dari clone baru)
## ⚠️ Yang Wulan laporkan jujur       (kesalahan sendiri + yang masih menggantung)
## ➡️ Siap fase berikutnya            (1-3 butir konkret)
```

📌 **Kalau Wulan salah di tengah jalan, tulis di laporan** — bukan disembunyikan.
Contoh nyata: *"Wulan sempat salah dua kali: simpan salinan dokumen sebelum
diedit lalu menimpanya balik; commit vonis mendarat di branch review bukan di
main"*. Bos menerima laporan yang mengaku salah; yang ditolak adalah laporan
"semua sempurna" tanpa bukti.

---

## 6. 🔐 KREDENSIAL REPO — PROSEDUR YANG BENAR

Repo private tidak bisa dibaca tanpa kredensial yang hidup. Urutannya:

```
1. CEK dulu apakah repo memang private:
   curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/<owner>/<repo>
   → 404 (padahal repo ada) = PRIVATE, butuh kredensial
   → 200 = publik, TIDAK butuh kredensial (jangan cari-cari token!)

2. Cari token yang ADA di mesin (nama variabel saja, JANGAN cetak nilainya):
   grep -rhio "^[A-Z0-9_]*\(TOKEN\|PAT\|KEY\)[A-Z0-9_]*=" <env files> | sort -u

3. UJI token itu HIDUP atau MATI sebelum dipakai:
   curl -s -H "Authorization: Bearer $T" https://api.github.com/user
   → "Bad credentials" / 401 = MATI (jangan diteruskan ke git)

4. MASIH GAGAL → BERHENTI & MINTA BOS. Jangan coba 5 cara lain.
```

⚠️ **JANGAN PERNAH mencetak nilai token** ke layar, pesan, berkas repo, atau
dokumen. Tulis `<ada, disembunyikan>`. **JANGAN tulis token di dokumen repo** —
harga peristiwanya boleh dicatat, nilainya tidak.

⚠️ **Jangan menyimpulkan "repo tidak ada" dari 404.** 404 di GitHub = bisa
"memang tidak ada" **atau** "private". Bedakan:
```bash
curl -s https://api.github.com/users/<owner>/repos?per_page=100 \
  | python3 -c "import sys,json;[print(r['name'],r['private']) for r in json.load(sys.stdin)]"
```
Repo yang **tidak muncul** di daftar publik + 404 saat diakses langsung = private.

---

## 7. 🧯 JEBAKAN YANG SUDAH TERBUKTI

| # | Jebakan | Kenyataan | Obat |
|---|---|---|---|
| 1 | **Dokumen bilang "sudah ada", kode bilang tidak** | Dokumen = klaim; kode = bukti | Verifikasi tiap [FAKTA] ke `grep`/`ls` sebelum melapor |
| 2 | **Label versi menipu** (`versi: "fase1"` padahal fase lain) | Label di `/api/status` tidak dimiliki fase baru | Uji **endpoint nyata** (harus 404/200), bukan label |
| 3 | **`git fetch` gagal "could not read Username"** → disimpulkan repo hilang | Itu **kredensial** yang kurang, bukan repo hilang | Cek dulu publik/private; jangan ulangi perintah yang sama 3× |
| 4 | **Salinan lokal bersih disimpulkan "belum dikerjakan"** | Lokal bisa ketinggalan branch remote | Laporkan ketiga sumber (remote/lokal/live) terpisah |
| 5 | **Catatan lama menormalkan hal terlarang** | Agen baru membacanya sebagai izin | Tandai `BUKAN PROSEDUR / bukan preseden` secara eksplisit |
| 6 | **Commit message dipercaya sebagai bukti** | Judul bisa tidak sesuai isi | `git show <sha> -- <berkas>` — baca isinya |
| 7 | **Branch `main` ikut dianggap berubah** padahal cuma branch agen | `main` harus dicek sendiri | `git log --oneline origin/main -3` terpisah |
| 8 | **Pagar baru hijau diujinya, tapi buta untuk bentuk data yang dipakai** | Uji hanya menguji satu bentuk kiriman (§4e) | Uji **tiap bentuk** kiriman; periksa field yang dibaca pagar vs yang dikirim pemanggil |
| 9 | **Suntikan mutasi melempar TypeError** → disimpulkan "pagar hiasan" | Tanda tangan fungsi berubah, lambda tidak menerima argumen baru | Tiru tanda tangan (`lambda p, efektif=False`) atau `mock.patch`; **uji 3 keadaan** (§4f) |
| 10 | **"Sudah diperbaiki" tapi bug sama muncul lagi** | Perbaikan ditempel di jalur lain dari tempat bug | Bandingkan titik bug vs titik perbaikan; minta pagar di **payload efektif** (§4g) |
| 11 | **Repo private + token mati → menyimpulkan "belum dikerjakan"** | Bisa jadi memang belum di-push | Sebut 3 sumber (remote/lokal/live) terpisah; minta Bos jadikan publik atau beri PAT baru — **jangan** habiskan waktu mencari token |
| 12 | **SALAH REPO** → melapor "belum di-commit" / "belum sampai ke GitHub" | Project Bos sering ≥2 repo (`eduai-publishing` + `statistik-lab`); fase baru bisa mendarat di repo yang tidak diduga. Terukur 21 Okt 2026: Wulan lapor "Fase 2 tidak ada" padahal `f561b5c` rapi di `eduai-publishing` | `git ls-remote origin` di **SETIAP** repo project, cari sha/message-nya; kalau nama branch tak diberikan → TANYA (§1b) |
| 13 | **Modul + tabel + uji hijau, tapi NOL pemanggil** → "mesin ✅" | Fase fondasi memang begini; tapi kalau dilaporkan "selesai" jadi menyesatkan | Selalu cek impor di `main.py` + rute + `grep -rln` di luar berkasnya (§3b) |
| 14 | **`docker cp` berkas ke container PRODUKSI untuk uji** | Berkas tak terlarang tapi gambar produksi jadi beda dari `Dockerfile` | `.venv` lokal dulu → container uji → prod hanya pilihan terakhir + catat di laporan (§3c) |
| 15 | **Fungsi "bekukan versi" dipanggil dua kali → memundurkan versi yang benar** | `kunci_hasil()` tanpa draf baru tetap menurunkan versi terkunci lama lalu mengunci versi sebelumnya ⇒ narasi membaca ANGKA LAMA. Uji bawaan hijau karena hanya menguji 1× panggil | Uji **idempoten**: panggil 2×, harus `None` + jumlah terkunci tetap 1 (§4h) |
| 16 | **"Salinan dokumen" dibuat SEBELUM diedit, lalu disalin balik** → catatan vonis HILANG | Berkas `.md` cadangan berisi versi lama menimpa versi yang sudah disunting. Ketahuan hanya dari `grep` di clone baru | Cadangan hanya SEBELUM suntingan, bernama `*.bak-<tujuan>`, **jangan pernah** disalin balik. Pakai `git diff` untuk membandingkan (§5b) |
| 17 | **Commit catatan vonis mendarat di branch review, `main` tidak dapat** | Merge dilakukan dari `origin/main` + branch **kode** ⇒ commit catatan (branch lain) tidak terbawa. `main` naik, kode masuk, catatan tidak | `git cherry-pick <sha-catatan>` di branch merge; verifikasi `grep -c "VONIS REVIEW"` di **clone baru** (§5c) |
| 18 | **`git push origin origin/<branch>:refs/heads/x` gagal** `src refspec … does not match any` | `origin/…` bukan nama ref lokal yang bisa di-push | Pakai **sha** atau **nama branch lokal** (§5e) |
| 19 | **Pesan merge berisi daftar fitur padahal baru FONDASI** | `git log` jadi satu-satunya dokumen yang dibaca orang; "Fase 2 merge" terbaca "fitur jalan" | Buka pesan merge dengan peringatan `⚠️ INI FONDASI, BUKAN FITUR JADI` + sebut apa yang belum dipasang (§5d) |
| 20 | **Token dipotong DULU, mesin dipanggil kemudian** → gagal = token hangus | Pola `kembalikan_banyak` **sudah ada** di repo (8× di `ai.py`), jadi rute baru yang tidak memakainya = menyimpang | Bungkus kerja dengan `try/except` + `kembalikan_banyak`; probe dengan memaksa mesin melempar (§4j) |
| 21 | **Uji hijau 13/13 padahal satu MODE tidak pernah diuji** | Kasus uji hanya PLS; jalur SPSS (mayoritas user) **400 di setiap percobaan** karena bentuk field salah | Daftar mode dari `grep '== \'pls\''`, bandingkan dengan mode di uji; coba satu kasus nyata per mode (§4k) |
| 22 | **Uji gagal karena server sebelah tidak hidup** → disimpulkan bug kode | `--host 127.0.0.1` + gateway bridge tak terjangkau ⇒ `ConnectionRefused` menyesatkan | Cari IP host yang **terbukti** tersambung (`socket.create_connection`), uvicorn `--host 0.0.0.0` (§4l) |
| 23 | **Nama variabel saling mengandung** (`Harga` ⊂ `Harga Diskon`) → butir Y masuk daftar X | `startswith(dasar + '_')` bukan batas tegas | Bandingkan **dasar** (`k.rsplit('_',1)[0]`), atau simpan pemetaan saat instrumen dibuat (`defensive-data-shape-parsing` pitfall 12) |
| 24 | **Pemetaan hasil→hipotesis `ketemu=True` tapi angkanya KOSONG** | Cabang `interaksi`/moderasi mengembalikan `b=None, p=None, signifikan=None` padahal mesin punya `delta_r2`/`jenis`/`arah`/`kalimat`. Uji bawaan cuma cek `ketemu` → hijau | Uji **per cabang jenis jalur**, dan bandingkan `b` ke **angka mesin** (lapis 3), bukan cuma `not None` (§4m) |
| 25 | **Satu besaran dua presisi** (`b=0.0496` vs `b=0.049598` dalam satu tabel) | Mesin mengirim angka bulat di satu kunci (`koef`) dan penuh di kunci lain (`kaitan`); pemetaan ambil sumber beda per jalur | Ambil presisi penuh dari **satu sumber**; melanggar aturan \"sumber angka HANYA hasil mesin, jangan dibulatkan\" (§4m) |
| 26 | **Dua nama variabel → dasar kolom SAMA** (`Kualitas Produk` ≡ `Kualitas_Produk`) | Pemetaan nama→kolom tidak injektif ⇒ data dua variabel tertukar diam-diam | Pagar `kolom_tabrakan` saat susun peta + batas tegas pola `<dasar>_<angka>$` (§4n) |
| 27 | **Pagar tabrakan hanya memeriksa dasar SAMA PERSIS** → `Harga 1` vs `Harga` lolos | Mesin membaca variabel = nama sebelum `_` **terakhir**, jadi `Harga_1_1` → `Harga_1` dan `Harga_1` → `Harga`; mesin balas **200** dengan X1 = gabungan 2 variabel | Bandingkan **daftar kolom** hasil `buat_instrumen()`, periksa 3 relasi: sama persis · saling mengawali · dasar+nomor bentrok (§4n) |
| 28 | **`PUT /data` terima `baris` berbentuk OBJEK → `POST /olah-data` 500** (`KeyError: 0`) | Rute tidak memeriksa bentuk tiap elemen; `GET /data` mengembalikan apa adanya ⇒ layar mengirim balik bentuk yang sama | Periksa bentuk **tiap elemen** koleksi di pintu masuk (422), jangan dibiarkan ke mesin (§4o) |
| 29 | **`int('tiga')` → 500 di `/peta` dan `/peta/sahkan`** | Field dari AI/parsing naskah sering bukan angka; `jumlah_butir` sudah dijaga tapi `jumlah_hipotesis` terlewat | Probe `['abc', None, -3, 3.7, '', [], {}]` untuk **semua** field `int()`; sapu ke field sejenis (§4p) |
| 30 | **Probe Wulan memeriksa kunci kontrak LAMA** → lapor "BUG" palsu | `kolom_x`/`kolom_y` sengaja diganti `peran` di ronde sebelumnya; skrip lama masih menuntutnya | Baca tanda tangan fungsi versi **sekarang** sebelum menuduh; regresi + satu area baru tiap ronde (§4q) |
| 31 | **Rute TULIS lengkap, rute BACA tidak ada** → hasil masuk DB, tak bisa dibaca | `POST /olah-data` + `/kunci-hasil` ada, `GET /hasil` tidak ⇒ langkah narasi mustahil. Uji hijau, karena uji hanya memeriksa respons POST | Kelompokkan rute GET vs POST; setiap hasil yang ditulis **wajib** punya pembaca (§4r) |
| 32 | **Data bisa ditulis ke nilai yang tak pernah dibaca kode** | 3 `tahap` disimpan, `olah-data` hardcode `utama` ⇒ data `simulasi` 409 selamanya ("tersimpan sia-sia") | Lacak tiap field yang disimpan → apakah ada kode yang **memakainya selain saat menyimpan** (§4r) |
| 33 | **Fungsi pembangun fitur ada, NOL pemanggil** | `frekuensi_kolom` & `tingkat_pengembalian` (isi BAB IV 4.1) 0 pemanggil ⇒ mesin ditulis, tak disambung | `grep -rn <fn> app/` untuk tiap fungsi publik; nol pemanggil = fitur belum ada walau kodenya ada (§4r) |
| 34 | **Fuzz \"semua fungsi publik\" → 213 \"meledak\"** padahal bukan bug | Fungsi berat-`db`/internal tak tahan `None`, tapi pemanggilnya selalu benar ⇒ salah saring, bisa jadi tuduhan palsu | Saring dulu: hanya fungsi **murni** yang dipanggil **rute** dengan **data user**; akui salah ukur di laporan (§4r) |
| 35 | **Fungsi keadaan ber-`jenis`: `jenis` jadi PARAMETER tapi tidak dipakai di query**, dan rute tidak meneruskannya | Penomoran `nomor` terpisah per jenis, pagar "versi terkunci" membandingkan lintas jenis ⇒ **simulasi dulu → hasil penelitian TIDAK BISA dikunci** (409). Semua uji hijau karena selalu pakai urutan `utama` dulu | Uji **urutan TERBALIK** (jenis "latihan" masuk lebih awal) + `assert 'jenis=' in source` + cek rute meneruskan parameternya (§4s) |
| 36 | **Layar memanggil endpoint yang TIDAK ADA** (`/kunci` vs `/kunci-hasil`, `/olah` vs `/olah-data`, `/pra` vs `/pra-survei`) ⇒ 3 tombol inti **404** | Uji Python tidak menyentuh template. Juga arah sebaliknya: `GET /hasil` + `GET /profil` ada tapi **tak pernah dipanggil layar** ⇒ angka tak tampil | `comm` dua arah antara endpoint di template dan `@router` di rute; keduanya bug (§4t) |
| 37 | **Uji teks laporan hijau padahal prosanya cacat** (`H1: H1:`, `— —`, `p=None` tercetak) | Uji hanya cek `200` + `'signifikan' in teks` — tidak pernah membaca kalimatnya | Uji **teks**: regex label dobel, separator dobel, `None`/`nan`, dan angka teks ⊆ angka mesin (§4u) |
| 38 | 🚨 **Efek tidak langsung tanpa `p` divonis \"hipotesis ditolak\"** | Bootstrap tak menghasilkan `p`; kode memperlakukan `None` sebagai \"tidak signifikan\" ⇒ pernyataan **salah secara statistik** di naskah mahasiswa | `None` ≠ nol ≠ tidak signifikan. Wajib tulis apa adanya (*\"diuji bootstrap, p tidak tersedia\"*) atau minta mesin mengirim nilai bootstrap (§4u) |

| 39 | **Perbaikan terlihat benar, tapi uji anti-regresinya TIDAK BERGIGI** (`'  ' not in _teks.replace('  ', '  ', 0)`) | Baris uji ditambahkan bersama perbaikannya — kelihatan menutup, tapi ekspresinya selalu `True` (replace dengan hitungan 0 = tanpa perubahan) ⇒ bug bisa kembali tanpa tertangkap. Terukur 21 Okt 2026 (spasi dobel narasi) | Jangan percaya baris uji baru hanya karena ADA. Untuk tiap asersi baru ronde ini: baca ekspresinya, lalu **suntik balik bug-nya** dan pastikan asersi itu MERAH (§4f). Kalau tetap hijau → tulis sendiri probe-nya (§4u) |
| 41 | **Branch fase baru bercabang SEBELUM merge fase sebelumnya** → `git diff main..branch` menunjukkan dokumen **−118 baris**, isinya **§15c + §15d (vonis review)** | Branch dibuat dari `cb36678` (akhir Fase 3), sedangkan merge `3ca2f2d` + vonis `ef402e2` belum ada di induknya. Merge apa adanya = jejak review 9 ronde **hilang dari `main`**, dan tak ada uji yang menangkap | Cek `git merge-base` + `git log BASE..origin/main` SEBELUM baca kode; baris `-` yang menghapus VONIS = tanda bahaya; `git merge origin/main --no-commit` lalu `grep -c` kedua vonis wajib ≥1 (§4t-3) |
| 42 | **Probe Wulan melapor 500/422 padahal kiriman sendiri salah bentuk** — 3× dalam satu sesi (peta `variabel` vs `fokus`, segmen `tema/kutipan` vs `teks/informan/teknik/jenis`, `SimpleNamespace` tanpa `.email`) | Semua disangka bug kode; kenyataannya Wulan mengarang bentuk data & objek tiruan yang tidak lengkap | Sebelum menuduh: baca bentuk dari **uji bawaan**, signature fungsi, dan objek yang di-inject ke `dependency_overrides` (pakai `User` asli dari DB) (§4v) |
| 43 | **Saldo uji diset lewat `u.token_saldo = 500`** → tetap **403 BUTUH_UPGRADE**, lalu sempat dicurigai pagar token rusak | Kolom itu **tidak ada** di tabel `User`; saldo dibaca dari buku besar `SaldoToken` via `kuota._saldo.sisa()`. `except: pass` menyembunyikan galatnya | Isi saldo lewat jalur resmi `kuota._saldo.masuk(db, u, 500, 'uji', ...)`; jangan mengarang kolom user (§4v) |
| 44 | **Prosa 4.3 menukar istilah: "satu jenis informan"** padahal 3 informan & 1 teknik | Angka mesin `jumlah_informan=3, jumlah_teknik=1` diterjemahkan ke kalimat dengan kata yang salah ⇒ **salah metodologi** di naskah kualitatif | Uji pasangan **(angka, kata)**: `jumlah_teknik==1` → prosa wajib menyebut **teknik**, bukan informan (§4w) |
| 46 | **AI balas HTTP 200 tapi `content` KOSONG** → aplikasi balas 502, user lihat `HTTP 502</div>` | `OUT 0` di log router. Model reasoning menghabiskan `max_tokens` untuk `reasoning_content` sebelum menulis `content` (`finish_reason=length`). Terukur: `max_tokens=200` → kosong; `enable_thinking:False` → terisi | Pasang `enable_thinking:False` di **payload utama + coba-ulang**; baca `finish_reason`; pesan galat sebut SEBAB (bukan kode HTTP); layar cek `content-type` sebelum `r.json()` (§4x-1) |
| 47 | **Probe melapor "8/8 KOSONG" padahal semua 200** | `json.loads(mentah)` utuh pada balasan berekor `data: [DONE]` ⇒ `JSONDecodeError` ⇒ dicatat kosong. **Tanda: `finish=None` di semua percobaan** | `json.JSONDecoder().raw_decode()` dari `{` pertama. `finish=None` massal = alat ukurnya salah, bukan API-nya (§4x-1) |
| 48 | **Menyimpulkan "mount Docker tidak sinkron"** karena berkas host `1` vs container `0` | Nilainya memang berbeda pada jam itu — `gerbang_baca_judul.py` mematikan saklar AI saat diuji lalu menyalakannya lagi. Bukan mount rusak | Pastikan dulu nilai yang dibandingkan memang **seharusnya** sama; periksa gerbang yang menyentuh berkas itu, jangan langsung menuduh prasarana (§4x-1) |

| 49 | **`git push` ditolak `! [rejected] ... (fetch first)`** → sempat dibaca "repo rusak / kredensial mati" | Artinya **remote lebih baru**: ada fase lain sudah di-push dan belum pernah dilihat lokal. Terukur 21 Okt 2026: 7 commit Fase 1 jembatan (`629c4ab`) sudah di remote, lokal belum | `git fetch` **tanpa pull** → petakan dua arah (`HEAD..origin` vs `origin..HEAD`) → cek hunk beririsan → **branch cadangan** → `git merge` → **verifikasi DUA ARAH** (`grep -c` penanda kode sendiri MASIH ada + kode remote masuk) (§5e-2) |
| 50 | **`git push` gagal `could not read Username for github.com`** di repo yang belum punya `credential.helper` | Bukan token mati — repo itu memang belum diberi helper. Repo lain di project sama sudah punya | Pinjam helper yang terbukti: `git -c credential.helper="store --file=/opt/data/vault/.git-credentials-<nama>" push ...` — hanya untuk owner sama; jangan cetak isi vault, jangan simpan token baru (§5e-2) |
| 51 | **Melapor "sudah merge/push" dari `git log` repo KERJA** | `git log` lokal menampilkan commit yang **belum** di-push. Terukur: Bos bertanya *"sudah kamu push?"* dan jawabannya **belum**, walau commit-nya terlihat rapi | Bukti sah = `git fetch` lalu `git branch -r --contains <sha>` per commit; sebut hasil per-sha, bukan satu kalimat "sudah" (§5e-2, §5c) |

---

## 8. 📌 PRINSIP PUTUSAN

1. **Verifikasi dulu, percaya kemudian.** Klaim tanpa bukti kode = belum terbukti.
2. **Cari bug, bukan cuma "jalan".** Yang paling berbahaya justru yang **tampak
   selesai** (dokumen rapi, +45 baris, tanpa kode).
3. **Yang BELUM diputuskan harus ditandai [USULAN]** — jangan dibiarkan terbaca
   sebagai keputusan. Kalau agen lain menandainya benar, itu **nilai plus**.
4. **Jangan menambah lapisan.** Kalau fitur bisa ditumpangkan ke mekanisme yang
   sudah ada (mis. pola versioning, dompet token, editor), **pakai itu** — pola
   kedua = bug menunggu.
5. **Lapor jujur soal yang belum.** Bos menolak kata "sempurna" tanpa bukti;
   sebaliknya laporan yang menyebut celah **menambah** kepercayaan.

---

## 🔗 Terkait

- `requesting-code-review` — pipeline review **perubahan sendiri** sebelum commit.
  Skill ini untuk **branch ORANG LAIN**. Jangan digabung.
- `github-repo-research` — riset repo publik + verifikasi star/nama mirip.
- `eduai-publishing` — aturan batas proyek & pagar repo EduAi.
- `verifikasi-klaim-kapabilitas-alat-baru` — pola umum "TIDAK ADA adalah klaim".
- `architecture-discussion-and-planning` — mode diskusi rancangan (catat saja).
- `akar-bukan-tambalan` — kalau menemukan tambalan, cari akarnya.
- `test-gate-design` — gerbang yang tak bisa gagal = hiasan (§4d memakai prinsip ini).

## 🧰 Berkas pendukung

- `scripts/probe_teks_narasi.py` — **probe TEKS PROSA** (narasi bab, laporan,
  ringkasan). Salin ke repo salinan, sesuaikan `KONFIG` + `siapkan_kasus()`,
  jalankan `python3 probe_teks_narasi.py`. 6 kelas: label dobel (`H1: H1:`) ·
  separator dobel (`— —`) · literal `None`/`nan` tercetak · **angka desimal prosa
  ⊆ angka mesin** (sisir `hasil` rekursif) · **nilai tanpa `p` tidak divonis** ·
  label yang diminta benar-benar muncul. **Sejak ronde 9 (21 Okt 2026) juga
  memeriksa SPASI DOBEL** di dalam baris + pasangan `penanda_dua_keadaan`
  (mis. `'] melewati nol'` vs `']  melewati'`) — cacat khas f-string bersyarat
  `{'tidak' if sig else ''} kata`. Menangkap bug terukur: efek tidak
  langsung tanpa `p` divonis *"hipotesis ditolak"* (§4u, §4t-2). EXIT 1 kalau ada temuan.
- `scripts/probe_layar_vs_rute.py` — **probe LAYAR ↔ RUTE, dua arah.** Salin ke
  root repo salinan, jalankan `python3 probe_layar_vs_rute.py --kombinasi <modul>`.
  Menangkap dua kelas bug yang **tidak bisa** ditangkap uji Python: (A) template
  memanggil endpoint yang tidak terdaftar (tombol 404 — terukur: `/kunci` vs
  `/kunci-hasil`, `/olah` vs `/olah-data`, `/pra` vs `/pra-survei`) dan
  (B) rute terdaftar tapi tak pernah dipanggil layar (fitur tak tampil —
  terukur: `GET /hasil`, `GET /profil`). EXIT 1 kalau ada temuan (§4t).
- `scripts/probe_kunci_ber_jenis.py` — **probe fungsi KEADAAN ber-kolom-pembeda**
  (`jenis`/`mode`/`tahap`/`kategori`). 3 lapis: (1) apakah kolom pembeda muncul
  di **badan query** (bukan cuma tanda tangan) · (2) apakah **rute meneruskan**
  parameternya · (3) instruksi uji **urutan TERBALIK** (nilai "latihan" masuk
  lebih dulu). Menangkap bug terukur: `kunci_hasil` ber-`jenis` tapi query tak
  memakainya ⇒ **simulasi dulu → hasil penelitian tidak bisa dikunci** (§4s).

- `scripts/probe_rute_berpagar.py` — **probe tandingan untuk RUTE BERPAGAR.**
  Salin ke repo salinan, sesuaikan `KONFIG`, jalankan
  `.venv/bin/python probe_rute_berpagar.py`. 5 kelas: pagar login · kebocoran
  antar-user · **urutan potong token (mesin dipaksa gagal → token wajib kembali)**
  · pagar masukan (harus pesan, bukan 500) · mode yang tidak muncul di uji.
  EXIT 1 kalau ada temuan.
- `scripts/probe_tandingan.py` — **probe tandingan siap pakai.** Salin ke dalam
  repo salinan, sesuaikan `KONFIG` (endpoint, env kunci, header), jalankan
  `.venv/bin/python probe_tandingan.py`. Menguji 5 kelas: autentikasi aneh ·
  bentuk data menyimpang · data mustahil · kebocoran peran · determinisme &
  tanpa-simpan. Keluar EXIT 1 kalau ada temuan, supaya bisa dipakai di gerbang.
- `scripts/uji_gigi_pagar_3_keadaan.py` — **buktikan ujinya bergigi, bukan cuma
  hijau.** Salin ke dalam repo, sesuaikan `KONFIG` + `jalankan_kasus()`, jalankan
  `.venv/bin/python uji_gigi_pagar_3_keadaan.py`. Tiga keadaan: pagar asli (harus
  400) · pagar dimatikan (harus 200) · pagar **buta untuk satu bentuk** (harus
  200 di bentuk itu, 400 di bentuk lain). Keadaan ke-3 yang membuktikan uji
  menangkap bug spesifik (§4f).
- `scripts/probe_pemetaan_hipotesis.py` — **probe untuk modul ADAPTER/penerjemah**
  (hasil mesin → istilah user: hipotesis H1..Hn, label, jalur). Uji **3 lapis**:
  `ketemu` · angka terisi · **angka SAMA PERSIS dengan mesin**. Menangkap dua bug
  yang lolos uji bawaan: cabang `interaksi`/moderasi yang `b=None` padahal mesin
  punya `delta_r2`, dan **presisi bercampur** (`0.0496` vs `0.049598`) dalam satu
  tabel. EXIT 1 kalau ada temuan (§4m).
- `scripts/probe_rute_koleksi.py` — **probe RUTE PENERIMA KOLEKSI + field `int()`.**
  Salin ke root repo salinan, sesuaikan `KONFIG`, jalankan
  `.venv/bin/python probe_rute_koleksi.py`. 5 kelas: baris berbentuk **objek**
  (harus 4xx, bukan 500 di rute pasca) · baris **campur** · sel sampah
  (None/string) · field `int()` menerima `['abc', None, -3, 3.7, '', [], {}]` ·
  `id` entitas aneh. Menangkap dua 500 yang lolos uji bawaan Fase 3
  (`KeyError: 0` di `baris_ke_objek`, `ValueError` di `jumlah_hipotesis`).
  EXIT 1 kalau ada temuan (§4o/§4p).
- `references/kwitansi-review-bab4-fase3-21okt2026.md` — **lanjutan**: peta
  repo/branch akhir sesi · urutan commit Fase 3 (`81ad1d2`→`24b9349`) + cara
  menentukan *"bug fase mana"* · bug per ronde (ronde 1–4) · **audit global
  lintas fase: 4 lubang pemasangan** (`GET /hasil` tidak ada, `tahap=simulasi`
  tak bisa diolah, 2 fungsi 0 pemanggil, nol template) · daftar yang sudah
  terbukti BENAR (jangan diuji ulang) · **jebakan lingkungan uji** (uv pip
  non-zero tanpa pesan, `--host 127.0.0.1` tak terjangkau container,
  `raise_server_exceptions=True` untuk mengejar 500, peta wajib `bukti`).
- `references/kwitansi-review-bab4-21okt2026.md` — detail sesi + kwitansi angka
  (review dokumen, review kode fase 1 jembatan BAB IV, **merge Fase 1 → master
  dengan bukti clone-baru**, **review Fase 2 EduAi `f561b5c`: 6 bug + kasus
  "salah repo"**, **putaran 4 `5eeeff0`: 5 bug tuntas + vonis LULUS fondasi,
  termasuk dua kesalahan Wulan saat catat/merge yang melahirkan §5b–§5c**,
  **Fase 3 `81ad1d2`: 13 rute terpasang, tapi `kolom_y` list mematikan seluruh
  mode SPSS — plus jebakan jaringan uji container → server sebelah**,
  **putaran 5 `8f2a39e`: 5 bug tuntas; putaran 6 `93ad415`: 3 bug tuntas tapi
  jalur `interaksi`/moderasi `b=None` + presisi angka bercampur → §4m/§4n**,
  **putaran 7: 2 bug tuntas + uji 3-keadaan bergigi → 0 bug, lalu pencarian
  tambahan menemukan 5 bug baru (2×500): `baris` objek → `KeyError: 0`,
  `jumlah_hipotesis='tiga'` → `ValueError`, `kolom_tabrakan` buta untuk dasar
  saling mengawali → §4o/§4p/§4q`).
- `references/kwitansi-review-bab4-fase4-21okt2026.md` — **sesi Fase 4**:
  eksekusi catat+merge Fase 3 (`ef402e2`, konflik §15c→§15d), peta branch saat
  Fase 4 muncul, isi Fase 4 kedua repo (`59df57b` + `0c71143`), hasil review
  (8 rute kebocoran bersih, gerbang campuran keras, **1 bug istilah
  informan/teknik**), **4 gagal palsu Wulan sendiri**, dan perintah lingkungan
  uji yang terbukti (§4t-3, §4v, §4w).
- `references/kwitansi-push-ditolak-dan-merge-remote-21okt2026.md` —
  **ekor sesi**: Bos tanya *"sudah kamu push?"* → ternyata **belum**; push
  ditolak `fetch first` karena remote sudah punya Fase 1 jembatan; cara memetakan
  tabrakan **sebelum** merge (hunk beririsan?), verifikasi **dua arah** sesudah
  merge, `httpx` yang dibutuhkan uji remote, `sot.py` menolak dokumen tak
  terdaftar, dan bukti per-commit `git branch -r --contains` (§5e-2).
- `references/kwitansi-review-bab4-fase3-r8-r9-dan-merge-21okt2026.md` —
  **penutup rantai**: ronde 8 (4 cacat prosa: label dobel, `— —`, `None`
  tercetak, dan **vonis \"ditolak\" untuk `p` yang tidak ada** → CI bootstrap),
  ronde 9 (spasi dobel + **jebakan uji anti-regresi yang tidak bergigi**),
  vonis **LULUS**, dan **eksekusi catat+merge** ke `main` (`ef402e2`):
  §15c/§15d, konflik cherry-pick dokumen, verifikasi clone baru, dan
  ~~gerbang merah~~ yang ternyata **lingkungan uji**, bukan kerusakan `main`.

## ⚡ Perintah preflight (jalankan sebelum baca kode)
<!-- preflight -->

```bash
# 0. WAJIB: fetch dulu — clone basi = sumber tuduhan palsu (lihat references/)
git fetch origin --prune
# 1. Induk branch + commit main yang ketinggalan  → BUG PALING BERBAHAYA
BASE=$(git merge-base origin/main HEAD)
git log --oneline "$BASE" -1
git log --oneline "$BASE"..origin/main          # kalau ada isi = branch KETINGGALAN
git diff --diff-filter=D --name-only origin/main HEAD   # berkas yg "terhapus"

# 2. Apakah benar-benar ada kode, atau dokumen saja
git diff --stat origin/main HEAD | tail -3
```
