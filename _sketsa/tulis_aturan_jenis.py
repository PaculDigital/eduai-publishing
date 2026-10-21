"""TAMBAH aturan PEMILIHAN JENIS GRAFIK ke prompt G7e (ACC Bos "A").

🔴 MENGAPA (keluhan Bos 25Sep26):
   "Tanua hasil grafik hanya line saja? Tidak bisa grafik model bar atau
    pie yang bagus bagus gitu."
   → AI cenderung SELALU memilih "garis". Padahal kaidah visualisasi:
       · data WAKTU/tahun  → batang atau garis (JANGAN pai)
       · data KOMPOSISI    → pai (1 titik waktu)
       · data SEBARAN      → histogram
       · dua variabel      → sebar
   → Pai untuk data tren = SALAH KAIDAH (dikonfirmasi mata 25Sep26).

DITARUH di dalam G7e, tepat sebelum "🔴 PAGAR ANTI-MENGARANG".
TIDAK membuat aturan baru (aturan Bos: perbaiki yang lama).
"""
from pathlib import Path

p = Path('/opt/data/services/eduai-publishing/prompts/revisi_produksi.txt')
s = p.read_text(encoding='utf-8')

anchor = '    🔴 PAGAR ANTI-MENGARANG (PALING PENTING — INI NASKAH AKADEMIK):'
assert anchor in s, 'anchor tidak ditemukan — batalkan'
assert 'PILIH JENIS GRAFIK' not in s, 'aturan sudah ada — batalkan'

ATURAN = '''    📐 PILIH JENIS GRAFIK YANG BENAR (jangan selalu "garis"!):

       Cocokkan jenis dengan BENTUK DATA, bukan dengan selera:

       · Data PERKEMBANGAN MENURUT WAKTU (tahun, bulan, periode) —
         mis. "PDB 2015–2022", "penjualan per kuartal" →
         PAKAI "batang" (paling mudah dibaca) atau "garis" (kalau
         menonjolkan arah tren). DILARANG "pai" — pai untuk data waktu
         adalah SALAH KAIDAH (pai tidak punya urutan waktu).

       · Data KOMPOSISI / PANGGSA dari SATU keseluruhan pada SATU waktu —
         mis. "pangsa pasar 4 merek 2023", "komposisi biaya produksi" →
         PAKAI "pai" (bagian dari total).

       · Data SEBARAN / FREKUENSI nilai —
         mis. "sebaran skor 100 responden", "frekuensi nilai ujian" →
         PAKAI "histogram".

       · Hubungan DUA variabel angka pada banyak subjek —
         mis. "harga vs jumlah pembelian per toko" →
         PAKAI "sebar" (scatter).

       Contoh penerapan pada kalimat user:
         "buatkan grafik pertumbuhan GDP 2015–2018" → "batang"
         "buatkan pie komposisi pangsa pasar" → "pai"
         "histogram nilai ujian" → "histogram"
         "sebar hubungan harga dan penjualan" → "sebar"

       Kalau user MENYEBUT jenisnya, IKUTI user. Kalau tidak, pilih
       menurut kaidah di atas dan sebutkan alasannya singkat di kalimat
       pengantar (mis. "digambarkan sebagai diagram batang agar arah
       perubahan tahunan mudah dibaca").

'''

s = s.replace(anchor, ATURAN + anchor, 1)
p.write_text(s, encoding='utf-8')
print(f'✅ aturan pemilihan jenis ditambahkan · prompt {len(s):,} byte')
print(f'   cek: PILIH JENIS GRAFIK ×{s.count("PILIH JENIS GRAFIK")}')
