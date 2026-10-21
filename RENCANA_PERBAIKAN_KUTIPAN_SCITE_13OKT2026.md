<!-- SOT: RENCANA_PERBAIKAN_KUTIPAN_SCITE_13OKT2026.md — rencana perbaikan
      kutipan Scite. STATUS: SELESAI (sudah dikerjakan 13 Okt 2026). -->

# 📋 RENCANA PERBAIKAN — KUTIPAN SCITE EDUAI
**Tanggal:** 13 Okt 2026 · **Status:** MENUNGGU PERSETUJUAN BOS (belum ada kode disentuh)
**Sesi asal:** 20261013 (baca FLAG_OBROLAN.md → temuan kutipan kosong)

---

## 1️⃣ AKAR (satu kalimat)

`app/pustaka.py` memanggil alat MCP **`search_literature`** — alat itu **TIDAK
mengembalikan medan `citations` sama sekali**, sehingga `_kutipan_dari_hit()`
selalu menerima `None` ⇒ kutipan hilang **senyap** (tanpa galat, HTTP 200).

## 2️⃣ BUKTI UKUR (13 Okt 2026, di container eduai-app)

DOI sama `10.1080/00207543.2020.1836418`, dua alat berbeda:

| | `search_literature` (KODE SEKARANG) | `citation_graph` (BENAR) |
|---|---|---|
| medan `citations` | `False` (tak ada) | ada (via `edges`) |
| hasil `_kutipan_dari_hit` | **None** | **9 dari 20 edge** ada jenis+isi |
| isi nyata | — | "Various scholars have researched pricing (…) " |

Di pencarian nyata (`cari_semua()` kata kunci "pengaruh kualitas produk
terhadap keputusan pembelian"): **1 dari 10 artikel dapat kutipan**, padahal
`scite_tallies` menunjukkan artikel no.2 punya **75 sitasi**.

## 3️⃣ LOKASI BIAK (4 tempat, 1 akar)

```
app/pustaka.py:754   scite_kutipan()          → search_literature   ❌
app/pustaka.py:761   (ulang saat token basi)  → search_literature   ❌
app/pustaka.py:903   scite_kutipan_banyak()   → search_literature   ❌
app/pustaka.py:910   (ulang saat token basi)  → search_literature   ❌
```

## 4️⃣ PERBEDAAN BENTUK DATA (wajib dijembatani)

**LAMA** — `search_literature` → `hits[].citations[]`:
```
citations[] = {sourceDoi, targetDoi, section, type}   ← 4 medan, TANPA judul
```

**BARU** — `citation_graph` → `edges[]` + `papers{}`:
```
edges[]  = { s, t, d, type:[...], section:[...], snippets:[...] }
papers{} = { "<doi>": {title, year} }
   s = DOI pengutip (pengganti sourceDoi)
   t = DOI yang dikutip (pengganti targetDoi)
   type     = LIST (contoh ['mentioning']) — bukan string
   section  = LIST — bukan string
   snippets = LIST teks nyata (TIDAK semua edge punya)
```
⇒ **`_kutipan_dari_hit()` harus diganti** jadi penerjemah `edges` → kutipan.
   Judul diambil dari `papers[s]["title"]` (bukan dari edge).

## 5️⃣ RANCANGAN (nol mesin baru, nol alur baru)

1. **Fungsi BARU** `_kutipan_dari_edges(graf, doi_seed, maks)` — penerjemah
   tunggal `citation_graph` → list kutipan (bentuk SAMA seperti sekarang:
   `{doi, doi_sumber, judul, jenis, bagian, kutipan, tahun}`) supaya
   `referensi.html` **tidak perlu diubah**.
2. **`scite_kutipan_banyak()`** → panggil `citation_graph` sekali untuk SEMUA
   DOI (`seeds` maks 10 ⇒ dipecah per 10 kalau artikel > 10).
3. **`scite_kutipan()`** (1 DOI) → pakai jalur yang sama (satu pintu, jangan 2 aturan).
4. **`max_edges`** disetel berdasar jumlah seed (mis. 30/seed) supaya tidak
   terpotong, tapi tidak menggelembung.
5. **PAGAR (aturan Bos):** edge **tanpa** `snippets` **DAN** tanpa `type`
   ⇒ JANGAN ditampilkan (jangan munculkan baris kosong). Kalau kutipan
   benar-benar tidak ada ⇒ `None` ⇒ layar **tidak menampilkan apa pun**.
6. **Token basi (401)** ⇒ segarkan sekali, seperti pola yang sudah ada.

## 6️⃣ KUOTA (terukur dari `manage_subscription`, 13 Okt 2026)

```
1 panggilan citation_graph (1 seed)  = 1 kuota
1 panggilan citation_graph (2 seed)  = 1 kuota   ← TIDAK bertambah
1 panggilan search_literature        = 1 kuota
manage_subscription                  = 0 kuota (GRATIS)
```
⇒ Gabung semua DOI jadi SATU panggilan = **1 kuota/pencarian** (bukan 10).
    `scite_tallies` (angka didukung/dibantah) tetap **GRATIS** lewat endpoint publik.
    Sisa kuota saat rencana ditulis: **161** (terpakai 89/250, reset 19 Okt 2026).

## 7️⃣ YANG HARUS DIUJI (gerbang BERGIGI)

| # | Uji | Harus |
|---|---|---|
| 1 | `_kutipan_dari_edges` pada balasan nyata | ≥1 kutipan, bentuk lengkap |
| 2 | `scite_kutipan_banyak` 2 DOI | kedua DOI dapat hasil (atau None jujur) |
| 3 | DOI tanpa data | `None` — bukan crash, bukan palsu |
| 4 | Edge tanpa snippet | TIDAK muncul di hasil |
| 5 | Token dikosongkan | `None` (pagar) |
| 6 | **Suntik kerusakan**: balikkan ke `search_literature` | gerbang **HARUS GAGAL** |
| 7 | Kuota sebelum/sesudah 1 pencarian | naik **1** (bukan lebih) |

Gerbang lama `_gerbang_kutipan_scite.py` **wajib diperbarui** (sekarang masih
menguji `search_literature` sebagai sumber — itu sudah salah arah).

## 8️⃣ YANG BELUM DIUKUR / TERBUKA (jujur)

- `snippets` keterangan alat: *"OA sources only"* — **belum dipastikan** apakah
  artikel berbayar selalu kosong. Terukur: 4 dari 4 DOI berbayar **tetap dapat**
  snippet ⇒ dugaan "berbayar = kosong" **TIDAK terbukti**.
- Berapa `max_edges` paling pas (kecepatan vs kelengkapan) — **belum diukur**.
- Lama panggilan `citation_graph` dengan 10 seed — **belum diukur**.

## 9️⃣ CADANGAN (kalau Bos mau lebih sederhana)

Tampilkan **angka sitasi saja** (`scite_tallies`, gratis, selalu jalan) dan
**buang** janji "daftar kutipan" dari layar. Sederhana & jujur — tapi kehilangan
indikator "didukung/dibantah" yang Bos minta (banyak indikator biar user mudah pilih).

---

**KEPUTUSAN YANG DIMINTA DARI BOS:**
- (a) Setujui rencana ini (bagian 5 + 7) → Wulan koding
- (b) Ubah dulu (bagian mana)
- (c) Pilih cadangan bagian 9
