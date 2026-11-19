"""Render pustaka_hasil.html + naskah.html dengan data fid 81 (19 Nov 2026).

Cek Daftar Pustaka Hidup: ceklist 56 baris, tiap baris penulis-tahun +
dikutip/tidak dikutip, 'Langkah berikut' berisi hitungan yang benar,
ketuk baris menunjuk kartu lengkapnya (id entri-...), tidak ada kata
'salah' di teks tampil.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader(str(ROOT / "app" / "templates")))


def cek(nama, benar):
    print(("  LULUS  " if benar else "  GAGAL  ") + nama)
    return benar


def main():
    hasil = json.loads(
        (ROOT / "tests" / "fixtures" / "pustaka" / "hasil_fid81.json")
        .read_text(encoding="utf-8"))
    alasan = {}
    t = env.get_template("pustaka_hasil.html")
    html = t.render(hasil=hasil, fid=81, alasan=alasan,
                    keadaan="selesai", sisa_jeda=0, pesan=None,
                    fid_nama="SKRIPSI-Asih-Susanti-Putri.docx")
    ok = True
    n = html.count('class="baris-entri')
    ok &= cek("ceklist pustaka: 56 baris entri",
              n == len(hasil["entri"]) == 56)
    ok &= cek("ceklist: tiap baris punya data-entri ke kartu lengkap",
              html.count('data-entri="e') == 56
              and html.count('id="entri-e') == 56)
    ok &= cek("ceklist: penulis-tahun tampil (Agil 2023)",
              "Agil" in html and "(2023)" in html)
    ok &= cek("ceklist: penanda dikutip / tidak dikutip tampil",
              "dikutip" in html and "tidak dikutip" in html)
    ring = hasil["ringkasan"]
    langkah = (f"{ring['sitasi_tanpa_entri']} sitasi belum ada entrinya, "
               f"{ring['entri_tanpa_sitasi']} entri belum dikutip")
    ok &= cek("langkah berikut pustaka berisi hitungan benar",
              langkah in html)
    # Kata 'salah' tidak boleh di teks tampil (kelas CSS .tidak boleh).
    import re
    teks = re.sub(r"<[^>]+>", " ", html)
    teks = re.sub(r"\s+", " ", teks)
    ok &= cek("tidak ada kata 'salah' di teks tampil pustaka",
              "salah" not in teks.lower())
    print("\nLULUS" if ok else "\nGAGAL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
