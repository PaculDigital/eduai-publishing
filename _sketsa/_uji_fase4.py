"""UJI FASE 4 — parser.py (section + 6 intent + pengali)."""
import sys
sys.path.insert(0, '/app')
from app import parser

KASUS = [
    # (pesan user, section diharap, intent diharap, pengali diharap)
    # ── yang paling sering dipakai mahasiswa ──
    ('tolong perbaiki latar belakang saya',                  '1.1', 'REVISI', 1),
    ('latar belakang kurang dalam, perkaya',                 '1.1', 'PERKAYA_NARASI', 1),
    ('tambahkan data di rumusan masalah',                    '1.2', 'TAMBAH_DATA', 1),
    ('pembahasan saya kurang jelas, tolong perjelas',        '4.5', 'PERKAYA_NARASI', 1),
    ('revisi bab 3 dong',                                    '3.1', 'REVISI', 1),
    ('1.1 tolong diperpanjang',                              '1.1', 'PERKAYA_NARASI', 1),
    ('kesimpulan saya terlalu pendek',                       '5.1', 'PERKAYA_NARASI', 1),
    ('hipotesis saya salah, betulin',                        '2.4', 'REVISI', 1),
    ('koreksi uji hipotesis saya',                           '4.4', 'REVISI', 1),
    ('manfaat penelitian perlu ditambah',                    '1.4', 'TAMBAH_DATA', 1),
    # ── pengali 3: ganti metode ──
    ('ganti metode penelitian saya jadi kualitatif',          '3.1', 'GANTI_METODE', 3),
    ('ubah metode analisis jadi SEM',                         '3.1', 'GANTI_METODE', 3),
    # ── pengali 4: ubah alur ──
    ('ubah alur berpikir jadi induktif',                      None,  None, 4),
    ('ganti paradigma penelitian jadi kualitatif',            None,  None, 4),
    # ── pengali 5: ubah alur + semua bab ──
    ('ubah alur seluruh dokumen jadi induktif',               None,  None, 5),
    ('rombak alur dari bab 1 sampai bab 5',                   None,  None, 5),
    # ── pertanyaan (tidak mengubah dokumen) ──
    ('apa itu validitas?',                                    None,  'PERTANYAAN', 1),
    ('jelasin kenapa R2 saya rendah',                         None,  'PERTANYAAN', 1),
    # ── hapus ──
    ('hapus bab 5.3 keterbatasan',                           '5.3', 'HAPUS', 1),
    # ── tak jelas (harus minta AI) ──
    ('hmm tolong bantu ya',                                   None,  None, 1),
]

print('=' * 90)
print('UJI FASE 4 — parser.py : section + intent + pengali Token Revisi')
print('=' * 90)
print(f'{"PESAN USER":44s} {"SECTION":9s} {"INTENT":16s} {"X":2s} {"CONF":5s} {"AI?"}')
print('-' * 90)

lulus = gagal = 0
for pesan, sec_h, int_h, x_h in KASUS:
    h = parser.urai(pesan)
    ok_s = (sec_h is None) or (h['section'] == sec_h)
    ok_i = (int_h is None) or (h['intent'] == int_h)
    ok_x = (h['pengali'] == x_h)
    ok = ok_s and ok_i and ok_x
    lulus += ok
    gagal += (not ok)
    tanda = 'OK ' if ok else 'XX '
    print(f'{tanda}{pesan[:41]:41s} {h["section"]:9s} {h["intent"]:16s} '
          f'{h["pengali"]:>2d} {h["confidence"]:>5.2f} {"ya" if h["butuh_ai"] else "-"}')
    if not ok:
        print(f'    HARAP: section={sec_h} intent={int_h} pengali={x_h}')

print('-' * 90)
print(f'  HASIL: {lulus} LULUS, {gagal} GAGAL dari {len(KASUS)}')

print()
print('=' * 90)
print('UJI label_pengguna (DILARANG sebut "kuota"/angka token mentah)')
print('=' * 90)
for intent in ['PERKAYA_NARASI', 'GANTI_METODE', 'UBAH_ALUR', 'UBAH_ALUR_SEMUA', 'REVISI']:
    x = parser.pilih_pengali(intent, 'ubah alur semua bab' if intent.startswith('UBAH') else '')
    print(f'  {intent:18s} x{x}  -> "{parser.label_pengguna(intent, x)}"')
terlarang = ['kuota', 'token', 'rupiah', 'rp ']
for intent in parser.PENGALI_INTENT:
    teks = parser.label_pengguna(intent, parser.PENGALI_INTENT[intent]).lower()
    for t in terlarang:
        assert t not in teks, f'KATA TERLARANG "{t}" di label {intent}!'
print('  ✅ tidak ada kata terlarang (kuota/token/rupiah)')

print()
print('=' * 90)
print('UJI tahan data aneh')
print('=' * 90)
for nama, p in [('None', None), ('kosong', ''), ('spasi', '   '), ('emoji', '👍'),
                ('panjang 5000', 'revisi latar belakang '*250)]:
    try:
        h = parser.urai(p)
        print(f'  {nama:12s} -> {h["section"]}/{h["intent"]} x{h["pengali"]} conf={h["confidence"]} ai={h["butuh_ai"]}')
    except Exception as e:
        print(f'  {nama:12s} -> GAGAL {type(e).__name__}: {e}')

print()
print(f'  katalog section: {len(parser.daftar_section())} item')
print(f'  kategori: {list(parser.SECTIONS_CATALOG.keys())}')
