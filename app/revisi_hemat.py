"""REVISI HEMAT — petakan ulang HANYA bagian yang berubah + tetangganya.

═══════════════════════════════════════════════════════════════════════════
PUTUSAN BOS 13 Nov 2026 ("baca semua itu boros"):
    Jev/Hakim/LLM HANYA baca sekali, peta disimpan di database. Kalau naskah
    direvisi, HANYA bagian yang berubah yang dipetakan ulang, BESERTA
    tetangganya (bagian sebelum + sesudah, karena batas diputuskan di tepi).
    Hakim memeriksa ulang SELURUH peta (gratis, karena Hakim hanya kode).
    Baca ulang penuh HANYA bila perubahannya struktural.

PERILAKU LAMA (yang diganti): naskah berubah sedikit saja -> Jev baca ulang
SEMUA (~22,5 panggilan, ~Rp140-210 per revisi). Itu yang Bos sebut boros.

CARA KERJA (ringkas):
    1. Peta tersimpan membawa `peta_surveyor` (baris + label + goyang + p)
       dan `sidik_bagian` (tiap bagian: rentang baris + hash teksnya).
    2. Saat periksa ulang: diff baris lama vs baris baru (difflib, murni
       teks, tanpa Jev) -> bagian mana yang berubah.
    3. Bagian yang tidak berubah DIPAKAI ULANG (0 panggilan Jev).
    4. Bagian yang berubah + 1 tetangga tiap sisi dipetakan ulang lewat
       `petakan_teks` dengan awal/akhir (Jev hanya melihat rentang itu).
    5. Label digabung (lama dipetakan ulang ke indeks baru + label baru),
       demosi v14 diterapkan ulang pada peta gabungan, Hakim mengaudit
       SELURUH peta gabungan, agen kedua HANYA untuk butir BARU ditandai.
    6. Hasil gabungan disimpan (peta_json + sidik per bagian + sidik
       seluruh naskah yang baru).

PAGAR (WAJIB):
    P1  Modul ini TIDAK menyalin logika Jev/Hakim/jembatan. Semua yang
        sudah ada dipakai lewat fungsinya masing-masing (petakan_teks,
        periksa_peta, dari_surveyor, pendapat_kedua). Yang ditulis di sini
        hanyalah: diff, sidik per bagian, penggabungan, dan orkestrasi.
    P2  Gagal apa pun di jalur hemat -> kembalikan None -> pemanggil pakai
        baca penuh (perilaku lama). Hemat TIDAK BOLEH menghentikan produksi.
    P3  Naskah yang TIDAK berubah -> peta hasil IDENTIK dengan simpanan
        (0 panggilan Jev). Ini diuji eksplisit; bila label berubah pada
        naskah tak berubah, itu REGRESI.
    P4  Peta lama yang belum punya sidik per bagian -> baca penuh
        (kompatibilitas mundur). Jangan pernah pakai ulang secara salah.
    P5  Jangan ubah: urutan rantai agen kedua, prompt, max_tokens,
        saklar, aturan v14/v15/v15b, logika label Jev sendiri.

    CATATAN KEJUJURAN (tepi yang diketahui, 13 Nov 2026):
    Petakan parsial menjalankan `_petakan_dari_hasil` apa adanya, termasuk
    demosi v14 INTERNAL-nya yang memakai `gabung` PARSIAL. Bila rentang
    yang berubah mencakup blok daftar isi, demosi parsial bisa mendemosi
    satu-dua baris yang demosi global (yang diterapkan ulang sesudah
    gabung) tidak akan demosikan — dan demosi tidak bisa "dibatalkan".
    Praktiknya: blok daftar isi ada di awal naskah; revisi yang menyentuh
    awal naskah + blok daftar isi sekaligus jarang, dan Hakim mengaudit
    peta gabungan sesudahnya. Uji regresi (hemat vs penuh, naskah uji)
    mengunci tidak ada perbedaan label; ukur ulang 279 baris live sesudah
    deploy tetap disarankan sebagai bukti akhir.
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import difflib
import hashlib
import json
import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# ── AMBANG (dengan alasan; lihat `deteksi_struktural`) ───────────────────
TETANGGA = 1                # 1 bagian sebelum + 1 sesudah (batas di tepi)
AMBANG_STRUKTURAL_PERSEN = 25   # >25% baris berubah -> baca penuh: hematnya
                                # sudah kecil (<75% panggilan tersisa) dan
                                # risiko efek batas naik; baca penuh lebih aman
AMBANG_STRUKTURAL_BLOK = 10     # >10 blok berubah terpisah -> baca penuh:
                                # edit tersebar = naskah hampir baru

LABEL_SAH = ('bab', 'subbab', 'paragraf', 'biasa')

# Kunci internal di peta_json (hanya untuk DB, TIDAK dikembalikan ke layar).
KUNCI_INTERNAL = ('peta_surveyor', 'sidik_bagian', 'hakim_bagian')

# Pola judul untuk deteksi struktural (konservatif, hanya untuk MEMUTUSKAN
# baca penuh vs hemat — TIDAK PERNAH untuk melabel; pelabelan tetap Jev).
# BAB: "BAB I", "BAB 1", "Bab II ..." (romawi/angka, huruf besar/kecil).
# Subbab bernomor: "1.2 ...", "2.1.3 ..." (dua tingkat atau lebih).
_POLA_BAB = re.compile(r'^\s*BAB\s+([IVXLCDM]+|\d+)\b', re.IGNORECASE)
_POLA_SUBBAB = re.compile(r'^\s*\d+(?:\.\d+)+\s+\S')


# ══════════════════════════════════════════════════════════════════════════
#  SIDIK
# ══════════════════════════════════════════════════════════════════════════

def sidik_teks(teks: str) -> str:
    """Sidik jari teks (SHA-256). Sama rumusnya dengan peta_halus._sidik."""
    return hashlib.sha256((teks or '').encode('utf-8')).hexdigest()


def _sidik_baris(baris: list[str], awal: int, akhir: int) -> str:
    return sidik_teks('\n'.join(baris[awal:akhir]))


# ══════════════════════════════════════════════════════════════════════════
#  BAGIAN (rentang baris) — cermin logika `peta_jembatan.dari_surveyor`
# ══════════════════════════════════════════════════════════════════════════

def _nomor_dari_teks(t: str) -> str:
    """Ambil nomor '1.2' / '2.1.3' dari awal baris judul.

    Sama polanya dengan `peta_jembatan._nomor_dari_teks` (ditulis ulang di
    sini supaya modul ini tidak bergantung pada impor privat; uji mengunci
    perilakunya terhadap jembatan).
    """
    m = re.match(r'^\s*(\d+(?:\.\d+)*|[A-Z])[.)]?\s+\S', t)
    return m.group(1) if m else ''


def bagi_bagian(baris: list[str], gabung: dict | None,
                kode_label: dict | None = None,
                label: dict | None = None,
                sistematika: set | None = None,
                boleh: dict | None = None) -> list[dict[str, Any]]:
    """Bagi daftar baris menjadi BAGIAN (rentang [awal, akhir)).

    Posisi awal bagian = gabungan:
      · kunci `gabung` (judul BAB deterministik), dan
      · baris berlabel 'bab'/'subbab' (dari Jev),
    dikurangi baris sistematika / yang `boleh` nyatakan tidak boleh dipakai
    — PERSIS seperti `peta_jembatan.dari_surveyor` menghitung `pos`.
    Tanpa `label` (mis. untuk susun baru yang belum dipetakan Jev), hanya
    `gabung` + `kode_label` yang dipakai: hasilnya lebih kasar (beberapa
    subbab Jev menyatu dengan bagian sebelumnya) tapi TIDAK PERNAH salah
    arah — bagian yang digabung hanya membuat hematnya lebih kecil, bukan
    labelnya salah (uji mengunci ini).

    Tiap bagian: {'id', 'judul', 'awal', 'akhir', 'sidik'}.
    'id' = nomor bab ('BAB I') atau nomor subbab ('1.2') atau ''.
    """
    gabung = gabung or {}
    kode_label = kode_label or {}
    label = label or {}
    sistematika = sistematika or set()
    boleh = boleh or {}

    pos: list[int] = []
    for i in sorted(gabung.keys()):
        if i in sistematika:
            continue
        if isinstance(boleh, dict) and boleh.get(i) is False:
            continue
        pos.append(i)
    for i in sorted(kode_label.keys()):
        if i in sistematika:
            continue
        if isinstance(boleh, dict) and boleh.get(i) is False:
            continue
        pos.append(i)
    for i, lab in label.items():
        if lab not in ('bab', 'subbab'):
            continue
        if i in sistematika:
            continue
        if isinstance(boleh, dict) and boleh.get(i) is False:
            continue
        if isinstance(boleh, list) and 0 <= i < len(boleh) and not boleh[i]:
            continue
        pos.append(i)
    pos = sorted(set(pos))
    if not pos:
        # Naskah tanpa satu pun judul: satu bagian mencakup semua baris.
        if not baris:
            return []
        return [{'id': '', 'judul': '', 'awal': 0, 'akhir': len(baris),
                 'sidik': _sidik_baris(baris, 0, len(baris))}]

    bab_kini = ''
    keluar: list[dict[str, Any]] = []
    for n, i in enumerate(pos):
        akhir = pos[n + 1] if n + 1 < len(pos) else len(baris)
        nomor = ''
        if i in gabung:
            g = gabung.get(i)
            if isinstance(g, (tuple, list)):
                nomor = str(g[0] or '').strip() if g else ''
            else:
                nomor = str(g or '').strip()
            bab_kini = nomor
        elif label.get(i) == 'subbab':
            nomor = _nomor_dari_teks(str(baris[i] or ''))
            if not nomor and bab_kini:
                nomor = bab_kini
        elif i in kode_label:
            nomor = _nomor_dari_teks(str(baris[i] or ''))
            if not nomor and bab_kini:
                nomor = bab_kini
        judul = ' '.join(str(baris[i] or '').split()).strip()
        keluar.append({
            'id': nomor, 'judul': judul, 'awal': i, 'akhir': akhir,
            'sidik': _sidik_baris(baris, i, akhir),
        })
    return keluar


# ══════════════════════════════════════════════════════════════════════════
#  DIFF BARIS (murni teks, tanpa Jev)
# ══════════════════════════════════════════════════════════════════════════

def diff_baris(baris_lama: list[str], baris_baru: list[str]):
    """Opcode difflib (autojunk=False: naskah punya banyak baris pendek
    berulang seperti 'BAB I' — autojunk bisa salah menyelaraskan)."""
    sm = difflib.SequenceMatcher(None, baris_lama, baris_baru, autojunk=False)
    return sm.get_opcodes()


def peta_posisi(opcodes, n_lama: int, n_baru: int) -> list[int]:
    """S(p) = indeks baru dari garis batas SEBELUM baris lama p.

    Sisipan tepat di batas p ikut bagian SEBELUMNYA (bagian yang berakhir
    di p), kecuali sisipan di posisi 0 yang ikut bagian pertama — jadi
    rentang bagian yang dipetakan menutup [0, n_baru) tanpa celah dan tanpa
    tumpang tindih. Baris lama yang dihapus "runtuh" ke titik sisipan.
    """
    # indeks baru dari tiap baris lama yang masih hidup (None = terhapus)
    hidup: list[int | None] = [None] * n_lama
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            for k in range(i2 - i1):
                hidup[i1 + k] = j1 + k
    # S(p): indeks baru baris lama pertama yang hidup pada/ sesudah p.
    out: list[int] = [n_baru] * (n_lama + 1)
    berikut = n_baru
    for p in range(n_lama, -1, -1):
        if p < n_lama and hidup[p] is not None:
            berikut = hidup[p]
        out[p] = berikut
    # Sisipan di posisi 0 ikut bagian pertama: batas 0 tetap 0.
    out[0] = 0
    return out


def petakan_rentang(opcodes, n_lama: int, n_baru: int,
                    awal_lama: int, akhir_lama: int) -> tuple[int, int]:
    """Petakan rentang lama [awal_lama, akhir_lama) ke koordinat baru."""
    s = peta_posisi(opcodes, n_lama, n_baru)
    a = s[max(0, min(awal_lama, n_lama))]
    b = s[max(0, min(akhir_lama, n_lama))]
    if a > b:
        a, b = b, a
    return (max(0, a), min(n_baru, b))


# ══════════════════════════════════════════════════════════════════════════
#  DETEKSI STRUKTURAL
# ══════════════════════════════════════════════════════════════════════════

def urutan_judul(baris: list[str]) -> list[str]:
    """Urutan nomor judul (BAB + subbab bernomor) di naskah.

    Hanya NOMOR yang dibandingkan (judul boleh berubah kata-katanya —
    itu revisi biasa, bukan struktural). Subbab tanpa nomor tidak masuk
    urutan ini (ditangani lewat rentang + tetangga + audit Hakim).
    """
    keluar: list[str] = []
    for s in baris:
        m = _POLA_BAB.match(s or '')
        if m:
            keluar.append('BAB:' + m.group(1).upper())
            continue
        m2 = _POLA_SUBBAB.match(s or '')
        if m2:
            keluar.append('SUB:' + m2.group(0).split()[0])
    return keluar


def deteksi_struktural(baris_lama: list[str], baris_baru: list[str],
                       opcodes) -> tuple[bool, str]:
    """True bila perubahan STRUKTURAL -> baca ulang penuh.

    Struktural = salah satu:
      (a) urutan nomor judul berubah (BAB/subbab ditambah, dihapus,
          atau dipindah) — struktur global bergeser, rentang lama tidak
          lagi sejajar;
      (b) >AMBANG_STRUKTURAL_PERSEN baris berubah — naskah hampir baru,
          hematnya sudah kecil;
      (c) >AMBANG_STRUKTURAL_BLOK blok berubah terpisah — edit tersebar.
    Perubahan kata-kata dalam judul yang sama nomornya BUKAN struktural.
    """
    if urutan_judul(baris_lama) != urutan_judul(baris_baru):
        return True, 'urutan nomor judul berubah'
    berubah = sum((i2 - i1) + (j2 - j1)
                  for tag, i1, i2, j1, j2 in opcodes if tag != 'equal')
    total = max(len(baris_lama), len(baris_baru), 1)
    if berubah * 100 > AMBANG_STRUKTURAL_PERSEN * total:
        return True, ('%d%% baris berubah (>%d%%)'
                      % (berubah * 100 // total, AMBANG_STRUKTURAL_PERSEN))
    blok = sum(1 for tag, *_ in opcodes if tag != 'equal')
    if blok > AMBANG_STRUKTURAL_BLOK:
        return True, ('%d blok berubah terpisah (>%d)'
                      % (blok, AMBANG_STRUKTURAL_BLOK))
    return False, ''


# ══════════════════════════════════════════════════════════════════════════
#  RENCANA (murni: tanpa Jev, tanpa I/O)
# ══════════════════════════════════════════════════════════════════════════

def _normalisasi_label(label) -> dict[int, str]:
    """Kunci label dari JSON (str) -> int; buang label tak sah."""
    keluar: dict[int, str] = {}
    if not isinstance(label, dict):
        return keluar
    for k, v in label.items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            continue
        if v in LABEL_SAH:
            keluar[i] = v
    return keluar


def _normalisasi_peta(peta_lama) -> dict | None:
    """Muat peta tersimpan -> bentuk kerja, atau None bila tak bisa dipakai.

    Syarat bisa dipakai: dict dengan 'peta_surveyor' berisi 'baris' (list)
    + 'label' (dict), DAN 'sidik_bagian' tak kosong. Tanpa itu -> baca
    penuh (kompatibilitas mundur, P4).
    """
    if isinstance(peta_lama, str):
        try:
            peta_lama = json.loads(peta_lama)
        except Exception:
            return None
    if not isinstance(peta_lama, dict):
        return None
    surv = peta_lama.get('peta_surveyor')
    bagian = peta_lama.get('sidik_bagian')
    if not isinstance(surv, dict) or not isinstance(surv.get('baris'), list):
        return None
    if not isinstance(bagian, list) or not bagian:
        return None
    if not isinstance(surv.get('label'), dict):
        return None
    # Validasi ringan tiap bagian (rentang sah, sidik ada).
    for b in bagian:
        if not isinstance(b, dict):
            return None
        if not isinstance(b.get('sidik'), str) or not b.get('sidik'):
            return None
        if not isinstance(b.get('awal'), int) or not isinstance(b.get('akhir'), int):
            return None
    return {
        'baris': list(surv['baris']),
        'label': _normalisasi_label(surv.get('label')),
        'goyang': surv.get('goyang') or [],
        'p': {int(k): v for k, v in (surv.get('p') or {}).items()
              if str(k).lstrip('-').isdigit()},
        'bagian': bagian,
        'hakim': peta_lama.get('hakim') or {},
        'hakim_bagian': peta_lama.get('hakim_bagian') or [],
        'mentah': peta_lama,
    }


def rencanakan(peta_lama, baris_baru: list[str]) -> dict[str, Any]:
    """Tentukan jalan: 'pakai_ulang' | 'hemat' | 'penuh'.

    peta_lama: dict peta_json tersimpan (atau str JSON-nya).
    baris_baru: daftar baris naskah baru (SUDAH dibersihkan seperti susun).
    """
    lama = _normalisasi_peta(peta_lama)
    if lama is None:
        return {'jalan': 'penuh', 'alasan': 'peta lama tanpa sidik per bagian'}
    baris_lama = lama['baris']
    opcodes = diff_baris(baris_lama, baris_baru)
    if all(tag == 'equal' for tag, *_ in opcodes):
        return {'jalan': 'pakai_ulang', 'alasan': 'naskah tidak berubah',
                'lama': lama}
    struktural, alasan = deteksi_struktural(baris_lama, baris_baru, opcodes)
    if struktural:
        return {'jalan': 'penuh', 'alasan': 'struktural: ' + alasan,
                'lama': lama}

    # ── Bagian mana yang berubah? (rentang lama -> baru via opcode) ──────
    n_lama, n_baru = len(baris_lama), len(baris_baru)
    berubah_idx: list[int] = []
    for n, b in enumerate(lama['bagian']):
        a_baru, b_baru = petakan_rentang(opcodes, n_lama, n_baru,
                                         int(b['awal']), int(b['akhir']))
        sidik_baru = _sidik_baris(baris_baru, a_baru, b_baru)
        if sidik_baru != b['sidik']:
            berubah_idx.append(n)
    if not berubah_idx:
        # Diff ada tapi tak satu pun bagian berubah sidiknya (mis. hanya
        # baris kosong/whitespace yang ikut diff) -> pakai ulang, hemat 100%.
        return {'jalan': 'pakai_ulang',
                'alasan': 'hanya baris kosong berubah', 'lama': lama}

    # ── Perluas ke tetangga (1 bagian sebelum + 1 sesudah tiap yang berubah).
    rentang_idx = set()
    for n in berubah_idx:
        for m in (n - TETANGGA, n, n + TETANGGA):
            if 0 <= m < len(lama['bagian']):
                rentang_idx.add(m)
    awal = n_baru
    akhir = 0
    for m in sorted(rentang_idx):
        b = lama['bagian'][m]
        a_baru, b_baru = petakan_rentang(opcodes, n_lama, n_baru,
                                         int(b['awal']), int(b['akhir']))
        awal = min(awal, a_baru)
        akhir = max(akhir, b_baru)
    # Rentang tidak boleh kosong: bila pemetaan runtuh (mis. bagian yang
    # berubah terhapus seluruhnya), ambil titik hapusnya + tetangga.
    if awal >= akhir:
        awal = max(0, min(n_baru - 1, awal - 1)) if n_baru else 0
        akhir = min(n_baru, awal + 1)
    return {'jalan': 'hemat', 'awal': awal, 'akhir': akhir,
            'bagian_berubah': [lama['bagian'][n].get('id', '') or
                               lama['bagian'][n].get('judul', '')[:40]
                               for n in berubah_idx],
            'jumlah_bagian': len(lama['bagian']),
            'jumlah_berubah': len(berubah_idx),
            'alasan': ('%d dari %d bagian berubah'
                       % (len(berubah_idx), len(lama['bagian']))),
            'lama': lama}


# ══════════════════════════════════════════════════════════════════════════
#  PENGGABUNGAN (label lama dipetakan ke indeks baru + label baru)
# ══════════════════════════════════════════════════════════════════════════

def _peta_indeks(opcodes, n_lama: int) -> dict[int, int]:
    """Indeks baru tiap baris lama yang masih hidup (None = terhapus)."""
    keluar: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            for k in range(i2 - i1):
                keluar[i1 + k] = j1 + k
    return keluar


def gabungkan_label(label_lama: dict[int, str], opcodes,
                    n_lama: int, label_baru: dict[int, str],
                    awal: int, akhir: int,
                    kode_label_baru: dict | None = None) -> dict[int, str]:
    """Label gabungan: baris di luar rentang pakai label lama (dipetakan
    ke indeks baru), baris di dalam rentang pakai label baru. Terakhir,
    `kode_label` baru (deterministik, teks baru) menimpa semua — sama
    seperti jalur penuh yang menerapkannya di akhir."""
    peta = _peta_indeks(opcodes, n_lama)
    gabung: dict[int, str] = {}
    for i_lama, lab in label_lama.items():
        ni = peta.get(i_lama)
        if ni is None:
            continue                       # baris lama terhapus
        if awal <= ni < akhir:
            continue                       # di dalam rentang: label baru
        gabung[ni] = lab
    for i, lab in (label_baru or {}).items():
        #  Pagar: label parsial HANYA berlaku di dalam rentang. Bila hasil
        #  parsial membawa kunci di luar rentang (tidak seharusnya), abaikan
        #  — label lama yang dipetakan yang menang di luar rentang.
        if awal <= int(i) < akhir and lab in LABEL_SAH:
            gabung[int(i)] = lab
    for i, lab in (kode_label_baru or {}).items():
        if lab in LABEL_SAH:
            gabung[int(i)] = lab
    return gabung


def gabungkan_goyang(goyang_lama, opcodes, n_lama: int,
                     goyang_baru, awal: int, akhir: int):
    """Goyang gabungan — bentuk sama: [(i, [suara, ...]), ...]."""
    peta = _peta_indeks(opcodes, n_lama)
    gabung: dict[int, Any] = {}
    for item in (goyang_lama or []):
        try:
            i, suara = item[0], item[1]
        except Exception:
            continue
        ni = peta.get(int(i))
        if ni is None or (awal <= ni < akhir):
            continue
        gabung[ni] = suara
    for item in (goyang_baru or []):
        try:
            i, suara = item[0], item[1]
        except Exception:
            continue
        if awal <= int(i) < akhir:                  # pagar: hanya di rentang
            gabung[int(i)] = suara
    return [[i, gabung[i]] for i in sorted(gabung)]


def gabungkan_p(p_lama: dict, opcodes, n_lama: int,
                p_baru: dict, awal: int, akhir: int) -> dict[int, Any]:
    """Confidence gabungan (kunci int)."""
    peta = _peta_indeks(opcodes, n_lama)
    gabung: dict[int, Any] = {}
    for k, v in (p_lama or {}).items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            continue
        ni = peta.get(i)
        if ni is None or (awal <= ni < akhir):
            continue
        gabung[ni] = v
    for k, v in (p_baru or {}).items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            continue
        if awal <= i < akhir:                       # pagar: hanya di rentang
            gabung[i] = v
    return gabung


# ══════════════════════════════════════════════════════════════════════════
#  KOREKSI GLOBAL PASCA-GABUNG (v14 — satu-satunya yang butuh konteks penuh)
# ══════════════════════════════════════════════════════════════════════════

def _terapkan_demosi_v14(baris, label, kand, gabung) -> None:
    """Demosi blok daftar isi/sistematika pada label gabungan.

    Satu-satunya koreksi deterministik yang butuh konteks GLOBAL (blok
    dihitung dari gabung seluruh naskah) sehingga hasil parsial bisa
    berbeda dari hasil penuh. Aturan 2/4/5 + koreksi batas + bab
    deterministik bersifat lokal (baris + tetangga langsung) dan sudah
    diterapkan benar oleh petakan parsial itu sendiri.
    Gagal apa pun -> dilewati diam-diam (audit Hakim tetap jadi pagar).
    """
    try:
        from .peta3_jev import modul_surveyor as _modul
        m = _modul()
        if m is None:
            return
        deteksi = getattr(m, '_deteksi_blok_daftar_isi', None)
        demosi = getattr(m, '_demosi_blok_daftar_isi', None)
        if deteksi is None or demosi is None:
            return
        blok = deteksi(baris, gabung or {})
        demosi(baris, label, kand or [], set(blok))
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] demosi v14 dilewati: %s: %s',
                    type(e).__name__, e)


def _tandai_sistematika_gabung(baris, label, kand, gabung) -> set:
    """Himpunan baris sistematika pada peta gabungan (untuk jembatan)."""
    try:
        from .peta3_jev import modul_surveyor as _modul
        m = _modul()
        if m is None:
            return set()
        fn = getattr(m, '_tandai_sistematika', None)
        if fn is None:
            return set()
        return set(fn(baris, label, kand, gabung) or [])
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] sistematika gabungan dilewati: %s: %s',
                    type(e).__name__, e)
        return set()


# ══════════════════════════════════════════════════════════════════════════
#  AGEN KEDUA PADA PETA GABUNGAN (hanya butir BARU ditandai Hakim)
# ══════════════════════════════════════════════════════════════════════════

def _baru_ditandai(idx: int, peta_gabung: dict, lama: dict) -> bool:
    """True bila baris ini BELUM pernah ditandai Hakim sebelumnya.

    Bandingkan (teks, label): format baru `hakim_bagian` (teks lengkap)
    didahulukan; format lama `hakim.bagian_curiga` (judul 60 kar) sebagai
    cadangan. Tanpa jejak lama apa pun -> anggap BARU (panggil agen kedua,
    jangan diam-diam lewati — bila ragu, panggil).
    """
    baris = peta_gabung.get('baris') or []
    teks = (baris[idx] if 0 <= idx < len(baris) else '') or ''
    teks = ' '.join(str(teks).split()).strip()
    lab = (peta_gabung.get('label') or {}).get(idx)
    for b in (lama.get('hakim_bagian') or []):
        if not isinstance(b, dict):
            continue
        if b.get('status') not in ('ragu', 'curiga'):
            continue
        if (b.get('teks') or '').strip() == teks and b.get('label') == lab:
            return False
    for b in ((lama.get('hakim') or {}).get('bagian_curiga') or []):
        if not isinstance(b, dict):
            continue
        if (b.get('judul') or '') == teks[:60] and b.get('label') == lab:
            return False
    return True


def _konteks_lebar(idx: int, peta_gabung: dict) -> dict:
    """Konteks lebar untuk agen kedua — sama bentuknya dengan yang dipakai
    `_petakan_dari_hasil` (3 baris sebelum/sesudah + judul bab terdekat)."""
    baris = peta_gabung.get('baris') or []
    label = peta_gabung.get('label') or {}
    gabung = peta_gabung.get('gabung') or {}
    sebelum = [baris[k] for k in range(max(0, idx - 3), idx)]
    sesudah = [baris[k]
               for k in range(idx + 1, min(len(baris), idx + 4))]
    judul = None
    for k in range(idx - 1, -1, -1):
        if k in gabung:
            g = gabung[k]
            judul = ' '.join(g).strip() if isinstance(g, (tuple, list)) \
                else str(g).strip()
            break
        if label.get(k) == 'bab':
            judul = baris[k]
            break
    return {'sebelum': sebelum, 'sesudah': sesudah,
            'judul_bab_terdekat': judul}


def _terapkan_agen_kedua(peta_gabung: dict, baru_idx: list[int],
                         fn_pendapat_kedua) -> dict[str, Any]:
    """Adili butir baru dengan agen kedua (aturan `pendapat_kedua`
    yang sama seperti jalur penuh, mode='agen-kedua').

    Kembalikan {'jml', 'berbalik': [[i, lama, baru]], 'antrean': [i],
    'jawaban': [...]}. fn None -> tidak ada panggilan, semua kosong.
    """
    hasil = {'jml': 0, 'berbalik': [], 'antrean': [], 'jawaban': []}
    if fn_pendapat_kedua is None or not baru_idx:
        return hasil
    try:
        from .peta3_jev import modul_surveyor as _modul
        m = _modul()
        putuskan = getattr(m, 'pendapat_kedua', None) if m is not None else None
    except Exception:
        putuskan = None
    if putuskan is None:
        log.warning('[revisi_hemat] pendapat_kedua tak tersedia: agen kedua '
                    'dilewati (label Jev dipakai)')
        return hasil
    baris = peta_gabung.get('baris') or []
    label = peta_gabung.get('label') or {}
    p = peta_gabung.get('p') or {}
    semua = peta_gabung.get('semua') or {}
    for gi in sorted(baru_idx):
        suara = list(semua.get(gi) or [label.get(gi)])
        conf = [p.get(gi, 0.5)] * len(suara) if suara else [0.5]
        if not suara or suara[0] is None:
            continue
        label_jev = label.get(gi)
        try:
            jw2 = fn_pendapat_kedua(
                gi, baris[gi], list(suara), list(conf),
                _konteks_lebar(gi, peta_gabung))
        except Exception:
            jw2 = None
        try:
            put = putuskan(gi, baris[gi], list(suara), list(conf), jw2,
                           mode='agen-kedua')
        except Exception as e:                              # noqa: BLE001
            log.warning('[revisi_hemat] putusan agen kedua gagal L%d: %s',
                        gi, e)
            continue
        if not isinstance(put, dict) or put.get('putusan') == 'bukan-goyang':
            continue
        hasil['jml'] += 1
        hasil['jawaban'].append({
            'idx': gi, 'label_jev': label_jev,
            'label_kedua': (jw2 or {}).get('label')
                           if isinstance(jw2, dict) else None,
            'confidence': (jw2 or {}).get('confidence')
                          if isinstance(jw2, dict) else None,
            'putusan': put.get('putusan'),
            'label_akhir': put.get('label'),
            'alasan': (jw2 or {}).get('alasan', '')
                      if isinstance(jw2, dict) else '',
            'model': (jw2 or {}).get('model', '')
                     if isinstance(jw2, dict) else ''})
        if put.get('putusan') == 'berbalik':
            hasil['berbalik'].append([gi, label.get(gi), put.get('label')])
            label[gi] = put.get('label')
        elif put.get('putusan') == 'antrean-manusia':
            hasil['antrean'].append(gi)
    return hasil


# ══════════════════════════════════════════════════════════════════════════
#  SIMPANAN (DB) — bentuk baru peta_json
# ══════════════════════════════════════════════════════════════════════════

def _kunci_str(d: dict) -> dict:
    """Kunci int -> str (JSON)."""
    return {str(k): v for k, v in (d or {}).items()}


def siapkan_simpan(hasil: dict, peta_surveyor: dict,
                   audit_hakim: dict | None) -> dict:
    """Bangun salinan DB dari `hasil`: hasil + snapshot surveyor ringkas
    + sidik per bagian + jejak audit Hakim per butir.

    `hasil` yang dikembalikan ke layar TIDAK membawa kunci internal
    (tetap ramping); salinan DB-lah yang membawanya. Gagal apa pun ->
    kembalikan `hasil` apa adanya (hemat tidak jalan, tapi peta tetap
    tersimpan seperti dulu).
    """
    try:
        baris = peta_surveyor.get('baris') or []
        label = peta_surveyor.get('label') or {}
        gabung = peta_surveyor.get('gabung') or {}
        kode_label = peta_surveyor.get('kode_label') or {}
        sistematika = set(peta_surveyor.get('sistematika') or [])
        boleh = peta_surveyor.get('boleh_dipakai_fitur') or {}
        bagian = bagi_bagian(baris, gabung, kode_label, label,
                             sistematika, boleh)
        simpan = dict(hasil)
        simpan['peta_surveyor'] = {
            'baris': [str(x) for x in baris],
            'label': _kunci_str(label),
            'goyang': [[int(i), list(v)] for i, v in
                       (peta_surveyor.get('goyang') or [])],
            'p': _kunci_str(peta_surveyor.get('p') or {}),
        }
        simpan['sidik_bagian'] = bagian
        if isinstance(audit_hakim, dict):
            # Jejak per butir (teks lengkap, bukan 60 kar) supaya revisi
            # berikutnya bisa membedakan "sudah diadili" vs "baru".
            simpan['hakim_bagian'] = [
                {'i': b.get('i'), 'label': b.get('label'),
                 'status': b.get('status'),
                 'teks': ' '.join(str(
                     baris[b['i']] if isinstance(b.get('i'), int)
                     and 0 <= b['i'] < len(baris) else '').split()).strip()}
                for b in (audit_hakim.get('bagian') or [])
                if isinstance(b, dict)]
        return simpan
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] siapkan_simpan gagal: %s: %s',
                    type(e).__name__, e)
        return dict(hasil)


def buang_kunci_internal(peta: dict) -> dict:
    """Buang kunci internal dari salinan yang dikembalikan ke layar."""
    if not isinstance(peta, dict):
        return peta
    keluar = dict(peta)
    for k in KUNCI_INTERNAL:
        keluar.pop(k, None)
    return keluar


# ══════════════════════════════════════════════════════════════════════════
#  ORKESTRASI — periksa_hemat
# ══════════════════════════════════════════════════════════════════════════

def _gerbang_kosong(_peta_sementara):
    """Gerbang Lapis 2 untuk petakan parsial: KOSONG.

    Agen kedua TIDAK dipanggil di dalam petakan parsial — ia dipanggil
    SEKALI di akhir, pada peta gabungan, hanya untuk butir BARU. Bila
    gerbang ini tidak disuntik, `petakan_dari_teks` membangun rantai
    otomatis dan agen kedua terpanggil di dalam parsial (boros + ganda).
    """
    return set()


def _buang_daftar_isi(teks: str) -> str:
    try:
        from .state import buang_daftar_isi as _buang
        return _buang(teks or '')
    except Exception:
        return teks or ''


def periksa_hemat(teks: str, peta_lama, mode: str = 'peta_awal',
                  fn_petakan_teks=None, fn_susun_teks=None,
                  fn_pendapat_kedua=None) -> dict | None:
    """Jalur hemat. Kembalikan None bila TIDAK BISA -> pemanggil pakai
    baca penuh (perilaku lama). Bila bisa, kembalikan:
      {'jalan': 'pakai_ulang'|'hemat', 'hasil': {...}, 'simpan': {...}}.

    `teks`: naskah mentah (seperti yang diterima peta_mulai).
    `peta_lama`: dict peta_json tersimpan (atau str JSON-nya).
    `fn_petakan_teks`: (teks_bersih, awal, akhir, pendapat_kedua_fn,
        hakim_tandai_fn) -> dict surveyor | None. Bawaan: petakan_teks
        produksi (Jev sungguhan). Uji menyuntik palsu pencatat panggilan.
    `fn_susun_teks`: (teks_bersih) -> dict susun | None. Bawaan: susun
        produksi (deterministik, tanpa Jev).
    `fn_pendapat_kedua`: fn agen kedua untuk peta gabungan (None = mati).
    """
    try:
        lama = _normalisasi_peta(peta_lama)
    except Exception:
        return None
    if lama is None:
        return None
    try:
        teks_bersih = _buang_daftar_isi(teks)
    except Exception:
        return None

    # ── susun baru (deterministik, gratis, tanpa Jev) ────────────────────
    if fn_susun_teks is None:
        try:
            from .peta3_jev import susun_teks as _susun
            fn_susun_teks = _susun
        except Exception:
            return None
    try:
        susun_baru = fn_susun_teks(teks_bersih)
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] susun baru gagal: %s: %s',
                    type(e).__name__, e)
        return None
    if not isinstance(susun_baru, dict) or not isinstance(
            susun_baru.get('baris'), list):
        return None
    baris_baru = susun_baru['baris']

    # ── rencanakan ────────────────────────────────────────────────────────
    rencana = rencanakan(lama['mentah'], baris_baru)
    if rencana['jalan'] == 'pakai_ulang':
        hasil = buang_kunci_internal(dict(lama['mentah']))
        hasil['ok'] = True
        hasil['gratis'] = True
        hasil['dari_simpanan'] = True
        hasil['mode'] = mode
        return {'jalan': 'pakai_ulang', 'hasil': hasil, 'simpan': None}
    if rencana['jalan'] != 'hemat':
        return None
    awal, akhir = int(rencana['awal']), int(rencana['akhir'])

    # ── petakan parsial (Jev HANYA untuk rentang) ─────────────────────────
    if fn_petakan_teks is None:
        try:
            from .peta3_jev import petakan_teks as _petakan_teks
            fn_petakan_teks = _petakan_teks
        except Exception:
            return None
    try:
        parsial = fn_petakan_teks(
            teks_bersih, awal, akhir,
            pendapat_kedua_fn=None, hakim_tandai_fn=_gerbang_kosong)
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] petakan parsial gagal: %s: %s',
                    type(e).__name__, e)
        return None
    if not isinstance(parsial, dict) or not isinstance(
            parsial.get('label'), dict):
        return None

    # ── gabungkan ─────────────────────────────────────────────────────────
    opcodes = diff_baris(lama['baris'], baris_baru)
    n_lama = len(lama['baris'])
    label_gabung = gabungkan_label(
        lama['label'], opcodes, n_lama, parsial.get('label') or {},
        awal, akhir, susun_baru.get('kode_label') or {})
    goyang_gabung = gabungkan_goyang(
        lama.get('goyang') or [], opcodes, n_lama,
        parsial.get('goyang') or [], awal, akhir)
    p_gabung = gabungkan_p(
        lama.get('p') or {}, opcodes, n_lama,
        parsial.get('p') or {}, awal, akhir)
    _terapkan_demosi_v14(baris_baru, label_gabung,
                         susun_baru.get('kand') or [],
                         susun_baru.get('gabung') or {})

    sist = _tandai_sistematika_gabung(
        baris_baru, label_gabung, susun_baru.get('kand') or [],
        susun_baru.get('gabung') or {})
    boleh: dict[int, bool] = {}
    for i in label_gabung:
        boleh[i] = True if i in (susun_baru.get('kode_label') or {}) \
            else (i not in sist)
    peta_gabung = {
        'baris': baris_baru,
        'kand': susun_baru.get('kand') or [],
        'label': dict(label_gabung),
        'goyang': goyang_gabung,
        'p': dict(p_gabung),
        'gabung': susun_baru.get('gabung') or {},
        'buang': susun_baru.get('buang') or [],
        'sistematika': sorted(sist),
        'boleh_dipakai_fitur': boleh,
        'kode_label': susun_baru.get('kode_label') or {},
        'semua': parsial.get('semua') or {},
    }

    # ── Hakim audit SELURUH peta gabungan (gratis, deterministik) ─────────
    try:
        from .hakim_peta import periksa_peta as _periksa
        audit = _periksa(peta_gabung)
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] audit Hakim gagal: %s: %s',
                    type(e).__name__, e)
        return None

    # ── Agen kedua HANYA untuk butir BARU ditandai Hakim ──────────────────
    ak = {'jml': 0, 'berbalik': [], 'antrean': [], 'jawaban': []}
    if isinstance(audit, dict) and audit.get('ok'):
        try:
            from .hakim_peta import tandai_ragu_curiga as _tandai
            ditandai = _tandai(peta_gabung) or set()
        except Exception:
            ditandai = set()
        baru = [i for i in sorted(ditandai)
                if _baru_ditandai(i, peta_gabung, lama)]
        if baru and fn_pendapat_kedua is not None:
            ak = _terapkan_agen_kedua(peta_gabung, baru, fn_pendapat_kedua)
            # Audit ulang sesudah putusan agen kedua (sama seperti jalur
            # penuh yang mengaudit peta FINAL, bukan pra-agen-kedua).
            try:
                from .hakim_peta import periksa_peta as _periksa2
                audit = _periksa2(peta_gabung)
            except Exception:
                pass

    # ── Jembatan -> daftar (bentuk state.petakan) ─────────────────────────
    try:
        from .peta_jembatan import dari_surveyor as _jembatan
        _bagian = _jembatan(peta_gabung, teks_bersih)
    except Exception as e:                                  # noqa: BLE001
        log.warning('[revisi_hemat] jembatan gagal: %s: %s',
                    type(e).__name__, e)
        return None
    if not _bagian:
        return None
    sid = sidik_teks(teks)
    hasil = {
        'mode': mode, 'jumlah': len(_bagian),
        'daftar': [
            {'id': f'b{i}', 'bab': d.get('section_id') or str(i + 1),
             'subbab': '', 'judul_bab': d.get('section_title') or '',
             'sub_judul': '', 'masalah': 'struktur dari peta naskah',
             'saran': '', 'berat': 'ringan'}
            for i, d in enumerate(_bagian)],
        'diam': False,
        'pesan': 'EduAi sudah membaca struktur naskahmu (peta 3 tingkat).',
        'peta_dari': 'jev',
        'peta_alasan': ('jev hemat: %s (rentang baris %d-%d dari %d)'
                        % (rencana.get('alasan', ''), awal, akhir,
                           len(baris_baru))),
        'bab_terdeteksi': [
            {'bab': d.get('section_id') or str(i + 1),
             'judul': d.get('section_title') or ''}
            for i, d in enumerate(_bagian)],
        'ok': True, 'gratis': True,
        'sidik': sid, 'model': 'peta3_jev',
        'pesan_kuota': ('Tahap ini GRATIS — membaca naskah tidak memakai '
                        'Token Revisi.'),
        'hakim': {
            'jumlah_sepakat': audit.get('jumlah_sepakat'),
            'jumlah_ragu': audit.get('jumlah_ragu'),
            'jumlah_curiga': audit.get('jumlah_curiga'),
            'jumlah_belum': audit.get('jumlah_belum'),
            'alasan': audit.get('alasan'),
            'bagian_curiga': [b for b in (audit.get('bagian') or [])
                              if b.get('status') == 'curiga'],
        } if isinstance(audit, dict) else {},
        'revisi_hemat': {
            'jalan': 'hemat', 'awal': awal, 'akhir': akhir,
            'bagian_berubah': rencana.get('bagian_berubah') or [],
            'agen_kedua_jml': ak.get('jml', 0),
            'agen_kedua_antrean': ak.get('antrean', []),
        },
    }
    simpan = siapkan_simpan(hasil, peta_gabung, audit)
    # Jejak agen kedua disimpan (bukan dikembalikan ke layar).
    simpan['agen_kedua'] = ak.get('jawaban', [])
    return {'jalan': 'hemat', 'hasil': hasil, 'simpan': simpan}
