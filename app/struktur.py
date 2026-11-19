"""Pembantu alur pilot "Periksa Struktur" (15 Nov 2026).

MURNI (stdlib + json saja, tanpa Jev, tanpa DB) supaya gampang diuji.
Dipakai endpoint status, gerbang ambang di `peta_mulai`, dan pemicu otomatis.

SATU GARIS AWAL (perintah Boss 08:41 WIB): manual dan otomatis memakai
SATU penghitung perubahan yang sama, `peta_sidik` + baris peta tersimpan
saat pemeriksaan terakhir. Menekan tombol ATAU jalan otomatis sama-sama
memperbarui keduanya, jadi penghitung mulai dari nol lagi dan tidak ada
perubahan yang diperiksa dua kali.
"""
from __future__ import annotations

import json
import re

from .ambang_periksa import bandingkan_perubahan

LABEL_SAH = ('bab', 'subbab', 'paragraf', 'biasa')

_ROMAWI_BAB = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
_ANGKA_ROMAWI_BAB = {v: k for k, v in _ROMAWI_BAB.items()}
_POLAA_BAB_BERLABEL = re.compile(r'^\s*BAB\s+([IVX]+|\d+)\b',
                                 re.IGNORECASE)


def _nomor_penanda_bab_telanjang(teks: str) -> int | None:
    """Angka bab dari penanda TELANJANG ('BAB II', 'BAB 3') atau None.

    Hanya yang telanjang (tidak ada teks sesudah penanda): sebutan bab
    di Sistematika Penulisan ('BAB II TINJAUAN PUSTAKA') BUKAN awal
    bab, peta lengkap fid 81 memuat 5 sebutan itu (baris 191-207) di
    samping 5 penanda telanjang yang asli (baris 0/211/385/607/833),
    jadi pola awalan saja akan memecah pengelompokan jadi 10 kelompok.
    Cermin _POLAA_BAB_JUDUL + _angka_bab di bagian_awal.py (pemindai
    gerbang yang sama), diperketat jadi telanjang; struktur.py tidak
    boleh mengimpor bagian_awal (bagian_awal memakai struktur, impor
    balik = siklus).
    """
    s = ' '.join(str(teks or '').split()).strip()
    m = re.fullmatch(r'BAB\s+([IVX]+|\d+)', s, re.IGNORECASE)
    if not m:
        return None
    t = m.group(1).upper()
    if t in _ROMAWI_BAB:
        return _ROMAWI_BAB[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def _nomor_dari_judul_bab(teks: str) -> int | None:
    """Angka bab dari judul bab berlabel ('BAB II TINJAUAN PUSTAKA')."""
    m = _POLAA_BAB_BERLABEL.match(' '.join(str(teks or '').split()))
    if not m:
        return None
    t = m.group(1).upper()
    if t in _ROMAWI_BAB:
        return _ROMAWI_BAB[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def keadaan_tombol(sudah_diperiksa: bool, berubah_berarti: bool) -> dict:
    """Keadaan tombol "Periksa Struktur" untuk satu naskah.

    - belum pernah diperiksa -> aktif, "Periksa Struktur".
    - sudah diperiksa + tidak ada perubahan berarti -> nonaktif,
      "Sudah Diperiksa".
    - sudah diperiksa + ada perubahan berarti -> aktif, "Periksa Lagi".
    """
    if not sudah_diperiksa:
        return {'keadaan': 'belum', 'aktif': True,
                'label': 'Periksa Struktur'}
    if berubah_berarti:
        return {'keadaan': 'berubah', 'aktif': True, 'label': 'Periksa Lagi'}
    return {'keadaan': 'sudah', 'aktif': False, 'label': 'Sudah Diperiksa'}


def nilai_gerbang(*, peta_json, peta_sidik: str, sidik_kini: str,
                  teks_kini_bersih: str, fn_susun_teks=None) -> dict:
    """SATU gerbang untuk manual + otomatis (garis awal tunggal).

    `teks_kini_bersih`: teks naskah sekarang SESUDAH `buang_daftar_isi`
    (pemanggil yang membuangnya, baris peta tersimpan sudah bersih).
    `sidik_kini`: sidik teks MENTAH sekarang (dipakai pagar C2).
    Perbandingan ambang memakai peta tersimpan itu sendiri
    (`ambang_periksa.bandingkan_perubahan`), bukan teks lama terpisah ,
    jadi manual dan otomatis sungguh membaca garis awal yang sama.
    `fn_susun_teks`: hanya untuk uji (bawaan: susun produksi).

    Kembalikan dict:
      keadaan: 'belum' | 'sudah' | 'berubah'
      sudah_diperiksa, bisa_periksa, berubah_berarti, berubah_besar,
      otomatis (boleh jalan sendiri), detail (ukuran perubahan).
    """
    if not peta_json or not peta_sidik:
        return {'keadaan': 'belum', 'sudah_diperiksa': False,
                'bisa_periksa': True, 'berubah_berarti': False,
                'berubah_besar': False, 'otomatis': False,
                'detail': {'alasan': 'belum pernah diperiksa'}}
    if peta_sidik == sidik_kini:
        return {'keadaan': 'sudah', 'sudah_diperiksa': True,
                'bisa_periksa': False, 'berubah_berarti': False,
                'berubah_besar': False, 'otomatis': False,
                'detail': {'alasan': 'naskah tidak berubah'}}
    detail = bandingkan_perubahan(peta_json, teks_kini_bersih or '',
                                  fn_susun_teks)
    berubah = bool(detail['berubah_berarti'])
    besar = bool(detail['berubah_besar'])
    # (15 Nov 2026, perintah Bos 09:15) Otomatis TIDAK PERNAH membaca ulang
    # penuh: perubahan struktural (besar ATAU kecil) hanya mengaktifkan
    # tombol manual ("Periksa Lagi"). Batas laju 24 jam TIDAK di sini
    # (butuh waktu pemeriksaan terakhir dari DB — dicek endpoint).
    struktural = bool(detail.get('struktural')
                      or detail.get('struktural_kecil'))
    otomatis = besar and not struktural
    return {'keadaan': 'berubah' if berubah else 'sudah',
            'sudah_diperiksa': True,
            'bisa_periksa': berubah,
            'berubah_berarti': berubah,
            'berubah_besar': besar,
            'otomatis': otomatis,
            'detail': detail}


def _teks_subbab_normal(teks: str) -> str:
    """Judul subbab tanpa nomor, penanda bab, dan awalan 'SUB-BAB'.

    '1.2 Perkembangan ...' dan 'SUB-BAB Perkembangan ...' adalah judul
    yang sama; begitu pula '1.4 Posisi ...' dan 'Posisi ...' telanjang.
    Cermin _judul_subbab_normal di bagian_awal.py (perbaikan Daftar Isi
    f1ed9e3), supaya panel 'Struktur naskah' dan Daftar Isi membuang
    gema yang sama.
    """
    s = ' '.join(str(teks or '').split()).strip().lower()
    s = re.sub(r'^bab\s+(?:[ivx]+|\d+)[\s.]*', '', s)
    s = re.sub(r'^\d+\.\d+\s*', '', s)
    s = re.sub(r'^sub[ -]?bab\b\s*', '', s)
    return s.strip()


def _judul_bab_penuh(baris, label, idx_awal: int, nomor: int) -> str:
    """Judul bab lengkap ('BAB I PENDAHULUAN') dari penanda telanjang.

    Penanda telanjang ('BAB I') tidak membawa nama bab; namanya ada di
    baris tak berlabel pertama sesudahnya ('PENDAHULUAN', baris 2 fid 81;
    'TINJAUAN PUSTAKA', baris 213). Dipakai panel ceklist Struktur
    naskah (19 Nov 2026): mahasiswa melihat nama babnya, bukan cuma
    'BAB I'. Bila tidak ketemu, kembalikan penanda telanjangnya saja.
    """
    romawi = _ANGKA_ROMAWI_BAB.get(nomor) or str(nomor)
    dasar = f'BAB {romawi}'
    for j in range(idx_awal + 1, min(idx_awal + 4, len(baris))):
        teks = ' '.join(str(baris[j] or '').split()).strip()
        if not teks:
            continue
        lab = label.get(str(j)) or label.get(j) or ''
        if lab:
            break
        if _nomor_penanda_bab_telanjang(teks) is not None:
            break
        if teks.upper() in ('LAMPIRAN', 'DAFTAR PUSTAKA'):
            break
        return f'{dasar} {teks}'
    return dasar


def ceklist_struktur(peta_json, menunggu_idx: set | None = None) -> dict:
    """Ceklist Struktur naskah: 5 baris bab untuk layar mahasiswa.

    Membungkus `ringkas_peta`: hanya kelompok bab (LAMPIRAN bukan bab,
    jadi tidak masuk), tiap baris membawa `judul` lengkap
    ('BAB I PENDAHULUAN'), `nomor` (1-5), `ada` (True bila babnya
    ketemu di naskah), dan `diperiksa`. Bab yang tidak ketemu tetap
    tampil sebagai baris Belum (!), supaya mahasiswa langsung tahu
    bab mana yang hilang. Dipakai panel ceklist (19 Nov 2026).
    """
    ringkasan = ringkas_peta(peta_json, menunggu_idx=menunggu_idx)
    keluar: dict = {'bab': [], 'jumlah_ragu': ringkasan['jumlah_ragu'],
                    'jumlah_curiga': ringkasan['jumlah_curiga'],
                    'jumlah_menunggu': ringkasan['jumlah_menunggu']}
    ada_nomor = set()
    for bab in ringkasan.get('bab', []):
        judul = str(bab.get('judul', '') or '').strip()
        if judul.upper() == 'LAMPIRAN':
            continue
        nomor = bab.get('nomor')
        if nomor is None:
            nomor = _nomor_dari_judul_bab(judul)
        if nomor is None or not 1 <= nomor <= 6:
            continue
        ada_nomor.add(nomor)
        keluar['bab'].append({
            'judul': bab.get('judul_penuh') or judul,
            'nomor': nomor, 'ada': True,
            'diperiksa': bool(bab.get('diperiksa')),
            'subbab': bab.get('subbab') or []})
    for nomor in range(1, 6):
        if nomor in ada_nomor:
            continue
        romawi = _ANGKA_ROMAWI_BAB.get(nomor) or str(nomor)
        keluar['bab'].append({
            'judul': f'BAB {romawi}', 'nomor': nomor, 'ada': False,
            'diperiksa': False, 'subbab': []})
    keluar['bab'].sort(key=lambda b: b['nomor'])
    return keluar


def langkah_berikut_struktur(ceklist_bab, bagian_awal_selesai: bool,
                             diagram_selesai: bool) -> str | None:
    """Satu baris 'Langkah berikut' untuk ceklist Struktur naskah.

    - Ada bab yang tidak ketemu -> periksa judul bab di naskah.
    - Semua bab ada -> tahap berikutnya yang belum selesai
      (Bagian Awal dulu, lalu Diagram). Bila semua sudah selesai,
      None (baris tidak tampil). Murni, tanpa DB.
    """
    for bab in ceklist_bab or []:
        if not bab.get('ada'):
            return 'Periksa judul bab di naskah'
    if not bagian_awal_selesai:
        return 'Lengkapi Bagian Awal'
    if not diagram_selesai:
        return 'Buat Diagram Model'
    return None


def ringkas_peta(peta_json, menunggu_idx: set | None = None) -> dict:
    """Ringkas peta tersimpan jadi pohon bab/subbab untuk layar mahasiswa.

    Hanya yang sistem yakini yang tampil sebagai daftar; baris yang masih
    menunggu keputusan admin ditandai "sedang diperiksa" (bukan disembunyikan).
    `menunggu_idx`: indeks baris yang masih antre (dari tabel antrean).
    """
    menunggu_idx = set(menunggu_idx or set())
    keluar: dict = {'bab': [], 'jumlah_ragu': 0, 'jumlah_curiga': 0,
                    'jumlah_menunggu': len(menunggu_idx)}
    try:
        peta = json.loads(peta_json) if isinstance(peta_json, str) \
            else (peta_json or {})
    except Exception:                                       # noqa: BLE001
        return keluar
    surveyor = peta.get('peta_surveyor') or {}
    baris = [str(x) for x in (surveyor.get('baris') or [])]
    label = surveyor.get('label') or {}
    hakim = peta.get('hakim') or {}
    keluar['jumlah_ragu'] = int(hakim.get('jumlah_ragu') or 0)
    keluar['jumlah_curiga'] = int(hakim.get('jumlah_curiga') or 0)
    bab_kini = None
    nomor_bab_kini = None
    for i, teks in enumerate(baris):
        lab = label.get(str(i)) or label.get(i) or ''
        teks_ringan = ' '.join(teks.split()).strip()
        if not teks_ringan:
            continue
        # Penanda bab telanjang ('BAB II', tanpa nama dan tanpa label):
        # peta Jev tidak melabeli satu pun judul bab fid 81, jadi tanpa
        # ini 131 subbab menumpuk di bawah satu bab palsu berjudul
        # kosong dan template menampilkan kata ganti 'Bab' (cacat panel
        # 'Struktur naskah', 17 Nov 2026). Hanya yang telanjang dan
        # yang nomornya NAIK dari bab kini yang membuka kelompok baru:
        # sebutan di Sistematika ('BAB II TINJAUAN PUSTAKA') dan
        # penanda yang terulang tidak boleh memecah kelompok.
        # Baris berlabel 'bab'/'subbab' tidak disentuh di sini (label
        # Jev yang menang).
        if lab not in ('bab', 'subbab'):
            nomor = _nomor_penanda_bab_telanjang(teks_ringan)
            if nomor is not None and (nomor_bab_kini is None
                                      or nomor > nomor_bab_kini):
                bab_kini = {'judul': f'BAB {_ANGKA_ROMAWI_BAB[nomor]}',
                            'judul_penuh': _judul_bab_penuh(
                                baris, label, i, nomor),
                            'nomor': nomor,
                            'subbab': [],
                            'diperiksa': i not in menunggu_idx}
                keluar['bab'].append(bab_kini)
                nomor_bab_kini = nomor
                continue
            # Penanda lampiran telanjang ('LAMPIRAN', tanpa nama dan
            # tanpa label): isi lampiran sesudahnya bukan subbab BAB V
            # (cacat uji live 17 Nov 2026, fid 81: 46 subbab lampiran
            # menumpuk di BAB V, padahal BAB V hanya Kesimpulan +
            # Saran). Hanya sesudah bab dimulai dan hanya bila kelompok
            # kini belum lampiran; 'DAFTAR PUSTAKA' tidak membuka
            # kelompok (isinya bukan subbab, tidak ada yang menumpuk).
            # Kelompok ini tampil sebagai baris ke-6 di panel; Daftar
            # Isi tetap tidak memuat judul 'LAMPIRAN' (entri_daftar_isi
            # melewati entri level-0 kelompok ini, subbabnya tetap
            # level-1).
            if nomor_bab_kini is not None and bab_kini is not None \
                    and (bab_kini.get('judul') or '') != 'LAMPIRAN' \
                    and teks_ringan.upper() == 'LAMPIRAN':
                bab_kini = {'judul': 'LAMPIRAN', 'subbab': [],
                            'diperiksa': i not in menunggu_idx}
                keluar['bab'].append(bab_kini)
                continue
        if lab not in LABEL_SAH:
            continue
        butir = {'teks': teks_ringan, 'label': lab,
                 'diperiksa': i not in menunggu_idx}
        if lab == 'bab':
            _nomor = _nomor_dari_judul_bab(teks_ringan)
            bab_kini = {'judul': teks_ringan,
                        'judul_penuh': teks_ringan, 'nomor': _nomor,
                        'subbab': [],
                        'diperiksa': butir['diperiksa']}
            keluar['bab'].append(bab_kini)
            if _nomor is not None:
                nomor_bab_kini = _nomor
        elif lab == 'subbab':
            if bab_kini is None:
                bab_kini = {'judul': '', 'subbab': [], 'diperiksa': True}
                keluar['bab'].append(bab_kini)
            bab_kini['subbab'].append(butir)
            if not butir['diperiksa']:
                bab_kini['diperiksa'] = False
        # 'paragraf'/'biasa' tidak tampil di daftar bab (sesuai rancangan:
        # layar hasil hanya daftar bab/subbab).
    # Gema subbab: badan menulis judul yang sama dua kali berurutan
    # ('1.2 ...' lalu 'SUB-BAB ...'; '1.4 ...' lalu judul telanjang) dan
    # peta melabeli keduanya 'subbab' (cacat uji live 17 Nov 2026,
    # file 126; perbaikan Daftar Isi f1ed9e3 memakai aturan yang sama).
    # Hanya yang BERURUTAN yang dibuang: judul sah yang berulang
    # ('Ringkasan Bab') tidak pernah berurutan. Yang dipertahankan
    # ditandai diperiksa hanya bila SEMUA gema sudah diperiksa, supaya
    # baris yang masih antre tidak hilang dari penanda.
    for bab in keluar['bab']:
        bersih = []
        for sub in bab.get('subbab') or []:
            normal = _teks_subbab_normal(sub.get('teks', ''))
            if bersih and normal and normal == _teks_subbab_normal(
                    bersih[-1].get('teks', '')):
                bersih[-1]['diperiksa'] = bool(
                    bersih[-1].get('diperiksa')) and bool(
                    sub.get('diperiksa'))
                continue  # gema: judul sama persis, buang yang kedua
            bersih.append(sub)
        bab['subbab'] = bersih
        bab['diperiksa'] = bool(bab.get('diperiksa')) and all(
            s.get('diperiksa') for s in bersih)
    return keluar


# ── PEMERIKSAAN DI LATAR (15 Nov 2026, perintah Bos 11:12) ───────────────
#  Tombol "Periksa Struktur" membalas cepat; pemeriksaannya jalan di latar
#  memakai pekerja `proses` yang SUDAH ADA (pola `peta_otomatis`), dan
#  layar membaca keadaan dari server lewat `peta_status`, bukan dari
#  halaman, jadi tutup-buka halaman saat jalan tetap menampilkan
#  "Sedang Diperiksa".
#
#  MURNI (tanpa DB) supaya gampang diuji: pemanggil yang mengambil baris
#  proses dari DB, fungsi di sini hanya menilai dict-nya.

#  Komentar proses pemeriksaan struktur (manual MAUPUN otomatis). Komentar
#  manual: ['Pemeriksaan struktur']; otomatis: ['Pemeriksaan struktur
#  otomatis'], keduanya diawali teks yang sama, jadi satu penanda cukup.
KOMENTAR_PETA = 'Pemeriksaan struktur'


def adalah_proses_peta(komentar_json) -> bool:
    """True bila baris proses ini adalah pemeriksaan struktur (manual/otomatis).

    `komentar_json`: isi kolom komentar_json (JSON daftar teks, atau teks
    mentah bila bukan JSON). Proses lain (mis. revisi) TIDAK cocok, supaya
    revisi yang sedang jalan tidak membuat layar menampilkan
    "Sedang Diperiksa".
    """
    try:
        data = json.loads(komentar_json) if isinstance(komentar_json, str) \
            else komentar_json
    except Exception:                                       # noqa: BLE001
        data = None
    if isinstance(data, list):
        return any(isinstance(x, str) and x.startswith(KOMENTAR_PETA)
                   for x in data)
    if isinstance(data, str):
        return data.startswith(KOMENTAR_PETA)
    return isinstance(komentar_json, str) and \
        KOMENTAR_PETA in komentar_json


def keadaan_pemeriksaan(*, proses_jalan, proses_terakhir, peta_ada) -> dict:
    """Keadaan pemeriksaan struktur untuk layar (murni, tanpa DB).

    `proses_jalan`: dict {'kode', 'status', 'galat'} proses peta yang
    SEDANG jalan (status 'menunggu'/'jalan'), atau None.
    `proses_terakhir`: dict yang sama untuk proses peta TERAKHIR (apa pun
    statusnya, yang terbaru), atau None. Dipakai untuk vonis gagal yang
    jujur: bila upaya terakhir gagal, layar berkata gagal + tombol aktif
    lagi, bukan diam. Upaya terakhir yang berhasil menutupi kegagalan lama.
    `peta_ada`: True bila peta tersimpan ada (peta_json tidak kosong).

    Kembalikan {'keadaan': 'jalan'|'selesai'|'gagal'|'belum',
    'kode': kode proses (atau None), 'galat': pesan gagal (atau '')}.
    """
    if proses_jalan is not None:
        return {'keadaan': 'jalan', 'kode': proses_jalan.get('kode'),
                'galat': ''}
    if proses_terakhir is not None \
            and proses_terakhir.get('status') == 'gagal':
        return {'keadaan': 'gagal', 'kode': proses_terakhir.get('kode'),
                'galat': proses_terakhir.get('galat') or ''}
    if peta_ada:
        return {'keadaan': 'selesai', 'kode': None, 'galat': ''}
    return {'keadaan': 'belum', 'kode': None, 'galat': ''}
