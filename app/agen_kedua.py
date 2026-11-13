"""AGEN KEDUA — pembaca kedua rantai 3 langkah (Jev → Hakim → agen kedua).

Perintah Bos 11 Nov 2026 (Gas): naskah baru live TIDAK boleh butuh admin
melabeli. Rantai: Jev melabeli → Hakim menandai yang ragu → agen kedua
membaca baris yang ditandai dengan KONTEKS LEBAR dan memutuskan. Bila agen
kedua sepakat dengan Jev, label Jev dipakai. Bila beda (bukan soal judul
bab), keputusan agen kedua yang dipakai. Antrean manusia HANYA untuk yang
benar-benar buntu: naskah tanpa penanda bab sama sekali, atau agen kedua
dan Jev beda soal judul bab.

PENTING — agen kedua HARUS beda model/cara baca dari Jev 1.14, supaya tidak
mengulang salah yang sama:
  · Jalur UTAMA (pilot + pemakaian dari VM): model instruksi umum lewat
    jalur OpenRouter langsung, model pin `google/gemini-2.5-flash`
    (pilihan 11 Nov 2026: murah, JSON andal, 1 juta konteks). Penanya
    OpenRouter tinggal di `_sketsa/agen_kedua_openrouter.py` (perkakas
    pilot, BUKAN kode produksi) dan DISUNTIK lewat parameter `penanya` —
    modul ini tidak pernah memegang kunci OpenRouter.
  · Jalur PRODUKSI (di dalam container): combo umum 9router yang diatur
    Bos dari panel (BUKAN Jev — Jev hanya hidup di jembatan systemone).
    Model yang melayani = apa pun yang combo layani saat itu, DICATAT per
    panggilan dari balasan (`model` balasan). Belum teruji live dari
    container dalam tugas ini — wajib uji asap 1 panggilan sebelum saklar
    dinyalakan di produksi (lihat RANTAI_3_LANGKAH.md).
  · Rantai PRODUKSI (13 Nov 2026, Gas Bos): combo 9router dulu, gagal ->
    Apinex (model gratis free/gemini-3.8-flash, kaki KEDUA), gagal ->
    TokenHarbor (fallback lama, kaki KETIGA), gagal -> None (antrean).
    Kaki Apinex dilewati bila EDUAI_APINEX_KEY kosong — rantai tetap
    jalan tanpa kunci itu.
  · Pembanding CADANGAN (bukan pilihan utama): Jev 1.13 lewat jalan tol
    (`tanya_pembanding_113`). Dipakai HANYA bila model umum tidak bisa
    dipakai live (kredit/akses), dan pemakaiannya DICATAT di hasil
    (`model` = 1.13), tidak pernah diam-diam.

PAGAR:
  · Saklar mati `EDUAI_AGEN_KEDUA_AKTIF=0` (bawaan MATI, seperti kill-switch
    Hakim). Mati ⇒ `buat_pendapat_kedua_fn()` mengembalikan None ⇒ perilaku
    sama persis dengan v11 (Lapis 2 dilewati, nol panggilan tambahan).
  · GAGAL = None (bukan label tebakan): jaringan mati, balasan bukan JSON,
    label di luar 4 sah, confidence bukan angka ⇒ jawaban kedua dianggap
    tidak ada ⇒ baris masuk antrean manusia (aturan `pendapat_kedua`).
  · Suara Jev TIDAK ditunjukkan ke agen kedua (jawaban independen — kalau
    ditunjukkan, agen kedua tinggal meniru). Parameter `suara` diterima
    demi kesesuaian antarmuka `pendapat_kedua_fn`, tapi tidak masuk prompt.
  · Modul ini TIDAK PERNAH memanggil Jev kecuali lewat `tanya_pembanding_113`
    (pembanding cadangan, lewat jalan tol `jev.tanya` — bukan jalur sendiri).
  · Gerbang jalan tol Jev: modul ini tidak memuat URL endpoint Jev sebagai
    kode aktif (pola gerbang D1). Jalur produksi memakai `app.config`
    (ROUTER_BASE/ROUTER_KEY/AI_MODEL) seperti `app.ai`.
  · Gerbang setelan produksi: payload chat/completions di sini WAJIB memuat
    `enable_thinking: False` (keputusan Bos 29 Sep 2026, sama seperti
    `app.ai`) — agen kedua bukan model berpikir.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger('agen_kedua')

# ── label sah (sama seperti label manusia) ─────────────────────────────────
LABEL_SAH = ('bab', 'subbab', 'paragraf', 'biasa')

# ── saklar + setelan (env; bawaan MATI) ─────────────────────────────────────
#    EDUAI_AGEN_KEDUA_AKTIF=1  → rantai hidup (pabrik mengembalikan fn).
#    EDUAI_AGEN_KEDUA_TRANSPORT=fallback|router9|openrouter (bawaan
#    fallback: 9router dulu, gagal -> Apinex, gagal -> OpenRouter;
#    putusan Bos 13 Nov 2026 — Apinex urutan kedua, TokenHarbor ketiga).
#    Transport openrouter/fallback memakai EDUAI_FALLBACK_BASE/KEY dari
#    app.config (sama seperti app.ai) — kunci dibaca dari env, modul ini
#    tidak memegang kunci. Penanya yang disuntik hanya untuk pilot/uji.
#    Kaki Apinex memakai EDUAI_APINEX_BASE/KEY (env sendiri); kunci
#    kosong = kaki dilewati, bukan galat.
#    EDUAI_AGEN_KEDUA_MODEL  → nama model untuk penanya OpenRouter
#    (bawaan google/gemini-2.5-flash; penanya yang membacanya).
MODEL_OPENROUTER_BAWAAN = 'google/gemini-2.5-flash'
MODEL_OPENROUTER_CADANGAN = 'openai/gpt-4o-mini'
MODEL_JEV_113 = 'SATPAM/typesafe/jev-1.13'
BATAS_DETIK = float(os.getenv('EDUAI_AGEN_KEDUA_TIMEOUT') or '60')
# Percobaan pertama di mode fallback (combo 9router) dibatasi singkat
# supaya tidak menggantung: combo yang providernya mati terbukti
# timeout 60 dtk (uji asap 12 Nov 2026), bukan gagal cepat.
BATAS_DETIK_R9 = float(os.getenv('EDUAI_AGEN_KEDUA_TIMEOUT_R9') or '20')
# Batas jawaban 2048 (dulu 512): ukur live 13 Nov 2026 — 12 dari 39
# panggilan fallback terpotong (finish=length) tepat di 512, model
# menjawab bertele-tele sebelum JSON-nya. 2048 = 4x ruang; penagihan
# mengikuti token yang benar dipakai, bukan batasnya. Dipakai KETIGA
# jalur (combo 9router, Apinex, dan fallback) — ketiganya berbagi
# konstanta ini.
MAKS_TOKEN_JAWAB = 2048

# Kaki KEDUA rantai (13 Nov 2026, Gas Bos): Apinex, model gratis
# 'free/gemini-3.8-flash' — model yang SAMA dengan fallback TokenHarbor
# supaya keputusan konsisten; biaya 0 (jatah harian Apinex, bukan saldo).
# Base + kunci dari env EDUAI_APINEX_BASE / EDUAI_APINEX_KEY. Kunci
# kosong = kaki dilewati diam-diam (rantai tetap jalan: combo ->
# TokenHarbor); deploy tanpa kunci TIDAK BOLEH merusak apa pun.
APINEX_BASE_BAWAAN = 'https://api.apinex.bond/v1'
MODEL_APINEX_BAWAAN = 'free/gemini-3.8-flash'

# ── log keputusan (in-memory; pabrik menempelkan salinan ke fn.log) ─────────
LOG_KEPUTUSAN: list[dict[str, Any]] = []


def aktif() -> bool:
    """Saklar mati rantai. Bawaan MATI; nyala hanya bila env = '1'."""
    return (os.getenv('EDUAI_AGEN_KEDUA_AKTIF') or '0').strip() == '1'


def transport() -> str:
    """Transport agen kedua: 'fallback' (bawaan), 'router9', 'openrouter'.

    fallback = coba combo 9router dulu, gagal -> Apinex, gagal ->
    OpenRouter/TokenHarbor (putusan Bos 13 Nov 2026: Apinex urutan
    kedua, TokenHarbor ketiga).
    """
    t = (os.getenv('EDUAI_AGEN_KEDUA_TRANSPORT') or 'fallback').strip().lower()
    return t if t in ('router9', 'openrouter', 'fallback') else 'fallback'


# ── aturan label manusia (patokan yang SAMA, disalin verbatim ke prompt) ────
ATURAN_LABEL = (
    'bab = judul bab (mis. BAB I PENDAHULUAN, CHAPTER II, I. PENDAHULUAN). '
    'subbab = judul bagian di dalam bab, ATAU penomoran yang MENGEPALAI blok '
    'penjelasan sendiri (mis. "2.1 Latar Belakang" diikuti uraian). '
    'paragraf = kalimat isi biasa, TERMASUK kalimat pertama di bawah '
    'judul/butir. '
    'biasa = BUKAN ketiganya: penomoran di dalam enumerasi sebaris, salinan '
    'sistematika/daftar isi, running head (judul bab yang terulang di tengah '
    'naskah), fragmen tabel, header output (mis. SPSS), sitasi, atau nomor '
    'halaman.'
)


# ── v14: daftar periksa TAJAM untuk baris kandidat bab (11 Nov 2026) ──────
#    Salah terbesar v11/v13: 42 baris benarnya `biasa` dilabeli `bab`
#    (salinan sistematika/daftar isi). Prompt lama hanya berkata "salinan
#    ... adalah biasa" tanpa sinyal yang bisa diperiksa; uji live v13 pada
#    3 baris bab yang ditandai: agen benar 1/3. Daftar ini memberi sinyal
#    konkret yang bisa dicek dari baris + konteksnya.
ATURAN_BAB_TAJAM = (
    'Sebelum menjawab "bab", PERIKSA dulu lima hal ini — bila SATU saja '
    'cocok, jawab "biasa", BUKAN "bab": '
    '(1) baris diawali ":" (contoh ": PENGANTAR" — itu ekor judul yang '
    'terbelah, bukan judul); '
    '(2) baris hanya "BAB I"/"Bab II"/"CHAPTER I" TELANJANG tanpa judul, '
    'sementara di dekatnya (dalam beberapa baris) ada uraian sistematika '
    'seperti "Bab ini", "Pada bab ini", "terdiri dari", atau "Berisi '
    'tentang" — itu salinan SISTEMATIKA PENULISAN, bukan bab asli; '
    '(3) baris mengandung nomor halaman di ujungnya (contoh ".... 1", '
    '".. 28", "???? 4", titik-titik panjang diikuti angka/romawi) — itu '
    'entri DAFTAR ISI, bukan judul bab; '
    '(4) baris adalah judul daftar isi itu sendiri ("TABLE OF CONTENS", '
    '"DAFTAR ISI") atau judul bab yang terulang berurutan rapat '
    '(BAB I sampai BAB V dalam belasan baris) — itu daftar isi, bukan '
    'badan naskah; '
    '(5) baris diawali penanda huruf kecil ("a)", "b.", "c)") dan diikuti '
    'butir huruf lain — itu butir daftar, bukan subbab. '
    'Sebaliknya, "bab" HANYA bila baris adalah judul bab ASLI di badan '
    'naskah: penanda bab + judul bersih, tanpa nomor halaman, dan tidak '
    'berada dalam daftar salinan. Penanda huruf yang MENGEPALAI blok '
    'penjelasan (judul pendek lalu uraian panjang) adalah "subbab"; '
    'penanda huruf yang kalimat definisi lengkap ("... yaitu ...") adalah '
    '"paragraf".'
)


def _prompt(teks_baris: str, konteks: dict | None) -> str:
    """Prompt klasifikasi 4 label dengan konteks lebar (Bahasa Indonesia).

    `konteks` (dari wiring Lapis 2): {'sebelum': [...], 'sesudah': [...],
    'judul_bab_terdekat': str|None}. Bila konteks kosong, hanya barisnya.
    """
    ctx = konteks or {}
    sebelum = [b for b in (ctx.get('sebelum') or []) if (b or '').strip()]
    sesudah = [b for b in (ctx.get('sesudah') or []) if (b or '').strip()]
    bab = (ctx.get('judul_bab_terdekat') or '').strip()
    bagian = [
        'Kamu membaca satu baris dari sebuah skripsi/tesis berbahasa '
        'Indonesia (kadang Inggris) dan menentukan jenis baris itu.',
        'Jawab HANYA dengan satu objek JSON singkat — tanpa kata lain '
        'sebelum atau sesudahnya, tanpa penjelasan, tanpa pembuka, tanpa '
        'uraian: {"label": "...", "confidence": 0.0-1.0, "alasan": "..."}. '
        'Label HANYA salah satu: bab, subbab, paragraf, biasa. Confidence '
        '= keyakinanmu 0 sampai 1 (di bawah 0,5 berarti kamu tidak yakin). '
        'Alasan MAKSIMAL SATU kalimat pendek (maksimal 15 kata).',
        'Aturan: ' + ATURAN_LABEL,
    ]
    if bab:
        bagian.append('Judul bab terdekat di atas baris ini: ' + bab)
    if sebelum:
        bagian.append('Baris SEBELUM baris ini:\n' + '\n'.join(sebelum))
    bagian.append('BARIS YANG DINILAI:\n' + (teks_baris or '').strip())
    if sesudah:
        bagian.append('Baris SESUDAH baris ini:\n' + '\n'.join(sesudah))
    bagian.append(
        'Perhatikan: baris yang bentuknya seperti judul TAPI hanya salinan '
        'daftar isi/sistematika, atau judul bab yang terulang sebagai running '
        'head, adalah "biasa", BUKAN "bab". Baris penomoran yang hanya butir '
        'di tengah kalimat adalah "biasa", BUKAN "subbab".')
    bagian.append('Daftar periksa sebelum menjawab "bab": ' + ATURAN_BAB_TAJAM)
    bagian.append('INGAT: keluaranmu HANYA satu objek JSON singkat. Jangan '
                  'menulis apa pun selain JSON itu.')
    return '\n\n'.join(bagian)


def _urai_jawaban(mentah: str) -> dict | None:
    """Ambil objek JSON pertama dari balasan, validasi label + confidence.

    Gagal (bukan JSON / label tidak sah / confidence bukan angka) ⇒ None
    (jawaban kedua dianggap tidak ada — baris masuk antrean, bukan ditebak).
    """
    if not isinstance(mentah, str) or not mentah.strip():
        return None
    try:
        awal = mentah.find('{')
        if awal < 0:
            return None
        isi = json.JSONDecoder().raw_decode(mentah[awal:])[0]
    except Exception:
        return None
    if not isinstance(isi, dict):
        return None
    label = isi.get('label')
    conf = isi.get('confidence')
    if label not in LABEL_SAH:
        return None
    if not isinstance(conf, (int, float)) or isinstance(conf, bool):
        return None
    conf = max(0.0, min(1.0, float(conf)))
    alasan = isi.get('alasan')
    return {'label': label, 'confidence': conf,
            'alasan': alasan if isinstance(alasan, str) else ''}


def _urai_balasan_chat(mentah: str) -> tuple[str, str]:
    """Urai balasan /chat/completions → (konten, model_melayani).

    Menangani bentuk SSE (`data: {...} data: [DONE]`) maupun JSON polos,
    dengan whitespace di depan (pelajaran 17 Sep 2026).
    """
    i = mentah.find('data: [DONE]')
    body = mentah[:i] if i > 0 else mentah
    body = body.strip()
    if body.startswith('data:'):
        body = body.split('data:', 1)[1].strip()
    awal = body.find('{')
    if awal < 0:
        raise RuntimeError('balasan bukan JSON')
    j = json.JSONDecoder().raw_decode(body[awal:])[0]
    ch = (j.get('choices') or [{}])[0]
    konten = (ch.get('message') or {}).get('content')
    if not konten:
        raise RuntimeError('konten kosong dari model')
    if ch.get('finish_reason') == 'length':
        raise RuntimeError('jawaban terpotong (finish=length)')
    return konten, j.get('model') or ''


def _panggil_router9(prompt: str, timeout: float | None = None) -> tuple[str, str]:
    """Transport PRODUKSI: combo umum 9router (model diatur Bos dari panel).

    Memakai setelan yang SAMA dengan `app.ai` (ROUTER_BASE/ROUTER_KEY/
    AI_MODEL dari `app.config`). Model yang melayani dicatat dari balasan.
    """
    from app.config import ROUTER_BASE, ROUTER_KEY, AI_MODEL

    body = {
        'model': AI_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': MAKS_TOKEN_JAWAB,
        'temperature': 0.2,
        # Keputusan Bos 29 Sep 2026: agen kedua bukan model berpikir.
        'enable_thinking': False,
    }
    header = {'Content-Type': 'application/json'}
    if ROUTER_KEY:
        header['Authorization'] = f'Bearer {ROUTER_KEY}'
    req = urllib.request.Request(
        ROUTER_BASE.rstrip('/') + '/chat/completions',
        data=json.dumps(body).encode(), headers=header)
    try:
        with urllib.request.urlopen(req, timeout=timeout or BATAS_DETIK) as r:
            mentah = r.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'combo HTTP {e.code}: {e.read().decode()[:200]}')
    except Exception as e:
        raise RuntimeError(f'combo tidak bisa dihubungi: {type(e).__name__}: {e}')
    return _urai_balasan_chat(mentah)


def _panggil_openrouter(prompt: str, timeout: float | None = None) -> tuple[str, str]:
    """Transport CADANGAN produksi: OpenRouter langsung (fallback).

    Memakai EDUAI_FALLBACK_BASE/KEY dari `app.config` (sama seperti
    `app.ai` jalur 2) — kunci dibaca dari env, tidak ditulis di kode.
    Model dari EDUAI_AGEN_KEDUA_MODEL_FALLBACK (bawaan 'gemini-3.8-flash',
    nama TokenHarbor — FALLBACK_BASE adalah tokenharbor.ai, bukan
    openrouter.ai, jadi nama 'google/...' ditolak 404).
    """
    from app.config import FALLBACK_BASE, FALLBACK_KEY

    model = (os.getenv('EDUAI_AGEN_KEDUA_MODEL_FALLBACK')
             or 'gemini-3.8-flash').strip()
    if not FALLBACK_BASE or not FALLBACK_KEY:
        raise RuntimeError('OpenRouter tidak terpasang '
                           '(EDUAI_FALLBACK_BASE/KEY kosong)')
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': MAKS_TOKEN_JAWAB,
        'temperature': 0.2,
        # Keputusan Bos 29 Sep 2026: agen kedua bukan model berpikir.
        'enable_thinking': False,
        'response_format': {'type': 'json_object'},
    }
    header = {'Content-Type': 'application/json',
              'Authorization': f'Bearer {FALLBACK_KEY}'}
    req = urllib.request.Request(
        FALLBACK_BASE.rstrip('/') + '/chat/completions',
        data=json.dumps(body).encode(), headers=header)
    try:
        with urllib.request.urlopen(req, timeout=timeout or BATAS_DETIK) as r:
            mentah = r.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'OpenRouter HTTP {e.code}: {e.read().decode()[:200]}')
    except Exception as e:
        raise RuntimeError(f'OpenRouter tidak bisa dihubungi: {type(e).__name__}: {e}')
    return _urai_balasan_chat(mentah)


def _panggil_apinex(prompt: str, timeout: float | None = None) -> tuple[str, str]:
    """Kaki KEDUA rantai produksi: Apinex (model gratis, jatah harian).

    POST {EDUAI_APINEX_BASE}/chat/completions, model 'free/gemini-3.8-flash'
    — model yang SAMA dengan fallback TokenHarbor supaya keputusan
    konsisten; biaya 0 (jatah harian Apinex, bukan saldo). Kunci dari env
    EDUAI_APINEX_KEY; kunci kosong = kaki dilewati (RuntimeError
    'apinex tidak terpasang'), BUKAN galat yang menghentikan rantai.
    """
    base = (os.getenv('EDUAI_APINEX_BASE') or APINEX_BASE_BAWAAN).strip()
    key = (os.getenv('EDUAI_APINEX_KEY') or '').strip()
    model = (os.getenv('EDUAI_AGEN_KEDUA_MODEL_APINEX')
             or MODEL_APINEX_BAWAAN).strip()
    if not key:
        raise RuntimeError('apinex tidak terpasang '
                           '(EDUAI_APINEX_KEY kosong)')
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': MAKS_TOKEN_JAWAB,
        'temperature': 0.2,
        # Keputusan Bos 29 Sep 2026: agen kedua bukan model berpikir.
        'enable_thinking': False,
        'response_format': {'type': 'json_object'},
    }
    header = {'Content-Type': 'application/json',
              'Authorization': f'Bearer {key}'}
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions',
        data=json.dumps(body).encode(), headers=header)
    try:
        with urllib.request.urlopen(req, timeout=timeout or BATAS_DETIK) as r:
            mentah = r.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'apinex HTTP {e.code}: {e.read().decode()[:200]}')
    except Exception as e:
        raise RuntimeError(f'apinex tidak bisa dihubungi: {type(e).__name__}: {e}')
    return _urai_balasan_chat(mentah)


def _coba_transport(nama: str, prompt: str) -> dict | None:
    """Satu percobaan transport -> jawab valid, atau None bila gagal.

    Gagal = tidak bisa dihubungi / HTTP galat / balasan bukan JSON /
    label tidak sah / model yang melayani adalah Jev (bukan model umum).
    """
    try:
        if nama == 'openrouter':
            konten, model_layani = _panggil_openrouter(prompt)
        elif nama == 'apinex':
            konten, model_layani = _panggil_apinex(prompt,
                                                   timeout=BATAS_DETIK_R9)
        else:
            konten, model_layani = _panggil_router9(prompt, timeout=BATAS_DETIK_R9)
    except Exception as e:
        log.warning('[agen_kedua] %s gagal: %s', nama, e)
        return None
    if 'jev' in (model_layani or '').lower():
        log.warning('[agen_kedua] %s melayani model Jev (%s), bukan model umum',
                    nama, model_layani)
        return None
    jawab = _urai_jawaban(konten)
    if jawab is None:
        log.warning('[agen_kedua] %s balasan tidak terbaca: %r', nama, konten[:160])
        return None
    jawab['model'] = model_layani or ''
    jawab['transport'] = nama
    return jawab


def tanya_agen_kedua(teks_baris: str, konteks: dict | None = None,
                     suara: list | None = None, penanya=None,
                     model: str | None = None) -> dict | None:
    """Tanya agen kedua: label + confidence + alasan, atau None bila gagal.

    `suara` (suara Jev) diterima demi antarmuka, tapi SENGAJA tidak masuk
    prompt — jawaban kedua harus independen, bukan meniru Jev.
    `penanya` = callable(prompt) -> (konten, model_melayani) yang disuntik
    (dipakai pilot OpenRouter + uji offline). Tanpa penanya, dipakai jalur
    produksi: transport dari `transport()` — 'fallback' (bawaan: 9router
    dulu, gagal -> Apinex, gagal -> OpenRouter), 'router9', atau
    'openrouter'.
    GAGAL APAPUN ⇒ None (bukan label tebakan).
    """
    prompt = _prompt(teks_baris, konteks)
    if penanya is not None:
        try:
            konten, model_layani = penanya(prompt)
        except Exception as e:
            log.warning('[agen_kedua] panggilan gagal: %s', e)
            return None
        jawab = _urai_jawaban(konten)
        if jawab is None:
            log.warning('[agen_kedua] balasan tidak terbaca: %r', konten[:160])
            return None
        jawab['model'] = model_layani or (model or '')
        jawab['transport'] = 'openrouter'
        return jawab
    t = transport()
    urutan = {'router9': ('router9',),
              'openrouter': ('openrouter',)}.get(
                  t, ('router9', 'apinex', 'openrouter'))
    for nama in urutan:
        jawab = _coba_transport(nama, prompt)
        if jawab is not None:
            return jawab
    return None


def tanya_pembanding_113(teks_baris: str, konteks: dict | None = None) -> dict | None:
    """Pembanding CADANGAN (bukan pilihan utama): Jev 1.13 lewat jalan tol.

    Dipakai HANYA bila model umum tidak bisa dipakai live (kredit/akses).
    Pemakaiannya WAJIB dicatat di hasil (`model` = 1.13) — tidak pernah
    diam-diam. 1.13 pensiun ≈13 Des 2026.
    """
    from app import jev

    ctx = konteks or {}
    bahan = '\n'.join(
        [b for b in (ctx.get('sebelum') or []) if (b or '').strip()]
        + [(teks_baris or '').strip()]
        + [b for b in (ctx.get('sesudah') or []) if (b or '').strip()])
    pertanyaan = {
        'label_baris': {
            'type': 'choice',
            'instructions': (
                'Baris tengah di bawah ini jenis apa dalam skripsi? '
                + ATURAN_LABEL),
            'criteria': {
                'bab': 'judul bab',
                'subbab': 'judul bagian di dalam bab / penomoran yang '
                          'mengepalai blok penjelasan sendiri',
                'paragraf': 'kalimat isi biasa',
                'biasa': 'bukan ketiganya (enumerasi, salinan daftar isi, '
                         'running head, fragmen tabel, sitasi)'},
        },
    }
    try:
        jawab = jev.tanya(bahan, pertanyaan, model=MODEL_JEV_113)
    except Exception as e:
        log.warning('[agen_kedua] pembanding 1.13 gagal: %s', e)
        return None
    if not jawab:
        return None
    isi = jawab.get('label_baris') or {}
    pilihan = isi.get('choice')
    conf = isi.get('confidence')
    if pilihan not in LABEL_SAH or not isinstance(conf, (int, float)):
        return None
    return {'label': pilihan, 'confidence': max(0.0, min(1.0, float(conf))),
            'alasan': 'pembanding Jev 1.13 (cadangan)',
            'model': 'typesafe/jev-1.13', 'transport': 'jev-1.13'}


def buat_pendapat_kedua_fn(penanya=None, model: str | None = None):
    """Pabrik fn Lapis 2: fn(idx, teks_baris, suara, p, konteks=None).

    Saklar MATI ⇒ None (perilaku v11, nol panggilan). Saklar NYALA ⇒ fn
    yang memanggil agen kedua per baris yang ditandai Hakim (v13; warisan
    v12: per baris goyang) dan mencatat tiap keputusan
    ke `fn.log` (list dict) + `LOG_KEPUTUSAN`. `penanya` yang disuntik
    dipakai sebagai transport; tanpa penanya dipakai combo 9router.
    """
    if not aktif():
        return None

    def fn(idx, teks_baris, suara, p, konteks=None):
        jawab = tanya_agen_kedua(teks_baris, konteks, suara,
                                  penanya=penanya, model=model)
        rekaman = {
            'idx': idx,
            'teks': (teks_baris or '')[:160],
            'suara_jev': list(suara or []),
            'label_kedua': jawab['label'] if jawab else None,
            'confidence': jawab['confidence'] if jawab else None,
            'alasan': jawab['alasan'] if jawab else '',
            'model': jawab['model'] if jawab else '',
            'transport': jawab['transport'] if jawab else '',
        }
        fn.log.append(rekaman)
        LOG_KEPUTUSAN.append(rekaman)
        if jawab is None:
            return None
        return {'label': jawab['label'], 'confidence': jawab['confidence'],
                'alasan': jawab['alasan'], 'model': jawab['model']}

    fn.log = []
    return fn
