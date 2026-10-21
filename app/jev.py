"""🛣️ JALAN TOL JEV — SATU-SATUNYA JALUR KE JEV. TIDAK ADA JALAN LAIN.

═══════════════════════════════════════════════════════════════════════════
PERINTAH BOS (09 Okt 2026, verbatim):
   "Pasang apapun itu menjadi jalan tol dan tidak pernah rusak untuk jalur
    jev. Saya tidak mau ada kejadian berulang ulang, kamu buat masalah dan
    salah terus, script kamu atau apapun itu. Tulis jalan tol ini untuk jev
    di semua tempat dan jadi jalan satu satunya, tidak ada jalan lain."
   "Hapus jalur B yang menyesatkan. Kita panggil jev satu satunya jalur SOT"

═══════════════════════════════════════════════════════════════════════════
KENAPA MODUL INI ADA (akar masalah berulang, terukur):

  Jalur B (JALAN MENYESATKAN — DIHAPUS):
     9router:20128/v1/chat/completions   ← endpoint SARAT-UMUM
     ⇒ koneksi "JEV" di 9router → openrouter.ai/api/v1/CHAT/COMPLETIONS
     ⇒ Jev HANYA hidup di /systemone ⇒ endpoint ini MENOLAK Jev
     ⇒ pesannya MENIPU: "HTTP 503" / "invalid_union" / "decisions HTTP 400"
     ⇒ terlihat seperti 9router/Jev rusak, padahal SALAH JALUR

  Jalur SOT (SATU-SATUNYA YANG SAH):
     jembatan 172.17.0.1:8130/v1/chat/completions
     ⇒ teruskan ke openrouter.ai/api/v1/systemone
     ⇒ TERBUKTI HIDUP: 5 pertanyaan · 1 panggilan · 0,7 detik · semua terbaca

═══════════════════════════════════════════════════════════════════════════
JALAN TOL INI MERANGKAP 4 HAL (supaya "tidak pernah rusak"):

  ① JALUR DIPAKSA  — BASE selalu jembatan, TIDAK BISA ditimpa .env ke 9router
  ② SKEMA DIPAKSA  — `periksa_skema()` menolak sebelum kirim (3 tipe, criteria
                     per-tipe). Salah bentuk = TIDAK PERNAH sampai ke Jev.
  ③ SEHAT DICEK    — `cek_siap()` panggil /health jembatan; kalau mati ⇒ LAPOR
                     jelas ("Jev mati, sebab X"), JANGAN diam & kirim sampah
  ④ HASIL DIPERIKSA— balasan wajib memuat nama pertanyaan yang diminta; kalau
                     tidak ⇒ laporkan `gagal_baca`, JANGAN diam-diam kosong

═══════════════════════════════════════════════════════════════════════════
CARA PAKAI (WAJIB — semua modul lewat sini):

    from . import jev
    jawab = jev.tanya(bahan, {'ada_abstrak': {'type': 'noul', 'pertanyaan': '...'}})
    if jawab is None:
        s = jev.cek_siap()          # kenapa? laporkan ke pemakai
        ...
    # jawab['ada_abstrak']['noul']  ← angka 0..1

DILARANG (gerbang `_gerbang_jev_jalantol.py` menahannya):
    · membuat urllib.request.Request sendiri ke endpoint Jev
    · menulis URL jembatan/9router langsung di modul lain
    · mengirim pertanyaan tanpa lewat `jev.tanya()`
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger('jev')

# ═══════════════════════════════════════════════════════════════════════════
# ① JALUR DIPAKSA — jembatan SOT. `${EDUAI_JEV_URL}` hanya boleh menunjuk
#    jembatan; nilai lain (khususnya 9router) DITOLAK KERAS.
# ═══════════════════════════════════════════════════════════════════════════
JEMBATAN_DEFAULT = 'http://172.17.0.1:8130/v1/chat/completions'
JEMBATAN_HEALTH = 'http://172.17.0.1:8130/health'

#  ⚠️ VERSI MODEL — PIN, JANGAN PAKAI ALIAS (`jev-latest`/`jev-preview`).
#     Ambang kita (satpam 0,80 · ragu 0,95) disetel untuk SATU versi; alias
#     berpindah sendiri saat rilis baru ⇒ ambang jadi tidak sah tanpa ada yang
#     mengubahnya. Resmi: "pin that version's ID instead of the alias."
#
#  📌 1.14 SUDAH DIUJI 21 Okt 2026 — TIDAK DINAIKKAN (SOT §16).
#     34 pertanyaan · 3 naskah Indonesia ⇒ 34/34 jawaban IDENTIK dengan 1.13,
#     Δ noul rata 0,001–0,018; 1.14 malah lebih goyah di naskah sulit
#     (5/9 vs 3/9 berubah); biaya & token identik.
#     Kapan naik: ada naskah asing nyata · butuh tipe `box` · 1.13 mendekati
#     pensiun (≈13 Des 2026). Nama yang HIDUP di jembatan: 'typesafe/jev-1.14'.
MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.13'

#  Tanda jalur MENYESATKAN — kalau muncul, tolak (jangan diam-diam jalan).
_TANDA_SESAT = (':20128', '9router:', '/v1/chat/completions')  # dicek bersama host


def _jalur() -> str:
    """URL jembatan SOT. Menolak KERAS jalur menyesatkan (9router)."""
    url = (os.getenv('EDUAI_JEV_URL') or JEMBATAN_DEFAULT).strip()
    # 9router:20128 = jalur B (menyesatkan) — TOLAK.
    if ':20128' in url or '9router' in url:
        log.error('[jev] ⛔ EDUAI_JEV_URL menunjuk 9router (JALUR B MENYESATKAN) '
                  '— dipaksa ke jembatan SOT: %s', JEMBATAN_DEFAULT)
        return JEMBATAN_DEFAULT
    return url


BASE = _jalur()

# ── kunci: jembatan TIDAK butuh kunci (ia ambil sendiri dari DB 9router).
#    Kunci hanya dipakai kalau ada deployment khusus; default kosong.
KUNCI = (os.getenv('EDUAI_JEV_KEY') or '').strip()
BATAS_DETIK = float(os.getenv('EDUAI_JEV_TIMEOUT') or '90')

# ═══════════════════════════════════════════════════════════════════════════
# ② SKEMA DIPAKSA — aturan resmi jev-1.13 (terukur ke /systemone, 07 Okt 2026)
# ═══════════════════════════════════════════════════════════════════════════
TIPE_SAH = ('noul', 'choice', 'score')


def periksa_skema(pertanyaan: Any) -> list[str]:
    """Kembalikan daftar keluhan. KOSONG = skema sah.

    ATURAN (jangan diubah tanpa ukur ulang ke /systemone):
      · `questions` WAJIB objek {nama: {...}} — BUKAN list
      · `type` hanya: noul · choice · score
      · `instructions` WAJIB ada (teks bebas) — nama field RESMI Jev.
        (`pertanyaan` diterima sebagai alias supaya kode lama tetap jalan)
      · `criteria` PER-TIPE:
           noul   → OBJEK {true: deskripsi, false: deskripsi} — WAJIB `object`
                    kalau ada (dokumen RESMI `rerank`/`autoformat`: NoulCriteria)
                    ⚠️ TERUKUR 09 Okt 2026 ke jembatan: noul + criteria OBJEK
                    = OK (noul 0,79) · noul + criteria STRING = HTTP 502 Zod
                    `expected: "object"` ⇒ yang salah BENTUKNYA, bukan fieldnya.
                    ✅ BOLEH ada · DILARANG kalau bukan objek.
           choice → OBJEK {nama_opsi: deskripsi}
           score  → ARRAY ['tingkat 0', 'tingkat 1', …] (2–10 tingkat)
    """
    keluhan: list[str] = []
    if not isinstance(pertanyaan, dict) or not pertanyaan:
        return ['`questions` WAJIB objek {nama: {...}} berisi minimal 1 pertanyaan']
    for nama, q in pertanyaan.items():
        if not isinstance(q, dict):
            keluhan.append(f'{nama}: isi pertanyaan WAJIB objek')
            continue
        tipe = q.get('type')
        if tipe not in TIPE_SAH:
            keluhan.append(f'{nama}: type {tipe!r} tidak sah '
                           f'(hanya {"/".join(TIPE_SAH)})')
            continue
        if not str(q.get('instructions') or q.get('pertanyaan')
                   or q.get('question') or '').strip():
            keluhan.append(f'{nama}: wajib punya `instructions` (teks pertanyaan)')
        ada_crit = 'criteria' in q
        if tipe == 'noul':
            #  ✅ BOLEH (dan dianjurkan RESMI) — TAPI WAJIB OBJEK {true,false}.
            #  Terukur 09 Okt 2026: criteria STRING ⇒ 502 Zod `expected object`.
            if ada_crit:
                c = q.get('criteria')
                if not isinstance(c, dict):
                    keluhan.append(f'{nama}: noul `criteria` WAJIB OBJEK '
                                   '{{"true": …, "false": …}} — bentuk lain '
                                   '(string/list) ⇒ 502 semu')
                elif not ({'true', 'false'} & set(c.keys())):
                    keluhan.append(f'{nama}: noul `criteria` WAJIB memuat kunci '
                                   '`true` dan/atau `false`')
        elif tipe == 'choice':
            if not ada_crit or not isinstance(q.get('criteria'), dict):
                keluhan.append(f'{nama}: choice WAJIB `criteria` OBJEK '
                               '{{nama_opsi: deskripsi}}')
        elif tipe == 'score':
            c = q.get('criteria')
            if not isinstance(c, list) or not (2 <= len(c) <= 10):
                keluhan.append(f'{nama}: score WAJIB `criteria` ARRAY '
                               'berisi 2–10 tingkat')
    return keluhan


class SkemaSalah(ValueError):
    """Dilempar SEBELUM kirim — supaya salah bentuk tidak pernah sampai Jev."""


# ═══════════════════════════════════════════════════════════════════════════
# ③ SEHAT DICEK — jembatan hidup?
# ═══════════════════════════════════════════════════════════════════════════
def cek_siap() -> dict:
    """Cek jembatan Jev hidup. SELALU kembalikan dict (tidak pernah melempar).

    {'siap': bool, 'sebab': str, 'kunci': str|None}
    """
    try:
        with urllib.request.urlopen(JEMBATAN_HEALTH, timeout=15) as r:
            h = json.loads(r.read().decode())
        if h.get('ok'):
            return {'siap': True, 'sebab': 'jembatan hidup',
                    'kunci': h.get('kunci')}
        return {'siap': False, 'sebab': f'jembatan balas tidak ok: {h}',
                'kunci': h.get('kunci')}
    except Exception as e:
        return {'siap': False,
                'sebab': f'jembatan tidak bisa dihubungi ({type(e).__name__})',
                'kunci': None}


# ═══════════════════════════════════════════════════════════════════════════
# TANYA — satu-satunya pintu ke Jev
# ═══════════════════════════════════════════════════════════════════════════
def tanya(bahan: str, pertanyaan: dict, model: str | None = None) -> dict | None:
    """Tanya Jev lewat JALAN TOL. Kembalikan dict jawaban atau None.

    TIDAK PERNAH melempar galat jaringan (pagar P1) — pemanggil SELALU bisa
    lanjut. Yang MELEMPAR hanya `SkemaSalah`, karena itu salah PROGRAMMER
    (harus diperbaiki, bukan ditelan).

    Balasan: {'<nama pertanyaan>': {'noul'|'choice'|'score': ..., 'confidence': ...}}
    """
    # ② skema diperiksa SEBELUM kirim — salah bentuk tidak pernah sampai Jev
    keluhan = periksa_skema(pertanyaan)
    if keluhan:
        raise SkemaSalah('Skema pertanyaan Jev salah — perbaiki dulu: '
                         + ' | '.join(keluhan))

    if not isinstance(bahan, str) or not bahan.strip():
        log.warning('[jev] bahan KOSONG — tidak dikirim (cegah 503 semu)')
        return None

    #  Normalisasi: `pertanyaan` (alias kita) → `instructions` (field RESMI Jev)
    q_kirim = {}
    for nama, q in pertanyaan.items():
        q2 = dict(q)
        if 'pertanyaan' in q2 and 'instructions' not in q2:
            q2['instructions'] = q2.pop('pertanyaan')
        q_kirim[nama] = q2

    body = {
        'model': model or MODEL_DEFAULT,
        'messages': [{'role': 'user',
                      'content': json.dumps({'state': bahan,
                                             'questions': q_kirim})}],
    }
    header = {'Content-Type': 'application/json'}
    if KUNCI:
        header['Authorization'] = f'Bearer {KUNCI}'
    req = urllib.request.Request(BASE, data=json.dumps(body).encode(),
                                 headers=header)
    try:
        with urllib.request.urlopen(req, timeout=BATAS_DETIK) as r:
            mentah = r.read().decode()
    except urllib.error.HTTPError as e:                        # P1: telan
        pesan = ''
        try:
            pesan = e.read().decode()[:300]
        except Exception:
            pass
        log.warning('[jev] Jev HTTP %s: %s', e.code, pesan)
        return None
    except Exception as e:                                     # P1: telan
        log.warning('[jev] Jev tidak bisa dihubungi: %s: %s', type(e).__name__, e)
        return None

    return urai(mentah, diminta=set(pertanyaan))


def urai(mentah: str, diminta: set | None = None) -> dict | None:
    """Urai balasan jembatan. Balasan bisa dibungkus (pilihan / message.content).

    ④ HASIL DIPERIKSA: kalau `diminta` diberi dan nama pertanyaan tidak ada
       di balasan ⇒ log TERANG (jangan diam-diam kosong).
    """
    isi: Any = None
    try:
        d = json.loads(mentah)
        # jembatan balas {'choices':[{'message':{'content': '<json>'}}]} atau
        # langsung {'<nama>': {...}}
        if isinstance(d, dict) and 'choices' in d:
            konten = ((d['choices'] or [{}])[0].get('message') or {}).get('content')
            isi = json.loads(konten) if isinstance(konten, str) else konten
        else:
            isi = d
    except Exception:
        try:
            isi = _json_awal(mentah)
        except Exception:
            isi = None

    if not isinstance(isi, dict) or not isi:
        log.warning('[jev] balasan tidak terbaca (%d byte)', len(mentah or ''))
        return None

    #  jawaban bisa bersarang: {nama: {choice:{...}}} atau {nama: {noul: 0.9}}
    if diminta:
        ada = set(isi)
        hilang = diminta - ada
        if hilang and len(hilang) == len(diminta):
            # mungkin bersarang satu tingkat
            for v in isi.values():
                if isinstance(v, dict) and (diminta & set(v)):
                    isi = v
                    break
    return isi


def _json_awal(teks: str) -> Any:
    """Ambil objek JSON pertama dari teks (balasan kadang berbalut penjelasan)."""
    t = teks.strip()
    if t.startswith('```'):
        t = t.strip('`').strip()
        if t[:4].lower() == 'json':
            t = t[4:].strip()
    mulai = t.find('{')
    while mulai != -1:
        for akhir in range(len(t), mulai, -1):
            try:
                return json.loads(t[mulai:akhir])
            except Exception:
                continue
        mulai = t.find('{', mulai + 1)
    raise ValueError('tidak ada JSON di balasan')


# ── nama singkat supaya pemanggil lama tetap jalan (tanya_bebas lama)
def tanya_bebas(bahan: str, pertanyaan: dict) -> dict | None:
    """Alias kompatibel: `tanya_bebas(bahan, questions)` — TANPA arg `peta`."""
    return tanya(bahan, pertanyaan)
