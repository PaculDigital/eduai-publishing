"""GERBANG RAPI BAB (14 Okt 2026) — BERGIGI.

Menguji fungsi `rapi_bab()`: menyatukan penulisan bab supaya catatan
pembimbing bisa dicocokkan ke peta Jev (yang memakai angka).

Sifat yang dijaga:
  1. 'BAB I'/'bab i'/'BAB 1'  -> '1'  (semua bentuk jadi satu)
  2. 'BAB IV' -> '4' · 'bab iii' -> '3'
  3. Tidak dikenali -> DIKEMBALIKAN APA ADANYA (jangan menebak)
  4. Kosong -> kosong
  5. Dipakai di catat() + simpan_usulan() (pemanggil nyata)
  6. BERGIGI: matikan rapi_bab -> asersi 1-2 HARUS GAGAL

Dijalankan DI DALAM container (Rp 0, tanpa AI, tanpa DB produksi).
"""
import sys

sys.path.insert(0, '/app')

LULUS, GAGAL = [], []


def cek(nama, benar, bukti=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  OK  ' if benar else '  X   ') + nama +
          (('  [%s]' % bukti) if bukti else ''))


from app.pembimbing import rapi_bab      # noqa: E402

print('== UJI 1: BENTUK ROMAWI -> ANGKA ==')
kasus_romawi = [
    ('BAB I', '1'), ('bab i', '1'), ('Bab I', '1'),
    ('BAB II', '2'), ('bab ii', '2'),
    ('BAB III', '3'), ('bab iii', '3'), ('BAB III ', '3'),
    ('BAB IV', '4'), ('bab iv', '4'),
    ('BAB V', '5'), ('BAB VI', '6'), ('BAB VII', '7'),
]
for masuk, harap in kasus_romawi:
    hasil = rapi_bab(masuk)
    cek('%r -> %r' % (masuk, harap), hasil == harap, hasil)

print()
print('== UJI 2: SUDAH ANGKA (tidak diubah) ==')
for masuk in ('1', '2', '3', '4', ' 3 '):
    harap = masuk.strip()
    hasil = rapi_bab(masuk)
    cek('%r -> %r' % (masuk, harap), hasil == harap, hasil)

print()
print('== UJI 3: TIDAK DIKENALI -> APA ADANYA (JANGAN menebak) ==')
for masuk in ('BAB VIII', 'Tinjauan AI', 'Pendahuluan', 'BAB X',
              'Bab Metode'):
    hasil = rapi_bab(masuk)
    cek('%r tidak diubah jadi angka' % masuk, hasil == masuk, hasil)

print()
print('== UJI 4: KOSONG ==')
cek("'' -> ''", rapi_bab('') == '', repr(rapi_bab('')))
cek('None -> tidak meledak', rapi_bab(None) == '', repr(rapi_bab(None)))

print()
print('== UJI 5: SATU BENTUK untuk bab yang SAMA ==')
tiga_cara = ['BAB III', 'bab iii', 'BAB 3']
hasil_set = {rapi_bab(x) for x in tiga_cara}
cek('BAB III / bab iii / BAB 3 -> SATU nilai', len(hasil_set) == 1,
    str(hasil_set))

print()
print('== UJI 6: PEMANGGIL NYATA (kode, bukan tebakan) ==')
s_pemb = open('/app/app/pembimbing.py', encoding='utf-8').read()
s_asis = open('/app/app/asisten.py', encoding='utf-8').read()
cek('catat() memakai rapi_bab',
    'section_id=rapi_bab(section_id)' in s_pemb)
cek('simpan_usulan() memakai rapi_bab',
    "section_id=rapi_bab(u['bab']" in s_asis)
cek('asisten.py mengimpor rapi_bab',
    'daftar_berkas, rapi_bab' in s_asis)

print()
print('== UJI 7: COCOK KE PETA JEV (data nyata produksi) ==')
import json                                        # noqa: E402
import sqlite3                                     # noqa: E402

con = sqlite3.connect('/app/data/eduai.db')
r = con.execute('select peta_json from profil_dokumen where file_id=9'
                ).fetchone()
if r and r[0]:
    peta = json.loads(r[0])
    bab_peta = {str(x.get('bab') or '').strip()
                for x in (peta.get('daftar') or [])}
    print('   peta Jev fid=9 punya bab: %s' % sorted(bab_peta))
    rows = con.execute('''select id, section_id from catatan_pembimbing
                          where pembimbingan_id=112 order by id''').fetchall()
    cocok = gagal = 0
    for cid, sec in rows:
        hasil = rapi_bab(sec or '')
        if hasil in bab_peta:
            cocok += 1
            print('   id=%s %-10r -> %-4r OK' % (cid, sec or '', hasil))
        else:
            gagal += 1
            print('   id=%s %-10r -> %-4r (peta tak punya)'
                  % (cid, sec or '', hasil))
    cek('cocok >= 6 dari 8 (setelah dirapikan)', cocok >= 6,
        '%d cocok / %d gagal' % (cocok, gagal))
else:
    print('   (peta fid=9 tidak ada — lewati, jujur)')
con.close()

print()
print('== UJI GIGI: matikan rapi_bab -> asersi HARUS GAGAL ==')
import app.pembimbing as PB                        # noqa: E402
asli = PB.rapi_bab
PB.rapi_bab = lambda t: (t or '')                  # dipalsukan: tidak merapikan
try:
    gigi = PB.rapi_bab('BAB III')                  # lewat modul, BUKAN binding lokal
    cek('GIGI: dipalsukan -> tidak lagi "3"', gigi != '3', repr(gigi))
finally:
    PB.rapi_bab = asli
    cek('rapi_bab dipulihkan', PB.rapi_bab('BAB III') == '3')

print()
print('LULUS %d / GAGAL %d' % (len(LULUS), len(GAGAL)))
for g in GAGAL:
    print('   GAGAL:', g)
raise SystemExit(0 if not GAGAL else 1)
