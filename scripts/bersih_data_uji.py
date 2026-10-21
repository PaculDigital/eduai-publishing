"""BERSIH-BERSIH data uji (27Sep26) — ACC Bos: semua bau uji.

Urutan aman FK: tautan pembimbingan_berkas → catatan_pembimbing →
pembimbingan → notifikasi uji → saldo uji → files.
File 60 (naskah asli Fazri) DIPERTAHANKAN.
Backup DB dulu ke _arsip.
"""
import shutil
from pathlib import Path

from sqlalchemy import text
from app.models import SessionLocal

db = SessionLocal()
q = lambda s: db.execute(text(s))

# 0. backup DB sebelum hapus
sumber = Path('/app/data/eduai.db')
tujuan = Path('/app/data/backup-bersih-27sep.db')
if sumber.exists() and not tujuan.exists():
    shutil.copy2(sumber, tujuan)
    print('backup DB →', tujuan, tujuan.stat().st_size, 'byte')

# Urutan FK yang BENAR (baca DDL 27Sep):
#   catatan.induk_id→catatan; catatan.berkas_id→pembimbingan_berkas;
#   pembimbingan_berkas→pembimbingan & files;
#   proses_ai/profil_dokumen→files.
q("DELETE FROM catatan_pembimbing WHERE isi LIKE '%Uji%' "
  "OR pembimbingan_id <= 8 OR berkas_id <= 6 OR penulis_id <= 8")
q("DELETE FROM pembimbingan_berkas WHERE pembimbingan_id <= 8")
q("DELETE FROM pembimbingan WHERE id <= 8")
q("DELETE FROM notifikasi WHERE jenis IN ('pembimbing_diundang',"
  "'hasil_ai_siap')")
q("DELETE FROM saldo_token WHERE catatan LIKE '%uji%' "
  "OR sumber LIKE '%uji%'")
q("DELETE FROM proses_ai WHERE file_id IN (56,57,58,59,61)")
q("DELETE FROM revisi_history WHERE file_id IN (56,57,58,59,61)")
q("DELETE FROM versi_dokumen WHERE file_id IN (56,57,58,59,61)")
q("DELETE FROM section_state WHERE file_id IN (56,57,58,59,61)")
q("DELETE FROM notifikasi WHERE jenis IN ('pembimbing_diundang',"
  "'hasil_ai_siap') OR file_id IN (56,57,58,59,61)")
q("DELETE FROM profil_dokumen WHERE file_id IN (56,57,58,59,61)")
q("DELETE FROM pembimbingan_berkas WHERE file_id IN (56,57,58,59,61)")
q("DELETE FROM files WHERE id IN (56,57,58,59,61)")
db.commit()

# verifikasi sisa
for label, sql in [
    ('bimbingan uji sisa', "SELECT COUNT(*) FROM pembimbingan "
                           "WHERE nama LIKE '%Uji%'"),
    ('catatan uji sisa', "SELECT COUNT(*) FROM catatan_pembimbing "
                         "WHERE isi LIKE '%Uji%'"),
    ('file 60 masih ada', "SELECT id, nama FROM files WHERE id=60"),
    ('file uji sisa', "SELECT COUNT(*) FROM files "
                      "WHERE id IN (56,57,58,59,61)"),
    ('saldo uji sisa', "SELECT COUNT(*) FROM saldo_token "
                       "WHERE catatan LIKE '%uji%' OR sumber LIKE '%uji%'"),
    ('notifikasi uji sisa', "SELECT COUNT(*) FROM notifikasi WHERE jenis "
                            "IN ('pembimbing_diundang','hasil_ai_siap')"),
]:
    print(label, '→', q(sql).fetchall())
