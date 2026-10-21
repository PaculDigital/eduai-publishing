# 🚨 PETA TEMPAT "MENEBAK" DI EDUAI — HASIL AUDIT (04Okt2026)

**Perintah Bos:** "PILIHAN 2 — audit dulu, jangan koding apa pun."
**Pengakuan:** Wulan TAHU aturan "JANGAN MENEBAK" (Bos, 03Okt26), tapi mesin
deteksi bab EduAi MEMANG menebak, dan Wulan menambal tebakannya berulang
(bukan mencabutnya). Bos benar: "sampai kiamat tidak akan selesai."

**Status berkas ini:** CATATAN AUDIT. Tidak ada kode diubah.

---

## A. MESIN YANG MENEBAK (membaca pola tulis, bukan penanda)

| # | Berkas:baris | Fungsi | Cara menebak |
|---|---|---|---|
| 1 | `app/versi.py:70` | `_POLA_BAB` | regex `^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5})[ \t]*(.*)$` |
| 2 | `app/versi.py:149` | `deteksi_bab()` | iterasi _POLA_BAB + 6 penyaring tebakan |
| 3 | `app/versi.py:256` | `_deteksi_bagian()` | daftar kandidat bagian kedua |
| 4 | `app/versi.py:338` | `ambil_bab()` | ⚠️ kalau tak ketemu → **kembalikan naskah UTUH** (tebak) |
| 5 | `app/state.py:203` | `_POLA_BAB` (KEMBAR) | pola ke-2, terpisah dari versi.py |
| 6 | `app/state.py:266` | `_POLA_SUBBAB` | tebak sub-bab (1.1, 1.2, …) |
| 7 | `app/state.py:416` | `buang_daftar_isi()` | tebak mana daftar isi, mana judul asli |
| 8 | `app/state.py:600` | `deteksi_subbab()` | kategori `bab1`…`bab5` |
| 9 | `app/state.py:664` | `deteksi_bab_besar()` | kategori `bab` ← **INI yang bikin Asih terkunci** |
| 10 | `app/state.py:725` | `petakan()` | gabungan 8+9 |
| 11 | `app/konteks.py:593` | `petakan_paragraf()` | tebak paragraf |

**⇒ 11 mesin menebak, 2 di antaranya POLA KEMBAR (versi.py & state.py)
yang bisa berbeda perilaku. Ini akar: naskah apa pun bisa lolos celah.**

## B. PEMAKAI (yang ikut kena kalau tebakan salah)

| Berkas | Jumlah pemakaian |
|---|---|
| `app/ai.py` | 33 |
| `app/versi.py` | 20 |
| `app/belajar.py` | 16 |
| `app/state.py` | 10 |
| `app/peta_halus.py` | 8 |
| `app/catatan_ai.py` | 6 |
| `app/konteks.py` | 6 |
| `app/tulis_docx.py` | 2 |

**⇒ 101 titik pemakaian. Satu tebakan salah → menular ke SEMUA fitur.**

## C. PRODUSEN DATA (yang MENULIS ke `section_state`)

| Berkas:baris | Menulis kategori |
|---|---|
| `app/catatan_ai.py:301` | `SectionState(...)` ← satu-satunya penulis |
| `app/catatan_ai.py:193` | `kategori = str(b.get('kategori') or 'bab')` |
| `app/state.py:718` | `deteksi_bab_besar()` → `'bab'` |
| `app/state.py:656` | `deteksi_subbab()` → `get_category_for(nomor)` → `'babN'` |

**⇒ SATU kolom (`section_state.kategori`) diisi DUA mesin berbeda
dengan DUA format berbeda (`'bab'` vs `'bab1'`). Konsumen
(`app/belajar.py`) hanya kenal SATU format ⇒ cacat nyata produksi.**

## D. AKAR TUNGGAL

```
Naskah (.docx)
      │
      ▼
[11 mesin MENEBAK pola tulis]  ← tidak ada penanda tetap, tidak ada konfirmasi
      │
      ▼
kategori 'bab' ATAU 'bab1'  ← DUA format, tak sepakat
      │
      ▼
101 titik pemakaian → Belajar/catatan/peta/harga
```

**Kesimpulan: selama "bab" DITEBАК dari bentuk tulisan, tiap naskah baru =
celah baru. Tidak ada jumlah tambalan yang cukup. Akar harus dicabut:
bab ditetapkan SEKALI per naskah (dikonfirmasi manusia), lalu semua fitur
membacanya — TIDAK ada yang menebak ulang.**

---

## E. YANG BELUM WULAN SELESAIKAN (jujur)

- Bagan di atas baru dari grep + baca 6 berkas. **BELUM diperiksa:**
  `app/konteks.py` penuh, `app/peta_halus.py` penuh, `app/alur_awal.py:255`
  (`deteksi_isi`), `app/jenis.py:372` (`deteksi`), `app/gambar.py:435`.
- **BELUM ada daftar "mana yang dipakai fitur mana" per baris.**
- **BELUM ada usul perbaikan** — sesuai perintah Bos: audit dulu.
