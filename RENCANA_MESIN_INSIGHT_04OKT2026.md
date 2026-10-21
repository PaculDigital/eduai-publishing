# 🎓 MODE BELAJAR — LANGKAH 2: MESIN MINI INSIGHT (rencana kerja)

## APA YANG SUDAH ADA (jangan dibangun ulang!)

| Komponen | Berkas | Status |
|---|---|---|
| Halaman + pita tab + kartu | `app/belajar.py`, `templates/belajar.html` | ✅ LIVE |
| Tabel penyimpanan | `belajar_naskah` (`insight_json`, `soal_json`, `bab_selesai`) | ✅ ADA, 0 baris |
| Sumber data bab | `section_state` (`kategori`='bab1'..'bab5', `isi_teks`) | ✅ 15 baris |
| Mesin deteksi bab | `app/versi.py::deteksi_bab` | ✅ DIPERBAIKI |
| Jalur panggil LLM (satu pintu) | `app/ai.py::_panggil_9router` + `app/proses.py` (antrean) | ✅ ADA |
| Deteksi bab dari teks | `app/versi.py` | ✅ |

**⇒ Yang perlu DIBANGUN cuma: fungsi "bikin insight" yang mengisi
`belajar_naskah.insight_json` — memakai bahan yang sudah ada.**

## PRINSIP HEMAT TOKEN (§4.8, wajib)

```text
1. SUMBER = section_state.isi_teks (bab SUDAH direvisi) — JANGAN baca ulang .docx
2. HITUNG PER TAHAP: bab selesai → hitung bab itu saja (mini, ~2.000 token)
3. SIMPAN PERMANEN di belajar_naskah.insight_json → buka lagi = 0 token
4. MODEL RINGAN untuk mini insight (output pendek)
5. TIDAK ADA on/off (on/off = hitung ulang = boros)
```

## RANCANGAN TEKNIS

```text
app/belajar.py (TAMBAH, tidak bikin berkas baru):
  ├─ _bahan_bab(db, fid, n: int) -> str
  │     Ambil isi bab n dari section_state (kategori='babN').
  │     ⚠️ Pakai fungsi yang SUDAH ADA; jangan bikin pembaca .docx kedua.
  ├─ async hitung_insight(db, u, bn: BelajarNaskah, n: int) -> dict
  │     Panggil LLM lewat _panggil_9router (SATU PINTU).
  │     Prompt: minta 3-5 butir insight + kutipan sumber (guardrail §4.8).
  │     Simpan ke bn.insight_json (JSON per bab).
  ├─ baca_insight(bn, n) -> list   (dari DB, 0 token)
  └─ TAHAP_INSIGHT = peta nomor bab → kunci JSON

Rute baru (main.py):
  POST /belajar/insight   → hitung insight bab (1 bab per klik)
  (butuh pagar: user login + naskah sudah diaktifkan + bab sudah direvisi)
```

## PAGAR WAJIB (jangan sampai bisa disalahgunakan)

```text
1. Harus login.
2. Naskah itu harus SUDAH DIAKTIFKAN oleh user.
3. Bab yang dihitung harus SUDAH DIREVISI (section_state ada).
4. Bab yang sama → kalau insight sudah ada di DB → pakai yang tersimpan (0 token).
5. WAJIB uji: klik 2× bab yang sama → panggilan LLM hanya 1× (bukti hemat).
```

## URUTAN KERJA (ikut kebiasaan Bos)

```text
S1. Baca lengkap: konteks_dari_bab() ai.py:1924 + cara ai_revisi memanggil LLM
S2. SKETSA HTML dulu: apa yang mahasiswa LIHAT saat klik "Mulai Belajar"
    (2 pilihan bentuk) → Bos pilih
S3. Bangun app/belajar.py (fungsi insight) + rute + pagar
S4. Gerbang: periksa_kode.sh + uji baru app/_uji_insight_belajar.py
S5. Uji dengan NASKAH NYATA (S1 unmul 5 bab) — ukur token nyata
S6. Potret + vision → lapor → minta izin deploy
```

## ⚠️ RISIKO YANG WULAN SEBUTKAN JUJUR

```text
1. TOKEN: mini insight tetap MEMAKAI token user? atau masuk paket?
   → §4.8 bilang "biaya AI 0,78%" → artinya DITANGGUNG PAKET, bukan token user.
   → PERLU KEPUTUSAN BOS: ini masuk paket (gratis) atau potong saldo?
2. Model: pakai combo `EduAi` (sama seperti revisi) atau model ringan khusus?
3. Kalau naskahnya jelek/kosong → insight bisa ngawur. Guardrail: WAJIB kutip sumber.
4. Simulasi sidang (L3) belum — LANGKAH 3.
```

## ❓ PERTANYAAN KE BOS (sebelum koding)

```text
Q1. Biaya token mini insight: DITANGGUNG PAKET (mahasiswa tidak bayar) atau
    potong saldo token mahasiswa?
    A. Ditanggung paket (sesuai §4.8 "0,78% biaya") ← Wulan sarankan
    B. Potong saldo/token mahasiswa
Q2. Sumber isi bab: dari `section_state.isi_teks` (hasil revisi, sudah ada)
    atau baca ulang naskah?
    A. section_state (HEMAT) ← Wulan sarankan
    B. baca ulang naskah
```
