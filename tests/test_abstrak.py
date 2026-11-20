"""Cek Abstrak: pemeriksa di bagian_awal.py (20 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB live. Vonis LLM diuji lewat
`jawaban_llm` (teks jawaban palsu). Spasi diuji lewat fixture .docx
kecil (python-docx). Abstrak uji memakai variabel fid 81 (Digital
Marketing, Orientasi Kewirausahaan, Keberlanjutan Usaha).
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import bagian_awal as BA


def cek(nama, benar):
    print(("  LULUS  " if benar else "  GAGAL  ") + nama)
    return benar


# Abstrak uji: 180 kata ID, 198 kata EN (dalam 150-300).
KALIMAT_ID = ('Penelitian ini menguji pengaruh digital marketing dan '
              'orientasi kewirausahaan terhadap keberlanjutan usaha pada '
              'UMKM kuliner ayam bakar di Kabupaten Bekasi. ')
KALIMAT_EN = ('This study examines the effect of digital marketing and '
              'entrepreneurial orientation on business sustainability of '
              'grilled chicken culinary MSMEs in Bekasi Regency. ')
DRAF_BENAR = {'id': [KALIMAT_ID * 9], 'en': [KALIMAT_EN * 9],
              'kunci_id': ['digital marketing', 'orientasi kewirausahaan',
                           'keberlanjutan usaha'],
              'kunci_en': ['digital marketing', 'entrepreneurial orientation',
                           'business sustainability']}
BAGIAN = {'masalah': 'UMKM kuliner ayam bakar sulit bertahan.',
          'tujuan': 'Menguji pengaruh digital marketing.',
          'hipotesis': 'Digital marketing berpengaruh positif.',
          'metode': 'Kuantitatif, 100 responden, regresi.',
          'hasil': 'Digital marketing berpengaruh signifikan.',
          'kesimpulan': 'Digital marketing meningkatkan keberlanjutan.'}
JAWABAN_COCOK = ('{"vonis": [{"nama": "cocok_id", "vonis": "cocok", '
                 '"alasan": "Abstrak menyebut masalah, metode, hasil."}, '
                 '{"nama": "cocok_en", "vonis": "cocok", '
                 '"alasan": "Isi Inggris sama dengan Indonesia."}, '
                 '{"nama": "kunci", "vonis": "cocok", '
                 '"alasan": "Kata kunci sesuai variabel."}]}')
JAWABAN_TIDAK = ('{"vonis": [{"nama": "cocok_id", "vonis": "tidak", '
                 '"alasan": "Abstrak tidak menyebut hasil."}, '
                 '{"nama": "cocok_en", "vonis": "cocok", '
                 '"alasan": "Isi Inggris sama."}, '
                 '{"nama": "kunci", "vonis": "ragu", '
                 '"alasan": "Kata kunci belum bisa diputuskan."}]}')


def buat_docx(jalur, spasi, ada_abstrak=True):
    """Fixture .docx kecil: judul ABSTRAK + 2 paragraf isi + BAB I."""
    from docx import Document
    doc = Document()
    if ada_abstrak:
        doc.add_paragraph('ABSTRAK')
        for teks in ('Paragraf abstrak pertama yang cukup panjang untuk '
                     'diperiksa spasinya dengan benar.',
                     'Paragraf abstrak kedua yang juga cukup panjang.'):
            p = doc.add_paragraph(teks)
            p.paragraph_format.line_spacing = spasi
    doc.add_paragraph('BAB I')
    doc.add_paragraph('Paragraf bab satu.')
    doc.save(str(jalur))


def main():
    lulus = 0
    total = 0

    def t(nama, benar):
        nonlocal lulus, total
        total += 1
        if cek(nama, benar):
            lulus += 1

    # --- _teks_abstrak ---
    teks = BA._teks_abstrak(DRAF_BENAR)
    t('_teks_abstrak: id 180 kata', len(teks['id'].split()) == 180)
    t('_teks_abstrak: kunci digabung koma',
      teks['kunci_id'].startswith('digital marketing,'))
    t('_teks_abstrak: bukan dict -> kosong',
      BA._teks_abstrak(None) == {'id': '', 'en': '', 'kunci_id': '',
                                 'kunci_en': ''})
    t('sidik_abstrak: stabil + beda bila isi beda',
      BA.sidik_abstrak(DRAF_BENAR) == BA.sidik_abstrak(DRAF_BENAR)
      and BA.sidik_abstrak(DRAF_BENAR)
      != BA.sidik_abstrak({**DRAF_BENAR, 'id': ['beda']}))

    # --- susun_prompt_abstrak ---
    prompt = BA.susun_prompt_abstrak(teks, BAGIAN)
    t('prompt: memuat abstrak ID + EN',
      'UMKM kuliner ayam bakar' in prompt and 'grilled chicken' in prompt)
    t('prompt: memuat 6 bagian',
      all(k in prompt for k in ('Rumusan Masalah', 'Tujuan Penelitian',
                                'Hipotesis', 'Metode', 'Hasil Penelitian',
                                'Kesimpulan')))
    t('prompt: meminta JSON saja', 'Jawab HANYA dengan JSON' in prompt)

    # --- urai_jawaban_abstrak ---
    vonis = BA.urai_jawaban_abstrak(JAWABAN_COCOK)
    t('urai: 3 vonis cocok',
      [v['vonis'] for v in vonis] == ['cocok', 'cocok', 'cocok'])
    vonis2 = BA.urai_jawaban_abstrak(JAWABAN_TIDAK)
    t('urai: tidak + ragu dipertahankan',
      [v['vonis'] for v in vonis2] == ['tidak', 'cocok', 'ragu'])
    vonis3 = BA.urai_jawaban_abstrak('bukan json')
    t('urai rusak: semua ragu',
      [v['vonis'] for v in vonis3] == ['ragu', 'ragu', 'ragu'])
    vonis4 = BA.urai_jawaban_abstrak(
        '{"vonis": [{"nama": "cocok_id", "vonis": "aneh", "alasan": ""}]}')
    t('urai: vonis di luar 3 sah -> ragu',
      vonis4[0]['vonis'] == 'ragu'
      and vonis4[0]['alasan'] == 'Belum bisa diputuskan dari naskah.')

    # --- periksa_panjang_abstrak ---
    pj = BA.periksa_panjang_abstrak(teks)
    t('panjang: 180/198 kata -> lulus', pj['vonis'] == 'lulus')
    pj2 = BA.periksa_panjang_abstrak({'id': 'Terlalu pendek.',
                                      'en': 'Too short.'})
    t('panjang: 2/2 kata -> tidak + sebut jumlah',
      pj2['vonis'] == 'tidak' and '2 kata' in pj2['alasan'])

    # --- periksa_spasi_abstrak (fixture docx) ---
    with tempfile.TemporaryDirectory() as tmp:
        f1 = Path(tmp) / 'spasi1.docx'
        buat_docx(f1, 1.0)
        t('spasi: 1.0 -> lulus',
          BA.periksa_spasi_abstrak(f1)['vonis'] == 'lulus')
        f2 = Path(tmp) / 'spasi15.docx'
        buat_docx(f2, 1.5)
        sp15 = BA.periksa_spasi_abstrak(f2)
        t('spasi: 1.5 -> tidak + sebut angka',
          sp15['vonis'] == 'tidak' and '1.5' in sp15['alasan'])
        f3 = Path(tmp) / 'tanpa.docx'
        buat_docx(f3, 1.0, ada_abstrak=False)
        t('spasi: tanpa bagian abstrak -> ragu',
          BA.periksa_spasi_abstrak(f3)['vonis'] == 'ragu')
        t('spasi: jalur tidak ada -> ragu',
          BA.periksa_spasi_abstrak(Path(tmp) / 'hilang.docx')['vonis']
          == 'ragu')

    # --- periksa_abstrak (lengkap) ---
    with tempfile.TemporaryDirectory() as tmp:
        f1 = Path(tmp) / 'spasi1.docx'
        buat_docx(f1, 1.0)
        hasil = BA.periksa_abstrak(DRAF_BENAR, BAGIAN, jalur_docx=f1,
                                   jawaban_llm=JAWABAN_COCOK)
        t('lengkap: 5 temuan',
          len(hasil['temuan']) == 5)
        t('lengkap: ringkasan cocok 3 lulus 2',
          hasil['ringkasan'] == {'cocok': 3, 'lulus': 2, 'tidak': 0,
                                 'ragu': 0})
        t('lengkap: semua cocok/lulus -> langkah None',
          hasil['langkah_berikut'] is None)
        hasil2 = BA.periksa_abstrak(DRAF_BENAR, BAGIAN, jalur_docx=f1,
                                    jawaban_llm=JAWABAN_TIDAK)
        t('lengkap: ada tidak -> langkah sebut label',
          hasil2['langkah_berikut'] == 'Perbaiki Abstrak cocok dengan isi.')
        hasil3 = BA.periksa_abstrak(DRAF_BENAR, BAGIAN, jalur_docx=f1,
                                    jawaban_llm=None)
        t('lengkap: tanpa jawaban LLM -> vonis LLM ragu',
          [v['vonis'] for v in hasil3['temuan'][:3]]
          == ['ragu', 'ragu', 'ragu'])
        hasil4 = BA.periksa_abstrak(None, BAGIAN, jalur_docx=f1,
                                    jawaban_llm=JAWABAN_COCOK)
        t('lengkap: abstrak kosong -> semua ragu (5)',
          hasil4['ringkasan'] == {'cocok': 0, 'lulus': 0, 'tidak': 0,
                                  'ragu': 5}
          and hasil4['langkah_berikut'] is not None)

    # --- Aturan lama tidak berubah ---
    t('HARGA_ABSTRAK tetap 6', BA.HARGA_ABSTRAK == 6)
    t('HARGA_BUAT/UPDATE tetap 2',
      BA.HARGA_BUAT == 2 and BA.HARGA_UPDATE == 2)

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    raise SystemExit(main())
