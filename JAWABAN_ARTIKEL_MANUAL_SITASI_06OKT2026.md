# ✅ JAWABAN — ARTIKEL MANUAL: MASUK DAFTAR PUSTAKA & DIPAKAI SITASI? (06 Okt 2026)

> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Ok setuju. Tapi kalo user juga cari artikel secara manual apakah juga nanti
> di masukkan dalam daftar pustaka dan juga di pakai sebagai sitasi dalam
> pembuatan bab nya"*

---

## 🎯 JAWABAN WULAN: **HARUS — dan mesinnya SUDAH SIAP MENERIMA**

Wulan cek kode. Jawabannya **YA, harus masuk** — karena kalau tidak, fitur
"cari manual" jadi **sia-sia** (user cari susah-susah, hasilnya tidak dipakai).

---

## 🔍 HASIL CEK KODE (bukan dugaan)

### Syarat artikel masuk daftar pustaka (`pustaka.py:696`)
```python
def daftar_pustaka_apa7(artikel):
    """Susun daftar pustaka APA 7 dari artikel TERVERIFIKASI saja.
    Aturan (dari skill): HANYA referensi terverifikasi yang masuk daftar."""
    for r in artikel:
        if r.get('doi_status') not in ('verified', 'no_doi'):
            continue                       # unverified JANGAN masuk
        if not r.get('doi_status') == 'verified' and not r.get('garuda_id'):
            continue                       # tanpa DOI tapi ada GarudaID → boleh
```

### 🔑 TEMUAN PENTING — **syaratnya TEMPAT, bukan ASAL**
Fungsi ini **tidak peduli artikel itu dari AI atau dari user.**
Yang ia periksa cuma: **apakah artikelnya sah secara bukti?**

| Syarat | Artinya |
|---|---|
| `doi_status = 'verified'` | DOI-nya **benar ada di CrossRef** |
| atau `doi_status = 'no_doi'` **+ punya `garuda_id`** | Artikel Garuda **boleh tanpa DOI** |
| Kalau tidak terverifikasi | **TIDAK masuk** daftar pustaka |

⇒ **KESIMPULAN: artikel manual BISA masuk daftar pustaka — asal dia lolos
audit yang sama.** Mesinnya **sudah siap**; tidak perlu diubah.

### Mesin pendukung yang juga sudah ada
| Fungsi | Letak | Guna untuk artikel manual |
|---|---|---|
| `audit_doi(doi)` | `pustaka.py:381` | ✅ **cek DOI ke CrossRef** (anti-karangan) |
| `daftar_pustaka_apa7()` | `pustaka.py:696` | ✅ susun APA 7 (asal terverifikasi) |
| `ringkas_untuk_ai()` | `pustaka.py:727` | ✅ bentuk teks siap masuk prompt AI |
| `_pilih_relevan()` | `kerangka.py:406` | ✅ saring agar nyambung naskah |

---

## 🎯 ALUR YANG WULAN USULKAN (kompak)

```
User cari manual → dapat artikel
        ↓
AUDIT DOI (audit_doi) ← pagar anti-karangan, SAMA seperti artikel AI
        ↓
   ┌─ LOLOS → tanda ✅ TERVERIFIKASI
   │    → boleh masuk DAFTAR PUSTAKA
   │    → boleh DIPAKAI SITASI saat tulis bab
   │
   └─ TIDAK LOLOS → tanda ⚠️ BELUM TERVERIFIKASI
        → boleh DILIHAT (user yang putuskan)
        → TIDAK masuk daftar pustaka
        → TIDAK dipakai sitasi
        → pesan jujur: "artikel ini belum bisa diverifikasi — 
           tidak akan dipakai sebagai sitasi"
```

### Contoh tampilan ke user
```
🔎 Hasil pencarian kamu:

 1. Yusnia (2020) — Customer Experience...      ✅ TERVERIFIKASI
 2. Smith (2021) — The Role of...               ✅ TERVERIFIKASI
 3. Blog Sumber Tidak Jelas (2019)...           ⚠️ BELUM TERVERIFIKASI
    └ artikel ini tidak akan dipakai sebagai sitasi
```

⇒ **Prinsip penting:** user **tetap boleh mencari apa saja** (kebebasan), tapi
yang **masuk naskah & daftar pustaka** hanya yang **terbukti nyata**. Ini
melindungi mahasiswa dari sitasi palsu **dan** melindungi reputasi EduAi.

---

## ⚠️ SATU HAL YANG WULAN HARUS SEBUT JUJUR (temuan penting)

**Ada 1 tempat yang BELUM bisa menerima artikel manual** — Wulan temukan dari kode:

Di `bangun_isi()` (`kerangka.py:354`) — fungsi yang **menulis bab** — saat ini:
```python
h = _pustaka.cari_semua(tema_kerja)     # ← dia CARI SENDIRI
artikel = h.get('artikel') or []
```
⇒ **Fungsi ini mencari ulang dari nol**, **tidak menerima artikel kiriman user.**

**Artinya sekarang:** kalau user menambah artikel manual, lalu menekan
"Setuju tulis bab" — **artikel manual itu BELUM tentu terpakai**, karena
`bangun_isi()` mencari sendiri, bukan memakai daftar gabungan.

### 🔧 Perbaikan yang Wulan usulkan (kecil, satu titik)
`bangun_isi()` diberi **parameter baru**: `artikel_tambahan` (opsional).
```
alur baru:
  daftar = cari_semua(tema)              ← dari AI
  daftar = daftar + artikel_manual_user  ← dari user (sudah diaudit)
  daftar = dedup(daftar)                 ← buang kembar
  daftar = _pilih_relevan(daftar, ...)   ← saring
        ↓
  bangun_isi(..., artikel_dipakai=daftar)  ← TERIMA kiriman, jangan cari ulang
```
⇒ **Perubahan kecil** (1 parameter + 1 jalur), **tidak membongkar** alur lama.
Kalau `artikel_tambahan` kosong → **perilaku lama tetap jalan persis.**

---

## 📌 KESIMPULAN — 3 jawaban tegas

| Pertanyaan Bos | Jawaban |
|---|---|
| Artikel manual **masuk daftar pustaka**? | ✅ **Ya** — asal lolos audit DOI |
| Artikel manual **dipakai sitasi saat buat bab**? | ✅ **Ya** — dan **harus**, kalau tidak fiturnya sia-sia |
| **Rumit?** | ❌ **Tidak** — mesinnya sudah ada; **1 perbaikan kecil** di `bangun_isi()` |

⇒ Sekali lagi: **mesinnya sudah satu.** Auto AI dan manual memakai
`pustaka.cari_semua()` + `audit_doi()` + `daftar_pustaka_apa7()` yang **sama**.
Yang perlu ditambah cuma: **artikel manual boleh DIIKUTSERTAKAN**.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Artikel manual yang TIDAK lolos audit** → tetap ditampilkan (dengan tanda
   ⚠️) tapi tidak dipakai? Atau **tidak ditampilkan sama sekali**?
2. **Siapa yang memutuskan artikel mana dipakai** saat tulis bab —
   semua yang lolos dipakai otomatis, atau **user memilih** mana yang dipakai?
3. **Pagar P3 harus tetap** ("hanya terverifikasi yang masuk daftar pustaka") —
   setuju? (Wulan sarankan **YA**, itu yang menjaga mutu)
4. **Perbaikan `bangun_isi()`** (menerima artikel kiriman) — boleh dikerjakan
   saat fitur ini dibangun? (Wulan sarankan ya; kecil, tidak membongkar)

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **TERUKUR**: `daftar_pustaka_apa7()` syaratnya **status verifikasi, BUKAN asal** → artikel manual bisa masuk
- [x] **TERUKUR**: `audit_doi()` sudah ada → bisa dipakai untuk artikel manual
- [x] **TEMUAN**: `bangun_isi()` masih **cari ulang sendiri** → perlu 1 perbaikan kecil
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
