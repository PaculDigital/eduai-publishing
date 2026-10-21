"""PROSES AI DI LATAR BELAKANG — Langkah A (ACC Bos 16Sep26).

═══ KENAPA MODUL INI ADA (akar masalah, TERUKUR — bukan dugaan) ═══

Revisi naskah besar dulu berjalan SINKRON: satu HTTP request menunggu AI
sampai selesai. Bukti nyata 16Sep26 lewat domain publik:

    naskah 65.932 karakter → 2 bagian → AI dipanggil
    → Cloudflare memutus koneksi di 125 detik (HTTP 524)
    → user lihat "error code: 524"
    → kuota SUDAH dipotong 9→7 (pemakaian_ai berubah)
    → revisi_history = 0 · versi_dokumen TIDAK bertambah
    ⇒ mahasiswa BAYAR tapi TIDAK dapat hasil.

Menaikkan AI_TIMEOUT_DETIK=420 TIDAK menolong: yang memutus Cloudflare,
bukan aplikasi. Batas Cloudflare hanya bisa dinaikkan sampai 100 detik
(Network → HTTP Response Timeout), dan selalu ada naskah yang lebih besar.

═══ SOLUSI (RANCANGAN BOS SENDIRI — MASTER_PLAN §4.12 poin F) ═══

Bos menulis: "KEDUANYA (skeleton jika ditunggui + boleh ditinggal, proses
jalan di server, hasil disimpan + notifikasi)."

Jadi: request user hanya MENITIPKAN pekerjaan → dibalas pendek dan cepat
("sedang diproses") → Cloudflare tidak pernah memutus. Pekerjaan dikerjakan
di LATAR BELAKANG lewat utas (thread); halaman memantau keadaannya.

═══ MENGAPA THREAD, BUKAN CELERY/REDIS ═══
Aturan Bos: TANPA dependency baru — container produksi Python murni stdlib.
`threading.Thread` sudah ada di stdlib, cukup untuk beban puluhan mahasiswa.
Kalau nanti ratusan sekaligus, baru pikirkan antrean sungguhan — dan itu
keputusan Bos, bukan diam-diam diubah Wulan.

═══ ATURAN YANG DIPATUHI ═══
1. JALUR AI TETAP SATU PINTU (9router). Utas ini memanggil fungsi revisi
   yang sudah ada — tidak membuat jalur AI kedua.
2. HASIL DISIMPAN DI TABEL `proses_ai`, bukan langsung ke .docx. Alasannya:
   user yang meninggalkan halaman lalu kembali tidak boleh menemukan
   dokumennya berubah sendiri tanpa dia tahu (rancangan §4.12: "saat user
   kembali, dokumen sudah terisi" — tapi user harus DIBERI TAHU).
3. `tahap` = TAHAP NYATA (Membaca → Menulis bagian N → Memeriksa → Selesai),
   BUKAN persentase karangan (§4.12: "Progress: pakai TAHAP NYATA").
4. KUOTA: DIPOTONG SEBELUM kerja (gerbang biaya lama, tidak diubah), TAPI
   DIKEMBALIKAN kalau procses gagal — termasuk kegagalan yang dulu tak
   tertangkap (koneksi putus / utas mati). Inilah jaminan uang mahasiswa.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import threading
import traceback
from collections import deque
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select

from .models import ProsesAI, SessionLocal

log = logging.getLogger('eduai.proses')

# ─ Keadaan yang DITAMPILKAN ke user (bahasa manusia, bukan kode) ──────────
TAHAP_MENUNGGU = 'Menunggu antrean'
TAHAP_MEMBACA = 'Membaca naskah'
TAHAP_MENYUSUN = 'Menyusun rencana revisi'
TAHAP_MEMERIKSA = 'Memeriksa hasil'
TAHAP_SELESAI = 'Selesai'
TAHAP_GAGAL = 'Gagal'


def tahap_menulis(ke: int, dari: int) -> str:
    """Kalimat tahap saat AI menulis bagian ke-N.

    SENGAJA menyebut "bagian ke-N dari M" (bukan "Bagian N") supaya mahasiswa
    paham naskahnya memang dikerjakan bertahap — dan tidak menyangka macet.
    """
    if dari <= 1:
        return 'Menulis hasil revisi'
    return f'Menulis bagian ke-{ke} dari {dari}'


def kode_baru() -> str:
    """Kode acak untuk URL status (bukan id berurutan → tidak bisa ditebak)."""
    return secrets.token_urlsafe(16)[:24]


# ══════════════════════════════════════════════════════════════════════════
#  BAGIAN 1 — CATATAN PROSES (dipakai endpoint & utas)
# ══════════════════════════════════════════════════════════════════════════

def mulai(db, *, user_id: int, file_id: Optional[int], komentar: list,
          jenis_dokumen: str = '', jumlah_bagian: int = 1,
          panjang: int = 0) -> ProsesAI:
    """Buat catatan proses baru berstatus 'menunggu'.

    Dipanggil SEBELUM utas dijalankan. Sengaja commit dulu: kalau utas
    langsung jalan dan server mati, catatannya tetap ada (tidak ada
    pekerjaan "hantu" yang tidak bisa dilacak).
    """
    p = ProsesAI(
        kode=kode_baru(),
        user_id=user_id,
        file_id=file_id,
        status='menunggu',
        tahap=TAHAP_MENUNGGU,
        komentar_json=json.dumps(komentar, ensure_ascii=False),
        jenis_dokumen=jenis_dokumen or '',
        jumlah_bagian=max(1, int(jumlah_bagian or 1)),
        panjang=int(panjang or 0),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _sesi_baru():
    """Sesi DB BARU untuk utas.

    ⚠️ WAJIB sesi baru: sesi milik request HTTP akan DITUTUP begitu request
    selesai — memakainya di utas lain = error 'session closed' yang sulit
    dilacak. Pelajaran ini sudah pernah kena di proyek ini.
    """
    return SessionLocal()


def ambil(db, kode: str, user_id: Optional[int] = None) -> Optional[ProsesAI]:
    """Ambil proses berdasarkan kode. Kalau `user_id` diisi → pastikan miliknya.

    Pemeriksaan pemilik WAJIB: tanpa itu, siapa pun yang tahu kodenya bisa
    membaca hasil revisi orang lain.
    """
    q = select(ProsesAI).where(ProsesAI.kode == kode)
    if user_id is not None:
        q = q.where(ProsesAI.user_id == user_id)
    return db.execute(q.limit(1)).scalar_one_or_none()


def ubah_tahap(kode: str, tahap: str, *, bagian_ke: int | None = None,
               status: str | None = None) -> None:
    """Perbarui tahap yang dilihat user. Aman dipanggil dari utas."""
    db = _sesi_baru()
    try:
        p = ambil(db, kode)
        if p is None:
            return
        p.tahap = tahap
        if bagian_ke is not None:
            p.bagian_ke = int(bagian_ke)
        if status is not None:
            p.status = status
        db.commit()
    except Exception as e:                                        # noqa: BLE001
        log.warning('[proses] ubah_tahap gagal: %s', e)
    finally:
        db.close()


def tandai_selesai(kode: str, *, hasil: str, hasil_json: str = '',
                   model_ai: str = '', token_in: int = 0,
                   token_out: int = 0, token_revisi: int = 0) -> None:
    """Tandai proses SELESAI beserta hasilnya.

    Hasil disimpan di sini dulu (bukan langsung ditulis ke .docx) — lihat
    penjelasan di kepala modul, poin 2.
    """
    db = _sesi_baru()
    try:
        p = ambil(db, kode)
        if p is None:
            return
        p.status = 'selesai'
        p.tahap = TAHAP_SELESAI
        p.hasil = hasil or ''
        p.hasil_json = hasil_json or ''
        p.model_ai = model_ai or ''
        p.token_in = int(token_in or 0)
        p.token_out = int(token_out or 0)
        p.token_revisi = int(token_revisi or 0)
        p.selesai = datetime.utcnow()
        p.dibaca = 0                    # belum dibaca → lonceng menyala
        #  Simpan dulu pekerjaan utama.
        db.commit()
        #  🔔 Pemicu notifikasi (ACC Bos 17Sep26) — SESI SENDIRI.
        #  ⚠️ Jangan pakai `db` yang sama: `catat()` bisa rollback saat gagal,
        #  dan itu akan membatalkan status 'selesai' yang baru disimpan.
        _simpan_notifikasi(p.user_id, 'revisi_selesai',
                           bagian=_bagian_dari(p), file_id=p.file_id)
    except Exception as e:                                        # noqa: BLE001
        log.warning('[proses] tandai_selesai gagal: %s', e)
    finally:
        db.close()


def tandai_gagal(kode: str, galat: str) -> None:
    """Tandai proses GAGAL + simpan alasannya.

    Alasan disimpan supaya kuota bisa dikembalikan DENGAN BUKTI, dan supaya
    mahasiswa dapat penjelasan yang jujur (bukan "terjadi kesalahan").
    """
    db = _sesi_baru()
    try:
        p = ambil(db, kode)
        if p is None:
            return
        p.status = 'gagal'
        p.tahap = TAHAP_GAGAL
        p.galat = (galat or '')[:2000]
        p.selesai = datetime.utcnow()
        #  🐛 17Sep26: WAJIB diset 0 — kalau proses ini sebelumnya pernah
        #  ditandai 'dibaca' (mis. user sudah buka lonceng saat status masih
        #  'jalan'), lonceng TIDAK akan menyala walau prosesnya gagal.
        #  Mahasiswa jadi tidak tahu revisinya gagal. `belum_dibaca()`
        #  menyaring `dibaca == 0`, jadi baris ini yang menjamin notifikasi
        #  gagal benar-benar muncul.
        p.dibaca = 0
        db.commit()
        #  🔔 Pemicu notifikasi (ACC Bos 17Sep26) — SESI SENDIRI,
        #  supaya kegagalan mencatat notifikasi tidak bisa merusak
        #  status 'gagal' + pengembalian kuota yang baru disimpan.
        _simpan_notifikasi(p.user_id, 'revisi_belum_berhasil',
                           alasan=p.galat, file_id=p.file_id)
    except Exception as e:                                        # noqa: BLE001
        log.warning('[proses] tandai_gagal gagal: %s', e)
    finally:
        db.close()


def _simpan_notifikasi(user_id: int, nama_jenis: str, **data) -> None:
    """Catat notifikasi memakai SESI SENDIRI — selalu aman.

    KENAPA DIPISAH: `notifikasi.catat()` bisa memanggil `rollback()` saat
    penulisan gagal. Kalau ia memakai sesi milik pemanggil, rollback itu
    akan MEMBATALKAN pekerjaan utama (status proses, potongan kuota) yang
    baru saja di-commit — kerugian yang jauh lebih besar daripada sekadar
    kehilangan satu notifikasi. Sesi terpisah menutup celah itu.
    """
    try:
        from .notifikasi import catat
        db2 = _sesi_baru()
        try:
            if catat(db2, user_id, nama_jenis, **data):
                db2.commit()
        finally:
            db2.close()
    except Exception as e:                                        # noqa: BLE001
        log.warning('[notifikasi] simpan %s gagal (diabaikan): %s', nama_jenis, e)


def tandai_dibaca(db, kode: str, user_id: int) -> bool:
    """Tandai hasil sudah dibaca user → lonceng berhenti menyala."""
    p = ambil(db, kode, user_id)
    if p is None or p.status != 'selesai':
        return False
    if not p.dibaca:
        p.dibaca = 1
        db.commit()
    return True


def belum_dibaca(db, user_id: int) -> list:
    """Daftar proses yang PERLU DIBERITAHUKAN ke user — untuk LONCENG.

    ACC Bos 16Sep26: notifikasi lewat lonceng di web (WA nanti saja).

    🐛 AKAR YANG DITUTUP 17Sep26 (temuan Wulan, ACC Bos):
    Dulu fungsi ini HANYA menyaring `status == 'selesai'`. Akibatnya proses
    yang GAGAL tidak pernah muncul di lonceng — mahasiswa tidak diberi tahu
    apa pun, padahal kuotanya sudah dikembalikan. Tampilan lonceng sendiri
    (editor.html) SUDAH lama menyiapkan cabang ikon '⚠️' untuk gagal, tapi
    cabang itu TIDAK PERNAH terpakai karena daftarnya tidak pernah memuat
    status 'gagal'. Sekarang 'gagal' IKUT masuk supaya mahasiswa tahu dan
    bisa mencoba lagi. Yang sedang berjalan TIDAK masuk sini (itu tugas
    `yang_sedang_jalan` — tampil di panel pantau, bukan lonceng).
    """
    return list(db.execute(
        select(ProsesAI).where(
            ProsesAI.user_id == user_id,
            ProsesAI.status.in_(('selesai', 'gagal')),
            ProsesAI.dibaca == 0,
        ).order_by(ProsesAI.id.desc()).limit(20)
    ).scalars())


def yang_sedang_jalan(db, user_id: int) -> list:
    """Proses yang masih berjalan — supaya halaman bisa menyambung lagi
    kalau user menutup lalu membuka tab (rancangan §4.12: 'boleh ditinggal')."""
    return list(db.execute(
        select(ProsesAI).where(
            ProsesAI.user_id == user_id,
            ProsesAI.status.in_(('menunggu', 'jalan')),
        ).order_by(ProsesAI.id.desc()).limit(20)
    ).scalars())


def _bagian_dari(p) -> str:
    """Sebutan bagian naskah untuk notifikasi (kalau ada).

    Dipakai supaya notifikasi berbunyi '"BAB II" baru saja dirapikan EduAi'
    — lebih terasa personal daripada 'Naskahmu'. Kalau tidak diketahui,
    kembalikan '' (pemanggil akan memakai 'Naskahmu').
    """
    try:
        j = getattr(p, 'jenis_dokumen', '') or ''
        b = getattr(p, 'bagian_ke', 0) or 0
        if b and j:
            return f'bagian ke-{b}'
    except Exception:                                             # noqa: BLE001
        pass
    return ''


def ringkas(p: ProsesAI) -> dict:
    """Bentuk ringkas untuk dikirim ke halaman (JSON).

    ⚠️ `hasil` TIDAK ikut di sini — naskah besar tidak boleh dikirim tiap
    kali halaman memantau status (boros & lambat). Ada endpoint tersendiri.
    """
    #  Pesan yang DILIHAT mahasiswa di lonceng.
    #  ⚠️ 17Sep26 (ACC Bos): SEMUA kalimat diambil dari `app/notifikasi.py`
    #  — satu sumber, gaya hangat, penyebutan pelaku = "EduAi".
    #  Alasan: dulu pesan gagal menampilkan galat TEKNIS mentah
    #  ("RuntimeError: provider AI tidak merespons") yang membingungkan dan
    #  terasa menakutkan. Bos minta nada yang mengingatkan, bukan menakuti.
    from .notifikasi import pesan as _pesan
    if p.status == 'gagal':
        _n = _pesan('revisi_belum_berhasil', alasan=p.galat or '')
        pesan, nada, tombol = _n['isi'], _n['nada'], _n['tombol']
    elif p.status == 'selesai':
        _n = _pesan('revisi_selesai', bagian=_bagian_dari(p))
        pesan, nada, tombol = _n['isi'], _n['nada'], _n['tombol']
    else:
        #  Sedang menunggu/jalan → tampilkan tahap apa adanya (termasuk
        #  'Menunggu antrean (posisi N dari M)') supaya user tahu kemajuannya.
        pesan = p.galat[:200] if p.galat else (p.tahap or '')
        nada, tombol = 'bantu', None
    return {
        'kode': p.kode,
        # 16Sep26: `file_id` + `judul` DITAMBAH karena lonceng (Langkah E)
        # perlu tahu proses ini milik BERKAS MANA. Tanpa ini halaman tidak
        # bisa menyaring → lonceng nyala di berkas yang salah.
        'file_id': p.file_id,
        # ⚠️ Kolom ProsesAI yang NYATA (app/models.py:568) = `bagian_ke` +
        #  `jumlah_bagian`. TIDAK ada `bagian`/`tahap_total` — Wulan sempat
        #  mengarang dan itu = AttributeError saat halaman dibuka.
        'judul': 'Revisi dokumen',
        'pesan': pesan,
        #  17Sep26: `nada` + `tombol` dari app/notifikasi.py supaya halaman
        #  bisa memilih warna/ikon & label tombol tanpa menulis kalimat sendiri.
        'nada': nada,
        'tombol': tombol,
        'tahap_selesai': p.bagian_ke or 0,
        'tahap_total': p.jumlah_bagian or 0,
        'status': p.status,
        'tahap': p.tahap,
        'bagian_ke': p.bagian_ke,
        'jumlah_bagian': p.jumlah_bagian,
        'panjang': p.panjang,
        'jenis_dokumen': p.jenis_dokumen,
        'model_ai': p.model_ai,
        #  TOKEN NYATA (17Sep26): dulu hanya `token_revisi` yang dikirim,
        #  padahal DB menyimpan token_in/token_out juga. Skrip uji & halaman
        #  jadi tidak bisa memverifikasi biaya sebenarnya. Ditambahkan supaya
        #  DAPAT DIPERIKSA (bukan dikarang).
        'token_in': p.token_in or 0,
        'token_out': p.token_out or 0,
        'token_revisi': p.token_revisi,
        'galat': p.galat,
        'dibaca': bool(p.dibaca),
        'dibuat': p.dibuat.isoformat() if p.dibuat else None,
        'selesai': p.selesai.isoformat() if p.selesai else None,
        'ada_hasil': bool(p.hasil),
    }


# ══════════════════════════════════════════════════════════════════════════
#  BAGIAN 2 — MENJALANKAN PEKERJAAN DI LATAR BELAKANG
# ══════════════════════════════════════════════════════════════════════════
#
#  🚦 ANTREAN & BATAS KONKURENSI (ACC Bos 17Sep26)
#
#  MASALAH YANG DITUTUP: `jalankan()` dulu LANGSUNG `thread.start()` tanpa
#  batas. 200 mahasiswa klik bersamaan = 200 utas + 200 event loop sekaligus
#  → memori habis, dan SQLite bisa kena "database is locked".
#
#  UKURAN NYATA 17Sep26 (bukan tebakan) — permintaan bertubi ke 9router:
#      5/10/20 permintaan pendek bersamaan → 100% OK
#      50 permintaan pendek (skenario Bos) → 50/50 OK, total 14,1 dtk
#      10 naskah 42rb kar bersamaan        → 10/10 OK, 7,5 dtk
#      25 naskah 42rb kar bersamaan        → 25/25 OK, 19,5 dtk (6→20 dtk/req)
#  ⇒ 9router sendiri SANGGUP. Yang perlu dijaga = SISI KITA (utas + SQLite).
#
#  KENAPA BATAS 8: pada 25 permintaan berat, waktu per-request naik ke 20 dtk
#  (dari 6 dtk). Dengan 8 sekaligus, antrean tetap MEMBATASI lonjakan tanpa
#  membuat mahasiswa menunggu lama. Angka ini dapat diubah lewat `.env`
#  (`EDUAI_AI_KONKUREN`) — KEPUTUSAN BOS, bukan diam-diam diubah Wulan.
#
#  PENTING: mahasiswa TIDAK melihat error apa pun. Yang terlihat hanyalah
#  tahap yang jujur: 'Menunggu antrean (posisi N dari M)' → lalu jalan.
# ══════════════════════════════════════════════════════════════════════════

#  Jumlah pekerjaan yang boleh JALAN BERSAMAAN. Sisanya menunggu giliran.
KONKUREN_MAKS = max(1, int(os.getenv('EDUAI_AI_KONKUREN', '8')))

#  Antrean FIFO sederhana + penghitung yang jalan. Dilindungi kunci supaya
#  aman dipakai dari banyak utas (endpoint HTTP memanggil dari utas lain).
_kunci_antrean = threading.Lock()
_sedang_jalan: int = 0
_antrean: deque = deque()          # kode proses yang MENUNGGU giliran


def _posisi_antrean(kode: str) -> tuple[int, int]:
    """(posisi kode di antrean, jumlah yang menunggu) — untuk ditampilkan."""
    with _kunci_antrean:
        try:
            return (_antrean.index(kode) + 1, len(_antrean))
        except ValueError:
            return (0, len(_antrean))


def _antre_atau_jalan(kode: str, kerja) -> bool:
    """Coba JALANKAN sekarang; kalau penuh → masuk antrean.

    Kembalikan True kalau langsung berjalan, False kalau menunggu giliran.
    Mahasiswa tetap melihat tahap yang jujur (bukan 'error').

    FORMAT TAHAP: 'Menunggu antrean (posisi N dari M)'
      N = giliran ke-N (1 = berikutnya). M = jumlah yang MENGANTRE saat itu.
      ⚠️ M bukan jumlah total permintaan — itu angka nyata panjang antrean,
      dan ikut menyusut saat antrean maju (lihat `_segarkan_posisi_antrean`).
    """
    global _sedang_jalan
    with _kunci_antrean:
        if _sedang_jalan < KONKUREN_MAKS:
            _sedang_jalan += 1
            langsung = True
            pos = total = 0
        else:
            _antrean.append(kode)
            langsung = False
            #  ⚠️ AKAR BUG TAMPILAN 17Sep26: dulu posisi dihitung dari
            #  `len(_antrean)` SEBELUM baris ini menambahkan dirinya → yang
            #  paling depan melihat 'posisi 0 dari 34'. Mahasiswa yang melihat
            #  'posisi 0' menyangka antreannya rusak. Sekarang dihitung SETELAH
            #  masuk: posisi 1 = giliran berikutnya. Terbukti nyata di uji
            #  50-mahasiswa (ada baris 'posisi 0 dari 34').
            pos = len(_antrean)
            total = len(_antrean)
    if langsung:
        ubah_tahap(kode, 'Mulai bekerja', status='jalan')
        _utas(kode, kerja)
        return True
    #  Tahap jujur: mahasiswa tahu dia MENGANTRE, bukan macet/error.
    ubah_tahap(kode, f'Menunggu antrean (posisi {pos} dari {total})',
               status='menunggu')
    return False


def _segarkan_posisi_antrean() -> None:
    """Perbarui tulisan posisi SEMUA yang masih mengantre.

    KENAPA: kalau tidak disegarkan, mahasiswa di posisi 34 terus melihat
    'posisi 34 dari 34' walau antrean sudah maju — dia menyangka tidak
    bergerak (padahal sedang maju). Tahap ditulis ulang supaya ANGKANYA
    JUJUR: posisi makin kecil = memang makin dekat.
    """
    with _kunci_antrean:
        sedang = list(_antrean)
    total = len(sedang)
    for i, k in enumerate(sedang, start=1):
        ubah_tahap(k, f'Menunggu antrean (posisi {i} dari {total})',
                   status='menunggu')


def _selesai_satu() -> None:
    """Dipanggil saat satu pekerjaan usai → beri giliran berikutnya."""
    global _sedang_jalan
    berikut: str | None = None
    with _kunci_antrean:
        _sedang_jalan = max(0, _sedang_jalan - 1)
        if _antrean and _sedang_jalan < KONKUREN_MAKS:
            berikut = _antrean.popleft()
            _sedang_jalan += 1
    #  Perbarui nomor posisi yang masih menunggu (supaya angkanya JUJUR —
    #  makin dekat giliran, makin kecil posisinya).
    _segarkan_posisi_antrean()
    if berikut:
        _lanjutkan_dari_antrean(berikut)


def _lanjutkan_dari_antrean(kode: str) -> None:
    """Jalankan pekerjaan yang tadinya mengantre (dicari di DB)."""
    db = _sesi_baru()
    try:
        p = ambil(db, kode)
        if p is None or p.status not in ('menunggu',):
            return
        kerja = getattr(p, '_kerja', None) or _kerja_terdaftar.get(kode)
    finally:
        db.close()
    if kerja is None:
        #  Tidak ada pekerjaan (mis. server restart) → jangan biarkan menggantung.
        tandai_gagal(kode, 'Antrean dilanjutkan tanpa pekerjaan (server mungkin '
                            'baru dijalankan ulang). Silakan ulangi.')
        _selesai_satu()
        return
    pos, total = _posisi_antrean(kode)
    if total:
        ubah_tahap(kode, f'Menunggu antrean (posisi {pos} dari {total})',
                   status='menunggu')
    ubah_tahap(kode, 'Mulai bekerja', status='jalan')
    _utas(kode, kerja)


#  Peta kode → fungsi kerja, untuk pekerjaan yang MENUNGGU giliran.
#  ⚠️ Hanya di memori. Kalau server mati, pekerjaan mengantre ditandai gagal
#  dengan pesan jujur (kuota dikembalikan oleh alur yang sudah ada).
_kerja_terdaftar: dict = {}


def _utas(kode: str, kerja) -> threading.Thread:
    """Buat + jalankan utas untuk satu pekerjaan (dipakai internal).

    🎯 25Sep26 (AKAR #12 — PROSES HANTU): utas WAJIB menutup status proses.
    Dulu, kalau `kerja` SELESAI TANPA memanggil `tandai_selesai` (mis. utas
    mati mendadak, pengecualian di luar `try`, atau container dimatikan
    di tengah jalan), baris DB tetap `status='jalan'` SELAMANYA — hantu yang
    menahan slot. Terbukti (uji 2 arah `uji_status_utas.py`):
        kerja GAGAL           → status='gagal'  ✅
        kerja sukses tanpa tD → status='jalan'  ❌ HANTU
    Akibat nyata: 8 hantu = slot habis = SEMUA permintaan berikutnya
    'Menunggu antrean' dan TIDAK PERNAH dilayani (bottle neck 420 dtk).

    PERBAIKAN: di `finally`, kalau status masih 'jalan'/'menunggu' →
    tandai gagal + KEMBALIKAN kuota. Slot PASTI dilepas, status PASTI tutup.
    """

    def _bungkus():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(kerja(Lapor(kode)))
        except Exception as e:                                    # noqa: BLE001
            jejak = traceback.format_exc()
            log.error('[proses] %s GAGAL: %s\n%s', kode, e, jejak)
            tandai_gagal(kode, f'{type(e).__name__}: {e}')
        finally:
            try:
                loop.close()
            except Exception:                                     # noqa: BLE001
                pass
            #  🛡️ PENJAGA HANTU — tutup status kalau masih menggantung.
            try:
                _tutup_bila_menggantung(kode)
            except Exception:                                     # noqa: BLE001
                log.exception('[proses] penjaga hantu gagal (kode=%s)', kode)
            #  Selalu lepaskan slot — termasuk saat gagal. Kalau tidak,
            #  antrean bisa macet selamanya (bug yang harus dihindari).
            _kerja_terdaftar.pop(kode, None)
            _selesai_satu()

    t = threading.Thread(target=_bungkus, name=f'proses-ai-{kode}',
                         daemon=True)
    t.start()
    return t


def _tutup_bila_menggantung(kode: str) -> bool:
    """Tutup proses yang masih `jalan`/`menunggu` → tandai gagal + balikkan kuota.

    Dipanggil di `finally` utas worker DAN saat start (pembersih hantu).
    Kembalikan True kalau status ditutup.
    """
    db = SessionLocal()
    try:
        p = db.execute(select(ProsesAI).where(
            ProsesAI.kode == kode)).scalar_one_or_none()
        if p is None:
            return False
        if p.status not in ('jalan', 'menunggu'):
            return False
        info_potong: list = []
        try:
            jj = json.loads(p.hasil_json or '{}')
            info_potong = jj.get('_info_potong') or []
        except Exception:                                         # noqa: BLE001
            info_potong = []
        kembalikan_bila_gagal(db, kode, p.user_id, info_potong)
        p.status = 'gagal'
        p.tahap = 'Gagal'
        p.galat = ('Proses berhenti tak terduga (utas mati sebelum selesai). '
                   'Token Revisi Anda sudah dikembalikan — silakan coba lagi.')
        p.selesai = datetime.utcnow()
        db.commit()
        log.warning('[proses] HANTU ditutup: %s (status jalan tanpa utas) '
                    '→ gagal + kuota dikembalikan', kode)
        return True
    finally:
        db.close()


def bersihkan_hantu() -> int:
    """Tutup SEMUA proses `jalan` yang utasnya sudah tidak ada. Kembalikan jumlah.

    Dipakai saat start aplikasi (`main.py`) — supaya hantu dari sesi
    sebelumnya (mis. container dimatikan mendadak) TIDAK menahan slot.
    """
    hidup = {t.name for t in threading.enumerate()
             if t.name.startswith('proses-ai-')}
    db = SessionLocal()
    n = 0
    try:
        baris = db.execute(select(ProsesAI).where(
            ProsesAI.status.in_(('jalan', 'menunggu')))).scalars().all()
        for p in baris:
            if f'proses-ai-{p.kode}' in hidup:
                continue
            info_potong: list = []
            try:
                jj = json.loads(p.hasil_json or '{}')
                info_potong = jj.get('_info_potong') or []
            except Exception:                                     # noqa: BLE001
                info_potong = []
            try:
                kembalikan_bila_gagal(db, p.kode, p.user_id, info_potong)
            except Exception:                                     # noqa: BLE001
                log.exception('[proses] gagal kembalikan kuota hantu %s',
                              p.kode)
            p.status = 'gagal'
            p.tahap = 'Gagal'
            p.galat = ('Proses dari sesi sebelumnya tidak selesai '
                       '(server berhenti). Token Revisi Anda sudah '
                       'dikembalikan — silakan coba lagi.')
            p.selesai = datetime.utcnow()
            n += 1
        if n:
            db.commit()
            log.warning('[proses] pembersih hantu: %d proses menggantung '
                        'ditutup + kuota dikembalikan', n)
    finally:
        db.close()
    #  Slot dihitung ulang dari utas HIDUP (bukan dari sisa angka lama).
    global _sedang_jalan
    with _kunci_antrean:
        _sedang_jalan = len(hidup)
        _antrean.clear()
    return n


def jalankan(kode: str, kerja) -> threading.Thread | None:
    """Jalankan `kerja` (fungsi async) — LANGSUNG bila slot kosong, kalau
    penuh MASUK ANTREAN (mahasiswa tidak pernah melihat error).

    `kerja` WAJIB menerima satu argumen: objek `Lapor`.

    KENAPA UTAS + EVENT LOOP SENDIRI: kode revisi EduAi memakai async/await
    (httpx). Utas biasa tidak punya event loop, jadi kita buat satu khusus
    untuk utas ini — tidak mengganggu loop utama FastAPI.

    Kembalikan Thread bila langsung jalan, None bila mengantre.
    """
    _kerja_terdaftar[kode] = kerja
    if _antre_atau_jalan(kode, kerja):
        return None                    # utas sudah dikelola di `_utas`
    return None


def statistik_antrean() -> dict:
    """Untuk PEMANTAUAN: berapa yang jalan, berapa mengantre, batasnya.

    Dipakai halaman admin/uji supaya antrean DAPAT DILIHAT, bukan dikira-kira.
    """
    with _kunci_antrean:
        return {
            'jalan': _sedang_jalan,
            'mengantre': len(_antrean),
            'batas': KONKUREN_MAKS,
        }


class Lapor:
    """Pemberi tahu tahap. Dipakai fungsi `kerja` supaya user melihat
    KEMAJUAN NYATA (Membaca → Menulis bagian N → Memeriksa)."""

    def __init__(self, kode: str):
        self.kode = kode

    def tahap(self, teks: str, bagian_ke: int | None = None) -> None:
        ubah_tahap(self.kode, teks, bagian_ke=bagian_ke)

    def menulis(self, ke: int, dari: int) -> None:
        self.tahap(tahap_menulis(ke, dari), bagian_ke=ke)


def kembalikan_bila_gagal(db, kode: str, user_id: int, info_potong: list) -> None:
    """Kembalikan kuota kalau proses GAGAL.

    ️ INI PENUTUP LUBANG YANG DITEMUKAN 16Sep26:
    Di alur lama, pengembalian kuota hanya terjadi di `except HTTPException`.
    Kalau koneksi diputus Cloudflare (524) atau utas mati, blok itu TIDAK
    pernah jalan → kuota HANGUS (bukti: 9→7 padahal revisi_history=0).
    Sekarang status proses disimpan di DB, jadi pengembalian bisa dilakukan
    berdasarkan FAKTA ('gagal'), bukan berdasarkan jenis exception.

    Dipanggil dari utas SETELAH pekerjaan selesai — lihat `pantau_dan_kembalikan`.
    """
    from .ai import _kembalikan_kuota                      # hindari impor lingkar
    p = ambil(db, kode, user_id)
    if p is None or p.status != 'gagal':
        return
    for ip in info_potong or []:
        try:
            _kembalikan_kuota(db, user_id, ip)
        except Exception as e:                                    # noqa: BLE001
            log.warning('[proses] gagal kembalikan kuota: %s', e)