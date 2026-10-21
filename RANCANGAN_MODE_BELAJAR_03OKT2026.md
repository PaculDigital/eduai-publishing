# 🎓 MODE BELAJAR — KEPUTUSAN DESAIN (ACC Bos 03Okt26)

## PUTUSAN BOS (verbatim + tafsir terukur)

| # | Pertanyaan | Jawaban Bos | Arti |
|---|---|---|---|
| 1 | Menu atau pita tab? | **A — PITA TAB** | Tab ke-3 di dashboard: `Naskah Saya \| Kolaborasi \| 🎓 Belajar`. TIDAK menambah menu baru. |
| 2 | Isi tab | **B — 3 KARTU TAHAP** | Siap Proposal → Siap Hasil → Siap Sidang |
| 3 | Panel skor | **DI ATAS** (permintaan Bos) | Panel skor = elemen PALING ATAS di dalam tab |
| 4 | "Rincian per Bab" | **B — DIBUANG** | Tidak ditampilkan. Cukup kartu tahap. |
| 5 | Tombol di kartu terkunci | **A — TAMPILKAN TAPI MATI** | Tombol "Belum terbuka" tetap tampil (disabled), supaya user tahu ada tahap berikutnya |

## KENAPA TAB, BUKAN MENU

Menu navigasi sekarang sudah: `Naskah Saya`, `Kolaborasi`, `Pengaturan`, `Sampah`
(jangan ditambah supaya user tidak bingung). Pita tab **sudah ada** di
`naskah.html` (Tab 1 Naskah Saya · Tab 2 Kolaborasi) → tinggal **tambah tab ke-3**.
⇒ Sesuai aturan Bos: "yang ADA bisa sinkron, jangan buat baru."

## URUTAN KERJA (JANGAN LOMPAT — mesin belum ada!)

```
LANGKAH 1 — HALAMAN (Tahap ini)
   · Pita tab ke-3 "🎓 Belajar" di naskah.html
   · Route GET /belajar
   · Panel skor di atas     → data JUJUR (kalau mesin belum ada: 0/0/0)
   · 3 kartu tahap          → kartu terbuka HANYA kalau bab-nya ada
   · Kartu terkunci + tombol mati
   ❗ TIDAK boleh mengaku sudah ada insight/soal kalau mesinnya belum ada.

LANGKAH 2 — MESIN MINI INSIGHT (L1)
   · Insight per bab dari bab yang SUDAH direvisi
   · Simpan ke belajar_naskah.insight_json (kolom SUDAH ADA)
   · Gerbang: insight WAJIB mengutip naskah, bukan mengarang

LANGKAH 3 — BANK SOAL 4 LEVEL (L2)
LANGKAH 4 — SIMULASI SIDANG (L3)  ← paling bernilai
LANGKAH 5 — SKOR PENGUASAAN (L4)
```

## ⚠️ SYARAT AKTIVASI (ACC Bos 03Okt26)

- **A** — dianggap terpakai **saat user klik "Aktifkan"** (bukan saat insight jadi).
- Naskah WAJIB dipilih saat aktivasi; **melekat pada 1 naskah**, tidak bisa ganti.
- Naskah lain → harus beli AddOn Rp 75.000 (+1 naskah) dulu.
- Kalau user aktivasi saat baru BAB I → tampilkan **kartu penenang jujur**
  (apa yang terbuka sekarang + apa yang menyusul + "tersimpan permanen").
- Jatah tidak kembali walau naskah dihapus (sudah terpakai).

## STRUKTUR BERTAHAP (dari MASTER_PLAN §4.8, ACC 13Sep26)

| Kondisi naskah | Mini Insight | Bank Soal | Ujian Proposal | Ujian Sidang |
|---|---|---|---|---|
| Baru BAB I | BAB I saja | ❌ | ❌ | ❌ |
| BAB I–II | BAB I, II | ❌ | ❌ | ❌ |
| **BAB I–III** | lengkap | ✅ | ✅ "Siap Proposal" | ❌ |
| BAB I–IV | + IV | ✅ + IV | ✅ | ❌ |
| **BAB I–V** | penuh | penuh | ✅ | ✅ "Siap Sidang" |

## KENAPA INI AMAN (mesin deteksi bab sudah diperbaiki 03Okt26)

Sebelum 03Okt26, 13 naskah mahasiswa terdeteksi **0 bab** → syarat
"bab selesai" mustahil diukur. Setelah perbaikan: 13 naskah → **5 bab**.
⇒ Mode Belajar BARU bisa dibangun sekarang.

## JEBAKAN YANG WAJIB DIHINDARI

1. **ANGKA BOHONG** — jangan tampilkan skor/insight kalau mesinnya belum ada.
   Kalau belum ada → tampilkan apa adanya ("Belum terbuka"), bukan 0 palsu yang
   seolah "sudah dinilai dan dapat nol".
2. **HALAMAN KOSONG** — user yang sudah bayar lalu melihat halaman kosong akan
   merasa ditipu. Kartu penenang WAJIB sebelum aktivasi.
3. **TAB KE-3 BUKAN MENU BARU** — jangan tambah item di navigasi atas.
4. **AddOn sudah dijual (Rp 75.000) tapi mesin belum ada** → beri label jujur
   ("Segera hadir") atau sembunyikan sampai LANGKAH 2 jadi.
