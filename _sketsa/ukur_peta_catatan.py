"""UKUR (Rp 0, tanpa AI): apakah catatan pembimbing bisa dipetakan
ke peta Jev yang SUDAH tersimpan?

Bentuk peta Jev (terbaca dari DB):
  {'jumlah': 12, 'daftar': [{'id':'B1.0-01','bab':'1','subbab':'',
     'judul_bab':'PENDAHULUAN','judul_subbab':'','masalah':'...'}, ...]}

Uji:
  A. AKURASI NAMA BAB — 'BAB III' vs 'BAB 3' vs 'bab iii' vs peta
  B. AKURASI TEKS     — teks_asli ditemukan di sub-bab yang benar?
"""
import json
import sqlite3
import sys

sys.path.insert(0, '/app')
DB = '/app/data/eduai.db'
ROMAWI = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII'}


def peta(fid):
    con = sqlite3.connect(DB)
    r = con.execute('select peta_json from profil_dokumen where file_id=?',
                    (fid,)).fetchone()
    con.close()
    if r and r[0]:
        try:
            return json.loads(r[0])
        except Exception:
            return None
    return None


def bab_dari_peta(d):
    """{nomor_bab: judul} dari peta Jev."""
    out = {}
    for x in (d or {}).get('daftar') or []:
        b = str(x.get('bab') or '').strip()
        if b:
            out.setdefault(b, x.get('judul_bab') or '')
    return out


def rapikan(s):
    """'BAB III'/'bab 3'/'BAB 3' -> nomor bab '3'."""
    t = (s or '').strip().upper().replace('BAB', '').strip()
    if t.isdigit():
        return t
    for n, r in ROMAWI.items():
        if t == r:
            return str(n)
    return t


print('=' * 64)
print('  A. AKURASI NAMA BAB')
print('=' * 64)
d = peta(9)
peta_bab = bab_dari_peta(d)
print('   peta Jev fid=9: %s bab -> %s' % (len(peta_bab), peta_bab))
print()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cats = con.execute('''select id, section_id, isi from catatan_pembimbing
                      where pembimbingan_id = 112 order by id''').fetchall()
print('   9 catatan pembimbing:')
print('   %-5s %-12s %-8s %s' % ('id', 'section_id', 'rapi', 'cocok dgn peta?'))
persis = kasar = gagal = 0
for c in cats:
    asli = (c['section_id'] or '')
    rapi = rapikan(asli)
    a = asli.strip().upper()
    if a in [(('BAB ' + b).upper()) for b in peta_bab] or a in peta_bab:
        hasil = 'YA (persis)'
        persis += 1
    elif rapi in peta_bab:
        hasil = 'YA (setelah dirapikan -> BAB %s = %s)' % (
            rapi, peta_bab.get(rapi, '')[:18])
        kasar += 1
    else:
        hasil = 'TIDAK (peta tak punya bab %r)' % rapi
        gagal += 1
    print('   %-5s %-12r %-8r %s' % (c['id'], asli, rapi, hasil))
print()
print('   ⇒ PERSIS        : %d' % persis)
print('   ⇒ SETELAH DIRAPIKAN: %d' % kasar)
print('   ⇒ GAGAL         : %d' % gagal)
print('   ⇒ TOTAL COCOK   : %d / %d' % (persis + kasar, len(cats)))

print()
print('=' * 64)
print('  B. AKURASI TEKS (teks_asli -> sub-bab)')
print('=' * 64)
teks = ('Data BPS menunjukkan 42 persen desa belum terjangkau internet '
        'cepat')
print('   teks_asli id=180: %r' % teks[:58])
print()
print('   PENTING: peta Jev TIDAK menyimpan TEKS naskah —')
print('            hanya bab/judul/masalah. Jadi mencocokkan teks ke')
print('            peta butuh TEKS NASKAH. Mari cek:')
print('     - berapa catatan yang punya teks_asli?')
con2 = sqlite3.connect(DB)
n_ada = con2.execute('''select count(*) from catatan_pembimbing
                        where teks_asli is not null and length(teks_asli)>5'''
                     ).fetchone()[0]
n_tot = con2.execute('select count(*) from catatan_pembimbing').fetchone()[0]
print('       ADA teks_asli : %d' % n_ada)
print('       TANPA teks    : %d' % (n_tot - n_ada))
print('       TOTAL         : %d' % n_tot)
con2.close()
