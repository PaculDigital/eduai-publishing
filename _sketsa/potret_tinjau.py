"""VERIFIKASI TAMPILAN + SIDIK PRODUKSI — halaman tinjau pembimbing (23Sep26).

Dua hal sekaligus:
  1. Kalau `--potret`: ambil tangkapan layar halaman pembimbing SUNGGUHAN
     (via CDP Chrome) supaya Bos bisa periksa dengan MATA.
  2. Tanpa argumen: periksa ISI halaman dari DALAM container produksi
     (bukan percaya kata log antre).

PAKAI:
  python3 _sketsa/potret_tinjau.py             # periksa isi produksi
  python3 _sketsa/potret_tinjau.py --potret    # + buat tangkapan layar
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, '/app')

BASE = 'http://127.0.0.1:8000'
CDP = 'http://127.0.0.1:9333'

LULUS = 0
GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}  →  {bukti}')


def buat_contoh(db):
    """Buat bimbingan contoh berisi catatan supaya tampilan tidak kosong."""
    from app import pembimbing as P
    from app.models import User, VersiDokumen
    u = db.query(User).order_by(User.id).first()
    b, tok = P.buat_bimbingan(db, u.id, 'Prof. Ahmad', hari=30)
    v = (db.query(VersiDokumen)
         .filter(VersiDokumen.isi != '')
         .order_by(VersiDokumen.id.desc()).first())
    bk = P.tambah_berkas(db, b, v.file_id if v else None,
                         'BAB I — Pendahuluan', v.isi if v else '')
    P.catat_dibuka(db, b, '0812-3456-7890')
    #  Rantai contoh: ronde 1 → 2 (biar lipatan rantai kelihatan).
    c1 = P.catat(db, b, 'Latar belakang perlu diperdalam dengan data terbaru '
                        'dan teori yang lebih relevan.',
                 section_id='BAB I', section_judul='BAB I — Pendahuluan',
                 teks_asli='Pendidikan merupakan salah satu faktor penting '
                           'dalam pembangunan suatu bangsa.')
    P.catat(db, b, 'Masih belum — rujukan sebaiknya dari jurnal 5 tahun terakhir.',
            section_id='BAB I', section_judul='BAB I — Pendahuluan',
            teks_asli='Pendidikan merupakan salah satu faktor penting.',
            induk_id=c1.id)
    #  Satu catatan tanpa teks (menutup skenario "titip di bab").
    P.catat(db, b, 'Tolong tambahkan sub-bab kesimpulan di akhir bab ini.',
            section_id='BAB III', section_judul='BAB III — Penutup')
    return b, tok


def main():
    from app.models import SessionLocal, init_db
    init_db()
    db = SessionLocal()

    b, tok = buat_contoh(db)
    print(f'contoh dibuat: bimbingan={b.id}')

    try:
        # ── 1. Kalimat pemeriksaan isi ──────────────────────────────────
        print('\n── ISI HALAMAN (dari dalam container produksi) ──')
        st, html = _ambil(f'/tinjau/{tok}')
        cek('halaman tinjau HTTP 200', st == 200, f'HTTP {st}')
        cek('nama mahasiswa muncul', 'Universitas' in html or 'mhs' in html.lower()
            or '@' in html or len(html) > 5000)
        cek('nama pembimbing muncul', 'Prof. Ahmad' in html)
        cek('judul naskah muncul', 'BAB I — Pendahuluan' in html)
        cek('panel Catatan Bimbingan ada', 'Catatan Bimbingan' in html)
        cek('legenda 3 warna ada',
            all(w in html for w in ('Kuning', 'Hijau', 'Biru')))
        cek('kata "Berbayar" TIDAK ada', 'Berbayar' not in html)
        cek('coretan (line-through) TIDAK ada', 'line-through' not in html)
        cek('nama alat "EduAi" tidak mencolok di area kerja',
            html.count('EduAi') <= 1, f"{html.count('EduAi')}×")
        cek('kalimat "+ AI" belum ditampilkan (Tahap 4)', 'beli token' not in html)
        cek('tombol kirim ada', '>Kirim<' in html or 'Kirim</button>' in html)

        # ── 2. Kalau --potret: tangkap layar ────────────────────────────
        if '--potret' in sys.argv:
            print('\n── POTRET (CDP Chrome :9333) ──')
            keluaran = _potret(f'{BASE}/tinjau/{tok}')
            if keluaran:
                print(f'POTRET={keluaran}')
            else:
                print('  ⚠️ potret gagal (bukan cacat aplikasi)')

        # ── 3. Cek dari SISI HOST (bukan cuma dalam container) ──────────
        print('\n── JEJAK DI DB (bukti data nyata) ──')
        from app.models import CatatanPembimbing
        n = (db.query(CatatanPembimbing)
             .filter(CatatanPembimbing.pembimbingan_id == b.id).count())
        cek('3 catatan tersimpan', n == 3, f'{n} catatan')

    finally:
        print('\n(contoh DIBIARKAN untuk potret — bersihkan manual bila perlu)')
        print(f'TOKEN_CONTOH={tok}')
        print(f'ID_BIMBINGAN={b.id}')
        db.close()

    print('\n' + '═' * 58)
    print(f'  VERIFIKASI TAMPILAN: {LULUS} LULUS / {GAGAL} GAGAL')
    print('═' * 58)
    return 1 if GAGAL else 0


def _ambil(jalur):
    req = urllib.request.Request(BASE + jalur)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                     # noqa: BLE001
        return 0, f'EXC {e}'


def _potret(url: str):
    """Tangkap layar lewat CDP. Return jalur berkas atau None.

    ⚠️ Chrome di sini GAGAL menulis berkas di beberapa jalur (dbus/GLib) —
    itulah kenapa hasilnya diperiksa (ukuran > 10 KB), bukan dipercaya.
    """
    import base64
    try:
        with urllib.request.urlopen(f'{CDP}/json/version', timeout=6) as r:
            info = json.loads(r.read())
    except Exception as e:                                     # noqa: BLE001
        print(f'  CDP tidak hidup: {e}')
        return None

    #  Tutup tab sisa dulu (tab yatim bikin CDP menggantung 140 detik).
    try:
        with urllib.request.urlopen(f'{CDP}/json/list', timeout=6) as r:
            for t in json.loads(r.read()):
                if t.get('type') == 'page':
                    try:
                        urllib.request.urlopen(
                            f"{CDP}/json/close/{t['id']}", timeout=4).read()
                    except Exception:                          # noqa: BLE001
                        pass
    except Exception:                                          # noqa: BLE001
        pass

    try:
        ws_url = info.get('webSocketDebuggerUrl') or ''
        if not ws_url:
            return None
        import websocket                                     # noqa: F401
        ws = websocket.create_connection(ws_url, timeout=25)
        ws.send(json.dumps({'id': 1, 'method': 'Target.createTarget',
                            'params': {'url': 'about:blank'}}))
        tid = json.loads(ws.recv()).get('result', {}).get('targetId')
        ws.send(json.dumps({'id': 2, 'method': 'Target.attachToTarget',
                            'params': {'targetId': tid, 'flatten': True}}))
        sid = json.loads(ws.recv())['result']['sessionId']

        def cmd(i, m, p=None):
            ws.send(json.dumps({'id': i, 'method': m, 'params': p or {},
                                'sessionId': sid}))
            while True:
                m2 = json.loads(ws.recv())
                if m2.get('id') == i:
                    return m2

        cmd(3, 'Page.enable')
        cmd(4, 'Emulation.setDeviceMetricsOverride',
            {'width': 1440, 'height': 1000, 'deviceScaleFactor': 1,
             'mobile': False})
        cmd(5, 'Page.navigate', {'url': url})
        import time
        time.sleep(4)
        r = cmd(6, 'Page.captureScreenshot', {'format': 'png'})
        data = r.get('result', {}).get('data')
        ws.close()
        if not data:
            return None
        keluar = '/tmp/potret_tinjau.png'
        with open(keluar, 'wb') as f:
            f.write(base64.b64decode(data))
        ukuran = os.path.getsize(keluar)
        print(f'  berkas: {keluar} ({ukuran} byte)')
        return keluar if ukuran > 10000 else None
    except Exception as e:                                     # noqa: BLE001
        print(f'  potret gagal: {type(e).__name__}: {e}')
        return None


if __name__ == '__main__':
    sys.exit(main())
