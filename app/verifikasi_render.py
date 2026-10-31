"""Verifikasi render final (paket sempurna item 5, Gas Bos 31 Okt 2026
malam). Laporan saja, TIDAK PERNAH menggagalkan buku.

Memeriksa dokumen DOCX final sesudah semua sisipan (indeks, singkatan,
sapuan) dan sesudah penyegaran nomor TOC pass 2: jumlah halaman dari
render nyata (teks per halaman sidecar) dan apakah setiap nomor halaman
di Daftar Isi dan di Indeks berada dalam rentang 1..total. Nomor di
luar rentang berarti pagination bergeser sesudah render terakhir
(mis. sisipan back matter), bukan berarti buku ditolak: hasilnya
dicatat di hasil_json untuk audit Wulan, bukan gerbang penolakan baru.
"""

import re

_JUDUL_INDEKS = ('INDEKS SUBJEK', 'INDEKS', 'INDEKS NAMA')
_JUDUL_AKHIR_INDEKS = ('DAFTAR PUSTAKA', 'GLOSARIUM', 'DAFTAR SINGKATAN')


def verifikasi(path_docx, halaman_render):
    """Return dict verifikasi. halaman_render = list teks per halaman
    dari render nyata (indeks 0 = halaman 1)."""
    from docx import Document
    doc = Document(path_docx)
    teks = [p.text for p in doc.paragraphs]
    total = len(halaman_render or [])

    # Daftar Isi: dari judul 'DAFTAR ISI' sampai judul bab badan
    # pertama (tanpa tab). Entri TOC bertab dengan nomor di akhir.
    toc = []
    toc_romawi = 0
    i_toc = None
    for i, t in enumerate(teks):
        if t.strip() == 'DAFTAR ISI':
            i_toc = i
            break
    if i_toc is not None:
        for t in teks[i_toc + 1:]:
            s = t.strip()
            if '\t' in t:
                akhir = t.rsplit('\t', 1)[1].strip()
                if akhir.isdigit():
                    toc.append((s.split('\t')[0].strip(), int(akhir)))
                elif akhir:
                    toc_romawi += 1
                continue
            if re.match(r'^BAB \d+\b', s.upper()):
                break

    # Indeks: seksi INDEKS SUBJEK/INDEKS/INDEKS NAMA (tanpa tab),
    # entri 'Istilah .... 3, 7' sampai seksi berikut.
    indeks = []
    di_indeks = False
    for t in teks:
        s = t.strip()
        if '\t' not in t and s.upper() in _JUDUL_INDEKS:
            di_indeks = True
            continue
        if di_indeks:
            if '\t' not in t and (
                    s.upper() in _JUDUL_AKHIR_INDEKS
                    or re.match(r'^BAB \d+\b', s.upper())):
                di_indeks = False
                continue
            if '....' in s:
                label, angka = s.split('....', 1)
                for pot in angka.split(','):
                    pot = pot.strip()
                    if pot.isdigit():
                        indeks.append((label.strip(), int(pot)))

    toc_luar = [(l, n) for l, n in toc if not 1 <= n <= total]
    indeks_luar = [(l, n) for l, n in indeks if not 1 <= n <= total]
    return {
        'halaman_total': total,
        'toc_entri': len(toc),
        'toc_romawi': toc_romawi,
        'toc_di_luar': toc_luar,
        'indeks_entri': len(indeks),
        'indeks_di_luar': indeks_luar,
        'lolos_rentang': not toc_luar and not indeks_luar,
    }
