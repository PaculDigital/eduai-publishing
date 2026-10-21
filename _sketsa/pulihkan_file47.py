"""Pulihkan file 47: kembalikan versi TERPAKAI ke v57 (4.522 kar) — 25Sep26.

KENAPA (ACC Bos "A"):
    C9 — bug "sukses palsu". DB produksi menyimpan v58 & v59 berisi **0 kar**,
    dan v59 berstatus `terpakai=1` → NASKAH MAHASISWA KOSONG.

    Pemilik file 47 = akun UJI (`uji-berbayar-e2e@test.local`), bukan mahasiswa
    nyata. Jadi aman dipulihkan.

YANG DILAKUKAN (hati-hati, bertahap):
    1. Hitung ulang & pastikan v57 memang versi BERISI terakhir.
    2. Set `terpakai=1` HANYA untuk v57, dan `terpakai=0` untuk versi kosong.
    3. JANGAN hapus apa pun — hapus = menghilangkan bukti (dan bisa menyesal).
       Versi kosong DIBIARKAN sebagai jejak.
    4. Tulis file .docx ulang? TIDAK di sini — cukup perbaiki rujukan versi,
       lalu verifikasi tampilan lewat potret.

WAJIB: pakai backup `_arsip/pre-pulih47-20260925/` kalau perlu dibalik.
"""
import sqlite3
import sys

DB = '/app/data/eduai.db'
FILE_ID = 47

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print('══ SEBELUM ══')
baris = [dict(x) for x in c.execute(
    'SELECT id, nomor, terpakai, length(isi) AS n FROM versi_dokumen '
    'WHERE file_id=? ORDER BY nomor', (FILE_ID,))]
for r in baris:
    print(f"  id {r['id']}  v{r['nomor']}  terpakai={r['terpakai']}  {r['n']:6d} kar")

# ── 1. Cari versi BERISI terakhir (yang punya isi nyata) ──────────────────
berisi = [r for r in baris if r['n'] > 0]
if not berisi:
    print('\n❌ TIDAK ADA versi berisi untuk file 47 — JANGAN diubah. Lapor Bos.')
    sys.exit(1)
target = max(berisi, key=lambda r: r['nomor'])
print(f"\n🎯 versi berisi terakhir = v{target['nomor']} ({target['n']} kar)")

terpakai_kini = [r for r in baris if r['terpakai']]
if terpakai_kini and terpakai_kini[0]['id'] == target['id']:
    print('✅ sudah benar — tidak ada yang perlu diubah.')
    sys.exit(0)

# ── 2. Pindahkan penanda terpakai ────────────────────────────────────────
c.execute('UPDATE versi_dokumen SET terpakai=0 WHERE file_id=?', (FILE_ID,))
c.execute('UPDATE versi_dokumen SET terpakai=1 WHERE id=?', (target['id'],))
c.commit()

print('\n══ SESUDAH ══')
for r in c.execute('SELECT id, nomor, terpakai, length(isi) AS n FROM versi_dokumen '
                   'WHERE file_id=? ORDER BY nomor', (FILE_ID,)):
    d = dict(r)
    tanda = '  ← TERPAKAI' if d['terpakai'] else ''
    print(f"  id {d['id']}  v{d['nomor']}  terpakai={d['terpakai']}  {d['n']:6d} kar{tanda}")

sisa = c.execute('SELECT count(*) FROM versi_dokumen WHERE file_id=? AND terpakai=1 '
                 'AND length(isi)=0', (FILE_ID,)).fetchone()[0]
print(f"\nversi KOSONG yang masih terpakai: {sisa}  (harus 0)")
print('✅ versi kosong DIBIARKAN sebagai bukti (tidak dihapus)')
