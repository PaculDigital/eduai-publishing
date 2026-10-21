import pathlib

BLOK = """
### ✅ C10 — DITUTUP 25Sep26 (BUG NYATA: naskah mahasiswa jadi KOSONG)

**BAGAIMANA KETEMU:** saat mengerjakan C7, uji `_uji_publik_komentar.py`
MENEMBAK endpoint nyata (`POST /api/ai/v1/revisi`) — bukan tiruan. Hasilnya
file 47 tersimpan v60 & v61 = **0 karakter**, v61 `terpakai=1` → NASKAH KOSONG,
padahal status `selesai` dan galat kosong. Lebih buruk: v57 (4.522 kar) sudah
**DIHAPUS** oleh "gear" sehingga tidak ada lagi yang bisa dipulihkan.

**MENGAPA C9 TIDAK CUKUP:** pagar C9 dipasang di loop penggabungan
(`hasil_bagian.append`). `konten` sudah KOSONG **sebelum** sampai situ, jadi
pagar itu tidak pernah dilewati. Uji C9 (16/0) HIJAU karena ujinya MENIRUKAN
jalur dengan kode sendiri — bukan menembak pintu aslinya.

**AKAR (3 pintu, terbaca dari kode):**
1. `versi.py simpan_versi_per_komentar()` — `for v in lama: v.terpakai = False`
   dijalankan **SEBELUM** tahu ada isi baru; kalau semua blok kosong →
   `return []` tanpa mengembalikan `terpakai` → versi lama MATI, tak ada pengganti.
2. `versi.py simpan_versi()` — `isi=''` ikut tersimpan + `terpakai=True`.
3. "Gear" memakai `db.delete(v)` → versi berisi HILANG PERMANEN.

**PERBAIKAN (ACC Bos "1+2+3"):**
* **Pagar 1** — `simpan_versi_per_komentar()`: periksa `layak` (ada isi bukan
  spasi) **DI DEPAN**; kalau tidak ada → `return []` tanpa menyentuh versi lama.
* **Pagar 1b** — `simpan_versi()`: tolak `isi` kosong → `return None`.
  Pemanggil `ai.py:1936` diperiksa (`if v is not None`).
* **Pagar 2** — `ai.py _revisi_kerja()`: `konten` kosong → log.error +
  HTTPException 503 (Token Revisi dikembalikan), TIDAK menyentuh versi_dokumen.
* **Pagar 3** — Gear **mengarsipkan** (`diarsipkan=True`), bukan `db.delete()`.
  Kolom `diarsipkan` ditambahkan lewat migrasi aditif yang SUDAH ADA di
  `models.py _migrasi_kolom()` (DEFAULT 0 → versi lama tetap "aktif").
  `daftar_versi(..., dengan_arsip=False)` menyaring arsip secara bawaan;
  `hapus_versi_file()` memakai `dengan_arsip=True` supaya arsip tidak jadi yatim.

**YANG TIDAK DIUBAH:** rumus §4.13, kuota, alur proses, kuota pengembalian.

**UJI `_uji_c10_versi_kosong.py` — 23 asersi, BERGIGI 5 arah:**
```
SEHAT                         → 23 LULUS / 0 GAGAL
RUSAK 1 (pagar "layak")       → 21/2  (2b, 2c GAGAL) ✅
RUSAK 2 (pagar isi kosong)    → 16/7  (1a-1d, 2c, 5e, 5e2 GAGAL) ✅
RUSAK 3 (gear menghapus)      → 21/2  (5b, 5b2 GAGAL) ✅
RUSAK 4 (daftar_versi arsip)  → 21/2  (4a, 4b GAGAL) ✅
RUSAK 5 (pagar ai.py)         → 22/1  (5f GAGAL) ✅
pulih                         → 23/0
```

**🚨 PELAJARAN UJI PALING PENTING (2× gagal di sesi ini):**
Asersi yang mencari **TEKS** tidak bisa melihat pagar yang **DIMATIKAN** —
mencabut pagar dengan `if False:` menyisakan teksnya tetap terbaca. Dua bentuk:
* asersi lama 5f mencari `if not (konten or '').strip():` + `raise HTTPException(503)`
  → pola itu JUGA cocok dengan pagar C9 LAMA → tidak bergigi.
* setelah diperbaiki jadi mencari penanda `C10`, tetap tidak bergigi — `if False:`
  di depan tidak mengubah teks.
⇒ **Yang benar: POTONG potongan pagarnya, JALANKAN, dan pastikan ia benar-benar
melempar.** Diimplementasikan di `_periksa_pagar_c10.py` (di jalankan di dalam
container; dedent JANGAN dilakukan — blok pagar sudah ber-indentasi 4).

**🚨 PELAJARAN DATA/UJI:**
* Uji yang menembak **endpoint nyata** MERUSAK data produksi. Wajib BACKUP DB
  sebelum menjalankan. Wulan lalai → v57 (4.522 kar) terhapus, dipulihkan dari
  `_arsip/pra-sot/20260925_010845-sot/eduai.db`.
* `_periksa_pagar_c10.py` dijalankan di DALAM container — `docker` TIDAK ada di
  dalam image, jadi jangan panggil `subprocess.run(['docker', ...])` dari sana.

**PEMULIHAN DATA:** `_sketsa/pulihkan_file47_dari_backup.py` → v57 (4.522 kar)
kembali & jadi `terpakai=1`. Versi kosong v59/v60/v61 DIBIARKAN sebagai jejak.

**TAYANG:** image `eduai-app:20260925_021902-sot` · `/health` 200 ·
uji C10 23/0 · C9 16/0 · C6 20/0 di image produksi.
"""

for nama, penanda in [
    ('PETA_PERCABANGAN_24SEP2026.md', 'C10 — DITUTUP 25Sep26'),
    ('MASTER_PLAN.md', 'C10 — naskah KOSONG'),
    ('FLAG_LANJUT_DISINI.md', 'C10'),
]:
    p = pathlib.Path(nama)
    if not p.exists():
        print(f'{nama}: TIDAK ADA'); continue
    s = p.read_text()
    if penanda in s:
        print(f'{nama}: sudah ada'); continue
    if nama == 'PETA_PERCABANGAN_24SEP2026.md':
        s = s.replace('| **C7** |', '| **C10** | ✅ **BUG: naskah jadi KOSONG** — gear menghapus versi berisi + versi 0-kar jadi terpakai | SELESAI 25Sep26 |\n| **C7** |', 1)
        anchor = '\n## 🧭 CARA MEMBUKTIKAN TIAP BARIS'
        s = s.replace(anchor, BLOK + anchor, 1) if anchor in s else s.rstrip() + '\n' + BLOK
    elif nama == 'MASTER_PLAN.md':
        s = s.rstrip() + ('\n\n### C10 — naskah KOSONG (DITUTUP 25Sep26)\n\n'
            'Uji C7 menembak endpoint nyata → file 47 tersimpan versi **0 karakter** '
            'yang langsung `terpakai=1` (naskah mahasiswa kosong), dan v57 (4.522 kar) '
            'sudah DIHAPUS gear. Akar: `versi.py` mematikan versi lama SEBELUM tahu ada '
            'isi baru; `simpan_versi` menerima isi kosong; gear memakai `db.delete()`.\n\n'
            'Perbaikan (ACC "1+2+3"): pagar `layak` di depan · tolak isi kosong di '
            '`simpan_versi` · pagar 503 di `ai.py` · gear **mengarsipkan** '
            '(`diarsipkan=True`, migrasi aditif) + `daftar_versi` menyaring arsip. '
            'Uji `_uji_c10_versi_kosong.py` 23/0 BERGIGI 5 arah. '
            'Tayang `eduai-app:20260925_021902-sot`.\n')
    else:
        s = s.rstrip() + ('\n| **C10** | ✅ **DITUTUP 25Sep26** — BUG NYATA: naskah mahasiswa '
            'jadi KOSONG. Uji C7 menembak endpoint nyata → v60/v61 (0 kar) tersimpan, v61 '
            'terpakai, v57 (4.522 kar) DIHAPUS gear. Pagar: `layak` di depan · tolak isi '
            'kosong `simpan_versi` · 503 di `ai.py` · gear ARSIP bukan HAPUS (kolom '
            '`diarsipkan`). Uji `_uji_c10_versi_kosong.py` 23/0 BERGIGI 5 arah. '
            'Tayang `eduai-app:20260925_021902-sot`. |\n')
    p.write_text(s)
    print(f'{nama}: DITAMBAH')
