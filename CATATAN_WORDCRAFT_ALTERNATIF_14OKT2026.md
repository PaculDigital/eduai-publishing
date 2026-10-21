<!-- SOT: CATATAN_WORDCRAFT_ALTERNATIF_14OKT2026 -->

# 🔎 CATATAN DISKUSI — WORDCRAFT sebagai ALTERNATIF ONLYOFFICE

> Dibuat: 14 Okt 2026 · atas permintaan Bos: *"Kamu catat dulu masalah wordcraft ini."*
> STATUS: **CATATAN DISKUSI — BUKAN TUGAS.** DILARANG DIKODING/DIINSTAL tanpa izin Bos.
> Sumber: repo resmi `github.com/storytold/wordcraft` + `ROADMAP.md` + `docs/mcp.md`
> (dibaca 14 Okt 2026, bukan dugaan).

---

## 1. APA ITU (fakta dari repo sendiri)

**WordCraft** — pengganti Microsoft Word sumber-terbuka, ditulis ulang **dari nol dalam Rust**
(clean-room). Bagian dari keluarga *Crafting Apps* (ArtCraft team). MIT OR Apache-2.0.

- Punya **ribbon** seperti Word, styles, tabel, track changes, referensi, mail merge.
- Bisa **.docx baca/tulis**, juga .odt/.rtf/.html/.md/.txt; ekspor PDF.
- Jalan di macOS/Windows/Linux/BSD **dan di browser (WebAssembly)**.
- Punya **CLI** (`wordcraft-cli`) + **MCP server** + control channel JSON (389 perintah).

## 2. ANGKA RESMI (dari ROADMAP.md, 10 Okt 2026)

| Ukuran | Nilai | Jenis |
|---|---|---|
| Cakupan katalog ribbon | 487/502 (97,0%) | terukur |
| **Siap kerja nyata** | **~60% (55–63%)** | perkiraan |
| Pengguna mainstream | ~55% | perkiraan |
| **Tahap** | **ALPHA** (belum beta) | pernyataan sendiri |
| Sisa ke beta | **~150–230 jam** | perkiraan |
| Sisa ke parity penuh Word | ~750–1.250 jam | perkiraan |
| Kode | ~88.700 baris Rust · 433 perintah · 855 uji | terukur |
| Rilis terakhir | v0.4.0 (10 Okt 2026) | terukur |

## 3. KENAPA BOS TERTARIK — INI BENAR

OnlyOffice memuat **ratusan aset** tiap tab editor dibuka (sdk, font, kamus, ikon — terlihat
di log EduAi). WordCraft **tidak perlu server**; versi web-nya = satu berkas WASM di browser.
⇒ **Beban jauh lebih ringan.** Klaim Bos masuk akal dan sesuai keunggulan resminya.

## 4. TIGA HAL YANG HARUS DIINGAT (bukan menolak, tapi fakta)

**① BELUM STABIL — ini kata pembuatnya sendiri.**
*"Stage: alpha"* · *"Ready for real work ~60%"* · *"~150–230 h to beta"*.
⇒ Bos TIDAK salah bilang "belum stabil". Bahkan repo-nya bilang begitu.

**② BENTROK ATURAN BOS YANG SUDAH TERKUNCI (02 Okt 2026, verbatim).**
> *"alat sama mahasiswa=pembimbing alatnya sama onlyoffice... Jadi resource sama, tidak ada
> html dll. Single source of truth."*

OnlyOffice sekarang = **satu dokumen hidup di server**, dua orang lihat hal yang sama
(D8 single source of truth, 1 editor oo-converter, 1 halaman `/edit/{fid}`).
WordCraft = aplikasi di **sisi klien**. ⇒ Kalau dipakai sebagai editor, model SOT itu
**harus dirancang ulang dari nol** — bukan sekadar tukar alat. Ini keputusan besar.

**③ YANG BISA DIPAKAI TANPA BONGKAR APA PUN = `wordcraft-cli`.**
Ini bisa jadi **pengganti/pendamping oo-converter** untuk: docx→pdf, ambil teks,
`inspect` struktur dokumen (JSON), render halaman jadi PNG.
Ringan, tidak menyentuh editor yang jalan sekarang. **Ini kandidat paling aman.**

## 5. YANG BELUM DIKETAHUI (jujur — belum diuji)

```
❌ Apakah versi web (WASM) benar-benar bisa dilayani dari VPS Bos?
❌ Apakah kuat membuka skripsi 2 MB (naskah Asih fid=81) tanpa rusak?
❌ Berapa beban memori nyata vs OnlyOffice? (BELUM diukur)
❌ Bagaimana komentar pembimbing (track changes) disimpan? Server siapa?
```

## 6. KESIMPULAN WULAN (untuk keputusan Bos nanti)

- **JANGAN ganti editor sekarang.** Alasan: (a) alpha; (b) bentrok D8 single source of truth;
  (c) akar macet OnlyOffice **belum terukur** — ganti alat tanpa tahu akar = bisa sia-sia.
- **JALAN AMAN = experiment TERPISAH** (container baru, 0 risiko ke produksi):
  ukur 3 naskah nyata → bandingkan angka → baru Bos putuskan.
- Prioritas sekarang (perintah Bos): **ukur akar macet + load lama OnlyOffice dulu.**

---
## CARA BALIK
Bos bilang *"lanjut wordcraft"* / *"buka catatan wordcraft"* → baca berkas ini + `ROADMAP.md`.
