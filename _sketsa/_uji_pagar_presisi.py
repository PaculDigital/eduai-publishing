"""UJI PAGAR PRESISI (Opsi 1, 28Sep26) — 2 ARAH + BUKTIAN BUKAN DUGAAN.

Yang diuji: dasar ukur pagar panjang kini PARAGRAF UTUH, bukan potongan
KUTIP-ASLI. Setiap kasus SEHAT wajib LULUS dan setiap kasus DIRUSAK wajib
GAGAL — termasuk bukti bahwa pagar LAMA menolak kasus sehat itu.
"""
import pathlib
import sys

sys.path.insert(0, '/app')
from app import pipa                       # noqa: E402
from app.pipa import periksa, pisah_paragraf  # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


def paragraf_acak(n_kar, awal, isi=None):
    """Bangun satu paragraf isi sepanjang n_kar.

    `isi` = kalimat pengisi; DIBERI PER BEDA per paragraf supaya dua
    paragraf buatan tidak dianggap KEMBAR oleh pencari kutipan
    (cacat uji 28Sep26: pengisi sama → 'kembar' palsu).
    """
    dasar = isi or ('Penelitian ini menguji pengaruh kualitas layanan terhadap '
                    'kepuasan pelanggan pada industri ritel modern di '
                    'Indonesia, dengan mempertimbangkan berbagai variabel '
                    'yang relevan. ')
    t = ''
    while len(t) < n_kar:
        t += dasar
    return awal + ' ' + t[:n_kar - len(awal) - 1].strip()


KUTIP_SENTENCE = ('Penelitian ini menguji pengaruh kualitas layanan '
                  'terhadap kepuasan pelanggan pada industri ritel modern '
                  'di Indonesia')

print('═' * 74)
print('A. SEHAT — "perdalam" yang dulu SELALU DITOLAK')
print('═' * 74)

#  Kasus nyata C7 28Sep26: kutip 1 kalimat, tulis ulang paragraf utuh.
PAR400 = paragraf_acak(400, KUTIP_SENTENCE + '.')
NAS = ('BAB I PENDAHULUAN\n\nLatar Belakang\n\n' + PAR400 +
       '\n\nRumusan masalah penelitian ini diuraikan pada bagian berikutnya '
       'dengan urutan yang logis.')
par = pisah_paragraf(NAS)
cek('A0 naskah punya paragraf isi 400 kar',
    any(len(p) >= 395 for p in par), f'paragraf={[len(p) for p in par]}')

GANTI_2K2 = paragraf_acak(900, 'Dalam perspektif yang lebih luas,')
jawab = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n\n'
         '[K1-KUTIP-ASLI] ' + KUTIP_SENTENCE +
         '.\n[K1-GANTI-JADI] ' + GANTI_2K2)

#  Bukti pagar LAMA (dasar = kutipan) MENOLAK kasus ini:
rasio_lama = len(GANTI_2K2) / max(1, len(KUTIP_SENTENCE + '.'))
cek('A1 (bukti lama) dasar-kutip memberi rasio melampaui batas 3×',
    rasio_lama > pipa.PANJANG_MAKS_KALI, f'{rasio_lama:.2f}×')

h = periksa(jawab, NAS)
rasio_baru = len(GANTI_2K2) / len(PAR400)
cek('A2 SEHAT: tulis 2,25× paragraf → DULU GAGAL, sekarang LULUS',
    h.ok and len(h.editan) == 1,
    f'ok={h.ok} rasio_paragraf={rasio_baru:.2f}× pesan={h.pesan[:60]!r}')
cek('A3 editan menunjuk paragraf yang benar',
    h.ok and h.editan[0].keadaan in ('cocok', 'toleran'),
    h.editan[0].keadaan if h.editan else '-')

#  SEHAT 2: ganti hampir sama panjang dengan paragraf (revisi biasa)
GANTI_1K = paragraf_acak(430, 'Dalam perspektif yang lebih luas,')
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] ' + KUTIP_SENTENCE +
            '.\n[K1-GANTI-JADI] ' + GANTI_1K, NAS)
cek('A4 SEHAT: ganti 1,07× paragraf → LULUS', h.ok and len(h.editan) == 1,
    f'ok={h.ok}')

#  SEHAT 3: satu komentar → DUA blok, dua paragraf berbeda
PAR_B = paragraf_acak(
    350, 'Rumusan masalah penelitian ini adalah',
    isi=('Seberapa besar pengaruh kualitas layanan terhadap kepuasan '
         'pelanggan, dan apakah efikasi diri memediasi hubungan tersebut. '))
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] ' + KUTIP_SENTENCE +
            '.\n[K1-GANTI-JADI] ' + GANTI_1K + '\n\n'
            '[K2-KUTIP-ASLI] ' + PAR_B[:120] +
            '\n[K2-GANTI-JADI] ' + paragraf_acak(380, 'Rumusan masalahnya'),
            NAS + '\n\n' + PAR_B)          # PAR_B WAJIB ikut di naskah
cek('A5 SEHAT: 2 blok / 2 paragraf → keduanya diterima',
    h.ok and len(h.editan) == 2 and not h.ditolak,
    f'ok={h.ok} editan={len(h.editan)} ditolak={h.ditolak}')

print()
print('═' * 74)
print('B. SEHAT — grafik/tabel (pengecualian yang sudah ACC 25Sep26)')
print('═' * 74)
PAR_GBR = paragraf_acak(
    200, 'Distribusi hasil uji ditampilkan berikut ini',
    isi=('Grafik batang membandingkan nilai mAP50-95 antar seri model yang '
         'diuji pada data validasi dan data uji. '))
NAS_G = NAS + '\n\n' + PAR_GBR
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] ' + PAR_GBR.split('. ')[0] +
            '.\n[K1-GANTI-JADI] ' +
            ('Distribusi hasil uji ditampilkan pada gambar berikut.\n\n'
             '[[GAMBAR-PNG-1]]\n\n'
             'Keterangan: sumbu tegak menunjukkan nilai mAP50-95 (%) '
             'sedangkan sumbu datar menunjukkan seri model yang diuji. '
             'Berdasarkan grafik terlihat bahwa seri model dengan performa '
            'tertinggi memperoleh nilai tertinggi pada kedua metrik. ') +
            paragraf_acak(700, 'Penjelasan lebih rinci'),
            NAS_G, 'BUAT_GRAFIK')
cek('B1 SEHAT: BUAT_GRAFIK 8× + lantai 1.200 kar → LULUS',
    h.ok and len(h.editan) == 1,
    f'ok={h.ok} ditolak={[(d["sebab"], d.get("rasio_paragraf")) for d in h.ditolak]}')

print()
print('═' * 74)
print('C. DIRUSAK — pagar HARUS bergigi')
print('═' * 74)

#  Kasus nyata C7: 7.201 kar menggantikan paragraf ratusan kar.
GANTI_RAKSASA = paragraf_acak(7201, 'Latar belakang penelitian ini')
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] ' + KUTIP_SENTENCE +
            '.\n[K1-GANTI-JADI] ' + GANTI_RAKSASA, NAS)
d = h.ditolak[0] if h.ditolak else {}
cek('C1 DIRUSAK: 7.201 kar vs paragraf 400 kar → DITOLAK',
    (not h.ok) and d.get('sebab') == 'ganti_terlalu_panjang',
    f'ok={h.ok} ditolak={[(x["sebab"]) for x in h.ditolak]}')
cek('C2 angka penyebab DICATAT (rasio terhadap paragraf, bukan kutipan)',
    d.get('panjang_paragraf', 0) >= 395 and d.get('rasio_paragraf', 0) > 15
    and d.get('batas', 0) > 1000,
    f"paragraf={d.get('panjang_paragraf')} rasio={d.get('rasio_paragraf')} "
    f"batas={d.get('batas')} ganti={d.get('panjang_ganti')}")

#  kutipan karangan
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] Kalimat ini tidak ada di naskah mana pun.\n'
            '[K1-GANTI-JADI] ' + GANTI_1K, NAS)
cek('C3 DIRUSAK: kutipan karangan → DITOLAK (jangan menebak)',
    (not h.ok) and h.ditolak and h.ditolak[0]['sebab'] == 'tidak_ketemu',
    h.ditolak[0]['sebab'] if h.ditolak else '-')

#  tanpa blok
h = periksa('[PROFIL] Paradigma=kuantitatif\n\nIni hasil revisi panjang...', NAS)
cek('C4 DIRUSAK: tanpa blok KUTIP/GANTI → DITOLAK', not h.ok,
    h.pesan[:60])

#  pagar bencana (naskah susut) tetap utuh
from app.pipa import cukup_panjang          # noqa: E402
ok, p = cukup_panjang(NAS, 'Hanya kalimat ini yang tersisa.')
cek('C5 DIRUSAK: naskah susut 99% → pagar bencana DITOLAK',
    (not ok) and 'dibatalkan' in p, p[:70])

#  LANTAI 200 kar: paragraf pendek tetap boleh tumbuh sampai 200 kar
PAR_PENDEK = paragraf_acak(
    60, 'Metode penelitian ini menggunakan pendekatan kuantitatif',
    isi=('Kuesioner disebar kepada responden yang dipilih secara '
         'purposive. '))
NAS_P = 'Metode\n\n' + PAR_PENDEK + '\n\nInstrumen penelitian telah diuji '
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] ' + PAR_PENDEK.split('. ')[0] +
            '.\n[K1-GANTI-JADI] ' + paragraf_acak(
                190, 'Metode penelitian ini menggunakan pendekatan kuantitatif',
                isi=('Kuesioner disebar kepada responden yang dipilih secara '
                     'purposive. ')),
            NAS_P)
cek('C6 SEHAT: paragraf 60 kar, tulis 190 kar → lantai 200 kar menolong',
    h.ok and len(h.editan) == 1,
    f'ok={h.ok} ditolak={[(d["sebab"], d.get("rasio_paragraf")) for d in h.ditolak]}')

#  Judul diganti jadi isi → tetap DITOLAK (perilaku pagar LAMA juga begini;
#  dicatat jujur: bukan efek perubahan 28Sep26, dan memang tidak boleh —
#  mengganti paragraf judul dengan tubuh tulisan membuat judul hilang).
NAS_JUDUL = 'BAB I\n\nPendahuluan\n\nLatar Belakang'
h = periksa('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI] Latar Belakang\n'
            '[K1-GANTI-JADI] ' + paragraf_acak(300, 'Latar belakang'), NAS_JUDUL)
cek('C7 DIRUSAK: judul 14 kar diisi tulisan 300 kar → DITOLAK',
    (not h.ok) and h.ditolak and
    h.ditolak[0]['sebab'] == 'ganti_terlalu_panjang',
    f"ok={h.ok} ditolak={[(d['sebab'], d.get('rasio_paragraf')) for d in h.ditolak]}")

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
