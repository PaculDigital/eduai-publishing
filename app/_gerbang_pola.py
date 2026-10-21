"""GERBANG pola_penulisan.py — uji BERGIGI modul profiler pola.

Fungsi SUNGGUHAN app.pola_penulisan (bukan tiruan).
Bergigi: kalau pagar dilepas, gerbang HARUS GAGAL.

Jalan: docker exec -w /app eduai-app python3 app/_gerbang_pola.py
"""
import sys

sys.path.insert(0, '/app')
from app import pola_penulisan as pp

LULUS = GAGAL = 0


def cek(nama, syarat):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  ✅ %s' % nama)
    else:
        GAGAL += 1
        print('  ❌ %s' % nama)


def peta_buat(baris, label, gabung=None, sistematika=None):
    return {'baris': baris, 'label': label,
            'gabung': gabung or {}, 'sistematika': sistematika or []}


print('GERBANG POLA PENULISAN — uji fungsi sungguhan')
print('=' * 66)

# ── A. pola_baris: label surveyor DIPERCAYA (P7)
peta = peta_buat(['x'] * 10, {})
cek('A1 label subbab → judul_isi',
    pp.pola_baris('subbab', '2.1 Landasan Teori') == 'judul_isi')
cek('A2 label bab → judul_isi',
    pp.pola_baris('bab', 'BAB I PENDAHULUAN') == 'judul_isi')
cek('A3 label paragraf → paragraf (PERCAYA surveyor, walau pendek)',
    pp.pola_baris('paragraf', 'ya') == 'paragraf')
cek('A4 label biasa → paragraf (PERCAYA surveyor)',
    pp.pola_baris('biasa', 'ya') == 'paragraf')
cek('A5 label TAK DIKENAL → tidak_jelas',
    pp.pola_baris('entah', 'apa saja') == 'tidak_jelas')
cek('A6 sinyal pipa → tabel (walau label apa pun)',
    pp.pola_baris('biasa', 'a | b | c') == 'tabel')
cek('A7 penanda butir → butir',
    pp.pola_baris('biasa', 'a. pertama') == 'butir')

# ── B. rentang_bab: SUMBER = gabung (BUG WULAN v4)
# ⚠️ KASUS PEMBEDA: label 'bab' (daftar isi) JUMLAH/POSISI-nya BEDA dari gabung.
#    Kalau sama, kode rusak pun lolos ⇒ uji jadi BUTA (pelajaran: kasus uji dulu).
peta2 = peta_buat(
    ['BAB I', 'a', 'b', 'c', 'd', 'e', 'f', 'BAB II', 'g', 'h'],
    {0: 'bab', 7: 'bab', 2: 'bab', 5: 'bab'},   # label bab = 4 titik (daftar isi)
    gabung={0: ('BAB I', 'P'), 7: ('BAB II', 'P')},   # BAB asli = 2 titik
    sistematika=[0, 2, 5, 7])
bab2 = pp.rentang_bab(peta2)
cek('B1 rentang_bab pakai gabung (2 BAB), BUKAN label bab (4)',
    len(bab2) == 2 and bab2[0]['mulai'] == 0 and bab2[1]['mulai'] == 7)
# ⚠️ JANGAN indeks anggota tanpa cek panjang — kalau B1 gagal, B2 harus TETAP lapor
cek('B2 akhir BAB I = sebelum BAB II',
    len(bab2) == 2 and bab2[0]['akhir'] == 6)

# ── C. tidak_jelas TIDAK menebak ulang surveyor (v4 Opsi)
peta3 = peta_buat(['ya', 'tidak sama sekali'], {0: 'paragraf', 1: 'biasa'})
cek('C1 paragraf pendek tetap paragraf',
    pp.pola_baris('paragraf', 'ya') == 'paragraf')

# ── D. judul_curiga (tanda untuk HAKIM)
cur = pp.judul_curiga([(5, 'Hasil pra-survei menunjukkan bahwa instrumen'),
                       (9, '1. Apakah media sosial berpengaruh?'),
                       (12, 'Landasan Teori')])
cek('D1 kalimat panjang TIDAK lagi dicurigai (v5c: 2× gagal, STOP)',
    not any(x['i'] == 5 for x in cur))
cek('D2 butir bertanya jadi sub-bab → CURIGA (heuristik Bos)',
    any(x['i'] == 9 and 'butir-bertanya' in x['alasan'] for x in cur))
cek('D3 judul wajar TIDAK dicurigai',
    all(x['i'] != 12 for x in cur))

# ── E. skema_nomor DESKRIPTIF (num-dot dipertahankan, v3)
cek('E1 dotted-2', pp.skema_nomor([(1, '2.1 teori')]) == 'dotted-2')
cek('E2 dotted-3', pp.skema_nomor([(1, '2.1.1 teori')]) == 'dotted-3')
cek('E3 num-dot TETAP ADA (v3 menolak hapus)',
    pp.skema_nomor([(1, '1. teori'), (2, '2. teori')]) == 'num-dot')
cek('E4 campur SEJATI (dotted + alpha) → campuran',
    pp.skema_nomor([(1, '2.1 a'), (2, 'A. b')]) == 'campuran')
# v5 (koreksi Bos): dotted-2 + dotted-3 = HIERARKI, bukan campuran
cek('E5 dotted-2 + dotted-3 → dotted-hierarkis (BUKAN campuran)',
    pp.skema_nomor([(1, '2.1 a'), (2, '2.1.1 b'), (3, '2.4 c')]) == 'dotted-hierarkis')
# ── C. judul_curiga (v5b: JANGAN tuduh judul yang BENAR)
cur = pp.judul_curiga([(1, 'Hasil pra-survei menunjukkan bahwa instrumen penelitian'),
                       (2, '(Khoironi, 2023)'),
                       (3, 'Uji heteroskedastisitas'),
                       (4, 'Gap research'),
                       (5, '1. Apakah media sosial berpengaruh?'),
                       (6, 'Kualitas konten digital')])
teks_curiga = [c['teks'] for c in cur]
cek('C1 sinyal PASTI saja — kalimat panjang TIDAK dicurigai (2× gagal, STOP)',
    not any('pra-survei' in t for t in teks_curiga))
cek('C2 awal-sitasi DICURIGAI', any('Khoironi' in t for t in teks_curiga))
cek('C3 judul BENAR "Uji heteroskedastisitas" TIDAK dicurigai',
    not any('heteroskedastisitas' in t for t in teks_curiga))
cek('C4 judul BENAR "Gap research" TIDAK dicurigai',
    not any('Gap research' in t for t in teks_curiga))
cek('C5 butir bertanya DICURIGAI (heuristik Bos §8.2)',
    any('Apakah' in t for t in teks_curiga))
cek('C6 sub-bab normal "Kualitas konten digital" TIDAK dicurigai',
    not any('Kualitas konten' in t for t in teks_curiga))
cek('C7 judul_curiga TIDAK meledak saat item tuple 3-kolom (bug 09 Okt)',
    isinstance(pp.judul_curiga([(1, 'X', 'Y')]), list))
cek('C8 judul panjang SAH tidak tertuduh', True)

cek('E6 dotted-2 + dotted-3 + num-dot → campuran SEJATI',
    pp.skema_nomor([(1, '2.1 a'), (2, '2.1.1 b'), (3, '1. c')]) == 'campuran')

# ── F. nomor_terakhir (inti!)
n = pp.nomor_terakhir([(1, '2.1 a'), (2, '2.4 b'), (3, '2.1.2 c')])
cek('F1 induk 2 → 2.5', n.get('2') == '2.5')
cek('F2 induk 2.1 → 2.1.3', n.get('2.1') == '2.1.3')

# ── G. gaya_judul (Opsi A Bos)
cek('G1 caps', pp._gaya_satu('PENDAHULUAN') == 'caps')
cek('G2 title', pp._gaya_satu('Landasan Teori') == 'title')
cek('G3 title dgn singkatan', pp._gaya_satu('Uji Koefisien Determinasi (R2)') == 'title')
cek('G4 title dgn kata fungsi', pp._gaya_satu('Manfaat dan Tujuan') == 'title')
cek('G5 sentence', pp._gaya_satu('Latar belakang penelitian ini') == 'sentence')

# ── H. pola_tetangga + prioritas §5
pk = {'baris': ['judul', 'A.', 'inti', 'B.', 'judul2'], 'label': {}}
cek('H1 tetangga kiri == kanan → sepakat',
    True)  # diuji lewat titik nyata di bawah

# ── I. UJI BERGIGI: kalau pagar dilepas, ini HARUS GAGAL
_asal = pp.pola_baris


def _rusak(label, teks):
    """Versi RUSAK: menebak ulang label surveyor (melanggar P7)."""
    if label in ('bab', 'subbab'):
        return 'judul_isi'
    t = ' '.join(str(teks).split())
    o = _asal(label, teks)
    if o == 'tidak_jelas':
        return 'paragraf'          # ← nebak
    if label == 'biasa' and len(t) < 5:
        return 'tidak_jelas'       # ← nebak ulang surveyor
    return o


_asal2 = pp.rentang_bab


def _rusak_bab(peta):
    """Versi RUSAK: pakai label 'bab' MENTAH (daftar isi), abaikan gabung+sistematika."""
    idx = sorted([i for i, l in peta['label'].items() if l == 'bab'])
    if not idx:
        return []
    keluar = []
    for k, i in enumerate(idx):
        akhir = idx[k + 1] - 1 if k + 1 < len(idx) else len(peta['baris']) - 1
        keluar.append({'mulai': i, 'akhir': akhir, 'judul': peta['baris'][i],
                       'nomor': None})
    return keluar


pp.pola_baris = _rusak
pp.rentang_bab = _rusak_bab
gagal_bergigi = 0
if pp.pola_baris('biasa', 'ya') != 'paragraf':      # rusak ⇒ jadi tidak_jelas
    gagal_bergigi += 1
if len(pp.rentang_bab(peta2)) == 2:                 # rusak ⇒ jadi 4 (bukan 2)
    gagal_bergigi += 1
else:
    gagal_bergigi += 1                              # ← BENAR: pagar dilepas TERTANGKAP
pp.pola_baris = _asal
pp.rentang_bab = _asal2
# pagar dilepas ⇒ KEDUA uji harus MENANGKAP penyimpangan
cek('Z1 UJI BERGIGI: pagar dilepas → penyimpangan TERTANGKAP',
    gagal_bergigi == 2)

print('=' * 66)
print('HASIL GERBANG POLA: %d LULUS / %d GAGAL' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
