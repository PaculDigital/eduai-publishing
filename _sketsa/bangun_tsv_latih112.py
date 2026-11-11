#!/usr/bin/env python3
"""Bangun ground_truth/ground_truth_latih112.tsv dari paket sengketa terpilih
+ label Wulan (tahap 3 latihan Jev/Hakim 112 naskah).

NOL panggilan Jev. Semua dari berkas tersimpan:
  _sketsa/paket_sengketa_terpilih.json  (254 baris terpilih)
  _sketsa/label_sementara.json         (label butir 1-254)
  pembagian.json                        (nama bidang kanonik per kode)
  teks_latih/<bidang>/                  (hanya untuk mengisi konteks 15 butir
                                         yang konteksnya kosong di paket)

Format TSV mengikuti paket lama (ground_truth_81.tsv dkk):
  no, jenis_sengketa, naskah, baris_no, teks_baris, konteks_sebelum,
  konteks_sesudah, bukti_run, label_benar, catatan_boss
Konteks beberapa baris digabung dengan ' | '. BOM dibersihkan dari teks.
catatan_boss berisi alasan label dari Wulan (awalan 'Wulan: '), mengikuti
praktik paket lama.

Aturan teks_baris:
- Bila konteks paket ada: teks_baris = baris mentah utuh pada posisi target
  (indeks len(konteks)-7, yaitu 6 baris sesudah). Bila cuplikan run hanya
  fragmen/ekor judul dari baris itu, fragmen dicatat di bukti_run.
- Bila konteks paket kosong (15 butir): teks_baris = cuplikan run apa adanya,
  konteks dicari bertarget di teks mentah lewat jangkar (lihat JANGKAR).
"""
import csv
import glob
import json
import os

DASAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAKET = os.path.join(DASAR, "_sketsa", "paket_sengketa_terpilih.json")
LABEL = os.path.join(DASAR, "_sketsa", "label_sementara.json")
PEMBAGIAN = os.path.join(DASAR, "pembagian.json")
KELUAR = os.path.join(DASAR, "ground_truth", "ground_truth_latih112.tsv")
RINGKASAN = os.path.join(DASAR, "ground_truth", "ringkasan_latih112.json")

# Butir tanpa konteks di paket -> (jangkar pencarian, direktori teks, berkas bila spesifik)
JANGKAR = {
    11: ("Tujuan Khusus", "administrasi-niaga", None),
    20: ("Tabel 4.1", "akuntansi", None),
    26: ("kendatipun", "bahasa-inggris", None),
    63: ("Pembantuan", "hukum-pidana", None),
    65: ("Buat layer baru", "informatika-multimedia", None),
    66: ("Movie Prambanan", "informatika-multimedia", None),
    100: ("Sistem Pemantauan Ketinggian Air", "pendidikan-elektro", None),
    105: ("alat penerima bunyi", "pendidikan-elektro", None),
    169: ("IMPLEMENTASI SISTEM dan HASIL PROGRAM", "informatika", "995314081_Full.txt"),
    170: ("PENUTUP", "informatika", "995314081_Full.txt"),
    183: ("Homogen", "pendidikan-bhs-arab", "skripsi-mulyani.txt"),
    184: ("Kesimpulan yang didapat adalah HoT", "pendidikan-bhs-arab", "skripsi-mulyani.txt"),
    189: ("Konsep metode menghafal", "pendidikan-bhs-arab", None),
    225: ("Jumlah Perceraian di Surabaya", "psikologi", "psikologi-skripsi.txt"),
    253: ("Unit Usaha Syariah", "tesis", "V1_tesis_root_1st_5th_chapter_seri.txt"),
}


def bersih(baris):
    return baris.replace("\ufeff", "").strip()


def gabung(baris_list):
    return " | ".join(bersih(b) for b in baris_list if bersih(b))


def cari_konteks(no, jangkar, direktori, berkas):
    """Cari baris jangkar di teks mentah, kembalikan (sebelum, sesudah, no_baris)."""
    folder = os.path.join(DASAR, "teks_latih", direktori)
    daftar = [os.path.join(folder, berkas)] if berkas else sorted(glob.glob(os.path.join(folder, "*.txt")))
    for jalan in daftar:
        with open(jalan, encoding="utf-8", errors="replace") as f:
            baris = f.read().splitlines()
        for i, b in enumerate(baris):
            if jangkar in b:
                return baris[max(0, i - 3):i], baris[i + 1:i + 4], i + 1
    raise SystemExit(f"jangkar butir {no} tidak ditemukan: {jangkar!r} di {folder}")


def utama():
    paket = json.load(open(PAKET, encoding="utf-8"))
    label = json.load(open(LABEL, encoding="utf-8"))
    pembagian = json.load(open(PEMBAGIAN, encoding="utf-8"))
    kode_ke_bidang = {}
    for b in pembagian["bidang"]:
        for kode in b["belajar"] + b["uji"]:
            kode_ke_bidang[kode] = b["bidang"]

    assert len(paket) == 254, len(paket)
    assert len(label) == 254, len(label)

    baris_keluar = []
    statistik = {"dari_baris_utuh": 0, "dari_cuplikan": 0, "konteks_jangkar": 0}
    for i, butir in enumerate(paket, start=1):
        lab, alasan = label[str(i)]
        konteks = butir["konteks"]
        bukti = butir["bukti"]
        if butir.get("kode_lain"):
            bukti += " | duplikat teks juga di: " + ", ".join(butir["kode_lain"])
        no_baris = butir.get("no_baris_mentah") or ""
        if konteks:
            target = len(konteks) - 7
            baris_utuh = bersih(konteks[target])
            cuplikan = bersih(butir["cuplikan"])
            if baris_utuh != cuplikan:
                bukti += f" | cuplikan run (fragmen/ekor): {cuplikan!r}"
                statistik["dari_baris_utuh"] += 1
            else:
                statistik["dari_cuplikan"] += 1
            teks = baris_utuh
            sebelum = gabung(konteks[:target])
            sesudah = gabung(konteks[target + 1:])
        else:
            jangkar, direktori, berkas = JANGKAR[i]
            sebelum_list, sesudah_list, no_baris = cari_konteks(i, jangkar, direktori, berkas)
            teks = bersih(butir["cuplikan"])
            sebelum = gabung(sebelum_list)
            sesudah = gabung(sesudah_list)
            bukti += " | konteks diisi bertarget dari teks mentah (paket kosong)"
            statistik["konteks_jangkar"] += 1
            statistik["dari_cuplikan"] += 1
        baris_keluar.append({
            "no": i,
            "jenis_sengketa": butir["jenis"],
            "naskah": butir["kode"],
            "baris_no": no_baris,
            "teks_baris": teks,
            "konteks_sebelum": sebelum,
            "konteks_sesudah": sesudah,
            "bukti_run": bukti,
            "label_benar": lab,
            "catatan_boss": f"Wulan: {alasan}",
            "_bidang": kode_ke_bidang.get(butir["kode"], butir["bidang"]),
        })

    kolom = ["no", "jenis_sengketa", "naskah", "baris_no", "teks_baris",
             "konteks_sebelum", "konteks_sesudah", "bukti_run",
             "label_benar", "catatan_boss"]
    with open(KELUAR, "w", encoding="utf-8", newline="") as f:
        tulis = csv.DictWriter(f, fieldnames=kolom, delimiter="\t",
                               extrasaction="ignore", lineterminator="\n")
        tulis.writeheader()
        tulis.writerows(baris_keluar)

    from collections import Counter
    per_bidang = Counter(r["_bidang"] for r in baris_keluar)
    per_jenis = Counter(r["jenis_sengketa"] for r in baris_keluar)
    per_label = Counter(r["label_benar"] for r in baris_keluar)
    per_bidang_label = {}
    for r in baris_keluar:
        per_bidang_label.setdefault(r["_bidang"], Counter())[r["label_benar"]] += 1
    ringkasan = {
        "berkas": "ground_truth_latih112.tsv",
        "total_baris": len(baris_keluar),
        "tanggal": "2026-11-11",
        "panggilan_jev": 0,
        "per_bidang": dict(sorted(per_bidang.items())),
        "per_jenis": dict(sorted(per_jenis.items())),
        "per_label": dict(sorted(per_label.items())),
        "per_bidang_label": {k: dict(sorted(v.items())) for k, v in sorted(per_bidang_label.items())},
        "bidang_tanpa_baris": ["teknik-pertanian"],
        "alasan_bidang_tanpa_baris": (
            "Satu-satunya naskah belajar teknik-pertanian (Y1) adalah grup 3; "
            "ketujuh kandidatnya berbasis idx yang ditunda (lihat _sketsa/"
            "kandidat_idx_grup3_tertunda.json), jadi tidak ada baris yang lolos."
        ),
        "teks_dari_baris_utuh": statistik["dari_baris_utuh"],
        "teks_dari_cuplikan": statistik["dari_cuplikan"],
        "konteks_diisi_jangkar": statistik["konteks_jangkar"],
        "kandidat_idx_grup3_tertunda": 738,
        "catatan": (
            "Label diisi Wulan dari teks (bukan Boss). Satu baris berlabel ragu "
            "(no 132). 41 dari 42 bidang terwakili."
        ),
    }
    json.dump(ringkasan, open(RINGKASAN, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"TSV: {len(baris_keluar)} baris -> {KELUAR}")
    print("statistik:", statistik)
    print("per_label:", dict(per_label))
    print("per_bidang:", dict(sorted(per_bidang.items())))


if __name__ == "__main__":
    utama()
