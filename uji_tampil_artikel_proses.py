"""Uji tampilan artikel minimal di halaman proses (display-only).

Jalankan dari root checkout: python3 uji_tampil_artikel_proses.py
Tidak menyentuh DB produksi, tidak menyentuh container produksi, hanya
loader palsu dan render Jinja dari berkas template di checkout.
"""
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

from app.proses import ARTIKEL_TAMPIL_MAKS, artikel_proses, bagi_artikel_tampil


def _baris(i, sumber):
    return {
        'surname_tampil': 'Penulis%d' % i,
        'tahun': str(2020 + i),
        'sumber': sumber,
        'ref_dict': {
            'authors': ['Penulis%d Penuh' % i],
            'year': 2020 + i,
            'title': 'Judul Artikel %d' % i,
            'source': sumber,
        },
    }


def _ambil_palsu(db, kode, bab):
    if bab == 1:
        sumber_list = ['Scopus', 'OpenAlex', 'CrossRef', 'Scopus',
                       'OpenAlex', 'CrossRef', 'Scopus', 'OpenAlex']
        return [_baris(i + 1, sumber_list[i]) for i in range(8)]
    if bab == 2:
        return [_baris(i + 1, 'Scopus') for i in range(3)]
    if bab == 3:
        return []
    raise RuntimeError('loader gagal untuk bab %d' % bab)


def _render(artikel_per_bab):
    env = Environment(loader=FileSystemLoader('app/templates'),
                      autoescape=True)
    env.globals['ikon'] = lambda *a, **k: ''
    env.globals['ikon_sprite'] = lambda *a, **k: ''
    tmpl = env.get_template('buku_proses.html')
    ctx = {
        'user': SimpleNamespace(nama='Uji Buku', email='uji@bikinaja.id'),
        'judul': 'Judul Uji', 'kode': 'KODEUJI', 'tahap': 'Menulis',
        'status': 'jalan', 'wa_aktif': False, 'bab_selesai': 0,
        'bab_total': 5, 'sedang_disempurnakan': False, 'galat': '',
        'antrean_pos': None, 'antrean_total': None,
        'subbab_per_bab': {}, 'artikel_per_bab': artikel_per_bab,
    }
    return tmpl.render(ctx)


KASUS = []


def kasus(nama):
    def deco(fn):
        KASUS.append((nama, fn))
        return fn
    return deco


@kasus('bagi-8-jadi-3-tampil-5-sisa')
def _():
    tampil, sisa = bagi_artikel_tampil(list(range(8)))
    assert tampil == [0, 1, 2], tampil
    assert sisa == [3, 4, 5, 6, 7], sisa


@kasus('bagi-3-tanpa-sisa')
def _():
    tampil, sisa = bagi_artikel_tampil(list(range(3)))
    assert tampil == [0, 1, 2] and sisa == []


@kasus('bagi-0-dan-none-tanpa-error')
def _():
    assert bagi_artikel_tampil([]) == ([], [])
    assert bagi_artikel_tampil(None) == ([], [])


@kasus('bagi-maks-tetap-3')
def _():
    assert ARTIKEL_TAMPIL_MAKS == 3


@kasus('artikel-proses-bab1-8-item-urut')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    assert len(data[1]) == 8, data
    assert data[1][0] == {'judul': 'Judul Artikel 1', 'penulis': 'Penulis1',
                          'tahun': '2021', 'sumber': 'Scopus'}, data[1][0]
    assert data[1][7]['judul'] == 'Judul Artikel 8'


@kasus('artikel-proses-tanpa-garuda-palsu')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    sumber_list = [a['sumber'] for a in data[1]]
    assert 'Garuda' not in sumber_list, sumber_list
    assert set(sumber_list) == {'Scopus', 'OpenAlex', 'CrossRef'}


@kasus('artikel-proses-bab-kosong-tidak-masuk')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    assert 3 not in data, data


@kasus('artikel-proses-loader-gagal-satu-bab-tetap-lanjut')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    assert 1 in data and 2 in data and 4 not in data, data


@kasus('artikel-proses-bab-total-0-kosong')
def _():
    assert artikel_proses(None, 'KODEUJI', 0, ambil=_ambil_palsu) == {}
    assert artikel_proses(None, '', 5, ambil=_ambil_palsu) == {}


@kasus('artikel-proses-judul-kosong-dilewati')
def _():
    def ambil(db, kode, bab):
        return [{'surname_tampil': 'X', 'tahun': '2020', 'sumber': 'Scopus',
                 'ref_dict': {'authors': ['X'], 'year': 2020, 'title': '',
                              'source': 'Scopus'}}]
    assert artikel_proses(None, 'KODEUJI', 1, ambil=ambil) == {}


@kasus('render-8-jadi-3-tampil-dan-and-more-5')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    html = _render(data)
    assert 'Judul Artikel 1' in html and 'Judul Artikel 3' in html
    assert 'and more... (5 lagi)' in html
    assert 'Judul Artikel 8' in html
    assert 'Bab 1 (8 artikel)' in html
    assert 'Referensi sedang disiapkan' not in html


@kasus('render-3-tanpa-expander')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    html = _render({2: data[2]})
    assert 'Bab 2 (3 artikel)' in html
    assert 'and more...' not in html


@kasus('render-kosong-placeholder-tanpa-error')
def _():
    html = _render({})
    assert 'Referensi sedang disiapkan' in html
    assert 'Judul Artikel' not in html


@kasus('render-badge-sumber-sesuai-db')
def _():
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    html = _render(data)
    assert '<span class="badge-sumber">Scopus</span>' in html
    assert '<span class="badge-sumber">OpenAlex</span>' in html
    assert '<span class="badge-sumber">CrossRef</span>' in html
    assert 'Garuda' not in html


def main():
    lulus = 0
    gagal = 0
    for nama, fn in KASUS:
        try:
            fn()
            print('  LULUS %s' % nama)
            lulus += 1
        except Exception as e:                                        # noqa: BLE001
            print('  GAGAL %s: %r' % (nama, e))
            gagal += 1
    print('LULUS %d, GAGAL %d' % (lulus, gagal))
    raise SystemExit(1 if gagal else 0)


if __name__ == '__main__':
    main()
