<!-- SOT: AUDIT_CORE_PETA_NASKAH_14OKT2026 -->

# 🔴 AUDIT CORE — PETA NASKAH (14 Okt 2026)

> **Perintah Bos:** *"Cek, audit dan pastikan. Jika ragu berhenti dan baca
> Dokumentasi resmi lagi dan bertanya. Lakukan dengan sangat hati-hati."*
> **Status:** AUDIT SAJA — **NOL kode disentuh.** Menunggu putusan Bos.

---

## 1. YANG WULAN TEMUKAN (terukur, bukan tebakan)

### 🔴 INTI MASALAH: ADA DUA MESIN PETA, YANG DIPAKAI PRODUKSI = YANG LAMA

```
Rute /v1/peta/mulai + /v1/peta/kerjakan  →  app/peta_halus.py   [26 Sep]
                                            ↑ INI yang tayang
peta3_jev.py                             →  TIDAK DIPAKAI app sama sekali
                                            (skrip root, TIDAK ikut image)
app/peta_jembatan.py                     →  hanya dipakai GERBANG UJI
app/hakim_peta.py                        →  hanya dipakai GERBANG UJI
```

**Bukti:**
```
app/ai.py:4278   from . import peta_halus as _p     ← produksi
grep peta3_jev   → 0 pemanggil di produksi (hanya di gerbang uji)
grep peta_jembatan → hanya app/_gerbang_jembatan.py (uji, bukan produksi)
docker exec eduai-app ls /app/peta3_jev.py → TIDAK ADA di container
```

### Akibatnya — yang Bos putuskan 08/09 Okt BELUM TERSAMBUNG

| Putusan Bos (dokumen) | Kenyataan di produksi |
|---|---|
| Peta 3 tingkat (BAB+SUB-BAB+PARAGRAF) | produksi = `peta_halus` (mesin 26 Sep) |
| 1 panggilan Jev untuk semua fitur | `peta3_jev` belum masuk app |
| Urutan: Jev surveyor → HAKIM → mesin → AI | `hakim_peta` **tidak dipanggil** produksi |
| Jembatan `peta_jembatan.dari_surveyor()` | **tidak dipanggil** produksi |
| Simpan peta ke `section_state` | belum (SOT §7 butir 8: "belum diisi") |

**Ini PERSIS kelas yang sama** dengan temuan hari ini: **mesin sudah ada, pintunya belum dipasang.**

---

## 2. YANG SUDAH SEHAT (jangan diutak-atik)

```
✅ app/peta_jembatan.py  → GERBANG 16/0 LULUS (jembatan sehat, resmi)
✅ app/hakim_peta.py     → pagar H1/P1-P6 lengkap, `p` BUKAN input keputusan
✅ Gerbang Jalantol Jev  → 28/0 (2 GAGAL = laporan .md K5 & validasi silang
                            BELUM DIBUAT — catatan, bukan kerusakan kode)
✅ Jalur biaya satu pintu: `satpam` → `jev.tanya` (D1/D2/D3 terbukti)
✅ peta3_jev.py           → terbukti unggul (Asih: bab 5/5, subbab 130,
                            paragraf 160; nol regresi)
```

---

## 3. ⚠️ RISIKO — INI CORE, JADI WAJIB HATI-HATI

```
R1. DUA MESIN PETA HIDUP BERDAMPINGAN = bahaya "perbaikan masuk salinan salah"
    (kelas yang SAMA dengan /api/addon vs /api/ai/v1/addon, sudah dibersihkan 14Okt)
R2. Menyambung peta3_jev MENGUBAH hasil peta untuk SEMUA fitur di hilir
    (kolaborasi, revisi, konversi jurnal, rujukan) ⇒ WAJIB uji regresi penuh
R3. JANGAN hapus peta_halus sebelum peta3_jev TERBUKTI bekerja di produksi
    (pagar Bos: "RAHU ⇒ berhenti, jangan hapus besar tanpa izin")
R4. `hakim_peta` pagar P6: DILARANG menyentuh `app/satpam.py` (jalur biaya)
R5. `URUTAN_RESMI` §CATATAN K5: criteria K5 + ambang 0,60/0,30 = TAMBAHAN WULAN
    yang DITANDAI "JANGAN dipakai produksi" ⇒ JANGAN dipakai saat menyambung
```

---

## 4. LAPISAN PEKERJAAN (WAJIB dibaca dulu sebelum koding)

Ini **BUKAN satu sambungan** — Wulan petakan di depan (pelajaran 14 Okt):

```
LAPIS 1  peta3_jev.py masuk paket app (bukan skrip root)
         → kenapa belum: `jalankan.sh`/Dockerfile tidak meng-COPY berkas root
         → risiko: sedang — menambah 1 berkas ke image

LAPIS 2  rute /v1/peta/* beralih ke jembatan `peta3_jev → peta_jembatan`
         → ini yang MENYENTUH CORE (semua fitur hilir ikut berubah hasil)
         → risiko: TINGGI — wajib uji regresi (Asih fid=81 baseline sudah ada)

LAPIS 3  hakim_peta dipanggil sesudah surveyor (LAPOR saja, jangan blokir)
         → risiko: sedang — tapi pagar H1/P1 menjamin mesin tetap jalan

LAPIS 4  simpan peta ke `section_state` + kolom mulai/akhir (bug `mulai`=0)
         → risiko: sedang — menyentuh DB (ada tabel lama, JANGAN ubah tabel)

LAPIS 5  PINTU LAYAR (tombol) — supaya user bisa menekan
         → risiko: rendah — inilah "pintu" yang hilang
```

**Bos: 5 lapis. Lapis 2 dan 4 menyentuh core & DB ⇒ JANGAN dikerjakan sekaligus.**

---

## 5. YANG WULAN SARANKAN (belum dikerjakan, tunggu putusan)

```
✅ Urutan AMAN (kalau Bos setuju):
   ① Lapis 1+5 dulu (peta3_jev masuk image + tombol) — risiko rendah,
     TIDAK mengubah hasil fitur lama (peta_halus tetap jalan)
   ② Uji regresi: bandingkan hasil peta3_jev vs peta_halus pada Asih (BASELINE ada)
   ③ Bos lihat bedanya → putuskan
   ④ BARU Lapis 2-4 (ganti mesin produksi + hakim + section_state)

❌ JANGAN: langsung tukar mesin produksi tanpa Bos lihat bedanya
   (kalau hasilnya beda & malah lebih jelek, SEMUA fitur hilir rusak sekaligus)
```

---

## 6. PERTANYAAN YANG WULAN TIDAK BISA JAWAB SENDIRI (minta putusan Bos)

```
Q1. Apakah peta3_jev MEMANG untuk menggantikan peta_halus di /v1/peta/*,
    atau untuk fitur LAIN (kolaborasi/konversi) saja?
Q2. Kalau menggantikan — Bos mau LIHAT perbandingan hasilnya dulu
    (naskah Asih) sebelum produksi ditukar?
Q3. `hakim_peta` sekarang TIDAK dipanggil produksi. Bos mau dipanggil?
    (Catatan K5: criteria K5 Wulan JANGAN dipakai produksi)
```

**Wulan berhenti di sini.** Tidak ada kode yang disentuh.
