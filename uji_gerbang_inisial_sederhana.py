"""Uji gerbang final inisial sederhana, tanpa LLM, tanpa DB, tanpa API.

Jalankan dari checkout: python3 uji_gerbang_inisial_sederhana.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.

Kasus dari fakta job 226: Bab 3 cakupan 8 dari 8, sitasi
snapshot 75, tapi masih ada 3 sitasi inisial saja yang tidak
bisa diperbaiki: E. M. (2003), M. (1990), F. D. (2003).
Perbaikan sederhana: hapus inisial tak terperbaiki secara
deterministik bila cakupan tetap di atas atau sama dengan
50 persen, gagal hanya bila cakupan jatuh di bawah 50 persen
atau tidak ada sitasi snapshot tersisa.
"""

import os
import sys

for p in (os.getcwd(), "/opt/data/services/eduai-publishing", "/app"):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from app import sitasi_anti_gagal as SG

LULUS = 0
GAGAL = []


def cek(nama, ok, info=""):
    global LULUS
    if ok:
        LULUS += 1
        print("  LULUS %s" % nama)
    else:
        GAGAL.append(nama)
        print("  GAGAL %s %s" % (nama, info))


REFS_8 = [
    "Marina, D. (2019). Judul satu.",
    "Zhiqiang, L. (2021). Judul dua.",
    "Prasanna, R. (2019). Judul tiga.",
    "Tidaar, A. (2019). Judul empat.",
    "Rosita, S. (2020). Judul lima.",
    "Arianto, B. (2021). Judul enam.",
    "Hardilawati, H. (2022). Judul tujuh.",
    "Macharia, J. (2023). Judul delapan.",
]

ROWS_8 = [
    {"kunci": "marina", "alias": ["dabic"], "tahun": "2019",
     "surname_tampil": "Marina", "ref_dict": {}},
    {"kunci": "zhiqiang", "alias": ["lu"], "tahun": "2021",
     "surname_tampil": "Zhiqiang", "ref_dict": {}},
    {"kunci": "prasanna", "alias": ["rpir"], "tahun": "2019",
     "surname_tampil": "Prasanna", "ref_dict": {}},
    {"kunci": "tidaar", "alias": ["universitas"], "tahun": "2019",
     "surname_tampil": "Tidaar", "ref_dict": {}},
    {"kunci": "rosita", "alias": [], "tahun": "2020",
     "surname_tampil": "Rosita", "ref_dict": {}},
    {"kunci": "arianto", "alias": [], "tahun": "2021",
     "surname_tampil": "Arianto", "ref_dict": {}},
    {"kunci": "hardilawati", "alias": [], "tahun": "2022",
     "surname_tampil": "Hardilawati", "ref_dict": {}},
    {"kunci": "macharia", "alias": [], "tahun": "2023",
     "surname_tampil": "Macharia", "ref_dict": {}},
]

TEKS_LOLOS_PLUS_INISIAL = (
    "Transformasi dibahas (Marina, 2019) dan (Zhiqiang, 2021) "
    "dan (Prasanna, 2019) dan (Tidaar, 2019) dan (Rosita, 2020) "
    "dan (Arianto, 2021) dan (Hardilawati, 2022) "
    "dan (Macharia, 2023). "
    "Klaim lama ditulis E. M. (2003) dan M. (1990) dan F. D. (2003)."
)

TEKS_TANPA_INISIAL = (
    "Transformasi dibahas (Marina, 2019) dan (Zhiqiang, 2021) "
    "dan (Prasanna, 2019) dan (Tidaar, 2019) dan (Rosita, 2020) "
    "dan (Arianto, 2021) dan (Hardilawati, 2022) "
    "dan (Macharia, 2023)."
)

TEKS_CAKUPAN_RENDAH_PLUS_INISIAL = (
    "Kinerja dibahas (Marina, 2019) dan (Zhiqiang, 2021). "
    "Klaim lama ditulis X. (1999)."
)


def test_hapus_inisial_sisa():
    teks_baru, dihapus = SG.hapus_inisial_sisa(TEKS_LOLOS_PLUS_INISIAL)
    cek("hapus-inisial-hilang-dari-teks",
        "E. M. (2003)" not in teks_baru
        and "M. (1990)" not in teks_baru
        and "F. D. (2003)" not in teks_baru,
        repr(teks_baru))
    cek("hapus-inisial-dicatat-3",
        len(dihapus) == 3,
        repr(dihapus))
    cek("hapus-inisial-tidak-menebak-nama",
        "Marina" in teks_baru and "Zhiqiang" in teks_baru,
        repr(teks_baru))


def test_lolos_sesudah_hapus_jalur_lama():
    hasil = SG.periksa_dan_perbaiki_bab(3, TEKS_LOLOS_PLUS_INISIAL, REFS_8)
    cek("lama-lolos-sesudah-hapus", hasil["lolos"] is True, repr(hasil))
    cek("lama-inisial-hilang",
        "E. M. (2003)" not in hasil["teks_baru"]
        and "M. (1990)" not in hasil["teks_baru"]
        and "F. D. (2003)" not in hasil["teks_baru"],
        repr(hasil["teks_baru"]))
    cek("lama-cakupan-tetap-lolos",
        hasil["cek_ulang"]["cakupan"]["persen"] >= 0.50,
        repr(hasil["cek_ulang"]["cakupan"]))
    cek("lama-dihapus-tercatat",
        len(hasil.get("inisial_dihapus", [])) == 3,
        repr(hasil.get("inisial_dihapus")))


def test_lolos_sesudah_hapus_jalur_snapshot():
    hasil = SG.periksa_dan_perbaiki_bab_snapshot(
        3, TEKS_LOLOS_PLUS_INISIAL, ROWS_8)
    cek("snapshot-lolos-sesudah-hapus", hasil["lolos"] is True, repr(hasil))
    cek("snapshot-inisial-hilang",
        "E. M. (2003)" not in hasil["teks_baru"]
        and "M. (1990)" not in hasil["teks_baru"]
        and "F. D. (2003)" not in hasil["teks_baru"],
        repr(hasil["teks_baru"]))
    cek("snapshot-cakupan-8-dari-8",
        hasil["cek_ulang"]["cakupan"]["cocok_jumlah"] == 8
        and hasil["cek_ulang"]["cakupan"]["total"] == 8,
        repr(hasil["cek_ulang"]["cakupan"]))
    cek("snapshot-dihapus-tercatat",
        len(hasil.get("inisial_dihapus", [])) == 3,
        repr(hasil.get("inisial_dihapus")))


def test_gagal_bila_cakupan_rendah():
    try:
        SG.periksa_dan_perbaiki_bab(
            3, TEKS_CAKUPAN_RENDAH_PLUS_INISIAL, REFS_8)
        cek("rendah-tetap-gagal", False, "tidak raise")
    except SG.GagalSitasiBersih as e:
        cek("rendah-pesan-manusia-sama",
            str(e) == SG.PESAN_GAGAL_BERSIH, repr(str(e)))
        cek("rendah-inisial-tersisa-1",
            len(e.inisial_tersisa) == 1, repr(e.inisial_tersisa))
        detail = SG.detail_galat_sitasi(
            3, e.cakupan, inisial_sisa=e.inisial_tersisa)
        cek("rendah-galat-sebut-bab-cakupan",
            "Bab 3" in detail and "cakupan" in detail, repr(detail))
        cek("rendah-galat-sebut-inisial-sisa",
            "inisial sisa" in detail and "X. (1999)" in detail,
            repr(detail))
        cek("rendah-galat-sebut-sitasi-snapshot",
            "sitasi snapshot" in detail, repr(detail))
    hasil = SG.periksa_dan_perbaiki_bab(
        3, TEKS_CAKUPAN_RENDAH_PLUS_INISIAL, REFS_8, gagal_keras=False)
    cek("rendah-flag-tanpa-raise",
        hasil["lolos"] is False and hasil["pesan"] == SG.PESAN_GAGAL_BERSIH,
        repr(hasil))


def test_tanpa_inisial_tidak_berubah():
    hasil = SG.periksa_dan_perbaiki_bab(3, TEKS_TANPA_INISIAL, REFS_8)
    cek("tanpa-inisial-lolos", hasil["lolos"] is True, repr(hasil))
    cek("tanpa-inisial-teks-sama",
        hasil["teks_baru"] == TEKS_TANPA_INISIAL, repr(hasil["teks_baru"]))
    hasil_snap = SG.periksa_dan_perbaiki_bab_snapshot(
        3, TEKS_TANPA_INISIAL, ROWS_8)
    cek("tanpa-inisial-snapshot-lolos",
        hasil_snap["lolos"] is True
        and hasil_snap["teks_baru"] == TEKS_TANPA_INISIAL,
        repr(hasil_snap))


def test_detail_inisial_maks_5():
    ringkas = [
        {"inisial": "A", "tahun": "2000", "raw": "A. (2000)", "jumlah": 1},
        {"inisial": "B", "tahun": "2001", "raw": "B. (2001)", "jumlah": 1},
        {"inisial": "C", "tahun": "2002", "raw": "C. (2002)", "jumlah": 1},
        {"inisial": "D", "tahun": "2003", "raw": "D. (2003)", "jumlah": 1},
        {"inisial": "E", "tahun": "2004", "raw": "E. (2004)", "jumlah": 1},
        {"inisial": "F", "tahun": "2005", "raw": "F. (2005)", "jumlah": 1},
    ]
    detail = SG.detail_galat_sitasi(
        3, {"total": 8, "cocok_jumlah": 8, "sitasi_snapshot": 8},
        inisial_sisa=ringkas)
    cek("detail-inisial-jumlah-6",
        "inisial sisa 6" in detail, repr(detail))
    cek("detail-inisial-contoh-maks-5",
        "E. (2004)" in detail and "F. (2005)" not in detail,
        repr(detail))


def main():
    test_hapus_inisial_sisa()
    test_lolos_sesudah_hapus_jalur_lama()
    test_lolos_sesudah_hapus_jalur_snapshot()
    test_gagal_bila_cakupan_rendah()
    test_tanpa_inisial_tidak_berubah()
    test_detail_inisial_maks_5()
    print("LULUS %s, GAGAL %s" % (LULUS, len(GAGAL)))
    if GAGAL:
        print("GAGAL: %s" % ", ".join(GAGAL))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
