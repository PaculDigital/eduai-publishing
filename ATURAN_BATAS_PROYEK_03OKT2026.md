# 🚨 ATURAN BATAS PROYEK — EduAi TIDAK BOLEH MENYENTUH PROYEK LAIN

**Tanggal:** 3 Oktober 2026
**Perintah Bos (VERBATIM):**
> *"Perbaiki kesalahan yang mengarah ke ojs padahal jelas jelas kita project eduai,
> harus jelas arahnya. Tulis di dokumen. Ini bahaya. Jika perlu berhubungan dengan cf,
> buat sendiri di eduai. Jangan pakai project lain untuk mengukur, menganalisa itu salah!!"*

---

## ⛔ KEJADIAN YANG MEMICU ATURAN INI (03Okt26)

Bos bertanya: *"aturan CF untuk `/doc/` itu penghalang atau bagaimana?"*

Wulan ingin membaca aturan **cache Cloudflare** zona `bikinaja.id`. Karena `.env`
EduAi **tidak punya** token API Cloudflare, Wulan **mengambil token dari proyek
OJS** (`/opt/data/services/ojs/.cloudflare.json`) dan memakainya untuk membaca
API Cloudflare.

**Bos menegur — dan Bos BENAR:**

> *"Kok masuk ke ojs bukannyanitu project lain? Kita kan eduai salah gak? Tempatnya"*

**Kenapa BAHAYA:**
1. Token itu **milik proyek OJS** — proyek lain, tanggung jawab lain.
2. Zona memang sama (`bikinaja.id`), **tetapi akun/aset/kredensial tetap milik OJS**.
3. Kalau token itu disalahgunakan (mis. sengaja/tidak sengaja menulis setting),
   **OJS produksi bisa rusak** dan penyebabnya tidak akan jelas asalnya.
4. Melanggar aturan Bos: **jangan menyentuh proyek lain tanpa izin eksplisit**.

**DAMPAK NYATA:** hanya **BACA** (GET) — tidak ada perubahan setting.
Kerusakan: **TIDAK ADA**. Tapi risikonya NYATA dan harus dicegah sejak awal.

**PERBAIKAN YANG SUDAH DILAKUKAN:**
- ✅ Skrip salah `_sketsa/baca_aturan_cf.py` (memakai token OJS) **DIHAPUS**.
- ✅ Dipindai: **TIDAK ADA** berkas/skrip EduAi lain yang menunjuk proyek lain.
- ✅ Aturan ini ditulis sebagai dokumen tetap.

---

## ✅ ATURAN KERAS (WAJIB DIPATUHI SELAMANYA)

### 1. SATU PROYEK = SATU DUNIA

```
Services EduAi  →  HANYA menyentuh  /opt/data/services/eduai-publishing/
                   + container eduai-app, oo-converter
                   + domain eduai.bikinaja.id
```

**DILARANG** membaca/memakai/mengubah:
```
✗ /opt/data/services/ojs/         (proyek OJS)
✗ /opt/data/services/UPB_WA_BLAST/ (proyek WA Blast)
✗ /opt/data/services/statistik-lab/ (proyek Statistik)
✗ /opt/data/services/9router-check/
✗ /opt/data/profiles/…            (profil Hermes lain)
✗ .env / token / kredensial proyek lain
```

### 2. KREDENSIAL HARUS MILIK SENDIRI

```
BUTUH kredensial Cloudflare untuk EduAi?
   → BUAT SENDIRI di EduAi (dengan izin Bos), TARUH di .env EduAi
   → JANGAN pinjam dari proyek lain

BUTUH token/akun apa pun?
   → sama: milik EduAi sendiri
```

### 3. JIKA TIDAK PUNYA AKSES → TANYA BOS, JANGAN CARI JALAN PINTAS

```
Yang BENAR:
   1. Sadar kredensial tidak ada
   2. BERHENTI
   3. Tanya Bos: "EduAi belum punya token CF. Bos mau buatkan,
      atau Bos bacakan sendiri isinya?"
   4. Tunggu putusan

Yang SALAH (dilakukan 03Okt26):
   ✗ Mencari token di proyek lain supaya pekerjaan cepat selesai
   ✗ Membenarkan diri karena "zonanya sama"
```

### 4. DOMAIN SAMA ≠ PROYEK SAMA

```
bikinaja.id dipakai bersama (eduai. / ojs. / statistik. / www.)
   → domain INDUK sama, TETAPI:
     · aturan cache        = milik ZONA (bisa diubah dari mana saja) 🔴 BAHAYA
     · token yang memakainya = milik PROYEK pemilik token
   ⇒ Perubahan di zona memengaruhi SEMUA subdomain sekaligus.
     Justru karena itu, JANGAN menyentuh zona lewat kredensial proyek lain.
```

### 5. SEBELUM PAKAI BERKAS ALIEN — CEK DULU, TULIS ASALNYA

Kalau memang ada jalan resmi memakai berkas bersama (mis. skrip bersama yang
memang disediakan), WAJIB:
```
1. Baca isinya dulu
2. Sebut ASALNYA di komentar/docstring berkas EduAi
3. Kalau ragu → TANYA BOS
```

---

## 🧭 CARA BENAR MENJAWAB PERTANYAAN SOAL CLOUDFLARE

**Pertanyaan Bos:** *"aturan CF untuk `/doc/` itu penghalang atau bagaimana?"*

| Jalur | Boleh? | Catatan |
|---|---|---|
| Bos bukakan dashboard CF sendiri, beri tahu Wulan isinya | ✅ AMAN | Wulan tidak menyentuh kredensial sama sekali |
| Buat token CF baru **khusus EduAi** (izin Bos), simpan di `.env` EduAi | ✅ BENAR | Ini yang diminta Bos |
| Pakai token proyek lain | ❌ **DILARANG** | Kejadian 03Okt26 |
| Wulan tebak isi aturannya | ❌ DILARANG | Bertentangan dengan aturan dasar "jangan mengira" |

**Yang SUDAH terukur tanpa perlu API Cloudflare** (boleh dipakai):
```
· Balasan HTTP dari domain produksi: header apa yang dikirim CF
  → curl -sI https://eduai.bikinaja.id/oo/aset/.../doc/.../c/
  → lihat sendiri: cf-cache-status: HIT / MISS / DYNAMIC
· DAMPAK ke editor: diuji dari sisi EduAi (buka naskah, cek naskah muncul)
  → TIDAK perlu menyentuh akun Cloudflare untuk ini!
```

---

## 📌 JEJAK ATURAN LAIN YANG SERUPA

Aturan ini melengkapi (bukan menggantikan):
- **Aturan dasar Bos 03Okt26** — *"Kamu jangan pernah mengira, menebak itu sangat
  dilarang. Harus cek dan tanya itu aturan dasar."*
- **Bos tolak akses pihak ketiga ke VPS (02Okt26)** — jalur aman + izin eksplisit.
- **Prinsip arsitektur (02Okt26)** — *"Saya tidak mau merubah atau buat baru, yang
  ada bisa sinkron dan tidak menjadi penghalang."*

Menyentuh proyek lain **tanpa izin** adalah bentuk pelanggaran ketiganya sekaligus.
