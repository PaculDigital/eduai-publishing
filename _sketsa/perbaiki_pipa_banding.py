"""PERBAIKAN: pipa menerima PEMBANDING yang BENAR (naskah yg dikirim ke AI).

🔴 AKAR (terbukti 25Sep26):
   `_revisi_kerja` baris 2060:  _pipa_periksa(konten, sebelum or '')
   `sebelum` HANYA terisi bila `bab != BAB_SELURUH` (baris 1576).
   ⇒ Saat bab='__seluruh__' (revisi seluruh dokumen / naskah besar),
     pembanding = '' → pipa balas "Naskah kosong — tidak ada yang bisa
     diperbaiki." → 503 SELALU.

   Terbukti uji 2 arah:
      periksa(konten, '')       → ok=False "Naskah kosong"   ← GEJALA
      periksa(konten, potongan) → editan=1  ✅ pipa BEKERJA

🛠️ PERBAIKAN: kumpulkan teks yang BENAR-BENAR dikirim ke AI (`naskah_dikirim`):
   - bila naskah dipotong  → gabungan semua `potongan` (= naskah)
   - bila konteks tetangga → `_isi_target` (yang dikirim)
   - selain itu            → naskah utuh (sebelum+sesudah bila sub-bab)
   Lalu pakai itu sebagai pembanding pipa.
"""
import ast
import pathlib

SRC = pathlib.Path('app/ai.py')
baris = SRC.read_text().split('\n')
print(f'ai.py {len(baris)} baris')

#  ── 1) Inisialisasi `naskah_dikirim` di BADAN LOOP (tepat sebelum konteks) ──
i_konteks = next(i for i, b in enumerate(baris)
                 if b.startswith(' ' * 8) and b.strip() == "konteks_terpakai = ''")
print(f'konteks_terpakai → baris {i_konteks + 1}')

AWAL = len(baris)
baris[i_konteks:i_konteks] = [
    '        #  📌 25Sep26 — `naskah_dikirim` = teks yang BENAR-BENAR dikirim ke',
    '        #     AI pada bagian ini. Pipa WAJIB memakai ini sebagai pembanding',
    '        #     KUTIP-ASLI. Sebelumnya pipa memakai `sebelum` yang KOSONG saat',
    '        #     bab="__seluruh__" → pipa balas "Naskah kosong" → 503 selalu.',
    '        naskah_dikirim = potongan',
]
print(f'+ 5 baris inisialisasi naskah_dikirim di {i_konteks + 1}')

#  ── 2) Di blok konteks: setelah `naskah = _isi_target`, catat naskah_dikirim ──
i_isi = next(i for i, b in enumerate(baris)
             if b.startswith(' ' * 20) and b.strip() == 'naskah = _isi_target')
print(f'naskah = _isi_target → baris {i_isi + 1}')

#  Geser 1 baris (karena sisipan sebelumnya) — cari ulang setelah modif
baris[i_isi:i_isi + 1] = [
    '                    naskah = _isi_target',
    '                    naskah_dikirim = _isi_target   # pipa banding = yg dikirim',
]
print(f'+ 1 baris naskah_dikirim = _isi_target')

#  ── 3) Ganti `_pipa_periksa(konten, sebelum or '')` → pakai naskah_dikirim ──
teks = '\n'.join(baris)
LAMA = "_cek_pipa = _pipa_periksa(konten, sebelum or '')"
BARU = ("_banding_pipa = (naskah_dikirim\n"
        "                             or (naskah if bab == BAB_SELURUH\n"
        "                                 else susun_ulang(sebelum, naskah, "
        "sesudah)))\n"
        "        _cek_pipa = _pipa_periksa(konten, _banding_pipa)")
assert LAMA in teks, 'anchor pipa tidak ditemukan'
teks = teks.replace(LAMA, BARU)
print('✅ pemanggil pipa diganti → pakai naskah_dikirim')

ast.parse(teks)
print('✅ sintaks OK')
SRC.write_text(teks)
print(f'💾 tersimpan · {len(teks.split(chr(10)))} baris')
