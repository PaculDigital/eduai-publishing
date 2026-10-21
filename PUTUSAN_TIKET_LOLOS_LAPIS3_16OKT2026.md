# 🔖 TIKET LOLOS — LAPIS 3 (Tanda Khusus per-Elemen)

<!-- SOT: tiket lolos Lapis 3 · 16 Okt 2026 · acuan tunggal untuk:
     (a) jawaban "sudah bayar lalu edit manual → lolos?";
     (b) sidik 1.500 huruf bab; (c) biaya Jev gratis;
     (d) tampilan ☑ Done. Jangan salin isinya ke dokumen lain — TUNJUK ke sini. -->

**Status: ✅ LIVE** — image `eduai-app:20261016_021214-sot`.

**Putusan Bos 16 Okt 2026 — TERKUNCI.**

## Masalah yang dijawab

> *"Tanya apa yang terjadi jika user sudah bayar dan sudah mendapatkan
> kebutuhannya di bab itu, kemudian user juga melakukan edit manual di
> hal lain di bab itu atau menambahkan kalimat yang sesuai tapi tidak
> merubah makna. Apa yang akan terjadi lolos atau tidak?"*
> — Bos, 16 Okt 2026

## Jawaban: **LOLOS** — karena dinilai MAKNA, bukan huruf

Sidik teks mentah (usul Wulan awal) **DITOLAK** karena tidak bisa membedakan:

| Kejadian | Makna berubah? | Sidik teks |
|---|---|---|
| tambah kalimat pendukung | ❌ tidak | dianggap **berubah** (salah) |
| perbaiki ejaan | ❌ tidak | dianggap **berubah** (salah) |
| ganti angka temuan | ✅ berubah | berubah (benar) |

⇒ Kalau pakai sidik teks, user yang **hanya menyempurnakan** akan diminta
bayar lagi = **TIDAK ADIL** & melanggar prinsip Bos *"tidak kerja bolak-balik"*.

## Putusan: **JEV MENILAI MAKNA** (pilihan A)

Saat user klik konversi ulang, Jev ditanya **1 pertanyaan choice**:

```
Bahan : BAB I versi lama (<1500 huruf>)  ═══  BAB I versi baru (<1500 huruf>)
Tanya : "Apakah bab ini masih membahas hal yang sama?"
        choice = { sama: "membahas hal yang sama",
                   beda: "sudah BERBEDA / fokus bergeser" }
```

| Jawaban Jev | Akibat |
|---|---|
| `sama` | tiket **TETAP** → elemen itu **Done** (tidak ditanya lagi) ✅ |
| `beda` / ragu / **Jev mati** | tiket **BATAL** → elemen ditanyakan kembali |

⚠️ **PRINSIP AMAN:** Jev mati/ragu ⇒ tiket **BATAL** (jangan biarkan lolos
tanpa pemeriksaan). Kegagalan teknis TIDAK boleh jadi pintu gratis.

## Putusan Bos (2 hal)

1. **Biaya Jev = GRATIS** (ditanggung EduAi) — user tidak rugi karena hanya
   memverifikasi. Pilihan **A**.
2. **Sidik = 1.500 huruf awal bab.** Pilihan **OK**.

## Peta 4 sambungan (NOL mesin baru · NOL tabel baru · NOL dompet baru)

| # | Sambungan | Berkas | Fungsi SUDAH ADA yang dipakai |
|---|---|---|---|
| 3a | Tulis tiket saat revisi sukses | `konversi.py` `catat_revisi()` (~2113) | wadah `KonversiNaskah.hasil_json` |
| 3b | Jev tanya makna | `konversi.py` fungsi baru kecil | `jev.tanya()` (jev.py:186) + `type='choice'` |
| 3c | Baca tiket sebelum konversi | `konversi.py` `periksa_sebelum_konversi()` (1689) | tanda dibaca → elemen Done dilewati |
| 3d | Layar: elemen Done | `artikel_konversi.html` | label Done/UnDone (putusan lama) |

## Bentuk tiket di `hasil_json`

```json
{
  "revisi": [ ... ],
  "artikel": { ... },
  "tiket": {
    "gap": {"bab": "1", "sidik": "<1500 huruf awal BAB I>",
            "waktu": "2026-10-16T01:20:00"}
  }
}
```

## ⚠️ Jejak sidik BAB

- 1.500 huruf awal bab tempat elemen tinggal (putusan §N no.7: *"Gap tinggal
  di BAB I ⇒ sidik = teks BAB I"*).
- Dipakai **hanya** sebagai bahan Jev (bukan pembanding hash) — supaya
  penambahan kalimat tidak otomatis membatalkan.

## Langkah koding

1. [ ] `tiket_baca()` + `tiket_tulis()` di `konversi.py` (murni, mudah diuji)
2. [ ] `tiket_periksa(db, u, fid, artikel, kurang)` — panggil Jev per elemen
       bertiket; `sama` → buang dari `kurang[]`
3. [ ] Sambung di `periksa_sebelum_konversi()` (setelah `periksa_mutu`)
4. [ ] Layar `artikel_konversi.html` — tampilkan elemen btiket sebagai **Done**
5. [ ] Gerbang bergigi + uji keadaan (sama / beda / Jev mati / bab tak berubah)
6. [ ] Deploy (`bash jalankan.sh`) setelah izin
