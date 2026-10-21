"""BAB IV — orkestrasi Hasil & Pembahasan (Fase 2, 21 Okt 2026).

Dua isi modul ini (fondasi — alur UI menyusul di fase berikutnya):

1. LAYANAN HASIL: menyimpan hasil hitung dari jembatan Statistik Lab
   sebagai versi-versi (`HasilBab4`), tombol Kunci Hasil, dan tarif
   generate mengikuti keputusan Bos:
     · Paket Olah Data (30 token, dibayar sekali di depan lewat layanan
       kerangka yang sudah ada) mencakup generate pertama.
     · Revisi data pada penelitian & data yang sama: generate ke-2
       s.d. ke-4 GRATIS (itu "gratis 3 kali" — tiga kali generate ULANG),
       generate ke-5 dan seterusnya 5 token per kali (dipotong pemanggil
       lewat kuota; modul ini hanya menghitung tarifnya).
   Narasi hanya boleh lahir dari hasil berstatus 'terkunci'.

2. MESIN ATURAN PETA: pemeriksa konsistensi peta penelitian + penentu
   label desain dari SIDIK JARI FAKTA (prinsip Bos: tanya fakta, bukan
   label). Fungsi-fungsi ini MURNI (tanpa AI, tanpa basis data) supaya
   bisa diuji sendiri dan tidak bisa "mengarang": unsur peta tanpa
   bukti kalimat ditandai sebagai masalah, bukan diteruskan.

Rancangan induk: DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md (§5, §10).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import HasilBab4, PetaBab4

TARIF_GENERATE_LANJUT = 5        # token, per generate sesudah jatah gratis
JATAH_GENERATE_GRATIS = 4        # 1 generate paket + 3 generate ulang gratis


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════
# LAYANAN HASIL
# ══════════════════════════════════════════════════════════════════════════
def simpan_hasil(db: Session, user_id: int, file_id: int, jenis: str,
                 mode: str, hasil: dict) -> HasilBab4:
    """Simpan hasil hitung sebagai VERSI BARU berstatus 'draf'."""
    terakhir = (db.query(HasilBab4)
                .filter_by(user_id=user_id, file_id=file_id, jenis=jenis)
                .order_by(HasilBab4.nomor.desc()).first())
    baris = HasilBab4(
        user_id=user_id, file_id=file_id, jenis=jenis, mode=mode,
        nomor=(terakhir.nomor + 1) if terakhir else 1,
        status='draf', hasil=json.dumps(hasil, ensure_ascii=False))
    db.add(baris)
    db.commit()
    db.refresh(baris)
    return baris


def jumlah_generate(db: Session, user_id: int, file_id: int,
                    jenis: str = 'olah_data') -> int:
    return (db.query(HasilBab4)
            .filter_by(user_id=user_id, file_id=file_id, jenis=jenis)
            .count())


def tarif_generate_berikutnya(db: Session, user_id: int, file_id: int,
                              jenis: str = 'olah_data') -> int:
    """Token untuk generate berikutnya: 0 selama dalam jatah gratis
    (1 paket + 3 ulang), 5 token sesudahnya. Keputusan Bos 21 Okt 2026."""
    return 0 if jumlah_generate(db, user_id, file_id, jenis) < JATAH_GENERATE_GRATIS \
        else TARIF_GENERATE_LANJUT


def kunci_hasil(db: Session, user_id: int, file_id: int,
                jenis: str = 'olah_data') -> HasilBab4 | None:
    """Bekukan versi draf TERBARU menjadi 'terkunci' (Kunci Hasil).

    Hanya satu versi terkunci yang berlaku pada satu waktu: versi
    terkunci sebelumnya (bila ada) diturunkan kembali ke 'draf' supaya
    sumber narasi tidak pernah ambigu."""
    draf = (db.query(HasilBab4)
            .filter_by(user_id=user_id, file_id=file_id, jenis=jenis,
                       status='draf')
            .order_by(HasilBab4.nomor.desc()).first())
    if draf is None:
        return None
    for lama in (db.query(HasilBab4)
                 .filter_by(user_id=user_id, file_id=file_id, jenis=jenis,
                            status='terkunci').all()):
        lama.status = 'draf'
        lama.dikunci_pada = None
    draf.status = 'terkunci'
    draf.dikunci_pada = _now()
    db.commit()
    db.refresh(draf)
    return draf


def hasil_terkunci(db: Session, user_id: int, file_id: int,
                   jenis: str = 'olah_data') -> HasilBab4 | None:
    return (db.query(HasilBab4)
            .filter_by(user_id=user_id, file_id=file_id, jenis=jenis,
                       status='terkunci')
            .order_by(HasilBab4.nomor.desc()).first())


def baca_hasil(baris: HasilBab4) -> dict:
    try:
        return json.loads(baris.hasil or '{}')
    except (TypeError, ValueError):
        return {}


# ══════════════════════════════════════════════════════════════════════════
# PETA — simpan & sahkan
# ══════════════════════════════════════════════════════════════════════════
def simpan_peta(db: Session, user_id: int, file_id: int, isi: dict) -> PetaBab4:
    terakhir = (db.query(PetaBab4)
                .filter_by(user_id=user_id, file_id=file_id)
                .order_by(PetaBab4.nomor.desc()).first())
    baris = PetaBab4(
        user_id=user_id, file_id=file_id,
        nomor=(terakhir.nomor + 1) if terakhir else 1,
        status='usulan', isi=json.dumps(isi, ensure_ascii=False))
    db.add(baris)
    db.commit()
    db.refresh(baris)
    return baris


def sahkan_peta(db: Session, peta_id: int) -> PetaBab4 | None:
    baris = db.get(PetaBab4, peta_id)
    if baris is None:
        return None
    baris.status = 'disahkan'
    baris.disahkan_pada = _now()
    db.commit()
    db.refresh(baris)
    return baris


def baca_peta(baris: PetaBab4) -> dict:
    try:
        return json.loads(baris.isi or '{}')
    except (TypeError, ValueError):
        return {}


# ══════════════════════════════════════════════════════════════════════════
# MESIN ATURAN PETA — murni, tanpa AI/DB
# ══════════════════════════════════════════════════════════════════════════
# Bentuk peta kuantitatif:
#   {jenis:'kuantitatif',
#    variabel:[{nama, peran:'X'|'M'|'Z'|'Y', bukti:'kalimat…'|None,
#               indikator:[…]}],
#    jalur:[{dari, ke, hipotesis:'H1', jenis:'langsung'|'tidak_langsung'|
#            'interaksi'}],
#    jumlah_hipotesis:int, target_sampel:int|None}
# Bentuk peta kualitatif:
#   {jenis:'kualitatif', fokus:[{nama, bukti}], informan:[{jenis, bukti}],
#    teknik:[…]}
def periksa_peta(peta: dict) -> list[dict]:
    """Periksa konsistensi peta. Kembalikan daftar masalah
    [{kode, pesan}] — kosong berarti peta konsisten & siap disahkan.

    Aturan kerasnya (keputusan Bos): unsur tanpa bukti = masalah;
    jumlah jalur (berlabel) harus sama dengan jumlah hipotesis;
    ada perantara ⇒ ada jalur masuk DAN keluar; ada penguat ⇒ ada
    jalur interaksi ke hasil."""
    masalah: list[dict] = []

    def tambah(kode: str, pesan: str) -> None:
        masalah.append({'kode': kode, 'pesan': pesan})

    if peta.get('jenis') == 'kualitatif':
        if not peta.get('fokus'):
            tambah('fokus_kosong', 'Fokus penelitian belum terisi.')
        if not peta.get('informan'):
            tambah('informan_kosong', 'Informan belum terdaftar.')
        for f in peta.get('fokus') or []:
            if not f.get('bukti'):
                tambah('tanpa_bukti',
                       f'Fokus "{f.get("nama", "?")}" tidak punya bukti '
                       'kalimat dari naskah — tidak boleh dikarang.')
        for i in peta.get('informan') or []:
            if not i.get('bukti'):
                tambah('tanpa_bukti',
                       f'Informan "{i.get("jenis", "?")}" tidak punya '
                       'bukti kalimat dari naskah.')
        return masalah

    variabel = peta.get('variabel') or []
    jalur = peta.get('jalur') or []
    nama_peran: dict[str, str] = {}
    for v in variabel:
        nama = str(v.get('nama') or '')
        if nama in nama_peran and nama_peran[nama] != v.get('peran'):
            tambah('peran_ganda',
                   f'"{nama}" muncul dengan dua peran berbeda '
                   f'({nama_peran[nama]} dan {v.get("peran")}).')
        nama_peran[nama] = v.get('peran')
        if not v.get('bukti'):
            tambah('tanpa_bukti',
                   f'Variabel "{nama}" tidak punya bukti kalimat dari '
                   'naskah — statusnya harus "tidak ditemukan", bukan '
                   'diteruskan.')
    peran_ada = set(nama_peran.values())
    if 'Y' not in peran_ada:
        tambah('tanpa_y', 'Belum ada variabel hasil (Y).')
    if 'X' not in peran_ada:
        tambah('tanpa_x', 'Belum ada variabel bebas (X).')
    if len([1 for r in peran_ada if r == 'Y']) and \
            sum(1 for v in variabel if v.get('peran') == 'Y') > 1:
        tambah('y_ganda', 'Variabel hasil (Y) lebih dari satu — model '
                          'BAB IV ini mendukung satu Y.')

    label = [str(j.get('hipotesis') or '') for j in jalur]
    if any(not h for h in label):
        tambah('jalur_tanpa_label', 'Ada jalur yang belum berlabel '
                                    'hipotesis (H1, H2, …).')
    if len(set(label)) != len(label):
        tambah('label_kembar', 'Ada label hipotesis yang dipakai dua '
                               'jalur sekaligus.')
    jml_hip = peta.get('jumlah_hipotesis')
    if jml_hip is not None and len(jalur) != int(jml_hip):
        tambah('jumlah_tak_sama',
               f'Jumlah jalur ({len(jalur)}) tidak sama dengan jumlah '
               f'hipotesis di naskah ({jml_hip}).')

    masuk = {str(j.get('ke')) for j in jalur}
    keluar = {str(j.get('dari')) for j in jalur}
    for v in variabel:
        if v.get('peran') == 'M':
            if v['nama'] not in masuk or v['nama'] not in keluar:
                tambah('perantara_terputus',
                       f'Perantara "{v["nama"]}" harus punya jalur masuk '
                       'DAN jalur keluar.')
        if v.get('peran') == 'Z':
            ada_interaksi = any(
                j.get('jenis') == 'interaksi' and str(j.get('ke')) in
                {n for n, r in nama_peran.items() if r == 'Y'}
                for j in jalur)
            if not ada_interaksi:
                tambah('penguat_tanpa_interaksi',
                       f'Penguat "{v["nama"]}" belum punya jalur '
                       'interaksi ke variabel hasil.')
    return masalah


def label_desain(fakta: dict) -> dict:
    """Tentukan label desain dari SIDIK JARI FAKTA (bukan tebakan label).

    fakta: {perlakuan: bool, kelompok_kontrol: bool,
            ukur_sebelum_sesudah: bool, sekali_sebar: bool}
    Kembalikan {desain, alasan[]} — desain salah satu dari:
    'eksperimen', 'pra-eksperimen', 'survei', 'korelasional',
    'belum_jelas' (fakta belum cukup — yang ditanyakan ke user adalah
    pertanyaan fakta, lihat DOKUMENTASI §5.3)."""
    perlakuan = bool(fakta.get('perlakuan'))
    kontrol = bool(fakta.get('kelompok_kontrol'))
    sebelum = bool(fakta.get('ukur_sebelum_sesudah'))
    sekali = bool(fakta.get('sekali_sebar'))
    if perlakuan and kontrol:
        return {'desain': 'eksperimen',
                'alasan': ['Ada perlakuan dan ada kelompok kontrol.']}
    if perlakuan and not kontrol:
        return {'desain': 'pra-eksperimen',
                'alasan': ['Ada perlakuan tapi tidak ada kelompok '
                           'kontrol.']}
    if sekali and not perlakuan:
        return {'desain': 'survei',
                'alasan': ['Data diambil sekali sebar (kuesioner) tanpa '
                           'perlakuan.']}
    if sebelum and not perlakuan:
        return {'desain': 'korelasional',
                'alasan': ['Ada pengukuran berulang tanpa perlakuan.']}
    return {'desain': 'belum_jelas',
            'alasan': ['Fakta lapangan belum cukup untuk menentukan '
                       'desain — tanyakan fakta kegiatannya, bukan '
                       'labelnya.']}
