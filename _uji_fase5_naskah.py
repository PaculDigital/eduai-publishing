"""Uji FASE 5 bagian 8 — naskah NYATA (dijalankan di dalam container produksi).

Bukti: konsistensi.py jalan di atas teks naskah sungguhan
(hasil ai._teks_dari_berkas + state.petakan), bukan cuma dict buatan.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')
from app import konsistensi as K
from app import state, ai as AI

KANDIDAT = []
for akar in ('/app/uploads', '/app/data/uploads', '/app/_arsip', '/tmp/naskah_uji'):
    if not os.path.isdir(akar):
        continue
    for dp, dn, fn in os.walk(akar):
        for f in fn:
            if f.lower().endswith('.docx') and '~$' not in f:
                p = os.path.join(dp, f)
                try:
                    KANDIDAT.append((os.path.getsize(p), p))
                except OSError:
                    pass
KANDIDAT.sort(reverse=True)
print(f"docx ditemukan: {len(KANDIDAT)}")
for s, p in KANDIDAT[:6]:
    print(f"  {s/1e6:7.2f} MB  {p}")

if not KANDIDAT:
    print("TIDAK ADA docx -> lewati")
    sys.exit(0)

ukuran, path = KANDIDAT[0]
print(f"\n=== UJI NASKAH: {os.path.basename(path)} ({ukuran/1e6:.2f} MB) ===")

t0 = time.time()
teks = AI._teks_dari_berkas(Path(path), os.path.basename(path))
t1 = time.time()
print(f"1. ekstrak : {len(teks):,} karakter dalam {t1-t0:.2f}s")

t0 = time.time()
peta = state.petakan(teks)
t1 = time.time()
print(f"2. petakan : {len(peta)} bagian dalam {t1-t0:.2f}s")
total_kar = 0
for p in peta:
    isi = p.get('isi_teks') or ''
    total_kar += len(isi)
    print(f"   {p['section_id']:14s} {len(isi):7,d} kar  [{p.get('kategori','')}]  {p.get('section_title','')[:44]}")
print(f"   TOTAL isi terpetakan: {total_kar:,} kar")

# judul diambil dari naskah: baris panjang pertama di bagian awal
judul_asli = ""
for p in peta:
    for baris in (p.get('isi_teks') or '').split('\n')[:20]:
        b = baris.strip()
        if len(b) > 45 and not b.upper().startswith(('BAB', 'HALAMAN', 'DAFTAR', 'LEMBAR')):
            judul_asli = b
            break
    if judul_asli:
        break

# variabel & hipotesis diambil dari naskah nyata (bukan dikarang) supaya
# pemeriksaan benar-benar menguji data asli user
kandidat_var = ["Kualitas Produk", "Kepuasan Konsumen", "Loyalitas", "Kinerja Karyawan",
                "Kepemimpinan", "Motivasi", "Komitmen Organisasi", "Kinerja Pegawai"]
var_ada = [v for v in kandidat_var if v.lower() in teks.lower()]
hipo_ada = sorted(set(__import__('re').findall(r'\bH\s*[1-9]\b', teks)))[:12]

brief = {"judul": judul_asli or "(judul tidak terdeteksi)",
         "variabel": var_ada or ["Variabel Tidak Ada"],
         "hipotesis": hipo_ada or ["H1"]}
print(f"3. brief uji: judul={judul_asli[:55]!r}")
print(f"   variabel ADA di naskah: {var_ada or '-'}")
print(f"   hipotesis ADA di naskah: {hipo_ada or '-'}")

rows = [{"section_id": p['section_id'],
         "section_title": p.get('section_title', ''),
         "isi_teks": p.get('isi_teks', '')} for p in peta]

t0 = time.time()
hasil = K.check_consistency(brief, rows)
t1 = time.time()
print(f"4. check_consistency: {t1-t0:.3f}s -> {hasil['summary']['counts']} ok={hasil['ok']}")
print(f"   total temuan: {len(hasil['issues'])}")
for i in hasil['issues'][:8]:
    print(f"   [{i['level']:7s}] {str(i.get('section')):10s} {i['message'][:105]}")

laporan = K.format_laporan(hasil)
low = laporan.lower()
terlarang = [t for t in ("kuota", "rupiah", "addon", "token ai", "rp ") if t in low]
print(f"\n5. laporan: {len(laporan)} kar · kata terlarang: {terlarang or 'BERSIH'}")
print(f"6. catatan_untuk_ai: {len(K.catatan_untuk_ai(hasil))} kar")

# uji tahan banting: naskah ASLI tanpa judul/variabel (kondisi nyata user baru)
hasil2 = K.check_consistency({}, rows)
print(f"7. tanpa brief: {hasil2['summary']['counts']} (tidak boleh crash)")
hasil3 = K.check_consistency(brief, [{"section_id": "__seluruh__", "isi_teks": teks}])
print(f"8. dokumen 1 bagian ({len(teks):,} kar): {hasil3['summary']['counts']}")

assert len(teks) > 10000, "teks naskah terlalu pendek"
assert isinstance(hasil['summary'], dict)
print("\n=== UJI NASKAH NYATA LULUS ===")
