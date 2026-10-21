# 🧭 RANCANGAN LAPIS 3 — BAB BERSAMAAN · 19 OKT 2026

<!-- 📌 SOT: RANCANGAN SAJA — nol baris kode. Status: BELUM dikerjakan, menunggu
     putusan Bos soal batas bab bersamaan (2 atau 3). Angka dasar dari
     `_ukur_waktu_sub_bab.py`. Bukan janji percepatan — perkiraan ±2,5×. -->

**STATUS: RANCANGAN SAJA — NOL BARIS KODE. Menunggu putusan Bos.**
Permintaan Bos: "Saya juga tidak menuntut cepat cepat dan hasil salah. Tapi saya
butuh optimalisasi." ⇒ Rancangan ini WAJIB menjaga mutu lebih dulu, kecepatan
nomor dua.

---

## 0. ANGKA DASAR (TERUKUR, bukan tebakan)

`_ukur_waktu_sub_bab.py`, 1 sub-bab, AI sungguhan:

| Tahap | Waktu | Porsi |
|---|---|---|
| **Architect** | 42,8 dtk | **39%** |
| Skeptic | 16,2 dtk | 14% |
| Pragmatist | 22,6 dtk | 20% |
| Editor | 27,9 dtk | 24% |
| Ringkasan sub-bab | 8,4 dtk | 7% |
| cari referensi | 1,7 dtk | 1% |

- **99% waktu habis menunggu AI.** Optimasi Python/berkas = 1% ⇒ tidak sepadan.
- 1 bab (intro + 3 sub + penutup + ringkasan) ≈ **6–7 menit**
- 1 buku 6 bab ≈ **±40 menit**

**Kesimpulan:** satu-satunya cara memotong besar = **mengerjakan beberapa bab
dalam waktu bersamaan**, karena ANTAR-BAB tidak saling menunggu isi — beda
dengan sub-bab DI DALAM bab yang memang berantai (`rolling = summary`).

---

## 1. LAPISAN (4)

### Lapis 3a — State per bab (WAJIB PERTAMA, tanpa ini = isi tercampur)
Masalah: `OUT_DIR`, `CKPT_FILE`, `VISUAL_DIR`, `OUTLINE` adalah **variabel
global modul**. Dua bab jalan bersamaan ⇒ menulis ke folder & checkpoint yang
SAMA.

Bukti dari kode:
- `buku_umum_pipeline.py:13` `OUT_DIR = "/opt/data/buku_umum_test"`
- `:15` `CKPT_FILE = os.path.join(OUT_DIR, "checkpoint.json")`
- `:593` `VISUAL_DIR = os.path.join(OUT_DIR, "visual")`
- `:720` `_temp_render.html` — **nama TETAP**, dua bab menimpa berkas yang sama
- `:892` `save_checkpoint()` menulis `CKPT_FILE` (dibagi semua bab)

**Obat:** tiap bab punya subfolder `OUT_DIR/bab{N}/` + checkpoint per bab.
`_temp_render.html` diberi nama unik per bab.
**Uji:** 2 bab jalan bersamaan → berkas `bab1.txt` dan `bab2.txt` harus berbeda
isi, dan tidak ada berkas di folder yang salah.

### Lapis 3b — Pengawas bab (orkestrator)
- Maks **3 bab** bersamaan (bukan 6). Alasan: 9router terbukti 8 bersamaan,
  tapi 3 memberi ruang untuk fallback model saat satu permintaan gagal.
- Antrean: bab 1..6, maks 3 jalan. Bab selesai → ambil berikutnya.
- Tiap bab dibungkus `try/except`: satu bab gagal **tidak** menggagalkan buku;
  dicatat `status=gagal` + alasannya.
- **Ringkasan antar-bab:** dulu bab 2 menerima `prev_summary` bab 1. Kalau
  bersamaan, ringkasan itu belum ada ⇒ kirim **judul bab + poin kunci outline**
  sebagai ganti ringkasan. Ini penurunan mutu yang HARUS diuji, bukan diabaikan.

### Lapis 3c — Pemeriksa mutu (gerbang isi)
Setelah semua bab jadi, periksa **sebelum** dirakit jadi `.docx`:
1. **Tidak berulang:** tiap pasangan bab diuji kemiripan kalimat pembuka dan
   paragraf inti. Ambang awal: **>25% kemiripan = curiga**.
2. **Tidak melenceng:** tiap bab harus memuat ≥3 poin kunci outline-nya.
3. **Sitasi cukup:** tiap bab ≥2 sitasi terverifikasi (penjaga lama).
Gagal → **perbaiki bab itu sekali**; masih gagal → lapor jujur "BAB N TIDAK
LOLOS" + alasannya. **JANGAN pura-pura selesai.**

### Lapis 3d — Sambung ke jalur latar
Sudah ada: `/buku/susun` → `app/proses.py` → `/buku/proses/{kode}`.
Tinggal panggil `susun_buku()` versi baru. Tahap yang dilaporkan ditambah:
`BAB 3, 4, 5 sedang ditulis bersamaan`.

---

## 2. RISIKO — TERBUKA, TIDAK DISEMBUNYIKAN

| Risiko | Besar | Penangkal |
|---|---|---|
| Isi bab saling berulang (karena tidak ada ringkasan bab sebelumnya) | **TINGGI** | Lapis 3c nomor 1 + perbaikan otomatis |
| Berkas saling menimpa | Sedang | Lapis 3a (nama unik + folder per bab) |
| 9router menolak saat 3 bab × 5 panggilan bersamaan | Sedang | Maks 3 bab; fallback model sudah ada |
| Token terpakai lebih besar (tidak ada penghematan) | Nol | Charge tetap di depan |
| Gagal total justru lebih lama | Rendah | Tiap bab terisolasi; bab lain tetap jalan |

---

## 3. PERKIRAAN HASIL — RENDAH HATI

| | Sekarang | Lapis 3 |
|---|---|---|
| 1 buku 6 bab | ±40 menit | **±15–18 menit** |
| Percepatan | — | **±2,5×** |

**BUKAN 6×.** Alasannya: 3 bab bersamaan, tapi tiap bab tetap 6–7 menit, dan
ekor terakhir tetap harus ditunggu (bab 6 selesai paling akhir).

---

## 4. CARA MENGUJI (WAJIB, TANPA AI = Rp 0)

1. **Uji state:** 2 bab bersamaan dengan AI dipalsukan → berkas tidak tercampur.
2. **Uji pemeriksa mutu:** suntik 2 bab yang isinya SAMA → harus tertangkap.
3. **Uji isolasi gagal:** buat bab 3 selalu gagal → bab lain tetap jadi, laporan
   jujur menyebut bab 3 gagal.
4. **Uji nyata 2 bab** (±14 menit, token kecil) → bandingkan isi dengan versi
   berurutan: harus sama-sama nyambung, tidak berulang.

**Gerbang dinyatakan bergigi kalau setiap suntikan menghasilkan GAGAL.**

---

## 5. YANG DIMINTA DARI BOS

Satu keputusan saja: **setuju maksimal 3 bab bersamaan**, atau **2 bab**
(lebih lambat sedikit, lebih aman).
