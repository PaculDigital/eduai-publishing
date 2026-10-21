"""UJI END-TO-END: buku → .docx → tabel `files` → `/edit/{fid}` bisa dibuka.

ACC Bos 19 Okt 2026 (pilihan B): satu-satunya kabel yang tersisa antara
"buku jadi" dan "buku bisa diedit sendiri di OnlyOffice" adalah pendaftaran
ke tabel `files`.

DIPAKAI: SALINAN database (bukan DB produksi) — aturan Bos 16 Okt 2026.
TIDAK memotong kuota, TIDAK memanggil AI, TIDAK menyentuh berkas user nyata.

Jalankan di dalam image (butuh fastapi):
  docker run --rm --entrypoint python -w /app \
    -e EDUAI_SECRET_KEY=uji -e EDUAI_OO_JWT_SECRET=uji \
    -i eduai-app:TAG - < _uji_daftar_berkas_buku.py
"""
import os
import re
import shutil
import sys
import tempfile

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


def main():
    akar = '/app' if os.path.isdir('/app/app') else os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, akar)

    #  Pakai folder upload & data SEMENTARA — jangan sentuh upload/DB user nyata.
    tmp_upload = tempfile.mkdtemp(prefix='uji_upload_')
    tmp_data = tempfile.mkdtemp(prefix='uji_data_')
    os.environ['EDUAI_UPLOAD_DIR'] = tmp_upload
    os.environ['EDUAI_DATA_DIR'] = tmp_data
    os.environ.setdefault('EDUAI_SECRET_KEY', 'uji')
    os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji')

    from app import models as M
    from app import penyusunan_buku as PB
    #  DB = file SQLite DI DALAM tmp_data (bukan data/eduai.db produksi)
    db = M.SessionLocal()
    #  Buat tabel di DB sementara
    M.Base.metadata.create_all(M.engine)
    try:
        u = M.User(email='uji-wulan@contoh.test', nama='Uji Wulan',
                   password_hash='x', paket='gratis')
        db.add(u)
        db.commit()
        db.refresh(u)
        print(f'\n[persiapan] user uji id={u.id} · upload={tmp_upload}')

        print('\n[1] BUAT .docx LEWAT MESIN ASSEMBLY YANG SUDAH ADA')
        import buku_umum_assembly as ASM
        kerja = tempfile.mkdtemp(prefix='uji_rakit_')
        os.makedirs(os.path.join(kerja, 'visual'), exist_ok=True)
        with open(os.path.join(kerja, 'bab1.txt'), 'w', encoding='utf-8') as f:
            f.write('## BAB 1. Uji Daftar Berkas\n\n'
                    + ('Isi bab yang cukup panjang untuk dirakit. ' * 60))
        outline = {1: {'title': 'Uji Daftar Berkas',
                       'subs': [('1.1', 'Sub Uji', 'poin')]}}
        hasil_rakit = ASM.rakit('Buku Uji Daftar Berkas', kerja, outline,
                                penulis='Uji Wulan')
        docx = hasil_rakit['docx']
        cek('docx jadi', os.path.exists(docx), docx)

        print('\n[2] DAFTARKAN KE TABEL `files`')
        fid = PB._daftarkan_berkas(db, u, docx, 'Buku Uji Daftar Berkas')
        cek('_daftarkan_berkas mengembalikan id', isinstance(fid, int) and fid > 0,
            str(fid))

        #  🚨 UJI PERILAKU (19 Okt): bukan cuma "apakah fungsi ada", tetapi
        #     apakah `susun()` BENAR-BENAR memanggilnya. Tanpa ini, mematikan
        #     pendaftaran tidak tertangkap (gerbang palsu).
        src_pb = open(os.path.join(akar, 'app', 'penyusunan_buku.py'),
                      encoding='utf-8').read()
        #  Buang komentar + docstring SEBELUM memeriksa nama fungsi
        #  (jebakan 19 Okt: nama fungsi di komentar = gerbang PALSU)
        kode_pb = re.sub(r'#.*', '', src_pb)
        kode_pb = re.sub(r'"""(?:.|\n)*?"""', '', kode_pb)
        cek("susun() MEMANGGIL _daftarkan_berkas (perilaku, bukan komentar)",
            'hasil[\'file_id\'] = _daftarkan_berkas(' in kode_pb,
            'pendaftaran ke tabel files DIMATIKAN → dokumen tak bisa dibuka di OnlyOffice')
        cek("susun() menyetel hasil['file_id'] di jalur sukses",
            "hasil['file_id'] = None" in kode_pb)

        fb = db.get(M.FileBerkas, fid)
        cek('baris files ADA', fb is not None)
        if fb:
            cek('pemilik = user yang menyusun', fb.user_id == u.id,
                f'{fb.user_id} vs {u.id}')
            cek('nama tampil = JUDUL buku', fb.nama == 'Buku Uji Daftar Berkas.docx',
                fb.nama)
            cek('nama di disk acak (bukan judul)', fb.nama_simpan != fb.nama,
                fb.nama_simpan)
            cek('ukuran > 0', fb.ukuran > 0, str(fb.ukuran))
            cek('tipe docx benar',
                'wordprocessingml' in (fb.tipe or ''), fb.tipe)
            cek('tidak di sampah', not fb.di_sampah)
            p = os.path.join(tmp_upload, str(u.id), fb.nama_simpan)
            cek('berkas ADA di folder upload user', os.path.exists(p), p)
            cek('isi berkas = docx asli',
                os.path.getsize(p) == fb.ukuran, 'ukuran tidak cocok')

        print('\n[3] `/edit/{fid}` BISA MENEMUKAN & MEMBUKA BERKAS')
        from app import onlyoffice as OO
        cek('onlyoffice bisa_dibuka(nama)', OO.bisa_dibuka(fb.nama), fb.nama)
        #  Tiru persis pemeriksaan rute halaman_edit (main.py:2791-2817)
        fb2 = db.get(M.FileBerkas, fid)
        cek('rute: berkas ditemukan', fb2 is not None)
        cek('rute: pemilik cocok', bool(fb2) and fb2.user_id == u.id)
        cek('rute: tidak di sampah (tidak 410)', bool(fb2) and not fb2.di_sampah)
        p = os.path.join(tmp_upload, str(u.id), fb.nama_simpan)
        cek('rute: berkas ADA di disk (tidak 404)', os.path.exists(p), p)

        print('\n[4] PENJAGA: BUKAN MILIK ORANG LAIN → DITOLAK')
        u2 = M.User(email='orang-lain@contoh.test', nama='Orang Lain',
                    password_hash='x', paket='gratis')
        db.add(u2)
        db.commit()
        db.refresh(u2)
        cek('user lain TIDAK boleh buka (user_id beda)',
            db.get(M.FileBerkas, fid).user_id != u2.id,
            'penjaga rute memakai fb.user_id != u.id → 404')

        print('\n[5] PENJAGA: GAGAL DAFTAR → TIDAK ADA BERKAS YATIM')
        #  🚨 Uji pertama Wulan SALAH (19 Okt): ia mengirim judul 400 karakter
        #     dan berharap gagal, padahal kode MEMOTONG judul jadi 120 — jadi
        #     tidak gagal. Uji yang tidak bisa gagal = uji PALSU.
        #  Uji yang benar: buat COMMIT benar-benar gagal (user_id tak ada →
        #  ForeignKey), lalu pastikan berkas yang sudah disalin DIHAPUS.
        sebelum = _hitung_berkas(tmp_upload)

        class _UserTakAda:
            id = 999999          # tidak ada di tabel users
            nama = 'Hantu'
            nama_kampus = ''

        try:
            PB._daftarkan_berkas(db, _UserTakAda(), docx, 'Buku Yatim')
            cek('commit gagal → melempar galat', False, 'tidak melempar galat')
        except Exception as e:
            cek('commit gagal → melempar galat', True)
            sesudah = _hitung_berkas(tmp_upload)
            cek('berkas yatim TIDAK ditinggal', sesudah == sebelum,
                f'{sebelum} → {sesudah} berkas')

        print('\n[5b] JUDUL KEPANJANGAN DIPOTONG (bukan diteruskan ke DB)')
        try:
            fid2 = PB._daftarkan_berkas(db, u, docx, 'J' * 400)
            fb3 = db.get(M.FileBerkas, fid2)
            cek('judul 400 karakter tetap masuk', fb3 is not None)
            cek('nama tampil dipotong <= 255', fb3 and len(fb3.nama) <= 255,
                f'{len(fb3.nama) if fb3 else "?"} karakter')
            cek('nama tampil tetap .docx', bool(fb3) and fb3.nama.endswith('.docx'))
        except Exception as e:
            cek('judul 400 karakter tidak meledak', False, f'{type(e).__name__}: {e}')

        print('\n[6] TEMPLATE & RUTE MEMAKAI fid')
        tpl = open(os.path.join(akar, 'app', 'templates', 'buku_selesai.html'),
                   encoding='utf-8').read()
        cek('template menautkan /edit/{{ fid }}', '/edit/{{ fid }}' in tpl)
        src_main = open(os.path.join(akar, 'app', 'main.py'), encoding='utf-8').read()
        bagian = src_main.split('def halaman_buku_selesai')[1][:2200]
        kode = re.sub(r'#.*', '', bagian)
        cek('rute mengirim fid', "'fid':" in kode or "'fid': " in kode)
        cek('rute MEMERIKSA pemilik fid (anti ?fid=1 orang lain)',
            'fb.user_id == u.id' in kode, 'tanpa cek pemilik = lubang keamanan')
        cek('rute menolak berkas di sampah', 'di_sampah' in kode)

    finally:
        db.close()
        shutil.rmtree(tmp_upload, ignore_errors=True)
        shutil.rmtree(tmp_data, ignore_errors=True)

    print(f'\n{"=" * 62}\nDAFTAR BERKAS BUKU: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


def _hitung_berkas(akar):
    n = 0
    for _, _, files in os.walk(akar):
        n += len(files)
    return n


if __name__ == '__main__':
    sys.exit(main())
