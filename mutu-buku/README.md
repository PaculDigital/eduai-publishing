# 🏆 MUTU BUKU — cara kerja agen kolaborasi

> 📌 **MULAI DARI SINI:** **`SOT-INDUK.md`** — peta mana yang BENAR,
> mana yang sudah DIBUANG. Berkas ini hanya menjelaskan **cara kerja review**.

> **Kenapa folder ini ada:** Bos minta *"upload juga tentang mutu buku, bagaimana
> agen Kolaborasi delegation yang kemarin untuk membuat buku yang bermutu, saya
> mau lihat skill-nya atau cara kerjanya."* (22 Okt 2026)
>
> Isi: **seluruh skill** `agen-kolaborator-review-gate` — 16 referensi + 8 skrip
> uji — apa adanya, tanpa dipotong.

---

## 1. Jawaban singkat: bagaimana buku jadi bermutu?

**Bukan karena satu AI pintar. Karena ADA YANG MEMERIKSA.**

```
        AGEN LAIN                    WULAN (penjaga main)
   ┌─────────────────┐         ┌──────────────────────────┐
   │ koding di       │         │ 1. cek klaim → kode      │
   │ branch sendiri  │  ────▶  │ 2. cari bug, UJI SENDIRI │
   │                 │         │ 3. vonis: LULUS / TOLAK  │
   └─────────────────┘         │ 4. baru merge ke main    │
                               └──────────────────────────┘
```

**Kunci mutunya:** agen lain **tidak boleh** menyentuh `main`. Semua lewat
gerbang. Kalau gagal, **ditolak dengan alasan tertulis** — bukan diperbaiki
diam-diam.

> **Peran yang diberikan Bos (verbatim 21 Okt 2026):**
> *"Semua kendali main adalah kamu, agen lain hanya buat koding di branch nya
> sendiri dan Kamu cek saja dan cari bug, sebelum bisa diintegrasikan ke main."*

---

## 2. Alur review — 6 langkah, jangan dibalik

| # | Langkah | Yang dilakukan |
|---|---|---|
| **0** | **JANGAN KODING** saat menerima rancangan | baca dulu, pahami maksud |
| **1** | **AMBIL SUMBER SEGAR** | `git fetch` dulu — **jangan** percaya clone basi |
| **2** | **BACA KODE, BUKAN KLAIM** | klaim "54 asersi" → hitung sendiri |
| **3** | **JALANKAN SENDIRI** | gerbang + uji bergigi di worktree bersih |
| **4** | **UJI YANG BELUM DIUJI** | cari celah yang agen tidak uji |
| **5** | **VONIS + CATAT + MERGE** | LULUS atau TOLAK, dengan alasan |

### Yang WAJIB di setiap review

| Hal | Kenapa |
|---|---|
| `git fetch` dulu | clone basi = salah tuduh |
| Worktree bersih (`git worktree add`) | jangan uji di tempat kerja agen |
| Jalankan **uji bergigi** | buktikan gerbang BISA gagal |
| Uji kasus **RUSAK** | buktikan generator menolak |
| Cek **buku baik tidak tertimpa** | uji yang agen sering lupa |
| Bandingkan **MD5** berkas asli | pastikan tidak diubah diam-diam |

---

## 3. Contoh nyata — 4 ronde review generator buku

Ini **riwayat sungguhan** 22 Okt 2026. Perhatikan: tiap ronde menemukan
sesuatu yang ronde sebelumnya lewat.

| Ronde | Commit | Asersi | Yang Wulan temukan |
|---|---|---|---|
| 1 | `34c02ad` | 48 | ✅ lulus · ⚠️ 2 celah pagar input |
| 2 | `69a64a6` | 54 | ✅ tabel+gambar jalan · 🔴 2 celah **masih bocor** |
| 3 | `82a99ee` | 54 | ✅ 2 celah **tertutup** + buku baik tidak tertimpa |
| 4 | `f1da9bf` | **57** | ✅ DAFTAR PUSTAKA + titik pemimpin → **MERGE** |

**Pelajaran:** ronde 2 Wulan **ulangi** uji yang sama dari ronde 1. Kalau tidak
diulang, celah yang belum diperbaiki akan lolos.

---

## 4. 2 celah nyata yang Wulan temukan (bukan teori)

### Celah 1 — berkas rusak tetap ditulis ke disk

```
input: bab = []  →  generator EXIT=1 (benar)
                 tapi tanpa-bab.docx 475.582 byte TETAP ADA  ← BAHAYA
```

**Kenapa berbahaya:** kalau disambung ke web, pengguna bisa **mengunduh .docx
rusak** walau proses dilaporkan gagal.

**Obat yang benar** (bukan tambalan): tulis ke `.tmp` → periksa → baru pindah
ke nama akhir. Kalau gagal, `.tmp` dihapus.

### Celah 2 — `romawi: "1"` diterima generator

```
TERTULIS: romawi.docx  ← ditulis dulu
  GAGAL  J2b nomor bab = angka Romawi SAH → 'BAB 1'
```

Generator **menulis** `BAB 1`, baru gerbang menolak. Harusnya tolak **sebelum**
menulis.

**Setelah diperbaiki (`82a99ee`):**
```
romawi = "1"  →  "Spec ditolak: romawi bab tidak sah: '1'"   EXIT=1
                 romawi.docx → TIDAK ADA ✅
```

---

## 5. 8 JEBAKAN yang sudah terbukti menjatuhkan Wulan

Ini bagian **paling berguna**. Semua pernah **benar-benar terjadi**.

| # | Jebakan | Akibat |
|---|---|---|
| 1 | **Clone/fetch basi** | menyimpulkan "klaim agen tidak terbukti" padahal branch belum di-fetch |
| 2 | **Regex `<w:t[^>]*>(.*?)</w:t>`** | bocor menyeberang tag → **2×** menuduh template rusak padahal sehat |
| 3 | **`<w:br/>` hilang** saat ekstraksi teks | **2×** salah bilang judul menyatu |
| 4 | **Saring daftar pakai regex validasi** | item rusak justru **terbuang** → gerbang LULUS padahal rusak |
| 5 | **"Ada minimal satu"** | satu item sehat **menutupi** item rusak |
| 6 | **Uji suntikan pola tak ketemu** | lulus **senyap** → gerbang tampak buta padahal benar |
| 7 | **Gerbang dijalankan di HOST** | hijau di host, **modul tidak ada di image** → produksi rusak senyap |
| 8 | **`sys.path` untuk uji bergigi** | `sys.modules` MENANG → suntikan tak pernah terbaca |

### Jebakan #7 — paling berbahaya (terukur 21 Okt 2026)

```
Semua gerbang LULUS:  BUKU LATAR 25/0 · ID BUKU→ALAT 55/0 · PORSI ALAT 138/0
TAPI:  docker exec eduai-app python3 -c "import jev_buku_umum"
       → ModuleNotFoundError
```

3 modul inti **tidak pernah ada** di image (`jev_buku_umum.py`,
`diagram_buku.py`, `tata_paragraf.py`) — bukan terhapus, memang **tidak pernah
ditulis di `Dockerfile`**.

**Kenapa lolos:** gerbang dijalankan **di host** dengan `sys.path` folder proyek.
Di host berkasnya ADA ⇒ hijau. `Dockerfile` = **daftar putih**.

**Akibat:** buku tetap terbit, "mirip benar", **tanpa Jev & tanpa 8 bentuk
diagram**. Ada `log.warning`, tapi tidak ada yang membacanya.

**Obat:** gerbang `gerbang_modul_di_image.py` — 15 modul wajib bisa diimpor
**dari image** lewat `docker exec` / `docker run --rm`.

---

## 6. Alat ukur yang dipakai (8 skrip)

| Skrip | Fungsi |
|---|---|
| `probe_kunci_ber_jenis.py` | periksa kunci per jenis dokumen |
| `probe_layar_vs_rute.py` | bandingkan yang tampil di layar vs yang dikirim rute |
| `probe_pemetaan_hipotesis.py` | uji pemetaan hipotesis |
| `probe_rute_berpagar.py` | uji rute yang punya pagar |
| `probe_rute_koleksi.py` | uji rute koleksi |
| `probe_tandingan.py` | uji tandingan (A vs B) |
| `probe_teks_narasi.py` | uji teks narasi |
| `uji_gigi_pagar_3_keadaan.py` | **uji bergigi** pagar 3 keadaan |

---

## 7. Prinsip putusan

| Prinsip | Arti |
|---|---|
| **LULUS butuh bukti** | bukan karena agen bilang begitu |
| **TOLAK dengan alasan** | bukan perbaiki diam-diam |
| **Uji harus BISA gagal** | gerbang yang tak pernah gagal = hiasan |
| **Sumber segar dulu** | `git fetch` sebelum menuduh |
| **Jujur soal yang belum** | tulis yang menggantung, jangan sembunyikan |
| **Salah sendiri diakui** | 1 kalimat, jangan berkilah |

---

## 8. Isi folder ini

```
mutu-buku/
├── README.md                        ← berkas ini
└── skill-agen-kolaborator/
    ├── SKILL.md                     ← 1.800+ baris, ALUR REVIEW lengkap
    ├── references/                  ← 16 berkas, kasus nyata per tanggal
    │   ├── review-berulang-generator-buku-22okt2026.md
    │   ├── template-vs-jenis-buku-22okt2026.md
    │   ├── vonis-dicabut-dan-ukur-kepresisian-22okt2026.md
    │   ├── jebakan-review-branch-dan-uji-cdp-22okt2026.md
    │   ├── jebakan-probe-http-cdp-dan-bug-cookie-22okt2026.md
    │   ├── bug-lahir-lagi-dan-container-bocor-21okt2026.md
    │   ├── jangan-tuduh-dari-clone-basi-21okt2026.md
    │   ├── kwitansi-*.md  (5 kwitansi review per fase)
    │   └── vonis-review-jujur-alat-uji.md
    └── scripts/                     ← 8 alat probe & uji bergigi
```

### Berkas yang paling berguna dibaca dulu

| Berkas | Isi |
|---|---|
| `SKILL.md` §1 | **alur review 6 langkah** |
| `SKILL.md` §7 | **8 jebakan terbukti** |
| `references/review-berulang-generator-buku-22okt2026.md` | 4 ronde review generator |
| `references/vonis-review-jujur-alat-uji.md` | cara jujur saat alat uji sendiri salah |
| `references/jangan-tuduh-dari-clone-basi-21okt2026.md` | jebakan #1 |

---

## 9. Bagaimana ini membuat buku BERMUTU

Buku tidak jadi bermutu karena AI-nya pintar. Buku jadi bermutu karena:

| # | Lapis mutu | Alat |
|---|---|---|
| 1 | **Format benar** | gerbang 57 asersi (`template-buku-resmi/`) |
| 2 | **Isi sesuai jenis** | spesifikasi per jenis (`jenis/`) |
| 3 | **Penulisan terkontrol** | tone + larangan budaya + Jev |
| 4 | **Ada yang memeriksa** | **folder ini** (`mutu-buku/`) |
| 5 | **Tidak lolos tanpa bukti** | uji bergigi wajib |

**Lapis 4 yang paling sering dilupakan orang.** Itu sebabnya Wulan push skill
ini — supaya agen lain bisa memakai cara kerja yang sama, bukan hanya melihat
hasilnya.

---

## 10. Cara pakai skill ini di repo lain

```
1. Baca SKILL.md §0  → JANGAN koding saat menerima rancangan
2. Baca SKILL.md §1  → alur review 6 langkah
3. Sebelum menuduh   → git fetch dulu (§1 jebakan #1)
4. Sebelum merge     → jalankan uji bergigi. Kalau tidak ada, BUAT.
5. Setelah merge     → tulis kwitansi (dicek apa | hasil apa)
6. Kalau salah       → akui 1 kalimat, jangan berkilah
```

---

*Dipush Wulan 22 Oktober 2026 — atas permintaan Bos.*
