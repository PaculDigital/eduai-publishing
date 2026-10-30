"""GERBANG BUKU LATAR — pekerjaan dititipkan, bukan ditunggu (ACC Bos 19 Okt 2026).

MASALAH YANG DIPERBAIKI (terukur): buku 6 bab = ±36 menit SATU request.
Tab ditutup = pekerjaan jalan tapi user tidak tahu apa-apa. Cloudflare bisa
memutus di ±125 dtk (HTTP 524) — pola SAMA dengan bug revisi 16 Sep yang
sudah dipecahkan `app/proses.py`.

YANG DIUJI (TANPA AI, TANPA KUOTA, DB SEMENTARA):
  [1] ATURAN: `/buku/susun` TIDAK memanggil `susun()` secara sinkron lagi
  [2] ATURAN: kuota TETAP dipotong di dalam `susun()` (bukan dipindah)
  [3] ATURAN: rute membuat baris `proses_ai` + mengalihkan ke halaman pantau
  [4] PERILAKU: pekerjaan latar BENAR-BENAR jalan & menandai selesai
  [5] PERILAKU: pekerjaan GAGAL → status 'gagal' + alasan tersimpan
  [6] PENJAGA: halaman pantau menolak kode milik user LAIN
  [7] HALAMAN: tidak memakai persen karangan; ada tautan ke hasil
  [8] HALAMAN: tidak membocorkan isi naskah

Jalankan di DALAM image (butuh fastapi):
  docker run --rm --entrypoint python -w /app \
    -e EDUAI_SECRET_KEY=uji -e EDUAI_OO_JWT_SECRET=uji -e EDUAI_ROUTER_KEY=uji \
    -i eduai-app:TAG - < _gerbang_buku_latar.py
"""
import os
import re
import shutil
import sys
import tempfile
import time

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


def _kode_tanpa_komentar(teks):
    """Buang komentar + docstring. JEBAKAN 19 Okt: nama fungsi di KOMENTAR
    membuat gerbang PALSU (lolos padahal kode sudah dicabut)."""
    t = re.sub(r'#.*', '', teks)
    t = re.sub(r'"""(?:.|\n)*?"""', '', t)
    t = re.sub(r"'''(?:.|\n)*?'''", '', t)
    t = re.sub(r'<script(?:.|\n)*?</script>', '', t)   # JS halaman punya komentar juga
    t = re.sub(r'/\*(?:.|\n)*?\*/', '', t)
    return t


def main():
    akar = '/app' if os.path.isdir('/app/app') else os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, akar)

    up = tempfile.mkdtemp(prefix='uji_up_')
    dat = tempfile.mkdtemp(prefix='uji_dat_')
    os.environ['EDUAI_UPLOAD_DIR'] = up
    os.environ['EDUAI_DATA_DIR'] = dat
    os.environ.setdefault('EDUAI_SECRET_KEY', 'uji')
    os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji')
    os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji')

    from app import models as M
    from app import proses as P
    M.Base.metadata.create_all(M.engine)
    db = M.SessionLocal()

    try:
        u = M.User(email='latarbuku@contoh.test', nama='Uji', password_hash='x',
                   paket='gratis')
        u2 = M.User(email='oranglain@contoh.test', nama='Lain', password_hash='x',
                    paket='gratis')
        db.add_all([u, u2])
        db.commit()
        db.refresh(u)
        db.refresh(u2)

        src_main = open(os.path.join(akar, 'app', 'main.py'), encoding='utf-8').read()
        main_bersih = _kode_tanpa_komentar(src_main)

        #  Ambil hanya badan fungsi buku_susun (bukan seluruh berkas — supaya
        #  rute LAIN yang memakai susun() tidak membuat uji gagal palsu).
        m = re.search(r'def buku_susun\(.*?(?=\n@_router_kolaborasi|\Z)', src_main, re.S)
        badan = _kode_tanpa_komentar(m.group(0) if m else '')
        cek('[0] badan fungsi buku_susun terbaca', len(badan) > 600,
            f'{len(badan)} karakter')

        print('\n[1] ATURAN: rute TIDAK menunggu mesin penyusun')
        #  Sinkron lama: `hasil = _susun.susun(db, u, ...)` dijalankan langsung.
        cek('tidak ada panggilan sinkron `_susun.susun(` di jalur rute',
            '_susun.susun(sdb' in badan and badan.count('_susun.susun(') == 1,
            'kalau >1 = masih ada jalur sinkron (user tetap menunggu 36 menit)')
        cek("memakai `_proses.jalankan(`", '_proses.jalankan(' in badan,
            'tanpa ini pekerjaan tidak jalan di latar')
        cek("memakai `_proses.mulai(`", '_proses.mulai(' in badan,
            'tanpa ini tidak ada baris status yang bisa dipantau')
        cek('mengalihkan ke halaman pantau',
            "'/buku/proses/'" in badan,
            'user tidak diarahkan ke halaman yang bisa dipantau')

        print('\n[2] ATURAN: kuota TETAP dipotong di dalam susun() (satu pintu)')
        src_susun = open(os.path.join(akar, 'app', 'penyusunan_buku.py'),
                         encoding='utf-8').read()
        susun_bersih = _kode_tanpa_komentar(src_susun)
        cek('susun() masih memotong kuota',
            'potong_banyak' in susun_bersih, 'gerbang biaya tercabut!')
        cek('rute TIDAK memotong kuota sendiri',
            'potong_banyak' not in badan,
            'dua tempat potong kuota = risiko terpotong 2×')

        print('\n[3] ATURAN: parameter pekerjaan DITITIPKAN (bisa dilanjutkan)')
        cek('judul dititipkan ke komentar_json',
            "'judul': judul" in badan or '"judul": judul' in badan,
            'tanpa ini pekerjaan tidak bisa dilanjutkan setelah request mati')

        print('\n[4] PERILAKU: pekerjaan latar BENAR-BENAR jalan & selesai')
        p1 = P.mulai(db, user_id=u.id, file_id=None, komentar=[],
                     jenis_dokumen='buku_umum', jumlah_bagian=1, panjang=10)
        jejak = []

        async def kerja_sukses(lapor):
            jejak.append('mulai')
            lapor.tahap('Menulis bab 1')
            jejak.append('tulis')
            P.tandai_selesai(p1.kode, hasil='Judul Uji',
                             hasil_json='{"bab_selesai": 2, "total_kata": 3000}')

        th = P.jalankan(p1.kode, kerja_sukses)
        for _ in range(60):
            db.expire_all()
            p = P.ambil(db, p1.kode)
            if p and p.status in ('selesai', 'gagal'):
                break
            time.sleep(0.1)
        db.expire_all()
        p = P.ambil(db, p1.kode)
        cek('pekerjaan dijalankan (utas hidup)', jejak == ['mulai', 'tulis'], str(jejak))
        cek("status akhir 'selesai'", p.status == 'selesai', p.status)
        cek('hasil_json tersimpan', '"bab_selesai"' in (p.hasil_json or ''), p.hasil_json[:60])
        cek('bukan HANTU (status tertutup)', p.status != 'jalan')

        print('\n[5] PERILAKU: pekerjaan GAGAL → jujur, tidak menggantung')
        p2 = P.mulai(db, user_id=u.id, file_id=None, komentar=[],
                     jenis_dokumen='buku_umum')
        status_akhir = {'s': None}

        async def kerja_gagal(lapor):
            lapor.tahap('Menulis bab 1')
            raise RuntimeError('AI tidak merespons')

        #  `tandai_gagal` dipanggil oleh pembungkus utas di `_utas` — kita
        #  biarkan mekanisme ASLI yang bekerja, jangan menirunya.
        P.jalankan(p2.kode, kerja_gagal)
        for _ in range(80):
            db.expire_all()
            q = P.ambil(db, p2.kode)
            if q and q.status in ('selesai', 'gagal'):
                status_akhir['s'] = q.status
                break
            time.sleep(0.1)
        db.expire_all()
        q = P.ambil(db, p2.kode)
        cek("status jadi 'gagal' (bukan menggantung 'jalan')",
            q.status == 'gagal', q.status)
        cek('alasan gagal tersimpan', bool(q.galat), q.galat[:60])

        print('\n[6] PENJAGA: halaman pantau menolak kode milik orang lain')
        cek('ambil() menyaring user_id',
            'user_id' in open(os.path.join(akar, 'app', 'proses.py'),
                              encoding='utf-8').read().split('def ambil')[1][:300])
        p3 = P.ambil(db, p1.kode, u2.id)
        cek('user LAIN tidak mendapat baris proses', p3 is None, str(p3))
        p4 = P.ambil(db, p1.kode, u.id)
        cek('pemilik tetap bisa membuka', p4 is not None)

        print('\n[7] HALAMAN PANTAU: tahap nyata, bukan persen karangan')
        tpl = open(os.path.join(akar, 'app', 'templates', 'buku_proses.html'),
                   encoding='utf-8').read()
        #  🚨 JEBAKAN 19 Okt: JANGAN buang `<script>` saat memeriksa template.
        #     Pemanggilan fetch ADA DI DALAM <script>. Versi pertama gerbang ini
        #     membuang script → 3 asersi gagal PALSU padahal halaman benar.
        #  Yang boleh dibuang hanya komentar CSS/HTML/JS.
        tpl_bersih = re.sub(r'/\*(?:.|\n)*?\*/', '', tpl)
        tpl_bersih = re.sub(r'^\s*//.*$', '', tpl_bersih, flags=re.M)
        tpl_bersih = re.sub(r'<!--(?:.|\n)*?-->', '', tpl_bersih)
        #  ⚠️ `width:100%` di media query = tata letak, BUKAN persen kemajuan.
        #     Yang dilarang: bar kemajuan dengan lebar berubah 0–100%.
        #     Jadi cari pola bar progres, bukan semua `width: N%`.
        ada_bar_progres = bool(re.search(
            r'class=["\'][^"\']*(progres|progress|bar-kemajuan|kemajuan-bar)', tpl_bersih))
        cek('tidak ada bar kemajuan berpersen (aturan §4.12)',
            not ada_bar_progres,
            'progress WAJIB tahap nyata: Menyiapkan → Menulis bab → Merakit → Selesai')
        cek('memantau endpoint proses yang SUDAH ADA',
            '/api/ai/v1/proses/' in tpl_bersih)
        #  30 Okt 2026 (G1/A4): halaman proses tidak lagi memanggil
        #  /hasil dan tidak lagi menampilkan kartu gagal. Tiga cek di
        #  bawah dibalik ke invarian baru: gagal bila perilaku lama
        #  kembali (fetch /hasil, kartu pesan-gagal, parse hasil_json
        #  di JS). Selesai resolve by kode dari server, bukan /hasil.
        cek('tidak memakai endpoint hasil (G1: resolve by kode)',
            '/hasil' not in tpl_bersih)
        cek('mengalihkan ke halaman hasil', '/buku/selesai?' in tpl_bersih)
        cek('tidak ada keadaan GAGAL yang terlihat (A4: sabar)',
            'pesan-gagal' not in tpl_bersih)
        cek('BISA DITINGGAL: halaman menyatakan boleh tutup tab',
            'tutup tab' in tpl)

        print('\n[8] HALAMAN PANTAU: tidak membocorkan isi naskah')
        #  ⚠️ Yang dilarang: menampilkan `j.hasil` (naskah penuh) atau
        #     `j.jawaban`. `hasil_json` BOLEH — itu metadata (jumlah bab,
        #     kata, nama berkas), bukan isi tulisan.
        bocor = []
        for pola in (r'\.hasil\b', r'\.jawaban\b'):
            for mm in re.finditer(pola, tpl_bersih):
                #  `hasil_json` bukan `hasil`
                if 'hasil_json' in tpl_bersih[max(0, mm.start() - 2):mm.end() + 6]:
                    continue
                bocor.append(mm.group(0))
        cek('tidak menampilkan isi naskah (`hasil`/`jawaban`)',
            not bocor, 'yang dipantau: ' + ', '.join(sorted(set(bocor))))
        cek('tidak memakai metadata hasil di template (G1: hasil_json di server)',
            'hasil_json' not in tpl_bersih)

    finally:
        db.close()
        shutil.rmtree(up, ignore_errors=True)
        shutil.rmtree(dat, ignore_errors=True)

    print(f'\n{"=" * 62}\nBUKU LATAR: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
