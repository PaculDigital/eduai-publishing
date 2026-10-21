"""Uji rantai fallback tokenharbor BARU (28Sep26): glm-5.3-flash → deepseek-v4.1-flash.

Dijalankan DI DALAM container (docker cp ke /tmp lalu docker exec python).
Tiga lapis uji, semua pakai kode asli app (bukan tiruan):
  A. daftar_fallback()        → urutan model dari .env container
  B. HTTP langsung per model  → model mana yang benar-benar hidup + waktunya
  C. _panggil_openrouter()    → jalur 2 SEBENARNYA (parser + penjaga app)
"""
import asyncio
import time

from app import config
from app.ai import _panggil_openrouter, _urai_jawaban, SYSTEM_REVISI

import httpx

NASKAH = (
    "Bab 1 latar belakang penelitian ini membahas pengaruh kualitas produk "
    "dan harga terhadap keputusan pembelian konsumen di Kota Padang. "
    "Banyak penelitian terdahulu menggunakan regresi berganda. "
) * 12  # ≈ 1.400 kar — cukup besar utk memicu kerja nyata, tetap cepat


def lapis_a() -> None:
    urut = config.daftar_fallback()
    print("A. daftar_fallback():")
    for i, (m, p) in enumerate(urut, 1):
        print(f"   {i}. {m} @{p or 'bawaan'}")
    assert urut and urut[0][0] == "glm-5.3-flash", urut
    assert any(m == "deepseek-v4.1-flash" for m, _ in urut), urut
    assert all("mimo" not in m for m, _ in urut), f"mimo masih ada: {urut}"
    print("   ✅ urutan benar, mimo sudah hilang")


def lapis_b() -> None:
    print("B. HTTP langsung ke tokenharbor:")
    for model in [m for m, _ in config.daftar_fallback()]:
        isi = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_REVISI},
                {"role": "user",
                 "content": "Balas HANYA dengan satu kata: SEHAT"},
            ],
            "max_tokens": 200,
            "temperature": 0.2,
        }
        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=90) as c:
                r = c.post(
                    f"{config.FALLBACK_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {config.FALLBACK_KEY}",
                             "Content-Type": "application/json"},
                    json=isi,
                )
            dt = time.monotonic() - t0
            if r.status_code != 200:
                print(f"   ❌ {model}: HTTP {r.status_code} {r.text[:160]}")
                continue
            konten, info = _urai_jawaban(r.text, model)
            print(f"   ✅ {model}: {dt:.1f} dtk · model_asli={info.get('model')}"
                  f" · keluar {len(konten)} kar · '{konten[:40]}'")
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ {model}: {type(e).__name__}: {e} "
                  f"({time.monotonic() - t0:.0f}dtk)")


def lapis_c() -> None:
    print("C. _panggil_openrouter() — jalur 2 asli aplikasi:")
    t0 = time.monotonic()
    teks, info = asyncio.run(
        _panggil_openrouter(
            "Tulis 1 komentar pembimbing pendek untuk cuplikan berikut.\n\n"
            + NASKAH,
            120,
        )
    )
    dt = time.monotonic() - t0
    print(f"   ✅ {dt:.1f} dtk · model={info.get('model')} · "
          f"jalur={info.get('jalur')} · {len(teks)} kar")
    print(f"   cuplikan: {teks[:160]!r}")
    assert teks.strip(), "jawaban kosong"
    assert "mimo" not in str(info.get("model", "")), info


if __name__ == "__main__":
    lapis_a()
    lapis_b()
    lapis_c()
    print("\nSEMUA LAPIS LULUS")
