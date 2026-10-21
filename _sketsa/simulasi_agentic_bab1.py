#!/usr/bin/env python3
"""SIMULASI AGENTIC EduAi — BAB I via InferHub. v3 (model final: cb/gpt-5.6-luna).

Pel. v1: max_tokens 1600 → output terpotong.
Pel. v2: model reasoning (flash) habis di thinking → jawaban kosong.
Pel. v3: pakai cb/gpt-5.6-luna (thinking minimal, cepat, murah) + max_tokens cukup.

Ukur saldo presisi: balance + session.spend_usdc (session 30s window — ambil setelah jeda).
"""
import json
import subprocess
import time
from pathlib import Path

KEY = "sk-airo-iQ9o0bU40Mt0Al2UeM80tLBF"
BASE = "https://api.inferhub.dev/v1"
MODEL = "cb/gpt-5.6-luna"
NASKAH = Path("/tmp/bab1_goras.txt")
OUT = Path("/opt/data/services/eduai-publishing/simulasi_bab1_hasil.json")


def curl_json(url, payload=None, timeout=400):
    if payload is None:
        cmd = ["curl", "-s", "-m", str(timeout), "-H", f"Authorization: Bearer {KEY}", url]
    else:
        cmd = ["curl", "-s", "-m", str(timeout), "-X", "POST", url,
               "-H", f"Authorization: Bearer {KEY}", "-H", "Content-Type: application/json",
               "-d", json.dumps(payload)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)


def metrik():
    j = curl_json(f"{BASE}/me/usage")
    return {"saldo": float(j["balance"]["amount_usdc"]),
            "sess": float(j["session"]["spend_usdc"]),
            "req": j["session"]["requests"]}


def chat(sysp, usr, mx=3000, temp=0.2):
    payload = {"model": MODEL, "temperature": temp, "max_tokens": mx,
               "messages": [{"role": "system", "content": sysp},
                            {"role": "user", "content": usr}]}
    t0 = time.monotonic()
    j = curl_json(f"{BASE}/chat/completions", payload)
    dt = time.monotonic() - t0
    if "choices" not in j:
        return {"ok": False, "err": str(j)[:250], "detik": dt, "usage": {}, "teks": ""}
    m = j["choices"][0]["message"]
    return {"ok": True, "teks": m.get("content") or "", "fin": j["choices"][0].get("finish_reason"),
            "usage": j.get("usage", {}), "detik": dt, "model": j.get("model")}


def putaran(no, nama, sysp, usr, mx=3000):
    r = chat(sysp, usr, mx)
    u = r.get("usage", {})
    c = float(u.get("cost") or 0)
    baik = r["ok"] and bool(r["teks"].strip())
    print(f"  [{no}] {nama:22s} {'OK ' if baik else 'GAGAL'} {r['detik']:6.1f}s "
          f"in={u.get('prompt_tokens',0):>7,} think={u.get('completion_thinking_tokens',0):>5,} "
          f"out={u.get('completion_tokens',0):>6,} ${c:.8f}")
    return {"no": no, "nama": nama, "detik": r["detik"], "baik": baik,
            "in": u.get("prompt_tokens", 0), "think": u.get("completion_thinking_tokens", 0),
            "out": u.get("completion_tokens", 0), "cost": c, "teks": r.get("teks", "")}


def main():
    naskah = NASKAH.read_text()
    print(f"NASKAH BAB I : {len(naskah):,} karakter / {len(naskah.split()):,} kata")
    print(f"MODEL        : {MODEL}")
    print("=" * 84)
    a = metrik()
    print(f"METRIK AWAL  : saldo={a['saldo']:.6f} | session_spend={a['sess']:.6f} | req={a['req']}\n")

    t0 = time.monotonic()
    tagged = f"<<<NASKAH\n{naskah}\nNASKAH;>>>"
    H = []

    H.append(putaran(1, "cek_kelengkapan",
        'Anda penguji naskah akademik Indonesia. Periksa KELENGKAPAN bagian wajib BAB I: '
        '(1) Latar Belakang (2) Rumusan Masalah (3) Tujuan (4) Batasan (5) Manfaat. '
        'Balas JSON: {"ada":["..."],"hilang":["..."],"catatan":"maks 20 kata"}', tagged, 1500))

    H.append(putaran(2, "cek_alur_logika",
        'Anda penguji logika akademik. Periksa ALUR BAB I: apakah masalah di Latar Belakang '
        'tercermin di Rumusan Masalah? Apakah Tujuan menjawab Rumusan Masalah satu-satu? '
        'Balas JSON: {"nyambung":true|false,"temuan":[{"masalah":"...","bukti":"<kutipan pendek>","saran":"..."}]} '
        'Maksimum 3 temuan.', tagged, 3000))

    H.append(putaran(3, "cek_puebi",
        'Anda editor bahasa Indonesia (PUEBI/KBBI). Temukan kesalahan ejaan NYATA pada naskah. '
        'Fokus: "di" kata depan vs awalan, huruf kapital, tanda baca, istilah asing. '
        'Balas JSON: {"temuan":[{"salah":"<kutipan asli>","benar":"<perbaikan>"}]} Maksimum 5.', tagged, 3000))

    H.append(putaran(4, "cek_istilah",
        'Anda penguji konsistensi akademik. Periksa BAB I: istilah teknis konsisten? variabel/objek '
        'disebut dengan nama sama? ada singkatan tanpa diperkenalkan? '
        'Balas JSON: {"temuan":[{"istilah":"...","masalah":"...","saran":"..."}]} Maksimum 4.', tagged, 3000))

    bahan = "\n\n".join(
        f"=== {h['nama'].upper()} ===\n{h['teks'][:2500] if h['baik'] else '(gagal)'}" for h in H[:4])
    H.append(putaran(5, "laporan_akhir",
        'Anda penyusun laporan untuk mahasiswa. Diberikan hasil 4 pemeriksaan BAB I. '
        'Susun LAPORAN (maks 350 kata) berisi: 1) status kelengkapan 2) 3 temuan logika terpenting '
        '3) 3 temuan ejaan terpenting 4) temuan konsistensi istilah 5) PRIORITAS PERBAIKAN (3 teratas). '
        'Gaya lugas, tidak menyalahkan, siap dikerjakan.', bahan, 2000))

    durasi = time.monotonic() - t0
    b = metrik()
    tin = sum(h["in"] for h in H); tthink = sum(h["think"] for h in H)
    tout = sum(h["out"] for h in H); tcost = sum(h["cost"] for h in H)
    sukses = sum(1 for h in H if h["baik"])

    print("\n" + "=" * 84)
    print("HASIL AKHIR — SIMULASI AGENTIC BAB I")
    print("=" * 84)
    print(f"  Putaran sukses      : {sukses}/{len(H)}")
    print(f"  Token input         : {tin:,}")
    print(f"  Token thinking      : {tthink:,}   (bagian dari output)")
    print(f"  Token output total  : {tout:,}")
    print(f"  TOTAL token         : {tin+tout:,}")
    print(f"  BIAYA (sum cost)    : ${tcost:.8f}")
    print(f"  DURASI dinding      : {durasi:.1f}s")
    print("-" * 84)
    print(f"  SALDO AWAL          : {a['saldo']:.6f} USDC")
    print(f"  SALDO AKHIR         : {b['saldo']:.6f} USDC")
    print(f"  SELISIH SALDO       : {a['saldo'] - b['saldo']:.6f} USDC")
    print(f"  Rupiah @16.000/USD  : Rp {(a['saldo']-b['saldo'])*16000:.2f}")
    print("\n--- LAPORAN AKHIR ---")
    print(H[-1]["teks"][:2200])

    OUT.write_text(json.dumps({
        "model": MODEL, "naskah_kata": len(naskah.split()),
        "putaran": [{k: v for k, v in h.items() if k != "teks"} for h in H],
        "total_in": tin, "total_think": tthink, "total_out": tout,
        "total_token": tin + tout, "biaya_usd": tcost, "durasi_detik": durasi,
        "saldo_awal": a["saldo"], "saldo_akhir": b["saldo"],
        "selisih_saldo": a["saldo"] - b["saldo"], "putaran_sukses": sukses,
    }, indent=1))
    print(f"\n✓ tersimpan: {OUT}")


if __name__ == "__main__":
    main()
