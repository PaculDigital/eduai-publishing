# 🔁 REVIEW BERULANG BRANCH GENERATOR — 22 Okt 2026 (putaran 2–4)

> 📎 **Lanjutan hari yang sama:** putaran berikutnya membahas **jenis buku**
> (monograf A5, referensi B5, buku ajar OBE) dan **keputusan Bos** soal
> template berbeda per jenis → `references/jenis-buku-keputusan-dan-angka-teknis-22okt2026.md`
> — berisi angka twip/`w:sz` semua jenis, jebakan `ceil` vs `round`, dan
> status jujur apa yang BELUM ada.

Lanjutan `generator-lewat-gerbang-22okt2026.md` (putaran 1, `34c02ad`).
Bos mengirim **tiga update berurutan** di hari yang sama:

```
34c02ad  gerbang v2 (48 asersi)      → Wulan TOLAK (pagar input bocor)
69a64a6  gerbang v3 (54, tabel+gambar) → Wulan TOLAK (2 cacat masih ada)
82a99ee  fix: tulis atomik + validasi romawi → Wulan terima kode
f1da9bf  gerbang v2.3 (57, daftar pustaka)  → Wulan terima, 1 hal perlu pengesahan
```

`main` tetap `ef402e2` sepanjang 4 putaran. **Cek ini setiap kali** — klaim
"main utuh" harus dibuktikan, bukan dipercaya.

---

## R6. 🚨 ANGKA ASERSI BEDA ≠ KLAIM SALAH — cek dulu APA yang dilewati

Putaran 2: Bos klaim **54 asersi**, Wulan jalankan ke **template asli** dapat
**50**. Wulan hampir menuduh klaim tidak terbukti.

Ternyata: asersi `TB1–TB4` (tabel) dan `GB1–GB2` (gambar) **dilewati** karena
template asli tidak punya tabel/gambar. Begitu dijalankan ke **buku hasil
generator** → **54 LULUS / 0 GAGAL**.

**Aturan:** kalau jumlah asersi tidak cocok, jangan langsung tuduh. Tanya:
1. Apakah gerbang **melewati** asersi yang prasyaratnya tidak ada?
2. Sudah dijalankan ke **berkas yang tepat** (template vs buku jadi)?

Angka yang benar = angka pada **berkas yang punya semua unsur**. Laporkan
keduanya: "50 pada template asli, 54 pada buku jadi — selisihnya asersi tabel
& gambar yang aktif hanya bila unsur itu ada."

**Pola ini berulang di putaran 4** (`f1da9bf`): 57 asersi total, tapi hanya
**50** menyala di template asli karena `DP1–DP3` (daftar pustaka) tidak punya
prasyarat di template.

---

## R7. 🧾 UJI "APAKAH BERKAS RUSAK TERTINGGAL" — urutan yang benar

Cara membuktikan cacat R1 (tulis-dulu-baru-periksa) sudah ditutup:

```bash
rm -f /tmp/keluaran.docx
python3 generator.py spec-rusak.json /tmp/keluaran.docx
echo "EXIT SEBENARNYA=$?"
ls -la /tmp/keluaran.docx     # ← TIDAK BOLEH ADA
ls /tmp/*.tmp.docx            # ← sisa sementara juga TIDAK BOLEH ADA
```

**Wajib `rm -f` dulu.** Tanpa itu, berkas dari percobaan sebelumnya ikut
terbaca dan Wulan bisa menyimpulkan "masih bocor" padahal sudah bersih.

**Uji tambahan yang TIDAK ada di laporan agen — dan paling penting:**

```bash
md5sum buku-baik.docx                    # catat
python3 generator.py spec-rusak.json buku-baik.docx   # coba TIMPA dengan spec rusak
md5sum buku-baik.docx                    # HARUS SAMA
```

Ini menguji: percobaan gagal **tidak merusak hasil kerja yang sudah benar**.
Tanpa uji ini, tulis atomik bisa "terlihat benar" tapi tetap menimpa di jalur
`os.replace` yang salah tempat.

---

## R8. 🚨 BAGIAN BARU YANG TIDAK ADA DI TEMPLATE — wajib disahkan, bukan diterima diam-diam

Putaran 4 (`f1da9bf`): commit berjudul *"titik pemimpin LITERAL di cache daftar
isi"*, tapi isinya **jauh lebih besar**:

1. Titik pemimpin literal di teks TOC (`KATA PENGANTAR.........3`) — benar,
   tahan LibreOffice/mesin tanpa tab-leader.
2. **3 asersi baru `DP1–DP3`** — DAFTAR PUSTAKA: posisi, minimal 1 entri,
   indentasi gantung `w:hanging`.

**Temuan Wulan:** template asli hanya punya 4 Heading1
(`KATA PENGANTAR`, `BAB I`, `BAB II`, `TENTANG PENULIS`) — **tidak ada
DAFTAR PUSTAKA**. Generator **menambahkannya**.

⇒ Ini **melampaui** perintah Bos *"semua buku mengikuti template ini persis"*.
Nilainya benar (buku tanpa pustaka bukan buku terbit), tapi **statusnya harus
disahkan**, bukan diterima diam-diam. Kalau tidak disahkan, agen berikutnya akan
bingung: "kenapa ada bagian yang tidak ada di file template?"

**Cara memeriksa** — bandingkan daftar Heading1 template vs hasil:
```bash
python3 - <<'PY'
import zipfile, re
for label, path in [('TEMPLATE','templates/template-buku-resmi.docx'),
                    ('HASIL','/tmp/buku.docx')]:
    d = zipfile.ZipFile(path).read('word/document.xml').decode()
    print(f'== {label} ==')
    for m in re.finditer(r'w:val="Heading1"', d):
        a, b = d.rfind('<w:p ', 0, m.start()), d.find('</w:p>', m.start())
        print(' ', repr(''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', d[a:b]))))
PY
```

**Kalimat vonis yang dipakai:**
> Soal kode tidak ada keberatan. Tapi `DAFTAR PUSTAKA` adalah **bagian baru**
> yang tidak ada di template — itu **melampaui** "persis template". Benar
> secara penerbitan, tapi harus **Bos sahkan** dulu, bukan Wulan putuskan.

---

## R9. ⚠️ AKSI YANG TIDAK PERNAH DIJALANKAN — jangan sebut "terbukti"

Putaran 2: Wulan cek `proses_ai` di DB produksi → **0 baris** berjenis buku,
padahal 88 baris ada (semua dari revisi naskah). Artinya jalur latar belakang
buku **terpasang tapi belum pernah dipakai sekali pun**.

**Aturan:** bedakan tiga tingkat bukti, dan sebut tingkatnya:

| Tingkat | Kalimat yang benar |
|---|---|
| Kode ada | "terpasang" |
| Pernah dijalankan & lulus | "terbukti jalan" |
| Dipakai pengguna nyata | "terbukti di produksi" |

Jangan naikkan tingkat tanpa bukti. Wulan hampir bilang "jalur latar belakang
sudah jalan" padahal cuma **terpasang**.

---

## R10. 🔍 JUGA PERIKSA: penanganan galat di pekerjaan latar belakang

Saat memeriksa jalur latar (`app/proses.py`), lihat apakah `_kerja` punya
penanganan galat:

```python
try:
    hasil = _susun.susun(...)
    _proses.tandai_selesai(...)
finally:
    sdb.close()            # ← tidak ada tandai_gagal()
```

Kalau `susun()` melempar di tengah, status di halaman pantau **menggantung
selamanya** ("Menyiapkan kerangka buku"). Pengguna menunggu tanpa tahu apa-apa.

**Cari dengan:**
```bash
grep -n "tandai_selesai\|tandai_gagal\|except" <rute>.py | head -20
```
Kalau ada `tandai_selesai` tapi **tidak ada** `tandai_gagal` di blok yang sama
→ celah ini ada.

---

## R11. ✅ YANG SELALU WULAN LAKUKAN (jangan dilewati)

```bash
# 1. Fetch DULU — jangan vonis dari salinan basi
git fetch --all --prune
git ls-remote origin refs/heads/<branch> refs/heads/main

# 2. Kerja di pohon BERSIH, jangan di tempat kerja agen
git worktree add -f /tmp/cek-<hash> origin/<branch>

# 3. Cek template/aset tak berubah
md5sum templates/*.docx

# 4. Jalankan SEMUA gerbang + SEMUA uji bergigi
for f in scripts/uji_*.py; do python3 "$f" >/dev/null 2>&1; echo "$f EXIT=$?"; done

# 5. Bersihkan
git worktree remove --force /tmp/cek-<hash>
```

**Kalau ada satu uji bergigi EXIT≠0 → itu vonis TOLAK**, bukan "kemungkinan".

---

## R12. Vonis berjenjang (bukan cuma terima/tolak)

Review berulang butuh **tiga tingkat vonis**, bukan dua:

| Vonis | Kapan |
|---|---|
| **TOLAK** | ada cacat yang bisa melukai pengguna (berkas rusak sampai ke tangan user) |
| **TERIMA DENGAN CATATAN** | kode bersih, tapi ada hal yang **bukan hak Wulan** putuskan (bagian baru, font berlisensi) |
| **TERIMA** | semua gerbang hijau + tidak ada hal terbuka |

`f1da9bf` masuk **TERIMA DENGAN CATATAN** — bukan karena kode kurang, tapi
karena `DAFTAR PUSTAKA` dan font 0/9 butuh keputusan Bos.

---

## R13. Jangan lupa: pertanyaan "lebih cepat" bisa menyesatkan

Bos sempat bertanya apakah generator sama lambatnya dengan mesin buku anak.
Jawaban terukur: **tidak** — generator **0 panggilan AI, <1 detik**; yang lambat
mesin **penulis isi** (4-agen council, ~138 panggilan, ~36 menit/6 bab).

**Pelajaran:** kalau ditanya soal kecepatan, **ukur dulu sumber waktunya**.
Dua alat yang terlihat "sama-sama buku" bisa beda 2000×. Menjawab "sama" tanpa
mengukur = menyesatkan.

**Cara mengukurnya (murah, tanpa menjalankan AI):**
```bash
# hitung panggilan LLM per unit kerja
sed -n '/def generate_sub_bab/,/^def /p' pipeline.py | grep -cE "call_llm\("
# cari batas waktu / konkurensi
grep -n "KONKUREN_MAKS\|_BATAS_BAB\|max_workers" pipeline.py
```
Lalu kalikan: `panggilan × jumlah bab × jumlah sub-bab`. Itu angka yang jujur.

---

## R14. 🪞 KOREKSI DIRI: Wulan 2× hampir menuduh kode sehat dalam satu sesi

Dua kegagalan palsu terjadi **di sesi yang sama** — keduanya jenis yang sama:
**membandingkan dua hal yang memang seharusnya berbeda, lalu menyimpulkan
"rusak".**

| # | Yang Wulan lakukan | Kenapa salah |
|---|---|---|
| 1 | Bandingkan paragraf ke-`i` template vs hasil, temukan `autoSpaceDE` hilang | Paragraf ke-`i` **bedanya isi** — sudah beda format sejak awal. Membandingkan per-indeks = membandingkan apel–jeruk |
| 2 | Hitung `14,0 ÷ 2,54 × 1440 = 7937`, temukan template `7938`, hampir bilang "template salah" | **Word membulatkan KE ATAS**. `round()` ≠ kebiasaan Word |

### Aturan yang menutup keduanya

**A. Bandingkan per-JENIS-BLOK, bukan per-indeks.** Kelompokkan paragraf
menurut `pStyle` + bentuk, lalu bandingkan **format tiap jenis**:
```python
# ✅ BENAR — apakah semua paragraf gaya X memakai format yang sama?
for gaya in set(p['gaya'] for p in paras):
    fmt = {frozenset(p['rpr']) for p in paras if p['gaya'] == gaya}
    ok = len(fmt) == 1        # satu bentuk format per jenis = sehat
```
Kalau dalam satu jenis blok ada **>1 bentuk format**, baru periksa varian
mana yang sah (sering ada varian beralasan: isi vs daftar vs keterangan).

**B. Angka turunan Word selalu `ceil`, jangan `round`.**
Berlaku untuk twip dari cm, dan untuk `w:sz` (2 × pt untuk pt bulat — aman,
tapi kalau pt pecahan seperti 10,5 → 21 tepat).

**Pelajaran induk:** sebelum menuduh template/kode rusak, tanya dulu
**"apakah dua hal ini memang seharusnya identik?"** Kalau tidak — jangan
bandingkan.

---

## R15. 📖 SKILL YANG BASI = SUMBER KESALAHAN REVIEW

Saat review, Wulan menemukan skill `publishing/template-buku-resmi` masih
menulis:

```
Status gerbang: 20 LULUS / 0 GAGAL
"Hirarki template: ... TENTANG PENULIS"   (tanpa DAFTAR PUSTAKA)
"Semua buku mengikuti template ini persis"  (14×20 untuk SEMUA jenis)
```

Padahal keadaan sebenarnya: **57 asersi**, ada **DAFTAR PUSTAKA**, dan
**template berbeda per jenis** (A5/B5 untuk monograf/referensi/ajar).

**Bahaya:** agen berikutnya membaca skill lama → memakai 14×20 untuk monograf →
**salah format tanpa ada yang tahu**, karena skill-nya "resmi".

**Aturan review:** saat mereview alat yang menyentuh angka template, **cek juga
skill yang mengaturnya**. Kalau skill lebih tua dari kode, laporkan:

> "Kode sudah 57 asersi, tapi skill masih menulis 20 dan masih bilang template
> ini untuk semua jenis buku. Itu perlu diperbarui, kalau tidak agen berikutnya
> akan mengikuti angka lama."

⚠️ Kalau skill itu **user-owned**, Wulan **tidak boleh** menambalnya sendiri —
sebutkan ke Bos dan sarankan `hermes curator adopt <nama-skill>`.

