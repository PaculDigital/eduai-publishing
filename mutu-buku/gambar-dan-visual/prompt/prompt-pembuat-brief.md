# Prompt Pembuat Brief Visual — DIAMBIL DARI KODE

> Sumber: `brief_visual.py` → `PROMPT_BRIEF_LITERAL` & `PROMPT_BRIEF_KONSEPTUAL`.
> Prompt ini MENGHASILKAN brief; brief lalu masuk ke blok gaya sebagai `{brief}`.

## PROMPT_BRIEF_LITERAL (dipakai buku anak) — 757 karakter

```text
Buatkan SATU brief visual (2-3 kalimat, bahasa Inggris) untuk ilustrasi
di tengah bab buku umum non-fiksi, berdasarkan ringkasan bab di bawah.

SYARAT BRIEF:
1. Pilih SATU momen paling visual dari isi bab — adegan yang pembaca
   "lihat" saat membaca bagian tengah bab.
2. Konkret dan spesifik: siapa/apa saja yang terlihat, sedang melakukan
   apa, objek dan latar apa. Jangan konsep abstrak tanpa wujud.
3. Setting dan tokoh: Indonesia sehari-hari (bukan model iklan);
   sesuaikan dengan contoh yang dipakai di bab bila ada.
4. JANGAN pernah meminta teks, huruf, angka, logo, atau tulisan
   di dalam gambar.
5. Hanya deskripsi visual — tanpa penjelasan, tanpa pembuka/penutup.

RINGKASAN BAB:
{ringkasan_bab}

SUB-BAB DI SEKITAR POSISI GAMBAR:
{sub_bab}
```

## PROMPT_BRIEF_KONSEPTUAL (dipakai buku umum) — 1251 karakter

```text
Dari ringkasan bab berikut, buatkan SATU brief visual KONSEPTUAL
(2-3 kalimat, bahasa Inggris) untuk ilustrasi buku non-fiksi premium.

CARA BERPIKIR (ikuti urutannya):
1. IDE INTI: rumuskan satu kalimat — apa ide terpenting bab ini?
2. METAFORA VISUAL: ubah ide itu menjadi metafora visual yang konkret
   dan mengejutkan TAPI langsung terbaca. Benda nyata disusun dengan
   cara tak biasa. Contoh: bab tentang jebakan utang -> "a person rowing
   a small boat while water pours in through the sieve they bail with".
3. KOMPOSISI: satu fokus utama, negative space lega di sekelilingnya.
   Jangan penuhi frame.
4. DILARANG: adegan literal sehari-hari, teks/huruf/angka/logo,
   lebih dari satu ide dalam satu gambar.
5. DILARANG unsur lintas-budaya yang tidak pantas untuk pembaca Indonesia:
   babi/celengan babi, minuman keras, rokok, simbol agama apa pun,
   mata uang/simbol asing (dollar, euro), bangunan ikon negara lain.
   Pilih benda netral & sesuai konteks Indonesia (mis. celengan tanah liat,
   kaleng, atau tabung bambu — bukan piggy bank).
6. Output hanya 2-3 kalimat deskripsi visual bahasa Inggris. Hindari kata
   abstract/conceptual/glowing/luminous/gradient/3D — buku ini gaya cetak,
   bukan layar.

RINGKASAN BAB:
{ringkasan_bab}
```
