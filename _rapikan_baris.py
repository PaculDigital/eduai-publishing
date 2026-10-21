#!/usr/bin/env python3
"""RAPIKAN PECAHAN BARIS PDF → teks wajar (pra-olahan, sebelum Jev).

MASALAH: PDF hasil cetak/ekspor memecah 1 kalimat jadi banyak baris pendek:
    "Penelitian ini membahas tentang kelayakan bisnis di bidang fashion yaitu"
    "accessories hijab, dengan fokus pada produk Hijab Tape AyuMeera yang dikelola"
⇒ Jev melihat potongan-potongan → mengira potongan pendek = judul.

CARA: sambung HANYA kalau DUA syarat terpenuhi:
   ① baris-ATAS belum selesai (tidak diakhiri . ! ? : ; " ) ])
   ② baris-INI jelas lanjutan: diawali HURUF KECIL, atau diawali angka
      tapi bukan pola nomor daftar/struktur.

JANGAN disambung kalau baris-ini JUDUL:
   · diawali BAB / 1. BAB / 2.1 / 1. / I. / Tabel / Gambar / Sumber / DAFTAR / Lampiran
   · HURUF BESAR SEMUA & pendek
   · pendek (≤40) & tidak diawali huruf kecil & tidak diawali angka-daftar
   · angka murni (nomor halaman)

⚠️ PELAJARAN: JANGAN pakai re.X (verbose) di sini — spasi dalam pola jadi
   diabaikan & `#` jadi komentar ⇒ regex salah senyap. Dipakai pola 1-baris.

Ini ALAT UJI — tidak mengubah mesin.
"""
import re
import sys

# penanda permulaan struktur (1-baris, TANPA re.X)
MULAI_BARU = re.compile(
    r'^\s*(?:BAB\b|\d+\.\s*BAB\b|\d+(?:\.\d+)+\.?\s|\d+\.\s*[A-Z]|[IVX]+\.\s'
    r'|Tabel\b|Gambar\b|Sumber\b|Keterangan\b|Lampiran\b|DAFTAR\b)',
    re.IGNORECASE)

AKHIR_KALIMAT = re.compile(r'[.!?:;"”\)\]]\s*$')
NUMPANG_ANGKA_SLASH = re.compile(r'^\d+[./]\d+')          # 2.1 / 1/2
HURUF_BESAR_SEMUA = re.compile(r'^[^a-z]{3,}$')
ANGKA_MURNI = re.compile(r'^\d{1,4}$')
DIAWALI_KECIL = re.compile(r'^[a-z(“]')


def _judul(s: str) -> bool:
    """Baris ini kemungkinan JUDUL ⇒ jangan disambung ke baris atas."""
    if MULAI_BARU.match(s):
        return True
    if ANGKA_MURNI.match(s):
        return True
    if len(s) <= 70 and HURUF_BESAR_SEMUA.match(s):
        return True
    # pendek & bukan lanjutan kalimat ⇒ judul
    if len(s) <= 40 and not DIAWALI_KECIL.match(s):
        return True
    return False


def rapikan(teks: str) -> str:
    keluar = []
    for b in teks.split('\n'):
        s = b.strip()
        if not s:
            keluar.append('')
            continue
        if not keluar or not keluar[-1].strip():
            keluar.append(s)
            continue
        atas = keluar[-1].strip()
        # ① baris-ini judul ⇒ jangan sambung
        if _judul(s):
            keluar.append(s)
            continue
        # ② baris-ATAS sudah selesai (ada tanda akhir) ⇒ jangan sambung
        if AKHIR_KALIMAT.search(atas):
            keluar.append(s)
            continue
        # ③ baris-ATAS itu JUDUL (pendek/berhuruf besar) ⇒ JANGAN sambung!
        #    (kalau disambung, judul akan menelan kalimat di bawahnya)
        if _judul(atas):
            keluar.append(s)
            continue
        # ④ sisanya: SAMBUNG
        keluar[-1] = atas + ' ' + s
    return '\n'.join(keluar)


def main():
    masuk = sys.argv[1] if len(sys.argv) > 1 else '_naskah.txt'
    keluar = sys.argv[2] if len(sys.argv) > 2 else '_naskah_rapi.txt'
    t = open(masuk, encoding='utf-8', errors='ignore').read()
    h = rapikan(t)
    open(keluar, 'w').write(h)
    b1, b2 = len(t.split('\n')), len(h.split('\n'))
    print('baris: %d → %d  (disambung %d)' % (b1, b2, b1 - b2))
    print('karakter: %d → %d' % (len(t), len(h)))


if __name__ == '__main__':
    main()
