#!/usr/bin/env python3
"""UJI PENCARIAN REFERENSI — 2 arah (nyambung LULUS, ngawur DITOLAK).

Aturan Bos: uji 2 arah — sehat harus LULUS, dirusak harus GAGAL.
Di sini: tema nyata → artikel harus NYAMBUNG; tema ngawur → harus tetap
mengembalikan sesuatu yang nyambung (bukan asal ada).

Juga menguji saringan `_nyambung()` secara TERPISAH dengan data palsu —
supaya kegagalan saringan ketahuan tanpa memanggil API (cepat & pasti).
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_pustaka_')
sys.path.insert(0, '/app')

from app import pustaka as P                                    # noqa: E402

L, GA = 0, 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


print('══ UJI PENCARIAN REFERENSI (PICO + AND) ══')

# ── A. KONSEP dari judul ──────────────────────────────────────────────
print('\n── A. Konsep dari judul (PICO) ──')
k = P.konsep_dari_judul('Pengaruh Aktivitas Fisik terhadap Siklus '
                        'Menstruasi pada Atlet Remaja')
nama_konsep = [x['konsep'] for x in k]
print(f'  konsep: {nama_konsep}')
cek('A1. konsep terdeteksi ≥ 3', len(k) >= 3, str(nama_konsep))
cek('A2. ada konsep "siklus menstruasi"', 'siklus menstruasi' in nama_konsep)
cek('A3. ada konsep "aktivitas fisik"', 'aktivitas fisik' in nama_konsep)

q = P.rumus_scopus(k)
print(f'  rumus: {q[:110]}…')
cek('A4. rumus Scopus pakai AND antar konsep', ' AND ' in q)
cek('A5. rumus Scopus pakai OR di dalam konsep',
    'TITLE-ABS-KEY(' in q and ' OR ' in q)

# ── B. Konsep judul lain (bukti TIDAK kaku pada 1 tema) ───────────────
print('\n── B. Tema lain ──')
k2 = P.konsep_dari_judul('Pengaruh Harga dan Promosi terhadap Keputusan '
                         'Pembelian')
n2 = [x['konsep'] for x in k2]
print(f'  konsep: {n2}')
cek('B1. tema bisnis terdeteksi ≥ 2 konsep', len(k2) >= 2, str(n2))
cek('B2. ada "keputusan pembelian"', 'keputusan pembelian' in n2)

# ── C. SARINGAN terpisah (data palsu — cepat, tanpa API) ──────────────
print('\n── C. Saringan _nyambung (data palsu) ──')
kw = P.kata_kunci('Pengaruh Aktivitas Fisik terhadap Siklus Menstruasi '
                  'pada Atlet Remaja')

tepat = {'title': 'Association between Physical Activity and Menstrual '
                  'Cycle Disorders in Female Athletes', 'abstract': ''}
ngawur1 = {'title': 'Copper induces cell death by targeting lipoylated TCA '
                    'cycle proteins', 'abstract': ''}
ngawur2 = {'title': 'Challenges and burden of the Coronavirus 2019 pandemic '
                    'for child and adolescent', 'abstract': ''}
ngawur3 = {'title': 'Lithium ion battery degradation', 'abstract': ''}
cek('C1. artikel TEPAT → LULUS', P._nyambung(tepat, kw) is True)
cek('C2. "Copper/TCА cycle" → DITOLAK', P._nyambung(ngawur1, kw) is False)
cek('C3. "COVID-19 adolescent" → DITOLAK', P._nyambung(ngawur2, kw) is False)
cek('C4. "lithium battery" → DITOLAK', P._nyambung(ngawur3, kw) is False)

# ── D. E2E NYATA (panggil 4 sumber) ───────────────────────────────────
print('\n── D. E2E nyata: cari 4 sumber ──')
h = P.cari_semua('Pengaruh Aktivitas Fisik terhadap Siklus Menstruasi '
                 'pada Atlet Remaja')
print(f'  per sumber : {h["jumlah_per_sumber"]}')
print(f'  unik {h["total_unik"]} · terverifikasi {h["terverifikasi"]}')
cek('D1. Scopus memberi hasil', h['jumlah_per_sumber'].get('Scopus', 0) > 0,
    str(h['jumlah_per_sumber']))
cek('D2. OpenAlex memberi hasil', h['jumlah_per_sumber'].get('OpenAlex', 0) > 0)
cek('D3. Garuda memberi hasil', h['jumlah_per_sumber'].get('Garuda', 0) > 0)
cek('D4. CrossRef memberi hasil', h['jumlah_per_sumber'].get('CrossRef', 0) > 0)
cek('D5. artikel unik ≥ 8 (cukup untuk BAB I)', h['total_unik'] >= 8,
    str(h['total_unik']))
cek('D6. ada yang TERVERIFIKASI', h['terverifikasi'] >= 5,
    str(h['terverifikasi']))

#  D7: judul hasil HARUS menyentuh konsep (bukti presisi)
konsep_kata = ['menstrua', 'physical', 'exercise', 'sport', 'athlet',
               'female', 'siklus', 'aktivitas', 'gizi', 'hormon']
nyambung_judul = [r for r in h['artikel']
                  if any(w in (r.get('title') or '').lower()
                         for w in konsep_kata)]
persen = 100 * len(nyambung_judul) / max(1, h['total_unik'])
print(f'  judul menyentuh tema: {len(nyambung_judul)}/{h["total_unik"]} '
      f'({persen:.0f}%)')
cek('D7. ≥ 70% judul menyentuh tema', persen >= 70, f'{persen:.0f}%')

#  D8: tidak ada judul ngawur yang jelas (pembanding negatif)
terlarang = ['lithium', 'battery', 'copper', 'biofilm', 'covid',
             'brain imaging', 'cancer cell']
ada_ngawur = [r.get('title') for r in h['artikel']
              if any(w in (r.get('title') or '').lower() for w in terlarang)]
cek('D8. TIDAK ada judul ngawur', not ada_ngawur, str(ada_ngawur)[:120])

print('\n── D9. Daftar pustaka APA 7 ──')
apa = P.daftar_pustaka_apa7(h['artikel'])
print(apa[:400] if apa else '(kosong)')
cek('D9. APA7 tidak kosong', len(apa) > 100, str(len(apa)))
cek('D10. APA7 tidak memuat yang unverified',
    'unverified' not in apa.lower())

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
