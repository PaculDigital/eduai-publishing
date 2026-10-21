# 🧪 UJI TOMBOL "PERIKSA DENGAN AI" + JAWABAN SOAL ATURAN CF

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.

**Tanggal:** 3 Oktober 2026 · **Status:** ✅ TERUJI, FITUR BEKERJA
**Image:** `eduai-app:20261003_044420-sot`

---

## BAGIAN 1 — TOMBOL "PERIKSA DENGAN AI": HASIL UJI

### Alur yang terbukti (uji dengan token NYATA + data NYATA)

```
1. Pembimbing buka /tinjau/{token}
   → karena identitas belum diisi: tampil "Undangan Kolaborasi Bimbingan"
     (tombol SENGAJA belum muncul — desain, bukan bug)
2. Isi identitas (nomor HP/email) → POST /tinjau/{token}/identitas → 303
3. Buka lagi /tinjau/{token}
   → ✅ TOMBOL MUNCUL: "Buka di editor" + "Periksa dengan AI"
4. Klik "Periksa dengan AI" TANPA AKUN
   → ✅ 303 → /daftar?dari=/tinjau/{token}
     (sesuai putusan Bos: klik AI = WAJIB DAFTAR, karena AI butuh dompet)
5. Klik "Periksa dengan AI" DENGAN AKUN
   → ✅ 303 → /tinjau/{token}?ai=jalan  (pekerjaan dititipkan ke utas latar)
6. Kerja latar dijalankan → ✅ SELESAI TANPA GALAT
   → ✅ 5 CATATAN BARU masuk ke naskah (id 19-23, warna biru = dari pembimbing)
```

### Mutu catatan AI (nyata, menunjuk teks yang ADA di naskah)

```
id 19 [Latar Belakang (BAB I)]
  "masih berupa template/instruksi penulisan, bukan narasi latar belakang"
  Kutipan: "Paragraf 1-2 berisi bahasan istilah paling luas mengenai suatu objek"

id 20 [Sub-bab 2.1 Penelitian Terkait (BAB II)]
  "beberapa butir penelitian terkait masih kosong (placeholder)"
  Kutipan: "Metode yang digunakan: {...}. Temuan Penelitian: {...}."

id 21 [Daftar Gambar]
  "sisa teks instruksi template masih tertinggal"
  Kutipan: "Untuk mengupdate tabel, silakan melakukan modifikasi pada Caption"

id 22 [Tabel 4.5 (BAB IV)]
  "terdapat baris yang disunting/dihilangkan (redacted) di tengah tabel hasil"
  Kutipan: "REDACTED FOR CONFIDENTIALITY"

id 23 [Daftar Pustaka]
  "jumlah rujukan belum memenuhi syarat minimal 30 referensi"
  Kutipan: "SESUAIKAN DENGAN ISTILAH DALAM PENELITIAN KALIAN"
```

✅ Semua kutipan **benar-benar ada** di naskah (bukan karangan AI).
✅ Setelah uji, 5 catatan uji **DIHAPUS** → naskah mahasiswa bersih kembali.

### 🚨 JEBAKAN UJI YANG DITEMUKAN (penting untuk lain kali)

Wulan menjalankan kerja latar **langsung** dengan `kerja(laporan.append)` →
```
AttributeError: 'builtin_function_or_method' object has no attribute 'tahap'
```
**Bukan bug kode.** `kerja` WAJIB menerima objek **`proses.Lapor`**
(`PR.Lapor(kode)`), bukan fungsi apa pun. Mesin proses BENAR:
```python
loop.run_until_complete(kerja(Lapor(kode)))   # app/proses.py:546
```
**PELAJARAN:** kalau mau menguji fungsi `kerja` di luar mesin proses, WAJIB
membungkusnya dengan `PR.Lapor('kode-uji')` — jangan mengirim callback sendiri.

### 🔍 JEBAKAN PENCARIAN AKAR (jangan ulangi)

Tombol tampak "tidak muncul" padahal **memang belum saatnya muncul**:
```
Halaman /tinjau/{token} punya DUA wajah:
   {% if not sudah_isi_identitas %}  → halaman UNDANGAN (tinjau.html:334)
   {% else %}                        → halaman TINJAUAN + tombol AI
```
**CARA CEPAT MEMERIKSA:** cari `"Periksa dengan AI"` DI HTML; kalau TIDAK ada
tapi CSS `.alat-baca` ADA → berarti yang tercetak adalah cabang `undangan`
(pembimbing belum isi identitas). Cek `Pembimbingan.identitas`.

**CARA MEMBUKTIKAN RUTE (bukan menebak):** bungkus
`_tpl.TemplateResponse` untuk mencetak konteks yang dikirim
(`_sketsa/akar_tombol_ai3.py` → jadi `scripts/intip_konteks_tinjau.py`).

---

## BAGIAN 2 — ATURAN CLOUDFLARE UNTUK `/doc/`: TIDAK MENGHALANGI

### Ukuran dari domain EduAi (bukan dari API Cloudflare)

```bash
curl -sI -H "Cache-Control: no-cache" \
  "https://eduai.bikinaja.id/oo/aset/<versi>/doc/<KEY>/c/?t=$RANDOM"
```

| Jalur | `cf-cache-status` | Arti |
|---|---|---|
| `/oo/aset/…/doc/<KEY>/c/` (kanal dokumen) | **BYPASS** | CF **tidak** menyimpan ✅ |
| `/oo/aset/…/web-apps/…/api.js` (aset editor) | **MISS** | diambil dari server, wajar ✅ |

**⇒ ATURAN CF TIDAK MENGHALANGI.** Cloudflare **menghormati** header kita
(`private, no-store`) untuk jalur dokumen.

### Uji dampak nyata

```
· 3× berturut buka kanal tanpa cookie → 303 konsisten (pagar sehat) ✅
· cache OO: baca60v1790446608 MASIH ADA (dokumen baca tersimpan) ✅
· penolakan Editor.bin (403/forbidden) di log OO → 0 ✅
```

### Pelajaran yang tetap berlaku

Meski sekarang `BYPASS`, **uji pagar WAJIB tetap bypass cache CF**
(`-H "Cache-Control: no-cache"` + parameter acak). Pada 03Okt26 pagi CF
menyajikan balasan LAMA (`cf-cache-status: HIT`, `age: 68`) untuk jalur itu —
bisa terjadi lagi kalau aturan CF berubah.

### ⚠️ Bahaya yang HARUS dihindari

Untuk memeriksa aturan CF, **JANGAN memakai token Cloudflare proyek lain**
(kejadian 03Okt26: Wulan memakai token `services/ojs`). Aturan batas proyek:
`ATURAN_BATAS_PROYEK_03OKT2026.md`. Cara aman: ukur dari sisi EduAi saja
(seperti di atas) — **tidak perlu API Cloudflare sama sekali**.

---

## Berkas uji

| Skrip | Isi |
|---|---|
| `_sketsa/uji_tombol_ai.py` | alur lengkap: undangan → identitas → tombol → klik tanpa akun |
| `_sketsa/uji_tombol_ai4.py` | klik dengan akun → `ai=jalan` |
| `_sketsa/akar_kerja_latar_ai2.py` | jalankan kerja latar dengan `PR.Lapor` benar |
| `_sketsa/akar_tombol_ai3.py` | intip konteks `TemplateResponse` |

Semua disalin ke skill: `skills/devops/eduai-publishing/scripts/`.
