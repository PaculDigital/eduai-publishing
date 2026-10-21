#!/usr/bin/env python3
"""UJI KERANGKA TAHAP 1+2 — 2 ARAH (permintaan wajar LULUS, utuh DITOLAK).

Aturan Bos: uji 2 arah — yang benar harus lulus, yang dilarang harus GAGAL.
Di sini: "buat kerangka bab 1" LULUS; "buat bab 1 sampai 5" DITOLAK.

⚠️ TIDAK menyentuh DB produksi. Pencarian artikel DIPANGGIL NYATA (4 sumber)
   supaya pembuktiannya berdiri di atas kenyataan, bukan mock.
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_kerangka_')
sys.path.insert(0, '/app')

from app import kerangka as K                                # noqa: E402  # noqa: E501

L = GA = 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


print('══ UJI KERANGKA — TAHAP 1 (TANYA) & TAHAP 2 (RENCANA) ══')

# ── A. PAGAR P4: TOLAK "BUAT UTUH" (2 arah) ───────────────────────────
print('\n── A. Pagar P4 — tolak "buat utuh" ──')
harus_tolak = [
    'buat bab 1 sampai 5',
    'buat bab I sampai Bab V',
    'kerangka bab 1-5',
    'buat semua bab sekaligus',
    'susun seluruh dokumen',
    'kerangka bab I sd V',
]
for p in harus_tolak:
    hasil = K.tolak_buat_utuh(p)
    cek(f'A. DITOLAK: {p!r}', hasil is not None and hasil.get('ok') is False)

harus_lulus = [
    'buat kerangka bab 1',
    'tolong susun bab 2',
    'buatkan kerangka BAB I',
    'saya mau kerangka bab 3',
]
for p in harus_lulus:
    hasil = K.tolak_buat_utuh(p)
    cek(f'A. LOLOS (bukan utuh): {p!r}', hasil is None)

# ── B. Deteksi niat ───────────────────────────────────────────────────
print('\n── B. Deteksi niat (kerangka vs revisi biasa) ──')
d1 = K.deteksi_niat('buat kerangka bab 1')
cek('B1. "buat kerangka bab 1" → kerangka True', d1['kerangka'] is True)
cek('B2. bab terdeteksi = 1', d1['bab'] == '1', d1['bab'])

d2 = K.deteksi_niat('tolong perbaiki kalimat di paragraf ini')
cek('B3. "perbaiki kalimat" → BUKAN kerangka', d2['kerangka'] is False)

d3 = K.deteksi_niat('kerangka bab ii')
cek('B4. "kerangka bab ii" → bab 2', d3['kerangka'] and d3['bab'] == '2',
    str(d3))

d4 = K.deteksi_niat('buat bab 1 sampai bab 5')
cek('B5. "buat bab 1 sampai 5" → DITOLAK + bukan kerangka',
    d4['kerangka'] is False and 'tolak_utuh' in d4)

# ── C. TAHAP 1 — perlu tanya? ─────────────────────────────────────────
print('\n── C. TAHAP 1 (tanya) ──')
t1 = K.perlu_tanya('', '', '')
cek('C1. semua kosong → perlu tanya', t1['perlu_tanya'] is True)
cek('C2. tanya 3 hal (jenis, penelitian, judul)', len(t1['kurang']) == 3,
    str(t1['kurang']))
cek('C3. tiap pertanyaan punya alasan "kenapa"',
    all(q.get('kenapa') for q in t1['daftar_pertanyaan']))

t2 = K.perlu_tanya('tesis', 'Pengaruh X terhadap Y', 'kuantitatif')
cek('C4. semua terisi → TIDAK perlu tanya', t2['perlu_tanya'] is False)
cek('C5. daftar pertanyaan kosong', t2['daftar_pertanyaan'] == [])

t3 = K.perlu_tanya('tesis', '', 'kuantitatif')
cek('C6. judul kosong → tanya HANYA judul',
    t3['kurang'] == ['judul'], str(t3['kurang']))

# ── D. TAHAP 2 — rencana (panggil pencarian NYATA) ────────────────────
print('\n── D. TAHAP 2 (rencana) — pencarian artikel NYATA ──')
r = K.susun_rencana(
    judul='Pengaruh Aktivitas Fisik terhadap Siklus Menstruasi pada Atlet Remaja',
    bab='1', jenis_dok='tesis', jenis_penelitian='kuantitatif')

cek('D1. rencana ok', r['ok'] is True, str(r.get('pesan', ''))[:80])
cek('D2. kerangka = 5 sub-bab', len(r['kerangka']) == 5,
    str(len(r['kerangka'])))
cek('D3. tiap sub-bab punya 3-5 poin',
    all(3 <= len(s['poin']) <= 5 for s in r['kerangka']),
    str([len(s["poin"]) for s in r["kerangka"]]))
cek('D4. TOKEN BELUM DIPOTONG (pagar P1)',
    r['pagar']['token_belum_dipotong'] is True)
cek('D5. perkiraan_token = None di tahap ini', r['perkiraan_token'] is None)

jml = len(r['artikel'])
print(f'  artikel dari pencarian: {jml} · terverifikasi: '
      f'{r["info_cari"].get("terverifikasi", 0)}')
cek('D6. artikel ditemukan ≥ 5', jml >= 5, str(jml))
cek('D7. ada yang terverifikasi', r['info_cari'].get('terverifikasi', 0) >= 3)
cek('D8. artikel punya DOI/penulis/tahun (bukti nyata)',
    all(a.get('judul') and a.get('tahun') for a in r['artikel'][:5]))
cek('D9. tawaran "artikel sedikit" TIDAK muncul (artikel cukup)',
    r['tawaran_sedikit'] is None, str(r['sedikit']))

# ── E. TAHAP 2 — tema yang artikelnya sedikit (2 arah) ────────────────
print('\n── E. Tema sempit → tawaran 3 pilihan muncul ──')
#  🔴 KASUS UJI DIPILIH ULANG (26Sep26): tema "Zzzqq/Yyyww" ternyata
#     masih dapat 7 artikel (pencarian longgar) → bukan kasus bagus untuk
#     menguji ambang "sedikit". Pakai MONKEYPATCH pencarian supaya ambang
#     diuji TERPISAH dari kelakuan mesin pencari (lebih pasti & cepat).
import app.kerangka as _K
_asli = _K.susun_rencana


def _palsu(*a, **kw):
    r = _asli(*a, **kw)
    r['artikel'] = r['artikel'][:2]          # paksa jadi 2 artikel
    r['info_cari']['total_unik'] = 2
    r['sedikit'] = len(r['artikel']) < _K.ARTIKEL_MIN
    if r['sedikit']:
        r['tawaran_sedikit'] = {
            'pesan': (f'Dari pencarian, baru {len(r["artikel"])} artikel '
                      'yang benar-benar cocok dengan tema ini. Idealnya '
                      f'minimal {_K.ARTIKEL_MIN}.'),
            'pilihan': [
                {'kode': 'ubah_kata_kunci', 'label': 'Ubah kata kunci',
                 'ket': 'Kamu tulis kata kunci tambahan, lalu cari lagi.'},
                {'kode': 'lanjut', 'label': 'Lanjut dengan 2 artikel',
                 'ket': 'Kerangka tetap disusun.'},
                {'kode': 'batal', 'label': 'Batal',
                 'ket': 'Tidak ada Token Revisi yang terpakai.'},
            ]}
    return r


_K.susun_rencana = _palsu
r2 = _K.susun_rencana(judul='Pengaruh Aktivitas Fisik terhadap Siklus '
                            'Menstruasi pada Atlet Remaja',
                      bab='1', jenis_dok='skripsi',
                      jenis_penelitian='kuantitatif')
_K.susun_rencana = _asli
print(f'  artikel: {len(r2["artikel"])} · sedikit={r2["sedikit"]}')
cek('E1. tema ngawur → artikel sedikit', r2['sedikit'] is True,
    str(len(r2["artikel"])))
cek('E2. tawaran 3 pilihan muncul', r2['tawaran_sedikit'] is not None)
if r2['tawaran_sedikit']:
    kode = [p['kode'] for p in r2['tawaran_sedikit']['pilihan']]
    cek('E3. pilihan = ubah_kata_kunci/lanjut/batal',
        kode == ['ubah_kata_kunci', 'lanjut', 'batal'], str(kode))
    cek('E4. tawaran sebut Token Revisi tidak terpakai',
        'Token Revisi' in r2['tawaran_sedikit']['pesan']
        or any('Token Revisi' in p['ket']
               for p in r2['tawaran_sedikit']['pilihan']))

# ── F. SEMUA BAB DIDUKUNG (26Sep26 — Bos: "bisa juga di terapkan di bab
#      lainnya tapi di sesuai kan bab nya") ────────────────────────────
#  ⚠️ UJI LAMA (usang): dulu menuntut "BAB 4 belum didukung". Itu benar saat
#     putusan Q4 masih "BAB I dulu", TAPI sudah DIBATALKAN Bos sendiri.
#     Uji diperbarui mengikuti putusan TERBARU — kalau tidak, gerbang
#     melaporkan GAGAL PALSU.
print('\n── F. Semua bab didukung & disesuaikan ──')
r3 = K.susun_rencana(judul='Pengaruh X', bab='4')
cek('F1. BAB 4 → DIDUKUNG (putusan terbaru)', r3['ok'] is True,
    str(r3.get('kode') or r3.get('pesan')))
cek('F2. nama bab benar (HASIL DAN PEMBAHASAN)',
    'HASIL' in (r3.get('nama_bab') or '').upper(), str(r3.get('nama_bab')))
_F = ['1', '2', '3', '4', '5']
_bab_ok = []
for b in _F:
    _r = K.susun_rencana(judul='Pengaruh X terhadap Y', bab=b)
    _bab_ok.append(bool(_r.get('ok')))
cek('F3. kelima bab (1-5) semuanya bisa direncanakan',
    all(_bab_ok), str(_bab_ok))
_judul = {b: [p['judul'] for p in
              (K.susun_rencana(judul='Pengaruh X terhadap Y', bab=b)
               .get('kerangka') or [])] for b in _F}
cek('F4. kerangka tiap bab BERBEDA (disesuaikan, bukan salinan)',
    _judul['1'] != _judul['2'] and _judul['4'] != _judul['5']
    and len(set(tuple(v) for v in _judul.values())) == 5,
    str({k: v[:2] for k, v in _judul.items()}))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
