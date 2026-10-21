"""Ethics Checker — Fase 7 EduAi Publishing.

Sumber: penelitian-bot/telegram-bot/agents/ethics-checker.js (READ-ONLY, 525 baris).
Adaptasi Python: 18 aturan etika dalam 3 kategori (kuantitatif, kualitatif, umum).
TIDAK menggunakan AI (Rp 0) — murni regex pattern matching.

Aturan:
  - severity: 'block' (ditolak), 'warn' (peringatan), 'info' (informasi)
  - Setiap aturan: id, pattern (regex), severity, reason, recommendation,
    commands (list), guide_steps (list), kaidah (referensi)

Fungsi:
  get_all_rules() → dict kategori → list aturan
  check_ethics(naskah, mode='kuantitatif') → dict hasil pemeriksaan
  format_ethics_report(hasil) → str laporan format teks
"""
import re
from typing import Any

# ════════════════════════════════════════════════════════════════
# 1. SEMUA 18 ATURAN ETIKA (adaptasi langsung dari JS)
# ════════════════════════════════════════════════════════════════

ETHICS_RULES = {
    "kuantitatif": [
        {
            "id": "no_fabrication",
            "pattern": re.compile(
                r"(?:fiktif|fiktif|fake|fabrication|generate\s*data|"
                r"tambah\s*responden\s*palsu|buat\s*data|karangan\s*data|"
                r"data\s*rekayasa|ngarang\s*data)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Fabrikasi data = research misconduct berat. "
                "Melanggar etika penelitian dan dapat menyebabkan "
                "skripsi/tesis ditolak atau dicabut gelarnya."
            ),
            "recommendation": (
                "Gunakan data riil dari responden. Jika sampel kurang: "
                "(1) perpanjang waktu pengambilan data, "
                "(2) perluas populasi, "
                "(3) konsultasi dengan dosen pembimbing."
            ),
            "commands": ["/kuesioner"],
            "guide_steps": [
                "Pastikan kuesioner Anda siap (/kuesioner)",
                "Sebarkan ke responden via Google Sheets (link otomatis share)",
                "Tunggu responden mengisi (minimal 30 untuk regresi)",
                "Jalankan /bab4 setelah data lengkap",
            ],
            "kaidah": (
                "Kode Etik Penelitian Indonesia; "
                "APA Ethics Code 8.10 (Falsification); "
                "Pedoman Tugas Akhir Bab Plagiarisme & Etika"
            ),
        },
        {
            "id": "no_force_significance",
            "pattern": re.compile(
                r"(?:paksa\s*(?:r²|p-value|signifikan|hasil)|"
                r"set\s*(?:r²|p-value)|"
                r"r²\s*(?:nya\s*)?(jadi|diubah|ditingkatkan|diperbesar)|"
                r"signifikan\s*(?:dong|aja|sih)|"
                r"p\s*-?\s*value\s*(?:kecil|diubah|diturunkan|jadi))",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Tidak bisa memaksakan nilai R² atau p-value. "
                "Nilai statistik ditentukan oleh data riil, bukan kehendak peneliti."
            ),
            "recommendation": (
                "Jika hasil tidak signifikan: "
                "(1) sampaikan apa adanya, "
                "(2) berikan justifikasi teoritik mengapa, "
                "(3) diskusikan dengan pembimbing untuk pengembangan riset lanjutan."
            ),
            "commands": ["/bab4", "/revisi"],
            "guide_steps": [
                "Jalankan /bab4 — sistem akan jujur menampilkan hasil riil",
                "Untuk Bab V (Kesimpulan), jika hipotesis ditolak: jelaskan justifikasi teoritik",
                "Untuk implikasi manajerial, fokus pada insight dari data meskipun tidak signifikan",
                "Gunakan /revisi untuk perkaya narasi pembahasan yang lebih dalam",
            ],
            "kaidah": (
                "Ghozali (2018), Aplikasi Analisis Multivariate; "
                "Sugiyono (2017), Metode Penelitian Kuantitatif"
            ),
        },
        {
            "id": "no_skip_validity",
            "pattern": re.compile(
                r"(?:skip|lewati|lompati|hapus|buang|tidak\s*perlu)\s*"
                r"(?:uji\s*)?(validitas|reliabilitas|validity|reliability)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Uji validitas dan reliabilitas WAJIB untuk instrumen kuantitatif. "
                "Tanpa uji ini, instrumen belum teruji kelayakannya."
            ),
            "recommendation": (
                "Pipeline /bab4 sudah otomatis menjalankan validitas "
                "(corrected item-total correlation) + reliabilitas (Cronbach's Alpha) "
                "dari data responden Anda."
            ),
            "commands": ["/bab4"],
            "guide_steps": [
                "Pastikan data responden sudah terisi di Google Sheets",
                "Jalankan /bab4 [Y] [X1,X2]",
                "Pipeline otomatis: deskriptif → validitas → reliabilitas → regresi → asumsi",
                "Hasil ditulis di Bab IV (4.2 Uji Instrumen)",
            ],
            "kaidah": (
                "Sugiyono (2017) Bab Instrument Testing; "
                "Arikunto (2013) Bab Validitas & Reliabilitas"
            ),
        },
        {
            "id": "no_skip_assumption",
            "pattern": re.compile(
                r"(?:skip|lewati|lompati|hapus|tidak\s*perlu)\s*"
                r"(?:uji\s*asumsi|normalitas|multikolinearitas|heteroskedastisitas|asumsi\s*klasik)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Uji asumsi klasik WAJIB sebelum regresi. "
                "Tanpa uji ini, hasil regresi belum bisa diinterpretasikan secara valid."
            ),
            "recommendation": (
                "Pipeline /bab4 sudah otomatis menjalankan normalitas "
                "(Shapiro-Wilk), multikolinearitas (VIF), heteroskedastisitas (Breusch-Pagan)."
            ),
            "commands": ["/bab4"],
            "guide_steps": [
                "/bab4 otomatis jalankan semua uji asumsi klasik",
                "Jika asumsi tidak terpenuhi: gunakan transformasi data atau metode alternatif (misal regresi robust)",
                "Gunakan /revisi [section] untuk diskusi lebih lanjut tentang penanganan asumsi",
            ],
            "kaidah": "Ghozali (2018) Bab Uji Asumsi Klasik",
        },
        {
            "id": "sample_min_30",
            "pattern": re.compile(
                r"(?:sampel\s*(?:cukup|aja)\s*(?:15|20|25)|n\s*=\s*(?:15|20|25))",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Untuk analisis regresi linear berganda, minimal n = 30 atau "
                "10× jumlah variabel independen (Hair et al.). "
                "Sampel terlalu kecil menurunkan power statistik."
            ),
            "recommendation": (
                "Naikkan sampel ke minimal 30 (atau 10× jumlah variabel X). "
                "Untuk SEM: minimal 100-200."
            ),
            "commands": ["/kuesioner"],
            "guide_steps": [
                "Untuk regresi linear: minimal 30 responden (atau 10× jumlah variabel X)",
                "Untuk SEM: minimal 100-200 responden",
                "Untuk Path Analysis dengan mediasi: minimal 100 responden",
                "Gunakan /kuesioner untuk memperbanyak link Google Sheets untuk diisi",
            ],
            "kaidah": (
                "Hair et al. (2019), Multivariate Data Analysis; "
                "Tabachnick & Fidell (2019)"
            ),
        },
        {
            "id": "sample_representative",
            "pattern": re.compile(
                r"(?:ganti|ubah|replace)\s*(?:populasi|sampel|sample|responden|target)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Mengubah populasi/sampel = mengubah metode sampling. "
                "Harus konsisten dengan Bab III (3.2 Populasi dan Sampel)."
            ),
            "recommendation": (
                "Jika ingin ubah sampel: "
                "(1) revisi dulu Bab III, "
                "(2) update Problem Formulation, "
                "(3) baru sesuaikan Bab IV."
            ),
            "commands": ["/revisi"],
            "guide_steps": [
                "Ubah populasi/sampel = ubah metode sampling di Bab III",
                "/revisi 3.2 [alasan perubahan] — akan cascade update ke Bab IV",
                "Atau buat proyek baru jika perubahan fundamental",
            ],
            "kaidah": (
                "Sugiyono (2017) Bab Populasi dan Sampel; "
                "Creswell (2014) Research Design"
            ),
        },
        {
            "id": "hypothesis_match",
            "pattern": re.compile(
                r"(?:ganti\s*hipotesis|ubah\s*h[1-9]|tambah\s*hipotesis\s*baru|tidak\s*perlu\s*hipotesis)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Hipotesis harus match dengan rumusan masalah (Bab I) "
                "dan diuji di Bab IV. Mengubah hipotesis = mengubah seluruh alur penelitian."
            ),
            "recommendation": (
                "Sebelum ubah hipotesis: "
                "(1) revisi rumusan masalah dulu, "
                "(2) update variabel & definisi operasional, "
                "(3) baru sesuaikan hipotesis."
            ),
            "commands": ["/revisi"],
            "guide_steps": [
                "/revisi 1.2 [rumusan masalah baru]",
                "/revisi 2.4 [hipotesis baru]",
                "Pastikan match: 1.2 (rumusan) ↔ 2.4 (hipotesis) ↔ 4.4 (uji)",
                "Setelah hipotesis berubah, /bab4 untuk re-analisis",
            ],
            "kaidah": (
                "Pedoman Skripsi Bab Hipotesis; "
                "Creswell (2014) Bab Hypothesis"
            ),
        },
    ],

    "kualitatif": [
        {
            "id": "min_informan",
            "pattern": re.compile(
                r"(?:cukup\s*(?:1|2|satu|dua)|"
                r"hanya\s*(?:1|2|satu|dua)\s*informan|"
                r"informan\s*(?:aja|saja)\s*(?:1|2))",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Untuk triangulasi, minimal 3-5 informan (kunci + pendukung). "
                "1-2 informan tidak cukup untuk keabsahan data kualitatif."
            ),
            "recommendation": (
                "Tambahkan informan sampai saturasi data tercapai "
                "(biasanya 5-15 informan untuk studi kasus)."
            ),
            "commands": ["/informan"],
            "guide_steps": [
                "Untuk studi kasus: minimal 3-5 informan (1 kunci + 3-5 pendukung)",
                "Untuk fenomenologi: minimal 5-10 informan",
                "Untuk grounded theory: sampai saturasi (bisa 15-30 informan)",
                "/informan untuk generate pedoman wawancara & kriteria informan",
            ],
            "kaidah": (
                "Moleong (2017) Bab Informan; "
                "Creswell (2014) Bab Sampling in Qualitative"
            ),
        },
        {
            "id": "no_skip_informed_consent",
            "pattern": re.compile(
                r"(?:skip|lewati|hapus|buang|tidak\s*perlu)\s*"
                r"(?:informed\s*consent|ethical\s*clearance|etika\s*penelitian|ethical\s*clearance)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Informed consent dan ethical clearance WAJIB untuk penelitian "
                "kualitatif yang melibatkan manusia."
            ),
            "recommendation": (
                "Saya bisa generate template informed consent dan/atau "
                "ethical clearance via /ethical."
            ),
            "commands": ["/ethical"],
            "guide_steps": [
                "/ethical untuk generate template informed consent",
                "/ethical untuk generate ethical clearance",
                "Pastikan semua informan menandatangani informed consent sebelum wawancara",
                "Simpan informed consent sebagai lampiran di skripsi",
            ],
            "kaidah": (
                "Pedoman Etika Penelitian; "
                "Komite Etik Penelitian; "
                "CIOMS Guidelines"
            ),
        },
        {
            "id": "no_skip_keabsahan",
            "pattern": re.compile(
                r"(?:skip|lewati|hapus|buang)\s*"
                r"(?:uji\s*keabsahan|keabsahan\s*data|triangulasi|member\s*check)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Uji keabsahan data (Lincoln & Guba) WAJIB untuk kualitatif: "
                "kredibilitas, transferabilitas, dependabilitas, konfirmabilitas."
            ),
            "recommendation": (
                "Saya bisa generate sub-bab Keabsahan Data via /keabsahan, "
                "yang mencakup triangulasi + member check + audit trail."
            ),
            "commands": ["/keabsahan"],
            "guide_steps": [
                "/keabsahan untuk generate 4 aspek Lincoln & Guba",
                "Lakukan triangulasi (sumber, teknik, waktu)",
                "Lakukan member check (konfirmasi ke informan)",
                "Simpan bukti triangulasi (foto, rekaman, catatan lapangan)",
            ],
            "kaidah": (
                "Lincoln & Guba (1985), Naturalistic Inquiry; "
                "Moleong (2017) Bab Uji Keabsahan"
            ),
        },
        {
            "id": "no_skip_miles_huberman",
            "pattern": re.compile(
                r"(?:skip|lewati|hapus)\s*"
                r"(?:miles|huberman|reduksi\s*data|analisis\s*tematik)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Analisis data kualitatif harus sistematis "
                "(misal Miles & Huberman atau Braun & Clarke). "
                "Tanpa ini, analisis tidak kredibel."
            ),
            "recommendation": (
                "Saya bisa generate analisis Miles & Huberman via /miles, "
                "yang mencakup 3 jalur: reduksi, penyajian, kesimpulan."
            ),
            "commands": ["/miles"],
            "guide_steps": [
                "Pastikan transkrip wawancara sudah diisi di Google Docs template",
                "/miles untuk generate analisis 3 jalur: reduksi, penyajian, kesimpulan",
                "Tambahkan /keabsahan untuk uji keabsahan data",
            ],
            "kaidah": "Miles & Huberman (1994), Qualitative Data Analysis",
        },
        {
            "id": "random_sampling_kualitatif",
            "pattern": re.compile(
                r"(?:random\s*sampling\s*(?:di|untuk|pada)\s*(?:kualitatif|penelitian\s*kualitatif)|"
                r"acak\s*di\s*kualitatif)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Random sampling TIDAK cocok untuk penelitian kualitatif. "
                "Kualitatif pakai purposive sampling, snowball, atau theoretical sampling."
            ),
            "recommendation": (
                "Untuk kualitatif: purposive sampling (sesuai kriteria), "
                "snowball sampling, atau theoretical sampling (untuk grounded theory)."
            ),
            "commands": ["/informan"],
            "guide_steps": [
                "/informan untuk generate kriteria & pedoman",
                "Purposive sampling: pilih informan sesuai kriteria yang sudah ditentukan",
                "Snowball sampling: informan merekomendasikan informan lain",
                "Hindari random sampling di kualitatif",
            ],
            "kaidah": (
                "Creswell (2014) Bab Sampling; "
                "Sugiyono (2017) Bab Teknik Sampling"
            ),
        },
    ],

    "general": [
        {
            "id": "no_fake_citations",
            "pattern": re.compile(
                r"(?:banyak\s*sitasi|sitasi\s*banyak|tambah\s*referensi\s*palsu|"
                r"fake\s*citation|ngarang\s*referensi|ngarang\s*sitasi|"
                r"sitasi\s*asal|buat\s*sitasi)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Sitasi harus dari artikel yang ada di literature pool "
                "(40 artikel ter-kurasi). Sitasi palsu = plagiarism."
            ),
            "recommendation": (
                "Saya rekomendasikan: "
                "(1) gunakan literatur dari /literatur, "
                "(2) minta saya cari literatur baru yang relevan, "
                "(3) baca & parafrase dari sumber valid."
            ),
            "commands": ["/literatur", "/parafrase"],
            "guide_steps": [
                "Cari literatur dari SINTA/Scopus via /literatur",
                "Baca artikel, pahami konteks, parafrase dengan kata sendiri",
                "Gunakan /parafrase untuk bantu parafrase otomatis + sitasi",
                "Hindari copy-paste langsung dari sumber",
            ],
            "kaidah": (
                "APA 7 Edition; "
                "Panduan Anti-Plagiarisme; "
                "Pedoman Skripsi Bab Sitasi"
            ),
        },
        {
            "id": "no_copy_paste",
            "pattern": re.compile(
                r"(?:copy\s*paste|salin\s*tempel|jiplak|tiru\s*persis|persis\s*sama)",
                re.IGNORECASE,
            ),
            "severity": "block",
            "reason": (
                "Copy-paste tanpa parafrase = plagiarism. "
                "Turnitin similarity harus < 25-30%."
            ),
            "recommendation": (
                "Gunakan /parafrase untuk menulis ulang dengan bahasa sendiri "
                "+ sitasi yang benar. Saya bisa bantu parafrase otomatis."
            ),
            "commands": ["/parafrase"],
            "guide_steps": [
                "Baca sumber asli, pahami konteks",
                "Parafrase dengan kata-kata sendiri (tidak boleh copy-paste)",
                "Tambahkan sitasi yang benar (Author, Year)",
                "Gunakan /parafrase untuk generate parafrase otomatis + cek similarity",
            ],
            "kaidah": (
                "Pedoman Anti-Plagiarism; "
                "UU Hak Cipta; "
                "Pedoman Tugas Akhir"
            ),
        },
        {
            "id": "title_consistency",
            "pattern": re.compile(
                r"(?:ganti\s*judul|ubah\s*judul\s*(?:total|menjadi)|"
                r"judul\s*beda\s*antar\s*bab)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Judul harus KONSISTEN di seluruh dokumen "
                "(cover, Bab I-V, lampiran). Inkonsistensi = revisi major."
            ),
            "recommendation": (
                "Saat ganti judul, saya akan cascade update ke: "
                "(1) Problem Formulation, "
                "(2) semua section reference ke judul, "
                "(3) output Google Docs. Konfirmasi dulu?"
            ),
            "commands": ["/revisi"],
            "guide_steps": [
                "/revisi judul [judul baru]",
                "Sistem akan cascade update ke Problem Formulation, semua section, dan Google Docs",
                "Konfirmasi perubahan sebelum eksekusi",
            ],
            "kaidah": (
                "Pedoman Skripsi Bab Konsistensi; "
                "APA 7 Title Format"
            ),
        },
        {
            "id": "no_bab_lompat",
            "pattern": re.compile(
                r"(?:langsung\s*bab\s*(?:iv|4|v|5)|"
                r"skip\s*bab\s*(?:i|1|ii|2|iii|3)|"
                r"lewati\s*bab)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Urutan bab harus berurutan dan logis. "
                "Bab IV tidak mungkin ada tanpa Bab I-III."
            ),
            "recommendation": (
                "Generate secara berurutan: "
                "Bab I → Bab II → Bab III → Bab IV → Bab V. "
                "Gunakan /outline untuk lihat progress."
            ),
            "commands": ["/outline", "/bab1", "/bab2", "/bab3", "/bab4", "/bab5"],
            "guide_steps": [
                "Mulai dari Bab I (Latar Belakang) → Bab II (Tinjauan Pustaka) → Bab III (Metode)",
                "Lanjut ke Bab IV (Hasil) → Bab V (Kesimpulan)",
                "/outline untuk lihat progress project",
                "Setiap bab tergantung bab sebelumnya (konsistensi)",
            ],
            "kaidah": "Pedoman Skripsi Bab Sistematika Penulisan",
        },
        {
            "id": "no_sitasi_wikipedia",
            "pattern": re.compile(
                r"(?:sitasi\s*wikipedia|citasi\s*blog|citasi\s*facebook|"
                r"citasi\s*tiktok|capai\s*website\s*random)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Wikipedia, blog, dan media sosial BUKAN sumber akademik "
                "untuk skripsi/tesis. Gunakan jurnal terakreditasi, buku teks, "
                "atau prosiding."
            ),
            "recommendation": (
                "Cari sumber di: "
                "(1) jurnal SINTA/Scopus, "
                "(2) buku teks terbitan PT/reputable, "
                "(3) prosiding seminar internasional."
            ),
            "commands": ["/literatur"],
            "guide_steps": [
                "Gunakan jurnal SINTA (sinta.kemdikbud.go.id) atau Scopus",
                "Buku teks dari PT reputable (UI Press, UGM Press, dll)",
                "Prosiding seminar internasional bereputasi",
                "/literatur untuk cari dari sumber valid",
            ],
            "kaidah": (
                "Panduan Sumber Akademik; "
                "Pedoman Skripsi Bab Tinjauan Pustaka"
            ),
        },
        {
            "id": "definisi_operasional_bab1",
            "pattern": re.compile(
                r"(?:definisi\s*operasional\s*di\s*bab\s*(?:1|i)|"
                r"ov\s*di\s*bab\s*(?:1|i)|"
                r"operasional\s*variabel\s*di\s*pendahuluan)",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Konvensi S1 Indonesia: Definisi Operasional variabel "
                "ditempatkan di BAB III (Metode Penelitian), BUKAN Bab I. "
                "Penempatan di Bab I akan ditolak dosen."
            ),
            "recommendation": (
                "Definisi Operasional akan di-generate di Bab III (3.x). "
                "Bab I cukup membahas variabel secara konseptual."
            ),
            "commands": ["/revisi"],
            "guide_steps": [
                "Definisi Operasional → Bab III (3.x), bukan Bab I",
                "Bab I: bahas variabel secara konseptual",
                "Bab III: definisi operasional + indikator + skala ukur",
                "/revisi 3.x untuk generate Definisi Operasional",
            ],
            "kaidah": (
                "Pedoman Skripsi Bab Definisi Operasional; "
                "Panduan S1 Indonesia"
            ),
        },
        {
            "id": "no_swot_dengan_data_sendiri",
            "pattern": re.compile(
                r"(?:skripsi\s*swot|swot\s*(?:saja|cuma)|cukup\s*swot\s*(?:aja|saja))",
                re.IGNORECASE,
            ),
            "severity": "info",
            "reason": (
                "SWOT saja cukup untuk S1 kualitatif. "
                "Untuk S2/S3 atau jurnal, perlu kerangka yang lebih kuat "
                "(misal Miles & Huberman + Triangulasi)."
            ),
            "recommendation": (
                "Untuk S1 kualitatif cukup SWOT + IFAS/EFAS. "
                "Tambahan bagus: /miles untuk reduksi data, "
                "/keabsahan untuk uji keabsahan."
            ),
            "commands": ["/swot", "/miles", "/keabsahan"],
            "guide_steps": [
                "S1 kualitatif: /swot + /miles + /keabsahan",
                "S2 kualitatif: tambah grounded theory atau case study mendalam",
                "Jurnal kualitatif: pakai thematic analysis (Braun & Clarke)",
                "Setiap framework punya kekuatan sendiri",
            ],
            "kaidah": "Pedoman Skripsi S1; Panduan Kualitatif S1",
        },
        {
            "id": "mode_consistency",
            "pattern": re.compile(
                r"(?:ganti\s*(?:mode|jenis)\s*penelitian|ubah\s*(?:kuantitatif|kualitatif))",
                re.IGNORECASE,
            ),
            "severity": "warn",
            "reason": (
                "Mengubah mode penelitian setelah Problem Formulation = "
                "mengubah seluruh desain. Semua Bab harus di-revisi."
            ),
            "recommendation": (
                "Mode penelitian ditentukan di awal. "
                "Jika ingin ganti mode, lebih baik buat proyek baru "
                "dengan mode yang sesuai."
            ),
            "commands": ["/start"],
            "guide_steps": [
                "Mode penelitian tidak bisa diubah di tengah jalan",
                "Buat proyek baru via /start jika ingin ganti mode",
                "Atau konsultasikan dulu dengan dosen pembimbing",
            ],
            "kaidah": "Pedoman Skripsi Bab Jenis Penelitian",
        },
    ],
}


# ════════════════════════════════════════════════════════════════
# 2. FUNGSI UTAMA
# ════════════════════════════════════════════════════════════════

def get_all_rules() -> dict:
    """Kembalikan semua aturan etika berdasarkan kategori.
    Adaptasi dari getAllRules() di JS (baris 511-517)."""
    return ETHICS_RULES


def check_ethics(naskah: str, mode: str = "kuantitatif") -> dict:
    """Periksa naskah terhadap 18 aturan etika.
    Adaptasi dari checkEthics() di JS (baris 309-379).

    Return: {action, violations, mode}
      action: 'BLOCK' | 'WARN' | 'INFO' | 'PROCEED'
    """
    if not naskah or not isinstance(naskah, str):
        return {"action": "PROCEED", "violations": [], "mode": mode}

    # Gabungkan aturan kategori spesifik + umum
    aturan_relevan = []
    aturan_relevan.extend(ETHICS_RULES.get(mode, []))
    aturan_relevan.extend(ETHICS_RULES.get("general", []))

    violations: list[dict] = []
    for rule in aturan_relevan:
        if rule["pattern"].search(naskah):
            violations.append({
                "id": rule["id"],
                "source": "rule",
                "severity": rule["severity"],
                "reason": rule["reason"],
                "recommendation": rule.get("recommendation", ""),
                "commands": rule.get("commands", []),
                "guide_steps": rule.get("guide_steps", []),
                "kaidah": rule.get("kaidah", ""),
            })

    if not violations:
        return {"action": "PROCEED", "violations": [], "mode": mode}

    # Tentukan action berdasarkan severity tertinggi
    has_block = any(v["severity"] == "block" for v in violations)
    has_warn = any(v["severity"] == "warn" for v in violations)
    has_info = any(v["severity"] == "info" for v in violations)

    if has_block:
        action = "BLOCK"
    elif has_warn:
        action = "WARN"
    elif has_info:
        action = "INFO"
    else:
        action = "PROCEED"

    return {"action": action, "violations": violations, "mode": mode}


# ════════════════════════════════════════════════════════════════
# 3. FORMAT LAPORAN
# ════════════════════════════════════════════════════════════════

def format_ethics_report(hasil: dict) -> str:
    """Format laporan pemeriksaan etika.
    Adaptasi dari formatEthicsResponse() di JS (baris 417-480).

    Return: string laporan format teks, atau '' kalau PROCEED.
    """
    if hasil.get("action") == "PROCEED":
        return ""

    icon_map = {"BLOCK": "⛔", "WARN": "⚠️", "INFO": "💡"}
    title_map = {
        "BLOCK": "Permintaan Ditolak — Melanggar Kaidah Penelitian",
        "WARN": "Peringatan — Perlu Pertimbangan",
        "INFO": "Informasi",
    }

    action = hasil.get("action", "WARN")
    icon = icon_map.get(action, "⚠️")
    title = title_map.get(action, "Peringatan")

    lines: list[str] = [f"{icon} *{title}*", ""]

    for i, v in enumerate(hasil.get("violations", []), 1):
        sev_icon = {"block": "⛔", "warn": "⚠️", "info": "💡"}.get(v.get("severity", "warn"), "⚠️")
        lines.append(f"{sev_icon} *Pelanggaran {i}:* {v.get('id', '?')}")
        lines.append(f"📋 *Alasan:* {v.get('reason', '')}")

        if v.get("recommendation"):
            lines.append(f"✅ *Rekomendasi:* {v.get('recommendation')}")

        if v.get("guide_steps"):
            lines.append("")
            lines.append("📝 *Langkah yang Bisa Dilakukan:*")
            for idx, step in enumerate(v["guide_steps"], 1):
                lines.append(f"   {idx}. {step}")

        if v.get("commands"):
            lines.append("")
            lines.append("🔧 *Command yang Bisa Membantu:*")
            for cmd in v["commands"]:
                lines.append(f"   • `{cmd}`")

        if v.get("kaidah"):
            lines.append("")
            lines.append(f"📖 *Kaidah:* {v.get('kaidah')}")

        lines.append("")

    if action == "BLOCK":
        lines.append("💡 *Pesan Agen:*")
        lines.append(
            "Saya di sini BUKAN untuk menuruti semua permintaan, "
            "tapi untuk menjaga kualitas akademik penelitian Anda. "
            "Tujuannya: menghasilkan skripsi/tesis/disertasi/jurnal "
            "yang BERKUALITAS dan LOLOS sidang."
        )
        lines.append("")
        lines.append(
            "Saya TIDAK meninggalkan Anda bingung — lihat rekomendasi "
            "+ langkah + command di atas untuk solusi konkret."
        )
        lines.append("")
        lines.append(
            "Jika Anda tetap merasa permintaan ini benar, "
            "mohon konsultasikan dulu dengan dosen pembimbing. "
            "Saya bisa membantu setelah ada justifikasi yang valid."
        )
    elif action == "WARN":
        lines.append("")
        lines.append("⚠️ *Pesan Agen:*")
        lines.append(
            "Permintaan ini BISA dilakukan tapi ada konsekuensi "
            "metodologis. Lanjutkan? [✅ Ya, Lanjutkan] [❌ Batal]"
        )
    elif action == "INFO":
        lines.append("")
        lines.append("💡 *Pesan Agen:*")
        lines.append(
            "Saya informasikan hal ini untuk pertimbangan Anda. "
            "Lihat rekomendasi di atas untuk langkah selanjutnya."
        )

    return "\n".join(lines)
