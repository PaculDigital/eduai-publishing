
import json, sys, time
sys.path.insert(0, "/app")
import peta3_jev as P
from app import satpam

POLA = {
 "paragraf": "satu atau beberapa KALIMAT MENGALIR penuh (ada subjek-predikat, diakhiri titik, panjang)",
 "butir": "baris DAFTAR: ada penanda di awal (a./b./1./2./-) lalu teks SINGKAT/FRAGMEN",
 "judul_isi": "JUDUL bagian akademik (mis. 2.1 Landasan Teori, 1.1 Latar Belakang) — pendek, tanpa titik akhir",
 "tabel": "baris di dalam TABEL: potongan sel, nama orang, angka halaman, judul kolom",
}
TANYA = {"c1": {"type": "choice",
  "instructions": "Bahan berikut 5 baris berurutan dari naskah. Baris yang ditandai (c1.tengah) BENTUKNYA apa?",
  "criteria": dict(POLA)}}

KASUS = [
 (78, 358, "judul_isi"), (78, 606, "judul_isi"), (78, 620, "judul_isi"), (78, 638, "judul_isi"),
 (115, 2, "judul_isi"), (115, 877, "butir"), (115, 3486, "tabel"), (115, 7997, "tabel"),
 (115, 8019, "tabel"), (115, 555, "paragraf"), (115, 4000, "paragraf"), (115, 6000, "paragraf"),
]
CACHE = {}
for fid in {k[0] for k in KASUS}:
    CACHE[fid] = P.petakan(fid, None, None, putaran=1)["baris"]

hasil = []
for fid, i, kunci in KASUS:
    b = CACHE[fid]
    # JENDELA 5 BARIS (lebih lebar)
    konteks = []
    for d in range(-2, 3):
        j = i + d
        if 0 <= j < len(b):
            tanda = ">>>" if d == 0 else "   "
            konteks.append("%s L%06d| %s" % (tanda, j, " ".join(b[j].split())[:80]))
    pak = {"isi": "\n".join(konteks)}
    bahan = json.dumps({"c1": pak}, ensure_ascii=False)
    pilih, confs = [], []
    for k in range(3):
        jw = satpam.tanya_bebas_mutu(bahan, TANYA) or {}
        blk = jw.get("c1") or {}
        v = blk.get("choice")
        if isinstance(v, dict): v = v.get("id") or v.get("label")
        c = blk.get("confidence")
        pilih.append(v); confs.append(float(c) if c is not None else None)
        time.sleep(0.4)
    vs = [x for x in pilih if x]
    utama = max(set(vs), key=vs.count) if vs else None
    cc = [c for c in confs if c is not None]
    conf = round(sum(cc)/len(cc), 2) if cc else None
    ok = utama == kunci
    hasil.append((fid, i, kunci, utama, conf, ok))
    print("[fid=%d L%06d] kunci=%-10s → %-10s conf=%-5s %s" % (fid, i, kunci, str(utama), str(conf), "OK" if ok else "SALAH"))

b_ok = sum(1 for h in hasil if h[5])
print()
print("RINGKASAN ULANG (jendela 5 baris) — %d/%d BENAR (%.0f%%)" % (b_ok, len(hasil), 100*b_ok/len(hasil)))
