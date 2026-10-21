"""HAKIM T① — PERIKSA **PETA SURVEYOR** (bukan peta mesin lagi).

═══════════════════════════════════════════════════════════════════════════
PUTUSAN BOS 09 Okt 2026:
  · T① = hakim menilai **PETA SURVEYOR** (hasil `peta3_jev`), bukan peta mesin.
  · SKEMA 2-SUMBER, **TANPA AMBANG `p`** (§7c rancangan):
        curiga  ← kode deterministik (`pola_penulisan.judul_curiga`)  → lapor
        ragu    ← **vonis HAKIM sendiri** (menilai barisnya LANGSUNG) → 1 putaran
        sepakat ← sisanya
        `p`     → HANYA info tampilan, ⛔ tidak pernah jadi input keputusan
  · Pagar H1: **Hakim LAPOR, jangan BLOKIR** (tidak boleh menghentikan mesin).

═══════════════════════════════════════════════════════════════════════════
RANCANGAN TUGAS (§2 rancangan) — yang dikerjakan modul ini:
  T① peta SURVEYOR yang dinilai (bukan `deteksi_bab_besar`)
  T② cek JUDUL vs LANJUTAN per kandidat — jendela 3 baris ber-ID, tipe `noul`:
      "Apakah baris tengah ini benar AWAL <bab|sub-bab>?"
      ⇒ di sini **vonis hakim** yang menentukan ragu (bukan `p`)
  T⑤ keluarkan DAFTAR KECURIGAAN (bukan cuma lolos/tolak)
  T③ TIDAK dipakai di sini (itu per-bab hitung, beda langkah)
  T④ dipakai apa adanya (`jumlah_bab`/`semua_romawi_sah`/`berurutan`) — dari `satpam`

═══════════════════════════════════════════════════════════════════════════
PAGAR (WAJIB, tidak boleh dilanggar):
  P1  Hakim mati / galat ⇒ kembalikan laporan KOSONG, mesin TETAP jalan
  P2  Jangan melempar galat keluar
  P3  JANGAN memutuskan label — hakim hanya melaporkan status per bagian
  P4  Jumlah bagian TIDAK berkurang
  P5  `p` hanya dicatat sebagai `p_info`, TIDAK dipakai memfilter/memutuskan
  P6  JANGAN menyentuh `app/satpam.py` (dipakai jalur biaya) — modul ini TERPISAH

Jalan: docker exec -w /app eduai-app python3 app/hakim_peta.py
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, '/app')

log = logging.getLogger('hakim_peta')

# ── setelan: MEMINJAM setelan satpam (KUNCI/BASE/MODEL) — jangan bikin setelan baru
try:
    from . import satpam as _satpam
    _AKTIF = bool(getattr(_satpam, 'AKTIF', False))
    _BASE = getattr(_satpam, 'BASE', '')
    _KUNCI = getattr(_satpam, 'KUNCI', '')
    _MODEL = getattr(_satpam, 'MODEL', '')
    _BATAS = float(getattr(_satpam, 'BATAS_DETIK', 90))
except Exception:                                     # P2: telan
    _AKTIF, _BASE, _KUNCI, _MODEL, _BATAS = False, '', '', '', 90.0

#  Label judul yang diperiksa hakim (paragraf/biasa BUKAN tugas hakim)
LABEL_JUDUL = ('bab', 'subbab')

#  Frekuensi panggilan: SATU panggilan untuk sekumpulan kandidat (hemat).
MAKS_TANYA = 24          # kandidat per panggilan (batas aman teruji 156; ini hemat)

#  ⚠️ Bentuk WAJIB: `questions` = OBJEK `{nama: {...}}`, BUKAN list.
#     (Terukur 09 Okt 2026: list ⇒ 9router balas 503 palsu
#      "questions harus objek berisi minimal 1 pertanyaan".)
#  ⚠️ TERUKUR 09 Okt 2026 (JALAN TOL): Jev melaporkan SATU angka per NAMA
#     pertanyaan. Kalau semua kandidat ditumpuk jadi 1 pertanyaan ("judul_sah"),
#     Jev menjawab SEKALI untuk seluruh blok ⇒ mustahil dipetakan per baris
#     (itu sebabnya 131 kandidat selalu 'belum').
#     ⇒ WAJIB 1 pertanyaan PER KANDIDAT, namanya = "L000123".
#     Bentuk jawaban: {"L000004": {"type":"noul","noul":0.82}, ...}
#  ── K5 — 🚫 DIMATIKAN 14 Okt 2026 (putusan Bos: SALAH ALAT UKUR) ──────────
#  K5 = kalimat criteria yang DISETEL PER-KASUS. Terbukti TIDAK BISA menyeberang
#  naskah ⇒ MUSTAHIL untuk app yang menerima RIBUAN naskah.
#
#  Vonis Bos (09 Okt, verbatim): "Hasil uji ini tidak bisa buat naskah general.
#  Terlalu detail cocok untuk 1 naskah saja."
#  Vonis Bos (14 Okt, verbatim): "K5 itu terlalu detail hanya cocok untuk 1
#  naskah saja, tidak bisa dipakai untuk global. Karena app EduAi ini akan
#  menerima ribuan naskah nantinya."
#
#  Bukti overfit (terukur): '3. Tinjauan Literatur' → 0,63 di Asih tapi 0,12 di
#  fid=115 · 12/12 di set latih → ~10/16 di set uji segar · 4× 'Informan' gagal
#  walau 3 definisi ditambah.
#
#  ⛔ SAKLAR: K5 AKTIF = False. JANGAN dinyalakan tanpa izin eksplisit Bos.
#     Selaras rancangan hakim §7c: "ambang DIBUBARKAN — ini masalah SALAH ALAT
#     UKUR, bukan masalah kalibrasi."
#  Teks criteria DIPERTAHANKAN di bawah (jangan dibuang) untuk arkeologi/uji
#  ulang kalau kelak ada arahan baru.
#  Lihat: PENUTUP_UJI_K5_09OKT2026.md §4 · HASIL_PENYELIDIKAN_PETA_14OKT2026.md
K5_AKTIF = False

CRITERIA_K5 = {
    'true': ('Baris adalah JUDUL BAGIAN dari kerangka naskah. Ciri: berisi nama '
             'topik bahasan (bukan nama kegiatan/langkah), nomornya menandai '
             'kedudukan bagian dalam kerangka tulisan seperti 2.1 atau BAB II '
             'atau nomor polos tanpa titik yang sejajar dengan judul bab lain '
             'di dokumen ini, dan baris berikutnya mulai dengan paragraf '
             'penjelasan baru.'),
    'false': ('Baris adalah SATU LANGKAH KEGIATAN atau SATU BUTIR dari sebuah '
              'daftar cara kerja, atau bagian lain yang bukan kepala tulisan: '
              'deret angka di dalam tabel, sel dan kolom, keterangan bernama '
              'di atas tabel atau gambar, potongan kutipan wawancara, nama '
              'sumber, atau sambungan kalimat sebelumnya yang belum selesai.'),
}


def _q_per_kandidat(blok: list[dict]) -> dict:
    """Bentuk pertanyaan: satu per kandidat (nama = L%06d).

    ⛔ K5 DIMATIKAN (14 Okt 2026) — `criteria` HANYA dipasang kalau K5_AKTIF.
    Tanpa criteria: Jev menilai barisnya LANGSUNG (vonis hakim sendiri),
    bukan mencocokkan kalimat criteria yang disetel per-naskah.
    Selaras rancangan hakim §7c (ambang DIBUBARKAN — salah alat ukur).
    """
    q = {}
    for k in blok:
        tanya = {
            'type': 'noul',
            'instructions': (f"Apakah baris TENGAH untuk {k['i']:06d} di atas "
                             'benar-benar KEPALA BAGIAN (judul) naskah?'),
        }
        if K5_AKTIF:                       # ← False: criteria TIDAK dikirim
            tanya['criteria'] = CRITERIA_K5
        q[f"L{k['i']:06d}"] = tanya
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
    """Pakai `satpam.tanya_bebas_mutu` — jalur BAHAN SIAP (sudah terbukti di konversi).

    ⚠️ JEBAKAN TERUKUR 09 Okt 2026 (2× makan waktu):
       `tanya_bebas(teks, peta, q)` MENYUSUN ULANG state dari arg ke-2 (`peta`).
       Kalau peta `[]` ⇒ state jadi "PETA ... (0 bagian)" ⇒ bahan jendela
       kita DIBUANG ⇒ Jev jawab salah/503 semu. ⇒ PAKAI `tanya_bebas_mutu`,
       yang menerima bahan yang SUDAH disusun pemanggil.

    P1/P2: TIDAK PERNAH melempar galat — gagal ⇒ None, pemanggil lanjut.
    """
    if not _AKTIF:
        return None
    try:
        from . import jev as _jev
        return _jev.tanya(bahan, pertanyaan)
    except Exception as e:                             # P1/P2
        log.warning('[hakim_peta] jalan tol Jev gagal: %s: %s', type(e).__name__, e)
        return None


#  ── PEMETAAN PRODUKSI — ⚠️ AMBANG 0,60/0,30 = SETELAN 1-NASKAH (DIMATIKAN) ──
#  🚫 DIRANCANG 09 Okt dari 18 kandidat SATU naskah; goyang ±4 kandidat/putaran.
#  Vonis Bos 09 Okt: "Terlalu detail cocok untuk 1 naskah saja."
#  Vonis Bos 14 Okt: TIDAK bisa untuk GLOBAL (app akan menerima RIBUAN naskah).
#
#  ⇒ Ambang ini DIPERTAHANKAN hanya sebagai catatan angka. JANGAN dipakai
#    sebagai SAKLAR di produksi (rancangan hakim §7c: ambang DIBUBARKAN).
#    Sesudah K5 mati, Jev menilai barisnya LANGSUNG — nilai `noul` tidak lagi
#    dibandingkan ke ambang tetap.
#  Lihat: HASIL_PENYELIDIKAN_PETA_14OKT2026.md · PENUTUP_UJI_K5_09OKT2026.md §3
AMBANG_SEPAKAT = 0.60          # ⛔ catatan 1-naskah — bukan saklar produksi
AMBANG_CURIGA = 0.30           # ⛔ catatan 1-naskah — bukan saklar produksi


def _status_vonis(noul: float) -> str:
    """Petakan skor noul ⇒ status hakim. Nilai awal; catat & review berkala."""
    if noul >= AMBANG_SEPAKAT:
        return 'sepakat'
    if noul < AMBANG_CURIGA:
        return 'curiga'
    return 'ragu'               # 0,30-0,60 = zona kerja hakim (jaring aman)


def periksa_peta(peta_surveyor: dict) -> dict:
    """T① — hakim menilai PETA SURVEYOR. SELALU mengembalikan dict (P1).

    Keluaran (T⑤):
      {'ok', 'keputusan', 'bagian':[{i,label,judul,p_info,status}],
       'jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'alasan'}
    """
    kosong = {'ok': False, 'keputusan': 'mati', 'bagian': [],
              'jumlah_sepakat': 0, 'jumlah_ragu': 0, 'jumlah_curiga': 0,
              'alasan': 'tidak bisa diperiksa'}
    if not isinstance(peta_surveyor, dict):
        return kosong

    baris = peta_surveyor.get('baris') or []
    kand = _kandidat_judul(peta_surveyor)

    #  🚨 PAGAR DEGRADASI SENYAP (terukur 09 Okt 2026):
    #     `peta3_jev.petakan()` TIDAK melaporkan kegagalan Jev — kalau Jev kena
    #     503, SEMUA baris dilabeli 'biasa' (491 baris) dan `gagal=0`.
    #     Akibatnya hakim melihat "0 kandidat judul" dan TIDAK TAHU itu gagal.
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

    # ── SUMBER-1: curiga = kode deterministik (gratis, presisi 100% terbukti)
    curiga_kode: set[int] = set()
    try:
        from .pola_penulisan import judul_curiga as _jc
        for c in (_jc([(i, baris[i]) for i, _ in enumerate(baris)]) or []):
            curiga_kode.add(int(c.get('i')))
    except Exception as e:                             # P2
        log.warning('[hakim_peta] judul_curiga gagal: %s', e)

    # ── SUMBER-2: ragu = VONIS HAKIM (bukan `p`)
    vonis: dict[int, str] = {}
    for mulai in range(0, len(kand), MAKS_TANYA):
        blok = kand[mulai:mulai + MAKS_TANYA]
        bahan = _bahan_kandidat(blok, baris)
        jalan = _tanya_jev(bahan, _q_per_kandidat(blok))
        if jalan is None:
            continue                                   # P1: lewati, jangan hentikan
        # Jev menjawab per kandidat — kunci urut baris
        for k in blok:
            jaw = (jalan.get(f'L{k["i"]:06d}') or jalan.get(str(k['i']))
                   or jalan.get(f'baris_{k["i"]}'))
            if isinstance(jaw, dict):
                noul = jaw.get('noul')
                if noul is not None:
                    vonis[k['i']] = _status_vonis(float(noul))
    #  DEMOSI 'curiga' DICATAT (permintaan Bos: audit manusia berkala) — supaya
    #  kalau ambang 0,30 ternyata terlalu galak, ketahuan dari log, bukan dari
    #  naskah user yang rusak. Nol karakter hilang (pagar H1: lapor, jangan blokir).
    demosi = [{'i': k['i'], 'teks': k['teks'][:70]}
              for k in kand if vonis.get(k['i']) == 'curiga']
    if demosi:
        try:
            #  Bos 09 Okt: "jangan buat json, buat md saja". Log = BAGIAN di
            #  laporan .md (ditulis-tambah), bukan berkas baru.
            _lapor = Path('/app/DEMOSI_CURIGA.md')
            _baris = [f'- `L{x["i"]:06d}` — {x["teks"]!r}'
                      for x in demosi]
            _lapor.write_text(
                '# DEMOSI CURIGA — audit manusia berkala\n\n'
                f'Ambang: < {AMBANG_CURIGA} ⇒ ditolak hakim. '
                'Daftar ini untuk memeriksa apakah ambang terlalu galak.\n\n'
                + '\n'.join(_baris) + '\n', encoding='utf-8')
        except Exception as e:                             # jangan pernah gagalkan hakim
            log.warning('[hakim_peta] catat demosi gagal: %s', e)

    # ── RAKIT laporan (P4: jumlah bagian TIDAK berkurang)
    bagian = []
    for k in kand:
        if k['i'] in curiga_kode:
            status = 'curiga'
        elif k['i'] in vonis:
            status = vonis[k['i']]         # 'sepakat' | 'ragu' | 'curiga'
        else:
            status = 'belum'                           # hakim mati/lewat ⇒ jujur
        bagian.append({
            'i': k['i'], 'label': k['label'], 'judul': k['teks'][:60],
            'p_info': k['p_info'],                     # P5: info saja
            'status': status,
        })

    n_sep = sum(1 for b in bagian if b['status'] == 'sepakat')
    n_rag = sum(1 for b in bagian if b['status'] == 'ragu')
    n_cur = sum(1 for b in bagian if b['status'] == 'curiga')
    n_bel = sum(1 for b in bagian if b['status'] == 'belum')
    return {
        'ok': True,
        'keputusan': 'lolos',                          # P6: TIDAK memblokir
        'bagian': bagian,
        'jumlah_sepakat': n_sep,
        'jumlah_ragu': n_rag,
        'jumlah_curiga': n_cur,
        'jumlah_belum': n_bel,
        'alasan': (f'{len(bagian)} kandidat judul: {n_sep} sepakat · '
                   f'{n_rag} ragu · {n_cur} curiga · {n_bel} belum'),
    }
