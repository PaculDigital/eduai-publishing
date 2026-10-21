<!-- SOT: RENCANA_SAMBUNG_PETA_14OKT2026 -->

# 🗺️ RENCANA SAMBUNG PETA NASKAH — BERDASARKAN PUTUSAN BOS 14 Okt 2026

> **Putusan Bos (verbatim, 14 Okt):**
> 1. *"Peta3_jev mengganti peta halus, sesuai uji dan keputusan 08/09 okt"*
> 2. *"Tidak sudah saya uji dan yang menggunakan jev lebih akurat dan presisi
>    dalam memetakan"*
> 3. *"Ya hakim, setelah jev memetakan, maka hakim untuk memperjelas dan fokus
>    sebelum mesin dan Ai bekerja"*
> 4. *"Peta halus dan kasar yang sebelumnya jangan di buang dan jadikan fallback
>    jika jev dan hakim mati"*

**Status:** RENCANA — **NOL kode disentuh.** Menunggu izin "mulai".

---

## 1. ARSITEKTUR YANG BOS PUTUSKAN (digambar jelas)

```
                    ┌──────────────────────────────┐
  naskah ──────────▶│ ① JEV SURVEYOR               │  peta3_jev.petakan()
                    │    "saya beri tahu bentuknya" │
                    └──────────────┬───────────────┘
                                   │  mati/galat?
                    ┌──────────────▼───────────────┐
                    │ FALLBACK: peta_halus + peta_bab│  ← PUTUSAN BOS #4
                    │ (yang LAMA, JANGAN dibuang)    │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ ② JEV HAKIM                  │  hakim_peta.periksa()
                    │    "saya periksa & LAPOR"     │  (LAPOR, jangan blokir)
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ ③ MESIN                      │  peta_jembatan.dari_surveyor()
                    │    "saya ikut petunjuk Jev"   │  → state.petakan()
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ ④ AI                         │  menulis isi
                    └──────────────────────────────┘
```

⚠️ **Yang berubah dari rencana Wulan kemarin:** Bos menambah **FALLBACK**.
Ini **memperbaiki** rencana Wulan — Wulan tadinya mau menyambung lalu
(cepat atau lambat) mengganti. Bos benar: **jangan buang yang lama**, jadikan
jaring pengaman. Kalau Jev & Hakim mati, produksi **tetap jalan**.

---

## 2. SATU HAL KRITIS YANG WULAN TEMUKAN (wajib Bos tahu)

### 🔴 `peta3_jev.py` sekarang = **SKRIP CLI**, BUKAN modul

```
Baris 13-17 : import level-atas (sys.path.insert('/app'), baca app.ai, app.satpam)
Baris 346   : def main()          ← pembungkus skrip
Baris 383   : if __name__ == '__main__': main()
```

Artinya: rute produksi **tidak bisa** `from . import peta3_jev` begitu saja —
fungsi `petakan()` ada di dalam berkas yang dirancang sebagai **program berdiri**,
yang saat impor akan menarik `app.ai` (putaran impor!) dan `sys.path.insert('/app')`.

**Jadi Lapis 1 BUKAN sekadar "kopy berkas".** Ini pekerjaan nyata:
```
· pindahkan `petakan()` + pembantunya ke modul bersih `app/peta3_jev.py`
· buang `sys.path.insert` & `main()` (biarkan tetap ada untuk CLI)
· impor `app.ai` di DALAM fungsi (hindari putaran impor — pelajaran lama)
```

Wulan **tidak mau menebak**. Ini yang Wulan maksud "berhenti dan pastikan".

---

## 3. ⚠️ FALLBACK — SATU JEBAKAN YANG WAJIB DIHINDARI

Bos minta fallback. Tapi ada **bahaya**: kalau fallback dipasang **diam-diam**,
user tidak akan pernah tahu peta yang dipakai = **peta lama** (mutu lebih rendah),
dan **Wulan juga tidak tahu** — jadi bug Jev tidak pernah ketahuan.

**Syarat Wulan (mohon persetujuan):**
```
① fallback JALAN, tapi WAJIB JEJAK: log + kolom penanda "peta_dari: jev|fallback"
② pesan ke user (halus): "struktur naskah dipetakan cara cadangan" — supaya jujur
③ fallback TIDAK dipakai kalau Jev jawab tapi RAGU sebagian
   (ragu sebagian ≠ mati; itu beda — biar Jev yang tangani goyangnya)
④ ambang "mati" harus jelas: galat · timeout · 0 jawaban — BUKAN "hasil jelek"
```

Kalau Bos setuju poin ③: fallback = **jaring pengaman**, bukan **jalan pintas
menyembunyikan kegagalan**.

---

## 4. 5 LAPIS — URUTAN & RISIKO

| # | Lapis | Berkas | Risiko | Uji |
|---|---|---|---|---|
| 1 | `peta3_jev` jadi MODUL (bukan skrip) | baru `app/peta3_jev.py` | sedang | gerbang impor + `petakan()` Asih |
| 2 | **HUBUNGKAN rute** `/v1/peta/*` → surveyor + **fallback** | `app/ai.py` (2 rute) | 🔴 **CORE** | regresi `_banding_baseline.py` |
| 3 | Hakim dipanggil sesudah surveyor (LAPOR) | `app/ai.py` | sedang | pagar H1/P1: hakim mati ⇒ mesin tetap jalan |
| 4 | Simpan peta ke `section_state` | `app/models.py`? | 🔴 **DB** | JANGAN ubah tabel lama |
| 5 | Pintu layar (tombol) | `app/templates/*.html` | rendah | gerbang layar |

**Aturan Wulan: Lapis 2 & 4 = core & DB ⇒ DILARANG dikerjakan dalam 1 deploy.**

---

## 5. URUTAN AMAN YANG WULAN SARANKAN

```
PUTARAN 1 (risiko rendah — TIDAK mengubah hasil fitur lama):
   Lapis 1 : peta3_jev jadi modul + gerbang impor
   + uji: petakan() Asih vs BASELINE_PETA3.json → harus IDENTIK
   ⇒ produksi BELUM berubah sedikit pun (peta_halus masih dipakai)

PUTARAN 2 (Bos lihat bedanya dulu):
   Jalankan pembanding: peta3_jev vs peta_halus pada Asih
   → sajikan tabel beda (butuh waktu Jev; Rp 0 utk pemeriksaan)
   ⇒ BOS PUTUSKAN lanjut atau tidak

PUTARAN 3 (core — sesudah Bos lihat):
   Lapis 2 : sambungkan rute + fallback + jejak
   Lapis 3 : hakim
   ⇒ uji regresi penuh + gerbang bergigi

PUTARAN 4:
   Lapis 4 + 5 : section_state + tombol layar
```

---

## 6. PAGAR YANG WULAN PEGANG (dari dokumen resmi)

```
✅ URUTAN: Jev surveyor → Jev hakim → mesin → AI   (TERKUNCI 09 Okt)
✅ Hakim = PEER REVIEWER (lapor), TIDAK meng-override peta surveyor (pagar H1)
✅ Jev SELALU di depan (gatekeeper) — putusan Bos 07 Okt
✅ JANGAN dipakai: criteria K5 + ambang 0,60/0,30 (URUTAN_RESMI §K5 = tambahan
   Wulan, ditandai JANGAN produksi)
✅ Jev TIDAK menilai MUTU tulisan — hanya BENTUK/STRUKTUR/KEBERADAAN
✅ Satu pintu biaya: `satpam` (hakim_peta modul TERPISAH, jangan menyentuh satpam)
✅ 503 ⇒ jangan vonis "batas tetap"; bahan terlalu besar ⇒ gelombang
✅ Uji naskah WAJIB lewat `app.ai._teks_dari_berkas` (JANGAN skrip host sendiri)
```

---

## 7. YANG WULAN TUNGGU DARI BOS

```
① Setuju rencana PUTARAN 1 dulu (peta3_jev jadi modul + gerbang, produksi
   belum berubah)? — risiko paling kecil, bukti paling cepat
② Setuju syarat FALLBACK (wajib JEJAK + tidak dipakai saat Jev cuma "ragu")?
③ Boleh mulai?
```
