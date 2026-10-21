"""GERBANG SALINAN MESIN BUKU — berkas di proyek HARUS identik dengan di /opt/data.

KENAPA: mesin buku tinggal di `/opt/data` (host), tetapi Docker hanya bisa
`COPY` berkas yang ada DI DALAM konteks build (`services/eduai-publishing/`).
Jadi berkas mesin harus DISALIN ke folder proyek.

BAHAYA SALINAN: dua berkas yang mestinya sama bisa MENYIMPANG diam-diam.
Kalau Wulan memperbaiki `/opt/data/buku_umum_assembly.py` tetapi lupa menyalin,
maka: gerbang host LULUS, image produksi masih versi LAMA ⇒ kerusakan lolos
deploy. Gerbang ini membuat penyimpangan itu MUSTAHIL dilewatkan.

Jalankan: /opt/data/.venv/bin/python _gerbang_salinan_mesin.py
"""
import hashlib
import os
import sys

LULUS = GAGAL = 0

#  (nama berkas, boleh tidak ada?)
SALINAN = [
    ('buku_umum_assembly.py', False),
    ('indeks_referensi.py', False),
    ('outline_buku.py', False),
    ('penyusun_buku.py', False),
    ('buku_umum_pipeline.py', False),
    ('jenis_buku.py', False),
    ('tone_menulis.py', False),
    ('brief_visual.py', False),
    ('label_infografis.py', False),
    ('larangan_budaya.py', False),
    ('verifikasi_sitasi.py', False),
    #  ⚠️ `peta3_jev.py` TIDAK masuk daftar ini: berkas itu memang MILIK proyek
    #     (bukan salinan dari /opt/data) — dipindahkan ke proyek 14 Okt 2026.
    #     Memasukkannya = memaksa aturan yang tidak berlaku (gagal palsu).
]

SUMBER = '/opt/data'
PROYEK = os.path.dirname(os.path.abspath(__file__))


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    print(f'\nsumber: {SUMBER}\nproyek: {PROYEK}\n')
    for nama, opsional in SALINAN:
        a = os.path.join(SUMBER, nama)
        b = os.path.join(PROYEK, nama)
        if not os.path.exists(a):
            if opsional:
                continue
            cek(f'{nama}: ADA di sumber', False, a)
            continue
        cek(f'{nama}: disalin ke proyek', os.path.exists(b),
            'TIDAK ADA di proyek → Dockerfile COPY akan gagal')
        if not os.path.exists(b):
            continue
        ha, hb = sha(a), sha(b)
        cek(f'{nama}: salinan IDENTIK dengan sumber', ha == hb,
            f'sumber={ha[:12]} proyek={hb[:12]} — '
            f'SALIN ULANG: cp {a} {b}')

    #  Berkas assembly WAJIB ikut Dockerfile
    df_path = os.path.join(PROYEK, 'Dockerfile')
    df = open(df_path, encoding='utf-8').read()
    #  `tahapan_diagram.py` masuk daftar karena AKAR NYATA 20 Okt 2026: berkas
    #  ada di proyek & host tapi TIDAK di COPY ⇒ `import tahapan_diagram`
    #  gagal di dalam image ⇒ Jev DIAM-DIAM dilewati, semua diagram balik ke
    #  template, dan di host tampak "sudah jalan". Gerbang ini menangkapnya.
    for nama in ('buku_umum_assembly.py', 'indeks_referensi.py',
                 'tahapan_diagram.py'):
        cek(f'Dockerfile COPY {nama}', f'COPY {nama}' in df,
            'mesin tidak ikut image → rute jalan tapi rakit gagal')

    #  python-docx WAJIB ada di requirements (akar 19 Okt)
    req = open(os.path.join(PROYEK, 'requirements.txt'), encoding='utf-8').read()
    cek('requirements memuat python-docx', 'python-docx' in req,
        'assembly butuh `docx`; tanpa ini produksi gagal "No module named docx"')

    print(f'\n{"=" * 62}\nSALINAN MESIN: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
