# 🧩 IDE — 2 KASUS YANG BOS TANGKAP (06 Okt 2026)

> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Jadi misal kasus, user tidak puas atas pencarian AI dan akan mencari manual
> lagi, bagaimana?"*
> *"Dan bagaimana jika user mau mencari artikel yang lain dan tidak ada
> hubungannya dengan workspace sekarang? Apa ide kamu?"*

---

## 📌 HASIL CEK KODE (06 Okt 2026 — bukan dugaan)

| Yang dicek | Kenyataan |
|---|---|
| Jumlah folder per user | **0 folder** (belum ada satu pun di produksi) |
| Berkas tanpa folder | **51 berkas** (semua) |
| Model `Folder` | `models.py:124` — punya `user_id` → **user BOLEH punya BANYAK folder** |
| Aturan tertulis di kode | *"SATU TINGKAT saja (tidak bersarang) — user HP mudah bingung"* |
| Hapus folder | *"TIDAK menghapus dokumen; dokumen jadi 'tanpa folder'"* |

⇒ **Penting:** user **SUDAH boleh punya banyak workspace** (folder banyak =
wajar, sudah dirancang begitu). Yang belum ada **cuma isinya** (belum ada
yang bikin folder).

---

## KASUS 1 — "User tidak puas pencarian AI, mau cari manual lagi"

### 🎯 Jawaban Wulan: **harus bisa, dan GRATIS (tidak kena token lagi)**

**Alasannya — logika bisnis, bukan teknis:**

| Keadaan | Kalau user harus bayar lagi | Kalau GRATIS |
|---|---|---|
| Hasil AI kurang pas | User merasa **dihukum 2×** → marah | User tenang, coba sendiri |
| Rating fitur | **Jelek** ("AI-nya gak guna, malah disuruh bayar") | Baik |
| Kepercayaan | Hilang | Terjaga |

⇒ **Yang salah = hasil AI, bukan user.** Jangan bebankan biaya koreksi ke user.

### 🔴 PAGAR PENTING — jangan sampai jadi celah gratis

Bahayanya kalau "Auto AI gagal → cari manual gratis" tanpa pagar:
```
Pencarian AI: kembali kosong → user dapat "tiket gratis" cari manual
        ↓
User ulang-ulang: minta AI (sengaja kata kunci aneh biar kosong)
   → dapat tiket gratis → cari manual sepuasnya
        ↓
= CELAH "CARI GRATIS TAK TERBATAS" (rugi Bos)
```

**USULAN WULAN — "Tiket Coba Ulang":**
| Aturan | Nilai |
|---|---|
| Syarat dapat tiket | Hasil AI **kosong** ATAU **≤2 artikel** (benar-benar gagal) |
| Jumlah tiket | **1× per workspace** (bukan per pencarian) |
| Masa berlaku | Hari itu saja (besok hangus) |
| Kalau hasil AI **BANYAK** tapi user tidak suka | **TIDAK dapat tiket** — user tetap bayar kalau mau cari sendiri |
| Kalau sudah punya tiket tapi tidak dipakai | Hangus, tidak menumpuk |

⇒ **Adil dua pihak:** user yang benar-benar dirugikan dapat kesempatan
koreksi gratis; user yang cuma "merasa kurang" tetap bayar.

### 📌 Perbedaan ini WAJIB dijelaskan di layar (jangan diam-diam)
```
Pencarian AI belum membuahkan hasil untuk judulmu.
Kamu dapat 1 kesempatan cari manual GRATIS hari ini.
   [ Coba cari sendiri → ]
```
Kalau hasilnya banyak tapi user mau cari lain:
```
Masih ada 12 artikel dari AI. Mau cari dengan kata kunci sendiri?
(Pencarian sendiri memakai 1 Token Revisi)
   [ Cari sendiri ]   [ Pakai yang ada ]
```
⇒ **Jujur & tidak mengejutkan.** User tahu harganya sebelum menekan.

---

## KASUS 2 — "User mau cari artikel lain, tidak berhubungan dengan workspace ini"

### 🎯 Jawaban Wulan: **harus bisa — dan ini justru FITUR, bukan masalah**

Kenapa? Karena mahasiswa **memang** butuh:
- makalah untuk **mata kuliah lain** (bukan skripsi),
- referensi untuk **penelitian kedua**,
- bacaan **pribadi** (bukan akademik),
- **bandingan** dari bidang lain.

**Poin penting (terukur):** `Folder` punya `user_id` → user **BOLEH punya banyak
workspace**. Jadi wadahnya **sudah ada**. Yang perlu diputuskan: **hasil
pencarian "lepas" itu disimpan di mana?**

### 💡 USULAN WULAN — pilihan saat simpan (bukan memaksa)

Setelah user selesai cari, saat mau simpan ke workspace, **beri pilihan**:
```
Simpan hasil pencarian ke mana?
  ( ) 📁 Skripsi Saya          ← workspace yang sedang dibuka
  ( ) 📁 Makalah Semester 7    ← workspace lain milik user
  ( ) ➕ Buat workspace baru...  ← mis. "Referensi Kuliah X"
  ( ) ⏭ Simpan tanpa workspace  ← lalu lintas, bisa dipindah nanti
```

⇒ **Tidak memaksa.** User pilih sendiri. Sistem tidak menebak.

### 🔴 TAPI INI YANG PALING PENTING — jangan kunci ke workspace

**Wulan usulkan: alat cari jangan MENEMPEL pada workspace.**

| Model A (salah) | **Model B (usulan Wulan)** ⭐ |
|---|---|
| Alat cari hanya ada di dalam workspace | Alat cari **berdiri sendiri** (tab 📚 Referensi di dashboard) |
| User harus masuk workspace dulu untuk cari | User bisa cari **kapan saja**, tanpa pilih workspace |
| Workspace = kotak tertutup | Workspace = **tempat menyimpan hasil**, bukan pintu masuk |
| Hasil "nyangkut" di 1 workspace | Hasil **disimpan sesuai pilihan user** |

⇒ Analogi: **Google Scholar tidak menempel di folder** — kita cari dulu, baru
simpan ke folder mana. **Itu yang user harapkan.**

---

## 🎯 GABUNGAN IDE WULAN (2 kasus + ide sebelumnya)

```
        Tab 📚 Referensi  (berdiri sendiri, bisa diakses kapan saja)
                    │
        ┌───────────┴───────────┐
        │                       │
  🤖 Bagian AI             🔎 Bagian Pencarian Saya
  (dari tema naskah)       (judul / kata kunci sendiri)
        │                       │
        │                  1 token (kecuali ada tiket)
        │                       │
        └───────────┬───────────┘
                    │
            HASIL (dikelompokkan per variabel)
                    │
        ┌───────────┴───────────┐
        │   Simpan ke mana?     │ ← user pilih sendiri
        │  ○ Skripsi Saya       │
        │  ○ Workspace lain     │
        │  ○ Buat baru          │
        │  ○ Tanpa workspace    │
        └───────────────────────┘
```

⇒ **Satu alat, dua jalur, hasil fleksibel.** Tidak ada yang terkunci ke
workspace, dan user tidak pernah dipaksa.

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Belum ada satu folder pun di produksi** (0 folder, 51 berkas tanpa folder).
   Artinya: fitur workspace **belum pernah dipakai orang sungguhan**. Kalau
   langsung menumpuk fitur jurnal di atasnya, **risikonya belum teruji.**
   Wulan sarankan **buat 1 workspace dulu** untuk mencoba alur ini.
2. **"Tiket coba ulang" harus dihitung di server.** Kalau disimpan di browser
   (seperti pola Statistik Lab), user bisa hapus cookie & dapat tiket lagi.
   ⇒ **wajib server-side** (per user + per workspace).
3. **Kalau user punya 10 workspace**, jumlah pencarian bisa banyak → biaya API
   naik. Token tetap penjaga utama; tiket hanya **pengecualian langka**.
4. **"Tanpa workspace" = berkas nyangkut.** Perlu disiapkan: cara user
   memindahkan hasil "lepas" ke workspace (rute pindah berkas **sudah ada**:
   `/folder/pindah`).

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Hasil AI kurang bagus → cari manual GRATIS** (usul Wulan: ya, dengan
   pagar "Tiket Coba Ulang") — setuju?
2. Berapa syarat dapat tiket: hasil **kosong** saja, atau **≤2 artikel**?
3. **Alat cari berdiri sendiri** (bisa dipakai tanpa pilih workspace) —
   setuju? (Wulan sarankan YA)
4. **Simpan ke workspace mana** = user pilih sendiri — setuju?
5. Perlu opsi **"tanpa workspace"** (simpan lepas), atau **wajib** pilih
   workspace?
6. **Pencarian lepas (bukan akademik)** — dibiarkan masuk juga, atau ada
   penanda "bukan untuk skripsi"?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Kode diperiksa: `Folder.user_id` → user BOLEH banyak workspace; kenyataan
      = **0 folder** di produksi
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
