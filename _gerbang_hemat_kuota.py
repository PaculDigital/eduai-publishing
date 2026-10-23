"""GERBANG HEMAT KUOTA SCITE (13Okt26).

Yang diuji:
 (1) Jalur banyak = 1 panggilan (hemat) — pakai fungsi PALSU, bukan Scite
     sungguhan, supaya 0 kuota & tidak bergantung jaringan.
 (2) Jumlah DOI yang ditanya IKUT terkirim sebagai `limit` (jebakan
     terukur: limit:1 ⇒ hanya 1 artikel kembali, sisanya hilang senyap).
 (3) Hasil jalur banyak == hasil jalur `_kutipan_dari_hit` (bentuk sama).
 (4) Cache benar: panggilan ulang 0 panggilan.
 (5) DOI kotor (URL/doi:) dinormalkan; duplikat dibuang.
"""
import sys
sys.path.insert(0, '/app')

from app import pustaka as P

LULUS = GAGAL = 0
JEJAK = []          # catat setiap panggilan ke Scite


def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  LULUS ', nama)
    else:
        GAGAL += 1
        print('  GAGAL ', nama, '<--', ket)


# ── Scite PALSU: balas 3 hits, catat argumen yang diterima ──
def _scite_mcp_palsu(nama_alat, argumen, token):
    JEJAK.append({'alat': nama_alat, 'argumen': dict(argumen or {})})
    return {
        'edges': [
            {'s': '10.9/x', 't': '10.1/a', 'type': ['supporting'],
             'section': ['Introduction'], 'snippets': ['temuan ini sejalan']},
            {'s': '10.9/y', 't': '10.1/a', 'type': ['contrasting'],
             'section': ['Methods'], 'snippets': ['hasil berbeda']},
            {'s': '10.9/z', 't': '10.1/b', 'type': ['mentioning'],
             'section': ['Results'], 'snippets': ['disebut sekilas']},
        ],
        'papers': {
            '10.9/x': {'title': 'Studi pendukung A', 'year': 2021},
            '10.9/y': {'title': 'Studi pembantah B', 'year': 2022},
            '10.9/z': {'title': 'Studi penyebut C', 'year': 2023},
        },
    }


P._scite_mcp = _scite_mcp_palsu
P._scite_token_segar = lambda: 'TOKEN_PALSU'

print('══ A. SATU PANGGILAN untuk banyak DOI (inti hemat) ══')
P._SCITE_KUTIPAN_CACHE.clear()
JEJAK.clear()
hasil = P.scite_kutipan_banyak(['10.1/a', '10.1/b', '10.1/c'], maks=5)
#  ⚠️ 13Okt26: alat baca Scite sudah `citation_graph` (bukan lagi
#     `search_literature`, yang tak punya `citations` ⇒ kutipan hilang
#     senyap). Gerbang ini ikut menyesuaikan.
panggil_baca = [j for j in JEJAK if j['alat'] == 'citation_graph']
cek('A1 3 DOI ⇒ HANYA 1 panggilan baca', len(panggil_baca) == 1,
    f'dapat {len(panggil_baca)} panggilan')
#  Pesan JUJUR (bukan IndexError mentah) kalau alatnya salah — gerbang
#  tetap EXIT 1, tapi yang baca langsung tahu sebabnya.
if not panggil_baca:
    print('  GAGAL  A0 alat baca BUKAN `citation_graph` '
          f'<-- jejak: {[j["alat"] for j in JEJAK]}')
    print()
    print('==================================================================')
    print('HASIL: 0 LULUS · 1 GAGAL  (alat baca salah — seharusnya '
          'citation_graph)')
    raise SystemExit(1)

cek('A2 ketiga DOI ada di SATU panggilan',
    sorted(panggil_baca[0]['argumen'].get('seeds') or []) ==
    ['10.1/a', '10.1/b', '10.1/c'])
cek('A3 kunci hasil lengkap (3 DOI)', set(hasil) == {'10.1/a', '10.1/b', '10.1/c'})

print()
print('══ B. `max_edges` WAJIB dibatasi (jebakan terukur) ══')
#  ⚠️ 13Okt26: `citation_graph` TIDAK punya `limit`. Batasnya `max_edges`
#     (batas TOTAL edge, default model 500). Tanpa batas → jawaban
#     membengkak & lama. Satu artikel saja bisa punya 20 edge.
cek('B1 max_edges diisi & wajar (≤ 200)',
    0 < (panggil_baca[0]['argumen'].get('max_edges') or 0) <= 200,
    f"max_edges = {panggil_baca[0]['argumen'].get('max_edges')}")
cek('B2 include_intent dipakai (jenis kutipan)',
    panggil_baca[0]['argumen'].get('include_intent') is True)
cek('B3 include_snippets dipakai (isi kutipan)',
    panggil_baca[0]['argumen'].get('include_snippets') is True)

print()
print('══ C. ISI kutipan benar (jenis + bagian) ══')
cek('C1 DOI a punya 2 kutipan', len(hasil['10.1/a'] or []) == 2)
cek('C2 jenis supporting ⇒ "didukung"',
    (hasil['10.1/a'] or [{}])[0].get('jenis') == 'didukung')
cek('C3 jenis contrasting ⇒ "dibantah"',
    (hasil['10.1/a'] or [{}, {}])[1].get('jenis') == 'dibantah')
cek('C4 bagian "Methods" ikut terbaca',
    (hasil['10.1/a'] or [{}, {}])[1].get('bagian') == 'Methods')
cek('C5 DOI tanpa kutipan ⇒ None', hasil['10.1/c'] is None)

print()
print('══ D. CACHE (panggilan ulang = 0 panggilan = 0 kuota) ══')
JEJAK.clear()
hasil2 = P.scite_kutipan_banyak(['10.1/a', '10.1/b', '10.1/c'], maks=5)
cek('D1 ulang ⇒ 0 panggilan', len(JEJAK) == 0, f'dapat {len(JEJAK)}')
cek('D2 hasil ulang sama', hasil2 == hasil)

print()
print('══ E. BERSIH-BERSIH doi (URL / doi: / duplikat) ══')
P._SCITE_KUTIPAN_CACHE.clear()
JEJAK.clear()
P.scite_kutipan_banyak(['https://doi.org/10.1/a', 'doi:10.1/a',
                        '10.1/a', 'http://dx.doi.org/10.1/b'], maks=5)
dikirim = (JEJAK[0]['argumen'].get('seeds') if JEJAK else []) or []
cek('E1 cuma 2 DOI unik terkirim', len(dikirim) == 2, f'{dikirim}')
cek('E2 awalan URL dibuang', dikirim[0] == '10.1/a', f'{dikirim}')
cek('E3 "doi:" dibuang', 'doi:10.1/a' not in dikirim)

print()
print('══ E4. DOI KOTOR ⇒ kutipan TETAP ketemu (jebakan 13Okt26) ══')
#  Inilah bug yang bikin 10 artikel dapat 0 kutipan: daftar memakai
#  DOI berawalan https://doi.org/, peta hasil memakai DOI bersih ⇒
#  .get() gagal senyap. Gerbang WAJIB menangkap bentuk ini.
P._SCITE_KUTIPAN_CACHE.clear()
JEJAK.clear()
_kotor = P.scite_kutipan_banyak(['https://doi.org/10.1/a'], maks=5)
cek('E4a kunci hasil = DOI BERSIH (bukan URL)',
    '10.1/a' in _kotor and 'https://doi.org/10.1/a' not in _kotor,
    f'{list(_kotor)}')
cek('E4b isi kutipan ikut terbaca', bool(_kotor.get('10.1/a')))
#  Bukti gigi: kalau pemetaan memakai DOI KOTOR, hasilnya HARUS None.
_kunci_dipakai = list(_kotor)[0]
cek('E4c DOI bersih == yang dikirim ke Scite',
    _kunci_dipakai == (JEJAK[0]['argumen'].get('seeds') or [''])[0])

print()
print('══ F. TITIK PAKAI di aplikasi sudah pakai jalur banyak ══')
try:
    with open('/app/app/pustaka.py', encoding='utf-8') as f:
        src = f.read()
    cek('F1 titik pakai memanggil scite_kutipan_banyak',
        'scite_kutipan_banyak(_dois' in src)
    #  ⚠️ `ThreadPoolExecutor` LEGAL untuk `mutu_jurnal` (SJR/CiteScore,
    #     gratis) dan `scite_tallies` (angka, pintu gratis tanpa kunci).
    #     Yang DILARANG = paralel per-DOI untuk KUTIPAN.
    #  ⚠️ JEBAKAN 06Okt26 (kena di sini): gerbang memeriksa KODE, bukan
    #     KOMENTAR. Komentar penjelas Wulan sendiri memuat kata
    #     "ThreadPoolExecutor" + "scite_kutipan" ⇒ GAGAL PALSU.
    #     ⇒ BUANG komentar + docstring dulu, baru cari pola.
    import re as _re
    _kode = _re.sub(r'#[^\n]*', '', src)
    _kode = _re.sub(r'"""[\s\S]*?"""', '', _kode)
    _kode = _re.sub(r"'''[\s\S]*?'''", '', _kode)
    _ada_par_kutipan = False
    for _m in _re.finditer(r'ThreadPoolExecutor[\s\S]{0,400}', _kode):
        _isi = _m.group(0)
        if 'scite_kutipan' in _isi and 'scite_kutipan_banyak' not in _isi:
            _ada_par_kutipan = True
    cek('F2 kutipan TIDAK lagi dipanggil per-DOI', not _ada_par_kutipan,
        'masih ada ThreadPoolExecutor memanggil scite_kutipan per DOI')
    #  F4 = gerbang ini BERGIGI: kalau pemeriksa dipaksa melihat kode
    #  lama, ia HARUS protes (bukan sekadar hijau).
    _kode_lama = _kode + ("\nfrom concurrent.futures import ThreadPoolExecutor\n"
                          "with ThreadPoolExecutor(max_workers=3) as tp:\n"
                          "    tp.map(scite_kutipan, dois)\n")
    _kena = False
    for _m in _re.finditer(r'ThreadPoolExecutor[\s\S]{0,400}', _kode_lama):
        if 'scite_kutipan' in _m.group(0):
            _kena = True
    cek('F4 pemeriksa BERGIGI (kode lama = ketahuan)', _kena)
    cek('F3 paralel untuk angka/mutu masih ada (memang sah)',
        'scite_tallies' in src and 'mutu_jurnal' in src)
except Exception as e:
    cek('F0 berkas terbaca', False, str(e)[:60])

print()
print('=' * 66)
print(f'HASIL: {LULUS} LULUS · {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
