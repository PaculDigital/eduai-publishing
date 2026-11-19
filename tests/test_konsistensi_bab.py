"""Cek konsistensi antar bab: ekstrak 6 bagian + urai jawaban LLM (19 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB. Fixture peta tiruan mengikuti
pola peta fid 81 (penanda telanjang BAB I..V, subbab berlabel, paragraf).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import konsistensi as kb


def cek(nama, benar):
    print(("  LULUS  " if benar else "  GAGAL  ") + nama)
    return benar


def peta_tiruan():
    """Peta kecil: 5 bab, 6 bagian yang dicari + 1 gema Sistematika."""
    baris = [
        'BAB I', 'PENDAHULUAN',
        '1.1 Latar Belakang',
        'Latar belakang masalah penelitian ini.',
        '1.2 Rumusan Masalah',
        'Apakah Digital Marketing berpengaruh terhadap Keberlanjutan Usaha?',
        'Apakah Orientasi Kewirausahaan berpengaruh terhadap Keberlanjutan Usaha?',
        '1.3 Tujuan Penelitian',
        'Tujuan penelitian ini untuk membuktikan pengaruh Digital Marketing terhadap Keberlanjutan Usaha.',
        '1.4 Sistematika Penulisan',
        'Bab IV memuat hasil penelitian dan pembahasan.',
        'BAB II', 'TINJAUAN PUSTAKA',
        '2.1 Digital Marketing',
        'Teori Digital Marketing.',
        '2.4 Hipotesis',
        'Hipotesis Pertama: Digital Marketing berpengaruh terhadap Keberlanjutan Usaha.',
        'Hipotesis Kedua: Orientasi Kewirausahaan berpengaruh terhadap Keberlanjutan Usaha.',
        'BAB III', 'METODE PENELITIAN',
        '3.1 Jenis dan Desain Penelitian',
        'Penelitian kuantitatif dengan pendekatan korelasional.',
        '3.5 Metode Analisis',
        'Analisis regresi linier berganda dan uji t untuk menguji hipotesis.',
        'BAB IV', 'HASIL DAN PEMBAHASAN',
        '4.1 Hasil Penelitian',
        'Hasil uji t menunjukkan Digital Marketing berpengaruh signifikan terhadap Keberlanjutan Usaha.',
        '4.2 Pembahasan',
        'Pembahasan hasil.',
        'BAB V', 'PENUTUP',
        '5.1 Kesimpulan',
        'Digital Marketing berpengaruh terhadap Keberlanjutan Usaha, sesuai hipotesis pertama.',
        '5.2 Saran',
        'Saran untuk penelitian berikutnya.',
    ]
    label = {}
    for i, t in enumerate(baris):
        if t.startswith('BAB ') and len(t.split()) == 2:
            continue
        if t in ('PENDAHULUAN', 'TINJAUAN PUSTAKA', 'METODE PENELITIAN',
                 'HASIL DAN PEMBAHASAN', 'PENUTUP'):
            continue
        if t[0].isdigit() and t[1] == '.':
            label[str(i)] = 'subbab'
        else:
            label[str(i)] = 'paragraf'
    return {'peta_surveyor': {'baris': baris, 'label': label}}


def main():
    lulus = 0
    total = 0

    def t(nama, benar):
        nonlocal lulus, total
        total += 1
        if cek(nama, benar):
            lulus += 1

    # --- Ekstrak 6 bagian dari peta tiruan ---
    bagian = kb.ekstrak_bagian_bab(peta_tiruan())
    t('masalah terekstrak (ada pertanyaan)',
      'Digital Marketing berpengaruh' in bagian['masalah'])
    t('tujuan terekstrak',
      'membuktikan pengaruh' in bagian['tujuan'])
    t('hipotesis terekstrak (H1 + H2)',
      'Hipotesis Pertama' in bagian['hipotesis']
      and 'Hipotesis Kedua' in bagian['hipotesis'])
    t('metode menggabungkan desain + analisis',
      'korelasional' in bagian['metode']
      and 'regresi linier berganda' in bagian['metode'])
    t('hasil terekstrak (uji t)',
      'uji t' in bagian['hasil'].lower())
    t('kesimpulan terekstrak',
      'berpengaruh terhadap Keberlanjutan' in bagian['kesimpulan'])
    t('gema Sistematika tidak tertangkap sebagai hasil',
      'Bab IV memuat hasil' not in bagian['hasil'])

    # --- Subbab wadah (tanpa paragraf langsung) dilewati ---
    # Pola fid 81: 'Hipotesis dan Model Penelitian' lalu 'Hipotesis';
    # 'Hasil Penelitian' lalu 'Deskripsi Data Penelitian'. Yang dipakai
    # subbab yang punya isi, bukan wadahnya.
    peta_wadah = {
        'peta_surveyor': {
            'baris': [
                'BAB II', 'TINJAUAN PUSTAKA',
                '2.4 Hipotesis dan Model Penelitian',
                '2.4.1 Hipotesis',
                'Hipotesis Pertama: X berpengaruh terhadap Y.',
                'BAB IV', 'HASIL DAN PEMBAHASAN',
                '4.1 Hasil Penelitian',
                '4.1.1 Hasil Analisis Data',
                'Hasil uji t menunjukkan X berpengaruh signifikan.',
            ],
            'label': {
                '2': 'subbab', '3': 'subbab', '4': 'paragraf',
                '7': 'subbab', '8': 'subbab', '9': 'paragraf',
            },
        }
    }
    b3 = kb.ekstrak_bagian_bab(peta_wadah)
    t('wadah hipotesis dilewati, isi H1 dipakai',
      'Hipotesis Pertama' in b3['hipotesis'])
    t('wadah hasil dilewati, isi uji t dipakai',
      'uji t' in b3['hasil'].lower())

    # --- Bagian hilang -> '' ---
    peta_kosong = {'peta_surveyor': {'baris': ['BAB I', 'PENDAHULUAN'],
                                     'label': {}}}
    b2 = kb.ekstrak_bagian_bab(peta_kosong)
    t('peta tanpa bagian -> semua kosong',
      all(v == '' for v in b2.values()))
    t('peta rusak (bukan JSON) -> semua kosong',
      all(v == '' for v in kb.ekstrak_bagian_bab('bukan-json').values()))

    # --- Prompt memuat 6 bagian + 5 sambungan ---
    prompt = kb.susun_prompt_bab(bagian)
    t('prompt memuat 6 judul bagian',
      all(x in prompt for x in ('Rumusan Masalah', 'Tujuan Penelitian',
                                'Hipotesis', 'Metode', 'Hasil Penelitian',
                                'Kesimpulan')))
    t('prompt memuat 5 sambungan',
      all(x in prompt for x in ('masalah_tujuan', 'tujuan_hipotesis',
                                'hipotesis_metode', 'metode_hasil',
                                'hasil_kesimpulan')))
    t('prompt menandai bagian hilang',
      '(tidak ditemukan di naskah)' in kb.susun_prompt_bab({}))

    # --- Urai jawaban LLM ---
    jawaban = json.dumps({'sambungan': [
        {'nama': 'masalah_tujuan', 'vonis': 'nyambung',
         'alasan': 'Tujuan menjawab pertanyaan pertama.'},
        {'nama': 'tujuan_hipotesis', 'vonis': 'nyambung', 'alasan': ''},
        {'nama': 'hipotesis_metode', 'vonis': 'putus',
         'alasan': 'Uji t tidak menguji H2 karena H2 tentang interaksi.'},
        {'nama': 'metode_hasil', 'vonis': 'ragu', 'alasan': 'Bukti kurang.'},
        {'nama': 'hasil_kesimpulan', 'vonis': 'aneh',
         'alasan': 'Vonis tidak sah.'},
    ]})
    vonis = kb.urai_jawaban_bab(jawaban)
    t('urai: 5 vonis', len(vonis) == 5)
    t('urai: nyambung dipertahankan',
      vonis[0]['vonis'] == 'nyambung')
    t('urai: alasan kosong diganti kalimat baku',
      vonis[1]['alasan'] != '')
    t('urai: putus + alasan spesifik',
      vonis[2]['vonis'] == 'putus' and 'H2' in vonis[2]['alasan'])
    t('urai: vonis tidak sah -> ragu',
      vonis[4]['vonis'] == 'ragu')
    t('urai: jawaban rusak -> semua ragu',
      all(v['vonis'] == 'ragu' for v in kb.urai_jawaban_bab('bukan json')))
    t('urai: jawaban kosong -> semua ragu',
      all(v['vonis'] == 'ragu' for v in kb.urai_jawaban_bab('')))

    # --- Langkah berikut ---
    t('langkah: ada putus -> sebut sambungannya',
      kb.langkah_berikut_bab(vonis) == 'Perbaiki sambungan Hipotesis ke Metode.')
    t('langkah: hanya ragu -> cek ke pembimbing',
      'pembimbing' in (kb.langkah_berikut_bab(
          [{'nama': 'x', 'label': 'A ke B', 'vonis': 'ragu',
            'alasan': ''}]) or ''))
    t('langkah: semua nyambung -> None',
      kb.langkah_berikut_bab([{'nama': 'x', 'label': 'A', 'vonis': 'nyambung',
                           'alasan': ''}]) is None)

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    sys.exit(main())
