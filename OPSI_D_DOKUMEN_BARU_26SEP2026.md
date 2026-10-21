# ✅ OPSI D SELESAI — DOKUMEN BARU LEWAT SERVER (26Sep26)

> **Status celah `CELAH_PROFIL_DRAFT_26SEP2026.md`: TERTUTUP.**
> Bos putuskan **OPSI D** 26Sep26.

---

## 🎯 PUTUSAN BOS & JAWABANNYA

**Pertanyaan Bos:** *"Pakai panggilan api buat dokumen baru kan bisa?"*

**Jawaban Wulan (TERUKUR, bukan dugaan):**

```
⛔ ConvertService.ashx OnlyOffice — untuk MEMBUAT berkas ia harus
   MENGUNDUH sendiri berkasnya lewat URL publik. Diuji:
     POST oo-converter/ConvertService.ashx (url=127.0.0.1:8000)
     → {"error":-8}
   (-8 = URL masukan tidak terjangkau; oo-converter tak bisa melihat
     loopback milik eduai-app). Juga: eduai-app → http://oo-converter
     = 403 (tidak diizinkan).
   ⇒ JALUR API = 2 perjalanan + rawan meleset. TIDAK PERLU.

✅ YANG DIPAKAI: pola yang SUDAH ADA & TERBUKTI di app/main.py:527-536
   (tulis berkas ke folder user → daftarkan baris `files`).
   + templat resmi OnlyOffice yang DISALIN ke repo.
```

**Templat:** `app/templat/naskah-baru.docx`
```
Sumber : oo-converter : /var/www/onlyoffice/documentserver/
                          document-templates/new/default/new.docx
Ukuran : 6.940 byte · md5 768733f19f75145f00a05dcd39f0255f
Sah    : 14 berkas dalam zip · word/document.xml ADA
Alasan disimpan di repo: supaya TIDAK bergantung container lain
                         (oo-converter bisa dibuat ulang kapan saja).
```

---

## ⚙️ CARA KERJA (yang dikoding)

```
app/dokumen_baru.py  — buat_dokumen_baru(db, u, nama, folder_id)
   PAGAR (4):
     1. Templat WAJIB ada → kalau tidak, tolak dengan pesan jelas
     2. Berkas ditulis DULU ke disk, baru db.commit()
     3. nama_simpan unik (token_hex) — pola SAMA dengan alur unggah
     4. commit gagal → berkas disk DIBUANG (jangan tinggalkan yatim)
   Bersihkan nama: buang '/' dan '\' (anti folder aneh), batasi 120 kar

RUTE BARU (TOP-LEVEL, semua GRATIS):
   POST /api/ai/v1/alur/dokumen-baru   → bikin naskah kosong
   POST /api/ai/v1/alur/petakan        → + `buat_dokumen=True`
   POST /api/ai/v1/alur/simpan         → BELUM ada dokumen? DIBUAT dulu
```

**Alur user (sesuai rancangan Bos):**
```
Klik "Mulai baru"  →  (opsional) server buat naskah kosong
     ↓
Isi jenjang → bidang → jenis → judul     ← SEMUA TERSIMPAN (nempel file_id)
     ↓
"Naskahmu sudah ada — tinggal EduAi susun kerangkanya"
```

---

## 🧪 BUKTI UJI — 42 LULUS / 0 GAGAL

```
_sketsa/uji_rute_alur.py   (HTTP nyata · berkas nyata · DB salinan)

D6.  simpan tanpa file_id → OK (dokumen dibuat otomatis)      ✅
D7.  balasan memuat file_id NYATA                             ✅
D8.  dokumen info lengkap                                     ✅
D9.  server balas nama_simpan nyata                           ✅
D10. ukuran file masuk akal (dari templat)                    ✅
D11. nama dokumen sesuai permintaan                           ✅
D11b. berkas BISA DIUNDUH via HTTP /unduh/{id} (bukti nyata)   ✅
D12. simpan lanjutan ke naskah yang SAMA → OK                 ✅
D13. nama ngawur ('../'×100 + 300 kar) → tetap aman           ✅
D14. bikin dokumen TANPA login → 401                          ✅
D4.  simpan judul ke naskah sama → selesai                    ✅

PLUS semua uji lama tetap hijau: gerbang besar 3 pagar · 4 langkah ·
identitas (logo boleh dilewati) · tanpa login 401.
```

---

## 🪤 2 JEBAKAN BARU (26Sep26 — pelajaran untuk uji berikutnya)

```
1. UJI CEK DB SALINAN, SERVER TULIS KE DB PRODUKSI
   Uji ini set EDUAI_DATA_DIR → DB salinan (proteksi produksi),
   TAPI server yang diuji menulis ke DB produksi. Wulan lalu
   membuka sesi DB sendiri → `fb=None` → 3 "GAGAL" PALSU.
   ⇒ ATURAN: buktikan hasil lewat BALASAN SERVER / HTTP
     (mis. GET /unduh/{fid} → 200 + byte), JANGAN buka DB sendiri.

2. SIMPAN TANPA file_id = MEMBUAT NASKAH BARU (OPSI D)
   Uji lama kirim judul tanpa file_id → server BENAR membuat naskah
   KEDUA (jenjang kosong) → tampak "GAGAL" padahal benar.
   ⇒ ATURAN: setelah respons pertama, SELALU teruskan `file_id`-nya
     ke langkah berikutnya. (Sekaligus jadi catatan FE: layar WAJIB
     menyimpan file_id draft.)
```

---

## 🔴 BELUM (jujur)

```
· TAMPILAN LAYAR (pintu 2 kartu + 4 langkah + panel dokumen baru) — belum
· DEPLOY `jalankan.sh` — belum (masih docker cp)
· Bersihkan DB uji (2 naskah "Uji Opsi D" + profil uji) — belum
```
