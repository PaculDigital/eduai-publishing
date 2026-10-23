# 📚 TEMPLATE RESMI vs 6 JENIS BUKU — konflik yang WAJIB diputuskan Bos

Diukur 22 Okt 2026 dari `SKILL.md` tiap skill buku. **Jangan disamakan.**

Konteks: Bos menetapkan *"semua buku mengikuti template ini persis"* (14×20 cm,
Palatino 10 pt). Ternyata 5 skill buku lain punya angka sendiri. Ini **konflik
nyata** yang tidak boleh dijawab sepihak oleh Wulan.

## 1. Angka tiap jenis (dibaca dari skill masing-masing)

| Skill | Ukuran | Font isi | Margin | Ciri khas |
|---|---|---|---|---|
| **Template resmi Bayana** | **14 × 20 cm** | **Palatino Linotype 10 pt** | **1,60 / 1,02 cm** | judul Trajan Pro 22 pt |
| `buku-umum` | **B5** (17,6 × 25,0) | Times New Roman 12 pt | 2,0 cm | naratif, "Anda" |
| `buku-referensi` | **B5** (17,6 × 25,0) | TNR 12 pt | 2,0 cm | tabel komparasi teori wajib/bab, indeks subjek+nama, APA7 |
| `buku-monograf` | **A5** (14,8 × 21,0) | **Cambria 11 pt** | 2,0 cm | novelty wajib, 150–180 hlm |
| `buku-ajar-obe` | — | **TNR 12 pt** | 2,0 cm | RPS OBE, TIU/TIK 9pt italic, hanging indent 0,6 cm, heading 16pt |
| `book-chapter` | **A5** (14,8 × 21,0) | **Cambria** | 2,0 cm | **maks 15 halaman**, glosarium tabel 2 kolom |
| `buku-anak` | 14 × 20 | Palatino 10 pt | 1,60 / 1,02 | "kamu", kalimat pendek, ilustrasi banyak |

⇒ **Enam ukuran, enam font, tiga ukuran halaman berbeda.** Tidak satu pun sama
kecuali buku anak dengan template resmi.

## 2. Kalau template resmi dipaksa ke semua jenis

| Skill | Yang berubah / rusak |
|---|---|
| `buku-monograf` | A5 → 14×20; **Cambria 11 pt → Palatino 10 pt** |
| `book-chapter` | A5 → 14×20; Cambria → Palatino; **batas 15 halaman jadi tak berlaku** |
| `buku-ajar-obe` | TNR 12 → Palatino 10; hanging indent 0,6 cm bisa rusak |
| `buku-referensi` | B5 → 14×20 (**sempit 3,6 cm**) → tabel komparasi teori bisa pecah |

## 3. Usulan Wulan: SATU template induk + PROFIL per jenis

Bukan 6 template terpisah. Bukan juga memaksa semua jadi satu.

```
template-buku-resmi.docx  (INDUK: struktur, gaya, penomoran, blok tabel/gambar)
   ↓ dibaca bersama profil
profil-buku-umum.json      → B5, TNR 12, margin 2,0
profil-buku-referensi.json → B5, TNR 12, margin 2,0
profil-buku-monograf.json  → A5, Cambria 11, margin 2,0
profil-buku-ajar.json      → 14×20, TNR 12, hanging indent 0,6
profil-book-chapter.json   → A5, Cambria, maks 15 halaman
profil-buku-anak.json      → 14×20, Palatino 10 (template resmi)
```

**Kenapa lebih baik:**
- Gerbang tetap **satu** (`periksa_buku_template.py` baca profil, bukan 6 gerbang)
- Struktur **satu sumber** (bab, sub-bab, daftar isi, penomoran) — nol duplikasi
- Setiap jenis tetap sah (monograf tetap Cambria 11)
- Ubah satu angka profil → semua buku jenis itu ikut

### WAJIB SAMA untuk semua jenis (wajah penerbit)
- Urutan bagian: sampul → hak cipta → pengantar → daftar isi → bab → **daftar pustaka** → tentang penulis
- Judul bab **dua baris** (`BAB I` + `<w:br/>` + judul)
- Nomor bab **Romawi**
- Gaya daftar isi: titik pemimpin + nomor halaman
- Blok tabel: garis `808080`, kepala abu `F2F2F2`
- Gambar + keterangan "Gambar: ..."

### BOLEH BEDA per profil
- Ukuran halaman (B5 / A5 / 14×20)
- Batas margin (2,0 / 1,60-1,02)
- Font & ukuran isi (TNR 12 / Cambria 11 / Palatino 10)
- Font judul (Trajan Pro 22 / Cambria 14 / TNR 16)
- Jarak baris (1,15 / 1,0 / line 240)

## 4. Yang lebih berbahaya dari format salah: ISI salah label

Format cuma separuh. **Ciri isi wajib per jenis:**

| Jenis | Ciri isi WAJIB |
|---|---|
| buku umum | naratif, "Anda", tanpa sitasi wajib |
| buku referensi | **tabel komparasi teori tiap bab**, indeks subjek + nama, APA7 |
| monograf | **novelty wajib**, satu penelitian, 150–180 hlm |
| buku ajar OBE | **RPS OBE**, TIU/TIK, latihan, hanging indent |
| book chapter | **maks 15 halaman**, glosarium 2 kolom |
| buku anak | "kamu", kalimat pendek, ilustrasi, larangan budaya ketat |

⇒ Format disamakan tapi isi tidak disesuaikan = **buku umum berlabel
"monograf"**. Lebih berbahaya daripada format melenceng.

## 5. Tiga pertanyaan yang WULAN TIDAK BOLEH JAWAB SENDIRI

1. **Template 14×20 cm untuk jenis apa saja?** Semua buku Bayana, atau cuma
   buku umum/anak? Kalau monograf tetap A5, apakah itu "melanggar" perintah
   "semua buku ikut template"?
2. **Kalau semua ikut template resmi** — bolehkah skill monograf/book-chapter/
   buku-ajar **diubah** (A5 → 14×20, Cambria → Palatino)? Itu mengubah standar
   yang sudah terpakai.
3. **Atau dua jalur:** buku **Bayana** (template resmi) vs buku **akademik**
   (A5/B5, Cambria/TNR) — dipisah jelas di `/buku`?

**Alasan harus tanya:** salah putus = **standar penerbit berubah** atau
**naskah akademik rusak formatnya**. Keduanya merusak.

## 6. Urutan pengerjaan yang Wulan sarankan

| # | Langkah | Alasan urutan |
|---|---|---|
| 1 | Kunci profil **buku-umum** = template resmi | sudah jalan, tinggal disahkan |
| 2 | Buat **kerangka profil** (1 JSON per jenis) | tanpa ini 6 jenis berceceran |
| 3 | **buku-ajar OBE** | paling jauh bedanya (hanging indent, TIU/TIK) — kalau ini bisa, sisanya mudah |
| 4 | **book-chapter** | ada aturan khas: maks 15 halaman |
| 5 | **monograf** | beda font paling jelas (Cambria 11) |
| 6 | **buku-referensi** | paling berat isinya (indeks + tabel komparasi) |

## 7. Catatan tentang DAFTAR PUSTAKA (temuan 22 Okt 2026)

Template asli hanya punya **4 Heading1**: `KATA PENGANTAR`, `BAB I`, `BAB II`,
`TENTANG PENULIS` — **tidak ada DAFTAR PUSTAKA**.

Generator v2.3 (`f1da9bf`) **menambahkannya**, lengkap dengan asersi
`DP1–DP3` (posisi, minimal 1 entri, indentasi gantung `w:hanging`) dan entri
daftar isi ber-nomor halaman.

**Nilai: benar** (buku tanpa pustaka bukan buku terbit). **Tapi statusnya harus
Bos sahkan** karena melampaui "persis template". Kalau disahkan, tulis di
`SKILL.md` sebagai *"bagian tambahan wajib"* supaya agen berikutnya tidak
bingung kenapa ada bagian yang tidak ada di file template.
