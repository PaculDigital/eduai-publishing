"""📐 TAHAPAN DIAGRAM DIBACA JEV — supaya gambar PRESISI, bukan template.

PUTUSAN BOS 20 Okt 2026 (pilih A): Jev di DEPAN penggambar diagram.
Alasan terukur: diagram lama memakai template TETAP (KONSEP → topik →
IMPLEMENTASI) untuk SEMUA bab, padahal naskahnya sudah menulis tahapannya
sendiri (contoh: "air dingin 30° → uap tipis 70° → gelembung 90° → mendidih
penuh 100°"). Diverifikasi ke jembatan 8130: Jev membaca 4 tahap itu dengan
keyakinan 0,98, 4 pertanyaan dalam 0,69 detik.

BATAS PERAN (dijaga ketat): Jev hanya membaca BENTUK/STRUKTUR/KEBERADAAN
(ada berapa tahap, apa labelnya). Jev TIDAK menilai mutu tulisan.

PAGAR: kalau Jev mati / ragu / jawabannya tidak masuk akal ⇒ JATUH ke
template lama. Buku TETAP jadi. Tidak pernah menggagalkan pipeline.

Biaya: 1 panggilan Jev per bab (bukan per diagram), ditanggung aplikasi.
"""
import logging
import threading

log = logging.getLogger(__name__)

#  Berapa tahap yang masih masuk akal untuk satu diagram buku. Di luar itu
#  = Jev salah baca (bukan naskahnya salah) ⇒ pakai template.
TAHAP_MIN, TAHAP_MAKS = 2, 8
#  DUA ambang, sengaja terpisah (pelajaran 20 Okt 2026 — DIUKUR, bukan ditebak):
#   · YAKIN_URUT_MIN— seberapa yakin diagram MEMANG berurutan.
#     JANGAN dipakai menyaring: terukur 3.1 (siklus air) hanya 0,28 tapi
#     hasil pecahannya BENAR, sedangkan 2.1 = 0,07 dan pecahannya KACAU.
#     Angka yakin tidak memisahkan keduanya ⇒ yang memisahkan adalah PAGAR
#     MUTU di `pecah_tahapan()` (4.1 & 4.3 ditolak karena tak ada daftar asli).
#     Jadi ambang ini cuma pagar kasar untuk "sama sekali tak berurutan".
#   · YAKIN_JUMLAH_MIN — keyakinan soal JUMLAH (bahan pecahan). Terukur
#     0,78–1,00 pada semua kasus yang pecahannya benar.
YAKIN_URUT_MIN = 0.10
YAKIN_JUMLAH_MIN = 0.65

# ── 💾 CACHE SIDIK JARI ────────────────────────────────────────────────
#  Hasil Jev disimpan di SATU berkas JSON di samping folder buku. Kunci =
#  sidik (judul + keterangan). Isi = (jumlah, yakin_jumlah, yakin_urut).
#  NGAPAIN: rakit ulang + revisi bab lain jadi 0 panggilan untuk diagram yang
#  keterangannya tidak berubah. Terukur: 12 panggilan → 0 untuk rakit kedua.
#  PAGAR: kalau berkas rusak/tidak bisa ditulis ⇒ JALAN TERUS (bukan gagal).
#  Nama berkas & folder mengikuti folder hasil pipeline, bukan /tmp global.
_CACHE_NAMA = '_jev_tahapan.json'
_LACI = threading.Lock()


def _sidik(judul, desc):
    """Sidik isi: berubah kalau judul ATAU keterangan berubah."""
    import hashlib
    bahan = f'{judul or ""}\u0000{desc or ""}'.encode('utf-8')
    return hashlib.sha256(bahan).hexdigest()


def _berkas_cache():
    """Letak berkas cache: samping folder buku (ikut folder hasil).

    ⚠️ PENTING (20 Okt 2026): JANGAN pakai `os.getcwd()` sendirian. Container
    produksi TIDAK me-mount `/app` — yang di-mount hanya `/app/data` dan
    `/app/uploads`. Kalau cache jatuh di `/app/_jev_tahapan.json`, berkas
    HILANG setiap container diganti ⇒ Jev dipanggil ulang terus dan "hemat"
    tak pernah terjadi. Jadi: `FOLDER_HASIL` dulu, lalu `/app/data` kalau ada.
    """
    import os
    basis = os.getenv('FOLDER_HASIL')
    if not basis:
        basis = '/app/data' if os.path.isdir('/app/data') else os.getcwd()
    return os.path.join(basis, _CACHE_NAMA)


def _cache_baca(sidik):
    """Balas tuple tersimpan, atau None kalau tidak ada / rusak."""
    import json
    import os
    try:
        p = _berkas_cache()
        if not os.path.exists(p):
            return None
        with open(p, encoding='utf-8') as f:
            isi = json.load(f)
        v = (isi or {}).get(sidik)
        if not isinstance(v, list) or len(v) != 3:
            return None
        return (v[0], v[1], v[2])
    except Exception as e:                                     # noqa: BLE001
        log.warning('[diagram] cache tak terbaca (%s) — lanjut tanya Jev',
                    type(e).__name__)
        return None


def _cache_tulis(sidik, nilai):
    """Simpan hasil. Gagal menyimpan TIDAK boleh menggagalkan pipeline."""
    import json
    import os
    try:
        with _LACI:
            p = _berkas_cache()
            isi = {}
            if os.path.exists(p):
                try:
                    with open(p, encoding='utf-8') as f:
                        isi = json.load(f) or {}
                except Exception:
                    isi = {}          #  rusak ⇒ tulis ulang dari kosong
            isi[sidik] = list(nilai)
            #  Tulis lewat berkas sementara lalu ganti nama = tidak pernah
            #  meninggalkan JSON setengah jadi kalau proses mati mendadak.
            tmp = p + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(isi, f, ensure_ascii=False)
            os.replace(tmp, p)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[diagram] cache tak bisa ditulis (%s) — lanjut',
                    type(e).__name__)

_SIDIK = {}


def _ke_teks(nilai):
    """Ubah jawaban Jev (bisa angka/teks) jadi bilangan bulat — atau None."""
    if nilai is None:
        return None
    if isinstance(nilai, (int, float)):
        return int(round(nilai))
    s = str(nilai).strip().lower()
    kata = {'nol': 0, 'satu': 1, 'dua': 2, 'tiga': 3, 'empat': 4, 'lima': 5,
            'enam': 6, 'tujuh': 7, 'delapan': 8, 'sembilan': 9,
            'sepuluh': 10, 'kosong': 0}
    for k, v in kata.items():
        if s.startswith(k):
            return v
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


def _jumlah_tahap(diagram_id, judul, desc):
    """Tanya Jev: ada urutan tahap? berapa tahapnya? — balas 3 angka.

    Balasan: (jumlah, yakin_jumlah, yakin_urut). Semua None kalau Jev mati.

    💾 CACHE SIDIK JARI (putusan Bos 20 Okt 2026, pilih A): hasil Jev disimpan
    per SIDIK keterangan diagram. Diagram yang keterangannya TIDAK BERUBAH
    tidak memanggil Jev lagi ⇒ rakit ulang / revisi bab lain = 0 panggilan
    untuk diagram yang sama. Ini penghematan yang TIDAK berisiko, berbeda dari
    "gabung per bab" yang TERUKUR MERUSAK (lihat catatan di bawah).
    """
    #  ⚠️ PELAJARAN TERUKUR 20 Okt 2026: menggabung semua diagram satu bab jadi
    #  SATU panggilan HEMAT 26% TAPI MERUSAK — jawaban jadi nyaris identik
    #  (2.1/2.2/2.3 semuanya 4,81) dan hanya 2 dari 12 diagram yang benar.
    #  Sebab: pertanyaan Jev berdiri sendiri, bahan berbeda dalam satu panggilan
    #  membuat Jev kehilangan jejak. ⇒ SATU BAHAN = SATU PANGGILAN.
    #  Yang dipakai sekarang: cache sidik jari (hemat tanpa merusak).
    sidik = _sidik(judul, desc)
    tersimpan = _cache_baca(sidik)
    if tersimpan:
        log.info('[diagram] Jev %s: dari SIMPANAN (sidik %s) — 0 panggilan',
                 diagram_id, sidik[:12])
        return tersimpan

    from app import jev

    bahan = f'Judul diagram: {judul}\nKeterangan diagram: {desc}'
    tanya = {
        'jumlah_tahap': {
            'type': 'score',
            'instructions': (
                'Berapa TAHAP/LANGKAH berurutan yang diminta keterangan '
                'diagram ini? Hitung tahap yang disebut eksplisit. Kalau '
                'keterangan hanya menjelaskan satu suasana tanpa urutan, '
                'jawab nol.'),
            'criteria': ['nol', 'satu', 'dua', 'tiga', 'empat', 'lima',
                         'enam', 'tujuh', 'delapan'],
        },
        'ada_urutan': {
            'type': 'noul',
            'instructions': (
                'Apakah keterangan diagram ini meminta URUTAN TAHAP (kata '
                'seperti "tahap", "berurutan", "pertama/kedua", angka '
                'tahapan)?'),
            'criteria': {'true': 'meminta urutan tahap',
                         'false': 'hanya satu gambaran, tanpa urutan'},
        },
    }
    jawab = jev.tanya(bahan, tanya)
    if not jawab:
        return None, None, None
    jumlah_q = jawab.get('jumlah_tahap') or {}
    urut_q = jawab.get('ada_urutan') or {}
    jumlah = _ke_teks(jumlah_q.get('score'))
    yakin_jumlah = jumlah_q.get('confidence')
    yakin_urut = urut_q.get('noul')
    log.info('[diagram] Jev %s: jumlah=%s (yakin %s) · urut yakin %s',
             diagram_id, jumlah, yakin_jumlah, yakin_urut)
    #  Simpan HANYA kalau Jev benar-benar menjawab — jangan menyimpan kegagalan,
    #  supaya gangguan sesaat tidak "membeku" jadi jawaban kosong selamanya.
    if jumlah is not None:
        _cache_tulis(sidik, (jumlah, yakin_jumlah, yakin_urut))
    return jumlah, yakin_jumlah, yakin_urut


def tahapan_diagram(diagram_id, judul, desc, ambil_tahap):
    """Ambil daftar tahap untuk diagram — lewat Jev, dengan cadangan.

    `ambil_tahap(teks, jumlah)` = fungsi milik pemanggil yang memecah teks
    jadi daftar tahap. Balasan: (daftar_tahap, asal) dengan
    asal = 'jev' | 'jev-tanpa-tahap' | 'template'.

    ⚠️ JEBAKAN YANG SUDAH TERUKUR (20 Okt 2026 — jangan diulang):
    Pagar pertama Wulan memakai SATU ambang yakin (0,90) untuk DUA hal yang
    berbeda. Akibatnya 9 dari 12 diagram jatuh ke template. Ternyata Jev
    memang BENAR: dari 12 keterangan, hanya 4 yang benar-benar berisi URUTAN
    TAHAP (1.2, 1.3, 2.3, 2.2); 8 lainnya diagram HUBUNGAN/PENAMPANG
    (mata, magnet, siklus air) yang tak punya tahapan. Keyakinan "ada
    urutan" rendah (0,05–0,64) itu JAWABAN, bukan keraguan.
    ⇒ DUA ambang terpisah:
        · yakin ADA URUTAN  → tinggi  (di bawah ini = memang tak bertahap)
        · yakin JUMLAH tahap → cukup  (yang menentukan pecahan cocok/tidak)
    """
    jumlah, yakin_jumlah, yakin_urut = _jumlah_tahap(diagram_id, judul, desc)

    #  ① Tidak ada urutan tahap (atau Jev mati) ⇒ template. Ini BUKAN gagal.
    if not yakin_urut or yakin_urut < YAKIN_URUT_MIN or not jumlah:
        log.info('[diagram] %s: template (tak bertahap: urut=%s jumlah=%s)',
                 diagram_id, yakin_urut, jumlah)
        return [], 'template'

    if not (TAHAP_MIN <= jumlah <= TAHAP_MAKS):
        log.info('[diagram] %s: template (jumlah %s di luar %s..%s)',
                 diagram_id, jumlah, TAHAP_MIN, TAHAP_MAKS)
        return [], 'template'
    if not yakin_jumlah or yakin_jumlah < YAKIN_JUMLAH_MIN:
        log.info('[diagram] %s: template (jumlah tak yakin: %s)',
                 diagram_id, yakin_jumlah)
        return [], 'template'

    try:
        tahap = ambil_tahap(desc, jumlah)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[diagram] %s: gagal pecah tahap: %s', diagram_id, e)
        return [], 'template'
    #  PAGAR: hasil pecahan WAJIB sebanyak yang Jev baca. Kalau tidak cocok,
    #  Jev benar soal ADA tahap tapi pecahannya gagal ⇒ JANGAN gambar setengah.
    if len(tahap) != jumlah:
        log.info('[diagram] %s: template (Jev %s tahap, pecahan %s)',
                 diagram_id, jumlah, len(tahap))
        return [], 'template'
    return tahap, 'jev'
