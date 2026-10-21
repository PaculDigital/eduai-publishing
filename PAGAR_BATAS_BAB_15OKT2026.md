<!-- SOT: PAGAR_BATAS_BAB_15OKT2026 -->
# 🔢 BUG BATAS BAB — DISERTASI 7 BAB MATI (diperbaiki 15 Okt 2026)

> **Status:** ✅ TAYANG PRODUKSI · image `eduai-app:20261015_002535-sot`
> **Mundur:** `eduai-app:cadangan-pra-sot`
> **Gerbang:** `app/_gerbang_batas_bab.py` — **55 LULUS / 0 GAGAL** (BERGIGI)

---

## 🔴 BUG NYATA (bukan teori — ada bukti)

**Berkas:** `app/belajar.py`

| Baris | Kode lama | Akibat |
|---|---|---|
| `_angka_romawi()` | `{1:'I',...,5:'V'}.get(n, str(n))` | bab **6+** → keluar **angka** (`'6'`) bukan `'VI'` |
| `_nomor_bab_dari_section()` | `n if 1 <= n <= 9 else None` | `'BAB X'` → **DITOLAK SENYAP** |
| `_romawi_ke_angka()` | `total if 1 <= total <= 9 else None` | idem |

### Rantai kerusakannya

```
Disertasi 7 bab
   ↓
_label_bab(6) → f'BAB {_angka_romawi(6)}' → 'BAB 6'   ❌ SALAH
   ↓
naskah TIDAK punya 'BAB 6' — dia punya 'BAB VI'
   ↓
label TIDAK KETEMU → Mode Belajar bab 6-8 MATI
```

### BUKTI NYATA dari peta Jev produksi

```
fid=112 bab: [..., 'BAB III', 'BAB VI']   ← naskah SUNGGUHAN punya BAB VI
fid=81  bab: ['BAB I','BAB II','BAB III','BAB IV','BAB V']
```

⇒ Kalau ada naskah 7 bab, bug ini **pasti** menggigit. Sekarang Bos belum
punya user disertasi, jadi **belum kelihatan** — tapi **rusak**.

---

## ✅ PERBAIKAN

**Satu konstanta, satu sumber:**

```python
BATAS_BAB = 20
```

Dipakai di **3 tempat** (semua di `app/belajar.py`):
1. `_angka_romawi(n)` — sekarang pakai tabel `('I'..'XX')`, **bukan** `dict 1-5`
2. `_nomor_bab_dari_section()` — `1 <= n <= BATAS_BAB` (dulu 9)
3. `_romawi_ke_angka()` — `1 <= total <= BATAS_BAB` (dulu 9)

**Kenapa 20:** jenjang tertinggi (disertasi) praktis 6-8 bab; 20 = lega, dan
**sama** dengan jangkauan `parser.py`. **JANGAN** dipatok lebih kecil lagi.

---

## 📊 HASIL UJI

| Uji | Hasil |
|---|---|
| `_angka_romawi(6)` | `'VI'` ✅ (dulu `'6'` ❌) |
| `_angka_romawi(7)` | `'VII'` ✅ |
| `_angka_romawi(20)` | `'XX'` ✅ |
| `_nomor_bab_dari_section('BAB X')` | `10` ✅ (dulu `None` ❌) |
| `_label_bab(6)` | `'BAB VI'` ✅ |
| Naskah nyata fid=112 | `BAB VI` **ketemu** ✅ |
| Salah tulis `'ZZ'` | ditolak (jujur, tidak menebak) ✅ |
| **GIGI:** kembalikan batas 5 | asersi **HARUS GAGAL** ✅ terbukti |

**Gerbang:** 55 LULUS / 0 GAGAL
**Regresi:** `_gerbang_rapi_bab` 32/0 · `_gerbang_pagar_mutu_peta` 15/0
**`sot.py`:** 0 masalah · **`periksa_kode.sh`:** LULUS

---

## ⚠️ CATATAN JUJUR — yang BELUM dikerjakan

Ada **6 penulis romawi** di app (bukan 1):

| Berkas | Arah | Batas | Bentuk |
|---|---|---|---|
| `belajar.py` | romawi↔angka | **20** (diperbaiki) | fungsi |
| `versi.py` | romawi→angka | **TAK TERBATAS** ✅ | algoritma |
| `kelompok_catatan.py` | romawi→angka | 15 | peta |
| `parser.py` | romawi→angka | 20 | peta |
| `peta_halus.py` | romawi→angka | 10 | peta |
| `konteks.py` | **angka→romawi** (kebalikan) | 8 | peta |

**Terukur (15 Okt):** arah romawi→angka **SEPAKAT** untuk I–X.
Yang beda hanya **jangkauan**. **Belum disatukan** (putusan Bos: kerjakan
yang perlu saja — bug nyata dulu).

**Risiko yang masih ada:** kalau salah satu peta diubah tanpa yang lain,
mereka bisa berpisah. Belum ada gerbang penjaga kesepakatan.

---

## 📋 JEJAK KEPUTUSAN

- **Bos pilih A** (15 Okt): "Perbaiki bug dulu (batas 5 → tak terbatas)",
  **bukan** B (samakan semua 6 penulis) — karena B lebih besar & belum perlu.
- C (bikin gerbang dulu) dikerjakan **bareng** A, bukan terpisah.
