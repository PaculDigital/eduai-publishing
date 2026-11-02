#!/usr/bin/env python3
"""Uji offline fallback Bumi (Gas Bos 2 Nov 2026). TANPA jaringan nyata,
TANPA kredit Bumi/InferHub/OpenRouter, TANPA order buku.

Kasus:
  1. Urutan rantai = InferHub, InferHub, Bumi, Bumi, Bumi, OpenRouter.
  2. InferHub gagal 2x -> Bumi sukses via polling -> OpenRouter TIDAK dipanggil.
  3. Bumi gagal (status failed) -> OpenRouter sukses, jadi jaring terakhir.
  4. BUMI_API_KEY kosong -> Bumi dilewati -> OpenRouter sukses.
  5. Sampul: aspect_ratio "2:3" diteruskan ke parameter Bumi.
  6. Unduh Bumi putus di percobaan pertama -> diunduh ulang dan sukses,
     generation_id tidak dibuang (pelajaran live 2 Nov 2026).
Jalankan: EDUAI_ROUTER_KEY=dummy INFERHUB_KEY=dummy python3 uji_fallback_bumi.py
"""
import base64
import os
import sys
import tempfile

os.environ.setdefault("EDUAI_ROUTER_KEY", "dummy")
os.environ.setdefault("INFERHUB_KEY", "dummy")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buku_umum_pipeline as P

PNG_PALSU = b"\x89PNG\r\n\x1a\nPALSU"


class Resp:
    def __init__(self, data=None, content=b""):
        self._data = data if data is not None else {}
        self.content = content
        self.status_code = 200

    def json(self):
        return self._data


class MockRequests:
    """Ganti P.requests.post/get. `mode` mengatur perilaku Bumi/OpenRouter."""

    def __init__(self, mode):
        self.mode = mode
        self.post_urls = []
        self.get_urls = []
        self.bumi_params = []
        self._poll_n = 0
        self._unduh_n = 0

    def post(self, url, headers=None, json=None, timeout=None, **kw):
        self.post_urls.append(url)
        if "bumi.digital" in url:
            self.bumi_params.append((json or {}).get("parameters") or {})
            if self.mode == "bumi_gagal":
                return Resp({"generation_id": "gen-gagal"})
            return Resp({"generation_id": "gen-1"})
        if "inferhub" in url:
            return Resp({"data": [{}]})
        if "openrouter" in url:
            b64 = base64.b64encode(PNG_PALSU).decode()
            return Resp({"choices": [{"message": {"images": [
                {"image_url": {"url": "data:image/png;base64," + b64}}]}}]})
        raise AssertionError("URL tak terduga: " + url)

    def get(self, url, headers=None, timeout=None, **kw):
        self.get_urls.append(url)
        if "bumi.digital" in url and "/generation/" in url:
            self._poll_n += 1
            if self.mode == "bumi_gagal":
                return Resp({"generation_id": "gen-gagal", "status": "failed",
                             "error": "model sibuk"})
            if self._poll_n == 1:
                return Resp({"generation_id": "gen-1", "status": "processing"})
            return Resp({"generation_id": "gen-1", "status": "completed",
                         "resultUrl": "https://contoh.test/hasil.png"})
        if url == "https://contoh.test/hasil.png":
            if self.mode == "unduh_putus":
                self._unduh_n += 1
                if self._unduh_n == 1:
                    raise Exception("IncompleteRead simulasi")
            return Resp(content=PNG_PALSU)
        raise AssertionError("GET tak terduga: " + url)


def jalankan(mode, kunci_bumi):
    """Pasang mock, panggil _gambar_satu, kembalikan hasil + mock."""
    if kunci_bumi is None:
        os.environ.pop("BUMI_API_KEY", None)
    else:
        os.environ["BUMI_API_KEY"] = kunci_bumi
    P.GAMBAR_MATI.clear()
    mock = MockRequests(mode)
    asli_post, asli_get = P.requests.post, P.requests.get
    asli_sleep = P.time.sleep
    P.requests.post, P.requests.get = mock.post, mock.get
    P.time.sleep = lambda *a, **k: None
    try:
        raw, model, galat = P._gambar_satu("ilustrasi uji, tanpa teks")
    finally:
        P.requests.post, P.requests.get = asli_post, asli_get
        P.time.sleep = asli_sleep
    return raw, model, galat, mock


def cek(nama, syarat):
    print(("OK  " if syarat else "GAGAL ") + nama)
    if not syarat:
        raise SystemExit(1)


def main():
    # Kunci OpenRouter di uji ini hanya kunci palsu untuk mock, bukan kunci nyata.
    os.environ["EDUAI_GAMBAR_FALLBACK_KEY"] = "kunci-uji-openrouter"
    cek("rantai urutan", P.GAMBAR_RANTAI == [
        ("inferhub", "gpt-image-2-codex"),
        ("inferhub", "cx/gpt-image-2-codex"),
        ("bumi", "is2i-gpt-image-2-5-sunburst"),
        ("bumi", "OpenAI/gpt-image-2.5-flare-promo"),
        ("bumi", "OpenAI/gpt-image-2.5-flare"),
        ("openrouter", "google/gemini-3.1-flash-lite-image"),
    ])
    raw, model, galat, mock = jalankan("bumi_ok", "kunci-uji")
    cek("Bumi sukses setelah InferHub gagal", raw == PNG_PALSU
        and model == "is2i-gpt-image-2-5-sunburst")
    cek("OpenRouter tidak dipanggil saat Bumi sukses",
        not any("openrouter" in u for u in mock.post_urls))
    cek("Bumi dipanggil dengan medium 1K termurah",
        mock.bumi_params and mock.bumi_params[0].get("quality") == "medium"
        and mock.bumi_params[0].get("resolution") == "1k"
        and mock.bumi_params[0].get("aspect_ratio") == "1:1")
    cek("Bumi dipoll sampai completed", mock._poll_n >= 2)

    raw, model, galat, mock = jalankan("bumi_gagal", "kunci-uji")
    cek("Bumi gagal -> OpenRouter jadi penolong terakhir",
        raw == PNG_PALSU
        and model == "google/gemini-3.1-flash-lite-image")
    cek("OpenRouter dipanggil setelah Bumi gagal",
        any("openrouter" in u for u in mock.post_urls))

    raw, model, galat, mock = jalankan("bumi_ok", None)
    cek("Kunci Bumi kosong -> dilewati ke OpenRouter, bukan crash",
        raw == PNG_PALSU
        and model == "google/gemini-3.1-flash-lite-image"
        and not any("bumi.digital" in u for u in mock.post_urls))

    raw, model, galat, mock = jalankan("unduh_putus", "kunci-uji")
    cek("Unduh Bumi putus -> diulang dan sukses, bukan buang generate",
        raw == PNG_PALSU
        and model == "is2i-gpt-image-2-5-sunburst"
        and mock._unduh_n == 2)

    with tempfile.TemporaryDirectory() as tmp:
        P.GAMBAR_MATI.clear()
        mock = MockRequests("bumi_ok")
        asli_post, asli_get = P.requests.post, P.requests.get
        asli_sleep = P.time.sleep
        P.requests.post, P.requests.get = mock.post, mock.get
        P.time.sleep = lambda *a, **k: None
        os.environ["BUMI_API_KEY"] = "kunci-uji"
        try:
            # InferHub gagal di mock, jadi sampul jatuh ke Bumi pertama.
            path = P.generate_sampul_api(
                "ilustrasi sampul tanpa teks",
                simpan=os.path.join(tmp, "cover.png"))
        finally:
            P.requests.post, P.requests.get = asli_post, asli_get
            P.time.sleep = asli_sleep
        cek("sampul portrait 2:3 ke Bumi dan berkas tersimpan",
            path and os.path.exists(path)
            and open(path, "rb").read() == PNG_PALSU
            and mock.bumi_params
            and mock.bumi_params[0].get("aspect_ratio") == "2:3")
    print("SEMUA UJI LULUS (mock, tanpa jaringan nyata, tanpa kredit)")


if __name__ == "__main__":
    main()
