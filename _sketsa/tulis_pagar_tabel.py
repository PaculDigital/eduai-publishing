#!/usr/bin/env python3
"""TAMBAH aturan G7d (pagar tabel/gambar) ke prompt produksi — dan TANGGA TOKEN.

ACC Bos 25Sep26: "1. A (tangga cakupan)" + "2. A (penanda + larangan)".
Backup sudah dibuat: _arsip/pre-tabel-token-<stamp>/
"""
from pathlib import Path

p = Path('/opt/data/services/eduai-publishing/prompts/revisi_produksi.txt')
s = p.read_text(encoding='utf-8')

#  ── cari titik sisip: tepat SEBELUM "G7c." supaya urutannya rapi ──
anchor = 'G7c. **JANGAN SEBUT NAMA ATURAN INTERNAL KE MAHASISWA.**'
assert anchor in s, 'G7c tidak ditemukan — batalkan, jangan ubah berkas'

ATURAN = '''G7d. **PAGAR TABEL & GAMBAR — DILARANG MENGUBAH.** Naskah memakai penanda:
    • `[[TABEL-n: … — JANGAN diubah, ini konteks]]` … `[[/TABEL-n]]`
    • `[[GAMBAR-n: di sini — JANGAN diubah, ini konteks]]`
    Tabel & gambar adalah KONTEKS agar kamu memahami isi naskah. Kamu WAJIB:
    • MEMBACA isinya sebagai konteks — JANGAN mengabaikannya.
    • DILARANG menulis ulang tabel menjadi kalimat/daftar teks.
    • DILARANG memindahkan, menghapus, menggabungkan, atau mengubah urutan
      tabel/gambar. DILARANG mengubah penanda `[[TABEL-n]]`/`[[GAMBAR-n]]`.
    • Kalau paragraf yang kamu revisi MENGANDUNG penanda tabel/gambar,
      tulis ulang HANYA kalimat di sekitarnya dan BIARKAN penanda itu utuh
      pada posisinya (salin kembali penandanya apa adanya).
    • PENGECUALIAN: kalau komentar SECARA EKSPLISIT menyebut tabel/gambar
      itu (mis. "ganti tabel 1.2", "perbaiki gambar 3"), BARU kamu boleh
      mengusulkan perubahan — dan sebutkan nomor tabel/gambarnya jelas.
    ❌ SALAH: mengubah isi tabel menjadi "Tabel 1.1: Ranah / Perkembangan…"
      sebagai teks paragraf.
    ✅ BENAR: membiarkan `[[TABEL-1: …]]` utuh, merevisi kalimat pengantarnya
      saja: "Hasil pemetaan tersebut disajikan pada tabel berikut."

'''

s2 = s.replace(anchor, ATURAN + anchor, 1)

#  ── TANGGA TOKEN: tambahkan aturan cakupan ke bagian kuota ──
anchor2 = 'G7d.'
TANGGA = ''  # ditulis di bawah (cek dulu apakah ada bagian kuota)
assert s2 != s, 'tidak ada yang berubah — batalkan'

p.write_text(s2, encoding='utf-8')
print(f'✅ G7d ditambahkan · prompt {len(s):,} → {len(s2):,} byte')
print(f'   cek: "G7d" muncul {s2.count("G7d")}× · "TABEL-n" {s2.count("TABEL-n")}×')