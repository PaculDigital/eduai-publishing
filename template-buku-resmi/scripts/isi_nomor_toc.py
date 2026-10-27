#!/usr/bin/env python3
"""Isi nomor halaman daftar isi buku hasil assembly (Mesin 2).

Latar (27 Okt 2026): `buku_umum_assembly.py` menulis daftar isi dengan
tab ber-dot-leader TAPI tanpa angka — hanya "Kata Pengantar" yang punya
"iii". Akibatnya daftar isi buku produksi kosong nomornya (terbukti di
kode dan di buku nyata). Mesin 1 (template-buku-resmi) TIDAK disentuh
untuk ini: ia tidak dipanggil app dan tidak ada di image Docker, jadi
perbaikan di sana = nol efek ke pelanggan.

Cara kerja (jalur operator, mesin yang sudah ada saja):
  1. Render DOCX -> PDF lewat WordCraft (`perender_halaman`; BUKAN
     soffice — soffice dihapus dari desain 26 Okt 2026).
  2. Baca teks per halaman lewat `pdftotext` (di hermes: salinan
     permanen /opt/data/services/pdftotext/bin — JANGAN /tmp).
  3. Cari halaman tiap judul, LEWATI SELURUH span halaman daftar isi
     (pelajaran perbaikan span TOC: saringan titik saja rapuh lintas
     perender karena judul membungkus ke baris tanpa titik).
  4. Tulis angka sebagai run baru sesudah run tab di paragraf daftar
     isi. Entri yang sudah bernomor dilewati (idempotent: jalan dua
     kali = hasil sama).
  5. Simpan ke KELUAR. Angka = nomor halaman hasil render (bukan nomor
     folio cetak — bila buku mencetak folio berbeda, itu soal terpisah).

Pakai: python3 isi_nomor_toc.py MASUK [KELUAR]
  KELUAR default = MASUK dengan ".bernomor" sebelum ".docx".
Keluar: 0 bila semua terisi; 1 bila ada yang hilang (berkas tetap
ditulis dengan yang terisi + daftar HILANG dicetak lantang); 2 bila
gagal total (tidak bisa render/baca/halaman tidak ditemukan di berkas).
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import perender_halaman
from docx import Document


def halaman_teks(pdf, total):
    """Teks per halaman (huruf besar), via pdftotext -layout."""
    out = []
    for i in range(1, total + 1):
        t = subprocess.run(['pdftotext', '-f', str(i), '-l', str(i),
                            '-layout', str(pdf), '-'],
                           check=True, capture_output=True,
                           text=True).stdout
        out.append(t.upper())
    return out


def span_toc(halaman):
    """Halaman daftar isi + lanjutan berurutan bertitik 10+ (1-based)."""
    mulai = None
    for i, t in enumerate(halaman):
        if any(b.strip() == 'DAFTAR ISI' for b in t.splitlines()):
            mulai = i + 1
            break
    if mulai is None:
        return set()
    span = {mulai}
    h = mulai + 1
    while h <= len(halaman):
        n = sum(1 for b in halaman[h - 1].splitlines()
                if re.search(r'\.{10,}', b.strip()))
        if n < 3:
            break
        span.add(h)
        h += 1
    return span


def kunci_dari_judul(judul):
    """Kunci cari judul di halaman isi (huruf besar)."""
    m = re.match(r'^BAB\s+(\d+)\.', judul)
    if m:
        return 'BAB ' + m.group(1)
    m = re.match(r'^(\d+\.\d+)\s+(\S+)', judul)
    if m:
        return m.group(1) + ' ' + m.group(2)
    return judul


def cari_halaman(kunci, halaman, toc_pages):
    """Halaman pertama (di luar span TOC) yang barisnya = kunci / diawali kunci."""
    kunci = kunci.upper()
    for i, t in enumerate(halaman):
        h = i + 1
        if h in toc_pages:
            continue
        for baris in t.splitlines():
            b = baris.strip()
            if b == kunci or b.startswith(kunci + ' '):
                return h
    return None


def _sudah_bernomor(paragraf):
    """True bila paragraf TOC sudah punya run angka sesudah tab."""
    runs = paragraf.runs
    if not runs:
        return False
    ada_tab = any('\t' in r.text for r in runs)
    terakhir = runs[-1].text.strip()
    return ada_tab and re.fullmatch(r'[ivxlcdm\d]+', terakhir, re.I) is not None


def paragraf_toc(doc):
    """(entri, sudah) — entri = [(judul, paragraf)] yang perlu diisi."""
    paras = doc.paragraphs
    awal = None
    for i, p in enumerate(paras):
        if p.text.strip().upper() == 'DAFTAR ISI':
            awal = i
            break
    if awal is None:
        return None, None
    entri, sudah = [], []
    for p in paras[awal + 1:]:
        xml = p._p.xml
        if 'w:type="page"' in xml:
            break
        if p.text.strip() == 'BAB 1':
            break
        judul = p.text.strip()
        if not judul:
            continue
        if _sudah_bernomor(p):
            sudah.append((judul.split('\t')[0].strip(),
                          p.runs[-1].text.strip()))
        else:
            entri.append((judul, p))
    return entri, sudah


def _salin_font(run_baru, run_contoh):
    try:
        run_baru.font.name = run_contoh.font.name
        run_baru.font.size = run_contoh.font.size
        run_baru.font.bold = run_contoh.font.bold
        run_baru.font.italic = run_contoh.font.italic
    except Exception:
        pass


def main(argv):
    if len(argv) < 2 or len(argv) > 3:
        print('Pakai: python3 isi_nomor_toc.py MASUK [KELUAR]')
        return 2
    masuk = Path(argv[1])
    if len(argv) == 3:
        keluar = Path(argv[2])
    else:
        keluar = masuk.with_name(masuk.stem + '.bernomor' + masuk.suffix)
    if not masuk.exists():
        print(f'GAGAL: berkas tidak ada: {masuk}')
        return 2

    total = perender_halaman.hitung_halaman(str(masuk))
    if total is None:
        print('GAGAL: perender tidak tersedia (WORDCRAFT_CLI/PATH/docker hermes).')
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / 'buku.pdf'
        if not perender_halaman.render_pdf(str(masuk), str(pdf)):
            print('GAGAL: render PDF gagal.')
            return 2
        try:
            halaman = halaman_teks(pdf, total)
        except FileNotFoundError:
            print('GAGAL: pdftotext tidak ditemukan — di hermes pakai '
                  'PATH=/opt/data/services/pdftotext/bin:$PATH.')
            return 2
        toc_pages = span_toc(halaman)

        doc = Document(str(masuk))
        entri, sudah = paragraf_toc(doc)
        if entri is None:
            print('GAGAL: paragraf DAFTAR ISI tidak ditemukan di berkas.')
            return 2
        terisi, hilang = [], []
        for judul, p in entri:
            h = cari_halaman(kunci_dari_judul(judul), halaman, toc_pages)
            if h is None:
                hilang.append(judul)
                continue
            contoh = p.runs[0] if p.runs else None
            baru = p.add_run(str(h))
            if contoh is not None:
                _salin_font(baru, contoh)
            terisi.append((judul, h))
        doc.save(str(keluar))

    for judul, h in terisi:
        print(f'  TERISI: {judul} -> {h}')
    for judul, _ in sudah:
        print(f'  SUDAH: {judul} (dibiarkan)')
    if hilang:
        print('HILANG (tidak ditulis, periksa judulnya):')
        for judul in hilang:
            print(f'  - {judul}')
    print(f'RINGKAS ISI NOMOR TOC: {len(terisi)} terisi, '
          f'{len(sudah)} sudah, {len(hilang)} hilang -> {keluar}')
    return 1 if hilang else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
