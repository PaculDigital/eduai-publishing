#!/usr/bin/env python3
"""UKUR BIAYA AGENTIC PER BAB — pakai DELTA SALDO NYATA (metode Bos: "dari sekian jadi sekian").

Temuan: `usage.cost` per-request tidak reliabel (sering flat $0.00001000 = nilai minimum,
kadang melompat anomali). Sumber kebenaran = `balance.amount_usdc` (6 desimal) dan
`window.spend_usdc`. 1 request kecil di bawah ~$0.00001 tidak terlihat; karena itu per BAB
dijalankan sekali penuh lalu ukur delta saldo total.

Format output: tabel biaya nyata + margin untuk harga jual.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

KEY = "sk-airo-iQ9o0bU40Mt0Al2UeM80tLBF"
BASE = "https://api.inferhub.dev/v1"
MODEL = "cb/gpt-5.6-luna"
OUT = Path("/opt/data/services/eduai-publishing/biaya_agentic_nyata.json")


def raw():
    out = subprocess.run(["curl", "-s", "-m", "60", "-H", f"Authorization: Bearer {KEY}",
                          f"{BASE}/me/usage"], capture_output=True, text=True).stdout
    return json.loads(out.strip())


def chat(sysp, usr, mx=3000, temp=0.2):
    p = {"model": MODEL, "temperature": temp, "max_tokens": mx,
         "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": usr}]}
    out = subprocess.run(["curl", "-s", "-m", "400", "-X", "POST", f"{BASE}/chat/completions",
                          "-H", f"Authorization: Bearer {KEY}", "-H", "Content-Type: application/json",
                          "-d", json.dumps(p)], capture_output=True, text=True).stdout
    try:
        j = json.loads(out)
        return j if "choices" in j else None
    except Exception:
        return None


TUGAS = {
    "BAB I": [
        ("cek_kelengkapan", 'Periksa KELENGKAPAN BAB I: Latar Belakang, Rumusan Masalah, Tujuan, Batasan, Manfaat. Balas JSON {"ada":[],"hilang":[],"catatan":""}.', 1500),
        ("cek_alur_logika", 'Periksa ALUR BAB I: masalah di Latar Belakang tercermin di Rumusan Masalah? Tujuan menjawab RM satu-satu? Balas JSON {"nyambung":bool,"temuan":[{"masalah":"","bukti":"","saran":""}]} maks 3.', 3000),
        ("cek_puebi", 'Temukan kesalahan ejaan PUEBI NYATA pada naskah. Balas JSON {"temuan":[{"salah":"","benar":""}]} maks 5.', 3000),
        ("cek_istilah", 'Periksa konsistensi istilah & singkatan. Balas JSON {"temuan":[{"istilah":"","masalah":"","saran":""}]} maks 4.', 3000),
    ],
    "BAB II": [
        ("cek_struktur_teori", 'Periksa STRUKTUR BAB II: tiap variabel punya landasan teori? grand theory → variabel? Balas JSON {"grand_theory":"","variabel":[{"nama":"","teori":"","ada":bool}],"hilang":[]}.', 3000),
        ("cek_sitasi_apa", 'Periksa SITASI APA 7 dalam teks: format benar? pola konsisten? Balas JSON {"temuan":[{"kutipan":"","masalah":"","benar":""}]} maks 6.', 3000),
        ("cek_konsistensi_variabel", 'Definisi tiap variabel KONSISTEN antar subbab? indikator selaras definisi? Balas JSON {"temuan":[{"variabel":"","masalah":"","saran":""}]} maks 5.', 3000),
        ("cek_kerangka_hipotesis", 'Periksa KERANGKA BERPIKIR & HIPOTESIS: dasar teori ada? arah hipotesis jelas? Balas JSON {"temuan":[{"hipotesis":"","masalah":"","saran":""}]} maks 5.', 3000),
    ],
    "BAB III": [
        ("cek_desain_metode", 'Periksa DESAIN BAB III: sesuai tujuan? konsisten dengan instrumen? Balas JSON {"desain":"","cocok":bool,"temuan":[]} maks 3.', 3000),
        ("cek_populasi_sampel", 'Periksa POPULASI & SAMPEL: teknik sampling? jumlah & rumus hitung benar? Balas JSON {"teknik":"","jumlah":"","rumus":"","temuan":[{"masalah":"","saran":""}]} maks 4.', 3000),
        ("cek_instrumen_variabel", 'Periksa INSTRUMEN: tiap variabel punya item? skala jelas? tabel operasional lengkap? Balas JSON {"temuan":[{"variabel":"","masalah":"","saran":""}]} maks 5.', 3000),
        ("cek_analisis_data", 'Periksa TEKNIK ANALISIS: sesuai hipotesis? uji tepat (PLS-SEM untuk mediasi)? Balas JSON {"teknik":"","aplikasi":"","temuan":[{"masalah":"","saran":""}]} maks 4.', 3000),
        ("cek_etika_validitas", 'Periksa VALIDITAS/RELIABILITAS & ETIKA: uji validitas disebut? GOF ada? Balas JSON {"temuan":[{"aspek":"","status":"","saran":""}]} maks 4.', 3000),
    ],
}


def jalankan(nama, file):
    naskah = Path(file).read_text()
    print(f"\n{'='*88}\n{nama} — {len(naskah.split()):,} kata\n{'='*88}")
    tagged = f"<<<NASKAH\n{naskah}\nNASKAH;>>>"
    a = raw()
    s0 = float(a["balance"]["amount_usdc"]); w0 = float(a["window"]["spend_usdc"])
    print(f"  SALDO AWAL: {s0:.6f} USDC")
    t0 = time.monotonic()
    tot_in = tot_out = 0
    ok = gagal = 0
    for i, (nm, sysp, mx) in enumerate(TUGAS[nama], 1):
        j = chat(sysp, tagged, mx)
        if j is None:
            gagal += 1
            print(f"    [{i}] {nm:28s} GAGAL")
            continue
        u = j["usage"]
        tot_in += u["prompt_tokens"]; tot_out += u["completion_tokens"]
        ok += 1
        print(f"    [{i}] {nm:28s} OK in={u['prompt_tokens']:>7,} out={u['completion_tokens']:>5,}")
    durasi = time.monotonic() - t0
    time.sleep(2)
    b = raw()
    s1 = float(b["balance"]["amount_usdc"]); w1 = float(b["window"]["spend_usdc"])
    biaya = s0 - s1
    if biaya <= 0:
        biaya = w1 - w0
    hasil = {"bab": nama, "kata": len(naskah.split()), "putaran": ok + gagal, "sukses": ok,
             "token_in": tot_in, "token_out": tot_out, "total_token": tot_in + tot_out,
             "saldo_awal": s0, "saldo_akhir": s1, "biaya_usd": biaya,
             "durasi_detik": durasi}
    print(f"  SALDO AKHIR: {s1:.6f} | BIAYA NYATA: ${biaya:.6f} | {durasi:.1f}s | {tot_in+tot_out:,} token")
    return hasil


def main():
    print(f"MODEL: {MODEL}\nMETODE: delta saldo nyata (bukan usage.cost)")
    hasil = []
    for nama, f in [("BAB I", "/tmp/bab1_goras.txt"), ("BAB II", "/tmp/bab2_goras.txt"),
                    ("BAB III", "/tmp/bab3_goras.txt")]:
        hasil.append(jalankan(nama, f))

    print("\n" + "=" * 88)
    print("BIAYA AGENTIC NYATA PER BAB (terverifikasi dari saldo)")
    print("=" * 88)
    print(f"{'BAB':8s} {'kata':>7s} {'token':>9s} {'putaran':>8s} {'USD':>12s} {'Rp':>8s} {'detik':>7s}")
    print("-" * 88)
    for h in hasil:
        print(f"{h['bab']:8s} {h['kata']:>7,} {h['total_token']:>9,} {h['sukses']}/{h['putaran']:<6} "
              f"{h['biaya_usd']:>12.6f} {h['biaya_usd']*16000:>8.2f} {h['durasi_detik']:>7.1f}")

    tot = sum(h["biaya_usd"] for h in hasil)
    tot_tok = sum(h["total_token"] for h in hasil)
    print("-" * 88)
    print(f"{'TOTAL':8s} {sum(h['kata'] for h in hasil):>7,} {tot_tok:>9,} {'':>8s} "
          f"{tot:>12.6f} {tot*16000:>8.2f}")

    print("\n=== ANALISIS MARGIN (harga jual per paket BAB) ===")
    for h in hasil:
        print(f"\n  Paket Agentic {h['bab']}  (biaya modal ${h['biaya_usd']:.6f} = Rp {h['biaya_usd']*16000:.2f})")
        for harga in [5000, 10000, 15000, 25000]:
            margin = (harga - h["biaya_usd"] * 16000) / harga * 100
            print(f"    jual Rp {harga:>6,} → margin {margin:6.2f}%  (laba Rp {harga - h['biaya_usd']*16000:>8.2f})")

    OUT.write_text(json.dumps(hasil, indent=1))
    print(f"\n✓ tersimpan: {OUT}")


if __name__ == "__main__":
    main()
