"""GERBANG UJI T5.2 — ASISTEN PEMBIMBING (ACC Bos 27Sep26).

Uji 2 arah (standar Bos): SEHAT LULUS + DIRUSAK GAGAL.
Jalan dari DALAM container (python + DB produksi tersedia):
  docker exec -e TOKEN_UJI=... -e EMAIL_UJI=... eduai-app \
      sh -c 'cd /app && PYTHONPATH=/app python scripts/uji_asisten.py'

Kasus:
  1. urai_usulan JSON sah → terurai
  2. dirusak: JSON rusak / kosong / bukan list → None (biaya dikembalikan)
  3. dirusak: usulan tanpa catatan → dibuang
  4. duplikat catatan → dibuang
  5. biaya: akun baru → trial (gratis)
  6. biaya: trial sudah terpakai → saldo dipotong 1
  7. dirusak: saldo 0 & trial habis → ditolak RAMAH
  8. simpan_usulan: usulan LANGSUNG jadi catatan pembimbing (C5)
  9. dirusak: kutipan karangan → teks_asli kosong (tanpa sorotan palsu)
 10. dirusak: bimbingan orang lain → ditolak
 11. AI NYATA: 1 panggilan ujung-ke-ujung (ukur waktu + nama model)
"""
import asyncio
import os
import sys

sys.path.insert(0, '/app')
LULUS, GAGAL = 0, []


def cek(nama, kondisi):
    global LULUS
    if kondisi:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL.append(nama)
        print(f'  ❌ {nama}')


from app import asisten as A                      # noqa: E402
from app.models import (SessionLocal, Pembimbingan, User,  # noqa: E402
                        CatatanPembimbing)
from app import pembimbing as P                   # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

db = SessionLocal()

print('— kasus 1: JSON sah —')
j = '{"usulan":[{"bab":"BAB I","kutipan":"latar belakang penelitian ini","catatan":"Perjelas alasan pemilihan topik."}]}'
h = A.urai_usulan(j)
cek('terurai 1 usulan', h is not None and len(h) == 1
    and h[0]['bab'] == 'BAB I')

print('— kasus 2: dirusak —')
cek('JSON rusak → None', A.urai_usulan('maaf aku bingung {{') is None)
cek('kosong → None', A.urai_usulan('') is None)
cek('usulan bukan list → None', A.urai_usulan('{"usulan": "habis"}') is None)

print('— kasus 3/4: filter —')
h = A.urai_usulan('{"usulan":[{"bab":"X","catatan":""},'
                  '{"bab":"Y","catatan":"sama"},{"bab":"Z","catatan":"sama"}]}')
cek('usulan tanpa catatan dibuang + duplikat dibuang',
    h is not None and len(h) == 1)

print('— kasus 5/6/7: biaya —')
u = db.scalars(__import__('sqlalchemy').select(User)
               .where(User.email == os.getenv('EMAIL_UJI', ''))).first()
if u is None:
    print('set EMAIL_UJI')
    sys.exit(2)

#  rapikan setelan trial uji SEBELUM uji (idempoten)
kunci = A.KUNCI_TRIAL.format(uid=u.id)
for s in db.scalars(__import__('sqlalchemy').select(__import__('app.models', fromlist=['Setelan']).Setelan)
                    .where(__import__('app.models', fromlist=['Setelan']).Setelan.kunci == kunci)).all():
    db.delete(s)
db.commit()

b = A.biaya_untuk(db, u)
cek('akun tanpa trial → gratis', b == {'pakai_trial': True, 'butuh': 0})

bayar = A.potong_biaya(db, u)
cek('trial terpakai', bayar.get('ok') and bayar.get('sumber') == 'trial')
cek('trial tak disodorkan lagi', not A.sisa_trial(db, u))

from app import saldo as _saldo                   # noqa: E402
sisa_awal = _saldo.sisa(db, u)
bayar2 = A.potong_biaya(db, u)
cek('sesudah trial → potong 1 dari saldo',
    bayar2.get('ok') and bayar2.get('sumber') == 'saldo'
    and bayar2.get('sisa') == sisa_awal - 1)
A.kembalikan_biaya(db, u, 'saldo')
cek('kembalikan biaya = sisa awal', _saldo.sisa(db, u) == sisa_awal)

#  dirusak: saldo 0 → tolak ramah
saldo_baru = None
from app.models import SaldoToken                 # noqa: E402
#  catat saldo jadi 0 via pakai sebanyak sisa (hanya kalau ada)
if sisa_awal > 0:
    _saldo.pakai(db, u, sisa_awal, sumber='uji-nolkan')
tolak = A.potong_biaya(db, u)
cek('saldo 0 + trial habis → ditolak ramah',
    not tolak.get('ok') and 'Token Revisi' in tolak.get('pesan', '')
    and 'AddOn' in tolak.get('pesan', ''))
#  kembalikan saldo untuk uji berikutnya
_saldo.kembalikan(db, u, sisa_awal, sumber='uji-kembalikan')

print('— siapkan bimbingan uji —')
token = P.buat_token()
bim = Pembimbingan(user_id=u.id, nama='Uji T52', identitas='', wa='', email='',
                   token_sidik=P.sidik_token(token), hari=7,
                   kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=7))
db.add(bim)
db.commit()
db.refresh(bim)

print('— kasus 8/9: simpan_usulan —')
usulan = [
    {'bab': 'BAB I', 'kutipan': '', 'catatan': 'Uji catatan tanpa kutipan.'},
]
n = A.simpan_usulan(db, bim, usulan)
rows = db.scalars(__import__('sqlalchemy').select(CatatanPembimbing)
                  .where(CatatanPembimbing.pembimbingan_id == bim.id)).all()
cek('usulan masuk sebagai catatan pembimbing (C5)',
    n == 1 and len(rows) == 1 and rows[0].dari_pembimbing == 1
    and rows[0].warna == 'kuning')

db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == bim.id).delete()
db.commit()

print('— kasus 10: dirusak, bimbingan orang lain —')
from app import kolaborasi as K                   # noqa: E402
#  Pembuat kebingungan: pemilik "asing" WAJIB BUKAN u. Produksi cuma punya
#  1 akun → buat user sementara, lalu HAPUS bersih setelah uji.
user_baru = User(email='uji-asing-t52@eduai.test', password_hash='x',
                 role='client', paket='gratis')
db.add(user_baru)
db.commit()
db.refresh(user_baru)
b_asing = Pembimbingan(user_id=user_baru.id,
                       nama='Asing', identitas='orang-lain@x.com',
                       wa='', email='', token_sidik=P.sidik_token(P.buat_token()),
                       hari=7, kedaluwarsa=datetime.now(timezone.utc)
                       + timedelta(days=7))
db.add(b_asing)
db.commit()
db.refresh(b_asing)
dapat = K._bimbingan_milik(db, b_asing.id, u)     # noqa: SLF001
db.delete(b_asing)
db.commit()
db.delete(user_baru)
db.commit()
cek('bimbingan milik orang lain → None (ditolak)', dapat is None)

print('— kasus 11: AI NYATA ujung-ke-ujung —')
#  berkas naskah uji: pakai _contoh naskah pendek buatan
teks_uji = ('BAB I PENDAHULUAN\n1.1 Latar Belakang\n'
            'Penelitian ini mengkaji pengaruh motivasi terhadap kinerja '
            'karyawan pada kantor kelurahan. Penelitian sebelumnya menunjukkan '
            'bahwa motivasi berpengaruh signifikan. ') * 30
import types                                      # noqa: E402
from app.rute_pembimbing import _isi_naskah       # noqa: E402


def _tiruan(db_, bk):
    return teks_uji


#  suntik naskah tiruan TANPA menulis DB produksi: monyet-tempel fungsi baca
A.naskah_bimbingan = (lambda db_, b_: teks_uji)   # noqa: SLF001

hasil = asyncio.run(A.kerjakan(db, bim, u))
print('   hasil:', {k: hasil.get(k) for k in
                    ('ok', 'dibuat', 'sumber', 'model', 'detik')})
cek('AI nyata: ok=True', hasil.get('ok') is True)
cek('AI nyata: catatan masuk (0..8)', 0 <= hasil.get('dibuat', -1) <= 8)
cek('AI nyata: model tercatat', bool(hasil.get('model')))
cek('AI nyata: waktu < 120 dtk', hasil.get('detik', 999) < 120)
#  jejak wajib: model ASLI (bukan nama combo)
print('   model asli:', hasil.get('model'), '| sumber biaya:',
      hasil.get('sumber'), '| detik:', hasil.get('detik'))

print('— rapikan data uji —')
db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == bim.id).delete()
db.delete(bim)
db.commit()
db.close()

print()
print(f'HASIL: {LULUS} LULUS / {len(GAGAL)} GAGAL')
if GAGAL:
    print('GAGAL:', GAGAL)
    sys.exit(1)
print('GERBANG T5.2 LULUS ✅')
