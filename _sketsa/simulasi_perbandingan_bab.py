#!/usr/bin/env python3
"""SIMULASI AGENTIC — Bandingkan BAB I vs II vs III (InferHub, cb/gpt-5.6-luna).

Menjawab pertanyaan Bos: "bab paling banyak token = paling mahal?"
Uji: apakah BAB II (12.998 kata, 3x BAB I) benar-benar paling mahal,
     atau BAB III (3.634 kata) yang paling mahal karena kompleksitas cek?
"""
import json
import subprocess
import time
from pathlib import Path

KEY = "sk-airo-iQ9o0bU40Mt0Al2UeM80tLBF"
BASE = "https://api.inferhub.dev/v1"
MODEL = "cb/gpt-5.6-luna"
OUT = Path("/opt/data/services/eduai-publishing/simulasi_perbandingan_bab.json")


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
            "sess": float(j["session"]["spend_usdc"]), "req": j["session"]["requests"]}


def chat(sysp, usr, mx=3000, temp=0.2):
    payload = {"model": MODEL, "temperature": temp, "max_tokens": mx,
               "messages": [{"role": "system", "content": sysp},
                            {"role": "user", "content": usr}]}
    t0 = time.monotonic()
    j = curl_json(f"{BASE}/chat/completions", payload)
    dt = time.monotonic() - t0
    if "choices" not in j:
        return {"ok": False, "err": str(j)[:200], "detik": dt, "usage": {}, "teks": ""}
    m = j["choices"][0]["message"]
    return {"ok": True, "teks": m.get("content") or "", "usage": j.get("usage", {}),
            "detik": dt, "fin": j["choices"][0].get("finish_reason")}


# ── Definisi tugas agentic PER BAB (disesuaikan kompleksitasnya) ──────────
TUGAS = {
    "BAB I": [
        ("cek_kelengkapan",
         'Anda penguji naskah akademik Indonesia. Periksa KELENGKAPAN bagian wajib BAB I: '
         '(1) Latar Belakang (2) Rumusan Masalah (3) Tujuan (4) Batasan (5) Manfaat. '
         'Balas JSON: {"ada":[],"hilang":[],"catatan":"maks 20 kata"}', 1500),
        ("cek_alur_logika",
         'Anda penguji logika akademik. Periksa ALUR BAB I: apakah masalah di Latar Belakang '
         'tercermin di Rumusan Masalah? Apakah Tujuan menjawab RM satu-satu? '
         'Balas JSON: {"nyambung":bool,"temuan":[{"masalah":"","bukti":"","saran":""}]} maks 3.', 3000),
        ("cek_puebi",
         'Anda editor bahasa Indonesia (PUEBI/KBBI). Temukan kesalahan ejaan NYATA. '
         'Balas JSON: {"temuan":[{"salah":"","benar":""}]} maks 5.', 3000),
        ("cek_istilah",
         'Anda penguji konsistensi akademik. Istilah teknis konsisten? Singkatan diperkenalkan? '
         'Balas JSON: {"temuan":[{"istilah":"","masalah":"","saran":""}]} maks 4.', 3000),
    ],
    "BAB II": [
        ("cek_struktur_teori",
         'Anda penguji telaah pustaka. Periksa STRUKTUR BAB II: setiap variabel punya landasan teori? '
         'grand theory → variabel? ada variabel tanpa teori? '
         'Balas JSON: {"grand_theory":"","variabel":[{"nama":"","teori":"","ada":bool}],"hilang":[]}', 3000),
        ("cek_sitasi_apA",
         'Anda penguji sitasi APA 7. Periksa SITASI dalam teks BAB II: format APA benar? '
         'Ada sitasi tanpa penulis/tahun? Ada pola tidak konsisten (mis. "menurut X (2020)" vs "(X, 2020)")? '
         'Balas JSON: {"temuan":[{"kutipan":"","masalah":"","benar":""}]} maks 6.', 3000),
        ("cek_konsistensi_teori_variabel",
         'Anda penguji konsistensi. Periksa apakah definisi tiap variabel di BAB II KONSISTEN '
         'antar subbab (tidak berubah makna)? Apakah indikator selaras dengan definisi? '
         'Balas JSON: {"temuan":[{"variabel":"","masalah":"","saran":""}]} maks 5.', 3000),
        ("cek_kerangka_berpikir",
         'Anda penguji. Periksa KERANGKA BERPIKIR & HIPOTESIS di BAB II: hipotesis punya dasar teori? '
         'arah hipotesis (positif/negatif) jelas? konsisten dengan definisi variabel? '
         'Balas JSON: {"temuan":[{"hipotesis":"","masalah":"","saran":""}]} maks 5.', 3000),
    ],
    "BAB III": [
        ("cek_desain_metode",
         'Anda penguji metodologi. Periksa DESAIN PENELITIAN BAB III: desain sesuai tujuan penelitian? '
         'pendekatan kuantitatif/kualitatif konsisten dengan instrumen? '
         'Balas JSON: {"desain":"","cocok":bool,"temuan":[]} maks 3.', 3000),
        ("cek_populasi_sampel",
         'Anda penguji metodologi. Periksa POPULASI & SAMPEL: teknik sampling disebutkan? '
         'jumlah sampel & cara hitung (rumus) ada dan benar? kriteria inklusi jelas? '
         'Balas JSON: {"teknik":"","jumlah":"","rumus":"","temuan":[{"masalah":"","saran":""}]} maks 4.', 3000),
        ("cek_instrumen_variabel",
         'Anda penguji metodologi. Periksa INSTRUMEN: setiap variabel punya item? '
         'skala pengukuran jelas? tabel operasional variabel lengkap? '
         'Balas JSON: {"temuan":[{"variabel":"","masalah":"","saran":""}]} maks 5.', 3000),
        ("cek_analisis_data",
         'Anda penguji metodologi. Periksa TEKNIK ANALISIS DATA: sesuai hipotesis? '
         'uji yang dipilih tepat (mis. PLS-SEM untuk mediasi)? aplikasi disebut? '
         'Balas JSON: {"teknik":"","aplikasi":"","temuan":[{"masalah":"","saran":""}]} maks 4.', 3000),
        ("cek_etika_validitas",
         'Anda penguji metodologi. Periksa ETIKA & VALIDITAS RELIABILITAS: uji validitas/reliabilitas '
         'disebutkan? uji asumsi/GOF ada? prosedur etika penelitian dijelaskan? '
         'Balas JSON: {"temuan":[{"aspek":"","status":"","saran":""}]} maks 4.', 3000),
    ],
}


def jalankan_bab(nama, naskah):
    print(f"\n{'='*86}\n{nama} — {len(naskah.split()):,} kata / {len(naskah):,} karakter\n{'='*86}")
    a = metrik()
    print(f"  metrik awal: saldo={a['saldo']:.6f} sess={a['sess']:.6f} req={a['req']}")
    tagged = f"<<<NASKAH\n{naskah}\nNASKAH;>>>"
    t0 = time.monotonic()
    H = []
    for i, (nm, sysp, mx) in enumerate(TUGAS[nama], 1):
        r = chat(sysp, tagged, mx)
        u = r.get("usage", {}); c = float(u.get("cost") or 0)
        baik = r["ok"] and bool(r["teks"].strip())
        print(f"    [{i}] {nm:30s} {'OK ' if baik else 'GAGAL'} {r['detik']:6.1f}s "
              f"in={u.get('prompt_tokens',0):>7,} out={u.get('completion_tokens',0):>5,} ${c:.8f}")
        H.append({"nama": nm, "detik": r["detik"], "baik": baik,
                  "in": u.get("prompt_tokens", 0), "think": u.get("completion_thinking_tokens", 0),
                  "out": u.get("completion_tokens", 0), "cost": c, "teks": r.get("teks", "")})

    # laporan akhir
    bahan = "\n\n".join(f"=== {h['nama'].upper()} ===\n{h['teks'][:2200] if h['baik'] else '(gagal)'}" for h in H)
    r = chat('Anda penyusun laporan untuk mahasiswa. Diberikan hasil pemeriksaan naskah. '
             'Susun LAPORAN (maks 300 kata): status, temuan utama, PRIORITAS PERBAIKAN 3 teratas. '
             'Gaya lugas, siap dikerjakan.', bahan, 2000)
    u = r.get("usage", {}); c = float(u.get("cost") or 0)
    baik = r["ok"] and bool(r["teks"].strip())
    print(f"    [{len(H)+1}] {'laporan_akhir':30s} {'OK ' if baik else 'GAGAL'} {r['detik']:6.1f}s "
          f"in={u.get('prompt_tokens',0):>7,} out={u.get('completion_tokens',0):>5,} ${c:.8f}")
    H.append({"nama": "laporan_akhir", "detik": r["detik"], "baik": baik,
              "in": u.get("prompt_tokens", 0), "think": u.get("completion_thinking_tokens", 0),
              "out": u.get("completion_tokens", 0), "cost": c, "teks": r.get("teks", "")})

    durasi = time.monotonic() - t0
    b = metrik()
    hasil = {
        "bab": nama, "kata": len(naskah.split()), "karakter": len(naskah),
        "putaran": len(H), "putaran_sukses": sum(1 for h in H if h["baik"]),
        "total_in": sum(h["in"] for h in H), "total_out": sum(h["out"] for h in H),
        "total_think": sum(h["think"] for h in H),
        "total_token": sum(h["in"] + h["out"] for h in H),
        "biaya_usd": sum(h["cost"] for h in H), "durasi_detik": durasi,
        "saldo_awal": a["saldo"], "saldo_akhir": b["saldo"],
        "selisih_saldo": a["saldo"] - b["saldo"], "laporan": H[-1]["teks"],
    }
    print(f"  → TOTAL: {hasil['total_token']:,} token | ${hasil['biaya_usd']:.8f} | "
          f"{durasi:.1f}s | selisih saldo {hasil['selisih_saldo']:.6f} USDC")
    return hasil


def main():
    print(f"MODEL: {MODEL}")
    sem = []
    for nama, f in [("BAB I", "/tmp/bab1_goras.txt"), ("BAB II", "/tmp/bab2_goras.txt"),
                    ("BAB III", "/tmp/bab3_goras.txt")]:
        sem.append(jalankan_bab(nama, Path(f).read_text()))

    print("\n" + "=" * 86)
    print("PERBANDINGAN BIAYA AGENTIC PER BAB")
    print("=" * 86)
    print(f"{'BAB':8s} {'kata':>7s} {'tok_in':>9s} {'tok_out':>8s} {'TOTAL':>9s} "
          f"{'USD':>12s} {'Rp':>8s} {'detik':>7s} {'putaran':>8s}")
    print("-" * 86)
    for s in sem:
        print(f"{s['bab']:8s} {s['kata']:>7,} {s['total_in']:>9,} {s['total_out']:>8,} "
              f"{s['total_token']:>9,} {s['biaya_usd']:>12.8f} {s['biaya_usd']*16000:>8.2f} "
              f"{s['durasi_detik']:>7.1f} {s['putaran_sukses']}/{s['putaran']:>4}")

    print("\n=== URUTAN DARI YANG PALING MAHAL ===")
    for s in sorted(sem, key=lambda x: -x["biaya_usd"]):
        print(f"  {s['bab']:8s} ${s['biaya_usd']:.8f}  ({s['kata']:,} kata)")

    OUT.write_text(json.dumps(sem, indent=1))
    print(f"\n✓ tersimpan: {OUT}")


if __name__ == "__main__":
    main()
