"""UJI KONSISTENSI — verifikasi kebenaran 4 cek di app/konsistensi.py.

KENAPA ADA: Fase 5 sudah LIVE tapi tidak ada uji otomatis di container.
Uji ini memverifikasi KEBENARAN fungsi, bukan hanya apakah bisa di-import.
"""
import sys
sys.path.insert(0, '/app/app')

from konsistensi import (
    check_judul_consistency,
    check_variable_consistency,
    check_hipotesis_consistency,
    check_ov_consistency,
    check_consistency,
    format_laporan,
    catatan_untuk_ai,
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
    print("═══ UJI KONSISTENSI ═══\n")

    # Data uji dengan format YANG BENAR (sesuai brief.py baris 56)
    brief = {
        "judul": "KINERJA KARYAWAN",
        "variabel": [
            {"nama": "X1", "label": "Kompensasi Finansial", "jenis": "independen"},
            {"nama": "X2", "label": "Disiplin Kerja", "jenis": "independen"},
            {"nama": "Y",  "label": "Kinerja", "jenis": "dependen"},
        ],
        "hipotesis": ["H1: Kompensasi berpengaruh terhadap Kinerja",
                       "H2: Disiplin berpengaruh terhadap Kinerja"],
        "ov": "Kinerja diukur dengan skala Likert 5 poin",
    }

    # Section state valid: content >= 400 char (ambang check_variable/hipotesis)
    section_lengkap = [
        {"section_id": "1.1", "title": "Latar Belakang",
         "content": "KINERJA KARYAWAN menjadi fokus utama penelitian ini. Variabel X1 yang merupakan Kompensasi Finansial dan X2 yang merupakan Disiplin Kerja serta Y yang merupakan Kinerja karyawan diukur dalam penelitian ini. H1 dan H2 dinyatakan sebagai hipotesis yang akan diuji. Penelitian ini bertujuan untuk membuktikan pengaruh antara variabel independen dan dependen."},
        {"section_id": "4.1", "title": "Hasil Penelitian",
         "content": "Hasil penelitian menunjukkan bahwa Kompensasi Finansial (X1) dan Disiplin Kerja (X2) berpengaruh secara signifikan terhadap Kinerja (Y). H1 yang menyatakan bahwa Kompensasi berpengaruh terhadap Kinerja diterima. H2 yang menyatakan bahwa Disiplin berpengaruh terhadap Kinerja juga diterima. Temuan ini konsisten dengan teori motivasi kerja yang telah dipublikasikan oleh para ahli."},
        {"section_id": "3.1", "title": "Definisi Operasional",
         "content": "Kinerja karyawan diukur menggunakan skala Likert 5 poin. Variabel Y (Kinerja) merupakan variabel dependen yang diukur melalui indikator kinerja yang telah ditetapkan oleh perusahaan."},
    ]

    # ── (1) check_judul: judul PERSIS → 0 issues ──
    print("[1] check_judul_consistency")
    r1 = check_judul_consistency(brief, section_lengkap)
    cek("judul PERSIS → 0 issues", len(r1.get("issues", [])) == 0)
    cek("judul PERSIS → summary string", isinstance(r1.get("summary"), str))

    # (2) judul HAMPIR PERSIS (beda 1 kata) → frasa tidak ditemukan di bawah ambang → 0 issues (DESAIN)
    section_judul_beda = [
        {"section_id": "1.1", "title": "Latar Belakang",
         "content": "Kinerja pegawai merupakan aspek penting dalam organisasi. Penelitian ini membahas tentang KINERJA PEGAWAI yang menjadi fokus utama. Variabel X1 (Kompensasi) dan X2 (Disiplin) serta Y (Kinerja) diukur dalam penelitian ini. H1 dan H2 dinyatakan."},
    ]
    r2 = check_judul_consistency(brief, section_judul_beda)
    cek("judul hampir persis (1 kata beda) → 0 issues (desain: frasa di bawah ambang 0.6)",
        len(r2.get("issues", [])) == 0)

    # (3) variabel semua disebut → 0 issues
    print("\n[2] check_variable_consistency")
    r3 = check_variable_consistency(brief, section_lengkap)
    cek("semua variabel disebut → 0 issues", len(r3.get("issues", [])) == 0)

    # (4) variabel Y hilang → 1+ issues
    section_y_hilang = [
        {"section_id": "4.1", "title": "Hasil Penelitian",
         "content": "Kompensasi Finansial (X1) berpengaruh signifikan terhadap organisasi. Hasil penelitian menunjukkan bahwa X1 memiliki pengaruh yang kuat terhadap kinerja organisasi secara keseluruhan. Temuan ini membuktikan bahwa variabel independen pertama memberikan kontribusi yang besar. Namun variabel tersebut tidak disebutkan secara eksplisit dalam bagian ini meskipun merupakan variabel dependen utama yang diukur dalam penelitian ini. Penelitian selanjutnya disarankan untuk memperhatikan hal ini."},
    ]
    r4 = check_variable_consistency(brief, section_y_hilang)
    cek("variabel Y hilang → 1+ issues", len(r4.get("issues", [])) >= 1)

    # (5) tanpa variabel di brief → 0 issues (bukan crash)
    brief_no_var = {"judul": "Test"}
    r5 = check_variable_consistency(brief_no_var, section_lengkap)
    cek("tanpa variabel di brief → 0 issues (bukan crash)", len(r5.get("issues", [])) == 0)

    # ── (6) check_hipotesis: H1+H2 disebut → 0 issues ──
    print("\n[3] check_hipotesis_consistency")
    r6 = check_hipotesis_consistency(brief, section_lengkap)
    cek("H1+H2 disebut → 0 issues", len(r6.get("issues", [])) == 0)

    # (7) H1 tidak disebut → 1+ issues
    section_no_hyp = [
        {"section_id": "4.1", "title": "Hasil Penelitian",
         "content": "Hasil penelitian menunjukkan bahwa terdapat pengaruh yang signifikan antara variabel independen dan dependen. Temuan ini membuktikan bahwa hipotesis yang diajukan sebelumnya dapat diterima berdasarkan data yang diperoleh. Bagian pembahasan ini fokus pada temuan umum tanpa menyebut nomor hipotesis tertentu karena keterbatasan ruang. Analisis lebih lanjut akan dilakukan pada bagian berikutnya dengan seksama."},
    ]
    r7 = check_hipotesis_consistency(brief, section_no_hyp)
    cek("H1 tidak disebut → 1+ issues", len(r7.get("issues", [])) >= 1)

    # (8) tanpa hipotesis di brief → 0 issues (bukan crash)
    brief_no_hyp = {"judul": "Test", "variabel": [{"nama": "X1", "label": "A"}]}
    r8 = check_hipotesis_consistency(brief_no_hyp, section_lengkap)
    cek("tanpa hipotesis di brief → 0 issues (bukan crash)", len(r8.get("issues", [])) == 0)

    # ── (9) check_ov: OV disebut → 0 issues ──
    print("\n[4] check_ov_consistency")
    r9 = check_ov_consistency(brief, section_lengkap)
    cek("OV disebut → 0 issues", len(r9.get("issues", [])) == 0)

    # (10) OV tidak disebut → 1+ issues
    section_no_ov = [
        {"section_id": "3.1", "title": "Definisi Operasional",
         "content": "Bagian ini mendefinisikan variabel yang digunakan dalam penelitian. Kinerja merupakan variabel dependen yang diukur menggunakan skala Likert. Namun Definisi Operasional tidak dituliskan secara eksplisit dengan tabel yang memuat kolom Variabel, Dimensi, Indikator, Skala Ukur, dan Skala Pengukuran."},
    ]
    r10 = check_ov_consistency(brief, section_no_ov)
    cek("OV tidak disebut → 1+ issues", len(r10.get("issues", [])) >= 1)

    # ── (11) check_consistency wrapper ──
    print("\n[5] check_consistency (wrapper)")
    r11 = check_consistency(brief, section_lengkap)
    cek("wrapper tidak crash", r11 is not None)
    cek("wrapper punya 'issues' (list)", isinstance(r11.get("issues"), list))
    cek("wrapper punya 'summary' (dict)", isinstance(r11.get("summary"), dict))
    cek("wrapper punya 'ok' (bool)", isinstance(r11.get("ok"), bool))

    # (12) wrapper section kosong → tidak crash
    r12 = check_consistency(brief, [])
    cek("wrapper section kosong → tidak crash", r12 is not None)

    # (13) wrapper brief None → tidak crash
    r13 = check_consistency(None, None)
    cek("wrapper brief None → tidak crash", r13 is not None)

    # ── (14) format_laporan ──
    print("\n[6] format_laporan")
    laporan = format_laporan(r11)
    cek("laporan bukan string kosong", len(laporan) > 0)
    cek("laporan mengandung 'Konsistensi'", "Konsistensi" in laporan)

    # (15) catatan_untuk_ai: tidak mengandung kata terlarang
    catatan = catatan_untuk_ai(r11)
    cek("catatan_untuk_ai tidak mengandung 'user'", "user" not in catatan.lower())
    cek("catatan_untuk_ai tidak mengandung 'kata terlarang'",
        not any(kata in catatan.lower() for kata in ["kuota", "token", "rupiah", "harga"]))

    # ── RINGKASAN ──
    print("\n" + "=" * 62)
    print(f"LULUS: {LULUS}   GAGAL: {GAGAL}")
    print("=" * 62)
    return 1 if GAGAL else 0


if __name__ == "__main__":
    sys.exit(main())
