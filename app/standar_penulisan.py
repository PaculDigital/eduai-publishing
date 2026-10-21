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
