# SOT — FITUR PUBLISH BUKU (17 Okt 2026)

Sumber kebenaran fitur **Publish Buku** di EduAi. Kalau bertentangan dengan
catatan lain, **dokumen ini menang**.

## 1. PUTUSAN BOS (TERKUNCI 17 Okt 2026)

| # | Putusan | Nilai |
|---|---|---|
| 1 | Jumlah kartu | **5** (bukan 4) |
| 2 | Jenis buku | Buku Ajar · Buku Umum · Buku Monograf · Book Chapter · **Buku Referensi** |
| 3 | Desain tampilan | **A — Kartu Bergambar** (dari 3 sketsa: A/B/C) |
| 4 | Input Buku Referensi | **FLEKSIBEL** — tema bebas ATAU bahan sendiri (dua-duanya) |
| 5 | Pita tab di HP | **Bisa digeser ke samping (1 baris)**, bukan melipat |
| 6 | Cara kerja | Sketsa HTML dulu → Bos pilih → baru koding |

Sketsa asli: `_sketsa/sketsa_publish_buku_17okt2026.html`
Potret: `_potret/publish-buku/SKETSA-PC-1440.png` + `SKETSA-HP-390.png`

## 2. LIMA JENIS BUKU ↔ SKILL ↔ MESIN

| # | Jenis | Skill | Status skill | Mesin (dipakai ulang) |
|---|---|---|---|---|
| 1 | Buku Ajar | `buku-ajar-obe` | ✅ ADA | `bcp_full_pipeline.py` + `bcp_phase3_visual.py` |
| 2 | Buku Umum | `buku-umum` | ✅ ADA | `buku_umum_pipeline.py` + `buku_umum_assembly.py` |
| 3 | Buku Monograf | `buku-monograf` | ✅ ADA | pipeline 5 tahap |
| 4 | Book Chapter | `book-chapter` | ✅ ADA | `scripts/book_chapter_pipeline.py` |
| 5 | **Buku Referensi** | `buku-referensi` | ❌ **BELUM ADA** | rencana: sambung `buku_umum_pipeline` + prompt teori |

⚠️ **Buku Referensi = `siap: False`** di `app/buku.py` ⇒ tombol "Segera"
(disabled). **JANGAN** diubah jadi `True` sebelum skill + mesinnya benar-benar
ada dan teruji. Tombol yang menjanjikan fitur kosong = janji palsu.

### Buku Referensi vs Buku Umum — BEDANYA
| Aspek | Buku Umum | Buku Referensi |
|---|---|---|
| Isi | narasi/argumen penulis | **kumpulan teori & konsep** |
| Sitasi | ≥5 per bab | **≥15 per bab** |
| Pembaca | umum | dosen/mahasiswa cari landasan teori |
| Tone | formal-santai naratif | padat, ensiklopedis |

Mesin yang **bisa dipakai ulang** (jangan bikin baru):
`buku_umum_pipeline.py` (chunking per sub-bab) · `buku_umum_assembly.py`
(glosarium, indeks, ISBN, daftar isi) · `bcp_phase3_visual.py` (visual) ·
`verifikasi_sitasi.py` (anti-halusinasi) · Scopus/OpenAlex (sudah di EduAi).

## 3. BERKAS YANG DISENTUH

| Berkas | Perubahan |
|---|---|
| `app/templates/_menu.html` | +1 tab "Publish Buku" → `/buku` |
| `app/templates/naskah.html` | pita tab bisa digeser |
| `app/templates/belajar.html` | pita tab bisa digeser |
| `app/templates/submit_jurnal.html` | pita tab bisa digeser |
| `app/templates/referensi.html` | pita tab bisa digeser |
| `app/templates/kolaborasi.html` | pita tab bisa digeser |
| `app/templates/plagiarisme.html` | pita tab bisa digeser |
| `app/templates/buku.html` | **BARU** — halaman 5 kartu |
| `app/buku.py` | **BARU** — daftar jenis buku (satu sumber) |
| `app/main.py` | +import `_buku` + rute `GET /buku` |

Cadangan: `_arsip/pre-publish-buku-20261017-144003/`

## 4. CARA PITA TAB BISA DIGESER (pola TERBUKTI)

Pola ini **sudah ada** di `artikel.html` sebelum 17 Okt. Wulan hanya menyalinnya
ke 6 berkas lain — **bukan bikin baru**:

```css
.pita{display:flex;gap:8px;margin-bottom:20px;border-bottom:2px solid var(--garis);
      flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;
      scrollbar-width:thin;padding-bottom:2px}
.pita a{...;white-space:nowrap;display:inline-flex;align-items:center;gap:6px}
```

Kunci: `flex-wrap:nowrap` + `overflow-x:auto` + `white-space:nowrap`.
Kalau `flex-wrap:wrap` masih ada → tab MELIPAT (gejala yang dilaporkan Bos).

## 5. JEBAKAN YANG SUDAH TERUKUR

1. **CSS pita TIDAK seragam** — ada 2 kelas (`.pita-tab` dan `.pita`), tersebar
   di 9 berkas dengan `margin` & `font-size` berbeda. JANGAN asal ganti satu;
   ubah per berkas dan verifikasi 1 per 1.
2. **Gerbang anti-bikin-baru BERGIGI** — 17 Okt Wulan sempat menulis
   `_sketsa/potret_sketsa.py`; `periksa_kode.sh` **MENOLAK** (B2: 48 alat potret
   sudah ada). Alat itu dipindah ke `_arsip/…/potret_sketsa_DITOLAK.py`.
   ⇒ Untuk potret sketsa: pakai alat yang ADA, atau minta izin Bos dulu.
3. **Nama ikon WAJIB dicek ke sprite** (`app/static/ikon/lucide.svg`, 68 ikon).
   Yang TIDAK ADA: `book`, `layers`, `award`, `package`, `store`, `microscope`.
   Yang ADA & dipakai: `book-open`, `graduation-cap`, `clipboard-check`,
   `file-text`, `list`.
4. **`TemplateResponse` wajib `request` + `user`** — tanpa itu header nav error.
5. **Jangan bikin dompet/jatah baru** — potong kuota lewat `kuota.potong_banyak()`
   yang SUDAH ADA.

## 6. YANG BELUM DIKERJAKAN (tunggu perintah Bos)

- [ ] `POST /buku/mulai` → buat dokumen baru sesuai jenis terpilih
- [ ] Sambung pipeline per jenis (5 mesin berbeda)
- [ ] Skill `buku-referensi` + prompt gaya teori padat sitasi
- [ ] Potong kuota (pakai `kuota.potong_banyak`, bukan dompet baru)
- [ ] Tombol "Mulai" diuji end-to-end dengan akun user nyata
- [ ] Halaman `/buku` dipotret versi LIVE (bukan sketsa) & dikirim ke Bos

## 7. GERBANG

Sebelum deploy WAJIB:
```bash
cd /opt/data/services/eduai-publishing
bash scripts/periksa_kode.sh && bash jalankan.sh
```
17 LULUS / 0 GAGAL · anti-bikin-baru bersih · setelan produksi sesuai.
