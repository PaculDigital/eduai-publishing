"""UJI LENGKAP OPSI A + BUG ke-18 — 24Sep26 (perintah Bos: "uji sampai fondasi kuat").

DIJALANKAN DI DALAM CONTAINER, memakai app.state ASLI.
Mencakup:
  BAGIAN 1 — 5 NASKAH CONTOH (berkas .docx)
  BAGIAN 2 — 5 NASKAH WEB (dari repository kampus, hasil konversi PDF/DOCX)
  BAGIAN 3 — UJI BADAI (data ekstrem)
  BAGIAN 4 — PAGAR HARGA (naskah tidak boleh hilang)
"""
import sys, os, re, glob, zipfile, traceback, json
sys.path.insert(0, '/app')
from app.state import (deteksi_subbab, deteksi_bab_besar, petakan,
                       buang_daftar_isi, awal_isi_naskah)

POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\s+([A-Z][^\n]{2,110})$', re.M)
LULUS = GAGAL = 0
def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat: LULUS += 1; print(f'  ✅ {nama:<52} {ket}')
    else:      GAGAL += 1; print(f'  ❌ {nama:<52} {ket}')

def baca_docx(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml)))

def proses(nama, teks):
    """Ukur satu naskah + asersi dasar."""
    try:
        bersih = buang_daftar_isi(teks)
        sub = deteksi_subbab(bersih)
        peta = petakan(bersih)
        err = None
    except Exception:
        return None, None, traceback.format_exc()
    return {'nama': nama, 'asli': len(teks), 'bersih': len(bersih),
            'awal': awal_isi_naskah(teks), 'lama': len(POLA_LAMA.findall(bersih)),
            'sub': len(sub), 'peta': peta}, err, None

# ═══════════════════════════════════════════════════════════════════════
print('=' * 104)
print('BAGIAN 1+2 — NASKAH CONTOH & NASKAH WEB  (dijalankan di container, app.state ASLI)')
print('=' * 104)
print(f'{"naskah":<34}{"asli":>9}{"bersih":>9}{"awal%":>7}{"lama":>6}{"baru":>6}{"peta":>6}')
print('-' * 104)

SEMUA = []
for p in sorted(glob.glob('/app/_uji_webtxt/*.txt')):
    SEMUA.append(('WEB ' + os.path.basename(p).replace('.txt',''), open(p).read()))
for p in sorted(glob.glob('/app/_contoh-dokumen/**/*.docx', recursive=True)):
    try: SEMUA.append(('CONTOH ' + os.path.basename(p)[:24], baca_docx(p)))
    except Exception as e: print(f'  (gagal baca {p}: {str(e)[:40]})')

HASIL = []
for nama, teks in SEMUA:
    h, err, _ = proses(nama, teks)
    if err:
        cek(f'{nama} — tidak error', False, err.splitlines()[-1][:50]); continue
    HASIL.append(h)
    print(f'{nama[:33]:<34}{h["asli"]:>9,}{h["bersih"]:>9,}'
          f'{h["awal"]/max(1,h["asli"])*100:>6.0f}%{h["lama"]:>6}{h["sub"]:>6}{len(h["peta"]):>6}')

print('-' * 104)
print('\nASESORI DASAR (semua naskah):')
for h in HASIL:
    cek(f'{h["nama"][:32]} — tidak error', True)
    cek(f'{h["nama"][:32]} — naskah tidak hilang', h['bersih'] > h['asli'] * 0.2,
        f'{h["bersih"]:,}/{h["asli"]:,}')
    if h['peta']:
        tot = sum(len(x['isi_teks']) for x in h['peta'])
        cek(f'{h["nama"][:32]} — cakupan peta ≥90%', tot >= h['bersih'] * 0.9,
            f'{tot/h["bersih"]*100:.0f}%')
        besar = max(x['char_count'] for x in h['peta'])
        cek(f'{h["nama"][:32]} — tak ada bagian >80%', besar < h['bersih'] * 0.8,
            f'terbesar {besar/h["bersih"]*100:.0f}%')

# ═══════════════════════════════════════════════════════════════════════
print()
print('=' * 104)
print('BAGIAN 3 — UJI BADAI (data ekstrem)')
print('=' * 104)
BADAI = [
    ('kosong ""', ''), ('None', None), ('1 karakter', 'a'),
    ('hanya spasi', '   \n\n  \t '), ('hanya newline', '\n\n\n'),
    ('5rb kar tanpa newline', 'A' * 5000), ('angka semua', '12345' * 500),
    ('100rb baris', '\n'.join(f'baris {i}' for i in range(100000))),
    ('Windows \\r\\n', 'BAB I\r\nPENDAHULUAN\r\n1.1. Latar\r\nIsi.\r\n' * 30),
    ('emoji unicode', 'BAB I 🚀\n🌏 PENDAHULUAN\n1.1. Latar 🎯\nIsi.\n' * 30),
    ('HTML mentah', '<html><body>BAB I<br>1.1. Latar</body></html>' * 40),
    ('null byte', 'BAB I\x00PENDAHULUAN\x001.1. Latar\x00' * 40),
    ('kutipan aneh', '"""BAB I"""\n\'1.1.\' Latar\n' * 60),
    ('BAB I berulang 10rb', 'BAB I\nPENDAHULUAN\n1.1 Latar\n' * 10000),
]
for nama, teks in BADAI:
    try:
        s = deteksi_subbab(teks); b = deteksi_bab_besar(teks); p = petakan(teks)
        cek(f'badai: {nama}', True, f'sub={len(s)} bab={len(b)} peta={len(p)}')
    except Exception as e:
        cek(f'badai: {nama}', False, f'{type(e).__name__}: {str(e)[:40]}')

print('\n  --- serangan "1.1." PALSU ---')
PALSU = [
    ('desimal statistik 8.28 kg', 'BAB I\nPENDAHULUAN\n8.28 kg. The highest was 45.2 percent\n' * 20),
    ('nomor tak wajar 99.99', 'BAB I\nPENDAHULUAN\n99.99 Sesuatu Yang Tidak Wajar\n' * 20),
    ('"1.1." tanpa judul', 'BAB I\nPENDAHULUAN\n1.1.\n1.2.\n1.3.\n' * 20),
    ('"1.1" di tengah kalimat', 'BAB I\nPENDAHULUAN\nPengaruh 1.1. besar terhadap hasil sangat\n' * 20),
    ('daftar isi "1.1. Latar .... 5"', 'DAFTAR ISI\n1.1. Latar Belakang ....... 5\n1.2. Rumusan ....... 8\nBAB I\nPENDAHULUAN\nIsi asli ' * 40),
]
for nama, teks in PALSU:
    try:
        s = deteksi_subbab(teks)
        cek(f'palsu: {nama}', True, f'{len(s)} sub-bab')
    except Exception as e:
        cek(f'palsu: {nama}', False, str(e)[:40])

# ═══════════════════════════════════════════════════════════════════════
print()
print('=' * 104)
print('BAGIAN 4 — PAGAR HARGA (naskah tidak boleh hilang)')
print('=' * 104)
PAGAR = [
    ('"1.1." bergaya baru', 'BAB I\nPENDAHULUAN\n1.1. Latar Belakang\n' + 'Isi. ' * 400 +
     '\n1.2. Rumusan\n' + 'Rumus. ' * 100 + '\nBAB II\nTINJAUAN\n2.1. Teori\n' + 'Teori. ' * 400),
    ('"1.1" bergaya lama', 'BAB I\nPENDAHULUAN\n1.1 Latar\n' + 'Isi. ' * 400 + '\n1.2 Rumusan\n' + 'R. ' * 100),
    ('tanpa nomor', 'BAB I\nPENDAHULUAN\nLatar Belakang\n' + 'Isi. ' * 400),
    ('daftar isi + isi (UIR-like)',
     'DAFTAR ISI\nBAB I :PENDAHULUAN\n1.1 Latar Belakang ......... 1\nBAB II : TELAAH ...\n2.1 Teori ......... 5\n'
     + 'BAB I\nPENDAHULUAN\n1.1 Latar Belakang\n' + 'Isi nyata. ' * 300 + '\n1.2 Rumusan\n' + 'R. ' * 100),
]
for nama, teks in PAGAR:
    bersih = buang_daftar_isi(teks); peta = petakan(bersih)
    tot = sum(len(x['isi_teks']) for x in peta)
    cek(f'{nama} — tidak hilang', len(bersih) > len(teks) * 0.3,
        f'{len(bersih):,}/{len(teks):,}')
    if 'daftar isi' in nama:
        cek(f'{nama} — daftar isi DIBUANG', 'DAFTAR ISI' not in bersih[:60], f'awal_isi={awal_isi_naskah(teks)}')

print(f'\n{"=" * 104}\nHASIL: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 104}')
sys.exit(0 if GAGAL == 0 else 1)
