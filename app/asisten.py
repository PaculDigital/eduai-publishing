"""ASISTEN PEMBIMBING — T5.2 (ACC Bos: RENCANA §3.2 TAHAP 5.2).

═══════════════════════════════════════════════════════════════════════════
ATURAN BESAR (pelanggaran = bongkar ulang)
═══════════════════════════════════════════════════════════════════════════
1. RUBRIK TERPISAH dari AI mahasiswa (aturan Bos: "JANGAN SAMA BISA
   BAHAYA"). Prompt di sini = sudut PANDANG PEMBIMBING: struktur bab,
   kelengkapan metodologi, sitasi, kejelasan argumentasi. DILARANG
   menyalin/memanggil SYSTEM_REVISI milik ai.py.
2. SATU PINTU AI: panggilan tetap lewat `ai._panggil_router()`
   (9router → fallback OpenRouter). TIDAK ada jalur/provider kedua.
3. HANYA BACA naskah. Hasil = USULAN CATATAN yang LANGSUNG MASUK
   (putusan Bos C5) lewat `pembimbing.catat()` — naskah tidak disentuh.
4. BIAYA (putusan Bos **C7**, 29Sep26): **yang KLIK = yang BAYAR**.
   Trial 1× gratis per AKUN PEMBAYAR, sesudah itu 1 Token Revisi per
   operasi dari SALDO PUNYA PEMBAYAR (`saldo.pakai`). Dompet orangnya
   masing-masing — DILARANG memotong pemilik naskah untuk klik orang lain.
   Pagar P1 cek dulu → P2 gagal = kembalikan (pola peta/kerjakan).
5. DILARANG kata menakutkan (PERINGATAN/GAGAL/HABIS/BAHAYA) — pesan
   selalu kasih jalan keluar.
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Pembimbingan, Setelan, User

log = logging.getLogger('eduai.asisten')

#  ── Batas kerja ──────────────────────────────────────────────────────────
#  Naskah dipotong supaya jawaban tetap < 100 dtk (batas praktis Cloudflare
#  524 lewat domain — terukur 27Sep26). 40.000 kar ≈ 3-5 bab pertama.
NASKAH_MAKS = 40_000
USULAN_MAKS = 8          # pagar: AI tak boleh menagih 50 catatan sekaligus
PILIHAN_PER_ROUND = 5    # alur PILIHAN (15 Nov 2026, koreksi Bos 16:36):
                         # AI memberi 5 pilihan per round, bukan 8.
HARGA_TOKEN = 1          # 1 Token Revisi per operasi (sesudah trial)

#  ── HEMAT TOKEN (15Okt26) ────────────────────────────────────────────────
#  AKAR: asisten mengirim naskah UTUH (40.000 kar) ke AI padahal alat hemat
#  SUDAH ADA (`app/konteks.py`, terbukti hemat 91% — terukur 25Sep26) dan
#  sudah dipakai jalur revisi mahasiswa (`ai.py:2444-2477`).
#
#  CARA: naskah dipecah jadi BAGIAN (bab/sub-bab) lewat `konteks.petakan()`,
#  lalu AI menerima: judul bab + sebelum + sesudah + ISI TARGET + tugasan
#  (`konteks.bangun_prompt()`). Bagian target digilir supaya SELURUH naskah
#  tetap tertinjau (bukan cuma bab pertama).
#
#  PAGAR (pola terbukti `ai.py`):
#    · Gagal apa pun → JALUR LAMA (naskah utuh). Tinjauan TIDAK pernah gagal
#      karena optimasi ini.
#    · Naskah pendek / cuma 1 bagian → langsung jalur lama (tak ada gunanya).
#  CATATAN PENTING: `simpan_usulan()` TETAP memakai naskah UTUH untuk MENCARI
#  KUTIPAN (verifikasi sorotan). Yang dipotong HANYA yang dikirim ke AI.
KONTEKS_MIN_PECAH = 6_000   # di bawah ini tak perlu dipecah
KONTEKS_MAKS_KAR = 6_000    # batas 1 bagian yang dikirim (~1.800 token)

#  ── KUNCI setelan/percakapan ────────────────────────────────────────────
KUNCI_TRIAL = 'asisten_trial_{uid}'      # nilai = 1 sesudah trial terpakai


# ══════════════════════════════════════════════════════════════════════════
# RUBRIK PEMBIMBING — TERPISAH SENGAJA dari prompt revisi mahasiswa
# ══════════════════════════════════════════════════════════════════════════
RUBRIK = (
    'Kamu membantu seorang DOSEN PEMBIMBING menelaah draf karya tulis '
    'ilmiah mahasiswanya. Tugasmu MENANDAI hal yang perlu ditanyakan atau '
    'diperbaiki mahasiswa — BUKAN menulis ulang drafnya.\n'
    'Periksa dengan sudut pandang pembimbing:\n'
    '1. STRUKTUR: urutan bab/subbab logis? ada bagian yang melompat?\n'
    '2. KELENGKAPAN METODE: rumusan masalah ↔ metode ↔ instrumen ↔ analisis '
    'saling nyambung? (CATATAN: jumlah sampel, teknik sampling, skala, dan '
    'teknik analisis adalah KEBEBASAN penulis — beri saran HANYA bila ada '
    'pertentangan internal antar bagian, bukan karena beda selera.)\n'
    '3. RUYUNG RUJUKAN: klaim penting tanpa rujukan? sitasi tidak konsisten?\n'
    '4. KEJELASAN: kalimat ambigu, istilah teknis tanpa definisi operasional.\n'
    'ATURAN JAWABAN (mutlak):\n'
    '- Balas HANYA JSON: {"usulan": [{"bab": "...", "kutipan": "...", '
    '"catatan": "..."}]}\n'
    f'- Maksimal {USULAN_MAKS} usulan, pilih yang paling penting saja.\n'
    '- "kutipan" = potongan teks ASLI dari draf (persis, 8-15 kata) yang '
    'jadi tempat catatan menempel. Ambil dari draf, jangan karang.\n'
    '- "catatan" = 1-2 kalimat bahasa saran yang hangat, siap dibaca '
    'mahasiswa. Tanpa kata AI/model/sistem.\n'
    '- Kalau draf sudah rapi dan tidak ada yang layak ditandai, balas '
    '{"usulan": []} — jangan mencari-cari kesalahan kecil.\n'
    '- Dilarang menambah data, angka, atau rujukan karangan.'
)


def sisa_trial(db: Session, pembayar: User) -> bool:
    """True kalau akun ini BELUM memakai trial gratis (1× seumur akun)."""
    kunci = KUNCI_TRIAL.format(uid=pembayar.id)
    baris = db.get(Setelan, kunci)
    return baris is None or (baris.nilai or '') != '1'


def _tandai_trial(db: Session, pembayar: User) -> None:
    kunci = KUNCI_TRIAL.format(uid=pembayar.id)
    baris = db.get(Setelan, kunci)
    if baris is None:
        db.add(Setelan(kunci=kunci, nilai='1', oleh='asisten-trial'))
    else:
        baris.nilai = '1'
    db.commit()


def biaya_untuk(db: Session, pembayar: User) -> dict:
    """Beritahu panggilan: pakai trial atau potong saldo.

    Harga alur PILIHAN (koreksi Bos 16:36 WIB): 1 Token Revisi PER BUTIR
    yang diterima; 'butuh' di sini = 1 per butir, trial menanggung butir
    pertama. Alur lama (satu operasi langsung jadi catatan) tetap 1.
    """
    if sisa_trial(db, pembayar):
        return {'pakai_trial': True, 'butuh': 0}
    return {'pakai_trial': False, 'butuh': HARGA_TOKEN}


# ══════════════════════════════════════════════════════════════════════════
#  PERINTAH LUAS, khusus ALUR PILIHAN (15 Nov 2026)
# ══════════════════════════════════════════════════════════════════════════
#  Lapisan 1 = yang SUDAH ADA: `_boleh_potong` (alur + cakupan dokumen
#  lewat `ai._boleh_konteks` / `parser.pilih_pengali`).
#  Lapisan 2 = contoh Boss yang TIDAK ditangkap lapisan 1 (TERUKUR):
#    "perbaiki semuanya" → _boleh_konteks True (sempit), SALAH, harus luas.
#    "tolong tinjau"     → _boleh_konteks True (sempit), SALAH, harus luas.
#    "tinjau semuanya"   → _boleh_konteks True (sempit), SALAH, harus luas.
#  Tambahan lapisan 2 (HANYA di sini, parser bersama TIDAK diubah,
#  harga revisi mahasiswa tidak boleh ikut berubah):
#    · kata semua/seluruh ("perbaiki semuanya", "tinjau semuanya");
#    · perintah tanpa sasaran: sesudah buang kata pengisi + kata kerja,
#      yang tersisa kosong atau hanya kata dokumen ("tolong tinjau",
#      "cek naskah").
#  Tetap sempit: "perbaiki 2.1" (ada nomor bagian), "tambahkan teori
#  pemasaran" (ada topik), "perbaiki bab 2" (ada bab).
_KATA_SEMUA_PILIHAN = ('semua', 'seluruh', 'keseluruhan')
_KATA_PENGISI = ('tolong', 'mohon', 'coba', 'ya', 'dong', 'saja', 'aja')
_KATA_KERJA_PILIHAN = ('tinjau', 'periksa', 'cek', 'lihat', 'review',
                      'telaah', 'perbaiki', 'tambahkan', 'tambah', 'ubah',
                      'ganti', 'betulkan', 'revisi')
_KATA_DOKUMEN_PILIHAN = ('naskah', 'dokumen', 'draf', 'skripsi', 'tulisan',
                        'karya')


def _perintah_luas(cmd: str) -> bool:
    """True kalau perintah ini LUAS (→ alur pilihan, naskah utuh).

    Perintah kosong = luas. Yang sudah ada (`_boleh_potong`) dulu,
    baru dua pola lapisan 2 di atas.
    """
    cmd = (cmd or '').strip()
    if not cmd:
        return True
    if not _boleh_potong([cmd]):
        return True
    t = cmd.lower()
    if any(k in t for k in _KATA_SEMUA_PILIHAN):
        return True
    kata = [w for w in re.split(r'[^a-z0-9.]+', t)
            if w and w not in _KATA_PENGISI
            and w not in _KATA_KERJA_PILIHAN]
    if not kata:
        return True
    if all(w in _KATA_DOKUMEN_PILIHAN for w in kata):
        return True
    return False


def potong_biaya(db: Session, pembayar: User, jumlah: int = 1) -> dict:
    """Pagar P1: potong Token Revisi (bila trial sudah terpakai).

    HARGA (koreksi Bos 16:36 WIB): 1 Token Revisi PER BUTIR yang diterima.
    Trial 1x per akun menanggung butir PERTAMA; sisanya dari saldo.
    `jumlah=1` = alur lama (satu operasi Asisten langsung jadi catatan)
    , perilakunya PERSIS seperti sebelum generalisasi (uji F1/F2).

    Cek dulu (jangan potong setengah-setengah): kalau saldo tidak cukup
    untuk SEMUA butir, tolak dengan pesan ramah + jalan keluar.

    Return {'ok': True, 'sumber': 'trial'|'saldo'|'campur',
            'dipotong': <yang dipotong dari saldo>, 'sisa': int} ATAU
    {'ok': False, 'pesan': ...}, pesan RAMAH + jalan keluar.
    """
    jumlah = max(1, int(jumlah or 1))
    pakai_trial = sisa_trial(db, pembayar)
    butuh = jumlah - (1 if pakai_trial else 0)
    if butuh > 0:
        from . import saldo as _saldo
        sisa_kini = _saldo.sisa(db, pembayar)
        if sisa_kini < butuh:
            #  Aturan 5: jalan keluar harus yang BENAR-BENAR bisa dipakai.
            #  Paket gratis TERKUNCI dari AddOn (config.boleh_beli_addon,
            #  MASTER_PLAN 4.10), dulu pesannya tetap menyuruh ke AddOn,
            #  jalan buntu bagi pembimbing paket gratis.
            from .config import boleh_beli_addon          # noqa: PLC0415
            if boleh_beli_addon(pembayar.paket or 'gratis'):
                jalan = 'Tambah sedikit lewat menu AddOn, atau '
            else:
                jalan = ('Tingkatkan paket ke Penulis dulu supaya bisa isi '
                         'saldo, atau ')
            if jumlah == 1:
                #  ⚠️ Teks ini PERSIS seperti sebelum generalisasi (uji F2
                #     menguncinya), jangan ubah satu kata pun.
                pesan = (
                    'Asisten tinjauan butuh 1 Token Revisi untuk jalan lagi, dan '
                    'saldomu belum cukup. ' + jalan +
                    'lanjut menandai catatan secara manual, dua-duanya jalan.')
            else:
                pesan = (
                    f'Menerima {jumlah} pilihan butuh {jumlah} Token Revisi, '
                    f'dan saldomu belum cukup untuk semuanya. ' + jalan +
                    'pilih lebih sedikit, atau lanjut menandai catatan '
                    'secara manual, dua-duanya jalan.')
            return {'ok': False, 'pesan': pesan}
    if pakai_trial:
        _tandai_trial(db, pembayar)
    sisa_akhir = None
    if butuh > 0:
        from . import saldo as _saldo
        hasil = _saldo.pakai(db, pembayar, butuh, sumber='asisten_pembimbing',
                             catatan=(f'{jumlah} pilihan diterima'
                                      if jumlah > 1 else
                                      'Tinjauan AI, Tab Kolaborasi'))
        sisa_akhir = hasil.get('sisa')
    else:
        from . import saldo as _saldo
        sisa_akhir = _saldo.sisa(db, pembayar, seed=False)
    sumber = ('campur' if (pakai_trial and butuh > 0)
              else ('trial' if pakai_trial else 'saldo'))
    return {'ok': True, 'sumber': sumber, 'dipotong': butuh,
            'sisa': sisa_akhir}


def kembalikan_biaya(db: Session, pembayar: User, sumber: str,
                     jumlah: int = 1) -> None:
    """Pagar P2: AI tidak memberi hasil → biaya kembali penuh.

    Aturan 5: trial 1x seumur akun pun kembali — gagal = trial TIDAK
    terpakai, pembimbing boleh coba lagi. Dulu cabang trial langsung
    kembali tanpa mengembalikan apa pun, jadi trial hangus sia-sia
    padahal AI tidak memberi hasil.

    `jumlah` = yang dipotong DARI SALDO (lihat `potong_biaya` → 'dipotong').
    Alur lama (jumlah=1) perilakunya PERSIS seperti sebelumnya.
    'campur' = trial + saldo: trial dikembalikan (bendera dihapus) DAN
    saldo dikembalikan sejumlah `jumlah`.
    """
    if sumber == 'trial' or sumber == 'campur':
        kunci = KUNCI_TRIAL.format(uid=pembayar.id)
        baris = db.get(Setelan, kunci)
        if baris is not None:
            db.delete(baris)
            db.commit()
        if sumber == 'trial':
            return
    if sumber != 'saldo' and sumber != 'campur':
        return
    from . import saldo as _saldo
    _saldo.kembalikan(db, pembayar, max(0, int(jumlah or 0)),
                      sumber='asisten_kembali',
                      catatan='Tinjauan AI: AI tidak memberi hasil')


# ══════════════════════════════════════════════════════════════════════════
# NASKAH & PANGGILAN
# ══════════════════════════════════════════════════════════════════════════

def naskah_bimbingan(db: Session, b: Pembimbingan) -> str:
    """Ambil teks naskah UTAMA dari bimbingan (berkas pertama yang berisi).

    Memakai mesin baca yang SUDAH ada di rute_pembimbing (`_isi_naskah`)
    , sama persis dengan yang dilihat pembimbing di layar. Tanpa menulis
    apa pun ke DB.
    """
    from .rute_pembimbing import _isi_naskah          # noqa: PLC0415
    from .pembimbing import daftar_berkas             # noqa: PLC0415
    for bk in daftar_berkas(db, b.id):
        teks = _isi_naskah(db, bk)
        if (teks or '').strip():
            return teks[:NASKAH_MAKS]
    return ''


# ══════════════════════════════════════════════════════════════════════════
# HEMAT TOKEN — kirim BAGIAN + tetangga, bukan naskah utuh (15Okt26)
# ══════════════════════════════════════════════════════════════════════════

def _bagian_dari(teks: str) -> list[dict]:
    """Pecah naskah jadi BAGIAN (bab/sub-bab) memakai mesin yang SUDAH ADA.

    Memakai `state.petakan()` + `state.buang_daftar_isi()` + `konteks.bangun_prompt()`
    — sama seperti jalur revisi mahasiswa (`ai.py:2447-2477`). TIDAK ada mesin baru.
    Return [] kalau gagal / tak ada gunanya (pemanggil pakai jalur lama).
    """
    from .state import petakan as _petakan, buang_daftar_isi as _buang  # noqa: PLC0415
    peta = _petakan(_buang(teks))
    return [x for x in (peta or []) if (x.get('isi_teks') or '').strip()]


def _baca_giliran(db: Session, b_id: int) -> int:
    """Ambil nomor giliran terakhir untuk bimbingan ini (0 kalau belum ada)."""
    from .models import Setelan                      # noqa: PLC0415
    k = f'asisten_giliran_{int(b_id)}'
    row = db.scalar(select(Setelan).where(Setelan.kunci == k))
    try:
        return int(row.nilai) if row is not None else 0
    except (TypeError, ValueError):
        return 0


def _simpan_giliran(db: Session, b_id: int, n: int) -> None:
    """Catat giliran berikutnya (dipakai operasi selanjutnya)."""
    from .models import Setelan                      # noqa: PLC0415
    k = f'asisten_giliran_{int(b_id)}'
    row = db.scalar(select(Setelan).where(Setelan.kunci == k))
    if row is None:
        db.add(Setelan(kunci=k, nilai=str(int(n))))
    else:
        row.nilai = str(int(n))
    #  tidak commit di sini — `simpan_usulan()` yang commit (pola 17Sep26)


def _catatan_terbaru(db: Session, b_id: int, batas: int = 12) -> list[str]:
    """Komentar (isi catatan) pembimbing pada bimbingan ini — untuk PAGAR.

    KENAPA ADA (15Okt26): pagar `ai._boleh_konteks()` memutuskan boleh/tidak
    naskah dipotong dengan MEMBACA KOMENTAR. Asisten dulu tidak mengirim
    komentar apa pun ⇒ pagar tak bisa bekerja ⇒ asisten SELALU memotong,
    termasuk saat permintaan pembimbing sifatnya MENYELURUH ("ubah alur").

    Sumber: `catatan_pembimbing.isi` yang `dari_pembimbing = 1` (bukan
    penanda pribadi mahasiswa). Ambil yang TERBARU, dibatasi jumlahnya.

    Gagal apa pun → [] (pemanggil tetap jalan; pagar default = boleh potong).
    """
    try:
        from .models import CatatanPembimbing as _CP      # noqa: PLC0415
        baris = db.scalars(
            select(_CP.isi)
            .where(_CP.pembimbingan_id == int(b_id),
                   _CP.dari_pembimbing == 1)
            .order_by(_CP.id.desc())
            .limit(int(batas))
        ).all()
        return [str(x).strip() for x in baris if (x or '').strip()]
    except Exception as e:                                # noqa: BLE001
        log.warning('[asisten] baca catatan pembimbing gagal (%s: %s) '
                    '→ pagar pakai default', type(e).__name__, e)
        return []


def _boleh_potong(komentar: list[str]) -> bool:
    """Pagar: boleh dipotong? Pakai pemeriksa yang SUDAH ADA (`ai._boleh_konteks`).

    TIDAK menyalin aturan — memanggil mesin yang sama supaya asisten dan
    revisi mahasiswa TIDAK pernah beda pendapat (satu sumber kebenaran).

    Default kalau pemeriksa tak bisa dipanggil = True (perilaku hemat),
    supaya optimasi ini tidak pernah mematikan tinjauan.
    """
    if not komentar:
        return True          # tak ada komentar → target sudah jelas dari UI
    try:
        from .ai import _boleh_konteks as _cek           # noqa: PLC0415
        return bool(_cek(list(komentar)))
    except Exception as e:                               # noqa: BLE001
        log.warning('[asisten] pagar _boleh_konteks gagal (%s: %s) '
                    '→ potong (perilaku hemat)', type(e).__name__, e)
        return True


def _siapkan_kirim(db: Session, b: Pembimbingan, teks: str,
                   perintah: str | None = None) -> tuple[str, int]:
    """Siapkan teks yang DIKIRIM ke AI: bagian terpilih + tetangganya.

    Return (teks_kirim, nomor_bagian). GAGAL APA PUN → (teks, -1) = jalur lama
    (naskah utuh) supaya tinjauan TIDAK pernah gagal karena optimasi ini.

    PAGAR: naskah pendek (< KONTEKS_MIN_PECAH) → langsung jalur lama.
    PAGAR 2 (15Okt26): permintaan pembimbing yang menyentuh SELURUH dokumen
    ("ubah alur", "perbaiki benang cerita") → WAJIB naskah utuh.

    PAGAR 3 (15 Nov 2026, alur pilihan): perintah yang DIBERIKAN SEKARANG
    (bukan dari catatan lama) ikut diperiksa, kosong/luas berarti naskah UTUH.
    `perintah=None` = pemanggil lama (halaman Kolaborasi) → perilaku lama
    (gerbang baca catatan) tanpa perubahan.
    """
    try:
        if len(teks) < KONTEKS_MIN_PECAH:
            log.info('[asisten] naskah %d kar < %d → kirim utuh (tak perlu pecah)',
                     len(teks), KONTEKS_MIN_PECAH)
            return teks, -1

        #  ══ PAGAR 3: perintah kosong/luas → JANGAN dipotong ══
        if perintah is not None and _perintah_luas(perintah):
            log.info('[asisten] PAGAR 3: perintah kosong/luas (%r) '
                     '→ kirim naskah UTUH %d kar',
                     (perintah or '')[:40], len(teks))
            return teks, -1

        #  ══ PAGAR 2: permintaan MENYELURUH → JANGAN dipotong (15Okt26) ══
        #  Pakai pemeriksa yang SUDAH ADA (`ai._boleh_konteks`, 1931) yang
        #  membaca komentar lewat `parser.pilih_pengali` (UBAH_ALUR ×4,
        #  +SEMUA ×5). Aturan ini TIDAK disalin — supaya asisten & revisi
        #  mahasiswa tidak pernah beda pendapat.
        komentar = _catatan_terbaru(db, b.id)
        if not _boleh_potong(komentar):
            log.info('[asisten] PAGAR: permintaan menyeluruh (dari %d catatan) '
                     '→ kirim naskah UTUH %d kar', len(komentar), len(teks))
            return teks, -1

        peta = _bagian_dari(teks)
        if len(peta) < 2:
            log.info('[asisten] peta %d bagian → kirim utuh (tak ada tetangga)',
                     len(peta))
            return teks, -1

        #  Giliran: SATU bagian sekali operasi, maju terus supaya seluruh
        #  naskah tertinjau (bab 1, lalu bab 2, dst — berputar kembali).
        #  🚨 KUNCI: 1 bagian + tetangganya = itulah yang menghemat token.
        #     Mengirim beberapa bagian sekaligus hampir tak menghemat
        #     (terukur 15Okt26: 3 bagian cuma hemat 2,8%).
        posisi = _baca_giliran(db, b.id) % len(peta)
        bagian = peta[posisi]
        target = str(bagian.get('section_id') or '').strip()
        if not target:
            log.info('[asisten] bagian ke-%d tanpa section_id → kirim utuh', posisi)
            return teks, -1

        from .konteks import bangun_prompt as _bangun     # noqa: PLC0415
        isi = str(bagian.get('isi_teks') or '')[:KONTEKS_MAKS_KAR]
        kirim = _bangun(bagian_target=target, peta=peta, isi_saat_ini=isi)
        if not kirim:
            log.info('[asisten] bagian %s → konteks kosong → kirim utuh', target)
            return teks, -1

        #  Pagar terakhir: hasil HARUS benar-benar lebih kecil, kalau tidak
        #  percuma (dan bisa lebih besar karena kepala peta).
        if len(kirim) >= len(teks):
            log.info('[asisten] potongan %d kar >= utuh %d kar → kirim utuh',
                     len(kirim), len(teks))
            return teks, -1

        #  Giliran berikutnya: maju 1 (berputar).
        _simpan_giliran(db, b.id, (posisi + 1) % len(peta))
        log.info('[asisten] konteks DIPAKAI: bagian ke-%d/%d (%s) '
                 '→ kirim %d kar (dari %d) | hemat %d kar (%.0f%%)',
                 posisi + 1, len(peta), target, len(kirim), len(teks),
                 len(teks) - len(kirim),
                 100.0 * (len(teks) - len(kirim)) / max(1, len(teks)))
        return kirim, posisi
    except Exception as e:                             # noqa: BLE001
        #  🚨 GAGAL → jalur lama. Tinjauan tetap jalan.
        log.warning('[asisten] hemat token gagal (%s: %s) → pakai naskah utuh',
                    type(e).__name__, e)
        return teks, -1


async def kerjakan(db: Session, b: Pembimbingan, pembayar: User,
                   perintah: str | None = None) -> dict:
    """Jalankan satu operasi Asisten: AI meninjau naskah → usulan.

    DUA MODE (15 Nov 2026):
      · `perintah=None` (halaman Kolaborasi) atau perintah SEMPIT
        ("perbaiki 2.1") → ALUR LAMA: 1 token per operasi, usulan
        LANGSUNG masuk sebagai catatan.
      · perintah KOSONG atau LUAS (sidebar) → ALUR PILIHAN: pembuatan
        daftar GRATIS (tidak ditagih), AI memberi 5 pilihan per round,
        disimpan sebagai DAFTAR PILIHAN (bukan catatan). Tagihan jatuh
        saat pembimbing menerima butirnya (1 token per butir, lewat
        `terima_pilihan`).

    Return dict ringkas untuk JSON:
      alur lama → {ok, dibuat, sumber, model, detik, pesan}
      alur pilihan → {ok, mode='pilih', dibuat=0, jumlah, sumber, pesan}
    Pagar: naskah kosong → biaya tidak dipotong sama sekali.
    Biaya (C7): `pembayar` = akun yang MENEKAN TOMBOL — diisi oleh
    rute `/kolaborasi/asisten` dengan `u` (login), BUKAN pemilik naskah.
    """
    import time                                        # noqa: PLC0415
    teks = naskah_bimbingan(db, b)
    if not (teks or '').strip():
        return {'ok': False, 'dibuat': 0, 'pesan': (
            'Naskahnya belum terbaca di sini. Pastikan mahasiswa sudah '
            'menambahkan berkas ke kolaborasi ini, lalu coba lagi ya.')}

    #  ── Mode: pilihan (sidebar, perintah kosong/luas) vs langsung ──
    mode_pilih = False
    if perintah is not None:
        mode_pilih = _perintah_luas(perintah)

    bayar = None
    if not mode_pilih:
        bayar = potong_biaya(db, pembayar)
        if not bayar.get('ok'):
            return {'ok': False, 'dibuat': 0, 'pesan': bayar['pesan']}

    t0 = time.monotonic()
    #  HEMAT TOKEN: kirim BAGIAN + tetangga, bukan naskah utuh (15Okt26).
    kirim, kunci_bagian = _siapkan_kirim(db, b, teks, perintah=perintah)
    hemat = len(teks) - len(kirim)
    #  Alur pilihan: minta 5 (bukan 8) + pola sudah_ada supaya AI tidak
    #  mengulang catatan yang sudah ada (pola pembimbing_ai, ditambah
    #  saringan keras di bawah, perintah LLM saja tidak cukup).
    rubrik_pakai = RUBRIK
    tambahan = ''
    if mode_pilih:
        rubrik_pakai = RUBRIK.replace(
            f'Maksimal {USULAN_MAKS} usulan',
            f'Maksimal {PILIHAN_PER_ROUND} usulan')
        try:
            from . import pembimbing_ai as PAI           # noqa: PLC0415
            from .pembimbing import daftar_berkas as _dfb  # noqa: PLC0415
            _semua = _dfb(db, b.id)
            _bk0 = _semua[0] if _semua else None
            _sudah = (PAI._catatan_isi_sebelumnya(db, _bk0)
                      if _bk0 is not None else [])
        except Exception:                              # noqa: BLE001
            _sudah = []
        if _sudah:
            potong = [str(x)[:160] for x in _sudah[:8]]
            tambahan = (
                '\nCatatan yang SUDAH ada (jangan diulang, cari yang belum '
                'tersentuh):\n- ' + '\n- '.join(potong) + '\n')
    user_msg = ('Draf mahasiswa (dapat dipotong di akhir):\n\n'
                f'{kirim}\n\n'
                f'{tambahan}'
                'Berikan tinjauan sesuai aturan jawaban.')
    model, dibuat = '', 0
    jumlah_pilihan = 0
    tersaring = 0
    try:
        from . import ai as AI                         # noqa: PLC0415
        konten, info = await AI._panggil_router(user_msg, 120.0,
                                                system=rubrik_pakai)
        model = str(info.get('model') or '')
        usulan = urai_usulan(konten, teks)
        if usulan is None:
            raise RuntimeError('jawaban tidak bisa diurai')
        if mode_pilih:
            #  Saringan keras (deterministik) + potong jadi 5 per round.
            from . import pembimbing as P              # noqa: PLC0415
            from .pembimbing import daftar_berkas as _dfb  # noqa: PLC0415
            _semua = _dfb(db, b.id)
            _bk0 = _semua[0] if _semua else None
            mentah = len(usulan)
            disaring = P.saring_usulan_baru(db, b.id, usulan)
            tersaring = mentah - len(disaring)
            usulan = disaring[:PILIHAN_PER_ROUND]
            jumlah_pilihan = len(usulan)
            if usulan and _bk0 is not None:
                P.simpan_daftar_pilihan(db, b.id, _bk0.id, 'asisten',
                                        usulan)
        else:
            dibuat = simpan_usulan(db, b, usulan)
            if dibuat == 0 and not usulan:
                # draf rapi = hasil sah, biaya tidak dikembalikan (kerja jalan)
                log.info('[asisten] bimbingan %s: AI bilang sudah rapi', b.id)
    except Exception as e:                             # noqa: BLE001
        if bayar is not None:
            kembalikan_biaya(db, pembayar, bayar.get('sumber', ''),
                             bayar.get('dipotong', 1))
        detik = round(time.monotonic() - t0, 1)
        log.warning('[asisten] bimbingan %s gagal setelah %.1f dtk: %s',
                    b.id, detik, e)
        #  Aturan 5: pesan kembali harus jujur per sumber biaya. Dulu
        #  'Saldo sudah kembali utuh' juga muncul untuk trial, padahal
        #  trial tidak memakai saldo (dan dulu trialnya hangus).
        #  Alur pilihan TIDAK memotong apa pun, jangan klaim pengembalian.
        if mode_pilih:
            pesan_gagal = (
                'AI masih sibuk menyelesaikan tinjauan naskah ini. '
                'Coba lagi beberapa saat lagi ya.')
        elif bayar.get('sumber') == 'trial':
            pesan_gagal = (
                'AI masih sibuk menyelesaikan tinjauan naskah ini. '
                'Jatah gratis pertamamu masih tersimpan, coba lagi '
                'beberapa saat lagi ya.')
        else:
            pesan_gagal = (
                'AI masih sibuk menyelesaikan tinjauan naskah ini. '
                'Saldo sudah kembali utuh, coba lagi beberapa saat lagi ya.')
        return {'ok': False, 'dibuat': 0, 'detik': detik,
                'pesan': pesan_gagal}
    detik = round(time.monotonic() - t0, 1)
    if mode_pilih:
        log.info('[asisten] bimbingan %s: %d pilihan disiapkan (%s, %.1f dtk)',
                 b.id, jumlah_pilihan, model, detik)
        return {'ok': True, 'mode': 'pilih', 'dibuat': 0,
                'jumlah': jumlah_pilihan, 'sumber': 'gratis',
                'model': model, 'detik': detik,
                'pesan': ((
                    f'{jumlah_pilihan} pilihan revisi dari AI sudah '
                    'disiapkan di panel. Pilih yang mau dipakai jadi '
                    'catatan.'
                    if jumlah_pilihan else
                    ('Semua temuan baru sudah ada sebagai catatan, tidak '
                     'ada pilihan baru.'
                     if tersaring else
                     'AI sudah meninjau naskah ini: drafnya sudah rapi, tidak '
                     'ada catatan wajib. Silakan lanjut menandai bagian '
                     'spesifik bila perlu.')))}
    log.info('[asisten] bimbingan %s: %d usulan masuk (%s, %s, %.1f dtk, '
             'biaya=%s, pembayar=%s)', b.id, dibuat, model, info.get('model'),
             detik, bayar.get('sumber'), getattr(pembayar, 'id', '?'))
    #  C7 — jujur di layar SIAPA yang membayar (token milik yang klik).
    if bayar.get('sumber') == 'trial':
        ket_biaya = ', memakai jatah gratis pertama akunmu.'
    else:
        ket_biaya = (f", 1 Token Revisi dari saldomu, sisa "
                     f"{bayar.get('sisa')}.")
    return {'ok': True, 'dibuat': dibuat, 'sumber': bayar.get('sumber'),
            'model': model, 'detik': detik,
            #  🚨 kurung WAJIB: tanpa ini `a if c else b + ket` diurai jadi
            #     `a if c else (b + ket)` → keterangan biaya tak pernah muncul
            #     pada jalur sukses (tertangkap uji C7 29Sep26).
            'pesan': ((
                f'{dibuat} catatan saran dari AI sudah masuk ke daftar kamu.'
                if dibuat else
                'AI sudah meninjau naskah ini: drafnya sudah rapi, tidak '
                'ada catatan wajib. Silakan lanjut menandai bagian spesifik '
                'bila perlu.')
                + ket_biaya)}


def terima_pilihan(db: Session, b: Pembimbingan, pembayar: User,
                   berkas_id, pilih: str) -> dict:
    """Terima pilihan revisi AI → jadi catatan pembimbing (kuning).

    HARGA (koreksi Bos 16:36 WIB): 1 Token Revisi PER BUTIR yang diterima;
    trial 1x menanggung butir pertama; tulis manual tetap gratis (tidak
    lewat sini). Cek dulu (jangan potong setengah-setengah): saldo tidak
    cukup untuk SEMUA butir → tolak semua dengan pesan ramah.
    Gagal simpan sesudah potong → biaya kembali penuh (pagar P2).

    `pilih` = indeks dipisah koma ("0,2") dari daftar pilihan yang
    tersimpan (Setelan). Yang tidak dipilih TETAP di daftar (bisa
    diterima nanti); yang sudah diterima DIBUANG dari daftar. Daftar
    kosong → baris dihapus. Yang tidak dipilih TIDAK tersimpan di mana
    pun selain daftar ini, round berikutnya menimpanya.
    """
    from . import pembimbing as P                     # noqa: PLC0415
    try:
        bid = int(str(berkas_id or '').strip())
    except (ValueError, TypeError):
        return {'ok': False, 'dibuat': 0, 'pesan': (
            'Berkas pilihan ini tidak ditemukan. Minta tinjauan AI lagi '
            'untuk pilihan baru ya.')}
    sumber, daftar = P.muat_daftar_pilihan(db, b.id, bid)
    if not daftar:
        return {'ok': False, 'dibuat': 0, 'pesan': (
            'Daftar pilihan sudah tidak ada. Minta tinjauan AI lagi untuk '
            'pilihan baru ya.')}
    try:
        indeks = sorted({int(x) for x in str(pilih or '').split(',')
                         if (x or '').strip()})
    except ValueError:
        return {'ok': False, 'dibuat': 0, 'pesan': (
            'Pilihan tidak dikenali. Coba pilih lagi ya.')}
    dipilih_idx = {i for i in indeks if 0 <= i < len(daftar)}
    if not dipilih_idx:
        return {'ok': False, 'dibuat': 0, 'pesan': (
            'Tidak ada pilihan yang dipilih.')}
    dipilih = [daftar[i] for i in sorted(dipilih_idx)]

    #  Berkas WAJIB milik bimbingan ini (jangan bisa ditembus dengan
    #  menebak angka), diperiksa SEBELUM potong apa pun.
    bk = None
    if sumber == 'periksa':
        from .models import BerkasPembimbingan as _BB    # noqa: PLC0415
        bk = db.get(_BB, bid)
        if bk is None or bk.pembimbingan_id != b.id:
            return {'ok': False, 'dibuat': 0, 'pesan': (
                'Berkas pilihan ini tidak ditemukan. Minta tinjauan AI '
                'lagi untuk pilihan baru ya.')}

    #  ── Potong per butir (trial menanggung pertama) ──────────────────
    bayar = potong_biaya(db, pembayar, jumlah=len(dipilih))
    if not bayar.get('ok'):
        return {'ok': False, 'dibuat': 0, 'pesan': bayar['pesan']}

    #  ── Simpan lewat mesin yang SUDAH ADA ────────────────────────────
    try:
        if sumber == 'periksa':
            from . import pembimbing_ai as PAI           # noqa: PLC0415
            jumlah = PAI.simpan_catatan(db, bk, dipilih)
        else:
            jumlah = simpan_usulan(db, b, dipilih)
    except Exception as e:                                # noqa: BLE001
        kembalikan_biaya(db, pembayar, bayar.get('sumber', ''),
                         bayar.get('dipotong', 0))
        log.warning('[asisten] terima pilihan gagal: %s', e)
        if bayar.get('sumber') == 'trial':
            pesan_gagal = (
                'Pilihan belum tersimpan. Jatah gratis pertamamu masih '
                'tersimpan, coba lagi ya.')
        elif bayar.get('sumber') == 'campur':
            pesan_gagal = (
                'Pilihan belum tersimpan. Jatah gratis dan saldo sudah '
                'kembali utuh, coba lagi ya.')
        else:
            pesan_gagal = (
                'Pilihan belum tersimpan. Token Revisi sudah kembali '
                'utuh, coba lagi ya.')
        return {'ok': False, 'dibuat': 0, 'pesan': pesan_gagal}

    #  ── Buang yang sudah diterima dari daftar ────────────────────────
    sisa = [d for i, d in enumerate(daftar) if i not in dipilih_idx]
    if sisa:
        P.simpan_daftar_pilihan(db, b.id, bid, sumber, sisa)
    else:
        P.hapus_daftar_pilihan(db, b.id, bid)

    if bayar.get('sumber') == 'trial':
        ket = ', memakai jatah gratis pertama akunmu.'
    elif bayar.get('dipotong', 0) > 0:
        ket = (f", {bayar['dipotong']} Token Revisi dari saldomu, sisa "
               f"{bayar.get('sisa')}.")
    else:
        ket = ''
    return {'ok': True, 'dibuat': jumlah, 'dipotong': bayar.get('dipotong', 0),
            'sisa': bayar.get('sisa'),
            'pesan': (f'{jumlah} pilihan sudah menjadi catatan.' + ket)}


# ══════════════════════════════════════════════════════════════════════════
# PARSER & PENYIMPANAN
# ══════════════════════════════════════════════════════════════════════════
_RE_JSON = re.compile(r'\{.*\}', re.S)


def urai_usulan(jawab: str, naskah: str = '') -> list[dict] | None:
    """Urai jawaban AI → list usulan {'bab','kutipan','catatan'}.

    Return None = bentuk TIDAK bisa dipercaya (pemanggil kembalikan biaya).
    Return []  = AI jujur bilang draf rapi (hasil sah).
    """
    if not (jawab or '').strip():
        return None
    m = _RE_JSON.search(jawab)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    daftar = data.get('usulan')
    if not isinstance(daftar, list):
        return None
    bersih = []
    for x in daftar[:USULAN_MAKS]:
        if not isinstance(x, dict):
            continue
        catatan = str(x.get('catatan') or '').strip()
        kutipan = str(x.get('kutipan') or '').strip()
        if not catatan:
            continue
        bersih.append({
            'bab': str(x.get('bab') or '').strip()[:80],
            'kutipan': kutipan,
            'catatan': catatan,
        })
    #  buang duplikat catatan yang persis sama
    unik, kunci_lama = [], set()
    for u in bersih:
        k = u['catatan'].lower()
        if k in kunci_lama:
            continue
        kunci_lama.add(k)
        unik.append(u)
    return unik[:USULAN_MAKS]


def simpan_usulan(db: Session, b: Pembimbingan,
                  usulan: list[dict]) -> int:
    """Masukkan usulan sebagai CATATAN PEMBIMBING sungguhan (putusan C5).

    Peraturan yang ikut:
      · `dari_pembimbing=True` → warna kuning, sisi pembimbing (sama
        seperti catatan tulisan tangan pembimbing — mahasiswa melihat
        SATU sumber catatan, bukan dua kanal berbeda).
      · Kutipan yang TIDAK ditemukan di naskah → teks_asli dikosongkan
        (catatan tetap masuk tanpa sorotan palsu — jujur, tidak menebak).
      · `catat()` tidak commit (desain 17Sep26) → kita commit di sini.
    """
    if not usulan:
        return 0
    from .pembimbing import catat, daftar_berkas, rapi_bab   # noqa: PLC0415
    berkas_list = daftar_berkas(db, b.id)
    bk = berkas_list[0] if berkas_list else None
    naskah = naskah_bimbingan(db, b)
    jumlah = 0
    for u in usulan:
        teks_asli = ''
        if u['kutipan']:
            #  cari kutipan di naskah (normalisasi spasi ringan)
            pola = re.sub(r'\s+', ' ', u['kutipan']).strip()
            sumber = re.sub(r'\s+', ' ', naskah) if naskah else ''
            if pola and pola.lower() in sumber.lower():
                teks_asli = u['kutipan']
        catat(db, b, u['catatan'],
              section_id=rapi_bab(u['bab'] or 'Tinjauan AI')[:80],
              section_judul=(u['bab'] or 'Tinjauan AI')[:200],
              teks_asli=teks_asli,
              berkas_id=(bk.id if bk is not None else None))
        jumlah += 1
    db.commit()
    return jumlah
