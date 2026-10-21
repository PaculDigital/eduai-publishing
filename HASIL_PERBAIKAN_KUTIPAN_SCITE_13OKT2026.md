<!-- SOT: HASIL_PERBAIKAN_KUTIPAN_SCITE_13OKT2026.md — hasil perbaikan
      kutipan Scite (citation_graph). STATUS: SELESAI, gerbang 29/0. -->

# ✅ PERBAIKAN KUTIPAN SCITE EDUAI — SELESAI 13 Okt 2026

**Status:** kode selesai · gerbang 29/0 BERGIGI · menunggu deploy
**Berkas rencana:** `RENCANA_PERBAIKAN_KUTIPAN_SCITE_13OKT2026.md`
**Backup:** `_arsip/pre-kutipan-citationgraph-20261013-042205/`

---

## 🎯 AKAR (satu kalimat)

`app/pustaka.py` memanggil alat MCP **`search_literature`** — alat itu
**TIDAK mengembalikan medan `citations`** ⇒ kutipan hilang **SENYAP**
(tanpa galat, HTTP 200, log bersih). Satu-satunya alat yang punya kutipan =
**`citation_graph`** + `include_intent=True` + `include_snippets=True`.

## 🔬 BUKTI (terukur, DOI sama `10.1080/00207543.2020.1836418`)

| | `search_literature` (lama) | `citation_graph` (baru) |
|---|---|---|
| medan `citations` | `False` | ada (via `edges`) |
| hasil | **None** | **9 dari 20 edge** ada jenis + isi |

## 📍 BIAK YANG DICABUT (4 titik, 1 akar)

```
app/pustaka.py:754  scite_kutipan()        → citation_graph  ✅
app/pustaka.py:903  scite_kutipan_banyak() → citation_graph  ✅
+ fungsi BARU `_kutipan_dari_edges()` — penerjemah edges→kutipan
  `_kutipan_dari_hit()` DIPERTAHANKAN hanya sebagai pembanding (bukan produksi)
```

## 📐 BENTUK DATA `citation_graph` (terukur)

```
edges[]  = {s, t, d, type:[...], section:[...], snippets:[...]}
papers{} = {'<doi>': {title, year}}
   s = DOI pengutip · t = DOI dikutip
   type & section = LIST (bukan string) · judul TIDAK di edge → dari papers{}
```
PAGAR: edge tanpa `snippets` DAN tanpa `type` **dibuang** — layar tidak
menampilkan baris kosong (aturan Bos). Tidak ada yang layak ⇒ `None`.

## 📊 HASIL SEBELUM vs SESUDAH (pencarian nyata, kunci sama)

| | Sebelum | Sesudah |
|---|---|---|
| Artikel dapat kutipan | **1** dari 10 | **5** dari 12 |
| Kuota | 1 | **1** (tetap) |
| Lama | 20,4 dtk | **18,0 dtk** |
| Artikel no.2 (`10.1504/IJSEM.2019.100944`) | 0 (padahal 75 sitasi) | **5 kutipan nyata** |

## 💰 KUOTA (terukur dari `manage_subscription`)

```
citation_graph 1 seed  = 1 kuota
citation_graph 2 seed  = 1 kuota   ← TIDAK bertambah
citation_graph 3 seed  = 1 kuota
manage_subscription    = 0 kuota (GRATIS, alat ukur resmi)
scite_tallies (angka)  = 0 kuota (endpoint publik, bukan MCP)
```
⇒ SEMUA DOI dikirim SEKALI JALAN = **1 kuota/pencarian** (bukan 10).
   `seeds` dibatasi Scite 10 ⇒ dipecah per 10 kalau artikel > 10.

## 🧪 GERBANG

`_gerbang_kutipan_scite.py` — **29 LULUS / 0 GAGAL**, BERGIGI:
- 8 grup uji (A token · B alat benar · C angka · D kutipan nyata ·
  E banyak-DOI · F pagar · G penerjemah diuji SENDIRI)
- **Uji bergigi TERBUKTI:** sed `citation_graph` → `search_literature`
  ⇒ **5 GAGAL, EXIT 1** ✅ (gerbang yang tak bisa gagal = tidak menjaga)

⚠️ JEBAKAN JEBAKAN di gerbang: `B4` sengaja memeriksa **KODE sumber**
(bukan hanya perilaku) — supaya kalau akar lama bangkit, langsung tertangkap.

## ⚠️ YANG BELUM DIUKUR (jujur)

- Keterangan alat bilang snippet *"OA sources only"*, TAPI terukur 4 dari 4
  DOI **berbayar** tetap dapat snippet ⇒ dugaan "berbayar = kosong"
  **TIDAK terbukti**.
- `max_edges` paling pas (kecepatan vs kelengkapan) — belum disetel optimal
  (dipakai 30/DOI, batas 200).
- Lama `citation_graph` dengan 10 seed — belum diukur terpisah.
