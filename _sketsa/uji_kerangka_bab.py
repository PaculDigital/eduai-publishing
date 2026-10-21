#!/usr/bin/env python3
"""UJI KERANGKA 5 BAB + TAHAP 3 — 2 arah.

Menguji:
  A. 5 bab punya kerangka, DISESUAIKAN kaidahnya (isi beda tiap bab)
  B. tabel & grafik sesuai bab (BAB II kerangka pikir, BAB IV grafik data)
  C. TAHAP 3 (bangun_isi) — sitasi nyata + APA7 + TIDAK potong token
  D. Pagar P3 — hanya artikel terverifikasi masuk daftar pustaka
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_kb_')
sys.path.insert(0, '/app')

from app import kerangka as K                                # noqa: E402
from app import kerangka_bab as KB                           # noqa: E402

L = GA = 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


print('══ UJI KERANGKA 5 BAB + TAHAP 3 ══')

# ── A. 5 bab ada + isi BERBEDA (disesuaikan) ──────────────────────────
print('\n── A. 5 bab, kerangka disesuaikan ──')
daftar = KB.daftar_bab()
print(f'  bab tersedia: {[d["bab"] for d in daftar]}')
cek('A1. ada 5 bab', len(daftar) == 5, str(len(daftar)))
cek('A2. bab 1..5 lengkap',
    sorted(d['bab'] for d in daftar) == ['1', '2', '3', '4', '5'])

judul_sub: dict[str, list[str]] = {}
for b in ['1', '2', '3', '4', '5']:
    x = KB.ambil(b)
    judul_sub[b] = [j for (_, j, _) in x['sub_bab']]
    cek(f'A3.{b}. BAB {b} punya {len(x["sub_bab"])} sub-bab '
        f'({x["nama"]})', len(x['sub_bab']) == 5, str(len(x['sub_bab'])))

#  isi tiap bab HARUS berbeda (bukti "disesuaikan", bukan salinan)
kumpul = [tuple(judul_sub[b]) for b in judul_sub]
cek('A4. judul sub-bab tiap bab BERBEDA (tidak salinan)',
    len(set(kumpul)) == 5, str(len(set(kumpul))))
print(f'  BAB 1: {judul_sub["1"][0]}')
print(f'  BAB 2: {judul_sub["2"][0]}')
print(f'  BAB 3: {judul_sub["3"][0]}')
print(f'  BAB 4: {judul_sub["4"][0]}')
print(f'  BAB 5: {judul_sub["5"][0]}')

#  ciri khas tiap bab
cek('A5. BAB II punya "Hipotesis" (khas tinjauan pustaka)',
    any('Hipotesis' in j for j in judul_sub['2']), str(judul_sub['2']))
cek('A6. BAB III punya "Analisis Data" (khas metode)',
    any('Analisis' in j for j in judul_sub['3']), str(judul_sub['3']))
cek('A7. BAB IV punya "Hasil Uji Hipotesis" (khas hasil)',
    any('Uji Hipotesis' in j for j in judul_sub['4']), str(judul_sub['4']))
cek('A8. BAB V punya "Kesimpulan"', any('Kesimpulan' in j
                                        for j in judul_sub['5']))
cek('A9. BAB V TIDAK punya "Latar Belakang" (beda dari BAB I)',
    not any('Latar Belakang' in j for j in judul_sub['5']))

# ── B. TABEL & GRAFIK sesuai bab ──────────────────────────────────────
print('\n── B. Tabel & grafik disesuaikan bab ──')
b2 = KB.ambil('2')['butuh']
b4 = KB.ambil('4')['butuh']
cek('B1. BAB II butuh tabel penelitian terdahulu',
    any('terdahulu' in t for t in b2['tabel']), str(b2['tabel']))
cek('B2. BAB II butuh gambar kerangka pikir',
    any('kerangka pikir' in g for g in b2['grafik']), str(b2['grafik']))
cek('B3. BAB IV butuh tabel hasil uji',
    any('hipotesis' in t for t in b4['tabel']), str(b4['tabel']))
cek('B4. BAB IV butuh grafik', len(b4['grafik']) >= 1, str(b4['grafik']))
cek('B5. BAB I TIDAK butuh grafik (tidak mengarang)',
    KB.ambil('1')['butuh']['grafik'] == [])

# ── C. TAHAP 3 — bangun_isi ───────────────────────────────────────────
print('\n── C. TAHAP 3 (bangun_isi) — sitasi nyata ──')
h = K.bangun_isi(judul='Pengaruh Aktivitas Fisik terhadap Siklus '
                       'Menstruasi pada Atlet Remaja',
                 bab='1', jenis_dok='tesis', jenis_penelitian='kuantitatif')
cek('C1. bangun_isi ok', h['ok'] is True)
cek('C2. nama bab terisi', h['nama_bab'] == 'PENDAHULUAN', h['nama_bab'])
cek('C3. kerangka 5 sub-bab', len(h['kerangka']) == 5)
cek('C4. artikel nyata ditemukan', len(h['artikel']) >= 5,
    str(len(h['artikel'])))
cek('C5. daftar pustaka APA7 terbentuk', len(h['daftar_pustaka']) > 100,
    str(len(h['daftar_pustaka'])))
cek('C6. TOKEN TIDAK DIPOTONG di fungsi ini',
    h['pagar']['token_dipotong_di_api'] is True)
cek('C7. sitasi terverifikasi dilaporkan',
    h['pagar']['sitasi_terverifikasi'] >= 3,
    str(h['pagar']['sitasi_terverifikasi']))

#  Pagar P3: daftar pustaka TIDAK memuat yang unverified
unver = [r for r in h['artikel'] if r.get('doi_status') == 'unverified']
print(f'  artikel unverified: {len(unver)}')
cek('C8. daftar pustaka tidak memuat DOI unverified',
    all((r.get('doi') or '') not in h['daftar_pustaka']
        for r in unver if r.get('doi')),
    str([r.get('doi') for r in unver][:2]))

# ── D. TAHAP 3 untuk BAB IV (paling banyak tabel+grafik) ──────────────
print('\n── D. TAHAP 3 BAB IV (tabel + grafik terbanyak) ──')
h4 = K.bangun_isi(judul='Pengaruh Aktivitas Fisik terhadap Siklus '
                        'Menstruasi pada Atlet Remaja', bab='4')
cek('D1. BAB IV ok', h4['ok'] is True)
cek('D2. BAB IV punya 2 tabel', len(h4['tabel']) == 2, str(len(h4['tabel'])))
cek('D3. BAB IV punya 2 grafik', len(h4['grafik']) == 2,
    str(len(h4['grafik'])))
cek('D4. jenis grafik BAB IV = batang',
    all(g['jenis'] == 'batang' for g in h4['grafik']),
    str([g['jenis'] for g in h4['grafik']]))
cek('D5. nama bab = HASIL DAN PEMBAHASAN',
    h4['nama_bab'] == 'HASIL DAN PEMBAHASAN', h4['nama_bab'])

# ── E. BAB 6 / bab tidak ada → jujur ──────────────────────────────────
print('\n── E. Bab tidak tersedia → jujur ──')
h6 = K.bangun_isi(judul='X', bab='6')
cek('E1. BAB 6 (daftar pustaka) → tidak berkerangka (jujur)',
    h6['ok'] is False, str(h6.get('kode')))
r9 = K.susun_rencana(judul='X', bab='9')
cek('E2. BAB 9 → pesan sebut bab yang tersedia',
    r9['ok'] is False and 'BAB 1' in (r9.get('pesan') or ''),
    r9.get('pesan', '')[:90])

# ── F. semua bab bisa direncanakan ────────────────────────────────────
print('\n── F. Tahap 2 untuk SEMUA bab ──')
for b in ['1', '2', '3', '4', '5']:
    rr = K.susun_rencana(judul='Pengaruh Harga terhadap Keputusan Pembelian',
                         bab=b, jenis_dok='skripsi')
    cek(f'F.{b}. BAB {b} rencana ok ({rr.get("nama_bab", "")})',
        rr['ok'] is True and len(rr['kerangka']) == 5,
        str(rr.get('kode') or len(rr.get('kerangka', []))))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
