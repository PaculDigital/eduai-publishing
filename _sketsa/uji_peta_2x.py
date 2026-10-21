"""UJI NYATA: panggil peta 2x — berapa kali JEV dipanggil? (BUKTI untuk Bos)

Menghitung panggilan Jev dari LOG container (baris '[jev]') — sumber nyata,
bukan tebakan. Dijalankan DI DALAM container eduai-app.

Ronde:
  1) peta_awal naskah fid (peta lama dibersihkan) -> Jev dipanggil
  2) peta_awal naskah SAMA                        -> harus 0 (dari simpanan)
  3) naskah sedikit BERUBAH (sidik beda)          -> Jev dipanggil lagi
"""
import json
import re
import shutil
import subprocess
import sqlite3
import time
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8000'
DB = '/app/data/eduai.db'
LULUS, GAGAL = [], []


def cek(nama, benar, bukti=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  OK  ' if benar else '  X   ') + nama +
          (('  [%s]' % bukti) if bukti else ''))


def token(uid):
    from app.auth import buat_token
    return buat_token(uid)


def panggil(path, data=None, tok=None, timeout=900):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body,
                                 method='POST' if body else 'GET')
    req.add_header('Content-Type', 'application/json')
    if tok:
        from app.config import SESSION_COOKIE
        req.add_header('Cookie', '%s=%s' % (SESSION_COOKIE, tok))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, 'GALAT: %s' % e


def nama_cookie():
    try:
        from app.main import SESSION_COOKIE
        return SESSION_COOKIE
    except Exception:
        return 'eduai_sesi'


def main():
    con = sqlite3.connect(DB)
    row = con.execute(
        "select id, user_id, nama from files where id=112").fetchone()
    fid, uid, nama = row
    print('berkas uji: fid=%s user=%s %s' % (fid, uid, (nama or '')[:40]))
    con.execute("update profil_dokumen set peta_json='', peta_sidik='', "
                "peta_dibuat=null where file_id=?", (fid,))
    con.commit()
    con.close()

    tok = token(uid)
    cookie = nama_cookie()
    isi = {'file_id': fid, 'mode': 'peta_awal'}
    hasil = {}
    for ronde in (1, 2):
        t0 = time.time()
        st, teks = panggil('/api/ai/v1/peta/mulai', isi, tok)
        dt = time.time() - t0
        try:
            j = json.loads(teks)
        except Exception:
            j = {}
        print()
        print('=== RONDE %d ===' % ronde)
        print('  HTTP          : %s' % st)
        print('  detik         : %.1f' % dt)
        print('  peta_dari     : %s' % j.get('peta_dari'))
        print('  dari_simpanan : %s' % j.get('dari_simpanan'))
        print('  jumlah bagian : %s' % j.get('jumlah'))
        hasil[ronde] = (st, dt, j)

    cek('RONDE 1: HTTP 200', hasil[1][0] == 200, hasil[1][0])
    cek('RONDE 1: peta dari JEV', hasil[1][2].get('peta_dari') == 'jev',
        hasil[1][2].get('peta_dari'))
    cek('RONDE 1: tidak dari simpanan',
        not hasil[1][2].get('dari_simpanan'))
    cek('RONDE 2: HTTP 200', hasil[2][0] == 200, hasil[2][0])
    cek('RONDE 2: DARI SIMPANAN (tidak panggil Jev)',
        bool(hasil[2][2].get('dari_simpanan')))
    cek('RONDE 2: jauh lebih cepat dari ronde 1',
        hasil[2][1] < hasil[1][1] * 0.5,
        '%.1f vs %.1f dtk' % (hasil[2][1], hasil[1][1]))

    print()
    print('LULUS %d / GAGAL %d' % (len(LULUS), len(GAGAL)))
    return 0 if not GAGAL else 1


if __name__ == '__main__':
    raise SystemExit(main())
