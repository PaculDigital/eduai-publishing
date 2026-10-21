"""Uji sambungan konversi — v2 (alat ukur DIPERBAIKI, 07 Okt 2026).

PELAJARAN v1 (3 gagal PALSU): jangan cari penanda di SELURUH sumber
(termasuk komentar) — cari di KODE saja (buang baris komentar & string).
"""
import ast
import inspect
import sys

sys.path.insert(0, '/app')
from app import konversi as K

HASIL = {'lulus': 0, 'gagal': 0, 'gagal_nama': []}


def cek(nama, syarat, ket=''):
    if syarat:
        HASIL['lulus'] += 1
        print(f'LULUS  {nama}')
    else:
        HASIL['gagal'] += 1
        HASIL['gagal_nama'].append(nama)
        print(f'GAGAL  {nama} {ket}')


def kode_saja(fn) -> str:
    """Sumber fungsi TANPA komentar & docstring (cari penanda di KODE saja)."""
    src = inspect.getsource(fn)
    baris = [b.split('#', 1)[0] for b in src.splitlines()]
    teks = '\n'.join(baris)
    for kutip in ('"""', "'''"):
        while teks.count(kutip) >= 2:
            i = teks.find(kutip)
            j = teks.find(kutip, i + 3)
            teks = teks[:i] + teks[j + 3:]
    return teks


# ── 1. Pembaca JSON ───────────────────────────────────────────────────
cek('S1 JSON polos terbaca',
    K._urai_artikel('{"judul":"Uji"}') == {'judul': 'Uji'})
cek('S2 pagar ```json dibuang',
    K._urai_artikel('```json\n{"judul":"Pagar"}\n```') == {'judul': 'Pagar'})
cek('S3 kata pengantar dibuang',
    K._urai_artikel('Ini artikelnya:\n{"judul":"Ngasal"}\nSemoga.') == {'judul': 'Ngasal'})
cek('S4 sampah → None', K._urai_artikel('tidak ada json') is None)
cek('S5 kosong → None', K._urai_artikel('') is None)
cek('S6 list JSON → None', K._urai_artikel('[1,2]') is None)
cek('S6b JSON cacat → None', K._urai_artikel('{"judul": "x"') is None)

# ── 2. Normalisasi bentuk ─────────────────────────────────────────────
n = K.normalisasi_artikel({'judul': 'X'})
for k in K.BAGIAN_WAJIB:
    cek(f'S7 kunci "{k}" selalu ada', k in n)
cek('S7b elemen jadi dict', isinstance(n.get('elemen'), dict))
cek('S7c bentuk baku = yang dipakai artikel_ke_teks',
    set(['judul', 'penulis', 'abstrak_id', 'abstract_en', 'kata_kunci',
         'daftar_pustaka', 'elemen']).issubset(n.keys()))
n2 = K.normalisasi_artikel({'kata_kunci': 'harga, promosi'})
cek('S8 kata_kunci string → list', n2['kata_kunci'] == ['harga', 'promosi'])
cek('S9 penulis salah bentuk → []', K.normalisasi_artikel({'penulis': 'A'})['penulis'] == [])
cek('S10 pustaka string → list',
    K.normalisasi_artikel({'daftar_pustaka': 'Satu\nDua'})['daftar_pustaka'] == ['Satu', 'Dua'])
cek('S11 elemen kosong dibuang',
    K.normalisasi_artikel({'elemen': {'a': 'x', 'b': ''}})['elemen'] == {'a': 'x'})
cek('S11b None masuk akal', K.normalisasi_artikel(None)['judul'] == '')

# ── 3. Pesan & prompt ─────────────────────────────────────────────────
p = K.susun_pesan('naskah uji', 'kuantitatif',
                  {'nama': 'Asih', 'email': 'a@b.c'}, {'kerangka': []}, 'JPEM')
cek('S12 pesan memuat nama', 'Asih' in p)
cek('S12b pesan memuat email', 'a@b.c' in p)
cek('S12c pesan memuat template', 'JPEM' in p)
cek('S12d pesan memuat naskah', 'naskah uji' in p)
pr = K.muat_prompt()
cek('S13 prompt artikel terbaca', len(pr) > 1000, f'{len(pr)} kar')
#  ⚠️ v1 & v2 SALAH DUA KALI di sini. Akarnya:
#     '## PERAN'.startswith('#') == True  → judul markdown dikira komentar!
#     Uji lama memakai startswith('#') sehingga SELALU gagal, padahal
#     pembersihnya BENAR (header '# …' memang sudah dibuang).
#  Uji yang benar: baris pertama tidak boleh KOMENTAR SEJATI ('# ' diikuti
#  spasi = komentar berkas); judul markdown ('##' / '#Kata') SAH.
bersih = K._bersihkan_komentar_header(pr)
b1 = (bersih.splitlines() or [''])[0]
cek('S13b header komentar sejati sudah dibuang',
    not b1.startswith('# '), f'baris-1={b1[:40]!r}')
cek('S13b2 judul markdown DIPERTAHANKAN', b1.startswith('##'), f'= {b1[:30]!r}')
cek('S13b3 header mentah memang mulai komentar sejati',
    (pr.splitlines() or [''])[0].startswith('# '))
cek('S13c pembersih TIDAK membuang isi', 'PERAN' in bersih and len(bersih) > 5000)

# ── 4. Kode saja (bukan komentar) ─────────────────────────────────────
kode = kode_saja(K.jalankan_konversi)
cek('S14 KODE pakai _panggil_router', '_panggil_router' in kode)
cek('S14b KODE pasok system=', 'system=sistem' in kode)
cek('S14c KODE TIDAK pakai _revisi_dengan_failover',
    '_revisi_dengan_failover' not in kode)
cek('S15 KODE tidak memotong kuota', 'potong_konversi' not in kode)
cek('S15b KODE tidak menyimpan hasil', 'simpan_hasil' not in kode)
cek('S16 KODE laporkan nama model asli', "'model'" in kode)

# ── 5. Fungsi wajib ada (dipakai rute nanti) ──────────────────────────
for nm in ('jalankan_konversi', 'normalisasi_artikel', '_urai_artikel',
           'susun_pesan', 'simpan_hasil', 'gagalkan',
           'periksa_sebelum_konversi', 'daftar_revisi', 'hitung_biaya_revisi'):
    cek(f'S17 fungsi {nm}() ada', callable(getattr(K, nm, None)))

print(f'\nTOTAL: {HASIL["lulus"]} LULUS / {HASIL["gagal"]} GAGAL')
if HASIL['gagal']:
    print('YANG GAGAL: ' + ', '.join(HASIL['gagal_nama']))
sys.exit(1 if HASIL['gagal'] else 0)
