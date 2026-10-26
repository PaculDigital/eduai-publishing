# EduAi — Platform Revisi Naskah Akademik

> Pintu masuk dokumen: **SOT.md** (lalu `docs/sot/`). Berkas di `_arsip/` adalah riwayat, bukan panduan.

> Asisten penulisan akademik: **membaca bentuk naskah, merevisi terkontrol,
> menyusun buku, dan mengonversi ke artikel jurnal.**
> Bukan generator tulisan dari nol — mesin **merevisi naskah yang sudah ada**.

---

## Apa yang dikerjakan

| Fitur | Keterangan |
| :- | :- |
| **Revisi naskah** | Mahasiswa meminta perbaikan bab/subbab tertentu; AI merevisi, hasilnya bisa diterima atau ditolak per bagian |
| **Peta naskah** | Jev (TypeSafe) membaca **bentuk** naskah: berapa bab, subbab, di mana letaknya — sebelum mesin & AI bekerja |
| **Buku** | Menyusun buku utuh (umum, ajar OBE, referensi, monograf, book chapter) dari RPS/naskah — termasuk ilustrasi, diagram, dan tata paragraf |
| **Konversi artikel jurnal** | Naskah skripsi/tesis → satu artikel jurnal utuh, dengan pemeriksaan 11 elemen wajib |
| **Kolaborasi pembimbing** | Pembimbing membaca naskah (OnlyOffice, mode baca) dan memberi catatan; mahasiswa menerima notifikasi |
| **Statistik & data** | Simulasi data penelitian, uji asumsi, analisis jalur |
| **Kuota & token** | Satu dompet token per akun; potong tepat satu kali di server saat pekerjaan selesai |

---

## Prinsip yang mengikat kode ini

1. **Jev hanya membaca BENTUK/STRUKTUR/KEBERADAAN** — tidak menilai mutu tulisan.
2. **Satu pintu AI** — semua panggilan model lewat 9router; tidak ada jalur kedua.
3. **Jev di depan, bukan di belakang** — Jev mengenali → mesin olah → AI tulis → Jev periksa hasil.
4. **Jangan menambal, cari akar** — perbaikan di sumbernya, bukan di hilir.
5. **Gerbang hijau di host ≠ produksi sehat** — bukti produksi hanya `docker exec`/`docker run`.

---

## Struktur folder

```
app/                     Kode aplikasi (88 modul)
  ├── main.py            Rute utama
  ├── ai.py              Pipa AI (satu pintu)
  ├── jev.py             Pemanggil Jev (jembatan 8130)
  ├── satpam.py          Pagar skema + validasi
  ├── peta3_jev.py       Mesin peta naskah
  ├── kuota.py           Dompet token
  ├── konversi.py        Konversi artikel jurnal
  ├── static/            CSS, JS, font, sprite ikon
  └── templates/         Template Jinja

buku_umum_*.py           Mesin buku (pipeline, assembly, gerbang)
jev_buku_umum.py         Jev untuk buku
diagram_buku.py          Diagram & ilustrasi buku
tata_paragraf.py         Tata letak paragraf

scripts/                 Gerbang uji & perkakas
  ├── periksa_kode.sh    Gerbang WAJIB sebelum deploy
  ├── gerbang_uji.sh     Kumpulan gerbang aplikasi
  └── salin_restart.sh   Salin berkas + buktikan md5 + restart

_sketsa/                 Alat uji & skrip sekali-pakai (dipensiunkan, tidak dihapus)
  └── jalankan_semua_gerbang.sh   Daftar lengkap gerbang (dijalankan dari sini)
_bahan/                  Bahan rujukan
_ikon-asli/              Wujud resmi ikon Lucide (untuk gerbang anti-karangan)
brand-ikon/              Aset merek

Dockerfile               Image produksi
jalankan.sh              Jalur deploy resmi (build → gerbang → up)
SOT_JEV_*.md             Source of Truth (status, putusan, larangan)
```

---

## Menjalankan

### Produksi (jalur resmi — jangan dilangkahi)

```bash
bash jalankan.sh
```

Urutannya: periksa kode → build image → **gerbang modul di image** → jalankan
container → cek kesehatan. Kalau gerbang gagal, deploy **berhenti**.

### Cek tanpa deploy

```bash
bash scripts/periksa_kode.sh          # gerbang statis + modul
python3 sot.py --periksa              # SOT selaras dengan kode?
```

### Uji cepat (bukan produksi)

```bash
bash scripts/salin_restart.sh eduai-app app/main.py
```

⚠️ `docker cp` **wajib** diikuti `docker restart` — aplikasi memuat kode sekali
saat start, tanpa `--reload`.

---

## Layanan pendukung

| Layanan | Port | Peran |
| :- | :- | :- |
| `eduai-app` | 8100 → 8000 | Aplikasi utama |
| `oo-converter` | 18081 | OnlyOffice editor & konversi |
| `satpam-jev` | 8130 | Jembatan Jev: chat → TypeSafe `/systemone` |
| 9router | 20128 | Gerbang AI tunggal (semua model) |

Domain produksi: `eduai.bikinaja.id`

---

## Rahasia — TIDAK ada di repo

Berkas berikut **sengaja dikecualikan** lewat `.gitignore` dan **tidak pernah**
masuk repo:

```
.env                    Semua kunci API (Scopus, Router, InferHub, dll)
.jwt_oo_secret          Rahasia OnlyOffice
data/*.db               Database user
data/*token*.json       Token layanan pihak ketiga
_arsip/                 Arsip historis
_contoh-dokumen/        Contoh dokumen besar
_potret/                Tangkapan layar uji
```

Untuk menjalankan sendiri, buat `.env` dari contoh di dokumentasi dan isi
kunci milik sendiri. **Jangan pernah** commit `.env`.

---

## Batas proyek

Repo ini **satu dunia**: hanya berkas di folder ini. Kredensial, `.env`, atau
berkas proyek lain (OJS, WA Blast, statistik-lab) **tidak boleh** dipinjam —
walau domainnya sama. Butuh kredensial → buat sendiri, taruh di `.env` repo ini.

---

## Dokumen acuan

| Berkas | Isi |
| :- | :- |
| `SOT_JEV_BUKU_UMUM_20OKT2026.md` | **Source of Truth** — status terkini, putusan, larangan |
| `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md` | Peta naskah & peran Jev |
| `ATURAN_BATAS_PROYEK_03OKT2026.md` | Batas keras antar-proyek |
| `PANDUAN_PAKAI_JEV.md` | Cara memakai Jev dengan benar |

> **Aturan tertulis tidak memaksa — hanya gerbang yang bisa GAGAL.**
> Karena itu setiap aturan penting di repo ini punya gerbangnya sendiri.
