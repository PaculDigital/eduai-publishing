#!/usr/bin/env python3
"""UJI LONCENG: proses GAGAL harus MUNCUL di lonceng (akar 17Sep26).

Sebelum perbaikan: `belum_dibaca()` hanya menyaring status 'selesai' →
proses gagal tidak pernah muncul, mahasiswa tidak diberi tahu.
"""
import sys
sys.path.insert(0, '/app')
from app.models import SessionLocal, ProsesAI
from app import proses as P
from sqlalchemy import select

lulus = gagal = 0


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  ✅ {nama} {bukti}')
    else:
        gagal += 1
        print(f'  ❌ {nama} {bukti}')


db = SessionLocal()
KODE_OK = 'UJI-LONCENG-SELESAI'
KODE_NO = 'UJI-LONCENG-GAGAL'

# bersihkan sisa
for k in (KODE_OK, KODE_NO):
    p = db.execute(select(ProsesAI).where(ProsesAI.kode == k)).scalar_one_or_none()
    if p:
        db.delete(p)
db.commit()

# 1) proses SELESAI
db.add(ProsesAI(kode=KODE_OK, user_id=5, status='menunggu', tahap=P.TAHAP_MENUNGGU))
# 2) proses GAGAL — sekaligus sudah pernah 'dibaca' (kasus paling keras)
db.add(ProsesAI(kode=KODE_NO, user_id=5, status='menunggu', tahap=P.TAHAP_MENUNGGU,
                dibaca=1))
db.commit()
db.close()

P.tandai_selesai(KODE_OK, hasil='x', model_ai='uji')
P.tandai_gagal(KODE_NO, 'RuntimeError: provider AI tidak merespons')

db = SessionLocal()
daftar = P.belum_dibaca(db, 5)
kode_ada = {x.kode for x in daftar}
print(f'\n=== LONCENG user 5 ({len(daftar)} item) ===')

cek('proses SELESAI masuk lonceng', KODE_OK in kode_ada)
cek('proses GAGAL masuk lonceng', KODE_NO in kode_ada,
    '(DULU TIDAK MUNCUL — ini akar yang ditutup)')

# pesan gagal harus menyebut kuota dikembalikan (inti kepercayaan)
pg = next((x for x in daftar if x.kode == KODE_NO), None)
if pg:
    try:
        r = P.ringkas(pg)
        # ⚠️ 17Sep26: cari AKAR kata, bukan kata utuh. Versi lama mencari
        # "dikembalikan" padahal kalimat barunya memakai "kembalikan" —
        # skrip uji jadi GAGAL PALSU. Pelajaran: pencocokan kata di uji
        # harus tahan perubahan imbuhan.
        cek('pesan gagal menyertakan jalan keluar',
            'kembali' in (r.get('pesan') or '').lower(),
            f'→ "{r["pesan"][:90]}"')
        cek('status terkirim = gagal', r.get('status') == 'gagal')
        #  Galat teknis mentah TIDAK boleh bocor ke mahasiswa.
        bocor = [k for k in ('RuntimeError', 'Traceback', 'provider',
                             'HTTP 5', 'KeyError')
                 if k.lower() in (r.get('pesan') or '').lower()]
        cek('galat teknis tidak bocor ke pesan', not bocor,
            f'→ BOCOR: {bocor}' if bocor else '')
    except Exception as e:
        gagal += 1
        print(f'  ❌ ringkas() error: {type(e).__name__}: {e}')

# cek `dibaca` direset walau tadinya 1
pg2 = db.execute(select(ProsesAI).where(ProsesAI.kode == KODE_NO)).scalar_one_or_none()
cek('tandai_gagal MENYET ULANG dibaca=0', pg2 is not None and pg2.dibaca == 0,
    f'(nilai={pg2.dibaca if pg2 else "?"})')

# bersihkan
for k in (KODE_OK, KODE_NO):
    p = db.execute(select(ProsesAI).where(ProsesAI.kode == k)).scalar_one_or_none()
    if p:
        db.delete(p)
db.commit()
db.close()

print(f'\nHASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
