# 🧾 Vonis review = JUJUR soal alat uji, bukan cuma soal kode agen lain

Lahir dari sesi review 21–22 Okt 2026 (Statistik Lab, branch `9faa4c8` /
`7c05b8a`). Bos menutup sesi dengan pertanyaan tajam:

> *"Kok sekarang kamu sering salah dan lambat respon. Apa yang terjadi?"*

Itu **sinyal kelas**, bukan keluhan sekali. Jawabannya harus masuk ke cara
Wulan menulis laporan review.

---

## 1. 📊 Laporan WAJIB memisahkan "bug kode" dari "salah alat uji"

Laporan lama Wulan berbentuk daftar "GAGAL". Bos membacanya sebagai *"kode saya
rusak"*. Padahal setelah dihitung:

| Sumber | Jumlah |
|---|---|
| "GAGAL" yang dilaporkan Wulan | 16 |
| **Bug kode SUNGGUHAN** | **2** |
| Salah alat uji Wulan | 14 |

⇒ Format laporan yang benar — **dua tabel terpisah, di awal**:

```
## ✅ Terbukti bekerja        (bukti positif, angka)
## 🔴 Bug kode NYATA          (dengan reproduksi + kontrol pembanding)
## ⚠️ Celah (bukan bug)       (belum ada, dampaknya apa)
## 📋 Jujur — salah Wulan     (N kesalahan, tabel: salah → akibat)
```

Aturan: **kalau satu asersi GAGAL, tulis juga kontrolnya.** Contoh yang dipakai
dan berhasil meyakinkan: `segmen ="bukan array"` → `TypeError`, sedangkan data
normal → `err: None`. Kontrol itu yang membuktikan bugnya nyata, bukan masalah
lama.

⚠️ **Jangan pernah menulis "kode agen lain salah" tanpa kontrol pembanding.**
Itu tuduhan, bukan temuan.

---

## 2. 🧮 Akui salah pakai ANGKA, bukan penjelasan

Pola yang diterima Bos:

> *"Wulan salah 5× dalam pengujian ini. Semua karena cara menangani
> `confirm()`, bukan karena kode. **Kode Bos tidak satu pun yang salah dari 5
> kesalahan itu.**"*

Yang **ditolak**: paragraf panjang membela diri, atau diam soal kesalahan
sendiri lalu langsung pindah ke kesimpulan.

Aturan:
- **Sebut jumlahnya** ("5×", "8×").
- **Sebut akarnya satu kalimat** (mis. *"semua karena menebak bentuk data"*).
- **Sebutkan pemisahnya tegas**: berapa bug kode, berapa salah Wulan.
- **Jangan mengulang penjelasan yang sama** di beberapa bagian laporan.

---

## 3. 🎯 Kalau Bos tanya "kenapa lambat", JANGAN mengarang angka kecepatan

Wulan **tidak** punya catatan waktu per panggilan model. Menjawab
*"modelnya lambat"* = melanggar aturan Bos (laporan lambat WAJIB menyebut waktu
terukur + nama model asli + panjang prompt, kalau tidak ⇒ **tarik klaimnya**).

Yang **boleh** dan sudah terbukti diterima:

> *"Wulan tidak bisa mengukur kecepatan model dari sini, dan Wulan tidak akan
> mengarang angka. Yang Wulan tahu pasti: 5 tebakan salah = 5 putaran uji ulang,
> satu putaran 2–4 menit ⇒ ±15 menit terbuang untuk kesalahan yang tidak perlu."*

⇒ Sebab lambat yang **jujur & terukur**: **jumlah putaran ulang**, bukan
spekulasi tentang model/provider.

---

## 4. 🚦 Titik berhenti: 10 putaran tanpa temuan = STOP dan serahkan ke Bos

Sesi itu menghabiskan ±10 putaran memperbaiki skrip uji. Yang akhirnya
menyelesaikan: **menyerahkan verifikasi 30 detik ke Bos** (buka halaman, klik
Simpan, klik Buka). Terukur lebih murah daripada satu putaran CDP.

**Aturan:**

> Setelah **3 putaran** memperbaiki **alat uji** tanpa hasil baru, hentikan.
> Laporkan: apa yang sudah pasti, apa yang belum bisa dibuktikan, dan
> **satu langkah manual** yang Bos bisa lakukan sendiri (< 1 menit).

Jangan dibungkus sebagai "masih Wulan cek" — itu yang membuat Bos merasa
lambat.

---

## 5. ✅ Merge & deploy: urutan yang dipakai dan hasilnya EXIT 0

```bash
# 1. cadangan titik mundur (branch, BUKAN tag yang mengganggu)
git branch -f cadangan-pra-<sha-pendek>-$(date +%H%M)

# 2. merge --no-ff supaya riwayat branch agen tetap terlihat
git -c user.name="Wulan" -c user.email="wulan@bikinaja.id" \
    merge <sha> --no-ff -m "<ringkas: fitur + perbaikan>"

# 3. buktikan fitur ADA di working tree SEBELUM build
grep -c "<nama fungsi baru>" app/templates/x.html
grep -c "<penanda fitur lama>"  app/templates/x.html   # perbaikan LAMA masih utuh

# 4. gerbang
python gerbang_sintaks_js.py && python sot.py --periksa

# 5. push (credential helper dari vault, token disamarkan)
git -c credential.helper="store --file=/opt/data/vault/.git-credentials-eduai" \
    push origin master 2>&1 | sed 's/gh[pousr]_[A-Za-z0-9]*/<TOKEN>/g'

# 6. deploy
bash jalankan.sh        # background + notify_on_complete; cek "EXIT=0"

# 7. bukti di IMAGE, bukan di host
docker inspect <container> --format 'image: {{.Config.Image}}'
docker exec <container> python3 -c "import PIL; print(PIL.__version__)"
```

⚠️ **Bukti "fitur ada" harus dari image/container**, bukan `grep` di host.
Memori Bos sudah mencatat jebakan `Dockerfile` = daftar putih (`ModuleNotFoundError`
walau 142 gerbang hijau karena gerbangnya jalan di HOST).

⚠️ **Sesudah merge, jalankan uji ke `BASE` produksi**, bukan hanya container —
dan skrip uji wajib bisa menerima `sys.argv[1]` sebagai `BASE`.

⚠️ **Uji yang LULUS di container bisa belum diulang di produksi.** Kalau itu
terjadi, **jangan klaim "terbukti di produksi"**. Tulis apa adanya: uji X lulus
di container, uji Y belum bisa diulang karena alat ujinya rusak.

---

## 6. 📌 Ringkas: pemicu → tindakan

| Pemicu | Tindakan |
|---|---|
| Bos: *"kamu sering salah dan lambat"* | hitung **jumlah putaran ulang**, akui dengan angka, jangan spekulasi model |
| 3+ GAGAL pada kode yang lulus di tempat lain | **alat uji salah** sampai terbukti sebaliknya |
| 3 putaran memperbaiki alat uji tanpa hasil | **STOP**, serahkan 1 langkah manual ke Bos |
| Mau melapor "bug" | sertakan **kontrol pembanding** (data normal = tanpa galat) |
| Merge & deploy | `--no-ff`, cadangan branch, bukti dari **image**, uji ke `BASE` produksi |
