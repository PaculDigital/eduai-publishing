#!/usr/bin/env python3
"""Uji Bab IV sinkron Diagram (18 Nov 2026, GAS Bos 19:27 WIB).

Jalankan `python3 tests/test_bab4.py`, keluar 0 bila semua lulus.
Sinkronisasi Diagram dengan Bab IV: keduanya menerima model yang
sama (banyak Y, 2 perantara M, 2 penguat Z) secara fleksibel.

Aturan yang diuji (keputusan Boss 18 Nov 19:27 WIB):
  1. periksa_peta menerima multi-Y, 2M, 2Z (flag 'y_ganda' dihapus);
     aturan struktural TETAP per variabel (tiap M jalur masuk DAN
     keluar; tiap Z jalur interaksi ke hasil, dari Z itu sendiri).
  2. Payload PLS memakai SEMUA Y (satu Y tetap satu nama seperti
     dulu; banyak Y jadi daftar nama konstruk hasil).
  3. Simulasi: 2M sudah didukung mesin (paralel + berjenjang);
     multi-Y, 2Z, banyak X, campuran M+Z TETAP ditolak mesin BUAT
     DATA (templatnya tetap) — batas ini dikunci tes, bukan dipaksa.
  4. Pemeta hasil ke hipotesis tidak lagi terikat satu Y (jalur X→M
     ketemu walau mediasinya hanya berakhir di Y2).
  5. Arah balik: peta Bab IV multi-Y/2M/2Z dibaca Diagram lewat
     model_dari_peta_bab4 dengan benar (lewat diteruskan, kode
     Y1/Y2/M1/M2/Z1/Z2 terbentuk, gambar tidak menabrak).
"""
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_bab4_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def cek_gagal(nama, fn):
    try:
        fn()
    except ValueError:
        cek(nama, True)
    except Exception as e:  # noqa: BLE001
        cek(nama, False, f'galat lain: {type(e).__name__}: {e}')
    else:
        cek(nama, False, 'tidak menolak')


from app import bab4 as B4
from app import diagram as DG


def _v(nama, peran, indikator=None):
    return {'nama': nama, 'peran': peran,
            'bukti': f'Kalimat bukti {nama}.',
            'indikator': indikator or []}


def _j(dari, ke, hip, jenis='langsung', lewat=None):
    d = {'dari': dari, 'ke': ke, 'hipotesis': hip, 'jenis': jenis}
    if lewat:
        d['lewat'] = lewat
    return d


def _kode_masalah(peta):
    return [m['kode'] for m in B4.periksa_peta(peta)]


def _peta_dasar():
    return {'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                         _v('Loyalitas', 'Y')],
            'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                      _j('Harga', 'Kepuasan', 'H2'),
                      _j('Kepuasan', 'Loyalitas', 'H3')],
            'jumlah_hipotesis': 3}


def _peta_multi_y():
    return {'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                         _v('Loyalitas', 'Y'),
                         _v('Keputusan Beli', 'Y')],
            'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                      _j('Harga', 'Keputusan Beli', 'H2'),
                      _j('Harga', 'Kepuasan', 'H3'),
                      _j('Kepuasan', 'Loyalitas', 'H4')],
            'jumlah_hipotesis': 4}


def _peta_2m():
    return {'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                         _v('Kepercayaan', 'M'), _v('Loyalitas', 'Y')],
            'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                      _j('Harga', 'Kepuasan', 'H2'),
                      _j('Kepuasan', 'Loyalitas', 'H3'),
                      _j('Harga', 'Kepercayaan', 'H4'),
                      _j('Kepercayaan', 'Loyalitas', 'H5')],
            'jumlah_hipotesis': 5}


def _peta_2z():
    return {'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [_v('Harga', 'X'), _v('Promosi', 'Z'),
                         _v('Iklan', 'Z'), _v('Loyalitas', 'Y')],
            'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                      _j('Promosi', 'Loyalitas', 'H2', 'interaksi'),
                      _j('Iklan', 'Loyalitas', 'H3', 'interaksi')],
            'jumlah_hipotesis': 3}


def _peta_2m_2z_2y():
    return {'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                         _v('Kepercayaan', 'M'), _v('Promosi', 'Z'),
                         _v('Iklan', 'Z'), _v('Loyalitas', 'Y'),
                         _v('Keputusan Beli', 'Y')],
            'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                      _j('Harga', 'Keputusan Beli', 'H2'),
                      _j('Harga', 'Loyalitas', 'H3', 'tidak_langsung',
                         'Kepuasan'),
                      _j('Harga', 'Keputusan Beli', 'H4', 'tidak_langsung',
                         'Kepercayaan'),
                      _j('Harga', 'Kepuasan', 'H5'),
                      _j('Kepuasan', 'Loyalitas', 'H6'),
                      _j('Harga', 'Kepercayaan', 'H7'),
                      _j('Kepercayaan', 'Keputusan Beli', 'H8'),
                      _j('Promosi', 'Loyalitas', 'H9', 'interaksi'),
                      _j('Iklan', 'Keputusan Beli', 'H10', 'interaksi')],
            'jumlah_hipotesis': 10}


def _tumpang(a, b):
    return not (a['x'] + a['w'] <= b['x'] or b['x'] + b['w'] <= a['x']
                or a['y'] + a['h'] <= b['y']
                or b['y'] + b['h'] <= a['y'])


def jalankan():
    print('Bagian 1 — periksa_peta menerima multi-Y, 2M, 2Z')
    cek('periksa_peta: peta dasar 1X/1M/1Y tanpa masalah',
        _kode_masalah(_peta_dasar()) == [])
    cek('periksa_peta: multi-Y diterima (y_ganda hilang)',
        _kode_masalah(_peta_multi_y()) == [],
        str(_kode_masalah(_peta_multi_y())))
    cek('periksa_peta: 2M diterima',
        _kode_masalah(_peta_2m()) == [],
        str(_kode_masalah(_peta_2m())))
    cek('periksa_peta: 2Z diterima',
        _kode_masalah(_peta_2z()) == [],
        str(_kode_masalah(_peta_2z())))
    cek('periksa_peta: 2M + 2Z + 2Y diterima',
        _kode_masalah(_peta_2m_2z_2y()) == [],
        str(_kode_masalah(_peta_2m_2z_2y())))
    _m_tanpa_keluar = _peta_dasar()
    _m_tanpa_keluar['jalur'] = [_j('Harga', 'Loyalitas', 'H1'),
                                _j('Harga', 'Kepuasan', 'H2')]
    _m_tanpa_keluar['jumlah_hipotesis'] = 2
    cek('periksa_peta: M tanpa jalur keluar tetap masalah',
        _kode_masalah(_m_tanpa_keluar) == ['perantara_terputus'],
        str(_kode_masalah(_m_tanpa_keluar)))
    _m_tanpa_masuk = _peta_dasar()
    _m_tanpa_masuk['jalur'] = [_j('Harga', 'Loyalitas', 'H1'),
                               _j('Kepuasan', 'Loyalitas', 'H2')]
    _m_tanpa_masuk['jumlah_hipotesis'] = 2
    cek('periksa_peta: M tanpa jalur masuk tetap masalah',
        _kode_masalah(_m_tanpa_masuk) == ['perantara_terputus'],
        str(_kode_masalah(_m_tanpa_masuk)))
    _z_tanpa = _peta_dasar()
    _z_tanpa['variabel'] = [_v('Harga', 'X'), _v('Promosi', 'Z'),
                            _v('Loyalitas', 'Y')]
    _z_tanpa['jalur'] = [_j('Harga', 'Loyalitas', 'H1'),
                         _j('Promosi', 'Loyalitas', 'H2', 'langsung')]
    _z_tanpa['jumlah_hipotesis'] = 2
    cek('periksa_peta: Z tanpa interaksi tetap masalah',
        _kode_masalah(_z_tanpa) == ['penguat_tanpa_interaksi'],
        str(_kode_masalah(_z_tanpa)))
    _z2_satu = _peta_2z()
    _z2_satu['jalur'] = [_j('Harga', 'Loyalitas', 'H1'),
                         _j('Promosi', 'Loyalitas', 'H2', 'interaksi')]
    _z2_satu['jumlah_hipotesis'] = 2
    _kode_z2 = _kode_masalah(_z2_satu)
    _pesan_z2 = [m['pesan'] for m in B4.periksa_peta(_z2_satu)]
    cek('periksa_peta: 2Z, Z kedua tanpa interaksi ketahuan',
        _kode_z2 == ['penguat_tanpa_interaksi']
        and any('Iklan' in p for p in _pesan_z2)
        and not any('Promosi' in p for p in _pesan_z2),
        str(_kode_z2) + ' ' + str(_pesan_z2))
    _jml = _peta_dasar()
    _jml['jumlah_hipotesis'] = 5
    cek('periksa_peta: jumlah jalur beda jumlah hipotesis tetap masalah',
        'jumlah_tak_sama' in _kode_masalah(_jml))
    _tanpa_label = _peta_dasar()
    _tanpa_label['jalur'] = [_j('Harga', 'Loyalitas', ''),
                             _j('Harga', 'Kepuasan', 'H2'),
                             _j('Kepuasan', 'Loyalitas', 'H3')]
    cek('periksa_peta: jalur tanpa label tetap masalah',
        'jalur_tanpa_label' in _kode_masalah(_tanpa_label))

    print('Bagian 2 — payload hitung memakai semua Y')
    _kolom_1y = ['Harga_1', 'Harga_2', 'Kepuasan_1', 'Loyalitas_1']
    _p_pls_1y = _peta_dasar()
    _p_pls_1y['metode'] = 'PLS-SEM'
    _pay_1y = B4.susun_payload_hitung(_p_pls_1y, _kolom_1y)
    cek('payload PLS 1Y: kolom_y_konstruk tetap satu nama (string)',
        _pay_1y['mode'] == 'pls'
        and _pay_1y['kolom_y_konstruk'] == 'Loyalitas',
        str(_pay_1y.get('kolom_y_konstruk')))
    _kolom_2y = ['Harga_1', 'Kepuasan_1', 'Loyalitas_1',
                 'Keputusan_Beli_1']
    _p_pls_2y = _peta_multi_y()
    _p_pls_2y['metode'] = 'PLS-SEM'
    _pay_2y = B4.susun_payload_hitung(_p_pls_2y, _kolom_2y)
    cek('payload PLS multi-Y: kolom_y_konstruk daftar semua Y',
        _pay_2y['kolom_y_konstruk'] == ['Loyalitas', 'Keputusan Beli'],
        str(_pay_2y.get('kolom_y_konstruk')))
    _p_pls_0y = {'jenis': 'kuantitatif', 'metode': 'PLS-SEM',
                 'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M')],
                 'jalur': [_j('Harga', 'Kepuasan', 'H1')],
                 'jumlah_hipotesis': 1}
    _pay_0y = B4.susun_payload_hitung(_p_pls_0y, ['Harga_1'])
    cek('payload PLS tanpa Y: kolom_y_konstruk tetap None',
        _pay_0y['kolom_y_konstruk'] is None)
    _pay_spss_2y = B4.susun_payload_hitung(_peta_multi_y(), _kolom_2y)
    _peran_spss = set(_pay_spss_2y['peran'].values())
    cek('payload SPSS multi-Y: peran kolom memakai Y1/Y2',
        _pay_spss_2y['mode'] == 'spss' and 'Y1' in _peran_spss
        and 'Y2' in _peran_spss, str(_peran_spss))
    _kolom_2m2z = ['Harga_1', 'Kepuasan_1', 'Kepercayaan_1',
                   'Promosi_1', 'Iklan_1', 'Loyalitas_1',
                   'Keputusan_Beli_1']
    _pay_spss_2m2z = B4.susun_payload_hitung(_peta_2m_2z_2y(),
                                             _kolom_2m2z)
    _peran_2m2z = set(_pay_spss_2m2z['peran'].values())
    cek('payload SPSS 2M/2Z/2Y: peran kolom M1/M2/Z1/Z2/Y1/Y2',
        {'M1', 'M2', 'Z1', 'Z2', 'Y1', 'Y2'} <= _peran_2m2z,
        str(_peran_2m2z))

    print('Bagian 3 — simulasi: 2M bisa, multi-Y/2Z/banyak X tidak')
    cek('simulasi mediasi 1X/1M/1Y',
        B4.susun_permintaan_simulasi(_peta_dasar())['model'] == 'mediasi')
    cek('simulasi mediasi-paralel 2M',
        B4.susun_permintaan_simulasi(_peta_2m())['model']
        == 'mediasi-paralel')
    _berjenjang = {'jenis': 'kuantitatif', 'metode': 'regresi',
                   'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                                _v('Kepercayaan', 'M'),
                                _v('Loyalitas', 'Y')],
                   'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                             _j('Harga', 'Kepuasan', 'H2'),
                             _j('Kepuasan', 'Kepercayaan', 'H3'),
                             _j('Kepercayaan', 'Loyalitas', 'H4')],
                   'jumlah_hipotesis': 4}
    cek('simulasi mediasi-berjenjang 2M bersambung',
        B4.susun_permintaan_simulasi(_berjenjang)['model']
        == 'mediasi-berjenjang')
    _moderasi = {'jenis': 'kuantitatif', 'metode': 'regresi',
                 'variabel': [_v('Harga', 'X'), _v('Promosi', 'Z'),
                              _v('Loyalitas', 'Y')],
                 'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                           _j('Promosi', 'Loyalitas', 'H2', 'interaksi')],
                 'jumlah_hipotesis': 2}
    cek('simulasi moderasi 1Z',
        B4.susun_permintaan_simulasi(_moderasi)['model'] == 'moderasi')
    cek_gagal('simulasi multi-Y ditolak mesin (batas dikunci)',
              lambda: B4.susun_permintaan_simulasi(_peta_multi_y()))
    cek_gagal('simulasi 2Z ditolak mesin (batas dikunci)',
              lambda: B4.susun_permintaan_simulasi(_peta_2z()))
    _multi_x = {'jenis': 'kuantitatif', 'metode': 'regresi',
                'variabel': [_v('Harga', 'X'), _v('Kualitas', 'X'),
                             _v('Loyalitas', 'Y')],
                'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                          _j('Kualitas', 'Loyalitas', 'H2')],
                'jumlah_hipotesis': 2}
    cek_gagal('simulasi banyak X ditolak mesin (batas dikunci)',
              lambda: B4.susun_permintaan_simulasi(_multi_x))
    _campuran = {'jenis': 'kuantitatif', 'metode': 'regresi',
                 'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                              _v('Promosi', 'Z'), _v('Loyalitas', 'Y')],
                 'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                           _j('Harga', 'Kepuasan', 'H2'),
                           _j('Kepuasan', 'Loyalitas', 'H3'),
                           _j('Promosi', 'Loyalitas', 'H4', 'interaksi')],
                 'jumlah_hipotesis': 4}
    cek_gagal('simulasi campuran M+Z ditolak mesin (batas dikunci)',
              lambda: B4.susun_permintaan_simulasi(_campuran))

    print('Bagian 4 — pemeta hasil ke hipotesis tidak terikat satu Y')
    _peta_hasil = {'jenis': 'kuantitatif', 'metode': 'regresi',
                   'variabel': [_v('Harga', 'X'), _v('Kepuasan', 'M'),
                                _v('Promosi', 'Z'), _v('Loyalitas', 'Y'),
                                _v('Keputusan Beli', 'Y')],
                   'jalur': [_j('Harga', 'Loyalitas', 'H1'),
                             _j('Harga', 'Keputusan Beli', 'H2'),
                             _j('Harga', 'Keputusan Beli', 'H3',
                                'tidak_langsung', 'Kepuasan'),
                             _j('Harga', 'Kepuasan', 'H4'),
                             _j('Kepuasan', 'Keputusan Beli', 'H5'),
                             _j('Promosi', 'Keputusan Beli', 'H6',
                                'interaksi')],
                   'jumlah_hipotesis': 6}
    _hasil = {'mode': 'spss',
              'koef': [{'nama': 'X1', 'b': 0.50, 'p': 0.01}],
              'kaitan': {
                  # Label mesin = label_peran (M1/Z1 bernomor walau
                  # satu perantara/penguat), bukan 'M'/'Z' polos.
                  'mediasi': [{'x': 'X1', 'm': 'M1', 'y': 'Y2',
                               'a': {'b': 0.40, 'p': 0.02},
                               'b': {'b': 0.30, 'p': 0.03},
                               'cp': {'b': 0.20, 'p': 0.04},
                               'tidak_langsung': {'b': 0.12,
                                                  'p': 0.05}}],
                  'moderasi': [{'x': 'X1', 'z': 'Z1', 'y': 'Y2',
                                'dengan_interaksi': {
                                    'interaksi': {'b': 0.15, 'p': 0.01}},
                                'delta_r2': 0.05, 'jenis': 'menguatkan',
                                'arah': 'positif',
                                'kalimat': 'Z menguatkan.'}]}}
    _petakan = {e['hipotesis']: e for e in
                B4.petakan_hasil_ke_hipotesis(_peta_hasil, _hasil)}
    cek('pemeta multi-Y: H3 tidak langsung ke Y2 ketemu',
        _petakan['H3']['ketemu'] is True
        and _petakan['H3']['b'] == 0.12,
        str(_petakan['H3']))
    cek('pemeta multi-Y: H4 X→M ketemu walau mediasi hanya di Y2',
        _petakan['H4']['ketemu'] is True
        and _petakan['H4']['b'] == 0.40,
        str(_petakan['H4']))
    cek('pemeta multi-Y: H5 M→Y2 ketemu',
        _petakan['H5']['ketemu'] is True
        and _petakan['H5']['b'] == 0.30,
        str(_petakan['H5']))
    cek('pemeta multi-Y: H6 interaksi ke Y2 ketemu',
        _petakan['H6']['ketemu'] is True
        and _petakan['H6']['b'] == 0.15,
        str(_petakan['H6']))
    cek('pemeta multi-Y: H1 X→Y1 ketemu lewat koef',
        _petakan['H1']['ketemu'] is True
        and _petakan['H1']['b'] == 0.50,
        str(_petakan['H1']))
    cek('pemeta multi-Y: H2 X→Y2 ketemu lewat cp',
        _petakan['H2']['ketemu'] is True
        and _petakan['H2']['b'] == 0.20,
        str(_petakan['H2']))

    print('Bagian 5 — arah balik: peta Bab IV dibaca Diagram')
    _peta_rt = _peta_2m_2z_2y()
    _mentah = DG.model_dari_peta_bab4(_peta_rt)
    _model, _masalah = DG.normalisasi_model(_mentah)
    cek('balik: peta 2M/2Z/2Y lolos normalisasi Diagram',
        _model is not None, str(_masalah))
    _kode = {v['nama']: v['kode'] for v in _model['variabel']}
    cek('balik: kode Y1/Y2/M1/M2/Z1/Z2 terbentuk',
        _kode == {'Harga': 'X1', 'Kepuasan': 'M1',
                  'Kepercayaan': 'M2', 'Promosi': 'Z1', 'Iklan': 'Z2',
                  'Loyalitas': 'Y1', 'Keputusan Beli': 'Y2'},
        str(_kode))
    _h3 = next(j for j in _model['jalur']
               if j['hipotesis'] == 'H3')
    cek('balik: lewat tidak langsung diteruskan (H3 lewat M1)',
        _h3['lewat'] == 'M1' and _h3['jenis'] == 'tidak_langsung',
        str(_h3))
    _tata = DG.tata_letak(_model)
    _kotak = _tata['kotak']
    cek('balik: tujuh oval tergambar (X1 M1 M2 Z1 Z2 Y1 Y2)',
        sorted(k['id'] for k in _kotak)
        == ['M1', 'M2', 'X1', 'Y1', 'Y2', 'Z1', 'Z2'],
        str(sorted(k['id'] for k in _kotak)))
    _tumpuk = [(a['id'], b['id']) for i, a in enumerate(_kotak)
               for b in _kotak[i + 1:] if _tumpang(a, b)]
    cek('balik: oval tidak menabrak', not _tumpuk, str(_tumpuk))
    _mentah_my = DG.model_dari_peta_bab4(_peta_multi_y())
    _model_my, _masalah_my = DG.normalisasi_model(_mentah_my)
    cek('balik: peta multi-Y lolos normalisasi, kode Y1/Y2',
        _model_my is not None and
        [v['kode'] for v in _model_my['variabel']
         if v['peran'] == 'Y'] == ['Y1', 'Y2'],
        str(_masalah_my))


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
