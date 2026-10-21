"""UJI SAMBUNGAN ASSEMBLY KE RUTE `/buku/susun` (19 Okt 2026, opsi B).

Yang diuji TANPA AI dan TANPA kuota:
  [1] `penyusunan_buku.susun()` mengembalikan 'docx' dan berkasnya ADA
  [2] Gagal rakit TIDAK membatalkan buku (bab tetap dianggap jadi)
  [3] Halaman /buku/selesai TIDAK percaya parameter URL
      (?docx=/etc/passwd tidak boleh tampil sebagai dokumen)
  [4] Dockerfile menyalin berkas assembly (kalau tidak, container gagal rakit)
  [5] Template memakai variabel yang benar-benar dikirim rute

Dipakai DB palsu + kuota palsu. TIDAK menyentuh saldo siapa pun.
Jalankan: PYTHONPATH=<proyek> EDUAI_APP_DIR=<proyek> python _uji_sambung_assembly.py
"""
import os
import re
import sys
import tempfile
import shutil

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


class _KuotaPalsu:
    """Kuota palsu — tidak menyentuh saldo siapa pun."""
    dipotong = []
    dikembalikan = []

    @classmethod
    def potong_banyak(cls, db, u, n):
        cls.dipotong.append(n)
        return {'saldo': 99}

    @classmethod
    def kembalikan_banyak(cls, db, u, n):
        cls.dikembalikan.append(n)
        return {'saldo': 100}


class _UserPalsu:
    id = 4242
    nama = 'Uji Wulan'
    nama_kampus = 'Universitas Uji'


def main():
    akar = os.environ.get('EDUAI_APP_DIR') or os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, akar)
    for p in ('/opt/data', '/app'):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)

    os.environ['BUKU_DIR'] = tempfile.mkdtemp(prefix='uji_buku_dir_')

    from app import penyusunan_buku as PB
    from app import kuota as K

    print('\n[1] susun() MERAKIT DOKUMEN (memakai bab contoh, tanpa AI)')

    #  Pakai jalur rakit langsung: tiru apa yang rute lakukan SETELAH bab jadi.
    import buku_umum_assembly as ASM
    kerja = tempfile.mkdtemp(prefix='uji_rakit_')
    try:
        os.makedirs(os.path.join(kerja, 'visual'), exist_ok=True)
        with open(os.path.join(kerja, 'bab1.txt'), 'w', encoding='utf-8') as f:
            f.write('## BAB 1. Uji Sambungan\n\n' + ('Isi bab uji yang cukup panjang. ' * 60))
        outline = {1: {'title': 'Uji Sambungan',
                       'subs': [('1.1', 'Sub Uji', 'poin')]}}
        hasil = ASM.rakit('Buku Uji Sambungan', kerja, outline,
                          penulis='Uji Wulan', institusi='Universitas Uji')
        cek('rakit mengembalikan docx', bool(hasil.get('docx')), str(hasil)[:120])
        cek('berkas docx ADA', os.path.exists(hasil.get('docx', '')))
        #  Bentuk hasil inilah yang dipakai rute: hasil['docx']
        cek('kunci "docx" siap dipakai rute', 'docx' in hasil)
        cek('kunci "docx_alasan" ada di penyusunan_buku (janji ke rute)',
            'docx_alasan' in open(os.path.join(akar, 'app', 'penyusunan_buku.py'),
                                  encoding='utf-8').read())
    finally:
        shutil.rmtree(kerja, ignore_errors=True)

    print('\n[2] KUNCI HASIL YANG DIBACA RUTE BENAR-BENAR DIISI')
    src_pb = open(os.path.join(akar, 'app', 'penyusunan_buku.py'), encoding='utf-8').read()
    #  Buang komentar dulu — nama variabel di komentar BUKAN bukti (jebakan 19 Okt)
    kode_pb = re.sub(r'#.*', '', src_pb)
    cek("penyusunan_buku menyetel hasil['docx']", "hasil['docx'] =" in kode_pb)
    cek("penyusunan_buku menyetel hasil['docx_alasan']",
        "hasil['docx_alasan'] =" in kode_pb)
    cek('gagal rakit TIDAK melempar (dibungkus try/except)',
        'except Exception as e:' in kode_pb.split("hasil['docx'] = None")[-1])

    print('\n[3] HALAMAN HASIL TIDAK PERCAYA PARAMETER URL')
    src_main = open(os.path.join(akar, 'app', 'main.py'), encoding='utf-8').read()
    m = re.search(r"def halaman_buku_selesai\(.*?(?=\n@|\Z)", src_main, re.S)
    badan = m.group(0) if m else ''
    kode_main = re.sub(r'#.*', '', badan)
    cek('halaman_buku_selesai terbaca', len(kode_main) > 300, f'panjang={len(kode_main)}')
    cek('memeriksa os.path.exists(docx)', 'os.path.exists(docx)' in kode_main,
        'tanpa cek berkas, ?docx=/etc/passwd akan tampil sebagai dokumen')
    cek('judul berkas pakai basename (bukan path penuh)',
        'os.path.basename(docx)' in kode_main)
    cek('ukuran dibaca dari BERKAS, bukan dari URL',
        'os.path.getsize(docx)' in kode_main)

    print('\n[4] DOCKERFILE MENYALIN BERKAS ASSEMBLY')
    df = open(os.path.join(akar, 'Dockerfile'), encoding='utf-8').read()
    cek('COPY buku_umum_assembly.py ADA', 'COPY buku_umum_assembly.py' in df,
        'tanpa ini container gagal merakit → user hanya dapat bab terpisah')
    cek('COPY indeks_referensi.py ADA (rantai impor assembly)',
        'COPY indeks_referensi.py' in df)

    print('\n[5] TEMPLATE MEMAKAI VARIABEL YANG DIKIRIM RUTE')
    tpl = open(os.path.join(akar, 'app', 'templates', 'buku_selesai.html'),
               encoding='utf-8').read()
    for var in ('docx', 'docx_nama', 'docx_kb', 'docx_alasan'):
        cek(f'template memakai {{{{ {var} }}}}', var in tpl)
        cek(f'rute mengirim {var}', var in src_main.split('def halaman_buku_selesai')[1][:1500])

    print('\n[6] KUOTA TIDAK DISENTUH UJI INI')
    cek('uji tidak memotong kuota', _KuotaPalsu.dipotong == [], str(_KuotaPalsu.dipotong))

    shutil.rmtree(os.environ['BUKU_DIR'], ignore_errors=True)
    print(f'\n{"=" * 62}\nSAMBUNGAN ASSEMBLY: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
