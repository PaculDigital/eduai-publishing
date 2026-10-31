"""Uji gerbang per subbab, galat detail, metrik baris snapshot,
Layer 1 dihapus, dan cache bidang (Gas Bos 31 Okt 2026 12:03).

Pola sama dengan uji_anti_gagal_sitasi.py: mock, tanpa LLM nyata,
tanpa DB produksi, tanpa API. DB uji hanya sqlite memori untuk
cache_topik. Uji pipeline memakai call_llm palsu.

Jalankan dari checkout: /opt/data/.venv/bin/python uji_gerbang_subbab.py
Keluar 0 bila semua lulus, 1 bila ada yang gagal.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


ROWS = [
    {'kunci': 'dabic', 'alias': ['marina'], 'tahun': '2019',
     'surname_tampil': 'Dabic', 'authors': ['Dabic, Marina']},
    {'kunci': 'lu', 'alias': ['zhiqiang'], 'tahun': '2021',
     'surname_tampil': 'Lu', 'authors': ['Lu, Zhiqiang']},
    {'kunci': 'tidaar', 'alias': ['universitas'], 'tahun': '2019',
     'surname_tampil': 'Tidaar', 'authors': ['Universitas Tidaar']},
    {'kunci': 'macharia', 'alias': [], 'tahun': '2020',
     'surname_tampil': 'Macharia', 'authors': ['Macharia, Daoping']},
    {'kunci': 'rosita', 'alias': [], 'tahun': '2020',
     'surname_tampil': 'Rosita', 'authors': ['Rosita, R.']},
    {'kunci': 'arianto', 'alias': [], 'tahun': '2021',
     'surname_tampil': 'Arianto', 'authors': ['Arianto, B.']},
    {'kunci': 'hardilawati', 'alias': [], 'tahun': '2020',
     'surname_tampil': 'Hardilawati', 'authors': ['Hardilawati, W. L.']},
    {'kunci': 'prasanna', 'alias': ['rpir'], 'tahun': '2019',
     'surname_tampil': 'Prasanna', 'authors': ['Prasanna, R.']},
]


def main():
    from app.gerbang_subbab import (
        periksa_subbab, rows_dari_refs_dicts, GagalSubbab)
    from app import sitasi_anti_gagal as SG
    from app import cek_awal as CA

    print('[1] GERBANG LOLOS BILA ADA SITASI SNAPSHOT')
    r = periksa_subbab(
        'Menurut Dabic (2019), transformasi digital mengubah bisnis '
        'secara luas dan mendalam di banyak sektor.', ROWS,
        bab=2, subbab='2.1')
    cek('lolos bila ada sitasi snapshot kurung', r['lolos'], str(r['masalah']))
    cek('snapshot_count 1', r['snapshot_count'] == 1, str(r['snapshot_count']))
    r = periksa_subbab(
        'Dabic (2019) menyatakan transformasi digital mengubah bisnis '
        'secara luas dan mendalam di banyak sektor.', ROWS,
        bab=2, subbab='2.1')
    cek('lolos bila ada sitasi snapshot naratif', r['lolos'], str(r['masalah']))

    print('\n[2] GERBANG GAGAL BILA 0 SNAPSHOT')
    r = periksa_subbab(
        'Menurut Verhoef (2021), digital mengubah bisnis secara luas.',
        ROWS, bab=2, subbab='2.2')
    cek('gagal bila 0 snapshot', not r['lolos'], str(r))
    cek('teks bersih tanpa sitasi luar',
        'Verhoef' not in r['teks_bersih'], r['teks_bersih'])
    cek('luar dihapus tercatat', len(r['luar_dihapus']) == 1,
        str(r['luar_dihapus']))

    print('\n[3] GERBANG GAGAL BILA HANYA INISIAL SAJA')
    # Inisial M tidak cocok dengan kandidat Dabic (inisial D) maupun
    # Lu (inisial L), jadi tidak bisa diperbaiki deterministik.
    r = periksa_subbab(
        'Menurut (M., 2019), digital mengubah bisnis secara luas.',
        ROWS, bab=2, subbab='2.3')
    cek('gagal bila hanya inisial tak terperbaiki',
        not r['lolos'] and r['inisial_sisa'], str(r))
    cek('snapshot_count 0', r['snapshot_count'] == 0,
        str(r['snapshot_count']))

    print('\n[4] GERBANG LOLOS BILA SITASI MEMAKAI ALIAS, TAHUN SAMA')
    r = periksa_subbab(
        'Menurut Marina (2019), transformasi digital mengubah bisnis '
        'secara luas dan mendalam di banyak sektor.', ROWS,
        bab=2, subbab='2.4')
    cek('lolos alias Marina untuk Dabic 2019', r['lolos'], str(r['masalah']))
    r = periksa_subbab(
        'Menurut Zhiqiang (2021), adopsi teknologi mengubah bisnis '
        'secara luas dan mendalam di banyak sektor.', ROWS,
        bab=2, subbab='2.4')
    cek('lolos alias Zhiqiang untuk Lu 2021', r['lolos'], str(r['masalah']))

    print('\n[5] GERBANG GAGAL BILA TAHUN BEDA')
    r = periksa_subbab(
        'Menurut Marina (2020), transformasi digital mengubah bisnis.',
        ROWS, bab=2, subbab='2.5')
    cek('gagal bila tahun beda', not r['lolos'], str(r))
    cek('sitasi tahun beda dihapus sebagai luar',
        'Marina (2020)' not in r['teks_bersih'], r['teks_bersih'])

    print('\n[6] SITASI LUAR TERHAPUS DETERMINISTIK, TIDAK TERSISA')
    r = periksa_subbab(
        'Menurut Dabic (2019), digital penting. Sementara Verhoef (2021) '
        'dan Ries (2011) menulis hal lain yang juga menarik.',
        ROWS, bab=2, subbab='2.6')
    cek('lolos sesudah luar dihapus', r['lolos'], str(r['masalah']))
    cek('tidak ada sitasi luar tersisa', not r['luar_sisa'],
        str(r['luar_sisa']))
    cek('sitasi snapshot dipertahankan',
        'Dabic (2019)' in r['teks_bersih'], r['teks_bersih'])
    cek('dua sitasi luar dihapus', len(r['luar_dihapus']) == 2,
        str(r['luar_dihapus']))

    print('\n[7] SITASI CAMPURAN: SATU SURNAME SNAPSHOT, SATU LUAR')
    r = periksa_subbab(
        'Menurut Dabic dan Verhoef (2019), digital mengubah bisnis '
        'secara luas dan mendalam di banyak sektor.', ROWS,
        bab=2, subbab='2.7')
    cek('tidak dihitung luar (satu surname snapshot)',
        r['lolos'] and not r['luar_dihapus'], str(r))

    print('\n[8] BARIS DARI REFS DICT SAMA ARAH DENGAN PANEN')
    refs = [{'authors': ['Dabic, Marina'], 'year': 2019},
            {'authors': ['Lu, Zhiqiang'], 'year': 2021}]
    rows_turunan = rows_dari_refs_dicts(refs)
    cek('turunan 2 baris', len(rows_turunan) == 2, str(rows_turunan))
    cek('kunci dabic, alias marina',
        rows_turunan[0]['kunci'] == 'dabic'
        and 'marina' in rows_turunan[0]['alias'], str(rows_turunan[0]))

    print('\n[9] GALAT DETAIL MEMUAT BAB, CAKUPAN, PESAN MANUSIA')
    detail = SG.detail_galat_sitasi(
        2, {'total': 8, 'cocok_jumlah': 0, 'sitasi_snapshot': 0})
    cek('detail memuat Bab 2', 'Bab 2' in detail, detail)
    cek('detail memuat 0 dari 8', '0 dari 8' in detail, detail)
    cek('detail memuat sitasi snapshot 0', 'sitasi snapshot 0' in detail,
        detail)
    e_detail = SG.GagalSitasiBersih(
        nomor_bab=2, cakupan={'total': 8, 'cocok_jumlah': 0},
        detail_text=detail)
    cek('galat detail memuat pesan manusia',
        SG.PESAN_GAGAL_BERSIH in str(e_detail), str(e_detail))
    cek('galat detail memuat Token sudah kembali',
        'Token sudah kembali' in str(e_detail), str(e_detail))
    e_default = SG.GagalSitasiBersih(nomor_bab=5)
    cek('galat default tetap pesan tepat',
        str(e_default) == SG.PESAN_GAGAL_BERSIH, str(e_default))
    try:
        raise GagalSubbab(bab=2, subbab='2.2', hasil={
            'cakupan_total': 8, 'cakupan_cocok': 0, 'snapshot_count': 0,
            'luar_dihapus': ['Verhoef (2021)'], 'inisial_sisa': []})
    except GagalSubbab as e_sub:
        cek('GagalSubbab memuat bab dan subbab',
            'Bab 2' in str(e_sub) and '2.2' in str(e_sub), str(e_sub))
        cek('GagalSubbab adalah ValueError (tidak di-retry A1)',
            isinstance(e_sub, ValueError), type(e_sub).__name__)
        cek('GagalSubbab memuat cakupan 0 dari 8',
            '0 dari 8' in str(e_sub), str(e_sub))
    else:
        cek('GagalSubbab bisa di-raise', False)

    print('\n[10] METRIK CEK PER BAB BARU: PER BARIS SNAPSHOT')
    teks_7dari8 = (
        'Dabic (2019) menulis. Lu (2021) menulis. Tidaar (2019) menulis. '
        'Macharia (2020) menulis. Rosita (2020) menulis. '
        'Arianto (2021) menulis. Hardilawati (2020) menulis. '
        'Tidak ada sitasi kedelapan di sini.')
    tmp = tempfile.mkdtemp(prefix='uji_cek_awal_')
    try:
        os.makedirs(os.path.join(tmp, 'visual'), exist_ok=True)
        with open(os.path.join(tmp, 'visual', 'tabel_bab2.json'),
                  'w', encoding='utf-8') as f:
            f.write('[{"a": 1}]')
        hasil = CA.periksa_bab_awal(
            2, teks_7dari8, tmp, snapshot_rows=ROWS)
        gabung = ' '.join(hasil['masalah'] + hasil['curiga'])
        cek('pesan 7 dari 8 baris snapshot',
            '7 dari 8 baris snapshot' in gabung, gabung)
        cek('tidak ada lagi 7 dari 15 surname',
            '15' not in gabung, gabung)
        hasil0 = CA.periksa_bab_awal(
            2, 'Tidak ada sitasi sama sekali di sini.', tmp,
            snapshot_rows=ROWS)
        gabung0 = ' '.join(hasil0['masalah'] + hasil0['curiga'])
        cek('pesan 0 dari 8 baris snapshot',
            '0 dari 8 baris snapshot' in gabung0, gabung0)
        hasil_kosong = CA.periksa_bab_awal(
            2, teks_7dari8, tmp, snapshot_rows=[])
        gabung_k = ' '.join(hasil_kosong['masalah'] + hasil_kosong['curiga'])
        cek('snapshot kosong eksplisit tidak lolos diam',
            'tidak ada baris snapshot' in gabung_k, gabung_k)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print('\n[11] LAYER 1 TIDAK LAGI DIPANGGIL (penyusun_buku)')
    import penyusun_buku as PB
    cek('tidak ada string perbaikan TIDAK lebih baik di sumber',
        'perbaikan TIDAK lebih baik' not in open(
            PB.__file__, encoding='utf-8').read())
    # Alur susun_buku dengan generate_bab palsu: buku berulang harus
    # memanggil generate_bab tepat 2 kali (satu per bab), tanpa
    # putaran perbaikan, dan tanpa pesan perbaikan penuh di lapor.
    import buku_umum_pipeline as PIPE
    asli_generate = PIPE.generate_bab
    pesan_lapor = []

    def _gen_palsu(n, info, ringkasan, jenis=None, tier=None):
        teks = isi_unik_palsu(1) if n in (1, 2) else isi_unik_palsu(n)
        return teks, f'ringkasan bab {n}', len(teks.split()), 3

    def isi_unik_palsu(n, jumlah_kalimat=34):
        topik = {1: ('uap air naik', 'titik embun', 'awan putih'),
                 2: ('butir air bergabung', 'gaya tarik', 'hujan turun')}[n]
        kal = []
        for i in range(jumlah_kalimat):
            kal.append(f'Pada bagian {i + 1}, {topik[0]} sehingga {topik[1]} '
                       f'menjadi penentu utama bagi {topik[2]} di lingkungan itu.')
        return ' '.join(kal)

    def _lapor(pesan, *_a, **_k):
        pesan_lapor.append(str(pesan))

    outline_palsu = {
        1: {'title': 'Terjadinya Awan',
            'subs': [(1, 'Uap air', 'panas matahari membuat air menguap')]},
        2: {'title': 'Terjadinya Hujan',
            'subs': [(1, 'Butir air', 'titik air bergabung dan menjadi berat')]},
    }
    tmp2 = tempfile.mkdtemp(prefix='uji_layer1_')
    try:
        PIPE.generate_bab = _gen_palsu
        # Hitung panggilan generate_bab lewat pembungkus.
        hitung = {'n': 0}
        _gen_asli_palsu = PIPE.generate_bab

        def _gen_hitung(n, info, ringkasan, jenis=None, tier=None):
            hitung['n'] += 1
            return _gen_asli_palsu(n, info, ringkasan, jenis=jenis, tier=tier)

        PIPE.generate_bab = _gen_hitung
        r_layer = PB.susun_buku('Judul Uji', outline_palsu, jenis='anak',
                                keluar_dir=tmp2, lapor=_lapor)
        cek('generate_bab hanya 2 panggilan, tanpa putaran perbaikan',
            hitung['n'] == 2, str(hitung['n']))
        cek('tidak ada pesan perbaikan penuh di lapor',
            not any('perbaikan TIDAK lebih baik' in p for p in pesan_lapor),
            str(pesan_lapor))
        cek('mutu_lolos False secara jujur untuk buku berulang',
            r_layer['mutu_lolos'] is False, str(r_layer['mutu_lolos']))
    finally:
        PIPE.generate_bab = asli_generate
        import shutil
        shutil.rmtree(tmp2, ignore_errors=True)

    print('\n[12] TULIS ULANG SUBBAB HANYA SEKALI (pipeline, LLM palsu)')
    import buku_umum_pipeline as PIPE2
    asli_call = PIPE2.call_llm
    hitung_arsitek = {'n': 0}
    teks_gagal_gate = (
        'Menurut Verhoef (2021), digital mengubah bisnis secara luas '
        'dan mendalam di banyak sektor dan pasar.')

    def _call_palsu(prompt, **kw):
        if 'Kamu adalah Architect' in (prompt or ''):
            hitung_arsitek['n'] += 1
        return teks_gagal_gate

    tmp3 = tempfile.mkdtemp(prefix='uji_gate_pipeline_')
    try:
        PIPE2.call_llm = _call_palsu
        PIPE2.folder_bab(tmp3)
        os.makedirs(os.path.join(tmp3, 'visual'), exist_ok=True)
        refs_pipeline = [{'authors': ['Dabic, Marina'], 'year': 2019,
                          'title': 'Uji', 'source': 'Scopus'},
                         {'authors': ['Lu, Zhiqiang'], 'year': 2021,
                          'title': 'Uji2', 'source': 'OpenAlex'}]
        try:
            PIPE2.generate_sub_bab(
                2, 'Bab Uji', '2.1', 'Sub Uji', 'poin kunci', 'ringkasan',
                refs=refs_pipeline, jenis='referensi', dari_snapshot=True,
                snapshot_rows=ROWS[:2])
            cek('GagalSubbab di-raise sesudah tulis ulang gagal', False)
        except GagalSubbab as e_pipe:
            cek('GagalSubbab di-raise sesudah tulis ulang gagal', True,
                str(e_pipe))
            cek('arsitek dipanggil tepat 2 kali (awal + 1 tulis ulang)',
                hitung_arsitek['n'] == 2, str(hitung_arsitek['n']))
        except Exception as e_lain:
            cek('GagalSubbab di-raise (bukan galat lain)', False,
                f'{type(e_lain).__name__}: {e_lain}')
    finally:
        PIPE2.call_llm = asli_call
        try:
            PIPE2.lepas_folder()
        except Exception:
            pass
        import shutil
        shutil.rmtree(tmp3, ignore_errors=True)

    print('\n[13] TEMPLATE KERANGKA MEMBAWA BIDANG KE SUSUN')
    try:
        # Template memakai ikon() dan fungsi lain dari konteks app,
        # jadi uji ini hanya memeriksa teks sumber, bukan render penuh.
        _tpl_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
        if not os.path.isdir(_tpl_dir):
            _tpl_dir = '/opt/data/services/eduai-publishing/app/templates'
        with open(os.path.join(_tpl_dir, 'buku_outline.html'),
                  encoding='utf-8') as _f:
            _sumber_tpl = _f.read()
        cek('form Setuju memuat hidden bidang',
            'action="/buku/susun"' in _sumber_tpl
            and 'name="bidang"' in _sumber_tpl, 'hidden bidang tidak ada')
        cek('form edit memuat hidden bidang',
            'action="/buku/outline/simpan"' in _sumber_tpl
            and _sumber_tpl.count('name="bidang"') >= 2,
            f"jumlah hidden bidang: {_sumber_tpl.count('name=\"bidang\"')}")
    except Exception as e_tpl:
        cek('template kerangka diperiksa', False,
            f'{type(e_tpl).__name__}: {e_tpl}')

    print(f'\n{"=" * 64}\nGERBANG SUBBAB: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 64}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
