"""Penanya OpenRouter untuk agen kedua — PERKAKAS PILOT (bukan kode produksi).

Dipakai pilot rantai 3 langkah dari VM (di luar container): memanggil model
instruksi umum PINNED lewat jalur OpenRouter langsung, memakai koneksi
`custom.openrouter` yang sudah terdaftar (kunci lewat surrogate authd —
nilai kunci TIDAK PERNAH muncul di sini, di argumen, atau di log).

Model utama: google/gemini-2.5-flash (11 Nov 2026, harga terukur
$0,30/1 juta token masuk, $2,50/1 juta keluar; saldo akun tersisa ~$6,38).
Cadangan: openai/gpt-4o-mini ($0,15/1 juta masuk, $0,60/1 juta keluar).

Pemakaian:
    from agen_kedua_openrouter import buat_penanya
    penanya = buat_penanya()  # atau buat_penanya('openai/gpt-4o-mini')
    konten, model_layani = penanya(prompt)

Berkas ini tinggal di _sketsa/ (arsip) — gerbang jalan tol Jev dan gerbang
setelan produksi TIDAK memeriksanya (keputusan Bos 07 Okt 2026).
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request

MODEL_UTAMA = 'google/gemini-2.5-flash'
MODEL_CADANGAN = 'openai/gpt-4o-mini'
URL = 'https://openrouter.ai/api/v1/chat/completions'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError('redirect refused, verify the endpoint')


def buat_penanya(model: str = MODEL_UTAMA, timeout: float = 60.0):
    """Kembalikan penanya(prompt) -> (konten, model_melayani).

    Gagal (HTTP/galat) ⇒ MELEMPAR RuntimeError (pemanggil agen_kedua
    menelannya jadi None → baris masuk antrean, bukan label tebakan).
    """
    def penanya(prompt: str):
        body = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 512,
            'temperature': 0.2,
            'response_format': {'type': 'json_object'},
        }
        req = urllib.request.Request(
            URL, data=json.dumps(body).encode(),
            headers={'Content-Type': 'application/json'})
        add_surrogate_to_request(
            req, 'custom.openrouter', allowed_hosts=['openrouter.ai'])
        try:
            with urllib.request.build_opener(NoRedirect()).open(
                    req, timeout=timeout) as r:
                mentah = r.read().decode()
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f'OpenRouter HTTP {e.code}: {e.read().decode()[:200]}')
        except Exception as e:
            raise RuntimeError(
                f'OpenRouter tidak bisa dihubungi: {type(e).__name__}: {e}')
        try:
            j = json.loads(mentah)
        except Exception:
            raise RuntimeError('balasan OpenRouter bukan JSON')
        ch = (j.get('choices') or [{}])[0]
        konten = (ch.get('message') or {}).get('content')
        if not konten:
            raise RuntimeError('konten kosong dari OpenRouter')
        return konten, j.get('model') or model

    penanya.model = model
    return penanya
