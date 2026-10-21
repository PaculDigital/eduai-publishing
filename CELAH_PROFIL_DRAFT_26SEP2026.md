# ✅ CELAH INI SUDAH TERTUTUP — OPSI D (ACC Bos 26Sep26)

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **Status: SELESAI.** Bos memilih **OPSI D** 26Sep26.
> Solusi terpasang: server MEMBUAT dokumen kosong lebih dulu, jadi
> `file_id` selalu menunjuk berkas nyata (tidak ada nilai palsu `0`).
> Bukti: `_sketsa/uji_rute_alur.py` **42 LULUS / 0 GAGAL**.
> Dokumen penyelesaian: `OPSI_D_DOKUMEN_BARU_26SEP2026.md`.
> Isi di bawah ini DIPERTAHANKAN sebagai catatan proses berpikir
> (kenapa Opsi A/B/C tidak dipilih) — JANGAN dijadikan rencana kerja.

---

# 🧩 CELAH RANCANGAN: "MULAI BARU" BELUM PUNYA TEMPAT DI DB

**Tanggal:** 26Sep26 · **Ditemukan:** uji rute alur (3 gagal nyata) · **Status:** TUNGGU PUTUSAN BOS

---

## 🔍 MASALAHNYA (terbukti, bukan dugaan)

```
Tabel `profil_dokumen` dibuat dengan asumsi: SETIAP profil SELALU
terikat pada satu berkas naskah.

  file_id  : NOT NULL · ForeignKey('files.id') · UNIK (uq_profil_file)

Kenyataan rancangan Bos (putusan ①GERBANG BESAR):
  user boleh pilih "MULAI BARU" → isi jenjang/bidang/jenis/judul
  SEBELUM ada berkas naskah apa pun.

⇒ Tidak ada tempat menyimpan hasil 4 langkah itu.
⇒ Percobaan `file_id = 0` → DB menolak:
     "FOREIGN KEY constraint failed"
   (BENAR — id 0 tidak ada di tabel files. Mesin tidak salah.)
```

**Bukti uji:** `_sketsa/uji_rute_alur.py` → **28 LULUS / 3 GAGAL**
(D2 simpan 3 langkah · D3 langkah berikut · D4 simpan judul).

**Dampak kalau dibiarkan:** user bisa mengisi 4 langkah di layar, tapi
begitu disimpan **hilang** — dan dia akan mengulang dari nol tiap masuk.
Itu persis yang Bos tidak mau ("user kecewa → berhenti").

---

## 🚧 OPSI (Wulan belum koding apa pun — menunggu putusan)

### ⭐ OPSI A — `file_id` BOLEH KOSONG (NULL)
`file_id` diubah jadi **nullable** (`NULL` = belum terikat berkas).
Profil draft disimpan dengan `file_id = NULL`. Begitu user mengunggah
naskah → profil yang sama diisi `file_id`-nya.
- ✅ **Paling jujur**: "belum ada berkas" MEMANG tidak sama dengan
  "berkas id 0" — dibedakan, bukan disamarkan.
- ✅ UNIK `uq_profil_file` tetap aman: SQLite membolehkan banyak NULL.
- ✅ Sekali migrasi (`ALTER TABLE`), tidak mengubah kode lain yang
  membaca `file_id` (mereka tetap dapat angka saat berkas ada).
- ⚠️ Perlu migrasi DB produksi (backup dulu — rutin, sudah biasa).
- ⚠️ Kode lain yang `db.get(FileBerkas, prof.file_id)` WAJIB tahan
  `None` → Wulan sisir & tambah pagar (bukan tambal, memang benar).

### OPSI B — buat baris `files` "kosong" sebagai penampung
Saat user pilih "Mulai baru", server membuat 1 berkas placeholder
(`nama = '(draft)'`) lalu profil menunjuk ke sana.
- ❌ **Berisiko**: placeholder muncul di daftar berkas user sebagai
  naskah palsu; user bisa mengklik & bingung. Menyamar, bukan
  menyelesaikan.
- ❌ Menambah sampah di tabel `files` tiap user baru.

### OPSI C — simpan 4 langkah di `User` saja (bukan per naskah)
Kolom jenjang/bidang/mode/judul ditaruh di tabel `users`.
- ❌ Melanggar putusan ⑫ Bos ("simpan di akun **dan boleh timpa per
  naskah**"). Kalau user punya 2 naskah berbeda → judul saling menimpa.
- ❌ Nanti tetap butuh tempat per-naskah → kerja dua kali.

---

## 📌 REKOMENDASI WULAN

**OPSI A** — karena paling sesuai kenyataan (draft ≠ berkas), tidak
menyamar, dan menutup celah sampai akar. Migrasi kecil: 1 kolom
`file_id` → nullable + 1 sisir `None` di kode pembaca.

**Pertanyaan balik ke Bos (biar tidak salah pilih):**
kalau user pilih "Mulai baru" lalu **tidak pernah** mengunggah naskah —
profil draft itu tetap disimpan selamanya, atau perlu dibersihkan
otomatis (mis. >60 hari tidak disentuh)? Keputusan T3.3 (Kunci Naskah
+ arsip >60 hari) sepertinya satu keluarga — bisa digabung.

---

## ✅ YANG SUDAH JADI (biar jelas batasnya)

```
app/alur_awal.py      mesin: 38/0 (gerbang + 4 langkah + identitas)
app/rute_alur.py      rute: 28/31 (belum login, 9 rute terdaftar TOP-LEVEL)
  ✅ /alur/pintu · /alur/pilihan · /alur/contoh-judul   (tanpa login)
  ✅ /alur/petakan (3 PAGAR terbukti) · /alur/langkah
  ✅ /identitas GET+POST (logo boleh dilewati — terbukti)
  ❌ /alur/simpan → TERBLOKIR celah di atas
```

---
*Menunggu putusan Bos: Opsi A / B / C (Wulan sarankan A).*
