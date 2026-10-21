# DIAGNOSA INFERHUB — 20 Okt 2026 (SUDAH SELESAI, DISIMPAN UNTUK JEJAK)

Enam skrip di folder ini dipakai **sekali** untuk menemukan sebab
"Credits exhausted" pada ilustrasi buku. **JANGAN dijalankan rutin** —
biayanya kena kuota InferHub.

## Hasil akhir (jangan diulang)

| Pertanyaan | Jawaban terukur |
|---|---|
| Kunci aplikasi salah? | **TIDAK** — `INFERHUB_KEY` di `.env` = sama dengan di container |
| Saldo InferHub habis? | **TIDAK** — `$7,57` |
| Yang habis apa? | **Kredit CodeBuddy** (galat 14018) karena model `cb/…` |
| Model gambar hidup | **`gemini-2.5-flash-image`** (TANPA `cb/`) — HTTP 200, 782 KB |
| Model tanpa `cb/` lain | 8 dari 9 nama tebakan **404** |

## Skrip

| Berkas | Gunanya |
|---|---|
| `daftar_model_inferhub.py` | Ambil `GET /v1/models` (403 model), cetak ringkas |
| `saring_model_gambar.py` | Saring model yang punya output **image** |
| `uji_model_gambar_asli.py` | Uji satu per satu model tanpa `cb/` → cari yang HIDUP |
| `diagnosa_inferhub.py` | Bandingkan model teks vs gambar, baca kode galat |
| `diagnosa_kunci_gambar.py` | Bandingkan kunci aplikasi vs kunci notes |
| `cari_model_gambar.py` | Percobaan pertama (nama dikarang) — **8/9 gagal**, jadi bukti bahwa nama model HARUS dibaca dari daftar |

⚠️ **Pelajaran:** `cari_model_gambar.py` adalah cara yang **SALAH** —
mengarang nama model. Yang benar: `daftar_model_inferhub.py` +
`saring_model_gambar.py` dulu, baru uji.

## Kalau nanti gambar gagal lagi

1. Cek `MODEL` — kalau ada prefix `cb/`, itu jalur CodeBuddy.
2. Uji `gemini-2.5-flash-image` langsung (1 panggilan saja, hemat).
3. Kalau 429/14018 ⇒ **kredit CodeBuddy**, bukan InferHub.
4. Kalau 401 ⇒ kunci memang salah.

Rujukan: skill `inferhub-text-to-image` bagian *prefix `cb/`*.
