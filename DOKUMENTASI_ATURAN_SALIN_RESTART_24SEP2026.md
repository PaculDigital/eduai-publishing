# ATURAN WAJIB: `docker cp` HARUS DIIKUTI `docker restart`

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


**Tanggal:** 24 September 2026
**Status:** ✅ **STANDAR WAJIB** — keputusan Bos: *"Ya jadikan standar setelah
docker cp selalu docker restart jadi gak ada kode lama lagi."*
**Skrip resmi:** `scripts/salin_restart.sh`

---

## 1. MASALAHNYA (akar, terukur)

`docker cp` **HANYA menukar berkas di disk container**. Server yang **sedang
jalan** tidak otomatis membaca ulang berkas itu.

Sebabnya: `eduai-app` dijalankan **TANPA `--reload`**:

```
$ docker inspect eduai-app --format '{{json .Config.Cmd}}'
["uvicorn","app.main:app","--host","0.0.0.0","--port","8000",
 "--proxy-headers","--forwarded-allow-ips","*"]
                   ↑ TIDAK ADA --reload
```

Artinya **kode dimuat SEKALI saat container start**. Sesudah itu, mengubah
berkas di disk **tidak berpengaruh** sampai prosesnya dimulai ulang.

### Akibat yang terukur (24Sep26)

| Ukuran | Angka |
|---|---|
| Container hidup | **8 jam** |
| `docker cp` yang Wulan lakukan | berkali-kali |
| Baris pengintai `log.warning('[INTIP] …')` muncul di log | **0 KALI** |
| Kesimpulan | **seluruh perubahan memakai KODE LAMA** |

Wulan **menguji barang yang salah**, lalu **salah lapor**: HTML tampak benar
(karena berkasnya memang baru), tapi **layar tidak berubah** (karena server
pakai kode lama). Ini akar dari kebingungan "kok hasilnya tidak berubah".

### Uji pembuktian (bersih, terukur)

Penanda `'jejak_uji': 'PENANDA12345'` disisipkan ke nilai yang **dikirim
server ke halaman**, lalu dibaca lewat halaman `/tinjau/<token>`:

| Perlakuan | Penanda terbaca di halaman? | Arti |
|---|---|---|
| `docker cp` **saja** | **TIDAK** | kode lama dipakai |
| `docker cp` + **`docker restart`** | **YA** | kode baru dipakai ✅ |

---

## 2. ATURANNYA (mulai 24Sep26, WAJIB)

> ### 🚨 SETIAP `docker cp` ke `/app/...` **WAJIB** diikuti `docker restart`
> ### + tunggu sampai `/health` = **200**, sebelum **apa pun** diuji.

**Pakai skrip resmi** (jangan hafal urutannya):

```bash
# banyak berkas sekaligus → restart HANYA SEKALI
bash scripts/salin_restart.sh eduai-app app/sorotan.py app/rute_pembimbing.py

# hanya memeriksa keadaan container
bash scripts/salin_restart.sh eduai-app --periksa
```

Yang skrip itu lakukan:
1. Salin berkas → **buktikan md5 host == container** (bukan sekadar "tidak error")
2. `docker restart`
3. Tunggu `/health` = **200** (45 detik; berhenti lebih awal kalau wadah mati)
4. Cetak cara membuktikan lebih kuat (tanda `[INTIP]` di log)

Terukur: **5 detik** (versi pertama yang salah: 46 detik 🌶️).

---

## 3. CARA MEMBUKTIKAN KODE BARU BENAR-BENAR DIPAKAI

Jangan percaya berkas saja — berkas bisa baru sementara server masih lama.

```bash
# 1) titipkan sebaris penanda di fungsi yang diuji
#    (contoh, DIHAPUS lagi sesudahnya)
log.warning('[INTIP] berkas_id=%r', berkas_id)

# 2) jalankan lewat skrip (ada restart)
bash scripts/salin_restart.sh eduai-app app/rute_pembimbing.py

# 3) panggil fiturnya, lalu periksa log
docker logs --since 60s eduai-app | grep INTIP
#    ADA    → kode baru sudah dipakai ✅
#    0 baris → kode lama masih hidup ❌
```

⚠️ **Jangan uji dengan `python -c "import …"`** — proses baru SELALU membaca
berkas dari disk, jadi jawabannya selalu "ada" **walau server masih kode
lama**. Itu uji palsu. **Uji WAJIB lewat proses server yang hidup**
(panggil halaman/HTTP, atau `grep` log server).

⚠️ **Hati-hati salah pilih kata penanda.** 24Sep26 Wulan memakai kata
`PENANDA` — padahal kata itu **sudah ada** di kode (`PENANDA PARAGRAF`),
jadi penanda tampak "masih ada" padahal kode sudah bersih. Pakai kata yang
**tidak mungkin muncul** di sumber (mis. `ZZUJI12345`).

---

## 4. HUBUNGAN DENGAN `jalankan.sh` (DEPLOY)

| | Cara | Kenapa | Perlu restart manual? |
|---|---|---|---|
| **Uji cepat** | `docker cp` + `salin_restart.sh` | tidak perlu build image berkali-kali saat mencari akar bug | **YA — wajib** |
| **Tayang produksi** | `bash jalankan.sh` | build **IMAGE BARU** → kode pasti baru | **TIDAK** |

**Deploy TIDAK terkena masalah ini** — image-nya baru, jadi kode pasti baru.
`docker cp` dipakai **hanya untuk uji cepat**, itu pun wajib restart.

⚠️ Masih berlaku: **`docker restart` TIDAK membaca ulang `.env`** (env
ditempel saat `docker run`) → kalau yang diubah `.env`, **WAJIB**
`bash jalankan.sh`.

---

## 5. PELAJARAN DI SEKITARNYA (jangan diulang)

1. **Syarat yang tidak dibutuhkan → GAGAL PALSU.** Versi pertama skrip
   menunggu `docker inspect .State.Health.Status == healthy`. Container
   `eduai-app` **TIDAK punya healthcheck** → statusnya `none` → skrip
   melaporkan "BELUM melayani" padahal `/health` **200**.
   ⇒ **Ukuran utama = `/health` dari DALAM container.**
2. **Baca berkas ≠ bukti perilaku.** Berkas baru + server lama = gejala
   "kode benar tapi hasil salah". Ini juga pelajaran lama
   (`📏 BACA ATRIBUT ≠ UKUR PERILAKU`).
3. **Uji WAJIB berdiri sendiri.** Skrip uji tidak boleh bergantung pada
   berkas yang hanya ada kalau disiapkan manual.

---

## 6. BERKAS YANG DISENTUH

| Berkas | Perubahan |
|---|---|
| `scripts/salin_restart.sh` | **BARU** — standar salin + restart + verifikasi |
| `MASTER_PLAN.md` | Ditambah butir aturan wajib di bagian prasarana |
| `FLAG_LANJUT_DISINI.md` | Blok pelajaran 24Sep26 |
| `DOKUMENTASI_ATURAN_SALIN_RESTART_24SEP2026.md` | Berkas ini |
| Skema skill `vps-service-management` | Aturan kelas-umum |
