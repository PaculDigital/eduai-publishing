#!/usr/bin/env python3
"""VERIFIKASI BIAYA — cara yang benar: delta saldo (Bos minta "dari sekian jadi sekian").

Masalah: `usage.cost` per-request tidak reliabel (kadang $0.00001000 flat = nilai minimum,
kadang $0.00003480 = anomali). Saldo punya resolusi 6 desimal ($0.000001).
Solusi: jalankan N request, ukur DELTA SALDO nyata, bagi rata.
"""
import json
import subprocess
import time
from pathlib import Path

KEY = "sk-airo-iQ9o0bU40Mt0Al2UeM80tLBF"
BASE = "https://api.inferhub.dev/v1"
MODEL = "cb/gpt-5.6-luna"


def raw():
    out = subprocess.run(["curl", "-s", "-m", "60", "-H", f"Authorization: Bearer {KEY}",
                          f"{BASE}/me/usage"], capture_output=True, text=True).stdout
    return json.loads(out.strip())


def chat(sysp, usr, mx=3000):
    p = {"model": MODEL, "temperature": 0.2, "max_tokens": mx,
         "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": usr}]}
    out = subprocess.run(["curl", "-s", "-m", "300", "-X", "POST", f"{BASE}/chat/completions",
                          "-H", f"Authorization: Bearer {KEY}", "-H", "Content-Type: application/json",
                          "-d", json.dumps(p)], capture_output=True, text=True).stdout
    try:
        j = json.loads(out)
        if "choices" not in j:
            return None
        return j
    except Exception:
        return None


def main():
    naskah = Path("/tmp/bab1_goras.txt").read_text()
    tagged = f"<<<NASKAH\n{naskah}\nNASKAH;>>>"
    sysp = ('Anda penguji naskah akademik. Periksa KELENGKAPAN bagian wajib BAB I '
            '(Latar Belakang, Rumusan Masalah, Tujuan, Batasan, Manfaat). '
            'Balas JSON {"ada":[],"hilang":[],"catatan":""}.')

    print("STRATEGI: 5 request identik, ukur DELTA SALDO NYATA (bukan usage.cost)")
    print("=" * 80)

    a = raw()
    s0 = float(a["balance"]["amount_usdc"])
    w0 = float(a["window"]["spend_usdc"])
    print(f"SALDO AWAL      : {s0:.6f} USDC")
    print(f"window spend    : {w0:.6f}\n")

    costs, toks_in, toks_out = [], [], []
    t0 = time.monotonic()
    for i in range(1, 6):
        j = chat(sysp, tagged)
        if j is None:
            print(f"  [{i}] GAGAL")
            continue
        u = j["usage"]
        c = float(u.get("cost") or 0)
        costs.append(c)
        toks_in.append(u["prompt_tokens"])
        toks_out.append(u["completion_tokens"])
        print(f"  [{i}] {j['choices'][0]['message'].get('content','')[:40]!r:44s} "
              f"in={u['prompt_tokens']:>6,} out={u['completion_tokens']:>5,} "
              f"usage.cost=${c:.8f}")
    durasi = time.monotonic() - t0

    time.sleep(3)
    b = raw()
    s1 = float(b["balance"]["amount_usdc"])
    w1 = float(b["window"]["spend_usdc"])

    print("\n" + "=" * 80)
    print("HASIL VERIFIKASI")
    print("=" * 80)
    print(f"  SALDO AWAL          : {s0:.6f} USDC")
    print(f"  SALDO AKHIR         : {s1:.6f} USDC")
    print(f"  SELISIH (NYATA)     : {s0 - s1:.6f} USDC")
    print(f"  window spend delta  : {w1 - w0:.6f} USDC")
    print(f"  sum usage.cost      : {sum(costs):.8f} USDC")
    print(f"  request             : {len(costs)} (durasi {durasi:.1f}s)")
    print(f"  rata-rata token in  : {sum(toks_in)//len(toks_in):,}")
    print(f"  rata-rata token out : {sum(toks_out)//len(toks_out):,}")
    print()
    print(f"  → BIAYA PER REQUEST (dari selisih saldo) : ${(s0-s1)/len(costs):.8f}")
    print(f"  → Rp per request (@16.000)              : Rp {(s0-s1)/len(costs)*16000:.4f}")


if __name__ == "__main__":
    main()
