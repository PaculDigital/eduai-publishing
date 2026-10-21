# 💾 CACHE JEV PER DIAGRAM — hemat tanpa merusak

> **Tanggal:** 20 Oktober 2026 · **Oleh:** Wulan
> **Putusan Bos:** pilih **A** — "Tetap 12 panggilan + pasang cache sidik jari"

## ⛔ Yang DIBATALKAN dan kenapa (penting, jangan diulang)

Sebelum ini Wulan mengusulkan **menggabung semua diagram satu bab jadi SATU
panggilan Jev** dengan alasan hemat 26%. **Bos bertanya "atau justru jadi
bencana?" — dan jawabannya: BENCANA.** Sudah diukur, hasilnya:

| Bab | Jawaban sama dengan cara per-diagram |
|---|---|
| Bab 1 | 2 dari 2 ✅ |
| Bab 2 | **0 dari 3** ❌ |
| Bab 3 | **0 dari 3** ❌ |
| Bab 4 | **0 dari 2** ❌ |
| Bab 5 | **0 dari 1** ❌ |
| Bab 6 | **0 dari 1** ❌ |
| **Total** | **2 dari 12** |

**Bukti kerusakan** — dalam satu panggilan, jawaban jadi nyaris identik:

```
per-diagram (BENAR)      gabung per bab (RUSAK)
2.1 → jumlah 3           2.1 → 4,81
2.2 → jumlah 4           2.2 → 4,81
2.3 → jumlah 5           2.3 → 4,88
```

Jev berhenti membedakan satu diagram dengan yang lain. **Sebabnya** sesuai
catatan resmi Jev: pertanyaan Jev berdiri sendiri, satu jawaban bukan konteks
bagi pertanyaan lain. Bahan berbeda dalam satu panggilan = Jev kehilangan jejak.

**Kenapa ini berbahaya:** jawabannya TIDAK error — keluar angka wajar (4,81),
lalu dibulatkan jadi 5, keterangan dipecah 5 label, dan **diagram keluar ngawur
tanpa satu pesan error**. Persis kegagalan "tampak selesai padahal palsu".

## 📌 ATURAN YANG LAHIR DARI TEMUAN INI

> **SATU BAHAN = SATU PANGGILAN.**
> Fan-out banyak pertanyaan dalam satu panggilan hanya aman kalau bahannya
> SAMA (mis. 5 pertanyaan atas satu bab) — BUKAN kalau bahannya berbeda.

## ✅ YANG DIPASANG: cache sidik jari

`tahapan_diagram.py` — hasil Jev disimpan per **sidik sha256(judul + keterangan)**.

| | Ronde 1 (kosong) | Ronde 2 (cache penuh) |
|---|---|---|
| Panggilan Jev | 12 | **0** |
| Waktu | ~6,5 dtk | **0,023 dtk** |
| Hasil | 7 Jev + 5 template | **SAMA PERSIS** |

**Hemat ronde kedua = 100%**, bukan 26% — dan nol risiko karena jawabannya
identik (dibuktikan, bukan diasumsikan).

### Berkas
`_jev_tahapan.json` di samping folder hasil (`FOLDER_HASIL`).
Isi: `{sidik: [jumlah, yakin_jumlah, yakin_urut]}`.

### Pagar yang dipasang
1. **Jev mati (balas None) TIDAK disimpan** — gangguan sesaat tidak membeku
   jadi "template selamanya"
2. **Berkas rusak ⇒ tetap jalan** (tanya Jev lagi, lalu timpa jadi sehat)
3. **Tulis atomik** (`.tmp` lalu `os.replace`) — tidak pernah meninggalkan
   JSON setengah jadi
4. **Judul ATAU keterangan berubah ⇒ panggilan baru** (cache tidak menyajikan
   yang basi)
5. **Gagal menyimpan TIDAK menggagalkan pipeline**

## 🧪 Gerbang

| Gerbang | Hasil |
|---|---|
| `gerbang_cache_jev.py` | **13 lulus / 0 gagal** |
| `gerbang_diagram_jev.py` | 23 / 0 (tidak rusak) |
| `gerbang_gambar_docx.py` | 17 / 0 (tidak rusak) |

**BERGIGI** — cache dilepas (`tersimpan = None`) ⇒ **2 uji GAGAL**:
- `② panggilan kedua TIDAK memanggil Jev` → jadi 1 panggilan
- `⑥ rakit ulang 12 diagram = 0 panggilan` → jadi 12 panggilan

## ⚠️ Pelajaran uji (jangan diulang)
Gerbang cache versi pertama **HIASAN**: Wulan mengganti `_jumlah_tahap` untuk
memalsukan Jev — padahal cache ada DI DALAM fungsi itu, jadi cache tak pernah
diuji. **Obat: palsukan Jev di lapisan paling bawah (`app.jev.tanya`)**, bukan
di fungsi yang sedang diuji.

## Status
- Kode host & folder proyek **identik** (sha256 `c7849a908b4c0b83`)
- **BELUM deploy** — image belum dibangun ulang
