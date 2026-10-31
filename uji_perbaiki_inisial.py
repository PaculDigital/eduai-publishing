"""Uji perbaikan inisial job 228, Gas Bos 31 Okt 2026 19:52, tanpa Jev.

Dua langkah yang diuji:
1. Prompt penulis memakai nama belakang lengkap saja, tanpa inisial.
2. Jaring pengaman gerbang subbab: inisial sisa yang tidak bisa
   diperbaiki pasti dihapus deterministik, asal subbab masih punya
   minimal 1 sitasi snapshot sah dan tidak ada sitasi luar tersisa.
   Bila syarat itu tidak terpenuhi, tetap GagalSubbab.

Jalankan dari checkout: python3 uji_perbaiki_inisial.py
Keluar 0 bila semua lulus, 1 bila ada yang gagal. Mock LLM, tanpa
jaringan, tanpa DB produksi, tanpa buku baru.
"""
import io
import os
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=""):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print("  OK %s" % nama)
    else:
        GAGAL += 1
        print("  GAGAL %s   %s" % (nama, bukti))


REFS = [
    {"authors": ["Masina N.P.S."], "year": 2026,
     "title": "Challenges faced by informal sector entrepreneurs",
     "journal": "Journal of Sustainable Development Law and Policy",
     "doi": "", "type": "article", "source": "Scopus"},
    {"authors": ["Saenz-Royo C."], "year": 2025,
     "title": "Wind of change for agent decisions",
     "journal": "Socio Economic Planning Sciences",
     "doi": "", "type": "article", "source": "Scopus"},
    {"authors": ["Daskevic D."], "year": 2025,
     "title": "Alignment of innovation diffusion and project management",
     "journal": "Business Management and Economics Engineering",
     "doi": "", "type": "article", "source": "Scopus"},
    {"authors": ["Kankanamge A.K.S.U."], "year": 2026,
     "title": "Smart technology adoption evidence",
     "journal": "Human Behavior and Emerging Technologies",
     "doi": "", "type": "article", "source": "Scopus"},
    {"authors": ["Chege Samwel Macharia", "Wang Daoping"], "year": 2020,
     "title": "The influence of technology innovation on SME performance",
     "journal": "Technology in Society",
     "doi": "", "type": "article", "source": "CrossRef"},
]

ROWS = []
for ref in REFS:
    # Baris snapshot seperti dari pra_panen.ambil_snapshot, dengan
    # ref_dict yang sama seperti yang dipakai gerbang.
    nama = ref["authors"][0].split()[0]
    ROWS.append({
        "kunci": nama.lower().replace("a", "a"),
        "alias": [],
        "tahun": str(ref["year"]),
        "surname_tampil": nama,
        "ref_dict": dict(ref),
    })
# Perbaiki kunci agar cocok dengan nama belakang yang benar.
ROWS[0]["kunci"] = "masina"
ROWS[1]["kunci"] = "saenz-royo"
ROWS[1]["surname_tampil"] = "Saenz-Royo"
ROWS[2]["kunci"] = "daskevic"
ROWS[3]["kunci"] = "kankanamge"
ROWS[4]["kunci"] = "macharia"


def teks_27_plus_4():
    """Teks subbab: 27 sitasi snapshot sah + 4 inisial tanpa kandidat."""
    kalimat = []
    sah = [
        "(Masina, 2026)", "(Saenz-Royo, 2025)", "(Daskevic, 2025)",
        "(Kankanamge, 2026)", "(Macharia, 2020)",
    ]
    for i in range(27):
        sit = sah[i % len(sah)]
        kalimat.append(
            "Kalimat argumen nomor %s yang didukung oleh referensi %s "
            "tentang adopsi teknologi dan kinerja usaha kecil." % (i + 1, sit))
    kalimat.append(
        "Kalimat dengan sitasi inisial yang tidak bisa diperbaiki "
        "pasti (Z., 2026) dan (Q., 2025) di tengah argumen.")
    kalimat.append(
        "Kalimat lain dengan sitasi inisial (X., 2024) dan (W., 2023) "
        "yang juga tidak punya kandidat di daftar snapshot.")
    return "\n\n".join(kalimat)


def main():
    import buku_umum_pipeline as pipe
    from app.gerbang_subbab import (
        periksa_subbab, hapus_sitasi_inisial, GagalSubbab)

    print("[1] NAMA BELAKANG DARI PENULIS")
    cek("Masina N.P.S. menjadi Masina",
        pipe._nama_belakang_dari_penulis("Masina N.P.S.") == "Masina")
    cek("Saenz-Royo C. menjadi Saenz-Royo",
        pipe._nama_belakang_dari_penulis("Saenz-Royo C.") == "Saenz-Royo")
    cek("Daskevic D. menjadi Daskevic",
        pipe._nama_belakang_dari_penulis("Daskevic D.") == "Daskevic")
    cek("Kankanamge A.K.S.U. menjadi Kankanamge",
        pipe._nama_belakang_dari_penulis("Kankanamge A.K.S.U.")
        == "Kankanamge")
    cek("Chege Samwel Macharia menjadi Macharia",
        pipe._nama_belakang_dari_penulis("Chege Samwel Macharia")
        == "Macharia")
    cek("Porter, M. E. menjadi Porter",
        pipe._nama_belakang_dari_penulis("Porter, M. E.") == "Porter")

    print("[2] BARIS REFERENSI UNTUK PENULIS, TANPA INISIAL")
    baris = pipe._daftar_referensi_untuk_penulis(REFS)
    teks_daftar = "\n".join(baris)
    cek("Masina (2026) ada di daftar penulis",
        "Masina (2026). Challenges faced by informal sector entrepreneurs."
        in teks_daftar, teks_daftar)
    cek("Saenz-Royo (2025) ada di daftar penulis",
        "Saenz-Royo (2025). Wind of change for agent decisions."
        in teks_daftar)
    cek("Daftar penulis tidak memuat N.P.S. atau A.K.S.U.",
        "N.P.S." not in teks_daftar and "A.K.S.U." not in teks_daftar,
        teks_daftar)
    cek("Sitasi penulis Masina benar, bukan N.P.S.",
        pipe._sitasi_untuk_penulis(REFS[0]) == "(Masina, 2026)",
        pipe._sitasi_untuk_penulis(REFS[0]))
    cek("Sitasi penulis dua penulis memakai nama belakang",
        pipe._sitasi_untuk_penulis(REFS[4])
        == "(Macharia & Daoping, 2020)",
        pipe._sitasi_untuk_penulis(REFS[4]))

    print("[3] PROMPT PENULIS, EDITOR, SKEPTIK")
    prompt_a = pipe.architect_prompt(
        3, "Adopsi Teknologi", "3.1", "Definisi", "key points",
        "ringkasan", refs=REFS, jenis="referensi", dari_snapshot=True)
    cek("Prompt architect memuat aturan nama belakang lengkap",
        "benar Masina et al. (2026)" in prompt_a
        and "salah M. et al. (2026)" in prompt_a
        and "salah N.P.S. (2026)" in prompt_a)
    cek("Prompt architect tidak memakai (N.P.S., 2026) sebagai sitasi sah",
        "(N.P.S., 2026)" not in prompt_a)
    prompt_e = pipe.editor_prompt(
        "Definisi", "draf", "kritik", "saran",
        jenis="referensi", refs=REFS, dari_snapshot=True)
    cek("Prompt editor memuat Masina (2026) di daftar, bukan N.P.S.",
        "Masina (2026)." in prompt_e and "(N.P.S., 2026)" not in prompt_e)
    prompt_s = pipe.skeptic_prompt(
        "Definisi", "draf", refs=REFS, jenis="referensi",
        dari_snapshot=True)
    cek("Prompt skeptik memuat Masina (2026) di daftar",
        "Masina (2026)." in prompt_s)

    print("[4] INISIAL YANG BISA DIPERBAIKI, DIPERBAIKI DULU")
    r = periksa_subbab(
        "Menurut (N.P.S., 2026), sektor informal menghadapi tantangan "
        "teknologi yang nyata dan terukur di banyak kota.",
        ROWS, bab=3, subbab="3.1")
    cek("N.P.S. (2026) diperbaiki menjadi Masina, bukan langsung dihapus",
        r["lolos"] and r["inisial_sisa"] == []
        and "Masina" in r["teks_bersih"], str(r))

    print("[5] JARING PENGAMAN: 27 SAH + 4 INISIAL TANPA KANDIDAT")
    teks = teks_27_plus_4()
    r1 = periksa_subbab(teks, ROWS, bab=3, subbab="3.1")
    cek("Sebelum pengaman, gerbang gagal karena inisial sisa",
        (not r1["lolos"]) and len(r1["inisial_sisa"]) == 4
        and r1["snapshot_count"] >= 1 and r1["luar_sisa"] == [],
        str(r1))
    cek("Syarat jaring pengaman terpenuhi untuk kasus ini",
        pipe._boleh_jaring_pengaman_inisial(r1))
    bersih, dihapus = hapus_sitasi_inisial(r1["teks_bersih"])
    cek("Pengaman menghapus tepat 4 sitasi inisial",
        len(dihapus) == 4, str(dihapus))
    r2 = periksa_subbab(bersih, ROWS, bab=3, subbab="3.1")
    cek("Sesudah pengaman, inisial 0 dan subbab lolos",
        r2["lolos"] and r2["inisial_sisa"] == []
        and r2["snapshot_count"] >= 1, str(r2))
    cek("Kalimat yang kehilangan sitasi tetap ada tanpa sitasi",
        "Kalimat dengan sitasi inisial yang tidak bisa diperbaiki pasti"
        in bersih
        and "Kalimat lain dengan sitasi inisial" in bersih)

    print("[6] JARING PENGAMAN TIDAK BOLEH MENUTUPI MASALAH LAIN")
    cek("0 sitasi snapshot tidak boleh pakai jaring pengaman",
        not pipe._boleh_jaring_pengaman_inisial({
            "inisial_sisa": [{"raw": "(Z., 2026)"}],
            "snapshot_count": 0, "luar_sisa": [],
            "masalah": ["0 sitasi snapshot formal",
                        "4 sitasi inisial saja masih tersisa"]}))
    cek("Sitasi luar tersisa tidak boleh pakai jaring pengaman",
        not pipe._boleh_jaring_pengaman_inisial({
            "inisial_sisa": [{"raw": "(Z., 2026)"}],
            "snapshot_count": 5, "luar_sisa": ["(Smith, 2020)"],
            "masalah": ["1 sitasi luar daftar masih tersisa",
                        "4 sitasi inisial saja masih tersisa"]}))
    cek("Tanpa inisial sisa tidak boleh pakai jaring pengaman",
        not pipe._boleh_jaring_pengaman_inisial({
            "inisial_sisa": [], "snapshot_count": 5, "luar_sisa": [],
            "masalah": []}))

    print("[7] PEMANGGIL GERBANG: MOCK LLM, KASUS JOB 228")
    teks_tetap = teks_27_plus_4()

    def palsu(prompt, max_tokens=3000, timeout=120, retries=5):
        if "Buat ringkasan" in (prompt or ""):
            return ("TOKOH UTAMA: Adopsi teknologi.\n"
                    "KONSEP INTI: Adopsi teknologi.\n"
                    "KHAS BAB INI: Definisi.\n\nRingkasan singkat.")
        return teks_tetap

    lama = pipe.call_llm
    pipe.call_llm = palsu
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, "visual"), exist_ok=True)
    pipe._FOLDER_UTAS[threading.get_ident()] = tmp
    try:
        buf = io.StringIO()
        lama_stdout = sys.stdout
        sys.stdout = buf
        try:
            final, summary, wc, cit = pipe.generate_sub_bab(
                3, "Adopsi Teknologi", "3.1", "Definisi", "key points",
                "ringkasan", refs=REFS, jenis="referensi",
                dari_snapshot=True, snapshot_rows=ROWS)
        finally:
            sys.stdout = lama_stdout
        keluar = buf.getvalue()
    except GagalSubbab as e:
        cek("Pemanggil gerbang tidak gagal untuk kasus 27+4",
            False, str(e))
        final = ""
        keluar = ""
    finally:
        pipe.call_llm = lama
        pipe._FOLDER_UTAS.pop(threading.get_ident(), None)
    if final:
        cek("Pemanggil gerbang lolos lewat jaring pengaman",
            "jaring pengaman" in keluar and "inisial dihapus 4" in keluar,
            keluar[-500:])
        cek("Teks akhir pemanggil tidak memuat inisial Z., Q., X., W.",
            "(Z., 2026)" not in final and "(Q., 2025)" not in final
            and "(X., 2024)" not in final and "(W., 2023)" not in final)
        cek("Teks akhir pemanggil masih memuat sitasi snapshot sah",
            "(Masina, 2026)" in final and "(Macharia, 2020)" in final)

    print("[8] PEMANGGIL GERBANG TETAP GAGAL BILA 0 SITASI SAH")
    teks_kosong = ("Kalimat tanpa sitasi sama sekali, hanya argumen "
                   "umum tentang teknologi dan usaha kecil.")

    def palsu_kosong(prompt, max_tokens=3000, timeout=120, retries=5):
        if "Buat ringkasan" in (prompt or ""):
            return ("TOKOH UTAMA: Adopsi.\nKONSEP INTI: Adopsi.\n"
                    "KHAS BAB INI: Definisi.\n\nRingkasan.")
        return teks_kosong

    pipe.call_llm = palsu_kosong
    tmp2 = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp2, "visual"), exist_ok=True)
    pipe._FOLDER_UTAS[threading.get_ident()] = tmp2
    try:
        buf = io.StringIO()
        lama_stdout = sys.stdout
        sys.stdout = buf
        try:
            pipe.generate_sub_bab(
                3, "Adopsi Teknologi", "3.1", "Definisi", "key points",
                "ringkasan", refs=REFS, jenis="referensi",
                dari_snapshot=True, snapshot_rows=ROWS)
            cek("0 sitasi sah tetap GagalSubbab", False, "tidak raise")
        except GagalSubbab:
            cek("0 sitasi sah tetap GagalSubbab", True)
        finally:
            sys.stdout = lama_stdout
    finally:
        pipe.call_llm = lama
        pipe._FOLDER_UTAS.pop(threading.get_ident(), None)

    print("LULUS %s, GAGAL %s" % (LULUS, GAGAL))
    return 0 if GAGAL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
