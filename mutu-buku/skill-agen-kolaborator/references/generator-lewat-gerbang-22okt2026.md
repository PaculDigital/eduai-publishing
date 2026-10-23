# 🧊 REVIEW "GENERATOR MELEWATI GERBANG" — 22 Okt 2026

> 📎 **Putaran berikutnya hari yang sama** (`69a64a6` → `82a99ee` → `f1da9bf`):
> `references/review-berulang-generator-buku-22okt2026.md`
> — jumlah asersi beda ≠ klaim salah · uji "berkas rusak tertinggal" (wajib
> `rm -f` dulu + uji timpa-berkas-baik) · **bagian baru di luar template
> (DAFTAR PUSTAKA)** · vonis **berjenjang** · "terpasang ≠ terbukti jalan".

Kelas review yang belum tertangkap katalog lama: **alat yang MENGHASILKAN
berkas, lalu memeriksa berkasnya sendiri.** Gerbangnya bisa sangat bagus
(48 asersi, 10 suntikan tertangkap) sementara **pagar masukannya bocor** —
berkas rusak sudah sampai ke tangan pengguna sebelum gerbang menolak.

Konteks nyata: review branch `agen/wulan/template-buku-generator`
(`34c02ad`, repo `eduai-publishing`) — generator `.docx` buku dari template
resmi. Semua klaim agen TERBUKTI, tapi Wulan menolak merge.

---

## R1. 🚨 TULIS-DULU-BARU-PERIKSA = berkas rusak tetap tertinggal

Pola cacat yang terbukti:

```python
buat(spec, arg[1])                        # ← berkas LANGSUNG ditulis ke disk
if '--tanpa-gerbang' not in sys.argv:
    r = subprocess.run([sys.executable, str(GERBANG), arg[1]])
    sys.exit(r.returncode)                # ← exit 1 benar, TAPI berkasnya SUDAH ADA
```

Bukti terukur: spec `{"bab": []}` → **EXIT 1** (perilaku benar), tapi
`tanpa-bab2.docx` **475.582 byte tetap ada di disk.**

**Kenapa ini kelas cacat, bukan detail:** begitu disambung ke web, pengguna
bisa **mengunduh berkas rusak** walau proses dilaporkan gagal. Sama bahayanya
dengan pagar yang cuma tulisan.

**Obat (URUTAN, bukan pemeriksaan baru):**
```
tulis ke berkas SEMENTARA  →  jalankan gerbang  →  gerbang EXIT 0 ?
                                                   ├─ ya  → os.replace(tmp, final)
                                                   └─ tidak → hapus tmp
```

**Cara menemukannya saat review** — jangan baca gerbangnya saja, baca
**urutan tulis**:
```bash
grep -n "open(\|write_text\|writestr\|subprocess.run\|sys.exit" <generator>.py | tail -20
```
Kalau `sys.exit(r.returncode)` muncul **sesudah** penulisan berkas → celah ini ada.

**Uji pembuktian (wajib, murah):**
```bash
python3 <generator>.py spec-rusak.json /tmp/keluaran.docx ; echo "EXIT=$?"
ls -la /tmp/keluaran.docx    # ← kalau ada padahal EXIT=1 → CELAH TERBUKTI
```

## R2. 🚨 VALIDASI INPUT DILAKUKAN GERBANG, BUKAN GENERATOR

`"romawi": "1"` (angka Arab, seharusnya `"I"`) **diterima** generator dan
ditulis jadi `BAB 1`. Baru gerbang menangkapnya (`J2b GAGAL`).

Akibat praktis: pesan galat datang **setelah** kerja mahal selesai, dan
berkasnya sudah jadi. Untuk mesin yang memanggil LLM/AI per bab, ini berarti
**biaya terbuang** sebelum input ditolak.

**Aturan:** generator WAJIB menolak input tak sah **sebelum** menulis apa pun —
`sys.exit("romawi harus angka Romawi: I, II, III…")`, exit ≠ 0, nol berkas.
Gerbang tetap dipertahankan sebagai lapis kedua (memeriksa hasil), bukan
sebagai satu-satunya pagar.

## R3. 🧾 EXIT CODE TERTUTUP PIPA — Wulan hampir salah baca 2×

```bash
python3 generator.py a.json b.docx 2>&1 | tail -6 ; echo "EXIT=$?"
```
`$?` di atas = **exit `tail`**, bukan generator. Wulan sempat mencatat
"EXIT=0" untuk generator yang sebenarnya **EXIT=1**.

**Aturan:** untuk memvonis exit code, jalankan TANPA pipa:
```bash
python3 generator.py a.json b.docx >/tmp/log.txt 2>&1 ; echo "EXIT SEBENARNYA=$?"
tail -20 /tmp/log.txt
```
(Aturan ini sudah ada untuk build/test; berlaku juga untuk skrip generator.)

## R4. ✅ YANG BENAR DARI AGEN INI — tiru, jangan curigai

| Yang dilakukan agen | Kenapa bagus |
|---|---|
| Hitung sendiri lalu **laporkan 0/9 font terpasang** | Jujur tidak berpura-pura aman |
| Tolak menaruh font berbayar di repo publik | Alasan lisensi/DMCA, ditulis di `fonts/README.md` |
| `periksa_font.py --folder` untuk folder privat | Jalan sah tanpa melanggar lisensi |
| 48 asersi + **10 suntikan** semua tertangkap | Gerbangnya sendiri kuat & bergigi |
| `git worktree add -f` untuk review di pohon bersih | Tidak mengotori kerja agen |

⚠️ **Pelajaran**: kalau gerbangnya bagus dan klaimnya jujur, **tetap cari celah
di URUTAN/INPUT**, bukan hanya di asersi. Kualitas gerbang tidak menutup celah
pagar masukan.

## R5. Vonis yang dipakai (contoh kalimat)

> Menolak merge bukan karena gerbangnya lemah — gerbangnya justru bagus —
> tapi karena **berkas rusak bisa sampai ke tangan pengguna** sebelum gerbang
> menolak.

Kalimat ini penting: menolak **dengan alasan yang tepat**, bukan menuduh
kualitas kerja agen rendah.
