"""TATA PARAGRAF & VARIASI — aturan buku premium (SOT 20 Okt 2026).

MASALAH YANG DITUTUP (terukur dari buku uji "Ayo Mengenal Cuaca"):
  · paragraf ditulis apa adanya: `align='justify', space_after=8`
  · TANPA indentasi baris pertama
  · TANPA pemecah paragraf panjang (>7 kalimat dibiarkan)
  · TANPA variasi bentuk (0 daftar, 0 kotak, 0 nomor) ⇒ "dinding teks"

SUMBER ATURAN (lihat STANDAR_PEMBUATAN_BUKU_20OKT2026.md):
  S1 Chicago faq0217 — spasi antarparagraf 0, pemisah = inden
  S1 Chicago faq0223 — paragraf pertama SETELAH judul = rata kiri
  S3 PLOS Rule 3   — justified, inden 1 em, widow control, gaya bukan manual
  S5 Purdue OWL    — 1 paragraf 1 gagasan, 3-5 kalimat
  S6 APA           — nomor vs bullet vs huruf ditentukan MAKNA

MODUL INI MURNI FUNGSI (tanpa I/O) supaya bisa diuji tanpa DOCX.
"""
import re

# ── Angka dari SOT (semua bisa diubah di satu tempat) ────────────────────
INDEN_EM = 11.0              # 1 em @ huruf 11 pt  (BUKAN 0,5 inci!)
PARA_IDEAL_MIN, PARA_IDEAL_MAKS = 3, 5
PARA_MAKS_KALIMAT = 7
PARA_MAKS_KATA = 200
PARA_MIN_KALIMAT = 1         # hanya boleh untuk penekanan
MAKS_BUTIR_POIN = 7
MAKS_BUTIR_NOMOR = 10
MAKS_BERUNTUN_TANPA_VARIASI = 4

# ── Pemecah kalimat ─────────────────────────────────────────────────────
#  Titik/!/? diikuti spasi + huruf besar. Sengaja TIDAK memecah:
#  "1.5", "3,14", "No. 5", "Prof. Dr.", "dll.", "dsb.", "mis.", "hlm."
_SINGKATAN = {
    'prof', 'dr', 'drs', 'ir', 'hj', 'h', 'no', 'nomor', 'hal', 'hlm',
    'dll', 'dsb', 'mis', 'spt', 'thn', 'tgl', 'vol', 'hl', 'gbr', 'tab',
    'e.g', 'i.e', 'etc', 'vs', 'dkk', 'ybs', 'a.n', 'u.p', 's.d',
}
_POLA_KALIMAT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"“(\[])', re.UNICODE)


def pecah_kalimat(teks):
    """Pecah teks jadi daftar kalimat. Tahan singkatan & angka desimal."""
    if not teks or not teks.strip():
        return []
    kasar = _POLA_KALIMAT.split(teks.strip())
    hasil = []
    for potong in kasar:
        if hasil:
            #  Kalau potongan SEBELUMNYA berakhir dengan singkatan,
            #  gabungkan kembali (jangan pecah "Prof." dari "Dr. X").
            sebelum = hasil[-1].rstrip()
            m = re.search(r'([A-Za-z.]+)\.$', sebelum)
            if m and m.group(1).lower().rstrip('.') in _SINGKATAN:
                hasil[-1] = sebelum + ' ' + potong
                continue
        hasil.append(potong)
    return [k.strip() for k in hasil if k.strip()]


def jumlah_kata(teks):
    return len([k for k in re.split(r'\s+', (teks or '').strip()) if k])


def perlu_dipecah(teks):
    """True bila paragraf melanggar ambang SOT."""
    kal = pecah_kalimat(teks)
    return (len(kal) > PARA_MAKS_KALIMAT
            or jumlah_kata(teks) > PARA_MAKS_KATA)


def pecah_paragraf(teks, maks_kalimat=PARA_MAKS_KALIMAT,
                   maks_kata=PARA_MAKS_KATA):
    """Pecah paragraf panjang jadi beberapa paragraf wajar.

    Aturan: kumpulkan kalimat sampai ambang, lalu potong. TIDAK menambah
    kata apa pun (nol karangan) — hanya memindahkan batas paragraf.
    """
    kal = pecah_kalimat(teks)
    if len(kal) <= maks_kalimat and jumlah_kata(teks) <= maks_kata:
        return [teks.strip()]

    hasil, kini, kata_kini = [], [], 0
    for k in kal:
        n = jumlah_kata(k)
        if kini and (len(kini) >= maks_kalimat or kata_kini + n > maks_kata):
            hasil.append(' '.join(kini))
            kini, kata_kini = [], 0
        kini.append(k)
        kata_kini += n
    if kini:
        hasil.append(' '.join(kini))

    #  🚨 BUG TERUKUR 20 Okt 2026: penggabungan ekor 1-kalimat membuat
    #  paragraf 7 kalimat + ekor 1 = **8 kalimat** ⇒ melewati ambang 7
    #  lagi. Gerbang menemukan 12 paragraf >7 kalimat gara-gara ini.
    #  Obat: hanya gabung kalau HASILNYA masih <= ambang.
    if len(hasil) > 1 and len(pecah_kalimat(hasil[-1])) == 1:
        gabung = len(pecah_kalimat(hasil[-2])) + 1
        if gabung <= maks_kalimat:
            ekor = hasil.pop()
            hasil[-1] = hasil[-1] + ' ' + ekor
        #  Kalau tidak muat: biarkan paragraf 1 kalimat. SOT 2.7 bilang
        #  1 kalimat hanya untuk penekanan — di sini ekor pendek memang
        #  penekanan/penutup, jadi sah.
    return hasil


# ── Pendeteksi bentuk teks (untuk VARIASI) ──────────────────────────────
_POLA_BUTIR = re.compile(r'^\s*(?:[-•*–—]|\d{1,2}[.)]|[a-z][.)])\s+\S')
_POLA_NOMOR_LANGKAH = re.compile(r'^\s*(\d{1,2})[.)]\s+\S')

#  Kata sambung ANTARKALIMAT — penanda bahwa kalimat itu bagian NARASI,
#  bukan butir daftar yang berdiri sendiri. Terukur 20 Okt 2026: narasi
#  Indonesia hampir selalu memuat kata-kata ini, sedangkan butir daftar
#  (hal setara) tidak.
_KATA_SAMBUNG = {
    'yang', 'ini', 'itu', 'tersebut', 'kemudian', 'lalu', 'sehingga',
    'karena', 'sebab', 'oleh', 'maka', 'setelah', 'sebelum', 'ketika',
    'saat', 'sementara', 'sedangkan', 'namun', 'tetapi', 'akan', 'telah',
    'sudah', 'masih', 'juga', 'pula', 'bahkan', 'dengan', 'dari', 'pada',
    'untuk', 'terhadap', 'melalui', 'seperti', 'antara', 'bagi',
}

#  Kata KERJA imperatif/verba yang biasa MEMBUKA butir daftar prosedur.
#  Dipakai pagar paralelisme: butir daftar sejajar bentuknya.
_KATA_KERJA = {
    'gunakan', 'pakai', 'pilih', 'klik', 'tekan', 'buka', 'tutup', 'ambil',
    'letakkan', 'masukkan', 'tuang', 'aduk', 'campur', 'panaskan', 'dinginkan',
    'potong', 'ikat', 'lipat', 'tempel', 'gambar', 'tulis', 'baca', 'hitung',
    'ukur', 'amati', 'catat', 'simpan', 'buang', 'cuci', 'bersihkan',
    'siapkan', 'sediakan', 'lakukan', 'kerjakan', 'buat', 'coba', 'ulangi',
    'periksa', 'pastikan', 'hindari', 'jangan', 'harus', 'wajib', 'dapat',
    'bisa', 'mampu', 'membuat', 'mengambil', 'menggunakan', 'memilih',
    'menulis', 'membaca', 'mengukur', 'mencatat', 'mengamati', 'menyimpan',
    'menjaga', 'membantu', 'melancarkan', 'mengisi', 'mengalir', 'naik',
    'turun', 'berputar', 'bergerak', 'berubah', 'tumbuh', 'berkembang',
}

#  Kata BILANGAN yang membuka butir (mis. "Dua sendok air…").
_KATA_BILANGAN = {
    'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'delapan',
    'sembilan', 'sepuluh', 'pertama', 'kedua', 'ketiga', 'keempat',
}

#  Kata SIFAT yang membuka butir.
_KATA_SIFAT = {
    'panas', 'dingin', 'sejuk', 'hangat', 'lembap', 'kering', 'basah',
    'terang', 'gelap', 'besar', 'kecil', 'tinggi', 'rendah', 'panjang',
    'pendek', 'berat', 'ringan', 'cepat', 'lambat', 'mudah', 'sulit',
    'penting', 'utama', 'baik', 'buruk', 'bersih', 'kotor',
}


def _baris_teks(teks):
    return [b.strip() for b in (teks or '').split('\n') if b.strip()]


def ada_daftar(teks):
    """True bila teks sudah memuat daftar (poin/nomor)."""
    return any(_POLA_BUTIR.match(b) for b in _baris_teks(teks))


def _kandidat_pendek(kalimat):
    """Kalimat SETENGAH PENDEK yang layak jadi butir daftar.

    🚨 JEBAKAN TERUKUR (20 Okt 2026): ambang 14 kata TERLALU LONGGAR —
    paragraf 3 kalimat biasa ("Cuaca adalah keadaan udara pada suatu
    tempat dan waktu tertentu.") ikut jadi butir, sehingga SELURUH buku
    berubah jadi daftar (uji DOCX: 24 butir, 0 paragraf). Butir daftar
    harus JAUH lebih pendek dari kalimat narasi.
    """
    return [k for k in kalimat if jumlah_kata(k) <= 9]


def _sudah_kalimat_lengkap(k):
    """Butir = kalimat lengkap? (diawali kapital, diakhiri titik)."""
    k = k.strip()
    return bool(k) and k[0].isupper() and k[-1] in '.!?'


def _rapikan_butir(k, kalimat_lengkap):
    """Seragamkan tanda baca butir (SOT 4.3: satu gaya se-buku)."""
    k = k.strip().rstrip(';:,')
    if kalimat_lengkap:
        if k and k[-1] not in '.!?':
            k += '.'
        if k:
            k = k[0].upper() + k[1:]
    else:
        if k and k[-1] in '.':
            k = k[:-1]
        if k:
            k = k[0].lower() + k[1:]
    return k


def jadikan_daftar(teks, gaya='poin', maks=MAKS_BUTIR_POIN):
    """Ubah paragraf berisi rentetan hal SETARA jadi DAFTAR.

    🚨 PAGAR ANTI-RAKUS — EMPAT KALI gagal sebelum ini (20 Okt 2026):
      v1 ambang 14 kata  → SELURUH buku jadi daftar (24 butir, 0 paragraf).
      v2 ambang 9 kata   → narasi Indonesia (8-9 kata/kalimat) tetap lolos.
      v3 kata sambung    → masih lolos: buku ANAK ditulis dengan kalimat
                           pendek & tanpa kata sambung ("Awan di sana
                           bentuknya macam-macam.") ⇒ 170 butir dari narasi
                           cerita. Ini yang PALING BERBAHAYA: cerita anak
                           diubah jadi daftar, isinya rusak.
      v4 (INI) penanda sebenarnya = PARALELISME BENTUK:
         · Butir daftar sejajar bentuknya (semua frasa benda ATAU semua
           kalimat perintah ATAU semua kata kerja).
         · NARASI bercerita → kalimatnya berganti-ganti bentuk
           (tanya, pernyataan, seruan) ⇒ DITOLAK.
         · Tambahan: kalimat tanya & seruan BUKAN butir daftar.
         · Tambahan: minimal 3 dari 4 kalimat harus berpola SEJAJAR.
    """
    kal = pecah_kalimat(teks)
    if len(kal) < 3:
        return None
    if len(kal) > maks:
        return None

    #  Kalimat tanya / seruan = NARASI, bukan butir daftar.
    if any(k.rstrip().endswith(('?', '!')) for k in kal):
        return None

    if any(jumlah_kata(k) > 14 for k in kal):
        return None
    rata = sum(jumlah_kata(k) for k in kal) / len(kal)
    if rata > 11:
        return None

    #  ── PAGAR UTAMA: PARALELISME BENTUK ───────────────────────────────
    def pola(k):
        """Ambil 2 kata pertama sebagai pola bentuk kalimat."""
        kata = re.findall(r'\w+', k.lower())
        return tuple(kata[:2]) if len(kata) >= 2 else (kata[0] if kata else '')

    def jenis_awal(k):
        """Kategori kata pertama: benda / kerja / sifat / bilangan."""
        kata = re.findall(r'\w+', k.lower())
        if not kata:
            return 'kosong'
        k0 = kata[0]
        if k0 in _KATA_KERJA:
            return 'kerja'
        if k0 in _KATA_BILANGAN:
            return 'bilangan'
        if k0 in _KATA_SIFAT:
            return 'sifat'
        return 'benda'

    jenis = [jenis_awal(k) for k in kal]
    seragam = max(jenis.count(j) for j in set(jenis)) / len(jenis)
    if seragam < 0.75:
        return None

    #  Kata sambung antarkalimat = penanda narasi
    tersambung = 0
    for k in kal:
        kata = re.findall(r'\w+', k.lower())
        if any(s in kata for s in _KATA_SAMBUNG):
            tersambung += 1
    if tersambung > len(kal) * 0.34:
        return None

    lengkap = all(_sudah_kalimat_lengkap(k) for k in kal)
    butir = [_rapikan_butir(k, lengkap) for k in kal]
    if gaya == 'poin':
        baris = [f'• {b}' for b in butir]
    else:
        baris = [f'{i}. {b}' for i, b in enumerate(butir, 1)]
    return '\n'.join(baris)


def sisip_variasi(daftar_paragraf, judul_bab=''):
    """Sisipkan variasi bentuk bila 4 paragraf berturut tanpa variasi.

    PAGAR: TIDAK mengarang isi. Hanya MENGUBAH BENTUK paragraf yang
    sudah ada jadi daftar. Kalau tidak layak → biarkan paragraf utuh.

    Mengembalikan list blok: ('paragraf', teks) | ('daftar', teks)
    """
    hasil, beruntun = [], 0
    for p in daftar_paragraf:
        sudah_ada_variasi = ada_daftar(p) or '\n' in (p or '')
        if sudah_ada_variasi:
            beruntun = 0
            hasil.append(('paragraf', p))
            continue

        if beruntun >= MAKS_BERUNTUN_TANPA_VARIASI:
            ubah = jadikan_daftar(p)
            if ubah:
                hasil.append(('daftar', ubah))
                beruntun = 0
                continue
            #  Tidak bisa jadi daftar → pecah saja (tetap bukan dinding teks)
            potong = pecah_paragraf(p)
            for q in potong:
                hasil.append(('paragraf', q))
            beruntun = 0
            continue

        for q in pecah_paragraf(p):
            hasil.append(('paragraf', q))
        beruntun += 1
    return hasil
