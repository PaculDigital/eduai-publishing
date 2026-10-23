# 🧊 REVIEW IDE ARSITEKTUR + JALUR LATAR — 22 Okt 2026

Lanjutan `references/vonis-dicabut-dan-ukur-kepresisian-22okt2026.md`
(rantai: `34c02ad` → `69a64a6` → `82a99ee`, repo `eduai-publishing`).

> 📎 **Lanjutannya ada di dua berkas ini** (putaran 3–4 hari yang sama):
> - `references/review-berulang-generator-buku-22okt2026.md` — jumlah asersi
>   beda ≠ klaim salah · uji "berkas rusak tertinggal" · **bagian baru di luar
>   template** · vonis **berjenjang** (tolak / terima-dengan-catatan / terima)
> - `references/template-vs-jenis-buku-22okt2026.md` — konflik **template resmi
>   (14×20, Palatino 10) vs 6 jenis buku** (B5/A5, TNR/Cambria) + usulan
>   **satu induk + profil per jenis**
>
> ⚠️ Skill `template-buku-resmi` milik Bos (user-owned) — **jangan ditulis
> agen**. Usulan perubahan tulis di rujukan sini, sampaikan ke Bos; adopsi
> lewat `hermes curator adopt template-buku-resmi`.

Sesi ini dua pertanyaan Bos yang **bukan** soal bug:
**(A)** *"apakah jalur latar buku sudah jalan?"*
**(B)** *"bagaimana generator ini bisa jalan untuk produksi bermutu? Apa ide kamu?"*

Dua-duanya dijawab dengan **peta lapisan**, bukan opini.

---

## L1. 🚨 "TERPASANG" ≠ "TERBUKTI JALAN"

Bos: *"Ya cek, sepertinya sudah."* — dan memang **terpasang**. Tapi terpasang
bukan terbukti jalan.

| Bukti TERPASANG (murah, tidak cukup) | Bukti TERBUKTI JALAN |
|---|---|
| `git ls-remote` cocok | ada baris DB hasil pekerjaan jenis itu |
| `app.routes` memuat path | ada berkas hasil di disk |
| template `.html` ada di image | ada entri log/tahap yang pernah maju |
| `grep` kode menemukan `_proses.jalankan(...)` | hitungan `proses_ai where jenis_dokumen like '%buku%'` > 0 |

**Hasil ukur nyata:**

```
docker exec eduai-app python3 -c "... from app.main import app; print routes"
/buku {'GET'} · /buku/mulai {'POST'} · /buku/susun {'POST'}
/buku/proses/{kode} {'GET'} · /buku/selesai {'GET'} · /buku/siapkan {'GET'}
template buku_proses.html 10032 byte ✅
proses_ai: 88 baris — jenis_dokumen 'buku': 0  ← BELUM PERNAH DIPAKAI
```

⇒ Kalimat yang benar: **"terpasang, belum pernah dijalankan sekali pun"**.
Bukan "sudah jalan" (berlebihan) dan bukan "belum ada" (salah).

**Perintah pemeriksaan (jalankan di container produksi, bukan host):**
```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep -i <app>
docker exec <app> python3 -c "from app.main import app; [print(r.path, getattr(r,'methods','')) for r in app.routes if '<kata>' in getattr(r,'path','')]"
docker exec <app> python3 -c "
import sqlite3,os
c=sqlite3.connect(os.getenv('EDUAI_DB') or '/app/data/eduai.db')
print('total', c.execute('select count(*) from proses_ai').fetchone()[0])
print('jenis', c.execute(\"select jenis_dokumen,count(*) from proses_ai group by 1\").fetchall())"
```

⚠️ **Baca kode di HOST tidak membuktikan apa pun soal produksi.** Host bisa
lebih baru dari image. Bukti produksi hanya `docker exec <container> ...`.

---

## L2. 🔴 CELAH: pekerjaan latar tanpa `tandai_gagal`

```python
async def _kerja(lapor):
    sdb = SessionLocal()
    try:
        hasil = _susun.susun(...)        # ← kalau ini MELEMPAR di bab 3 dari 6
        _proses.tandai_selesai(...)      #    baris ini tak pernah jalan
    finally:
        sdb.close()                      # ← dan tidak ada tandai_gagal
```

Akibatnya status `proses_ai` **menggantung di tahap terakhir yang tercatat**
("Menyiapkan kerangka buku") **selamanya**. Pengguna menunggu tanpa kabar;
tidak ada bedanya dari mesin yang benar-benar masih bekerja.

**Cara menemukannya saat review jalur latar — baca badan `_kerja`:**
```bash
grep -n "async def _kerja" -A25 app/main.py | grep -nE "try|except|finally|tandai_"
```
Kalau `finally` ada tapi `except` + `tandai_gagal` tidak → celah ini ada.
Ini **5 baris obat**, dampaknya besar. Sebut sebagai temuan **nomor satu**
saat melapor.

---

## L3. 🧭 PERTANYAAN "BAGAIMANA PRODUKSI BERMUTU" — jawab dengan PETA LAPISAN

Bos mengusulkan: *"bikin konten buku dengan AI format MD lalu docx, kalau sudah
jadi susun dan masukkan ke template — sepertinya lebih cepat."*

Jawaban yang diterima **bukan** "ide Bos bagus/kurang", tapi memetakan **4 lapis**:

| Lapis | Isi | Status terukur |
|---|---|---|
| 1. Penulis isi | mesin buku (4-agen council) | ✅ bermutu, **lambat sengaja** |
| 2. Perakit .docx | generator v2 | ✅ 54 asersi, <1 detik |
| 3. Pagar mutu | larangan_budaya · mutu_isi_buku · gerbang 54 · periksa_font | ✅ ada, urutannya perlu dibakukan |
| 4. Kejujuran ke pengguna | tahap nyata · "boleh tutup tab" · peringatan font | ⚠️ sebagian |

**Temuan kunci yang menghemat seluruh sesi:** mesin buku **sudah menulis
hampir-Markdown** (`### Judul Sub Bab` + penanda `[TABEL:…]`/`[DIAGRAM:…]`).
Jadi usul Bos = **tambah satu penerjemah MD di ujung generator**, bukan
membangun jalur kedua. Persis aturan Bos *"jangan buat baru, lebih optimal kan
yang sudah ada"*.

**Yang perlu DIPERIKSA dulu sebelum menjawab** (jangan mengarang bentuk blok):
```bash
# blok apa yang sudah diterima generator?
grep -n "def isi_blok" -A25 <generator>.py     # paragraf / tabel / gambar / daftar?
# mesin penulis menulis dalam bentuk apa?
grep -n "def parse_bab_file" -A15 <pipeline>.py
```
Hasil nyata: generator terima `str` (paragraf), `{"tabel":…}` (TB1–TB4),
`{"gambar":…}` (GB1–GB2). **Belum ada blok daftar** → itu juga yang menjelaskan
selisih `ListParagraph` di §V4 catatan sebelumnya.

---

## L4. ⚡ SOAL KECEPATAN — hitung panggilan jaringan dulu, jangan menebak

| | Generator .docx | Mesin penulis buku |
|---|---|---|
| Panggilan AI | **0** | **~138** untuk 6 bab |
| Waktu | < 1 detik | puluhan menit (1 bab ≈ 260–478 dtk) |

Sumber lambat (dibaca dari kode): **5–6 panggilan per sub-bab**
(architect → skeptic → pragmatist → editor → perbaikan sitasi → summarize),
+1 intro per bab, +visual (tabel/diagram/ilustrasi ≈24 gambar).

**Usul percepatan yang aman (dan pagarnya):**

| Cara | Efek | Risiko / pagar |
|---|---|---|
| Paralel **per BAB** (bukan per sub-bab) | ~6× | tiap bab punya outline sendiri ⇒ aman; **wajib +1 panggilan penyambung benang merah** |
| Paralel per sub-bab | terlihat hemat | ❌ sub-bab berantai (butuh ringkasan sebelumnya) ⇒ isi berulang. **Sudah terbukti rusak** |
| Kurangi agen 4 → 2 | ~50% | mutu turun — **jangan usul tanpa menyebut ini** |
| Pindah ke latar belakang | tab ditutup aman | **ini yang paling perlu**, dan fondasinya sudah ada |

Pagar wajib untuk paralel: bandingkan **3-gram antar bab**; >15% sama = tandai.

---

## L5. Bentuk laporan yang dipakai (Bos setuju)

1. **Tabel "Ide Bos vs Ide Wulan"** dengan kolom *beda sasaran* — bukan
   pemenang. Kalimat kuncinya:
   > "Ide Bos menyelesaikan **format**. Ide Wulan menyelesaikan **kecepatan**.
   > Kalau hanya MD→docx: buku tetap 36 menit. Kalau hanya paralel: format
   > tetap beda."
2. **Urutan kerja bernomor dengan bobot** (kecil/sedang/besar) + kenapa penting.
3. **Satu keputusan di akhir** — mulai dari yang mana. Jangan tawarkan lima.
4. Sebut **penghalang non-kode** (font 0/9) terpisah dari vonis kode.

Yang ditolak Bos: paragraf panjang tanpa angka, dan saran "percepat" tanpa
menyebut harga mutunya.
