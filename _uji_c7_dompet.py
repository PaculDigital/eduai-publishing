"""GERBANG C7 — DOMPET "YANG KLIK = YANG BAYAR" (putusan Bos 29Sep26).

Uji 2 arah (standar Bos): SEHAT LULUS · KODE LAMA GAGAL.
Panggilan AI DIPALSUKAN (stub) → tidak memanggil model, tidak makan saldo.

Jalankan dari DALAM container, WAJIB pada salinan DB (bukan produksi):
  docker exec -e EDUAI_DATA_DIR=/tmp/c7_uji -e APP_ROOT=/app eduai-app \
      sh -c 'rm -rf /tmp/c7_uji && python3 /tmp/_uji_c7_dompet.py'

ARAH SEHAT (kode sekarang: pembayar = `u` yang klik):
  1. pembimbing klik → sumber=trial (trial PEMBIMBING terpakai)
  2. dompet PEMILIK TIDAK tersentuh (utuh 5)          ← inti C7
  3. klik ke-2 → saldo PEMBIMBING -1, pemilik tetap 5
  4. pesan jujur: "jatah gratis pertama" lalu "sisa N"
  5. pagar P2: AI gagal → saldo PEMBIMBING kembali utuh
  6. catatan masuk (C5) tetap jalan

ARAH RUSAK (simulasi kode LAMA `b_pemilik`): uji-1 GAGAL —
  sumber jadi 'saldo' + saldo PEMILIK terpotong → assertion 2 & 3 gagal.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

APP_ROOT = os.getenv('APP_ROOT', '/app')
sys.path.insert(0, APP_ROOT)

LULUS, GAGAL = 0, []


def cek(nama, kondisi):
    global LULUS
    if kondisi:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL.append(nama)
        print(f'  ❌ {nama}')


from app.config import DB_PATH                      # noqa: E402

#  PAGAR: jangan sampai uji ini menulis DB produksi.
if 'c7' not in str(DB_PATH) and os.getenv('UJI_C7') != '1':
    print(f'TOLAK: DB ({DB_PATH}) bukan salinan uji. '
          'Set EDUAI_DATA_DIR=/tmp/c7_uji dulu.')
    sys.exit(2)

from app import asisten as A                        # noqa: E402
from app import kolaborasi as K                     # noqa: E402
from app import saldo as S                          # noqa: E402
from app import models as M                         # noqa: E402
from app import pembimbing as P                     # noqa: E402

M.Base.metadata.create_all(M.engine)
db = M.SessionLocal()

EMAIL_PEM = 'c7-pemilik@uji.test'
EMAIL_PMB = 'c7-pembimbing@uji.test'

#  bersihkan sisa uji sebelumnya (idempoten)
for em in (EMAIL_PEM, EMAIL_PMB):
    for u in db.query(M.User).filter(M.User.email == em).all():
        db.query(M.Pembimbingan).filter(
            M.Pembimbingan.user_id == u.id).delete(synchronize_session=False)
        db.query(M.SaldoToken).filter(
            M.SaldoToken.user_id == u.id).delete(synchronize_session=False)
        db.query(M.Setelan).filter(
            M.Setelan.kunci == A.KUNCI_TRIAL.format(uid=u.id)).delete(
            synchronize_session=False)
        db.delete(u)
db.commit()

#  ── susun dunia uji ───────────────────────────────────────────────────────
pem = M.User(email=EMAIL_PEM, password_hash='x', role='client', paket='gratis')
pmb = M.User(email=EMAIL_PMB, password_hash='x', role='client', paket='gratis')
db.add_all([pem, pmb])
db.commit()
db.refresh(pem)
db.refresh(pmb)

#  pemilik: trial SUDAH terpakai + saldo 5  → kalau kode salah potong DIA,
#  angkanya bergerak dan uji GAGAL.
db.add(M.Setelan(kunci=A.KUNCI_TRIAL.format(uid=pem.id), nilai='1',
                 oleh='uji'))
#  pembimbing: trial BELUM terpakai + saldo 1
S.masuk(db, pem, 5, sumber='uji-c7', catatan='awal pemilik')
S.masuk(db, pmb, 1, sumber='uji-c7', catatan='awal pembimbing')
db.commit()

bim = M.Pembimbingan(
    user_id=pem.id, nama='Uji C7', identitas=EMAIL_PMB, wa='', email='',
    token_sidik=P.sidik_token(P.buat_token()), hari=7,
    kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=7))
db.add(bim)
db.commit()
db.refresh(bim)

#  ── palsukan AI (tanpa model nyata) ──────────────────────────────────────
TEKS = ('BAB I PENDAHULUAN\n1.1 Latar Belakang\n'
        'Penelitian ini mengkaji pengaruh motivasi terhadap kinerja. '
        'Sumber rujukan menunjukkan hasil berbeda. ') * 5
JAWAB = ('{"usulan":[{"bab":"BAB I","kutipan":"pengaruh motivasi",'
         '"catatan":"Perjelas alasan pemilihan topik ini."}]}')
from app import ai as AI                            # noqa: E402


async def _stub(user_msg, timeout, system=None):
    return JAWAB, {'model': 'uji-c7-stub'}


async def _gagal(user_msg, timeout, system=None):
    raise RuntimeError('uji: AI sengaja dibuat gagal')


A.naskah_bimbingan = lambda _db, _b: TEKS           # noqa: E731
AI._panggil_router = _stub

print('— kasus 1: pembimbing klik (trial milik PEMBIMBING) —')
h1 = asyncio.run(K.kolaborasi_asisten(bim.id, None, pmb, db))
sisa_pem_1 = S.sisa(db, pem)
sisa_pmb_1 = S.sisa(db, pmb)
cek('klik pertama sukses', h1.get('ok') is True)
cek('sumber biaya = trial (trial PEMBIMBING, bukan pemilik)',
    h1.get('sumber') == 'trial')
cek('DOMPET PEMILIK utuh 5 (inti C7)', sisa_pem_1 == 5)
cek('trial PEMBIMBING terpakai',
    not A.sisa_trial(db, pmb))
cek('catatan AI masuk (C5)', h1.get('dibuat', 0) >= 1)
cek('pesan jujur sebut jatah gratis',
    'jatah gratis pertama' in (h1.get('pesan') or ''))

print('— kasus 2: klik ke-2 → potong SALDO PEMBIMBING —')
h2 = asyncio.run(K.kolaborasi_asisten(bim.id, None, pmb, db))
cek('klik ke-2 sukses', h2.get('ok') is True)
cek('sumber biaya = saldo', h2.get('sumber') == 'saldo')
cek('SALDO PEMBIMBING terpotong 1 → 0', S.sisa(db, pmb) == 0)
cek('DOMPET PEMILIK tetap 5', S.sisa(db, pem) == 5)
cek('pesan sebut sisa saldo', 'sisa' in (h2.get('pesan') or ''))

print('— kasus 3: pagar P2 — AI gagal → uang pembimbing kembali —')
S.masuk(db, pmb, 1, sumber='uji-c7', catatan='isi ulang untuk P2')
AI._panggil_router = _gagal
h3 = asyncio.run(K.kolaborasi_asisten(bim.id, None, pmb, db))
cek('AI gagal → tidak dihitung sukses', h3.get('ok') is False)
cek('saldo PEMBIMBING kembali utuh 1', S.sisa(db, pmb) == 1)
cek('dompet pemilik tetap 5', S.sisa(db, pem) == 5)
AI._panggil_router = _stub

print('— kasus 4: pagar keamanan — bimbingan orang lain ditolak —')
asing = M.User(email='c7-asing@uji.test', password_hash='x', role='client',
               paket='gratis')
db.add(asing)
db.commit()
db.refresh(asing)
b_asing = M.Pembimbingan(
    user_id=asing.id, nama='Asing', identitas='bukan-kamu@x.com', wa='',
    email='', token_sidik=P.sidik_token(P.buat_token()), hari=7,
    kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=7))
db.add(b_asing)
db.commit()
db.refresh(b_asing)
h4 = asyncio.run(K.kolaborasi_asisten(b_asing.id, None, pmb, db))
cek('bimbingan orang lain → ditolak', h4.get('ok') is False)

#  rapikan
db.query(M.CatatanPembimbing).filter(
    M.CatatanPembimbing.pembimbingan_id.in_([bim.id, b_asing.id])).delete(
    synchronize_session=False)
for bb in (bim, b_asing):
    db.delete(bb)
for u in (pem, pmb, asing):
    db.query(M.SaldoToken).filter(M.SaldoToken.user_id == u.id).delete(
        synchronize_session=False)
    db.query(M.Setelan).filter(
        M.Setelan.kunci == A.KUNCI_TRIAL.format(uid=u.id)).delete(
        synchronize_session=False)
    db.delete(u)
db.commit()
db.close()

print()
print(f'HASIL: {LULUS} LULUS / {len(GAGAL)} GAGAL')
if GAGAL:
    print('GAGAL:', GAGAL)
    sys.exit(1)
print('GERBANG C7 DOMPET LULUS ✅')
