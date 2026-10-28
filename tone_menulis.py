"""TONE MENULIS per jenis buku — dipakai architect_prompt/skeptic/editor.

PUTUSAN BOS 18 Okt 2026: jenis buku menentukan SELURUH wajah buku, termasuk
CARA MENULISNYA. Buku anak bergambar clay tapi teksnya gaya buku bisnis =
lebih aneh daripada tidak ada pilihan sama sekali.

⚠️ SATU-SATUNYA tempat aturan tone. JANGAN menulis "Formal-santai-naratif"
langsung di pipeline lagi — gerbang memeriksa ini.
"""

TONE_MENULIS = {
    "umum": {
        "tone": (
            "Formal-santai-naratif. Bukan buku ajar. Pembaca adalah umum "
            "(profesional, mahasiswa, pengusaha). Tulis seperti \"ngobrol cerdas\" "
            "— kredibel tapi mengalir, tidak menggurui."
        ),
        "sapaan": "Anda",
        "pembaca": "pembaca dewasa: profesional, mahasiswa, pengusaha",
        "paragraf": "60-100 kata, 3-5 kalimat",
        "kata_target": "800-1200 kata",
        "intro_kata": "300-400 kata",
        "penutup_kata": "200-300 kata",
        "sitasi": "Sitasi APA 7: (Penulis, Tahun) — WAJIB minimal 2 sitasi",
        "hook": "buka dengan cerita nyata, anekdot, atau data mengejutkan (BUKAN teori)",
        "personal": "- Personal: \"Anda\", \"kita\", \"pembaca\" >= 20%",
        "larangan": (
            "- DILARANG: \"Penting untuk dicatat\", \"Secara komprehensif\", "
            "\"Di era digital ini\""
        ),
        "istilah": "",
    },
    "anak": {
        "tone": (
            "Bahasa sederhana dan hangat, seperti bercerita kepada anak usia 4-10 "
            "tahun. Kalimat PENDEK (maksimal 12 kata). Satu gagasan per kalimat. "
            "Banyak contoh yang bisa dilihat anak di rumah atau sekolah. Sapaan "
            "langsung \"kamu\". Hindari istilah teknis; kalau perlu, jelaskan dengan "
            "perbandingan yang akrab. Nada mengajak bermain, BUKAN mengajari."
        ),
        "sapaan": "kamu",
        "pembaca": "anak usia 4-10 tahun (dibacakan orang tua/guru)",
        "paragraf": "55-85 kata, 4-5 kalimat",
        "kata_target": "250-400 kata",
        "intro_kata": "100-150 kata",
        "penutup_kata": "80-120 kata",
        "sitasi": (
            "TIDAK memakai sitasi akademik (Penulis, Tahun) — buku anak bukan karya "
            "ilmiah. Kalau perlu menyebut sumber, tulis sebagai kalimat biasa."
        ),
        "hook": (
            "buka dengan pertanyaan yang membuat anak penasaran atau pengalaman "
            "sehari-hari yang dia kenal (hujan, mainan, hewan)"
        ),
        "personal": "- Personal: panggil \"kamu\" langsung, minimal 30% kalimat",
        "larangan": (
            "- DILARANG: kalimat lebih dari 12 kata, istilah teknis tanpa penjelasan, "
            "nada memerintah, dan kata \"sebagaimana\", \"adapun\", \"demikian\""
        ),
        "istilah": (
            "- Istilah sulit WAJIB langsung dijelaskan dalam tanda kurung dengan "
            "bahasa anak. Contoh: \"menguap (air berubah jadi uap, seperti asap di "
            "atas air panas)\""
        ),
    },
    "pendidikan": {
        "tone": (
            "Jelas, bertahap, dan membimbing — seperti guru yang sabar. Satu gagasan "
            "per paragraf. Istilah ilmiah BOLEH dipakai TAPI wajib langsung "
            "dijelaskan. Urutan langkah harus tersurat (pertama, kedua, ketiga). "
            "Nada membimbing, bukan bermain-main seperti buku anak."
        ),
        "sapaan": "kamu",
        "pembaca": "siswa SD-SMP, dibimbing guru",
        "paragraf": "55-80 kata, 4-5 kalimat",
        "kata_target": "500-800 kata",
        "intro_kata": "150-250 kata",
        "penutup_kata": "120-180 kata",
        "sitasi": (
            "Sebut sumber seperti buku pelajaran: (Nama Buku, Tahun) atau "
            "\"menurut buku ..., ...\". Tidak perlu gaya APA 7 penuh."
        ),
        "hook": (
            "buka dengan pertanyaan pemandu atau contoh yang dekat dengan "
            "pengalaman siswa di sekolah/rumah"
        ),
        "personal": "- Personal: panggil \"kamu\" langsung, ajak mengamati",
        "larangan": (
            "- DILARANG: paragraf lebih dari 90 kata, istilah ilmiah tanpa "
            "penjelasan, lompatan langkah (pertama ke ketiga tanpa kedua), "
            "dan sapaan \"Anda\" (buku ini menyapa \"kamu\")"
        ),
        "istilah": (
            "- Istilah ilmiah WAJIB dijelaskan sekali di kemunculan pertama. "
            "Contoh: \"penguapan (perubahan air menjadi uap)\""
        ),
    },
    # Ditambahkan 23 Okt 2026 (barang 9 Fase 4) — menyelaraskan aplikasi
    # dengan profil SSOT (template-buku-resmi/jenis/*/profil.json), supaya
    # monograf & buku ajar tidak lagi jatuh ke nada jenis lain.
    "monograf": {
        "tone": (
            "Akademik formal — orang ketiga, tanpa sapaan 'Anda', istilah "
            "konsisten, kalimat lugas. Nada peneliti yang melaporkan dan "
            "membahas hasil, bukan menggurui pembaca."
        ),
        "sapaan": None,
        "pembaca": "dosen, peneliti, mahasiswa pascasarjana",
    },
    "buku_ajar": {
        "tone": (
            "Instruksional akademik — terstruktur dan jelas, menyapa pembaca "
            "'Anda', istilah konsisten, setiap konsep diikuti contoh konkret. "
            "Setiap bab: tujuan pembelajaran di awal, latihan, checklist, "
            "dan rangkuman di akhir."
        ),
        "sapaan": "Anda",
        "pembaca": "mahasiswa, dibimbing dosen",
    },
    # Ditambahkan 28 Okt 2026 (mesin referensi web) — skill buku-referensi:
    # akademik-presisi DENGAN suara penulis. Entri LENGKAP (semua kunci yang
    # dipakai architect_prompt/editor_prompt) supaya jenis ini tidak KeyError
    # seperti entri minimal monograf/buku_ajar.
    "referensi": {
        "tone": (
            "Akademik-presisi: kalimat definisional, lugas, tidak berputar. "
            "Padat dan presisi, TAPI suara penulis hadir lewat definisi yang "
            "ditegakkan dan posisi ilmiah yang dinyatakan eksplisit. Bukan "
            "ensiklopedia kering, bukan narasi populer."
        ),
        "sapaan": "Anda",
        "pembaca": "pembaca yang merujuk: akademisi, peneliti, mahasiswa pascasarjana",
        "paragraf": "60-100 kata, 3-5 kalimat",
        "kata_target": "800-1200 kata",
        "intro_kata": "300-400 kata",
        "penutup_kata": "200-300 kata",
        "sitasi": (
            "Sitasi APA 7 PER-KLAIM dari daftar referensi terverifikasi: "
            "setiap klaim faktual wajib sitasi; definisi dari sumber primer; "
            "TIDAK ada angka minimum per bab (angka minimum = sitasi tempelan)"
        ),
        "hook": (
            "buka dengan PETA BAB: ruang lingkup bab, urgensi ilmiahnya, "
            "dan struktur pembahasan — BUKAN anekdot, BUKAN cerita, BUKAN data "
            "mengejutkan"
        ),
        "personal": (
            "- Suara penulis hadir lewat POSISI ILMIAH eksplisit (sub-bab N.4), "
            "bukan lewat sapaan personal"
        ),
        "larangan": (
            "- DILARANG: anekdot/kisah pembuka, \"Menurut para ahli...\" tanpa "
            "menyebut nama ahli dan karyanya, klaim faktual tanpa sitasi, "
            "ilustrasi 3D dekoratif, dan ciri AI: \"Penting untuk dicatat\", "
            "\"Secara komprehensif\", \"Di era digital ini\""
        ),
        "istilah": (
            "- Satu istilah = satu makna, konsisten di seluruh buku; istilah "
            "asing miring. Istilah baru WAJIB dicatat di akhir sub-bab dalam "
            "blok [ISTILAH BARU] (satu baris per istilah: Istilah: definisi "
            "operasional yang dipakai buku ini)"
        ),
    },
}


def tone(jenis="umum"):
    """Ambil aturan penulisan untuk jenis buku. Tolak jenis asing (jangan fallback)."""
    if jenis not in TONE_MENULIS:
        raise ValueError(
            f"jenis buku '{jenis}' tidak dikenal. Pilihan: {', '.join(TONE_MENULIS)}")
    return TONE_MENULIS[jenis]


def blok_tone(jenis="umum", bagian="isi"):
    """Blok teks siap tempel ke prompt (bagian: intro|isi|penutup)."""
    t = tone(jenis)
    baris = [f"TONE: {t['tone']}", ""]
    if bagian == "intro":
        baris.append(f"- Panjang: {t['intro_kata']}")
    elif bagian == "penutup":
        baris.append(f"- Panjang: {t['penutup_kata']}")
    else:
        baris.append(f"- Panjang: {t['kata_target']}")
    baris += [
        f"- Paragraf: {t['paragraf']}",
        f"- Pembaca: {t['pembaca']}",
        f"- Hook: {t['hook']}",
        t["sitasi"],
        t["personal"],
        t["larangan"],
    ]
    if t["istilah"]:
        baris.append(t["istilah"])
    return "\n".join(b for b in baris if b)


if __name__ == "__main__":
    for j in TONE_MENULIS:
        t = tone(j)
        print(f"{j:12s} sapaan={t['sapaan']:6s} paragraf={t['paragraf']:22s} "
              f"target={t['kata_target']}")
    try:
        tone("remaja")
        print("SALAH: jenis asing tidak dilempar")
    except ValueError as e:
        print("BENAR:", e)
