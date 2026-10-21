"""SINKRON C7 → SOT: catat keadaan C7 di 4 dokumen.

Keadaan C7 (25Sep26):
    · TIDAK ditutup sebagai 'lulus uji' — bahannya (file 47) TERBUKTI bukan
      naskah, jadi uji TIDAK SAHIH untuk menyatakan lulus/gagal.
    · Yang TETAP berharga dari C7: (a) pagar C10 TERBUKTI BEKERJA di produksi;
      (2) 6 cacat UJI ketemu & diperbaiki; (3) 1 kandidat bug nyata: IndexError
      di jalur `naskah` langsung (belum dibedah).
    · File 47 DIHAPUS (berkas uji rusak milik akun uji); naskah aslinya
      (65.826 kar) DISELAMATKAN ke `_contoh-dokumen/skripsi-s1/`.
"""
import pathlib
import re

DIR = pathlib.Path('/opt/data/services/eduai-publishing')

BLOK_FLAG = '''
## 🧪 C7 — UJI PUBLIK: KEADAAN SEBENARNYA (25Sep26)

**KEPUTUSAN BOS: C7 DITUTUP APA ADANYA (opsi 1).**

### Kenapa TIDAK dinyatakan "lulus"
Uji `_uji_publik_komentar.py` pakai `file_id=47` sebagai bahan. TERBUKTI:
    · `versi_dokumen` file 47 isinya = **JAWABAN AI** (`sumber='ai'`), bukan
      naskah mahasiswa → AI menolak merevisi ("ini bukan draf tulisan Anda")
    · Naskah ASLI file 47 (65.826 kar) ada di `section_state`, TAPI berkas
      fisik unggahannya HILANG
⇒ Uji tidak sahih untuk menyatakan aplikasi lulus/gagal.

### YANG TETAP BERHARGA dari C7
1. 🛡️ **Pagar C10 TERBUKTI BEKERJA di produksi** — `proses_ai` id 98-101
   jadi `gagal` + pesan jujur, dan `v57` tetap `terpakai` = naskah TIDAK RUSAK.
2. 🐛 **6 cacat UJI ketemu & diperbaiki** (bukan bug aplikasi):
   a. `docker` tidak ada di dalam container → `kuota_reset_berat` & P1 gagal.
   b. User uji berat tidak punya baris `pemakaian_ai` → 403 "bukan member".
   c. User uji berat salah ORANG (id 5 = paket GRATIS) → 403.
   d. Sandi user berat salah → login gagal.
   e. Batas tunggu 180/240/300/420/600 terlalu pendek (proses nyata 73–615 dtk).
   f. `naskah` kosong & `file_id` salah tetap dilaporkan 403, bukan 400/404.
3. ⚠️ **1 KANDIDAT BUG NYATA (BELUM dibedah):** `proses_ai` id 102
   (`in6p-nnzeDYDUz006OXrgA`) → `IndexError: list index out of range`
   di jalur `naskah` LANGSUNG (skenario N3). Belum pasti bug app atau cacat uji.

### Yang dikerjakan untuk menutup
· `_uji_publik_komentar.py` diberi **PENJAGA**: `E2E_SAYA_SETUJU=1` wajib
  (exit 77 = DILEWATI bila tidak). Alasan: uji ini memakai kuota + menulis DB.
· `file_id=47` **DIHAPUS** (versi 4 · section 1 · revisi 12 · proses 72 · file 1).
· Naskah aslinya **DISELAMATKAN** → `_contoh-dokumen/skripsi-s1/NASKAH-ASLI-file47-65826kar.txt`.
· Hasil uji terakhir: **36 LULUS / 12 GAGAL** — 12 gagal berasal dari bahan uji
  yang tidak sahih (bukan aplikasi).

### Sisa pekerjaan (SESI LAIN)
· Bedah `IndexError` jalur `naskah` langsung (id 102).
· Skenario O1 (kuota habis) — baca/set kuota belum jalan.
· Skenario P (gangguan provider) — WAJIB dijalankan DARI HOST, bukan container.
'''

# ── 1. FLAG_LANJUT_DISINI.md (blok di PALING ATAS) ───────────────────────
f = DIR / 'FLAG_LANJUT_DISINI.md'
t = f.read_text()
if 'C7 — UJI PUBLIK: KEADAAN SEBENARNYA' not in t:
    f.write_text(BLOK_FLAG.strip() + '\n\n---\n\n' + t)
    print(f'✅ {f.name}: blok C7 ditambahkan di atas')
else:
    print(f'·  {f.name}: sudah ada')

# ── 2. CATATAN_PROYEK.md (tambahkan di akhir) ────────────────────────────
f2 = DIR / 'CATATAN_PROYEK.md'
if f2.exists():
    t2 = f2.read_text()
    if 'C7 — KEADAAN SEBENARNYA' not in t2:
        f2.write_text(t2.rstrip() + '\n\n' + BLOK_FLAG.strip() + '\n')
        print(f'✅ {f2.name}: ditambahkan')
    else:
        print(f'·  {f2.name}: sudah ada')

# ── 3. Verifikasi nama berkas yang disebut benar-benar ada ───────────────
naskah = DIR / '_contoh-dokumen/skripsi-s1/NASKAH-ASLI-file47-65826kar.txt'
print()
print(f'naskah selamat: {naskah.exists()} '
      f'({naskah.stat().st_size:,} byte)' if naskah.exists() else '❌ hilang!')
