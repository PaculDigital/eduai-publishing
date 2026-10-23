#!/usr/bin/env python3
"""Probe tandingan untuk RUTE BERPAGAR (token/kuota + kebocoran antar-user).

Dipanggil saat review branch agen lain yang menambah rute HTTP baru.
Fokus pada 4 kelas yang uji bawaan hampir selalu buta:

  G1 PAGAR LOGIN       — tanpa sesi harus ditolak
  G2 KEBOCORAN USER    — user lain menyentuh berkas orang harus 404/403
  G3 URUTAN POTONG     — token dipotong SEBELUM kerja? (kalau mesin gagal, hangus?)
  G4 PAGAR MASUKAN     — data kosong / tahap asing / bentuk salah = PESAN, bukan 500
  G5 MODE TERLEWAT     — jalur/mode yang tidak muncul di uji bawaan

CARA PAKAI
  1. Salin ke dalam repo salinan (JANGAN ke repo produksi).
  2. Sesuaikan KONFIG di bawah.
  3. .venv/bin/python probe_rute_berpagar.py   # EXIT 1 kalau ada temuan

JANGAN pakai assert — satu probe meledak tidak boleh menghentikan sisanya.
"""
import sys, types, traceback

# ─────────────────────────── KONFIG ───────────────────────────
KONFIG = {
    'modul_rute':      'app.bab4_rute',            # modul berisi `router`
    'modul_model':     'app.models',
    'modul_kuota':     'app.kuota',
    'modul_mesin':     'app.jembatan_statistik',   # klien layanan sebelah (opsional)
    'dep_login':       'app.auth:wajib_login_api',
    'dep_db':          'app.models:get_db',
    'berkas_id_sendiri': 10,
    'berkas_id_orang':   20,
    'user_id':         1,
    'user_id_orang':   2,
    'rute_file': [                                 # rute yang menerima file_id
        ('GET',  '/api/bab4/ringkasan?file_id={fid}'),
        ('GET',  '/api/bab4/instrumen?file_id={fid}'),
        ('GET',  '/api/bab4/data?file_id={fid}'),
    ],
    'rute_tarif': ('POST', '/api/bab4/olah-data', {'file_id': 10}),
    'nama_env_kunci': 'EDUAI_STATISTIK_KUNCI',     # untuk info saja
}
# ──────────────────────────────────────────────────────────────

TEMUAN = []


def cek(nama, ok, info=''):
    print(('  OK  ' if ok else '  BUG ') + nama + ('' if ok else f'  -> {info}'))
    if not ok:
        TEMUAN.append(nama)


def _imp(spec):
    mod, _, attr = spec.partition(':')
    m = __import__(mod, fromlist=[attr or '__x__'])
    return getattr(m, attr) if attr else m


def main():
    sys.path.insert(0, '.')
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    M = _imp(KONFIG['modul_model'])
    rute = _imp(KONFIG['modul_rute'])
    kuota = _imp(KONFIG['modul_kuota'])
    dep_db = _imp(KONFIG['dep_db'])
    dep_login = _imp(KONFIG['dep_login'])

    engine = create_engine('sqlite://', connect_args={'check_same_thread': False},
                           poolclass=StaticPool)
    M.Base.metadata.create_all(engine)
    Sesi = sessionmaker(bind=engine)

    db = Sesi()
    for uid, email in ((KONFIG['user_id'], 'a@x.id'), (KONFIG['user_id_orang'], 'b@x.id')):
        db.add(M.User(id=uid, email=email, nama=email, password_hash='x'))
    for fid, uid in ((KONFIG['berkas_id_sendiri'], KONFIG['user_id']),
                     (KONFIG['berkas_id_orang'], KONFIG['user_id_orang'])):
        db.add(M.FileBerkas(id=fid, user_id=uid, nama=f'{fid}.docx',
                            nama_simpan=f'{fid}.docx', ukuran=1))
    db.commit()
    db.close()

    def _db():
        s = Sesi()
        try:
            yield s
        finally:
            s.close()

    app = FastAPI()
    app.include_router(rute.router)
    app.dependency_overrides[dep_db] = _db
    klien = TestClient(app, raise_server_exceptions=False)

    def sebagai(uid):
        app.dependency_overrides[dep_login] = lambda: types.SimpleNamespace(id=uid)
        return klien

    # ── G1 PAGAR LOGIN ────────────────────────────────────────
    print('== G1. Pagar login ==')
    app.dependency_overrides.pop(dep_login, None)
    url = KONFIG['rute_file'][0][1].format(fid=KONFIG['berkas_id_sendiri'])
    try:
        r = klien.get(url)
        cek('tanpa sesi ditolak (401/403/3xx)', r.status_code in (401, 403, 302, 307),
            r.status_code)
    except Exception as e:
        cek('tanpa sesi ditolak', False, f'{type(e).__name__}: {e}')

    # ── G2 KEBOCORAN ANTAR-USER ───────────────────────────────
    print()
    print('== G2. Kebocoran antar-user ==')
    orang = sebagai(KONFIG['user_id_orang'])
    for metode, pola in KONFIG['rute_file']:
        u = pola.format(fid=KONFIG['berkas_id_sendiri'])
        try:
            r = orang.get(u) if metode == 'GET' else orang.post(u, json={})
            cek(f'{metode} {u} -> 404/403', r.status_code in (404, 403), r.status_code)
        except Exception as e:
            cek(f'{metode} {u}', False, type(e).__name__)

    # ── G4 PAGAR MASUKAN ──────────────────────────────────────
    print()
    print('== G4. Pagar masukan (harus PESAN, bukan 500) ==')
    sendiri = sebagai(KONFIG['user_id'])
    metode, url, isi = KONFIG['rute_tarif']
    for nama, ubah in [
        ('file_id tidak ada', {'file_id': 999999}),
        ('file_id null', {'file_id': None}),
        ('payload kosong', {}),
    ]:
        try:
            body = dict(isi); body.update(ubah)
            r = sendiri.post(url, json=body)
            cek(f'{nama} -> 4xx', 400 <= r.status_code < 500, r.status_code)
        except Exception as e:
            cek(f'{nama} tidak meledak', False, f'{type(e).__name__}: {e}')

    # ── G3 URUTAN POTONG TOKEN ────────────────────────────────
    print()
    print('== G3. Urutan potong token (paling mahal kalau salah) ==')
    asli_potong = getattr(kuota, 'potong_banyak', None)
    asli_kembali = getattr(kuota, 'kembalikan_banyak', None)
    jejak = {'potong': 0, 'kembali': 0}

    if asli_potong is None:
        print('  SKIP  modul kuota tidak punya potong_banyak')
    else:
        def potong_palsu(*a, **k):
            jejak['potong'] += 1
            raise RuntimeError('SALDO_KURANG_SIMULASI')

        kuota.potong_banyak = potong_palsu
        try:
            r = sendiri.post(url, json=isi)
            cek('potong dipanggil saat tarif > 0', jejak['potong'] >= 1,
                f"dipanggil {jejak['potong']}x (tarif mungkin 0 = jatah paket, cek ringkasan)")
        except Exception as e:
            cek('potong dipanggil', False, type(e).__name__)
        finally:
            kuota.potong_banyak = asli_potong

        # mesin dipaksa gagal -> token WAJIB kembali
        jejak.update(potong=0, kembali=0)
        modul_mesin = None
        try:
            modul_mesin = _imp(KONFIG['modul_mesin'])
        except Exception:
            pass

        def potong_ok(*a, **k):
            jejak['potong'] += 1
            return {'dipotong': 1}

        def kembali_ok(*a, **k):
            jejak['kembali'] += 1

        kuota.potong_banyak = potong_ok
        if asli_kembali:
            kuota.kembalikan_banyak = kembali_ok
        hitung_asli = getattr(modul_mesin, 'hitung', None) if modul_mesin else None
        if hitung_asli:
            def meledak(*a, **k):
                raise RuntimeError('MESIN MATI (simulasi probe)')
            modul_mesin.hitung = meledak
        try:
            r = sendiri.post(url, json=isi)
            if jejak['potong']:
                cek('token DIKEMBALIKAN saat kerja gagal',
                    jejak['kembali'] >= 1 or r.status_code < 500,
                    f"potong {jejak['potong']}x, kembali {jejak['kembali']}x, "
                    f"respons {r.status_code} -> TOKEN HANGUS")
            else:
                print('  SKIP  token tidak dipotong (tarif 0) — ulangi dengan tarif > 0')
        finally:
            if hitung_asli:
                modul_mesin.hitung = hitung_asli
            kuota.potong_banyak = asli_potong
            if asli_kembali:
                kuota.kembalikan_banyak = asli_kembali

    # ── G5 MODE TERLEWAT ──────────────────────────────────────
    print()
    print('== G5. Mode/jalur yang tidak muncul di uji bawaan ==')
    try:
        import subprocess
        keluar = subprocess.run(['grep', '-rn', "== 'pls'\\|== 'spss'\\|mode ==", 'app/'],
                                capture_output=True, text=True).stdout
        mode_kode = sorted({ln.split('==')[-1].strip().strip("':") for ln in keluar.splitlines()})
        uji = subprocess.run(['sh', '-c', "grep -l 'pls\\|spss' uji_*.py 2>/dev/null"],
                             capture_output=True, text=True).stdout.split()
        print(f'  mode di kode : {mode_kode}')
        print(f'  berkas uji   : {uji or "TIDAK ADA yang menyebut mode"}')
        print('  >> periksa manual: setiap mode di atas WAJIB punya satu kasus uji nyata')
    except Exception as e:
        print('  SKIP ', type(e).__name__)

    print()
    print(f'RINGKAS: {len(TEMUAN)} temuan -> {TEMUAN}')
    return 1 if TEMUAN else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
