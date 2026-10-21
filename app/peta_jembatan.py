"""JEMBATAN PETA — SURVEYOR (`peta3_jev`) → bentuk `state.petakan()` (list[dict]).

═══════════════════════════════════════════════════════════════════════════
PUTUSAN BOS 09 Okt 2026 = **OPSI A**
    "surveyor jadi SUMBER, jembatan menerjemahkan."
    ⇒ Surveyor (Jev) = SUMBER struktur.
    ⇒ Fungsi ini = PENERJEMAH ke bentuk lama ⇒ 5 pemakai LAMA TIDAK DIUBAH.
    ⇒ NOL risiko ke harga kuota (`state.petakan` = penentu harga).

ALASAN (aturan induk Bos — "jangan buat baru, sinkron yang sudah ada"):
    • Bentuk keluaran DUA peta itu BEDA ⇒ TIDAK bisa tukar-emblek:

        state.petakan()   : teks   → list[dict]  (section_id, section_title,
                                                    isi_teks, char_count, kategori)
                                                    ← sumbernya REGEX
        peta3_jev.petakan : fid    → dict        (baris, kand, label, gabung,
                                                    p, sistematika, ...)
                                                    ← sumbernya JEV

    • Kalau ditimpa langsung, 5+ pemakai rusak & HARGA KUOTA bisa berubah.
    • Pola jembatan ini SUDAH ADA di proyek: `app/konteks.py:134`
      ("terjemahkan keluaran state.petakan() → bentuk konteks.py").
      Sama persis polanya: perubahan TERISOLASI, berkas terbukti tak disentuh.

PAGAR (WAJIB, jangan dilanggar):
    P1  Berkas ini TIDAK mengubah `state.py`, `ai.py`, atau `peta3_jev.py`.
    P2  Kalau surveyor GAGAL/mati → KEMBALI KE CARA LAMA (`state.petakan`).
        Jev mati TIDAK BOLEH menghentikan jalur lama (pagar P1/P2 rancangan).
    P3  Keluaran WAJIB bentuk SAMA PERSIS dengan `state.petakan()` —
        kunci: section_id · section_title · kategori · char_count · isi_teks.
    P4  `nomor` sub-bab dinormalkan SAMA gaya lama (`title_for`/`get_category_for`).

STATUS: BARU 09 Okt 2026 — belum dipasang ke pemakai mana pun (uji dulu).
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def _norm_title(nomor: str) -> str:
    """Judul baku kode — SAMA seperti `state.title_for()` (impor, jangan salin)."""
    try:
        from .state import title_for
        return title_for(nomor) or ''
    except Exception:
        return ''


def _norm_kategori(nomor: str) -> str:
    """Kategori — SAMA seperti `state.get_category_for()` (impor, jangan salin)."""
    try:
        from .state import get_category_for
        return get_category_for(nomor) or ''
    except Exception:
        return ''


def dari_surveyor(peta_surveyor: dict[str, Any] | None,
                  teks: str = '') -> list[dict[str, Any]] | None:
    """Terjemahkan keluaran `peta3_jev.petakan()` → bentuk `state.petakan()`.

    Kembalikan `None` (BUKAN list kosong) kalau surveyor tidak bisa dipakai —
    supaya PEMANGGIL tahu harus kembali ke cara lama (pagar P2).
    List kosong = surveyor JALAN tapi memang tidak ada bagian.

    Bentuk masukan (`peta3_jev.petakan`, terverifikasi 09 Okt):
        {'baris': [...], 'kand': [(i, teks), ...], 'label': {i: 'bab'|'subbab'|
         'paragraf'|'biasa'}, 'gabung': {i: 'BAB I'}, 'p': {i: 0.97}, ...}

    Bentuk keluaran (WAJIB sama dengan state.petakan, pagar P3):
        [{'section_id','section_title','kategori','char_count','isi_teks'}, ...]
    """
    if not isinstance(peta_surveyor, dict):
        return None
    try:
        baris = peta_surveyor.get('baris')
        label = peta_surveyor.get('label')
        if not isinstance(baris, list) or not isinstance(label, dict) or not label:
            return None

        # ── Kumpulkan posisi awal tiap JUDUL (bab + subbab).
        #    ⚠️ Label 'bab' di peta3_jev BISA berisi baris yang sebenarnya
        #    daftar isi. Pagar: `boleh_dipakai_fitur` (dari `asal`/`sistematika`).
        #    Kalau ada, PAKAI. Kalau tidak ada, jangan menebak — pakai apa adanya.
        boleh = peta_surveyor.get('boleh_dipakai_fitur')
        sist = set(peta_surveyor.get('sistematika') or [])
        gabung = peta_surveyor.get('gabung') or {}

        pos: list[int] = []

        # ── PERBAIKAN 14 Okt 2026: BAB ASLI dari `gabung` WAJIB masuk `pos`.
        #    Dokumen `CATATAN_KEPUTUSAN_PETA3` baris 141:
        #      "BAB ASLI = len(r['gabung']) + jumlah label 'bab' YANG BUKAN
        #       sistematika"  ⇒ `gabung` = SUMBER bab (kode murni, STABIL
        #       lintas-run), BUKAN hiasan.
        #    AKAR BUG TERUKUR (Asih fid=81): `gabung`={0:'BAB I', 211:...}
        #    sedangkan label 'bab' jatuh di baris 191-207 (= DAFTAR ISI).
        #    ⇒ tanpa baris ini, 130 subbab keluar TANPA nomor bab dan
        #      `section_id` semuanya kosong.
        for i in sorted(gabung.keys()):
            if i in sist:
                continue
            if isinstance(boleh, dict) and boleh.get(i) is False:
                continue
            pos.append(i)

        for i, lab in label.items():
            if lab not in ('bab', 'subbab'):
                continue
            if isinstance(boleh, list) and 0 <= i < len(boleh) and not boleh[i]:
                continue                       # ditandai TIDAK boleh dipakai
            if isinstance(boleh, dict) and boleh.get(i) is False:
                continue
            if i in sist:
                continue
            pos.append(i)
        pos = sorted(set(pos))
        if not pos:
            return []

        # ── Potong isi antar-posisi (pola sama `deteksi_subbab`).
        #    Batas akhir = posisi judul berikutnya; yang terakhir = akhir teks.
        batas: list[tuple[int, int]] = []
        for n, i in enumerate(pos):
            akhir = pos[n + 1] if n + 1 < len(pos) else len(baris)
            batas.append((i, akhir))

        hasil: list[dict[str, Any]] = []
        gab = peta_surveyor.get('gabung') or {}
        _bab_kini = ''          # nomor BAB yang sedang berjalan (dari `gabung`)
        for i, akhir in batas:
            # nomor: dari `gabung` kalau ada (judul BAB asli), kalau tidak
            # pakai 'subbab' polos (tanpa nomor) — JANGAN menebak nomor.
            nomor = ''
            if i in gab:
                _g = gab.get(i)
                #  bentuk terukur peta3_jev: tuple ('BAB I', 'PENDAHULUAN').
                #  `section_id` WAJIB ringkas ('BAB I') supaya SAMA dengan
                #  `state.petakan()` (pagar P3) — nama bab TIDAK digabung.
                if isinstance(_g, (tuple, list)):
                    nomor = str(_g[0] or '').strip() if _g else ''
                else:
                    nomor = str(_g or '').strip()
                _bab_kini = nomor            # bagian berikut ikut bab ini
            elif label.get(i) == 'subbab':
                nomor = _nomor_dari_teks(str(baris[i] or ''))
                #  ⚠️ PERBAIKAN 14 Okt: subbab TANPA nomor sendiri tetap perlu
                #     tahu bab induknya ⇒ `section_id` = nomor bab (bukan '').
                #     Kalau tidak, seluruh peta keluar tanpa id (bug terukur).
                if not nomor and _bab_kini:
                    nomor = _bab_kini
            isi = '\n'.join(str(x) for x in baris[i:akhir])
            judul_asli = ' '.join(str(baris[i] or '').split()).strip()
            hasil.append({
                'section_id': nomor,
                # ⚠️ ATURAN BUG ke-16 (16Sep26): JUDUL ASLI NASKAH SELALU MENANG.
                'section_title': judul_asli or _norm_title(nomor) or f'Bagian {i}',
                'kategori': _norm_kategori(nomor),
                'char_count': len(isi),
                'isi_teks': isi,
            })
        return hasil
    except Exception as e:                                  # pagar P2
        log.warning('[peta_jembatan] gagal menerjemahkan peta surveyor: %s: %s',
                    type(e).__name__, e)
        return None


def _nomor_dari_teks(t: str) -> str:
    """Ambil nomor '1.2' / '2.1.3' / 'A.' dari awal baris judul.

    ⛔ TIDAK MENEBAK bentuk naskah (larangan Bos) — hanya MEMBACA nomor yang
    SUDAH tertulis di baris itu. Kalau tidak ada nomor, kembalikan ''.
    """
    import re
    m = re.match(r'^\s*(\d+(?:\.\d+)*|[A-Z])[.)]?\s+\S', t)
    if not m:
        return ''
    return m.group(1)
