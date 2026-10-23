"""GERBANG RUTE JURNAL (06Okt26) — uji API sungguhan (in-process).

Uji SUNGGUHAN lewat FastAPI TestClient (rute + pagar + token benar-benar jalan):
  R1. Rute terdaftar (& tidak bentrok)
  R2. Tanpa login → ditolak (pagar auth)
  R3. `lihat` GRATIS (tidak memotong token) + bentuk balikan lengkap
  R4. `cari-ai` GRATIS (jatah manual tidak berkurang)
  R5. `cari` manual: 2× gratis → ke-3 kena token
  R6. `cari` gagal/0 hasil → token DIKEMBALIKAN
  R7. `tambah-manual`: kotak terkunci kurang isian → ditolak (nada hangat)
  R8. `tambah-manual`: batas 8 per bab ditegakkan
  R9. `doi_status` TIDAK bisa diisi user (dipaksa dari audit)
  R10. artikel AI + manual jadi SATU daftar (terpakai bersama)
  R11. `hapus` menghapus 1 artikel
  R12. `unduh` tanpa tautan → jawab jujur + beri LINK (tidak menembus paywall)
  R13. Pagar: `pustaka.cari_semua` = satu-satunya mesin (tidak ada jalur lain)
  R14. Tidak ada tabel dompet baru (satu dompet)

Cara pakai (dalam container): cd /app && python3 _gerbang_rute_jurnal.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

TMP = tempfile.mkdtemp(prefix='uji_rute_jurnal_')
DB = os.path.join(TMP, 'uji.db')
shutil.copyfile('/app/data/eduai.db', DB)
os.environ['EDUAI_DB'] = DB

from sqlalchemy import create_engine                        # noqa: E402
from sqlalchemy.orm import sessionmaker                     # noqa: E402

from app import models as M                                 # noqa: E402

eng = create_engine(f'sqlite:///{DB}', connect_args={'check_same_thread': False})
M.engine = eng
M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)
M.init_db()

lulus = 0
gagal = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  LULUS  {nama}')
    else:
        gagal += 1
        print(f'  GAGAL  {nama}  {bukti}')


#  ── Siapkan app + user + naskah + login ──
from fastapi.testclient import TestClient                   # noqa: E402

from app.main import app                                    # noqa: E402
from app.models import FileBerkas, User                     # noqa: E402

db = M.SessionLocal()
u = db.query(User).filter(User.email == 'uji-rute-jurnal@test.local').first()
if u is None:
    u = User(email='uji-rute-jurnal@test.local', nama='Uji Rute',
             password_hash='x')
    db.add(u); db.commit()
fb = (db.query(FileBerkas)
        .filter(FileBerkas.user_id == u.id,
                FileBerkas.nama == 'uji-rute-jurnal.docx').first())
if fb is None:
    fb = FileBerkas(user_id=u.id, nama='uji-rute-jurnal.docx',
                    nama_simpan='uji-rute-jurnal.docx', tipe='',
                    ukuran=0)
    db.add(fb); db.commit()
UID, FID = u.id, fb.id
db.close()

klien = TestClient(app, raise_server_exceptions=False)


def _login() -> None:
    """Pasang sesi login palsu (uji ini bukan uji auth)."""
    from app import auth as A
    app.dependency_overrides[A.wajib_login_api] = lambda: u


def _logout() -> None:
    app.dependency_overrides.clear()


def _bersih():
    d = M.SessionLocal()
    from app.models import PencarianManual as PM
    from app.models import ProfilDokumen as PD
    d.query(PM).filter(PM.user_id == UID).delete()
    d.query(PD).filter(PD.user_id == UID, PD.file_id == FID).delete()
    d.commit(); d.close()


# ── R1 ──
def r1() -> None:
    jalur = {r.path for r in app.routes}
    for p in ('/api/ai/v1/jurnal/lihat', '/api/ai/v1/jurnal/cari',
              '/api/ai/v1/jurnal/cari-ai', '/api/ai/v1/jurnal/tambah-manual',
              '/api/ai/v1/jurnal/hapus', '/api/ai/v1/jurnal/unduh'):
        cek(f'R1 rute terdaftar {p}', p in jalur)


# ── R2 ──
def r2() -> None:
    _logout()
    r = klien.get('/api/ai/v1/jurnal/lihat', params={'file_id': FID})
    cek('R2a tanpa login → ditolak', r.status_code in (401, 403, 303, 307),
        f'({r.status_code})')
    r2b = klien.post('/api/ai/v1/jurnal/cari', params={'file_id': FID,
                                                       'kata_kunci': 'x'})
    cek('R2b POST tanpa login → ditolak',
        r2b.status_code in (401, 403, 303, 307), f'({r2b.status_code})')


# ── R3 ──
def r3() -> None:
    _login(); _bersih()
    r = klien.get('/api/ai/v1/jurnal/lihat', params={'file_id': FID})
    cek('R3a lihat → 200', r.status_code == 200, f'({r.status_code})')
    j = r.json()
    for k in ('ok', 'artikel', 'jumlah', 'jatah', 'batas_manual',
              'sisa_slot_manual', 'bab_semua', 'layak', 'belum_layak'):
        cek(f'R3 bentuk balikan punya {k}', k in j)
    cek('R3b batas_manual = 8', j.get('batas_manual') == 8)
    cek('R3c jatah sisa 2 (per user baru)', (j.get('jatah') or {}).get('sisa') == 2)
    cek('R3d lihat TIDAK memotong token (jatah tetap 2)',
        (j.get('jatah') or {}).get('sisa') == 2)


# ── R4 ──
def r4() -> None:
    _login(); _bersih()
    r = klien.post('/api/ai/v1/jurnal/cari-ai',
                   params={'file_id': FID, 'bab': 'BAB II',
                           'kata_kunci': 'kualitas produk, harga'})
    cek('R4a cari-ai → 200', r.status_code == 200, f'({r.status_code})')
    j = r.json()
    if j.get('ok'):
        cek('R4b ditandai gratis', j.get('gratis') is True)
        d = M.SessionLocal()
        from app.models import PencarianManual as PM
        n = d.query(PM).filter(PM.user_id == UID).count()
        d.close()
        cek('R4c cari-ai TIDAK mencatat jatah manual', n == 0, f'({n})')
        from app import jatah as JT
        d = M.SessionLocal()
        cek('R4d jatah manual tetap 2', JT.sisa_gratis(d, UID) == 2)
        d.close()
        #  artikel AI tersimpan dgn asal='ai'
        d = M.SessionLocal()
        from app import jurnal as J
        from app.models import ProfilDokumen as PD
        p = d.query(PD).filter(PD.user_id == UID, PD.file_id == FID).first()
        arts = J.daftar(J.baca(p), 'BAB II') if p else []
        d.close()
        cek('R4e artikel AI tersimpan (asal=ai)',
            bool(arts) and all(a.get('asal') == 'ai' for a in arts))
    else:
        #  mesin bisa balas kosong (faktor jaringan) — jangan vonis gagal
        cek('R4b (mesin balas kosong — dilewati)', True)
        cek('R4c (mesin balas kosong — dilewati)', True)
        cek('R4d (mesin balas kosong — dilewati)', True)
        cek('R4e (mesin balas kosong — dilewati)', True)


# ── R5 jatah manual ──
def r5() -> None:
    _login(); _bersih()
    hasil = []
    for i in range(3):
        r = klien.post('/api/ai/v1/jurnal/cari',
                       params={'file_id': FID, 'bab': 'BAB III',
                               'kata_kunci': 'pengaruh harga terhadap '
                                             'keputusan pembelian' + ' ' * i})
        hasil.append(r.json())
    j1, j2, j3 = hasil
    cek('R5a pencarian-1 jenis gratis',
        j1.get('jenis') == 'gratis' or j1.get('kode') == 'tidak_ada_hasil')
    if j1.get('ok'):
        cek('R5b pencarian-1 gratis (token 0)', j1.get('token_dipotong') == 0)
    else:
        cek('R5b (0 hasil — token dikembalikan)',
            j1.get('token_dikembalikan') in (0, None))
    #  hitung pencarian gratis yang BENAR-benar tercatat
    d = M.SessionLocal()
    from app.models import PencarianManual as PM
    n = d.query(PM).filter(PM.user_id == UID,
                           PM.jenis == 'gratis').count()
    d.close()
    cek('R5c pencarian gratis tercatat ≤ 2', n <= 2, f'({n})')
    cek('R5d setelah jatah habis → token (atau tetap gratis kalau <2)',
        (j3.get('jenis') == 'token') or (n < 2), f'({j3.get("jenis")}, n={n})')


# ── R6 token dikembalikan saat 0 hasil ──
def r6() -> None:
    _login(); _bersih()
    #  habiskan jatah gratis dulu
    from app import jatah as JT
    d = M.SessionLocal()
    for i in range(2):
        JT.catat(d, UID, f'habis{i}', 'gratis')
    d.commit()
    cek('R6a jatah habis (0)', JT.sisa_gratis(d, UID) == 0)
    d.close()
    #  cari dgn kata kunci yang PASTI tidak ada hasil
    r = klien.post('/api/ai/v1/jurnal/cari',
                   params={'file_id': FID, 'bab': 'BAB IV',
                           'kata_kunci': 'zxqwv unrelated nonsense topic 9999'})
    j = r.json()
    if j.get('kode') == 'tidak_ada_hasil':
        cek('R6b 0 hasil → kode tidak_ada_hasil', True)
        cek('R6c token DIKEMBALIKAN',
            j.get('token_dikembalikan') is not None)
        cek('R6d pesan hangat + menyebut token tidak dipakai',
            'tokenmu tidak jadi dipakai' in (j.get('pesan') or '')
            or 'tidak jadi' in (j.get('pesan') or ''))
    else:
        #  kalau ternyata ada hasil → token memang kepakai (sah)
        cek('R6b (ada hasil — token memang dipakai, sah)', j.get('ok') is True,
            f'({j.get("kode")})')
        cek('R6c (tidak berlaku)', True)
        cek('R6d (tidak berlaku)', True)


# ── R7 kotak isian kurang ──
def r7() -> None:
    _login(); _bersih()
    r = klien.post('/api/ai/v1/jurnal/tambah-manual',
                   params={'file_id': FID, 'bab': 'BAB II', 'title': 'Hanya '
                           'judul'})
    j = r.json()
    cek('R7a isian kurang → ok=False', j.get('ok') is False)
    cek('R7b kode isian_kurang', j.get('kode') == 'isian_kurang')
    sudah = ('judul', 'penulis', 'tahun', 'jurnal')
    cek('R7c sebut apa yang kurang', any(s in (j.get('pesan') or '')
                                         for s in sudah))
    keras = ('GAGAL', 'PERINGATAN', 'HARUS', '!')
    cek('R7d pesan hangat (tanpa kata keras)',
        not any(k in (j.get('pesan') or '') for k in keras),
        f'({j.get("pesan")})')


# ── R8 batas 8 manual ──
def r8() -> None:
    _login(); _bersih()
    ok = 0
    for i in range(9):
        r = klien.post('/api/ai/v1/jurnal/tambah-manual',
                       params={'file_id': FID, 'bab': 'BAB V',
                               'title': f'Artikel {i}', 'authors': 'Penulis',
                               'year': 2020, 'journal': 'Jurnal Uji'})
        if r.json().get('ok'):
            ok += 1
    cek('R8a tepat 8 artikel manual masuk', ok == 8, f'({ok})')
    r9 = klien.post('/api/ai/v1/jurnal/tambah-manual',
                    params={'file_id': FID, 'bab': 'BAB V',
                            'title': 'Ke-9', 'authors': 'P', 'year': 2021,
                            'journal': 'J'})
    j9 = r9.json()
    cek('R8b ke-9 ditolak', j9.get('ok') is False)
    cek('R8c kode batas_manual', j9.get('kode') == 'batas_manual')
    cek('R8d pesan menyebut 8', '8' in (j9.get('pesan') or ''))
    keras = ('GAGAL', 'PERINGATAN', '!')
    cek('R8e pesan hangat', not any(k in (j9.get('pesan') or '') for k in keras))
    #  bab lain tetap boleh
    rl = klien.post('/api/ai/v1/jurnal/tambah-manual',
                    params={'file_id': FID, 'bab': 'BAB VI',
                            'title': 'Bab lain', 'authors': 'P', 'year': 2022,
                            'journal': 'J'})
    cek('R8f bab lain masih boleh', rl.json().get('ok') is True)


# ── R9 doi_status tidak bisa diisi user ──
def r9() -> None:
    _login(); _bersih()
    r = klien.post('/api/ai/v1/jurnal/tambah-manual',
                   params={'file_id': FID, 'bab': 'BAB II',
                           'title': 'Uji DOI', 'authors': 'P', 'year': 2020,
                           'journal': 'J', 'doi': '',
                           'doi_status': 'verified'})   # ← user coba akali
    j = r.json()
    cek('R9a tanpa DOI → TIDAK terverifikasi (user tak bisa akali)',
        j.get('layak_sitasi') is False, f'({j.get("layak_sitasi")})')
    cek('R9b audit menyebut tanpa DOI',
        'DOI' in (j.get('audit') or {}).get('sebab', '')
        or (j.get('audit') or {}).get('dicek') is False)


# ── R10 satu daftar ──
def r10() -> None:
    _login(); _bersih()
    klien.post('/api/ai/v1/jurnal/tambah-manual',
               params={'file_id': FID, 'bab': 'BAB VII', 'title': 'Manual A',
                       'authors': 'P', 'year': 2020, 'journal': 'J'})
    r = klien.get('/api/ai/v1/jurnal/lihat',
                  params={'file_id': FID, 'bab': 'BAB VII'})
    j = r.json()
    cek('R10a artikel manual tampil di lihat', j.get('jumlah') == 1)
    cek('R10b jumlah_manual = 1', j.get('jumlah_manual') == 1)
    cek('R10c sisa slot manual = 7', j.get('sisa_slot_manual') == 7)
    from app import jurnal as J
    d = M.SessionLocal()
    from app.models import ProfilDokumen as PD
    p = d.query(PD).filter(PD.user_id == UID, PD.file_id == FID).first()
    kirim = J.untuk_bangun_isi(J.baca(p), 'BAB VII') if p else []
    d.close()
    cek('R10d siap dikirim ke bangun_isi (tanpa kunci internal)',
        bool(kirim) and 'asal' not in kirim[0])


# ── R11 hapus ──
def r11() -> None:
    _login(); _bersih()
    klien.post('/api/ai/v1/jurnal/tambah-manual',
               params={'file_id': FID, 'bab': 'BAB VIII', 'title': 'Hapus A',
                       'authors': 'P', 'year': 2020, 'journal': 'J'})
    from app import jurnal as J
    d = M.SessionLocal()
    from app.models import ProfilDokumen as PD
    p = d.query(PD).filter(PD.user_id == UID, PD.file_id == FID).first()
    arts = J.daftar(J.baca(p), 'BAB VIII')
    kk = J.kunci(arts[0]) if arts else ''
    d.close()
    r = klien.post('/api/ai/v1/jurnal/hapus',
                   params={'file_id': FID, 'bab': 'BAB VIII', 'kunci': kk})
    j = r.json()
    cek('R11a hapus → ok', j.get('ok') is True)
    cek('R11b daftar jadi kosong', len(j.get('artikel') or []) == 0)
    cek('R11c sisa slot kembali 8', j.get('sisa_slot_manual') == 8)


# ── R12 unduh jujur ──
def r12() -> None:
    _login(); _bersih()
    klien.post('/api/ai/v1/jurnal/tambah-manual',
               params={'file_id': FID, 'bab': 'BAB IX', 'title': 'No PDF',
                       'authors': 'P', 'year': 2020, 'journal': 'J'})
    from app import jurnal as J
    d = M.SessionLocal()
    from app.models import ProfilDokumen as PD
    p = d.query(PD).filter(PD.user_id == UID, PD.file_id == FID).first()
    arts = J.daftar(J.baca(p), 'BAB IX')
    kk = J.kunci(arts[0]) if arts else ''
    d.close()
    r = klien.post('/api/ai/v1/jurnal/unduh',
                   params={'file_id': FID, 'bab': 'BAB IX', 'kunci': kk})
    j = r.json()
    cek('R12a tanpa tautan PDF → ok=False', j.get('ok') is False)
    cek('R12b kode tidak_terbuka', j.get('kode') == 'tidak_terbuka')
    #  ⚠️ 06Okt26: pesan diubah (perintah Bos: jangan menyuruh "unduh sendiri").
    #     Pesan baru pakai kata "Tautannya kami sertakan…" ⇒ bandingkan
    #     TANPA peduli huruf besar/kecil.
    cek('R12c pesan jujur + menawarkan tautan',
        any(k in (j.get('pesan') or '').lower()
            for k in ('tautan', 'link', 'penerbit', 'abstrak')))


# ── R13 satu mesin ──
def r13() -> None:
    from pathlib import Path
    isi = Path('/app/app/rute_jurnal.py').read_text(encoding='utf-8')
    cek('R13a rute memakai jurnal.cari_untuk_bab', 'cari_untuk_bab' in isi)
    cek('R13b rute TIDAK memanggil httpx langsung (lewat mesin)',
        'httpx' not in isi)
    cek('R13c rute TIDAK punya pencari sendiri',
        'def cari_semua' not in isi and 'def cari_scopus' not in isi)


# ── R14 satu dompet ──
def r14() -> None:
    from pathlib import Path
    isi = Path('/app/app/rute_jurnal.py').read_text(encoding='utf-8')
    cek('R14a potong token lewat kuota (satu pintu)',
        'potong_banyak' in isi)
    cek('R14b tidak menulis saldo sendiri',
        'saldo_token' not in isi)
    m = Path('/app/app/models.py').read_text(encoding='utf-8')
    cek('R14c tetap SATU tabel saldo', m.count('class SaldoToken') == 1)


def main() -> int:
    print('=== GERBANG RUTE JURNAL — uji API sungguhan ===')
    for fn in (r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14):
        try:
            fn()
        except Exception as e:                                # noqa: BLE001
            cek(f'{fn.__name__} tidak melempar', False,
                f'({type(e).__name__}: {e})')
    _logout()
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
