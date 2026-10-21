"""Versi dokumen per BAB + rollback — (ACC Bos 14Sep26).

═══════════════════════════════════════════════════════════════════════════
PRINSIP (kata Bos): "selalu ada backup di VPS, tapi maksimal 2 supaya
mahasiswa tidak bingung — sistemnya geser seperti gear."

  • Hasil revisi AI TIDAK PERNAH menimpa dokumen asli.
  • Setiap revisi → VERSI BARU (baris baru di tabel `versi_dokumen`).
  • Versi yang dipakai mahasiswa = yang `terpakai=True`.
  • Tersimpan maksimal VERSI_SIMPAN = 2 versi lama per (file, bab).
  • Versi ke-3 muncul → versi TERTUA auto-dibuang (gear berputar).
  • Mahasiswa bisa rollback 2×: "Kembalikan versi sebelumnya".
═══════════════════════════════════════════════════════════════════════════

Bab dideteksi dari teks dokumen:
  "BAB I PENDAHULUAN", "BAB II TINJAUAN PUSTAKA", ...
  Angka Romawi DAN Arab didukung. Huruf besar/kecil didukung.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import VersiDokumen, VersiPipa, _now

log = logging.getLogger('eduai.versi')

# Berapa versi lama yang disimpan per (file, bab). ACC Bos: 2.
VERSI_SIMPAN = 2
BAB_SELURUH = '__seluruh__'

# ── Pola judul bab ──────────────────────────────────────────────────────
# Didukung:  BAB I   BAB II   BAB 3   BAB IV   BAB V
#            (judul opsional di belakangnya)
#
# JEBAKAN yang sudah diuji pada tesis asli (14Sep26) dan HARUS ditolak:
#   1. Daftar isi ......... "BAB I  PENDAHULUAN12"      → ada nomor halaman
#   2. Kalimat penjelas ... "Bab I Pendahuluan. Bab ini menguraikan..."
#      (huruf kecil di tengah teks paragraf — bukan judul berdiri sendiri)
#   3. Sub-bab ............ "BAB II: SUB-BAB 2.3 TEORI PENDUKUNG"
#      (judul bab yang mengandung ': SUB-BAB' — bukan bab baru)
_ROMawi = 'IVXLCDM'
# 🔴 BUG NYATA (ditemukan 03Okt26, skripsi S1 nyata UNMUL 5 MB):
# Sebelumnya pola ini memakai `\b` (batas kata) setelah nomor bab, jadi WAJIB
# ada spasi/tanda setelah nomor:
#     "BAB I PENDAHULUAN"  ✓   "BAB IPENDAHULUAN"  ✗ GAGAL
# Naskah nyata SANGAT SERING menempelkan judul tanpa spasi ("BAB IPENDAHULUAN",
# "BAB IIIMETODOLOGI PENELITIAN") karena hasil ekspor Word/Docs. Akibatnya
# deteksi_bab() balas 0 bab → peta bab HILANG → AI menerima naskah sebagai
# satu unit, kuota salah, Mode Belajar mustahil. Terukur: SKRIPSI S1 = 0 bab
# (padahal punya 5), TESIS S2 7 bab hanya terbaca 3 → 4 bab layanan HILANG.
#
# ⚠️ KENAPA BUG INI LAMA TAK KETAHUAN: pola ini adalah SALINAN KEDUA. Yang
#    pertama ada di `app/state.py` dan SUDAH diperbaiki 16Sep26 (lihat
#    state.py komentar "BUG NYATA ke-7"). Berkas ini TIDAK ikut diperbaiki
#    karena saat itu tidak ada grep menyeluruh untuk pola kembar.
#    ⇒ PELAJARAN: setiap kali memperbaiki pola regex, GREP dulu seluruh app/.
#
# POLA BARU = SAMA dengan app/state.py:203 (terbukti pada naskah nyata):
#   • TANPA `\b` → menerima judul menempel ("BAB IPENDAHULUAN")
#   • nomor romawi 1–5 huruf, WAJIB HURUF BESAR (`[IVXLC]{1,5}`), supaya
#     kalimat biasa "bab ini menjelaskan" TIDAK ikut tertangkap
#   • kata "BAB" tetap case-insensitive (naskah nyata menulis "Bab")
# ⚠️ Penyaring daftar isi (_NOMOR_NEMPEL) & penanda kalimat penjelas di
#    bawahnya TETAP dipakai — jangan dihapus.
# ⭐ 05Okt26 (putusan Bos "A"): + angka Arab & romawi-titik, disamakan
#   dengan app/state.py & cari_bagian.py. Pola kembar (pelajaran 03Okt26).
#   ⚠️ `[ \t\r]*`: PDF menulis 'IV. HASIL \r' — `$` cocok SEBELUM '\n', BUKAN '\r'.
_POLA_BAB = re.compile(
    r'^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5}|\d{1,2})[ \t]*(.*)$',
    re.MULTILINE,
)
#  romawi + TITIK tanpa kata "BAB" — nomor di grup(1), judul di grup(2)
_POLA_BAB_TITIK = re.compile(
    r'^[ \t]*([IVXLC]{1,5})\.[ \t]+([A-Z][A-Z0-9 ,\-]{3,70})[ \t\r]*$',
    re.MULTILINE,
)
# Judul bab dianggap SALAH kalau mengandung penanda ini
# (judul KOSONG tetap sah — mis. baris cuma "BAB I" tanpa judul di belakangnya)
_TOLAK_JUDUL = re.compile(r'sub[\s_-]*bab', re.IGNORECASE)
# Nomor halaman nempel di ujung judul → "PENDAHULUAN12"
_NOMOR_NEMPEL = re.compile(r'(\D)\d{1,3}$')
# ── PENANDA KALIMAT PENJELAS (ACC Bos 15Sep26) ──────────────────────────
# Di tesis Bos, bagian "Sistematika Penulisan" memuat kalimat seperti
#   "Bab II Kajian Pustaka. Bab ini menyajikan landasan teori ..."
# Bentuknya mirip judul bab, tapi sebenarnya KALIMAT BIASA di dalam BAB I.
# Kalimat penjelas hampir selalu memakai kata penunjuk berikut setelah
# "Bab <nomor> ... ." → dipakai untuk MEMBEDAKAN dari judul bab asli.
_PENANDA_KALIMAT = re.compile(
    r'\b(Bab ini|bab ini|Bab tersebut|bab tersebut|menguraikan|menyajikan|'
    r'menjelaskan|memuat|membahas|berisi|berkaitan|Bab\s+[IVXLCDM\d]+\s+'
    r'(?:ini|tersebut))\b'
)


def _romawi_ke_int(s: str) -> int:
    """Konversi angka Romawi → int. '' kalau tidak valid."""
    peta = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    s = (s or '').upper()
    if not s or any(c not in peta for c in s):
        return 0
    hasil, sblm = 0, 0
    for c in reversed(s):
        n = peta[c]
        if n < sblm:
            hasil -= n
        else:
            hasil += n
            sblm = n
    return hasil


def nomor_bab_ke_label(n: int) -> str:
    """1 → 'BAB I', 4 → 'BAB IV'. >10 tetap pakai angka Arab."""
    romawi = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
              7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'}
    return f'BAB {romawi.get(n, str(n))}'


def _potong_pembuka(teks: str) -> tuple[int, str]:
    """Posisi awal ISI naskah + teks setelah pembuka (cover/daftar).

    🎯 AKAR (diuji 29Sep2026, naskah nyata file78): `deteksi_bab()` dulu
    memindai SELURUH teks → kandidat "BAB I ... VII" di DAFTAR ISI (bertitik,
    4.455-9.834 kar) menang duluan karena diurutkan dari atas. Akibatnya
    "BAB III" terpotong 650 kar (baris daftar isi) dan revisi bab ditolak
    mesin: "Bagian naskah yang ditunjuk catatan tidak ditemukan".

    ATURAN AKAR yang SUDAH ADA (state.awal_isi_naskah, 16Sep26, 6/6 dokumen
    nyata): awal isi = "BAB I" pertama yang judulnya BERSIH. Pemakaian baru
    ini HANYA membuang bagian pembuka dari HITUNGAN DETEKSI — posisi yang
    dikembalikan tetap absolut di teks asli supaya `ambil_bab()` /
    `susun_ulang()` persis seperti sebelumnya.

    GAGAL AMAN: balik (0, teks) → perilaku LAMA persis sama (tidak ada yang
    dipotong). Kami juga memastikan potongan benar-benar dari jalur akar
    (`buang_daftar_isi(teks) == teks[ofs:]`), bukan jalur pembersih baris —
    kalau tidak cocok, tidak ada yang diubah (dilarang menebak).
    """
    if not teks:
        return 0, teks
    try:
        from .state import awal_isi_naskah as _awal
        from .state import buang_daftar_isi as _buang
        ofs = int(_awal(teks) or 0)
        if ofs > 0 and _buang(teks) == teks[ofs:]:
            return ofs, teks[ofs:]
    except Exception as e:                                        # noqa: BLE001
        log.warning('[versi] _potong_pembuka gagal (%s) → jalur lama', e)
    return 0, teks


def deteksi_bab(teks: str) -> list[dict]:
    """Cari batas bab dalam teks.

    Mengembalikan list of dict: {label, nomor, judul, posisi, akhir, isi}
      - `posisi` = indeks awal bab (termasuk judulnya)
      - `akhir`  = indeks akhir bab (= posisi bab berikutnya, atau len(teks))
      - `isi`    = potongan teks bab tersebut

    List kosong = dokumen tidak punya judul bab (dianggap 1 bab utuh).

    PENYARING (hasil uji tesis asli 14Sep26) — tolak kandidat kalau:
      • judulnya mengandung 'SUB-BAB' (itu sub-bab, bukan bab baru)
      • judulnya diakhiri angka (nomor halaman nempel, ciri daftar isi)
      • baris judulnya terlalu panjang (kemungkinan kalimat, bukan judul)
      • nomor bab melompat jauh ke belakang (mis. BAB II setelah BAB V)
    """
    teks = teks or ''
    ofs_pembuka, _ = _potong_pembuka(teks)
    baris_awal = teks[:1] and teks.split('\n')
    kandidat = []
    for m in _POLA_BAB.finditer(teks):
        # kandidat di bagian PEMBUKA (daftar isi, cover) bukan judul bab asli
        if ofs_pembuka and m.start() < ofs_pembuka:
            continue
        angka = m.group(1)
        judul = (m.group(2) or '').strip(' .:-\t')
        nomor = int(angka) if angka.isdigit() else _romawi_ke_int(angka)
        if nomor <= 0:
            continue
        # (a) sub-bab / judul kosong
        if _TOLAK_JUDUL.search(judul):
            continue
        # (b) nomor halaman nempel di ujung judul (ciri daftar isi)
        if judul and _NOMOR_NEMPEL.search(judul):
            continue
        # (d) huruf kecil di judul SETELAH nomor, mis. "BAB I pendahuluan"
        #     (pola baru: group 2 = judul, jadi "bab"/"Bab" sudah tertangani
        #     oleh (?i:BAB) di awal; di sini sisa pemeriksaan tetap dipakai
        #     untuk menjaga perilaku lama).
        pre = teks[m.start():m.start() + 3]
        rest_baris = teks[m.start():teks.find('\n', m.start()) if teks.find('\n', m.start()) > 0 else len(teks)]
        if pre == 'bab':
            continue
        # (e) JUDUL + KALIMAT PENJELAS jadi satu paragraf (ACC Bos 15Sep26)
        #     Kasus nyata tesis Bos: "Bab II Kajian Pustaka. Bab ini
        #     menyajikan landasan teori ..." — judulnya SAH, tapi kalimat
        #     penjelas menempel di belakangnya.
        #     ⚠ SEBELUMNYA baris seperti ini DIBUANG UTUH → judul bab
        #       asli ikut hilang (tesis Bos: cuma 1 dari 5 bab terdeteksi).
        #     ⚠ TAPI jangan langsung terima: di tesis Bos ada JUGA kalimat
        #       SISTEMATIKA PENULISAN di dalam BAB I yang berbentuk sama
        #       ("Bab II Kajian Pustaka. Bab ini menyajikan ...") — itu
        #       BUKAN judul bab. Pembedanya:
        #         (i)  judul bab asli ditulis SEBAGAI JUDUL (bold/heading),
        #              sedangkan kalimat penjelas tidak.
        #         (ii) kalimat penjelas biasanya BERAKHIR titik pada baris
        #              yang sama dan paragrafnya panjang (≥ 200 kar).
        #         (iii) judul bab asli biasanya diikuti isi bab yang sangat
        #              panjang setelahnya.
        #     Aturan pakai: terima hanya kalau judulnya PENDEK (≤ 70 kar)
        #     DAN tidak mengandung kata penanda kalimat penjelas.
        if pre == 'Bab' and ('. ' in rest_baris[4:]):
            judul_awal = rest_baris.split('. ', 1)[0].strip(' .:-\t')
            sisa = re.sub(r'^(Bab|BAB|bab)\s+([IVXLCDM]+|\d{1,2})\s*[:.]?\s*',
                          '', judul_awal).strip(' .:-\t')
            # Ajakan kalimat penjelas (bukan judul bab)
            if _PENANDA_KALIMAT.search(rest_baris):
                continue
            if sisa and len(sisa) <= 70:
                judul = sisa
            elif not judul:
                continue        # benar-benar tanpa judul → bukan bab sah
        # (c) baris judul terlalu panjang = kemungkinan kalimat (bukan judul)
        if len(judul) > 90:
            continue
        kandidat.append({
            'nomor': nomor,
            'label': nomor_bab_ke_label(nomor),
            'judul': judul,
            'posisi': m.start(),
        })

    if not kandidat:
        #  ⭐ 05Okt26 (putusan Bos "A"): bentuk "IV. HASIL DAN PEMBAHASAN" —
        #     romawi + TITIK tanpa kata "BAB" (nyata di 290462754.pdf).
        #     Hanya dijalankan kalau pola utama TIDAK menemukan apa pun,
        #     supaya perilaku lama TIDAK berubah sedikit pun.
        for m in _POLA_BAB_TITIK.finditer(teks):
            if ofs_pembuka and m.start() < ofs_pembuka:
                continue
            nomor = _romawi_ke_int(m.group(1))
            if nomor <= 0:
                continue
            judul = (m.group(2) or '').strip(' .:-\t')
            if not judul or len(judul) > 90 or _TOLAK_JUDUL.search(judul):
                continue
            kandidat.append({
                'nomor': nomor,
                'label': nomor_bab_ke_label(nomor),
                'judul': judul,
                'posisi': m.start(),
            })
    if not kandidat:
        return []

    # Urutkan & buang nomor duplikat (ambil kemunculan pertama)
    kandidat.sort(key=lambda x: x['posisi'])
    unik, terlihat = [], set()
    for t in kandidat:
        if t['nomor'] in terlihat:
            continue
        terlihat.add(t['nomor'])
        unik.append(t)

    # Buang bab yang nomornya melompat jauh ke belakang dari maksimum
    # (mis. kandidat 'BAB II' palsu muncul setelah 'BAB IV' asli)
    maks = max(b['nomor'] for b in unik)
    unik = [b for b in unik if b['nomor'] >= maks - 4] or unik

    # Hitung akhir tiap bab
    for i, t in enumerate(unik):
        t['akhir'] = unik[i + 1]['posisi'] if i + 1 < len(unik) else len(teks)
        t['isi'] = teks[t['posisi']:t['akhir']]
        t['panjang'] = len(t['isi'])
    return unik


from . import peta3_jev as _peta3


def _surveyor_teks(bersih: str) -> dict | None:
    """Peta surveyor dari TEKS yang SUDAH dibersihkan (pintu LAYAR — Lapis 5).

    Dipakai `versi._deteksi_bagian()`. Kembalikan None kalau surveyor mati /
    tidak tersedia ⇒ pemanggil memakai `state.petakan()` (cara lama).
    """
    return _peta3.petakan_teks(bersih or '')


def _deteksi_bagian(teks: str) -> list[dict]:
    """Deteksi bagian naskah LEBIH HALUS dari `deteksi_bab()` — kenal SUB-BAB.

    🔴 BUG NYATA ke-20 (24Sep26, ACC Bos "Opsi 1"): `metode lama HANYA mengenal
    judul "BAB I / BAB II". Padahal daftar pilihan di UI memakai SUB-BAB
    ('1.1', '1.2', '3.4'). Akibatnya `ambil_bab(teks, '1.2')` SELALU gagal →
    balik SELURUH teks (baris 211 versi lama) → revisi 1 paragraf mengirim
    seluruh naskah → 4 Token Revisi. Terukur 24Sep26 pada tesis Bos
    (63.797 kar): minta '1.2' (1.135 kar) tapi yang dikirim 63.797 kar.

    KENAPA pakai `state.petakan()`: fungsinya SUDAH ADA, sudah teruji, dan
    sudah bisa mengenali pola '1.1', 'BAB I', maupun 'BAB I  PENDAHULUAN'.
    Aturan Bos: "sambungkan komponen yang SUDAH ADA, jangan bangun mesin baru".
    Import dilakukan DI DALAM fungsi supaya tidak ada impor melingkar
    (`state.py` mengimpor `models`, bukan `versi`).

    ══ LAPIS 5 (14 Okt 2026) — PINTU LAYAR SURVEYOR JEV ═══════════════════
    Putusan Bos 14 Okt: "Peta3_jev mengganti peta halus" + "peta halus ...
    jangan di buang dan jadikan fallback jika jev dan hakim mati".
    Fungsi ini = PINTU yang dilihat user di editor (pemilih bab/akordeon),
    jadi surveyor WAJIB masuk lewat sini — bukan lewat rute baru.

    URUTAN: ① surveyor Jev (`peta3_jev` → `peta_jembatan`)  ② kalau kosong/
    gagal/mati ⇒ `state.petakan()` (cara lama, APA ADANYA — TIDAK dibuang).
    Bentuk keluaran TIDAK berubah ⇒ pemanggil lama aman.

    Kembalikan [] kalau tidak ada sama sekali / gagal → pemanggil pakai
    hasil `deteksi_bab()` (jalur lama, tidak berubah).
    """
    try:
        from .state import (awal_isi_naskah as _awal,
                            buang_daftar_isi as _buang, petakan as _petakan)
        bersih = _buang(teks or '')

        # ── ① SURVEYOR JEV (jalur PERTAMA — Lapis 5) ──────────────────
        peta = None
        try:
            from .peta_jembatan import dari_surveyor as _jembatan
            peta = _jembatan(_surveyor_teks(bersih), bersih)
            if peta:
                log.info('[versi] _deteksi_bagian: jalur JEV (%d bagian)',
                         len(peta))
            else:
                peta = None
        except Exception as e:                                # noqa: BLE001
            log.info('[versi] _deteksi_bagian: surveyor dilewati (%s)', e)
            peta = None

        # ── ② FALLBACK: cara lama (peta_halus/state) — TIDAK diubah ────
        if not peta:
            peta = _petakan(bersih)
    except Exception as e:                                        # noqa: BLE001
        log.warning('[versi] _deteksi_bagian gagal (%s) → pakai deteksi_bab', e)
        return []

    if not peta:
        return []

    # 🔴 AKAR (29Sep2026): peta dibuat dari teks yang SUDAH dibuang daftar isi,
    # tapi letak tiap bagian dulu dicari di teks ASLI yang MASIH memuat daftar →
    # judul "1.1 Latar Belakang ...." di DAFTAR ISI ketemu duluan (pos 4.647)
    # → potongan 1.1 berisi baris daftar gambar, bukan isinya.
    # Kini dicari di teks yang sama dengan yang dipakai membangun peta, lalu
    # posisinya dikembalikan ke skala teks asli (supaya `susun_ulang` utuh).
    # Pagar: ofs hanya diambil kalau potongan memang jalur akar
    # (`awal_isi_naskah` == selisih panjang) — selain itu jalur lama persis.
    ofs = len(teks) - len(bersih) if len(bersih) < len(teks) else 0
    if ofs <= 0 or _awal(teks) != ofs:
        ofs = 0
    dasar = teks[ofs:] if ofs else teks

    # Peta tidak menyertakan `posisi`/`akhir` → cari sendiri letak tiap bagian
    # di dalam teks (sekali jalan, maju terus) supaya bisa dipotong.
    hasil, cari_dari = [], 0
    for bagian in peta:
        sid = str(bagian.get('section_id') or '').strip()
        judul = str(bagian.get('section_title') or '').strip()
        isi = bagian.get('isi_teks') or ''
        if not sid or not isi:
            continue
        # Penanda awal: judul bagian kalau ada (paling khas), kalau tidak
        # potongan awal isi. `rfind` dari posisi sebelumnya = urutan terjaga.
        pos = -1
        if judul:
            pos = dasar.find(f'{sid} {judul}', cari_dari)
            if pos < 0:
                pos = dasar.find(judul, cari_dari)
        if pos < 0:
            awal_isi = isi.strip()[:60]
            if awal_isi:
                pos = dasar.find(awal_isi, cari_dari)
        if pos < 0:
            pos = cari_dari
        akhir = pos + len(isi)
        if akhir > len(dasar):
            akhir = len(dasar)
        hasil.append({
            'label': sid,
            'nomor': 0,
            'judul': judul,
            'posisi': pos + ofs,
            'akhir': akhir + ofs,
            'isi': teks[pos + ofs:akhir + ofs],
        })
        cari_dari = min(akhir, len(dasar))

    return hasil if len(hasil) > 1 else []


def ambil_bab(teks: str, label: str, judul_bab: str = '') -> tuple[str, str, str]:
    """Ambil isi satu bagian dari teks dokumen.

    Mengembalikan (sebelum, isi_bab, sesudah) — supaya bisa disusun ulang
    tanpa kehilangan bagian lain dokumen.
      - `label` = '__seluruh__'  → seluruh teks dianggap satu bagian
      - `judul_bab` = pembeda kalau ada dua bagian berlabel sama

    🔴 URUTAN PENCARIAN (BUG ke-20, 24Sep26): bagian HALUS ('1.2') dicari
    DULU lewat `_deteksi_bagian()`. Kalau tidak ketemu baru jatuh ke
    `deteksi_bab()` ('BAB I') — jalur LAMA, TIDAK diubah, supaya:
      1. pemakaian lama yang mengirim 'BAB III' tetap jalan persis sama;
      2. kalau peta gagal, perilaku kembali seperti sebelumnya (aman).
    """
    teks = teks or ''
    if not label or label == BAB_SELURUH:
        return '', teks, ''

    for daftar in (_deteksi_bagian(teks), deteksi_bab(teks)):
        for b in daftar:
            if b['label'] != label:
                continue
            if judul_bab and b.get('judul') != judul_bab:
                continue
            return teks[:b['posisi']], b['isi'], teks[b['akhir']:]
    return '', teks, ''          # tidak ketemu → anggap seluruh teks



def susun_ulang(sebelum: str, isi_baru: str, sesudah: str) -> str:
    """Gabungkan kembali sebelum + isi bab baru + sesudah."""
    kiri = sebelum or ''
    kanan = sesudah or ''
    tengah = (isi_baru or '').strip()
    out = kiri + tengah
    if kanan:
        out += ('\n\n' if not kanan.startswith('\n') else '') + kanan
    return out


# ═══════════════════════════════════════════════════════════════════════
#  TIGA JALUR REVISI PER-BAGIAN (rancangan ACC Bos 29Sep26, dikoding 30Sep26)
#   · ambil_pembuka  → JALUR 1: hanya paragraf pembuka BAB (judul → sub-bab 1)
#   · ambil_bab      → JALUR 3: seluruh BAB utuh (sudah ada dari dulu)
#   · ambil_bab ('3.1' ...) → JALUR 2 dipanggil per sub-bab di sisi ai.py
#   · harga_flat     → harga Token FLAT (putusan Bos 30Sep26: "flat menang")
# ═══════════════════════════════════════════════════════════════════════

def ambil_pembuka(teks: str, label_bab: str) -> tuple[str, str, str]:
    """Ambil HANYA paragraf pembuka sebuah BAB besar (JALUR 1).

    Batas: dari judul BAB (`deteksi_bab`) sampai sub-bab PERTAMA di dalam
    rentang bab itu (`_deteksi_bagian`) — sub-bab TIDAK ikut terpotong.

    Kegagalan AMAN (pola persis `ambil_bab`):
      - `label_bab` kosong / `__seluruh__` → seluruh teks
      - bab tidak ditemukan → `('', teks, '')` (seluruh teks, bukan nol)
    Sengaja TIDAK menebak: kalau deteksi gagal, pemanggil yang memutus
    (ai.py memakai nilai ini hanya bila `isi` terisi — lihat `_ambil_lingkup`).
    """
    teks = teks or ''
    if not label_bab or label_bab == BAB_SELURUH:
        return '', teks, ''
    for b in deteksi_bab(teks):
        if b['label'] != label_bab:
            continue
        pos, akhir = b['posisi'], b['akhir']
        batas = akhir
        #  ⭐ BATAS SUB-BAB PERTAMA = PETAKAN (sumber kebenaran versi).
        #  🔴 TERBUKTI 30Sep26 (file78): `_deteksi_bagian` menangkap
        #     'Gambar 3.1 Kerangka Pemikiran' (86143) — sedangkan isi 3.1
        #     asli mulai 84511. Batas lama → pembuka MEMUAT isi sub-bab
        #     → jalur 1 menyentuh sub-bab (cacat). `petakan` memberi
        #     `isi_teks` sub-bab yang benar; posisi absolut dicari dengan
        #     `find` di dalam rentang bab (aman: potongan 1.625 kar unik).
        #  GAGAL AMAN: tetap batas versi lama (perilaku lama persis).
        try:
            from .state import petakan as _petakan, \
                buang_daftar_isi as _buang
            _peta = _petakan(_buang(teks))
            for e in _peta:            #  entri terurut urut dokumen
                if '.' not in str(e.get('section_id') or ''):
                    continue           #  bab besar ≠ sub-bab
                _isi = str(e.get('isi_teks') or '')
                _pos0 = teks.find(_isi, pos, akhir) if _isi else -1
                if pos < _pos0 < akhir:
                    batas = _pos0      #  sub-bab PERTAMA dalam rentang bab
                    break
        except Exception as e:                                # noqa: BLE001
            log.warning('[versi] ambil_pembuka petakan gagal (%s) '
                        '→ batas deteksi lama', e)
        return teks[:pos], teks[pos:batas], teks[batas:]
    return '', teks, ''


def harga_flat(teks: str, label: str, lingkup: str = '') -> int:
    """Harga Token Revisi FLAT untuk Pintu A (putusan Bos 30Sep26 — "flat menang").

    Aturan (rancangan TIGA JALUR §A.3 + keputusan 30Sep26):
      · Jalur 1 (`lingkup='pembuka'`)            → 1
      · Jalur 2 (sub-bab terpilih, dipanggil 1×)  → 1 per sub-bab
      · Jalur 3 (BAB utuh: `label` berlabel besar) → 1 pembuka + 1 per sub-bab
      · label tidak ditemukan / gagal deteksi     → 1 (gagal aman, JANGAN 0:
        harga 0 = revisi gratis yang tak pernah ditagih — itu kebocoran uang)

    Yang TIDAK memakai flat (tetap rumus lama ÷10.000 × pengali):
    Pintu B (`__seluruh__` / tanpa label) dan `pengali > 1` — keputusan itu
    di sisi ai.py (pembaca), fungsi ini murni hitungan struktur.
    """
    teks = teks or ''
    if lingkup == 'pembuka':
        return 1
    if not label or label == BAB_SELURUH:
        return 1
    if '.' in str(label):                 # sub-bab → 1 blok = 1 token
        return 1
    for b in deteksi_bab(teks):           # BAB besar → 1 pembuka + N sub-bab
        if b['label'] == label:
            n = sum(1 for sb in _deteksi_bagian(teks)
                    if b['posisi'] < sb['posisi'] < b['akhir'])
            return 1 + n
    return 1


# ═══════════════════════════════════════════════════════════════════════
#  PENYIMPANAN VERSI (gear 2)
# ═══════════════════════════════════════════════════════════════════════

def versi_terpakai(db: Session, file_id: int, bab: str) -> VersiDokumen | None:
    """Versi yang sedang dipakai untuk (file, bab). None kalau belum ada."""
    return db.scalars(
        select(VersiDokumen)
        .where(VersiDokumen.file_id == file_id,
               VersiDokumen.bab == bab,
               VersiDokumen.terpakai.is_(True))
        .order_by(VersiDokumen.nomor.desc())
    ).first()


def daftar_versi(db: Session, file_id: int, bab: str | None = None,
                 dengan_arsip: bool = False) -> list[VersiDokumen]:
    """Semua versi (file, [bab]) — terbaru dulu.

    ══ C10 (25Sep26) — versi TERARSIP disembunyikan secara bawaan ════════
    Versi tua yang digeser "gear" kini DITANDAI `diarsipkan=True` (bukan
    dihapus) supaya naskah tidak bisa hilang permanen. Bawaan: arsip TIDAK
    ikut — jadi riwayat & tombol mundur berperilaku sama seperti sebelumnya.

    `dengan_arsip=True` dipakai HANYA oleh alat pemulihan/audit.
    """
    q = select(VersiDokumen).where(VersiDokumen.file_id == file_id)
    if bab:
        q = q.where(VersiDokumen.bab == bab)
    if not dengan_arsip:
        q = q.where(VersiDokumen.diarsipkan.is_(False))
    return list(db.scalars(q.order_by(VersiDokumen.bab, VersiDokumen.nomor.desc())).all())


def bisa_mundur(db: Session, file_id: int, bab: str) -> bool:
    """True kalau masih ada versi lama yang bisa dikembalikan."""
    return len(daftar_versi(db, file_id, bab)) > 1


def simpan_versi_per_komentar(
    db: Session,
    user_id: int,
    file_id: int,
    bab: str,
    blok: list[dict],
    komentar: list | None = None,
    model: str = '',
) -> list[VersiDokumen]:
    """Simpan SATU VERSI PER KOMENTAR — inti penyederhanaan 17Sep26 (ACC Bos).

    ═══ KENAPA INI DIBUAT ═══
    Sebelum ini, 1 bab berisi 5 komentar → tersimpan sebagai **1 versi besar**
    (seluruh isi bab ditimpa). Akibatnya mahasiswa yang ingin membatalkan
    HANYA poin ke-2 harus MUNDUR SELURUH BAB — terlalu kasar, dan itulah yang
    membuat Bos bingung: *"Lha kalo yang direvisi lain lain / banyak hal dalam
    1 bab bagaimana?"*

    Bos minta: **"Perbaiki dan buat sederhana saja, jangan tambah rumit."**
    Jadi bentuknya SENGAJA sederhana — satu komentar = satu baris riwayat:
        ✨ K1 · Perbaiki kalimat pembuka        2 menit lalu
        ✨ K2 · Tambah penjelasan di paragraf 3  2 menit lalu
    Klik salah satu → hanya perbaikan ITU yang dibatalkan.

    ═══ CARA KERJA (tanpa mesin diff — sengaja sederhana) ═══
    `blok` = daftar {nomor, ringkas, isi} hasil urai jawaban AI per komentar
    (sudah diurai oleh `_pisah_blok_komentar()` di ai.py). Tiap komentar
    disimpan sebagai baris `versi_dokumen` tersendiri dengan `nomor` yang
    berbeda, sehingga riwayat & tombol mundur bekerja per komentar.

    Kuota TIDAK dihitung di sini — pemotongan tetap memakai mekanisme lama
    (÷10.000 + pengali + cap), persis seperti perintah Bos: *"mekanisme
    pemotongan kuota revisi sudah ada"*.
    """
    bab = bab or BAB_SELURUH
    komentar = komentar or []
    tersimpan: list[VersiDokumen] = []

    # ══ C10 (25Sep26) — PAGAR PINTU MASUK: JANGAN matikan versi lama dulu ══
    #  🚨 BUG NYATA (temuan saat uji C7, DB produksi file 47):
    #      v60 & v61 tersimpan **0 karakter** dan v61 `terpakai=1` →
    #      NASKAH MAHASISWA KOSONG.
    #
    #  RANTAI LAMA (salah urutan):
    #      baris 369-370  semua versi lama dimatikan (`v.terpakai = False`)
    #      baris 372-375  blok KOSONG dilewati (`if not isi: continue`)
    #      baris 401-402  `if not tersimpan: return []`
    #      ⇒ kalau SEMUA blok kosong: tidak ada versi baru, TAPI versi lama
    #        sudah terlanjur dimatikan, dan TIDAK ADA yang mengembalikannya.
    #
    #  PERBAIKAN: periksa dulu — kalau TIDAK ADA satu pun isi yang layak,
    #  KEMBALIKAN `[]` **SEBELUM** menyentuh versi lama sama sekali.
    layak = [b for b in (blok or []) if (b.get('isi') or '').strip()]
    if not layak:
        log.warning('[versi] DITOLAK: tidak ada isi layak (file=%s bab=%s) — '
                    'versi lama TIDAK disentuh', file_id, bab)
        return []

    #  Nomor lanjut dari versi terakhir bab ini (biar riwayat tetap berurutan).
    lama = daftar_versi(db, file_id, bab)          # terbaru dulu
    nomor = (lama[0].nomor + 1) if lama else 1
    for v in lama:
        v.terpakai = False

    for b in blok:
        isi = (b.get('isi') or '').strip()
        if not isi:
            continue
        #  Ringkasan untuk judul baris riwayat: pakai kalimat komentar asli
        #  bila ada (lebih dikenal mahasiswa), kalau tidak pakai ringkas AI.
        try:
            kn = int(b.get('nomor') or 0)
        except (TypeError, ValueError):
            kn = 0
        judul = ''
        if 1 <= kn <= len(komentar):
            judul = str(komentar[kn - 1]).strip()
        if not judul:
            judul = (b.get('ringkas') or '').strip()
        if len(judul) > 80:
            judul = judul[:77].rstrip() + '…'

        baru = VersiDokumen(
            user_id=user_id, file_id=file_id, bab=bab, nomor=nomor,
            isi=isi,
            komentar=(f'K{kn} · {judul}' if kn else judul) or 'Perbaikan EduAi',
            model=model or '', terpakai=True, dibuat=_now(),
            ukuran=len(isi.encode('utf-8')),
        )
        db.add(baru)
        tersimpan.append(baru)
        nomor += 1

    if not tersimpan:
        return []

    db.flush()

    # ── gear: sisakan VERSI_SIMPAN versi TERAKHIR per bab ──
    #  ⚠️🔴 JEBAKAN BESAR YANG DITUTUP (17Sep26, ketemu saat uji pertama):
    #  Aturan gear VERSI_SIMPAN (=2, ACC Bos 14Sep26) dibuat untuk riwayat
    #  PER BAB — 1 perbaikan = 1 baris. Begitu satuannya berubah jadi
    #  PER KOMENTAR, aturan lama itu MEMBUANG KOMENTAR PERTAMA begitu
    #  mahasiswa mengirim 3 komentar (3 baris > 2) — hasil revisi HILANG
    #  dari riwayat. Uji nyata: 3 komentar → hanya 2 tersisa (K1 lenyap).
    #
    #  Karena Bos minta "revisi SESUAI YANG DIKOMENTARI SAJA", setiap komentar
    #  WAJIB punya barisnya sendiri. Jadi:
    #    · penjaga ukuran tetap berlaku, tapi dihitung per PUTARAN (proses),
    #      bukan per baris — satu putaran = satu set komentar, tidak dipotong;
    #    · yang dibuang hanya set SETELAHNYA (versi lebih tua), seperti gear.
    #
    #  ══ C10 (25Sep26) — JANGAN HAPUS, CUKUP DIARSIPKAN ═══════════════════
    #  🚨 BUG NYATA (temuan uji C7): gear memakai `db.delete()` → versi lama
    #  yang BERISI hilang PERMANEN dari DB. Bukti: v57 (4.522 kar) LENYAP
    #  setelah 2 putaran revisi kosong, sehingga TIDAK ADA lagi versi berisi
    #  untuk dipulihkan.
    #
    #  SEKARANG: versi tua **diarsipkan** (`diarsipkan=True`) — hilang dari
    #  daftar aktif & tombol mundur, TAPI datanya TETAP ADA untuk pemulihan.
    #  Mahasiswa tidak bisa kehilangan naskah lagi.
    semua = daftar_versi(db, file_id, bab)          # terbaru dulu
    #  Kelompokkan per PUTARAN memakai waktu dibuat (detik yang sama = 1 set).
    kunci_set: list[object] = []
    for v in semua:
        k = v.dibuat.replace(microsecond=0) if v.dibuat else None
        if k not in kunci_set:
            kunci_set.append(k)
    diarsipkan_kini = 0
    for k in kunci_set[VERSI_SIMPAN:]:              # sisakan 2 PUTARAN terakhir
        for v in [x for x in semua if (x.dibuat.replace(microsecond=0)
                                       if x.dibuat else None) == k]:
            if not getattr(v, 'diarsipkan', False):
                v.diarsipkan = True                 # ARSIP, bukan HAPUS (C10)
                diarsipkan_kini += 1
    db.commit()
    if diarsipkan_kini:
        log.info('[versi] %d versi tua DIARSIPKAN (bukan dihapus) — file=%s bab=%s',
                 diarsipkan_kini, file_id, bab)
    log.info('[versi] simpan %d versi per-komentar (file=%s bab=%s)',
             len(tersimpan), file_id, bab)
    return tersimpan


def simpan_versi(
    db: Session,
    user_id: int,
    file_id: int,
    bab: str,
    isi: str,
    komentar: list | None = None,
    model: str = '',
) -> VersiDokumen:
    """Simpan hasil revisi sebagai VERSI BARU (tidak menimpa apa pun).

    Aturan gear (ACC Bos): simpan maksimal VERSI_SIMPAN versi lama per
    (file, bab); kelebihannya dibuang dari yang TERTUA.
    """
    bab = bab or BAB_SELURUH
    #  🚨 C10 (25Sep26) — PINTU MASUK: tolak isi KOSONG.
    #  Temuan uji C7: `isi=''` ikut tersimpan sebagai versi baru & langsung
    #  `terpakai=True` → NASKAH MAHASISWA KOSONG. Versi lama JANGAN disentuh.
    if not (isi or '').strip():
        log.warning('[versi] simpan_versi DITOLAK: isi kosong (file=%s bab=%s)',
                    file_id, bab)
        return None

    lama = daftar_versi(db, file_id, bab)          # terbaru dulu
    nomor = (lama[0].nomor + 1) if lama else 1

    # semua versi lama → tidak terpakai lagi
    for v in lama:
        v.terpakai = False

    baru = VersiDokumen(
        user_id=user_id, file_id=file_id, bab=bab, nomor=nomor,
        isi=isi or '',
        komentar='\n'.join(komentar or []),
        model=model or '', terpakai=True, dibuat=_now(),
        # Ukuran versi DIHITUNG KE KUOTA STORAGE (ACC Bos 15Sep26).
        # Backup/riwayat ikut menghabiskan kuota → user terdorong menambah
        # storage. Versi lama bernilai 0 (gratis) ditangani di migrasi.
        ukuran=len((isi or '').encode('utf-8')),
    )
    db.add(baru)
    db.flush()

    # ── gear: sisakan VERSI_SIMPAN versi SEBELUM yang terbaru ──
    #  ══ C10 (25Sep26) — ARSIPKAN, JANGAN HAPUS ═════════════════════════
    #  Dulu `db.delete()` → versi berisi HILANG PERMANEN (bukti: v57 4.522 kar
    #  lenyap). Kini cukup ditandai `diarsipkan=True`.
    semua = daftar_versi(db, file_id, bab)         # termasuk yang baru
    harus_buang = semua[VERSI_SIMPAN + 1:]         # +1 = versi terpakai
    n_arsip = 0
    for v in harus_buang:
        if not getattr(v, 'diarsipkan', False):
            v.diarsipkan = True
            n_arsip += 1
    if n_arsip:
        log.info('[versi] %d versi lama DIARSIPKAN (file=%s bab=%s)',
                 n_arsip, file_id, bab)

    db.commit()
    db.refresh(baru)
    return baru


# ═══════════════════════════════════════════════════════════════════════
#  PENDAMPING PIPA — bentuk mentah KUTIP/GANTI (Opsi D, 29Sep26, ACC Bos
#  "D1 + (a)"). Tabel BARU `versi_pipa`; `versi_dokumen` TIDAK disentuh.
# ═══════════════════════════════════════════════════════════════════════

def simpan_pipa(db: Session, versi_ids: list[int], file_id: int,
                teks: str) -> int:
    """Simpan bentuk mentah pendamping untuk SETIAP baris versi.

    Kembalikan jumlah baris BARU yang ditulis.

    ⚠️ GAGAL DI SINI BUKAN GAGAL REVISI — pemanggil wajib menangkap dan
    mencatat dengan `log.exception` (pintu terapkan akan jujur menolak /
    jalur Salin hasil tetap tersedia). Versi & ingatan dokumen tetap utuh.
    """
    if not (teks or '').strip() or not versi_ids:
        return 0
    baru = 0
    for vid in versi_ids:
        if not vid:
            continue
        lama = db.scalars(
            select(VersiPipa).where(VersiPipa.versi_id == vid)).first()
        if lama is not None:
            lama.teks = teks
            lama.file_id = file_id
            continue
        db.add(VersiPipa(versi_id=int(vid), file_id=file_id, teks=teks,
                         dibuat=_now()))
        baru += 1
    db.commit()
    return baru


def ambil_pipa(db: Session, versi_id: int | None) -> str:
    """Bentuk mentah pendamping satu baris versi. '' kalau tidak ada.

    Versi LAMA (sebelum Opsi D) tidak punya pendamping → '' → pintu
    terapkan memakai jalur lama (pagar Opsi A yang menolak jujur).
    """
    if not versi_id:
        return ''
    try:
        r = db.scalars(select(VersiPipa).where(
            VersiPipa.versi_id == versi_id)).first()
        return (r.teks or '') if r is not None else ''
    except Exception as e:                                   # noqa: BLE001
        log.warning('[versi] ambil_pipa gagal (versi=%s): %s', versi_id, e)
        return ''


def mundurkan(db: Session, file_id: int, bab: str) -> VersiDokumen | None:
    """Kembalikan ke versi SEBELUMNYA (rollback 1 langkah).

    Mengembalikan versi yang kini terpakai, atau None kalau tidak ada
    versi sebelumnya (sudah paling lama).
    """
    semua = daftar_versi(db, file_id, bab)         # terbaru dulu
    if len(semua) < 2:
        return None
    kini = next((v for v in semua if v.terpakai), semua[0])
    idx = semua.index(kini)
    if idx + 1 >= len(semua):
        return None                                 # sudah di versi tertua
    tujuan = semua[idx + 1]
    kini.terpakai = False
    tujuan.terpakai = True
    db.commit()
    db.refresh(tujuan)
    return tujuan


def mundur_ke(db: Session, file_id: int, bab: str, nomor: int) -> VersiDokumen | None:
    """Kembalikan dokumen ke TITIK RIWAYAT tertentu (ACC Bos 14Sep26).

    Riwayat ditampilkan bahasa waktu ("5 menit lalu · ✨ AI"), tapi di belakang
    tetap ada `nomor`. UI mengirim titik yang diklik user.

    Aturan penting:
      - Tidak boleh "maju" ke versi yang lebih baru dari yang sekarang.
      - Titik yang ditinggalkan TIDAK dihapus (bisa naik lagi kapan pun).
      - Mengembalikan versi tujuan, atau None kalau titiknya tidak ada.
    """
    semua = daftar_versi(db, file_id, bab)         # terbaru dulu
    if not semua:
        return None
    tujuan = next((v for v in semua if v.nomor == nomor), None)
    if tujuan is None or tujuan.terpakai:
        return None                                 # tidak ada / sudah aktif

    # tidak boleh maju: nomor tujuan harus LEBIH KECIL dari yang sekarang
    kini = next((v for v in semua if v.terpakai), semua[0])
    if tujuan.nomor >= kini.nomor:
        return None

    kini.terpakai = False
    tujuan.terpakai = True
    db.commit()
    db.refresh(tujuan)
    return tujuan


def hapus_versi_file(db: Session, file_id: int) -> int:
    """Hapus semua versi milik sebuah berkas (dipakai saat berkas dihapus).

    C10 (25Sep26): WAJIB menyertakan yang DIARSIPKAN (`dengan_arsip=True`) —
    kalau tidak, versi arsip menjadi yatim (berkasnya hilang, barisnya tinggal)
    dan menumpuk selamanya di DB.
    """
    semua = daftar_versi(db, file_id, dengan_arsip=True)
    #  ⚠️ Pendamping pipa (tabel `versi_pipa`) ikut dibersihkan — kalau
    #     dibiarkan, barisnya jadi yatim (versinya sudah dihapus).
    try:
        for v in semua:
            db.query(VersiPipa).filter(
                VersiPipa.versi_id == v.id).delete(synchronize_session=False)
    except Exception as e:                                   # noqa: BLE001
        log.warning('[versi] hapus pendamping pipa gagal: %s', e)
    for v in semua:
        db.delete(v)
    if semua:
        db.commit()
    return len(semua)
