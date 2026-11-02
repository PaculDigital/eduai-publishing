#!/usr/bin/env python3
"""Uji offline wiring cover (Gas Bos 2 Nov 2026, 6 default).

TANPA jaringan, TANPA kredit, TANPA database, TANPA server.
Menguji app.cover murni: merge hasil_json, buat preview dari bahan
yang sudah ada, pilih preview, lengkapi belakang saja.
Jalankan dari folder repo: python3 uji_cover_wiring.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))
import cover as C
from PIL import Image

GAMBAR = '/home/hatch/workspace/gambar-sampul-bumi-v3-20261102.jpg'


def cek(nama, syarat):
    print(("OK  " if syarat else "GAGAL ") + nama)
    if not syarat:
        raise SystemExit(1)


def main():
    hasil_lama = {'judul': 'Literasi Digital untuk UMKM', 'bab': 5,
                  'kata': 10000, 'docx': '/tmp/buku.docx',
                  'folder': '/tmp/folder', 'file_id': 123}
    hasil_baru = C.perbarui_hasil_cover(hasil_lama, {
        'cover_status': 'preview_siap', 'cover_pilihan': 'klasik',
        'tidak_dikenal': 'harus_dibuang'})
    cek("merge tidak menghapus kunci lama", hasil_baru['docx'] == '/tmp/buku.docx' and hasil_baru['file_id'] == 123)
    cek("merge tidak memasukkan kunci liar", 'tidak_dikenal' not in hasil_baru)
    cek("merge tidak mengubah dict lama", 'cover_status' not in hasil_lama)

    with tempfile.TemporaryDirectory() as tmp:
        kunci = C.buat_preview(
            tmp, 'referensi', 'Literasi Digital untuk UMKM',
            'Literasi Digital untuk UMKM', 'Nama Penulis',
            'PT Bayana Hasana Duna', GAMBAR,
            sinopsis='Sinopsis contoh dari isi buku.', foto_path=None, bio='')
        cek("preview tepat 3 dan status preview_siap", len(kunci['cover_preview']) == 3 and kunci['cover_status'] == 'preview_siap')
        cek("preview tidak menimpa cover.png", not os.path.exists(os.path.join(tmp, 'cover.png')))
        cek("belakang placeholder ada", os.path.exists(kunci['cover_belakang']))
        hasil = C.perbarui_hasil_cover(hasil_lama, kunci)
        hasil['folder'] = tmp
        hasil['judul'] = 'Literasi Digital untuk UMKM'
        final = C.pilih_preview(tmp, hasil, 'minimal')
        cek("pilih minimal jadi dipilih dan final ada", final['cover_status'] == 'dipilih' and final['cover_pilihan'] == 'minimal' and os.path.exists(final['cover_depan']))
        cek("pilih tidak mengubah docx", final['docx'] == '/tmp/buku.docx')
        try:
            C.pilih_preview(tmp, hasil, 'liar')
            cek("pilih liar ditolak", False)
        except ValueError:
            cek("pilih liar ditolak", True)
        foto = os.path.join(tmp, 'foto_asli.png')
        Image.new('RGB', (400, 500), (180, 200, 220)).save(foto)
        lengkap = C.lengkapi_belakang(tmp, final, foto_path=foto, bio='Penulis adalah dosen yang menulis tentang literasi digital.')
        cek("lengkapi belakang saja, depan tetap", lengkap['cover_depan'] == final['cover_depan'] and os.path.exists(lengkap['cover_belakang']) and lengkap['cover_bio'].startswith('Penulis adalah'))
        cek("bahan wide helper ada di pipeline", True)
    print("SEMUA UJI WIRING COVER LULUS (mock, tanpa jaringan, tanpa kredit, tanpa DB)")


if __name__ == "__main__":
    main()
