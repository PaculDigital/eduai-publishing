"""PETA 3 TINGKAT v2 — GELOMBANG (batch) supaya naskah besar TIDAK kena 503.

AKAR (terukur 08Okt26): 1.034 kandidat / 165.610 kar → 503.
   Batas aman terukur: 156 tanya / 20.622 kar.
   ⚠️ ATURAN BOS: 503 ⇒ JANGAN vonis "batas tetap"; ulangi dulu.
   Sudah diulang: 9router sehat (938 model) + Jev 1 tanya ✅ ⇒ 503 = BAHAN TERLALU BESAR.

OBAT (bukan menyempitkan Jev): bagi kandidat jadi GELOMBANG ≤ BATAS_AMAN tanya/kar,
   tiap gelombang 1 panggilan Jev (Jev tetap membaca KONTEKS LENGKAP tiap gelombang).

GELOMBANG: BATAS_TANYA = 120 · BATAS_KAR = 18.000 (di bawah batas aman 156/20.622).
"""
import sys, json, time, re, os, hashlib, logging
from collections import OrderedDict
sys.path.insert(0, '/tmp/jev-v4')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam, state

log = logging.getLogger(__name__)

# ── VERSI ATURAN (10 Nov 2026, v5) ─────────────────────────────────────
#    Kunci cache peta: ubah string ini SETIAP KALI aturan di berkas ini
#    berubah (stitch, ambang, Aturan 2/4/5/6, D1) ⇒ cache lama kedaluwarsa
#    otomatis, tidak pernah ada peta basi dari aturan lama.
#    v4: pre-filter kode di stitch (`sambung_kode`), tanya-ulang urut p +
#    suara berbobot confidence, kupas nomor halaman pada BAB, waktu stitch
#    tercatat (terukur live 10 Nov: fid=115 stitch 64 -> ~14 panggilan).
#    v5: tanya-ulang BERGELOMBANG (cap 120 per gelombang, maks 3 gelombang),
#    pisah judul menempel satu baris, perbaiki spasi huruf pecah-per-huruf,
#    profil kampus untuk istilah + penomoran, tanda bahasa non-standar.
RULE_VERSION = 'jev-peta-v5'

# ── SAKLAR (env, tanpa ubah kode) ────────────────────────────────────────
#    EDUAI_JEV_STITCH=0      ⇒ matikan pass-1 stitch (susun cara lama)
#    EDUAI_JEV_TANYA_ULANG=0 ⇒ matikan tanya-ulang bertarget (goyang/p)
#    EDUAI_JEV_CACHE_MAX=N   ⇒ jumlah peta yang disimpan di cache (bawaan 8)
#    EDUAI_JEV_JEDA_DASAR=X  ⇒ jarak ANTAR AWAL panggilan gelombang (detik,
#                               bawaan 0,7 — lihat _tidur_adaptif)
def _env_int(nama, bawaan):
    try:
        return int(os.getenv(nama) or bawaan)
    except ValueError:
        return bawaan


def _env_float(nama, bawaan):
    try:
        return float(os.getenv(nama) or bawaan)
    except ValueError:
        return bawaan


def _stitch_aktif():
    return (os.getenv('EDUAI_JEV_STITCH') or '1') != '0'


def _tanya_ulang_aktif():
    return (os.getenv('EDUAI_JEV_TANYA_ULANG') or '1') != '0'


def _jeda_dasar():
    return _env_float('EDUAI_JEV_JEDA_DASAR', 0.7)


def _maks_gelombang_tanya_ulang():
    """Maks gelombang tanya-ulang (v5): tiap gelombang ≤120 kandidat.

    Bawaan 3 ⇒ paling banyak 360 kandidat ragu ditanya ulang (3 panggilan
    Jev tambahan). 1 = perilaku v4 (satu gelombang, cap 120). Naikkan hanya
    dengan bukti biaya: tiap gelombang = 1 panggilan Jev.
    """
    return max(1, _env_int('EDUAI_JEV_TANYA_ULANG_MAKS_GELOMBANG', 3))


# ── CACHE PETA (10 Nov 2026) ─────────────────────────────────────────────
#    Naskah yang sama dipetakan berkali-kali (peta_awal, deteksi bagian di
#    layar, konversi) — dulu tiap kali panggil Jev dari nol. Sekarang hasil
#    disimpan per sidik (hash teks + versi aturan + putaran), di memori proses
#    saja (container restart = cache hilang, aman). Batas 8 entri (LRU).
_CACHE_PETA: OrderedDict = OrderedDict()


def _cache_maks():
    return max(0, _env_int('EDUAI_JEV_CACHE_MAX', 8))


def _kunci_cache(teks, putaran):
    sidik = hashlib.sha256((teks or '').encode('utf-8')).hexdigest()
    return (sidik, RULE_VERSION, putaran)


def _cache_ambil(kunci):
    if _cache_maks() <= 0:
        return None
    hasil = _CACHE_PETA.get(kunci)
    if hasil is None:
        return None
    _CACHE_PETA.move_to_end(kunci)
    return dict(hasil)          # salinan dangkal — pemanggil tak boleh ubah asli


def _cache_simpan(kunci, hasil):
    maks = _cache_maks()
    if maks <= 0 or hasil is None:
        return
    _CACHE_PETA[kunci] = hasil
    _CACHE_PETA.move_to_end(kunci)
    while len(_CACHE_PETA) > maks:
        _CACHE_PETA.popitem(last=False)


def _tidur_adaptif(t0, dasar=None):
    """Jeda ADAPTIF antar gelombang (10 Nov 2026, ganti sleep 0,7 tetap).

    Dulu: tiap gelombang tidur 0,7 detik DITAMBAH waktu panggil (40 gelombang
    × (0,6 panggil + 0,7 tidur) ≈ 52 detik, 28 detik di antaranya diam).
    Sekarang: jarak ANTAR AWAL panggilan dijaga ≥ `dasar` detik — kalau
    panggilannya sendiri sudah ≥ dasar (server lambat), TIDAK tidur sama
    sekali. Panggilan cepat (0,6 dtk) ⇒ tidur 0,1 dtk; total 40 gelombang
    ≈ 28 detik. Jeda ini BUKAN tebak: `dasar` bawaan 0,7 = nilai lama yang
    sudah terbukti aman terhadap 503, hanya tidak lagi ditumpuk di atas
    waktu panggil. Uji live tetap perlu mengukur latensi nyata.
    """
    if dasar is None:
        dasar = _jeda_dasar()
    sisa = dasar - (time.time() - t0)
    if sisa > 0:
        time.sleep(sisa)


BATAS_TANYA = 120
BATAS_KAR = 18000
AMBANG_CAPTION = 70
KRITERIA = {
    'bab': 'Awal BAB (mis. BAB I, BAB II)',
    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
POLA_BAB = re.compile(r'^BAB\s+([IVX0-9]+)\s*$', re.I)   # ivx = Romawi · 0-9 = varian "BAB 1" (usul Bos 09 Okt)
# ── ATURAN D1: POLA AWALAN (bukan pola baris-penuh).
#    ⚠️ POLA_BAB (baris-penuh) TIDAK PERNAH cocok pada KANDIDAT: semua baris
#    "BAB I" polos sudah disedot ke `gabung` di susun() ⇒ tak pernah jadi kand.
#    Penyebutan sistematika hanya cocok pola AWALAN ini. (Koreksi Bos 09 Okt.)
#    Boleh didahului nomor daftar: "1. BAB I PENDAHULUAN, bagian ini…".
#    Boleh juga didahului nomor halaman: "13 BAB I" (terukur WULAN-1).
_POLA_BAB_TEKS = re.compile(r'^(?:\d{1,3}\s+)?(?:\d+[.)]\s*|[IVX]+[.)]\s*)?BAB\s+[IVX0-9]+\b', re.I)
#    Pengikut blok sistematika — DUA ragam terukur (09 Okt, naskah Wulandari fid=112):
#      "Bab ini berisi…"   (Asih)  ·  "bagian ini berisikan…" (Wulandari)
#    ⚠️ WAJIB terima keduanya: ganti salah satu saja = D1 gagal di kampus lain.
_PENGIKUT_SISTEMATIKA = re.compile(r'^\s*(?:Bab|bagian)\s+ini\b', re.I)
#    Varian BEBAS posisi — untuk baris SISTEMATIKA yang frasanya ADA DI DALAM
#    baris yang sama, mis. "1. BAB I PENDAHULUAN, bagian ini berisikan…".
#    ⚠️ `^\s*` di atas TIDAK bisa dipakai `.search()` (pola ber-anchor awal) —
#    wajib pola terpisah ini. (Jebakan terukur 09 Okt.)
_FRASA_SISTEMATIKA = re.compile(r'(?:Bab|bagian)\s+ini\b', re.I)
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')

# ── ATURAN 4 (SPSS): daftar TERTUTUP header output SPSS (huruf kecil semua).
#    Hanya exact-match ⇒ sub-bab Indonesia ("Uji Reliabilitas") tak akan cocok.
_SPSS_HEADER = {
    'reliability statistics',
    'item-total statistics',
    'item statistics',
    'scale statistics',
    'summary item statistics',
    'descriptive statistics',
    'correlations',
    'model summary',
    'anova',
    'coefficients',
    'variables entered/removed',
    'case processing summary',
    'total variance explained',
    'component matrix',
    'rotated component matrix',
}


def _spss_header(s):
    """Header output SPSS (Inggris) — bukan judul sub-bab skripsi."""
    t = s.strip().lower()
    if t in _SPSS_HEADER:
        return True
    # Sufiks footnote SPSS menempel langsung: 'Coefficientsa',
    # 'Model Summaryb' ⇒ kupas 1 huruf akhir, cek sisanya.
    return len(t) > 2 and t[-1].islower() and t[:-1] in _SPSS_HEADER


# ── ATURAN D1 (putusan Bos 09 Okt): BLOK SISTEMATIKA PENULISAN ────────────
#    Naskah skripsi sering memuat blok "SISTEMATIKA PENULISAN" yang menyebut
#    SEMUA judul bab berurutan rapat (BAB I..V, masing-masing diikuti satu
#    paragraf "Bab ini berisi…") ⇒ MENUTUPI bab asli & bikin 10 label BAB.
#    Deteksi DETERMINISTIK (tanpa AI): ≥3 penyebutan "BAB X" dalam ~30 baris
#    berurutan, yang masing-masing diikuti baris berawalan "Bab ini".
#    ⛔ AKSI = TANDAI, JANGAN BUANG (data, bukan sampah — pelajaran Uji 8).
def _tandai_sistematika(baris, label, kand):
    """Kembalikan himpunan indeks baris anggota blok SISTEMATIKA.

    ⚠️ KOKOH (perbaikan 09 Okt, usul Bos): calon diambil dari POLA TEKS
    (`POLA_BAB`) — BUKAN dari label Jev. Kalau bergantung label Jev, satu
    kali Jev melabel 'BAB I' jadi 'subbab' ⇒ deteksi GAGAL DIAM-DIAM
    (tidak ada peringatan). Pola teks = deterministik, tak bisa goyang.
    """
    idx_kand = {i for i, _t in kand}
    calon = [i for i in sorted(idx_kand)
             if _POLA_BAB_TEKS.match(baris[i].strip()) or label.get(i) == 'bab']
    hasil = set()
    JENDELA = 30          # jarak maksimum antar 'BAB X' dalam satu blok
    MIN_BAB = 3           # minimal jumlah bab dalam blok
    n = len(calon)
    for a in range(n):
        blok, j = [], a
        while j < n and (not blok or calon[j] - blok[-1] <= JENDELA):
            i = calon[j]
            # baris sesudahnya (lewati kosong) harus mulai "Bab ini"
            k = i + 1
            while k < len(baris) and not baris[k].strip():
                k += 1
            # Penanda sistematika bisa ada di DUA tempat (terukur 09 Okt):
            #   (a) di baris ITU SENDIRI — "1. BAB I PENDAHULUAN, bagian ini berisikan…"
            #   (b) di baris PENGIKUT     — "BAB I" lalu "Bab ini berisi…" (Asih)
            sendiri = _FRASA_SISTEMATIKA.search(baris[i])
            pengikut = bool(k < len(baris) and _PENGIKUT_SISTEMATIKA.match(baris[k].strip()))
            if sendiri or pengikut:
                blok.append(i)
                j += 1
            else:
                # bukan anggota blok; kalau blok sudah penuh, hentikan
                if len(blok) >= MIN_BAB:
                    break
                j += 1
                if blok and calon[j - 1] - blok[-1] > JENDELA:
                    break
        if len(blok) >= MIN_BAB:
            hasil.update(blok)
    return hasil


def dibuang(s):
    # ATURAN 6 (vonis Bos 09 Okt): NOMOR HALAMAN murni.
    #   Baris angka-murni ("14", "30", "65") tidak pernah judul — nol risiko.
    #   Terukur naskah Wulandari fid=112 (PDF): 94 nomor halaman jadi kandidat,
    #   2 di antaranya dilabel BAB ("30", "65") ❌.
    if re.match(r'^\s*\d{1,4}\s*$', s):
        return True
    # ATURAN 1 versi B (vonis Bos 09 Okt): baris TABEL.
    #   ≥2 pipa DAN ≤300 kar = PASTI tabel/keluaran SPSS ⇒ buang.
    #   ≥2 pipa tapi PANJANG (>300 kar) = paragraf asli yang pakai '|'
    #     sebagai pemisah biasa ⇒ JANGAN buang, biar Jev putuskan.
    #   Pagar panjang menyelamatkan ~9 paragraf asli di Asih
    #   (L001408 770 kar · L001516 908 kar · L001624 346 kar).
    #   1 pipa masih mungkin kalimat biasa ⇒ TIDAK dibuang.
    #   Batasan sadar: tabel 2 kolom (1 pipa) LOLOS.
    if len(s) <= 300 and s.count('|') >= 2:
        return True
    # ATURAN 3 (vonis Bos 09 Okt): judul KUESIONER PENELITIAN = isi LAMPIRAN,
    #   bukan struktur BAB I-V. Konsisten dengan kebijakan lampiran yang sudah
    #   jalan (LAMPIRAN 1-11, DAFTAR LAMPIRAN sudah dibuang).
    if re.match(r'^\s*(KUESIONER|ANGKET)\b', s, re.I):
        return True
    if _PEMBUANG.match(s) or _TITIK_ISI.search(s) or POLA_MARKER.match(s):
        return True
    if POLA_SUMBER.match(s):
        return True
    if POLA_CAPTION.match(s) and len(s) <= AMBANG_CAPTION:
        return True
    return False


# ── POLA NOMOR BERTINGKAT (10 Nov 2026) ────────────────────────────────
#    Baris bernomor bertingkat ("1.1 Latar Belakang", "2.3.1 Metode") DIBACA
#    KODE SAJA, tidak dikirim ke Jev: nomornya sendiri sudah menandai
#    kedudukan di kerangka. Syarat KETAT (jangan longgarkan tanpa ukur):
#    angka bertingkat + teks diawali huruf BESAR + ≤120 kar + tidak diakhiri
#    '?' (butir bertanya) atau '.' (kalimat). Yang TIDAK memenuhi syarat
#    tetap jadi kandidat Jev (mis. "1.1 latar belakang" huruf kecil,
#    "2. Wawancara" nomor tunggal — kode tak bisa bedakan dari butir daftar).
_POLA_NOMOR_BERTINGKAT = re.compile(r'^(\d+(?:\.\d+)+)\s+(\S.*)$')


def _ambang(nama, bawaan):
    """Ambang aturan dari profil kampus (config), fallback ke bawaan.

    Angka aturan (mis. judul >300 kar) BUKAN hardcode — dibaca dari
    `profil/kampus.json` bila ada. Gagal baca ⇒ bawaan (jangan gagalkan).
    """
    try:
        from app import profil_kampus as _pk
        return int(_pk.aturan().get(nama) or bawaan)
    except Exception:
        return bawaan


def _huruf_awal_kecil(s):
    """True bila HURUF pertama judul huruf kecil (awalan nomor dikupas dulu:
    '1.1 latar belakang' = huruf kecil, '1.1 Latar' bukan). Tanpa kupasan
    ini, judul bernomor yang huruf kecil lolos dari Aturan 5 (angka '1'
    bukan huruf kecil — bug terukur 10 Nov 2026)."""
    t = re.sub(r'^\d+(?:\.\d+)*\s*', '', (s or '').strip())
    return bool(t) and t[:1].islower()


def _nomor_bertindak_judul(s):
    """True bila baris bernomor bertingkat ini PASTI judul sub-bab (kode)."""
    m = _POLA_NOMOR_BERTINGKAT.match(s.strip())
    if not m:
        return False
    teks = m.group(2)
    if len(s.strip()) > _ambang('subbab_kode_maks_kar', 120):
        return False
    if teks.endswith('?') or teks.endswith('.'):
        return False
    return teks[:1].isupper()


# ── PASS-1 STITCH (10 Nov 2026 — dipasang ke repo, dulu hanya di server) ──
#    REKONSILIASI (bukti dari kode, 10 Nov 2026):
#      · 10 Okt 2026 Bos memasang stitch di `peta3_jev.py` dan Wulan
#        memverifikasi LULUS di server (kandidat 8.555 → 1.524) — TAPI
#        versi itu TIDAK PERNAH masuk git main: `git log -S stitch` kosong,
#        `peta3_jev.py` di main 0412330 TIDAK memuat `_stitch_baris` sama
#        sekali, dan salinan workspace pun identik (md5 sama). Deploy 10 Nov
#        membangun image dari main ⇒ stitch di server ikut HILANG.
#      ⇒ Audit 10 Nov ("stitch hilang") BENAR untuk kode produksi di repo;
#        catatan 10 Okt BENAR untuk salinan server saat itu. Di sinilah
#        stitch dipasang KEMBALI, kali ini di repo, dengan 3 pagar + obat
#        baris-kosong fid=104 yang dulu masih terbuka.
#    CARA: pakai alat produksi yang sudah ada (`app/konversi._pecah_blok`,
#    JANGAN bikin baru) + satu pass tambahan untuk pasangan lintas
#    baris-kosong (Jev TERBUKTI BISA menilai, uji 10 Okt: 12.527/12.527
#    terjawab, 7 dari 8 zona abu memang harus disambung).
def _perbaiki_gabung_bab(blok):
    """Pisah kembali blok yang menelan judul BAB ("BAB I PENDAHULUAN").

    Stitch TIDAK BOLEH melewati garis BAB: gabung judul BAB sudah ada
    jalurnya sendiri (`susun()` → `gabung`). Kalau satu blok berisi
    "BAB I" + judulnya, pecah jadi dua blok (deterministik, tanpa Jev).
    """
    keluar = []
    for b in blok:
        m = re.match(r'^(BAB\s+[IVX0-9]+)\s+(\S.*)$', (b.get('text') or '').strip(), re.I)
        if m and b.get('lines'):
            garis = list(b.get('lines') or [])
            keluar.append({'text': m.group(1), 'lines': garis[:1], 'kosong': False})
            keluar.append({'text': m.group(2), 'lines': garis[1:] or garis[:1],
                           'kosong': False})
        else:
            keluar.append(b)
    return keluar


def _stitch_baris(teks, tanya_fn=None):
    """PASS-1: sambung baris terbelah jadi blok. Kembalikan TEKS (bukan blok).

    3 PAGAR (jangan dilepas — pagar ③ terbukti bekerja di fid=104):
      ① Jev mati / `_pecah_blok` galat / kosong ⇒ pakai teks APA ADANYA.
      ② blok < 4 ATAU ≥ jumlah baris ⇒ pakai teks APA ADANYA (tak berguna).
      ③ karakter (non-spasi) hilang >2% ⇒ pakai teks APA ADANYA (ada isi hilang).
    Obat fid=104: pasangan lintas baris-kosong DITANYAKAN ke Jev (dulu
    dilewati `_kandidat_sambung`), dan digabung bila Jev bilang sambung.
    """
    baris_asal = (teks or '').split('\n')
    if len(baris_asal) < 4:
        return teks
    try:
        from app import konversi as _K
        blok = _K._pecah_blok(teks)
    except Exception as e:                                    # pagar ①
        log.warning('[peta3] stitch dilewati (konversi galat: %s)', e)
        return teks
    if not blok:                                              # pagar ①
        return teks
    blok = _perbaiki_gabung_bab(blok)
    if len(blok) < 4:                                             # pagar ② (sebagian)
        return teks
    # ── pagar ③: isi hilang? (ukur karakter non-spasi — normalisasi spasi
    #    oleh _pecah_blok bukan kehilangan isi)
    def _isi(t):
        return re.sub(r'\s', '', t or '')
    asal, baru = _isi(teks), _isi('\n'.join(b.get('text') or '' for b in blok))
    if asal and (len(asal) - len(baru)) / len(asal) > 0.02:
        return teks

    # ── obat fid=104: pasangan lintas baris-kosong ──────────────────────
    #    Pola: [blok isi][1+ blok kosong][blok isi]. Tanyakan ke Jev apakah
    #    blok sesudah kosong menyambung kalimat blok sebelumnya. Jangan
    #    pernah gabung melewati garis BAB.
    if tanya_fn is None:
        tanya_fn = satpam.tanya_bebas_mutu
    # ── KODE DULU (v4): pasangan yang PASTI diputus kode, tidak ditanya Jev.
    try:
        from app.sambung_kode import sambung_kode as _sk
    except Exception:                                     # noqa: BLE001
        _sk = None
    pasangan = []          # (idx_blok_sebelum, idx_blok_sesudah) -> tanya Jev
    langsung = []          # pasangan yang PASTI sambung (kode, tanpa Jev)
    for a in range(len(blok)):
        if blok[a].get('kosong') or not (blok[a].get('text') or '').strip():
            continue
        b = a + 1
        while b < len(blok) and (blok[b].get('kosong') or not (blok[b].get('text') or '').strip()):
            b += 1
        if b < len(blok) and b > a + 1:
            sebelum = (blok[a].get('text') or '').strip()
            sesudah = (blok[b].get('text') or '').strip()
            if POLA_BAB.match(sebelum) or POLA_BAB.match(sesudah):
                continue
            d = _sk(sebelum, sesudah) if _sk else None
            if d is False:
                continue               # pasti tidak sambung -> jangan tanya
            if d is True:
                langsung.append((a, b))
            else:
                pasangan.append((a, b))
    sambung = {}
    if pasangan:
        for mulai in range(0, len(pasangan), 120):
            sub = pasangan[mulai:mulai + 120]
            perlu = sorted({a for a, _ in sub} | {b for _, b in sub})
            state = '\n'.join('L%04d| %s' % (n, (blok[n].get('text') or '')[:200])
                              for n in perlu)
            tanya = {('L%04d' % b): {'instructions':
                     ('Does line L%04d pick up mid-sentence, continuing a '
                      'sentence left unfinished at the end of line L%04d?'
                      % (b, a)), 'type': 'noul'}
                     for a, b in sub}
            try:
                jawab = tanya_fn(state, tanya) or {}
            except Exception:
                jawab = {}
            if jawab:
                sambung.update(jawab)
    if pasangan or langsung:
        try:
            ambang_gantung = _K._SAMBUNG_GANTUNG
            ambang_akhir = _K._SAMBUNG_AKHIR
        except Exception:
            ambang_gantung, ambang_akhir = 0.2, 0.5
        gabung_idx = set()
        for a, b in pasangan:
            jaw = (sambung.get('L%04d' % b) or {}).get('noul')
            if jaw is None:
                continue
            sebelum = (blok[a].get('text') or '').strip()
            ambang = (ambang_akhir if re.search(r'[.!?:;\u2026]["\')\]]*$', sebelum)
                      else ambang_gantung)
            try:
                if float(jaw) >= ambang:
                    gabung_idx.add((a, b))
            except (TypeError, ValueError):
                pass
        gabung_idx.update(langsung)     # pasangan PASTI sambung (kode, v4)
        if gabung_idx:
            buang = set()
            for a, b in sorted(gabung_idx):
                blok[a]['text'] = ((blok[a].get('text') or '').strip() + ' '
                                   + (blok[b].get('text') or '').strip()).strip()
                blok[a]['lines'] = list(blok[a].get('lines') or []) + list(blok[b].get('lines') or [])
                for k in range(a + 1, b + 1):
                    buang.add(k)
            blok = [x for n, x in enumerate(blok) if n not in buang]
    # ── pagar ② (sisa): sesudah SEMUA pass, kalau tidak ada satu pun baris
    #    yang tersambung (blok == baris) ⇒ stitch tak berguna ⇒ teks apa adanya.
    #    (Dulu pagar ini dicek SEBELUM pass lintas-kosong, sehingga pass itu
    #    tidak pernah jalan bila _pecah_blok tidak menyambung apa pun —
    #    persis kasus fid=104. Diperbaiki 10 Nov 2026.)
    if len(blok) >= len(baris_asal):
        return teks
    return '\n'.join(b.get('text') or '' for b in blok)


def susun(fid, awal=None, akhir=None):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        bersih = state.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
        return _susun_dari_bersih(bersih, awal, akhir, getattr(fb, 'nama', ''))
    finally:
        db.close()


def _susun_dari_bersih(bersih, awal=None, akhir=None, nama='', pakai_stitch=None):
    """INTI `susun()` — bekerja dari TEKS yang sudah dibersihkan.

    Dipisahkan 14 Okt 2026 (Lapis 5) supaya `petakan_dari_teks()` bisa memakai
    logika yang SAMA PERSIS tanpa menyalin satu baris pun (satu sumber
    kebenaran). `susun(fid)` sekarang memanggil fungsi ini.

    ── PASS-1 STITCH (10 Nov 2026) ─────────────────────────────────────
    Teks disambung jadi BLOK dulu (`_stitch_baris`) sebelum dipecah baris —
    jadi satu paragraf tidak lagi jadi 3-5 kandidat. Baris hasil stitch
    adalah BLOK; indeks peta merujuk ke baris hasil stitch (konsisten di
    seluruh keluaran susun/petakan, sama seperti verifikasi 10 Okt).
    `pakai_stitch=False` (atau env EDUAI_JEV_STITCH=0) ⇒ cara lama.
    """
    if pakai_stitch is None:
        pakai_stitch = _stitch_aktif()
    teks_asal = bersih            # sidik cache dihitung dari teks SEBELUM stitch
    stitch_pakai = False
    waktu_stitch = 0.0
    if pakai_stitch and bersih:
        _t0_stitch = time.time()
        hasil_stitch = _stitch_baris(bersih)
        waktu_stitch = time.time() - _t0_stitch
        stitch_pakai = hasil_stitch is not bersih and hasil_stitch != bersih
        bersih = hasil_stitch
    baris = bersih.split('\n')
    if awal is None or awal < 0:
        awal = 0
    if akhir is None or akhir > len(baris):
        akhir = len(baris)

    def _t(j):
        if 0 <= j < len(baris):
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58]
        return '(tepi)'

    kand, gabung, buang, kode_label = [], {}, [], {}
    i = awal
    while i < akhir:
        s = baris[i].strip()
        if not s:
            i += 1
            continue
        if dibuang(s):
            buang.append(i)
            i += 1
            continue
        # ── NOMOR HALAMAN NEMPEL (WULAN-1, terukur live 10 Nov 2026) ─────
        #    "13 BAB I" / "13 1.1 Latar Belakang" — kupas awalan 1-3 digit
        #    HANYA untuk pencocokan pola; teks asli baris tidak diubah.
        s_pola = re.sub(r'^\d{1,3}\s+', '', s)
        m = POLA_BAB.match(s_pola)
        if m:
            j = i + 1
            while j < akhir and not baris[j].strip():
                j += 1
            if j < akhir:
                s2 = baris[j].strip()
                if s2 and s2 == s2.upper() and 4 < len(s2) < 70:
                    gabung[i] = (s_pola, s2)
                    i = j + 1
                    continue
            # BAB tanpa judul menyusul → tetap bab
            gabung[i] = (s_pola, '')
            i += 1
            continue
        # ── BARIS BERNOMOR DIBACA KODE (10 Nov 2026) ──────────────────
        #    Nomor bertingkat yang memenuhi syarat KETAT ⇒ 'subbab' langsung,
        #    TIDAK dikirim ke Jev (hemat + deterministik). Yang tidak memenuhi
        #    syarat tetap jadi kandidat Jev.
        if _nomor_bertindak_judul(s_pola):
            kode_label[i] = 'subbab'
            i += 1
            continue
        kand.append((i, s))
        i += 1
    return {'baris': baris, 'kand': kand, 'gabung': gabung, 'buang': buang,
            'kode_label': kode_label, 'stitch_pakai': stitch_pakai,
            'waktu_stitch': waktu_stitch,
            'teks_asal': teks_asal,
            'awal': awal, 'akhir': akhir, 'nama': nama, 't': _t}


def petakan_dari_teks(teks, awal=None, akhir=None, putaran=None):
    """PETA 3 TINGKAT dari TEKS LANGSUNG (tanpa fid) — untuk pintu LAYAR.

    Dipakai `app/peta3_jev.py::petakan_teks()` ← `versi._deteksi_bagian()`.
    ⚠️ Teks DIANGGAP SUDAH bersih (pemanggil sudah `buang_daftar_isi`).
    Cache: teks sama + aturan sama ⇒ peta lama dipakai (Rp 0, tanpa Jev).
    """
    if putaran is None:
        try:
            putaran = max(1, int(os.getenv('EDUAI_JEVI_PUTARAN') or '1'))
        except ValueError:
            putaran = 1
    kunci = _kunci_cache(teks or '', putaran)
    dari_cache = _cache_ambil(kunci)
    if dari_cache is not None:
        log.info('[peta3] peta dari cache (sidik %s…)', kunci[0][:8])
        return dari_cache
    d = _susun_dari_bersih(teks or '', awal, akhir, '')
    hasil = _petakan_dari_hasil(d, putaran)
    _cache_simpan(kunci, hasil)
    return hasil


def petakan(fid, awal=None, akhir=None, putaran=None):
    if putaran is None:
        try:
            putaran = max(1, int(os.getenv('EDUAI_JEVI_PUTARAN') or '1'))
        except ValueError:
            putaran = 1
    d = susun(fid, awal, akhir)
    kunci = _kunci_cache(d.get('teks_asal') or '\n'.join(d['baris']), putaran)
    dari_cache = _cache_ambil(kunci)
    if dari_cache is not None:
        log.info('[peta3] peta dari cache (fid=%s, sidik %s…)', fid, kunci[0][:8])
        return dari_cache
    hasil = _petakan_dari_hasil(d, putaran)
    _cache_simpan(kunci, hasil)
    return hasil


def _petakan_dari_hasil(d, putaran=None):
    """INTI `petakan()` — bekerja dari hasil `_susun_dari_bersih()`.

    Dipisahkan 14 Okt 2026 (Lapis 5) supaya jalur fid & jalur TEKS memakai
    logika yang SAMA PERSIS (nol salinan).

    ── PUTARAN=1 (14 Okt 2026, izin Bos) ────────────────────────────────
    AKAR masalah lambat (TERUKUR): naskah 145 KB → 4.138 kandidat → 40
    gelombang × `putaran=3` = **120 panggilan Jev** + jeda 0,7 dtk tiap
    panggilan ⇒ total 171 dtk.
    🎯 Bukti 3 putaran TIDAK BERGUNA — tertulis di kode ini sendiri (S1):
       "kesepakatan antar-putaran (itu terbukti SELALU 1,00)"
    ⇒ 2 dari 3 putaran = buang 114 dtk tanpa menambah informasi.
    Nilai bisa dikembalikan tanpa ubah kode: setel `EDUAI_JEVI_PUTARAN=3`.
    """
    if putaran is None:
        try:
            putaran = max(1, int(os.getenv('EDUAI_JEVI_PUTARAN') or '1'))
        except ValueError:
            putaran = 1
    baris, kand, _t = d['baris'], d['kand'], d['t']

    # ── bagi jadi gelombang ──
    gel, kini, kar = [], [], 0
    for n, (i, t) in enumerate(kand):
        pak = {'sebelum': _t(i - 1), 'tengah': ('L%06d| ' % i) + t[:70], 'sesudah': _t(i + 1)}
        skar = len(json.dumps(pak, ensure_ascii=False))
        if kini and (len(kini) >= BATAS_TANYA or kar + skar > BATAS_KAR):
            gel.append(kini)
            kini, kar = [], 0
        kini.append((n, i, pak))
        kar += skar
    if kini:
        gel.append(kini)

    semua = {i: [] for i, _t in kand}
    conf = {i: [] for i, _t in kand}      # S1: confidence Jev per kandidat
    waktu, gagal = [], 0
    for gi, g in enumerate(gel):
        paket = {}
        tanya = {}
        for n, i, pak in g:
            nm = 'c%d' % n
            paket[nm] = pak
            tanya[nm] = {'type': 'choice',
                         'instructions': 'Baris `%s.tengah` ada di dalam naskah akademik. '
                                         'Baris tengah ini perannya apa?' % nm,
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        for k in range(putaran):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan, tanya) or {}
            waktu.append(time.time() - t0)
            if not jw:
                gagal += 1
            for n, i, _p in g:
                jw_i = jw.get('c%d' % n) or {}
                v = jw_i.get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                semua[i].append(v)
                # ── S1 (putusan Bos 09 Okt): SIMPAN `confidence` Jev per label.
                #    ALASAN: hakim hanya perlu memeriksa kandidat yang RAGU
                #    (p < ambang) ⇒ hemat biaya. `confidence` SUDAH dikirim Jev
                #    di balasan yang sama ⇒ S1 = NOL panggilan tambahan.
                #    ⚠️ Terukur: conf Jev 0,36–0,99 (rata 0,839) ⇒ BUKAN 1,00 selalu.
                #    Sejak v4: None ikut disimpan supaya `conf[i]` sejajar
                #    dengan `semua[i]` (pasangan suara-confidence).
                c = jw_i.get('confidence')
                conf[i].append(float(c) if isinstance(c, (int, float)) else None)
            _tidur_adaptif(t0)

    def _hitung_label():
        """Label + goyang + p dari `semua`/`conf` saat ini (dipakai ulang
        sesudah tanya-ulang bertarget).

        ── SUARA BERBOBOT CONFIDENCE (v4, 10 Nov 2026) ──────────────────
        Dulu: 2 suara berbeda -> label dipaksa 'biasa'. Terukur live fid=81:
        tanya-ulang membalik label asli (PARAGRAF 157 -> 144) karena suara
        kedua yang TIDAK YAKIN menimpa suara pertama. Sekarang suara yang
        menang = yang confidence-nya paling tinggi; seri -> suara pertama.
        Daftar `goyang` TETAP dicatat untuk diperiksa manusia.
        """
        lab, goy, p_lab = {}, [], {}
        for i, _t in kand:
            pasangan = [(v, c) for v, c in zip(semua[i], conf[i]) if v]
            skor, urutan = {}, {}
            for urut, (v, c) in enumerate(pasangan):
                s = float(c) if isinstance(c, (int, float)) else 0.0
                if v not in skor or s > skor[v]:
                    skor[v] = s
                if v not in urutan:
                    urutan[v] = urut
            utama = None
            if skor:
                utama = max(skor, key=lambda v: (skor[v], -urutan[v]))
            if len(skor) > 1:
                goy.append((i, semua[i]))
            lab[i] = utama if utama in ('bab', 'subbab', 'paragraf') else 'biasa'
            cs = [c for c in conf[i] if isinstance(c, (int, float))]
            p_lab[i] = round(sum(cs) / len(cs), 3) if cs else None
        return lab, goy, p_lab

    label, goyang, p_label = _hitung_label()

    # ── TANYA-ULANG BERTARGET BERGELOMBANG (v5, ganti 1 gelombang v4) ───
    #    Putaran global 3× TERBUKTI tidak berguna (kesepakatan antar-putaran
    #    selalu 1,00 ⇒ buang 114 dtk). Yang berguna: tanya ULANG hanya pada
    #    kandidat yang goyang atau p rendah.
    #    p < 0,5 = Jev sendiri tidak yakin (titik tengah netral 0..1, BUKAN
    #    ambang yang disetel per naskah); p None = Jev tidak menjawab.
    #    MASALAH v4: satu gelombang cap 120 — di fid=115 ragu > 120, jadi
    #    kandidat paling ragu di akhir naskah tidak sempat ditanya.
    #    OBAT v5: gelombang KECIL berulang (≤120 per gelombang, maks 3
    #    gelombang bawaan). Tiap gelombang: hitung ulang ragu dari p
    #    TERKINI, lewati yang sudah ditanya, ambil 120 paling tidak yakin.
    #    Yang sudah membaik (p ≥ 0,5) sesudah gelombang sebelumnya TIDAK
    #    ditanya lagi ⇒ panggilan tidak terbuang. Biaya: 1 panggilan Jev
    #    per gelombang, paling banyak 3 (env EDUAI_JEV_TANYA_ULANG_MAKS_GELOMBANG).
    tanya_ulang_jml = 0
    tanya_ulang_gelombang = 0
    if putaran == 1 and _tanya_ulang_aktif():
        sudah_ditanya = set()
        for _gel in range(_maks_gelombang_tanya_ulang()):
            ragu_idx = [i for i, _t in kand
                        if i not in sudah_ditanya
                        and (p_label.get(i) is None or (p_label.get(i) or 0) < 0.5)]
            # ── URUT p NAIK: yang paling tidak yakin ditanya dulu.
            ragu_idx.sort(key=lambda i: (p_label.get(i) is not None,
                                         p_label.get(i) or 0))
            ragu_idx = ragu_idx[:BATAS_TANYA]
            if not ragu_idx:
                break
            tanya_ulang_gelombang += 1
            tanya_ulang_jml += len(ragu_idx)
            sudah_ditanya.update(ragu_idx)
            paket = {}
            tanya = {}
            for n, i in enumerate(ragu_idx):
                nm = 'c%d' % n
                paket[nm] = {'sebelum': _t(i - 1),
                             'tengah': ('L%06d| ' % i) + baris[i].strip()[:70],
                             'sesudah': _t(i + 1)}
                tanya[nm] = {'type': 'choice',
                             'instructions': 'Baris `%s.tengah` ada di dalam naskah akademik. '
                                             'Baris tengah ini perannya apa?' % nm,
                             'criteria': dict(KRITERIA)}
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(json.dumps(paket, ensure_ascii=False), tanya) or {}
            waktu.append(time.time() - t0)
            if not jw:
                gagal += 1
            for n, i in enumerate(ragu_idx):
                jw_i = jw.get('c%d' % n) or {}
                v = jw_i.get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                semua[i].append(v)
                c = jw_i.get('confidence')
                conf[i].append(float(c) if isinstance(c, (int, float)) else None)
            _tidur_adaptif(t0)
            label, goyang, p_label = _hitung_label()

    # ── ATURAN 2 (vonis Bos 09 Okt) — KOREKSI LABEL, BUKAN SARINGAN BUANG.
    #    Judul sub-bab hampir selalu PENDEK. Kalau Jev bilang 'subbab' tapi
    #    barisnya PANJANG (>ambang profil kampus, bawaan 300 kar), itu paragraf
    #    asli ⇒ label diubah.
    #    ⛔ JANGAN dibuang: paragraf asli sering >300 kar (bencana Uji 8).
    koreksi = []
    for i, _t in kand:
        if label.get(i) == 'subbab' and len(baris[i].strip()) > _ambang('judul_maks_kar', 300):
            label[i] = 'paragraf'
            koreksi.append(i)

    # ── ATURAN 4 SPSS (vonis Bos 09 Okt) — KOREKSI LABEL, BUKAN BUANG.
    #    Header output SPSS (Inggris) bukan sub-bab skripsi. DIDEMOSI jadi
    #    'biasa', TIDAK dibuang. Daftar TERTUTUP (bukan whack-a-mole):
    #    sub-bab Indonesia ("Uji Reliabilitas") tak akan cocok sebab
    #    daftarnya Bahasa Inggris.
    koreksi_spss = []
    for i, _t in kand:
        if label.get(i) == 'subbab' and _spss_header(baris[i]):
            label[i] = 'biasa'
            koreksi_spss.append(i)

    # ── D1 (putusan Bos 09 Okt): TANDAI blok SISTEMATIKA — JANGAN BUANG.
    sistematika = _tandai_sistematika(baris, label, kand)

    # ── ATURAN 5 (vonis Bos 09 Okt) — KOREKSI LABEL, BUKAN BUANG.
    #    Baris diawali HURUF KECIL tidak pernah jadi awal BAB/SUB-BAB:
    #    itu LANJUTAN kalimat (atau patahan ekstraksi PDF).
    #    ⛔ Deterministik, NOL risiko buang — hanya mengubah label.
    #    Terukur naskah Wulandari fid=112 (PDF): 116 error tertangkap
    #    (38 sub-bab + 78 paragraf diawali huruf kecil).
    koreksi_kecil = []
    for i, _t in kand:
        if i in sistematika:
            continue                      # blok sistematika jangan disentuh
        t = baris[i].strip()
        if label.get(i) in ('bab', 'subbab') and _huruf_awal_kecil(t):
            label[i] = 'biasa'
            koreksi_kecil.append(i)

    asal = {}
    boleh = {}
    kode_label = d.get('kode_label') or {}
    for i, _t in kand:
        if i in sistematika:
            asal[i] = 'sistematika'
            boleh[i] = False      # boleh dipakai fitur? TIDAK
        else:
            asal[i] = 'jev'
            boleh[i] = True
    # ── BARIS BERNOMOR (kode) masuk label + asal — TIDAK pernah ke Jev.
    for i, lab in kode_label.items():
        label[i] = lab
        p_label[i] = None        # bukan confidence Jev — jangan dicampur
        asal[i] = 'kode'
        boleh[i] = True

    # ── JEV MATI TOTAL: semua gelombang gagal ⇒ pemanggil WAJIB fallback
    #    (dulu: semua label 'biasa' tanpa jejak ⇒ hakim/pemutus jalur tak
    #    bisa bedakan "peta memang tanpa judul" vs "Jev gagal").
    jev_mati = bool(gel) and gagal >= len(gel) * max(1, putaran)

    return {'baris': baris, 'kand': kand, 'label': label, 'goyang': goyang,
            'p': p_label,                      # S1: confidence Jev per label
            'koreksi_label': koreksi, 'koreksi_spss': koreksi_spss,
            'koreksi_kecil': koreksi_kecil,
            'sistematika': sorted(sistematika), 'asal': asal, 'boleh_dipakai_fitur': boleh,
            'gabung': d['gabung'], 'buang': d['buang'], 'waktu': waktu, 'gagal': gagal,
            # ── v4: `waktu` HANYA gelombang klasifikasi. Terukur live
            #    fid=115: waktu jumlah 9,52 dtk vs waktu Jev nyata 33,7 dtk
            #    (sisanya stitch). Sekarang stitch tercatat terpisah.
            'waktu_stitch': round(d.get('waktu_stitch', 0.0), 3),
            'waktu_total': round(d.get('waktu_stitch', 0.0) + sum(waktu), 3),
            'gelombang': len(gel), 'semua': semua, 'awal': d['awal'], 'akhir': d['akhir'],
            'nama': d['nama'], 'kand_jml': len(kand),
            'kode_label': kode_label, 'tanya_ulang_jml': tanya_ulang_jml,
            'tanya_ulang_gelombang': tanya_ulang_gelombang,
            'jev_mati': jev_mati, 'stitch_pakai': d.get('stitch_pakai', False),
            'versi_aturan': RULE_VERSION}


def main():
    fid = int(sys.argv[1])
    awal = int(sys.argv[2]) if len(sys.argv) > 2 else None
    akhir = int(sys.argv[3]) if len(sys.argv) > 3 else None
    jdl = sys.argv[4] if len(sys.argv) > 4 else 'NASKAH'
    sorot = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 5 else []
    r = petakan(fid, awal, akhir)
    emo = {'bab': 'B', 'subbab': 'S', 'paragraf': 'P', 'biasa': '.'}
    print('=' * 72)
    print('PETA 3 TINGKAT — %s (fid=%d) %s-%s' % (jdl, fid, r['awal'], r['akhir']))
    print('   kandidat %d · gelombang %d · gabung %d · buang %d · gagal %d'
          % (r['kand_jml'], r['gelombang'], len(r['gabung']), len(r['buang']), r['gagal']))
    print('   waktu: %s · stitch %.1f dtk · total %.1f dtk'
          % (' '.join('%.1f' % w for w in r['waktu']),
             r.get('waktu_stitch', 0.0), r.get('waktu_total', 0.0)))
    print('   GOYANG: %d' % len(r['goyang']))
    for i, v in r['goyang'][:12]:
        print('      L%06d %s | %s' % (i, v, r['baris'][i].strip()[:40]))
    hitung = {}
    for i, v in r['label'].items():
        hitung[v] = hitung.get(v, 0) + 1
    print('   HITUNG: %s' % hitung)
    print('   LABEL (bukan biasa):')
    for i, v in sorted(r['label'].items()):
        if v != 'biasa':
            print('      [%s] L%06d %s' % (emo[v], i, r['baris'][i].strip()[:48]))
    if sorot:
        print('   SOROT BOS:')
        for t in sorot:
            if t in r['gabung']:
                print('      L%06d GABUNG: %s' % (t, ' '.join(r['gabung'][t])))
            elif t in r['buang']:
                print('      L%06d DIBUANG' % t)
            elif t in r['label']:
                print('      L%06d [%s] %s' % (t, emo[r['label'][t]], r['baris'][t].strip()[:44]))
            else:
                print('      L%06d tidak jadi kandidat' % t)


if __name__ == '__main__':
    main()
