<!-- RANCANGAN (RIWAYAT) — SOT: bukan sumber status. Dilarang koding sampai Bos bilang "mulai". -->
# 📐 RANCANGAN v3 — PROFILER POLA PENULISAN (murni kode, tanpa Jev)

> **v1** = rancangan Bos · **v2** = tambahan Wulan (3 butir) · **v3** = koreksi Bos atas v2.
> **Vonis Bos atas v2:** §8.1 disetujui + 2 perbaikan · **§8.2 DITOLAK** (solusi salah sasaran) ·
> §8.3 disetujui + 1 perbaikan. ⇒ v3 = hasil koreksi.
> **Perintah Bos:** *"Ya"* — rancang profiler pola.
> **Dasar:** Uji P gagal (33%/17%) → **JANGAN pakai Jev untuk baca pola.**
> **Prinsip:** AI menulis kata · kode menulis angka **dan pola**.
> **Status:** 📝 RANCANGAN. Nol baris kode diubah.

---

## 0. KENAPA KODE (bukan Jev)

Untuk revisi, AI butuh pola *level bagian* (skema nomor BAB ini apa? gaya judulnya?
penanda butirnya?) — semua bisa diturunkan **deterministik dari label surveyor**:
"2.1, 2.2, 2.3" ⇒ skema dotted-2 (100% tepat, nol biaya, tidak goyang).
Uji P menguji klasifikasi per-baris oleh Jev — **pertanyaan yang salah** untuk kebutuhan ini.
Yang dibutuhkan bukan "Jev menebak pola", melainkan **"kode membaca pola dari peta"**.

---

## 1. MASUKAN & KELUARAN

**Masuk:** peta induk `peta3_jev.petakan()` — `label` per baris, `gabung` (BAB merge), `baris` mentah.

**Keluar:**
- **Profil per BAB** (§2) — dipakai kontrak AI revisi & hakim T④.
- **Pola per baris** (§3) — kolom `pola`: judul_isi / butir / tabel / paragraf / tidak_jelas.

**Rentang BAB** = dari baris label 'bab' sampai baris 'bab' berikutnya (atau akhir naskah).
BAB dari `gabung` ikut dihitung.

---

## 2. PROFIL PER BAB — aturan deteksi (deterministik)

### 2.1 `skema_nomor` — skema penomoran sub-bab se-BAB
```python
def skema_nomor(subbabs):  # [(i, teks), ...] label 'subbab' dalam 1 BAB
    hasil = []
    for i, t in subbabs:
        s = t.strip()
        if re.match(r'^\d+\.\d+\.\d+\b', s): hasil.append('dotted-3')   # 2.1.1
        elif re.match(r'^\d+\.\d+\b', s):   hasil.append('dotted-2')   # 2.1
        elif re.match(r'^[A-Z]\.\s', s):    hasil.append('alpha-dot')  # A.
        elif re.match(r'^\d+\)\s', s):      hasil.append('paren-num')  # 1)
        else:                               hasil.append('tanpa-nomor')
    unik = set(hasil)
    return unik.pop() if len(unik) == 1 else 'campuran'
```
> 🔧 **v2 §8.2: `num-dot` (`^\d+\.\s`) DIHAPUS dari sini.** Lihat §8.2.

### 2.2 `gaya_judul` — kapitalisasi judul
Kupas awalan nomor (`^(\d+\.)+\s*|^[A-Z]\.\s*|^\d+\)\s*`), lalu per judul:
`caps` / `title` / `sentence`. Agregasi se-BAB seperti §2.1; beda ⇒ `campuran`.

### 2.3 `butir` — penanda daftar di dalam bagian
Pindai baris label `biasa`/`paragraf` dalam rentang BAB, cocokkan awal baris:
- `^[a-z]\.\s` → `alpha-dot` (a.)
- `^\d+\.\s` → `num-dot` (1.)
- `^[-•–]\s` → `dash`
- tidak ada ⇒ `tidak-ada`; lebih dari satu ⇒ `campuran`

### 2.4 `nomor_terakhir` — untuk penomoran lanjutan
Urai nomor dotted, kelompokkan per induk: "2.1".."2.4" ⇒ induk "2", maks 4 ⇒ berikutnya "2.5".
Untuk dotted-3 sama, per induk "2.1".

### 2.5 `ada_tabel`
`True` jika ada baris pipa ≥2 atau caption Tabel dalam rentang BAB.

---

## 3. POLA PER BARIS — pemetaan deterministik (tanpa Jev)

```python
def pola_baris(label, teks):
    t = teks.strip()
    if label in ('bab', 'subbab'):
        return 'judul_isi'
    if t.count('|') >= 2:
        return 'tabel'
    if re.match(r'^([a-zA-Z]|\d+)[\.\)]\s|^[-•–]\s', t):
        return 'butir'
    return 'paragraf'          # default aman
```
> 🔧 **v2 §8.1: tambah gerbang `tidak_jelas` SEBELUM jatuh ke `paragraf`.** Lihat §8.1.

---

## 3b. POLA BERTETANGGA (v2 §8.3 — jawaban permintaan Bos)

Bos: *"harus ada yang melihat pola sekitarnya seperti **beretangga** juga... Jadi **tidak aneh** polanya."*

Profil per BAB = **rata-rata se-bab** (bukan tetangga). Fungsi ini melengkapi:
```python
def pola_tetangga(peta, posisi, jendela=1):
    """Lihat pola bagian sebelum & sesudah posisi (bukan isinya).
    v3: LEWATI tetangga ber-pola 'tidak_jelas' — itu bukan pola, tidak ada sinyal."""
    kiri  = _pola_sah(peta, posisi - jendela)   # None kalau tidak_jelas/kosong
    kanan = _pola_sah(peta, posisi + jendela)
    if kiri and kiri == kanan:
        return kiri            # sepakat → pakai itu
    if kiri:
        return kiri            # tidak sepakat → ikut KIRI (paling dekat)
    if kanan:
        return kanan
    return None                # → jatuh ke profil BAB → default

def _pola_sah(peta, pos):
    p = pola_pada(peta, pos)
    return None if p in (None, 'tidak_jelas') else p   # v3
```

---

## 4. MESIN RENUMBER (v2 — spek, belum dikoding)

```python
def sisip_subbab(peta, idx_bab, setelah_nomor, judul_baru):
    """Sisip sub-bab baru setelah `setelah_nomor`.
    Kembalikan (peta_baru, daftar_perubahan)."""
```
**Pagar (wajib):**
- TOLAK jika `skema_nomor == 'campuran'` (jangan tebak).
- **Cascade:** nomor yang digeser ikut menggeser anaknya (2.2→2.3 ⇒ 2.2.1→2.3.1).
- **Referensi silang:** pindai `sub[-\s]?bab\s+<nomor_lama>` di seluruh naskah ⇒ TANDAI.
- Jangan sentuh nomor di luar BAB ini. Jangan "perbaiki" typo penulis.
- Daftar isi / daftar tabel ⇒ tandai perlu regenerasi.

---

## 5. INTEGRASI (Opsi C Bos)

```python
def pola_untuk_titik(peta, posisi, permintaan_pembimbing=None):
    # v3 — SUSUNAN 5 TINGKAT (koreksi Bos: proteksi 'tidak_jelas' DI TARGET,
    #                            bukan di tetangga)
    if permintaan_pembimbing and 'pola' in permintaan_pembimbing:
        return permintaan_pembimbing['pola']       # ① PEMBIMBING menimpa
    sendiri = pola_pada(peta, posisi)
    if sendiri == 'tidak_jelas':
        return 'tidak_jelas'                       # ② TARGET tak pasti ⇒ LARANG
    if sendiri:
        return sendiri                             #    target sendiri sudah pasti
    tetangga = pola_tetangga(peta, posisi)          # ③ TETANGGA (lewati tidak_jelas)
    if tetangga:
        return tetangga
    profil = profil_bab_terdekat(peta, posisi)
    if profil:
        return profil                               # ④ PROFIL BAB (rata-rata)
    return PROFIL_DEFAULT                           # ⑤ aman: paragraf
```
⚠️ **Kunci koreksi Bos (v3):** `tidak_jelas` = **tidak ada sinyal pola**, bukan pola.
⇒ Proteksinya berposisi **TARGET** (②: kalau titiknya sendiri tak pasti → larang),
**bukan** diwariskan lewat tetangga. Tetangga `tidak_jelas` cuma **dilewati** (③).

**Kontrak AI revisi:**
```
Prompt: "Tulis ISI saja. BENTUK: <skema>, <gaya_judul>, <butir>.
         NOMOR: <nomor_baru> (sudah ditetapkan, JANGAN mengarang)."
Validasi kode: judul output diawali nomor yang ditetapkan?
```
**Kaitan modul (sesuai H2 — terpisah, tidak digabung):**
- Konsumen: `peta3_jev` (surveyor, tidak diubah) → `pola_penulisan.py` (BARU, 1 modul)
  → hakim T④ `berurutan` + kontrak AI revisi.

---

## 6. VALIDASI (tanpa Jev, jadi cepat)

1. Jalankan profiler di peta Asih (fid=81) + Wulandari (fid=115, jalur resmi).
2. Verifikasi manusia ±5 menit: cocokkan profil per BAB dengan naskah.
3. Kriteria lolos: **100%** pada peta yang benar (deterministik — kalau salah, itu bug regex).
3b. **Validasi `AMBANG_KAR` (§8.1)**: jalankan profiler di Asih + Wulandari, hitung
    berapa baris jadi `tidak_jelas`. Kalau **kebanyakan** (mis. >20% naskah rusak/lapor),
    ambang salah ⇒ **lapor ke Bos, jangan kunci sendiri**. (Ambang 40 = usulan, BUKAN kunci.)

---

## 7. PAGAR

- P1: **Nol panggilan Jev** di profiler. Pola = baca peta, bukan tanya model.
- P2: `campuran` ⇒ lapor, jangan renumber otomatis.
- P3: Jangan perbaiki typo/penomoran penulis — hanya sisip baru yang menggeser.
- P4: Referensi silang yang terdampak WAJIB ditandai (tidak boleh putus diam-diam).
- P5: Tidak ada tabel/kolom DB baru untuk v1 (profil dihitung on-the-fly dari peta).
- **P6 (v2 §8.1):** baris tak yakin ⇒ `tidak_jelas`, AI **DILARANG** menyentuh.
- **P7:** profiler **TIDAK BOLEH memutuskan label**. Profiler = pembaca, bukan penebak.
- **P8 (v3 §8.1):** gerbang `tidak_jelas` **HANYA untuk label `biasa`**. Label `paragraf`
  dari surveyor **DIPERCAYA** (kecuali sinyal struktur jelas: pipa → tabel,
  penanda butir → butir). Gerbang tidak boleh menimpa surveyor.
- **P9 (v3 §8.2):** `num-dot` **DIPERTAHANKAN** (deskriptif). Pencegahan baris salah
  label = tugas **HAKIM** (heuristik curiga), **bukan** profiler.

---

## 8. TAMBAHAN (v2 usulan Wulan → v3 hasil koreksi Bos)

> **Ringkas vonis Bos:** §8.1 ✅ disetujui (+2 perbaikan) · §8.2 ❌ **ditolak** ·
> §8.3 ✅ disetujui (+lewati `tidak_jelas`).
> **Bonus temuan Bos:** §8.2 (v2) ↔ §10.2 (v2) saling bertentangan → **§8.2 yang mengalah.**

### 8.1 — Pola `tidak_jelas` (isi lubang nyata)
**Masalah:** di naskah Wulandari, baris label `'biasa'` banyak yang sebenarnya **pecahan tabel**
(`AyuMeera)`, `(Regina – Div AyuMeera)`, `5 Adyatma`). Tidak mengandung `|` → **jatuh ke `paragraf`**.
⇒ AI dikasih tahu "ini paragraf" padahal pecahan tabel → **AI bisa bikin paragraf dari pecahan.**

**Perbaikan v3 (ganti `return 'paragraf'`) — gerbang HANYA untuk label `biasa`:**
```python
def pola_baris(label, teks):
    t = teks.strip()
    # ① label SURVEYOR = SUDAH DIPUTUSKAN Jev → DIPERCAYA (kecuali sinyal struktur jelas)
    if label in ('bab', 'subbab'):
        return 'judul_isi'
    if label == 'paragraf':          # ← v3: surveyor sudah bilang paragraf
        if t.count('|') >= 2:  return 'tabel'      # sinyal struktur jelas
        if re.match(BUTIR_RE, t): return 'butir'   # sinyal struktur jelas
        return 'paragraf'            # PERCAYA surveyor, jangan tebak ulang (P7)
    # ② label 'biasa' / lain → barulah gerbang kepastian berlaku
    if t.count('|') >= 2:  return 'tabel'
    if re.match(BUTIR_RE, t): return 'butir'
    if len(t) < AMBANG_KAR or not re.search(r'[.!?]["\')\]]?$', t):
        return 'tidak_jelas'         # fragmen / potongan / tak berujung titik
    return 'paragraf'
```
**Aturan konsumen (dua-duanya):**
- pola `tidak_jelas` ⇒ AI **DILARANG menyentuh** bagian itu (proteksi **di target**).
- `tidak_jelas` **BUKAN pola** (tidak ada sinyal) ⇒ **diabaikan saat jadi tetangga** (§3b).

⚠️ **`AMBANG_KAR` (usul 40) = SEMENTARA.** Wajib divalidasi di peta Asih (fid=81) +
Wulandari (fid=115) **sebelum dikunci** (§6 langkah 3b).

⚠️ **Catatan koreksi Bos (v3):** v2 salah menerapkan ambang panjang ke SEMUA baris —
itu profiler **menebak ulang** surveyor, melanggar P7 sendiri. Kini label `paragraf`
dari surveyor **dipercaya**; gerbang hanya menyaring baris yang surveyor belum
pasti (`biasa`).

### 8.2 — ~~§2.1 vs §2.3 BENTROK~~ ❌ **USUL DITOLAK BOS (v3)**

**Usul v2 (DITOLAK):** hapus `num-dot` dari §2.1, `1.` tunggal ⇒ selalu butir.

**ALASAN PENOLAKAN BOS (v3, dikunci):**
1. **Konfliknya TIDAK PERNAH terjadi secara perilaku.** §2.1 memindai label **`subbab`**;
   §2.3 memindai label **`biasa`/`paragraf`**. **Populasinya beda** — label sudah
   mendisambiguasi lebih dulu. Satu regex di dua tempat ≠ satu baris dua putusan.
2. **Menghapus `num-dot` malah merusak deskripsi:** skripsi bernomor datar ("1.", "2.", "3.")
   akan terbaca `tanpa-nomor` **padahal bernomor** ⇒ skema_nomor salah deskripsi.
3. **Melanggar P7 & §10.2 v2 sendiri:** "`1.` tunggal ⇒ selalu butir" **adalah regex
   memutuskan bentuk** — persis yang dilarang Bos 08 Okt.
4. **Tidak mencegah kasus L000608:** baris itu salah karena **surveyor (Jev)** melabelinya
   `subbab`, **bukan** karena profiler. Titik salahnya di surveyor, bukan di §2.1.

**KEPUTUSAN v3:** `num-dot` **DIPERTAHANKAN** di §2.1 sebagai skema **deskriptif**.
Pencegahan L000608 = tugas **HAKIM** (heuristik curiga, bukan profiler):
```
HEURISTIK CURIGA (hakim, bukan profiler):
  baris berlabel 'subbab' TAPI (awalannya '1.'/'2.' tunggal) DAN (diakhiri '?')
  ⇒ flag untuk review (jangan langsung dikunci)
```
⚠️ **Bonus temuan Bos:** §8.2 (v2) vs §10.2 (v2) saling bertentangan dalam satu dokumen —
§10.2 melarang regex memutuskan bentuk, §8.2 menyuruhnya. **v3: §8.2 yang mengalah.**

### 8.3 — §3b pola bertetangga + prioritas ①→④
Lihat §3b & §5. Prioritas final: **pembimbing > tetangga > profil bab > default**.

---

## 9. YANG BELUM ADA (jujur)

| Hal | Status |
|---|---|
| Kolom `pola` di peta | ❌ belum ada (profiler belum dikode) |
| Nomor otomatis + geser nomor (§4) | ❌ spek saja |
| Sambung ke Kolaborasi | ❌ `kolaborasi.py` 0 panggilan peta |
| Kolom `mulai`/`akhir` | ❌ masih bug (nilai 0) |
| Uji P L1 (3 pertanyaan sempit) | ⏸️ cadangan, **bukan** gerbang kritis |

---

## 10. ⛔ YANG TIDAK DIUSULKAN (pagar)

1. **Tidak** pakai Jev untuk baca pola (Uji P: 33%/17% — sudah terbukti gagal).
2. **Tidak** pakai regex untuk **memutuskan** bentuk/label (larangan Bos 08 Okt).
3. **Tidak** bikin tabel/kolom DB baru (§P5).
4. **Tidak** suruh AI memutuskan bentuk/nomor.
5. **Tidak** "perbaiki" typo/penomoran penulis (§P3).
