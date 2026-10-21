"""PERIKSA dampak hapus file 47 — apa saja yang menempel padanya.

KENAPA: sebelum menghapus, harus tahu apa yang ikut terhapus:
    versi_dokumen, section_state, proses_ai, profil_dokumen, revisi_history,
    pembimbingan_berkas, catatan_pembimbing.
"""
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

print('=== ISI FILE 47 (nama & pemilik) ===')
r = c.execute('select f.id,f.nama,f.user_id,u.email from files f '
              'join users u on u.id=f.user_id where f.id=47').fetchone()
print(f"  file {r['id']} | {r['nama']} | pemilik={r['email']} (id {r['user_id']})")
print()

TABEL = ['versi_dokumen', 'section_state', 'proses_ai', 'profil_dokumen',
         'revisi_history', 'pembimbingan_berkas', 'catatan_pembimbing',
         'sesi_edit']
print('=== YANG MENEMPEL DI FILE 47 ===')
for t in TABEL:
    try:
        kol = [d[1] for d in c.execute(f'PRAGMA table_info({t})')]
        if 'file_id' not in kol:
            print(f'  {t:22s} (tidak punya kolom file_id — dilewati)')
            continue
        n = c.execute(f'select count(*) from {t} where file_id=47').fetchone()[0]
        print(f'  {t:22s} = {n}')
    except Exception as e:                                     # noqa: BLE001
        print(f'  {t:22s} (galat: {e})')
