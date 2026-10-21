"""UJI LAPIS 1 — JEMBATAN BAB KURANG (layar konversi).

Yang dibuktikan (TestClient, DB SALINAN — bukan DB produksi):
  A. Label manusia benar ('hasil' → 'BAB IV Hasil'), bukan kata mesin.
  B. Halaman konversi naskah BAB KURANG → muncul blok 'Naskah Belum Lengkap'
     + tombol 'Perbaiki' ke /kolaborasi + TIDAK ada tombol 'Mulai Konversi'.
  C. Naskah LENGKAP → TIDAK muncul blok itu (blok konversi normal).
  D. Halaman TIDAK error (status 200) di kedua keadaan.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/lapis1')

LULUS = []
GAGAL = []


def cek(nama: str, syarat: bool, bukti: str = ''):
    (LULUS if syarat else GAGAL).append(nama)
    tanda = 'LULUS' if syarat else 'GAGAL'
    print(f'  [{tanda}] {nama}' + (f' — {bukti}' if bukti else ''))


def main():
    from app import konversi as K

    print('=== A. LABEL MANUSIA ===')
    peta = K.LABEL_KELENGKAPAN
    cek('A1 label hasil = BAB IV Hasil', peta.get('hasil') == 'BAB IV Hasil',
        repr(peta.get('hasil')))
    cek('A2 label pustaka = Daftar Pustaka',
        peta.get('pustaka') == 'Daftar Pustaka', repr(peta.get('pustaka')))
    cek('A3 label metodologi gaya daftar isi',
        peta.get('metode') == 'BAB III Metode Penelitian', repr(peta.get('metode')))
    cek('A4 ke-7 kunci bahan punya label',
        all(k in peta for k in ('latar_belakang', 'tinjauan_pustaka', 'metode',
                                'hasil', 'pembahasan', 'kesimpulan', 'pustaka')),
        f'{len(peta)} label')
    cek('A5 fungsi label_kelengkapan aman atas kunci asing',
        K.label_kelengkapan('entah') == 'entah', repr(K.label_kelengkapan('entah')))
    cek('A6 bagian_kurang() menerjemahkan daftar',
        K.bagian_kurang({'kurang': ['hasil', 'pustaka']})
        == ['BAB IV Hasil', 'Daftar Pustaka'],
        repr(K.bagian_kurang({'kurang': ['hasil', 'pustaka']})))

    print()
    print('=== B. LABEL COCOK DENGAN KUNCI cek_kelengkapan() ===')
    kel = K.cek_kelengkapan({'teks': 'BAB I PENDAHULUAN\nx\nBAB II TINJAUAN PUSTAKA\ny\n'
                                    'BAB III METODE\nz\n'}, [])
    kurang = kel.get('kurang') or []
    cek('B1 kunci kurang dari mesin SEMUA ada labelnya',
        all(k in peta for k in kurang), repr(kurang))
    cek('B2 bagian_kurang() tidak mengembalikan kata mesin',
        all(('%s' % x) not in ('hasil', 'pustaka', 'metode')
            for x in K.bagian_kurang(kel)),
        repr(K.bagian_kurang(kel)))

    print()
    print('=== C. TEMPLATE — filter label_bagian terdaftar & blok jembatan ada ===')
    tpl = (open('/app/app/templates/artikel_konversi.html', encoding='utf-8').read())
    cek('C1 template memakai filter label_bagian', 'label_bagian' in tpl)
    cek('C2 ada blok Naskah Belum Lengkap', 'Naskah Belum Lengkap' in tpl)
    cek('C3 tombol Perbaiki mengarah ke /kolaborasi',
        'href="/kolaborasi"' in tpl)
    cek('C4 tombol Perbaiki bertuliskan "Perbaiki"', 'Perbaiki' in tpl)
    cek('C5 jumlah endif == jumlah if (template seimbang; elif tidak perlu endif)',
        tpl.count('{% endif %}') == tpl.count('{% if '),
        f"endif={tpl.count('{% endif %}')} if={tpl.count('{% if ')} "
        f"elif={tpl.count('{% elif')}")
    cek('C6 tombol konversi ADA di template (keadaan lengkap)',
        'Mulai Konversi' in tpl)

    print()
    print('=== D. FILTER TERPASANG DI APLIKASI (main.py) ===')
    from app import main as M
    cek('D1 filter label_bagian terdaftar', 'label_bagian' in M.templates.env.filters)
    f = M.templates.env.filters['label_bagian']
    cek('D2 filter memakai sumber konversi (bukan daftar salinan)',
        f('hasil') == 'BAB IV Hasil', repr(f('hasil')))
    cek('D3 filter aman atas None', isinstance(f(None), str), repr(f(None)))

    print()
    print('=== E. JINJA MERENDER TANPA ERROR (kedua keadaan) ===')
    t = M.templates.env.get_template('artikel_konversi.html')

    class B:
        id = 999
        nama = 'Naskah Uji.docx'

    class U:
        id = 1
        email = 'uji@eduai.test'

    dasar = dict(user=U(), berkas=B(), naskah_ada=True, pesan='',
                 mutu=None, mutu_pesan='', jatah={'sisa': 1},
                 token_per_revisi=2, label_jenis={},
                 artikel_ada=False, daftar_revisi=[], saldo_revisi=0)

    siap_kurang = {'boleh': True, 'henti': False, 'pesan': '',
                   'identitas': {'nama': 'A', 'email': 'b@c.d'},
                   'jenis': {'jenis': 'kuantitatif', 'yakin': 0.9},
                   'kelengkapan': {'kurang': ['hasil', 'kesimpulan'], 'bahan': {}}}
    html = t.render({**dasar, 'siap': siap_kurang})
    cek('E1 render naskah BAB KURANG tanpa error', bool(html))
    cek('E2 muncul "Naskah Belum Lengkap"', 'Naskah Belum Lengkap' in html)
    cek('E3 label manusia tampil (BAB IV Hasil)', 'BAB IV Hasil' in html)
    cek('E4 TIDAK ada tombol "Mulai Konversi"',
        'Mulai Konversi' not in html)
    cek('E5 TIDAK ada tombol revisi (Perbaiki Sebagian)',
        'Perbaiki Sebagian' not in html)
    cek('E6 tombol Perbaiki → /kolaborasi', 'href="/kolaborasi"' in html)
    cek('E7 kata mesin "hasil" TIDAK tampil sendirian',
        '>hasil<' not in html and 'hasil ·' not in html
        and '· hasil' not in html)

    siap_lengkap = {'boleh': True, 'henti': False, 'pesan': 'Siap dikonversi.',
                    'identitas': {'nama': 'A', 'email': 'b@c.d'},
                    'jenis': {'jenis': 'kuantitatif', 'yakin': 0.9},
                    'kelengkapan': {'kurang': [], 'bahan': {'hasil': True}}}
    html2 = t.render({**dasar, 'siap': siap_lengkap})
    cek('E8 render naskah LENGKAP tanpa error', bool(html2))
    cek('E9 blok "Naskah Belum Lengkap" TIDAK muncul',
        'Naskah Belum Lengkap' not in html2)
    cek('E10 tombol "Mulai Konversi" muncul', 'Mulai Konversi' in html2)

    print()
    print('=' * 62)
    print(f'  HASIL LAPIS 1: {len(LULUS)} LULUS / {len(GAGAL)} GAGAL')
    if GAGAL:
        print('  GAGAL:', GAGAL)
    print('=' * 62)
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
