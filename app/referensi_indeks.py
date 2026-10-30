"""Bantu rakit buku referensi — glosarium, pustaka, dan indeks bernomor.

Dipakai HANYA jalur kartu buku-referensi di app/penyusunan_buku.susun().
Tidak mengimpor modul host (/opt/data) — stdlib + python-docx saja.

Alur (sesudah S.susun_buku, sebelum/sesudah isi_nomor):
  1. kumpulkan_istilah(): petik blok [ISTILAH BARU] dari berkas bab txt
     -> glosarium {istilah: definisi}; blok DIHAPUS dari txt supaya tidak
     tercetak mentah di buku (rakit membaca txt yang sama).
     29 Okt 2026 — ditambah EKSTRAKSI DETERMINISTIK: blok tidak pernah
     keluar dari dewan (0 blok di 8/8 bab uji) sehingga glosarium kosong
     -> indeks subjek kosong -> gerbang R1 gagal. Definisi kini juga
     diekstrak dari narasi (pola 'X adalah ...', sub Definisi dulu);
     HANYA dari teks yang ada, tidak mengarang definisi. Istilah blok
     (bila ada) menang atas hasil ekstraksi.
  2. kumpulkan_pustaka(): gabung refs_bab{n}.json dari folder visual PER
     BAB (keluar/bab{n}/visual/) — rakit HANYA mencari di satu folder
     visual, sehingga pustaka bab-bab awal hilang tanpa langkah ini
     (cacat lama jalur umum, tidak diubah di sini).
  3. kumpulkan_nama(): kandidat surname dari string pustaka (APA
     maupun Nama Depan Nama Belakang; pencocokan badan menyaring
     kandidat yang salah).
  4. isi_indeks(): sesudah isi_nomor, isi nomor halaman entri indeks di
     docx dari teks per halaman sidecar; halaman TOC dan halaman
     back-matter DIKECUALIKAN dari pencarian.
  5. kumpulkan_singkatan() + isi_singkatan(): Daftar Singkatan
     deterministik dari teks bab (pola 'Kepanjangan (SINGKATAN)' dan
     sebaliknya, plus akronim sering muncul); ditulis bernomor halaman
     seperti indeks. Gagal di sini TIDAK menggagalkan buku (singkatan
     hanya peringatan gerbang Rw, bukan cek keras).
"""

import json
import os
import re

# Judul seksi yang dikenali sebagai pembatas saat mengganti entri indeks.
_SEKSI = ('GLOSARIUM', 'INDEKS SUBJEK', 'INDEKS NAMA', 'INDEKS',
          'DAFTAR PUSTAKA', 'DAFTAR SINGKATAN', 'TENTANG PENULIS')

# Kata generik yang TIDAK layak jadi istilah glosarium (kata tunjuk,
# kata ganti, kata umum). Berlaku untuk istilah SATU kata; istilah
# multi-kata yang diawali kata-kata ini juga ditolak bila kata
# pertamanya ada di sini (kecuali sudah lolos saring awalan Konsep/dkk).
_ISTILAH_STOP_1 = {
    'ini', 'itu', 'tersebut', 'hal', 'penelitian', 'buku', 'bab',
    'penulis', 'pembaca', 'mereka', 'kami', 'kita', 'anda',
    'pendekatan', 'model', 'teori', 'studi', 'analisis', 'hasil',
    'data', 'sistem', 'konsep', 'istilah', 'definisi', 'pengertian',
    'catatan', 'contoh', 'tabel', 'gambar', 'bagian', 'uraian',
    'pembahasan', 'kajian', 'temuan', 'metode', 'strategi', 'kebijakan',
    'kesimpulan', 'ringkasan', 'pendahuluan', 'penutup', 'saran',
    'rekomendasi',
}
# Kata fungsi di dalam istilah = tanda itu klausa, bukan istilah.
_ISTILAH_STOP_DALAM = {'yang', 'dengan', 'untuk', 'dari', 'dalam',
                       'pada', 'adalah', 'merupakan', 'dan', 'atau',
                       'terhadap', 'bukan', 'juga', 'dapat', 'bahwa',
                       'melalui', 'tanpa', 'antara', 'atas', 'oleh',
                       'kepada', 'bagi', 'secara'}
# Kata kerja yang TIDAK BOLEH muncul dalam istilah: istilah adalah
# frasa nomina — bila kandidat mengandung kata kerja, itu klausa
# ('Digital participant menempatkan UMKM'), bukan istilah. Daftar ini
# sengaja eksplisit (bukan awalan me-/di-/ber-): partisipel seperti
# 'berorientasi', 'berbasis', 'terdistribusi' SAH muncul dalam istilah.
_ISTILAH_KATA_KERJA = {
    'menempatkan', 'memandang', 'memposisikan', 'menjadikan',
    'diperlakukan', 'dimodelkan', 'dimaknai', 'berfungsi',
    'diposisikan', 'didefinisikan', 'diartikan', 'mengacu', 'merujuk',
    'dipahami', 'dibaca', 'digambarkan', 'diisyaratkan',
    'dimaksudkan', 'dianggap', 'disebut', 'dinamakan', 'menunjukkan',
    'menjelaskan', 'menggambarkan', 'membedakan', 'menekankan',
    'menandai', 'ditempatkan', 'diletakkan', 'diberlakukan',
    'diterapkan', 'digunakan', 'dipakai', 'dimanfaatkan', 'dilakukan',
    'diberikan', 'dinyatakan', 'dirumuskan', 'ditetapkan', 'dibahas',
    'diuraikan', 'dikemukakan', 'diajukan', 'ditawarkan', 'dicapai',
    'dihasilkan', 'diperoleh', 'ditemukan', 'diamati', 'dicatat',
    'dilaporkan', 'diidentifikasi', 'diklasifikasikan', 'diukur',
    'dinilai', 'dievaluasi', 'dibandingkan', 'dihubungkan',
    'dikaitkan', 'dipengaruhi', 'ditentukan', 'dibentuk', 'dibangun',
    'dikembangkan', 'diciptakan', 'mengarahkan', 'menggerakkan',
    'mendorong', 'menghambat', 'memengaruhi', 'mempengaruhi',
    'membatasi', 'memperluas', 'memperkuat', 'memperlemah', 'mengubah',
    'menggantikan', 'menggabungkan', 'memisahkan', 'menghubungkan',
    'mengaitkan',
}

# Kata yang TIDAK BOLEH muncul di mana pun dalam istilah: urutan
# (enumerasi wacana, bukan konsep), kata tunjuk, dan kata ganti waktu.
_ISTILAH_TOLAK_DIMANA = {
    'pertama', 'kedua', 'ketiga', 'keempat', 'kelima', 'keenam',
    'ketujuh', 'kedelapan', 'kesembilan', 'kesepuluh',
    'ini', 'itu', 'tersebut', 'sini', 'situ', 'sana',
    'berikutnya', 'selanjutnya',
}
# Kata pertama yang TIDAK BOLEH mengawali istilah: kata tunjuk, kuantor,
# konjungsi/preposisi, peran (penulis/pembaca), dan penanda gambar/tabel.
# Istilah asli selalu diawali kata benda — bukan kata-kata ini.
_ISTILAH_AWAL_TOLAK = {
    'ini', 'itu', 'tersebut', 'hal', 'para', 'setiap', 'semua',
    'beberapa', 'banyak', 'berbagai', 'seluruh',
    'bagi', 'karena', 'di', 'dalam', 'ketika', 'jika', 'apabila',
    'sementara', 'namun', 'tetapi', 'sehingga', 'oleh', 'menurut',
    'berdasarkan', 'melalui', 'dengan', 'tanpa', 'antara', 'setelah',
    'sebelum', 'selama', 'hingga', 'sampai', 'yaitu', 'yakni',
    'artinya', 'maksudnya', 'untuk', 'dari', 'pada', 'atas', 'tentang',
    'penulis', 'pembaca', 'peneliti', 'diagram', 'tabel', 'gambar',
    'bila',
}

# Kata yang TIDAK layak jadi singkatan: judul seksi, angka Romawi,
# penanda daftar, kata umum caps.
_SINGKATAN_STOP = {
    'BAB', 'DAFTAR', 'PUSTAKA', 'GLOSARIUM', 'INDEKS', 'NAMA', 'SUBJEK',
    'SINGKATAN', 'TENTANG', 'PENULIS', 'KATA', 'PENGANTAR', 'ISI',
    'HALAMAN', 'TABEL', 'GAMBAR', 'EDITOR', 'DAN', 'YANG', 'DARI',
    'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
    'XI', 'XII', 'XIII', 'XIV', 'XV',
}

# Kata kerja definisi yang dikenali ekstraktor glosarium.
_KATA_DEFINISI = (
    'adalah', 'merupakan', 'didefinisikan sebagai',
    'diartikan sebagai', 'mengacu pada', 'merujuk pada',
    'dipahami sebagai', 'dapat diartikan sebagai', 'didefinisikan',
    'sebagai',
)


def _path_bab(keluar, n):
    """Berkas txt satu bab (dua kemungkinan letak, seperti susun())."""
    utama = os.path.join(keluar, f'bab{n}', f'bab{n}.txt')
    if os.path.exists(utama):
        return utama
    return os.path.join(keluar, f'bab{n}.txt')


def kumpulkan_istilah(keluar, outline):
    """Petik [ISTILAH BARU] dari txt bab -> (glosarium, jumlah_diambil).

    Format blok (dari prompt architect): baris penanda '[ISTILAH BARU]'
    diikuti baris 'Istilah: definisi'. Blok berakhir di baris kosong,
    penanda '[' lain, atau judul sub '###'. Baris yang tidak berpola
    'Istilah: definisi' DIBIARKAN (tidak dihapus) — konservatif.
    """
    glos = {}
    diambil = 0
    for n in sorted(k for k in outline if isinstance(k, int)):
        path = _path_bab(keluar, n)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            baris = f.read().splitlines()
        keluar_baris = []
        i = 0
        while i < len(baris):
            b = baris[i].strip()
            # 29 Okt 2026 (temuan uji 219): penanda SEBARIS ('[ISTILAH BARU:
            # ...]') dan penutup yatim ('[/ISTILAH BARU]') TIDAK ditangkap
            # cek standar di bawah (yang menuntut ']' sesudah BARU) —
            # keduanya nyasar ke docx final. Hapus barisnya (istilah tanpa
            # definisi TIDAK dikarang ke glosarium; perbaikan format ada di
            # prompt arsitek, bukan di sini).
            if b.startswith('[ISTILAH BARU:') or b.startswith('[/ISTILAH BARU]'):
                i += 1
                continue
            if b.startswith('[ISTILAH BARU]'):
                # Sisa baris penanda setelah ']' diabaikan; kumpulkan
                # baris istilah berikutnya.
                i += 1
                while i < len(baris):
                    t = baris[i].strip()
                    if (not t or t.startswith('[')
                            or t.startswith('###')):
                        break
                    if ':' in t:
                        istilah, definisi = t.split(':', 1)
                        istilah, definisi = istilah.strip(), definisi.strip()
                        if istilah and definisi and istilah not in glos:
                            glos[istilah] = definisi
                            diambil += 1
                        i += 1
                    else:
                        break
                # Baris penanda + baris istilah TIDAK ditulis kembali
                # (= blok terhapus dari txt); baris pemutus (kosong/'###')
                # tetap diproses normal oleh loop.
                continue
            keluar_baris.append(baris[i])
            i += 1
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(keluar_baris) + ('\n' if keluar_baris else ''))
    # 29 Okt 2026 — PENGAMAN DETERMINISTIK (lihat docstring): blok
    # [ISTILAH BARU] tidak pernah keluar dari dewan (0 blok di 8/8 bab
    # uji) sehingga glosarium kosong -> indeks subjek kosong -> gerbang
    # R1 gagal. Ekstrak definisi dari narasi sebagai pelengkap — HANYA
    # dari teks yang ada, tidak mengarang definisi. Istilah blok (bila
    # ada) menang atas hasil ekstraksi.
    try:
        for istilah, definisi in _ekstrak_definisi_dari_teks(
                keluar, outline).items():
            glos.setdefault(istilah, definisi)
    except Exception:
        pass  # ekstraksi gagal = glosarium tetap dari blok saja
    return glos, diambil


def _teks_semua_sub(keluar, outline):
    """Semua sub-bab (judul, teks) dari txt bab, urut bab lalu sub.

    Baris penanda '[' (tabel/gambar/dll) dibuang — ekstraktor bekerja
    atas narasi saja. Baris sebelum sub pertama ikut sebagai sub
    berjudul '' (intro bab).
    """
    semua = []
    for n in sorted(k for k in outline if isinstance(k, int)):
        path = _path_bab(keluar, n)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                baris = f.read().splitlines()
        except Exception:
            continue
        judul, isi = '', []
        for b in baris:
            s = b.strip()
            if s.startswith('### '):
                if judul or isi:
                    semua.append((judul, ' '.join(isi)))
                judul, isi = s[4:].strip(), []
                continue
            if s.startswith('['):
                continue
            if s.upper() == 'GLOSARIUM':
                continue  # judul blok glosarium terdistribusi, bukan isi
            if s:
                isi.append(s)
        if judul or isi:
            semua.append((judul, ' '.join(isi)))
    return semua


def _istilah_sah(istilah, pola_titik_dua=False):
    """Validasi istilah kandidat -> istilah bersih atau None."""
    istilah = re.sub(r'\s+sendiri$', '', istilah.strip())
    # Akronim dalam kurung di ujung istilah bukan bagian nama
    # ('Resource-Based View (RBV)' -> 'Resource-Based View'; akronimnya
    # sudah ditangani Daftar Singkatan). Kurung terjemahan dipertahankan
    # ('Kemampuan dinamis (dynamic capabilities)').
    m_akr = re.match(r'^(.*?)\s*\(([A-Z][A-Z0-9]{1,7})\)$', istilah)
    if m_akr:
        istilah = m_akr.group(1)
    # Kupas penanda butir ('- ', '• ') dan nomor sub ('3.1 ') di depan,
    # serta tanda kutip di ujung ('"e-commerce"' -> 'e-commerce').
    istilah = re.sub(r'^[\-\•\s]+', '', istilah)
    istilah = re.sub(r'^\d+(\.\d+)*\s+', '', istilah)
    istilah = istilah.strip('"\'“”‘’')
    if ':' in istilah or ';' in istilah:
        return None  # gabungan judul + istilah, bukan satu istilah
    kata = istilah.strip().strip('.,;:').split()
    if not (1 <= len(kata) <= 4):
        return None
    if kata[0].strip('.,;:').lower() in _ISTILAH_AWAL_TOLAK:
        return None
    if len(kata) == 1 and kata[0].strip('.,;:').lower() in _ISTILAH_STOP_1:
        return None
    if any(w.strip('.,;:').lower() in _ISTILAH_STOP_DALAM for w in kata):
        return None
    if any(w.strip('.,;:').lower() in _ISTILAH_KATA_KERJA for w in kata):
        return None
    if any(w.strip('.,;:').lower() in _ISTILAH_TOLAK_DIMANA
           for w in kata):
        return None
    if kata[-1].strip('.,;:').lower() in ('penulis', 'pembaca',
                                          'peneliti'):
        return None  # label peran ('Posisi penulis'), bukan istilah
    if any(w.strip('.,;:').lower().endswith('nya') and len(w) > 3
           for w in kata):
        return None  # bentuk posesif ('hasilnya', 'implikasinya')
    if pola_titik_dua and any(w.strip('.,;:').lower() in _ISTILAH_STOP_1
                               for w in kata):
        return None
    for w in kata:
        if any(ch.isdigit() for ch in w) \
                and not re.fullmatch(r'\d+\.\d+', w):
            return None  # angka di istilah, kecuali pola '4.0'
    bersih = ' '.join(kata)
    if not bersih:
        return None
    if not bersih[0].isupper() and not bersih.startswith('e-'):
        # Istilah tengah kalimat ('ekonomi digital') dinormalisasi ke
        # huruf kapital awal; istilah 'e-...' dipertahankan apa adanya.
        bersih = bersih[0].upper() + bersih[1:]
    if len(kata) == 1 and len(bersih) < 4 and not bersih.isupper():
        return None
    return bersih


def _definisi_bersih(definisi):
    """Definisi: buang sitasi '(...tahun...)', rapikan, batasi panjang.

    Definisi ANAFORIK ditolak ('... yang tersebut ...', '... yang
    dimaksud ...'): glosarium harus berdiri sendiri — pembaca yang
    membuka istilah tidak membawa konteks kalimat sebelumnya.
    """
    d = re.sub(r'\([^)]*\d{4}[^)]*\)', '', definisi or '')
    d = re.sub(r'\s+', ' ', d).strip().strip('.,;:')
    if any(w.strip(',.').lower() in ('tersebut', 'dimaksud')
           for w in d.split()):
        return None
    # Rujukan meta-terminologi buku ('akan dipertahankan konsisten
    # sepanjang buku') bukan definisi — tolak supaya definisi substantif
    # berikutnya yang menang.
    dl = d.lower()
    if any(frasa in dl for frasa in (
            'sepanjang buku', 'pada sub-bab', 'telah ditetapkan',
            'akan dipertahankan', 'berlaku konsisten',
            'sebagaimana didefinisikan', 'sebagaimana ditegaskan')):
        return None
    if len(d.split()) < 4:
        return None
    if len(d) > 300:
        d = d[:300].rsplit(' ', 1)[0]
    return d


def _ekstrak_definisi_dari_teks(keluar, outline):
    """Ekstrak {istilah: definisi} dari narasi bab (deterministik).

    Pola: kalimat 'ISTILAH adalah/merupakan/didefinisikan sebagai/...'
    (awal maupun tengah kalimat) dan baris 'Istilah: definisi'. Sub
    'Definisi' diproses dulu (paling kanonik); definisi pertama menang.
    Batas 300 entri.
    """
    kata_kerja = '|'.join(sorted(_KATA_DEFINISI, key=len, reverse=True))
    # 'sebagai' HANYA di pola awal kalimat: di tengah kalimat ia
    # menempel pada kata kerja ('memandang X sebagai Y', 'berfungsi
    # sebagai Y') sehingga istilah yang tertangkap adalah klausa
    # ('Digital participant memandang UMKM'), bukan istilah.
    kata_kerja_tengah = '|'.join(
        sorted((k for k in _KATA_DEFINISI if k != 'sebagai'),
               key=len, reverse=True))
    pola_kalimat = re.compile(
        r'^([A-Za-z][^,;:\(\)\[\]]{0,60}?)\s+(?:' + kata_kerja +
        r')\s+(.+)$')
    pola_titik_dua = re.compile(r'^([A-Za-z][^:,;]{1,50}):\s+(.+)$')
    subs = _teks_semua_sub(keluar, outline)
    # Sub Definisi dulu, lalu sisanya — definisi pertama menang.
    subs.sort(key=lambda s: 0 if 'definisi' in s[0].lower() else 1)
    glos, lihat = {}, set()

    def _tambah(istilah, definisi):
        if istilah is None or istilah.lower() in lihat:
            return False
        definisi = _definisi_bersih(definisi)
        if not definisi:
            return False
        glos[istilah] = definisi
        lihat.add(istilah.lower())
        return len(glos) >= 300

    pola_kata_kerja = re.compile(r'\b(?:' + kata_kerja_tengah + r')\b')
    for judul, teks in subs:
        for kalimat in re.split(r'(?<=[.!?])\s+', teks):
            k = kalimat.strip()
            # Pola awal kalimat: 'ISTILAH adalah ...'.
            m = pola_kalimat.match(k)
            if m and _tambah(_istilah_sah(m.group(1)), m.group(2)):
                return glos
            # Pola tengah kalimat: '..., ISTILAH didefinisikan ...'.
            # Istilah = kata-kata sesudah koma terakhir sebelum kata
            # kerja (maks 4 kata) — mis. 'Di Indonesia, UMKM
            # didefinisikan ...' -> 'UMKM'. Satu kalimat boleh
            # mendefinisikan dua istilah ('Digitalisasi ... sedangkan
            # transformasi digital adalah ...').
            for vm in pola_kata_kerja.finditer(k):
                sebelum = k[:vm.start()].split()
                idx_koma = max([i for i, w in enumerate(sebelum)
                                if w.endswith(',')], default=-1)
                potong = sebelum[idx_koma + 1:]
                # Kupas kata sambung di depan ('sedangkan transformasi
                # digital adalah ...' -> 'transformasi digital').
                while len(potong) > 1 and potong[0].lower().strip(',') in (
                        'sedangkan', 'sementara', 'namun', 'tetapi',
                        'dan', 'atau', 'serta', 'lalu', 'kemudian',
                        'bahkan', 'justru', 'melainkan', 'padahal',
                        'sehingga', 'karena', 'yang'):
                    potong = potong[1:]
                if not potong:
                    continue
                if _tambah(_istilah_sah(' '.join(potong[-4:])),
                           k[vm.end():]):
                    return glos
        if len(glos) >= 300:
            break
    # Pola titik dua, per kalimat (baris 'Istilah: definisi ...' menjadi
    # kalimat sendiri sesudah pemisahan kalimat, karena baris aslinya
    # diakhiri titik).
    for judul, teks in subs:
        for kalimat in re.split(r'(?<=[.!?])\s+', teks):
            m = pola_titik_dua.match(kalimat.strip())
            if not m:
                continue
            istilah = _istilah_sah(m.group(1), pola_titik_dua=True)
            if istilah is None or istilah.lower() in lihat:
                continue
            definisi = _definisi_bersih(m.group(2))
            if definisi:
                glos[istilah] = definisi
                lihat.add(istilah.lower())
                if len(glos) >= 300:
                    return glos
    return glos


def kumpulkan_singkatan(keluar, outline):
    """Kumpulkan {SINGKATAN: kepanjangan} dari teks bab (deterministik).

    Pola: 'Kepanjangan (SINGKATAN)', 'SINGKATAN (kepanjangan)', plus
    akronim yang muncul >=3x tanpa kepanjangan (entri tanpa kepanjangan).
    HANYA dari teks yang ada — tidak mengarang kepanjangan.
    """
    from collections import Counter
    teks_prosa = []
    for n in sorted(k for k in outline if isinstance(k, int)):
        path = _path_bab(keluar, n)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                baris = [b.strip() for b in f.read().splitlines()
                         if b.strip()
                         and not b.strip().startswith('[')
                         and not b.strip().startswith('### ')
                         and b.strip().upper() != 'GLOSARIUM']
        except Exception:
            continue
        teks_prosa.append(' '.join(baris))
    teks = ' '.join(teks_prosa)

    # Kata klausa di dalam kepanjangan = tanda itu rujukan judul/kalimat,
    # bukan kepanjangan ('Dalam keluarga ini, Technology Acceptance
    # Model'). Kata hubung daftar ('dan', 'of', 'and') DIBOLEHKAN.
    _KEPANJANGAN_TOLAK = {
        'dalam', 'yang', 'ini', 'itu', 'tersebut', 'dari', 'untuk',
        'dengan', 'pada', 'kepada', 'oleh', 'sebagai', 'adalah',
        'merupakan', 'yakni', 'yaitu', 'ketika', 'jika', 'apabila',
        'karena', 'sehingga', 'namun', 'tetapi', 'sementara', 'melalui',
        'tanpa', 'antara', 'setelah', 'sebelum', 'selama', 'hingga',
        'sampai', 'atas', 'tentang', 'bagi', 'menurut', 'berdasarkan',
    }

    def _kepanjangan_sah(kep):
        kata = kep.strip().strip('.,;:').split()
        # Hitung kata pecah-hubung juga ('Undang-Undang' = 2 kata).
        n_kata = len(re.split(r'[\s-]+', kep.strip().strip('.,;:')))
        if not (2 <= n_kata <= 8):
            return None
        if any(any(ch.isdigit() for ch in w) for w in kata):
            return None
        rendah = [w.strip(',.').lower() for w in kata]
        if any(w in _KEPANJANGAN_TOLAK for w in rendah):
            return None
        atas = [w.strip(',.').upper() for w in kata]
        if atas[0] in _SINGKATAN_STOP:
            return None
        if any(w in ('BAB', 'DAFTAR', 'PUSTAKA', 'GLOSARIUM', 'INDEKS',
                     'TABEL', 'GAMBAR') for w in atas):
            return None
        return ' '.join(kata)

    def _akronim_sah(akr):
        if not (2 <= len(akr) <= 8):
            return None
        if akr in _SINGKATAN_STOP:
            return None
        return akr

    # Kumpulkan SEMUA kandidat, lalu pilih yang TERPENDEK per akronim:
    # rujukan judul ('Perbandingan Kritis Teori Berbasis Sumber Daya')
    # selalu lebih panjang dari kepanjangan asli ('Resource-Based View').
    kandidat = {}

    def _ekspansi_dari_ekor(segmen):
        """Kepanjangan dari ekor segmen sebelum '(AKR)'.

        Kupas kata awal yang berupa kata klausa ('menurut', 'dalam',
        'ini') atau huruf kecil yang diikuti kata kapital ('teori
        Resource-Based View' -> 'Resource-Based View'). Kepanjangan
        huruf kecil utuh ('usaha mikro, kecil, dan menengah') TIDAK
        dikupas (tidak ada kata kapital sesudahnya) — dipertahankan.
        """
        kata = segmen.split()
        while kata:
            w0 = kata[0].strip(',.').lower()
            if w0 in _KEPANJANGAN_TOLAK:
                kata = kata[1:]
                continue
            if kata[0][0].islower() and any(
                    w and w[0].isupper() for w in kata[1:]):
                kata = kata[1:]
                continue
            break
        if not kata:
            return None
        return _kepanjangan_sah(' '.join(kata))

    # Pola 'Kepanjangan (AKR)': JANGAN pakai regex rentang (temuan
    # 29 Okt 2026 — rentang kiri-terjauh menelan kepanjangan bersih di
    # dalamnya bila diawali kata klausa, lalu kandidat bersih hilang
    # karena finditer tidak mencoba ulang). Ambil per kemunculan kurung:
    # segmen sesudah batas kalimat/kurung terakhir sebelum '(AKR)'.
    for m in re.finditer(r'\(([A-Z][A-Z0-9]{1,7})\)', teks):
        akr = _akronim_sah(m.group(1))
        if not akr:
            continue
        ekor = teks[max(0, m.start() - 120):m.start()]
        batas = max(ekor.rfind('.'), ekor.rfind('!'), ekor.rfind('?'),
                    ekor.rfind('('))
        segmen = ekor[batas + 1:]
        kep = _ekspansi_dari_ekor(segmen)
        if kep:
            kandidat.setdefault(akr, []).append(
                (len(re.split(r'[\s-]+', kep)), m.start(), kep))
    for m in re.finditer(r'\b([A-Z][A-Z0-9]{1,7})\s*\(([^()]{2,70}?)\)',
                         teks):
        akr = _akronim_sah(m.group(1))
        kep = _kepanjangan_sah(m.group(2))
        if kep and akr:
            kandidat.setdefault(akr, []).append(
                (len(re.split(r'[\s-]+', kep)), m.start(), kep))
    # --- Pola baru G7 (30 Okt 2026): kenapa dulu hanya 3 ---
    # Dulu: (1) kepanjangan hanya dari kurung, padahal naskah ini
    # hampir tidak pernah menulis akronim dalam kurung (hanya UMKM
    # 2x); teori ditulis utuh ('Resource Based View' 7x) tanpa
    # akronimnya, jadi tidak tertangkap. (2) Akronim sering muncul
    # butuh >=3x, padahal TAM/RBV/DOI/ROI hanya 1x di badan.
    # (3) Tanpa saringan kemunculan, sitasi 'RPIR et al.' (16x) dan
    # penanda 'SUB-BAB' (SUB 4x) justru tertangkap sebagai singkatan.
    # Perbaikan: (a) kemunculan SAH: bukan pecahan kata berhubung,
    # bukan sitasi 'et al.', bukan kata penanda huruf besar berurutan
    # (3+ kata kapital berturut-turut, misal baris 'SUB-BAB 5.1
    # DEFINISI DAN KONSEP KUNCI ...'); ambang turun ke >=1x karena
    # akronim yang dipakai sekali tetap dipakai. (b) derivasi inisial:
    # frasa multi-kata yang huruf awalnya membentuk token yang juga
    # muncul mandiri (misal 'Resource Based View' + token RBV)
    # memberi kepanjangan terverifikasi huruf per huruf, tanpa
    # mengarang. (c) urutan menang: kepanjangan kurung yang
    # TERverifikasi inisialnya dulu, lalu derivasi, lalu kepanjangan
    # kurung tak terverifikasi (perilaku lama), lalu token mandiri
    # tanpa kepanjangan.
    import bisect as _bisect

    _KONEKTOR = {'dan', 'and', 'of', 'the', 'di', 'atau', 'or',
                   'akan'}

    def _inisial_cocok(frasa, token):
        """True bila inisial frasa (konektor dihitung atau dilewat)
        sama dengan token. Dipakai memverifikasi kepanjangan kurung
        ('Usaha Mikro, Kecil, dan Menengah' -> UMKM lewat varian
        lepas-konektor; 'Kesiapan teknologi' -> KT, bukan TOE)."""
        kata = [w.strip(',.()') for w in re.split(r'[\s-]+', frasa)
                if w.strip(',.()')]
        if not kata:
            return False
        rendah = [w.lower() for w in kata]
        penuh = ''.join(w[0].upper() for w in rendah if w)
        lepas = ''.join(w[0].upper() for w in rendah
                        if w and w not in _KONEKTOR)
        return token in (penuh, lepas)

    def _turunan_inisial(mandiri):
        """{token: frasa tampil} dari frasa yang inisialnya = token.

        Frasa tidak boleh melewati batas kalimat, tidak boleh
        mengandung kata huruf besar semua (penanda), dan kata isinya
        minimal 2 huruf. Tambahan anti-kebetulan: satu kemunculan
        frasa hanya dihitung bila minimal 2 kata isinya berhuruf
        awal kapital (ciri frasa istilah, bukan kalimat biasa yang
        kebetulan inisialnya sama, misal 'firma tunggal akan
        menghasilkan' untuk TAM). Bila satu token punya beberapa
        frasa, frasa tersering menang, seri = yang pertama muncul.
        Tampilan frasa diambil dari token mentah aslinya, jadi koma
        ('Usaha Mikro, Kecil, dan Menengah') dan pemisah hubung
        ('Technology Organization Environment') dipertahankan
        bentuk wajarnya.
        """
        mentahan = teks.split()
        bagian = []
        for ri, mentah in enumerate(mentahan):
            inti = mentah.strip('.,;:!?()[]{}')
            if not inti:
                bagian.append(None)
                continue
            akhir = mentah.endswith(('.', '!', '?'))
            potongan = inti.split('-')
            for j, pot in enumerate(potongan):
                if not pot.isalpha():
                    bagian.append(None)
                    continue
                bagian.append((pot, akhir and j == len(potongan) - 1, ri))
        temu = {}
        for token in mandiri:
            per_mulai = {}
            for i, ent in enumerate(bagian):
                if ent is None:
                    continue
                kata0, _, _ = ent
                if len(kata0) < 2 or kata0.isupper():
                    continue
                if kata0[0].upper() != token[0]:
                    continue
                for lewati in (False, True):
                    huruf = []
                    kata_frasa = []
                    raw_awal = None
                    raw_akhir = None
                    j = i
                    cocok = False
                    while j < len(bagian) and len(huruf) < len(token) \
                            and len(kata_frasa) <= len(token) + 2:
                        ent2 = bagian[j]
                        if ent2 is None:
                            break
                        w2, akhir2, ri2 = ent2
                        if len(w2) < 2 or not w2.isalpha() \
                                or w2.isupper():
                            break
                        rendah = w2.lower()
                        if lewati and rendah in _KONEKTOR and j != i:
                            kata_frasa.append(w2)
                            raw_akhir = ri2
                            if akhir2:
                                break
                            j += 1
                            continue
                        huruf.append(w2[0].upper())
                        kata_frasa.append(w2)
                        if raw_awal is None:
                            raw_awal = ri2
                        raw_akhir = ri2
                        if ''.join(huruf) != token[:len(huruf)]:
                            break
                        if akhir2 and len(huruf) < len(token):
                            break
                        if len(huruf) == len(token):
                            cocok = True
                            break
                        j += 1
                    if not cocok:
                        continue
                    # Kata isi = kata frasa di luar konektor.
                    isi = [w for w in kata_frasa
                           if w.lower() not in _KONEKTOR]
                    kapital = sum(1 for w in isi if w[0].isupper())
                    if kapital < 2:
                        continue
                    if raw_awal is None:
                        continue
                    if raw_awal == raw_akhir:
                        tampil_mentah = mentahan[raw_awal].replace(
                            '-', ' ')
                    else:
                        tampil_mentah = ' '.join(
                            mentahan[raw_awal:raw_akhir + 1])
                    tampil_mentah = tampil_mentah.strip('.,;:!?()[]{}')
                    tampil = _kepanjangan_sah(tampil_mentah)
                    if tampil is None:
                        continue
                    kunci = ' '.join(w.lower() for w in kata_frasa)
                    sudah = per_mulai.setdefault(i, set())
                    if kunci in sudah:
                        continue
                    sudah.add(kunci)
                    entri = temu.setdefault(token, {}).setdefault(
                        kunci, [{}, 0])
                    entri[0][tampil] = entri[0].get(tampil, 0) + 1
                    entri[1] += 1
        # Frasa derivasi wajib muncul minimal 2x: ciri istilah yang
        # dipakai berulang, bukan kebetulan satu kalimat (misal
        # 'Temuan Alfarizi menunjukkan' yang hanya 1x untuk TAM).
        # Bentuk tampil yang dipakai = bentuk tersering frasa itu
        # (misal 'Resource Based View' 7x menang atas bentuk hubung
        # 'Resource-Based View' 1x).
        hasil = {}
        for token, daftar in temu.items():
            terbaik = None
            for kunci, (bentuk_hitung, total) in daftar.items():
                if total < 2:
                    continue
                bentuk = max(bentuk_hitung.items(),
                             key=lambda kv: kv[1])[0]
                if terbaik is None or total > terbaik[0]:
                    terbaik = (total, bentuk)
            if terbaik is not None:
                hasil[token] = terbaik[1]
        return hasil


    # Kemunculan SAH per token (bukan hitung mentah): lewati pecahan
    # kata berhubung (SUB dalam SUB-BAB), sitasi 'et al.' (RPIR),
    # dan kata yang hanya muncul dalam runtunan 3+ kata kapital
    # (kata penanda SUB-BAB, bukan singkatan yang dipakai di prosa).
    kata_urut = [(m.start(), m.group(0)) for m in
                 re.finditer(r'[A-Za-z]+(?:-[A-Za-z]+)*', teks)]
    mulai_kata = [s for s, _ in kata_urut]
    baik = Counter()
    for m in re.finditer(r'\b[A-Z]{2,8}\b', teks):
        token = m.group(0)
        if token in _SINGKATAN_STOP or _akronim_sah(token) is None:
            continue
        if m.start() > 0 and teks[m.start() - 1] == '-':
            continue
        if m.end() < len(teks) and teks[m.end()] == '-':
            continue
        if re.match(r'\s+et al\.', teks[m.end():m.end() + 10]):
            continue
        idx = _bisect.bisect_right(mulai_kata, m.start()) - 1
        if idx >= 0:
            kiri = idx
            while kiri - 1 >= 0 and kata_urut[kiri - 1][1].isupper() \
                    and len(kata_urut[kiri - 1][1]) >= 2:
                kiri -= 1
            kanan = idx
            while kanan + 1 < len(kata_urut) \
                    and kata_urut[kanan + 1][1].isupper() \
                    and len(kata_urut[kanan + 1][1]) >= 2:
                kanan += 1
            if kanan - kiri + 1 >= 3:
                continue
            # Label huruf besar berurutan yang diakhiri titik dua
            # ('CATATAN EDITORIAL: ...') bukan singkatan yang dipakai.
            if kanan - kiri + 1 >= 2:
                akhir_run = kata_urut[kanan][0] + len(kata_urut[kanan][1])
                j = akhir_run
                while j < len(teks) and teks[j] == ' ':
                    j += 1
                if j < len(teks) and teks[j] == ':':
                    continue
        baik[token] += 1

    sing = {}
    for akr, daftar in kandidat.items():
        terverifikasi = [d for d in daftar
                         if _inisial_cocok(d[2], akr)]
        if terverifikasi:
            terverifikasi.sort()
            sing[akr] = terverifikasi[0][2]
    turunan = _turunan_inisial(set(baik))
    for akr, frasa in turunan.items():
        if akr not in sing:
            sing[akr] = frasa
    for akr, daftar in kandidat.items():
        if akr not in sing:
            daftar.sort()
            sing[akr] = daftar[0][2]
    for akr, c in baik.most_common():
        if akr in sing or akr in _SINGKATAN_STOP:
            continue
        if _akronim_sah(akr) is None:
            continue
        sing[akr] = ''
        if len(sing) >= 100:
            break
    return sing


def kumpulkan_pustaka(keluar, outline):
    """Gabung refs_bab{n}.json per bab (dedup, urut kemunculan)."""
    hasil, lihat = [], set()
    for n in sorted(k for k in outline if isinstance(k, int)):
        for cand in (os.path.join(keluar, f'bab{n}', 'visual',
                                  f'refs_bab{n}.json'),
                     os.path.join(keluar, 'visual', f'refs_bab{n}.json')):
            if not os.path.exists(cand):
                continue
            try:
                with open(cand, encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                continue
            if not isinstance(data, list):
                continue
            for entri in data:
                if isinstance(entri, str) and entri.strip() \
                        and entri not in lihat:
                    lihat.add(entri)
                    hasil.append(entri)
            break
    return hasil


def kumpulkan_nama(daftar_pustaka):
    """Kandidat surname dari string pustaka (APA maupun Nama Depan
    Nama Belakang).

    30 Okt 2026 (akar R2 job 220): versi lama mengembalikan NAMA LENGKAP
    per token ('Wan Laura Hardilawati' utuh), tapi badan hanya memuat
    surname di sitasi ('Hardilawati'), sehingga kunci lengkap tidak pernah
    cocok dan entri nama 0. Versi baru mengembalikan kata PERTAMA dan
    kata TERAKHIR tiap token penulis; pencocokan badan di isi_indeks
    menyaring kandidat yang salah (nama depan tidak muncul di sitasi,
    jadi tidak jadi entri). Posisi surname bervariasi (terakhir untuk
    Indonesia/Barat, pertama untuk Tionghoa/Slavik), jadi kedua ujung
    dikembalikan. Inisial murni dan token institusi dibuang. Urut
    kemunculan, dedup.
    """
    _INSTITUSI = {'universitas', 'institut', 'kementerian', 'badan',
                  'bank', 'perusahaan', 'pt', 'cv', 'yayasan',
                  'sekolah', 'fakultas', 'jurusan', 'program'}
    nama, lihat = [], set()

    def _tambah(kata):
        if kata and kata not in lihat:
            lihat.add(kata)
            nama.append(kata)

    def _inisial(kata):
        # True bila kata murni inisial: satu huruf, atau 2-4 huruf
        # kapital semua ('RPIR'), atau bentuk bertitik ('J.', 'J.P.').
        w = kata.replace('.', '')
        if not w:
            return True
        if len(w) == 1:
            return True
        if len(w) <= 4 and w.isupper():
            return True
        if '.' in kata and len(w) <= 2:
            return True
        return False

    for entri in (daftar_pustaka or []):
        m = re.search(r'^(.*?)\s*\(\d{4}\)', entri)
        segmen = m.group(1) if m else entri.split('(')[0]
        for tok in re.split(r',|&', segmen):
            t = tok.strip().rstrip('.')
            if not t or t.lower().startswith('et al'):
                continue
            kata = t.split()
            if not kata:
                continue
            if kata[0].lower() in _INSTITUSI:
                continue  # token institusi, bukan nama orang
            if len(kata) == 1:
                if not _inisial(kata[0]):
                    _tambah(kata[0])
                continue
            for w in (kata[0], kata[-1]):
                if not _inisial(w):
                    _tambah(w.rstrip('.'))
    return nama


def _teks_halaman_normal(teks_per_halaman):
    """Normalisasi masukan sidecar -> {nomor_halaman: teks}.

    Sidecar mengirim list (indeks 0 = halaman 1); dict diterima juga
    (kunci string JSON dinormalisasi ke int).
    """
    if isinstance(teks_per_halaman, dict):
        return {int(k): (v or '') for k, v in teks_per_halaman.items()}
    return {i + 1: (t or '') for i, t in enumerate(teks_per_halaman or [])}


def _rentang_isi(halaman):
    """(halaman_isi_awal, halaman_back_matter_awal).

    Isi mulai dari halaman pertama yang DIAWALI baris 'BAB N';
    back-matter mulai dari halaman pertama sesudahnya yang DIAWALI
    baris seksi (Glosarium/Indeks/Daftar Pustaka/dll). TOC (sebelum BAB
    pertama) otomatis di luar rentang.

    29 Okt 2026 — WAJIB baris pertama halaman, bukan baris mana saja:
    blok 'Glosarium' terdistribusi di DALAM sub-bab (judul blok di tengah
    halaman) sebelumnya disangka back-matter sehingga rentang isi
    terpotong di Bab 1-2 — istilah/nama/singkatan bab-bab akhir tidak
    pernah tercocokkan. Seksi badan akhir selalu diawali page break
    (judul di puncak halaman), sedangkan blok terdistribusi tidak.
    """
    awal, back = None, None
    for p in sorted(halaman):
        baris = [b.strip() for b in (halaman[p] or '').splitlines()
                 if b.strip()]
        if not baris:
            continue
        pertama = baris[0].upper()
        if awal is None:
            if re.match(r'^BAB \d+\b', pertama):
                awal = p
            continue
        if back is None and pertama in _SEKSI:
            back = p
    if awal is None:
        awal = min(halaman) if halaman else 1
    if back is None:
        back = (max(halaman) + 1) if halaman else awal
    return awal, back


def _halaman_cocok(halaman, isi, kunci):
    """Halaman isi tempat kunci muncul (batas kata, fallback substring).

    Teks halaman dinormalisasi (lipat whitespace jadi satu spasi) dulu:
    pdftotext memenggal nama/tabel melintasi baris ('Alexandrova\\nE.'),
    tanpa ini pencocokan batas kata gagal walau namanya ada di halaman.
    """
    def _norm(teks):
        return re.sub(r'\s+', ' ', teks or '')

    pola = re.compile(r'\b' + re.escape(kunci) + r'\b', re.IGNORECASE)
    cocok = [p for p in sorted(isi)
             if pola.search(_norm(halaman[p]))]
    if not cocok:
        kl = kunci.lower()
        cocok = [p for p in sorted(isi)
                 if kl in _norm(halaman[p]).lower()]
    return cocok


def _adalah_judul_seksi(teks):
    t = teks.strip().upper()
    return t in _SEKSI or re.match(r'^BAB \d+\b', t) is not None



def _tandai_judul_tetap(doc):
    """Set keep_with_next pada judul seksi back-matter (29 Okt 2026).

    Judul yang orphan di bawah halaman (isi di halaman berikut) adalah
    keluhan Boss di buku 219. keep_with_next = Word memindahkan judul
    bersama isi ke halaman berikut bila isi tidak muat — persis yang
    Boss minta ('judul pindah ke halaman berikutnya saja').
    Dipanggil isi_indeks + isi_singkatan sebelum save, sehingga berlaku
    apapun modul yang membuat judulnya (rakit, indeks_referensi, atau
    buat_judul fallback di sini).
    """
    for pr in doc.paragraphs:
        if pr.text.strip().upper() in ('INDEKS SUBJEK', 'INDEKS NAMA',
                                       'INDEKS', 'DAFTAR SINGKATAN'):
            pr.paragraph_format.keep_with_next = True


def isi_indeks(path_docx, teks_per_halaman, glosarium, nama_list):
    """Isi nomor halaman entri Indeks Subjek + Indeks Nama di docx.

    Entri tanpa halaman DILEWATI (indeks hanya memuat istilah yang bisa
    dilacak — entri tanpa nomor adalah indeks rusak). Seksi yang belum
    ada DIBUAT (sebelum Daftar Pustaka bila ada, else akhir dokumen).
    Mengembalikan {'subjek': n, 'nama': n, 'isi_awal': p, 'back_awal': p}.
    """
    from docx import Document
    halaman = _teks_halaman_normal(teks_per_halaman)
    awal, back = _rentang_isi(halaman)
    isi = {p: halaman[p] for p in halaman if awal <= p < back}

    entri_subjek = {}
    for istilah in (glosarium or {}):
        cocok = _halaman_cocok(halaman, isi, istilah)
        if cocok:
            entri_subjek[istilah] = cocok
    entri_nama = {}
    for nm in (nama_list or []):
        cocok = _halaman_cocok(halaman, isi, nm)
        if cocok:
            entri_nama[nm] = cocok

    doc = Document(path_docx)

    def cari_judul(predikat):
        # WAJIB baca doc.paragraphs SEGAR tiap panggilan (temuan review
        # agen 28 Okt 2026 — bug mematikan): doc.paragraphs adalah daftar
        # yang dibuat ulang tiap diakses; snapshot lama (`paras = ...`)
        # TIDAK melihat judul yang baru dibuat buat_judul() sehingga
        # cari_judul mengembalikan None -> hapus_entri_lama(None) crash.
        # Di produksi, fallback add_indeks hanya menulis 'INDEKS' (tanpa
        # 'Indeks Nama') sehingga jalur buat_judul SELALU terpicu.
        # 29 Okt 2026 — LEWATI entri Daftar Isi: TOC memakai tab + nomor
        # halaman ('Indeks\\t', 'Glosarium\\t29'); judul seksi asli TIDAK
        # pernah bertab. Tanpa ini, entri TOC 'Indeks' membayangi seksi
        # Indeks Subjek asli: entri indeks tersisip di depan (wilayah
        # TOC yang dilewati konverter) sehingga gerbang tidak melihatnya
        # dan R1 gagal walau glosarium sudah terisi.
        # 30 Okt 2026 (akar R2 job 220): cari dari AKHIR dan hanya
        # sesudah Bab terakhir. Baris badan 'Indeks' di Bab 1 (paragraf
        # 131 job 220, dari teks bab, tanpa tab) dulu dicocokkan duluan
        # oleh pencarian maju, sehingga hapus menghapus 124 paragraf
        # badan Bab 1 dan 124 entri subjek tersisip di tengah Bab 1,
        # sementara seksi indeks asli tidak pernah disentuh. Seksi back
        # matter selalu sesudah Bab terakhir; pencarian mundur menemukan
        # judul asli duluan. Filter tab (TOC) tetap berlaku. Paras dibaca
        # segar tiap panggilan (doc.paragraphs dibuat ulang tiap akses).
        paras = doc.paragraphs
        mulai = 0
        for _i, _pr in enumerate(paras):
            if re.match(r'^BAB \d+\b', _pr.text.strip().upper()):
                mulai = _i + 1
        for idx in range(len(paras) - 1, mulai - 1, -1):
            pr = paras[idx]
            if '\t' in pr.text:
                continue
            if predikat(pr.text.strip().upper()):
                return idx
        return None

    idx_subjek = cari_judul(lambda t: t in ('INDEKS SUBJEK', 'INDEKS'))
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')

    def hapus_entri_lama(idx_judul):
        """Hapus paragraf sesudah judul sampai seksi berikut/akhir."""
        if idx_judul is None:
            return  # tidak ada judul = tidak ada entri lama untuk dihapus
        j = idx_judul + 1
        while j < len(doc.paragraphs):
            if _adalah_judul_seksi(doc.paragraphs[j].text):
                break
            p_el = doc.paragraphs[j]._p
            p_el.getparent().remove(p_el)
            # Indeks bergeser: paragraf berikutnya menempati posisi j.
        # (loop tanpa j += 1 sengaja — penghapusan menggeser sisanya)

    def sisipkan_entri(idx_judul, entri):
        """Sisipkan baris 'Istilah .... 3, 7' sesudah judul, urut."""
        if idx_judul is None:
            # Jangan pernah crash TypeError samar: judul hilang = gagal
            # jelas, pemanggil (susun) menggagalkan buku + refund token.
            raise RuntimeError('judul seksi indeks tidak ditemukan')
        anchor = doc.paragraphs[idx_judul]._p
        # 29 Okt 2026 (keluhan Boss di buku 219: indeks berantakan):
        # URUTAN sudah benar (key=str.lower, 0 inversi di 219) — dipertahankan.
        # FORMAT: titik literal '....' diganti tab leader Word (titik mengisi
        # sampai margin, nomor rata kanan — rapi seperti indeks cetak).
        # BATAS: maks 10 halaman pertama per entri (urutan halaman =
        # pembahasan awal/definisi dulu). Tanpa batas, 'UMKM' 188 halaman
        # dan 'Literasi digital' 162 halaman — tidak bisa dipakai.
        from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
        _seksi = doc.sections[0]
        _tab_pos = _seksi.page_width - _seksi.left_margin - _seksi.right_margin
        for istilah in sorted(entri, key=str.lower):
            halaman_str = ', '.join(str(p) for p in entri[istilah][:10])
            pr = doc.add_paragraph()
            pr.paragraph_format.tab_stops.add_tab_stop(
                _tab_pos, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            _r1 = pr.add_run(istilah)
            _r1.add_tab()
            pr.add_run(halaman_str)
            anchor.addnext(pr._p)
            anchor = pr._p

    def buat_judul(judul, sebelum_idx=None):
        pr = doc.add_paragraph()
        run = pr.add_run(judul)
        run.bold = True
        if sebelum_idx is not None:
            target = doc.paragraphs[sebelum_idx]._p
            target.addprevious(pr._p)
            # Indeks paragraf bergeser; hitung ulang posisi judul baru.
            for idx, pp in enumerate(doc.paragraphs):
                if pp._p is pr._p:
                    return idx
        return len(doc.paragraphs) - 1

    if idx_subjek is None:
        idx_subjek = buat_judul('Indeks Subjek',
                                sebelum_idx=idx_pustaka)
        # Posisi lain bergeser setelah penyisipan — hitung ulang.
        idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
        idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')
    if idx_nama is None:
        # Indeks Nama sesudah Indeks Subjek (atau sebelum Pustaka).
        idx_nama = buat_judul(
            'Indeks Nama',
            sebelum_idx=idx_pustaka if idx_pustaka is not None
            and idx_pustaka > idx_subjek else None)
        idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')

    hapus_entri_lama(idx_subjek)
    # Indeks nama bergeser oleh penghapusan — hitung ulang.
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    hapus_entri_lama(idx_nama)
    idx_subjek = cari_judul(lambda t: t in ('INDEKS SUBJEK', 'INDEKS'))
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    sisipkan_entri(idx_subjek, entri_subjek)
    # Geseran: sisipan subjek menggeser semua paragraf sesudahnya.
    # Hitung ulang posisi judul nama SEBELUM menyisipkan entri nama
    # (tanpa ini entri nama tersisip di bawah entri subjek pertama).
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    sisipkan_entri(idx_nama, entri_nama)
    _tandai_judul_tetap(doc)
    doc.save(path_docx)
    return {'subjek': len(entri_subjek), 'nama': len(entri_nama),
            'isi_awal': awal, 'back_awal': back}


def isi_singkatan(path_docx, teks_per_halaman, singkatan):
    """Tulis seksi Daftar Singkatan bernomor halaman di docx.

    Entri: 'SINGKATAN — Kepanjangan .... hal' (halaman kemunculan
    PERTAMA di isi; tanpa kepanjangan: 'SINGKATAN .... hal'). Entri
    tanpa halaman DILEWATI (prinsip yang sama dengan isi_indeks).
    Seksi yang belum ada DIBUAT sebelum Daftar Pustaka bila ada, else
    akhir dokumen. Bila tidak ada entri, docx TIDAK disentuh.
    Mengembalikan jumlah entri yang ditulis.
    """
    from docx import Document
    halaman = _teks_halaman_normal(teks_per_halaman)
    awal, back = _rentang_isi(halaman)
    isi = {p: halaman[p] for p in halaman if awal <= p < back}

    entri = {}
    for sing, kep in (singkatan or {}).items():
        cocok = _halaman_cocok(halaman, isi, sing)
        if cocok:
            entri[sing] = (kep, cocok[0])
    if not entri:
        return 0

    doc = Document(path_docx)

    def cari_judul(predikat):
        # Sama seperti isi_indeks: paragraf segar tiap panggilan, dan
        # LEWATI entri Daftar Isi (bertab) supaya tidak membayangi
        # seksi asli di badan akhir.
        # 30 Okt 2026 (akar R2 job 220): cari dari AKHIR dan hanya
        # sesudah Bab terakhir. Baris badan 'Indeks' di Bab 1 (paragraf
        # 131 job 220, dari teks bab, tanpa tab) dulu dicocokkan duluan
        # oleh pencarian maju, sehingga hapus menghapus 124 paragraf
        # badan Bab 1 dan 124 entri subjek tersisip di tengah Bab 1,
        # sementara seksi indeks asli tidak pernah disentuh. Seksi back
        # matter selalu sesudah Bab terakhir; pencarian mundur menemukan
        # judul asli duluan. Filter tab (TOC) tetap berlaku. Paras dibaca
        # segar tiap panggilan (doc.paragraphs dibuat ulang tiap akses).
        paras = doc.paragraphs
        mulai = 0
        for _i, _pr in enumerate(paras):
            if re.match(r'^BAB \d+\b', _pr.text.strip().upper()):
                mulai = _i + 1
        for idx in range(len(paras) - 1, mulai - 1, -1):
            pr = paras[idx]
            if '\t' in pr.text:
                continue
            if predikat(pr.text.strip().upper()):
                return idx
        return None

    def hapus_entri_lama(idx_judul):
        if idx_judul is None:
            return
        j = idx_judul + 1
        while j < len(doc.paragraphs):
            if _adalah_judul_seksi(doc.paragraphs[j].text):
                break
            p_el = doc.paragraphs[j]._p
            p_el.getparent().remove(p_el)

    def sisipkan_entri(idx_judul):
        if idx_judul is None:
            raise RuntimeError('judul seksi singkatan tidak ditemukan')
        anchor = doc.paragraphs[idx_judul]._p
        for sing in sorted(entri, key=str.lower):
            kep, hal = entri[sing]
            baris = (f'{sing} — {kep} .... {hal}' if kep
                     else f'{sing} .... {hal}')
            pr = doc.add_paragraph()
            pr.add_run(baris)
            anchor.addnext(pr._p)
            anchor = pr._p

    def buat_judul(judul, sebelum_idx=None):
        pr = doc.add_paragraph()
        run = pr.add_run(judul)
        run.bold = True
        if sebelum_idx is not None:
            target = doc.paragraphs[sebelum_idx]._p
            target.addprevious(pr._p)
            for idx, pp in enumerate(doc.paragraphs):
                if pp._p is pr._p:
                    return idx
        return len(doc.paragraphs) - 1

    idx_sing = cari_judul(lambda t: t == 'DAFTAR SINGKATAN')
    idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')
    if idx_sing is None:
        idx_sing = buat_judul('Daftar Singkatan',
                              sebelum_idx=idx_pustaka)
    hapus_entri_lama(idx_sing)
    idx_sing = cari_judul(lambda t: t == 'DAFTAR SINGKATAN')
    sisipkan_entri(idx_sing)
    _tandai_judul_tetap(doc)
    doc.save(path_docx)
    return len(entri)
