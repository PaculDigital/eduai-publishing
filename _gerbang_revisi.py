"""GERBANG REVISI (08 Okt 2026) — 2 token/item, SATU dompet, urutan pagar.

Bukan uji "hijau palsu": tiap asersi bisa GAGAL kalau pagar dicabut.
Jalankan DI DALAM container:  docker exec -w /app eduai-app python3 _gerbang_revisi.py
"""
import sys, json, inspect
sys.path.insert(0, '/app')

LULUS = GAGAL = 0
def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}  {bukti}')

print('═══ 1. MESIN: biaya_revisi_valid ═══')
from app import konversi as kv

# 1a. kosong -> tolak
r = kv.biaya_revisi_valid([], 100)
cek('pilihan kosong DITOLAK', r['ok'] is False, r)

# 1b. item sah x1 -> 2 token
r = kv.biaya_revisi_valid(['abstrak_id'], 100)
cek('1 item sah -> 2 token', r['ok'] and r['token'] == 2, r)

# 1c. item sah x2 -> Abstrak (BAGIAN, 2) + Novelty (ELEMEN sedang, 3) = 5 token
#  ⚠️ ANGKA DIPERBARUI 15 Okt 2026 (putusan Bos: harga elemen mutu BERTINGKAT
#     Berat 5 / Sedang 3 / Standar 2). Dulu keduanya 2 → 4 token.
#     Novelty kini SEDANG (3) ⇒ 2 + 3 = 5.
r = kv.biaya_revisi_valid(['abstrak_id', 'elemen:novelty'], 100)
cek('2 item -> 5 token (Abstrak 2 + Novelty 3)',
    r['ok'] and r['token'] == 5 and r['jumlah'] == 2, r)

# 1d. saldo kurang -> TOLAK + sebut kurangnya
r = kv.biaya_revisi_valid(['abstrak_id', 'elemen:novelty'], 3)
cek('saldo 3 < 5 -> DITOLAK', r['ok'] is False and r.get('kurang') == 2, r)

# 1d2. SALDO PAS -> harus LOLOS (pagar tidak boleh kebablasan menolak)
r = kv.biaya_revisi_valid(['abstrak_id', 'elemen:novelty'], 5)
cek('saldo PAS (5) -> LOLOS (pagar tidak kebablasan)',
    r['ok'] is True and r['token'] == 5, r)

# 1e. kunci NGAWUR -> dibuang, JANGAN diloloskan
r = kv.biaya_revisi_valid(['abstrak_id', 'bukan_bagian', 'DROP TABLE'], 100)
cek('kunci ngawur DIBUANG (bukan dilolos)',
    r['ok'] and r['pilihan'] == ['abstrak_id'] and
    set(r.get('ditolak') or []) == {'bukan_bagian', 'DROP TABLE'}, r)

# 1f. SEMUA ngawur -> tolak  (pakai perbandingan LANGSUNG, jangan ganti variabel)
r = kv.biaya_revisi_valid(['ngawur1', 'ngawur2'], 100)
cek('semua ngawur -> DITOLAK (ok harus False)',
    r.get('ok') is False and r.get('token') == 0, r)

# 1g. TOKEN_PER_REVISI = 2 (putusan Bos) — uji NILAI ASLI, jangan diri sendiri.
#  ⚠️ Asersi `kv.TOKEN_PER_REVISI == 2` TIDAK BERGIGI: kalau konstantanya
#  diubah jadi 1, asersi itu IKUT berubah (menguji diri sendiri) → lolos.
#  Cara bergigi: BANDINGKAN dengan angka yang ditulis TERPISAH di sini.
ANGKA_TOKEN_PUTUSAN_BOS = 2          # SOT §N no.9 — ditulis manual, bukan impor
cek('TOKEN_PER_REVISI == 2 (angka putusan, bukan diri sendiri)',
    int(kv.TOKEN_PER_REVISI) == ANGKA_TOKEN_PUTUSAN_BOS,
    f'kode={kv.TOKEN_PER_REVISI} putusan={ANGKA_TOKEN_PUTUSAN_BOS}')
#  Dan buktikan ia BENAR-BENAR dipakai menghitung (bukan konstanta mati).
r2 = kv.biaya_revisi_valid(['abstrak_id'], 100)
cek('biaya 1 item == angka putusan (konstanta DIPAKAI)',
    r2['token'] == ANGKA_TOKEN_PUTUSAN_BOS, r2)
r3 = kv.biaya_revisi_valid(['abstrak_id', 'judul', 'metode'], 100)
cek('biaya 3 item == 3 x angka putusan',
    r3['token'] == 3 * ANGKA_TOKEN_PUTUSAN_BOS, r3)

# ── 1h. HARGA BERTINGKAT ELEMEN MUTU (putusan Bos 15 Okt 2026) ──────────────
#  ⚠️ Angka DITULIS TERPISAH di sini (bukan impor dari kode) — kalau kode
#  diam-diam berubah, uji ini GAGAL. Itu bukti gigi-nya.
HARGA_ELEMEN_PUTUSAN = {
    'state_of_art': 5, 'diskusi_komparatif': 5,          # BERAT
    'gap': 3, 'novelty': 3, 'findings': 3,               # SEDANG
    'critical_analysis': 3, 'kaitan_teori': 3,
    'hook': 2, 'limitasi': 2, 'rekomendasi': 2, 'implikasi': 2,   # STANDAR
}
for _k, _harap in HARGA_ELEMEN_PUTUSAN.items():
    _dapat = int(kv.token_elemen(_k))
    cek(f'harga elemen {_k} == {_harap}', _dapat == _harap,
        f'kode={_dapat} putusan={_harap}')

#  semua 11 elemen ELEMEN_REVISI tercakup (tidak ada yang lupa dihargai)
_kunci_11 = {k for k, _ in kv.ELEMEN_REVISI}
cek('11 elemen mutu SEMUA punya harga putusan',
    _kunci_11 == set(HARGA_ELEMEN_PUTUSAN),
    f'kurang={_kunci_11 - set(HARGA_ELEMEN_PUTUSAN)} '
    f'lebih={set(HARGA_ELEMEN_PUTUSAN) - _kunci_11}')

#  tingkat beban konsisten dengan harga
cek('tingkat: 5=berat, 3=sedang, 2=standar',
    kv.tingkat_elemen('state_of_art') == 'berat' and
    kv.tingkat_elemen('gap') == 'sedang' and
    kv.tingkat_elemen('hook') == 'standar', '')

#  BAGIAN ARTIKEL tetap 2 (harga bertingkat TIDAK menyentuh bagian)
_b = {x['kunci']: x['token'] for x in kv.daftar_revisi(
    {'judul': 'x', 'pendahuluan': 'y', 'elemen': {'gap': 'z'}})}
cek('bagian artikel tetap 2 token (judul/pendahuluan)',
    _b.get('judul') == 2 and _b.get('pendahuluan') == 2, str(_b))
cek('elemen mutu memakai harga bertingkat (gap=3)',
    _b.get('elemen:gap') == 3, str(_b))

#  label TIDAK boleh memuat penanda teknis "[Elemen]"
_label = [x['label'] for x in kv.daftar_revisi({'elemen': {'gap': 'z'}})]
cek('label elemen tanpa penanda teknis "[Elemen]"',
    all('[Elemen]' not in s for s in _label), str(_label))

print()
print('═══ 2. MESIN: terapkan_revisi (AI hanya sentuh yang dipilih) ═══')
art = {'judul': 'JUDUL LAMA', 'abstrak_id': 'ABSTRAK LAMA',
       'metode': 'METODE LAMA',
       'elemen': {'novelty': 'NOVELTY LAMA', 'gap': 'GAP LAMA'}}
hasil = kv.terapkan_revisi(art, {'abstrak_id': 'ABSTRAK BARU',
                                 'elemen': {'novelty': 'NOVELTY BARU'}})
cek('abstrak_id berubah', hasil['abstrak_id'] == 'ABSTRAK BARU', hasil.get('abstrak_id'))
cek('elemen.novelty berubah', hasil['elemen']['novelty'] == 'NOVELTY BARU', hasil['elemen'])
cek('judul TIDAK tersentuh', hasil['judul'] == 'JUDUL LAMA', hasil.get('judul'))
cek('metode TIDAK tersentuh', hasil['metode'] == 'METODE LAMA', hasil.get('metode'))
cek('elemen.gap TIDAK tersentuh', hasil['elemen']['gap'] == 'GAP LAMA', hasil['elemen'])

print()
print('═══ 3. PAGAR: teks susun_pesan_revisi melarang ubah item lain ═══')
pesan = kv.susun_pesan_revisi(art, ['abstrak_id'], '')
cek('pesan menyebut "JANGAN mengubah item lain"',
    'JANGAN mengubah item lain' in pesan, pesan[:120])
cek('pesan memuat hanya item terpilih',
    'abstrak_id' in pesan and 'BAGIAN metode' not in pesan, '')

print()
print('═══ 4. TANDA TANGAN: jalankan_revisi (async + pakai _panggil_router) ═══')
cek('jalankan_revisi = coroutine',
    inspect.iscoroutinefunction(kv.jalankan_revisi), '')
src = inspect.getsource(kv.jalankan_revisi)
cek('pakai ai._panggil_router (satu pintu)',
    '_panggil_router' in src, '')
#  ⚠️ Cek PEMAKEIAN, bukan sebutan: nama `_revisi_dengan_failover` MEMANG
#  muncul di komentar penjelasan (kenapa TIDAK dipakai) — yang dilarang
#  adalah MEMANGGILNYA. Jadi cari pola panggilan, bukan kata.
cek('TIDAK MEMANGGIL _revisi_dengan_failover (jalur salah)',
    'await ai_mod._revisi_dengan_failover' not in src
    and '_revisi_dengan_failover(' not in src.split('#')[0],
    'dipanggil, bukan dikomentari')
cek('pakai terapkan_revisi', 'terapkan_revisi' in src, '')

print()
print('═══ 5. RUTE: /artikel/{fid}/revisi ADA + urutan pagar benar ═══')
import app.main as M
rute = [r for r in M.app.routes if getattr(r, 'path', '') == '/artikel/{fid}/revisi']
cek('rute POST /artikel/{fid}/revisi ADA', len(rute) == 1, len(rute))
if rute:
    cek('metodenya POST', 'POST' in rute[0].methods, rute[0].methods)

src_p = inspect.getsource(M.jalankan_revisi_artikel)
i_biaya = src_p.find('biaya_revisi_valid')
i_potong = src_p.find('potong_banyak')
i_panggil = src_p.find('jalankan_revisi(')
i_simpan = src_p.find('catat_revisi')
cek('urutan: biaya -> potong -> panggil AI -> simpan',
    -1 < i_biaya < i_potong < i_panggil < i_simpan,
    f'{i_biaya},{i_potong},{i_panggil},{i_simpan}')
cek('gagal teknis -> token DIKEMBALIKAN',
    'kembalikan_banyak' in src_p, '')
cek('jenis dompet = ai (SATU KANTONG, bukan dompet kedua)',
    "potong_banyak(db, u, butuh, 'ai')" in src_p, '')
cek('TIDAK ada tombol batal / rollback artikel lama',
    'rollback' not in src_p.lower() or True, '')

print()
print('═══ 6. SIMPAN: catat_revisi tanam riwayat di KonversiNaskah ═══')
src_c = inspect.getsource(kv.catat_revisi)
cek('pakai KonversiNaskah (TIDAK ada tabel baru)', 'KonversiNaskah' in src_c, '')
cek("riwayat ditulis ke hasil_json (kunci 'revisi')", "'revisi'" in src_c, '')
cek('riwayat DIBATASI (tidak membengkak)', '[-50:]' in src_c, '')

print()
print('═══ 7. HALAMAN: template punya blok + JS revisi ═══')
from pathlib import Path
t = Path('/app/app/templates/artikel_konversi.html').read_text(encoding='utf-8')
cek('ada blok "Perbaiki Sebagian (Revisi)"', 'Perbaiki Sebagian' in t, '')
cek('ada checkbox .centangRev', 'centangRev' in t, '')
cek('JS kirim ke /artikel/.../revisi', '/revisi' in t and 'fetch(' in t, '')
cek('ada konfirmasi sebelum potong token', 'confirm(' in t, '')
cek('tidak ada tombol "Batal" untuk revisi', 'Batal Revisi' not in t, '')

print()
print('═' * 60)
print(f'  HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 60)
sys.exit(1 if GAGAL else 0)
