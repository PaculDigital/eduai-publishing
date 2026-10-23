#!/usr/bin/env python3
"""Indeks buku referensi — Subjek + Nama, BER-NOMOR HALAMAN.

═══════════════════════════════════════════════════════════════════════════
KENAPA BERKAS INI ADA
═══════════════════════════════════════════════════════════════════════════
Skill `buku-referensi` (17 Okt 2026) menetapkan:
    "Indeks Subjek + Indeks Nama — WAJIB. Ini pembeda utama buku referensi."

Masalahnya: `add_indeks()` di `buku_umum_assembly.py` hanya menulis DAFTAR
ISTILAH tanpa nomor halaman, dan hanya dari glosarium:

    INDEKS
    digitalisasi
    platform

Itu belum layak disebut indeks. Indeks sejati memetakan ISTILAH → HALAMAN.

═══════════════════════════════════════════════════════════════════════════
CARA KERJANYA (2 LANGKAH — tidak bisa 1 langkah)
═══════════════════════════════════════════════════════════════════════════
python-docx TIDAK tahu nomor halaman (pagination itu urusan Word, bukan file).
Jadi WAJIB dua langkah:

  LANGKAH 1 (sebelum final)
      Tandai setiap kemunculan istilah di paragraf dengan BOOKMARK tersembunyi.
      → `tandai_istilah(doc, istilah)`

  LANGKAH 2 (setelah Word/LibreOffice menghitung halaman)
      Buka berkas .docx hasil, baca nomor halaman tiap bookmark via
      `page_number` dari LibreOffice/Word, lalu tulis daftar indeks.
      → `rakit_indeks(daftar_halaman)`

  ALTERNATIF tanpa Office (dipakai di sini):
      `hitung_halaman_perkiraan()` — menghitung dari aliran teks.
      CUKUP untuk buku digital & pratinjau, TIDAK untuk cetak.
      Untuk cetak WAJIB langkah 2 dengan Word/LibreOffice.

═══════════════════════════════════════════════════════════════════════════
ATURAN ENTRI (dari skill buku-referensi)
═══════════════════════════════════════════════════════════════════════════
  · Hanya istilah yang DIDEFINISIKAN atau DIBAHAS SUBSTANTIF — bukan setiap
    kemunculan kata. Istilah yang muncul 50× tapi lewat = tidak masuk indeks.
  · Istilah yang cuma muncul 1× biasanya tidak layak jadi entri.
  · Istilah asing dicetak miring di indeks (konsisten dengan isi buku).

═══════════════════════════════════════════════════════════════════════════
PEMAKAIAN
═══════════════════════════════════════════════════════════════════════════
    from indeks_referensi import kumpulkan_entri, tulis_indeks_subjek, tulis_indeks_nama

    # 1. kumpulkan dari naskah
    subjek, nama = kumpulkan_entri(teks_per_halaman, glosarium=GLOSARIUM)

    # 2. tulis ke docx
    tulis_indeks_subjek(doc, subjek)
    tulis_indeks_nama(doc, nama)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER


# ══════════════════════════════════════════════════════════════════════════
#  POLA NAMA — untuk Indeks Nama
# ══════════════════════════════════════════════════════════════════════════
#  ⚠️ Ini penangkap KASAR, bukan NER. Tujuan: menangkap "Nama (Tahun)" dan
#  "Nama & Nama (Tahun)" yang lazim di sitasi akademik.
#  Yang TIDAK tertangkap: nama tanpa tahun, nama di tengah kalimat.
#  ⇒ Hasil tetap perlu KURASI MANUAL (aturan skill: "kurasi manual setelah
#    auto-generate").
_RE_NamaTahun = re.compile(
    r'\b([A-Z][a-z]{2,}(?:\s+(?:&|dan)\s+[A-Z][a-z]{2,})?(?:\s+et\s+al\.?)?)'
    r'\s*\((\d{4})\)'
)

#  Kata yang sering muncul di awal kalimat & BUKAN nama orang.
_BUKAN_NAMA = {
    'Tahun', 'Pada', 'Dalam', 'Menurut', 'Sejak', 'Hingga', 'Namun', 'Selain',
    'Dengan', 'Untuk', 'Dari', 'Ketika', 'Setelah', 'Sebelum', 'Karena',
    'Berdasarkan', 'Tabel', 'Gambar', 'Bab', 'Sumber', 'Data', 'Hasil',
    'Penelitian', 'Teori', 'Konsep', 'Model', 'Undang', 'Peraturan',
    'Indonesia', 'Sementara', 'Adapun', 'Oleh', 'Antara', 'Melalui',
}


@dataclass
class Entri:
    """Satu entri indeks: teks + daftar halaman (urut, tanpa duplikat)."""
    teks: str
    halaman: set[int] = field(default_factory=set)
    asing: bool = False

    def tambah(self, nomor: int) -> None:
        self.halaman.add(nomor)

    @property
    def halaman_urut(self) -> list[int]:
        return sorted(self.halaman)

    @property
    def teks_halaman(self) -> str:
        """'12, 15, 20-22' — halaman berurutan digabung jadi rentang."""
        h = self.halaman_urut
        if not h:
            return ''
        hasil, mulai, sebelum = [], h[0], h[0]
        for n in h[1:]:
            if n == sebelum + 1:
                sebelum = n
                continue
            hasil.append(f'{mulai}' if mulai == sebelum else f'{mulai}-{sebelum}')
            mulai = sebelum = n
        hasil.append(f'{mulai}' if mulai == sebelum else f'{mulai}-{sebelum}')
        return ', '.join(hasil)


# ══════════════════════════════════════════════════════════════════════════
#  KUMPULKAN ENTRI DARI NASKAH
# ══════════════════════════════════════════════════════════════════════════
def _hitung_kemunculan(teks: str, istilah: str) -> int:
    """Hitung kemunculan istilah (batas kata, tanpa peduli besar-kecil huruf)."""
    pola = r'(?<!\w)' + re.escape(istilah) + r'(?!\w)'
    return len(re.findall(pola, teks, re.IGNORECASE))


def kumpulkan_entri(
    teks_per_halaman: dict[int, str],
    glosarium: dict[str, str] | None = None,
    min_muncul: int = 2,
    maks_halaman: int = 6,
) -> tuple[dict[str, Entri], dict[str, Entri]]:
    """Kumpulkan entri Indeks Subjek & Indeks Nama.

    Parameter
    ---------
    teks_per_halaman : {nomor_halaman: teks halaman itu}
        Nomor halaman HARUS nomor cetak (bukan indeks list).
    glosarium : istilah yang WAJIB masuk indeks apa pun frekuensinya
        (istilah yang didefinisikan penulis = layak dirujuk).
    min_muncul : istilah non-glosarium minimal muncul berapa kali.
        2 = ambang aman. Yang muncul 1× biasanya lewat, bukan dibahas.
    maks_halaman : kalau istilah muncul di LEBIH dari ini halaman, entri
        dibuang — tanda kata umum ("data", "sistem") bukan istilah khas buku.
        Set 0 untuk mematikan batas.

    Kembalikan
    ----------
    (subjek, nama) — dua dict {kunci_lower: Entri}
    """
    glosarium = glosarium or {}
    subjek: dict[str, Entri] = {}
    nama: dict[str, Entri] = {}

    #  ── 1. SUBJEK dari glosarium (selalu masuk, apa pun frekuensinya) ──
    for istilah in glosarium:
        subjek[istilah.lower()] = Entri(teks=istilah)
        if istilah != istilah.lower() or ' ' not in istilah:
            # istilah asing sering huruf kecil semua / frasa → miring
            subjek[istilah.lower()].asing = istilah.islower()

    #  ── 2. SUBJEK dari naskah (frekuensi cukup) ──
    for nomor, teks in teks_per_halaman.items():
        #  istilah glosarium
        for kunci, e in subjek.items():
            if _hitung_kemunculan(teks, e.teks):
                e.tambah(nomor)
        #  kata benda berulang yang BUKAN di glosarium
        kata = re.findall(r'\b[a-z]{5,}\b', teks.lower())
        for k in set(kata):
            if k in subjek:
                continue
            total = _hitung_kemunculan(teks, k)
            if total < min_muncul:
                continue
            subjek[k] = Entri(teks=k.capitalize())
            subjek[k].tambah(nomor)

    #  ── 3. NAMA dari pola "Nama (Tahun)" ──
    for nomor, teks in teks_per_halaman.items():
        for m in _RE_NamaTahun.finditer(teks):
            orang = m.group(1).strip()
            if orang in _BUKAN_NAMA:
                continue
            if len(orang) < 3:
                continue
            nama.setdefault(orang.lower(), Entri(teks=orang)).tambah(nomor)

    #  ── 4. SARING: buang yang tersebar terlalu luas (kata umum) ──
    #  ⚠️ ISTILAH GLOSARIUM DIKECUALIKAN dari saringan ini.
    #     Istilah yang didefinisikan penulis WAJIB bisa dirujuk pembaca, walau
    #     muncul di 30 halaman. Tanpa pengecualian ini, istilah pokok buku
    #     justru hilang dari indeks (bug 17 Okt 2026 — terukur lewat uji).
    def _saring(d: dict[str, Entri], kunci_kebal: set[str] | None = None
                ) -> dict[str, Entri]:
        kebal = kunci_kebal or set()
        hasil = {}
        for k, e in d.items():
            if not e.halaman:
                continue          # tidak muncul di naskah → tak ada gunanya
            if maks_halaman and k not in kebal and len(e.halaman) > maks_halaman:
                continue          # kata umum, bukan istilah khas buku ini
            hasil[k] = e
        return hasil

    kebal = {k.lower() for k in glosarium}
    return _saring(subjek, kebal), _saring(nama)


# ══════════════════════════════════════════════════════════════════════════
#  TULIS KE DOCX
# ══════════════════════════════════════════════════════════════════════════
def _tulis_blok(doc, judul: str, entri: dict[str, Entri],
                font_size: int = 11, page_break: bool = True) -> int:
    """Tulis satu blok indeks (subjek ATAU nama). Kembalikan jumlah entri."""
    from docx.shared import Pt as _Pt

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = _Pt(12)
    p.paragraph_format.space_after = _Pt(12)
    if page_break:
        p.paragraph_format.page_break_before = True
    r = p.add_run(judul)
    r.bold = True
    r.font.size = _Pt(16)

    if not entri:
        from docx.shared import Pt as _P
        kosong = doc.add_paragraph('(belum ada entri — isi setelah naskah selesai)')
        kosong.alignment = WD_ALIGN_PARAGRAPH.CENTER
        kosong.runs[0].italic = True
        kosong.runs[0].font.size = _P(10)
        return 0

    #  Urut abjad
    urut = sorted(entri.values(), key=lambda e: e.teks.lower())

    #  Kelompok per huruf awal (A, B, C, ...) — lazim di buku referensi
    huruf_kini = ''
    for e in urut:
        h = e.teks[0].upper()
        if h != huruf_kini:
            huruf_kini = h
            kepala = doc.add_paragraph()
            kepala.paragraph_format.space_before = _Pt(10)
            kepala.paragraph_format.space_after = _Pt(2)
            kr = kepala.add_run(h)
            kr.bold = True
            kr.font.size = _Pt(13)

        baris = doc.add_paragraph()
        pf = baris.paragraph_format
        pf.left_indent = Cm(0.8)
        pf.first_line_indent = Cm(-0.8)
        pf.space_after = _Pt(2)
        #  tab kanan + titik-titik penghubung → nomor halaman rata kanan
        pf.tab_stops.add_tab_stop(
            Cm(13.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

        r1 = baris.add_run(e.teks)
        r1.font.size = _Pt(font_size)
        r1.italic = bool(e.asing)
        r2 = baris.add_run('\t' + e.teks_halaman)
        r2.font.size = _Pt(font_size)

    return len(urut)


def tulis_indeks_subjek(doc, subjek: dict[str, Entri]) -> int:
    """Tulis INDEKS SUBJEK (dengan page break di depan)."""
    return _tulis_blok(doc, 'INDEKS SUBJEK', subjek, page_break=True)


def tulis_indeks_nama(doc, nama: dict[str, Entri]) -> int:
    """Tulis INDEKS NAMA (menyambung, tanpa page break)."""
    return _tulis_blok(doc, 'INDEKS NAMA', nama, page_break=False)


# ══════════════════════════════════════════════════════════════════════════
#  HITUNG HALAMAN — perkiraan (tanpa Word/LibreOffice)
# ══════════════════════════════════════════════════════════════════════════
def halaman_perkiraan(teks: str, baris_per_halaman: int = 30,
                      kata_per_baris: int = 12) -> int:
    """Perkiraan jumlah halaman satu blok teks.

    Default 30 baris × 12 kata ≈ 360 kata/halaman — cocok untuk B5, TNR 12pt,
    spasi 1,15.

    ⚠️ BATAS KEPERCAYAAN: ini PERKIRAAN. Untuk buku cetak, nomor halaman
    WAJIB diambil dari Word/LibreOffice setelah dokumen dirender. Jangan
    kirim ke percetakan dengan nomor hasil perkiraan.
    """
    jumlah_kata = len(teks.split())
    return max(1, round(jumlah_kata / (baris_per_halaman * kata_per_baris)))


def bagi_per_halaman(bab_per_num: dict[int, str], bab_awal: int = 1,
                     pembuka: int = 5) -> dict[int, str]:
    """Bagi naskah per bab jadi {nomor_halaman_cetak: teks}.

    `pembuka` = jumlah halaman sebelum BAB 1 (cover, ISBN, pengantar, daftar isi).

    ⚠️ Sama seperti `halaman_perkiraan`: ini perkiraan. Cukup untuk menakar
    isi indeks & pratinjau, BUKAN untuk nomor cetak final.
    """
    hasil: dict[int, str] = {}
    nomor = bab_awal + pembuka
    for _, teks in sorted(bab_per_num.items()):
        n = halaman_perkiraan(teks)
        #  bagi teks rata per halaman supaya istilah bisa dipetakan
        kata = teks.split()
        per = max(1, len(kata) // max(1, n))
        for i in range(n):
            potong = ' '.join(kata[i * per:(i + 1) * per])
            if potong:
                hasil[nomor] = potong
            nomor += 1
    return hasil


# ══════════════════════════════════════════════════════════════════════════
#  HALAMAN TERUKUR DARI RENDER (barang 7 RENCANA-BANGUN-SSOT, 23 Okt 2026)
#  Menggantikan perkiraan 360 kata/halaman untuk nomor CETAK: teks diambil
#  per halaman dari PDF hasil render (LibreOffice/Word), jadi nomor yang
#  tertulis di indeks adalah nomor yang benar-benar dilihat pembaca.
# ══════════════════════════════════════════════════════════════════════════
def halaman_dari_render(path_pdf):
    """Kembalikan list teks per halaman dari PDF render (indeks 0 = hlm 1)."""
    import subprocess
    r = subprocess.run(['pdftotext', '-layout', str(path_pdf), '-'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'pdftotext gagal: {r.stderr[:200]}')
    return r.stdout.split('\x0c')


def petakan_istilah_terukur(istilah, path_pdf):
    """{istilah: [nomor halaman, ...]} diukur dari render — BUKAN perkiraan.

    Inilah pengganti jalur bagi_per_halaman() untuk nomor indeks final.
    bagi_per_halaman()/halaman_perkiraan() tetap ada untuk pratinjau kasar
    dan DILARANG dipakai untuk nomor cetak.
    """
    halaman = halaman_dari_render(path_pdf)
    hasil = {}
    for kata in istilah:
        pola = re.compile(rf'\b{re.escape(kata)}\b', re.I)
        hasil[kata] = [i + 1 for i, teks in enumerate(halaman) if pola.search(teks)]
    return hasil
