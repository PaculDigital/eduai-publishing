# ✅ PASS-1 STITCH DI SURVEYOR — TERPASANG (10 Okt 2026)

> **Putusan Bos: "A"** — pasang Pass-1 stitch ke surveyor.
> Backup: `_arsip/pre-stitch-surveyor-10okt26/peta3_jev.py` (md5 `7e0cd4f7…`)

---

## 1. MASALAH YANG DITUTUP

Surveyor mengirim **hampir semua baris** sebagai kandidat:

| naskah | baris | kandidat | rasio | sampah ≤2 kar |
|---|---|---|---|---|
| fid=115 | 8.755 | **8.555** | 97,7% | 5.623 (64%) |
| fid=104 | 25.055 | 12.302 | 49,1% | 12.916 (52%) |
| fid=81 | 1.874 | 491 | 26,2% | 655 |

**Sebab:** file PDF/konversi-luar memecah kalimat jadi baris pendek — bahkan
**1 HURUF per baris**:

```
L000907 'D' · L000908 'i' · L000909 'n' · L000910 'a' · L000911 'A' · L000912 'l'
⇒ tulisan "Dina Alna Helmania Putri, …" TERPECAH PER HURUF
```

Akibatnya: 8.555 pertanyaan Jev untuk 1 naskah ⇒ lambat 3 menit + perhatian Jev
terbagi (temuan "kekaburan menular", 09 Okt).

---

## 2. OBAT — PASS-1 STITCH (cara RESMI, bukan tebakan)

Pakai alat produksi **yang sudah ada** (`app/konversi.py:874 _pecah_blok`) —
**JANGAN bikin baru** (aturan Bos).

```
KODE : saring kandidat pasangan (penyebab 503 = panjang state)
JEV  : 1 pertanyaan noul per pasangan —
       "Does line Lxxx pick up mid-sentence, continuing a sentence left
        unfinished at the end of line Lxxx-1?"
KODE : sambung mengikuti ambang cookbook (0,2 sesudah kata menggantung ·
       0,5 sesudah tanda akhir) — ambang di KODE, bukan di Jev
```

Kalimat ini **diambil dari cookbook resmi TypeSafe** (`cookbook-structure-recovery`),
bukan karangan.

---

## 3. HASIL TERUKUR

### fid=115 (baris pecah per-HURUF)
```
SEBELUM: 8.755 baris · 8.563 kandidat · sampah ≤2 kar 5.623
SESUDAH: 1.586 baris · 1.524 kandidat · sampah ≤2 kar   48   ✅ −98%+
waktu 35 dtk · judul selamat: LATAR BELAKANG 5 · TINJAUAN 7 · METODE 16 ·
HASIL 61 · KESIMPULAN 10
```

### fid=81 (naskah normal — KONTROL)
```
1874 baris · 491 kandidat — TIDAK BERUBAH ✅ (tidak merusak yang sudah benar)
```

### fid=104 (baris dipisah baris-kosong) — **PAGAR ③ BEKERJA**
```
[peta3] stitch buang isi (147.352 → 143.012 kar) — pakai teks apa adanya
⇒ `_pecah_blok` MELEWATI pasangan lintas-baris-kosong (konversi.py:867)
   sehingga blok berisi baris-kosong TERBUANG (hilang 3%)
⇒ PAGAR ③ menolak, sistem pakai teks APA ADANYA ⇒ TIDAK RUSAK ✅
⇒ BELUM ditutup: fid=104 butuh penanganan baris-kosong (temuan lanjutan)
```

### Temuan pendukung: Jev MEMANG BISA menilai baris-kosong
```
Uji `uji_jev_kosong_penuh.py` (fid=104, SELURUH 12.527 pasangan):
   terjawab 12.527/12.527 (100%) · 60 dtk
   sebaran noul: min 0,02 · median 0,37 · maks 0,95 (sebaran LEBAR = Jev menilai)
Periksa MATA pada zona abu (0,32–0,63): 7 dari 8 MEMANG HARUS DISAMBUNG
   contoh paling kuat: 'namun' + 'juga' → 0,94 ✅ (satu frasa, dipisah PDF)
⇒ Jev tepat; yang kurang cuma "KODE tidak menanyakan" pasangan lintas-kosong.
```

---

## 4. 3 PAGAR DI KODE (jangan dilepas)

Ada di `peta3_jev.py::_stitch_baris()`:

```
① Jev mati / balik kosong        ⇒ pakai teks APA ADANYA (Jev TAK boleh jadi penghalang)
② blok < 4 ATAU ≥ jumlah baris   ⇒ pakai teks APA ADANYA (tak ada gunanya)
③ karakter turun >2%             ⇒ pakai teks APA ADANYA (ada isi HILANG ⇒ tolak)
```

Pagar ③ **TERBUKTI BEKERJA** (menahan fid=104 yang kehilangan 3%).

---

## 5. ❌ YANG TIDAK DIPAKAI

| Alat | Kenapa dibuang |
|---|---|
| `_rapikan_baris.py` (kode menebak lewat panjang + huruf besar) | **MENELAN JUDUL** — 'Metode Analisa Data' & 'Kesimpulan' HILANG ditelan paragraf. Gagal 3× (tercatat di catatan 09 Okt). fid=104: 0%. |
| Konteks jenis panjang ke prompt Jev | TERUKUR GAGAL — `max_tokens_exceeded`, 84% kandidat tak terjawab. Lihat `VONIS_KONTEKS_JENIS_DIBUANG_10OKT2026.md`. |

---

## 6. KESEHATAN

```
gerbang jalan tol JEV : 30 LULUS / 0 GAGAL ✅
periksa_kode.sh       : LULUS ✅
peta3_jev.py          : berubah (stitch) — backup ada
```

---

## 7. SISA (jujur)

```
⚠️ fid=104 (baris dipisah baris-kosong) BELUM ditutup — pagar menahannya
   (aman, tapi naskahnya belum rapi). Obat: `_kandidat_sambung` jangan
   lewati pasangan lintas-kosong ⇒ Jev yang menilai baris kosong itu
   pemisah atau bukan (sudah TERBUKTI BISA, lihat §3).
⚠️ Belum diuji: peta BAB penuh 3 naskah sesudah stitch (sedang dijalankan).
⚠️ peta3_jev.py belum masuk `app/` (app/peta_halus_jev.py masih cara lama).
```
