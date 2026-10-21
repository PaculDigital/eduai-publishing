# 🗺️ POSISI PRODUKSI vs BELUM MASUK — EduAi (10 Okt 2026)

<!-- 🗺️ SOT: LAPORAN/PETA posisi (RIWAYAT) — bukan penentu status. Status ada di SOT.md + sot.py -->

> Dibuat untuk menjawab kebingungan: *"posisi produksi sekarang, sama tidak dengan
> peta3_jev yang terbaru, karena belum deploy"*
> Semua angka di bawah hasil **cek langsung ke container** `eduai-app`.
>
> 🚩 **DIPERBARUI 10 Okt 2026:** §5 keamanan bertambah pembersihan DB produksi
> (48 berkas + 8 akun uji dibuang) — lihat `PAGAR_PINTU_NASKAH_10OKT2026.md` §5.

---

## 1. JAWABAN SINGKAT

**BEDA.** Produksi **BELUM** memakai `peta3_jev`. Yang jalan ke user sekarang masih
mesin peta **LAMA** (`app/peta_halus.py`, 26 Sep).

```
YANG DIPAKAI USER SEKARANG  : app/peta_halus.py       (26 Sep — cara LAMA)
YANG SUDAH DIBANGUN, BELUM  : peta3_jev.py + peta_bab_jev.py + peta_halus_jev.py
                              + hakim_peta.py + peta_jembatan.py
```

---

## 2. BERKASNYA DI MANA? (hasil cek)

| Berkas | Di container | Di host | Dipanggil rute produksi? |
|---|---|---|---|
| `app/peta_halus.py` | ✅ | ✅ | **✅ YA — ini yang LIVE** |
| `peta3_jev.py` (surveyor) | ✅ `/app/` | ✅ | ❌ tidak |
| `peta_bab_jev.py` (peta bab) | ✅ `/app/` | ✅ *(disalin 10 Okt)* | ❌ tidak |
| `peta_halus_jev.py` (peta sub-bab) | ✅ `/app/` | ✅ *(disalin 10 Okt)* | ❌ tidak |
| `app/hakim_peta.py` (Jev hakim) | ✅ | ✅ | ❌ tidak — 🚩 setelan 1-naskah |
| `app/peta_jembatan.py` (mesin sambung) | ✅ | ✅ | ❌ tidak |
| `saringan_bersih.py` (alat saring) | ✅ | ✅ | ❌ tidak (alat, bukan jalur) |

**Bukti tidak dipanggil:** `grep "peta3_jev\|peta_jembatan\|hakim_peta"` di
`app/main.py` dan `app/ai.py` = **KOSONG**. Yang menyebut hanya berkas uji/gerbang.

⚠️ **Penting:** `peta_bab_jev.py` & `peta_halus_jev.py` **dulu HANYA ADA DI CONTAINER**
(tidak ada salinan di host). Kalau container dibangun ulang ⇒ **hilang permanen**.
Sudah disalin 10 Okt ke host (`_sketsa/peta-jev/`) + `_arsip/pre-bersih-container-10okt26/`.

---

## 3. URUTAN RANTAI BARU (sudah lengkap, belum disambung)

```
① JEV SURVEYOR   peta3_jev.py       → mengukur bentuk (bab/subbab/paragraf/biasa)
② JEV HAKIM      hakim_peta.py      → peer reviewer (LAPOR, tidak override)
③ MESIN          peta_jembatan.py   → terjemahkan → bentuk state.petakan()
④ AI             app/ai.py          → menulis isi
```
Rantai ①→④ **sudah ada semua**, tetapi **belum ada rute yang memanggilnya**.
Deploy = menyambungkan rute ke rantai ini. **Belum diminta Bos.**

---

## 4. KESEHATAN (10 Okt 2026, sesudah bersih-bersih)

```
gerbang jalan tol JEV : 30 LULUS / 0 GAGAL  ✅
periksa_kode.sh       : LULUS ✅
aplikasi produksi     : HTTP 200 ✅ (dari dalam container)
import peta3_jev      : OK ✅
root /app/ bersih     : dari 139 berkas → 4 berkas penting saja
```

---

## 5. KEAMANAN SESUDAH BERSIH-BERSIH

```
DIHAPUS  : 124 artefak uji (_a1…_h20, cek2-7, ukur, ukur2, l3, selidik_indeks_geser)
DISALIN  : peta3_jev · peta_bab_jev · peta_halus_jev · saringan_bersih
           → _sketsa/peta-jev/ DAN _arsip/pre-bersih-container-10okt26/
DISIMPAN : daftar lengkap 139 berkas di _arsip/pre-bersih-container-10okt26/
           (kalau ada yang ternyata masih dibutuhkan, bisa ditelusuri)
```

---

## 6. YANG BELUM DIPUTUSKAN BOS

```
⬜ Deploy rantai baru (sambungkan rute → peta3_jev → hakim → jembatan)
   ⇒ ini MENGUBAH produksi ⇒ butuh izin eksplisit + gerbang
⬜ MUTU FILE di HULU (saat unggah) — arah yang Bos tunjuk untuk naskah rusak
⬜ peta3_jev.py masih di root /app/, belum jadi bagian paket app/
```
