"""UJI PERILAKU Sambungan B — artikel bab jadi bahan AI (13Okt26).

Membuktikan TANPA DB & tanpa panggil AI:
  1. pakai_di_banyak() MENYALIN artikel ke bab tujuan.
  2. untuk_bangun_isi() bab tujuan MEMUAT artikel itu.
  3. bangun_isi(artikel_dipakai=...) memakai bahan itu (tidak cari ulang).
"""
import sys

sys.path.insert(0, '/app')

from app import jurnal as J

ART = {
    'title': 'Pengaruh Mindfulness pada Performa Atlet',
    'doi': '10.1000/uji.b', 'doi_status': 'verified',
    'penulis': 'Susanti', 'tahun': 2021,
    'jurnal': 'Jurnal Uji', 'sumber': 'openalex',
}

lulus, gagal = [], []


def cek(nama, benar, ket=''):
    (lulus if benar else gagal).append(nama)
    print(f'  {"LULUS " if benar else "GAGAL "} {nama} {ket}')


print('═══ UJI SAMBUNGAN B ═══')

#  ── 1. artikel masuk bab III ──
d = J.tambah({}, 'BAB III', [ART], asal='ai')
cek('B1 artikel masuk BAB III', len(J.daftar(d, 'BAB III')) == 1,
    f'(n={len(J.daftar(d, "BAB III"))})')

#  ── 2. pakai ulang ke BAB II ──
k = J.kunci(ART)
d = J.pakai_di_banyak(d, 'BAB III', ['BAB II'], k)
n3, n2 = len(J.daftar(d, 'BAB III')), len(J.daftar(d, 'BAB II'))
cek('B2 BAB III tetap 1 (tidak terhapus)', n3 == 1, f'(n={n3})')
cek('B3 BAB II dapat artikel pakai-ulang', n2 == 1, f'(n={n2})')

#  ── 3. bahan untuk AI: bab tujuan MEMUAT artikel ──
bahan2 = J.untuk_bangun_isi(d, 'BAB II')
bahan3 = J.untuk_bangun_isi(d, 'BAB III')
cek('B4 bahan BAB II memuat 1 artikel', len(bahan2) == 1,
    f'(n={len(bahan2)})')
cek('B5 bahan BAB III memuat 1 artikel', len(bahan3) == 1,
    f'(n={len(bahan3)})')
cek('B6 judul artikel BENAR di bahan BAB II',
    bool(bahan2) and 'Mindfulness' in str(bahan2[0].get('title')), '')

#  ── 4. bab KOSONG → bahan kosong (perilaku lama, jangan mengarang) ──
bahan1 = J.untuk_bangun_isi(d, 'BAB I')
cek('B7 BAB I kosong → bahan kosong (tidak mengarang)', len(bahan1) == 0,
    f'(n={len(bahan1)})')

#  ── 5. DOI SELALU ikut (pagar audit tetap) ──
cek('B8 DOI ikut terkirim (audit tetap jalan)',
    bool(bahan2) and bahan2[0].get('doi') == '10.1000/uji.b',
    f'(doi={bahan2[0].get("doi") if bahan2 else None})')

print()
print(f'HASIL: {len(lulus)} LULUS · {len(gagal)} GAGAL')
if gagal:
    print('   GAGAL: ' + ', '.join(gagal))
    sys.exit(1)
print('   ✅ artikel bab benar-benar menjadi bahan AI.')
sys.exit(0)
