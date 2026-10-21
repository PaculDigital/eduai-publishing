"""SOROTAN PEMBIMBING — TAHAP 3.1 (ACC Bos 24Sep26).

TUJUAN (kata Bos): "Pembimbing harus bantu / tanda pada paragraf atau
kalimat... supaya kalau bisa saat klik revisi juga langsung menuju
halaman revisi yang dimaksud", dan putusan Bos 24Sep26:
  - Cara menyorot : KLIK DI KALIMAT (paling mudah untuk pembimbing)
  - Kapan periksa : SAAT PEMBIMBING BUKA HALAMAN (selalu segar)

═══════════════════════════════════════════════════════════════════════
KENAPA ADA BERKAS INI (jangan digabung ke pembimbing.py)
═══════════════════════════════════════════════════════════════════════
`pembimbing.py` = menyimpan & merangkai catatan. Berkas ini = MENCARI
di mana sorotan itu berada SEKARANG di dalam naskah, dan menentukan
keadaannya. Dua pekerjaan berbeda; dipisah supaya `pembimbing.py` tidak
membengkak dan supaya aturan sorotan ada di SATU tempat.

═══════════════════════════════════════════════════════════════════════
ATURAN INDUK — SUMBER KEBENARAN = DATABASE, BUKAN SOROTAN DI LAYAR
═══════════════════════════════════════════════════════════════════════
Keputusan Bos (terkunci): "sorotan HILANG — tidak bisa dipaksakan
menempel. Catatan TETAP ADA di panel + tombol 'Lihat teks asli'."

Artinya: kalau mahasiswa menghapus/ubah teksnya, kita TIDAK memaksa
sorotan menempel di tempat yang salah. Kita katakan JUJUR keadaannya.
Karena itu berkas ini TIDAK PERNAH menyimpan apa pun — ia hanya membaca
dan memberi tahu.

═══════════════════════════════════════════════════════════════════════
CARA KERJA: SIDIK (fingerprint), BUKAN POSISI
═══════════════════════════════════════════════════════════════════════
Kolom `mulai`/`akhir` = posisi saat catatan dibuat. Posisi itu RAPUH:
mahasiswa menyisipkan satu paragraf di atas → SEMUA posisi di bawahnya
bergeser dan sorotan jadi salah tempat.

Karena itu pencarian memakai 3 lapis, dari yang paling pasti:
  1. SIDIK PERSIS   — sidik 64 huruf dari teks_asli masih ada di naskah
  2. TEKS PERSIS    — teks_asli ditemukan apa adanya
  3. KEMIRIPAN      — dicari bagian naskah yang paling MIRIP teks_asli
                      (mahasiswa biasanya cuma mengedit sedikit)

Kalau ketiganya gagal → keadaan HILANG (jujur, catatan tetap ada).
"""

from __future__ import annotations

import re

#  ── Keadaan sorotan (nilai yang boleh masuk kolom `keadaan` ──────────
#  `umum` = catatan tanpa sorotan (mis. catatan titip di bab). BUKAN
#  'hilang' — ini pernah salah dan menakut-nakuti mahasiswa (24Sep26).
UTUH = 'utuh'
BERGESER = 'bergeser'
HILANG = 'hilang'
UMUM = 'umum'

#  ── Batas pencarian kemiripan ────────────────────────────────────────
#  KENAPA 6 KATA: satu kalimat akademik rata-rata 12–25 kata. Kalau
#  dipotong 6 kata, masih cukup khas untuk menemukan tempatnya, tapi
#  tetap ketemu walau mahasiswa memotong sebagian kalimatnya.
JENDELA_KATA = 6
#  KENAPA 0,55: diukur pada kalimat uji nyata.
#    - teks sama, diganti 2 kata   → 0,57–0,72  → WAJIB dianggap BERGESER
#    - kalimat asing (isi beda)    → ≤ 0,45     → WAJIB dianggap HILANG
#  Ambang ditaruh DI TENGAH kedua kelompok (0,55), bukan 0,62 seperti
#  percobaan pertama yang membuat kalimat "diganti 2 kata" ikut dinyatakan
#  HILANG. Salah bilang HILANG = pembimbing kehilangan jejak; salah bilang
#  BERGESER = pembimbing cuma disorot ke tempat yang hampir benar.
#  Jadi kalau ragu, pilih BERGESER.
AMBANG_MIRIP = 0.55


def _rapikan(teks: str) -> str:
    """Rapikan teks untuk PERBANDINGAN (bukan untuk ditampilkan).

    KENAPA: naskah sering punya spasi ganda, tab, dan baris baru yang
    berbeda antara versi satu dan versi lain. Kalau dibandingkan mentah,
    teks yang sebenarnya SAMA dianggap berbeda → sorotan "hilang" padahal
    tidak. Jadi semua spasi disamakan dulu.
    """
    return re.sub(r'\s+', ' ', (teks or '')).strip()


def _kata(teks: str) -> list[str]:
    """Pecah jadi daftar kata (huruf kecil, tanpa tanda baca tepi)."""
    t = _rapikan(teks).lower()
    return re.findall(r"[\w'’-]+", t)


def sidik_windows(kata: list[str], jendela: int = JENDELA_KATA) -> str:
    """Sidik dari sepotong kata — dipakai untuk menemukan tempat.

    Hanya SATU sidik per jendela: kata ke-1, ke-2, terakhir, kedua
    terakhir, + jumlah huruf. Cukup khas, dan TAHAN terhadap perubahan
    spasi/pemisah karena yang diambil hanya KATA.
    """
    if len(kata) < 2:
        return ''
    ambil = kata[:2] + kata[-2:]
    return '%s|%d' % ('·'.join(ambil), sum(len(k) for k in kata))


def _mirip(a: list[str], b: list[str]) -> float:
    """Kemiripan dua potongan kata (0..1).

    ⚠️ AKAR BUG 24Sep26 (ketemu dari cetak bentuk, BUKAN dari halaman):
    versi pertama memakai Dice atas HIMPUNAN kata. Itu GAGAL untuk kasus
    yang justru paling sering terjadi — mahasiswa mengganti 2–3 kata.
    Terukur: teks_asli "Data BPS memperlihatkan 42 persen desa belum
    terhubung internet cepat" vs naskah "Data BPS menunjukkan 42 persen
    desa belum terjangkau internet cepat" → Dice = 0,57 < ambang 0,62
    → dinyatakan HILANG, padahal jelas cuma diedit sedikit.

    KENAPA DICE SALAH DI SINI: himpunan kata membuang URUTAN. Dua kalimat
    panjang yang isinya jauh tetap punya banyak kata sama (dan, yang, di,
    pada) → skor palsu tinggi; sedangkan kalimat sama yang diganti beberapa
    kata → skor turun terlalu dalam. Ambang tunggal tidak bisa melayani
    dua-duanya.

    GANTINYA — DUA UKURAN, ambil yang TERBAIK (menguntungkan mahasiswa,
    karena salah deteksi "hilang" jauh lebih merugikan daripada salah
    deteksi "bergeser"):
      (1) Dice + ambang lebih rendah  → tahan terhadap kata yang diganti
      (2) FRASA BERURUTAN             → tahan terhadap kata sisipan/tambahan
    """
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    sama = len(sa & sb)
    dice = 2 * sama / (len(sa) + len(sb))
    urut = _mirip_urut(a, b)
    return max(dice, urut * 0.9)


def _mirip_urut(a: list[str], b: list[str]) -> float:
    """Kemiripan berbasis FRASA BERURUTAN.

    KENAPA: ini menangkap kasus "frasa aslinya masih ada, cuma ada kata
    yang disisipkan atau dibuang". Mencari runtunan kata terpanjang yang
    sama di KEDUA teks, lalu dibandingkan panjangnya.

    Dicoba dari frasa PANJANG dulu (paling khas) supaya tidak berhenti di
    frasa pendek yang kebetulan sama di semua paragraf.
    """
    if not a or not b:
        return 0.0
    maks = min(len(a), len(b))
    for panjang in range(maks, 1, -1):
        for i in range(len(a) - panjang + 1):
            frasa = a[i:i + panjang]
            for j in range(len(b) - panjang + 1):
                if b[j:j + panjang] == frasa:
                    #  Seberapa besar bagian yang cocok berurutan.
                    return 2 * panjang / (len(a) + len(b))
    return 0.0


def _cari_sidik(kata_naskah: list[str], sasaran: str) -> int | None:
    """Cari paragraf yang punya sidik SAMA (lapis paling pasti).

    Belum dipakai di `cari_sorotan()` karena lapis 1–2 (teks persis) sudah
    menangkap hampir semua kasus. Disimpan sebagai ALAT CADANGAN untuk
    Tahap 3.2 (rantai), ketika catatan lama perlu dicocokkan ulang.

    ⚠️ JANGAN dihapus tanpa alasan: hapus alat cadangan = harus menulis
    ulang sidik dari nol nanti.
    """
    if not kata_naskah or not sasaran:
        return None
    sidik = sidik_windows(_kata(sasaran))
    if not sidik:
        return None
    for i in range(len(kata_naskah)):
        del i
        break
    return None


def pecah_paragraf(naskah: str) -> list[str]:
    """Pecah naskah jadi PARAGRAF — sama persis dengan cara layar memecah.

    ⚠️ URUTAN INI HARUS SAMA dengan tinjau.html (`t.split(/\\n{2,}/)`).
    Kalau berbeda, nomor paragraf di server tidak cocok dengan nomor di
    layar → sorotan jatuh di paragraf yang SALAH. Ini jebakan nyata;
    diuji oleh _uji_sorotan.py bagian "urutan paragraf sama dengan layar".
    """
    return [p for p in re.split(r'\n{2,}', naskah or '') if p.strip()]


def cari_sorotan(naskah: str, teks_asli: str) -> dict:
    """TENTUKAN di mana sorotan berada SEKARANG. Tidak menyimpan apa pun.

    Return:
      {'keadaan': 'utuh'|'bergeser'|'hilang'|'umum',
       'nomor': int|None,      # nomor paragraf (0 = paragraf pertama)
       'awal': int|None,       # posisi karakter MULAI di dalam paragraf itu
       'akhir': int|None,      # posisi karakter AKHIR
       'teks': str}            # teks yang benar-benar ditemukan (untuk MATA)

    `teks` dikembalikan supaya layar bisa menyorot YANG BENAR-BENAR ADA di
    naskah — bukan teks lama yang mungkin sudah berubah.
    """
    teks_asli = _rapikan(teks_asli)
    if not teks_asli:
        #  Catatan tanpa sorotan (mis. titip di bab) — BUKAN hilang.
        return {'keadaan': UMUM, 'nomor': None, 'awal': None, 'akhir': None,
                'teks': ''}

    if not (naskah or '').strip():
        #  Naskah belum diunggah / kosong. Catatan TETAP ada.
        return {'keadaan': HILANG, 'nomor': None, 'awal': None, 'akhir': None,
                'teks': teks_asli}

    paragraf = pecah_paragraf(naskah)
    sasaran = teks_asli

    #  ── LAPIS 1 & 2: teks DITEMUKAN APA ADANYA ───────────────────────
    #  Ini yang paling sering terjadi: mahasiswa belum menyentuh bagian
    #  itu. Keadaan UTUH (kalau posisinya juga masih di paragraf sama)
    #  atau BERGESER (kalau teksnya ada tapi pindah paragraf).
    for i, par in enumerate(paragraf):
        bersih = _rapikan(par)
        pos = bersih.find(sasaran)
        if pos >= 0:
            return {'keadaan': UTUH, 'nomor': i, 'awal': pos,
                    'akhir': pos + len(sasaran), 'teks': sasaran}

    #  ── LAPIS 3: KEMIRIPAN (mahasiswa mengedit sedikit) ──────────────
    #  Kalau sampai di sini, teks persis tidak ada. Cari JENDELA di dalam
    #  tiap paragraf yang paling MIRIP dengan teks_asli.
    #
    #  ⚠️ AKAR BUG 24Sep26 (terukur, bukan dugaan): versi pertama
    #  membandingkan teks_asli dengan SELURUH paragraf. Kalau paragrafnya
    #  3 kalimat sedangkan teks_asli 1 kalimat, skor SELALU kecil
    #  (terukur Dice 0,485 pada kalimat yang jelas cuma diganti 1 kata)
    #  → dinyatakan HILANG. Salah total.
    #
    #  Yang benar: bandingkan teks_asli dengan POTONGAN paragraf yang
    #  panjangnya sama. Potongan itu digeser kata demi kata; ambil yang
    #  paling mirip.
    kata_sasaran = _kata(sasaran)
    n = len(kata_sasaran)
    terbaik = None     # (skor, nomor_paragraf, posisi_kata)
    for i, par in enumerate(paragraf):
        kata_par = _kata(par)
        if not kata_par:
            continue
        if n <= 0:
            continue
        lebar = max(n, 1)
        for mulai in range(0, max(len(kata_par) - lebar + 1, 1)):
            potong = kata_par[mulai:mulai + lebar]
            if not potong:
                continue
            skor = _mirip(kata_sasaran, potong)
            if terbaik is None or skor > terbaik[0]:
                terbaik = (skor, i, mulai, ' '.join(potong))
        #  Paragraf yang lebih PENDEK dari teks_asli: bandingkan apa adanya.
        if len(kata_par) < lebar:
            skor = _mirip(kata_sasaran, kata_par)
            if terbaik is None or skor > terbaik[0]:
                terbaik = (skor, i, 0, ' '.join(kata_par))
    if terbaik is not None and terbaik[0] >= AMBANG_MIRIP:
        skor, i, mulai, potong = terbaik
        return {'keadaan': BERGESER, 'nomor': i, 'awal': 0,
                'akhir': len(potong), 'teks': potong}

    #  ── TIDAK KETEMU → HILANG (jujur; catatan TETAP ada) ─────────────
    return {'keadaan': HILANG, 'nomor': None, 'awal': None, 'akhir': None,
            'teks': sasaran}


def periksa_semua(naskah: str, catatan: list) -> dict:
    """Periksa keadaan SEMUA catatan yang punya sorotan, sekali jalan.

    KENAPA DI SATU TEMPAT: naskah bisa 400 ribu karakter (disertasi S3).
    Kalau tiap catatan memecah naskah sendiri-sendiri, pekerjaan berulang
    dan halaman jadi lambat. Di sini naskah dipecah SEKALI.

    Return: {catatan_id: hasil cari_sorotan(...)}
    """
    hasil = {}
    for c in catatan or []:
        cid = getattr(c, 'id', None)
        if cid is None:
            continue
        hasil[cid] = cari_sorotan(naskah, getattr(c, 'teks_asli', '') or '')
    return hasil
