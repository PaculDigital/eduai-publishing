# 9 JEBAKAN REVIEW & UJI CDP — TERUKUR (22 Okt 2026, statistik-lab)

Lahir dari review `eef25a9` → `812d69b` → `88eb330` → `f00ff4e` → `3d32c07`
→ `b66a862` → `1fc7bbb` → merge `dfad606`. Sembilan kelas kesalahan Wulan yang
**MENGHABISKAN putaran**. Hafalkan sebelum review.

Rujukan jebakan sisi-cara-uji: `references/jebakan-palsu-gagal-cdp-22okt2026.md`
(ada di skill `statistik-lab-cdp-tangkapan-layar`).

---

## J1. 🚨 CLONE BASI → MENUDUH "KLAIM AGEN TIDAK TERBUKTI" (kesalahan terburuk)

Wulan menyimpulkan agen Boss **berbohong** soal dua bug yang sudah diperbaiki.
Kenyataannya: perbaikan **benar-benar ada & sudah dipush** — Wulan memeriksa
clone yang **fetch terakhirnya sebelum** commit itu mendarat. Bos mengoreksi
langsung dan Wulan harus minta maaf.

**ATURAN KERAS:**
```
fetch  →  cari commit di SEMUA branch remote  →  BARU menyimpulkan
```
```bash
git -c credential.helper="store --file=<kredensial>" fetch origin
git branch -r --contains <hash>          # hash ada di remote mana saja
git log --oneline origin/<branch> -6     # bandingkan dengan yang Wulan punya
```

**JANGAN** menyimpulkan "tidak ada" / "tidak terbukti" dari repo lokal.
Kalau hash yang disebut Bos **tidak ketemu**, kemungkinan besar: (a) clone basi,
atau (b) pekerjaan mendarat dengan **hash LAIN** (kasus nyata: `4668116` →
mendarat sebagai `812d69b`). **Substansi > hash.** Verifikasi ke kode, bukan ke hash.

**Kalimat yang HARAM tanpa fetch:** *"klaim agen tidak terbukti"*, *"tidak ada di repo"*.

---

## J2. 🚨 UJI MEMAKAI PRODUKSI LAMA → 8 GAGAL PALSU

Wulan menguji fitur baru lewat domain, dapat **8 dari 9 GAGAL**, dan hampir
melaporkan "kode Bos rusak". Padahal **image produksi masih versi SEBELUM commit**
yang diuji.

**CEK DULU SEBELUM UJI (1 perintah):**
```bash
git log --oneline -1 HEAD
docker exec <container> cat /app/IMAGE_TAG   # atau: docker inspect --format '{{.Config.Image}}'
```
Kalau tag image **lebih tua** dari commit → **JANGAN uji lewat domain**.
Uji di container uji dengan kode disalin (`docker cp` + restart), atau build dulu.

**ATURAN INDUK:** hasil "GAGAL" dari uji yang menembak **produksi** tidak sah
sebagai vonis atas commit yang **belum deploy**.

---

## J3. 🚨 PORT LOOPBACK KONTAINER → URL UJI SELALU "Connection refused"

Port `127.0.0.1:8120` milik **loopback container**, bukan host. Chrome di host
tidak bisa membukanya → halaman kosong → "elemen tidak ditemukan" (GAGAL PALSU).

**CARA BENAR — tembak IP kontainer dari host:**
```bash
IP=$(docker inspect <container> --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
URL_UJI="http://$IP:8000/kualitatif" .venv/bin/python <uji.py>
```
Atau `docker exec` ke dalam container. **Jangan** `127.0.0.1:<port-host>`.

Cek cepat: `curl -s -o /dev/null -w "%{http_code}" http://$IP:8000/health` → 200.
Dari **dalam** container `curl` sering **tidak ada** → pakai
`python3 -c "import urllib.request as u; print(u.urlopen(...).status)"`.

---

## J4. 🚨 UJI MEMBACA VARIABEL YANG TIDAK BISA DIBACA → "tidak terbaca" PALSU

Tiga sebab nyata dalam SATU sesi:
| Yang diuji | Kenapa selalu kosong |
|---|---|
| `window.KUAL` | dideklarasikan `let KUAL` → **bukan** properti `window` |
| `localStorage.getItem('kual')` | kunci sebenarnya **`kualitatif_v1`** |
| `document.querySelector(...)` | panel masih **tersembunyi**, perlu diklik dulu |

**ATURAN: ukur KELUARAN yang dilihat mesin/user, bukan variabel internal.**
Contoh yang MENANG: alih-alih membaca `KUAL.swot.faktor[i].bobot`, baca
**`localStorage` mentah** (`lsPotongan`) + **teks skor di layar**.
Terbukti: `"bobot":0.25` benar-benar tersimpan sementara pembacaan variabel
bilang "tidak terbaca".

**Cari kunci yang benar dengan `grep`, jangan tebak:**
```bash
grep -n "KUNCI_SIMPAN\|localStorage.setItem" app/templates/<halaman>.html | head
```

---

## J5. POLA UJI YANG LOLOS SEMUA JEBAKAN DI ATAS

Yang akhirnya menghasilkan **9 LULUS / 0 GAGAL** setelah 5 percobaan gagal:

1. **Buka tab sendiri** lewat `PUT /json/new?<url>` (`GET` → **405**).
2. **Buktikan halaman yang termuat** — cek penanda DOM yang khas halaman itu
   (`pintu-swot`, `kartu-pilih`) **sebelum** mencari elemen lain. Kalau penanda
   tidak ada → **halaman salah**, bukan fitur hilang.
3. **Klik dulu** untuk membuka panel tersembunyi.
4. **Ukur perilaku**, bukan atribut: `getBoundingClientRect()` untuk lebar,
   `localStorage` mentah untuk nilai tersimpan, teks skor untuk hasil hitung.
5. **Uji bergigi**: kembalikan bug lama → uji **wajib** GAGAL. Kalau tetap
   LULUS, ujinya buta.

Template siap pakai: **`references/uji-cdp-perilaku-halaman.py`** (CDP, sudah
memuat 6 penjebak di bawah + uji bergigi).

---

## J6. MEMBACA KODE ≠ MEMBUKTIKAN PERILAKU

Untuk 10 temuan audit `3d32c07`, Wulan **membaca kode** dulu (cepat, benar
semua), **lalu** membuktikan 3 yang paling berisiko lewat browser. Itu urutan
yang benar dan hemat:

```
baca kode → susun daftar temuan → pilih 2-3 paling berisiko → buktikan di halaman
```
Membuktikan ke-10-nya lewat browser = lambat & rapuh.
Membuktikan **nol** lewat browser = vonis tanpa bukti perilaku.

**Yang WAJIB dibuktikan di halaman** (tidak cukup baca kode):
- nilai input yang bisa **hilang saat diketik** (`0.25` → `0`)
- lebar/posisi elemen di **layar HP**
- teks yang **dilihat user** (vonis, pesan galat)

---

## J7. 🚨 ASERSI SALAH TEMPAT → temuan "gagal" padahal fitur benar

Enam GAGAL PALSU dalam satu sesi, tak satu pun bug kode. Pola yang berulang:

| Wulan menguji | Kenyataan | Cara benar |
|---|---|---|
| cari `"Kutipan"` di **kartu pintu** | istilah itu hidup di **dalam** alur (Langkah 2), kartu pintu memakai contoh lain | uji istilah di tempat ia **dirender** (`grep -n "Kutipan"`) |
| `innerText` seluruh halaman, lalu "tidak muncul" | elemen ada & berisi, tapi induknya `display:none` | periksa `indukSembunyi` / `getBoundingClientRect().width > 0` |
| klik tombol **berbeda** untuk uji anti-duplikat | item ke-2 memang item BARU → wajar bertambah | klik tombol **sama** (`[data-x="0"]`), cek `disabled` |
| `placeholder === 'percaya pada review'` | sebenarnya `'cth: percaya pada review'` | pakai `in`, jangan `==` |
| tulis `.value` berisi `\n` di JS satu-lini | `SyntaxError: Invalid or unexpected token` | berkas `.py` + `String.fromCharCode(10,10)` |
| ambil ID dari tebakan (`mk-*`) | ID sebenarnya `kj-*` | `grep -n 'id="' <template>` DULU, jangan tebak nama ID |

**ATURAN INDUK:** sebelum menyebut "GAGAL", tanya satu pertanyaan —
*"apakah asersi Wulan ini menyentuh tempat yang BENAR?"*
Skrip uji yang salah = paling sering menyalahkan kode orang lain.

**Cara cepat membedakan uji-salah vs kode-salah:** jalankan asersi yang sama
terhadap **kode lama yang sudah pasti berperilaku X**. Kalau kode lama juga
"gagal" dengan asersi itu → **asersinya** yang salah.

---

## J8. 📊 SKALA BUKTI — jangan pukul rata semua temuan

Sesi 22 Okt 2026: 10 temuan audit, Wulan buktikan **4 di browser produksi**,
sisanya diverifikasi dari kode + gerbang. Itu **cukup** dan hemat.

| Kelas temuan | Bukti minimum |
|---|---|
| Nilai hilang saat diketik, lebar elemen di HP, teks yang dilihat user | **browser, wajib** |
| Parser menerima Markdown (`**KODE:**`) | jalankan **parser SUNGGUHAN** dari template via `node`, jangan salin logikanya ke Python |
| Bentuk keluaran AI (`bentuk='kartu'`) | panggil rute **hidup** sekali, cek hasil + kata terlarang |
| Ada/tidak ada fungsi, aturan pagar | baca kode + gerbang (cukup) |

**Parser:** `eval` potongan kode template HARUS di dalam sebuah **fungsi**
(`function urai(teks){ ... }`), bukan di akar skrip — kalau tidak, `return`
di dalam potongan menjadi `SyntaxError: Illegal return statement` dan hasilnya
**9 GAGAL PALSU**. Ambil HANYA baris parser (5 baris), bukan blok `if (...) return`.

---

## J9. 🚨 KATA KUNCI ASERSI ADA DI TEKS BAWAAN HALAMAN → "bug" palsu

Review `1fc7bbb` (perbaikan "foto mati permanen"). Wulan menguji
*"foto BARU yang gagal dimuat TIDAK boleh ditulis 'terhapus'"* dengan:

```python
tulisTerhapus: /terhapus/i.test(w.innerText)      # ❌ TERLALU LEBAR
```

Hasil: GAGAL — padahal pesan foto yang benar (`"Foto gagal dimuat — mungkin
sinyal putus sesaat"`) sudah tampil. Kata **"terhapus"** berasal dari
**petunjuk bawaan** panel: *"…tersimpan 3 hari lalu terhapus otomatis"*.

Obat: **cari FRASA pesan, bukan kata tunggal yang juga hidup di teks lain.**

```python
tulisTerhapus: /Foto sudah terhapus/i.test(txt)   # ✅ frasa pesan yang khas
```

**Aturan induk:** sebelum memakai kata kunci sebagai bukti, `grep` kata itu di
template — kalau muncul >1 tempat, asersinya WAJIB dipersempit ke frasa.
Ini sepupu J7: J7 salah **tempat**, J9 salah **lebar** asersi.

---

## J10. 🚨 403 DARI DOMAIN BELUM TENTU BUG APLIKASI — baca BADAN galatnya

Sesi merge `1fc7bbb`: uji unggah foto lewat domain dapat
**HTTP 403** dan Wulan hampir melaporkannya sebagai "rute unggah rusak di
produksi". Badan balasannya:

```
error code: 1010
```

Itu **Cloudflare** (menolak User-Agent klien), **bukan** aplikasi. Bukti
pembeda — klien yang sama, hanya UA diganti:

```
UA Python biasa  -> 403  error code: 1010
UA browser       -> 200  {"boleh":true,"id":...}
```

**Prosedur wajib saat uji rute lewat domain (Cloudflare di depan):**

```python
HEADER_BROWSER = {
    'User-Agent': ('Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/151.0 Mobile Safari/537.36'),
    'Accept': 'application/json',
}
```

1. **Cetak BADAN galat**, jangan cuma kode. `error code: 10xx` / HTML
   "Just a moment" / "Attention Required" = **lapis Cloudflare**.
2. Bandingkan **UA browser vs UA skrip**. Beda hasil ⇒ lapis depan, bukan kode.
3. Untuk memisahkan lapis: uji dari **dalam** container
   (`docker exec ... python3 -c "urllib.request.urlopen(http://127.0.0.1:8000/...)`).
   200 di dalam + 403 di domain ⇒ **pasti** gateway.
4. Baru setelah itu menyebut "bug". Menyebut "bug kode" untuk galat gateway =
   melanggar aturan Bos (502/403 kelas gateway, bukan kode).

⚠️ Ini **bukan** "Cloudflare rusak" — jangan tulis begitu. Yang dicatat adalah
**cara membedakan**, bukan klaim negatif tentang alat.
