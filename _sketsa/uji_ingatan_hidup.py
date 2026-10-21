"""BUKTI INGATAN JALAN — 3 uji berurutan (LANGKAH 2+3+1).

Uji A: revisi PERTAMA '1.2' → ingatan harus tercatat '1.2' (BUKAN __seluruh__)
Uji B: revisi KEDUA '1.2'   → prompt HARUS memuat CATATAN REVISI SEBELUMNYA
Uji C: catat_revisi tidak lagi gagal walau naskah dipotong (naskah_utuh)
"""
import asyncio, sys, os, glob
sys.path.insert(0, '/app')
import sqlalchemy as sa
from app.models import SessionLocal, User, FileBerkas
from app import ai as mod_ai
from app.config import UPLOAD_DIR

DITANGKAP = {}


async def pengganti(user_msg, jml_komentar):
    DITANGKAP['msg'] = user_msg
    return ('[PROFIL]\nkeperluan: uji\n\nDRAF:\nDraf uji (tidak dipakai).',
            'uji-palsu', {'token_in': 111, 'token_out': 222, 'model': 'uji'})


mod_ai._revisi_dengan_failover = pengganti


class L:
    def tahap(self, *a, **k): pass
    def menulis(self, *a, **k): pass


class Req:
    def __init__(self, d): self._d = d
    async def json(self): return self._d


def hitung(db, sql):
    return db.execute(sa.text(sql)).scalar()


async def main():
    db = SessionLocal()
    u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
    fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    naskah = mod_ai._teks_dari_berkas(
        UPLOAD_DIR / str(u.id) / fb.nama_simpan, fb.nama).strip()
    print(f'naskah: {fb.nama} · {len(naskah):,} kar · file_id={fb.id}')
    print(f'ingatan AWAL: section_state='
          f'{hitung(db, "SELECT COUNT(*) FROM section_state")} · '
          f'revisi_history={hitung(db, "SELECT COUNT(*) FROM revisi_history")}')

    for putaran in (1, 2):
        print(f'\n═══ UJI {chr(64+putaran)}: revisi putaran ke-{putaran} (bab=1.2) ═══')
        DITANGKAP.clear()
        await mod_ai._revisi_kerja(
            Req({'naskah': naskah, 'bab': '1.2',
                 'komentar': ['Perbaiki kalimat rumusan masalah ini.']}),
            u, db, _lapor=L())
        msg = DITANGKAP.get('msg', '')
        print(f'  pesan dikirim: {len(msg):,} kar')
        print(f'  ada blok konteks tetangga : '
              f'{"✓" if "BAGIAN SEBELUMNYA" in msg else "—"}')
        ada = 'CATATAN REVISI SEBELUMNYA' in msg
        print(f'  ada CATATAN REVISI SEBELUMNYA : {"✓" if ada else "—"} '
              f'{"← INGATAN DIPAKAI!" if ada else "(wajar di putaran 1)"}')
        if ada:
            i = msg.index('CATATAN REVISI SEBELUMNYA')
            print(f'      isi: {msg[i:i+150]!r}')

    print('\n═══ HASIL AKHIR INGATAN ═══')
    print(f'  section_state  : '
          f'{hitung(db, "SELECT COUNT(*) FROM section_state")} baris')
    print(f'  revisi_history : '
          f'{hitung(db, "SELECT COUNT(*) FROM revisi_history")} baris')
    for r in db.execute(sa.text(
            'SELECT id, file_id, section_id, section_title, char_count, '
            'jenis_revisi FROM section_state ORDER BY id')):
        print(f'    → [{r[0]}] file={r[1]} sec={r[2]!r} {r[3]!r} '
              f'{r[4]} kar jenis={r[5]}')
    for r in db.execute(sa.text(
            'SELECT id, section_id, intent, token_in, token_out '
            'FROM revisi_history ORDER BY id')):
        print(f'    hist [{r[0]}] sec={r[1]!r} {r[2]} tok={r[3]}/{r[4]}')
    db.close()

asyncio.run(main())
