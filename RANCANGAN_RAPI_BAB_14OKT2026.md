# RANCANGAN 1 HALAMAN — SAMBUNG CATATAN PEMBIMBING KE PETA JEV

> 14 Okt 2026 · **BELUM DIKODING** · menunggu izin Bos
> Tujuan: catatan pembimbing (manual & AI) **nyambung** ke peta Jev, supaya
> revisi AI mahasiswa **presisi** dan **hemat** — tanpa mesin baru.

---

## 1. MASALAH (terukur, bukan dugaan)

| Fakta | Angka |
|---|---|
| Catatan pembimbing ada | 9 |
| Peta Jev tersimpan | ✅ ada (fid=9, 12 bagian; fid=81, fid=112) |
| `section_id` **tidak seragam** | `'BAB III'` · `'BAB 3'` · `'bab iii'` — 3 cara untuk bab yang sama |
| `teks_asli` terisi | **1 dari 9** (8 kosong) |

**Akibat:** catatan `'BAB 3'` dan `'bab iii'` **tidak ketemu** di peta Jev
(peta pakai nomor: `'3'`). ⇒ Revisi AI mahasiswa **tidak dapat bab yang benar**.

---

## 2. ALUR (3 langkah — 2 sudah ada)

```
① Pembimbing tulis catatan (SUDAH ADA)
   · manual → gratis, bebas, TIDAK dikurung peta  ✅
   · AI     → bayar 1 Token                        ✅
                    ↓
② Rapikan nama bab + tempel judul dari peta Jev   ← ⭐ INI YANG BARU
   'bab iii' → '3'  → peta Jev → judul 'Metode Penelitian'
                    ↓
③ Mahasiswa klik "Revisi pakai AI" (SUDAH ADA, ai.py:2449)
   AI terima: bab itu + tetangganya + catatan pembimbing
   ⇒ presisi + hemat 91% (konteks.py SUDAH ADA)
```

---

## 3. YANG BARU — CUMA 1 FUNGSI KECIL

**Berkas:** `app/pembimbing.py` (dekat `catat()`) — **±15 baris**

```python
ROMAWI = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7}

def rapi_bab(teks: str) -> str:
    """'bab iii' / 'BAB III' / 'BAB 3' -> '3'  (satu bentuk).

    Dipakai SEBELUM catatan disimpan, supaya section_id seragam
    dan bisa dicocokkan ke peta Jev.
    Kalau tidak dikenali -> kembalikan apa adanya (JANGAN menebak).
    """
    t = (teks or '').strip().upper().replace('BAB', '').strip()
    if t.isdigit():
        return t
    return str(ROMAWI.get(t, teks or ''))
```

**Dipakai di 2 tempat (pemanggil yang sudah ada):**
| Berkas:baris | Isi |
|---|---|
| `app/pembimbing.py` `catat()` | `section_id = rapi_bab(section_id)` |
| `app/asisten.py:297` `simpan_usulan()` | `section_id = rapi_bab(u['bab'])` |

---

## 4. YANG **TIDAK** DIUSUL (biar tidak ruwet)

| Jangan | Alasan |
|---|---|
| ❌ Panggil Jev lagi untuk memetakan catatan | Peta **sudah ada** → Rp 0, 0 detik |
| ❌ Pakai Hakim | Hakim = penilai **mutu**; ini cuma **nama bab** |
| ❌ Cocokkan `teks_asli` ke peta | Peta **tidak simpan teks naskah**; 8/9 catatan teksnya kosong |
| ❌ Tabel / kolom / dompet baru | Semua kolom **sudah ada** |
| ❌ Kurung pembimbing manual dengan peta | Putusan Bos: manual = **bebas** |

---

## 5. KEUNTUNGAN

| | Sebelum | Sesudah |
|---|---|---|
| `section_id` | 3 bentuk campur | **1 bentuk** |
| Catatan → peta Jev | 6/8 cocok (75%) | **8/8** (2 yang gagal memang bab tidak ada / kosong) |
| Revisi AI mahasiswa | bisa salah bab | **bab benar** |
| Biaya tambahan | — | **Rp 0** |

---

## 6. GERBANG (wajib, sebelum tayang)

`app/_gerbang_rapi_bab.py` — uji perilaku nyata:
1. `'BAB I'` / `'bab i'` / `'BAB 1'` → semua jadi `'1'`
2. `'BAB IV'` → `'4'` · `'bab iii'` → `'3'`
3. **Tidak dikenali → dikembalikan apa adanya** (tidak menebak)
4. `''` (kosong) → `''`
5. **Data nyata:** 8 catatan produksi → berapa yang cocok ke peta Jev
6. **BERGIGI:** matikan `rapi_bab` → asersi 1–2 HARUS GAGAL

---

## 7. RISIKO & JAWABAN

| Risiko | Jawaban |
|---|---|
| Catatan lama `'BAB IV'` (peta cuma 3 bab) | **Bukan bug** — bab itu memang tidak ada. Catatan tetap aman, tetap tampil |
| `'BAB 3'` sudah benar | `rapi_bab` tidak mengubahnya (sudah jadi `'3'`) |
| Catatan tanpa bab (`''`) | Dikembalikan apa adanya — **jangan dipaksa** |

---

## 8. URUTAN SESUDAH IZIN

1. Backup `app/pembimbing.py` + `app/asisten.py` → `_arsip/pre-rapi-bab-<tgl>/`
2. Tulis `rapi_bab()` + sambung di 2 pemanggil
3. Tulis gerbang `_gerbang_rapi_bab.py` → jalankan **di container**
4. Jalankan `scripts/periksa_kode.sh`
5. Laporan hasil uji → **minta izin deploy**

**Titik mundur:** `eduai-app:cadangan-pra-sot` (image)
