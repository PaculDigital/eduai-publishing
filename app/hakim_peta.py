"""HAKIM v2 — AUDIT STRUKTURAL DETERMINISTIK + JEV HANYA PERTANYAAN SEMPIT.

═══════════════════════════════════════════════════════════════════════════
BENTUK BARU (putusan Bos 10 Okt 2026 — K5 DIHAPUS, jangan pasang kembali):
  · KODE melakukan audit struktural deterministik (nomor loncat, subbab
    yatim tanpa BAB induk, judul >300 karakter, judul berawalan huruf kecil,
    fragmen tabel/SPSS) ⇒ mengeluarkan sepakat/curiga + alasan.
  · Jev HANYA menjawab pertanyaan sempit yang kode tidak bisa putuskan
    (satu pertanyaan generik TANPA criteria, tanpa ambang yang disetel
    per naskah) ⇒ hasilnya hanya bisa jadi 'ragu' atau 'sepakat'.
  · Manusia memeriksa yang 'curiga'. Hakim TIDAK PERNAH memblokir atau
    mengubah label (pagar H1).

KENAPA K5 MATI (jangan dihidupkan lagi):
  K5 = kalimat criteria yang disetel PER KASUS. Terbukti tidak bisa
  menyeberang naskah (12/12 set latih → ~10/16 set uji segar; '3. Tinjauan
  Literatur' 0,63 di Asih tapi 0,12 di fid=115). Vonis Bos 14 Okt: "K5 itu
  terlalu detail hanya cocok untuk 1 naskah saja, tidak bisa dipakai untuk
  global. Karena app EduAi ini akan menerima ribuan naskah nantinya."
  Teks criteria K5 SUDAH DIHAPUS dari berkas ini (riwayat ada di git).

ATURAN VONIS (tanpa ambang yang disetel per naskah):
  · 'curiga'  ← SATU saja aturan deterministik kena (alasan tercatat).
  · 'ragu'    ← kode tidak menemukan apa pun, TAPI Jev (pertanyaan sempit)
                menjawab noul < 0,5. 0,5 = titik tengah netral skala 0..1
                (Jev sendiri tidak yakin), BUKAN ambang yang disetel.
  · 'sepakat' ← kode bersih dan (tidak perlu tanya Jev, atau Jev ≥ 0,5).
  · 'belum'   ← Jev mati / tidak ditanya karena di luar batas (jujur).
  `p` surveyor HANYA info tampilan, tidak pernah jadi input keputusan.

PAGAR (WAJIB, tidak boleh dilanggar):
  P1  Hakim mati / galat ⇒ kembalikan laporan KOSONG, mesin TETAP jalan.
  P2  Jangan melempar galat keluar.
  P3  JANGAN memutuskan label — hakim hanya melaporkan status per bagian.
  P4  Jumlah bagian TIDAK berkurang.
  P5  `p` hanya dicatat sebagai `p_info`, TIDAK dipakai memfilter/memutuskan.
  P6  JANGAN menyentuh `app/satpam.py` (dipakai jalur biaya) — modul ini TERPISAH.
  P7  Kill-switch: env EDUAI_HAKIM_AKTIF=0 ⇒ hakim mati (laporan 'mati').

PEMASANGAN PRODUKSI (10 Nov 2026):
  `app/ai.py::peta_mulai` memanggil `periksa_peta()` sesudah surveyor dan
  menempel ringkasannya di balasan ('hakim') — log saja, tidak mengubah
  label atau bentuk balasan lama. `app/versi.py::_deteksi_bagian` memanggil
  yang sama untuk log. Matikan kapan saja: EDUAI_HAKIM_AKTIF=0.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, '/app')

log = logging.getLogger('hakim_peta')

# ── setelan: MEMINJAM setelan satpam — jangan bikin setelan baru.
#  v8 (10 Nov 2026): pinjaman BASE/KUNCI/MODEL/BATAS_DETIK DIHAPUS — tidak
#  pernah dibaca (Hakim bertanya lewat `jev.tanya()`, model ikut
#  `jev.MODEL_DEFAULT`). Yang dipinjam hanya AKTIF (kill-switch).
try:
    from . import satpam as _satpam
    _AKTIF = bool(getattr(_satpam, 'AKTIF', False))
except Exception:                                     # P2: telan
    _AKTIF = False

#  Label judul yang diperiksa hakim (paragraf/biasa BUKAN tugas hakim)
LABEL_JUDUL = ('bab', 'subbab')

#  Frekuensi panggilan: SATU panggilan untuk sekumpulan kandidat (hemat).
MAKS_TANYA = 24          # kandidat per panggilan (batas aman teruji 156; ini hemat)
MAKS_TANYA_TOTAL = 48    # batas pertanyaan sempit per peta — selebihnya 'belum'

#  Ambang 'ragu' skala noul 0..1 (dokumen RESMI TypeSafe, halaman Noul):
#  "A good starting point is 0.7 for yes and 0.3 for no. ... Values
#  between 0.3 and 0.7 can go to a person rather than either code path."
#  Dulu 0,5 (titik tengah netral) — akibatnya noul 0,5–0,7 yang menurut
#  dokumen resmi masih pita tengah (layak diperiksa manusia) sudah
#  dibaca 'sepakat'. Sekarang < 0,7 ⇒ 'ragu' (masuk antrean manusia),
#  ≥ 0,7 ⇒ 'sepakat'. Hakim tetap LOG SAJA, tidak memblokir — perubahan
#  ini hanya menambah bendera ragu, bukan vonis baru.
AMBANG_RAGU = 0.7

#  ── daftar TERTUTUP header output SPSS (salinan daftar di peta3_jev.py —
#     ubah keduanya bila daftar berubah; hanya exact-match, huruf kecil).
_SPSS_HEADER = {
    'reliability statistics', 'item-total statistics', 'item statistics',
    'scale statistics', 'summary item statistics', 'descriptive statistics',
    'correlations', 'model summary', 'anova', 'coefficients',
    'variables entered/removed', 'case processing summary',
    'total variance explained', 'component matrix', 'rotated component matrix',
}

_ROMAWI = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
           'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}
_POLA_BAB = re.compile(r'^BAB\s+([IVX0-9]+)\b', re.I)
_POLA_NOMOR = re.compile(r'^(\d+(?:\.\d+)*)\.?\s')

# ── kupas nomor halaman ("13 BAB I" -> "BAB I"), dipakai saat MENCARI pola.
try:
    from .sambung_kode import tanpa_nomor_halaman as _tanpa_no
except Exception:                                     # noqa: BLE001
    def _tanpa_no(s):
        return re.sub(r'^\d{1,3}\s+', '', (s or '').strip(), count=1)
_POLA_SPSS_KATA = re.compile(
    r'\b(Coefficients|Cronbach|Sum of Squares|Mean Square|Sig\.|Std\. Error|'
    r'Reliability Statistics|Model Summary|ANOVA|Descriptive Statistics|'
    r'Correlations)\b', re.I)

#  Titik injeksi untuk uji offline (HANYA dipakai tes — produksi None).
_TANYA_FN = None
_JUDUL_CURIGA_FN = None


def aktif() -> bool:
    """Kill-switch hakim: env EDUAI_HAKIM_AKTIF=0 ⇒ mati. Bawaan hidup."""
    return (os.getenv('EDUAI_HAKIM_AKTIF') or '1') != '0'


def _q_per_kandidat(blok: list[dict]) -> dict:
    """Pertanyaan SEMPIT, generik, TANPA criteria (K5 mati).

    Satu pertanyaan per kandidat (nama = L%06d). Jev menilai barisnya
    LANGSUNG — tidak ada kalimat criteria yang disetel per naskah.
    """
    q = {}
    for k in blok:
        q[f"L{k['i']:06d}"] = {
            'type': 'noul',
            'instructions': (f"Apakah baris TENGAH untuk {k['i']:06d} di atas "
                             'benar-benar KEPALA BAGIAN (judul) naskah?'),
        }
    return q


def _kandidat_judul(peta_surveyor: dict) -> list[dict]:
    """Ambil kandidat berlabel judul dari peta surveyor (TANPA mengubah label)."""
    baris = peta_surveyor.get('baris') or []
    label = peta_surveyor.get('label') or {}
    gabung = peta_surveyor.get('gabung') or {}
    p = peta_surveyor.get('p') or {}
    sist = set(peta_surveyor.get('sistematika') or [])

    out = []
    for i, lab in sorted(label.items()):
        if lab not in LABEL_JUDUL or i in sist or i >= len(baris):
            continue
        out.append({
            'i': int(i),
            'label': lab,
            'teks': ' '.join(str(baris[i]).split()),
            'induk': gabung.get(i) or gabung.get(min(gabung, key=lambda k: abs(k - i))) if gabung else None,
            'p_info': p.get(i),                    # ⚠️ hanya INFO, bukan input keputusan
        })
    return out


def _bahan_kandidat(kand: list[dict], baris: list[str]) -> str:
    """JENDELA 3 BARIS ber-ID (cara terbukti: peta halus v10, 4/4 nol salah)."""
    bagian = []
    for k in kand:
        i = k['i']
        atas = ' '.join(str(baris[i - 1]).split())[:70] if i > 0 else '(awal naskah)'
        tengah = ' '.join(str(baris[i]).split())[:90]
        bawah = ' '.join(str(baris[i + 1]).split())[:70] if i + 1 < len(baris) else '(akhir naskah)'
        bagian.append(
            f'BARIS L{i:06d} (label surveyor: {k["label"]})\n'
            f'   atas   : {atas}\n'
            f'   TENGAH : {tengah}\n'
            f'   bawah  : {bawah}'
        )
    return '\n'.join(bagian)


def _tanya_jev(bahan: str, pertanyaan: dict) -> dict | None:
    """Tanya Jev lewat jalan tol. TIDAK PERNAH melempar galat — gagal ⇒ None."""
    if _TANYA_FN is not None:                    # injeksi uji offline
        try:
            return _TANYA_FN(bahan, pertanyaan)
        except Exception as e:                     # P1/P2
            log.warning('[hakim_peta] tanya injeksi gagal: %s: %s',
                        type(e).__name__, e)
            return None
    if not _AKTIF:
        return None
    try:
        from . import jev as _jev
        return _jev.tanya(bahan, pertanyaan)
    except Exception as e:                             # P1/P2
        log.warning('[hakim_peta] jalan tol Jev gagal: %s: %s', type(e).__name__, e)
        return None


def _judul_curiga_kode(baris: list[str]) -> dict[int, list[str]]:
    """Sinyal curiga dari `pola_penulisan.judul_curiga` (2 sinyal PASTI:
    awal-sitasi, butir-bertanya). Kembalikan {i: [alasan]}."""
    fn = _JUDUL_CURIGA_FN
    if fn is None:
        try:
            from .pola_penulisan import judul_curiga as fn
        except Exception as e:                         # P2
            log.warning('[hakim_peta] judul_curiga gagal: %s', e)
            return {}
    try:
        hasil = fn([(i, baris[i]) for i in range(len(baris))]) or []
    except Exception as e:                             # P2
        log.warning('[hakim_peta] judul_curiga gagal: %s', e)
        return {}
    keluar: dict[int, list[str]] = {}
    for c in hasil:
        try:
            keluar.setdefault(int(c.get('i')), []).extend(c.get('alasan') or [])
        except Exception:
            continue
    return keluar


def _huruf_awal_kecil(s):
    """True bila HURUF pertama judul huruf kecil (awalan nomor dikupas dulu:
    '1.1 latar belakang' = huruf kecil. Salinan helper di peta3_jev.py —
    hakim tidak boleh mengimpor skrip root)."""
    t = re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', (s or '').strip())
    return bool(t) and t[:1].islower()


def _audit_struktural(peta_surveyor: dict, kand: list[dict]) -> dict[int, list[str]]:
    """AUDIT STRUKTURAL DETERMINISTIK (kode saja, nol goyang).

    Aturan (putusan Bos 10 Okt 2026):
      · nomor-loncat      — urutan bernomor melompat (1.1 → 1.3, BAB II → BAB IV),
                            HANYA bila nomor yang dilewati tidak ada di mana
                            pun dalam teks naskah (v4, 10 Nov 2026)
      · subbab-yatim      — subbab tanpa BAB induk; HANYA bila naskah tidak
                            punya BAB sama sekali — subbab sebelum BAB pertama
                            adalah pendahuluan, bukan yatim (v4, 10 Nov 2026)
      · judul-panjang     — judul >300 karakter (ambang dari profil kampus)
      · judul-huruf-kecil — judul diawali huruf kecil
      · fragmen-tabel     — judul berisi pipa tabel / header SPSS
      · bab-ganda         — nomor BAB yang sama muncul dua kali
    Kembalikan {i: [alasan, ...]}. Kosong = kode tidak menemukan apa pun.
    """
    try:
        from .profil_kampus import aturan as _aturan
        maks_kar = int((_aturan() or {}).get('judul_maks_kar') or 300)
    except Exception:
        maks_kar = 300
    baris = peta_surveyor.get('baris') or []
    gabung = peta_surveyor.get('gabung') or {}
    temuan: dict[int, list[str]] = {}

    def _tambah(i, alasan):
        temuan.setdefault(int(i), []).append(alasan)

    # ── NOMOR YANG MUNCUL DI TEKS (v4, 10 Nov 2026) ─────────────────────
    #    Loncatan HANYA ditandai bila nomor yang dilewati TIDAK ADA di mana
    #    pun dalam naskah. Terukur live: "4.3.3 Reduksi Data" dan "3.3 Metode
    #    Pengumpulan Data" ditandai nomor-loncat padahal judul asli — nomor
    #    yang dilewati muncul di bagian lain naskah (daftar isi / rujukan).
    nomor_di_teks: set[str] = set()
    bab_di_teks: set[str] = set()
    for _bt in baris:
        _tt = _tanpa_no(' '.join(str(_bt).split()))
        nomor_di_teks.update(re.findall(r'\b(\d+(?:\.\d+)+)\b', _tt))
        # rujukan BAB bisa di tengah kalimat ("seperti pada BAB II") —
        # cari di mana pun, bukan hanya awal baris.
        bab_di_teks.update(m.upper()
                           for m in re.findall(r'\bBAB\s+([IVX0-9]+)\b', _tt, re.I))

    # ── ZONA PENDAHULUAN (v4, 10 Nov 2026) ──────────────────────────────
    #    Subbab SEBELUM BAB pertama adalah pendahuluan (PERSETUJUAN
    #    PEMBIMBING, MOTTO, ...) — terukur WULAN-1: 15 curiga, kebanyakan
    #    subbab-yatim dari pendahuluan. Bila naskah MEMANG tidak punya BAB
    #    sama sekali, tetap ditandai (uji offline: fixture tanpa bab).
    ada_bab_sama_sekali = bool(gabung) or any(
        k.get('label') == 'bab'
        or _POLA_BAB.match(_tanpa_no(k.get('teks') or ''))
        for k in kand)

    # ── urutan nomor + BAB ganda + subbab yatim ──────────────────────────
    bab_angka_terakhir = None
    bab_nomor: dict[str, int] = {}
    nomor_induk: dict[str, int] = {}     # induk -> nomor anak terakhir
    for k in kand:
        i, teks = k['i'], k['teks']
        m_bab = _POLA_BAB.match(_tanpa_no(teks))
        if k['label'] == 'bab' or m_bab:
            if m_bab:
                nomor = m_bab.group(1).upper()
                if nomor in bab_nomor:
                    _tambah(i, 'bab-ganda')
                bab_nomor[nomor] = i
                if nomor in _ROMAWI:
                    angka = _ROMAWI[nomor]
                    if bab_angka_terakhir is not None and angka > bab_angka_terakhir + 1:
                        _loncat = [r for r, a in _ROMAWI.items()
                                   if bab_angka_terakhir < a < angka]
                        if not any(r in bab_di_teks for r in _loncat):
                            _tambah(i, 'nomor-loncat')
                    bab_angka_terakhir = angka
            continue
        # subbab bernomor: cek induk + loncatan
        m = _POLA_NOMOR.match(_tanpa_no(teks))
        if m:
            nomor = m.group(1)
            bagian = nomor.split('.')
            if len(bagian) >= 2:
                induk = '.'.join(bagian[:-1])
                anak = int(bagian[-1])
                if induk in nomor_induk and anak > nomor_induk[induk] + 1:
                    _loncat = [f'{induk}.{n}'
                               for n in range(nomor_induk[induk] + 1, anak)]
                    if not any(n in nomor_di_teks for n in _loncat):
                        _tambah(i, 'nomor-loncat')
                nomor_induk[induk] = max(nomor_induk.get(induk, 0), anak)
        if not ada_bab_sama_sekali:
            _tambah(i, 'subbab-yatim')

    # ── bentuk judul (per kandidat) ──────────────────────────────────────
    for k in kand:
        i, teks = k['i'], k['teks']
        if len(teks) > maks_kar:
            _tambah(i, 'judul-panjang')
        if _huruf_awal_kecil(teks):
            _tambah(i, 'judul-huruf-kecil')
        if '|' in teks or _POLA_SPSS_KATA.search(teks) \
                or teks.strip().lower() in _SPSS_HEADER:
            _tambah(i, 'fragmen-tabel')
    # ── sinyal judul_curiga (2 sinyal PASTI) ─────────────────────────────
    for i, alasan in _judul_curiga_kode(baris).items():
        if any(k['i'] == i for k in kand):
            for a in alasan:
                _tambah(i, a)
    return temuan


def _butuh_tanya_jev(k: dict) -> bool:
    """Kode tidak bisa putuskan? Hanya judul yang mirip kalimat: diakhiri
    titik (kalimat selesai) atau panjang 120-300 kar. Yang lain cukup kode."""
    teks = k.get('teks') or ''
    return teks.endswith('.') or 120 < len(teks) <= 300


def tandai_ragu_curiga(peta_surveyor: dict) -> set:
    """GATING RANTAI v13 (Gas Bos 11 Nov 2026) — himpunan idx baris yang
    Hakim tandai 'ragu'/'curiga' pada peta ini.

    Dipakai Lapis 2 sebagai gerbang: agen kedua HANYA dipanggil untuk
    baris di himpunan ini (bukan per baris goyang). TIDAK PERNAH melempar:
    hakim mati / galat / tanpa kandidat ⇒ himpunan kosong (Lapis 2 tidak
    memanggil agen kedua sama sekali — gagal tertutup, bukan tebak).
    """
    try:
        hasil = periksa_peta(peta_surveyor)
    except Exception as e:                                  # P1: telan
        log.warning('[hakim_peta] tandai gagal: %s: %s',
                    type(e).__name__, e)
        return set()
    if not isinstance(hasil, dict) or not hasil.get('ok'):
        return set()
    return {int(b['i']) for b in (hasil.get('bagian') or [])
            if b.get('status') in ('ragu', 'curiga')}


def periksa_peta(peta_surveyor: dict) -> dict:
    """Hakim v2 — audit peta surveyor. SELALU mengembalikan dict (P1).

    Keluaran:
      {'ok', 'keputusan', 'bagian':[{i,label,judul,p_info,status,alasan}],
       'jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'jumlah_belum',
       'alasan'}
    'keputusan' selalu 'lolos' — hakim LAPOR, jangan BLOKIR (pagar H1).
    """
    kosong = {'ok': False, 'keputusan': 'mati', 'bagian': [],
              'jumlah_sepakat': 0, 'jumlah_ragu': 0, 'jumlah_curiga': 0,
              'jumlah_belum': 0, 'alasan': 'tidak bisa diperiksa'}
    if not aktif():
        return {**kosong, 'alasan': 'hakim dimatikan (EDUAI_HAKIM_AKTIF=0)'}
    if not isinstance(peta_surveyor, dict):
        return kosong

    baris = peta_surveyor.get('baris') or []
    kand = _kandidat_judul(peta_surveyor)

    #  🚨 PAGAR DEGRADASI SENYAP (terukur 09 Okt 2026):
    #     `peta3_jev.petakan()` TIDAK melaporkan kegagalan Jev — kalau Jev kena
    #     503, SEMUA baris dilabeli 'biasa' dan `gagal=0`.
    #     ⇒ Wajib DIBEDAKAN: "peta memang tanpa judul" vs "surveyor gagal".
    _label = peta_surveyor.get('label') or {}
    if not kand:
        _ada_judul = any(v in LABEL_JUDUL for v in _label.values())
        if _label and not _ada_judul:
            return {**kosong,
                    'alasan': ('surveyor DEGRADASI: %d baris semuanya berlabel '
                               "'biasa' — Jev kemungkinan gagal (503). JANGAN "
                               'anggap peta tanpa judul.' % len(_label)),
                    'degradasi': True}
        return {**kosong, 'alasan': 'tidak ada kandidat judul'}

    # ── SUMBER-1: curiga = audit struktural deterministik (kode) ─────────
    curiga_kode = _audit_struktural(peta_surveyor, kand)

    # ── SUMBER-2: ragu = vonis Jev atas pertanyaan SEMPIT ────────────────
    #    Hanya untuk judul yang kode tidak bisa putuskan (mirip kalimat),
    #    maksimal MAKS_TANYA_TOTAL pertanyaan per peta (hemat).
    perlu = [k for k in kand if k['i'] not in curiga_kode and _butuh_tanya_jev(k)]
    perlu = perlu[:MAKS_TANYA_TOTAL]
    vonis: dict[int, str] = {}
    for mulai in range(0, len(perlu), MAKS_TANYA):
        blok = perlu[mulai:mulai + MAKS_TANYA]
        bahan = _bahan_kandidat(blok, baris)
        jalan = _tanya_jev(bahan, _q_per_kandidat(blok))
        if jalan is None:
            continue                                   # P1: lewati, jangan hentikan
        for k in blok:
            jaw = (jalan.get(f"L{k['i']:06d}") or jalan.get(str(k['i']))
                   or jalan.get(f'baris_{k["i"]}'))
            if isinstance(jaw, dict):
                noul = jaw.get('noul')
                if noul is not None:
                    try:
                        vonis[k['i']] = ('ragu' if float(noul) < AMBANG_RAGU
                                         else 'sepakat')
                    except (TypeError, ValueError):
                        pass

    # ── RAKIT laporan (P4: jumlah bagian TIDAK berkurang) ────────────────
    bagian = []
    for k in kand:
        alasan = list(curiga_kode.get(k['i']) or [])
        if alasan:
            status = 'curiga'
        elif k['i'] in vonis:
            status = vonis[k['i']]         # 'sepakat' | 'ragu'
            if status == 'ragu':
                alasan = ['jev-ragu']
        else:
            status = 'belum' if _butuh_tanya_jev(k) else 'sepakat'
        bagian.append({
            'i': k['i'], 'label': k['label'], 'judul': k['teks'][:60],
            'p_info': k['p_info'],                     # P5: info saja
            'status': status, 'alasan': alasan,
        })
        if status == 'curiga':
            log.warning('[hakim_peta] curiga L%06d (%s): %s',
                        k['i'], k['teks'][:60], ', '.join(alasan))

    n_sep = sum(1 for b in bagian if b['status'] == 'sepakat')
    n_rag = sum(1 for b in bagian if b['status'] == 'ragu')
    n_cur = sum(1 for b in bagian if b['status'] == 'curiga')
    n_bel = sum(1 for b in bagian if b['status'] == 'belum')
    return {
        'ok': True,
        'keputusan': 'lolos',                          # H1: TIDAK memblokir
        'bagian': bagian,
        'jumlah_sepakat': n_sep,
        'jumlah_ragu': n_rag,
        'jumlah_curiga': n_cur,
        'jumlah_belum': n_bel,
        'alasan': (f'{len(bagian)} kandidat judul: {n_sep} sepakat · '
                   f'{n_rag} ragu · {n_cur} curiga · {n_bel} belum'),
    }
