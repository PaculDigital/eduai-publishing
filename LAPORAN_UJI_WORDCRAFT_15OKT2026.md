<!-- SOT: LAPORAN_UJI_WORDCRAFT_15OKT2026 -->

# 🔬 LAPORAN UJI — WORDCRAFT sebagai ALTERNATIF/PENDAMPING ONLYOFFICE

> Dibuat: 15 Okt 2026 · atas perintah Bos: *"install latest dan buat seperti posisi onlyoffice sekarang"*
> STATUS: **UJI SELESAI — KEPUTUSAN: WordCraft = ALAT BANTU WULAN, BUKAN PENGGANTI.**
> Melanjutkan: `CATATAN_WORDCRAFT_ALTERNATIF_14OKT2026.md`

---

## 1. APA YANG DIUJI

| Hal | Nilai |
|---|---|
| Versi | **WordCraft v0.7.0** (terbit 14 Okt 2026) |
| Sumber | rilis resmi GitHub `storytold/wordcraft` — **sidik SHA-256 DIPERIKSA, cocok** |
| Berkas diuji | `wordcraft-web-0.7.0.zip` (14,3 MB) + `wordcraft-0.7.0-linux-x86_64.tar.gz` (92,8 MB) |
| CLI | `bin/wordcraft-cli` **73 MB** (BUKAN paket terpisah — ada DI DALAM paket Linux) |
| Simpan tetap | `/opt/data/services/wordcraft-uji/bin/wordcraft-cli` |
| Font tambahan | `/opt/data/.fonts/` — Carlito, Caladea, Liberation (20 berkas, 7,2 MB) |

**Font pengganti (SAH, repo resmi Debian — bukan bajakan):**
- `Carlito` = kembaran **Calibri** · `Caladea` = kembaran **Cambria**
- `Liberation Serif/Sans/Mono` = kembaran **Times New Roman / Arial / Courier New**
- Semua **metric-compatible** ⇒ ukuran huruf identik, jumlah halaman tetap

---

## 2. HASIL UKUR — NYATA, 3 NASKAH ASLI MAHASISWA

| Naskah | Ukuran | `info` | `text` | `convert` PDF | RAM puncak |
|---|---|---|---|---|---|
| Asih (133 hlm) | 2,28 MB | 1,65 dtk | 0,56 dtk | **2,03 dtk** | 94 MB |
| Fazri (57 hlm) | 5,08 MB | 0,78 dtk | 0,39 dtk | **1,87 dtk** | 94 MB |
| Wulandari (50 hlm) | 0,56 MB | 0,40 dtk | 0,14 dtk | **0,56 dtk** | 94 MB |

**Pembanding OnlyOffice (mesin produksi, ConvertService + JWT):**

| Naskah | OnlyOffice PDF | WordCraft PDF |
|---|---|---|
| Asih | 28,1 dtk | **2,03 dtk** (14× lebih cepat) |
| Fazri | 19,0 dtk | **1,87 dtk** (10× lebih cepat) |
| Wulandari | 8,0 dtk | **0,56 dtk** (14× lebih cepat) |

**RAM: 94 MB vs OnlyOffice 4,86 GB ⇒ ringan ~50×**

---

## 3. 🚨 TEMUAN PENENTU — HALAMAN BELUM SAMA

| Naskah | OnlyOffice | WordCraft | Beda |
|---|---|---|---|
| Asih | 126 hlm | 133 hlm | **+7** ❌ |
| Fazri | 54 hlm | 57 hlm | **+3** ❌ |
| Wulandari | 47 hlm | 50 hlm | **+3** ❌ |

### Akar (TERUKUR, bukan dugaan)

**BUKAN masalah font.** Dibuktikan dengan naskah Wulandari (100% Times New Roman →
WordCraft pakai Liberation Serif, kembaran persis) — **tetap beda 3 halaman**.

**Bukti dari teks per halaman (pypdfium2):**

| | Halaman 2 |
|---|---|
| OnlyOffice | `"LEMBAR PERSETUJUAN PEMBIMBING…"` (725 huruf) ✅ |
| WordCraft | `"ii / 2026"` (8 huruf) ❌ **halaman kosong** |

**Sebab: WordCraft belum benar menangani perintah bagian-bagian (section) naskah:**

```xml
<w:titlePg/>              <!-- halaman pertama beda (cover) -->
<w:vAlign w:val="both"/>  <!-- isi ditengahkan tegak -->
```

Naskah skripsi punya **3 bagian (sectPr)** dengan pengaturan berbeda. Tiap kali WordCraft
melewati bagian seperti ini, ia **menyisipkan halaman kosong** ⇒ total bertambah 3–7 halaman.

⇒ **INI CACAT MESIN TATA LETAK WordCraft** (masih ALPHA — kata pembuatnya sendiri
"~150–230 jam ke beta"). **TIDAK BISA ditambal** dengan font atau pengaturan dari sisi kita.

---

## 4. ⛔ KOREKSI PENTING — WORDCRAFT ≠ SERVER

| | OnlyOffice | WordCraft |
|---|---|---|
| Jenis | **Server** (dokumen hidup di VPS) | **Aplikasi desktop / browser** |
| Naskah mahasiswa | di server Kita, semua orang lihat yang sama | di komputer mahasiswa masing-masing |
| Cocok dgn D8 SOT | ✅ satu dokumen, satu kebenaran | ❌ memutus model SOT |

**Konsekuensi:** WordCraft versi web **TIDAK BISA** jadi "workspace milik kita" seperti
OnlyOffice — naskah tidak pernah masuk ke server. Kalau dipaksa jadi workspace, harus
dibangun jembatan remote dari nol (belum ada, alpha, dan VPS cuma sisa 4,7 GB).

### Tentang MCP — TIDAK DIPAKAI di EduAi (jangan dibingungkan lagi)

WordCraft punya **MCP**, tapi **bukan untuk Kita**. MCP itu jembatan supaya **AI menyetir
aplikasi WordCraft** yang ada **di komputer yang sama** (`--control` hanya `127.0.0.1`).

| Bagian WordCraft | Dipasang di mana | Untuk siapa | Dipakai EduAi? |
|---|---|---|---|
| **Aplikasi WordCraft** (jendela) | desktop masing-masing orang | orang itu sendiri | ❌ tidak nyambung |
| **MCP** | ikut aplikasi itu | AI di komputer ITU | ❌ **tidak dipakai** |
| **`wordcraft-cli`** (tanpa jendela) | **VPS Kita** | **Wulan** | ✅ **INI yang dipakai** |

**Alasan singkat:** MCP hanya bisa bicara ke aplikasi di **komputer yang sama**. VPS Kita
bukan komputer mahasiswa ⇒ MCP **tidak bisa** dipakai untuk membaca naskah mahasiswa.
Yang bisa = **CLI**-nya, karena CLI jalan **di VPS** dan bisa buka berkas **di VPS**.

⇒ **MCP tidak perlu diurus, tidak perlu dipasang, tidak masuk rencana apa pun.**

**Koreksi catatan lama:** Wulan sempat (a) bilang "tidak ada pintu naskah" — itu salah, yang
Wulan baca cuma API WASM browser, bukan MCP; lalu (b) menyebut MCP sebagai alasan WordCraft
berguna untuk Kita — **itu juga salah**. Yang berguna untuk Kita **cuma CLI**.

---

## 5. ✅ KEPUTUSAN — 2 ALAT, 2 TUGAS (putusan Bos 15 Okt: "A")

| Tugas | Alat | Alasan |
|---|---|---|
| **PDF resmi mahasiswa** | **OnlyOffice** (tetap) | Halaman DIJAMIN persis; WordCraft meleset 3–7 hlm |
| **Wulan baca naskah** | **WordCraft CLI** | 10× lebih cepat, RAM 94 MB, akurat |
| **Wulan "lihat" tampilan** | **WordCraft CLI** `render` | PNG halaman — Wulan selama ini BUTA tampilan |
| **Wulan periksa struktur** | **WordCraft CLI** `inspect` | JSON: bab, sub-bab, tabel, paragraf |

**NOL perubahan pada produksi EduAi.** OnlyOffice tetap utuh. WordCraft hanya alat di sisi Wulan.

---

## 6. CARA PAKAI (untuk Wulan)

```bash
WC=/opt/data/services/wordcraft-uji/bin/wordcraft-cli
export HOME=/opt/data                 # supaya font tambahan terbaca

$WC info    naskah.docx               # halaman, kata, paragraf (JSON)
$WC text    naskah.docx               # teks polos
$WC inspect naskah.docx               # struktur dokumen (JSON)
$WC render  naskah.docx out.png --page 3   # halaman jadi gambar
$WC convert naskah.docx out.pdf       # PDF (⚠️ JANGAN untuk naskah resmi mahasiswa)
```

> `$WC mcp` ada, tapi **TIDAK DIPAKAI** — lihat §4 (MCP hanya untuk aplikasi desktop).

### Larangan
- ❌ **JANGAN** pakai `convert` WordCraft untuk PDF yang diserahkan ke mahasiswa/dosen
- ❌ **JANGAN** ganti OnlyOffice sebagai editor produksi
- ❌ **JANGAN** salin font Windows asli (Calibri/Times) — melanggar lisensi Microsoft

---

## 7. BAHAN TERSIMPAN (SETELAH BERSIH-BERSIH 15 Okt)

```
/opt/data/services/wordcraft-uji/            TOTAL 78 MB
  bin/wordcraft-cli                       ← ALAT UTAMA (71 MB)
  fontkit/                                ← 20 font pengganti (7,2 MB)
  contoh-halaman1.png                     ← bukti Wulan bisa "lihat" naskah
  rilis.json · SHA256SUMS.txt             ← bukti sidik asli
  cek_teks.py                             ← alat bantu uji
```

**Sudah DIBUANG (326 MB, hemat disk):** paket unduhan 93 MB · versi web zip+isi 54 MB ·
bongkaran 171 MB · font mentah 4 MB. Disk VPS: 4,2 GB → **4,5 GB sisa**.

**Font terpasang:** `/opt/data/.fonts/` (20 berkas) — WAJIB `export HOME=/opt/data` saat pakai CLI.

---

## CARA BALIK
Bos bilang *"lanjut wordcraft"* → baca berkas ini + `CATATAN_WORDCRAFT_ALTERNATIF_14OKT2026.md`.
