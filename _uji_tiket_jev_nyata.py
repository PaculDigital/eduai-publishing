"""UJI JEV SUNGGUHAN — apakah Jev bisa menilai MAKNA bab?

Uji ini memanggil JEV ASLI (bukan palsu). Membuktikan:
  ① bab ditambah kalimat pendukung  → Jev jawab 'sama'  → LOLOS
  ② bab diganti fokus total         → Jev jawab 'beda'  → BATAL

⚠️ Biaya: 2 pertanyaan choice pendek (gratis untuk user — ditanggung EduAi).
"""
import sys
import time

sys.path.insert(0, "/app")
from app import jev as J                       # noqa: E402
from app import tiket_lolos as T               # noqa: E402

print("  Jev siap?", J.cek_siap())
print()

BAB_AWAL = (
    'BAB I PENDAHULUAN\n\n'
    'Latar belakang: industri kuliner di kota ini tumbuh pesat, namun belum '
    'ada kajian tentang pengaruh kualitas layanan terhadap kepuasan pelanggan '
    'pada warung kopi lokal. Penelitian ini bertujuan mengisi celah tersebut '
    'dengan menguji hubungan kualitas layanan, harga, dan kepuasan pelanggan. '
    * 6)

#  ① ditambah kalimat PENDUKUNG — makna TETAP
BAB_TAMBAH = BAB_AWAL + (
    '\n\nSebagai tambahan, penulis mencatat bahwa data ini dikumpulkan pada '
    'bulan Januari 2026 dengan izin pemilik warung.')

#  ② FOKUS DIGANTI TOTAL — makna BERUBAH
BAB_GANTI = (
    'BAB I PENDAHULUAN\n\n'
    'Latar belakang: penelitian ini membahas pengaruh pupuk organik terhadap '
    'hasil panen padi di desa X. Fokus utama adalah kandungan nitrogen tanah, '
    'bukan kualitas layanan. Tujuan penelitian ini mengukur produktivitas '
    'pertanian dan efisiensi pupuk. Tidak ada pembahasan kepuasan pelanggan. '
    * 6)

skema = T._skema_pertanyaan()

for nama, baru, harap in [('① ditambah kalimat pendukung', BAB_TAMBAH, 'sama'),
                          ('② fokus diganti total', BAB_GANTI, 'beda')]:
    bahan = T._bahan_banding(BAB_AWAL[:1500], baru[:1500])
    t0 = time.time()
    jawab = J.tanya(bahan, skema)
    dtk = time.time() - t0
    putusan = ''
    yakin = 0.0
    if isinstance(jawab, dict):
        isi = jawab.get('masih_sama') or {}
        if isinstance(isi, dict):
            putusan = str(isi.get('choice') or '').strip().lower()
            try:
                yakin = float(isi.get('confidence') or 0)
            except (TypeError, ValueError):
                yakin = 0.0
    tanda = '✅' if putusan == harap else '❌'
    print(f"  {tanda} {nama}: Jev bilang '{putusan}' (yakin {yakin:.2f}) "
          f"· harap '{harap}' · {dtk:.1f} dtk")
    if not isinstance(jawab, dict):
        print(f"       balasan mentah: {str(jawab)[:200]}")
