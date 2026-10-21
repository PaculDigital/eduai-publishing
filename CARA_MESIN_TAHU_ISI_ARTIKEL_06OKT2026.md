# 🔍 CARA MESIN TAHU ISI ARTIKEL TANPA MENGUNDUH & TANPA HALUSINASI

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.

## (06 Okt 2026 — jawaban pertanyaan Bos)

> Kata Bos (verbatim): *"Setuju A, tapi kata kata jangan unduh sendiri, kemudian
> saya bingung bagaimana jika berkas tidak bisa diunduh, script/bot bisa tahu
> isinya tanpa halusinasi?"*

---

## 1. MASALAH YANG BOS TANGKAP (tepat sekali)

Kalau berkas PDF tidak bisa diambil, ada **2 jalan salah**:

| Jalan salah | Akibat |
|---|---|
| ❌ AI **menebak** isi artikel dari judul | **HALUSINASI** — kelas kesalahan yang sama dengan `spark`; AI mengarang temuan/angka yang tidak ada di artikel |
| ❌ Bot **dipaksa** unduh terus | Lambat, kena 403/login, dan **melanggar** aturan Bos ("jangan download artikel") |

**Yang Bos cari:** jalan ketiga — mesin tahu **isi** artikel dari data **NYATA**,
bukan tebakan.

---

## 2. JAWABAN: SUDAH ADA — "ABSTRAK" (bukan berkas, bukan tebakan)

Tiap sumber **sudah menyediakan abstrak** — ringkasan resmi yang **ditulis
penulis artikelnya sendiri**. Itu **bukan karangan mesin**.

**Terukur (baru diuji, 06 Okt 2026):**

| Sumber | Abstrak tersedia? | Panjang terukur |
|---|---|---|
| **Garuda** | ✅ | 664 · 1038 · 2000 huruf |
| **Crossref** | ✅ (sebagian) | 1163 · 2666 huruf, 0 kalau penulis tak menyertakan |
| **OpenAlex** | ✅ (`abstract_inverted_index`) | direkonstruksi `_abstrak_openalex()` |
| **Scopus** | ✅ (`dc:description`) | — |

⇒ **Jadi: tak perlu unduh berkas untuk tahu isinya.** Abstrak = sumber
**NYATA** (kata penulis sendiri) + sudah tersimpan di tiap artikel.

---

## 3. PAGAR ANTI-HALUSINASI (yang WAJIB ditambahkan)

Abstrak saja belum cukup — AI **tetap bisa** mengarang di luar abstrak.
⇒ Wajib 3 pagar:

### Pagar 1 — AI HANYA boleh memakai yang ADA
- Yang dikirim ke AI: **judul + abstrak + jurnal + tahun** (data nyata).
- Aturan tertulis ke AI: *"Yang tidak ada di abstrak/judul → JANGAN tulis.
  Jangan menambah temuan, angka, atau nama penulis dari luar."*

### Pagar 2 — BERI TANDA kalau isi kurang
- Kalau abstrak **kosong** (0 huruf) → tandai artikel **"⚠️ ISI TERBATAS"**.
- Artikel bertanda ini **TIDAK boleh** jadi dasar kalimat temuan.
  Paling banyak: disebut judulnya saja di daftar pustaka.

### Pagar 3 — TAMPILKAN sumbernya ke user
- User bisa **baca abstraknya sendiri** (dan klik link ke artikel asli).
- Kalau AI menulis sesuatu, user bisa **cek** apakah memang ada di abstrak.
⇒ Sesuai 3 pilar Bos: **NYATA** (bisa dibuktikan) · **TERKELOMPOK** ·
**TERPAGAR**.

---

## 4. ALUR BARU (sederhana, tidak bikin mesin baru)

```
User cari artikel
      ↓
Mesin ambil: judul + abstrak + jurnal + tahun + link  ← SEMUA data nyata
      ↓
Simpan. Beri penanda:
   • abstrak ADA    → ✅ siap dipakai
   • abstrak KOSONG → ⚠️ "isi terbatas" (jangan jadi dasar temuan)
      ↓
AI menulis bab → HANYA pakai judul+abstrak yang ADA
      ↓
User lihat daftar artikel + abstrak + tombol LINK   ← bisa cek sendiri
```

**Tidak ada**: unduh paksa, tebak isi, jalan masuk liar.

---

## 5. KATA-KATA DI LAYAR (perbaikan atas perintah Bos)

❌ **DILARANG** (kata lama): *"…supaya kamu bisa membukanya **sendiri** ya."*
✅ **GANTI** jadi: *"Tautan artikelnya kami sertakan di sini."*

**Pesan baru (3 keadaan):**

| Keadaan | Pesan |
|---|---|
| Berkas berhasil | *"Artikel tersimpan di berkas naskahmu ya."* |
| Terbuka tapi berkas tak terambil | *"Artikelnya terbuka. Tautannya kami sertakan di bawah ini."* |
| Berbayar / tertutup | *"Artikel ini tersedia di penerbit. Tautannya kami sertakan di bawah ini."* |
| Isi terbatas | *"Abstrak artikel ini tidak dicantumkan. Kami sediakan tautannya supaya bisa kamu cek langsung."* |

⚠️ **Aturan kata Bos:** JANGAN menyuruh user "unduh sendiri" — cukup
**sertakan tautan**.

---

## 6. 📊 RINGKAS: APA YANG BERUBAH

| Bagian | Sebelum | Sesudah |
|---|---|---|
| Sumber isi | hanya judul | **judul + abstrak** (nyata) |
| Berkas tak terambil | kirim DOI saja | kirim **tautan artikel** + pesan jujur |
| Artikel tanpa abstrak | tak ditandai | ditandai **⚠️ isi terbatas** |
| Kata "unduh sendiri" | ada | **DIHAPUS** |
| AI mengarang | tak ada pagar | **3 pagar** (hanya yang ada · tanda · tampilkan) |

---

## 7. ⚠️ YANG BELUM DIKERJAKAN (jujur)

- Pagar 1–3 **belum dikode** — ini rancangan, **butuh izin Bos**.
- `is_oa=True` yang menebak di `tautan_garuda()` **belum dihapus** (bagian
  dari perbaikan A).
- Uji: perlu dibuktikan AI **benar-benar** tidak mengarang saat abstrak kosong
  (uji bergigi: beri artikel tanpa abstrak → AI harus MENOLAK menulis temuan).
