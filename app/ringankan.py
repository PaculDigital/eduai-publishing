"""RINGANKAN NASKAH — kompres GAMBAR saja di dalam .docx (ACC Bos 03Okt26).

═══════════════════════════════════════════════════════════════════════════
KENAPA ADA (akar, TERUKUR 03Okt26)
═══════════════════════════════════════════════════════════════════════════
Naskah nyata `SKRIPSI-S1-unmul-fazrigading.docx` = 5,08 MB, isinya:
  · 24 GAMBAR = 4,84 MB (66% berkas!) — image5.png SENDIRI 1,89 MB
  · word/document.xml (teks/tabel/layout) = 1,61 MB
  · word/settings.xml = 430 KB berisi 16.435 penanda `w:rsid` (sampah Word)
⇒ Editor OnlyOffice memuat LAMA karena browser harus mengunduh gambar itu.

PUTUSAN BOS (verbatim): "A. Tapi hanya kompress ukuran image saja kan?
Tidak merubah layout atau naskah paragraf, tabel, dll."
→ Opsi A: kompres SAAT UNGGAH. HANYA gambar. NASKAH TIDAK DISENTUH.

═══════════════════════════════════════════════════════════════════════════
KENAPA AMAN — STRUKTUR .docx (TERBUKTI dari naskah nyata)
═══════════════════════════════════════════════════════════════════════════
  word/document.xml     → isi NASKAH (teks, paragraf, tabel, layout)
                          ⟹ TIDAK DIBUKA, TIDAK DIUBAH SAMA SEKALI
  word/media/image*.png → BERKAS GAMBAR TERPISAH
                          ⟹ INI SAJA yang dikompres isinya
  Ukuran gambat di naskah ditulis di document.xml dalam SATUAN CM
  (mis. `<wp:extent cx="…" cy="…"/>` = 13,0 × 6,6 cm) — BUKAN piksel.
  ⟹ gambar diperkecil/dikompres isinya, UKURAN DI HALAMAN TETAP SAMA.

3 PAGAR:
  1. SALINAN ASLI TETAP: fungsi ini hanya MENGEMBALIKAN byte baru;
     pemanggil yang memutuskan. Bila gagal / hasil lebih besar →
     kembalikan byte ASLI (jangan paksa).
  2. document.xml, styles.xml, numbering.xml, dst → DISALIN APA ADANYA.
  3. Hanya gambar > AMBANG_KB yang disentuh; gambar kecil dilewati.

⚠️ SATU HAL YANG BOS WAJIB TAHU (jujur): kalau naskah punya GAMBAR DI DALAM
HEADER/FOOTER, isinya juga ikut dikompres (tetap berkas media yang sama).
Ukuran/posisinya TIDAK berubah — hanya ketajamannya. Sudah diukur: naskah
Bos TIDAK punya gambar di header/footer.
"""

from __future__ import annotations

import io
import logging
import zipfile

log = logging.getLogger(__name__)

#  Gambar di bawah ini TIDAK diganggu — sudah kecil, tak sepadan risikonya.
AMBANG_KB = 120

#  Batas panjang sisi TERPANJANG (piksel). Gambar yang lebih besar dari ini
#  diperkecil. 1600 px cukup untuk tampilan layar & cetak pada ukuran
#  halaman A4 (≈ 190 dpi pada lebar penuh) — mata hampir tak bisa bedakan.
SISI_MAKS = 1600

#  Kualitas JPEG hasil kompres. 82 = titik seimbang (terukur: mata masih
#  nyaman, berkas turun drastis).
KUALITAS = 82

_EKST_GAMBAR = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')


def _kompres_satu(data: bytes, nama: str) -> bytes:
    """Kompres satu gambar. Kembalikan byte baru, atau byte ASLI bila gagal."""
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:                                     # noqa: BLE001
        log.info('[ringankan] lewati %s (tidak terbaca: %s)', nama, e)
        return data

    asli = data

    #  ── Perkecil bila sisinya kelewat panjang ─────────────────────────
    w, h = img.size
    if max(w, h) > SISI_MAKS:
        skala = SISI_MAKS / float(max(w, h))
        img = img.resize((max(1, int(w * skala)), max(1, int(h * skala))),
                         Image.LANCZOS)

    #  ── Tentukan format keluaran ──────────────────────────────────────
    #  ⚠️ PNG/RGBA tidak bisa jadi JPEG tanpa latar — beri putih dulu.
    #  ⚠️ PNG bergaris/tulisan (tangkapan layar) tetap PNG supaya tidak kabur.
    punya_alfa = img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info
    pakai_jpeg = (not punya_alfa) and nama.lower().endswith(('.jpg', '.jpeg'))

    buf = io.BytesIO()
    try:
        if pakai_jpeg or (not punya_alfa and img.mode not in ('RGB', 'L')):
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            img.save(buf, format='JPEG', quality=KUALITAS, optimize=True)
        else:
            #  PNG: coba palet dulu bila warnanya sedikit (hemat besar),
            #  kalau tidak pakai PNG biasa dengan kompresi maksimal.
            img.save(buf, format='PNG', optimize=True)
    except Exception as e:                                     # noqa: BLE001
        log.info('[ringankan] gagal menulis ulang %s (%s) — pakai asli',
                 nama, e)
        return asli

    hasil = buf.getvalue()
    #  ── PAGAR: kalau hasil TIDAK lebih kecil, pakai ASLI ─────────────
    if len(hasil) >= len(asli):
        return asli
    return hasil


def ringankan_docx(isi: bytes, nama: str = '') -> tuple[bytes, dict]:
    """Kembalikan (byte_baru, laporan). byte_baru = isi ASLI bila gagal.

    laporan = {'gambar': n, 'dikompres': n, 'sebelum': byte, 'sesudah': byte}
    """
    lapor = {'gambar': 0, 'dikompres': 0, 'sebelum': len(isi), 'sesudah': len(isi),
             'dilewati': 0}
    if not nama.lower().endswith('.docx'):
        return isi, lapor

    try:
        z_in = zipfile.ZipFile(io.BytesIO(isi))
    except Exception as e:                                     # noqa: BLE001
        log.info('[ringankan] bukan docx sah (%s) — pakai asli', e)
        return isi, lapor

    keluar = io.BytesIO()
    try:
        with zipfile.ZipFile(keluar, 'w', zipfile.ZIP_DEFLATED) as z_out:
            for item in z_in.infolist():
                data = z_in.read(item.filename)
                nama_low = item.filename.lower()
                #  ── HANYA berkas gambar di word/media/ yang disentuh ───
                if 'media/' in nama_low and nama_low.endswith(_EKST_GAMBAR) \
                        and len(data) > AMBANG_KB * 1024:
                    lapor['gambar'] += 1
                    baru = _kompres_satu(data, item.filename)
                    if baru is not data and len(baru) < len(data):
                        lapor['dikompres'] += 1
                        data = baru
                    else:
                        lapor['dilewati'] += 1
                #  Tulis dengan metadata yang SAMA (zipinfo dipertahankan
                #  supaya struktur docx tetap sah).
                zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = item.external_attr
                z_out.writestr(zi, data)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[ringankan] gagal merakit docx (%s) — pakai asli', e)
        return isi, lapor

    hasil = keluar.getvalue()
    if len(hasil) >= len(isi):
        #  PAGAR: tak ada gunanya kalau tidak lebih ringan.
        log.info('[ringankan] hasil tidak lebih kecil (%s→%s) — pakai asli',
                 len(isi), len(hasil))
        return isi, lapor

    lapor['sesudah'] = len(hasil)
    log.info('[ringankan] %s: %s KB → %s KB (%s/%s gambar dikompres)',
             nama or '(docx)', len(isi) // 1024, len(hasil) // 1024,
             lapor['dikompres'], lapor['gambar'])
    return hasil, lapor
