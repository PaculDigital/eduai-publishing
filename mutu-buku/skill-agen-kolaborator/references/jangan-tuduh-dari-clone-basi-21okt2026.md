# 🚨 Jangan menuduh "klaim agen tidak terbukti" dari clone basi

**Tanggal:** 21 Okt 2026 · **Sumber:** koreksi Bos langsung · **Tingkat:** kelas bug proses, paling merusak di peran penjaga `main`

---

## Yang terjadi (verbatim Bos)

> *"keliru soal 'klaim agen tidak terbukti'. Clone Wulan basi saat memeriksa.
> Faktanya: agen Boss sudah benar-benar memperbaiki dua bug itu dan push sendiri
> ke branch ini (812d69b), plus membangun sistem bentuk resmi di master
> (21ce531) — perbaikan itu mendarat sesudah fetch terakhir Wulan, jadi tidak
> terlihat. Yang tidak ada memang hash '4668116' di repo ini (pekerjaannya
> mendarat sebagai 812d69b), tapi substansi laporan agen itu benar."*

Urutannya:

1. Wulan menyelesaikan perbaikan di `master`, lalu memeriksa branch agen.
2. Wulan mencari hash `4668116` yang disebut agen → **tidak ketemu**.
3. Wulan **menyimpulkan** "klaim agen tidak terbukti" dan melaporkannya ke Bos.
4. Padahal pekerjaan agen **sudah ada** — sebagai `812d69b`, mendarat **sesudah**
   fetch terakhir Wulan.
5. Bos mengoreksi. Substansi laporan agen **benar 100%**.

⇒ **Yang salah: Wulan. Yang benar: agen.** Wulan kan sudah minta maaf.

---

## Akar

**Hash BUKAN identitas pekerjaan.** Tiga sebab hash bisa berbeda dari yang disebut:

| Sebab | Akibat pada hash |
|---|---|
| Commit masuk setelah fetch terakhir | tidak ada di clone lokal sama sekali |
| Squash / rebase sebelum push | hash semua commit berubah |
| Cherry-pick ke branch lain | isi sama, hash beda |
| Push ulang setelah review dimulai | hash bergeser di tengah review |

Dan **clone lokal bukan cermin remote**. Kesimpulan "tidak ada" dari clone lokal
hanya sah untuk **satu titik waktu**, dan titik itu kadang sudah lewat.

---

## Urutan wajib SEBELUM menyebut "tidak terbukti" / "tidak ada"

```bash
# 1. FETCH DULU — tanpa ini semua kesimpulan di bawahnya batal
git fetch origin --prune

# 2. Lihat SEMUA branch remote, bukan cuma yang Anda kira
git branch -r
git log --oneline origin/<branch> -5

# 3. Cari SUBSTANSI, bukan hash: grep isi yang diklaim di seluruh riwayat
git log --all --oneline -S'enable_thinking'   -- app/
git log --all --oneline -S"r.headers.get"     -- app/
git log --all --oneline --grep='kartu\|bentuk\|502\|parser'

# 4. Bandingkan TANGGAL commit vs kapan clone terakhir disentuh
git log -1 --format='%ci  %h  %s' origin/<branch>
git reflog show origin/<branch> 2>/dev/null | head -3
```

Kalau langkah 3 **menemukan** kodenya, agen benar — berhenti menuduh, langsung
review isinya.

---

## Aturan kalimat (paling penting)

| ❌ JANGAN tulis | ✅ TULIS |
|---|---|
| "klaim agen tidak terbukti" | "hash X tidak ada di clone saya per <waktu>; substansinya sedang saya cari" |
| "agen belum mengerjakan" | "di clone saya per <waktu> belum terlihat; saya fetch ulang dulu" |
| "perbaikan itu tidak ada" | "perbaikan itu tidak ada **di ref yang saya periksa**" |

Kalimat pertama menuduh orang lain berbohong. Kalimat kedua jujur soal **batas
alat ukur sendiri**. Akibatnya jauh berbeda, padahal fakta yang Wulan pegang sama.

---

## Pola induk

Sama seperti §4q **"probe Wulan sendiri bisa basi"** — tapi arahnya keluar:

> **Sebelum menyalahkan PIHAK LAIN, pastikan dulu DATA YANG SAYA PEGANG masih
> berlaku. Basi bukan bukti.**

---

## Kalau ternyata Wulan salah

1. **Akui 1 kalimat, jangan dibela.** Contoh yang diterima Bos:
   *"Wulan minta maaf atas kesimpulan yang terburu-buru itu."*
2. Sebut **apa yang salah** (clone basi), bukan cuma "maaf saya salah".
3. Sebut **apa yang benar** (substansi agen benar, hash-nya `812d69b`).
4. Lanjut kerja — jangan berhenti di permintaan maaf.

Bos (`wulan-farming-reporting`) secara konsisten lebih menghargai koreksi terbuka
daripada argumen yang mempertahankan klaim lama.

---

## Cek cepat sebelum laporan

- [ ] Sudah `git fetch origin --prune` **di ronde ini**, bukan ronde lalu?
- [ ] Kalau hash tidak ketemu: sudah cari **substansi** (`-S` / `--grep`) di
      **semua** ref, bukan cuma satu branch?
- [ ] Kata "tidak terbukti" / "tidak ada" sudah diganti kalimat yang menyebut
      **batas pemeriksaan**?
- [ ] Sudah bandingkan **tanggal commit** dengan waktu clone terakhir disentuh?
