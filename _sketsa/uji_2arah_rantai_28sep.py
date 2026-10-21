"""Uji 2 ARAH rantai fallback (28Sep26).

SEHAT  : lapis 1 (glm) dipakai → sukses.
DIRUSAK: lapis 1 sengaja dibuat model tak ada → app HARUS jatuh ke
         lapis 2 (deepseek-v4.1-flash) DAN tetap menghasilkan jawaban.
"""
import asyncio
import time

from app import config
from app import ai

PROMPT = "Balas HANYA dengan satu kata: OK"


def sehat() -> None:
    t0 = time.monotonic()
    teks, info = asyncio.run(ai._panggil_openrouter(PROMPT, 90))
    print(f"SEHAT   : {time.monotonic() - t0:.1f} dtk · model={info.get('model')}"
          f" · '{teks[:30]}'")
    assert info.get("model") == "glm-5.3-flash", info


def dirusak() -> None:
    asli = config.FALLBACK_MODEL
    config.FALLBACK_MODEL = "model-tidak-ada-999"   # lapis 1 dipaksa MATI
    try:
        t0 = time.monotonic()
        teks, info = asyncio.run(ai._panggil_openrouter(PROMPT, 90))
        dt = time.monotonic() - t0
        print(f"DIRUSAK : {dt:.1f} dtk · jatuh ke model={info.get('model')}"
              f" · '{teks[:30]}'")
        assert info.get("model") == "deepseek-v4.1-flash", \
            f"harusnya jatuh ke deepseek, dapat {info}"
    finally:
        config.FALLBACK_MODEL = asli


if __name__ == "__main__":
    sehat()
    dirusak()
    print("2 ARAH LULUS — lapis 1 mati → lapis 2 (deepseek) menolong")
