"""Cek awal buku (30 Okt 2026): potensi gagal dicek di AWAL, bukan di gerbang akhir.

Alasan bisnis: token kembali utuh saat gerbang gagal (net 0), tapi waktu
(~36 menit per buku) + biaya LLM bab/gambar yang dibuang + kepercayaan
pelanggan tetap hilang. Cek di sini deterministik (tanpa LLM, tanpa Jev),
murah, dan tidak membakar token/biaya baru.

Isi:
  1. periksa_outline(outline, jumlah_harus): cek struktur referensi di
     Gate 1 (jumlah bab vs paket, tepat 5 sub, kata kunci N.3/N.4, judul
     ganda). Dipakai di /buku/outline (tampil), /buku/susun (tolak tanpa
     pekerjaan), dan susun() (tolak sebelum potong token).
  2. skor_risiko(outline, jumlah_harus): Hijau/Kuning/Merah + alasan,
     untuk halaman outline sebelum user menekan Setuju.
  3. periksa_bab_awal(n, teks, folder_bab, outline_bab): cek BARU per bab
     (tabel R3, posisi R4, surname R2). Cek kata/sitasi/bentuk sudah di
     Lapisan 1 (mutu_isi_buku) dan TIDAK diulang di sini.
  4. gerbang_dengan_perbaikan(gate_fn, repair_fn, lapor): gerbang gagal
     pada hal deterministik -> perbaikan sekali -> gerbang ulang -> baru
     gagal. Tanpa ini, buku yang sebenarnya bisa diselamatkan ikut
     terbuang + refund.
"""
import json
import os
import re

from . import referensi_indeks as _RI

_SUB_WAJIB_3 = 'perbandingan kritis'
_SUB_WAJIB_4 = ('posisi', 'sintesis')
_JUDUL_SUB_BAKU = {
    'definisi dan konsep kunci',
    'perkembangan teori dan kajian',
    'perbandingan kritis',
    'posisi dan sintesis penulis',
    'implikasi',
}
_FRASA_POSISI = (
    'posisi penulis',
    'sintesis penulis',
    'penulis berpendapat',
    'penulis menilai',
    'penulis menyimpulkan',
    'penulis menegaskan',
    'menurut penulis',
    'pandangan penulis',
)


def _babs(outline):
    """[(nomor, bab)] terurut; kunci str-digit diterima (dari JSON)."""
    if not isinstance(outline, dict):
        return []
    out = []
    for k, v in outline.items():
        try:
            n = int(k)
        except (TypeError, ValueError):
            continue
        if isinstance(v, dict):
            out.append((n, v))
    return sorted(out, key=lambda x: x[0])


def _bersih(teks):
    return bool(teks and str(teks).strip())


def _subs(bab):
    subs = (bab or {}).get('subs') or []
    return [s for s in subs if isinstance(s, (list, tuple)) and len(s) >= 3]


def periksa_outline(outline, jumlah_harus=None):
    """Cek struktur referensi. Return {'lolos': bool, 'masalah': [...]}.

    Hanya cek BARU (di luar outline_buku.periksa yang memeriksa bentuk:
    judul kosong, sub kosong, key_points kosong). Masalah = keras
    (produksi tidak boleh lanjut).
    """
    masalah = []
    babs = _babs(outline)
    if not babs:
        return {'lolos': False, 'masalah': ['outline tidak punya bab']}
    if jumlah_harus is not None and len(babs) != jumlah_harus:
        masalah.append(
            f'jumlah bab {len(babs)} tidak sesuai paket '
            f'(harus {jumlah_harus})')
    judul_lihat = {}
    for n, bab in babs:
        judul = str(bab.get('title') or '').strip()
        if not judul:
            masalah.append(f'BAB {n}: judul kosong')
            continue
        kunci = judul.lower()
        if kunci in judul_lihat:
            masalah.append(
                f'judul bab ganda: BAB {judul_lihat[kunci]} dan BAB {n} '
                f'({judul})')
        else:
            judul_lihat[kunci] = n
        subs = _subs(bab)
        if len(subs) != 5:
            masalah.append(f'BAB {n}: {len(subs)} sub-bab (harus 5)')
        ada3 = ada4 = False
        for s in subs:
            nomor = str(s[0])
            judul_sub = str(s[1] or '').lower()
            if nomor.endswith('.3'):
                ada3 = True
                if _SUB_WAJIB_3 not in judul_sub:
                    masalah.append(
                        f'BAB {n}: sub {s[0]} harus mengandung '
                        f'"Perbandingan Kritis"')
            if nomor.endswith('.4'):
                ada4 = True
                if not any(k in judul_sub for k in _SUB_WAJIB_4):
                    masalah.append(
                        f'BAB {n}: sub {s[0]} harus mengandung '
                        f'"Posisi" atau "Sintesis"')
            if not _bersih(s[1]):
                masalah.append(f'BAB {n}: judul sub kosong ({s[0]})')
        if subs and not ada3:
            masalah.append(f'BAB {n}: tidak ada sub .3 (Perbandingan Kritis)')
        if subs and not ada4:
            masalah.append(f'BAB {n}: tidak ada sub .4 (Posisi/Sintesis)')
    return {'lolos': not masalah, 'masalah': masalah}


def skor_risiko(outline, jumlah_harus=None):
    """(level, [alasan]). Merah = ada masalah keras; Kuning = peringatan;
    Hijau = bersih. Alasan dibatasi 12 butir supaya halaman tidak penuh."""
    cek = periksa_outline(outline, jumlah_harus)
    if not cek['lolos']:
        return 'Merah', list(cek['masalah'])
    peringatan = []
    for n, bab in _babs(outline):
        judul = str(bab.get('title') or '').strip()
        if judul and len(judul) < 12:
            peringatan.append(
                f'BAB {n}: judul sangat pendek ({len(judul)} huruf)')
        for s in _subs(bab):
            judul_sub = str(s[1] or '').strip()
            poin = str(s[2] or '').strip()
            if judul_sub and judul_sub.lower() in _JUDUL_SUB_BAKU:
                peringatan.append(
                    f'BAB {n}: sub {s[0]} belum diperkaya topik bab')
            if poin and len(poin) < 30:
                peringatan.append(
                    f'BAB {n}/{s[0]}: key_points sangat pendek')
    if peringatan:
        return 'Kuning', peringatan[:12]
    return 'Hijau', []


def _baca_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _refs_dari_json(data):
    if isinstance(data, list):
        return [str(x) for x in data if x]
    if isinstance(data, dict):
        refs = data.get('refs') or data.get('referensi') or []
        return [str(x) for x in refs if x]
    return []


def periksa_bab_awal(n, teks, folder_bab, outline_bab=None):
    """Cek BARU per bab (di luar Lapisan 1). Return {'masalah', 'curiga'}.

    Semua string diawali 'BAB {n}: ' supaya bab_bermasalah() Lapisan 1
    membacanya dan putaran perbaikan ikut memperbaiki bab ini.
    Tidak pernah raise: berkas tak terbaca = curiga, bukan crash.
    outline_bab diterima untuk perluasan; cakupan sub sudah di Lapisan 1.
    """
    masalah, curiga = [], []
    teks = teks or ''
    visual = os.path.join(folder_bab or '', 'visual')
    # R3 (proksi: berkas tabel bab ada dan tidak kosong; gerbang final
    # yang menilai tabelnya benar-benar komparasi).
    tabel_path = os.path.join(visual, f'tabel_bab{n}.json')
    try:
        tabel = _baca_json(tabel_path)
        ada_tabel = bool(tabel)
    except Exception:
        ada_tabel = False
    if not ada_tabel:
        masalah.append(
            f'BAB {n}: tidak ada tabel (syarat R3: tabel komparasi per bab)')
    # R4 (proksi berbasis frasa; gerbang final yang menilai).
    teks_rendah = teks.lower()
    kalimat_posisi = None
    for frasa in _FRASA_POSISI:
        idx = teks_rendah.find(frasa)
        if idx >= 0:
            awal = teks.rfind('.', 0, idx) + 1
            akhir = teks.find('.', idx)
            if akhir < 0:
                akhir = len(teks)
            kalimat_posisi = teks[awal:akhir].strip()
            break
    if kalimat_posisi is None:
        masalah.append(
            f'BAB {n}: tidak ada kalimat posisi penulis eksplisit '
            f'(syarat R4)')
    elif len(kalimat_posisi.split()) < 10:
        curiga.append(
            f'BAB {n}: kalimat posisi penulis terlalu pendek '
            f'({len(kalimat_posisi.split())} kata)')
    # R2: surname referensi bab ini cocok dengan sitasi di badan bab ini.
    refs_path = os.path.join(visual, f'refs_bab{n}.json')
    try:
        refs = _refs_dari_json(_baca_json(refs_path))
    except Exception:
        refs = None
    if refs is None:
        curiga.append(f'BAB {n}: berkas referensi bab tidak terbaca')
    elif not refs:
        curiga.append(f'BAB {n}: tidak ada referensi (indeks nama kosong)')
    else:
        kandidat = _RI.kumpulkan_nama(refs)
        cocok = 0
        for cand in kandidat:
            if re.search(r'\b' + re.escape(cand) + r'\b', teks,
                         re.IGNORECASE):
                cocok += 1
        if kandidat and cocok == 0:
            masalah.append(
                f'BAB {n}: 0 dari {len(kandidat)} surname referensi cocok '
                f'dengan sitasi di badan (prediksi R2 kosong)')
        elif kandidat and cocok < len(kandidat):
            curiga.append(
                f'BAB {n}: hanya {cocok} dari {len(kandidat)} surname '
                f'cocok dengan sitasi di badan')
    return {'masalah': masalah, 'curiga': curiga}


def gerbang_dengan_perbaikan(gate_fn, repair_fn, lapor=None):
    """Gerbang gagal -> perbaikan deterministik sekali -> gerbang ulang.

    Return True bila lolos (awal atau sesudah perbaikan). Raise
    RuntimeError bila tetap gagal (pesan menyebut perbaikan sudah dicoba)
    atau bila perbaikan sendiri gagal (pesan menyebut keduanya).
    """
    def _lapor(pesan):
        if lapor is not None:
            try:
                lapor(pesan)
            except Exception:
                pass

    try:
        gate_fn()
        return True
    except Exception as e:
        e1 = e
    _lapor(f'Gerbang gagal, mencoba perbaikan deterministik sekali: {e1}')
    try:
        repair_fn()
    except Exception as e_repair:
        raise RuntimeError(
            f'{e1} (perbaikan deterministik gagal: {e_repair})')
    try:
        gate_fn()
        _lapor('Perbaikan deterministik berhasil, gerbang lolos')
        return True
    except Exception as e2:
        raise RuntimeError(
            f'{e2} (perbaikan deterministik sudah dicoba sekali)')
