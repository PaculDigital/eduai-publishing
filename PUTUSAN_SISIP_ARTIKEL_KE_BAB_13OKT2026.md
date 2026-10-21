<!-- SOT: PUTUSAN_SISIP_ARTIKEL_KE_BAB_13OKT2026.md — keputusan Bos 13 Okt 2026
      (pilihan A + "sisip saja" + "dua-duanya"). STATUS: BELUM DIKODING,
      sketsa sudah disetujui. -->

# 📄 PUTUSAN BOS — SISIPKAN ARTIKEL KE BAB (13 Okt 2026)

> **Putusan Bos (verbatim):** *"Opsi A"* · *"1. Sisip saja."* ·
> *"2. Bisa 2 2nya"*
>
> **Masalah yang Bos angkat (verbatim):**
> *"Kan aneh jika cari sebuah artikel. Sudah dapat kemudian dianggurin
> sebagai data saja, tidak berfungsi."*
> dan: *"Misal sudah dapat artikel untuk bab 3 misalnya, kemudian dia ingin
> artikel tersebut juga muncul di bab 1 atau 2. Nah bagaimana mekanisme yang
> mudah dan sederhana"*

---

## A. KEPUTUSAN TERKUNCI

| # | Soal | Putusan | Arti |
|---|---|---|---|
| 1 | Cara menyisipkan | **SISIP SAJA** | Paragraf Bos **tidak ditulis ulang**. Hanya ditambah `(Nama, Tahun)` di kalimat yang cocok. |
| 2 | Siapa pilih paragraf | **DUA-DUANYA** | AI menunjuk paragraf → Bos boleh **setuju / pilih sendiri / lewati**. |
| 3 | Artikel dipakai di bab lain | **CENTANG** | Satu tombol "Pakai juga di bab…" → centang bab tujuan. |
| 4 | Daftar pustaka | **1 ENTRI** | Artikel dipakai di 3 bab tetap **satu** entri (tidak dobel). |
| 5 | Langkah kerja | **SKETSA DULU** | Sketsa sudah disetujui Bos → boleh lanjut koding. |

**Berkas sketsa yang disetujui:**
`_sketsa/sketsa_sisip_artikel_13okt2026.html`
(potret: `/opt/data/sketsa_sisip_hp_tuhur.png`)

---

## B. 🔑 TEMUAN TERUKUR — MESINNYA SUDAH ADA (jangan bikin baru)

Sebelum bicara koding, ini **fakta dari kode** (bukan rencana):

| Yang dibutuhkan | Status | Lokasi terukur |
|---|---|---|
| Artikel tersimpan per bab | ✅ ADA | `profil_dokumen.jurnal_json` → `app/jurnal.py:20` |
| Pakai ulang antar bab | ✅ ADA | `app/jurnal.py:212` → `pakai_di()` |
| Riwayat "dipakai juga di" | ✅ ADA | `pakai_di()` tulis `dipakai_juga_di` |
| Info daftar bab pemakai | ✅ ADA | `app/jurnal.py:206` → `sudah_dipakai_di()` |
| Kirim artikel ke AI | ✅ ADA | `kerangka.py:329` `bangun_isi()`, param `artikel_dipakai` di `:332` |
| Bahan AI dari abstrak asli | ✅ ADA | `app/pagar_artikel.py:82` → `teks_untuk_ai()` |
| Aturan anti-halusinasi | ✅ ADA | `app/pagar_artikel.py:109` → `aturan_prompt()` |
| Cek DOI (pagar) | ✅ ADA | `pustaka.py:490` → `audit_doi()` |
| Daftar pustaka APA 7 | ✅ ADA | `pustaka.py:1740` → `daftar_pustaka_apa7()` |
| **Yang belum ada** | ❌ | **tombol/UI** yang memanggil semua di atas |

### 🎯 KESIMPULAN PENTING
Yang Bos rasakan (**"artikel dianggurin, tidak berfungsi"**) memang **nyata**:
artikel **sudah** tersimpan + **sudah** ada fungsi untuk memakainya kembali,
tapi **belum ada satu pun tombol** yang menyambungkannya ke paragraf naskah.

⇒ **Bukan mesin baru. Ini PEMASANGAN SAMBUNGAN.**

---

## C. 🧭 ALUR YANG DIPUTUSKAN

```
① Artikel dicari (sudah jalan hari ini)
        ↓
② Bos centang artikel → dipakai di bab mana saja  [pakai_di]
        ↓
③ Bos klik "Sisipkan ke paragraf"
   → mesin kirim artikel ke AI                     [artikel_dipakai]
   → bahan = judul + ABSTRAK ASLI penulis          [teks_untuk_ai]
   → AI diberi aturan ketat                        [aturan_prompt]
        ↓
④ AI MENUNJUK paragraf paling cocok
   → Bos: [Sisipkan] [Pilih lain] [Lewati]
        ↓
⑤ Mesin periksa: kutipan ada di artikel kiriman?
   ADA → lolos  ·  TIDAK → dibuang
        ↓
⑥ Daftar pustaka otomatis (hanya yang lolos DOI)   [daftar_pustaka_apa7]
```

---

## D. 🛡️ PAGAR — YANG MUSTAHIL TERJADI

Karena AI **hanya** boleh memakai artikel yang **Bos centang**:

| Mustahil | Sebab |
|---|---|
| AI mengutip artikel yang tidak ada | AI hanya **diberi** artikel centang, tidak boleh mencari sendiri |
| AI mengarang nama penulis / tahun | Bahan datang dari **abstrak asli penulis**, bukan karangan AI |
| Kutipan tanpa entri daftar pustaka | Kutipan diperiksa ke daftar kiriman; tidak ada → dibuang |
| Daftar pustaka dobel | `pakai_di()` tidak menambah hitungan ulang di bab tujuan |
| Artikel tanpa DOI masuk daftar pustaka | `daftar_pustaka_apa7()` hanya meloloskan `verified` / `no_doi` |

⚠️ **Artikel tanpa abstrak** ditandai `isi_terbatas` — boleh muncul di daftar
pustaka, **TIDAK boleh** jadi dasar temuan (pagar yang sudah jalan).

---

## E. ⚙️ RINCIAN TEKNIS YANG PERLU DIINGAT SAAT KODING

1. **Paragraf tidak ditulis ulang.** AI hanya **menyisipkan** `(Nama, Tahun)`.
   Kalimat asli Bos utuh. (Putusan 1: "sisip saja".)
2. **Dua jalur penunjukan** harus ada di layar: usulan AI **dan** pilih sendiri.
3. **Bab tujuan** diambil dari daftar bab yang **sudah terdeteksi** untuk
   naskah itu (jangan ketik bebas).
4. **Jangan panggil AI untuk hal yang bisa dihitung kode** — cek kutipan,
   cek DOI, rakit daftar pustaka semua **kode**, bukan AI.
5. **Pakai ulang tidak kena kuota dobel** (putusan 06Okt, sudah dikode).

---

## F. ⏭️ URUTAN KERJA YANG DISETUJUI

1. Sambungan A — tombol **"Pakai juga di bab…"** (centang bab).
2. Sambungan B — tombol **"Sisipkan ke paragraf"** + usulan AI + pilih sendiri.
3. Gerbang baru (bergigi) untuk keduanya.
4. Uji HTTP end-to-end → **minta izin deploy**.

> ⚠️ **DILARANG dikoding sebelum Bos bilang "mulai".**
