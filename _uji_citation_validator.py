"""UJI CITATION VALIDATOR — Fase 6 EduAi Publishing.

KENAPA ADA: app/citation_validator.py sudah dibuat (adaptasi dari
penelitian-bot/citation-validator.js READ-ONLY) tapi belum ada uji
otomatis di container. Gerbang kode (pyflakes) tidak menangkap bug
logika — hanya syntax error. Uji ini memverifikasi KEBENARAN fungsi.

DESAIN: menggunakan data sintetis (bukan literatur nyata) agar uji
deterministik dan tidak bergantung pada DB atau API luar.
"""
import sys
sys.path.insert(0, '/app/app')

from citation_validator import (
    extract_citations,
    build_author_index,
    is_citation_valid,
    validate_content,
    format_report,
)

LULUS = 0
GAGAL = 0


def cek(nama, kondisi, detail=""):
    global LULUS, GAGAL
    if kondisi:
        LULUS += 1
        print(f"  ✅ {nama}")
    else:
        GAGAL += 1
        print(f"  ❌ {nama} {detail}")


def main():
    print("═══ UJI CITATION VALIDATOR ═══\n")

    # ── Literatur sintetis ──
    literature = [
        {
            "title": "Pengaruh Kompensasi terhadap Kinerja Karyawan",
            "authors": "Smith, John and Doe, Jane",
            "year": "2023",
        },
        {
            "title": "Disiplin Kerja dan Produktivitas",
            "authors": "Brown, Alice",
            "year": "2022",
        },
        {
            "title": "Motivasi Intrinsik dalam Organisasi",
            "authors": "Johnson, Robert",
            "year": "2021",
        },
    ]

    # ═══ (1) extract_citations ═══
    print("[1] extract_citations")

    # (a) satu sitasi valid
    text_a = "Penelitian sebelumnya menunjukkan hasil yang signifikan (Smith, 2023)."
    cit_a = extract_citations(text_a)
    cek("1 sitasi ditemukan", len(cit_a) == 1)
    if cit_a:
        cek("  author = Smith", cit_a[0]["author"] == "Smith")
        cek("  year = 2023", cit_a[0]["year"] == "2023")

    # (b) sitasi et al.
    text_b = "Studi lain juga membuktikan hal ini (Smith et al., 2023)."
    cit_b = extract_citations(text_b)
    cek("sitasi et al. ditemukan", len(cit_b) == 1)
    if cit_b:
        cek("  author = Smith et al.", "et al." in cit_b[0]["author"])

    # (c) sitasi multi-penulis
    text_c = "Hasilnya konsisten (Smith & Doe, 2023)."
    cit_c = extract_citations(text_c)
    cek("sitasi multi-penulis ditemukan", len(cit_c) == 1)

    # (d) tidak ada sitasi
    text_d = "Tidak ada sitasi di kalimat ini."
    cit_d = extract_citations(text_d)
    cek("tanpa sitasi → 0", len(cit_d) == 0)

    # (e) teks kosong
    cit_e = extract_citations("")
    cek("teks kosong → 0", len(cit_e) == 0)

    # (f) teks None
    cit_f = extract_citations(None)
    cek("teks None → 0", len(cit_f) == 0)

    # ═══ (2) build_author_index ═══
    print("\n[2] build_author_index")
    idx = build_author_index(literature)
    cek("indeks dibangun", len(idx.get("byLastName", {})) > 0)
    cek("byYear tidak kosong", len(idx.get("byYear", {})) > 0)

    # (b) author tidak ada
    idx_kosong = build_author_index([])
    cek("literature kosong → indeks kosong",
        len(idx_kosong.get("byLastName", {})) == 0)

    # ═══ (3) is_citation_valid ═══
    print("\n[3] is_citation_valid")

    # (a) sitasi valid (Smith, 2023)
    hasil_a = is_citation_valid(
        {"author": "Smith", "year": "2023"}, idx
    )
    cek("Smith 2023 → valid", hasil_a.get("valid") is True)

    # (b) sitasi tidak valid (Jones, 2099)
    hasil_b = is_citation_valid(
        {"author": "Jones", "year": "2099"}, idx
    )
    cek("Jones 2099 → tidak valid", hasil_b.get("valid") is False)

    # (c) sitasi valid dengan initial (S. Smith, 2023)
    hasil_c = is_citation_valid(
        {"author": "Sa Smith", "year": "2023"}, idx
    )
    cek("S. Smith 2023 → valid (partial match)", hasil_c.get("valid") is True)

    # ═══ (4) validate_content ═══
    print("\n[4] validate_content")

    # (a) konten dengan sitasi valid → ok=True
    content_a = (
        "Penelitian Smith (2023) menunjukkan bahwa kompensasi berpengaruh. "
        "Temuan ini sejalan dengan Doe (2023)."
    )
    val_a = validate_content(content_a, literature)
    cek("sitasi valid → ok=True", val_a.get("ok") is True)
    cek("invalidCitations = 0", len(val_a.get("invalidCitations", [])) == 0)

    # (b) konten dengan sitasi tidak valid → ok=False
    content_b = (
        "Menurut teori (Jones, 2099), kompensasi sangat penting. "
        "Ini adalah klaim panjang yang tidak memiliki sitasi yang valid di daftar literatur."
    )
    val_b = validate_content(content_b, literature)
    cek("sitasi tidak valid → ok=False", val_b.get("ok") is False)
    cek("invalidCitations > 0", len(val_b.get("invalidCitations", [])) > 0)

    # (c) klaim panjang tanpa sitasi → unsupportedClaims
    content_c = (
        "Hasil penelitian menunjukkan bahwa terdapat pengaruh yang sangat signifikan "
        "antara variabel independen dan variabel dependen dalam konteks organisasi modern. "
        "Temuan ini membuktikan bahwa hipotesis yang diajukan sebelumnya dapat diterima."
    )
    val_c = validate_content(content_c, literature)
    cek("klaim panjang tanpa sitasi terdeteksi", len(val_c.get("unsupportedClaims", [])) > 0)

    # (d) teks kosong → ok=True (bukan crash)
    val_d = validate_content("", literature)
    cek("teks kosong → ok=True (bukan crash)", val_d.get("ok") is True)

    # (e) None → ok=True (bukan crash)
    val_e = validate_content(None, literature)
    cek("teks None → ok=True (bukan crash)", val_e.get("ok") is True)

    # ═══ (5) format_report ═══
    print("\n[5] format_report")
    laporan = format_report(val_b)
    cek("laporan bukan kosong", len(laporan) > 0)
    cek("laporan mengandung 'Citation Validation'", "Citation Validation" in laporan)
    cek("laporan mengandung 'ISSUES FOUND'", "ISSUES FOUND" in laporan)

    laporan_ok = format_report(val_a)
    cek("laporan ok mengandung 'PASSED'", "PASSED" in laporan_ok)

    # ═══ (6) edge case: literature None ═══
    print("\n[6] Edge cases")
    val_f = validate_content(content_a, None)
    cek("literature None → tidak crash", val_f is not None)

    val_g = validate_content(content_a, [])
    cek("literature kosong → tidak crash", val_g is not None)

    # ═══ RINGKASAN ═══
    print("\n" + "=" * 62)
    print(f"LULUS: {LULUS}   GAGAL: {GAGAL}")
    print("=" * 62)
    return 1 if GAGAL else 0


if __name__ == "__main__":
    sys.exit(main())
