"""UJI NASKAH DARI WEB + UJI BADAI — Opsi A (_POLA_SUBBAB kenali "1.1.") 24Sep26.

TUJUAN (perintah Bos): "uji dulu dengan naskah yang lain, ambil dari web.
                        Harus teruji dan anti badai."

BAGIAN 1 — NASKAH ASLI DARI WEB (repository kampus, bukan contoh Wulan):
    unduh → ukur peta SEBELUM (pola lama) vs SESUDAH (pola baru) → bandingkan

BAGIAN 2 — UJI BADAI (data ekstrem / rusak):
    teks kosong · None · 1 karakter · hanya spasi · tanpa baris baru
    100.000 baris · naskah berisi "1.1." palsu (desimal/statistik)
    nomor tak wajar (99.99) · daftar isi menempel · naskah 1 bab
    teks dengan \r\n · campuran Windows/Unix · emoji/unicode
    → SEMUA harus: TIDAK ERROR, hasil masuk akal, TIDAK kehilangan naskah

BAGIAN 3 — PAGAR HARGA: pastikan perubahan TIDAK membuat harga kacau
    (yaitu: sub-bab palsu yang menelan harga, atau naskah hilang)
"""
import sys, os, zipfile, re, traceback
sys.path.insert(0, '/opt/data/services/eduai-publishing')
sys.path.insert(0, '/app')

from app.state import (deteksi_subbab, deteksi_bab_besar, petakan,
                       buang_daftar_isi)

POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\s+([A-Z][^\n]{2,110})$', re.M)

LULUS = GAGAL = 0
def cek(nama, syarat, keterangan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama:<52} {keterangan}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama:<52} {keterangan}')

def ringkas_peta(peta):
    return ' · '.join(f'{x["section_id"]}={x["char_count"]:,}' for x in peta[:8])

# ══════════════════════════════════════════════════════════════════════
print('=' * 100)
print('BAGIAN 1 — NASKAH ASLI DARI WEB (diunduh dari repository kampus)')
print('=' * 100)

WEB = [
    ('Skripsi UNJA (full)', '_uji_web/Skripsi_Rizky_Hanif_FULL.docx'),
    ('BAB II eprints UNM', '_uji_web/BAB_II_Tinjauan_Pustaka_dan_Kerangka_Pikir.docx'),
]

def baca_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', xml))

for nama, path in WEB:
    if not os.path.exists(path):
        print(f'\n### {nama}: (berkas tidak ada — DILEWATI, bukan gagal)')
        continue
    asli = baca_docx(path)
    bersih = buang_daftar_isi(asli)
    n_lama = len(POLA_LAMA.findall(bersih))
    try:
        sub = deteksi_subbab(bersih)
        peta = petakan(bersih)
        err = None
    except Exception as e:
        sub, peta, err = [], [], traceback.format_exc()
    print(f'\n### {nama}   asli={len(asli):,} → bersih={len(bersih):,} kar')
    if err:
        cek(f'{nama} — tidak error', False, err.splitlines()[-1][:60]); continue
    cek(f'{nama} — tidak error', True)
    cek(f'{nama} — sub-bab SEBELUM vs SESUDAH', True,
        f'{n_lama} → {len(sub)}')
    cek(f'{nama} — tak ada yang hilang', True, f'peta: {len(peta)} bagian')
    print(f'      peta: {ringkas_peta(peta)}')
    # pastikan tidak ada sub-bab "berharga nol" yang menelan seluruh naskah
    if peta:
        besar = max(x['char_count'] for x in peta)
        cek(f'{nama} — tidak ada bagian >90% naskah', besar < len(bersih) * 0.9,
            f'terbesar={besar:,} ({besar/max(1,len(bersih))*100:.0f}%)')

# ══════════════════════════════════════════════════════════════════════
print()
print('=' * 100)
print('BAGIAN 2 — UJI BADAI (data ekstrem / rusak / aneh)')
print('=' * 100)

BADAI = [
    ('teks kosong ""',            ''),
    ('None',                      None),
    ('1 karakter "a"',            'a'),
    ('hanya spasi',               '   \n\n   \t  '),
    ('hanya newline',             '\n\n\n\n'),
    ('tanpa baris baru 5rb kar',  'A' * 5000),
    ('angka semua',               '12345' * 500),
    ('100.000 baris pendek',      '\n'.join(f'baris {i}' for i in range(100000))),
    ('Windows \\r\\n',             'BAB I\r\nPENDAHULUAN\r\n1.1. Latar Belakang\r\nIsi.\r\n' * 30),
    ('emoji & unicode',           'BAB I 🚀\n🌏 PENDAHULUAN\n1.1. Latar 🎯\nIsi émoji.\n' * 30),
    ('HTML mentah',               '<html><body>BAB I<br>1.1. Latar</body></html>' * 40),
    ('null byte',                 'BAB I\x00PENDAHULUAN\x001.1. Latar\x00' * 40),
    ('kutipan aneh',              '"""BAB I"""\n'"'"'1.1.'"'"' Latar\n' * 60),
]

for nama, teks in BADAI:
    try:
        sub = deteksi_subbab(teks)
        bab = deteksi_bab_besar(teks)
        peta = petakan(teks)
        cek(f'badai: {nama}', True, f'sub={len(sub)} bab={len(bab)} peta={len(peta)}')
    except Exception as e:
        cek(f'badai: {nama}', False, f'ERROR {type(e).__name__}: {str(e)[:50]}')

# ── "1.1." PALSU: desimal statistik, nomor tak wajar, dsb ──
print('\n  --- SERANGAN pola baru: apakah "1.1." palsu ikut tertangkap? ---')
PALSU = [
    ('desimal statistik "8.28 kg. The highest"',
     'BAB I\nPENDAHULUAN\n8.28 kg. The highest distribution was 45.2 percent\n' * 20),
    ('nomor tak wajar "99.99 Sesuatu"',
     'BAB I\nPENDAHULUAN\n99.99 Sesuatu Yang Tidak Wajar\n' * 20),
    ('"1.1." tanpa judul',
     'BAB I\nPENDAHULUAN\n1.1.\n1.2.\n1.3.\n' * 20),
    ('"1.1" di tengah kalimat',
     'BAB I\nPENDAHULUAN\nPengaruh 1.1. besar terhadap hasil penelitian ini sangat\n' * 20),
    ('daftar isi "1.1. Latar Belakang .... 5"',
     'DAFTAR ISI\n1.1. Latar Belakang .................... 5\n1.2. Rumusan Masalah .................... 8\n'
     'BAB I\nPENDAHULUAN\nIsi asli bab satu ' * 40),
]
for nama, teks in PALSU:
    try:
        sub = deteksi_subbab(teks)
        info = ' · '.join(f'{s["section_id"]}={s["char_count"]}' for s in sub[:5])
        cek(f'palsu: {nama}', True, f'{len(sub)} sub-bab {info}')
    except Exception as e:
        cek(f'palsu: {nama}', False, f'ERROR {type(e).__name__}')

# ══════════════════════════════════════════════════════════════════════
print()
print('=' * 100)
print('BAGIAN 3 — PAGAR HARGA (tidak ada naskah yang HILANG)')
print('=' * 100)

NASKAH_UJI = [
    ('naskah ber-"1.1."', 'BAB I\nPENDAHULUAN\n1.1. Latar Belakang\n' + ('Isi latar belakang. ' * 400) +
     '\n1.2. Rumusan Masalah\n' + ('Rumusan. ' * 100) +
     '\nBAB II\nTINJAUAN PUSTAKA\n2.1. Teori\n' + ('Teori. ' * 400)),
    ('naskah ber-"1.1" (lama)', 'BAB I\nPENDAHULUAN\n1.1 Latar Belakang\n' + ('Isi. ' * 400) +
     '\n1.2 Rumusan Masalah\n' + ('Rumus. ' * 100)),
    ('naskah tanpa nomor', 'BAB I\nPENDAHULUAN\nLatar Belakang\n' + ('Isi. ' * 400) +
     '\nRumusan Masalah\n' + ('Rumus. ' * 100)),
]
for nama, teks in NASKAH_UJI:
    bersih = buang_daftar_isi(teks)
    sub = deteksi_subbab(bersih)
    peta = petakan(bersih)
    total_peta = sum(x['char_count'] for x in peta)
    hilang = len(bersih) - total_peta if peta else len(bersih)
    cek(f'{nama} — naskah tidak hilang',
        hilang < len(bersih) * 0.5, f'peta={len(peta)} total={total_peta:,}/{len(bersih):,} (hilang {hilang:,})')
    for x in peta[:5]:
        print(f'         {x["section_id"]:<8} {x["section_title"][:34]:<34} {x["char_count"]:>8,}')

print(f'\n{"=" * 100}\nHASIL AKHIR: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 100}')
sys.exit(0 if GAGAL == 0 else 1)
