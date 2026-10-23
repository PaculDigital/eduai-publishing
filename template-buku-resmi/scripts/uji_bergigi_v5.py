#!/usr/bin/env python3
"""UJI BERGIGI v5 — gerbang-gerbang BARU Fase 2/3 (barang 18).

Setiap suntikan WAJIB tertangkap gerbangnya, dan kasus kontrol WAJIB
lolos — gerbang yang menolak semua atau menerima semua sama-sama
tak berguna. Mencakup: penolakan tanpa pustaka (#4), gerbang profil
(#6), gerbang tulisan (#10), gate kemiripan (#11), pemeriksa gambar
(#15), gerbang font (#8), regresi emas (#17).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SINI = Path(__file__).resolve().parent
PROFIL = SINI.parent / 'jenis' / 'monograf' / 'profil.json'
LULUS = GAGAL = 0


def ok(nama, syarat):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}')


def jalan(*args):
    return subprocess.run([sys.executable, *[str(a) for a in args]],
                          capture_output=True, text=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix='bergigi5-'))
    spec = json.loads((SINI / 'contoh_monograf.json').read_text(encoding='utf-8'))
    emas = tmp / 'emas-monograf.docx'
    jalan(SINI / 'buat_buku.py', SINI / 'contoh_monograf.json', emas,
          '--profil', PROFIL, '--tanpa-ukur')
    ok('KONTROL buku monograf utuh terbangun', emas.exists())

    # 1) tanpa pustaka -> ditolak sebelum menulis
    s1 = {k: v for k, v in spec.items() if k != 'daftar_pustaka'}
    p1 = tmp / 's1.json'; p1.write_text(json.dumps(s1))
    o1 = tmp / 's1.docx'
    r = jalan(SINI / 'buat_buku.py', p1, o1, '--profil', PROFIL)
    ok('#4 spec tanpa pustaka DITOLAK & berkas tidak tercipta',
       r.returncode != 0 and not o1.exists())

    # 2) gerbang profil: buku induk ditolak, monograf diterima
    induk = Path.home() / 'workspace' / 'buku-contoh-template-v2.docx'
    if induk.exists():
        r = jalan(SINI / 'periksa_buku_template.py', induk, f'--profil={PROFIL}')
        ok('#6 gerbang profil MENOLAK buku induk (ukuran salah)', r.returncode == 1)
    r = jalan(SINI / 'periksa_buku_template.py', emas, f'--profil={PROFIL}', '--wajib-pustaka')
    ok('#6 gerbang profil MENERIMA monograf + pustaka wajib', r.returncode == 0)

    # 3) gerbang tulisan: yatim + kata terlarang tertangkap; kontrol bersih
    s3 = json.loads(json.dumps(spec))
    s3['bab'][0]['paragraf_pembuka'][0] += (' Rujukan lain (Hartono, 2019) menyebut '
                                            'minuman keras dalam contoh yang keliru.')
    p3 = tmp / 's3.json'; p3.write_text(json.dumps(s3))
    o3 = tmp / 's3.docx'
    jalan(SINI / 'buat_buku.py', p3, o3, '--profil', PROFIL, '--tanpa-gerbang', '--tanpa-ukur')
    r = jalan(SINI / 'periksa_tulisan.py', o3, f'--profil={PROFIL}')
    ok('#10 gerbang tulisan MENANGKAP yatim + kata terlarang',
       r.returncode == 1 and 'tanpa entri' in r.stdout and 'minuman keras' in r.stdout)
    r = jalan(SINI / 'periksa_tulisan.py', emas, f'--profil={PROFIL}')
    ok('#10 gerbang tulisan MENERIMA buku bersih', r.returncode == 0)

    # 4) gate kemiripan: paragraf ganda tertangkap; kontrol bersih
    s4 = json.loads(json.dumps(spec))
    s4['bab'][2]['paragraf_pembuka'] = list(s4['bab'][0]['paragraf_pembuka'])
    p4 = tmp / 's4.json'; p4.write_text(json.dumps(s4))
    o4 = tmp / 's4.docx'
    jalan(SINI / 'buat_buku.py', p4, o4, '--profil', PROFIL, '--tanpa-gerbang', '--tanpa-ukur')
    r = jalan(SINI / 'cek_kemiripan.py', o4)
    ok('#11 gate kemiripan MENANGKAP paragraf ganda', r.returncode == 1)
    r = jalan(SINI / 'cek_kemiripan.py', emas)
    ok('#11 gate kemiripan MENERIMA buku unik', r.returncode == 0)

    # 5) pemeriksa gambar: patuh lulus, tak patuh gagal
    from PIL import Image
    patuh = tmp / 'patuh.png'; Image.new('RGB', (600, 400), (255, 255, 255)).save(patuh)
    liar = tmp / 'liar.png'; Image.new('RGB', (1200, 400), (30, 30, 120)).save(liar)
    r1 = jalan(SINI / 'periksa_gambar.py', patuh, f'--profil={PROFIL}')
    r2 = jalan(SINI / 'periksa_gambar.py', liar, f'--profil={PROFIL}')
    ok('#15 gambar patuh LULUS & gambar liar GAGAL', r1.returncode == 0 and r2.returncode == 1)

    # 6) gerbang font konsisten dengan kenyataan fc-list
    ada = subprocess.run(['fc-list', ':', 'family'], capture_output=True, text=True).stdout.lower()
    r = jalan(SINI / 'periksa_font.py', '--profil', PROFIL)
    ok('#8 gerbang font: exit sesuai ada/tidaknya Cambria',
       (r.returncode == 0) == ('cambria' in ada))

    # 7) regresi emas menangkap perubahan isi
    s7 = json.loads(json.dumps(spec))
    s7['bab'][0]['judul'] = 'Pendahuluan yang Diubah Diam-diam'
    p7 = tmp / 's7.json'; p7.write_text(json.dumps(s7))
    o7 = tmp / 's7.docx'
    jalan(SINI / 'buat_buku.py', p7, o7, '--profil', PROFIL, '--tanpa-gerbang', '--tanpa-ukur')
    sys.path.insert(0, str(SINI))
    import uji_regresi_emas as emas_mod
    beda = emas_mod.sidik(o7)['hash_paragraf'] != emas_mod.sidik(emas)['hash_paragraf']
    ok('#17 sidik jari emas BERBEDA saat isi diubah', beda)

    print(f'\nRINGKAS UJI BERGIGI v5: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
