"""LARANGAN BUDAYA INDONESIA — modul BERSAMA untuk SEMUA jalur gambar AI.

Pemicu: teguran Bos 18 Okt 2026 — "Celengan jangan babi".
Akar: kata "piggy bank" keluar dari LLM SENDIRI, bukan dari prompt kita, karena
itu istilah Inggris paling umum untuk celengan. Untuk pembaca Indonesia
(mayoritas muslim), babi di ilustrasi = salah total, bukan soal selera.

⇒ SATU modul, dipanggil semua jalur (buku, cover, web, materi EduAi).
   JANGAN mengetik ulang daftar per proyek — di sinilah satu-satunya SOT.

Pakai:
    from larangan_budaya import periksa, larangan_prompt, LARANGAN_BUDAYA_PROMPT

    # 1) sebelum kirim ke model gambar (cegah)
    prompt = base_prompt + " " + larangan_prompt()
    # 2) sebelum generate (tolak brief/prompt yang bocor)
    kena, alasan = periksa(prompt_user)   # kena=True -> JANGAN generate
"""
import re

# ══════════════════════════════════════════════════════════════════════════
# DAFTAR LARANGAN
# ══════════════════════════════════════════════════════════════════════════
KATA_TERLARANG_BUDAYA = {
    # ── babi (paling penting untuk pasar Indonesia) ──
    'pig', 'piggy', 'piglet', 'hog', 'swine', 'boar', 'pork', 'bacon',
    'ham', 'sausage', 'porky',
    # ── alkohol & rokok ──
    'beer', 'wine', 'champagne', 'whisky', 'whiskey', 'vodka', 'cocktail',
    'liquor', 'cigarette', 'cigarette', 'cigar', 'vape', 'smoking', 'smoker',
    # ── simbol agama / okultisme ──
    'cross', 'crucifix', 'jesus', 'christ', 'bible', 'santa', 'christmas',
    'halloween', 'pumpkin', 'tarot', 'ouija', 'pentagram', 'skull', 'demon',
    'devil', 'rosary', 'menorah', 'quran vers, no',
    # ── lambang negara (HARAM di buku/produk komersial) ──
    'garuda', 'eagle crest', 'national emblem', 'state symbol', 'coat of arms',
    # ── ketidakpantasan ──
    'nude', 'naked', 'bikini', 'lingerie', 'erotic', 'gambling', 'casino',
    'poker', 'roulette', 'slot machine',
    # ── mata uang / ikon asing (bukan konteks Indonesia) ──
    'dollar', 'euro', 'yen', 'pound sterling', 'greenback', 'cent sign',
    'statue of liberty', 'eiffel', 'big ben', 'colosseum',
    # ══════════════════════════════════════════════════════════════════════
    #  🇮🇩 KATA INDONESIA — 19 Okt 2026
    #  🚨 CACAT YANG DITUTUP (TERUKUR): daftar ini SELURUHNYA Bahasa Inggris.
    #     Brief Indonesia "susunan botol alkohol dan gelas anggur" LOLOS dari
    #     larangan budaya — artinya gambar berisi alkohol BISA terbit di buku.
    #     Karena mesin tulis kita menulis Bahasa Indonesia, ini bukan kasus
    #     langka: hampir semua brief Indonesia lolos dari penjagaan.
    #  ⚠️ `periksa()` mencocokkan PER KATA (`\b`), jadi bentuk berimbuhan
    #     ('daging babi' = dua kata) harus masuk FRASA_TERLARANG di bawah.
    # ══════════════════════════════════════════════════════════════════════
    # babi
    'babi', 'babilah', 'celeng', 'bacon', 'ham', 'sosis',
    # alkohol
    'alkohol', 'beralkohol', 'anggur', 'miras', 'minuman keras', 'bir',
    'arak', 'tuak', 'sake', 'soju', 'wiski', 'vodka', 'sampanye', 'koktail',
    'mabuk', 'pesta mabuk',
    # rokok
    'rokok', 'merokok', 'perokok', 'kretek', 'cerutu', 'vape', 'pod',
    # agama / okultisme
    'salib', 'yesus', 'kristus', 'alkitab', 'injil', 'natal', 'pohon natal',
    'halloween', 'labu', 'tarot', 'terawang', 'bintang lima', 'tengkorak',
    'setan', 'iblis', 'rosario', 'kuran', 'quran', 'masjid', 'gereja',
    'pura', 'vihara', 'ka bah', 'kabah',
    # lambang negara
    'garuda', 'lambang negara', 'burung garuda', 'pancasila', 'bendera merah putih',
    # ketidakpantasan
    'telanjang', 'bugil', 'seksi', 'erotis', 'judi', 'kasino', 'taruhan',
    'mesin slot', 'poker',
    # mata uang asing
    'dolar', 'euro', 'yen', 'poundsterling', 'tanda dolar', '$',
}

# Frasa yang wajib dicari sebagai frasa utuh (pakai \b), bukan per kata
FRASA_TERLARANG = ('piggy bank', 'eagle crest', 'national emblem',
                   'state symbol', 'coat of arms', 'slot machine',
                   'pound sterling', 'statue of liberty', 'big ben',
                   # 🇮🇩 frasa Indonesia (19 Okt 2026) — `periksa()` mencocokkan
                   # per kata, jadi bentuk dua kata WAJIB didaftarkan di sini.
                   'daging babi', 'minuman keras', 'pesta mabuk', 'pohon natal',
                   'lambang negara', 'burung garuda', 'bintang lima',
                   'mesin slot', 'tanda dolar', 'bendera merah putih')

# Larangan yang ditempel ke prompt model gambar.
LARANGAN_BUDAYA_PROMPT = (
    "Strictly no pigs, no piggy banks, no pork, no alcoholic drinks, no cigarettes, "
    "no religious symbols of any faith, no national emblems or state symbols "
    "(no Garuda, no eagle crest), no foreign/Western currency symbols, "
    "no dollar signs, no foreign landmarks or foreign banknote figures. "
    "Plain unmarked coins and banknotes only — absolutely no letter, no character, "
    "no number, no emblem, no logo stamped or printed on any coin, note or object. "
    "All objects, materials and props must suit everyday Indonesian context. "
)

# Pengganti yang AMAN & sesuai konteks Indonesia (untuk saran perbaikan brief)
PENGGANTI_AMAN = {
    'celengan': 'celengan tanah liat / kaleng / tabung bambu',
    'tabungan': 'kantong kain, kaleng, tabung bambu',
    'uang': 'koin polos tanpa cap, uang kertas polos',
    'wadah': 'keranjang bambu, bakul, anyaman pandan',
    'bangunan': 'rumah panggung, warung, masjid/netral',
}


def larangan_prompt():
    """Teks larangan siap tempel di prompt model gambar."""
    return LARANGAN_BUDAYA_PROMPT


def periksa(teks):
    """Periksa teks (brief/prompt) terhadap larangan budaya.

    Return: (kena: bool, alasan: list[str])

    ⚠️ JEBAKAN TERUKUR (18 Okt 2026): JANGAN pakai `[a-z' ]+` — itu menyatukan
    seluruh kalimat jadi SATU "kata" sehingga `'pig' in kata` SELALU False ⇒
    larangan babi LOLOS tanpa galat apa pun. Wajib `[a-z0-9']+`.
    """
    if not teks:
        return False, []
    rendah = teks.lower()
    kata = set(re.findall(r"[a-z0-9']+", rendah))
    temuan = []

    for t in FRASA_TERLARANG:
        if re.search(r'\b' + re.escape(t) + r'\b', rendah):
            temuan.append(t)

    for t in KATA_TERLARANG_BUDAYA:
        if ' ' in t:
            continue                      # frasa sudah ditangani di atas
        if t in kata:
            temuan.append(t)

    # Simbol mata uang asing
    for simbol, nama in (('$', 'dollar sign'), ('€', 'euro sign'),
                         ('£', 'pound sign'), ('¥', 'yen sign')):
        if simbol in teks:
            temuan.append(nama)

    if not temuan:
        return False, []
    return True, ["memuat unsur terlarang budaya: " + ", ".join(sorted(set(temuan)))]


def periksa_atau_gagal(teks, konteks="prompt"):
    """Periksa dan LEMPAR ValueError kalau melanggar (untuk jalur produksi)."""
    kena, alasan = periksa(teks)
    if kena:
        raise ValueError(f"{konteks} ditolak — " + "; ".join(alasan))
    return True


if __name__ == "__main__":
    import sys
    contoh = [
        ("babi", "A tin piggy bank cracked open with coins spilling out"),
        ("babi", "An old piggy bank on a wooden table"),
        ("garuda", "Coins stamped with an eagle crest emblem"),
        ("dollar", "Coins marked with a $ sign falling into a wallet"),
        ("aman", "A clay savings jar with a coin slot on a woven bamboo mat"),
        ("aman", "A bamboo tube savings container, plain coins beside it"),
    ]
    gagal = 0
    for nama, t in contoh:
        kena, alasan = periksa(t)
        harus_kena = nama != "aman"
        ok = (kena == harus_kena)
        print(f"{'LULUS' if ok else 'GAGAL'}  [{nama:7s}] {t[:52]:54s} {'' if ok else alasan}")
        gagal += 0 if ok else 1
    print(f"\n=== {len(contoh)-gagal} LULUS / {gagal} GAGAL ===")
    sys.exit(1 if gagal else 0)
