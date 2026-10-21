# PUTUSAN FITUR LoA (Letter of Acceptance) JEMT — 16 Okt 2026

<!-- SOT: dokumen ini BUKAN sumber kebenaran. Sumber resmi: SOT.md.
     Status DIHITUNG dari kode oleh sot.py, bukan dihafal di sini.
     Kalau bertentangan dengan SOT.md ⇒ SOT.md MENANG. -->

Status: **PUTUSAN TERKUNCI — mesin SEDANG DIBANGUN**
Pemilik putusan: Bos. Dicatat: Wulan.

---

## 1. APA ITU LoA DI SINI

LoA = **surat keterangan diterima** (PDF) yang diterbitkan **EduAi sendiri**.

⚠️ **TERBUKTI 16 Okt 2026 (baca sumber OJS):** OJS 3.5 **TIDAK punya** fitur
"Letter of Acceptance". Tidak ada berkas LoA, tidak ada genre LoA (12 genre
JEMT: Article Text, Data Set, Image… semua bukan LoA), tidak ada status
"LoA terbit". Yang OJS punya = **email keputusan**
(`DecisionAcceptNotifyAuthor.php` dll).

⇒ Jadi LoA **dicetak EduAi** dari data yang ada. Bukan minta berkas ke OJS.

---

## 2. PUTUSAN BOS (TERKUNCI)

| # | Hal | Putusan |
|---|---|---|
| 1 | Pembuat LoA | **EduAi** (bukan OJS, bukan admin manual) |
| 2 | Pemicu | status artikel **DITERIMA** (dibaca dari Tridarma) |
| 3 | Kop surat | **DITETAPKAN** (lihat §3) |
| 4 | Nomor LoA | `<volume>.<nomor_artikel>` → contoh `1.001` |
| 5 | Nomor artikel | **naik terus** tiap LoA terbit: 001 → 002 → 003 |
| 6 | Volume | naik **HANYA kalau Bos ubah manual** di pengaturan |
| 7 | Volume + Nomor terbitan (isi surat) | **ambil dari Tridarma** |
| 8 | Kalau Tridarma kosong | **LoA TIDAK TERBIT** (tunggu jurnal diisi) |
| 9 | QR Code | belum diputuskan |
| 10 | Uji | pakai data uji di Tridarma, **dihapus lagi** setelah terbukti |

---

## 3. KOP SURAT — BENTUK FINAL (disetujui Bos 16 Okt 2026)

```
┌───────────────────────────────────────────────────────┐
│ [LOGO]  TRIDARMA.ID                                   │
│         Jurnal Ekonomi dan Manajemen Tridarma         │
│         Tridarma Journal Publishing                   │
│ ───────────────────────────────────────────────────── │
│   E-ISSN: 3163-608X • Terbit 6× • Web:… • Email:…     │  ← RATA TENGAH
└───────────────────────────────────────────────────────┘
```

Perjalanan koreksinya (4 putaran, Bos benar semua):
1. ❌ tulisan hanya di kanan logo → **lubang kosong di bawah logo**
2. ❌ Wulan pindah logo ke tengah → **salah** (logo harus tetap kiri)
3. ❌ Wulan taruh semua tulisan di bawah logo → **salah** (3 baris tetap di kanan logo)
4. ✅ **BENAR**: logo kiri + 3 baris di kanan logo + baris E-ISSN **turun rata tengah**

**Berkas template final:** `app/templates/loa/loa-jemt.html`
(asal: ZIP Bos `tridarma-loa/agent/template-loa-jemt-agent.html`)

---

## 4. 14 ISIAN (token `{{...}}` di template)

| Token | Isi | Sumber |
|---|---|---|
| `loa_number` | nomor LoA | EduAi (urut) |
| `article_title` | judul artikel | Tridarma |
| `authors` | nama penulis | Tridarma |
| `affiliation` | afiliasi | Tridarma |
| `submission_id` | id naskah OJS | Tridarma |
| `acceptance_date` | tanggal diterima | Tridarma |
| `volume` / `issue` / `publication_date` | terbitan | **Tridarma (issues)** |
| `editor_name` | Chief Editor | pengaturan EduAi |
| `issue_place` / `issue_date` | kota + tanggal surat | pengaturan EduAi |
| `contact_email` / `contact_wa` | kontak jurnal | pengaturan EduAi |
| `verify_url` | URL verifikasi | EduAi |

---

## 5. BAHAN SUDAH ADA (nol mesin baru)

| Kebutuhan | Yang dipakai |
|---|---|
| Cetak PDF | `weasyprint==69.0` (sudah ada, dipakai plagiarisme) |
| QR Code | `qrcode[pil]==8.2` (sudah ada, dipakai QRIS `main.py:1684`) |
| Data artikel | `app/submit_jurnal.py` (kartu Daftar Artikel) |
| Simpan berkas | pola `app/rute_jurnal.py` |
| Baca Tridarma | jembatan `article_status.php` (diperluas) |

---

## 6. STRUKTUR OJS (TERBACA DARI SUMBER, 16 Okt 2026)

```
publications.issue_id        →  Repo::issue()->get($id)
                                 → getVolume() · getNumber() · getDatePublished()
publications.date_published  →  tanggal artikel terbit
submissions.stage_id/status  →  tahap & keputusan
```
❗ JEMT **belum punya terbitan**: `SELECT COUNT(*) FROM issues` = **0**.
❗ Kolom `submissions` TIDAK punya `date_published` (ada di `publications`).

---

## 7. YANG BELUM DIPUTUSKAN

- QR Code + halaman verifikasi (di EduAi atau Tridarma?)
- Tanda tangan Chief Editor (gambar) — masih kosong di template
