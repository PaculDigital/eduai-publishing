"""JENIS BUKU = SATU PAKET GAYA (putusan Bos 18 Okt 2026).

ARA BOS (verbatim): "kalo yang dipilih buku umum untuk jenis anak atau
pendidikan maka ilustrasi bergaya seperti contoh saya itu. Paham. Termasuk
infografis bergaya sama."

KEPUTUSAN BOS (18 Okt 2026):
  1. Jenis DIPILIH USER saat mulai buku → seluruh gaya ikut OTOMATIS.
  2. ANAK ≠ PENDIDIKAN (Anak lebih ceria/mainan; Pendidikan lebih jelas/instruktif).
  3. INFOGRAFIS IKUT gaya yang sama — satu buku satu identitas.

⚠️ PRINSIP: JANGAN campur. Buku Anak dengan diagram gaya dewasa = dua wajah
dalam satu buku. Modul ini SATU-SATUNYA tempat gaya per jenis ditentukan.

Pakai:
    from jenis_buku import paket, JENIS
    p = paket("anak")
    p["ilustrasi"]   # style block gambar AI
    p["palet"]       # palet infografis
    p["label"]       # bentuk & font label
    p["tone"]        # arahan menulis (bukan cuma gambar!)
"""

# ══════════════════════════════════════════════════════════════════════════
# JENIS BUKU
# ══════════════════════════════════════════════════════════════════════════
JENIS = {
    "umum": {
        "nama": "Buku Umum (dewasa)",
        "untuk": "bisnis, hukum, ekonomi, sosial, kepemimpinan",
        "contoh": "Ekonomi Digital, Manajemen Risiko, Hukum Bisnis",
    },
    "anak": {
        "nama": "Buku Anak",
        "untuk": "usia 4–10 tahun, cerita + pengetahuan dasar",
        "contoh": "Ayo Kenal Siklus Hujan, Petualangan di Pasar",
    },
    "pendidikan": {
        "nama": "Buku Pendidikan",
        "untuk": "SD–SMP, buku penunjang pelajaran, modul belajar",
        "contoh": "Modul IPA Kelas 5, Buku Latihan Matematika",
    },
}


# ══════════════════════════════════════════════════════════════════════════
# PAKET GAYA — satu entri = satu wajah buku yang utuh
# ══════════════════════════════════════════════════════════════════════════
PAKET = {
    # ── BUKU UMUM DEWASA (gaya lama, JANGAN diubah) ──────────────────────
    "umum": {
        "gaya_gambar": "premium-konseptual",
        "mode_brief": "konseptual",
        "ilustrasi": None,      # diambil dari brief_visual.STYLE_BUKU
        #  Jangkar konsistensi (barang 14, Fase 4): ditempel prompt_gambar
        #  ke setiap prompt jenis ini.
        "jangkar": (
            "Consistent series style for the whole book: the same flat "
            "vector editorial style, the same deep navy and terracotta "
            "palette, and one clear visual metaphor per illustration."
        ),
        "palet": {
            "krem": "#FFF9EE",
            "tinta": "#1B3A57",
            "aksen": "#F2994A",
            "hijau": "#27AE60",
            "biru": "#2D9CDB",
            "kuning": "#F2C94C",
            "merah": "#EB5757",
            "langit": "#E8F4FB",
        },
        "label": {
            "bentuk": "kotak",          # sudut agak tegas = terlihat dewasa
            "radius": "18px",
            "font": "'DejaVu Sans', Arial, sans-serif",
            "tebal": "700",
            "ukuran": "22px",
            "huruf_besar": False,
            "bayangan": "0 4px 0 #1B3A57",
        },
        "judul": {"ukuran": "44px", "huruf_besar": True, "tebal": "800"},
        "tone": (
            "Formal-santai-naratif (bukan buku ajar, tidak ada TIU/TIK/Latihan). "
            "Pembaca: profesional, mahasiswa, pengusaha. Tulis seperti 'ngobrol "
            "cerdas' — kredibel tapi mengalir, tidak menggurui."
        ),
        "tone_visual": "metafora konseptual, negative space lega, tenang & mahal",
    },

    # ── BUKU ANAK (gaya contoh Bos) ──────────────────────────────────────
    "anak": {
        "gaya_gambar": "anak",
        "mode_brief": "literal",
        #  🚨 DIUBAH 20 Okt 2026 atas PERINTAH BOS (verbatim):
        #  "Gambar ilustrasi background putih saja ada outline, daripd sekarang
        #   background coklat muda, seperti buku kuno/lawas dan terlihat kotor
        #   atau background abu abu muda / halus"
        #  Versi lama menulis `light blue background` + `smiling sun character`
        #  + `3D render` ⇒ latar BIRU BERGRADASI, tanpa garis tepi, dan
        #  matahari berwajah muncul di SETIAP gambar (isi melenceng dari bab).
        #  Perintah Bos MENGGANTI "verbatim 18 Okt" — bukan Wulan yang mengubah
        #  sendiri.
        "ilustrasi": (
            "Children's educational illustration, clean flat cartoon style, "
            "clear dark outlines around every shape, simple rounded forms, "
            "cheerful but controlled colors, on a clean PURE WHITE background "
            "(hex #FFFFFF), no cream, no beige, no blue tint, "
            "no gradient background, no vignette, no paper texture, no grain, "
            "no shadows on the background, no gradients on objects, "
            "no 3D render, no photorealism, "
            "no text, no words, no letters, no numbers, no watermark. "
            #  🚨 WAJIB: {brief} HARUS ADA. Tanpa placeholder ini, brief
            #  dibuang oleh .format() dan AI mengarang isi gambar sendiri
            #  (terukur 20 Okt: brief "anak menjiplak bayangan tongkat"
            #  menjadi gambar "anak membayar di kasir toko").
            "SCENE — illustrate EXACTLY this moment, nothing else: {brief}. "
            "The scene above is the SUBJECT; keep every object named in it"
        ),
        #  Jangkar konsistensi (barang 14, Fase 4).
        "jangkar": (
            "Consistent series style for the whole book: the same cheerful "
            "flat cartoon style and bright palette, and if a character "
            "appears, the same character design in every illustration."
        ),
        "palet": {
            # Langit cerah + krem hangat: sama seperti latar ilustrasi clay
            "krem": "#FFF6E5",
            "langit": "#DFF3FF",
            "tinta": "#2B4A63",          # navy lembut, bukan hitam pekat
            "aksen": "#FF8A3D",          # oranye hangat
            "hijau": "#5FD068",
            "biru": "#4EB8E8",
            "kuning": "#FFD23F",
            "merah": "#FF6B6B",
        },
        "label": {
            "bentuk": "kapsul",          # bulat penuh = ramah anak, seperti stiker
            "radius": "999px",
            "font": "'DejaVu Sans', 'Comic Sans MS', sans-serif",
            "tebal": "800",
            "ukuran": "24px",
            "huruf_besar": False,        # anak membaca lebih mudah HURUF BESAR?
            "bayangan": "0 5px 0 rgba(43,74,99,.85)",   # chunky, seperti mainan
        },
        "judul": {"ukuran": "50px", "huruf_besar": True, "tebal": "800"},
        "tone": (
            "Bahasa sederhana, kalimat PENDEK, sapaan langsung ke anak ('kamu'), "
            "banyak contoh yang bisa dilihat di rumah/sekolah. Hindari istilah "
            "teknis; kalau perlu, jelaskan dengan perbandingan. Nada hangat & "
            "mengajak bermain, bukan mengajari."
        ),
        "tone_visual": "ceria, bulat, warna cerah, banyak ruang bermain",
    },

    # ── BUKU PENDIDIKAN (lebih terstruktur, tetap kartun bersih) ─────────
    "pendidikan": {
        "gaya_gambar": "anak",       # gaya gambar SAMA (kartun), beda arahan
        "mode_brief": "berslot",     # barang 13: brief berslot + contoh jadi
        #  ⚠️ Sama seperti `anak`: latar putih + outline (perintah Bos
        #  20 Okt 2026). Versi lama `light blue background` + `3D render`.
        #  Ditulis ulang POSITIF-DULU (barang 14, 23 Okt 2026): subjek &
        #  deskripsi jelas di depan, larangan dipangkas pendek di ekor.
        #  ⚠️ {brief} WAJIB ada (lihat catatan paket `anak`).
        "ilustrasi": (
            "Illustrate exactly this scene for an educational book: {brief}. "
            "Clean flat educational cartoon illustration, clear dark outlines "
            "around every shape, simple rounded forms, one clear focal "
            "subject with generous empty space around it, calm controlled "
            "colors - deep navy and warm orange accents - on a clean pure "
            "white background (hex #FFFFFF). "
            "No text, no words, no letters, no numbers, no watermark, "
            "no gradients, no 3D render, no photorealism, "
            "no cream or beige tint."
        ),
        #  Jangkar konsistensi (barang 14): ditempel brief_visual ke SETIAP
        #  prompt jenis ini — gaya & tokoh sama di semua gambar satu buku.
        "jangkar": (
            "Consistent series style for the whole book: the same flat "
            "educational cartoon style, the same deep navy and warm orange "
            "palette, and if a person appears, the same simple character "
            "design in every illustration."
        ),
        "palet": {
            # Lebih kalem dari buku anak: untuk belajar, bukan bermain
            "krem": "#F7FAFC",
            "langit": "#E3F0F7",
            "tinta": "#1F3C56",
            "aksen": "#F08A3C",
            "hijau": "#3FA36B",
            "biru": "#3D8FC4",
            "kuning": "#F2C244",
            "merah": "#D9534F",
        },
        "label": {
            "bentuk": "kapsul",
            "radius": "16px",            # agak tegas: ini buku belajar
            "font": "'DejaVu Sans', Arial, sans-serif",
            "tebal": "700",
            "ukuran": "22px",
            "huruf_besar": False,
            "bayangan": "0 4px 0 rgba(31,60,86,.85)",
        },
        "judul": {"ukuran": "44px", "huruf_besar": True, "tebal": "800"},
        "tone": (
            "Jelas, bertahap, satu gagasan per paragraf. Boleh memakai istilah "
            "ilmiah TAPI wajib langsung dijelaskan. Ada urutan langkah yang "
            "tersurat (pertama, kedua, ketiga). Nada membimbing, sabar, tidak "
            "bermain-main seperti buku anak."
        ),
        "tone_visual": "rapi, berurutan, jelas dibaca, tetap ramah",
    },
}


def paket(jenis="umum"):
    """Ambil SATU PAKET gaya untuk jenis buku. Raise kalau jenis tidak dikenal.

    ⚠️ JANGAN fallback diam-diam ke 'umum': user yang memilih 'anak' tapi
    mendapat gaya dewasa akan bingung dan tidak sadar bukunya salah wajah.
    """
    if jenis not in PAKET:
        raise ValueError(
            f"jenis buku '{jenis}' tidak dikenal. Pilihan: {', '.join(PAKET)}")
    return PAKET[jenis]


def palet_infografis(jenis="umum"):
    """Palet untuk label_infografis — supaya infografis ikut jenis buku."""
    return dict(PAKET[paket(jenis) and jenis]["palet"])


def css_label(jenis="umum"):
    """CSS label sesuai jenis buku (bentuk, font, bayangan)."""
    lb = paket(jenis)["label"]
    return (
        f"border-radius:{lb['radius']};"
        f"font-family:{lb['font']};"
        f"font-weight:{lb['tebal']};"
        f"font-size:{lb['ukuran']};"
        f"box-shadow:{lb['bayangan']};"
    )


def label_css_penuh(jenis="umum"):
    """Blok CSS .label lengkap untuk jenis buku — dipakai html_infografis."""
    p = paket(jenis)
    lb, jd, t = p["label"], p["judul"], p["palet"]["tinta"]
    transform = "uppercase" if lb["huruf_besar"] else "none"
    jtransform = "uppercase" if jd["huruf_besar"] else "none"
    return f"""
  .label {{
    position:absolute; z-index:6; transform:translate(-50%,-50%);
    background:#fff; border:3px solid {t}; border-radius:{lb['radius']};
    padding:9px 18px; font-family:{lb['font']}; font-size:{lb['ukuran']};
    font-weight:{lb['tebal']}; color:{t}; box-shadow:{lb['bayangan']};
    white-space:nowrap; max-width:46%; line-height:1.15;
    text-transform:{transform};
  }}
  .judul {{
    position:absolute; top:24px; left:0; right:0; text-align:center;
    font-family:{lb['font']}; font-size:{jd['ukuran']}; font-weight:{jd['tebal']};
    letter-spacing:.5px; text-transform:{jtransform}; z-index:5;
    text-shadow:0 2px 0 #fff, 0 0 12px rgba(255,255,255,.85);
  }}
"""


if __name__ == "__main__":
    for j in PAKET:
        p = paket(j)
        print(f"{j:12s} gambar={p['gaya_gambar']:20s} brief={p['mode_brief']:11s} "
              f"label={p['label']['bentuk']:8s} radius={p['label']['radius']}")
    print()
    try:
        paket("remaja")
        print("SALAH: jenis asing tidak dilempar")
    except ValueError as e:
        print("BENAR:", e)
