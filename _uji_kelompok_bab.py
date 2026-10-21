"""UJI TAHAP 2.5 — KELOMPOK CATATAN PER BAB (ACC Bos 24Sep26).

Yang diuji BUKAN "tampilan bagus", tapi ATURAN yang Bos putuskan:
  1. Catatan dikelompokkan PER BAB.
  2. Bab TERBUKA otomatis = paling banyak catatan BARU (hanya SATU).
  3. Bab yang tidak punya catatan TIDAK ditampilkan (jangan 5 bab kosong).
  4. Dokumen TANPA bab → kelompok PER HARI (Hari ini / Kemarin / tanggal).
  5. Catatan tanpa bab → kelompok terakhir "Belum disebut bab-nya".
  6. EJAAN BEDA menyatu: "BAB III", "BAB 3", "bab iii" = SATU kelompok.
  7. Kotak "Bagian mana?" = DROPDOWN dari bab naskah (bukan ketik bebas).
  8. Naskah tanpa bab → kotak ketik tetap ada (JANGAN jalan buntu).
  9. Semua catatan tetap muncul — TIDAK ADA yang hilang dari layar.

Uji HALAMAN (lewat HTTP) + uji mesin (modul langsung).
"""
import sys
from datetime import date, datetime
from types import SimpleNamespace as SN

sys.path.insert(0, '/app')

import urllib.request

from app import kelompok_catatan as KC
from app import pembimbing as P
from app.models import SessionLocal, init_db

LULUS = GAGAL = 0


def cek(nama, syarat, sebab=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ GAGAL: {nama}  ({sebab})')


def catatan(judul, warna='kuning', dibuat=None, isi='contoh'):
    return SN(section_judul=judul, warna=warna, isi=isi, dibuat=dibuat,
              section_id=judul, lampiran='', tautan='', teks_asli='', id=1)


def simpul(kepala, terbaru=None, ronde=1):
    terbaru = terbaru or kepala
    return {'kepala': kepala, 'terbaru': terbaru, 'anak': [],
            'jumlah_ronde': ronde}


def ambil(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                     # noqa: BLE001
        return 0, str(e)


print('═' * 68)
print('UJI TAHAP 2.5 — KELOMPOK CATATAN PER BAB')
print('═' * 68)

# ══ A. MESIN: pengelompokan per bab ═════════════════════════════════════
print('\n── A. Pengelompokan per BAB ──')
HARI = date(2026, 9, 24)
R = [
    simpul(catatan('BAB III — METODE')),          # bab 3
    simpul(catatan('BAB I — PENDAHULUAN')),
    simpul(catatan('BAB I — PENDAHULUAN')),
    simpul(catatan('BAB 3')),                     # ejaan beda → harus SATU
    simpul(catatan('bab iii')),                   # ejaan beda → harus SATU
    simpul(catatan('BAB IV — HASIL', 'hijau')),
    simpul(catatan('')),                          # tanpa bab
]
g = KC.kelompokkan(R, ada_bab=True, hari_ini=HARI)
kunci = [x['kunci'] for x in g]

cek('A1 ada kelompok BAB 1/3/4 + tanpa bab', 
    'BAB 1' in kunci and 'BAB 3' in kunci and 'BAB 4' in kunci
    and KC.KUNCI_TANPA_BAB in kunci, f'dapat={kunci}')
cek('A2 ejaan "BAB III"/"BAB 3"/"bab iii" MENYATU',
    len([k for k in kunci if k == 'BAB 3']) == 1, f'{kunci}')
cek('A3 kelompok BAB 3 berisi 3 catatan',
    'BAB 3' in kunci and [x for x in g if x['kunci'] == 'BAB 3'][0]['jumlah'] == 3,
    f'{kunci}')
#  ⚠️ Uji ini HARUS tahan kalau penyatuan ejaan dirusak: dulu langsung
#  meledak ValueError ('BAB 1' is not in list) — uji yang MELEDAK bukan uji
#  yang GAGAL rapi. Sekarang diperiksa kehadirannya lebih dulu.
cek('A4 urutan bab menaik (1 → 3 → 4)',
    all(k in kunci for k in ('BAB 1', 'BAB 3', 'BAB 4'))
    and kunci.index('BAB 1') < kunci.index('BAB 3') < kunci.index('BAB 4'),
    f'{kunci}')
cek('A5 tanpa bab di PALING AKHIR',
    kunci[-1] == KC.KUNCI_TANPA_BAB, f'{kunci}')
cek('A6 hanya SATU kelompok terbuka',
    sum(1 for x in g if x['buka']) == 1,
    f"buka={[x['kunci'] for x in g if x['buka']]}")
cek('A7 yang terbuka = paling banyak catatan BARU (BAB 3 = 3)',
    [x['kunci'] for x in g if x['buka']] == ['BAB 3'],
    f"buka={[x['kunci'] for x in g if x['buka']]}")
cek('A8 label tanpa-bab berbahasa manusia (bukan kunci internal)',
    [x for x in g if x['kunci'] == KC.KUNCI_TANPA_BAB][0]['label']
    == 'Belum disebut bab-nya', '')

#  ⚠️ KASUS PALING MERUSAK: kalau tidak ada yang baru, JANGAN buka apapun.
print('\n── A9. Tidak ada catatan BARU → tidak ada yang dibuka ──')
gs = KC.kelompokkan([simpul(catatan('BAB I — X', 'hijau')),
                     simpul(catatan('BAB II — Y', 'hijau'))],
                    ada_bab=True, hari_ini=HARI)
cek('A9 tidak ada kelompok terbuka', sum(1 for x in gs if x['buka']) == 0,
    f"buka={[x['kunci'] for x in gs if x['buka']]}")

# ══ B. MESIN: dokumen TANPA bab → per hari ══════════════════════════════
print('\n── B. Dokumen TANPA bab → kelompok PER HARI ──')
U = [
    simpul(catatan('', 'kuning', datetime(2026, 9, 24, 10, 0))),
    simpul(catatan('', 'kuning', datetime(2026, 9, 24, 8, 0))),
    simpul(catatan('', 'hijau', datetime(2026, 9, 23, 9, 0))),
    simpul(catatan('', 'kuning', datetime(2026, 9, 18, 9, 0))),
    simpul(catatan('', 'kuning', datetime(2026, 8, 15, 9, 0))),
]
gu = KC.kelompokkan(U, ada_bab=False, hari_ini=HARI)
label = [x['label'] for x in gu]
cek('B1 kelompok per hari terbentuk', len(gu) == 4, f'{label}')
cek('B2 hari ini terkumpul 2 catatan',
    [x for x in gu if x['label'] == 'Hari ini'][0]['jumlah'] == 2, f'{label}')
cek('B3 "Kemarin" terbentuk', 'Kemarin' in label, f'{label}')
cek('B4 tanggal lama pakai tanggal nyata (15 Agu 2026)',
    '15 Agu 2026' in label, f'{label}')
cek('B5 terbaru di ATAS (Hari ini paling depan)', label[0] == 'Hari ini',
    f'{label}')

# ══ C. MESIN: kasus buruk ═══════════════════════════════════════════════
print('\n── C. Kasus buruk (yang paling merusak) ──')
cek('C1 rantai KOSONG → tidak error', KC.kelompokkan([], True, HARI) == [], '')
cek('C2 tanggal RUSAK → jujur "Tanggal tidak jelas"',
    KC._label_umum('bukan-tanggal', HARI) == 'Tanggal tidak jelas', '')
cek('C3 tanggal KOSONG → tidak diklaim "Hari ini"',
    KC._label_umum('', HARI) == 'Tanggal tidak jelas', '')
cek('C4 tanggal MASA DEPAN → tidak diklaim "Hari ini"',
    KC._label_umum('2030-01-01', HARI) == '1 Jan 2030', '')
cek('C5 nomor_bab baca angka & romawi',
    KC.nomor_bab('BAB 3') == 3 and KC.nomor_bab('bab iii') == 3
    and KC.nomor_bab('BAB IV') == 4, '')
cek('C6 nomor_bab TOLAK yang bukan bab',
    KC.nomor_bab('Metode Penelitian') is None
    and KC.nomor_bab('') is None, '')

# ══ D. MESIN: deteksi bab naskah (untuk dropdown) ══════════════════════
print('\n── D. Daftar bab naskah (isi dropdown) ──')
TEKS = ('BAB I\nPENDAHULUAN\nisi satu\nBAB II\nTINJAUAN PUSTAKA\nisi dua\n'
        'BAB III\nMETODE PENELITIAN\nisi tiga\n')
d = KC.daftar_bab_naskah(TEKS)
cek('D1 3 bab terdeteksi', len(d) == 3, f'{len(d)}')
cek('D2 label berisi nomor + judul',
    d and 'BAB I' in d[0]['label'] and 'PENDAHULUAN' in d[0]['label'],
    f'{d[0] if d else None}')
cek('D3 naskah TANPA bab (perjanjian) → daftar KOSONG',
    KC.daftar_bab_naskah('PERJANJIAN KERJA SAMA\nPasal 1\nPihak pertama...')
    == [], '')
cek('D4 naskah kosong → tidak error', KC.daftar_bab_naskah('') == [], '')

# ══ E. HALAMAN: HTTP (yang benar-benar dilihat pembimbing) ══════════════
print('\n── E. Halaman tinjau (HTTP) ──')
db = SessionLocal()
try:
    from app.models import Pembimbingan
    b = (db.query(Pembimbingan)
         .filter(Pembimbingan.nama == 'Prof. Uji Bab')
         .order_by(Pembimbingan.id.desc()).first())
    TOK = b.token if hasattr(b, 'token') else None
    #  token TIDAK disimpan mentah — ambil dari berkas uji
    import json
    try:
        TOK = json.load(open('/app/_tok25.json'))['token']
    except Exception:                                          # noqa: BLE001
        TOK = ''
finally:
    db.close()

if TOK:
    status, html = ambil(f'http://127.0.0.1:8000/tinjau/{TOK}')
    cek('E1 halaman terbuka', status == 200, f'HTTP {status}')
    cek('E2 ada kepala bab (kelompok)', 'kepala-bab' in html,
        f'kepala-bab={html.count("kepala-bab")}')
    cek('E3 ada 4 kelompok bab', html.count('class="kepala-bab') >= 4,
        f'={html.count(chr(34)+"kepala-bab")}')
    cek('E4 ada kelompok "Belum disebut bab-nya"',
        'Belum disebut bab-nya' in html, '')
    cek('E5 "BAB 3" menyatu jadi SATU kepala (bukan 3)',
        html.count('BAB 3 —') <= 2, f'={html.count("BAB 3 —")}')
    cek('E6 ada label "baru"', 'baru</span>' in html or 'baru</' in html, '')
    cek('E7 kotak "Bagian mana?" jadi DROPDOWN (<select>)',
        '<select name="section_judul"' in html, '')
    #  ⚠️ DIPERBAIKI 24Sep26 — asersi ini DULU SALAH (bukan bug aplikasi).
    #  Versi lama menuntut tulisan persis 'BAB III — METODE PENELITIAN'.
    #  Padahal naskah uji yang dipakai = TESIS S2 yang memang hanya punya
    #  2 bab (BAB I & BAB II). Jadi dropdown-nya BENAR isi 2 bab, tapi
    #  asersi menuntut bab yang tidak ada → GAGAL PALSU.
    #  Sekarang: diperiksa BENTUKNYA (ada minimal 2 pilihan berlabel "BAB "
    #  dengan nomor + judul), bukan teks mati. Lebih tahan perubahan.
    import re as _re
    pilihan_bab = _re.findall(r'<option value="(BAB [^"]{3,})"', html)
    cek('E8 dropdown berisi pilihan BAB (nomor + judul)',
        len(pilihan_bab) >= 2
        and all('—' in p for p in pilihan_bab),
        f'ketemu {len(pilihan_bab)}: {pilihan_bab[:3]}')
    cek('E9 kotak ketik bebas SUDAH TIDAK ADA',
        'placeholder="Bagian mana? (mis. BAB I' not in html, '')
    cek('E10 catatan tanpa bab TETAP tampil (tidak hilang)',
        'Mohon perbaiki penulisan daftar pustaka' in html, '')
    cek('E11 JS bukaBab ada', 'function bukaBab' in html, '')
    cek('E12 hanya SATU kelompok bertanda buka',
        html.count('kepala-bab buka') == 1, f'={html.count("kepala-bab buka")}')
    cek('E13 kelompok TERTUTUP pakai hidden (isinya tidak dirender tampil)',
        'class="isi-bab" hidden' in html, '')
else:
    print('  ⚠️  TOKEN tidak tersedia — uji halaman DILEWATI')

print()
print('═' * 68)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 68)
sys.exit(1 if GAGAL else 0)
