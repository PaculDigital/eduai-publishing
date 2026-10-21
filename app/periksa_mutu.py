"""PERIKSA MUTU NASKAH — fakta objektif, TANPA Jev, GRATIS.

Putusan Bos 10 Okt 2026 (pilihan "A"):
  · Pemeriksaan mutu naskah TIDAK melibatkan Jev (Jev TERBUKTI tidak bisa
    membedakan: dicoba 24 baris/naskah ⇒ naskah rusak dijawab 0% "potongan",
    sama dengan naskah sehat).
  · Biaya = Rp 0 (nol panggilan Jev). Yang dihitung hanya angka dari teks
    yang SUDAH dibaca (baca naskah sudah gratis).
  · Hasil = TAHU + TAWAR, bukan BLOKIR (pola "beri tahu" — berkas tetap boleh
    lanjut supaya user tidak kabur).

ANGKA PEMISAH (terukur 10 Okt 2026, 3 naskah nyata):
    naskah          baris isi 1 huruf   ≤2 kar   median panjang
    Asih (sehat)              1           0%       37 kar
    Wulandari-PDF         4.989          64%        1 kar   ← RUSAK
    Disertasi                 1           3%       15 kar   ← baris pendek

⇒ 1 angka (`huruf_tunggal`) sudah memisahkan sehat vs rusak dengan terang
  (1 vs 4.989). Tidak perlu penilaian ⇒ tidak perlu Jev.

KENAPA BUKAN Jev (bukti, bukan pendapat):
    Jev ditanya 24 baris/naskah "apakah baris ini potongan?" ⇒
    sehat 0/24 · RUSAK 0/24 · baris-pendek 0/24 ⇒ TIDAK BISA MEMBEDAKAN.
    Sebab: Jev menilai per baris tanpa pembanding ("D" terlihat baris biasa).

CARA PAKAI:
    from app.periksa_mutu import periksa
    lapor = periksa(teks_naskah)
    lapor['tingkat']  → 'sehat' | 'baris_pendek' | 'rusak_konversi'
    lapor['pesan']    → kalimat siap tampil ke user
"""
from __future__ import annotations

import statistics
from typing import Any

#  ── AMBANG (dari pengukuran, bukan tebakan) ────────────────────────────────
#  Batas huruf-tunggal: naskah rusak = 4.989 · naskah sehat = 1
#  ⇒ ambang 50 ada di tengah-tengah yang jauh (aman dari goyang).
AMBANG_HURUF_TUNGGAL = 50
#  Rasio baris <=2 karakter: rusak 64% vs sehat 0-3% ⇒ ambang 25%.
AMBANG_RASIO_PENDEK = 0.25
#  Median panjang baris: sehat 37 · baris-pendek 15 ⇒ ambang 20 kar.
AMBANG_MEDIAN = 20


def periksa(teks: str) -> dict[str, Any]:
    """Hitung FAKTA objektif dari teks naskah ⇒ putusan tingkat mutu.

    TIDAK memanggil Jev. TIDAK menyentuh berkas. Murni hitungan.

    Balikan:
      {
        'baris'          : jumlah baris berisi,
        'huruf_tunggal'  : jumlah baris yang isinya 1 huruf (tanda pecah),
        'rasio_pendek'   : porsi baris <=2 karakter,
        'median'         : median panjang baris,
        'tingkat'        : 'sehat' | 'baris_pendek' | 'rusak_konversi',
        'pesan'          : kalimat siap tampil,
        'saran'          : None | 'ganti_ke_docx' | 'lanjut_saja',
      }
    """
    baris = [x.strip() for x in (teks or '').split('\n')]
    isi = [x for x in baris if x]
    if not isi:
        return {
            'baris': 0, 'huruf_tunggal': 0, 'rasio_pendek': 0.0, 'median': 0,
            'tingkat': 'kosong',
            # pesan = ISI saja (tanpa judul) — judul sudah dipasang layar
            # dari `tingkat`. 11Okt26: dulu pesan memuat judul ⇒ terbaca DUA KALI.
            'pesan': ('Pastikan berkasnya berisi tulisan '
                      '(bukan hasil scan/gambar saja).'),
            'saran': 'lanjut_saja',
        }

    n = len(isi)
    huruf_tunggal = sum(1 for x in isi if len(x) == 1 and x.isalpha())
    le2 = sum(1 for x in isi if len(x) <= 2)
    rasio = le2 / n
    median = statistics.median(len(x) for x in isi)

    if huruf_tunggal >= AMBANG_HURUF_TUNGGAL:
        return {
            'baris': n, 'huruf_tunggal': huruf_tunggal,
            'rasio_pendek': rasio, 'median': median,
            'tingkat': 'rusak_konversi',
            'pesan': (f'Ada {huruf_tunggal:,} bagian yang isinya hanya 1 huruf '
                      f'(mis. "D", "i", "n", "a") — biasanya terjadi kalau '
                      f'berkas dikonversi dari PDF. Peta bab bisa jadi kurang '
                      f'rapi.').replace(',', '.'),
            'saran': 'ganti_ke_docx',
        }

    if rasio >= AMBANG_RASIO_PENDEK or median < AMBANG_MEDIAN:
        return {
            'baris': n, 'huruf_tunggal': huruf_tunggal,
            'rasio_pendek': rasio, 'median': median,
            'tingkat': 'baris_pendek',
            'pesan': (f'Rata-rata hanya {median:.0f} huruf per baris '
                      f'(umumnya 60-70). Teksnya tetap utuh — hanya pemetaan '
                      f'bab perlu lebih teliti.'),
            'saran': 'lanjut_saja',
        }

    return {
        'baris': n, 'huruf_tunggal': huruf_tunggal,
        'rasio_pendek': rasio, 'median': median,
        'tingkat': 'sehat',
        'pesan': (f'{n:,} baris, rata-rata '
                  f'{median:.0f} huruf per baris.'.replace(',', '.')),
        'saran': 'lanjut_saja',
    }
