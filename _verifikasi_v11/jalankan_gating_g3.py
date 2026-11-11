"""Run live kecil v14 — 1 naskah uji (G3, psikologi).

Jalankan DI DALAM container eduai-app (scratch /tmp/jev-v14-g3),
bukan di VM: Jev hanya jalan dari container (jembatan 172.17.0.1:8130).
Pola pelari gating AC2 (v13), diadaptasi untuk v14 + G3.

Yang dibuktikan:
  1. Wiring v14 end-to-end: Jev -> demosi blok v14 -> Hakim
     (tandai_ragu_curiga) -> agen kedua HANYA di baris ditandai
     (di sini PEREKAM, bukan agen sungguhan — adjudikasi dilakukan
     offline dari VM dengan prompt v14 yang baru).
  2. Label akhir di blok sistematika G3 (idx 46-60, 5 judul bab sampah
     no 250-254) dan penanda huruf subbab no 255 ('d. Mengenali Emosi
     Orang Lain') — bandingkan dengan peta v11 tersimpan.
  3. Gabung sesudah pembersihan v14 (salinan sistematika terbuang,
     bab asli utuh) + jumlah panggilan Jev.

DB produksi hanya dibaca (sidik COUNT sebelum/sesudah). Bukan deploy,
bukan restart. Saklar agen kedua TIDAK dinyalakan di container.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

SCRATCH = os.environ.get('SCRATCH', '/tmp/jev-v14-g3')
sys.path.insert(0, SCRATCH)
os.chdir(SCRATCH)

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
assert P.RULE_VERSION == 'jev-peta-v14', \
    'RULE_VERSION BUKAN v14: %r' % P.RULE_VERSION
# Bukti fungsi (0 Jev).
_b1 = _SK.sambung_kode('Kalimat pertama yang belum selesai', 'dan berlanjut di sini.')
print('bukti sk() dasar:', _b1, flush=True)
assert _b1 is True, 'sk() dasar BUKAN True — BERHENTI!'

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
HASIL_PATH = os.path.join(SCRATCH, 'hasil_gating_g3.json')
MODEL_SAH = 'typesafe/jev-1.14-20261014'
MODEL_RESMI = 'jev-1.14.0'


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
        'messages': [
            {'role': 'user',
             'content': json.dumps({
                 'state': 'PROBE MODEL: teks ini hanya untuk memeriksa '
                          'model yang dilayani.',
                 'questions': {'probe': {
                     'type': 'noul',
                     'instructions': 'Apakah teks ini menyebut sebuah '
                                     'model?'}}})},
        ],
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

rekaman = []


def _perekam(i, t, s, p, k=None):
    """Perekam Lapis 2: catat baris yang DIADILI (harus = baris ditandai
    Hakim), kembalikan None (label tidak berubah di run ini)."""
    rekaman.append({'idx': i, 'teks': t, 'suara': list(s or []),
                    'conf': list(p or []), 'konteks': k})
    return None


def main():
    t0 = time.time()
    s_sebelum = sidik()
    print('sidik sebelum:', s_sebelum, flush=True)
    with open(os.path.join(SCRATCH, 'G3.txt'), encoding='utf-8') as f:
        teks_asli = f.read()
    bersih = _ST.buang_daftar_isi(teks_asli)
    print('kata bersih:', len(bersih.split()), 'baris:',
          len(bersih.split('\n')), flush=True)

    # ── probe (maks 3x; yang SAH hanya typesafe/jev-1.14-20261014) ──
    bukti = None
    model_jalan = _J.MODEL_DEFAULT
    model_override = None
    total_probe = 0
    for pc in (1, 2, 3):
        try:
            bukti = probe_model(model_jalan)
            total_probe += 1
        except Exception as e:
            bukti = {'galat': '%s: %s' % (type(e).__name__, e)}
            total_probe += 1
        print('probe %d (diminta %s): %s'
              % (pc, model_jalan, json.dumps(bukti, ensure_ascii=False)),
              flush=True)
        dilayani = bukti.get('model_dilayani') or ''
        if dilayani == MODEL_SAH:
            break
        if dilayani == MODEL_RESMI and model_override is None:
            print('probe melayani jev-1.14.0 (TypeSafe terisi lagi) — '
                  'PINDAH ke OpenRouter langsung %s' % MODEL_SAH, flush=True)
            _J.MODEL_DEFAULT = MODEL_SAH
            model_jalan = MODEL_SAH
            model_override = ('typesafe-terisi-lagi: pindah ke openrouter '
                              'langsung agar tetap satu ID model')
            time.sleep(5)
            continue
        if pc < 3:
            print('probe bukan %s — tunggu 60 dtk lalu coba lagi' % MODEL_SAH,
                  flush=True)
            time.sleep(60)
    assert (bukti.get('model_dilayani') or '') == MODEL_SAH, \
        'probe model bukan %s: %r' % (MODEL_SAH, bukti.get('model_dilayani'))

    # ── petakan G3 dengan wiring v14 + perekam ──
    t0p = time.time()
    r = P.petakan_dari_teks(
        bersih, putaran=1,
        pendapat_kedua_fn=_perekam,
        hakim_tandai_fn=H.tandai_ragu_curiga)
    wall_p = round(time.time() - t0p, 2)
    print('petakan selesai %.1f dtk; panggilan Jev: %s; hakim_tandai: %s; '
          'rekaman: %d baris; goyang: %d'
          % (wall_p, hitung, r.get('hakim_tandai'), len(rekaman),
             len(r.get('goyang') or [])), flush=True)

    # ── flag pasca-koreksi: periksa_peta pada peta FINAL (+1 Jev) ──
    baris = r['baris']
    label = {int(k): v for k, v in (r.get('label') or {}).items()}
    gabung = {int(k): v for k, v in (r.get('gabung') or {}).items()}
    kand = sorted((i, baris[i]) for i in label if i < len(baris))
    sist = P._tandai_sistematika(baris, label, kand, gabung)
    peta_final = {'baris': baris, 'label': label, 'gabung': gabung,
                  'sistematika': sorted(sist), 'p': dict(r.get('p') or {})}
    hk_final = H.periksa_peta(peta_final)
    flag_final = sorted(
        int(b['i']) for b in (hk_final.get('bagian') or [])
        if b.get('status') in ('ragu', 'curiga'))
    flag_pra = sorted(r.get('hakim_tandai') or [])
    print('flag pra-koreksi: %s' % flag_pra, flush=True)
    print('flag pasca-koreksi: %s' % flag_final, flush=True)
    print('selisih pra vs pasca: hanya-pra %s, hanya-pasca %s'
          % (sorted(set(flag_pra) - set(flag_final)),
             sorted(set(flag_final) - set(flag_pra))), flush=True)
    # ── blok v14 (dihitung ulang dari baris + gabung ASLI tersimpan di
    #    susun — di sini dihitung dari baris + gabung bersih sebagai
    #    perkiraan bawah; blok polos sudah terbuang dari gabung) ──
    blok_kira = sorted(P._deteksi_blok_daftar_isi(baris, gabung))

    s_sesudah = sidik()
    hasil = {
        'kode': 'G3', 'rule_version': P.RULE_VERSION,
        'model_diminta': _J.MODEL_DEFAULT,
        'model_melayani': bukti.get('model_dilayani'),
        'model_override': model_override,
        'bukti_model': bukti,
        'probe_jml': total_probe,
        'panggilan_jev': dict(hitung),
        'panggilan_total': sum(hitung.values()),
        'wall_detik': round(time.time() - t0, 2),
        'wall_petakan_detik': wall_p,
        'sidik_sebelum': list(s_sebelum),
        'sidik_sesudah': list(s_sesudah),
        'sidik_berubah': list(s_sebelum) != list(s_sesudah),
        'hakim_tandai_pra': flag_pra,
        'hakim_tandai_galat': r.get('hakim_tandai_galat'),
        'hakim_final': {'jumlah_sepakat': hk_final.get('jumlah_sepakat'),
                        'jumlah_ragu': hk_final.get('jumlah_ragu'),
                        'jumlah_curiga': hk_final.get('jumlah_curiga'),
                        'jumlah_belum': hk_final.get('jumlah_belum')},
        'flag_pasca': flag_final,
        'flag_selisih': {'hanya_pra': sorted(set(flag_pra) - set(flag_final)),
                         'hanya_pasca': sorted(set(flag_final) - set(flag_pra))},
        'rekaman': rekaman,
        'pendapat_kedua_jml': r.get('pendapat_kedua_jml'),
        'pendapat_kedua_antrean': r.get('pendapat_kedua_antrean'),
        'goyang_jml': len(r.get('goyang') or []),
        'goyang': [[g[0], list(g[1])] for g in (r.get('goyang') or [])],
        'label': {str(k): v for k, v in sorted(label.items())},
        'gabung': {str(k): list(v) for k, v in sorted(gabung.items())},
        'sistematika': sorted(sist),
        'blok_kira_dari_gabung_bersih': blok_kira,
        'baris': baris,
        'bab_label': [b for b in (r.get('bab_label') or [])],
    }
    tmp = HASIL_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(hasil, f, ensure_ascii=False, indent=1)
    os.replace(tmp, HASIL_PATH)
    print('hasil tersimpan:', HASIL_PATH, flush=True)


if __name__ == '__main__':
    main()
