"""Verifikasi live optimasi Jev 1.14 RONDE 2 — SESUDAH optimasi (2 run/naskah).

Jalankan DI DALAM container eduai-app:  python3 -u /tmp/jev-r2/jalankan_r2.py
- Memuat peta3_jev.py + app.* dari scratch /tmp/jev-r2 (kode BRANCH
  agen/wulan/optimalkan-jev-hakim-v5 HEAD 9218170, RULE_VERSION
  jev-peta-v9, MODEL_DEFAULT 1.14), BUKAN /app. Dijaga assert __file__.
- Impor EAGER (pelajaran opt2 ronde 1): app.sambung_kode dan
  app.profil_kampus diimpor SEBELUM app.hakim_peta (yang menyisipkan
  '/app' di posisi 0 sys.path); impor MALAS di dalam peta3_jev jatuh ke
  /app (deploy) bila modul itu belum ada di sys.modules. SEMUA modul
  di-assert __file__-nya dari scratch, plus bukti fungsi sk() v8/v9
  sebelum run pertama — bila tidak cocok, BERHENTI.
- SETIAP run diawali probe bukti model yang dilayani; bila BUKAN
  jev-1.14.0, run itu BATAL (script berhenti, exit 1, hasil parsial
  disimpan dulu).
- 2 run petakan(fid) per naskah: 81, 112, 115. Cache peta DIMATIKAN.
  DB hanya dibaca (sidik files + proses_ai sebelum/sesudah tiap run,
  assert tidak berubah).
- Bila satu run gagal total (exception / jev_mati), ulangi SATU kali
  saja; bila tetap gagal, simpan parsial dan berhenti (exit 1).
- Pembungkus app.jev.tanya menghitung panggilan per jenis
  (choice/noul/lain) PLUS mencatat tiap panggilan 'noul' (stitch):
  bahan, pertanyaan, jawaban.
- Format per run SAMA seperti hasil_sebelum_opt_114.json (baris
  lengkap, kand, label, semua, conf, goyang + daftarnya, keempat
  koreksi, bab_kode/ganda/demosi, tanya_ulang + balik PB, gelombang,
  panggilan per jenis, wall, goyang_jml, sidik) + nomor run dan
  penanda ulangi + 'bab' gabungan (label Jev + gabung kode, untuk
  gerbang) + 'stitch_pasangan_ditanya_jml' (jumlah pasangan di dalam
  panggilan noul; 'stitch_pasangan_jml' tetap jumlah panggilan noul
  seperti sebelumnya).
- Hasil JSON ke /tmp/jev-r2/hasil_r2_114.json (disalin keluar).
- BIAYA: ~140 panggilan Jev petakan (2 x (7 + ~30 + ~29)) + 6 probe.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-r2')
os.chdir('/tmp/jev-r2')

import json
import re
import time
import urllib.request

_src_peta = open('/tmp/jev-r2/peta3_jev.py', encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src_peta, 'sisa sys.path jev-v4 masih ada!'

# URUTAN IMPOR PENTING (opt3): jev + konversi + satpam + sambung_kode +
# profil_kampus, SEMUA EAGER sebelum hakim_peta. Alasan: hakim_peta.py:57
# menyisipkan '/app' di posisi 0 sys.path, dan `app` adalah namespace
# package — impor MALAS di dalam peta3_jev (sambung_kode di _stitch_baris,
# perbaiki_spasi_huruf / perbaiki_fragmen_huruf di _susun_dari_bersih,
# profil_kampus) akan jatuh ke /app/app/*.py (deploy v7) bila modul itu
# belum ada di sys.modules. Pelari opt2 hanya assert modul impor-eager.
import peta3_jev as P
import app.jev as _J
import app.konversi as K
import app.satpam as S
import app.sambung_kode as SK
import app.profil_kampus as PK
import app.hakim_peta as H

print('peta3_jev dari:', P.__file__, flush=True)
print('jev dari:', _J.__file__, '| satpam dari:', S.__file__, flush=True)
print('konversi dari:', K.__file__, '| hakim dari:', H.__file__, flush=True)
print('sambung_kode dari:', SK.__file__, flush=True)
print('profil_kampus dari:', PK.__file__, flush=True)
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT, flush=True)
assert P.__file__.startswith('/tmp/jev-r2/'), 'peta3_jev BUKAN dari scratch!'
assert _J.__file__.startswith('/tmp/jev-r2/'), 'jev BUKAN dari scratch!'
assert K.__file__.startswith('/tmp/jev-r2/'), 'konversi BUKAN dari scratch!'
assert S.__file__.startswith('/tmp/jev-r2/'), 'satpam BUKAN dari scratch!'
assert SK.__file__.startswith('/tmp/jev-r2/'), 'sambung_kode BUKAN dari scratch!'
assert PK.__file__.startswith('/tmp/jev-r2/'), 'profil_kampus BUKAN dari scratch!'
assert H.__file__.startswith('/tmp/jev-r2/'), 'hakim BUKAN dari scratch!'
assert _J.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14', \
    'MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT
assert P.RULE_VERSION == 'jev-peta-v9', \
    'RULE_VERSION BUKAN v9: %r' % P.RULE_VERSION
# Bukti fungsi v8/v9 (0 Jev) di dalam pelari juga.
_bukti_sk = SK.sambung_kode('Kalimat pertama yang belum selesai',
                            'dan berlanjut di sini.')
print('bukti sk() v8:', _bukti_sk, '| modul:', SK.__file__, flush=True)
assert _bukti_sk is True, 'sambung_kode probe BUKAN True — kode v7 termuat, BERHENTI!'
_bukti_r21 = SK.sambung_kode('pasaran.”', '- “AyuMeera bisa jadi pilihan')
print('bukti sk() R2-1 (B-dash -> False):', _bukti_r21, flush=True)
assert _bukti_r21 is False, 'R2-1 BUKAN False — kode v8 termuat, BERHENTI!'
_bukti_r22 = SK.sambung_kode(
    '2. Manfaat Praktis',
    'Manfaat praktis dalam penelitian ini adalah dapat membantu')
print('bukti sk() R2-2 (judul 1 tingkat + ekor -> False):', _bukti_r22,
      flush=True)
assert _bukti_r22 is False, 'R2-2 BUKAN False — kode v8 termuat, BERHENTI!'
_bukti_r22b = SK.sambung_kode('1. Mendukung Strategi',
                              'Agresif (Khoironi, 2023)')
print('bukti sk() R2-2 lewat (lanjutan judul -> None):', _bukti_r22b,
      flush=True)
assert _bukti_r22b is None, 'R2-2 lewat BUKAN None — aturan kebablasan, BERHENTI!'

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'


def sidik():
    s = _ai.SessionLocal()
    try:
        return (s.execute(_text('SELECT COUNT(*) FROM files')).scalar(),
                s.execute(_text('SELECT COUNT(*) FROM proses_ai')).scalar(),
                s.execute(_text('SELECT MAX(id) FROM proses_ai')).scalar())
    finally:
        s.close()


def probe_model(model_str):
    """Bukti model yang DILAYANI jembatan untuk string model ini."""
    badan = {
        'model': model_str,
        'messages': [{'role': 'user',
                      'content': json.dumps({
                          'state': 'PROBE MODEL: teks ini hanya untuk '
                                   'memeriksa model yang dilayani.',
                          'questions': {'probe': {
                              'type': 'noul',
                              'instructions': 'Apakah teks ini menyebut '
                                              'sebuah model?'}}})}], 
    }
    req = urllib.request.Request(
        JEMBATAN, data=json.dumps(badan).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode())
    return {'model_dilayani': d.get('model'),
            'satpam_penyedia': d.get('satpam_penyedia'),
            'satpam_jejak': d.get('satpam_jejak'),
            'provider': d.get('provider')}


hitung = {'choice': 0, 'noul': 0, 'lain': 0}
log_stitch = []  # tiap panggilan 'noul': {bahan, pertanyaan, jawaban}
_orig_jev_tanya = _J.tanya


def _bungkus(bahan, pertanyaan, *a, **k):
    try:
        jenis = {(q or {}).get('type') for q in (pertanyaan or {}).values()}
    except Exception:
        jenis = set()
    if 'choice' in jenis:
        hitung['choice'] += 1
    elif 'noul' in jenis:
        hitung['noul'] += 1
    else:
        hitung['lain'] += 1
    jawaban = _orig_jev_tanya(bahan, pertanyaan, *a, **k)
    if 'noul' in jenis:
        try:
            log_stitch.append({
                'bahan': bahan,
                'pertanyaan': json.loads(json.dumps(pertanyaan, ensure_ascii=False, default=str)),
                'jawaban': json.loads(json.dumps(jawaban, ensure_ascii=False, default=str)),
            })
        except Exception as e:
            log_stitch.append({'bahan': str(bahan)[:500],
                               'pertanyaan': str(pertanyaan)[:500],
                               'jawaban': str(jawaban)[:500],
                               'catat_galat': str(e)})
    return jawaban


_J.tanya = _bungkus


def _label_hitung(label):
    lab = {}
    for v in label.values():
        lab[v] = lab.get(v, 0) + 1
    return lab


def _simpan(hasil):
    with open('/tmp/jev-r2/hasil_r2_114.json', 'w') as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)


def _normal_bab(judul):
    return re.sub(r'^\d+\.\s*', '', (judul or '').strip())


def _bab_gabung(r):
    """Judul BAB gabungan (label Jev + gabung kode), cara yang sama seperti
    pelari baseline114 / jalankan_gerbang.py — untuk gerbang offline."""
    bab = set()
    baris = r['baris']
    for i, v in sorted(r['label'].items()):
        if v == 'bab':
            t = _normal_bab(baris[i] if 0 <= i < len(baris) else '')
            if t:
                bab.add(t)
    for _penanda, _judul in (r.get('gabung') or {}).values():
        t = _normal_bab(('%s %s' % (_penanda, _judul)).strip())
        if re.match(r'^BAB\s+[IVX0-9]+', t):
            bab.add(t)
    return sorted(bab)


def _ringkas_run(r, fid, run_no, wall, pgl, s_sebelum, s_sesudah, ulangi,
                 galat_pertama):
    lab = _label_hitung(r['label'])
    return {
        'fid': fid,
        'run': run_no,
        'ulangi': ulangi,
        'galat_pertama': galat_pertama,
        'wall': wall,
        'panggilan': pgl,
        'panggilan_total': sum(pgl.values()),
        'stitch_pasangan_jml': len(log_stitch),
        'stitch_pasangan_ditanya_jml': sum(
            len(e.get('pertanyaan') or {}) for e in log_stitch),
        'stitch_log': list(log_stitch),
        'bab': _bab_gabung(r),
        'baris': list(r['baris']),
        'kand': [[i, t] for i, t in r['kand']],
        'kand_jml': r['kand_jml'],
        'label': {str(i): v for i, v in r['label'].items()},
        'label_hitung': lab,
        'semua': {str(i): list(v) for i, v in r['semua'].items()},
        'conf': {str(i): v for i, v in r['p'].items()},
        'goyang': [[i, list(v)] for i, v in r['goyang']],
        'goyang_jml': len(r['goyang']),
        'koreksi_label': r.get('koreksi_label'),
        'koreksi_spss': r.get('koreksi_spss'),
        'koreksi_kecil': r.get('koreksi_kecil'),
        'koreksi_batas_paragraf': r.get('koreksi_batas_paragraf'),
        'bab_kode': r.get('bab_kode'),
        'bab_ganda': r.get('bab_ganda'),
        'bab_demosi': r.get('bab_demosi'),
        'tanya_ulang_jml': r.get('tanya_ulang_jml'),
        'tanya_ulang_goyang_pb_jml': r.get('tanya_ulang_goyang_pb_jml'),
        'tanya_ulang_goyang_pb_balik': r.get('tanya_ulang_goyang_pb_balik'),
        'tanya_ulang_goyang_pb_balik_jml': r.get('tanya_ulang_goyang_pb_balik_jml'),
        'tanya_ulang_gelombang': r.get('tanya_ulang_gelombang'),
        'gelombang': r['gelombang'],
        'gabung_jml': len(r['gabung']),
        'buang_jml': len(r['buang']),
        'gagal': r['gagal'],
        'jev_mati': r.get('jev_mati'),
        'stitch_pakai': r.get('stitch_pakai'),
        'waktu_gelombang': r.get('waktu'),
        'waktu_stitch': r.get('waktu_stitch'),
        'waktu_total': r.get('waktu_total'),
        'sidik_sebelum': list(s_sebelum),
        'sidik_sesudah': list(s_sesudah),
    }


hasil = {'model_diminta': _J.MODEL_DEFAULT,
         'rule_version': P.RULE_VERSION,
         'cabang': 'agen/wulan/optimalkan-jev-hakim-v5',
         'komit': '9218170',
         'pelari': 'jalankan_r2.py (r2, impor eager sambung_kode+profil_kampus)',
         'bukti_impor': {'sk_probe': _bukti_sk,
                         'sk_r21_dash_false': _bukti_r21,
                         'sk_r22_judul1_false': _bukti_r22,
                         'sk_r22_lewat_none': _bukti_r22b,
                         'sambung_kode_file': SK.__file__,
                         'profil_kampus_file': PK.__file__,
                         'peta3_jev_file': P.__file__,
                         'rule_version': P.RULE_VERSION},
         'probe_per_run': [],
         'run': {}}
total_petakan = 0
total_probe = 0
for fid in (81, 112, 115):
    hasil['run'][str(fid)] = []
    for run_no in (1, 2):
        bukti = probe_model(_J.MODEL_DEFAULT)
        total_probe += 1
        print('fid=%s run %d bukti layan: %s'
              % (fid, run_no, json.dumps(bukti, ensure_ascii=False)), flush=True)
        hasil['probe_per_run'].append({'fid': fid, 'run': run_no,
                                       'bukti': bukti})
        if 'jev-1.14.0' not in (bukti.get('model_dilayani') or ''):
            print('MODEL SALAH DILAYANI: %r — RUN BATAL, TIDAK MASUK HASIL'
                  % bukti.get('model_dilayani'), flush=True)
            hasil['panggilan_petakan_total'] = total_petakan
            hasil['panggilan_probe_total'] = total_probe
            hasil['panggilan_total'] = total_petakan + total_probe
            _simpan(hasil)
            sys.exit(1)
        # Satu run, ulangi MAKSIMAL 1x bila gagal total.
        r = None
        galat_pertama = None
        ulangi = False
        for percobaan in (1, 2):
            P._CACHE_PETA.clear()
            for k in hitung:
                hitung[k] = 0
            del log_stitch[:]
            s_sebelum = sidik()
            t0 = time.time()
            try:
                r_coba = P.petakan(fid)
            except Exception as e:
                r_coba = None
                galat_pertama = '%s: %s' % (type(e).__name__, e)
                print('fid=%s run %d percobaan %d GALAT: %s'
                      % (fid, run_no, percobaan, galat_pertama), flush=True)
            if r_coba is not None and not r_coba.get('jev_mati'):
                r = r_coba
                wall = round(time.time() - t0, 2)
                pgl = dict(hitung)
                break
            if r_coba is not None and r_coba.get('jev_mati'):
                galat_pertama = 'jev_mati=True'
                print('fid=%s run %d percobaan %d: Jev mati'
                      % (fid, run_no, percobaan), flush=True)
            if percobaan == 1:
                ulangi = True
                print('fid=%s run %d: ulangi 1x (jeda 5 dtk)'
                      % (fid, run_no), flush=True)
                time.sleep(5)
                continue
            print('fid=%s run %d GAGAL TOTAL setelah 1 ulangan — BERHENTI'
                  % (fid, run_no), flush=True)
            hasil['panggilan_petakan_total'] = total_petakan
            hasil['panggilan_probe_total'] = total_probe
            hasil['panggilan_total'] = total_petakan + total_probe
            _simpan(hasil)
            sys.exit(1)
        total_petakan += sum(pgl.values())
        s_sesudah = sidik()
        ring = _ringkas_run(r, fid, run_no, wall, pgl, s_sebelum,
                            s_sesudah, ulangi, galat_pertama)
        hasil['run'][str(fid)].append(ring)
        print(f'=== fid={fid} run {run_no} wall: {wall} dtk | panggilan: '
              f'{ring["panggilan_total"]} {pgl} | stitch: '
              f'{len(log_stitch)} panggilan / '
              f'{ring["stitch_pasangan_ditanya_jml"]} pasangan | bab: '
              f'{ring["bab"]} | label: {ring["label_hitung"]} | '
              f'goyang: {ring["goyang_jml"]} | tanya-ulang: '
              f'{ring["tanya_ulang_jml"]} | ulangi: {ulangi} | '
              f'sidik: {s_sebelum} -> {s_sesudah} ===', flush=True)
        assert list(s_sebelum) == list(s_sesudah), \
            'DB BERUBAH selama run fid=%s!' % fid

hasil['panggilan_petakan_total'] = total_petakan
hasil['panggilan_probe_total'] = total_probe
hasil['panggilan_total'] = total_petakan + total_probe
_simpan(hasil)
print('TOTAL panggilan petakan: %d | probe: %d | gabungan: %d'
      % (total_petakan, total_probe, total_petakan + total_probe), flush=True)
print('SELESAI')
