"""BERSIHKAN USER DUMMY (id 4,5,6,7,8) + JEJAK AUDIT — 26Sep26.

Sesuai skill cascade-delete-sqlite:
- PRAGMA foreign_keys=ON sebagai tripwire (salah urutan = gagal, bukan yatim)
- urutan: anak file → files → anak user → pembimbingan berantai → folders → users
- jejak audit JSON (berapa baris per tabel)
- verifikasi yatim DUA ARAH di akhir
"""
import json
import sqlite3

UIDS = (4, 5, 6, 7, 8)
DB = '/app/data/eduai.db'

db = sqlite3.connect(DB)
db.execute('PRAGMA foreign_keys=ON')
jejak = {}

def ukur(sql, params=()):
    return db.execute(sql, params).fetchone()[0]

def hapus(tabel, where, params):
    n = db.execute(f'DELETE FROM {tabel} WHERE {where}', params).rowcount
    if n:
        jejak[tabel] = jejak.get(tabel, 0) + n
    return n

q_uid = ','.join('?' * len(UIDS))

# ── 0. kondisi awal ──
awal = {
    'users': ukur('SELECT COUNT(*) FROM users'),
    'files': ukur('SELECT COUNT(*) FROM files'),
    'files_dummy': ukur(f'SELECT COUNT(*) FROM files WHERE user_id IN ({q_uid})', UIDS),
    'pembimbingan': ukur('SELECT COUNT(*) FROM pembimbingan'),
    'catatan_pembimbing': ukur('SELECT COUNT(*) FROM catatan_pembimbing'),
}

# ── 1. rantai pembimbingan (anak paling dalam dulu) ──
# kolom pemilik user di pembimbingan — introspeksi, jangan menebak
fk = db.execute('PRAGMA foreign_key_list(pembimbingan)').fetchall()
kol_user = [r[3] for r in fk if r[2] == 'users']
assert kol_user, 'pembimbingan tak punya FK ke users?!'
kol_user = kol_user[0]

ids_pb = [r[0] for r in db.execute(
    f'SELECT id FROM pembimbingan WHERE {kol_user} IN ({q_uid})', UIDS).fetchall()]
q_pb = ','.join('?' * len(ids_pb)) if ids_pb else 'NULL'

# catatan: anak berantai (induk self-ref) → hapus by induk dulu, lalu sisanya
hapus('catatan_pembimbing',
      f'induk_id IN (SELECT id FROM catatan_pembimbing WHERE pembimbingan_id IN ({q_pb}))',
      ids_pb)
hapus('catatan_pembimbing', f'berkas_id IN (SELECT id FROM pembimbingan_berkas WHERE pembimbingan_id IN ({q_pb}))', ids_pb)
hapus('catatan_pembimbing', f'pembimbingan_id IN ({q_pb})', ids_pb)
hapus('pembimbingan_berkas', f'pembimbingan_id IN ({q_pb})', ids_pb)
hapus('pembimbingan', f'{kol_user} IN ({q_uid})', UIDS)

# ── 2. anak per-FILE (sebelum files) ──
ANAK_FILE = ('versi_dokumen', 'sesi_edit', 'belajar_naskah', 'profil_dokumen',
             'section_state', 'revisi_history', 'proses_ai', 'pembatalan_kuota')
for t in ANAK_FILE:
    hapus(t, f'file_id IN (SELECT id FROM files WHERE user_id IN ({q_uid}))', UIDS)

# ── 3. files (induk dari anak file) ──
hapus('files', f'user_id IN ({q_uid})', UIDS)

# ── 4. anak per-USER ──
ANAK_USER = ('versi_dokumen', 'pemakaian_ai', 'pembelian_addon', 'sesi_edit',
             'belajar_naskah', 'transaksi', 'profil_dokumen', 'section_state',
             'revisi_history', 'proses_ai', 'pembatalan_kuota', 'notifikasi',
             'saldo_token')
for t in ANAK_USER:
    hapus(t, f'user_id IN ({q_uid})', UIDS)

# ── 5. folders (dirujuk files.folder_id — files sudah bersih) ──
hapus('folders', f'user_id IN ({q_uid})', UIDS)

# ── 6. users (induk terakhir) ──
hapus('users', f'id IN ({q_uid})', UIDS)

db.commit()

# ── 7. verifikasi yatim DUA ARAH ──
yatim = {}
tabel = [r[0] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
for t in tabel:
    for fkrow in db.execute(f'PRAGMA foreign_key_list({t})').fetchall():
        kol, ref_t, ref_k = fkrow[3], fkrow[2], fkrow[4]
        alias = f'{t}_yatim'
        n = db.execute(
            f'SELECT COUNT(*) FROM {t} AS {alias} LEFT JOIN {ref_t} '
            f'ON {alias}.{kol}={ref_t}.{ref_k} '
            f'WHERE {alias}.{kol} IS NOT NULL AND {ref_t}.{ref_k} IS NULL').fetchone()[0]
        if n:
            yatim[f'{t}.{kol}->{ref_t}'] = n

akhir = {
    'users': ukur('SELECT COUNT(*) FROM users'),
    'files': ukur('SELECT COUNT(*) FROM files'),
    'pembimbingan': ukur('SELECT COUNT(*) FROM pembimbingan'),
    'catatan_pembimbing': ukur('SELECT COUNT(*) FROM catatan_pembimbing'),
    'sisa_user_ids': [r[0] for r in db.execute('SELECT id FROM users ORDER BY id')],
}

db.execute('VACUUM')
db.commit()
db.close()

print(json.dumps({'awal': awal, 'hapus': jejak, 'akhir': akhir,
                  'yatim': yatim}, ensure_ascii=False, indent=1))
