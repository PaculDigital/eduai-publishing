# Kwitansi Review BAB IV — 21 Okt 2026 (lanjutan: Fase 3 ronde 5–8 + audit global)

Lanjutan dari `kwitansi-review-bab4-21okt2026.md`. Bagian ini mencatat ronde
setelah Fase 3 masuk `eduai-publishing` branch `agen/wulan/bab4-statistik-backend`.

## Peta repo & branch (akhir sesi)

| Repo | Branch | Commit | Isi |
|---|---|---|---|
| `statistik-lab` | `master` | `629c4ab` | Fase 1 jembatan (LULUS, sudah merge) |
| `eduai-publishing` | `main` | `3810854` | Fase 2 fondasi (LULUS, merge + catatan §15c) |
| `eduai-publishing` | `agen/wulan/bab4-statistik-backend` | `440160b` | Fase 3 (belum merge; layar HTML + narasi + simulasi nyata) |

## Urutan commit Fase 3 (untuk melacak asal bug)

```
81ad1d2  Fase 3 inti: 11→12 rute /api/bab4, instrumen, data, pra-survei, olah, kunci
8f2a39e  Ronde 1: payload SPSS bentuk peran, refund token, pola kolom tegas, jumlah_butir
93ad415  Ronde 2: peta_hipotesis H1..Hn tersimpan, tolak tabrakan nama kolom
281c074  Ronde 3: hipotesis moderasi diisi (b/c/d), presisi penuh untuk jalur langsung
24b9349  Ronde 4: normalisasi baris objek, validasi sel angka, int() aman, bentrok awalan, kartu tahan bentuk
702ab37  Ronde 5: GET /hasil, olah tahap simulasi, GET /profil 4.1, payload kosong ditolak
b154820  Ronde 6: simulasi nyata via mesin BUAT DATA, narasi dari hasil terkunci, layar bab4.html
440160b  Bersih-bersih: buang variabel tak terpakai
```

**Cara menentukan "bug fase mana" (dipakai saat Bos bertanya):**
```bash
git log --oneline -S "def <fungsi>" --reverse <main>..<branch> -- app/<modul>.py
```
Terukur: `baris_ke_objek`, `buat_instrumen`, `susun_payload_hitung`,
`kartu_kesehatan`, dan rute `PUT /data` **semua lahir di `81ad1d2`** (Fase 3);
`periksa_peta` lahir di `f561b5c` (Fase 2) tapi pagar `kolom_tabrakan` ditambah
di Fase 3. Jawaban yang diterima: *"ini utang Fase 3, bukan regresi; `main`
belum punya `bab4.py` sama sekali sehingga produksi tidak terpengaruh."*

## Bug per ronde (semua TERBUKTI dengan eksekusi)

### Ronde 1 (`8f2a39e`) — vonis: belum boleh merge
1. **SPSS selalu gagal** — `kolom_y` dikirim sebagai **daftar** padahal kontrak
   minta satu nama kolom ⇒ mesin 400 di setiap percobaan. Uji bawaan cuma PLS.
2. **Token hangus** — potong dulu, mesin dipanggil kemudian; mesin mati ⇒ 502 +
   token terpotong (`kembalikan_banyak` sudah ada 8× di `ai.py`).
3. **Nama saling mengandung** — `Harga` vs `Harga Diskon` ⇒ butir Y masuk X.
4. `jumlah_butir = -3` → 0 kolom; `'abc'` → ValueError.

### Ronde 2 (`93ad415`) — 2 bug baru
1. `peta['jalur']` diabaikan ⇒ hasil mediasi tanpa penanda hipotesis ⇒ narasi
   tak bisa menulis "H3 ditolak".
2. `_nama_kolom` masih bisa menyatukan dua nama (`Kualitas Produk` ≡ `Kualitas_Produk`).

### Ronde 3 (`281c074`) — 2 bug baru
1. Jalur `interaksi`/moderasi: `b/p/signifikan = None` padahal mesin punya
   `delta_r2`/`jenis`/`arah`/`kalimat` ⇒ semua penelitian moderasi H-nya kosong.
2. Presisi bercampur: `koef` 4 desimal vs `kaitan` penuh ⇒ satu tabel memuat
   `b=0.0496` dan `b=0.049598`.

### Ronde 4 (`24b9349`) — 5 bug, 2 di antaranya HTTP 500
1. `PUT /data` menerima `baris` berbentuk **objek** ⇒ `POST /olah-data` **500**
   (`KeyError: 0` di `baris_ke_objek`). Pasti kejadian begitu layar disambung.
2. `jumlah_hipotesis='tiga'` ⇒ **500** di `/peta` dan `/peta/sahkan`.
3. Sel sampah (`None`/`"abc"`) diterima "tersimpan" ⇒ hasil hitung beda dari
   yang dilihat user.
4. `kolom_tabrakan` **buta** untuk dasar saling mengawali: `Harga 1` vs `Harga`
   ⇒ mesin 200 dengan `prediktor:['X1']` = gabungan 2 variabel, tanpa peringatan.
5. `kartu_kesehatan` meledak pada `variabel` str / `butir` dict.

Hasil akhir: uji bawaan **37 asersi LULUS**, 5 bug tuntas, 0 HTTP 500.

### Ronde 5 (`702ab37`) — 4 lubang audit global DITUTUP, tapi lahir 1 bug halus

Keempat temuan audit global di bawah diperbaiki: `GET /hasil` (+`?versi=`,
`?jenis=`), `olah-data` menerima `tahap=simulasi` (tarif 0, jenis hasil
`simulasi`), `GET /profil` (frekuensi + tingkat pengembalian), payload kosong
ditolak `ValueError`. Uji bawaan 37 → **46 asersi**.

**BUG BARU yang lolos semua uji bawaan** — `kunci_hasil` ber-`jenis`:

```
Urutan A (dipakai semua uji): olah utama v1 → kunci → 200 ✅
Urutan B (yang merusak):      olah simulasi v1 → kunci → 200 (SIMULASI TERKUNCI)
                              olah utama v1    → kunci → 409 "tidak ada hasil baru"
```

Sebab: `kunci_hasil(db, user_id, file_id, jenis='olah_data')` punya parameter
`jenis`, tapi **query di dalamnya tidak memakainya**, dan **rute tidak
meneruskannya**. `nomor` per jenis terpisah (keduanya mulai 1) ⇒ pagar "versi
terkunci" membandingkan lintas jenis.

Akibat nyata: peneliti yang **latihan dulu** mengunci hasil latihan, lalu hasil
penelitiannya **tidak pernah bisa dikunci** ⇒ narasi membaca angka latihan.

### Ronde 6 (`440160b`) — bug `jenis` TUNTAS + BERGIGI, tapi layar punya 3 cacat

Perbaikan: filter `jenis` ditambahkan di kedua query; rute tetap default
`olah_data` ⇒ simulasi tidak bisa dikunci. Uji bergigi: bug lama disuntik balik
(hapus filter `jenis`) → kunci simulasi jadi **200** ⇒ uji menangkap.

Commit ini juga menambah **layar** `app/templates/bab4.html` (+158), narasi
(`app/bab4_narasi.py` +125, tarif 30/5), `buat_data_simulasi` di jembatan, dan
`GET /data/unduh.csv`. Total rute **15**.

**3 cacat sambungan layar (temuan Wulan):**

| Dipanggil layar | Rute sebenarnya | Hasil |
|---|---|---|
| `/api/bab4/kunci` | `/api/bab4/kunci-hasil` | ❌ 404 |
| `/api/bab4/olah` | `/api/bab4/olah-data` | ❌ 404 |
| `/api/bab4/pra` | `/api/bab4/pra-survei` | ❌ 404 |
| `GET /api/bab4/hasil` (ada) | **tak pernah dipanggil layar** | angka tak tampil |
| `GET /api/bab4/profil` (ada) | **tak pernah dipanggil layar** | 4.1 tak tampil |

⇒ Tiga tombol inti (Olah, Kunci, Pra-Survei) mati; angka hasil & profil tidak
pernah terlihat user. **Uji Python tidak menyentuh template** — ini kelas bug
yang hanya tertangkap dengan membandingkan `grep endpoint` di template vs
`grep @router` di rute (dua arah).

**Yang sudah benar di ronde ini** (jangan diuji ulang): narasi tanpa kunci
hasil → 409 *"narasi hanya lahir dari angka yang sudah dikunci"* · `/bab4`
terdaftar di `main.py` · `buat_data_simulasi` ada di jembatan · `PUT
/narasi/teks`, `GET /data/unduh.csv`, `POST /simulasi/buat` terdaftar.

## Ronde 7 (`440160b` → perbaikan endpoint) — 3 cacat LAYAR TUNTAS, lahir 4 cacat PROSA

Perbaikan ronde 6: nama endpoint di `bab4.html` dibetulkan (`kunci` →
`kunci-hasil`, `olah` → `olah-data`, `pra` → `pra-survei`), layar sekarang
memanggil `GET /hasil` dan `GET /profil`. Agen juga menambahkan **gerbang
kontrak layar↔rute** di dalam `uji_bab4_fase3_sisa.py` (3 asersi: semua URL
layar terdaftar · layar memanggil `/hasil` · layar memanggil `/profil`).

⚠️ **Jebakan saat memeriksa probe sendiri:** Wulan sempat melaporkan *"13
endpoint YATIM"* — **salah ukur**. `r.path` pada router Starlette **sudah memuat
prefix** (`/api/bab4/...`), sementara probe menempelkan prefix lagi
(`'/api/bab4' + r.path`) ⇒ semua tampak yatim. Cara benar: bandingkan apa adanya
atau pakai `u == t or u.startswith(t) or t.startswith(u)`.

**Fitur baru ronde ini juga terverifikasi (Wulan uji sendiri):**

| Cek | Hasil |
|---|---|
| Pintu simulasi `POST /api/jembatan/simulasi` (repo `statistik-lab` `06cf13d`, branch belum merge ke `master`) | ✅ `uji_simulasi_jembatan.py` **5/5**; kolom **SAMA PERSIS** template instrumen; semua nilai Likert 1–5; `model` tak dikenal → 400; tanpa kunci → 401 |
| Narasi: tarif pertama | ✅ **30**, dipotong tepat 30 |
| Narasi: buat ulang | ✅ **5** |
| Sunting manual `PUT /narasi/teks` | ✅ **0 token**, berversi |
| `/bab4/{id}` layar tampil | ✅ 200, ada *Data Lapangan* & *Narasi*; berkas user lain → 404 |
| Narasi sebelum Kunci Hasil | ✅ 409 |

⚠️ **Catatan lingkungan:** pada sesi ini 9router membalas **401 `API key
required for remote API access`** sehingga narasi jatuh ke fallback tokenharbor
(`glm-5.3-flash`). Itu **kredensial**, bukan bug narasi — dan jalur mundur
deterministik tetap menghasilkan narasi. **Jangan laporkan sebagai bug kode.**

### 🐛 4 cacat PROSA di `bab4_narasi.susun_draf` (uji bawaan LULUS)

Uji bawaan hanya memeriksa `200` + `'signifikan' in teks`. Teks yang benar-benar
keluar:

```
- H3: pengaruh Harga terhadap Keputusan sebesar 0.0065 dengan nilai
  signifikansi — — hipotesis ditolak.

- H1: H1: b=-0.043379, p=0.605672 → tidak signifikan
- H3: H3: b=0.006458, p=None → tidak signifikan
```

| # | Cacat | Akar |
|---|---|---|
| 1 | **label dobel** `H1: H1:` | `susun_draf` menambah label padahal `ringkas` dari mesin sudah memuatnya |
| 2 | **`— —` dobel** | nilai kosong diformat dua kali (dua lapis) |
| 3 | 🚨 **vonis "ditolak" untuk `p` yang TIDAK ADA** | efek tidak langsung (`tidak_langsung`) dihitung bootstrap ⇒ mesin tidak mengirim `p`; kode memperlakukan `None` sebagai "tidak signifikan" lalu menulis **"hipotesis ditolak"** — **salah secara statistik**, dan pembimbing akan menanyakan p-value-nya |
| 4 | **`p=None` bocor ke teks** | `str(None)` ikut tercetak |

⇒ Probe baru: `scripts/probe_teks_narasi.py` (6 kelas). Prinsipnya: **prosa yang
salah tetap `200`** — uji status HTTP tidak pernah membacanya.

⚠️ **Salah ukur Wulan yang lain:** sempat menuduh *"angka `0.0119` tidak ada di
mesin"* — ternyata itu **R²** (`hasil['r2'] = 0.0119`). Sebelum menuduh angka
karangan, sisir **seluruh** `hasil` secara rekursif (termasuk `r2`, `r2_adj`,
`kaitan.mediasi[*].a.b`, dst.).

## Audit global lintas fase (`_g1.py`–`_g3.py`) — 4 lubang PEMASANGAN

| # | Temuan | Bukti |
|---|---|---|
| 1 | **`GET /hasil` TIDAK ADA** | 12 rute: POST olah-data/pra-survei/kunci-hasil ada, tapi tak ada GET untuk membaca hasil ⇒ narasi BAB IV mustahil |
| 2 | **Data `tahap=simulasi` tak bisa diolah** | tersimpan 3 tahap, `olah-data` hardcode `utama` ⇒ 409 "Data tahap utama masih kosong" |
| 3 | **`frekuensi_kolom` & `tingkat_pengembalian` 0 pemanggil** | isi BAB IV 4.1, mesin ditulis tapi tak disambung |
| 4 | **Nol template** | `grep -rln bab4 app/templates/` kosong ⇒ 12 rute tanpa satu halaman |
| 5 | `susun_payload_hitung` tetap kirim `peran: {}` saat peran hilang | pagar hulu sudah menolak, jadi berlapis rendah |

## Yang terbukti BENAR (jangan diuji ulang tiap ronde)

- `periksa_peta` tahan 9 bentuk aneh (None/list/str/indikator str/bukti int)
- `POST /peta` 9 bentuk aneh → **nol 500**
- Klien jembatan: payload kosong/None/baris kosong/peran kosong → **400 rapi**
- Rantai peta→instrumen→data→olah→kunci → 200; H1/H2/H3 angka = mesin
- Versi 1→2→3→4 tanpa bolong; kunci = versi terakhir; kunci kedua 409
- Tarif: generate 1–4 = 0 token, ke-5+ = 5 token; potong **tepat 5**, tidak dobel
- 6 rute kebocoran antar-user → 404 semua
- `peta_hipotesis` ikut terkunci
- Variabel tanpa peran ditolak (`peran_tak_dikenal`)

## Jebakan lingkungan uji (terukur, jangan diulang)

- `uv pip install --python .venv/bin/python uvicorn` bisa keluar non-zero tanpa
  pesan berguna; `VIRTUAL_ENV=.venv uv pip install` juga. Yang berhasil:
  `python3 -c "import subprocess; subprocess.run(['uv','pip','install','--python','.venv/bin/python','uvicorn'], capture_output=True)"` — lalu baca stdout/stderr.
- uvicorn `--host 127.0.0.1` ⇒ container **tidak bisa** menjangkau
  (`ConnectionRefused`); `172.17.0.1` juga **tidak selalu**. Yang berhasil:
  `--host 0.0.0.0` + **IP host di antarmuka docker** (mis. `172.17.0.11`),
  dibuktikan dulu dengan `socket.create_connection`.
- `eduai-app` tidak punya `numpy`; uji yang butuh numpy dijalankan di container
  uji, atau numpy dipasang di container itu (bukan produksi).
- `TestClient(..., raise_server_exceptions=True)` **wajib** saat mengejar 500:
  dengan `False` yang terlihat hanya "500 Internal Server Error", tanpa traceback.
- Peta harus punya `bukti` per variabel, kalau tidak `sahkan` → 422 `tanpa_bukti`
  dan semua langkah berikutnya 409 (jangan salahira sebagai bug).
