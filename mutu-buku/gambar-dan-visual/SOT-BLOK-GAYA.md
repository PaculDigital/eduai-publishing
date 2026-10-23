# 📌 SOT — BLOK GAYA ILUSTRASI BUKU

> **SINGLE SOURCE OF TRUTH.** Satu berkas ini yang benar.
> Diukur 22 Oktober 2026 dari kode hidup. Kalau ragu, baca ini — bukan berkas lain.

---

## 1. JAWABAN LANGSUNG — yang benar yang mana?

> ### ✅ YANG BENAR: `jenis_buku.py` → `PAKET[jenis]["ilustrasi"]`

**Alasannya bukan selera. Ini kode yang menentukan:**

```python
# brief_visual.py baris 692-696
if jenis is not None:
    import jenis_buku as JB
    pkg  = JB.paket(jenis)
    gaya = pkg["gaya_gambar"]
    blok = pkg["ilustrasi"] or STYLE_BUKU.get(gaya) or STYLE_BUKU[GAYA_DEFAULT]
    #      └──────────────┘
    #      INI MENANG. Titik.
```

`pkg["ilustrasi"]` **didahulukan**. `STYLE_BUKU` hanya dipakai kalau
`pkg["ilustrasi"]` kosong (`None`).

---

## 2. Siapa menang untuk tiap jenis — TERUKUR

| Jenis buku | Blok yang DIPAKAI | Panjang | Asal |
|---|---|---|---|
| **umum** | `premium-konseptual` | **597 char** | `brief_visual.STYLE_BUKU` |
| **anak** | PAKET anak | **571 char** | ✅ `jenis_buku.PAKET` |
| **pendidikan** | PAKET pendidikan | **536 char** | ✅ `jenis_buku.PAKET` |

Artinya: `PAKET["umum"]["ilustrasi"] = None` → jatuh ke `STYLE_BUKU`.
Untuk **anak & pendidikan**, `jenis_buku` **selalu menang**.

---

## 3. 🗑️ YANG HARUS DIBUANG

### `STYLE_BUKU['anak']` — 518 karakter — **MATI, TIDAK TERPAKAI**

| Bukti | Hasil |
|---|---|
| Dipakai `pkg["ilustrasi"]` untuk jenis anak? | ❌ **TIDAK** — `PAKET['anak']['ilustrasi']` **ADA** (571 char) |
| Jadi `STYLE_BUKU['anak']` pernah dieksekusi? | ❌ **TIDAK PERNAH** |
| Isinya sama dengan yang dipakai? | ❌ **BEDA** |

### Beda isinya — penyebab kebingungan

| Kalimat | `jenis_buku` (DIPAKAI) | `STYLE_BUKU` (MATI) |
|---|---|---|
| Gaya dasar | `clean flat cartoon style` | `clean flat cartoon style with clear dark outlines around every shape` |
| Outlines | ✅ kalimat **sendiri** | ✅ **menyatu** di kalimat gaya |
| Panjang | **571 char** | **518 char** |

**Inilah sumber "kok jadi beda-beda"** — dua salinan, dan yang mati lebih pendek.

---

## 4. YANG DIPERTAHANKAN — jangan dihapus

| Berkas | Bagian | Status | Alasan |
|---|---|---|---|
| `jenis_buku.py` | `PAKET['anak']['ilustrasi']` | ✅ **HIDUP** | ini yang dipakai |
| `jenis_buku.py` | `PAKET['pendidikan']['ilustrasi']` | ✅ **HIDUP** | ini yang dipakai |
| `jenis_buku.py` | `PAKET['umum']['ilustrasi'] = None` | ✅ **BENAR** | sengaja kosong → jatuh ke STYLE_BUKU |
| `brief_visual.py` | `STYLE_BUKU['premium-konseptual']` | ✅ **HIDUP** | dipakai buku umum |
| `brief_visual.py` | `STYLE_BUKU['editorial-lineart']` | ✅ **HIDUP** | pilihan gaya lain |
| `brief_visual.py` | `STYLE_BUKU['woodcut']` | ✅ **HIDUP** | pilihan gaya lain |
| `brief_visual.py` | `STYLE_BUKU['flat-editorial']` | ✅ **HIDUP** | pilihan gaya lain |
| `brief_visual.py` | `STYLE_BUKU['anak']` | 🗑️ **MATI** | **BUANG** |

> ⚠️ **4 gaya lain JANGAN dibuang.** `editorial-lineart`, `woodcut`,
> `flat-editorial` masih bisa dipilih lewat `gaya_gambar` untuk buku umum.

---

## 5. RENCANA PEMBERSIHAN — SUDAH DIKERJAKAN 22 Okt 2026 ✅

| # | Langkah | Status |
|---|---|---|
| **1** | Hapus `STYLE_BUKU['anak']` dari `brief_visual.py` (101–114) | ✅ **SELESAI** |
| **2** | Pastikan penghapusan tidak memicu error | ✅ `pkg["ilustrasi"]` anak = 571 char, aman |
| **3** | Uji bergigi + jalankan gerbang | ✅ **2/2 BERGIGI**, gerbang 19/0 |

### Bukti sebelum vs sesudah

| Jenis | Sebelum | Sesudah | Berubah? |
|---|---|---|---|
| umum | 597 char | **597 char** | ❌ tidak |
| anak | 571 char | **571 char** | ❌ tidak |
| pendidikan | 536 char | **536 char** | ❌ tidak |

**Nol perubahan perilaku.** Yang dihapus memang **tidak pernah dieksekusi**.

### Gerbang: 20 → 19 asersi (bukan melemah)

1 asersi hilang karena `STYLE_BUKU['anak']` **memang sudah tidak ada**.
Gerbang memeriksa **per isi dict**, jadi jumlahnya ikut turun.

**Dibuktikan masih bergigi 2/2:**

| Suntikan | Hasil |
|---|---|
| `STYLE_BUKU['flat-editorial']` tanpa `{brief}` | ✅ EXIT=1, 18 lulus / **1 gagal** |
| `PAKET['anak']['ilustrasi']` tanpa `{brief}` | ✅ EXIT=1, 17 lulus / **2 gagal** |
| Semua dipulihkan (kontrol) | ✅ EXIT=0 |

> ⚠️ **JEBAKAN UJI BERGIGI (Wulan salah 2× di hari yang sama):**
> (a) 20 Okt — rusak di memori **kalah** oleh `sys.modules`;
> (b) 22 Okt — rusak di memori **kalah** karena gerbang dijalankan **subprocess**
> (proses baru impor ulang). **Obat: suntik ke BERKAS ASLI**, jalankan, pulihkan.

### ⚠️ Yang HARUS diperiksa sebelum hapus

| Cek | Perintah | Harus |
|---|---|---|
| Tidak ada pemanggil langsung | `grep -rn "STYLE_BUKU\['anak'\]"` | kosong |
| `pkg['anak']['ilustrasi']` tidak kosong | sudah diukur | **571 char** ✅ |
| `GAYA_DEFAULT` bukan `'anak'` | `GAYA_DEFAULT = "premium-konseptual"` | ✅ bukan anak |

---

## 6. Pagar yang sudah ada — jangan dilemahkan

| Pagar | Asersi | Yang dijaga |
|---|---|---|
| `gerbang_placeholder_brief.py` | **20** | setiap blok gaya WAJIB punya `{brief}` |

Kedua salinan (`jenis_buku` dan `STYLE_BUKU`) **sama-sama punya `{brief}`** ✅
Jadi membuang salah satu **tidak** mematikan pagar ini.

---

## 7. Aturan tetap setelah dibersihkan

| # | Aturan |
|---|---|
| 1 | **Blok gaya HANYA ditulis di SATU tempat:** `jenis_buku.PAKET[jenis]["ilustrasi"]` |
| 2 | `brief_visual.STYLE_BUKU` hanya untuk gaya **tanpa paket** (umum) |
| 3 | Setiap blok gaya **WAJIB** punya `{brief}` |
| 4 | Kalau menambah jenis buku baru → tulis `ilustrasi` di `jenis_buku`, **bukan** di `STYLE_BUKU` |
| 5 | Jangan pernah menyalin blok gaya antar berkas |

---

## 8. Ringkas satu kalimat

> **Yang benar: `jenis_buku.py` → `PAKET[jenis]["ilustrasi"]`.
> Yang harus dibuang: `STYLE_BUKU['anak']` di `brief_visual.py` (518 char, mati).
> Yang jangan disentuh: 4 gaya lain di `STYLE_BUKU` + `PAKET['umum']['ilustrasi']=None`.**

---

*SOT dibuat Wulan 22 Oktober 2026. Angka dari kode hidup, bukan ingatan.*
