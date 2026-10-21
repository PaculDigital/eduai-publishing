# 📝 TAMBAH ARTIKEL DI TENGAH PEMBAHASAN BAB (06 Okt 2026)

> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Pertanyaan apakah user juga bisa tambah artikel di tengah-tengah pembahasan
> bab? Misal baru fokus di BAB II, kemudian user mau tambahkan artikel untuk
> bisa di bahas juga di bab tersebut."*
> *"Ya porsi 30% masih masuk akal agar tidak mengganggu core utama pembahasan
> bab."* ← ✅ **PUTUSAN: PORSI 30% DISETUJUI**

---

## ✅ PUTUSAN BOS (TERKUNCI)

| Hal | Putusan |
|---|---|
| Porsi artikel manual | **MAKS 30%** per bab |
| Alasan Bos (verbatim) | *"agar tidak mengganggu core utama pembahasan bab"* |

---

## 🎯 JAWABAN WULAN: **HARUS BISA — dan mesinnya SUDAH MENDUKUNG**

### Alasan kenapa HARUS bisa

Mahasiswa **memang bekerja per bab**, bukan sekaligus. Contoh nyata:
- Bab II = Tinjauan Pustaka → butuh **banyak** teori
- Bab III = Metode → butuh referensi **metode**, bukan teori
- Bab IV = Hasil → butuh referensi **pembanding** temuan

⇒ Kalau user **tidak bisa** menambah artikel saat sedang di Bab II, fiturnya
**tidak berguna** — user harus selesai semua bab dulu. Itu **tidak realistis**.

### ✅ Hasil cek kode — mesinnya sudah siap

| Kebutuhan | Sudah ada? |
|---|---|
| Kerangka **per bab** | ✅ `kerangka_bab.py` — ada bab **1, 2, 3** |
| Pengerjaan **satu bab saja** | ✅ `susun_rencana(bab=...)` + `bangun_isi(bab=...)` |
| **Pagar "bab dulu"** | ✅ Putusan Bos Q4 (26 Sep): *"Bab dulu = BAB I saja"* |
| **Ingatan per sub-bab** | ✅ `petakan()` di `state.py` + tabel `section_state` |
| Saring artikel **per bab** | ✅ `_pilih_relevan(artikel, naskah, judul)` |

⇒ Jadi **mekanisme per-bab sudah ada**. Yang perlu ditambah cuma:
**"tambah artikel manual" ditempelkan ke alur bab yang sedang dibuka.**

---

## 💡 IDE WULAN — 3 hal yang bikin ini rapi

### IDE 1 — 🚨 "Artikel punya SEBAB (bab mana dia dipakai)"

Ini **ide terpenting Wulan**, jawaban langsung pertanyaan Bos:

**Setiap artikel yang ditambahkan WAJIB ditandai: dipakai di Bab berapa.**

```
Tambah artikel untuk:  [ BAB II — Tinjauan Pustaka ▾ ]
                                              ↑ bukan ketik bebas, dropdown
   [ 10.29040/jie.v4i01.900        ]  [ Tambahkan ]
```

**Kenapa ini penting:**
| Tanpa penanda bab | Dengan penanda bab |
|---|---|
| Artikel Bab II bisa **nyasar** ke Bab IV | Artikel **selalu di bab yang benar** |
| Bingung "artikel ini buat apa?" | Jelas: *"dipakai di Bab II"* |
| Porsi 30% dihitung **global** (bab IV penuh artikel bab II) | Porsi 30% dihitung **per bab** ✅ (sesuai putusan Bos) |
| Daftar pustaka bisa **tidak sinkron** | Semua artikel bab II **keluar di daftar pustaka** |

⇒ **Ini yang membuat aturan 30% bisa dijalankan dengan adil** — kalau tanpa
penanda bab, "30%" jadi tidak jelas 30% dari apa.

### IDE 2 — Porsi 30% dihitung & ditampilkan JELAS

```
📚 Artikel untuk BAB II — Tinjauan Pustaka

   Dari AI        : 12 artikel   (porsi manual: 0/5)
   Saya tambah    :  3 artikel   ✅ masih boleh +2

   [ + Tambah artikel ]
```
Kalau sudah penuh:
```
   Dari AI        : 12 artikel
   Saya tambah    :  5 artikel   ← batas tercapai

   Kamu sudah menambah 5 artikel (30% dari bab ini).
   Sisanya dari pilihan AI supaya pembahasan tetap fokus 😊
   [ sudah penuh ]
```
⇒ Nada **hangat**, bukan melarang.

### IDE 3 — Artikel bisa DIPAKAI ULANG di bab lain (tanpa cari lagi)

Kalau user tambah 1 artikel di Bab II, lalu ternyata **sama** dibutuhkan di Bab IV
→ **boleh dipakai lagi**, **tanpa dihitung dua kali**.

```
Artikel ini sudah dipakai di Bab II.
 [ ✔ Pakai juga di Bab IV ]   ← 1 klik, tidak menambah kuota
```
⇒ Hemat kerja user, daftar pustaka tetap **satu** (tidak dobel).

---

## 📊 CARA PORSI 30% DIHITUNG (usul Wulan — biar jelas)

```
BAB II punya 12 artikel dari AI
   ↓
Batas manual = 30% × (12 + manual)
   ↓
Maks manual ≈ 5 artikel   (12 AI + 5 manual = 17; 5/17 = 29,4% ✅)

Kalau AI hanya dapat 4 artikel:
Maks manual ≈ 1 artikel   (4 + 1 = 5; 1/5 = 20% ✅)

Kalau AI dapat 0 artikel (gagal total):
   → Boleh manual lebih banyak (mis. maks 10)
     karena tidak ada "core" yang bisa diganggu
```

⚠️ **Poin terakhir perlu keputusan Bos** — kalau AI gagal total, apakah porsi
30% **dilonggarkan** (biar user tidak terkunci), atau **tetap 30%** (= user
hampir tidak bisa menambah apa pun)?

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Yang sudah bisa:** pengerjaan per bab, penyaringan per bab, ingatan per
   sub-bab. **Yang belum:** penanda "artikel ini untuk bab berapa" — ini
   **perlu ditambah** (tabel/kaitan baru).
2. **`bangun_isi()` masih cari ulang sendiri** (`kerangka.py:354`) → belum
   menerima artikel kiriman. **Perlu 1 perbaikan kecil** (sudah dicatat di
   berkas `JAWABAN_ARTIKEL_MANUAL_SITASI_06OKT2026.md`).
3. **Wulan BELUM memeriksa** apakah hasil per bab sudah **tersimpan** (supaya
   user bisa lanjut Bab III tanpa mengulang). Bila belum, itu perlu ditambah.
4. **Risiko "kunci di tengah jalan":** kalau user sudah menambah 5 artikel di
   Bab II, lalu AI **dijalankan ulang** dan mendapat 3 artikel lagi → porsi 30%
   jadi **berubah**. Perlu aturan: porsi dihitung **saat AI selesai**, bukan
   mengunci angka mati.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Artikel ditandai "untuk bab berapa"** (IDE 1) — setuju?
2. **Porsi 30% dihitung PER BAB** (bukan global) — betul begitu?
3. Kalau **AI gagal total** (0 artikel) → porsi manual **dilonggarkan**, atau
   tetap 30%?
4. **Tambah artikel hanya saat bab itu dibuka**, atau user bisa menambah ke
   **bab mana saja** kapan saja?
5. **Artikel boleh dipakai ulang** di bab lain tanpa hitung dobel (IDE 3)?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **PUTUSAN BOS TERKUNCI: porsi manual = MAKS 30% per bab**
- [x] **TERUKUR**: mesin per-bab sudah ada (`kerangka_bab.py`, `susun_rencana(bab=)`)
- [x] Jawaban Wulan: **HARUS BISA** — user memang kerja per bab
- [ ] Ditunggu putusan Bos (5 pertanyaan di atas)
- [ ] DILARANG dikoding sebelum Bos bilang mulai
