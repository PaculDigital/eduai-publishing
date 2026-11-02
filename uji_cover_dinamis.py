#!/usr/bin/env python3
"""Uji offline modul cover dinamis (Gas Bos 2 Nov 2026).

TANPA jaringan nyata, TANPA kredit, TANPA order buku, TANPA deploy.
Gambar memakai gambar yang sudah ada di workspace, bukan gambar baru.
Jalankan dari folder repo: python3 uji_cover_dinamis.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import susun_cover_dinamis as C
from PIL import Image

GAMBAR_BUMI = '/home/hatch/workspace/gambar-sampul-bumi-v3-20261102.jpg'
GAMBAR_MAT = '/home/hatch/workspace/uji-literasi-2026/media-generation-gambar-tema-cover-matematika-0-7e8010a3-a89a-41b8-96fb-b89919b61b52.png'


def cek(nama, syarat):
    print(("OK  " if syarat else "GAGAL ") + nama)
    if not syarat:
        raise SystemExit(1)


def main():
    cek("keluarga UMKM jadi bisnis", C.pilih_keluarga("Literasi Digital untuk UMKM", "") == "bisnis")
    cek("keluarga Matematika jadi pendidikan", C.pilih_keluarga("Matematika Dasar", "") == "pendidikan")
    cek("keluarga tidak dikenal jadi umum", C.pilih_keluarga("Topik Tanpa Kata Kunci Xyz", "") == "umum")
    cek("gaya Referensi utama realistis", C.pilih_gaya("referensi", "UMKM", "") == "realistis")
    cek("gaya Monograf utama minimalis", C.pilih_gaya("monograf", "Teori Sosial", "") == "minimalis")
    cek("gaya Umum utama 3d", C.pilih_gaya("umum", "Kreativitas", "") == "3d")
    cek("shot strategi jadi macro", C.pilih_shot("strategi dan keputusan dengan bidak catur") == "macro")
    cek("shot sistem jadi drone", C.pilih_shot("sistem pasar dan distribusi") == "drone")
    satu = C.pilih_cover("referensi", "Literasi Digital untuk UMKM", "Literasi Digital untuk UMKM", "penjual terkejut")
    dua = C.pilih_cover("referensi", "Literasi Digital untuk UMKM", "Literasi Digital untuk UMKM", "penjual terkejut")
    cek("pilih cover deterministik", satu == dua)
    cek("pilih cover Referensi UMKM klasik tosca", satu["varian"] == "klasik" and satu["aksen"] == (15, 118, 110) and satu["keluarga"] == "bisnis")
    cek("cek cover valid lolos", C.cek_cover(satu, "Literasi Digital untuk UMKM", "Nama Penulis", "PT Bayana Hasana Duna") == [])
    cek("cek cover em dash ditolak", len(C.cek_cover(satu, "Judul\u2014Salah", "Nama Penulis", "PT Bayana")) > 0)
    cek("cek cover varian liar ditolak", len(C.cek_cover({**satu, "varian": "liar"}, "Judul", "Penulis", "Penerbit")) > 0)

    with tempfile.TemporaryDirectory() as tmp:
        previews = C.preview_depan(
            GAMBAR_BUMI, "referensi", "BUKU REFERENSI",
            ["Literasi Digital", "untuk UMKM"], "Nama Penulis",
            "PT Bayana Hasana Duna  •  2026", "bisnis", tmp, "preview-umkm")
        cek("preview Referensi tepat 3", len(previews) == 3)
        cek("preview Referensi varian tersaring", [os.path.basename(p) for p in previews] == [
            "preview-umkm-1-klasik.png", "preview-umkm-2-minimal.png", "preview-umkm-3-foto_penuh_atas.png"])
        for p in previews:
            im = Image.open(p)
            cek(f"preview ukuran 1240x1754 {os.path.basename(p)}", im.size == (1240, 1754))

        depan = C.susun_depan(
            GAMBAR_MAT, "BUKU AJAR", ["Matematika", "Dasar"], "Nama Penulis",
            "PT Bayana Hasana Duna  •  2026", (29, 78, 216), (219, 234, 254),
            "minimal", os.path.join(tmp, "depan-mat.png"))
        cek("susun depan Minimal Matematika ukuran benar", Image.open(depan).size == (1240, 1754))

        foto_uji = os.path.join(tmp, "foto.png")
        Image.new('RGB', (400, 500), (200, 180, 160)).save(foto_uji)
        belakang = C.susun_belakang(
            "Matematika Dasar",
            "Matematika Dasar mengajak pembaca memahami konsep dasar lewat contoh nyata dan latihan bertahap.",
            foto_uji,
            "Penulis adalah dosen yang menulis tentang matematika dasar untuk mahasiswa dan pembaca umum.",
            (29, 78, 216), (219, 234, 254), os.path.join(tmp, "belakang-foto.png"))
        cek("susun belakang dengan foto ukuran benar", Image.open(belakang).size == (1240, 1754))

        belakang_kosong = C.susun_belakang(
            "Matematika Dasar",
            "Matematika Dasar mengajak pembaca memahami konsep dasar lewat contoh nyata.",
            None, "",
            (29, 78, 216), (219, 234, 254), os.path.join(tmp, "belakang-kosong.png"))
        cek("susun belakang tanpa foto dan bio tetap jadi, placeholder", Image.open(belakang_kosong).size == (1240, 1754))
    print("SEMUA UJI COVER DINAMIS LULUS (mock, tanpa jaringan nyata, tanpa kredit)")


if __name__ == "__main__":
    main()
