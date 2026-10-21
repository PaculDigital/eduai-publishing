"""GERBANG BESAR + 4 LANGKAH AWAL (ACC Bos 26Sep26).

=== KENAPA MODUL INI ADA ===
User masuk aplikasi dengan DUA kemungkinan yang sangat berbeda:
   A. BELUM punya apa-apa  → harus dibimbing dari nol
   B. SUDAH punya naskah   → jangan diminta mulai dari nol (nanti dia
                             kecewa/berhenti karena kerjanya diulang)

Kalau salah tebak, akibatnya BESAR: user yang sudah punya BAB I-III
diminta mengisi identitas & judul lagi = merasa aplikasi tidak mengerti
dia. Sebaliknya, user baru yang dipaksa mengunggah berkas = bingung.

Karena itu ada 3 PAGAR anti-salah-deteksi:
   P1. Pilihan user SAJA tidak cukup  → tetap tanya kalau tidak ada isi
   P2. Berkas SAJA tidak cukup        → tetap tanya niatnya apa
   P3. BACA ISI naskah                → tampilkan hasil deteksi → KONFIRMASI

=== PRINSIP (aturan Bos) ===
· SIMPLE — sedikit pertanyaan, tidak bikin bingung.
· LOGO belum ada → BOLEH DILEWATI, upload lain waktu, sistem tetap jalan.
· Jenjang/bidang/jenis WAJIB (supaya AI tidak salah arah), judul ikut.
· JANGAN bikin mesin baru kalau yang ada cukup:
      `app/jenis.py`  → 6 jenis dokumen + deteksi_struktur()
      `app/state.py`  → deteksi_bab_besar() + deteksi_subbab()
      `ProfilDokumen.sumber` ('unggah' | 'buat_baru') → SUDAH ADA
"""
from __future__ import annotations

import re
from typing import Any

# ══════════════════════════════════════════════════════════════════════════
# 8 BIDANG STUDI (putusan Bos 26Sep26 — 8 + "Lainnya")
#
# PERAN BIDANG (putusan ⑤): HANYA memberi CONTOH JUDUL + TEMA + ISTILAH.
# TIDAK mengubah kerangka (kerangka TETAP 5 bab). Jangan diperluas jadi
# daftar jurusan — cukup 8 ini supaya user tidak bingung memilih.
# ══════════════════════════════════════════════════════════════════════════
BIDANG: dict[str, dict[str, Any]] = {
    'manajemen': {
        'label': 'Manajemen & Bisnis',
        'istilah': ['kinerja karyawan', 'kepuasan pelanggan', 'keputusan '
                    'pembelian', 'keunggulan bersaing', 'strategi pemasaran'],
        'contoh': [
            'Pengaruh Kualitas Produk dan Harga terhadap Keputusan Pembelian',
            'Pengaruh Gaya Kepemimpinan terhadap Kinerja Karyawan',
            'Pengaruh Digital Marketing terhadap Minat Beli Konsumen',
        ],
    },
    'akuntansi': {
        'label': 'Akuntansi & Keuangan',
        'istilah': ['kepatuhan pajak', 'audit internal', 'profitabilitas',
                    'manajemen laba', 'kualitas laporan keuangan'],
        'contoh': [
            'Pengaruh Profitabilitas terhadap Nilai Perusahaan',
            'Faktor yang Mempengaruhi Kepatuhan Wajib Pajak',
            'Pengaruh Ukuran Perusahaan terhadap Manajemen Laba',
        ],
    },
    'teknik': {
        'label': 'Teknik & Teknologi',
        'istilah': ['efisiensi sistem', 'kualitas layanan digital', 'keamanan '
                    'informasi', 'adopsi teknologi', 'otomatisasi proses'],
        'contoh': [
            'Analisis Efisiensi Sistem Informasi pada Pelayanan Publik',
            'Faktor yang Mempengaruhi Adopsi Teknologi IoT di Industri',
            'Perancangan Sistem Monitoring Berbasis IoT',
        ],
    },
    'pertanian': {
        'label': 'Pertanian & Lingkungan',
        'istilah': ['produktivitas lahan', 'ketahanan pangan', 'konservasi',
                    'pengelolaan limbah', 'kesuburan tanah'],
        'contoh': [
            'Pengaruh Pupuk Organik terhadap Produktivitas Tanaman Padi',
            'Analisis Strategi Ketahanan Pangan Rumah Tangga Tani',
            'Pengelolaan Limbah Pertanian Menjadi Pupuk Kompos',
        ],
    },
    'pendidikan': {
        'label': 'Pendidikan',
        'istilah': ['hasil belajar', 'motivasi belajar', 'media '
                    'pembelajaran', 'minat belajar', 'kompetensi guru'],
        'contoh': [
            'Pengaruh Media Pembelajaran terhadap Hasil Belajar Siswa',
            'Pengaruh Motivasi Belajar terhadap Prestasi Akademik',
            'Analisis Kompetensi Guru dalam Implementasi Kurikulum',
        ],
    },
    'kesehatan': {
        'label': 'Kesehatan',
        'istilah': ['tingkat kepatuhan', 'kualitas pelayanan', 'status gizi',
                    'efektivitas terapi', 'perilaku hidup bersih'],
        'contoh': [
            'Pengaruh Kualitas Pelayanan terhadap Kepuasan Pasien',
            'Faktor yang Mempengaruhi Kepatuhan Minum Obat Pasien',
            'Hubungan Status Gizi dengan Prestasi Belajar Anak',
        ],
    },
    'hukum': {
        'label': 'Hukum & Sosial',
        'istilah': ['penegakan hukum', 'perlindungan konsumen', 'peran '
                    'kelembagaan', 'partisipasi masyarakat', 'efektivitas '
                    'regulasi'],
        'contoh': [
            'Efektivitas Penegakan Hukum terhadap Pelanggaran Lalu Lintas',
            'Perlindungan Hukum bagi Konsumen Marketplace',
            'Peran Kelembagaan Adat dalam Penyelesaian Sengketa',
        ],
    },
    'ekonomi': {
        'label': 'Ekonomi Pembangunan',
        'istilah': ['pertumbuhan ekonomi', 'tingkat pengangguran', 'kemiskinan',
                    'investasi daerah', 'pendapatan asli daerah'],
        'contoh': [
            'Pengaruh Investasi terhadap Pertumbuhan Ekonomi Daerah',
            'Analisis Faktor yang Mempengaruhi Tingkat Kemiskinan',
            'Pengaruh Tingkat Pengangguran terhadap Kemiskinan',
        ],
    },
    'lainnya': {
        'label': 'Bidang Lain',
        'istilah': [],
        'contoh': [],
    },
}

# ══════════════════════════════════════════════════════════════════════════
# 2 JENIS PENELITIAN (putusan ③⑦ — KUALITATIF nanti, tapi pintunya dibuka)
# ══════════════════════════════════════════════════════════════════════════
JENIS_PENELITIAN = {
    'kuantitatif': {
        'label': 'Kuantitatif (pakai angka & data statistik)',
        'ciri': ('mengukur pengaruh/hubungan antar variabel, memakai angka, '
                 'kuesioner, jumlah sampel, uji hipotesis'),
        'bab4': 'Hasil pengujian hipotesis (uji statistik) & pembahasan',
        'siap': True,
    },
    'kualitatif': {
        'label': 'Kualitatif (pakai wawancara & cerita/kejadian)',
        'ciri': ('menggali makna/pengalaman lewat wawancara, observasi, '
                 'dokumen; tidak memakai uji angka'),
        'bab4': 'Temuan tema-tema (narasi, kutipan wawancara) & pembahasan',
        'siap': False,          # putusan ⑦: dikerjakan NANTI
    },
}

# ══════════════════════════════════════════════════════════════════════════
# 4 LANGKAH (putusan ②③⑥ — jenjang → bidang → jenis → judul)
# ══════════════════════════════════════════════════════════════════════════
LANGKAH = [
    {'id': 'jenjang', 'nomor': 1, 'judul': 'Jenjang naskahmu?',
     'tanya': 'Ini untuk skripsi, tesis, atau disertasi?',
     'wajib': True},
    {'id': 'bidang', 'nomor': 2, 'judul': 'Bidang studimu?',
     'tanya': 'Pilih bidang yang paling dekat. Ini hanya untuk '
              'menyesuaikan contoh judul & istilah.',
     'wajib': True},
    {'id': 'jenis', 'nomor': 3, 'judul': 'Penelitianmu pakai angka?',
     'tanya': 'Kuantitatif (angka/kuesioner) atau kualitatif '
              '(wawancara/cerita)?',
     'wajib': True},
    {'id': 'judul', 'nomor': 4, 'judul': 'Judul penelitianmu?',
     'tanya': 'Tulis judulmu, atau pilih salah satu contoh di bawah.',
     'wajib': True},
]


# ══════════════════════════════════════════════════════════════════════════
#  PAGAR P1-P3 — DETEKSI JALUR: MULAI BARU vs LANJUTKAN
# ══════════════════════════════════════════════════════════════════════════
def petakan_jalur(pilihan: str | None,
                  ada_berkas: bool = False,
                  teks: str | None = None,
                  konfirmasi: bool | None = None) -> dict[str, Any]:
    """Tentukan jalur awal: 'baru' atau 'lanjut'.

    PAGAR (semua harus dilewati — tidak boleh salah tebak):
      P1. Pilihan 'lanjut' TANPA berkas → TANYA (jangan diamkan).
      P2. Ada berkas TAPI pilihan 'baru' → TANYA niatnya (contoh/rujukan?).
      P3. Ada ISI naskah → BACA, tampilkan hasil deteksi, minta konfirmasi.

    Balasan selalu berbentuk sama (supaya layar tidak perlu nebak):
      {'jalur': 'baru'|'lanjut'|None, 'tanya': str|None,
       'deteksi': {...}|None, 'pesan': str}
    """
    p = (pilihan or '').strip().lower()
    ada_isi = bool((teks or '').strip())

    # ── P1: minta lanjut tapi tidak ada berkas & tidak ada teks ────────
    if p == 'lanjut' and not ada_berkas and not ada_isi:
        return {
            'jalur': None,
            'tanya': 'unggah',
            'deteksi': None,
            'pesan': ('Baik, naskah yang mau dilanjutkan mana? Unggah '
                      'berkasnya (Word/PDF), nanti Wulan periksa sudah '
                      'sampai bagian mana. Kalau belum ada berkasnya, '
                      'pilih "Mulai baru" saja — bisa diisi nanti.'),
        }

    # ── P2: ada berkas tapi bilang "mulai baru" ───────────────────────
    if p == 'baru' and (ada_berkas or ada_isi):
        return {
            'jalur': None,
            'tanya': 'maksud_berkas',
            'deteksi': None,
            'pesan': ('Wulan lihat ada naskah yang diunggah, tapi kamu pilih '
                      '"Mulai baru". Naskah itu mau dipakai sebagai apa?'),
        }

    # ── P3: ada ISI → deteksi dulu, JANGAN langsung lanjut ────────────
    if ada_isi and konfirmasi is None:
        det = deteksi_isi(teks or '')
        return {
            'jalur': None,
            'tanya': 'konfirmasi',
            'deteksi': det,
            'pesan': det.get('ringkas') or '',
        }

    # ── user SUDAH konfirmasi hasil deteksi ───────────────────────────
    if konfirmasi is True:
        return {'jalur': 'lanjut', 'tanya': None, 'deteksi': deteksi_isi(teks or ''),
                'pesan': 'Siap, Wulan lanjutkan dari bagian yang belum ada.'}

    # ── user bilang deteksi SALAH → ke jalur baru (tanpa buang naskah) ─
    if konfirmasi is False:
        return {'jalur': 'baru', 'tanya': None, 'deteksi': None,
                'pesan': ('Tidak masalah. Kita mulai dari awal, dan naskah '
                          'yang tadi tetap tersimpan sebagai bahan.')}

    # ── MULAI BARU (bersih) ───────────────────────────────────────────
    if p == 'baru':
        return {'jalur': 'baru', 'tanya': None, 'deteksi': None,
                'pesan': 'Baik, kita mulai dari langkah pertama.'}

    # ── belum memilih apa-apa ─────────────────────────────────────────
    return {
        'jalur': None,
        'tanya': 'pintu',
        'deteksi': None,
        'pesan': ('Kamu sudah punya naskah yang mau dilanjutkan, atau mau '
                  'mulai dari nol?'),
    }


# ══════════════════════════════════════════════════════════════════════════
#  BACA ISI → APA YANG DIMILIKI USER (P3)
# ══════════════════════════════════════════════════════════════════════════
_BAB_POLA = re.compile(
    r'\bBAB\s+(I{1,3}V?|IV|V|VI)\b', re.IGNORECASE)


def deteksi_isi(teks: str, nama_berkas: str = '') -> dict[str, Any]:
    """Baca naskah user → jenis dokumen, bab yang sudah ada, jenis penelitian.

    Memakai mesin yang SUDAH ADA (`app/jenis.py`) — tidak menebak sendiri.
    Kalau ragu → katakan ragu (putusan ⑧: jangan tebak).

    ⚠️ JEBAKAN TERUKUR (26Sep26): `jenis.deteksi_struktur()` membalas
       TUPLE `(kategori, alasan)` — BUKAN dict. Wulan salah baca
       `.get('jenis')` → kosong. Yang benar: panggil `jenis.deteksi()`
       yang membalas objek `HasilDeteksi` dengan `.jenis`, `.label`,
       `.jenis` (+ `.yakin`, `.jenjang`).
    """
    teks = teks or ''
    bab_ada: list[str] = []
    for m in _BAB_POLA.finditer(teks):
        kode = m.group(1).upper().replace('IIII', 'III')
        if kode not in bab_ada:
            bab_ada.append(kode)
    # urutkan sesuai urutan bab yang wajar
    urut = ['I', 'II', 'III', 'IV', 'V', 'VI']
    bab_ada = [b for b in urut if b in bab_ada]

    # ── jenis dokumen: pakai mesin `app/jenis.py` (jangan bikin baru) ──
    #    `deteksi()` = pintu yang benar (balas objek HasilDeteksi).
    jenis = ''
    label_jenis = ''
    jenjang_resmi = ''
    ragu = False
    try:
        from . import jenis as _j
        h = _j.deteksi(teks, nama_berkas)
        jenis = getattr(h, 'jenis', '') or ''
        label_jenis = getattr(h, 'label', '') or ''
        jenjang_resmi = getattr(h, 'jenjang', '') or ''
        # `yakin=False` → mesin sendiri bilang RAGU → jangan tebak
        ragu = not bool(getattr(h, 'yakin', False))
    except Exception:
        pass

    # ── jenis penelitian: ciri angka vs cerita ──────────────────────────
    jenis_pen = ''
    try:
        _angka = ('signifikan', 'hipotesis', 'kuesioner', 'responden',
                  'regresi', 'korelasi', 'uji t', 'anova', 'sampel')
        _kata = ('wawancara', 'informan', 'observasi', 'fenomenologi',
                 'etnografi', 'studi kasus', 'triangulasi', 'naratif')
        _t = teks.lower()
        skor_a = sum(1 for k in _angka if k in _t)
        skor_k = sum(1 for k in _kata if k in _t)
        if skor_a > skor_k:
            jenis_pen = 'kuantitatif'
        elif skor_k > skor_a:
            jenis_pen = 'kualitatif'
    except Exception:
        pass

    # ── susun kalimat ramah (yang dibaca user di layar) ─────────────────
    bagian = []
    if label_jenis:
        bagian.append(label_jenis)
    if jenis_pen:
        bagian.append(JENIS_PENELITIAN[jenis_pen]['label'].split(' (')[0])
    posisi = ''
    if bab_ada:
        posisi = 'sudah ada BAB ' + ', '.join(bab_ada)
        if 'V' in bab_ada:
            posisi += ' (naskah sudah lengkap)'
    elif teks.strip():
        posisi = ('belum terlihat penomoran BAB — mungkin naskah masih '
                  'berupa draf atau artikel')

    # 11Okt26: `bagian` (jenis + jenis penelitian) DIKELUARKAN dari kalimat ini
    # — baris di atasnya di layar (`det-ringkas`) SUDAH menampilkannya ⇒ kalau
    # ikut di sini, terbaca DUA KALI. Kalimat ini = peta bab saja.
    kalimat = ' · '.join([x for x in [posisi] if x])
    ringkas = ''
    if kalimat:
        # 11Okt26: kalimat ini HANYA soal peta bab. Awalan "Terdeteksi:"
        # SUDAH dipakai baris di atasnya (`det-ringkas`) ⇒ jangan diulang.
        # Kata ragu dibuang; `ragu` tetap dipakai supaya tidak berpura-pura
        # yakin saat mesin sendiri bilang ragu.
        akhir = ' Mohon dipastikan.' if ragu else ''
        ringkas = f'{kalimat}.{akhir}'

    return {
        'jenis': jenis,
        'label_jenis': label_jenis,
        'jenjang': jenjang_resmi,
        'ragu': ragu,
        'jenis_penelitian': jenis_pen,
        'bab_ada': bab_ada,
        'sudah_lengkap': 'V' in bab_ada,
        'jumlah_karakter': len(teks.strip()),
        'ringkas': ringkas,
    }


# ══════════════════════════════════════════════════════════════════════════
#  4 LANGKAH — LANGKAH MANA BERIKUTNYA (layar tidak perlu menebak)
# ══════════════════════════════════════════════════════════════════════════
def langkah_berikut(data: dict[str, Any] | None) -> dict[str, Any]:
    """Tentukan langkah mana yang belum lengkap + pertanyaannya.

    SIMPLE (aturan Bos): pertanyaan satu-satu, tidak menumpuk.
    """
    d = data or {}
    if not d.get('jenjang'):
        return {'langkah': 'jenjang', 'nomor': 1,
                'tanya': LANGKAH[0]['tanya'], 'selesai': False}
    if not d.get('bidang'):
        return {'langkah': 'bidang', 'nomor': 2,
                'tanya': LANGKAH[1]['tanya'], 'selesai': False,
                'pilihan': [{'kode': k, 'label': v['label']}
                            for k, v in BIDANG.items()]}
    if not d.get('mode_penelitian'):
        return {'langkah': 'jenis', 'nomor': 3,
                'tanya': LANGKAH[2]['tanya'], 'selesai': False,
                'pilihan': [{'kode': k, 'label': v['label'],
                             'siap': v['siap']}
                            for k, v in JENIS_PENELITIAN.items()]}
    if not (d.get('judul') or '').strip():
        return {'langkah': 'judul', 'nomor': 4,
                'tanya': LANGKAH[3]['tanya'], 'selesai': False,
                'contoh': contoh_judul(d.get('bidang') or '',
                                       d.get('mode_penelitian') or '')}
    return {'langkah': None, 'nomor': 5, 'tanya': None, 'selesai': True,
            'pesan': ('Semua langkah awal sudah lengkap. Selanjutnya EduAi '
                      'susun kerangka BAB I untukmu.')}


def contoh_judul(bidang: str, mode: str = 'kuantitatif') -> list[str]:
    """3-5 contoh judul sesuai bidang (putusan ④).

    Bidang hanya memberi CONTOH (putusan ⑤) — bukan mengunci arah.
    Kalau bidang tidak dikenal → kembalikan daftar kosong (layar
    menyembunyikan bagian contoh, sistem tetap jalan).
    """
    b = BIDANG.get((bidang or '').strip().lower())
    if not b:
        return []
    return list(b.get('contoh') or [])


def daftar_bidang() -> list[dict[str, str]]:
    """Daftar 8 bidang untuk layar (label saja, urut sesuai BIDANG)."""
    return [{'kode': k, 'label': v['label']} for k, v in BIDANG.items()]


def daftar_jenjang() -> list[dict[str, str]]:
    """6 jenis dokumen dari `app/jenis.py` — JANGAN bikin daftar kedua."""
    try:
        from . import jenis as _j
        return [{'kode': k, 'label': v} for k, v in _j.LABEL_JENIS.items()]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════
#  IDENTITAS COVER — APA YANG WAJIB, APA YANG BOLEH DILEWATI
# ══════════════════════════════════════════════════════════════════════════
IDENTITAS_WAJIB = ('nama_lengkap', 'nim', 'nama_kampus')
IDENTITAS_OPSIONAL = ('kota_kampus', 'fakultas', 'program_studi',
                      'berkas_logo_id', 'pembimbing_1', 'pembimbing_2')

LABEL_IDENTITAS = {
    'nama_lengkap': 'Nama Lengkap',
    'nim': 'NIM',
    'nama_kampus': 'Nama Kampus',
    'kota_kampus': 'Kota Kampus',
    'fakultas': 'Fakultas',
    'program_studi': 'Program Studi',
    'berkas_logo_id': 'Logo Kampus',
    'pembimbing_1': 'Pembimbing 1',
    'pembimbing_2': 'Pembimbing 2',
}


def periksa_identitas(data: dict[str, Any] | None) -> dict[str, Any]:
    """Cek identitas cover. LOGO TIDAK WAJIB (aturan Bos: boleh dilewati).

    Balasan: {'lengkap': bool, 'kurang': [...], 'pesan': str,
              'boleh_lanjut': bool}
    ⇒ selalu `boleh_lanjut = True` kalau yang wajib saja sudah terisi,
      meski logo belum ada (sistem tetap jalan).
    """
    d = data or {}
    kurang = [k for k in IDENTITAS_WAJIB if not str(d.get(k) or '').strip()]
    belum_opsional = [k for k in IDENTITAS_OPSIONAL
                      if not d.get(k)]
    lengkap = not kurang

    if lengkap and belum_opsional:
        pesan = ('Identitas inti sudah lengkap. Yang belum ada: ' +
                 ', '.join(LABEL_IDENTITAS[k] for k in belum_opsional) +
                 ' — boleh diisi nanti, sistem tetap bisa jalan.')
    elif lengkap:
        pesan = 'Identitas sudah lengkap.'
    else:
        pesan = ('Masih perlu: ' +
                 ', '.join(LABEL_IDENTITAS[k] for k in kurang) + '.')

    return {
        'lengkap': lengkap,
        'kurang': kurang,
        'belum_opsional': belum_opsional,
        'boleh_lanjut': lengkap,        # logo TIDAK menghalangi
        'pesan': pesan,
    }
