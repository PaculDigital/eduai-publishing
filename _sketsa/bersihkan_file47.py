"""SELAMATKAN naskah asli file 47 (65.826 kar) ke berkas, lalu bersihkan.

KENAPA: file 47 = berkas UJI milik akun uji `uji-berbayar-e2e@test.local`.
    Isi `versi_dokumen`-nya = JAWABAN AI (bukan naskah) → bikin uji palsu gagal
    & membingungkan. Tapi `section_state`-nya memuat NASKAH ASLI 65.826 kar
    (skripsi YOLO Universitas Mulawarman) — itu BAHAN UJI BERHARGA.
    Jadi: SIMPAN dulu ke `_contoh-dokumen/`, BARU hapus file 47 dari DB.

Yang dikerjakan:
    1. tulis naskah asli → `_contoh-dokumen/skripsi-s1/NASKAH-ASLI-file47.txt`
    2. hapus file 47 + semua yang menempel (versi/section/proses/revisi)
"""
import pathlib
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

# ── 1. SIMPAN naskah asli ────────────────────────────────────────────────
r = c.execute("select isi_teks from section_state where file_id=47 "
              "and section_id='__seluruh__'").fetchone()
if r and r['isi_teks']:
    out = pathlib.Path('/app/_contoh-dokumen/skripsi-s1/'
                       'NASKAH-ASLI-file47-65826kar.txt')
    out.write_text(r['isi_teks'], encoding='utf-8')
    print(f'✅ DISELAMATKAN: {out} ({len(r["isi_teks"]):,} kar)')
else:
    print('⚠️ section_state file 47 kosong — tidak ada yang diselamatkan')

# ── 2. HAPUS file 47 + yang menempel ────────────────────────────────────
print()
print('=== MENGHAPUS file 47 ===')
for t in ['versi_dokumen', 'section_state', 'revisi_history', 'sesi_edit']:
    kol = [d[1] for d in c.execute(f'PRAGMA table_info({t})')]
    if 'file_id' not in kol:
        continue
    n = c.execute(f'delete from {t} where file_id=47').rowcount
    print(f'  {t:18s} → {n} baris dihapus')

#  proses_ai: pakai kolom apa? cek dulu kolomnya.
kp = [d[1] for d in c.execute('PRAGMA table_info(proses_ai)')]
if 'file_id' in kp:
    n = c.execute('delete from proses_ai where file_id=47').rowcount
    print(f'  proses_ai          → {n} baris dihapus')

n = c.execute('delete from files where id=47').rowcount
print(f'  files              → {n} baris dihapus')
c.commit()

print()
print('=== SISA (harus 0) ===')
for t in ['versi_dokumen', 'section_state', 'revisi_history']:
    n = c.execute(f'select count(*) from {t} where file_id=47').fetchone()[0]
    print(f'  {t:18s} = {n}')
n = c.execute('select count(*) from files where id=47').fetchone()[0]
print(f'  files              = {n}')
c.close()
