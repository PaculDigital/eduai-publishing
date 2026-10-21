#!/usr/bin/env python3
"""TAMBAH aturan G8 (buat tabel/grafik) ke prompt produksi — ACC Bos "C".

ISI ATURAN:
   · TABEL  → AI menulis tabel dalam bentuk yang bisa dipindah ke Word
   · GRAFIK → AI mengeluarkan DATA (JSON), app yang menggambar (app/gambar.py)
   · PAGAR ANTI-MENGARANG → angka WAJIB dari naskah; kalau tidak ada → TANYA
"""
from pathlib import Path

p = Path('/opt/data/services/eduai-publishing/prompts/revisi_produksi.txt')
s = p.read_text(encoding='utf-8')
assert 'G7e.' not in s, 'G7e sudah ada — batalkan'

anchor = 'G7c. **JANGAN SEBUT NAMA ATURAN INTERNAL KE MAHASISWA.**'
assert anchor in s, 'G7c tidak ditemukan — batalkan'
assert 'G7e.' not in s, 'G7e sudah ada — batalkan'

G8 = '''G7e. **MEMBUAT TABEL / GRAFIK (bila diminta).** DUA bentuk, JANGAN tertukar:

    (1) TABEL — tulis tabel sebagai BARIS berpemisah `|`:
         Judul Tabel | Keterangan | Nilai
         Baris 1     | …          | 12,5
         Baris 2     | …          | 7,8
         Kalimat pengantar tabel WAJIB ada sebelum tabel
         (mis. "Hasil pemetaan disajikan pada tabel berikut.").
         JANGAN memakai tanda bintang/bullet untuk mengisi tabel.

    (2) GRAFIK / HISTOGRAM / DIAGRAM — KAMU TIDAK MENGGAMBAR. Yang kamu
        kerjakan: mengeluarkan **DATA**-nya dalam bentuk berikut, PERSIS:

         [DATA-GRAFIK]
         {"jenis": "batang", "judul": "Pertumbuhan GDP 2015-2024",
          "satuan": "%", "data": [{"label": "2015", "nilai": 30},
          {"label": "2016", "nilai": 34}]}
         [/DATA-GRAFIK]

        `jenis` hanya boleh: "batang", "garis", "histogram", "pai", "sebar".
        Aplikasi yang akan MENGGAMBAR dari data itu.

    🔴 PAGAR ANTI-MENGARANG (PALING PENTING — INI NASKAH AKADEMIK):
       · Angka HANYA boleh diambil dari: (a) naskah/bagian yang kamu terima,
         (b) tabel yang sudah ada di naskah, (c) angka yang user sebutkan.
       · DILARANG MUTLAK mengarang, menaksir, atau "mengisi wajar" angka.
       · Kalau angka TIDAK ADA di bahan yang kamu terima → JANGAN membuat
         grafik. Tulis kalimat jujur, contohnya:
         "Grafik pertumbuhan tersebut memerlukan data angka yang belum ada
          pada bagian naskah ini. Mohon sebutkan datanya (per tahun) agar
          saya dapat menyusunnya."
       · Kalau user MEMANG menyebut angkanya, pakai apa adanya (jangan
         dibulatkan/diubah).
       · Sertakan sumber angka pada kalimat pengantar/keterangan
         (mis. "bersumber dari Tabel 1.2").

    ⚠️ SATU perintah = SATU keluaran. Kalau user minta grafik, JANGAN
       sekaligus menulis tabel angka yang sama panjang.

'''

s2 = s.replace(anchor, G8 + anchor, 1)
assert s2 != s, 'tidak ada perubahan — batalkan'
p.write_text(s2, encoding='utf-8')
print(f'✅ G8 ditambahkan · prompt {len(s):,} → {len(s2):,} byte (+{len(s2)-len(s):,})')
print(f'   cek: G8 {s2.count("G8.")}× · DATA-GRAFIK {s2.count("DATA-GRAFIK")}×')