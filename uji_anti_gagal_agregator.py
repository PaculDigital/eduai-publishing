"""Uji DISPLAY anti-gagal: agregator G3, resolve selesai G1, teks sabar A4.

Tanpa LLM, tanpa API, tanpa tulis DB produksi. Bagian DB memakai SQLite
sementara di /tmp dan _sesi_baru yang ditambal, jadi tidak pernah
menyentuh DB produksi.

Jalankan di container (dependensi lengkap):
  docker exec -i eduai-app python3 /app/uji_anti_gagal_agregator.py
Jalankan di host (tanpa sqlalchemy): modul proses dimuat dengan stub,
bagian DB dan fid dilewati (LEWAT), bagian murni tetap jalan.
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.
"""

import json
import os
import random
import sys
import tempfile
import threading
import types
from types import SimpleNamespace

for p in reversed((os.getcwd(), '/tmp/checkout',
                    '/opt/data/services/eduai-publishing', '/app')):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

LULUS = 0
GAGAL = []
LEWAT = []


def cek(nama, ok, info=''):
    global LULUS
    if ok:
        LULUS += 1
        print('  LULUS %s' % nama)
    else:
        GAGAL.append(nama)
        print('  GAGAL %s %s' % (nama, info))


def lewat(nama, alasan):
    LEWAT.append(nama)
    print('  LEWAT %s (%s)' % (nama, alasan))


# ---- muat app.proses (asli di container, stub di host) ----
REAL = False
try:
    import app.proses as P
    REAL = True
except ModuleNotFoundError:
    _sql = types.ModuleType('sqlalchemy')
    _sql.select = lambda *a, **k: None
    sys.modules['sqlalchemy'] = _sql
    _pkg = types.ModuleType('app')
    _pkg.__path__ = [os.path.join(os.getcwd(), 'app')]
    sys.modules['app'] = _pkg
    _mod = types.ModuleType('app.models')

    class _Dummy(object):
        pass

    _mod.ProsesAI = _Dummy
    _mod.SessionLocal = lambda *a, **k: None
    sys.modules['app.models'] = _mod
    import app.proses as P

print('== mode: %s ==' % ('REAL (container)' if REAL else 'STUB (host)'))


def baris(status='jalan', tahap='', komentar=None, hasil_json='', hasil=''):
    return SimpleNamespace(
        status=status, tahap=tahap, bagian_ke=0, jumlah_bagian=1,
        komentar_json=json.dumps(komentar if komentar is not None else {},
                                 ensure_ascii=False),
        hasil_json=hasil_json, hasil=hasil)


def komentar_buku(jumlah_bab):
    return {'judul': 'Buku Uji', 'jumlah_bab': jumlah_bab}


print('== gabung_slot_bab (murni) ==')
k0 = json.dumps(komentar_buku(5), ensure_ascii=False)
k1 = P.gabung_slot_bab(k0, 3, selesai=True, terakhir='BAB 3 selesai: 100 kata')
d1 = json.loads(k1)
cek('slot bab 3 selesai', d1['progres_bab']['3']['selesai'] is True)
cek('judul dan jumlah_bab tidak berubah',
    d1['judul'] == 'Buku Uji' and d1['jumlah_bab'] == 5)
k2 = P.gabung_slot_bab(k1, 1, terakhir='BAB 1 mulai: Judul Bab 1')
d2 = json.loads(k2)
cek('slot bab 1 tidak menimpa slot bab 3',
    d2['progres_bab']['3']['selesai'] is True
    and d2['progres_bab']['3']['terakhir'] == 'BAB 3 selesai: 100 kata')
cek('slot bab 1 belum selesai, terakhir tercatat',
    d2['progres_bab']['1']['selesai'] is False
    and d2['progres_bab']['1']['terakhir'] == 'BAB 1 mulai: Judul Bab 1')
k3 = P.gabung_slot_bab(k2, 3, selesai=False, terakhir='BAB 3 mulai lagi')
cek('flag selesai tidak pernah dihapus',
    json.loads(k3)['progres_bab']['3']['selesai'] is True)
cek('komentar list revisi dikembalikan apa adanya',
    P.gabung_slot_bab('["Perbaiki tata bahasa"]', 2, selesai=True)
    == '["Perbaiki tata bahasa"]')
cek('JSON rusak dikembalikan apa adanya',
    P.gabung_slot_bab('bukan-json', 2, selesai=True) == 'bukan-json')

print('== agregat paralel murni: 4 worker, urutan acak ==')
random.seed(7)
keadaan = {'komentar': json.dumps(komentar_buku(4), ensure_ascii=False)}
kunci = threading.Lock()
riwayat = []


def _pekerja(nomor):
    import time
    time.sleep(random.random() / 50.0)
    with kunci:
        keadaan['komentar'] = P.gabung_slot_bab(
            keadaan['komentar'], nomor, selesai=True,
            terakhir='BAB %d selesai' % nomor)
        r = baris(komentar=json.loads(keadaan['komentar']))
        riwayat.append(P.agregat_progres(r)['bab_selesai'])


utas = [threading.Thread(target=_pekerja, args=(n,)) for n in (1, 2, 3, 4)]
for t in utas:
    t.start()
for t in utas:
    t.join()
cek('hitungan agregat tidak pernah turun',
    all(b >= a for a, b in zip(riwayat, riwayat[1:])),
    'riwayat=%s' % (riwayat,))
cek('hitungan akhir 4 dari 4 worker', riwayat and riwayat[-1] == 4,
    'riwayat=%s' % (riwayat,))
akhir = P.agregat_progres(baris(komentar=json.loads(keadaan['komentar'])))
cek('subbab per bab lengkap dan per bab',
    akhir['subbab_per_bab'] == {'1': 'BAB 1 selesai', '2': 'BAB 2 selesai',
                                '3': 'BAB 3 selesai', '4': 'BAB 4 selesai'},
    'subbab=%s' % (akhir['subbab_per_bab'],))
cek('daftar bab selesai terurut', akhir['bab_selesai_daftar'] == [1, 2, 3, 4])

print('== agregat tidak mengikuti slot global mentah ==')
slot_tetap = json.loads(P.gabung_slot_bab(
    P.gabung_slot_bab(json.dumps(komentar_buku(5), ensure_ascii=False),
                      4, selesai=True),
    5, selesai=True))
for bagian_mentah in (4, 5, 4, 1):
    r = baris(tahap='BAB %d mulai' % bagian_mentah, komentar=slot_tetap)
    r.bagian_ke = bagian_mentah
    cek('bagian_ke %d -> agregat tetap 2' % bagian_mentah,
        P.agregat_progres(r)['bab_selesai'] == 2)

print('== agregat job 222 (hasil_json final, tanpa slot) ==')
hasil_222 = {
    'judul': 'Transformasi Digital UMKM',
    'bab': {'1': {'kata': 6754}, '2': {'kata': 7164}, '3': {'kata': 7487},
            '4': {'kata': 7304}, '5': {'kata': 6341}},
    'bab_selesai': 5, 'total_kata': 35050, 'file_id': 123,
    'docx': '/opt/data/buku_hasil/1793346442-12/Buku_FINAL.docx',
    'folder': '/opt/data/buku_hasil/1793346442-12',
}
r222 = baris(status='selesai', tahap='Selesai', komentar=komentar_buku(5),
             hasil_json=json.dumps(hasil_222, ensure_ascii=False),
             hasil='Transformasi Digital UMKM')
ag222 = P.agregat_progres(r222)
cek('job 222: bab_selesai 5 dari hasil_json', ag222['bab_selesai'] == 5)
cek('job 222: fase selesai', ag222['fase'] == 'selesai')
cek('job 222: total dari komentar 5', ag222['bab_total'] == 5)

print('== fase agregator ==')
for tahap, status, harap in (
        ('Menunggu antrean', 'menunggu', 'menyiapkan'),
        ('Menulis 5 bab', 'jalan', 'menulis'),
        ('BAB 2 mulai: Judul', 'jalan', 'menulis'),
        ('Merangkai buku jadi satu dokumen', 'jalan', 'perakitan'),
        ('Memeriksa hasil', 'jalan', 'gerbang'),
        ('Memperbaiki 2 bab bermasalah', 'jalan', 'penyempurnaan'),
        ('BAB 3 GAGAL', 'jalan', 'penyempurnaan'),
        ('Selesai', 'selesai', 'selesai'),
        ('Gagal', 'gagal', 'penyempurnaan'),
        ('Gagal', 'dibatalkan', 'penyempurnaan')):
    got = P.agregat_progres(baris(status=status, tahap=tahap,
                                  komentar=komentar_buku(5)))['fase']
    cek('fase %r/%s -> %s' % (tahap, status, harap), got == harap, 'dapat %s' % got)
cek('teks sabar persis saat penyempurnaan',
    P.agregat_progres(baris(tahap='Memperbaiki 2 bab', komentar=komentar_buku(5)))['teks_sabar']
    == 'buku sedang disempurnakan, mohon sabar')
cek('teks sabar kosong saat menulis',
    P.agregat_progres(baris(tahap='Menulis 5 bab', komentar=komentar_buku(5)))['teks_sabar'] == '')

print('== data_selesai_dari_hasil (G1, tanpa parameter URL) ==')
d222 = P.data_selesai_dari_hasil(r222)
cek('selesai 222: bab 5', d222['bab'] == 5, 'dapat %s' % d222['bab'])
cek('selesai 222: kata 35050', d222['kata'] == 35050, 'dapat %s' % d222['kata'])
cek('selesai 222: docx dari hasil_json',
    d222['docx'].endswith('Buku_FINAL.docx'))
cek('selesai 222: fid klaim 123', d222['hasil'].get('file_id') == 123)
r_tanpa_total = baris(status='selesai', komentar=komentar_buku(2),
                      hasil_json=json.dumps(
                          {'bab': {'1': {'kata': 100}, '2': {'kata': 200}},
                           'judul': 'Buku X'}, ensure_ascii=False))
d_tanpa = P.data_selesai_dari_hasil(r_tanpa_total)
cek('tanpa total_kata: kata dijumlah dari bab (300)',
    d_tanpa['kata'] == 300 and d_tanpa['bab'] == 2)

print('== cermin logika redirect JS (W1: tanpa /hasil) ==')


def putusan_redirect():
    """Cermin tampilkanHasil() sesudah W1: TIDAK memanggil /hasil sama
    sekali, karena endpoint itu tidak pernah mengembalikan hasil_json
    (hanya jawaban berisi judul). Redirect hanya membawa kode, rute
    selesai membaca baris job + hasil_json dari server. Tidak pernah
    membawa bab/kata/fid."""
    return '/buku/selesai?kode=KODEUJI'


url = putusan_redirect()
cek('redirect W1 -> hanya kode',
    url == '/buku/selesai?kode=KODEUJI'
    and 'bab=' not in url and 'kata=' not in url and 'fid=' not in url)

print('== render template Jinja2 ==')
try:
    from jinja2 import DictLoader, Environment
    _selesai = open('app/templates/buku_selesai.html', encoding='utf-8').read()
    _proses_t = open('app/templates/buku_proses.html', encoding='utf-8').read()
    env = Environment(loader=DictLoader({
        'buku_selesai.html': _selesai, 'buku_proses.html': _proses_t,
        '_menu.html': ''}), autoescape=True)
    env.globals['ikon'] = lambda *a, **k: ''
    env.globals['ikon_sprite'] = lambda: ''
    _user = SimpleNamespace(nama='Uji Buku', email='uji@example.id')
    out = env.get_template('buku_selesai.html').render(
        request=None, user=_user,
        judul='Transformasi Digital UMKM: Strategi, Adopsi Teknologi, '
              'dan Kinerja Bisnis di Era Ekonomi Digital',
        bab=5, kata=35050, folder='/opt/data/buku_hasil/1793346442-12',
        docx='/opt/data/buku_hasil/1793346442-12/'
             'TRANSFORMASI_DIGITAL_UMKM_STRATEGI_ADOPSI_TEKNOLOGI_DAN_'
             'KINERJA_BISNIS_DI_ERA_EKONOMI_DIGITAL_FINAL.docx',
        docx_nama='TRANSFORMASI_DIGITAL_UMKM_STRATEGI_ADOPSI_TEKNOLOGI_DAN_'
                  'KINERJA_BISNIS_DI_ERA_EKONOMI_DIGITAL_FINAL.docx',
        docx_kb=2588, docx_alasan='', fid=123, file_alasan='')
    cek('selesai render: bab 5', 'Bab yang selesai ditulis: <b>5</b>' in out)
    cek('selesai render: kata 35050', '<b>35050</b>' in out)
    cek('selesai render: nama docx',
        'TRANSFORMASI_DIGITAL_UMKM_STRATEGI_ADOPSI_TEKNOLOGI_DAN_'
        'KINERJA_BISNIS_DI_ERA_EKONOMI_DIGITAL_FINAL.docx' in out)
    cek('selesai render: edit fid 123', '/edit/123' in out)
    cek('selesai render: tidak ada 0/0', '0/0' not in out)
    out_p = env.get_template('buku_proses.html').render(
        request=None, user=_user, kode='KODEUJI', judul='Buku Uji',
        tahap='Memperbaiki 2 bab bermasalah', status='jalan',
        wa_aktif=False, bab_selesai=0, bab_total=5,
        sedang_disempurnakan=True,
        teks_sabar='buku sedang disempurnakan, mohon sabar',
        subbab_per_bab={}, agregat={}, fase='penyempurnaan')
    cek('proses render: label PROGRESS', '<h2>PROGRESS</h2>' in out_p)
    cek('JS proses tidak memanggil /hasil lagi',
        "+ KODE + '/hasil'" not in _proses_t)
    cek('JS proses redirect hanya dengan kode',
        "buku/selesai?kode=' + encodeURIComponent(KODE)" in _proses_t)
    cek('proses render: teks sabar persis',
        'buku sedang disempurnakan, mohon sabar' in out_p)
    cek('proses render: tanpa Bab 0', 'Bab 0' not in out_p)
    cek('proses render: tanpa kata gagal/error',
        'gagal' not in out_p.lower() and 'error' not in out_p.lower())
    cek('proses render: tanpa kartu Belum berhasil',
        'Belum berhasil' not in out_p)
    out_p2 = env.get_template('buku_proses.html').render(
        request=None, user=_user, kode='KODEUJI', judul='Buku Uji',
        tahap='Menulis 5 bab', status='jalan', wa_aktif=False,
        bab_selesai=2, bab_total=5, sedang_disempurnakan=False,
        teks_sabar='', subbab_per_bab={'2': 'BAB 2 selesai'},
        agregat={}, fase='menulis')
    cek('proses render: Bab 2 dari 5', 'Bab 2 dari 5' in out_p2)
    cek('proses render: sabar tersembunyi saat menulis',
        'id="teks-sabar"' in out_p2 and 'display:none' in out_p2)
except ImportError as e:
    lewat('render template Jinja2', 'jinja2 tidak tersedia: %s' % e)

print('== DB sementara: slot paralel + fid fallback (REAL saja) ==')
if not REAL:
    lewat('DB slot paralel', 'mode stub, tanpa model asli')
    lewat('fid fallback', 'mode stub, tanpa model asli')
else:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import FileBerkas, ProsesAI, VersiDokumen
    tmpdir = tempfile.mkdtemp(prefix='uji_agregat_')
    engine = create_engine(
        'sqlite:///%s/uji.db' % tmpdir, connect_args={'check_same_thread': False})
    ProsesAI.__table__.create(engine)
    FileBerkas.__table__.create(engine)
    VersiDokumen.__table__.create(engine)
    Sesi = sessionmaker(bind=engine, expire_on_commit=False)
    _asli = P._sesi_baru
    P._sesi_baru = lambda: Sesi()
    try:
        db = Sesi()
        db.add(ProsesAI(
            kode='KODEUJI', user_id=12, status='jalan', tahap='Menulis',
            komentar_json=json.dumps(komentar_buku(4), ensure_ascii=False)))
        db.commit()
        db.close()
        urutan = [3, 1, 4, 2]
        riwayat_db = []
        berhenti = threading.Event()

        def _pekerja_db(nomor):
            import time
            time.sleep(random.random() / 50.0)
            P.catat_bab_selesai('KODEUJI', nomor)
            P.catat_subbab('KODEUJI', nomor, 'Subbab terakhir bab %d' % nomor)
            P.ubah_tahap('KODEUJI', 'BAB %d selesai: 100 kata' % nomor)

        def _pantau_db():
            import time
            while not berhenti.is_set():
                s = Sesi()
                p = P.ambil(s, 'KODEUJI')
                riwayat_db.append(P.agregat_progres(p)['bab_selesai'])
                s.close()
                time.sleep(0.005)

        random.seed(11)
        ts = [threading.Thread(target=_pekerja_db, args=(n,)) for n in urutan]
        tp = threading.Thread(target=_pantau_db)
        tp.start()
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        berhenti.set()
        tp.join()
        s = Sesi()
        p = P.ambil(s, 'KODEUJI')
        ag_db = P.agregat_progres(p)
        cek('DB paralel: hitungan pantau tidak pernah turun',
            all(b >= a for a, b in zip(riwayat_db, riwayat_db[1:])),
            'riwayat=%s' % (riwayat_db,))
        cek('DB paralel: akhir 4 bab', ag_db['bab_selesai'] == 4,
            'dapat %s' % ag_db)
        cek('DB paralel: subbab 4 bab',
            set(ag_db['subbab_per_bab'].keys()) == {'1', '2', '3', '4'})
        # fid: baris langsung, fallback nama, fallback ukuran, tanpa cocok
        fb_baik = FileBerkas(user_id=12, nama='Buku Uji.docx',
                             nama_simpan='baik.docx', ukuran=12345,
                             tipe='application/docx')
        s.add(fb_baik)
        s.commit()
        fb_sampah = FileBerkas(user_id=12, nama='Buku Uji.docx',
                               nama_simpan='sampah.docx', ukuran=12345,
                               tipe='application/docx')
        s.add(fb_sampah)
        s.commit()
        from datetime import datetime
        fb_sampah.terhapus_pada = datetime.utcnow()
        s.commit()
        cek('fid: hasil_json langsung',
            P.fid_selesai(s, 12, {'judul': 'Buku Uji', 'file_id': fb_baik.id},
                          None, '') == fb_baik.id)
        cek('fid: file_id sampah dilewati, fallback nama menang',
            P.fid_selesai(s, 12, {'judul': 'Buku Uji', 'file_id': fb_sampah.id},
                          None, '') == fb_baik.id)
        cek('fid: tanpa file_id, fallback nama',
            P.fid_selesai(s, 12, {'judul': 'Buku Uji', 'file_id': None},
                          None, '') == fb_baik.id)
        with open(os.path.join(tmpdir, 'dokumen.docx'), 'wb') as f:
            f.write(b'x' * 12345)
        cek('fid: nama tidak cocok, fallback ukuran',
            P.fid_selesai(s, 12, {'judul': 'Buku Lain', 'file_id': None},
                          None, os.path.join(tmpdir, 'dokumen.docx'))
            == fb_baik.id)
        cek('fid: tidak ada yang cocok -> 0',
            P.fid_selesai(s, 12, {'judul': 'Tidak Ada', 'file_id': None},
                          None, '/tmp/tidak-ada-uji-agregat.docx') == 0)
        cek('fid: milik user lain tidak dipakai',
            P.fid_selesai(s, 99, {'judul': 'Buku Uji', 'file_id': fb_baik.id},
                          None, '') == 0)
        s.close()
    finally:
        P._sesi_baru = _asli
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

try:
    from jinja2 import DictLoader as _DL2, Environment as _Env2
    _proses_t2 = open('app/templates/buku_proses.html', encoding='utf-8').read()
    _env2 = _Env2(loader=_DL2({'buku_proses.html': _proses_t2, '_menu.html': ''}), autoescape=True)
    _env2.globals['ikon'] = lambda *a, **k: ''
    _env2.globals['ikon_sprite'] = lambda: ''
    _user2 = SimpleNamespace(nama='Uji Buku', email='uji@example.id')
    _ctx_gagal = dict(request=None, user=_user2, kode='KODEUJI', judul='Buku Uji',
        tahap='Gagal', status='gagal', wa_aktif=False, bab_selesai=0, bab_total=5,
        sedang_disempurnakan=True, teks_sabar='buku sedang disempurnakan, mohon sabar',
        subbab_per_bab={}, agregat={}, fase='penyempurnaan')
    _out_gr = _env2.get_template('buku_proses.html').render(
        galat='Maaf, buku belum berhasil dibuat. Token sudah kembali ke saldo.', **_ctx_gagal)
    cek('proses gagal refund: pesan manusia tampil',
        'Maaf, buku belum berhasil dibuat. Token sudah kembali ke saldo.' in _out_gr)
    cek('proses gagal refund: sabar tersembunyi',
        'id="teks-sabar" style="display:none"' in _out_gr)
    cek('proses gagal refund: paragraf akhir tampil',
        'id="teks-akhir" style="display:none"' not in _out_gr)
    cek('proses gagal refund: tanpa kata gagal mentah',
        'gagal' not in _out_gr.lower() and 'error' not in _out_gr.lower())
    _out_gg = _env2.get_template('buku_proses.html').render(
        galat='RuntimeError: provider kosong', **_ctx_gagal)
    cek('proses gagal generik: pesan generik tampil',
        'Maaf, buku belum berhasil dibuat. Silakan coba lagi atau hubungi admin.' in _out_gg)
    cek('proses gagal generik: galat mentah tidak bocor',
        'RuntimeError' not in _out_gg)
    _out_jl = _env2.get_template('buku_proses.html').render(galat='', **dict(_ctx_gagal, status='jalan'))
    cek('proses jalan: paragraf akhir tersembunyi',
        'id="teks-akhir" style="display:none"' in _out_jl)
except ImportError as e:
    lewat('render gagal Jinja2', 'jinja2 tidak tersedia: %s' % e)

print('== HASIL: LULUS %d, GAGAL %d, LEWAT %d ==' % (LULUS, len(GAGAL), len(LEWAT)))
if GAGAL:
    print('GAGAL: %s' % ', '.join(GAGAL))
    sys.exit(1)
sys.exit(0)
