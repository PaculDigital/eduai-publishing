"""Standar penulisan EduAi — aturan format dari pedoman yang diunggah.

SUMBER (bacaan utuh Wulan 26Sep26, teks + vision + koordinat):
  PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025
  (Universitas Pelita Bangsa) — 105 halaman, terbaca mesin.
  Ringkasan lengkap: ATURAN_FORMAT_PEDOMAN_26SEP2026.md +
                     ATURAN_SITASI_PEDOMAN_26SEP2026.md

DUA LAPIS (usulan Bos, ACC 26Sep26):
  1. ATURAN_BAKU  → default EduAi untuk SEMUA user (tanpa panduan sendiri)
  2. panduan_user → user unggah panduan kampusnya sendiri (per naskah,
                     disimpan di profil_dokumen.panduan_json) → MENANG
                     atas aturan baku.

Cara pakai di prompt AI: `ringkas_untuk_ai(profil)` → blok teks singkat
disuntik SEBELUM naskah (pola sama dengan catatan_konsistensi, ai.py:2052).

HARGA: pembacaan panduan user = Rp 0 (ekstraksi teks biasa, TANPA AI).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────
# ATURAN BAKU — persis dari pedoman (angka, jangan dikarang)
# ─────────────────────────────────────────────────────────────────
ATURAN_BAKU: dict[str, Any] = {
    "sumber": "Pedoman Penulisan Skripsi Prodi Manajemen, Edisi Revisi 2025",
    "kertas": {"ukuran": "A4 (297 x 210 mm)", "bahan": "HVS 80 gr/m2",
               "cetak": "tidak bolak-balik"},
    "margin_cm": {"atas": 4, "bawah": 3, "kiri": 4, "kanan": 3},
    "huruf": {"isi": "Times New Roman 12", "judul_sampul": "Times New Roman 14",
              "isi_sampul": "Times New Roman 16", "judul_bab": "Times New Roman 12"},
    "spasi": {"isi_paragraf": 1.5, "judul_tabel_gambar": 1.0,
              "kutipan_blok": 1.0, "bagian_awal": 1.0},
    "paragraf": {
        "perataan": "rata kiri kanan (justified)",
        "alinea_pertama": "rata kiri, TIDAK menjorok (di bawah judul)",
        "alinea_berikut": "menjorok 1 tab (ketukan ke-5) dari tepi kiri",
        "perincian": "pakai nomor angka/huruf; DILARANG bulir (-) atau titik tebal",
    },
    "penomoran_halaman": {
        "bagian_awal": "romawi kecil (i, ii, iii) sampai intisari",
        "bab_i_s_d_terakhir": "angka arab (1, 2, 3)",
        "letak_umum": "kanan atas",
        "letak_halaman_judul_bab": "tengah bawah",
        "jarak": "3 cm dari tepi kanan, 1,5 cm dari tepi atas/bawah",
    },
    "judul_bab": {"posisi": "tengah", "huruf": "tebal kapital",
                  "titik": "tanpa titik", "jarak_atas": "4 cm dari tepi atas"},
    "judul_subbab": {"posisi": "kiri", "huruf": "tebal", "gaya": "headline style",
                     "titik": "tanpa titik"},
    "judul_anaksubbab": {"posisi": "kiri", "huruf": "tebal",
                         "gaya": "sentence style", "titik": "tanpa titik"},
    "peringkat_penomoran": ["1: BAB, kapital, tengah", "2: 3.1 (angka titik)",
                            "3: 3.2.1 (angka titik)", "4: a. b. c. (huruf kecil titik)",
                            "5: (1) (2) kapital-kecil tanpa titik"],
    "tabel": {
        "penomoran": "rangkap dua: nomor bab . nomor tabel (Tabel 2.5)",
        "judul": "DI ATAS tabel, dari tepi kiri, tanpa titik, TIDAK ditebalkan",
        "posisi": "simetris di tengah",
        "garis": "hanya horizontal (atas kepala, bawah kepala, penutup); tanpa garis tegak",
        "kepala": "nama kolom ditebalkan; kolom angka rata kanan; angka pemisah titik",
        "sumber": "baris 'Sumber:' di bawah garis penutup, rata kiri",
        "larangan": "DILARANG copy-paste output SPSS → wajib diketik ulang; "
                    "variabel singkatan diganti nama mudah dibaca",
    },
    "gambar": {
        "penomoran": "rangkap dua (Gambar 4.3); grafik/bagan/foto/peta SATU penomoran",
        "judul": "DI BAWAH gambar, RATA TENGAH, "
                 "tanpa titik, TIDAK ditebalkan",
        "sumber": "baris 'Sumber:' di bawah judul gambar",
        "larangan": "gambar TIDAK BOLEH dipenggal (pindah halaman)",
        "sifat": "self-contained + ada penjelasan memadai",
    },
    "bahasa": {
        "pasif": "WAJIB bentuk pasif; DILARANG saya/aku/kita (kata pengantar: "
                 "'saya' diganti 'penulis')",
        "dilarang": ["kata penghubung (sehingga/sedangkan) di awal kalimat",
                     "'pada' di depan subjek",
                     "'dimana'/'dari' dipakai seperti where/of Inggris",
                     "salah bedakan awalan ke-/di- vs kata depan ke/di"],
        "istilah_asing": "cetak miring + dijelaskan artinya",
        "ejaan": "PUEBI (Permendikbud 50/2015); kosakata KBBI; "
                 "desimal pakai KOMA (50,5); bilangan di awal kalimat dieja",
    },
    "sitasi": {
        "bentuk": "nama akhir + tahun dalam kurung; >2 penulis → dkk (et al.)",
        "kutipan_pendek": "<40 kata: tanda kutip, terpadu, (Nama, tahun:halaman)",
        "kutipan_blok": ">=40 kata: tanpa tanda kutip, menjorok 1,2 cm dua sisi, "
                        "spasi tunggal, nomor halaman wajib",
        "tidak_langsung": "tanpa tanda kutip, terpadu; nomor halaman sangat dianjurkan",
        "daftar_pustaka": "hanya yang dikutip; nama akhir dulu tanpa gelar; "
                          "judul buku & nama jurnal miring; hanging indent",
    },
    "sistematika": {
        "awal": ["Sampul", "Judul", "Persetujuan", "Pengesahan", "Persembahan & Motto",
                 "Pernyataan Keaslian", "Kata Pengantar", "Daftar Isi", "Daftar Tabel",
                 "Daftar Gambar", "Daftar Lampiran", "Abstract", "Abstrak"],
        "inti": ["BAB I PENDAHULUAN (1.1-1.5)", "BAB II TINJAUAN PUSTAKA (2.1-2.3)",
                 "BAB III METODE PENELITIAN (3.1-3.5)",
                 "BAB IV HASIL DAN PEMBAHASAN (4.1-4.2)", "BAB V PENUTUP (5.1-5.2)"],
        "akhir": ["Daftar pustaka", "Lampiran-lampiran", "Riwayat Hidup"],
    },
    "jumlah_halaman": {"total_minimal": 50, "per_bab": {
        "I": 6, "II": 14, "III": 10, "IV": 17, "V": 3}},
}

# Blok yang disuntik ke prompt — sengaja PADAT (hemat token).
_TEKS_BAKU = """[STANDAR PENULISAN — WAJIB IKUTI]
Kertas A4; margin atas 4 / bawah 3 / kiri 4 / kanan 3 cm; isi TNR 12 spasi 1,5 justified.
Paragraf: alinea pertama rata kiri (tanpa menjorok); alinea berikut menjorok 1 tab.
Judul BAB: tengah, tebal kapital, tanpa titik, 4 cm dari tepi atas. Sub-bab: kiri, tebal.
Judul anak sub-bab: kiri, tebal, gaya kalimat (hanya kata pertama kapital).
Tabel: nomor bab.nomor (Tabel 2.5); judul DI ATAS, rata kiri, TIDAK tebal, tanpa titik;
garis hanya horizontal; kepala kolom tebal; angka rata kanan; "Sumber:" di bawah rata kiri;
DILARANG copy-paste output SPSS (wajib diketik ulang).
Gambar/grafik: nomor bab.nomor; judul DI BAWAH, RATA TENGAH, tidak tebal; "Sumber:" di
bawah judul; gambar tidak boleh dipenggal.
Nomor halaman: bagian awal romawi kecil; Bab I dst angka arab; umum kanan atas; halaman
judul bab tengah bawah.
Bahasa: WAJIB pasif, dilarang saya/aku/kita; tanpa "sehingga/sedangkan" di awal kalimat;
istilah asing miring; desimal pakai koma.
Sitasi: (Nama akhir, tahun:halaman); >2 penulis → dkk; kutipan >=40 kata = blok
(tanpa tanda kutip, menjorok 1,2 cm dua sisi, spasi tunggal, halaman wajib);
daftar pustaka hanya yang dikutip, judul buku & nama jurnal miring, hanging indent."""


def ringkas_untuk_ai(panduan: dict[str, Any] | None = None) -> str:
    """Blok aturan format untuk disuntik ke prompt AI.

    `panduan` = hasil ekstraksi panduan user (baca_panduan_berkas).
    Kosong/None → pakai ATURAN_BAKU (default EduAi).
    Kalau user punya panduan sendiri, baris kuncinya MENANG atas baku
    (isian panduan lebih spesifik kampus, jadi dipakai apa adanya).
    """
    if not panduan:
        return _TEKS_BAKU
    # Gandakan aturan baku, timpa dengan milik user per kunci.
    gabung = dict(ATURAN_BAKU)
    for kunci, nilai in panduan.items():
        if isinstance(nilai, dict) and isinstance(gabung.get(kunci), dict):
            gabung[kunci] = {**gabung[kunci], **nilai}
        else:
            gabung[kunci] = nilai
    blok = ["[STANDAR PENULISAN — WAJIB IKUTI]",
            "(dari panduan penulisan yang diunggah user — menang atas aturan baku)"]
    for bagian in ("kertas", "margin_cm", "huruf", "spasi", "paragraf"):
        if bagian in gabung:
            blok.append(f"{bagian}: {gabung[bagian]}")
    for bagian in ("penomoran_halaman", "judul_bab", "judul_subbab", "tabel",
                   "gambar", "bahasa", "sitasi"):
        if bagian in gabung:
            blok.append(f"{bagian}: {gabung[bagian]}")
    return "\n".join(blok)


# ─────────────────────────────────────────────────────────────────
# BACA PANDUAN USER (tanpa AI — ekstraksi teks biasa, Rp 0)
# ─────────────────────────────────────────────────────────────────
_POLA_MARGIN = re.compile(
    r"(?:tepi\s+(atas|bawah|kiri|kanan)|margin\s+(atas|bawah|kiri|kanan))"
    r"[^\d]{0,25}(\d+[,.]?\d*)\s*cm", re.I)
_POLA_SPASI = re.compile(r"spasi\s*(\d+[,.]?\d*)", re.I)
_POLA_HURUF = re.compile(
    r"(times\s+new\s+roman|arial|calibri|georgia|cambria)"
    r"[^\n]{0,20}?(\d{2})\s*(?:pt|poin)?", re.I)
_POLA_KERTAS = re.compile(r"\b(A4|A5|letter|f4|folio)\b", re.I)


def baca_panduan_berkas(jalur: str | Path) -> dict[str, Any]:
    """Ekstrak aturan format dari PDF/DOCX panduan penulisan (TANPA AI).

    Balasan dict SEBAGIAN — hanya bagian yang benar-benar terbaca.
    Bagian yang tidak terdeteksi TIDAK ditulis (jangan mengarang).
    """
    jalur = Path(jalur)
    teks = ""
    if jalur.suffix.lower() == ".pdf":
        # fitz hanya ada di venv pengembangan; produksi memakai pypdf
        # (pure python, tanpa kompilasi) — dua-duanya TANPA AI.
        try:
            import fitz  # type: ignore
            with fitz.open(jalur) as d:
                teks = "\n".join(p.get_text() for p in d)
        except Exception:                                    # noqa: BLE001
            teks = ""
        if not teks.strip():
            try:
                from pypdf import PdfReader
                teks = "\n".join((p.extract_text() or "")
                                 for p in PdfReader(str(jalur)).pages)
            except Exception:                                # noqa: BLE001
                teks = ""
    elif jalur.suffix.lower() in (".docx", ".doc"):
        try:
            import zipfile
            with zipfile.ZipFile(jalur) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
            teks = re.sub(r"<[^>]+>", " ", xml)
        except Exception:                                    # noqa: BLE001
            teks = ""
    teks = re.sub(r"[ \t]+", " ", teks)

    hasil: dict[str, Any] = {"sumber": jalur.name}
    if not teks.strip():
        hasil["catatan"] = "teks tidak terbaca (mungkin scan/gambar)"
        return hasil

    # margin: "tepi atas: 4 cm" / "margin kiri 4 cm"
    margin: dict[str, Any] = {}
    for m in _POLA_MARGIN.finditer(teks):
        sisi = (m.group(1) or m.group(2) or "").lower()
        if sisi and sisi not in margin:
            margin[sisi] = float(m.group(3).replace(",", "."))
    if margin:
        hasil["margin_cm"] = margin

    m = _POLA_KERTAS.search(teks)
    if m:
        hasil["kertas"] = {"ukuran": m.group(1).upper()}
    huruf = _POLA_HURUF.findall(teks[:20000])
    if huruf:
        # ambil pasangan paling sering muncul
        pola: dict[tuple[str, str], int] = {}
        for nama, uk in huruf:
            k = (nama.lower(), uk)
            pola[k] = pola.get(k, 0) + 1
        (nama, uk), jml = max(pola.items(), key=lambda kv: kv[1])
        hasil["huruf"] = {"isi": f"{nama.title()} {uk}", "jumlah_sebut": jml}
    spasi = _POLA_SPASI.findall(teks[:20000])
    if spasi:
        pola_s: dict[str, int] = {}
        for s in spasi:
            pola_s[s.replace(",", ".")] = pola_s.get(s.replace(",", "."), 0) + 1
        s_terbanyak = max(pola_s, key=lambda k: pola_s[k])
        hasil["spasi"] = {"isi_paragraf": float(s_terbanyak)}

    jumlah = re.search(r"minimal\s+(\d+)\s+halaman", teks, re.I)
    if jumlah:
        hasil["jumlah_halaman"] = {"total_minimal": int(jumlah.group(1))}
    hasil["panjang_teks"] = len(teks)
    return hasil


def muat_panduan(panduan_json: str | None) -> dict[str, Any] | None:
    """Baca kolom profil_dokumen.panduan_json → dict, atau None kalau kosong."""
    if not panduan_json or not panduan_json.strip():
        return None
    try:
        data = json.loads(panduan_json)
        return data if isinstance(data, dict) and data else None
    except (json.JSONDecodeError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────
# BAGIAN 2 — PEMERIKSA FORMAT (cek format pedoman, 19 Nov 2026)
# ─────────────────────────────────────────────────────────────────
# Gas Boss 19 Nov 2026 17:09 WIB (fitur 2 dari 10). Rancangan:
# RENCANA_FORMAT.md. Melengkapi modul ini (aturan ATURAN_BAKU sudah ada),
# BUKAN modul baru. Deterministik, TANPA LLM, GRATIS (0 token).
#
# TEMUAN SONDE fid 81 (sebelum bangun — jangan dihapus, ini pagar):
# - Font/ukuran/spasi/rata TIDAK tertulis di run. Semuanya None; font TNR 12
#   tertulis di DEFAULT DOKUMEN (docDefaults). Pemeriksa WAJIB menyelesaikan
#   rantai: run → gaya paragraf → default dokumen. Tanpa ini semua terbaca
#   None dan pemeriksa salah tandai.
# - Keterangan tabel/gambar asli dicari dari POSISI (sebelum tabel / sesudah
#   gambar), BUKAN dari teks saja — entri Daftar Tabel/Gambar ikut terbaca
#   sebagai 'Tabel 1. 1 ...\t26' dan harus dikecualikan (ada tab + nomor halaman).
# - Nomor tertulis '1. 1' (spasi sesudah titik); pemeriksa menormalkan spasi
#   saat membaca nomor ('1. 1' → '1.1'), tidak ditandai.
# - Batas jujur v1: jumlah halaman tidak diperiksa (python-docx tidak bisa
#   menghitung halaman); isi tabel dan kutipan blok ditunda ke v2.

# Delapan pemeriksaan v1 (id, label tampil).
PEMERIKSAAN_FORMAT = [
    ('margin', 'Margin'),
    ('huruf', 'Huruf isi'),
    ('spasi', 'Spasi isi'),
    ('perataan', 'Perataan isi'),
    ('judul_bab', 'Judul bab'),
    ('tabel', 'Keterangan tabel'),
    ('gambar', 'Keterangan gambar'),
    ('nomor_halaman', 'Nomor halaman'),
]

VONIS_SAH_FORMAT = ('lulus', 'tidak', 'ragu')

# Ambang dominan: bila ≥90% paragraf isi cocok, lulus (sisanya pengecualian
# yang sah, mis. kutipan blok atau keterangan di dalam isi).
AMBANG_DOMINAN_FORMAT = 0.9

# Jendela pencarian keterangan: keterangan tabel paling jauh 5 paragraf
# sebelum tabelnya; keterangan gambar paling jauh 3 paragraf tak-kosong
# sesudah gambarnya. Lebih jauh dari itu dianggap tidak ada (bukan pasangan).
JENDELA_TABEL_FORMAT = 5
JENDELA_GAMBAR_FORMAT = 3

# Gaya paragraf isi (yang dinilai huruf/spasi/perataan). Judul, keterangan,
# dan daftar isi memakai gaya lain dan dinilai oleh pemeriksanya sendiri.
GAYA_ISI_FORMAT = ('Normal', 'List Paragraph')

# Panjang minimal paragraf isi (karakter). Keterangan tabel/gambar, judul,
# dan baris 'Sumber:' semuanya pendek; paragraf isi asli panjang. Ambang ini
# memisahkan keduanya (sonde fid 81: ambang 80 memberi 180 paragraf isi,
# semuanya rata kiri kanan dan spasi 1,5).
PANJANG_MINIMAL_ISI_FORMAT = 80

_POLA_BAB_FORMAT = re.compile(r'^BAB\s+([IVXLC]+)\b', re.I)
_POLA_TABEL_FORMAT = re.compile(r'^Tabel\s+(\d+)\s*\.\s*(\d+)\b', re.I)
_POLA_GAMBAR_FORMAT = re.compile(r'^Gambar\s+(\d+)\s*\.\s*(\d+)\b', re.I)
_POLA_NOMOR_GANDA_FORMAT = re.compile(r'^\d+\s*\.\s*\d+$')

# Kata sesudah nomor yang menandakan RUJUKAN di dalam kalimat, bukan keterangan.
# Contoh rujukan: 'Tabel 4.1 menunjukkan bahwa...', 'Gambar 4.1 memperlihatkan...'.
# Keterangan asli adalah frasa benda ('Tabel 4.1 Hasil Uji Validitas...').
_KATA_RUJUKAN_FORMAT = frozenset([
    'menunjukkan', 'memperlihatkan', 'menampilkan', 'menjelaskan',
    'menggambarkan', 'menyajikan', 'mengindikasikan', 'dapat', 'terlihat',
    'pada', 'di', 'berikut', 'tersebut', 'ini', 'itu', 'bahwa',
])


def _adalah_keterangan(teks_bersih: str, pola) -> Any | None:
    """Cocokkan pola keterangan (Tabel/Gambar N.M). Balasan match atau None.

    Paragraf yang diawali nomor lalu kata rujukan ('menunjukkan', 'bahwa', ...)
    adalah kalimat isi yang MERUJUK tabel/gambar, bukan keterangan — ditolak.
    """
    m = pola.match((teks_bersih or '').strip())
    if not m:
        return None
    sisa = (teks_bersih or '').strip()[m.end():].strip()
    kata = re.split(r'[\s,.;:]+', sisa, maxsplit=1)[0].lower() if sisa else ''
    if kata in _KATA_RUJUKAN_FORMAT:
        return None
    return m


def _normal_nama_huruf(nama: str | None) -> str:
    """Normalkan nama huruf untuk dibandingkan ('Times New Roman' == 'times new roman')."""
    return re.sub(r'\s+', ' ', (nama or '').strip()).lower()


def _default_dokumen(doc) -> dict[str, Any]:
    """Baca default dokumen (docDefaults): huruf, ukuran, spasi.

    Inilah sumber nilai bila run dan gaya tidak menulis apa pun (kasus fid 81:
    semua run None, font TNR 12 hanya ada di sini). Balasan:
    {'huruf': str|None, 'ukuran_pt': float|None, 'spasi': float|None}.
    """
    hasil: dict[str, Any] = {'huruf': None, 'ukuran_pt': None, 'spasi': None}
    try:
        styles_el = doc.styles.element
    except Exception:                                          # noqa: BLE001
        return hasil
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    try:
        defaults = styles_el.find('w:docDefaults', ns)
        if defaults is None:
            return hasil
        rpr = defaults.find('w:rPrDefault/w:rPr', ns)
        if rpr is not None:
            fonts = rpr.find('w:rFonts', ns)
            if fonts is not None:
                hasil['huruf'] = (fonts.get('{%s}ascii' % ns['w'])
                                  or fonts.get('{%s}hAnsi' % ns['w']))
            sz = rpr.find('w:sz', ns)
            if sz is not None and sz.get('{%s}val' % ns['w']):
                try:
                    hasil['ukuran_pt'] = float(sz.get('{%s}val' % ns['w'])) / 2.0
                except (TypeError, ValueError):
                    pass
        ppr = defaults.find('w:pPrDefault/w:pPr', ns)
        if ppr is not None:
            sp = ppr.find('w:spacing', ns)
            if sp is not None:
                garis = sp.get('{%s}line' % ns['w'])
                aturan = sp.get('{%s}lineRule' % ns['w'])
                if garis and aturan == 'auto':
                    try:
                        hasil['spasi'] = float(garis) / 240.0
                    except (TypeError, ValueError):
                        pass
    except Exception:                                          # noqa: BLE001
        return hasil
    return hasil


def _spasi_ke_angka(nilai) -> float | None:
    """Ubah spasi python-docx jadi angka (kelipatan). Spasi tetap (Length)
    dan None → None (bukan kelipatan, tidak bisa dibandingkan dengan 1,5)."""
    if nilai is None:
        return None
    if isinstance(nilai, float):
        return nilai
    if isinstance(nilai, int):
        return float(nilai)
    return None


def _font_efektif(doc, paragraf, default: dict) -> tuple[str | None, float | None]:
    """Huruf + ukuran efektif satu paragraf (run → gaya → default dokumen)."""
    nama = None
    ukuran = None
    for r in (paragraf.runs or []):
        if not (r.text or '').strip():
            continue
        try:
            nama = r.font.name or None
        except Exception:                                      # noqa: BLE001
            nama = None
        try:
            ukuran = r.font.size.pt if r.font.size is not None else None
        except Exception:                                      # noqa: BLE001
            ukuran = None
        break
    if nama is None:
        try:
            nama = paragraf.style.font.name or None
        except Exception:                                      # noqa: BLE001
            nama = None
    if ukuran is None:
        try:
            ukuran = (paragraf.style.font.size.pt
                      if paragraf.style.font.size is not None else None)
        except Exception:                                      # noqa: BLE001
            ukuran = None
    if nama is None:
        nama = default.get('huruf')
    if ukuran is None:
        ukuran = default.get('ukuran_pt')
    return nama, ukuran


def _spasi_efektif(doc, paragraf, default: dict) -> float | None:
    """Spasi efektif satu paragraf (paragraf → gaya → default dokumen)."""
    try:
        nilai = _spasi_ke_angka(paragraf.paragraph_format.line_spacing)
    except Exception:                                          # noqa: BLE001
        nilai = None
    if nilai is None:
        try:
            nilai = _spasi_ke_angka(
                paragraf.style.paragraph_format.line_spacing)
        except Exception:                                      # noqa: BLE001
            nilai = None
    if nilai is None:
        nilai = default.get('spasi')
    return nilai


def _rata_efektif(doc, paragraf) -> str | None:
    """Perataan efektif satu paragraf (paragraf → gaya). None = rata kiri
    (bawaan Word). Balasan nama enum python-docx ('JUSTIFY', 'CENTER', ...)."""
    try:
        rata = paragraf.paragraph_format.alignment
    except Exception:                                          # noqa: BLE001
        rata = None
    if rata is None:
        try:
            rata = paragraf.style.paragraph_format.alignment
        except Exception:                                      # noqa: BLE001
            rata = None
    if rata is None:
        return None
    return str(rata).split(' ')[0]


def _tebal_efektif(doc, paragraf) -> bool:
    """True bila paragraf ini tebal (run pertama berteks → gaya)."""
    for r in (paragraf.runs or []):
        if not (r.text or '').strip():
            continue
        try:
            if r.bold is not None:
                return bool(r.bold)
        except Exception:                                      # noqa: BLE001
            pass
        break
    try:
        if paragraf.style.font.bold is not None:
            return bool(paragraf.style.font.bold)
    except Exception:                                          # noqa: BLE001
        pass
    return False


def _teks_bersih(paragraf) -> str:
    """Teks paragraf tanpa nomor halaman daftar isi (tab + angka di ujung)."""
    teks = (paragraf.text or '').strip()
    teks = re.sub(r'\t+\d+\s*$', '', teks).strip()
    return teks


def _ada_tab_nomor(teks: str) -> bool:
    """True bila teks mengandung tab + angka (ciri entri Daftar Isi/Tabel/Gambar)."""
    return bool(re.search(r'\t+\d+\s*$', teks or ''))


def baca_docx_format(jalur: str | Path) -> dict[str, Any]:
    """Baca .docx jadi model kecil untuk pemeriksa format.

    Balasan:
      {'seksi': [{'margin_cm': {...}|None per sisi, 'pgnum_fmt': str|None}],
       'elemen': [('p', info) | ('tbl', None), ...] berurutan,
       'default': {'huruf', 'ukuran_pt', 'spasi'}}
    info paragraf: {'teks', 'teks_bersih', 'gaya', 'font', 'ukuran_pt',
    'spasi', 'rata', 'tebal', 'ada_gambar'}.
    Nilai None berarti 'tidak tertulis di berkas' (bukan nol).
    """
    from docx import Document as _Doc
    from docx.text.paragraph import Paragraph as _Par
    from docx.table import Table as _Tab

    doc = _Doc(str(jalur))
    default = _default_dokumen(doc)

    seksi = []
    for s in doc.sections:
        margin = {}
        for sisi, ambil in (('atas', s.top_margin), ('bawah', s.bottom_margin),
                            ('kiri', s.left_margin), ('kanan', s.right_margin)):
            margin[sisi] = (round(ambil.cm, 1) if ambil is not None else None)
        fmt = None
        try:
            sectPr = s._sectPr
            for el in sectPr.iter():
                if el.tag.endswith('}pgNumType'):
                    fmt = el.get('{http://schemas.openxmlformats.org/'
                                 'wordprocessingml/2006/main}fmt')
                    break
        except Exception:                                      # noqa: BLE001
            fmt = None
        seksi.append({'margin_cm': margin, 'pgnum_fmt': fmt})

    elemen: list[tuple[str, Any]] = []
    for anak in doc.element.body.iterchildren():
        tag = anak.tag.split('}')[-1]
        if tag == 'p':
            p = _Par(anak, doc)
            teks = p.text or ''
            font, ukuran = _font_efektif(doc, p, default)
            ada_gambar = False
            for r in (p.runs or []):
                try:
                    if r._element.xpath('.//w:drawing'):
                        ada_gambar = True
                        break
                except Exception:                              # noqa: BLE001
                    continue
            elemen.append(('p', {
                'teks': teks,
                'teks_bersih': _teks_bersih(p),
                'gaya': (p.style.name if p.style is not None else ''),
                'font': font,
                'ukuran_pt': ukuran,
                'spasi': _spasi_efektif(doc, p, default),
                'rata': _rata_efektif(doc, p),
                'tebal': _tebal_efektif(doc, p),
                'ada_gambar': ada_gambar,
            }))
        elif tag == 'tbl':
            elemen.append(('tbl', None))
    return {'seksi': seksi, 'elemen': elemen, 'default': default}


def _adalah_judul(info: dict) -> bool:
    """True bila paragraf ini tampak seperti judul (gaya Heading atau rata
    tengah). Dipakai untuk membedakan judul bab asli dari entri Daftar Isi
    dan dari daftar Sistematika (keduanya Normal, rata kiri, bukan Heading).
    """
    return (str(info['gaya'] or '').startswith('Heading')
            or (info['rata'] or '') == 'CENTER')


def _batas_isi(elemen: list) -> tuple[int, int]:
    """Batas paragraf isi: dari judul bab pertama sampai 'DAFTAR PUSTAKA'.

    Balasan (awal, akhir) sebagai indeks ke daftar paragraf (bukan elemen).
    Judul dicari dengan _adalah_judul supaya entri Daftar Isi (Normal,
    rata kiri) tidak dipakai sebagai batas. Bila tidak ada judul bab,
    (0, jumlah paragraf) — seluruh naskah dinilai.
    """
    paragraf_idx = [i for i, (k, _) in enumerate(elemen) if k == 'p']
    awal = 0
    akhir = len(paragraf_idx)
    posisi_bab = None
    for pos, ei in enumerate(paragraf_idx):
        info = elemen[ei][1]
        if (_POLA_BAB_FORMAT.match(info['teks_bersih'] or '')
                and _adalah_judul(info)):
            posisi_bab = pos
            break
    if posisi_bab is not None:
        awal = posisi_bab
        for pos in range(posisi_bab + 1, len(paragraf_idx)):
            info = elemen[paragraf_idx[pos]][1]
            bersih = re.sub(r'\s+', ' ', (info['teks_bersih'] or '')).strip().upper()
            if bersih in ('DAFTAR PUSTAKA', 'DAFTAR  PUSTAKA') and _adalah_judul(info):
                akhir = pos
                break
    return awal, akhir


def _temuan(cek_id: str, vonis: str, alasan: str, lokasi: str = '') -> dict:
    """Satu baris temuan (pola konsistensi_bab)."""
    label = dict(PEMERIKSAAN_FORMAT).get(cek_id, cek_id)
    return {'id': cek_id, 'label': label, 'vonis': vonis,
            'alasan': alasan, 'lokasi': lokasi}


def _cek_margin(model: dict, aturan: dict) -> dict:
    """Margin tiap seksi harus 4/3/4/3 cm (dari ATURAN_BAKU)."""
    target = (aturan.get('margin_cm') or ATURAN_BAKU['margin_cm'])
    for i, s in enumerate(model['seksi']):
        for sisi in ('atas', 'bawah', 'kiri', 'kanan'):
            nilai = (s['margin_cm'] or {}).get(sisi)
            harap = target.get(sisi)
            if nilai is None or harap is None:
                continue
            if abs(float(nilai) - float(harap)) > 0.1:
                return _temuan(
                    'margin', 'tidak',
                    f'Margin {sisi} seksi {i + 1} {nilai} cm, '
                    f'seharusnya {harap} cm.',
                    f'Seksi {i + 1}')
    for i, s in enumerate(model['seksi']):
        if any(v is None for v in (s['margin_cm'] or {}).values()):
            return _temuan(
                'margin', 'ragu',
                f'Margin seksi {i + 1} tidak tertulis di berkas, '
                f'kemungkinan memakai bawaan 2,54 cm. Perlu diperiksa.',
                f'Seksi {i + 1}')
    return _temuan('margin', 'lulus',
                   'Margin semua seksi 4/3/4/3 cm.')


def _cek_dominan(model: dict, aturan: dict, cek_id: str) -> dict:
    """Pemeriksa dominan untuk huruf/spasi/perataan isi.

    Hanya paragraf isi (gaya Normal/List Paragraph) di antara judul bab
    pertama dan Daftar Pustaka. Bila ≥90% cocok → lulus.
    """
    elemen = model['elemen']
    awal, akhir = _batas_isi(elemen)
    paragraf_idx = [i for i, (k, _) in enumerate(elemen) if k == 'p']
    isi = []
    for pos in range(awal, akhir):
        info = elemen[paragraf_idx[pos]][1]
        teks = (info['teks_bersih'] or '').strip()
        if len(teks) < PANJANG_MINIMAL_ISI_FORMAT:
            continue
        if info['gaya'] not in GAYA_ISI_FORMAT:
            continue
        isi.append(info)
    if not isi:
        label = dict(PEMERIKSAAN_FORMAT).get(cek_id, cek_id)
        return _temuan(cek_id, 'ragu',
                       f'Tidak ada paragraf isi yang bisa dinilai untuk {label}.')
    if cek_id == 'huruf':
        harap_nama = _normal_nama_huruf(
            ((aturan.get('huruf') or {}).get('isi') or 'Times New Roman 12'))
        harap_nama = harap_nama.replace(' 12', '').strip()
        cocok = sum(
            1 for info in isi
            if _normal_nama_huruf(info['font']) == harap_nama
            and info['ukuran_pt'] is not None
            and abs(float(info['ukuran_pt']) - 12.0) < 0.5)
        if cocok / len(isi) >= AMBANG_DOMINAN_FORMAT:
            return _temuan('huruf', 'lulus',
                           f'Huruf isi Times New Roman 12 '
                           f'({cocok} dari {len(isi)} paragraf).')
        dominan: dict[tuple[str, Any], int] = {}
        for info in isi:
            k = (_normal_nama_huruf(info['font']) or 'tidak tertulis',
                 info['ukuran_pt'])
            dominan[k] = dominan.get(k, 0) + 1
        (nm, uk), jml = max(dominan.items(), key=lambda kv: kv[1])
        uk_teks = f'{uk} pt' if uk is not None else 'tanpa ukuran'
        return _temuan(
            'huruf', 'tidak',
            f'Huruf yang paling banyak dipakai: {nm or "tidak tertulis"} '
            f'{uk_teks} ({jml} dari {len(isi)} paragraf). '
            f'Seharusnya Times New Roman 12.')
    if cek_id == 'spasi':
        cocok = sum(1 for info in isi
                    if info['spasi'] is not None
                    and abs(float(info['spasi']) - 1.5) < 0.05)
        if cocok / len(isi) >= AMBANG_DOMINAN_FORMAT:
            return _temuan('spasi', 'lulus',
                           f'Spasi isi 1,5 ({cocok} dari {len(isi)} paragraf).')
        dominan_s: dict[str, int] = {}
        for info in isi:
            k = (f"{info['spasi']}" if info['spasi'] is not None
                 else 'tidak tertulis')
            dominan_s[k] = dominan_s.get(k, 0) + 1
        (nm, jml) = max(dominan_s.items(), key=lambda kv: kv[1])
        return _temuan(
            'spasi', 'tidak',
            f'Spasi yang paling banyak dipakai: {nm} '
            f'({jml} dari {len(isi)} paragraf). Seharusnya 1,5.')
    # perataan
    cocok = sum(1 for info in isi if (info['rata'] or '') == 'JUSTIFY')
    if cocok / len(isi) >= AMBANG_DOMINAN_FORMAT:
        return _temuan('perataan', 'lulus',
                       f'Perataan isi rata kiri kanan '
                       f'({cocok} dari {len(isi)} paragraf).')
    dominan_r: dict[str, int] = {}
    for info in isi:
        k = (info['rata'] or 'rata kiri (bawaan)')
        dominan_r[k] = dominan_r.get(k, 0) + 1
    (nm, jml) = max(dominan_r.items(), key=lambda kv: kv[1])
    return _temuan(
        'perataan', 'tidak',
        f'Perataan yang paling banyak dipakai: {nm} '
        f'({jml} dari {len(isi)} paragraf). '
        f'Seharusnya rata kiri kanan.')


def _cek_judul_bab(model: dict) -> dict:
    """Judul bab: tengah, tebal, kapital, tanpa titik (dari ATURAN_BAKU)."""
    elemen = model['elemen']
    bab = []
    for k, info in elemen:
        if k != 'p':
            continue
        teks = (info['teks_bersih'] or '').strip()
        m = _POLA_BAB_FORMAT.match(teks)
        if not m:
            continue
        # Judul bab asli: gaya Heading ATAU rata tengah. Tebal saja tidak
        # cukup — daftar Sistematika ('BAB I PENDAHULUAN', Normal, tebal,
        # rata kiri) bukan judul bab.
        if not _adalah_judul(info):
            continue
        bab.append((m.group(1), teks, info))
    if not bab:
        return _temuan('judul_bab', 'ragu',
                       'Tidak ada judul bab yang dikenali di naskah.')
    for nomor, teks, info in bab:
        if (info['rata'] or '') != 'CENTER':
            return _temuan(
                'judul_bab', 'tidak',
                f'Judul Bab {nomor} tidak rata tengah.',
                f'Bab {nomor}')
        if not info['tebal']:
            return _temuan(
                'judul_bab', 'tidak',
                f'Judul Bab {nomor} tidak tebal.',
                f'Bab {nomor}')
        judul = re.sub(r'\s+', ' ', teks).strip()
        if judul != judul.upper():
            return _temuan(
                'judul_bab', 'tidak',
                f'Judul Bab {nomor} tidak kapital semua.',
                f'Bab {nomor}')
        if judul.endswith('.'):
            return _temuan(
                'judul_bab', 'tidak',
                f'Judul Bab {nomor} diakhiri titik.',
                f'Bab {nomor}')
    return _temuan('judul_bab', 'lulus',
                   f'{len(bab)} judul bab sudah tengah, tebal, kapital, '
                   f'tanpa titik.')


def _batas_elemen(elemen: list) -> tuple[int, int]:
    """Batas isi sebagai indeks elemen: dari judul bab pertama sampai
    'DAFTAR PUSTAKA'. Dipakai pemeriksa tabel/gambar supaya tabel lampiran
    (yang memang tidak memakai keterangan 'Tabel N.M') tidak dinilai.
    Bila tidak ada judul bab, (0, jumlah elemen)."""
    awal = 0
    akhir = len(elemen)
    for i, (k, info) in enumerate(elemen):
        if k != 'p':
            continue
        if _POLA_BAB_FORMAT.match(info['teks_bersih'] or '') \
                and _adalah_judul(info):
            awal = i
            break
    else:
        return awal, akhir
    for j in range(awal + 1, len(elemen)):
        k, info = elemen[j]
        if k != 'p':
            continue
        bersih = re.sub(r'\s+', ' ', (info['teks_bersih'] or '')).strip().upper()
        if bersih in ('DAFTAR PUSTAKA', 'DAFTAR  PUSTAKA') and _adalah_judul(info):
            akhir = j
            break
    return awal, akhir


def _pasangan_tabel(model: dict) -> tuple[list, list, list, set]:
    """Pasangkan keterangan 'Tabel N.M' dengan tabel berikutnya.

    Hanya di dalam isi (judul bab pertama sampai Daftar Pustaka) — tabel
    lampiran tidak memakai keterangan 'Tabel N.M' dan tidak dinilai.
    Balasan (pasangan, tabel_tanpa_keterangan, keterangan_tanpa_tabel,
    indeks_gambar_tabel): pasangan = [(info_keterangan, indeks_elemen)].
    'Tabel' di sini bisa berupa elemen tabel (tbl) ATAU gambar yang
    ditempeli keterangan Tabel (hasil SPSS yang ditempel sebagai gambar —
    umum di fid 81). Keterangan dicari mundur paling jauh
    JENDELA_TABEL_FORMAT paragraf dari tabelnya; entri Daftar Tabel
    (tab + nomor halaman) dikecualikan.
    """
    elemen = model['elemen']
    awal_el, akhir_el = _batas_elemen(elemen)
    pasangan = []
    tanpa_keterangan = []
    tanpa_tabel = []
    gambar_tabel: set[int] = set()
    tertunda = None  # (info, jarak_paragraf_sejak_keterangan)
    for i in range(awal_el, akhir_el):
        k, info = elemen[i]
        if k == 'tbl':
            if tertunda is not None and tertunda[1] <= JENDELA_TABEL_FORMAT:
                pasangan.append((tertunda[0], i))
                tertunda = None
            else:
                tanpa_keterangan.append(i)
                if tertunda is not None:
                    tanpa_tabel.append(tertunda[0])
                    tertunda = None
            continue
        # k == 'p'
        teks = (info['teks'] or '')
        if _ada_tab_nomor(teks):
            # Entri Daftar Tabel: bukan keterangan, tapi tetap hitung jarak.
            if tertunda is not None:
                tertunda = (tertunda[0], tertunda[1] + 1)
            continue
        m = _adalah_keterangan(info['teks_bersih'] or '', _POLA_TABEL_FORMAT)
        if m:
            if tertunda is not None:
                tanpa_tabel.append(tertunda[0])
            tertunda = (info, 0)
            continue
        # Bukan keterangan. Gambar yang ditempeli keterangan Tabel = isi
        # tabel (bukan gambar); pasangkan, jangan hitung sebagai jarak.
        if info['ada_gambar'] and tertunda is not None \
                and tertunda[1] <= JENDELA_TABEL_FORMAT:
            pasangan.append((tertunda[0], i))
            gambar_tabel.add(i)
            tertunda = None
        elif tertunda is not None:
            tertunda = (tertunda[0], tertunda[1] + 1)
    if tertunda is not None:
        tanpa_tabel.append(tertunda[0])
    return pasangan, tanpa_keterangan, tanpa_tabel, gambar_tabel


def _cek_tabel(model: dict) -> dict:
    """Keterangan tabel: nomor rangkap dua, judul DI ATAS, rata kiri,
    tidak tebal, tanpa titik (dari ATURAN_BAKU)."""
    pasangan, tanpa_keterangan, tanpa_tabel, _ = _pasangan_tabel(model)
    if not pasangan and not tanpa_keterangan:
        return _temuan('tabel', 'lulus', 'Tidak ada tabel di naskah.')
    gagal_rata = []
    gagal_tebal = []
    gagal_titik = []
    for info, _ in pasangan:
        teks = re.sub(r'\s+', ' ', (info['teks_bersih'] or '')).strip()
        m = _POLA_TABEL_FORMAT.match(teks)
        nomor = f'{m.group(1)}.{m.group(2)}' if m else '?'
        if (info['rata'] or '') not in (None, 'LEFT'):
            gagal_rata.append(nomor)
        if info['tebal']:
            gagal_tebal.append(nomor)
        if teks.endswith('.'):
            gagal_titik.append(nomor)
    total = len(pasangan)
    if gagal_rata:
        contoh = gagal_rata[0]
        return _temuan(
            'tabel', 'tidak',
            f'{len(gagal_rata)} dari {total} keterangan tabel tidak rata kiri '
            f'(contoh: Tabel {contoh}).',
            f'Tabel {contoh}')
    if gagal_tebal:
        contoh = gagal_tebal[0]
        return _temuan(
            'tabel', 'tidak',
            f'{len(gagal_tebal)} dari {total} keterangan tabel ditebalkan '
            f'(contoh: Tabel {contoh}).',
            f'Tabel {contoh}')
    if gagal_titik:
        contoh = gagal_titik[0]
        return _temuan(
            'tabel', 'tidak',
            f'{len(gagal_titik)} dari {total} keterangan tabel diakhiri titik '
            f'(contoh: Tabel {contoh}).',
            f'Tabel {contoh}')
    if tanpa_keterangan:
        return _temuan(
            'tabel', 'ragu',
            f'{len(tanpa_keterangan)} tabel tanpa keterangan di atasnya. '
            f'Perlu diperiksa.',
            f'{len(tanpa_keterangan)} tabel')
    if tanpa_tabel:
        return _temuan(
            'tabel', 'ragu',
            f'{len(tanpa_tabel)} keterangan tabel tanpa tabel sesudahnya. '
            f'Perlu diperiksa.')
    return _temuan('tabel', 'lulus',
                   f'{len(pasangan)} keterangan tabel sudah di atas, '
                   f'rata kiri, tidak tebal, tanpa titik.')


def _cek_gambar(model: dict) -> dict:
    """Keterangan gambar: nomor rangkap dua, judul DI BAWAH, rata tengah,
    tidak tebal, tanpa titik (dari ATURAN_BAKU).

    Gambar yang ditempeli keterangan Tabel (hasil SPSS sebagai gambar)
    BUKAN gambar — sudah dinilai oleh _cek_tabel. Gambar di bagian awal
    (logo sampul, foto penulis) juga bukan gambar isi.
    """
    elemen = model['elemen']
    _, _, _, gambar_tabel = _pasangan_tabel(model)
    awal_el, akhir_el = _batas_elemen(elemen)
    dalam_isi = set(range(awal_el, akhir_el))
    pasangan = []
    tanpa_keterangan = []
    tanpa_tabel = []
    dipakai: set[int] = set()
    for i, (k, info) in enumerate(elemen):
        if k != 'p' or not info['ada_gambar']:
            continue
        if i in gambar_tabel:
            continue
        if i not in dalam_isi:
            continue
        # Cari paragraf tak-kosong berikutnya; berhenti bila ketemu gambar lain.
        ketemu = None
        jarak = 0
        for j in range(i + 1, len(elemen)):
            k2, info2 = elemen[j]
            if k2 != 'p':
                continue
            if info2['ada_gambar']:
                break
            if (info2['teks_bersih'] or '').strip() == '':
                continue
            jarak += 1
            if jarak > JENDELA_GAMBAR_FORMAT:
                break
            ketemu = (j, info2)
            break
        if ketemu is None:
            tanpa_keterangan.append(i)
            continue
        j, info2 = ketemu
        teks = (info2['teks'] or '')
        if _ada_tab_nomor(teks):
            tanpa_keterangan.append(i)
            continue
        m = _adalah_keterangan(info2['teks_bersih'] or '', _POLA_GAMBAR_FORMAT)
        if not m:
            tanpa_keterangan.append(i)
            continue
        dipakai.add(j)
        pasangan.append((info2, i))
    # Keterangan gambar yang tidak dipakai pasangan mana pun.
    for j, (k, info) in enumerate(elemen):
        if k != 'p' or j in dipakai:
            continue
        if j not in dalam_isi:
            continue
        teks = (info['teks'] or '')
        if _ada_tab_nomor(teks):
            continue
        if _adalah_keterangan(info['teks_bersih'] or '', _POLA_GAMBAR_FORMAT):
            tanpa_tabel.append(info)
    gagal_rata = []
    gagal_tebal = []
    gagal_titik = []
    for info, _ in pasangan:
        teks = re.sub(r'\s+', ' ', (info['teks_bersih'] or '')).strip()
        m = _POLA_GAMBAR_FORMAT.match(teks)
        nomor = f'{m.group(1)}.{m.group(2)}' if m else '?'
        if (info['rata'] or '') != 'CENTER':
            gagal_rata.append(nomor)
        if info['tebal']:
            gagal_tebal.append(nomor)
        if teks.endswith('.'):
            gagal_titik.append(nomor)
    total = len(pasangan)
    if gagal_rata:
        contoh = gagal_rata[0]
        return _temuan(
            'gambar', 'tidak',
            f'{len(gagal_rata)} dari {total} keterangan gambar tidak rata tengah '
            f'(contoh: Gambar {contoh}).',
            f'Gambar {contoh}')
    if gagal_tebal:
        contoh = gagal_tebal[0]
        return _temuan(
            'gambar', 'tidak',
            f'{len(gagal_tebal)} dari {total} keterangan gambar ditebalkan '
            f'(contoh: Gambar {contoh}).',
            f'Gambar {contoh}')
    if gagal_titik:
        contoh = gagal_titik[0]
        return _temuan(
            'gambar', 'tidak',
            f'{len(gagal_titik)} dari {total} keterangan gambar diakhiri titik '
            f'(contoh: Gambar {contoh}).',
            f'Gambar {contoh}')
    if tanpa_keterangan:
        return _temuan(
            'gambar', 'ragu',
            f'{len(tanpa_keterangan)} gambar tanpa keterangan di bawahnya. '
            f'Perlu diperiksa.',
            f'{len(tanpa_keterangan)} gambar')
    if tanpa_tabel:
        return _temuan(
            'gambar', 'ragu',
            f'{len(tanpa_tabel)} keterangan gambar tanpa gambar sebelumnya. '
            f'Perlu diperiksa.')
    if not pasangan:
        return _temuan('gambar', 'lulus', 'Tidak ada gambar di naskah.')
    return _temuan('gambar', 'lulus',
                   f'{len(pasangan)} keterangan gambar sudah di bawah, '
                   f'rata tengah, tidak tebal, tanpa titik.')


def _cek_nomor_halaman(model: dict) -> dict:
    """Nomor halaman: bagian awal romawi kecil, Bab I ke atas arab.

    pgNumType efektif = eksplisit, kalau tidak ada mewarisi seksi sebelumnya.
    """
    seksi = model['seksi']
    if len(seksi) <= 1:
        return _temuan(
            'nomor_halaman', 'ragu',
            'Naskah hanya punya satu seksi, nomor halaman tidak dibedakan '
            'antara bagian awal dan Bab I.')
    fmt_efektif = []
    terakhir = None
    for s in seksi:
        if s['pgnum_fmt']:
            terakhir = s['pgnum_fmt']
        fmt_efektif.append(terakhir)
    romawi = ('lowerRoman', 'upperRoman')
    pertama = fmt_efektif[0]
    if pertama is None:
        return _temuan(
            'nomor_halaman', 'ragu',
            'Format nomor halaman bagian awal tidak tertulis di berkas. '
            'Perlu diperiksa.')
    if pertama not in romawi:
        return _temuan(
            'nomor_halaman', 'tidak',
            'Nomor halaman bagian awal bukan romawi kecil.',
            'Bagian awal')
    for i in range(1, len(fmt_efektif)):
        fmt = fmt_efektif[i]
        if fmt is None:
            return _temuan(
                'nomor_halaman', 'ragu',
                f'Format nomor halaman seksi {i + 1} tidak tertulis di berkas. '
                f'Perlu diperiksa.',
                f'Seksi {i + 1}')
        if fmt in romawi:
            return _temuan(
                'nomor_halaman', 'tidak',
                f'Nomor halaman Bab I ke atas masih romawi di seksi {i + 1}.',
                f'Seksi {i + 1}')
        if fmt != 'decimal':
            return _temuan(
                'nomor_halaman', 'ragu',
                f'Format nomor halaman seksi {i + 1} tidak dikenali ({fmt}).',
                f'Seksi {i + 1}')
    return _temuan('nomor_halaman', 'lulus',
                   'Nomor halaman bagian awal romawi kecil, '
                   'Bab I ke atas angka arab.')


def periksa_format(jalur: str | Path,
                   aturan: dict[str, Any] | None = None) -> dict[str, Any]:
    """Periksa format satu .docx terhadap pedoman (deterministik, tanpa LLM).

    `aturan` = ATURAN_BAKU atau panduan user (gabung, pola ringkas_untuk_ai).
    Balasan: {'sidik_berkas', 'diperiksa_pada', 'ringkasan', 'temuan',
    'langkah_berikut'}. Tidak menulis apa pun ke docx.
    """
    from datetime import datetime, timezone
    import hashlib

    aturan = dict(aturan or ATURAN_BAKU)
    sidik = None
    try:
        with open(jalur, 'rb') as f:
            sidik = hashlib.sha256(f.read()).hexdigest()
    except Exception:                                          # noqa: BLE001
        sidik = None
    model = baca_docx_format(jalur)
    temuan = [
        _cek_margin(model, aturan),
        _cek_dominan(model, aturan, 'huruf'),
        _cek_dominan(model, aturan, 'spasi'),
        _cek_dominan(model, aturan, 'perataan'),
        _cek_judul_bab(model),
        _cek_tabel(model),
        _cek_gambar(model),
        _cek_nomor_halaman(model),
    ]
    ringkasan = {'lulus': sum(1 for t in temuan if t['vonis'] == 'lulus'),
                 'tidak': sum(1 for t in temuan if t['vonis'] == 'tidak'),
                 'ragu': sum(1 for t in temuan if t['vonis'] == 'ragu')}
    return {
        'sidik_berkas': sidik,
        'diperiksa_pada': datetime.now(timezone.utc).isoformat(),
        'ringkasan': ringkasan,
        'temuan': temuan,
        'langkah_berikut': langkah_berikut_format(temuan),
    }


def langkah_berikut_format(temuan: list[dict]) -> str:
    """Satu kalimat langkah berikut dari hasil pemeriksaan format."""
    tidak = [t for t in (temuan or []) if t.get('vonis') == 'tidak']
    ragu = [t for t in (temuan or []) if t.get('vonis') == 'ragu']
    if tidak:
        nama = ', '.join(t['label'] for t in tidak[:3])
        lebih = f' dan {len(tidak) - 3} lagi' if len(tidak) > 3 else ''
        return (f'Perbaiki dulu: {nama}{lebih}. '
                f'Ketuk tiap baris untuk melihat alasannya.')
    if ragu:
        return ('Ada yang perlu diperiksa sendiri — ketuk tiap baris '
                'untuk melihat alasannya.')
    return 'Semua format sudah sesuai pedoman.'

# ─────────────────────────────────────────────────────────────────
# BAGIAN 3 — CEK BAHASA PEDOMAN (Gas Boss 20 Nov 2026, fitur 3 dari 10)
# ─────────────────────────────────────────────────────────────────
# Pemeriksa deterministik TANPA LLM untuk aturan bahasa di
# ATURAN_BAKU["bahasa"]. Melengkapi modul ini (bukan modul baru).
# Memakai ulang baca_docx_format + _batas_isi dari Bagian 2 (Cek Format)
# supaya ruang lingkup paragraf isi sama persis.
# Batas jujur: pasif TIDAK bisa dipastikan mesin; vonis 'aktif' selalu
# 'ragu', tidak pernah 'tidak'. "pada" di depan subjek dan angka di awal
# kalimat TIDAK diperiksa di v1 (positif palsu: keterangan waktu dan
# potongan sitasi). KBBI dan istilah asing miring ditunda ke v2.

PEMERIKSAAN_BAHASA = [
    ('saya', 'Kata saya/aku/kita'),
    ('hubung_awal', 'Kata penghubung di awal kalimat'),
    ('dimana', 'Kata "dimana"'),
    ('dike_tempat', 'Awalan di-/ke- menempel'),
    ('desimal', 'Desimal pakai titik'),
    ('aktif', 'Kalimat aktif'),
]
VONIS_SAH_BAHASA = ('lulus', 'tidak', 'ragu')

# Kata tempat/waktu yang umum: awalan di-/ke- menempel pada kata ini
# hampir pasti salah (seharusnya dipisah: "di rumah", "ke kampus").
# 'mana' sengaja tidak ada: "dimana" ditangkap pemeriksa sendiri.
KATA_TEMPAT_BAHASA = (
    'rumah', 'kampus', 'sekolah', 'kantor', 'pasar', 'kota', 'desa',
    'jalan', 'tahun', 'bulan', 'hari', 'sini', 'sana', 'situ', 'dalam',
    'luar', 'atas', 'bawah', 'depan', 'belakang', 'samping', 'tengah',
    'pinggir', 'seberang',
)
# Subjek + kata kerja aktif yang umum (contoh untuk vonis 'ragu').
KATA_KERJA_AKTIF_BAHASA = (
    'melakukan', 'menunjukkan', 'menggunakan', 'memilih', 'meneliti',
    'menganalisis', 'mengumpulkan', 'mengolah', 'menyusun', 'menentukan',
    'memberikan',
)
PANJANG_MINIMAL_KALIMAT_BAHASA = 20

_POLAA_SAYA_BAHASA = re.compile(r'\b(?:saya|aku|kita|kami)\b', re.I)
_POLAA_HUBUNG_AWAL_BAHASA = re.compile(
    r'(?:^|[.!?]\s+)(?:sehingga|sedangkan)\b', re.I)
_POLAA_DIMANA_BAHASA = re.compile(r'\bdimana\b', re.I)
_POLAA_TEMPAT_BAHASA = re.compile(
    r'\b(?:di|ke)(?:' + '|'.join(KATA_TEMPAT_BAHASA) + r')\b', re.I)
_POLAA_DESIMAL_BAHASA = re.compile(r'(?<![A-Za-z0-9.])\d+\.\d{1,2}(?!\d)')
_POLAA_DESIMAL_KONTEKS_BAHASA = re.compile(
    r'(?:tabel|gambar|bab|subbab|bagian)\s+\d+\.\d+', re.I)
_POLAA_PASIF_BAHASA = re.compile(r'\b(?:di|ter)[a-z]{3,}\b', re.I)
_POLAA_AKTIF_BAHASA = re.compile(
    r'\b(?:peneliti|penulis|mahasiswa|penelitian ini)\s+(?:'
    + '|'.join(KATA_KERJA_AKTIF_BAHASA) + r')\b', re.I)
_POLAA_BELAH_BAHASA = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])')


def _teks_isi_bahasa(model: dict) -> list[str]:
    """Teks paragraf isi (ruang lingkup sama persis seperti Cek Format).

    Gaya Normal/List Paragraph, panjang >= 80, di antara judul bab
    pertama dan 'DAFTAR PUSTAKA'. Pola _cek_dominan: _batas_isi memberi
    posisi ke daftar paragraf, bukan indeks elemen.
    """
    elemen = model['elemen']
    awal, akhir = _batas_isi(elemen)
    paragraf_idx = [i for i, (k, _) in enumerate(elemen) if k == 'p']
    isi = []
    for pos in range(awal, akhir):
        info = elemen[paragraf_idx[pos]][1]
        teks = (info['teks'] or '').strip()
        if len(teks) < PANJANG_MINIMAL_ISI_FORMAT:
            continue
        if info['gaya'] not in GAYA_ISI_FORMAT:
            continue
        isi.append(teks)
    return isi


def _kalimat_isi_bahasa(isi: list[str]) -> list[str]:
    """Pecah paragraf isi jadi kalimat.

    Belah hanya sesudah . ! ? + spasi + huruf kapital/angka, supaya
    pecahan desimal (50,5) dan nomor daftar tidak memecah kalimat.
    Kalimat pendek (< 20 karakter, potongan sitasi) dibuang.
    """
    kalimat = []
    for t in isi:
        for k in _POLAA_BELAH_BAHASA.split(t):
            k = k.strip()
            if len(k) >= PANJANG_MINIMAL_KALIMAT_BAHASA:
                kalimat.append(k)
    return kalimat


def _temuan_bahasa(cek_id: str, vonis: str, alasan: str,
                   lokasi: str = '') -> dict:
    """Satu baris temuan bahasa (pola _temuan Bagian 2)."""
    label = dict(PEMERIKSAAN_BAHASA).get(cek_id, cek_id)
    return {'id': cek_id, 'label': label, 'vonis': vonis,
            'alasan': alasan, 'lokasi': lokasi}


def _contoh_bahasa(cocok: list, maks: int = 1) -> str:
    """Contoh pertama yang pendek, untuk alasan temuan."""
    for c in cocok:
        s = str(c).strip()
        if s:
            return s[:60]
    return ''


def _cek_kata_bahasa(isi: list[str], cek_id: str, pola) -> dict:
    """Pemeriksa tingkat kata: hitung kemunculan pola di teks isi.

    Ketemu -> 'tidak' (jumlah + contoh). Bersih -> 'lulus'.
    """
    gabung = '\n'.join(isi)
    cocok = pola.findall(gabung)
    if not cocok:
        return _temuan_bahasa(cek_id, 'lulus',
                              'Tidak ditemukan di paragraf isi.')
    contoh = _contoh_bahasa(cocok)
    return _temuan_bahasa(
        cek_id, 'tidak',
        f'Ditemukan {len(cocok)} kali di paragraf isi '
        f'(contoh: {contoh}).')


def _cek_desimal_bahasa(isi: list[str]) -> dict:
    """Desimal pakai titik (50.5), bukan pemisah ribuan (293.753) dan
    bukan rujukan Tabel/Gambar/Bab (4.1)."""
    gabung = '\n'.join(isi)
    cocok = []
    for m in _POLAA_DESIMAL_BAHASA.finditer(gabung):
        awal = max(0, m.start() - 30)
        konteks = gabung[awal:m.end() + 10]
        if _POLAA_DESIMAL_KONTEKS_BAHASA.search(konteks):
            continue
        cocok.append(m.group(0))
    if not cocok:
        return _temuan_bahasa('desimal', 'lulus',
                              'Tidak ada desimal pakai titik di isi.')
    return _temuan_bahasa(
        'desimal', 'tidak',
        f'Ditemukan {len(cocok)} desimal pakai titik '
        f'(contoh: {cocok[0]}). Seharusnya pakai koma (50,5).')


def _cek_aktif_bahasa(kalimat: list[str]) -> dict:
    """Kalimat yang tampak aktif (tanpa kata berawalan di-/ter-).

    Vonis selalu 'ragu', tidak pernah 'tidak': mesin tidak bisa
    memastikan pasif. Contoh diambil dari pola aktif eksplisit bila ada.
    """
    if not kalimat:
        return _temuan_bahasa('aktif', 'lulus',
                              'Tidak ada kalimat isi untuk diperiksa.')
    tanpa = [k for k in kalimat if not _POLAA_PASIF_BAHASA.search(k)]
    if not tanpa:
        return _temuan_bahasa('aktif', 'lulus',
                              'Semua kalimat isi memakai kata pasif.')
    contoh = _POLAA_AKTIF_BAHASA.search('\n'.join(tanpa))
    contoh_teks = (contoh.group(0) if contoh else tanpa[0][:60])
    return _temuan_bahasa(
        'aktif', 'ragu',
        f'{len(tanpa)} dari {len(kalimat)} kalimat tampak aktif '
        f'(contoh: {contoh_teks}). Perlu diperiksa, mesin tidak bisa '
        f'memastikan kalimat pasif.')


def periksa_bahasa(jalur: str | Path,
                   aturan: dict[str, Any] | None = None) -> dict[str, Any]:
    """Periksa bahasa satu .docx terhadap pedoman (deterministik, tanpa LLM).

    `aturan` = ATURAN_BAKU atau panduan user (gabung, pola ringkas_untuk_ai).
    Balasan: {'sidik_berkas', 'diperiksa_pada', 'ringkasan', 'temuan',
    'langkah_berikut'}. Tidak menulis apa pun ke docx.
    """
    from datetime import datetime, timezone
    import hashlib

    aturan = dict(aturan or ATURAN_BAKU)
    sidik = None
    try:
        with open(jalur, 'rb') as f:
            sidik = hashlib.sha256(f.read()).hexdigest()
    except Exception:                                          # noqa: BLE001
        sidik = None
    model = baca_docx_format(jalur)
    isi = _teks_isi_bahasa(model)
    kalimat = _kalimat_isi_bahasa(isi)
    temuan = [
        _cek_kata_bahasa(isi, 'saya', _POLAA_SAYA_BAHASA),
        _cek_kata_bahasa(isi, 'hubung_awal', _POLAA_HUBUNG_AWAL_BAHASA),
        _cek_kata_bahasa(isi, 'dimana', _POLAA_DIMANA_BAHASA),
        _cek_kata_bahasa(isi, 'dike_tempat', _POLAA_TEMPAT_BAHASA),
        _cek_desimal_bahasa(isi),
        _cek_aktif_bahasa(kalimat),
    ]
    ringkasan = {'lulus': sum(1 for t in temuan if t['vonis'] == 'lulus'),
                 'tidak': sum(1 for t in temuan if t['vonis'] == 'tidak'),
                 'ragu': sum(1 for t in temuan if t['vonis'] == 'ragu')}
    return {
        'sidik_berkas': sidik,
        'diperiksa_pada': datetime.now(timezone.utc).isoformat(),
        'ringkasan': ringkasan,
        'temuan': temuan,
        'langkah_berikut': langkah_berikut_bahasa(temuan),
    }


def langkah_berikut_bahasa(temuan: list[dict]) -> str:
    """Satu kalimat langkah berikut dari hasil pemeriksaan bahasa."""
    tidak = [t for t in (temuan or []) if t.get('vonis') == 'tidak']
    ragu = [t for t in (temuan or []) if t.get('vonis') == 'ragu']
    if tidak:
        nama = ', '.join(t['label'] for t in tidak[:3])
        lebih = f' dan {len(tidak) - 3} lagi' if len(tidak) > 3 else ''
        return (f'Perbaiki dulu: {nama}{lebih}. '
                f'Ketuk tiap baris untuk melihat alasannya.')
    if ragu:
        return ('Ada kalimat yang perlu diperiksa sendiri — ketuk tiap '
                'baris untuk melihat alasannya.')
    return 'Semua bahasa sudah sesuai pedoman.'
