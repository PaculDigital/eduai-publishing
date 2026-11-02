"""Modul sampul dinamis EduAi, dari rancangan cover dinamis 2 Nov 2026.

Rancangan saja yang dibangun di sini, bukan wiring produksi. Modul ini
tidak memanggil pipeline buku, tidak generate gambar, dan tidak mengubah
produksi. Ia hanya menyusun sampul depan dan belakang dari satu berkas
gambar yang sudah ada, plus data order yang diberikan pemanggil.

Aturan yang dikunci di modul ini, sesuai rancangan:
- Jenis buku menentukan layout, keluarga tema menentukan palet.
- Momen di outline menentukan shot, jenis dan tema menentukan gaya.
- Satu sampul, satu gaya, tidak dicampur, kecuali collage dengan satu
  simbol jangkar.
- Semua tulisan dipasang sebagai teks asli, bukan digambar AI.
- Gambar tanpa teks di dalamnya, warna cerah profesional.
- User memilih 1 dari 3 preview di akhir, bila tidak memilih pakai Klasik.
- Foto penulis asli atau placeholder siluet FOTO, bio asli atau
  placeholder belum diisi, AI dilarang mengarang foto dan bio.
- Tidak ada tanda em dash di teks sampul, pisahkan klausa dengan koma
  atau titik. Fungsi cek_cover menolak teks yang mengandung em dash.
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1240, 1754
NAVY = (30, 58, 95)
ABU = (100, 116, 139)
GARIS = (203, 213, 225)
TUBUH = (51, 65, 85)
PUTIH = (255, 255, 255)
HITAM = (0, 0, 0)
SILUET = (150, 170, 190)
FOTO_BG = (220, 230, 240)
BAWAH_GRADASI = (255, 246, 230)

PALET_KELUARGA = {
    "bisnis": {"aksen": (15, 118, 110), "atas": (232, 241, 250)},
    "pendidikan": {"aksen": (29, 78, 216), "atas": (219, 234, 254)},
    "kesehatan": {"aksen": (22, 101, 52), "atas": (220, 242, 228)},
    "teknologi": {"aksen": (76, 29, 149), "atas": (233, 230, 255)},
    "sosial": {"aksen": (194, 65, 12), "atas": (255, 237, 213)},
    "umum": {"aksen": (15, 118, 110), "atas": (232, 241, 250)},
}

KELUARGA_KATA_KUNCI = [
    ("bisnis", ["umkm", "bisnis", "pemasaran", "kewirausahaan", "ekonomi", "usaha"]),
    ("pendidikan", ["matematika", "pendidikan", "sains", "pembelajaran", "sekolah", "ajar"]),
    ("kesehatan", ["kesehatan", "gizi", "keperawatan", "sehat", "medis"]),
    ("teknologi", ["teknologi", "digital", "robot", "data", "komputer", "ai"]),
    ("sosial", ["sosial", "budaya", "sejarah", "bahasa", "masyarakat", "humaniora"]),
]

LAYOUT_JENIS = {
    "referensi": "klasik",
    "ajar": "minimal",
    "monograf": "editorial",
    "panduan": "bold",
    "umum": "ilustrasi_tematik",
    "chapter": "foto_penuh_atas",
}

LAYOUT_SPESIFIKASI = {
    "klasik": {"judul": 132, "belah_ketupat": True, "kilau": True, "rata_kiri": False},
    "minimal": {"judul": 110, "belah_ketupat": False, "kilau": False, "rata_kiri": False},
    "editorial": {"judul": 120, "belah_ketupat": False, "kilau": False, "rata_kiri": True},
    "bold": {"judul": 150, "belah_ketupat": True, "kilau": True, "rata_kiri": False},
    "ilustrasi_tematik": {"judul": 132, "belah_ketupat": True, "kilau": True, "rata_kiri": False},
    "foto_penuh_atas": {"judul": 132, "belah_ketupat": True, "kilau": True, "rata_kiri": False},
}

PREVIEW_JENIS = {
    "referensi": ["klasik", "minimal", "foto_penuh_atas"],
    "ajar": ["minimal", "klasik", "foto_penuh_atas"],
    "monograf": ["editorial", "minimal", "klasik"],
    "panduan": ["bold", "klasik", "foto_penuh_atas"],
    "umum": ["ilustrasi_tematik", "klasik", "foto_penuh_atas"],
    "chapter": ["foto_penuh_atas", "klasik", "minimal"],
}

SHOT = {
    "macro": "Close-up ekstrem, fokus tajam di objek, latar blur",
    "pov": "Sudut pandang orang pertama, seolah pembaca sendiri yang memegang",
    "drone": "Dari atas, pola terlihat utuh",
    "wide": "Pemandangan utuh, suasana tema terbangun",
    "close_up_objek": "Objek tanpa wajah, tetap bercerita",
    "candid": "Momen nyata tanpa pose, tidak menatap kamera",
    "low_high": "Dari bawah supaya objek terasa besar, atau dari atas supaya terasa luas",
    "back_side": "Manusia ada, wajah bukan pusat, aktivitasnya pusat",
}

GAYA = {
    "realistis": "Foto editorial, detail nyata, cahaya alami",
    "3d": "Bentuk 3 dimensi, warna cerah, volume jelas",
    "minimalis": "Judul besar jadi pusat, ruang kosong lega, satu blok warna aksen",
    "flat": "Bentuk datar vektor, warna blok sederhana, mudah dibaca di thumbnail",
    "abstract": "Bentuk abstrak dan potongan elemen, satu simbol jangkar dari tema",
    "clay": "Bentuk lunak seperti tanah liat, permukaan lembut, kesan playful",
}

GAYA_JENIS = {
    "referensi": ("realistis", "minimalis"),
    "ajar": ("realistis", "flat"),
    "monograf": ("minimalis", "realistis"),
    "panduan": ("flat", "3d"),
    "umum": ("3d", "flat"),
    "chapter": ("minimalis", "realistis"),
}

LABEL_JENIS = {
    "referensi": "BUKU REFERENSI",
    "ajar": "BUKU AJAR",
    "monograf": "MONOGRAF",
    "panduan": "BUKU PANDUAN",
    "umum": "BUKU UMUM",
    "chapter": "CHAPTER",
}


def cari_font(nama):
    # Urutan: font sistem (apt fonts-dejavu-core di image), lalu font
    # yang ikut COPY app (app/static/font), sebagai pengaman bila image
    # berubah. Jangan mengandalkan satu lokasi saja, itu pelajaran dari
    # container lama yang font DejaVu-nya hilang.
    dasar = [
        '/usr/share/fonts',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'font'),
        '/app/app/static/font',
    ]
    for d in dasar:
        for p in glob.glob(os.path.join(d, '**', nama), recursive=True):
            return p
    raise FileNotFoundError(nama)


def pilih_keluarga(tema, judul=""):
    teks = f"{tema} {judul}".lower()
    for keluarga, kata_list in KELUARGA_KATA_KUNCI:
        for kata in kata_list:
            if kata in teks:
                return keluarga
    return "umum"


def pilih_gaya(jenis, tema="", judul=""):
    utama, kedua = GAYA_JENIS.get(jenis, ("realistis", "minimalis"))
    teks = f"{tema} {judul}".lower()
    konseptual = ["teori", "metodologi", "konsep", "filsafat", "pemikiran"]
    if jenis in ("referensi", "ajar") and any(k in teks for k in konseptual):
        return kedua
    return utama


def pilih_shot(momen=""):
    teks = (momen or "").lower()
    if any(k in teks for k in ["strategi", "keputusan", "catur", "pilihan"]):
        return "macro"
    if any(k in teks for k in ["sistem", "peta", "pasar", "distribusi", "wilayah"]):
        return "drone"
    if any(k in teks for k in ["tangan", "menata", "menulis", "mengetik", "membuka"]):
        return "pov"
    if any(k in teks for k in ["objek", "alat", "bangun", "perkakas", "produk"]):
        return "close_up_objek"
    if any(k in teks for k in ["terkejut", "aha", "gembira", "emosi"]):
        return "candid"
    return "candid"


def pilih_cover(jenis, tema, judul="", momen=""):
    jenis_kunci = jenis.lower() if isinstance(jenis, str) else "umum"
    if jenis_kunci not in LABEL_JENIS:
        jenis_kunci = "umum"
    keluarga = pilih_keluarga(tema, judul)
    palet = PALET_KELUARGA[keluarga]
    return {
        "jenis": jenis_kunci,
        "label": LABEL_JENIS[jenis_kunci],
        "keluarga": keluarga,
        "aksen": palet["aksen"],
        "atas": palet["atas"],
        "varian": LAYOUT_JENIS[jenis_kunci],
        "gaya": pilih_gaya(jenis_kunci, tema, judul),
        "shot": pilih_shot(momen),
    }


def cek_cover(konfig, judul_teks="", penulis="", penerbit=""):
    galat = []
    if konfig.get("varian") not in LAYOUT_SPESIFIKASI:
        galat.append("varian tidak ada di daftar terkunci")
    if konfig.get("gaya") not in GAYA:
        galat.append("gaya tidak ada di daftar terkunci")
    if konfig.get("shot") not in SHOT:
        galat.append("shot tidak ada di daftar terkunci")
    if konfig.get("aksen") not in [p["aksen"] for p in PALET_KELUARGA.values()]:
        galat.append("aksen tidak ada di palet terkunci")
    for nama, teks in [("judul", judul_teks), ("penulis", penulis), ("penerbit", penerbit)]:
        if "\u2014" in (teks or ""):
            galat.append(f"{nama} mengandung em dash")
    return galat


def _campur(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _latar(atas):
    strip = Image.new('RGB', (1, 512))
    px = strip.load()
    for y in range(512):
        t = y / 511
        px[0, y] = _campur(atas, PUTIH, t / 0.5) if t < 0.5 else _campur(
            PUTIH, BAWAH_GRADASI, (t - 0.5) / 0.5)
    return strip.resize((W, H))


def _teks_tengah(d, teks, font, y, warna):
    box = d.textbbox((0, 0), teks, font=font)
    lebar = box[2] - box[0]
    d.text(((W - lebar) / 2 - box[0], y), teks, font=font, fill=warna)
    return y + (box[3] - box[1])


def _teks_renggang(d, teks, font, y, warna, x_tengah=W / 2, renggang=12):
    total = 0
    for ch in teks:
        box = d.textbbox((0, 0), ch, font=font)
        total += (box[2] - box[0]) + renggang
    total -= renggang
    x = x_tengah - total / 2
    for ch in teks:
        box = d.textbbox((0, 0), ch, font=font)
        d.text((x - box[0], y), ch, font=font, fill=warna)
        x += (box[2] - box[0]) + renggang


def _tempel_gambar(cover, gambar_path, y_gambar, tinggi_target=None, potong=None):
    img = Image.open(gambar_path).convert('RGB')
    if potong:
        iw, ih = img.size
        img = img.crop((0, int(ih * potong[0]), iw, int(ih * potong[1])))
    if tinggi_target:
        target_rasio = W / tinggi_target
        iw, ih = img.size
        rasio = iw / ih
        if rasio > target_rasio:
            lebar_baru = int(ih * target_rasio)
            kiri = (iw - lebar_baru) // 2
            img = img.crop((kiri, 0, kiri + lebar_baru, ih))
        else:
            tinggi_baru = int(iw / target_rasio)
            atas = (ih - tinggi_baru) // 2
            img = img.crop((0, atas, iw, atas + tinggi_baru))
        img = img.resize((W, tinggi_target), Image.LANCZOS)
    else:
        tinggi = int(W * img.size[1] / img.size[0])
        img = img.resize((W, tinggi), Image.LANCZOS)
    cover.paste(img, (0, y_gambar))
    return y_gambar + img.size[1]


def susun_depan(gambar_path, label, judul_baris, penulis, terbit,
                aksen, atas, varian, out_path):
    if varian not in LAYOUT_SPESIFIKASI:
        raise ValueError("varian tidak ada di daftar terkunci")
    spes = LAYOUT_SPESIFIKASI[varian]
    cover = _latar(atas)
    if spes["kilau"]:
        lapis = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lapis)
        dl.ellipse([-160, -160, 320, 320], fill=(255, 225, 170, 45))
        dl.ellipse([W - 320, H - 320, W + 160, H + 160], fill=(180, 210, 235, 40))
        lapis = lapis.filter(ImageFilter.GaussianBlur(70))
        cover = Image.alpha_composite(cover.convert('RGBA'), lapis).convert('RGB')
    d = ImageDraw.Draw(cover)
    serif_b = cari_font('DejaVuSerif-Bold.ttf')
    sans_b = cari_font('DejaVuSans-Bold.ttf')
    sans = cari_font('DejaVuSans.ttf')
    f_label = ImageFont.truetype(sans_b, 46)
    f_judul = ImageFont.truetype(serif_b, spes["judul"])
    f_penulis = ImageFont.truetype(serif_b, 58)
    f_terbit = ImageFont.truetype(sans, 40)

    def tengah(teks, font, y, warna):
        return _teks_tengah(d, teks, font, y, warna)

    if varian == "foto_penuh_atas":
        bawah_gambar = _tempel_gambar(cover, gambar_path, 0, tinggi_target=900)
        _teks_renggang(d, label, f_label, bawah_gambar + 60, aksen)
        d.rectangle([W / 2 - 90, bawah_gambar + 148, W / 2 + 90, bawah_gambar + 154], fill=aksen)
        y = bawah_gambar + 200
        for baris in judul_baris:
            y = tengah(baris, f_judul, y, NAVY) + 18
        y_penulis = tengah(penulis, f_penulis, y + 60, NAVY)
        d.rectangle([W / 2 - 100, y_penulis + 42, W / 2 + 100, y_penulis + 45], fill=GARIS)
        tengah(terbit, f_terbit, y_penulis + 70, ABU)
    elif spes["rata_kiri"]:
        x_kiri = 120
        _teks_renggang(d, label, f_label, 108, aksen, x_tengah=x_kiri + 200)
        d.rectangle([x_kiri, 196, x_kiri + 180, 200], fill=aksen)
        y = 250
        for baris in judul_baris:
            box = d.textbbox((0, 0), baris, font=f_judul)
            d.text((x_kiri, y), baris, font=f_judul, fill=NAVY)
            y += (box[3] - box[1]) + 18
        bawah_gambar = _tempel_gambar(cover, gambar_path, 600, potong=(0.08, 0.95))
        box = d.textbbox((0, 0), penulis, font=f_penulis)
        d.text((x_kiri, bawah_gambar + 50), penulis, font=f_penulis, fill=NAVY)
        y_penulis = bawah_gambar + 50 + (box[3] - box[1])
        d.rectangle([x_kiri, y_penulis + 42, x_kiri + 200, y_penulis + 45], fill=GARIS)
        d.text((x_kiri, y_penulis + 70), terbit, font=f_terbit, fill=ABU)
    else:
        _teks_renggang(d, label, f_label, 108, aksen)
        if spes["belah_ketupat"]:
            d.rectangle([W / 2 - 90, 196, W / 2 + 90, 202], fill=aksen)
            cx, cy, r = W / 2, 199, 12
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=aksen)
        else:
            d.rectangle([W / 2 - 90, 196, W / 2 + 90, 200], fill=aksen)
        y = 250
        for baris in judul_baris:
            y = tengah(baris, f_judul, y, NAVY) + 18
        if varian == "klasik":
            bawah_gambar = _tempel_gambar(cover, gambar_path, 600, potong=(0.08, 0.95))
        else:
            bawah_gambar = _tempel_gambar(cover, gambar_path, 600)
        y_penulis = tengah(penulis, f_penulis, bawah_gambar + 50, NAVY)
        d.rectangle([W / 2 - 100, y_penulis + 42, W / 2 + 100, y_penulis + 45], fill=GARIS)
        tengah(terbit, f_terbit, y_penulis + 70, ABU)
    cover.save(out_path)
    return out_path


def preview_depan(gambar_path, jenis, label, judul_baris, penulis, terbit,
                  keluarga, out_dir, nama_dasar="preview"):
    palet = PALET_KELUARGA.get(keluarga, PALET_KELUARGA["umum"])
    varians = PREVIEW_JENIS.get(jenis, PREVIEW_JENIS["referensi"])
    hasil = []
    for i, varian in enumerate(varians, start=1):
        out_path = os.path.join(out_dir, f"{nama_dasar}-{i}-{varian}.png")
        susun_depan(gambar_path, label, judul_baris, penulis, terbit,
                    palet["aksen"], palet["atas"], varian, out_path)
        hasil.append(out_path)
    return hasil


def _bungkus_kata(d, kata_list, font, lebar_maks):
    baris, jalan = [], []
    for k in kata_list:
        uji = jalan + [k]
        lebar = sum(d.textbbox((0, 0), w, font=font)[2] for w in uji) + 10 * (len(uji) - 1)
        if lebar <= lebar_maks:
            jalan = uji
        else:
            baris.append(jalan)
            jalan = [k]
    if jalan:
        baris.append(jalan)
    return baris


def _gambar_baris_justify(d, kata_list, x, y, font, lebar_maks, warna, rata_kanan=True):
    if len(kata_list) <= 1 or not rata_kanan:
        d.text((x, y), ' '.join(kata_list), font=font, fill=warna)
        return
    total = sum(d.textbbox((0, 0), w, font=font)[2] for w in kata_list)
    celah = (lebar_maks - total) / (len(kata_list) - 1)
    cx = x
    for w in kata_list:
        d.text((cx, y), w, font=font, fill=warna)
        cx += d.textbbox((0, 0), w, font=font)[2] + celah


def _gambar_paragraf_justify(d, teks, x, y, font, lebar_maks, warna, tinggi_baris):
    baris = _bungkus_kata(d, teks.split(), font, lebar_maks)
    for i, kata_list in enumerate(baris):
        terakhir = (i == len(baris) - 1)
        _gambar_baris_justify(d, kata_list, x, y, font, lebar_maks, warna,
                              rata_kanan=not terakhir)
        y += tinggi_baris
    return y


def susun_belakang(judul_kecil, sinopsis, foto_path, bio, aksen, atas, out_path):
    cover = _latar(atas)
    lapis = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lapis)
    dl.ellipse([-160, -160, 320, 320], fill=(255, 225, 170, 45))
    dl.ellipse([W - 320, H - 320, W + 160, H + 160], fill=(180, 210, 235, 40))
    lapis = lapis.filter(ImageFilter.GaussianBlur(70))
    cover = Image.alpha_composite(cover.convert('RGBA'), lapis).convert('RGB')
    d = ImageDraw.Draw(cover)
    serif = cari_font('DejaVuSerif.ttf')
    serif_b = cari_font('DejaVuSerif-Bold.ttf')
    sans_b = cari_font('DejaVuSans-Bold.ttf')
    sans = cari_font('DejaVuSans.ttf')
    mono = cari_font('DejaVuSansMono.ttf')
    f_judul = ImageFont.truetype(serif_b, 56)
    f_header = ImageFont.truetype(sans_b, 40)
    f_tubuh = ImageFont.truetype(serif, 34)
    f_bio = ImageFont.truetype(serif, 34)
    x_kiri, lebar_teks = 140, 960
    _teks_tengah(d, judul_kecil, f_judul, 110, NAVY)
    _teks_renggang(d, 'TENTANG BUKU INI', f_header, 230, aksen, renggang=8)
    d.rectangle([W / 2 - 90, 296, W / 2 + 90, 302], fill=aksen)
    cx, cy, r = W / 2, 299, 11
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=aksen)
    y = _gambar_paragraf_justify(d, sinopsis, x_kiri, 350, f_tubuh, lebar_teks, TUBUH, 50)
    y += 40
    _teks_renggang(d, 'TENTANG PENULIS', f_header, y, aksen, renggang=8)
    y_bio = y + 60
    foto_w, foto_h, gap = 220, 260, 30
    if foto_path and os.path.exists(foto_path):
        foto = Image.open(foto_path).convert('RGB')
        fw, fh = foto.size
        rasio = foto_w / foto_h
        if fw / fh > rasio:
            baru_w = int(fh * rasio)
            x0 = (fw - baru_w) // 2
            foto = foto.crop((x0, 0, x0 + baru_w, fh))
        else:
            baru_h = int(fw / rasio)
            y0 = (fh - baru_h) // 2
            foto = foto.crop((0, y0, fw, y0 + baru_h))
        foto = foto.resize((foto_w, foto_h), Image.LANCZOS)
        cover.paste(foto, (x_kiri, y_bio))
        d = ImageDraw.Draw(cover)
    else:
        d.rectangle([x_kiri, y_bio, x_kiri + foto_w, y_bio + foto_h], fill=FOTO_BG, outline=GARIS, width=2)
        d.ellipse([x_kiri + 70, y_bio + 30, x_kiri + 150, y_bio + 110], fill=SILUET)
        d.pieslice([x_kiri + 40, y_bio + 120, x_kiri + 180, y_bio + 240], 180, 360, fill=SILUET)
        f_foto = ImageFont.truetype(sans_b, 32)
        box_foto = d.textbbox((0, 0), 'FOTO', font=f_foto)
        lebar_foto = box_foto[2] - box_foto[0]
        d.text((x_kiri + (foto_w - lebar_foto) / 2 - box_foto[0], y_bio + 200), 'FOTO', font=f_foto, fill=ABU)
    d.rectangle([x_kiri, y_bio, x_kiri + foto_w, y_bio + foto_h], outline=GARIS, width=2)
    bio_teks = (bio or "").strip() or "[Bio penulis belum diisi]"
    x_kolom = x_kiri + foto_w + gap
    lebar_kolom = 1100 - x_kolom
    tinggi_bio = 48
    baris_kolom = _bungkus_kata(d, bio_teks.split(), f_bio, lebar_kolom)
    n_samping = foto_h // tinggi_bio
    samping = baris_kolom[:n_samping]
    sisa = ' '.join(' '.join(b) for b in baris_kolom[n_samping:]).split()
    bawah = _bungkus_kata(d, sisa, f_bio, lebar_teks) if sisa else []
    for i, kata_list in enumerate(samping):
        terakhir = (i == len(samping) - 1) and not bawah
        _gambar_baris_justify(d, kata_list, x_kolom, y_bio + i * tinggi_bio, f_bio,
                              lebar_kolom, ABU, rata_kanan=not terakhir)
    y_bio_akhir = y_bio + len(samping) * tinggi_bio
    bawah_foto = y_bio + foto_h
    if bawah:
        y_bawah = bawah_foto + 20
        for i, kata_list in enumerate(bawah):
            terakhir = (i == len(bawah) - 1)
            _gambar_baris_justify(d, kata_list, x_kiri, y_bawah + i * tinggi_bio, f_bio,
                                  lebar_teks, ABU, rata_kanan=not terakhir)
        y_bio_akhir = y_bawah + len(bawah) * tinggi_bio
    kotak_atas = max(y_bio_akhir, bawah_foto) + 50
    kotak = (460, kotak_atas, 780, kotak_atas + 170)
    d.rectangle(kotak, fill=PUTIH, outline=GARIS, width=2)
    x_bar = kotak[0] + 25
    pola = [3, 5, 4, 6, 3, 8, 4, 5, 6, 3, 4, 8, 5, 3, 6, 4]
    idx = 0
    while x_bar < kotak[2] - 30:
        lebar_bar = pola[idx % len(pola)]
        idx += 1
        d.rectangle([x_bar, kotak[1] + 15, x_bar + lebar_bar, kotak[1] + 110], fill=HITAM)
        x_bar += lebar_bar + 3
    f_isbn = ImageFont.truetype(mono, 22)
    _teks_tengah(d, 'ISBN 978-xxx-x-xxxxx-x', f_isbn, kotak[3] - 32, HITAM)
    f_kecil = ImageFont.truetype(sans, 38)
    _teks_tengah(d, 'Harga: [diisi penerbit]', f_kecil, kotak[3] + 35, ABU)
    _teks_tengah(d, 'PT Bayana Hasana Duna  •  bayana.id', f_kecil, kotak[3] + 100, ABU)
    cover.save(out_path)
    return out_path
