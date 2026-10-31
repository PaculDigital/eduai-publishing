"""Uji perbaikan mesin buku, Gas Boss 31 Okt 2026 17:05.

Pola sama dengan uji_gerbang_subbab.py: mock, tanpa LLM nyata,
tanpa DB produksi, tanpa API. Mock panggil_llm hanya menulis ulang
satu kalimat dengan kata berbeda, bukan provider asli.

Jalankan dari checkout: /opt/data/.venv/bin/python uji_perbaiki_mesin_buku.py
Keluar 0 bila semua lulus, 1 bila ada yang gagal.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s   %s' % (nama, bukti))


def _row(kunci, alias, tahun, tampil, judul, jurnal, sumber, artikel_id):
    return {'kunci': kunci, 'alias': alias, 'tahun': tahun,
            'surname_tampil': tampil, 'artikel_id': artikel_id,
            'urutan': artikel_id, 'sumber': sumber,
            'ref_dict': {'authors': [tampil], 'year': int(tahun),
                         'title': judul, 'journal': jurnal,
                         'doi': '', 'type': 'article', 'source': sumber}}


ROWS_8 = [
    _row('tidaar', [], '2019', 'Tidaar',
         'UMKM Sebagai Pilar Membangun Ekonomi Bangsa',
         'Jurnal REP', 'OpenAlex', 1),
    _row('hardilawati', [], '2020', 'Hardilawati',
         'Digitalisasi UMKM di Indonesia', 'Jurnal Ekonomi', 'OpenAlex', 2),
    _row('macharia', ['daoping'], '2020', 'Macharia',
         'The influence of technology innovation on SME performance',
         'Technology in Society', 'CrossRef', 3),
    _row('rosita', [], '2020', 'Rosita',
         'Transformasi digital usaha kecil', 'Jurnal Manajemen', 'OpenAlex', 4),
    _row('arianto', [], '2021', 'Arianto',
         'Adopsi teknologi oleh UMKM', 'Jurnal Bisnis', 'OpenAlex', 5),
    _row('marina', ['dabic'], '2019', 'Marina',
         'Pathways of SME internationalization',
         'Small Business Economics', 'CrossRef', 6),
    _row('zhiqiang', ['lu'], '2021', 'Zhiqiang',
         'Local Bank and SME Financing', 'Emerging Markets Finance', 'CrossRef', 7),
    _row('prasanna', ['rpir'], '2019', 'Prasanna',
         'Sustainability of SMEs in the Competition',
         'Jurnal Kinerja', 'CrossRef', 8),
]

SUBS_1 = [('1.1', 'Definisi dan Konsep Kunci',
           'definisi transformasi digital dan usaha kecil'),
          ('1.2', 'Perkembangan Teori dan Kajian',
           'perkembangan adopsi teknologi dan kinerja bisnis'),
          ('1.3', 'Perbandingan Kritis',
           'perbandingan teori adopsi dan keberlanjutan usaha kecil'),
          ('1.4', 'Posisi dan Sintesis Penulis',
           'posisi penulis atas adopsi teknologi'),
          ('1.5', 'Implikasi',
           'implikasi bagi pelaku usaha kecil')]

KALIMAT_GANDA_1 = ('Kapabilitas absorptif: kapasitas kognitif dan manajerial '
                   'pemilik usaha untuk mengenali, mengasimilasi, dan '
                   'mengaplikasikan pengetahuan teknologi baru ke dalam '
                   'rutinitas bisnis.')
KALIMAT_GANDA_3 = ('Kapabilitas absorptif: kapasitas kognitif pemilik usaha '
                   'mikro untuk mengenali, mengasimilasi, dan '
                   'mengaplikasikan pengetahuan teknologi baru ke dalam '
                   'rutinitas bisnis.')


def _mock_llm(prompt):
    """Tulis ulang palsu: kata berbeda, makna sama, tanpa sitasi baru."""
    if 'Kapabilitas absorptif' in prompt:
        return ('Kemampuan serap: daya nalar pengelola usaha kecil dalam '
                'memahami, menyerap, serta memanfaatkan ilmu dan teknologi '
                'terkini bagi kegiatan usahanya sehari-hari.')
    return None


def main():
    from app import perbaiki_mesin_buku as PM
    from app import sitasi_anti_gagal as SG

    print('[1] KALIMAT GANDA: HANYA KALIMAT ITU DITULIS ULANG')
    bab1 = ('### 1.1 Definisi dan Konsep Kunci\n\n' + KALIMAT_GANDA_1 +
            ' Kalimat lain bab satu yang membahas definisi usaha kecil '
            'dan transformasi digital secara luas dan mendalam di banyak '
            'sektor bisnis modern yang terus berubah. Menurut Tidaar (2019), '
            'usaha kecil menjadi pilar ekonomi bangsa yang penting dan '
            'terus berkembang di tengah persaingan pasar yang ketat.')
    bab3 = ('### 3.1 Definisi dan Konsep Kunci\n\n' + KALIMAT_GANDA_3 +
            ' Kalimat lain bab tiga yang membahas adopsi teknologi oleh '
            'pelaku usaha mikro dan dinamika perubahan perilaku bisnis '
            'di era ekonomi digital yang semakin cepat dan kompleks. '
            'Menurut Macharia (2020), inovasi teknologi memengaruhi kinerja '
            'usaha kecil melalui praktik keberlanjutan lingkungan yang '
            'diterapkan secara konsisten oleh para pelaku usaha.')
    teks = {1: bab1, 3: bab3}
    baru, lap = PM.tulis_ulang_ganda(teks, _mock_llm)
    cek('kalimat ganda habis sesudah tulis ulang',
        not PM._ganda(baru), str(PM._ganda(baru)))
    cek('satu kalimat ditulis ulang, dicatat',
        len(lap['ditulis_ulang']) == 1, str(lap))
    cek('kalimat baru ada, kalimat lama bab 3 hilang',
        'Kemampuan serap' in baru[3] and KALIMAT_GANDA_3 not in baru[3])
    cek('kalimat bab 1 dipertahankan',
        KALIMAT_GANDA_1 in baru[1])
    cek('sitasi bab 3 tidak berubah',
        SG.ekstrak_sitasi_badan(baru[3]) and
        len(SG.ekstrak_sitasi_badan(baru[3])) ==
        len(SG.ekstrak_sitasi_badan(bab3)))

    print('[2] PUSTAKA: COCOK JADI LENGKAP, LUAR DIHAPUS, GANDA JADI SATU')
    teks2 = {
        1: ('Menurut Tidaar (2019), usaha kecil penting. '
            'Menurut Baker (2012), teori lama juga disebut. '
            'Menurut Macharia dan Daoping (2020), inovasi memengaruhi kinerja. '
            'Daoping (2020) juga dikutip sendiri dalam kalimat panjang '
            'yang membahas pengaruh inovasi teknologi terhadap kinerja usaha '
            'kecil secara menyeluruh dan terukur di banyak sektor.'),
    }
    rows2 = {1: ROWS_8}
    bersih, lap_hapus = PM.hapus_luar_per_bab(teks2, rows2)
    cek('sitasi luar dihapus, sitasi campuran dipertahankan',
        'Baker (2012)' not in bersih[1] and
        'Macharia dan Daoping (2020)' in bersih[1],
        bersih[1])
    pustaka, lap_pus = PM.pustaka_kanonik(bersih, rows2)
    cek('tidak ada placeholder di pustaka',
        not any('belum tersedia' in e for e in pustaka), str(pustaka))
    cek('entri Macharia hanya satu, walau dikutip dua bentuk',
        sum(1 for e in pustaka if 'technology innovation' in e) == 1,
        str(pustaka))
    cek('entri Tidaar lengkap dengan judul',
        any('UMKM Sebagai Pilar' in e for e in pustaka), str(pustaka))
    cek('entri Baker tidak ada',
        not any('Baker' in e for e in pustaka), str(pustaka))

    print('[3] CAKUPAN: 7 DARI 8 MENJADI 8 DARI 8')
    teks3 = ('### 1.3 Perbandingan Kritis\n\n'
             'Menurut Tidaar (2019), usaha kecil penting. '
             'Menurut Hardilawati (2020), digitalisasi berjalan. '
             'Menurut Macharia (2020), inovasi memengaruhi kinerja. '
             'Menurut Rosita (2020), transformasi berjalan. '
             'Menurut Arianto (2021), adopsi teknologi meluas. '
             'Menurut Marina (2019), internasionalisasi berjalan. '
             'Menurut Zhiqiang (2021), pembiayaan usaha dibahas. '
             'Kalimat penutup subbab perbandingan yang merangkum teori '
             'adopsi dan keberlanjutan usaha kecil secara menyeluruh.')
    cak_awal = SG.hitung_cakupan_kunci(teks3, ROWS_8)
    cek('cakupan awal 7 dari 8, hilang prasanna',
        cak_awal['cocok_jumlah'] == 7 and 'prasanna' in cak_awal['hilang'],
        str(cak_awal))
    teks3_baru, sisipan = PM.sisip_cakupan_per_bab(
        teks3, 1, ROWS_8, SUBS_1)
    cak_akhir = SG.hitung_cakupan_kunci(teks3_baru, ROWS_8)
    cek('cakupan akhir 8 dari 8',
        cak_akhir['cocok_jumlah'] == 8, str(cak_akhir))
    cek('satu sisipan, mengandung sitasi dan judul dari database',
        len(sisipan) == 1 and 'Prasanna (2019)' in sisipan[0]['kalimat']
        and 'Sustainability of SMEs' in sisipan[0]['kalimat'],
        str(sisipan))
    cek('sisipan tidak mengarang klaim hasil',
        'meningkat' not in sisipan[0]['kalimat'] and
        'terbukti' not in sisipan[0]['kalimat'], str(sisipan))

    print('[4] GAGAL BERSIH: BARIS TANPA JUDUL TIDAK DIRAKIT')
    rows_tanpa_judul = [dict(r) for r in ROWS_8]
    rows_tanpa_judul[7] = dict(rows_tanpa_judul[7])
    rows_tanpa_judul[7]['ref_dict'] = dict(
        rows_tanpa_judul[7]['ref_dict'], title='')
    try:
        PM.sisip_cakupan_per_bab(teks3, 1, rows_tanpa_judul, SUBS_1)
        cek('baris tanpa judul menggagalkan', False, 'tidak raise')
    except SG.GagalSitasiBersih as e:
        cek('galat menyebut bab dan baris hilang',
            'Bab 1' in str(e) and 'prasanna' in str(e).lower(),
            str(e))

    print('[5] ORKESTRASI: LUAR, SISIP, GANDA, DALAM URUTAN WAJIB')
    bab1_o = ('### 1.1 Definisi dan Konsep Kunci\n\n' + KALIMAT_GANDA_1 +
              ' Menurut Tidaar (2019), usaha kecil penting dan terus '
              'berkembang di tengah persaingan pasar yang ketat dan luas. '
              'Menurut Baker (2012), teori lama juga disebut dalam kalimat '
              'panjang yang membahas sejarah teori organisasi secara umum.')
    bab3_o = ('### 3.1 Definisi dan Konsep Kunci\n\n' + KALIMAT_GANDA_3 +
              ' Menurut Macharia (2020), inovasi memengaruhi kinerja usaha '
              'kecil melalui praktik keberlanjutan yang diterapkan secara '
              'konsisten oleh para pelaku usaha di banyak sektor.')
    # Lengkapi bab 1 dan 3 sampai 7 dari 8, hilang prasanna di keduanya,
    # supaya sisipan prasanna diuji di dua bab sekaligus.
    tambahan = (' Menurut Hardilawati (2020), digitalisasi berjalan. '
                'Menurut Rosita (2020), transformasi berjalan. '
                'Menurut Arianto (2021), adopsi teknologi meluas. '
                'Menurut Marina (2019), internasionalisasi berjalan. '
                'Menurut Zhiqiang (2021), pembiayaan usaha dibahas.')
    bab1_o += tambahan
    bab3_o += tambahan
    teks_o = {1: bab1_o, 3: bab3_o}
    rows_o = {1: ROWS_8, 3: ROWS_8}
    subs_o = {1: SUBS_1, 3: SUBS_1}
    final, lap_o = PM.perbaiki_buku(teks_o, rows_o, subs_o, _mock_llm)
    cek('luar dihapus di orkestrasi',
        'Baker (2012)' not in final[1], str(lap_o['hapus_luar']))
    cek('cakupan akhir 8 dari 8 di kedua bab',
        SG.hitung_cakupan_kunci(final[1], ROWS_8)['cocok_jumlah'] == 8 and
        SG.hitung_cakupan_kunci(final[3], ROWS_8)['cocok_jumlah'] == 8)
    cek('ganda habis sesudah orkestrasi',
        not PM._ganda(final), str(PM._ganda(final)))
    cek('tidak ada kalimat tidak teratasi',
        not lap_o['ganda']['tidak_teratasi'], str(lap_o['ganda']))
    cek('inisial saja tetap 0',
        not SG.pindai_inisial(final[1]) and not SG.pindai_inisial(final[3]))
    pustaka_o, _ = PM.pustaka_kanonik(final, rows_o)
    cek('pustaka orkestrasi tanpa placeholder',
        not any('belum tersedia' in e for e in pustaka_o), str(pustaka_o))
    cek('pustaka orkestrasi 8 entri, satu per artikel',
        len(pustaka_o) == 8, str(pustaka_o))

    print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
