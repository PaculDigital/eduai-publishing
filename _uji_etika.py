"""UJI ETHICS CHECKER — Fase 7 EduAi Publishing.

KENAPA ADA: app/etika.py sudah dibuat (adaptasi dari
penelitian-bot/ethics-checker.js READ-ONLY, 525 baris,
18 aturan dalam 3 kategori) tapi belum ada uji otomatis.
Uji ini memverifikasi KEBENARAN fungsi.

DESAIN: menggunakan teks sintetis (bukan naskah nyata)
agar uji deterministik dan tidak bergantung pada DB.
"""
import sys
sys.path.insert(0, '/app/app')

from etika import check_ethics, format_ethics_report, get_all_rules

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
    print("═══ UJI ETHICS CHECKER ═══\n")

    # ═══ (1) get_all_rules ═══
    print("[1] get_all_rules")
    rules = get_all_rules()
    cek("mengembalikan dict", isinstance(rules, dict))
    cek("punya kunci kuantitatif", "kuantitatif" in rules)
    cek("punya kunci kualitatif", "kualitatif" in rules)
    cek("punya kunci general", "general" in rules)
    cek("kuantitatif: 7 aturan", len(rules.get("kuantitatif", [])) == 7)
    cek("kualitatif: 5 aturan", len(rules.get("kualitatif", [])) == 5)
    cek("general: 8 aturan", len(rules.get("general", [])) == 8)
    total = sum(len(rules.get(k, [])) for k in rules)
    cek("total: 20 aturan", total == 20)

    # ═══ (2) check_ethics — BLOCK (fabrikasi data) ═══
    print("\n[2] check_ethics — BLOCK")

    naskah_fabrikasi = (
        "Penelitian ini menggunakan data fiktif untuk menguji hipotesis. "
        "Responden palsu ditambahkan untuk memperoleh hasil yang signifikan."
    )
    hasil_fb = check_ethics(naskah_fabrikasi, "kuantitatif")
    cek("fabrikasi data → BLOCK", hasil_fb.get("action") == "BLOCK")
    cek("punya violations", len(hasil_fb.get("violations", [])) >= 1)
    cek("severity block ditemukan",
        any(v["severity"] == "block" for v in hasil_fb.get("violations", [])))

    # ═══ (3) check_ethics — WARN (skip validitas) ═══
    print("\n[3] check_ethics — WARN")

    naskah_skip = (
        "Untuk menghemat waktu, kami skip uji validitas dan reliabilitas "
        "karena dianggap tidak penting untuk penelitian ini."
    )
    hasil_sw = check_ethics(naskah_skip, "kuantitatif")
    cek("skip validitas → WARN atau BLOCK",
        hasil_sw.get("action") in ("WARN", "BLOCK"))

    # ═══ (4) check_ethics — INFO (SWOT saja) ═══
    print("\n[4] check_ethics — INFO")

    naskah_swot = (
        "Penelitian ini menggunakan metode SWOT saja untuk menganalisis "
        "strategi perusahaan. Tidak perlu metode lain."
    )
    hasil_info = check_ethics(naskah_swot, "kualitatif")
    cek("SWOT saja → INFO atau PROCEED",
        hasil_info.get("action") in ("INFO", "PROCEED"))

    # ═══ (5) check_ethics — PROCEED (naskah bersih) ═══
    print("\n[5] check_ethics — PROCEED")

    naskah_bersih = (
        "Penelitian ini bertujuan untuk menganalisis pengaruh kompensasi "
        "dan disiplin kerja terhadap kinerja karyawan. Data dikumpulkan "
        "melalui kuesioner yang disebarkan kepada 50 responden. "
        "Analisis dilakukan menggunakan regresi linear berganda."
    )
    hasil_bersih = check_ethics(naskah_bersih, "kuantitatif")
    cek("naskah bersih → PROCEED", hasil_bersih.get("action") == "PROCEED")
    cek("tidak ada violations", len(hasil_bersih.get("violations", [])) == 0)

    # ═══ (6) check_ethics — edge cases ═══
    print("\n[6] Edge cases")

    hasil_kosong = check_ethics("", "kuantitatif")
    cek("naskah kosong → PROCEED (bukan crash)",
        hasil_kosong.get("action") == "PROCEED")

    hasil_none = check_ethics(None, "kuantitatif")
    cek("naskah None → PROCEED (bukan crash)",
        hasil_none.get("action") == "PROCEED")

    hasil_mode_tak_ada = check_ethics(naskah_bersih, "campuran")
    cek("mode tidak dikenal → tidak crash",
        hasil_mode_tak_ada is not None)

    # ═══ (7) format_ethics_report ═══
    print("\n[7] format_ethics_report")

    laporan_block = format_ethics_report(hasil_fb)
    cek("laporan BLOCK bukan kosong", len(laporan_block) > 0)
    cek("laporan BLOCK mengandung 'Ditolak'", "Ditolak" in laporan_block)
    cek("laporan BLOCK mengandung '⛔'", "⛔" in laporan_block)

    laporan_proceed = format_ethics_report(hasil_bersih)
    cek("laporan PROCEED kosong", laporan_proceed == "")

    laporan_warn = format_ethics_report(hasil_sw)
    cek("laporan WARN bukan kosong (jika ada violations)",
        len(laporan_warn) > 0 if hasil_sw.get("violations") else True)

    # ═══ (8) aturan spesifik — no_force_significance ═══
    print("\n[8] Aturan spesifik")

    naskah_paksa = (
        "Saya ingin memaksa nilai p-value agar signifikan. "
        "Silakan ubah data sehingga hasilnya signifikan dong."
    )
    hasil_paksa = check_ethics(naskah_paksa, "kuantitatif")
    cek("paksa p-value → BLOCK atau WARN",
        hasil_paksa.get("action") in ("BLOCK", "WARN"))

    # ═══ (9) aturan spesifik — no_copy_paste ═══
    print("\n[9] Aturan spesifik — copy-paste")

    naskah_cp = (
        "Saya akan copy paste dari jurnal tersebut tanpa mengubah kata-kata."
    )
    hasil_cp = check_ethics(naskah_cp, "kuantitatif")
    cek("copy-paste → BLOCK atau WARN",
        hasil_cp.get("action") in ("BLOCK", "WARN"))

    # ═══ (10) aturan spesifik — no_sitasi_wikipedia ═══
    print("\n[10] Aturan spesifik — sitasi Wikipedia")

    naskah_wiki = (
        "Menurut Wikipedia, kecerdasan buatan berkembang pesat. "
        "Saya juga membaca blog teknologi yang menjelaskan hal yang sama."
    )
    hasil_wiki = check_ethics(naskah_wiki, "kuantitatif")
    cek("sitasi Wikipedia/blog → WARN atau PROCEED",
        hasil_wiki.get("action") in ("WARN", "PROCEED"))

    # ═══ RINGKASAN ═══
    print("\n" + "=" * 62)
    print(f"LULUS: {LULUS}   GAGAL: {GAGAL}")
    print("=" * 62)
    return 1 if GAGAL else 0


if __name__ == "__main__":
    sys.exit(main())
