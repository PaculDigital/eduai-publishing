"""KERANGKA PER BAB — TAHAP 1 (tanya) + TAHAP 2 (rencana) — 26Sep26.

📌 ARAHAN BOS (verbatim):
   "kerangka per bab saja, tidak seluruhnya bab I sampai Bab v, itu
    namanya buat utuh tidak boleh. Harus melalui progress agar mahasiswa
    paham. Kenapa 15 token kredit bab I karena kita juga mencari sitasi
    dan artikel uang sesuai tema dan judul penelitian. Dan juga termasuk
    buat grafik dan tabel di dalamnya"

📌 PUTUSAN BOS (26Sep26, 5 butir — TERKUNCI):
   Q1. Panjang      = 5 sub-bab · 3-5 poin tiap sub-bab
   Q2. Masuk naskah = panel rencana DULU → [Masukkan ke naskah]
   Q3. Artikel <5   = jujur + 3 pilihan (ubah kk / lanjut / batal)
   Q4. Bab dulu     = BAB I saja
   Q5. Gagal        = token kembali + lonceng (pola tandai_gagal() SUDAH ADA)

📌 BERKAS INI HANYA MENGERJAKAN TAHAP 1 & 2 (GRATIS — 0 token).
   TAHAP 3 (potong token) dibangun setelah ini terbukti di uji nyata.

📌 PAGAR YANG DIJAGA BERKAS INI:
   P1. Fungsi di sini TIDAK memotong token sama sekali.
   P4. `tolak_buat_utuh()` MENOLAK permintaan bab I–V sekaligus.
   P5. Jenis dokumen ragu → tanya user (aturan Lapis 1).
   P3. Sitasi WAJIB dari app/pustaka.py (audit DOI), DILARANG dikarang.
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger('eduai.kerangka')

#  ── Panjang kerangka (putusan Bos Q1) ──
SUBBAB_PER_BAB = 5          # pola umum: 5 sub-bab (putusan Bos Q1)
POIN_MIN = 3
POIN_MAKS = 5

#  ── Ambang artikel sedikit (putusan Bos Q3) ──
ARTIKEL_MIN = 5

#  ── Pola permintaan "buat utuh" yang WAJIB DITOLAK (pagar P4) ──
_POLA_UTUH = [
    r'bab\s*(i|1)\s*(sampai|sd|hingga|s/d|s\.d\.?|-)\s*(bab\s*)?(v|5|lima)',
    r'bab\s*(1|i)\s*[-–~]\s*(5|v)\b',
    r'(seluruh|semua|keseluruhan)\s+(bab|dokumen|skripsi|tesis)',
    r'bab\s*1\s*,\s*2\s*,\s*3',
    r'buat\s+(semua|seluruh)\s+bab',
    r'bab\s+i\s+sd\s+v',
]

#  ── Pola permintaan KERANGKA (yang dilayani) ──
_POLA_KERANGKA = [
    r'\b(kerangka|outline|kerangka\s+bab)\b',
    r'\bbuat(kan)?\s+bab\s+(i|1|ii|2|iii|3|iv|4|v|5)\b',
    r'\bsusun\s+bab\s+(i|1|ii|2|iii|3|iv|4|v|5)\b',
    r'\b(buat|susun)\s+kerangka\b',
]

#  ── Jenis dokumen yang DIKENALI (Lapis 1) ──
JENIS_DOKUMEN = {
    'skripsi': 'Skripsi (S1)',
    'tesis': 'Tesis (S2)',
    'disertasi': 'Disertasi (S3)',
    'artikel_jurnal': 'Artikel Jurnal',
    'proposal': 'Proposal Penelitian',
    'dokumen_umum': 'Dokumen Umum (non-akademik)',
}

def tolak_buat_utuh(permintaan: str) -> dict | None:
    """PAGAR P4 — tolak permintaan "buat utuh" bab I–V sekaligus.

    Return dict (kalau DITOLAK) atau None (kalau permintaan wajar).
    """
    t = (permintaan or '').lower()
    for pola in _POLA_UTUH:
        if re.search(pola, t):
            log.info('[kerangka] TOLAK buat-utuh: %r cocok %r', permintaan, pola)
            return {
                'ok': False,
                'kode': 'tolak_buat_utuh',
                'pesan': ('Kerangka dibuat PER BAB, satu bab satu kali, supaya '
                          'kamu paham alurnya. Ini juga membuat hasilnya lebih '
                          'teliti dan bisa kamu koreksi di tengah jalan.'),
                'saran': ('Mulai dari BAB I dulu ya. Setelah kamu pelajari dan '
                          'setujui, kita lanjut ke BAB II — begitu seterusnya. '
                          'Kalau memang perlu MEROMBA seluruh dokumen '
                          '(mis. ganti metode atau ubah alur penelitian), itu '
                          'jalur lain, bukan jalur kerangka bab.'),
            }
    return None


def deteksi_niat(permintaan: str) -> dict:
    """Apakah pesan user meminta KERANGKA (bukan revisi biasa)?

    Return {'kerangka': bool, 'bab': '1'/'' , 'alasan': str}
    """
    t = (permintaan or '').lower()
    utuh = tolak_buat_utuh(permintaan)
    if utuh:
        return {'kerangka': False, 'bab': '', 'tolak_utuh': utuh,
                'alasan': 'minta buat utuh (ditolak)'}
    for pola in _POLA_KERANGKA:
        if re.search(pola, t):
            m = re.search(r'bab\s*(i{1,3}v?|iv|v|1|2|3|4|5)\b', t)
            bab = ''
            if m:
                peta = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
                        '1': '1', '2': '2', '3': '3', '4': '4', '5': '5'}
                bab = peta.get(m.group(1), '')
            return {'kerangka': True, 'bab': bab or '1',
                    'alasan': f'cocok pola {pola!r}'}
    return {'kerangka': False, 'bab': '', 'alasan': 'bukan permintaan kerangka'}


def perlu_tanya(jenis_dok: str, judul: str, jenis_penelitian: str = '') -> dict:
    """TAHAP 1 — apakah AI perlu bertanya dulu? (GRATIS, tanpa AI).

    Sesuai aturan Lapis 1: kalau ragu → TANYA (jangan menebak), karena
    salah jenjang = naskah rusak.
    """
    kurang = []
    if not (jenis_dok or '').strip():
        kurang.append('jenis_dokumen')
    if not (judul or '').strip():
        kurang.append('judul')
    if not (jenis_penelitian or '').strip():
        kurang.append('jenis_penelitian')

    pertanyaan = {
        'jenis_dokumen': {
            'tanya': 'Karya ini untuk jenjang apa?',
            'pilihan': list(JENIS_DOKUMEN.values()),
            'kenapa': ('Standar penulisan tiap jenjang berbeda — kalau salah, '
                       'hasilnya tidak sesuai kaidah.'),
        },
        'jenis_penelitian': {
            'tanya': 'Penelitiannya pendekatan kuantitatif atau kualitatif?',
            'pilihan': ['Kuantitatif (angka, uji statistik)',
                        'Kualitatif (wawancara, makna, deskripsi)',
                        'Campuran (mixed methods)'],
            'kenapa': 'Alur dan isi tiap bab ditentukan pendekatan penelitian.',
        },
        'judul': {
            'tanya': 'Apa judul penelitianmu?',
            'pilihan': [],
            'kenapa': ('Judul menentukan kata kunci pencarian artikel & sitasi, '
                       'sehingga hasilnya tepat dan tidak meleset.'),
        },
    }
    return {
        'perlu_tanya': bool(kurang),
        'kurang': kurang,
        'daftar_pertanyaan': [pertanyaan[k] for k in kurang],
    }


def susun_rencana(judul: str, bab: str = '1', jenis_dok: str = '',
                  jenis_penelitian: str = '', tema: str = '',
                  maks_artikel: int = 20, saldo: int | None = None,
                  paket: str = 'gratis') -> dict:
    """TAHAP 2 — susun RENCANA (GRATIS, 0 token) untuk ditampilkan ke user.

    ⚠️ TIDAK memotong token. TIDAK memanggil AI tulis. Hanya:
       1. cari artikel NYATA (app.pustaka → audit DOI)
       2. ambil kerangka baku bab tsb
       3. laporkan perkiraan biaya + pagar artikel-sedikit

    Return dict siap dikirim ke tampilan.
    """
    tema_kerja = (tema or judul or '').strip()
    bab = str(bab or '1')

    #  ── 1. SITASI NYATA (app.pustaka — sudah teruji 21/0) ──
    artikel, info_cari, err = [], {}, ''
    try:
        from . import pustaka as _pustaka
        h = _pustaka.cari_semua(tema_kerja)
        artikel = h.get('artikel') or []
        info_cari = {
            'per_sumber': h.get('jumlah_per_sumber') or {},
            'total_unik': h.get('total_unik') or 0,
            'terverifikasi': h.get('terverifikasi') or 0,
            'kata_kunci': h.get('kata_kunci') or {},
        }
    except Exception as e:                                    # noqa: BLE001
        err = f'pencarian artikel gagal: {e}'
        log.warning('[kerangka] %s', err)

    #  ── 2. KERANGKA BAKU (disesuaikan per bab — arahan Bos 26Sep26) ──
    from . import kerangka_bab as _kb
    _b = _kb.ambil(bab)
    kerangka = [{'kode': k, 'judul': j, 'poin': p}
                for (k, j, p) in (_b.get('sub_bab') or [])]
    nama_bab = _b.get('nama') or ''
    butuh = _b.get('butuh') or {'tabel': [], 'grafik': []}

    #  ── HARGA per bab (satu sumber: config.token_bab) ──
    #     Bos: "Tiap bab punya pemotongan saldo berbeda, karena beda
    #     penanganan dan cara kerja." BAB IV punya DUA layanan terpisah.
    from .config import token_bab
    harga = int(token_bab(bab))
    harga_layanan = [{'kode': 'kerangka', 'nama': 'Kerangka & naskah bab',
                      'token': harga}]
    if bab == '4':
        harga_layanan = [
            {'kode': 'analisa', 'nama': 'Analisa & pembahasan',
             'token': int(token_bab('4'))},
            {'kode': 'olah_data', 'nama': 'Olah data (statistik)',
             'token': int(token_bab('4', 'olah_data'))},
        ]

    #  ⭐ CEK SALDO DI TAHAP 2 (perbaikan cacat rancangan, 26Sep26) ────────
    #     CACAT LAMA: harga ditampilkan tanpa melihat saldo user — user klik
    #     [Setuju] dulu, baru ditolak 402 di Tahap 3 (terasa dikecewakan).
    #     SEKARANG: saldo diperiksa SEBELUM setuju; tombol Setuju mati bila
    #     tidak cukup, dan user langsung diarahkan mengisi saldo.
    _saldo_ada = saldo is not None
    _cukup = (saldo >= harga) if _saldo_ada else None
    _kurang = (harga - saldo) if (_saldo_ada and not _cukup) else 0
    #  Ke mana diarahkan? Gratis → UPGRADE (tak boleh beli AddOn).
    if _cukup is False:
        from .config import boleh_beli_addon
        _arah = 'ADDON' if boleh_beli_addon(paket) else 'UPGRADE'
    else:
        _arah = None
    status_saldo = None
    if _cukup is False:
        status_saldo = {
            'cukup': False, 'saldo': saldo, 'butuh': harga, 'kurang': _kurang,
            'arahkan': _arah,
            'pesan': (f'Saldo Token Revisimu {saldo}, sedangkan bab ini perlu '
                      f'{harga} (kurang {_kurang}). '
                      + ('Tambah AddOn AI dulu ya — AddOn tidak hangus.'
                         if _arah == 'ADDON' else
                         'Upgrade ke paket Penulis dulu ya untuk bisa '
                         'menambah saldo.')),
        }
    elif _cukup is True:
        status_saldo = {
            'cukup': True, 'saldo': saldo, 'butuh': harga, 'kurang': 0,
            'sisa_setelah': saldo - harga,
            'pesan': (f'Saldo Token Revisimu {saldo} — cukup. Setelah '
                      f'dikerjakan, sisa {saldo - harga}.'),
        }

    #  ── 3. ARTIKEL SEDIKIT? (putusan Q3) ──
    sedikit = len(artikel) < ARTIKEL_MIN
    tawaran_sedikit = None
    if sedikit:
        tawaran_sedikit = {
            'pesan': (f'Dari pencarian, baru {len(artikel)} artikel yang '
                      f'benar-benar cocok dengan tema ini. Idealnya minimal '
                      f'{ARTIKEL_MIN} supaya kerangka punya dasar yang kuat.'),
            'pilihan': [
                {'kode': 'ubah_kata_kunci',
                 'label': 'Ubah kata kunci',
                 'ket': 'Kamu tulis kata kunci tambahan/ganti, lalu cari lagi.'},
                {'kode': 'lanjut', 'label': f'Lanjut dengan {len(artikel)} artikel',
                 'ket': 'Kerangka tetap disusun, tapi rujukannya lebih sedikit.'},
                {'kode': 'batal', 'label': 'Batal',
                 'ket': 'Tidak ada Token Revisi yang terpakai.'},
            ],
        }

    #  ── 4. KERANGKA TIDAK ADA untuk bab itu ──
    if not kerangka:
        from . import kerangka_bab as _kb2
        tersedia = [f'BAB {x["bab"]} ({x["nama"]})'
                    for x in _kb2.daftar_bab()]
        return {
            'ok': False,
            'kode': 'bab_belum_didukung',
            'pesan': (f'Kerangka BAB {bab} tidak tersedia. Yang tersedia: '
                      + ', '.join(tersedia) + '.'),
            'bab_tersedia': _kb2.BAB_KERANGKA,
        }

    return {
        'ok': True,
        'judul': judul,
        'bab': bab,
        'jenis_dokumen': jenis_dok,
        'jenis_penelitian': jenis_penelitian,
        'tema_pencarian': tema_kerja,
        'kerangka': kerangka,
        'nama_bab': nama_bab,
        'butuh': butuh,
        'panjang': {'sub_bab': len(kerangka), 'poin_per_sub': f'{POIN_MIN}-{POIN_MAKS}'},
        'artikel': [
            {'judul': r.get('title') or '',
             'penulis': r.get('authors') or '',
             'tahun': r.get('year') or 0,
             'jurnal': r.get('journal') or '',
             'doi': r.get('doi') or '',
             'status': r.get('doi_status') or '',
             'sumber': r.get('source') or ''}
            for r in artikel[:maks_artikel]
        ],
        'info_cari': info_cari,
        'sedikit': sedikit,
        'tawaran_sedikit': tawaran_sedikit,
        #  ⭐ HARGA PER BAB (ACC Bos 26Sep26): "Tiap bab punya pemotongan
        #     saldo berbeda, karena beda penanganan dan cara kerja."
        #     DITAMPILKAN di Tahap 2 SEBELUM user setuju, supaya mahasiswa
        #     tahu biayanya lebih dulu (dan bisa siapkan saldo).
        'harga_token': harga,           # int
        'harga_layanan': harga_layanan,  # daftar layanan (BAB IV ada 2)
        'perkiraan_token': harga,       # nama lama dipertahankan
        'saldo': saldo,
        'status_saldo': status_saldo,
        'boleh_setuju': bool(_cukup) if _cukup is not None else True,
        'catatan_biaya': ('Tahap ini GRATIS — belum ada Token Revisi yang '
                          'terpakai. Kalau kamu setuju, baru dipotong '
                          f'{harga} Token Revisi.'),
        'galat': err,
        'pagar': {
            'token_belum_dipotong': True,
            'sitasi_terverifikasi': info_cari.get('terverifikasi', 0),
            'aturan': 'Hanya artikel terverifikasi DOI yang boleh dikutip.',
        },
    }


# ══════════════════════════════════════════════════════════════════════════
#  TAHAP 3 — KERJAKAN (potong Token Revisi DI LUAR fungsi ini, pemanggil
#  yang memotong setelah user menekan [Setuju & Kerjakan] — pagar P1)
# ══════════════════════════════════════════════════════════════════════════
def bangun_isi(judul: str, bab: str = '1', jenis_dok: str = '',
               jenis_penelitian: str = '', tema: str = '',
               naskah: str = '', maks_artikel: int = 20,
               artikel_dipakai: list[dict] | None = None) -> dict:
    """Susun BAHAN kerangka: sitasi + kerangka + rencana tabel & grafik.

    ⚠️ Fungsi ini TIDAK memotong token dan TIDAK menulis .docx.
       Potong token dilakukan API (setelah persetujuan user).
       Penulisan .docx dilakukan jalur presisi (`app/tulis_docx.py`).

    `artikel_dipakai` (ACC Bos 06Okt26): daftar artikel dari LUAR — gabungan
    artikel AI + artikel yang DITAMBAHKAN USER (sudah diaudit). Kalau diisi,
    mesin TIDAK mencari ulang (hemat + artikel manual ikut terpakai).
    Kalau kosong/None → perilaku LAMA persis (cari sendiri via pustaka).

    Keluaran dipakai untuk:
      · prompt AI (kalau AI tersedia) → kerangka lebih hidup
      · cadangan: kerangka baku + poin + sitasi siap tulis
    """
    from . import kerangka_bab as _kb

    tema_kerja = (tema or judul or '').strip()
    bab = str(bab or '1')
    _b = _kb.ambil(bab)
    if not _b:
        return {'ok': False, 'kode': 'bab_belum_didukung',
                'pesan': f'BAB {bab} tidak punya kerangka baku.'}

    #  ── 1. SITASI NYATA (audit DOI) ──
    #     ACC Bos 06Okt26: bila `artikel_dipakai` DIISI (gabungan artikel AI +
    #     artikel manual user), PAKAI ITU — jangan cari ulang. Hemat + artikel
    #     manual ikut terpakai sebagai sitasi. Kalau kosong → perilaku LAMA.
    artikel, info = [], {}
    if artikel_dipakai:
        artikel = [a for a in artikel_dipakai if isinstance(a, dict)]
        info = {'per_sumber': {}, 'total_unik': len(artikel),
                'terverifikasi': info_terverifikasi(artikel),
                'dari_kiriman': True}
        info['per_sumber'] = {'AI + tambahan user': len(artikel)}
    else:
        try:
            from . import pustaka as _pustaka
            h = _pustaka.cari_semua(tema_kerja)
            artikel = h.get('artikel') or []
            info = {'per_sumber': h.get('jumlah_per_sumber') or {},
                    'total_unik': h.get('total_unik') or 0,
                    'terverifikasi': h.get('terverifikasi') or 0}
        except Exception as e:                                # noqa: BLE001
            log.warning('[kerangka] TAHAP 3 pencarian gagal: %s', e)

    #  ── 2. APA 7 — HANYA yang terverifikasi (pagar P3) ──
    daftar_pustaka = ''
    try:
        from . import pustaka as _p2
        daftar_pustaka = _p2.daftar_pustaka_apa7(artikel)
    except Exception:                                         # noqa: BLE001
        daftar_pustaka = ''

    #  ── 3. PAGAR ARTIKEL (06Okt26) — jawaban pertanyaan Bos:
    #     "bagaimana script tahu isi artikel tanpa halusinasi?" ⇒ dari
    #     ABSTRAK (kata penulis sendiri = data NYATA). Pagar:
    #     (a) hanya artikel berabstrak boleh jadi dasar temuan,
    #     (b) artikel tanpa abstrak DITANDAI `isi_terbatas` (dipakai UI ⚠️),
    #     (c) bahan nyata + aturan prompt disusun di sini supaya AI tidak
    #         menambah apa pun di luar abstrak/judul.
    try:
        from . import pagar_artikel as _pa
        artikel = _pa.tandai(artikel)
        _bagi = _pa.bagi(artikel)
        bahan_ai = _pa.teks_untuk_ai(artikel, maks=maks_artikel)
        aturan_ai = _pa.aturan_prompt()
        info_pagar_artikel = _bagi['jumlah']
    except Exception as e:                                    # noqa: BLE001
        log.warning('[kerangka] pagar artikel gagal: %s', e)
        bahan_ai, aturan_ai = '', ''
        info_pagar_artikel = {'layak': 0, 'terbatas': 0, 'total': 0}

    #  ── 4. RENCANA TABEL & GRAFIK (sesuai bab — arahan Bos) ──
    tabel = [{'judul': t, 'kolom': [], 'baris': []}
             for t in (_b.get('butuh') or {}).get('tabel', [])]
    grafik = [{'judul': g, 'jenis': _jenis_grafik(bab), 'data': []}
              for g in (_b.get('butuh') or {}).get('grafik', [])]

    #  ── 5. SARING artikel yang RELEVAN ke sub-bab (kalau naskah ada) ──
    relevan = _pilih_relevan(artikel, naskah, judul)

    return {
        'ok': True,
        'bab': bab, 'nama_bab': _b.get('nama') or '',
        'judul': judul, 'jenis_dokumen': jenis_dok,
        'jenis_penelitian': jenis_penelitian,
        'kerangka': [{'kode': k, 'judul': j, 'poin': p}
                     for (k, j, p) in (_b.get('sub_bab') or [])],
        'tabel': tabel,
        'grafik': grafik,
        'artikel': artikel[:maks_artikel],
        'artikel_relevan': relevan[:maks_artikel],
        'daftar_pustaka': daftar_pustaka,
        'info_cari': info,
        #  ── BAHAN NYATA UNTUK AI + ATURANNYA (pagar 1 & 3) ──
        'bahan_ai': bahan_ai,
        'aturan_ai': aturan_ai,
        'info_artikel': info_pagar_artikel,
        'pagar': {
            'token_dipotong_di_api': True,
            'sitasi_terverifikasi': info.get('terverifikasi', 0),
            'hanya_terverifikasi_masuk_daftar_pustaka': True,
            #  pagar baru: hanya artikel berabstrak boleh jadi dasar temuan
            'isi_dari_abstrak_bukan_tebakan': True,
            'artikel_layak': info_pagar_artikel.get('layak', 0),
            'artikel_isi_terbatas': info_pagar_artikel.get('terbatas', 0),
        },
    }


def info_terverifikasi(artikel: list[dict]) -> int:
    """Hitung berapa artikel yang lolos audit (aturan SAMA dgn pustaka P3).

    Dipakai saat artikel datang dari KIRIMAN (gabungan AI + tambahan user):
    `pustaka.cari_semua()` tidak dijalankan, jadi angkanya dihitung di sini
    agar pagar P3 tetap jujur.
    """
    n = 0
    for a in artikel or []:
        if not isinstance(a, dict):
            continue
        st = (a.get('doi_status') or '').strip()
        if st == 'verified' or (st == 'no_doi' and a.get('garuda_id')):
            n += 1
    return n


async def karang_dengan_artikel(judul: str, bab: str, bahan_ai: str,
                                aturan_ai: str,
                                kerangka: list[dict] | None = None,
                                timeout: float = 120.0) -> dict:
    """Minta AI MENULIS dengan artikel naskah sebagai sumber (SAMBUNGAN B-2).

    🚨 AKAR yang Wulan temukan 13Okt26: `bangun_isi()` SUDAH menyiapkan
    `bahan_ai` + `aturan_ai` (pagar 1 & 3), TAPI keduanya HANYA menumpang
    di balasan — TIDAK PERNAH dikirim ke model. Akibatnya AI tidak menulis
    apa pun dari artikel user; yang keluar cuma kerangka BAKU + daftar
    pustaka yang diraKit kode. Fungsi ini menutup lubang itu.

    Pintu AI yang dipakai: `ai._panggil_router` (SUDAH ADA — jalur 1 9router
    → jalur 2, sabar 90 dtk). TIDAK ada provider/jalur baru.

    Pagar yang dipertahankan (aturan Bos 13Okt26, "jangan sampai AI
    merekomendasikan artikel yang tidak valid"):
      · `aturan_ai` WAJIB ikut → AI dilarang menambah penulis/tahun/DOI.
      · Hanya artikel BERABSTRAK jadi sumber temuan (`pagar_artikel.bagi`).
      · `(Nama, Tahun)` di luar bahan → DIBUANG (dicek setelah jawaban).

    Mengembalikan {'ok', 'teks', 'sitasi_dipakai', 'sitasi_dibuang', ...}.
    """
    if not (bahan_ai or '').strip():
        return {'ok': False, 'kode': 'tanpa_bahan',
                'pesan': 'Belum ada artikel berabstrak untuk dijadikan sumber.',
                'teks': '', 'sitasi_dipakai': [], 'sitasi_dibuang': []}

    from . import pagar_artikel as _pa

    daftar_sub = '; '.join(
        f'{k.get("kode")} {k.get("judul")}'
        for k in (kerangka or []) if isinstance(k, dict))[:1500]

    perintah = (
        f'{aturan_ai}\n\n'
        f'JUDUL NASKAH: {judul}\nBAB: {bab}\n'
        + (f'SUB-BAB YANG HARUS DITULIS:\n{daftar_sub}\n' if daftar_sub else '')
        + '\nTULIS ISIAN BAB (bukan kerangka) memakai sumber di bawah.\n'
        'Syarat:\n'
        '1. Setiap klaim yang datang dari sumber WAJIB diberi kutipan '
        '(Nama, Tahun) — nama & tahun PERSIS seperti di sumber.\n'
        '2. DILARANG menyebut nama/tahun/DOI yang tidak ada di sumber.\n'
        '3. Tulis mengalir, bahasa Indonesia akademik, tanpa bullet berlebih.\n'
        '4. Kalau sumber tidak mendukung suatu klaim, jangan tulis klaim itu.\n'
        f'\n=== SUMBER (judul + penulis + tahun + abstrak) ===\n{bahan_ai}\n'
    )

    try:
        #  Pintu AI yang ADA (satu pintu: 9router → cadangan). Jangan bikin baru.
        from .ai import _panggil_router
        teks, info = await _panggil_router(perintah, timeout,
                                           system=aturan_ai)
    except Exception as e:                                        # noqa: BLE001
        log.warning('[kerangka] AI menulis gagal: %s', e)
        return {'ok': False, 'kode': 'ai_gagal', 'pesan': str(e)[:200],
                'teks': '', 'sitasi_dipakai': [], 'sitasi_dibuang': []}

    #  ── PAGAR: kutipan (Nama, Tahun) yang TIDAK ada di sumber → dibuang ──
    #     Dicek dengan teks sumber APA ADANYA (`bahan_ai`), jadi tidak
    #     bergantung pada tabel/fungsi baru. Pola sama seperti pemeriksa
    #     `DAFTAR SUMBER` yang sudah dipakai jalur lain.
    dipakai, dibuang = _pisah_kutipan(teks, bahan_ai)
    if dibuang:
        teks = _buang_kutipan(teks, dibuang)

    return {'ok': True, 'teks': teks, 'info': info,
            'sitasi_dipakai': dipakai, 'sitasi_dibuang': dibuang,
            'mesin': info.get('model') if isinstance(info, dict) else ''}


def _pisah_kutipan(teks: str, bahan: str) -> tuple[list[str], list[str]]:
    """Pisahkan kutipan `(Nama, Tahun)` yang ADA di bahan vs yang TIDAK.

    Pagar keras Bos 13Okt26: AI DILARANG menyebut nama/tahun yang tidak ada
    di sumber. Yang tidak ada → dilaporkan supaya bisa dibuang, bukan
    didiamkan.
    """
    import re as _re
    #  DUA pola kutipan (13Okt26 — pelajaran uji nyata):
    #   ① `(Susanti & Rahma, 2024)` / `(Wijaya, 2023)` — dalam kurung
    #   ② `Wijaya (2023)` / `Susanti dan Rahma (2024)` — naratif (AI sering
    #      pakai ini; pagar versi pertama BUTA pada pola ②)
    pola1 = _re.compile(r'\(([A-Z][A-Za-z\'\-]+)(?:\s*(?:&|dan)\s*'
                        r'([A-Z][A-Za-z\'\-]+))?[,\s]+(\d{4})\)')
    pola2 = _re.compile(r'([A-Z][A-Za-z\'\-]+)(?:\s*(?:&|dan)\s*'
                        r'([A-Z][A-Za-z\'\-]+))?\s+\((\d{4})\)')
    bahan_rendah = (bahan or '').lower()
    dipakai, dibuang = [], []
    for pola in (pola1, pola2):
        for m in pola.finditer(teks or ''):
            penuh = m.group(0).strip()
            nama = m.group(1)
            tahun = m.group(3)
            ada = (nama.lower() in bahan_rendah
                   and str(tahun) in bahan_rendah)
            if ada:
                if penuh not in dipakai:
                    dipakai.append(penuh)
            elif penuh not in dibuang:
                dibuang.append(penuh)
    return dipakai, dibuang


def _buang_kutipan(teks: str, dibuang: list[str]) -> str:
    """Buang kutipan bermasalah dari teks (tanpa merusak kalimat)."""
    for k in dibuang or []:
        teks = (teks or '').replace(k, '')
    return teks


def _jenis_grafik(bab: str) -> str:
    """Jenis grafik sesuai ciri bab (arahan Bos: 'termasuk grafik & tabel')."""
    return {'2': 'diagram_panah', '4': 'batang'}.get(str(bab), 'batang')


def _pilih_relevan(artikel: list[dict], naskah: str, judul: str) -> list[dict]:
    """Pilih artikel yang paling nyambung dengan NASKAH user (kalau ada).

    Kalau naskah kosong → kembalikan semua (tidak memotong pilihan user).
    """
    if not naskah:
        return list(artikel)
    teks = (naskah or '').lower()
    keluar = []
    for r in artikel:
        kata = [w for w in (r.get('title') or '').lower().split()
                if len(w) > 5]
        kena = sum(1 for w in kata if w in teks)
        if kena:
            keluar.append({**r, 'kena_naskah': kena})
    keluar.sort(key=lambda x: (-(x.get('kena_naskah') or 0),
                               -(x.get('cited_by_count') or 0)))
    return keluar or list(artikel)
