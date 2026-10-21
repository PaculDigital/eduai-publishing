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
    """Beritahu panggilan: pakai trial atau potong saldo."""
    if sisa_trial(db, pembayar):
        return {'pakai_trial': True, 'butuh': 0}
    return {'pakai_trial': False, 'butuh': HARGA_TOKEN}


def potong_biaya(db: Session, pembayar: User) -> dict:
    """Pagar P1: potong 1 Token Revisi (bila trial sudah terpakai).

    Return {'ok': True, 'sumber': 'trial'|'saldo', 'sisa': int} ATAU
    {'ok': False, 'pesan': ...} — pesan RAMAH + jalan keluar.
    """
    if sisa_trial(db, pembayar):
        _tandai_trial(db, pembayar)
        return {'ok': True, 'sumber': 'trial', 'sisa': None}
    from . import saldo as _saldo
    sisa_kini = _saldo.sisa(db, pembayar)
    if sisa_kini < HARGA_TOKEN:
        return {'ok': False, 'pesan': (
            'Asisten tinjauan butuh 1 Token Revisi untuk jalan lagi, dan '
            'saldomu belum cukup. Tambah sedikit lewat menu AddOn, atau '
            'lanjut menandai catatan secara manual — dua-duanya jalan.')}
    _saldo.pakai(db, pembayar, HARGA_TOKEN, sumber='asisten_pembimbing',
                 catatan='Tinjauan AI — Tab Kolaborasi')
    return {'ok': True, 'sumber': 'saldo', 'sisa': sisa_kini - HARGA_TOKEN}


def kembalikan_biaya(db: Session, pembayar: User, sumber: str) -> None:
    """Pagar P2: AI tidak memberi hasil → biaya kembali penuh."""
    if sumber != 'saldo':
        return
    from . import saldo as _saldo
    _saldo.kembalikan(db, pembayar, HARGA_TOKEN,
                      sumber='asisten_kembali',
                      catatan='Tinjauan AI: AI tidak memberi hasil')


# ══════════════════════════════════════════════════════════════════════════
# NASKAH & PANGGILAN
# ══════════════════════════════════════════════════════════════════════════

def naskah_bimbingan(db: Session, b: Pembimbingan) -> str:
    """Ambil teks naskah UTAMA dari bimbingan (berkas pertama yang berisi).

    Memakai mesin baca yang SUDAH ada di rute_pembimbing (`_isi_naskah`)
    — sama persis dengan yang dilihat pembimbing di layar. Tanpa menulis
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


def _siapkan_kirim(db: Session, b: Pembimbingan, teks: str) -> tuple[str, int]:
    """Siapkan teks yang DIKIRIM ke AI: bagian terpilih + tetangganya.

    Return (teks_kirim, nomor_bagian). GAGAL APA PUN → (teks, -1) = jalur lama
    (naskah utuh) supaya tinjauan TIDAK pernah gagal karena optimasi ini.

    PAGAR: naskah pendek (< KONTEKS_MIN_PECAH) → langsung jalur lama.
    PAGAR 2 (15Okt26): permintaan pembimbing yang menyentuh SELURUH dokumen
    ("ubah alur", "perbaiki benang cerita") → WAJIB naskah utuh.
    """
    try:
        if len(teks) < KONTEKS_MIN_PECAH:
            log.info('[asisten] naskah %d kar < %d → kirim utuh (tak perlu pecah)',
                     len(teks), KONTEKS_MIN_PECAH)
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


async def kerjakan(db: Session, b: Pembimbingan, pembayar: User) -> dict:
    """Jalankan satu operasi Asisten: AI meninjau naskah → usulan LANGSUNG
    masuk.

    Return dict ringkas untuk JSON:
      {ok, dibuat, sumber, model, detik, pesan}
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

    bayar = potong_biaya(db, pembayar)
    if not bayar.get('ok'):
        return {'ok': False, 'dibuat': 0, 'pesan': bayar['pesan']}

    t0 = time.monotonic()
    #  HEMAT TOKEN: kirim BAGIAN + tetangga, bukan naskah utuh (15Okt26).
    kirim, kunci_bagian = _siapkan_kirim(db, b, teks)
    hemat = len(teks) - len(kirim)
    user_msg = ('Draf mahasiswa (dapat dipotong di akhir):\n\n'
                f'{kirim}\n\n'
                'Berikan tinjauan sesuai aturan jawaban.')
    model, dibuat = '', 0
    try:
        from . import ai as AI                         # noqa: PLC0415
        konten, info = await AI._panggil_router(user_msg, 120.0,
                                                system=RUBRIK)
        model = str(info.get('model') or '')
        usulan = urai_usulan(konten, teks)
        if usulan is None:
            raise RuntimeError('jawaban tidak bisa diurai')
        dibuat = simpan_usulan(db, b, usulan)
        if dibuat == 0 and not usulan:
            # draf rapi = hasil sah, biaya tidak dikembalikan (kerja jalan)
            log.info('[asisten] bimbingan %s: AI bilang sudah rapi', b.id)
    except Exception as e:                             # noqa: BLE001
        kembalikan_biaya(db, pembayar, bayar.get('sumber', ''))
        detik = round(time.monotonic() - t0, 1)
        log.warning('[asisten] bimbingan %s gagal setelah %.1f dtk: %s',
                    b.id, detik, e)
        return {'ok': False, 'dibuat': 0, 'detik': detik, 'pesan': (
            'AI masih sibuk menyelesaikan tinjauan naskah ini. '
            'Saldo sudah kembali utuh — coba lagi beberapa saat lagi ya.')}
    detik = round(time.monotonic() - t0, 1)
    log.info('[asisten] bimbingan %s: %d usulan masuk (%s, %s, %.1f dtk, '
             'biaya=%s, pembayar=%s)', b.id, dibuat, model, info.get('model'),
             detik, bayar.get('sumber'), getattr(pembayar, 'id', '?'))
    #  C7 — jujur di layar SIAPA yang membayar (token milik yang klik).
    if bayar.get('sumber') == 'trial':
        ket_biaya = ' — memakai jatah gratis pertama akunmu.'
    else:
        ket_biaya = (f" — 1 Token Revisi dari saldomu, sisa "
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
