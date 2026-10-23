# 🧊 REVIEW LANJUTAN — VONIS DICABUT SETELAH PERBAIKAN TERUKUR

Sambungan `references/generator-lewat-gerbang-22okt2026.md`.
Sesi 22 Okt 2026, tiga ronde review branch `agen/wulan/template-buku-generator`
(repo `eduai-publishing`): `34c02ad` → `69a64a6` → `82a99ee`.

Fokus: **cara mencabut vonis hanya setelah bukti**, dan **cara mengukur
"apakah hasil generator PERSIS template"** — pertanyaan yang paling sering
ditanyakan Bos dan paling mudah dijawab dengan klaim palsu.

---

## V1. Ronde 2 — SEMUA klaim terverifikasi, gerbang naik 48 → 54 asersi

| Klaim agen | Hasil ukur Wulan |
|---|---|
| head `69a64a6` | ✅ cocok `ls-remote` |
| gerbang 54 asersi | ✅ **54/54** pada buku hasil |
| `main` tetap `ef402e2` | ✅ tidak tersentuh |
| MD5 template | ✅ `0bb7bc5c…` tidak berubah |

⚠️ **JEBAKAN ANGKA ASERSI:** gerbang pada **template asli** hanya melaporkan
**50 LULUS**, bukan 54. Kelihatan seperti klaim palsu — **ternyata bukan.**
Asersi tabel (TB1–TB4) dan gambar (GB1–GB2) **dilewati** kalau dokumen tidak
punya tabel/tidak punya gambar berketerangan. Template asli: 0 tabel,
3 gambar tanpa keterangan "Gambar...".

⇒ **Aturan: ukur asersi pada KARYA yang memicu semua asersi** (buku hasil),
bukan pada dokumen minimal (template). Selisih jumlah asersi antara keduanya
adalah **perilaku wajar**, BUKAN bukti klaim palsu. Selidiki dulu sebelum
menuduh — Wulan hampir mengulang kesalahan lama.

Hasil uji: `uji_bergigi_v3.py` 6/6 suntikan tertangkap; 2 cacat lama
(R1 tulis-dulu, R2 validasi-di-gerbang) **MASIH ADA** di `69a64a6`.

---

## V2. Ronde 3 (`82a99ee`) — perbaikan tepat sasaran, vonis DICABUT

Diff yang diperiksa: +46 baris di generator, +40 di uji generator, +24 di README.
Isinya **persis** obat yang diminta (bukan tambalan):

```python
ROMAWI_SAH = re.compile(r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$')
if not spec['bab']:  sys.exit('Spec ditolak: daftar "bab" kosong — buku wajib punya bab.')
for b in spec['bab']:
    if not ROMAWI_SAH.match(str(b.get('romawi',''))):
        sys.exit(f'Spec ditolak: romawi bab tidak sah: ...')

keluaran  = Path(arg[1])
sementara = keluaran.with_name(keluaran.name + '.tmp.docx')
try:
    buat(spec, str(sementara), ...)
    if gerbang(str(sementara)) != 0:
        sementara.unlink(missing_ok=True); sys.exit(1)
    sementara.replace(keluaran)          # ← baru jadi nama akhir
except BaseException:
    sementara.unlink(missing_ok=True); raise
```

### Bukti yang Wulan kumpulkan sebelum mencabut vonis

| Uji | Hasil |
|---|---|
| buku normal | **54/54 LULUS**, `buku.docx` 478.678 byte |
| spec `bab: []` | EXIT 1, nama akhir **TIDAK ADA** |
| spec `romawi: "1"` | EXIT 1, nama akhir **TIDAK ADA** |
| sisa `*.tmp.docx` | **TIDAK ADA** |
| **buku BAIK ditimpa spec RUSAK** | MD5 `d2d76641…` **TIDAK BERUBAH** |
| `uji_generator.py` | **29 LULUS / 0 GAGAL** (naik dari 16) |
| semua `uji_bergigi*` | EXIT 0 |

⇒ Vonis dicabut **hanya karena** uji baris ke-5 lulus. Uji itu yang paling
penting dan paling sering terlupa: membuktikan percobaan GAGAL tidak merusak
hasil kerja yang sudah BENAR. Tanpa itu, "sudah diperbaiki" belum terbukti aman.

**Asersi uji agen bertambah 16 → 29** dan lima di antaranya khusus menguji cacat
R1/R2 — jadi kalau nanti ada yang merusak lagi, uji menangkapnya. Ini bentuk
perbaikan yang benar: **obat + uji yang menjaga obatnya.**

---

## V3. PERTANYAAN BOS: "apakah hasil generator PERSIS template, termasuk ukuran?"

Jawaban wajib **diukur**. Cara yang terbukti:

### V3a. Ukur yang menentukan wajah buku dengan SIDIK SHA-256

```python
import hashlib, zipfile
def baca(p, n): return zipfile.ZipFile(p).read(n).decode('utf-8')
def sidik(s):  return hashlib.sha256(s.encode()).hexdigest()[:16]

sidik(baca(ASLI,'word/styles.xml'))   == sidik(baca(HASIL,'word/styles.xml'))
sidik(baca(ASLI,'word/fontTable.xml'))== sidik(baca(HASIL,'word/fontTable.xml'))
# + tiap <w:style w:styleId="Normal|Heading1|Heading2|TOC1|TOC2">
# + tiap <w:sectPr> → <w:pgSz .../> dan <w:pgMar .../>
# + <w:docDefaults>
```

**Hasil terukur:** styles.xml **IDENTIK** · fontTable **IDENTIK** · pgSz
**IDENTIK** · pgMar **IDENTIK** · docDefaults **IDENTIK** · semua gaya inti
**IDENTIK**.

⇒ Generator bekerja dengan cara **menyalin template lalu mengganti isi**, jadi
setelan halaman & gaya **tidak mungkin melenceng**. Keunggulan bentuk ini
dibanding generator yang membangun .docx dari nol — sebutkan ini saat melapor.

### V3b. 🚨 JANGAN membandingkan paragraf ke-i — isinya beda

Wulan sempat salah: membandingkan paragraf indeks 3 template vs hasil, melihat
`pPr` berbeda, lalu **hampir menuduh format hilang**. Ternyata itu paragraf
berbeda isi (template: Lorem ipsum; hasil: teks nyata).

⇒ **Cara benar:** kelompokkan paragraf per **(gaya, font, ukuran)** — bukan per
nomor — lalu bandingkan atribut `pPr` yang dipakai tiap kelompok
(`autoSpaceDE`, `autoSpaceDN`, `adjustRightInd`, `jc`, `spacing`, `ind`,
`keepNext`). Baru setelah itu selisihnya bermakna.

### V3c. Selisih jumlah berkas ZIP = wajar

Template 25 berkas, hasil 26 (`word/media/buku1.png`). Itu gambar baru dari
JSON — bukan cacat. Selisih jumlah gambar/tabel **wajar** karena isi berbeda.

### V3d. Cek "generator mengarang font?"

Uji yang benar: apakah ada pasangan `(font, sz)` yang **ADA di hasil tapi TIDAK
ADA di template**?
```python
asing = set(font_hasil) - set(font_template)   # hasil terukur: TIDAK ADA
```

---

## V4. BATAS KEPERSISAN YANG HARUS DISEBUT JUJUR

PERSIS: halaman · batas · gutter · header/footer · gaya Normal/Heading1/
Heading2/TOC1/TOC2 · font isi Palatino 10 pt · perataan both.

BELUM PERSIS:

| Hal | Selisih terukur |
|---|---|
| Paragraf daftar `ListParagraph` | Template `spacing after=200 line=276` + indentasi daftar; hasil paragraf biasa `after=0`, tanpa nomor |
| Blok daftar bernomor/berpoin | Belum ada — daftar jadi paragraf biasa |

⇒ Buku tanpa daftar bernomor: **siap produksi**. Buku yang butuh daftar persis
template: **belum**. Sampaikan pembatas ini **sebelum** ditanya.

---

## V5. FONT 0/9 — PENGHALANG YANG BUKAN SOAL KODE

```
periksa_font.py → RINGKAS: 0/9 font ada
```

Buku lolos 54 asersi XML, tapi **tetap berubah wujud** di mesin tanpa
`Palatino Linotype` / `Trajan Pro` — Word mengganti diam-diam.

Ini **bukan cacat agen**: menaruh font berbayar di repo publik = pelanggaran
lisensi/DMCA. Solusi sah: pasang di **mesin render/cetak**, periksa folder
privat dengan `periksa_font.py --folder`.

⚠️ **Jangan jadikan ini alasan menolak merge kode** — ini keputusan
infrastruktur/lisensi milik Bos, bukan cacat branch. Pisahkan vonis kode dari
vonis font, dan tanyakan yang kedua ke Bos.

---

## V6. CARA MELAPOR KE BOS (bentuk yang dipakai, dan Bos setuju)

1. **Tabel klaim vs hasil ukur** — satu baris per klaim, kolom `✅/⚠️/🔴`.
2. **Tabel uji Wulan** — nama uji + hasil angka, bukan "sudah dicek".
3. **Cacat: tunjukkan keluaran nyata** (exit code + `ls -la` berkas), bukan narasi.
4. **Penilaian per aspek** (gerbang / tabel-gambar / pagar input / font) — biar
   Bos tahu mana yang sudah beres dan mana yang belum.
5. **Satu keputusan di akhir** — merge sekarang / tunda / perbaiki dulu.
   Jangan tawarkan lima pilihan.

Yang **tidak** dipakai: paragraf panjang pujian untuk agen, atau sebaliknya
tuduhan tanpa bukti. Netral: "ini klaim, ini angka, ini vonis".

---

## V7. TEMUAN LAIN: LAMBAT BUKAN BERARTI BUG

Bos bertanya *"uji generate buku anak lama sekali, apakah generator ini sama?"*

Jawaban terukur — **dua mesin berbeda**:

| | Generator .docx | Mesin penulis buku (buku-umum) |
|---|---|---|
| Panggilan AI | **0** | **~138** untuk 6 bab |
| Waktu | < 1 detik | puluhan menit |
| Pekerjaan | merakit dari JSON | menulis isi pakai 4-agen council |

Sumber lambat pada mesin buku: **5–6 panggilan AI per sub-bab**
(architect → skeptic → pragmatist → editor → perbaikan sitasi → summarize),
+ 1 intro per bab, + visual (tabel/diagram/ilustrasi).

⚠️ **Pelajaran review:** sebelum menyimpulkan "lambat = ada bug", hitung dulu
**jumlah panggilan jaringan per unit kerja** dari kode. Beban yang disengaja
(4-agen council) bukan cacat — dan menyarankan "percepat" tanpa menyebut
trade-off mutu adalah saran yang salah.

Obat yang benar untuk keluhan "kelamaan" bukan memotong agen, tapi
**memindahkan ke latar belakang** (`/buku/susun` → titip `app/proses.py` →
ambil di `/buku/proses/{kode}`) supaya tab ditutup pun tidak menghilangkan hasil.
