"""Verifikasi live lapisan v11 — naskah UJI latihan 112 (tahap 5).

Jalankan DI DALAM container eduai-app:
  VERIF_KODES="AD3,Y2,..." VERIF_TAG=A python3 -u /tmp/jev-verifikasi-v11/jalankan_verifikasi_v11.py
- Memuat peta3_jev.py + app.* dari scratch /tmp/jev-verifikasi-v11 (kode
  BRANCH agen/wulan/optimalkan-jev-hakim-v5, RULE_VERSION jev-peta-v11,
  MODEL_DEFAULT 1.14), BUKAN /app. Dijaga assert __file__.
- URUTAN IMPOR PENTING: app.sambung_kode + app.profil_kampus EAGER
  SEBELUM app.hakim_peta (yang menyisipkan '/app' di posisi 0 sys.path);
  bukti sk() R2-1/R2-2 + profil_bentuk() v11 sebelum run pertama — bila
  tidak cocok, BERHENTI.
- SETIAP run diawali probe bukti model; bila BUKAN jev-1.14.0 (2x coba),
  entri itu dicatat GAGAL (probe salah) dan lanjut ke entri berikut.
- 1 run petakan_dari_teks() per entri (teks dari teks/ di scratch, sudah
  dibersihkan dulu dengan state.buang_daftar_isi — SAMA seperti jalur
  tahap 1). Cache peta DIMATIKAN. DB hanya dibaca (sidik files +
  proses_ai sebelum/sesudah tiap run; bila berubah, dicatat bendera).
- Sesudah petakan, Hakim v2 periksa_peta() (panggilan Jev hakim dihitung
  terpisah; bila hakim galat, dicatat, bukan crash).
- Bila jembatan 429/503/timeout: tunggu ~60 dtk, ulangi; sesudah 3x
  tetap gagal, entri dicatat GAGAL dan lanjut.
- Hasil JSON disimpan INKREMENTAL ke
  /tmp/jev-verifikasi-v11/hasil_verifikasi_v11_<TAG>.json sesudah tiap
  entri (parsial selamat bila proses mati).
- BIAYA: ~9 run + 9 probe (+ hakim seperlunya) per subset.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

SCRATCH = os.environ.get('SCRATCH', '/tmp/jev-verifikasi-v11')
sys.path.insert(0, SCRATCH)
os.chdir(SCRATCH)

import json
import re
import time
import urllib.request

_src_peta = open(os.path.join(SCRATCH, 'peta3_jev.py'), encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src_peta, 'sisa sys.path jev-v4 masih ada!'

# ── IMPOR EAGER (urutan penting: sambung_kode + profil_kampus dulu) ──
import app.sambung_kode as _SK
import app.profil_kampus as PK
import app.jev as _J
import peta3_jev as P
import app.konversi as K
import app.satpam as S
import app.hakim_peta as H
from app import state as _ST

print('peta3_jev dari:', P.__file__, flush=True)
print('jev dari:', _J.__file__, '| satpam dari:', S.__file__, flush=True)
print('konversi dari:', K.__file__, '| hakim dari:', H.__file__, flush=True)
print('sambung_kode dari:', _SK.__file__, '| state dari:', _ST.__file__, flush=True)
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT, flush=True)
for _nama, _mod in (('peta3_jev', P), ('jev', _J), ('konversi', K),
                    ('satpam', S), ('hakim', H), ('sambung_kode', _SK),
                    ('profil_kampus', PK), ('state', _ST)):
    assert _mod.__file__.startswith(SCRATCH + '/'), \
        '%s BUKAN dari scratch: %s' % (_nama, _mod.__file__)
assert _J.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14', \
    'MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT
assert P.RULE_VERSION == 'jev-peta-v11', \
    'RULE_VERSION BUKAN v11: %r' % P.RULE_VERSION
# Bukti fungsi v9/v10 (0 Jev) — aturan stitch R2-1/R2-2.
_b1 = _SK.sambung_kode('Kalimat pertama yang belum selesai', 'dan berlanjut di sini.')
print('bukti sk() dasar:', _b1, flush=True)
assert _b1 is True, 'sk() dasar BUKAN True — BERHENTI!'
_b2 = _SK.sambung_kode('pasaran.”', '- “AyuMeera bisa jadi pilihan')
print('bukti sk() R2-1 (B-dash -> False):', _b2, flush=True)
assert _b2 is False, 'R2-1 BUKAN False — BERHENTI!'
_b3 = _SK.sambung_kode('2. Manfaat Praktis',
                      'Manfaat praktis dalam penelitian ini adalah dapat membantu')
print('bukti sk() R2-2 (judul 1 tingkat + ekor -> False):', _b3, flush=True)
assert _b3 is False, 'R2-2 BUKAN False — BERHENTI!'
# Bukti Lapis 1 v11 (0 Jev) — profil_bentuk().
_p_romawi = P.profil_bentuk(
    'I. PENDAHULUAN\nII. TINJAUAN PUSTAKA\nIII. METODE PENELITIAN\n'
    'IV. HASIL DAN PEMBAHASAN\nV. KESIMPULAN DAN SARAN\n')
print('bukti profil romawi_tanpa_bab:', _p_romawi['penomoran_bab'],
      _p_romawi['romawi_judul'], flush=True)
assert _p_romawi['penomoran_bab'] == 'romawi_tanpa_bab', \
    'profil Romawi BUKAN romawi_tanpa_bab — BERHENTI!'
assert _p_romawi['aturan']['judul_romawi_tanpa_bab'] is True
_p_ch = P.profil_bentuk('CHAPTER I\nINTRODUCTION\nCHAPTER II\nREVIEW OF LITERATURE\n')
print('bukti profil chapter:', _p_ch['penomoran_bab'], _p_ch['chapter'], flush=True)
assert _p_ch['penomoran_bab'] == 'chapter', 'profil CHAPTER BUKAN chapter — BERHENTI!'
_p_bom = P.profil_bentuk('\ufeffBAB I PENDAHULUAN\nIsi bab satu.\n')
print('bukti profil BOM:', _p_bom['bom_jml'], flush=True)
assert _p_bom['bom_jml'] >= 1, 'profil BOM 0 — BERHENTI!'
_p_pem = P.profil_bentuk('===== SKRIPSI TIAR.doc =====\nI. PENDAHULUAN\n')
print('bukti profil pemisah:', _p_pem['pemisah_gabung_jml'], flush=True)
assert _p_pem['pemisah_gabung_jml'] >= 1, 'profil pemisah 0 — BERHENTI!'

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
TAG = os.environ.get('VERIF_TAG', 'X')
HASIL_PATH = os.path.join(SCRATCH, 'hasil_verifikasi_v11_%s.json' % TAG)


def sidik():
    s = _ai.SessionLocal()
    try:
        return (s.execute(_text('SELECT COUNT(*) FROM files')).scalar(),
                s.execute(_text('SELECT COUNT(*) FROM proses_ai')).scalar(),
                s.execute(_text('SELECT MAX(id) FROM proses_ai')).scalar())
    finally:
        s.close()


def probe_model(model_str):
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
    return _orig_jev_tanya(bahan, pertanyaan, *a, **k)


_J.tanya = _bungkus


def _teks_baris(r, i):
    b = r['baris']
    if isinstance(b, dict):
        return b.get(i, '')
    try:
        return b[i] if 0 <= i < len(b) else ''
    except Exception:
        return ''


def _normal_bab(judul):
    return re.sub(r'^\d+\.\s*', '', (judul or '').strip())


def _bab_gabung(r):
    bab = set()
    for i, v in sorted(r['label'].items()):
        if v == 'bab':
            t = _normal_bab(_teks_baris(r, i))
            if t:
                bab.add(t)
    for _penanda, _judul in (r.get('gabung') or {}).values():
        t = _normal_bab(('%s %s' % (_penanda, _judul)).strip())
        if re.match(r'^BAB\s+[IVX0-9]+', t):
            bab.add(t)
    return sorted(bab)


def _bab_semua(r):
    """Semua judul BAB: label 'bab' + SEMUA entri gabung (v11: judul
    Romawi tanpa kata BAB dan CHAPTER polos masuk gabung, bukan label)."""
    bab = set(_bab_gabung(r))
    for _penanda, _judul in (r.get('gabung') or {}).values():
        t = ('%s %s' % (_penanda, _judul)).strip()
        if t:
            bab.add(t)
    return sorted(bab)


def _bentuk(teks):
    """Catatan bentuk dari teks bersih (0 Jev)."""
    up = teks.upper()
    return {
        'chapter': len(re.findall(r'\bCHAPTER\s+[IVX0-9]+\b', up)),
        'bab_romawi': len(re.findall(r'\bBAB\s+[IVX]+\b', up)),
        'bab_arab': len(re.findall(r'\bBAB\s+\d+\b', up)),
        'bab_titik': len(re.findall(r'\bBAB\.\s*\d+', up)),
        'tabel_kata': len(re.findall(r'\bTABEL\b', up)),
        'daftar_isi': 'DAFTAR ISI' in up,
        'sistematika_kata': len(re.findall(r'SISTEMATIKA', up)),
        'kata': len(teks.split()),
        'baris': len(teks.split('\n')),
    }


def _simpan(hasil):
    tmp = HASIL_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HASIL_PATH)


MANIFEST = json.load(open(os.path.join(SCRATCH, 'manifest_verifikasi_v11.json')))
KODES = [k.strip() for k in os.environ.get('VERIF_KODES', '').split(',') if k.strip()]
ENTRI = [e for e in MANIFEST if e['kode'] in KODES]
print('entri diminta: %d dari %d (tag %s)' % (len(ENTRI), len(MANIFEST), TAG), flush=True)
assert len(ENTRI) == len(KODES), 'kode tidak ditemukan di manifest: %s' % (
    set(KODES) - {e['kode'] for e in ENTRI})

hasil = {'model_diminta': _J.MODEL_DEFAULT,
         'rule_version': P.RULE_VERSION,
         'kelompok': 'verifikasi-v11 tahap 5 (naskah uji)',
         'cabang': 'agen/wulan/optimalkan-jev-hakim-v5',
         'pelari': 'jalankan_verifikasi_v11.py (petakan_dari_teks 1 run + Hakim v2)',
         'bukti_impor': {'sk_dasar': _b1, 'sk_r21_dash_false': _b2,
                         'sk_r22_judul1_false': _b3,
                         'profil_romawi': _p_romawi['penomoran_bab'],
                         'profil_chapter': _p_ch['penomoran_bab'],
                         'profil_bom': _p_bom['bom_jml'],
                         'profil_pemisah': _p_pem['pemisah_gabung_jml'],
                         'sambung_kode_file': _SK.__file__,
                         'profil_kampus_file': PK.__file__,
                         'peta3_jev_file': P.__file__,
                         'rule_version': P.RULE_VERSION},
         'entri': []}
total_petakan = 0
total_hakim = 0
total_probe = 0
n_berhasil = 0
n_gagal = 0

for ent in ENTRI:
    kode = ent['kode']
    bidang = ent['bidang']
    nama = ent['nama']
    teks_rel = ent['teks_scratch']
    teks_path = os.path.join(SCRATCH, 'teks', teks_rel)
    print('=== %s %s: %s ===' % (kode, bidang, nama), flush=True)
    rec = {'kode': kode, 'bidang': bidang, 'nama': nama,
           'berkas_teks': teks_rel, 'kata_teks_asli': ent['kata_lokal']}
    try:
        with open(teks_path, encoding='utf-8') as f:
            teks_asli = f.read()
    except Exception as e:
        rec['status'] = 'gagal'
        rec['alasan'] = 'teks tidak terbaca di scratch: %s' % e
        hasil['entri'].append(rec)
        n_gagal += 1
        _simpan(hasil)
        continue
    bersih = _ST.buang_daftar_isi(teks_asli)
    rec['kata_teks_bersih'] = len(bersih.split())
    rec['baris_teks_bersih'] = len(bersih.split('\n'))
    rec['bentuk'] = _bentuk(bersih)
    # Profil bentuk Lapis 1 (0 Jev) — dicatat sebelum petakan.
    try:
        rec['profil_bentuk'] = P.profil_bentuk(bersih)
    except Exception as e:
        rec['profil_bentuk'] = {'galat': '%s: %s' % (type(e).__name__, e)}
    # ── probe (maks 2x; bila tetap bukan 1.14.0 -> gagal, lanjut) ──
    bukti = None
    for pc in (1, 2):
        try:
            bukti = probe_model(_J.MODEL_DEFAULT)
            total_probe += 1
        except Exception as e:
            bukti = {'galat': '%s: %s' % (type(e).__name__, e)}
            total_probe += 1
        print('%s probe %d: %s' % (kode, pc, json.dumps(bukti, ensure_ascii=False)), flush=True)
        if 'jev-1.14.0' in (bukti.get('model_dilayani') or ''):
            break
        if pc == 1:
            print('%s probe bukan 1.14.0 — tunggu 60 dtk lalu coba lagi' % kode, flush=True)
            time.sleep(60)
    rec['bukti_model'] = bukti
    if 'jev-1.14.0' not in (bukti.get('model_dilayani') or ''):
        rec['status'] = 'gagal'
        rec['alasan'] = 'probe model bukan jev-1.14.0: %r' % (bukti.get('model_dilayani'),)
        hasil['entri'].append(rec)
        n_gagal += 1
        _simpan(hasil)
        print('%s GAGAL: %s' % (kode, rec['alasan']), flush=True)
        continue
    # ── petakan (maks 3x, jeda 60 dtk antar coba) ──
    r = None
    galat_terakhir = None
    pgl_percobaan = []
    for perc in (1, 2, 3):
        P._CACHE_PETA.clear()
        for k in hitung:
            hitung[k] = 0
        s_sebelum = sidik()
        t0 = time.time()
        try:
            r_coba = P.petakan_dari_teks(bersih)
        except Exception as e:
            r_coba = None
            galat_terakhir = '%s: %s' % (type(e).__name__, e)
            print('%s petakan percobaan %d GALAT: %s' % (kode, perc, galat_terakhir), flush=True)
        pgl_percobaan.append(dict(hitung))
        if r_coba is not None and not r_coba.get('jev_mati'):
            r = r_coba
            wall = round(time.time() - t0, 2)
            pgl = dict(hitung)
            s_sesudah = sidik()
            break
        if r_coba is not None and r_coba.get('jev_mati'):
            galat_terakhir = 'jev_mati=True'
            print('%s petakan percobaan %d: Jev mati' % (kode, perc), flush=True)
        if perc < 3:
            print('%s petakan gagal — tunggu 60 dtk (percobaan %d/3)' % (kode, perc), flush=True)
            time.sleep(60)
    if r is None:
        rec['status'] = 'gagal'
        rec['alasan'] = 'petakan gagal sesudah 3x: %s' % galat_terakhir
        rec['panggilan_percobaan'] = pgl_percobaan
        total_petakan += sum(sum(p.values()) for p in pgl_percobaan)
        hasil['entri'].append(rec)
        n_gagal += 1
        _simpan(hasil)
        print('%s GAGAL: %s' % (kode, rec['alasan']), flush=True)
        continue
    total_petakan += sum(pgl.values())
    lab = {}
    for v in r['label'].values():
        lab[v] = lab.get(v, 0) + 1
    bab_label = [_teks_baris(r, i).strip() for i, v in sorted(r['label'].items()) if v == 'bab']
    goyang_rinci = [[i, list(v), _teks_baris(r, i)[:80]] for i, v in sorted(r['goyang'])]
    rec['status'] = 'berhasil'
    rec['wall_detik'] = wall
    rec['panggilan'] = pgl
    rec['panggilan_total'] = sum(pgl.values())
    rec['panggilan_percobaan'] = pgl_percobaan
    rec['kand_jml'] = r['kand_jml']
    rec['gelombang'] = r['gelombang']
    rec['tanya_ulang_jml'] = r.get('tanya_ulang_jml')
    rec['label'] = lab
    rec['label_penuh'] = {str(k): v for k, v in sorted(r['label'].items())}
    rec['baris_teks'] = bersih
    # baris hasil susun (indeks label_penuh/goyang mengacu ke sini, BUKAN
    # ke baris teks bersih — stitch bisa menggabung/menghapus baris).
    rec['baris'] = list(r['baris'])
    rec['gabung_penuh'] = {str(k): list(v)
                           for k, v in sorted((r.get('gabung') or {}).items())}
    rec['goyang_jml'] = len(r['goyang'])
    rec['goyang'] = goyang_rinci
    rec['bab_label'] = bab_label
    rec['bab_gabung'] = _bab_gabung(r)
    rec['bab_semua'] = _bab_semua(r)
    rec['gabung_jml'] = len(r['gabung'])
    rec['buang_jml'] = len(r['buang'])
    rec['gagal'] = r['gagal']
    rec['jev_mati'] = r.get('jev_mati')
    rec['bab_kode_jml'] = len(r.get('bab_kode') or [])
    rec['bab_ganda_jml'] = len(r.get('bab_ganda') or [])
    rec['bab_demosi_jml'] = len(r.get('bab_demosi') or [])
    rec['bab_demosi_teks'] = [_teks_baris(r, i).strip()[:120]
                             for i in (r.get('bab_demosi') or [])]
    rec['pisah_bab_ekor_jml'] = r.get('pisah_bab_ekor_jml')
    rec['pisah_subbab_ekor_jml'] = r.get('pisah_subbab_ekor_jml')
    rec['spasi_huruf_jml'] = r.get('spasi_huruf_jml')
    # ── v11 Lapis 1-3 ──
    rec['antrean_manusia'] = r.get('antrean_manusia')
    rec['alasan_antrean'] = r.get('alasan_antrean')
    rec['pendapat_kedua_jml'] = r.get('pendapat_kedua_jml')
    rec['pendapat_kedua_berbalik'] = r.get('pendapat_kedua_berbalik')
    rec['pendapat_kedua_antrean'] = r.get('pendapat_kedua_antrean')
    rec['sidik_sebelum'] = list(s_sebelum)
    rec['sidik_sesudah'] = list(s_sesudah)
    rec['sidik_berubah'] = list(s_sebelum) != list(s_sesudah)
    # ── Hakim v2 (panggilan Jev hakim dihitung terpisah) ──
    for k in hitung:
        hitung[k] = 0
    t0h = time.time()
    try:
        hk = H.periksa_peta(r)
        hk_galat = None
    except Exception as e:
        hk = None
        hk_galat = '%s: %s' % (type(e).__name__, e)
    wall_h = round(time.time() - t0h, 2)
    hpgl = dict(hitung)
    total_hakim += sum(hpgl.values())
    if hk is None:
        rec['hakim'] = {'galat': hk_galat}
    else:
        rec['hakim'] = {
            'jumlah_sepakat': hk.get('jumlah_sepakat'),
            'jumlah_ragu': hk.get('jumlah_ragu'),
            'jumlah_curiga': hk.get('jumlah_curiga'),
            'jumlah_belum': hk.get('jumlah_belum'),
            'alasan': hk.get('alasan'),
            'curiga_contoh': [(b.get('judul', '')[:100], b.get('alasan'))
                              for b in hk.get('bagian', [])
                              if b.get('status') == 'curiga'][:5],
            'ragu_contoh': [(b.get('judul', '')[:100], b.get('alasan'))
                            for b in hk.get('bagian', [])
                            if b.get('status') == 'ragu'][:5],
        }
    rec['hakim_panggilan'] = hpgl
    rec['hakim_panggilan_total'] = sum(hpgl.values())
    rec['hakim_wall_detik'] = wall_h
    hasil['entri'].append(rec)
    n_berhasil += 1
    _simpan(hasil)
    print('%s SELESAI wall %.2f dtk | panggilan %d %s | kand %d | label %s | '
          'goyang %d | bab_gabung %s | antrean %s %s | hakim %s +%d Jev | sidik %s -> %s'
          % (kode, wall, rec['panggilan_total'], pgl, r['kand_jml'], lab,
             len(r['goyang']), rec['bab_gabung'], rec['antrean_manusia'],
             rec['alasan_antrean'],
             {k: rec['hakim'].get(k) for k in
              ('jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'jumlah_belum')}
             if hk is not None else 'GALAT',
             rec['hakim_panggilan_total'], s_sebelum, s_sesudah), flush=True)

hasil['berhasil_jml'] = n_berhasil
hasil['gagal_jml'] = n_gagal
hasil['panggilan_petakan_total'] = total_petakan
hasil['panggilan_hakim_total'] = total_hakim
hasil['panggilan_probe_total'] = total_probe
hasil['panggilan_total'] = total_petakan + total_hakim + total_probe
_simpan(hasil)
print('SELESAI: berhasil %d | gagal %d | petakan %d | hakim %d | probe %d | total %d'
      % (n_berhasil, n_gagal, total_petakan, total_hakim, total_probe,
         total_petakan + total_hakim + total_probe), flush=True)
