"""Uji sitasi anti gagal (G4), tanpa LLM asli, tanpa DB, tanpa API.

Jalankan dari checkout: /opt/data/.venv/bin/python3 uji_anti_gagal_sitasi.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.

Fixture diambil dari fakta audit job 222, bukan dari folder job dan
bukan dari DOCX asli, supaya uji bisa jalan tanpa produksi:
  - Bab 5: inisial saja (H., 2025), (M., 2024), (Z., 2023), (E., 2021),
    (N., 2024), (N., 2025), seperti hitung DOCX audit (15 kemunculan).
  - Bab 4: 0 dari 8 surname referensi cocok dengan sitasi badan.
  - Pustaka: 19 sitasi badan hilang dari panen, diuji sebagian di
    sini (Vial 2019, Teece 2018, Rogers 2003, Davis 1989).
LLM diuji dengan mock callable, bukan call_llm asli.
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


REFS_BAB5 = [
    "Zhou, H. (2025). Digital economy and SME financing costs. "
    "Finance Research Letters.",
    "Alfarizi, M. (2024). Exploration of Technological Challenges. "
    "Jurnal Ekonomi.",
    "Sahudin, Z. (2023). Overview of Halal-Integrated Platform. "
    "Jurnal Ekonomi.",
    "Herari, N. (2024). Digital Marketing Transformation of Local MSME. "
    "Jurnal Ekonomi.",
    "Alexandrova, E. (2021). Opportunities and Limitations for the "
    "Digital Economy Development. Jurnal Ekonomi.",
    "Noerchoidah, N. (2025). Optimization of Digital Literacy Knowledge "
    "Sharing. Jurnal Ekonomi.",
    "Nugraha, N. (2025). Judul lain tahun sama untuk uji ambigu. "
    "Jurnal Ekonomi.",
    "Wulan, T. S. (2025). The Effect of Digital Marketing and Product "
    "Innovation on MSME Sales Performance. Jurnal Ekonomi.",
]

TEKS_BAB5 = (
    "Ekosistem digital dibahas panjang (H., 2025) dan (H., 2025) "
    "serta (M., 2024) dan (M., 2024) dan (M., 2024). "
    "Platform halal dibahas (Z., 2023) dan (E., 2021) "
    "dan (N., 2024) dan (N., 2025). "
    "Sitasi normal juga ada (Arianto, 2021) dan (Zhou, 2025)."
)

REFS_BAB4 = [
    "Santoso, A. (2020). Judul satu.",
    "Wijaya, B. (2021). Judul dua.",
    "Pratama, C. (2019). Judul tiga.",
    "Lestari, D. (2022). Judul empat.",
    "Kusuma, E. (2018). Judul lima.",
    "Firmansyah, F. (2023). Judul enam.",
    "Anggraini, G. (2020). Judul tujuh.",
    "Saputra, H. (2021). Judul delapan.",
]

TEKS_BAB4 = (
    "Kinerja dibahas (Vial, 2019) dan (Teece, 2018) "
    "dan (Rogers, 2003) dan (Davis, 1989) "
    "dan (Kaplan dan Norton, 1996)."
)

REFS_TUNGGAL = [
    "Zhou, H. (2025). Digital economy and SME financing costs.",
    "Alfarizi, M. (2024). Exploration of Technological Challenges.",
    "Sahudin, Z. (2023). Overview of Halal-Integrated Platform.",
    "Herari, N. (2024). Digital Marketing Transformation.",
]

TEKS_TUNGGAL = (
    "Ekosistem dibahas (H., 2025) dan (M., 2024) "
    "dan (Z., 2023) dan (N., 2024)."
)

TEKS_AMBIGU = (
    "Ekosistem digital dibahas secara umum (N., 2025) "
    "tanpa menyebut nama penulis di kalimat ini."
)

TEKS_AMBIGU_KONTEKS = (
    "Noerchoidah menjelaskan ekosistem digital (N., 2025) "
    "dengan bukti dari lapangan."
)


def test_inisial_bab5_tertangkap():
    hasil = SG.cek_hulu_bab(5, TEKS_BAB5, REFS_BAB5)
    cek("bab5-inisial-jumlah-lebih-nol", hasil["jumlah_inisial"] > 0,
        repr(hasil["jumlah_inisial"]))
    cek("bab5-inisial-contoh-M-2024",
        "(M., 2024)" in hasil["contoh_inisial"],
        repr(hasil["contoh_inisial"]))
    cek("bab5-inisial-gagal-hulu", hasil["lolos"] is False,
        repr(hasil["masalah"]))


def test_cakupan_bab4_di_bawah_ambang():
    cakupan = SG.hitung_cakupan(TEKS_BAB4, REFS_BAB4)
    cek("bab4-cakupan-nol-dari-delapan",
        cakupan["total"] == 8 and cakupan["cocok_jumlah"] == 0,
        repr(cakupan))
    cek("bab4-cakupan-di-bawah-50-persen", cakupan["persen"] < 0.50,
        repr(cakupan["persen"]))
    hasil = SG.cek_hulu_bab(4, TEKS_BAB4, REFS_BAB4)
    cek("bab4-gagal-hulu-karena-cakupan", hasil["lolos"] is False,
        repr(hasil["masalah"]))


def test_cakupan_ambang_50_persen_lolos():
    refs = [
        "Santoso, A. (2020). Judul satu.",
        "Wijaya, B. (2021). Judul dua.",
        "Pratama, C. (2019). Judul tiga.",
        "Lestari, D. (2022). Judul empat.",
    ]
    teks = "Pembahasan (Santoso, 2020) dan (Wijaya, 2021)."
    cakupan = SG.hitung_cakupan(teks, refs)
    cek("ambang-50-persen-tepat-lolos",
        cakupan["persen"] == 0.50
        and SG.cek_hulu_bab(1, teks, refs)["lolos"] is True,
        repr(cakupan))


def test_repair_tunggal():
    sebelum = TEKS_TUNGGAL
    hasil = SG.repair_bab(sebelum, REFS_TUNGGAL)
    sesudah = hasil["teks_baru"]
    cek("repair-tunggal-sebelum-ada-inisial", "(M., 2024)" in sebelum)
    cek("repair-tunggal-sesudah-jadi-surname",
        "(Alfarizi, 2024)" in sesudah
        and "(Zhou, 2025)" in sesudah
        and "(Sahudin, 2023)" in sesudah
        and "(Herari, 2024)" in sesudah,
        repr(sesudah))
    cek("repair-tunggal-tidak-sisa-inisial",
        "(M., 2024)" not in sesudah and hasil["jumlah_sisa"] == 0,
        repr(hasil))
    cek("repair-tunggal-cara-tunggal",
        all(d["cara"] == "tunggal" for d in hasil["diperbaiki"])
        and len(hasil["diperbaiki"]) == 4,
        repr(hasil["diperbaiki"]))


def test_ambigu_tidak_diganti_buta():
    hasil = SG.repair_bab(TEKS_AMBIGU, REFS_BAB5)
    cek("ambigu-tetap-di-teks",
        "(N., 2025)" in hasil["teks_baru"],
        repr(hasil["teks_baru"]))
    cek("ambigu-ditandai-dua-kandidat",
        len(hasil["ambigu"]) == 1
        and set(hasil["ambigu"][0]["kandidat"])
        == {"Noerchoidah", "Nugraha"},
        repr(hasil["ambigu"]))
    cek("ambigu-tidak-di-diperbaiki",
        all(d["raw"] != "(N., 2025)" for d in hasil["diperbaiki"]),
        repr(hasil["diperbaiki"]))


def test_ambigu_konteks_kedua_memilih():
    hasil = SG.repair_bab(TEKS_AMBIGU_KONTEKS, REFS_BAB5)
    cek("konteks-kedua-memilih-surname-kalimat",
        "(Noerchoidah, 2025)" in hasil["teks_baru"]
        and "(N., 2025)" not in hasil["teks_baru"],
        repr(hasil["teks_baru"]))
    cek("konteks-kedua-cara-tercatat",
        any(d["cara"].startswith("konteks_") for d in hasil["diperbaiki"]),
        repr(hasil["diperbaiki"]))


def test_llm_mock_hanya_kandidat():
    def mock_benar(prompt):
        assert "N., 2025" in prompt
        return '{"N., 2025": "Noerchoidah"}'

    hasil = SG.repair_bab(TEKS_AMBIGU, REFS_BAB5, panggil_llm=mock_benar)
    cek("llm-mock-memilih-kandidat",
        "(Noerchoidah, 2025)" in hasil["teks_baru"],
        repr(hasil["teks_baru"]))

    def mock_karang(prompt):
        return '{"N., 2025": "Zulkarnain"}'

    hasil2 = SG.repair_bab(TEKS_AMBIGU, REFS_BAB5, panggil_llm=mock_karang)
    cek("llm-mock-karangan-ditolak",
        "(N., 2025)" in hasil2["teks_baru"]
        and len(hasil2["ambigu"]) == 1,
        repr(hasil2))


def test_konsolidasi_pustaka_gabungan():
    panen = [
        "Bambang Arianto (2021). Pengembangan UMKM Digital di Masa "
        "Pandemi Covid-19. Jurnal Bisnis.",
        "Rahmi Rosita (2020). Pengaruh Pandemi Covid-19 terhadap UMKM "
        "di Indonesia. Jurnal Bisnis.",
        "Wan Laura Hardilawati (2020). Strategi Bertahan UMKM di Tengah "
        "Pandemi Covid-19. Jurnal Akuntansi.",
        "Chege Samwel Macharia, & Wang Daoping (2020). The influence "
        "of technology innovation on SME performance. Jurnal Bisnis.",
    ]
    teks_bab = [
        "Bab satu mengutip (Vial, 2019) dan (Teece, 2018) "
        "dan (Arianto, 2021).",
        "Bab dua mengutip (Rogers, 2003) dan (Davis, 1989) "
        "dan (Macharia dan Daoping, 2020).",
    ]
    pustaka, info = SG.gabung_pustaka_dengan_info(teks_bab, panen)
    gabung = "\n".join(pustaka)
    cek("pustaka-masuk-vial-2019", "Vial (2019)" in gabung, gabung)
    cek("pustaka-masuk-teece-2018", "Teece (2018)" in gabung, gabung)
    cek("pustaka-masuk-rogers-2003", "Rogers (2003)" in gabung, gabung)
    cek("pustaka-masuk-davis-1989", "Davis (1989)" in gabung, gabung)
    cek("pustaka-tidak-duplikat-arianto",
        gabung.count("Arianto (2021)") == 1
        and gabung.count("Arianto") >= 1,
        gabung)
    cek("pustaka-tidak-duplikat-macharia-daoping",
        info["ditambah_dari_badan"] == 4 and info["total"] == 8,
        repr(info))
    cek("pustaka-urutan-panen-dulu",
        pustaka[0].startswith("Bambang Arianto")
        and "Vial (2019)" in pustaka[4],
        repr(pustaka))
    cek("pustaka-entri-badan-tanpa-judul-karangan",
        "judul dan sumber belum tersedia di panen" in pustaka[4],
        repr(pustaka[4]))


def test_gagal_bersih_sesudah_repair_habis():
    try:
        SG.periksa_dan_perbaiki_bab(5, TEKS_AMBIGU, REFS_BAB5)
        cek("gagal-bersih-raise", False, "tidak raise")
    except SG.GagalSitasiBersih as e:
        cek("gagal-bersih-pesan-manusia",
            str(e) == SG.PESAN_GAGAL_BERSIH, repr(str(e)))
        cek("gagal-bersih-pesan-tanpa-error-mentah",
            "Traceback" not in str(e) and "Exception" not in str(e),
            repr(str(e)))
        cek("gagal-bersih-atribut-rincian",
            e.nomor_bab == 5 and len(e.inisial_tersisa) == 1,
            repr((e.nomor_bab, e.inisial_tersisa)))
    hasil = SG.periksa_dan_perbaiki_bab(
        5, TEKS_AMBIGU, REFS_BAB5, gagal_keras=False)
    cek("gagal-bersih-flag-tanpa-raise",
        hasil["lolos"] is False
        and hasil["pesan"] == SG.PESAN_GAGAL_BERSIH,
        repr(hasil))


def test_periksa_dan_perbaiki_lolos_sesudah_repair():
    hasil = SG.periksa_dan_perbaiki_bab(1, TEKS_TUNGGAL, REFS_TUNGGAL)
    cek("periksa-repair-lolos",
        hasil["lolos"] is True
        and "(Alfarizi, 2024)" in hasil["teks_baru"],
        repr(hasil))


def test_refs_dari_data():
    cek("refs-dari-list",
        SG.refs_dari_data(["A (2020). X.", "B (2021). Y."])
        == ["A (2020). X.", "B (2021). Y."])
    cek("refs-dari-dict",
        SG.refs_dari_data({"refs": ["A (2020). X."]})
        == ["A (2020). X."])
    cek("refs-dari-data-salah-kosong",
        SG.refs_dari_data("bukan-list") == [])


def test_inisial_multi_tertangkap():
    teks22 = ("(B.E., 2019) " * 5 + "(H., 2025) " * 4
              + "(M., 2024) " * 3 + "(Z., 2023) " * 3
              + "(E., 2021) " * 2 + "(N., 2024) " * 2
              + "(T.S., 2025) " * 2 + "(N., 2025)")
    temu = SG.pindai_inisial(teks22)
    cek("inisial-22-layer1", len(temu) == 22, repr(temu))
    cek("inisial-multi-BE-TS",
        ("BE", "2019") in [(t["inisial"], t["tahun"]) for t in temu]
        and ("TS", "2025") in [(t["inisial"], t["tahun"]) for t in temu],
        repr(temu))


def test_repair_multi_dan_tanpa_koma():
    refs_nyata = ["Putra B.E. (2019)", "Wulan T.S. (2025)",
                  "Alfarizi M. (2024)"]
    kand = SG._kandidat_dari_refs(refs_nyata)
    cek("kandidat-tanpa-koma",
        ("Putra", "2019", ("B", "E")) in [
            (k["surname"], k["tahun"], tuple(k["inisial"])) for k in kand]
        and ("Wulan", "2025", ("T", "S")) in [
            (k["surname"], k["tahun"], tuple(k["inisial"])) for k in kand]
        and ("Alfarizi", "2024", ("M",)) in [
            (k["surname"], k["tahun"], tuple(k["inisial"])) for k in kand],
        repr(kand))
    r = SG.repair_bab("Menurut (B.E., 2019), (T.S., 2025), (M., 2024).",
                      refs_nyata)
    cek("repair-multi-tanpa-koma",
        "(Putra, 2019)" in r["teks_baru"]
        and "(Wulan, 2025)" in r["teks_baru"]
        and "(Alfarizi, 2024)" in r["teks_baru"]
        and r["jumlah_sisa"] == 0, repr(r))


def test_inisial_tunggal_tidak_ditebak_ke_multi():
    r = SG.repair_bab("Menurut (B., 2019).", ["Putra B.E. (2019)"])
    cek("tunggal-tidak-tebak-multi",
        "(B., 2019)" in r["teks_baru"]
        and ("B", "2019") in [(t["inisial"], t["tahun"])
                              for t in r["tanpa_kandidat"]], repr(r))


if __name__ == "__main__":
    print("Uji sitasi anti gagal (G4)")
    test_inisial_bab5_tertangkap()
    test_cakupan_bab4_di_bawah_ambang()
    test_cakupan_ambang_50_persen_lolos()
    test_repair_tunggal()
    test_ambigu_tidak_diganti_buta()
    test_ambigu_konteks_kedua_memilih()
    test_llm_mock_hanya_kandidat()
    test_konsolidasi_pustaka_gabungan()
    test_gagal_bersih_sesudah_repair_habis()
    test_periksa_dan_perbaiki_lolos_sesudah_repair()
    test_refs_dari_data()
    test_inisial_multi_tertangkap()
    test_repair_multi_dan_tanpa_koma()
    test_inisial_tunggal_tidak_ditebak_ke_multi()
    print("LULUS %d, GAGAL %d" % (LULUS, len(GAGAL)))
    if GAGAL:
        print("GAGAL: %s" % ", ".join(GAGAL))
        sys.exit(1)
    sys.exit(0)
