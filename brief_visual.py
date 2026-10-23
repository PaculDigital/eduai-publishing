#!/usr/bin/env python3
"""
brief_visual.py — BRIEF DARI ISI BAB (Tahap 1), bukan dari label topik.

Terukur 18 Okt 2026, buku "Ekonomi Digital" bab 1-3 (ringkasan nyata dari
checkpoint /opt/data/buku_umum_test/checkpoint.json).

MASALAH YANG DIPERBAIKI
  Dulu: prompt gambar = label topik bab ("ilustrasi smartphone wallet") +
        template 3D "photorealistic, rich lighting" → hasil = wallpaper fintech
        generik, tidak ada hubungan dengan ISI bab, dan tidak tahan cetak B/W
        (render 3D rich-lighting jadi abu-abu kotor saat dicetak hitam-putih).

SOLUSI 2 TAHAP
  Tahap 1: LLM (call_llm yang sudah ada) menulis SATU brief visual konkret
           dari RINGKASAN BAB + sub-bab di sekitar posisi gambar.
  Tahap 2: prompt gambar = STYLE_BUKU + brief tahap 1.

GAYA: 'editorial-lineart' (default, ACC Bos 18 Okt 2026) — line art navy +
terracotta di atas LATAR PUTIH BERSIH. Tahan cetak B/W, timeless.
⚠️ 20 Okt 2026: latar krem DIGANTI putih bersih — Bos: "background coklat
muda, seperti buku kuno/lawas dan terlihat kotor". SATU gaya untuk SELURUH bab = identitas visual buku.

PAGAR QC (Bos: "kalau orang awam tidak bisa menebak bab ini tentang apa hanya
dari gambarnya, brief-nya terlalu generik"):
  apa_brief_generik() menolak brief yang tidak punya 3 unsur wajib:
    (1) ADA TOKOH (siapa) — minimal satu kata orang,
    (2) ADA ADEGAN/TINDAKAN (sedang apa) — kata kerja aksi,
    (3) ADA LATAR/OBJEK KONKRET — benda yang bisa disebut namanya.
  Brief ditolak → generate ulang brief (LLM), BUKAN ganti seed gambar.

API:
  brief_visual(ringkasan_bab, sub_bab=None, panggil_llm=None) -> str
  prompt_gambar(brief, gaya='editorial-lineart')            -> str
  buat_ilustrasi(ringkasan_bab, sub_bab=None, ...)          -> dict
  apa_brief_generik(brief) -> (bool, [alasan...])   # True = TERLALU GENERIK
"""
import json
import re

# ══════════════════════════════════════════════════════════════════════════
# GAYA GAMBAR BUKU — satu gaya untuk seluruh bab
# ══════════════════════════════════════════════════════════════════════════
STYLE_BUKU = {
    # DEFAULT v3 (koreksi Bos 20 Okt 2026) — LATAR BERSIH, BUKAN KREM.
    # 🚨 KELUHAN BOS (verbatim): "Gambar ilustrasi background putih saja ada
    #    outline, daripd sekarang background coklat muda, seperti buku kuno/
    #    lawas dan terlihat kotor atau background abu abu muda / halus".
    # AKAR: v2 menulis `on warm cream background` + `paper grain` ⇒ latar
    # krem + tekstur = kesan buku lawas/kotor.
    # OBAT: latar PUTIH bersih (hex eksplisit), outline tipis tegas, TANPA
    # tekstur kertas, TANPA warna krem/coklat di mana pun.
    "premium-konseptual": (
        "Premium conceptual editorial illustration for a bestselling "
        "non-fiction book, single clever visual metaphor, modern flat vector "
        "style, limited palette of deep navy and warm terracotta, "
        "on a clean PURE WHITE background (hex #FFFFFF), no cream, no beige, "
        "no brown tint anywhere, crisp thin dark outlines around every shape, "
        "one central focal subject with generous negative space, minimalist "
        "elegant composition, smooth flat surfaces with no paper texture, "
        "no grain, no stains, no vignette, no gradients, no photorealism, "
        "no 3D, no clutter, no text, no words, no letters, no watermark. "
        "Scene: {brief}"
    ),
    # v1 lama — line art tipis. Disimpan untuk buku teknis/panduan.
    # ⚠️ Latar krem DIGANTI putih bersih 20 Okt 2026 (keluhan Bos: "kotor").
    "editorial-lineart": (
        "Editorial book illustration, elegant thin line art, navy blue ink lines "
        "with warm terracotta accents on a clean PURE WHITE background "
        "(hex #FFFFFF), crisp dark outlines, minimalist flat design, no cream, "
        "no beige, no paper texture, no grain, no gradients, no shadows, no 3D, "
        "no photorealism, no glow, clean and professional, non-fiction book "
        "interior art. Scene: {brief}"
    ),
    # Cadangan — hanya dipakai kalau Bos minta variasi; TETAP 1 gaya per buku.
    "woodcut": (
        "Editorial book illustration, bold woodcut-style line art, single ink color "
        "with one accent color on a clean PURE WHITE background (hex #FFFFFF), "
        "crisp outlines, hatching for texture, no cream, no beige, no paper tone, "
        "no gradients, no 3D, no photorealism, non-fiction book interior art. "
        "Scene: {brief}"
    ),
    "flat-editorial": (
        "Editorial book illustration, flat vector shapes with limited palette "
        "(navy, terracotta) on a clean PURE WHITE background (hex #FFFFFF), "
        "crisp thin outlines, no cream, no beige, no gradients, "
        "no 3D, no photorealism, non-fiction book interior art. Scene: {brief}"
    ),
}
GAYA_DEFAULT = "premium-konseptual"

# Gaya buku ANAK / PENDIDIKAN.
#  🚨 CACAT TERUKUR 20 Okt 2026 (dilihat mata dari PNG hasil uji):
#  gaya ini tidak pernah menyebut latar putih / outline, dan MASIH menulis
#  `light blue background` ⇒ hasilnya latar BIRU BERGRADASI tanpa garis
#  tepi, padahal Bos minta "background putih saja ada outline".
#  `smiling sun character` juga MEMAKSA matahari berwajah muncul di tiap
#  gambar — itulah sebabnya isi gambar melenceng dari isi bab.
#  OBAT: latar PUTIH bersih, outline tegas, buang pemaksaan karakter
#  matahari; isi gambar WAJIB ikut brief (adegan dari bab).
#  ─────────────────────────────────────────────────────────────────────────
#  🗑️  `STYLE_BUKU["anak"]` DIHAPUS 22 Okt 2026 — atas perintah Bos:
#      "buang atau hapus yang tidak terpakai jadikan SOT, jangan berantakan"
#
#  ALASAN (terukur, bukan selera):
#    • `brief_visual.py:696` menulis:  blok = pkg["ilustrasi"] or STYLE_BUKU…
#    • Untuk jenis "anak", `jenis_buku.PAKET["anak"]["ilustrasi"]` = 571 char
#      ⇒ `STYLE_BUKU["anak"]` (518 char) TIDAK PERNAH DIEKSEKUSI.
#    • Kedua salinan isinya SUDAH BERBEDA ⇒ inilah sumber "kok jadi beda-beda".
#
#  SOT: `mutu-buku/gambar-dan-visual/SOT-BLOK-GAYA.md`
#  BLOK GAYA ANAK YANG BERLAKU: `jenis_buku.py` → `PAKET["anak"]["ilustrasi"]`
#
#  ⚠️ JANGAN ditambahkan kembali. Kalau perlu ubah gaya anak, ubah di
#     `jenis_buku.py` (satu tempat). 4 gaya lain di bawah tetap dipakai.
#  ─────────────────────────────────────────────────────────────────────────

# Buku anak butuh adegan yang DIKENALI ANAK, bukan metafora abstrak ⇒ mode brief
# `literal` yang benar untuk gaya ini. QC konseptual dimatikan, QC budaya TETAP.
MODE_BRIEF_PER_GAYA = {
    "anak": "literal",
    "premium-konseptual": "konseptual",
    "editorial-lineart": "konseptual",
}

# Larangan teks WAJIB di SETIAP prompt (hallucination huruf merusak buku)
EKOR_LARANGAN = ("No text, no words, no letters, no numbers, no watermark.")

# Template brief LITERAL (v1) — disimpan untuk buku praktis/panduan teknis.
PROMPT_BRIEF_LITERAL = """Buatkan SATU brief visual (2-3 kalimat, bahasa Inggris) untuk ilustrasi
di tengah bab buku umum non-fiksi, berdasarkan ringkasan bab di bawah.

SYARAT BRIEF:
1. Pilih SATU momen paling visual dari isi bab — adegan yang pembaca
   "lihat" saat membaca bagian tengah bab.
2. Konkret dan spesifik: siapa/apa saja yang terlihat, sedang melakukan
   apa, objek dan latar apa. Jangan konsep abstrak tanpa wujud.
3. Setting dan tokoh: Indonesia sehari-hari (bukan model iklan);
   sesuaikan dengan contoh yang dipakai di bab bila ada.
4. JANGAN pernah meminta teks, huruf, angka, logo, atau tulisan
   di dalam gambar.
5. Hanya deskripsi visual — tanpa penjelasan, tanpa pembuka/penutup.

RINGKASAN BAB:
{ringkasan_bab}

SUB-BAB DI SEKITAR POSISI GAMBAR:
{sub_bab}"""

# Template brief KONSEPTUAL (v2, DEFAULT) — ide Bos 18 Okt 2026, VERBATIM.
# Alasan: adegan literal = tampilan ilustrasi stok. Buku premium pakai metafora.
PROMPT_BRIEF_KONSEPTUAL = """Dari ringkasan bab berikut, buatkan SATU brief visual KONSEPTUAL
(2-3 kalimat, bahasa Inggris) untuk ilustrasi buku non-fiksi premium.

CARA BERPIKIR (ikuti urutannya):
1. IDE INTI: rumuskan satu kalimat — apa ide terpenting bab ini?
2. METAFORA VISUAL: ubah ide itu menjadi metafora visual yang konkret
   dan mengejutkan TAPI langsung terbaca. Benda nyata disusun dengan
   cara tak biasa. Contoh: bab tentang jebakan utang -> "a person rowing
   a small boat while water pours in through the sieve they bail with".
3. KOMPOSISI: satu fokus utama, negative space lega di sekelilingnya.
   Jangan penuhi frame.
4. DILARANG: adegan literal sehari-hari, teks/huruf/angka/logo,
   lebih dari satu ide dalam satu gambar.
5. DILARANG unsur lintas-budaya yang tidak pantas untuk pembaca Indonesia:
   babi/celengan babi, minuman keras, rokok, simbol agama apa pun,
   mata uang/simbol asing (dollar, euro), bangunan ikon negara lain.
   Pilih benda netral & sesuai konteks Indonesia (mis. celengan tanah liat,
   kaleng, atau tabung bambu — bukan piggy bank).
6. Output hanya 2-3 kalimat deskripsi visual bahasa Inggris. Hindari kata
   abstract/conceptual/glowing/luminous/gradient/3D — buku ini gaya cetak,
   bukan layar.

RINGKASAN BAB:
{ringkasan_bab}"""

# Alias lama (kompatibilitas)
PROMPT_BRIEF = PROMPT_BRIEF_LITERAL

# ══════════════════════════════════════════════════════════════════════════
# PAGAR QC — brief generik ditolak
# ══════════════════════════════════════════════════════════════════════════
KATA_ORANG = {
    'man', 'woman', 'people', 'person', 'vendor', 'owner', 'seller', 'buyer',
    'customer', 'merchant', 'student', 'teacher', 'worker', 'farmer', 'driver',
    'rider', 'couple', 'family', 'child', 'children', 'mother', 'father',
    'shopkeeper', 'pedagang', 'elderly', 'villager', 'clerk', 'trader',
    'passenger', 'commuter', 'neighbor', 'young', 'boy', 'girl', 'crowd',
    'staff', 'employee', 'guard', 'nurse', 'doctor', 'officer', 'baker',
    'tailor', 'fisherman', 'hand', 'hands', 'face', 'silhouette', 'figure',
}
KATA_AKSI = {
    'holding', 'scanning', 'smiling', 'showing', 'paying', 'counting', 'typing',
    'looking', 'reading', 'writing', 'talking', 'handing', 'buying', 'selling',
    'picking', 'packing', 'carrying', 'stacking', 'arranging', 'opening',
    'walking', 'sitting', 'standing', 'browsing', 'swiping', 'tapping',
    'recording', 'measuring', 'checking', 'signing', 'wrapping', 'pouring',
    'serving', 'waiting', 'haggling', 'loading', 'delivering', 'sorting',
}
KATA_LATAR = {
    'warung', 'shop', 'stall', 'market', 'stallfront', 'counter', 'table',
    'desk', 'kitchen', 'street', 'alley', 'office', 'classroom', 'warehouse',
    'shelves', 'shelf', 'crates', 'boxes', 'cart', 'truck', 'motorbike',
    'scooter', 'bicycle', 'phone', 'smartphone', 'laptop', 'terminal',
    'sack', 'basket', 'tray', 'mug', 'cup', 'board', 'sign', 'awning',
    'tiles', 'roof', 'window', 'door', 'stair', 'bench', 'field', 'rice',
    'noodles', 'coffee', 'sachets', 'packets', 'bottles', 'cash', 'coins',
    'notes', 'receipt', 'scanner', 'printer', 'charger', 'cable', 'network',
    'tower', 'antenna', 'screen', 'monitor', 'keyboard', 'drum', 'pan',
}

# ── Kosakata BUKU ANAK / PENDIDIKAN (tambah 18 Okt 2026) ──────────────────
# TERUKUR: brief buku anak "smiling sun above a calm blue sea with steam rising
# toward a fluffy cloud" DITOLAK QC literal karena 'sun'/'sea'/'cloud' tidak ada
# di daftar dewasa. Akibatnya ilustrasi buku anak mustahil lolos. Daftar alam &
# benda sehari-hari WAJIB ada supaya QC tidak memakan brief yang benar.
KATA_ORANG |= {
    'sun', 'moon', 'star', 'character', 'kid', 'kids', 'baby', 'friend',
    'grandmother', 'grandfather', 'grandma', 'grandpa', 'uncle', 'aunt',
    'animal', 'animals', 'cat', 'bird', 'fish', 'rabbit', 'butterfly',
}
KATA_AKSI |= {
    'rising', 'falling', 'flowing', 'drifting', 'floating', 'melting',
    'freezing', 'growing', 'sprouting', 'bird', 'flying', 'swimming',
    'smiling', 'waving', 'playing', 'jumping', 'singing', 'laughing',
    'evaporating', 'condensing', 'raining', 'shining', 'glowing',
}
KATA_LATAR |= {
    'sea', 'ocean', 'lake', 'river', 'water', 'wave', 'waves', 'cloud',
    'clouds', 'rain', 'steam', 'vapor', 'smoke', 'sun', 'moon', 'sky',
    'hill', 'mountain', 'forest', 'tree', 'trees', 'leaf', 'leaves', 'grass',
    'flower', 'flowers', 'seed', 'seeds', 'root', 'roots', 'garden', 'park',
    'beach', 'island', 'sand', 'soil', 'ground', 'land', 'earth', 'globe',
    'planet', 'wind', 'snow', 'ice', 'fire', 'light', 'shadow', 'rainbow',
    'school', 'library', 'playground', 'bedroom', 'yard', 'farm', 'barn',
    'puddle', 'bucket', 'well', 'pipe', 'tap', 'bottle', 'umbrella',
    'backpack', 'book', 'books', 'pencil', 'crayon', 'paper', 'toy', 'toys',
    'ball', 'kite', 'bicycle', 'bus', 'train', 'boat', 'plane', 'rocket',
}
KATA_ABSTRAK_TERLARANG = {
    'abstract', 'concept', 'conceptual', 'futuristic', 'glowing', 'hologram',
    'gradient', '3d', 'render', 'photorealistic', 'cyberspace', 'network of light',
}

# ══════════════════════════════════════════════════════════════════════════
# LARANGAN LINTAS-BUDAYA (teguran Bos 18 Okt 2026: "Celengan jangan babi")
# ══════════════════════════════════════════════════════════════════════════
#  SATU SUMBER KEBENARAN = /opt/data/larangan_budaya.py (modul bersama).
#  JANGAN mengetik ulang daftar di sini — dulu sempat terduplikasi.
from larangan_budaya import (KATA_TERLARANG_BUDAYA, LARANGAN_BUDAYA_PROMPT,
                             periksa as _periksa_budaya)


def apa_brief_terlarang_budaya(brief):
    """True = brief memuat unsur TERLARANG BUDAYA (babi/alkohol/lambang asing)."""
    return _periksa_budaya(brief)


# ══════════════════════════════════════════════════════════════════════════
# MODE BRIEF: 'literal' (v1) vs 'konseptual' (v2 — DEFAULT sejak 18 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  Temuan Bos: adegan LITERAL ("pemilik warung memegang HP") pasti terlihat
#  seperti ilustrasi stok, seberapa pun bagusnya gaya gambarnya. Buku premium
#  pakai METAFORA: satu ide bab → satu gambar cerdas (timbangan dengan HP di
#  satu sisi & koin di sisi lain = teknologi baru vs cara lama, seimbang).
#  ⇒ brief konseptual = DEFAULT. Mode literal disimpan untuk buku praktis/
#    panduan teknis yang butuh adegan nyata. JANGAN dicampur dalam 1 buku.
MODE_BRIEF = "konseptual"

# Benda/objek yang lazim jadi BAHAN metafora — dipakai QC mode konseptual
KATA_BENDA_METAFORA = {
    'scale', 'scales', 'balance', 'seesaw', 'boat', 'sieve', 'bucket', 'net',
    'ladder', 'door', 'key', 'lock', 'bridge', 'rope', 'thread', 'needle',
    'mirror', 'window', 'map', 'compass', 'hourglass', 'clock', 'lantern',
    'lamp', 'seed', 'tree', 'root', 'branch', 'soil', 'water', 'river',
    'rain', 'cloud', 'funnel', 'filter', 'net', 'cage', 'box', 'chest',
    'jar', 'bottle', 'funnel', 'sieve', 'sack', 'basket', 'pot', 'kettle',
    'candle', 'fire', 'smoke', 'thread', 'knot', 'chain', 'anchor', 'wheel',
    'gear', 'cog', 'engine', 'pipe', 'tap', 'bucket', 'umbrella', 'shield',
    'armour', 'sword', 'hammer', 'anvil', 'plough', 'sickle', 'harvest',
    'coin', 'coins', 'phone', 'smartphone', 'wallet', 'book', 'paper',
    'card', 'receipt', 'stamp', 'envelope', 'parcel', 'suitcase', 'stair',
    'staircase', 'hill', 'mountain', 'cliff', 'well', 'spring', 'pump',
    'va', 'vacuum', 'magnifier', 'telescope', 'microscope', 'balance',
    'domino', 'magnet', 'mirror', 'shadow', 'thread', 'web', 'spider',
    'nest', 'egg', 'shell', 'root', 'graft', 'scissors', 'tape', 'glue',
}
KATA_HUBUNGAN_KONSEP = {
    'balance', 'balanced', 'balancing', 'weighing', 'tipping', 'outweigh',
    'pouring', 'leaking', 'escaping', 'holding', 'carrying', 'bridging',
    'connecting', 'separating', 'growing', 'withering', 'stacking',
    'overflowing', 'sinking', 'floating', 'anchored', 'tangled', 'unravelling',
    'unraveling', 'opening', 'closing', 'locking', 'unlocking', 'chained',
    'funnelling', 'funneling', 'filtering', 'draining', 'filling', 'emptying',
    'splitting', 'merging', 'stretching', 'bending', 'breaking', 'repairing',
    'patching', 'stitching', 'tying', 'threading', 'woven', 'grafted',
    # ── Ditambah 18 Okt 2026 setelah CACAT TERUKUR: metafora bagus ("koin
    #    mengalir jadi sungai ke ponsel") DITOLAK karena kata kerjanya tidak
    #    ada di daftar. QC kata-kerja-tetap = rapuh; daftar harus LUAS.
    'spilling', 'flowing', 'flows', 'flow', 'streaming', 'streams', 'stream',
    'arranging', 'arranged', 'rearranging', 'assembling', 'forming', 'forming',
    'tracing', 'shaping', 'becoming', 'turning', 'replacing', 'absorbing',
    'dissolving', 'melting', 'evaporating', 'condensing', 'scattering',
    'gathering', 'collecting', 'stacked', 'layered', 'nested', 'mirrored',
    'reflecting', 'casting', 'radiating', 'extending', 'reaching', 'linking',
    'feeding', 'conducting', 'channeling', 'channelling', 'routing', 'leading',
    'rising', 'falling', 'climbing', 'descending', 'circling', 'orbiting',
    'cracking', 'shattering', 'splintering', 'collapsing', 'rebuilding',
    'weaving', 'braiding', 'wrapping', 'unwrapping', 'releasing', 'trapping',
    'freeing', 'blocking', 'guarding', 'protecting', 'sheltering', 'covering',
    'revealing', 'hiding', 'unfolding', 'folding', 'swapping', 'exchanging',
    'counting', 'measuring', 'sorting', 'dividing', 'sharing', 'splitting',
    'emerging', 'appearing', 'vanishing', 'fading', 'growing', 'shrinking',
    'standing', 'sits', 'sitting', 'lies', 'lying', 'resting', 'leaning',
}


def apa_brief_literal(brief):
    """QC mode LITERAL (v1): wajib TOKOH + AKSI + LATAR konkret."""
    if not brief or len(brief.split()) < 12:
        return True, ["brief terlalu pendek / kosong"]
    kata = set(re.findall(r"[a-z0-9]+", brief.lower()))
    alasan = []
    if not (kata & KATA_ORANG):
        alasan.append("tidak ada TOKOH (siapa yang terlihat)")
    if not (kata & KATA_AKSI):
        alasan.append("tidak ada AKSI (sedang melakukan apa)")
    if not (kata & KATA_LATAR):
        alasan.append("tidak ada LATAR/OBJEK konkret")
    abstrak = kata & KATA_ABSTRAK_TERLARANG
    if abstrak:
        alasan.append("mengandung kata abstrak/gaya terlarang: " + ", ".join(sorted(abstrak)))
    return (len(alasan) > 0), alasan


def apa_brief_konseptual(brief):
    """QC mode KONSEPTUAL (v2): wajib METAFORA BENDA + HUBUNGAN, TANPA adegan literal.

    Bukan cek "ada orang". Justru sebaliknya: kalau brief memuat ORANG + AKSI
    sehari-hari ("a warung owner holds up a phone"), itu ADEGAN LITERAL =
    ditolak, karena itu akar tampilan stok.
    """
    if not brief or len(brief.split()) < 12:
        return True, ["brief terlalu pendek / kosong"]
    kata = set(re.findall(r"[a-z0-9]+", brief.lower()))
    alasan = []
    if not (kata & KATA_BENDA_METAFORA):
        alasan.append("tidak ada BENDA metafora (objek nyata yang menyusun gagasan)")
    if not (kata & KATA_HUBUNGAN_KONSEP):
        alasan.append("tidak ada HUBUNGAN/GAGASAN (benda disusun jadi makna)")
    # Unsur terlarang budaya (babi/alkohol/simbol asing) — TEGURAN BOS 18 Okt 2026
    kena, alasan_budaya = apa_brief_terlarang_budaya(brief)
    if kena:
        alasan.extend(alasan_budaya)
    # Adegan literal: orang + kata kerja keseharian
    if (kata & KATA_ORANG) and (kata & KATA_AKSI):
        alasan.append("ini ADEGAN LITERAL (orang + aktivitas sehari-hari), "
                      "bukan metafora — ubah jadi susunan benda yang menyimbolkan ide")
    abstrak = kata & KATA_ABSTRAK_TERLARANG
    if abstrak:
        alasan.append("mengandung kata abstrak/gaya terlarang: " + ", ".join(sorted(abstrak)))
    return (len(alasan) > 0), alasan


def apa_brief_generik(brief, mode=MODE_BRIEF):
    """True = brief CACAT (harus ditulis ulang). Dispatch sesuai mode."""
    if mode == "literal":
        return apa_brief_literal(brief)
    return apa_brief_konseptual(brief)


# ══════════════════════════════════════════════════════════════════════════
#  QC DUA BAHASA — 19 Okt 2026
#
#  🚨 CACAT YANG DITUTUP: dua daftar kata di atas SELURUHNYA Bahasa Inggris.
#     TERUKUR: brief metafora bagus dalam Bahasa Indonesia ("Satu awan hujan
#     menggantung di atas deretan ember kosong, air mengalir ke dalam ember,
#     satu ember meluap") DITOLAK, padahal terjemahan Inggrisnya LOLOS.
#     Karena mesin tulis buku kita menulis Bahasa Indonesia, hampir SEMUA
#     brief ditolak ⇒ buku terbit tanpa ilustrasi.
#
#  KENAPA PAKAI AKAR KATA (bukan daftar kata utuh):
#     Bahasa Indonesia berimbuhan: "mengalir", "dialirkan", "aliran",
#     "mengalirkan". Daftar kata utuh akan bolong terus — itu tambalan yang
#     sudah terbukti gagal 18 Okt. ⇒ cocokkan pada AKAR kata.
#
#  PAGAR ANTI-SALAH-TOLAK: kalau bahasa tidak terdeteksi sebagai Bahasa
#  Indonesia, QC memakai daftar Inggris (perilaku lama, tidak berubah).
# ══════════════════════════════════════════════════════════════════════════

#  Penanda bahasa Indonesia yang sangat khas (bukan kata Inggris).
_PENANDA_ID = {
    'yang', 'dan', 'dari', 'untuk', 'dengan', 'pada', 'dalam', 'adalah',
    'sebuah', 'satu', 'dua', 'tiga', 'di', 'ke', 'ini', 'itu', 'atau',
    'ke', 'tidak', 'bukan', 'seperti', 'sambil', 'lalu', 'kemudian', 'jadi',
    'terlihat', 'tampak', 'sebagai', 'menjadi', 'atas', 'bawah', 'antara',
}

#  Akar kata BENDA yang boleh jadi metafora (benda nyata yang menyusun gagasan).
AKAR_BENDA_ID = (
    'awan', 'hujan', 'ember', 'corong', 'pipa', 'wadah', 'bak', 'tempayan',
    'gentong', 'kendi', 'botol', 'gelas', 'cangkir', 'mangkuk', 'panci',
    'ceret', 'ketel', 'timbangan', 'neraca', 'jungkat', 'kunci', 'gembok',
    'pintu', 'gerbang', 'jendela', 'cermin', 'peta', 'kompas', 'jam',
    'lonceng', 'lentera', 'lampu', 'lilin', 'api', 'asap', 'biji', 'benih',
    'tanaman', 'pohon', 'akar', 'cabang', 'daun', 'tanah', 'air', 'sungai',
    'laut', 'danau', 'sumur', 'mata air', 'pompa', 'kran', 'selang',
    'saringan', 'ayakan', 'jala', 'jaring', 'keranjang', 'kerat', 'peti',
    'kotak', 'lemari', 'tas', 'karung', 'tali', 'simpul', 'rantai', 'jangkar',
    'roda', 'gir', 'mesin', 'palu', 'landasan', 'kail', 'sabit', 'cangkul',
    'bajak', 'pisau', 'gunting', 'lem', 'kertas', 'buku', 'surat', 'amplop',
    'perangko', 'kartu', 'koin', 'uang', 'dompet', 'ponsel', 'telepon',
    'tangga', 'gunung', 'bukit', 'tebing', 'gua', 'jembatan', 'pelita',
    'payung', 'perisai', 'tameng', 'pedang', 'kaca', 'pembesar', 'teleskop',
    'mikroskop', 'magnet', 'bayangan', 'sarang', 'telur', 'cangkang',
    'gunting', 'jarum', 'benang', 'kain', 'anyaman', 'tumpukan', 'susunan',
    'lapisan', 'jejak', 'tapak', 'cetakan', 'cetak', 'cap', 'stempel',
    #  Tambahan untuk buku bertema alam/sosial (kalibrasi 19 Okt)
    'langit', 'bumi', 'angin', 'udara', 'uap', 'tetes', 'genangan',
    'kekeringan', 'panas', 'dingin', 'musim', 'sawah', 'ladang', 'kebun',
    'pasar', 'warung', 'toko', 'gudang', 'jalan', 'lorong', 'tangki',
    'saluran', 'bendungan', 'kincir', 'layar', 'perahu', 'angsa',
)

#  Akar kata HUBUNGAN (benda disusun jadi makna).
AKAR_HUBUNG_ID = (
    'alir', 'tumpah', 'luap', 'isi', 'kosong', 'turun', 'naik', 'jatuh',
    'angkat', 'angkat', 'susun', 'tata', 'atur', 'gabung', 'pisah', 'belah',
    'sambung', 'hubung', 'saring', 'tap', 'serap', 'kering', 'basah',
    'tumbuh', 'layu', 'mekar', 'bunga', 'buah', 'panen', 'tanam', 'tuai',
    'timbang', 'ukur', 'hitung', 'banding', 'seimbang', 'miring', 'berat',
    'ringan', 'tahan', 'tolak', 'tarik', 'dorong', 'angkat', 'jatuh',
    'buka', 'tutup', 'kunci', 'lepas', 'ikat', 'jerat', 'lilit', 'pilin',
    'anyam', 'tenun', 'jahit', 'tempel', 'rekat', 'pantul', 'serap',
    'cair', 'beku', 'uap', 'menguap', 'mengembun', 'hujam', 'siram',
    'genang', 'kucur', 'pancar', 'sebar', 'kumpul', 'ambil', 'beri',
    'terang', 'gelap', 'silau', 'redup', 'tunjuk', 'arah', 'putar',
    'balik', 'ulang', 'lanjut', 'henti', 'gerak', 'diam', 'tunggu',
    'bantu', 'hambat', 'lindung', 'jaga', 'rawat', 'simpan', 'buang',
)


def bahasa_brief(brief):
    """Tebak bahasa brief: 'id' kalau banyak penanda Indonesia, selain itu 'en'.

    🚨 JEBAKAN 19 Okt (TERUKUR): ambang ">=2 penanda" SALAH. Brief Indonesia
    yang pendek dan teknis ("Air dialirkan lewat pipa menuju wadah, aliran itu
    mengisi ember sampai meluap") hanya punya SATU penanda ('itu') ⇒ ditebak
    Inggris ⇒ ditolak QC Inggris. Ini justru persis kasus yang mau ditutup.

    ⇒ Dua jalur deteksi, salah satu cukup:
       (a) >=2 penanda kata umum Indonesia, ATAU
       (b) ada kata berimbuhan Indonesia (me-, di-, -kan, -nya, ber-, ter-)
           yang TIDAK ADA di bahasa Inggris.
    """
    teks = (brief or '').lower()
    kata = set(re.findall(r"[a-z]+", teks))
    if len(kata & _PENANDA_ID) >= 2:
        return 'id'
    if kata & _PENANDA_ID and re.search(
            r'\b(me[a-z]{3,}|di[a-z]{3,}|ber[a-z]{3,}|ter[a-z]{3,}|'
            r'[a-z]{4,}kan|[a-z]{4,}nya)\b', teks):
        return 'id'
    #  Jalur (b) saja: kata berimbuhan Indonesia tanpa penanda umum.
    if re.search(r'\b(me[a-z]{4,}|di[a-z]{4,}|ber[a-z]{4,})\b', teks) and \
            re.search(r'\b[a-z]{4,}(kan|nya)\b', teks):
        return 'id'
    return 'en'


def _cocok_akar(kata, akar):
    """True kalau kata memuat akar (imbuhan Indonesia: meng-alir-kan)."""
    return any(a in kata for a in akar)


def apa_brief_konseptual_id(brief):
    """QC mode KONSEPTUAL untuk brief Bahasa Indonesia (padanan versi Inggris)."""
    if not brief or len(brief.split()) < 12:
        return True, ["brief terlalu pendek / kosong"]
    kata = re.findall(r"[a-z]+", brief.lower())
    alasan = []
    if not any(_cocok_akar(k, AKAR_BENDA_ID) for k in kata):
        alasan.append("tidak ada BENDA metafora (objek nyata yang menyusun gagasan)")
    if not any(_cocok_akar(k, AKAR_HUBUNG_ID) for k in kata):
        alasan.append("tidak ada HUBUNGAN/GAGASAN (benda disusun jadi makna)")
    #  Unsur terlarang budaya tetap berlaku (teguran Bos 18 Okt 2026)
    kena, alasan_budaya = apa_brief_terlarang_budaya(brief)
    if kena:
        alasan.extend(alasan_budaya)
    abstrak = set(kata) & KATA_ABSTRAK_TERLARANG
    if abstrak:
        alasan.append("mengandung kata abstrak/gaya terlarang: "
                      + ", ".join(sorted(abstrak)))
    return (len(alasan) > 0), alasan


def apa_brief_generik_dua_bahasa(brief, mode=MODE_BRIEF):
    """QC yang MENGERTI Bahasa Indonesia. Dipakai pemanggil baru (19 Okt 2026)."""
    if mode == "literal":
        return apa_brief_literal(brief)
    if bahasa_brief(brief) == 'id':
        return apa_brief_konseptual_id(brief)
    return apa_brief_konseptual(brief)


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 1 — brief dari ISI bab
# ══════════════════════════════════════════════════════════════════════════
def _bersihkan_brief(teks):
    """Buang pembuka/penutup basa-basi LLM, sisakan deskripsi visual saja."""
    if not teks:
        return ""
    t = teks.strip()
    # buang pagar kode kalau LLM membungkusnya
    t = re.sub(r'^```[a-zA-Z]*\s*|\s*```$', '', t).strip()
    # buang label yang sering muncul
    t = re.sub(r'^(brief visual|brief|visual brief|scene|deskripsi)\s*:\s*', '', t,
               flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip().strip('"').strip()
    return t


# ══════════════════════════════════════════════════════════════════════════
# QC LAPIS 2 — "KHAS atau TIDAK" (temuan uji 18 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  Kenapa perlu: bab 2 "Model Bisnis Digital & Strategi Persaingan" dapat
#  adegan KURIR OJOL — nyambung ke "ekonomi digital", tapi kalau gambar itu
#  dipasang di bab 1 atau bab 3 juga tidak ada yang sadar. Ciri khas bab 2
#  (Airbnb kasur udara, Netflix vs Blockbuster, network effect) tidak muncul.
#  QC lapis 1 (tokoh+aksi+latar) LOLOS karena strukturnya memang lengkap.
#  ⇒ lapis 2 menilai: "khas bab ini, atau bisa dipakai bab mana saja?"
PROMPT_KHAS = """Kamu pemeriksa kualitas ilustrasi buku. Diberi RINGKASAN BAB dan
satu BRIEF ILUSTRASI. Tugasmu menilai: apakah adegan dalam brief itu KHAS untuk
bab ini, atau bisa dipasang di bab lain mana pun dalam buku yang sama tanpa
ada yang sadar salah pasang?

RINGKASAN BAB:
{ringkasan_bab}

BRIEF ILUSTRASI:
{brief}

Jawab HANYA dengan format dua baris ini, tanpa penjelasan tambahan:
KHAS: YA atau TIDAK
SEBAB: satu kalimat pendek (kalau TIDAK: sebut momen/istilah khas bab yang
seharusnya dijadikan adegan)"""


def _baca_vonis_khas(teks):
    """Baca jawaban LLM: return (khas:bool, sebab:str). Ragu = TIDAK (aman)."""
    if not teks:
        return False, "pemeriksa tidak menjawab"
    t = teks.upper()
    m = re.search(r'KHAS\s*[:=]\s*(YA|TIDAK|YES|NO)', t)
    if not m:
        return False, "jawaban tidak berbentuk (dianggap TIDAK)"
    khas = m.group(1) in ("YA", "YES")
    s = re.search(r'SEBAB\s*[:=]\s*(.+)', teks, re.I)
    sebab = s.group(1).strip().split("\n")[0] if s else ""
    return khas, sebab


def apa_brief_khas(brief, ringkasan_bab, panggil_llm=None):
    """QC lapis 2: (khas:bool, sebab:str). Ragu/kosong = TIDAK (aman)."""
    if panggil_llm is None:
        from buku_umum_pipeline import call_llm as panggil_llm
    teks = panggil_llm(
        PROMPT_KHAS.format(ringkasan_bab=(ringkasan_bab or "")[:3000], brief=brief),
        max_tokens=400, timeout=90)
    return _baca_vonis_khas(teks)


def brief_visual(ringkasan_bab, sub_bab="", panggil_llm=None, max_percobaan=3,
                 wajib_khas=True, mode=None, gaya=None):
    """Tahap 1: LLM menulis brief visual dari ringkasan bab.

    mode=None ⇒ otomatis ikut GAYA (MODE_BRIEF_PER_GAYA): gaya `anak` → literal,
    gaya konseptual → konseptual. Ini mencegah buku anak diminta metafora abstrak.

    mode='konseptual' (DEFAULT, v2) → metafora visual, adegan literal DITOLAK.
    mode='literal'    (v1)          → adegan sehari-hari (buku praktis/teknis).

    Dua lapis QC sebelum brief diterima:
      LAPIS 1 apa_brief_generik() — mode konseptual: wajib BENDA+HUBUNGAN,
                                    adegan literal ditolak.
      LAPIS 2 apa_brief_khas()    — wajib KHAS bab ini (bukan adegan generik).
    Gagal → brief DITULIS ULANG (bukan ganti seed gambar).

    panggil_llm: fungsi yang SUDAH ADA di pipeline (buku_umum_pipeline.call_llm).
    Return: dict {brief, generik, alasan, percobaan, khas, sebab_khas, mode}.
    """
    if panggil_llm is None:
        from buku_umum_pipeline import call_llm as panggil_llm  # satu pintu 9router

    # Mode otomatis ikut gaya (buku anak → literal; buku dewasa → konseptual)
    if mode is None:
        mode = MODE_BRIEF_PER_GAYA.get(gaya or GAYA_DEFAULT, "konseptual")

    pola = PROMPT_BRIEF_LITERAL if mode == "literal" else PROMPT_BRIEF_KONSEPTUAL
    prompt = pola.format(
        ringkasan_bab=(ringkasan_bab or "").strip()[:4000] or "(ringkasan kosong)",
        sub_bab=(sub_bab or "").strip()[:1200] or "(tidak disebutkan)",
    )
    catatan = ""
    alasan = []
    sebab = ""
    #  ┌─ 19 Okt 2026: JANGAN BUANG ILUSTRASI ────────────────────────────────
    #  🔴 CACAT TERUKUR: buku nyata 2 bab → bab 1 DILEWATI tanpa ilustrasi
    #     karena brief ditolak QC "tidak ada HUBUNGAN/GAGASAN", sementara
    #     bab 2 berhasil. Satu bab tanpa gambar = buku terasa cacat bagi
    #     pembeli, padahal brief yang ditolak itu BIASANYA cuma kurang satu
    #     kata kunci — bukan buruk.
    #  ⇒ SIMPAN brief TERBAIK (paling sedikit alasan tolak) dan pakai kalau
    #    semua percobaan habis. Pagar: brief yang melanggar BUDAYA atau
    #    KOSONG tetap TIDAK dipakai (itu bukan soal kata kunci).
    #  └───────────────────────────────────────────────────────────────────────
    cadangan = None          # (jumlah_alasan, brief)
    for n in range(1, max_percobaan + 1):
        teks = panggil_llm(prompt + catatan, max_tokens=600, timeout=90)
        brief = _bersihkan_brief(teks)
        #  ⚠️ 19 Okt 2026: WAJIB pakai versi DUA BAHASA. Versi lama hanya
        #  mengerti Bahasa Inggris ⇒ brief Indonesia yang bagus ditolak dan
        #  buku terbit tanpa ilustrasi.
        generik, alasan = apa_brief_generik_dua_bahasa(brief, mode=mode)
        if brief and not generik:
            khas, sebab = (True, "")
            if wajib_khas and mode != "literal":
                # ⚠️ Buku ANAK (mode literal) TIDAK butuh "khas bab ini": satu
                # bab siklus hujan boleh memakai matahari+awan+hujan yang sama
                # dengan bab lain — anak belajar dari pengulangan. QC ini
                # dulu MEMAKAN brief anak yang benar (18 Okt 2026).
                khas, sebab = apa_brief_khas(brief, ringkasan_bab, panggil_llm)
            if khas:
                return {"brief": brief, "generik": False, "alasan": [],
                        "percobaan": n, "khas": True, "sebab_khas": "",
                        "mode": mode, "cadangan_dipakai": False}
            alasan = ["tidak khas bab ini: " + (sebab or "bisa dipakai bab lain")]
        #  Simpan calon terbaik (paling sedikit alasan tolak) — dipakai kalau
        #  semua percobaan habis. Pagar budaya/kosong: JANGAN disimpan.
        if brief and len(brief.split()) >= 12:
            kena_budaya, _ = apa_brief_terlarang_budaya(brief)
            if not kena_budaya:
                jumlah = len(alasan) if alasan else 99
                if cadangan is None or jumlah < cadangan[0]:
                    cadangan = (jumlah, brief)
        if n < max_percobaan:
            # QC gagal → perbaiki BRIEF-nya, bukan ganti seed gambar
            if mode == "literal":
                tuntutan = (
                    "Tulis ulang brief yang memuat TOKOH jelas, AKSI yang terlihat, "
                    "dan LATAR/OBJEK konkret (contoh: warung, meja, ponsel, rak). "
                )
            else:
                tuntutan = (
                    "Tulis ulang sebagai METAFORA: susun BENDA NYATA dengan cara tak "
                    "biasa sehingga ide bab langsung terbaca (contoh: timbangan dengan "
                    "ponsel di satu sisi dan tumpukan koin di sisi lain, seimbang). "
                    "DILARANG orang sedang beraktivitas sehari-hari. Satu ide saja, "
                    "satu fokus, negative space lega. "
                )
            catatan = (
                "\n\nBRIEF SEBELUMNYA DITOLAK karena: " + "; ".join(alasan) +
                ". " + tuntutan +
                "WAJIB ambil momen/istilah KHAS bab ini (tokoh, kasus, atau contoh "
                "yang hanya ada di bab ini) supaya tidak bisa dipakai bab lain. "
                "Tanpa kata abstrak, tanpa 3D/glow/gradient."
            )
    #  Semua percobaan habis. Kalau ada calon yang tidak melanggar budaya,
    #  PAKAI itu — lebih baik gambar agak kurang sempurna daripada halaman
    #  kosong di buku yang dijual. `generik` tetap True supaya jujur bahwa
    #  brief ini tidak lolos QC; `cadangan_dipakai` = penanda untuk laporan.
    if cadangan:
        return {"brief": cadangan[1], "generik": True, "alasan": alasan,
                "percobaan": max_percobaan, "khas": False, "sebab_khas": sebab,
                "mode": mode, "cadangan_dipakai": True}
    return {"brief": "", "generik": True, "alasan": alasan, "percobaan": max_percobaan,
            "khas": False, "sebab_khas": sebab, "mode": mode,
            "cadangan_dipakai": False}


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 2 — prompt gambar = style block + brief
# ══════════════════════════════════════════════════════════════════════════
def prompt_gambar(brief, gaya=None, jenis=None):
    """Rakit prompt final: gaya buku + brief + LARANGAN BUDAYA + larangan teks.

    jenis: 'umum' | 'anak' | 'pendidikan' — SATU PAKET (Bos 18 Okt 2026).
    Kalau jenis diisi, `gaya` DIABAIKAN: jenis menentukan gaya & style block.
    """
    if not brief:
        raise ValueError("brief kosong — tahap 1 belum berhasil, jangan generate gambar")
    kena, alasan = apa_brief_terlarang_budaya(brief)
    if kena:
        raise ValueError("brief memuat unsur terlarang budaya: " + "; ".join(alasan))
    if jenis is not None:
        import jenis_buku as JB
        pkg = JB.paket(jenis)
        gaya = pkg["gaya_gambar"]
        blok = pkg["ilustrasi"] or STYLE_BUKU.get(gaya) or STYLE_BUKU[GAYA_DEFAULT]
    else:
        gaya = gaya or GAYA_DEFAULT
        blok = STYLE_BUKU.get(gaya) or STYLE_BUKU[GAYA_DEFAULT]
    brief = _bersihkan_brief(brief).rstrip('.')
    # Style block milik paket jenis SUDAH memuat "no text..." — jangan dobel
    ekor = "" if "no text" in blok.lower() else EKOR_LARANGAN
    return f"{blok.format(brief=brief)}. {LARANGAN_BUDAYA_PROMPT}{ekor}"


# ══════════════════════════════════════════════════════════════════════════
# JALUR LENGKAP (Tahap 1 → QC → Tahap 2 → gambar InferHub)
# ══════════════════════════════════════════════════════════════════════════
def buat_ilustrasi(ringkasan_bab, sub_bab="", gaya=None, panggil_llm=None,
                   simpan=None, ukuran="1024x1024", jenis=None):
    """Brief dari isi bab → QC → prompt → gambar. Return dict hasil lengkap."""
    pkg = None
    if jenis is not None:
        import jenis_buku as JB
        pkg = JB.paket(jenis)
        gaya = pkg["gaya_gambar"]
    b = brief_visual(ringkasan_bab, sub_bab=sub_bab, panggil_llm=panggil_llm,
                     gaya=gaya, mode=(pkg["mode_brief"] if pkg else None))
    hasil = {"brief": b, "gaya": gaya, "jenis": jenis, "prompt": "", "path": None, "galat": None}
    if not b["brief"]:
        hasil["galat"] = "brief ditolak QC: " + "; ".join(b["alasan"])
        return hasil
    hasil["prompt"] = prompt_gambar(b["brief"], gaya, jenis=jenis)

    #  Gambar: PAKAI MESIN YANG SUDAH ADA — `_gambar_inferhub` di
    #  buku_umum_pipeline. JANGAN bikin pemanggil InferHub kedua.
    #
    #  🚨 CACAT TERUKUR 20 Okt 2026: versi lama mengimpor DUA nama yang
    #  TIDAK ADA di buku_umum_pipeline.py — `_gambar_inferhub` dan
    #  `gambar_dari_prompt`. Keduanya ImportError ⇒ setiap panggilan
    #  buat_ilustrasi MATI dengan "cannot import name 'gambar_dari_prompt'".
    #  Akibatnya ilustrasi TIDAK PERNAH dibuat lewat jalur ini.
    #
    #  Obat: `generate_ilustrasi_api` sudah berisi kode InferHub yang
    #  teruji (model cb/gemini-2.5-flash-image, b64 inline, seed per varian).
    #  Ambil INTI-nya jadi `_gambar_inferhub(prompt, simpan, ukuran, seed)`
    #  di buku_umum_pipeline, lalu panggil dari sini — satu mesin, dua pintu.
    from buku_umum_pipeline import _gambar_inferhub
    hasil["path"] = _gambar_inferhub(hasil["prompt"], simpan, ukuran)
    if not hasil["path"]:
        hasil["galat"] = "gambar gagal: InferHub tidak mengembalikan berkas"
    return hasil


def prompt_dari_bab(bab_num, ringkasan_bab, sub_bab="", gaya=GAYA_DEFAULT,
                    panggil_llm=None, mode=None):
    """Pintu yang dipakai pipeline: hasilkan prompt TANPA memanggil API gambar.
    (pipeline yang menyimpan PNG-nya). Return dict brief+prompt."""
    b = brief_visual(ringkasan_bab, sub_bab=sub_bab, panggil_llm=panggil_llm,
                     mode=mode, gaya=gaya)
    if not b["brief"]:
        return {"bab": bab_num, "brief": "", "prompt": "", "galat":
                "brief ditolak QC: " + "; ".join(b["alasan"]), "brief_meta": b}
    return {"bab": bab_num, "brief": b["brief"],
            "prompt": prompt_gambar(b["brief"], gaya), "galat": None,
            "brief_meta": b}


# ══════════════════════════════════════════════════════════════════════════
# LANGKAH 3 — KURASI 3-PILIH-1 (ide Bos 18 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  Buku premium terlihat premium karena ada ART DIRECTION: manusia (atau LLM
#  penilai) memilih dari beberapa varian, bukan menerima yang pertama jadi.
#  Biaya naik 3× gambar (~Rp 21/gambar di InferHub) — sangat murah.
#  ⚠️ Var1 = brief & prompt yang SAMA, hanya seed/varian berbeda: gaya tetap
#  satu (identitas visual buku), yang dipilih adalah KOMPOSISI TERBAIK.
PROMPT_KURASI = """Kamu art director buku non-fiksi premium. Nilai 3 varian ilustrasi
untuk bab berikut. Pilih SATU yang paling layak cetak.

KRITERIA (urut kepentingan):
1. Metafora/gagasan langsung terbaca tanpa caption.
2. Satu fokus utama, negative space lega, tidak penuh sesak.
3. Bersih: TIDAK ada huruf/teks/angka nyasar, tidak ada objek cacat/ganda.
4. Rapi dan elegan, layak buku premium (bukan poster iklan).

BRIEF YANG DIMINTA:
{brief}

VARIAN:
{daftar}

Jawab HANYA dua baris:
PILIH: 1, 2, atau 3
SEBAB: satu kalimat pendek"""


def pilih_varian(brief, jumlah=3, panggil_llm=None, deskripsi=None):
    """Pilih 1 dari `jumlah` varian. Tanpa penglihatan gambar: pakai deskripsi.

    deskripsi: list[str] hasil pemeriksaan mata/vision per varian. Kalau None,
    fungsi ini menolak memilih (lebih baik gagal jelas daripada memilih buta).
    Return: (indeks_terpilih 1-based, sebab).
    """
    if not deskripsi or len(deskripsi) < jumlah:
        return None, ("kurasi butuh deskripsi tiap varian (hasil periksa mata); "
                      "tidak memilih secara buta")
    if panggil_llm is None:
        from buku_umum_pipeline import call_llm as panggil_llm
    daftar = "\n".join(f"{i}. {d}" for i, d in enumerate(deskripsi[:jumlah], 1))
    teks = panggil_llm(PROMPT_KURASI.format(brief=brief, daftar=daftar),
                       max_tokens=400, timeout=90)
    if not teks:
        return None, "penilai tidak menjawab"
    m = re.search(r'PILIH\s*[:=]\s*([1-9])', teks.upper())
    s = re.search(r'SEBAB\s*[:=]\s*(.+)', teks, re.I)
    if not m:
        return None, "jawaban tidak berbentuk"
    idx = int(m.group(1))
    if idx < 1 or idx > jumlah:
        return None, f"pilihan di luar rentang: {idx}"
    return idx, (s.group(1).strip().split("\n")[0] if s else "")


if __name__ == "__main__":
    # DEMO: pakai ringkasan NYATA dari checkpoint, panggil LLM sungguhan
    import os, sys, time
    ck = "/opt/data/buku_umum_e2e_test2/checkpoint.json"
    ring = {}
    if os.path.exists(ck):
        data = json.load(open(ck))
        for k, v in data.get("babs", {}).items():
            ring[int(k)] = v.get("summary", "")
    if not ring:
        print("checkpoint tidak ada — demo butuh ringkasan bab nyata")
        sys.exit(1)
    for bab in sorted(ring)[:int(sys.argv[1]) if len(sys.argv) > 1 else 1]:
        t0 = time.time()
        h = prompt_dari_bab(bab, ring[bab])
        print(f"\n=== BAB {bab} ({round(time.time()-t0,1)} s) ===")
        print("BRIEF :", h["brief"] or "(GAGAL)")
        print("QC    :", "LOLOS" if h["brief"] else h["galat"])
        print("PROMPT:", h["prompt"][:400], "...")
        if h["prompt"]:
            out = f"/opt/data/_demo_brief_bab{bab}.json"
            json.dump(h, open(out, "w"), indent=2, ensure_ascii=False)
            print("SIMPAN:", out)
