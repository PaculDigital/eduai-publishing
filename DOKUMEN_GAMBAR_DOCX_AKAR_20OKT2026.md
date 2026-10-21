<!-- 🚪 SOT: catatan akar hilangnya gambar di .docx — bukan penentu status aplikasi. Status ada di SOT.md + sot.py -->
# 🔍 GAMBAR CUMA 5 MASUK .DOCX — AKAR, BUKAN TAMBALAN

> **Tanggal:** 20 Oktober 2026 · **Oleh:** Wulan
> **Pemicu:** Bos pilih **A** — *"lacak kenapa gambar cuma 5 masuk .docx, cari akar bukan tambal"*
> **Status:** ✅ AKAR DICABUT · terbukti di buku nyata · **BELUM DEPLOY** (menunggu izin Bos)

---

## 1. Angka yang menipu

Waktu buku pendidikan anak 6 bab dirakit (19 Okt), laporan menulis **"5 gambar"**.
Di disk ada **52 berkas**. Terlihat seperti 47 gambar hilang. **Tidak.**

| Yang dihitung | Jumlah | Keterangan |
|---|---|---|
| Berkas di disk (semua jenis) | 52 | termasuk .html, .json, varian |
| Varian `_var1/_var2/_var3` | 18 | **memang tidak pernah** dibaca perakit |
| `.json` (brief/refs/tabel) | 18 | data, bukan gambar |
| `.html` diagram | 13 | **bahan**, belum gambar |
| Ilustrasi bab yang dipakai | 6 | `ilustrasi_bab{n}.png` |
| Diagram PNG | **0** | **inilah yang hilang** |
| **Masuk .docx** | **5** | 5 ilustrasi (bab 5 tidak punya berkasnya) |

Jadi "5" = 5 ilustrasi. Yang benar-benar hilang: **13 diagram** — dan **tabel** ikut tenggelam.

---

## 2. Tiga akar (semua TERUKUR, bukan dugaan)

### ① Renderer diagram = STUB, dan tidak pernah dipanggil
`buku_umum_pipeline.py:839 render_html_to_png()` isinya hanya menulis `.html`
lalu `return html_file` — komentarnya sendiri: *"FALLBACK: simpan HTML, render manual nanti"*.
Lebih parah: `generate_bab_visuals()` **tidak pernah memanggilnya** (hanya simpan `.html`).
Perakit mencari `diagram_{id}.png` (`assembly.py:557`) → tidak ada → **dilewati tanpa sepatah kata** (`:568`).

Penyebab stub tak pernah jalan: **Playwright/selenium/imgkit TIDAK ADA di image**
(sudah diukur 20 Okt). Yang ADA: WeasyPrint + PyMuPDF + PIL.

### ② Penanda `[DIAGRAM]`/`[TABEL]` tak terlihat perakit
Penulis (LLM) menaruh penanda di **tengah baris panjang** — judul sub-bab + seluruh
isi jadi SATU baris 7.102 karakter. Pembaca lama hanya mengenali penanda di **awal baris**
(`.startswith('[TABEL')`). Terukur: `parse_diagram_marker()` menemukan 12 diagram,
tetapi `blok_diagram_di_perakit` = **[ ] kosong di keenam bab**.

**Jebakan kedua di dalam akar ② (terbukti, hampir lolos):** memperbaiki
`.startswith` saja TIDAK cukup. Karena baris diawali `### `, blok `if startswith('### '): continue`
**menelan seluruh baris** — termasuk penanda di belakangnya. Perbaikan pertama Wulan
masih menghasilkan `['sub_heading']` saja. Yang benar: **penanda dicabut DULU, baru
sisa teks diuji sebagai judul.**

### ③ Gagal senyap: tidak ada laporan
- `generate_ilustrasi_api()`: hanya menyalin `var1` → default. Bab 5 tidak punya `var1`
  ⇒ tidak ada `ilustrasi_bab5.png` ⇒ tidak ada gambar, laporan tetap "visuals complete".
- Perakit: diagram yang tidak ada dilewati tanpa kata.
- `rakit()` bahkan tidak mengembalikan `visual_hilang`.

---

## 3. Obat (akar, bukan gejala)

| Akar | Berkas | Perubahan |
|---|---|---|
| ① | `buku_umum_pipeline.py:839` | `render_html_to_png()` kini **benar-benar** merender: HTML → PDF (WeasyPrint) → PNG 150dpi (PyMuPDF) → potong margin (PIL). Balas `None` kalau gagal (bukan path HTML). |
| ① | `buku_umum_pipeline.py` `generate_bab_visuals()` | render PNG **dipanggil**; yang gagal dicatat. |
| ② | `buku_umum_assembly.py` `parse_bab_file()` | `_pecah_penanda()` baru: penanda diburu di posisi mana pun; ada pola cadangan untuk penanda terpotong tanpa `]`. Penanda dicabut **sebelum** uji judul. |
| ③ | `buku_umum_assembly.py` `rakit()` | `visual_hilang` dilaporkan di hasil rakit (diagram & ilustrasi yang tidak ada). |
| — | `buku_umum_assembly.py:747` | ambang berkas bab `>200 byte` → `>0` (200 byte itu penjaga berkas kosong, bukan syarat bab sah; uji bab pendek jadi korban). |

JALUR OBAT ① **tidak menambah paket** — semua sudah ada di image `eduai-app`.

---

## 4. Bukti (dijalankan, bukan diklaim)

**Gerbang bergigi**: `_sketsa/gerbang_gambar_docx.py` → **17 LULUS / 0 GAGAL**
Diuji juga **ATAS KODE LAMA** → langsung `ValueError: 'diagram_marker' is not in list` = gerbang benar-benar bergigi.

**Buku yang sama, dirakit ulang (3× berturut-turut, hasil identik):**

| | Sebelum | Sesudah |
|---|---|---|
| Gambar | 5 | **17** (6 ilustrasi + 11 diagram) |
| Tabel | 0 | **10** |
| Paragraf | 157 | 237 |
| Isi tabel penanda di paragraf | ya (bocor) | **tidak** (dicabut) |
| Diagram PNG di disk | 0 | **13** |
| Visual hilang | **tidak dilaporkan** | `['b5-ilustrasi']` ← jujur |

**Bukti MATA:** gambar diambil **dari dalam .docx** lalu dilihat — header navy,
elips pusat, kotak KONSEP/IMPLEMENTASI, panah, teks — **tergambar benar**.

**Gerbang salinan mesin:** `_gerbang_salinan_mesin.py` → **25 LULUS / 0 GAGAL**
(sha256 host == proyek, supaya perbaikan ikut ke image).

---

## 5. Yang BELUM (jujur)

1. **BELUM DEPLOY.** Kode baru ada di host + `services/eduai-publishing/` + container `eduai-app`.
   Image belum dibangun ulang. **Menunggu izin Bos.**
2. **11 dari 13 diagram** masuk — 2 tidak karena memang **tidak ada penanda di naskah**
   (1.1 dan 4.1 dibuatkan HTML-nya oleh pipa tapi tidak dirujuk teks).
3. **`b5-ilustrasi`** masih hilang — akar ③ baru **DILAPORKAN**, belum diperbaiki
   (gambar ulang bab 5 butuh keputusan Bos: render ulang varian atau pakai var2).
4. **Diagram masih template generik** (KONSEP → topik → IMPLEMENTASI), belum
   menggambarkan isi spesifik seperti yang diminta teks ("empat tahap air mendidih").
   Itu cacat **MUTU**, bukan cacat "tidak masuk" — terpisah.
5. Ikon emoji 📊/💡 tampil sebagai kotak kosong di render (font emoji tak ada).
6. `docx.tables` tidak dilaporkan oleh `_uji_rakit_docx.py` (laporan ujinya belum
   membaca `tabel`) — angka tabel di atas diukur langsung dari `.docx`.

---

## 6. Pelajaran (masuk memori/skill)

- **"X masuk" ≠ "X ada di disk".** Hitung dari berkas KELUARAN (baca ulang .docx),
  bukan dari kode yang seharusnya bekerja.
- **Fungsi bernama "render" yang `return` path HTML = STUB.** Cek isi fungsi, jangan
  percaya namanya.
- **Uji harus pakai bentuk data NYATA.** Uji Wulan awal pakai penanda di awal baris
  ⇒ LULUS palsu. Yang menangkap akar ② hanya naskah asli (baris 7.102 karakter).
- **Perbaikan pertama belum tentu benar.** `startswith` dibetulkan, tetap 0 diagram,
  karena `continue` judul menelan baris. Wajib ukur ULANG setelah patch.
