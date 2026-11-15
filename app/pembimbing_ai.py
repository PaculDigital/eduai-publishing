"""PEMBIMBING AI — periksa naskah mahasiswa, hasilkan CATATAN (ACC Bos 03Okt26).

═══════════════════════════════════════════════════════════════════════════
ATURAN BESAR (mengapa berkas ini ada terpisah)
═══════════════════════════════════════════════════════════════════════════
1. BERKAS TERPISAH dari `rute_pembimbing.py` — sengaja. Tiang T1 di berkas
   itu berbunyi "halaman tinjau TIDAK menyentuh app/ai.py". Supaya tiang itu
   TETAP UTUH, semua pekerjaan AI dikumpulkan di SINI, dan rute pembimbing
   hanya MEMANGGIL fungsi di berkas ini.

2. AI **TIDAK PERNAH** menyentuh naskah (putusan C3). Hasil AI = BARIS
   CATATAN di tabel `catatan_pembimbing` yang SUDAH ADA (putusan D2).
   Tidak ada tabel baru, tidak ada dokumen baru, tidak ada versi baru.

3. SATU DOMPET (putusan D3): tagihan 1 Token Revisi PER BUTIR yang
   diterima (koreksi Bos 16:36 WIB), lewat `asisten.potong_biaya`
   (trial 1x menanggung butir pertama). PEMBUATAN daftar pilihan
   GRATIS, tidak ditagih. Yang memotong = YANG KLIK (putusan C7).
   Tidak ada jatah/jatahun/dompet kedua.

4. FAIL-SAFE (pagar 1): kalau AI gagal → daftar pilihan tidak dibuat,
   dan karena pembuatan daftar GRATIS, tidak ada kuota yang dipakai
   (tidak ada yang dikembalikan). Kalau penerimaan butir gagal sesudah
   potong → biaya kembali penuh (pagar P2 di `terima_pilihan`).
   Jalur lama (catatan manual, lihat naskah) TIDAK terpengaruh.

5. Saklar ON/OFF ada di `app/config.py::PEMBIMBING_AI_AKTIF`.
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from . import pembimbing as P
from .models import BerkasPembimbingan, User

log = logging.getLogger('eduai.pembimbing.ai')

#  ── Kalimat siap pakai (aturan Bos: hangat, ada jalan keluar, tanpa kata
#     menakutkan, TIDAK menyebut "AI"/"Wulan"/nama model) ─────────────────
KALIMAT_SAKLAR_MATI = (
    'Fitur periksa otomatis sedang tidak dipakai. Catatan Anda tetap bisa '
    'ditulis manual seperti biasa ya.'
)
KALIMAT_BELUM_AKUN = (
    'Untuk memakai periksa otomatis, perlu akun dulu supaya hasilnya tersimpan '
    'dan bisa Anda lihat kembali kapan saja.'
)
KALIMAT_SALDO_KOSONG = (
    'Periksa otomatis memakai kuota yang sama seperti fitur lain. Kuota Anda '
    'sedang kosong — isi ulang dulu ya, setelah itu tinggal klik lagi.'
)
KALIMAT_SEDANG_BEKERJA = (
    'Masih ada pemeriksaan yang berjalan. Mohon tunggu sebentar ya.'
)
KALIMAT_SELESAI = (
    'Pemeriksaan selesai. Pilih revisi yang mau dipakai di panel, atau '
    'tulis sendiri.'
)


# ══════════════════════════════════════════════════════════════════════════
#  GERBANG
# ══════════════════════════════════════════════════════════════════════════
def aktif() -> bool:
    """Saklar fitur (pagar 2). Dibaca ULANG tiap panggilan supaya bisa
    dimatikan tanpa restart."""
    from . import config as C
    return bool(getattr(C, 'PEMBIMBING_AI_AKTIF', True))


def boleh_pakai(db: Session, u: User) -> tuple[bool, str]:
    """Boleh/tidak user ini memakai periksa otomatis DARI PINTU PEMBIMBING.

    ⚠️ INI PINTU KHUSUS. `_member_berbayar()` di ai.py menolak paket
    `gratis` (gerbang §4.10). Di sini paket `gratis` DIBUKA — karena putusan
    Bos: pembimbing = user paket `gratis` dengan 3 token, bebas dipakai
    sebagai mahasiswa ATAU pembimbing.

    Pembukaan ini TIDAK melemahkan §4.10: jalur normal (naskah sendiri di
    /edit) tetap menolak `gratis` tanpa transaksi. Yang dibuka hanyalah
    pintu tinjau naskah ORANG.

    Kembalikan (boleh, sebab).
    """
    if not aktif():
        return False, 'saklar_mati'
    if u is None:
        return False, 'belum_akun'
    if getattr(u, 'role', '') == 'admin':
        return True, 'admin'
    paket = (u.paket or 'gratis')
    #  Paket berbayar → lewat aturan biasa (sudah pasti boleh).
    if paket != 'gratis':
        return True, 'berbayar'
    #  Paket gratis → hanya kalau dia memang PEMILIK saldo (belum habis)
    #  ATAU masih punya trial 1x (koreksi harga 16:36 WIB: trial
    #  menanggung butir pertama yang diterima, jadi trial pun jalan
    #  masuk, dulu saldo 0 + trial tersisa tetap ditolak).
    from . import saldo as S
    if S.sisa(db, u) <= 0:
        try:
            from . import asisten as _A                    # noqa: PLC0415
            if _A.sisa_trial(db, u):
                return True, 'gratis_pembimbing'
        except Exception:                                  # noqa: BLE001
            pass
        return False, 'saldo_kosong'
    return True, 'gratis_pembimbing'


# ══════════════════════════════════════════════════════════════════════════
#  PERIKSA
# ══════════════════════════════════════════════════════════════════════════
def sidik_untuk_ai(db: Session, bk: BerkasPembimbingan) -> str:
    """Cap isi naskah — dipakai supaya AI tidak memeriksa naskah yang sama
    dua kali (hemat kuota pembimbing)."""
    teks = _teks_naskah(db, bk)
    return P.sidik_teks(teks)[:64] if teks else ''


def _teks_naskah(db: Session, bk: BerkasPembimbingan) -> str:
    """Ambil ISI naskah (bukan catatan AI). Pakai pembaca yang SUDAH ADA."""
    from .rute_pembimbing import _isi_naskah   # noqa: PLC0415 (hindari lingkar)
    try:
        return _isi_naskah(db, bk) or ''
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pembimbing-ai] gagal baca naskah berkas %s: %s',
                    getattr(bk, 'id', '?'), e)
        return ''


def bangun_prompt(nama_mhs: str, judul: str, teks: str,
                  sudah_ada: list[str] | None = None) -> str:
    """Susun permintaan ke model — MINTA CATATAN, bukan tulis ulang naskah.

    Bentuk keluaran WAJIB JSON supaya bisa diurai pasti (bukan tebak-tebakan
    dari kalimat bebas). Kalau model bandel, `urai_catatan()` yang menjaga.
    """
    daftar_lama = ''
    if sudah_ada:
        potong = [str(x)[:160] for x in sudah_ada[:8]]
        daftar_lama = (
            '\nCatatan yang SUDAH ada (jangan diulang, cari yang belum '
            'tersentuh):\n- ' + '\n- '.join(potong) + '\n'
        )

    return (
        'Anda membantu seorang pembimbing meninjau naskah mahasiswa.\n'
        f'Nama mahasiswa: {nama_mhs or "(tidak disebut)"}\n'
        f'Judul naskah: {judul or "(tidak disebut)"}\n'
        f'{daftar_lama}\n'
        'TUGAS: temukan hal yang perlu diperbaiki pada naskah di bawah.\n'
        'ATURAN KERAS:\n'
        '1. JANGAN menulis ulang naskah. JANGAN memberi kalimat pengganti.\n'
        '2. Tulis CATATAN saja — tunjuk lokasinya, jelaskan masalahnya.\n'
        '3. Bahasa Indonesia sopan, seperti dosen membimbing, bukan menghakimi.\n'
        '4. Maksimal 5 catatan. Pilih yang paling penting saja.\n'
        '5. Setiap catatan wajib menunjuk bagian naskah yang benar-benar ada.\n\n'
        'Balas HANYA dengan JSON begini (tanpa penjelasan lain):\n'
        '{"catatan":[{"bagian":"<nama bab/sub-bab>",'
        '"kutipan":"<8-15 kata persis dari naskah>",'
        '"soal":"<apa yang perlu diperbaiki, 1-2 kalimat>",'
        '"saran":"<arah perbaikannya, 1-2 kalimat>"}]}\n\n'
        'NASKAH:\n'
        '─────\n'
        f'{teks}\n'
        '─────\n'
    )


def urai_catatan(jawab: str) -> list[dict]:
    """Ubah jawaban model → daftar catatan bersih.

    Tabah terhadap: pagar ```json, teks pembuka/penutup, kunci kurang.
    Kembalikan [] kalau benar-benar tidak ada catatan yang bisa dipakai —
    pemanggil yang memutuskan langkah berikutnya (JANGAN mengarang).
    """
    if not jawab:
        return []
    teks = jawab.strip()
    #  Buang pagar kode kalau ada.
    if teks.startswith('```'):
        teks = teks.split('\n', 1)[1] if '\n' in teks else teks
        if teks.rstrip().endswith('```'):
            teks = teks.rstrip()[:-3]
    #  Ambil blok JSON pertama yang seimbang.
    mulai = teks.find('{')
    if mulai < 0:
        return []
    dalam, akhir = 0, -1
    for i in range(mulai, len(teks)):
        if teks[i] == '{':
            dalam += 1
        elif teks[i] == '}':
            dalam -= 1
            if dalam == 0:
                akhir = i + 1
                break
    if akhir < 0:
        return []
    try:
        data = json.loads(teks[mulai:akhir])
    except Exception:                                          # noqa: BLE001
        return []
    butir = data.get('catatan') if isinstance(data, dict) else None
    if not isinstance(butir, list):
        return []

    hasil: list[dict] = []
    for c in butir:
        if not isinstance(c, dict):
            continue
        soal = str(c.get('soal') or '').strip()
        if not soal:
            continue                    # tanpa isi masalah → tidak berguna
        hasil.append({
            'bagian': str(c.get('bagian') or '').strip()[:120],
            'kutipan': str(c.get('kutipan') or '').strip()[:300],
            'soal': soal[:600],
            'saran': str(c.get('saran') or '').strip()[:600],
        })
    return hasil[:5]


def rapikan_isi(c: dict) -> str:
    """Bentuk isi catatan yang enak dibaca pembimbing & mahasiswa."""
    bagian = c.get('bagian') or ''
    kepala = f'[{bagian}] ' if bagian else ''
    baris = [f'{kepala}{c.get("soal", "")}'.strip()]
    if c.get('kutipan'):
        baris.append(f'Kutipan: "{c["kutipan"]}"')
    if c.get('saran'):
        baris.append(f'Arah perbaikan: {c["saran"]}')
    return '\n'.join(x for x in baris if x)


# ══════════════════════════════════════════════════════════════════════════
#  EKSEKUSI — panggil model, lalu TULIS hasilnya sebagai CATATAN
# ══════════════════════════════════════════════════════════════════════════
#  ⚠️ SATU PINTU: model hanya dipanggil lewat `app/ai.py::_panggil_router`.
#     TIDAK ADA jalur/provider kedua (aturan keras Bos). Yang dipinjam hanya
#     FUNGSI-nya, dan itu memang didesain untuk dipakai bersama (lihat
#     komentar `system` di sana — "rubrik TERPISAH ... tanpa membuat
#     jalur/provider kedua").
SYSTEM_PEMBIMBING = (
    'Anda pembimbing akademik yang meninjau naskah mahasiswa. Anda HANYA '
    'menulis catatan perbaikan; Anda TIDAK menulis ulang naskah. Bahasa '
    'Indonesia sopan, jelas, dan mendorong perbaikan. Balas dengan JSON '
    'sesuai permintaan.'
)


def simpan_catatan(db: Session, bk: BerkasPembimbingan,
                   daftar: list[dict]) -> int:
    """Simpan daftar catatan periksa sebagai BARIS CATATAN.

    Mesin yang SAMA dengan langkah 5 `periksa()` yang lama, dipindah ke
    fungsi bernama supaya penerimaan pilihan (`asisten.terima_pilihan`)
    memakai jalur simpan yang persis sama (bukan salinan). Dipakai HANYA
    saat pembimbing MENERIMA butirnya (saat itulah 1 token per butir
    dipotong, trial menanggung butir pertama).
    """
    b = _bimbingan_dari(db, bk)
    #  Pertahanan kedua (putusan Bos 18:48 WIB, samakan dengan
    #  `simpan_usulan`): kutipan yang tidak ada di naskah disimpan
    #  dengan teks_asli kosong DAN tanpa baris Kutipan di isi, catatan
    #  tetap masuk tanpa sorotan palsu.
    teks = _teks_naskah(db, bk)
    jumlah = 0
    for c in daftar:
        kutip = (c.get('kutipan') or '')[:300]
        teks_asli = (kutip if P.kutipan_ada_di_naskah(kutip, teks) else '')
        P.catat(db, b, rapikan_isi({**c, 'kutipan': teks_asli}),
                section_judul=(c.get('bagian') or '')[:120],
                berkas_id=bk.id, teks_asli=teks_asli,
                dari_pembimbing=False)      # ← sumber: mesin, bukan orang
        jumlah += 1
    db.commit()
    return jumlah


async def periksa(
    db: Session,
    bk: BerkasPembimbingan,
    *,
    pemakai: User,
    nama_mhs: str = '',
    lapor=None,
) -> dict:
    """Jalankan pemeriksaan AI → DAFTAR PILIHAN (bukan langsung catatan).

    HARGA (koreksi Bos 16:36 WIB): pembuatan daftar GRATIS (tidak
    ditagih). Tagihan jatuh saat pembimbing MENERIMA butirnya, 1 Token
    Revisi per butir, trial menanggung butir pertama (lewat
    `asisten.terima_pilihan`). Karena tidak ada yang dipotong di sini,
    TIDAK ADA pengembalian kuota.

    URUTAN:
      1. Gerbang: saklar → pemakai → saldo/trial (TIDAK memotong)
      2. Baca naskah
      3. Panggil model (satu pintu, dengan fallback bawaan)
      4. Urai → SARING KERAS (buang yang kutipannya sudah jadi catatan)
         → simpan sebagai DAFTAR PILIHAN (Setelan, bukan catatan)
      5. Gagal di langkah mana pun → sebab jujur (tidak ada kuota yang
         dipakai, jadi tidak ada yang dikembalikan)

    Kembalikan dict: {ok, sebab, jumlah, mode='pilih', pesan}
    """
    from . import ai as AI                       # noqa: PLC0415

    #  ── 1. Gerbang ────────────────────────────────────────────────────────
    boleh, sebab = boleh_pakai(db, pemakai)
    if not boleh:
        pesan = {
            'saklar_mati': KALIMAT_SAKLAR_MATI,
            'belum_akun': KALIMAT_BELUM_AKUN,
            'saldo_kosong': KALIMAT_SALDO_KOSONG,
        }.get(sebab, KALIMAT_SAKLAR_MATI)
        return {'ok': False, 'sebab': sebab, 'jumlah': 0, 'pesan': pesan}

    #  ── 2. Naskah ─────────────────────────────────────────────────────────
    if lapor:
        lapor.tahap('Membaca naskah')
    teks = _teks_naskah(db, bk)
    if len(teks.strip()) < 200:
        return {'ok': False, 'sebab': 'naskah_kosong', 'jumlah': 0,
                'pesan': 'Naskah ini masih kosong, belum ada yang bisa '
                         'diperiksa. Coba lagi setelah ada isinya ya.'}

    #  ── 3. Panggil model (satu pintu) ────────────────────────────────────
    try:
        if lapor:
            lapor.tahap('Memeriksa isi naskah')
        judul = getattr(bk, 'judul', '') or ''
        sudah = _catatan_isi_sebelumnya(db, bk)
        prompt = bangun_prompt(nama_mhs, judul, teks, sudah_ada=sudah)
        from . import config as C                              # noqa: PLC0415
        timeout = float(getattr(C, 'AI_TIMEOUT_DETIK', 420))
        jawab, info = await AI._panggil_router(
            prompt, timeout, system=SYSTEM_PEMBIMBING)
        log.info('[pembimbing-ai] model=%s panjang_jawab=%s',
                 (info or {}).get('model', '?'), len(jawab or ''))

        #  ── 4. Urai + saring keras + simpan sebagai DAFTAR PILIHAN ──────
        if lapor:
            lapor.tahap('Menyusun pilihan revisi')
        catatan = urai_catatan(jawab)
        if not catatan:
            raise ValueError('model tidak memberi catatan yang bisa dipakai')
        b = _bimbingan_dari(db, bk)
        #  Saringan keras (deterministik, koreksi Bos 16:36 WIB): yang
        #  kutipannya sudah jadi catatan tidak ditawarkan lagi. Prompt
        #  `sudah_ada` saja tidak cukup (LLM bisa tetap mengulang).
        catatan = P.saring_usulan_baru(db, b.id, catatan)
        if not catatan:
            return {'ok': True, 'sebab': 'selesai', 'jumlah': 0,
                    'mode': 'pilih',
                    'pesan': 'Semua temuan baru sudah ada sebagai catatan, '
                             'tidak ada pilihan baru.'}
        #  Verifikasi jangkar (putusan Bos 18:48 WIB): buang yang
        #  mengada-ada (kutipan / bagian tidak ada di naskah).
        catatan = P.saring_usulan_nyata(db, bk.id, teks, catatan)[:5]
        if not catatan:
            return {'ok': True, 'sebab': 'selesai', 'jumlah': 0,
                    'mode': 'pilih',
                    'pesan': 'Tidak ada temuan baru yang terverifikasi '
                             'dari naskah ini.'}
        P.simpan_daftar_pilihan(db, b.id, bk.id, 'periksa', catatan)

        log.info('[pembimbing-ai] selesai: %s pilihan (bimbingan %s, '
                 'berkas %s)', len(catatan), getattr(bk, 'pembimbingan_id', '?'),
                 bk.id)
        return {'ok': True, 'sebab': 'selesai', 'jumlah': len(catatan),
                'mode': 'pilih', 'pesan': KALIMAT_SELESAI}

    except Exception as e:                                     # noqa: BLE001
        #  Tidak ada yang dipotong di sini → tidak ada yang dikembalikan.
        log.warning('[pembimbing-ai] pemeriksaan gagal: %s', e)
        return {'ok': False, 'sebab': 'ai_gagal', 'jumlah': 0,
                'pesan': 'Pemeriksaan belum berhasil kali ini, kuota Anda '
                         'tidak terpakai. Bisa dicoba lagi sebentar lagi.'}


def _bimbingan_dari(db: Session, bk: BerkasPembimbingan):
    """Ambil induk bimbingan dari satu berkas."""
    from .models import Pembimbingan                          # noqa: PLC0415
    return (db.query(Pembimbingan)
            .filter(Pembimbingan.id == bk.pembimbingan_id)
            .one_or_none())


def _catatan_isi_sebelumnya(db: Session, bk: BerkasPembimbingan,
                            batas: int = 8) -> list[str]:
    """Ambil potongan catatan yang SUDAH ada untuk berkas ini.

    Dipakai supaya model tidak mengulang catatan yang sama (hemat kuota
    pembimbing) — sekaligus membuat pemeriksaan berikutnya makin berguna.
    """
    from .models import CatatanPembimbing                       # noqa: PLC0415
    baris = (db.query(CatatanPembimbing)
             .filter(CatatanPembimbing.berkas_id == bk.id)
             .order_by(CatatanPembimbing.id.desc())
             .limit(batas).all())
    return [(c.isi or '')[:160] for c in baris if (c.isi or '').strip()]
