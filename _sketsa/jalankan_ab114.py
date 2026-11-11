"""Uji banding TERKENDALI jev-1.13 vs jev-1.14 di fid=81 (naskah nyata Asih).

PERBAIKAN atas skrip lama (audit 10 Nov 2026):
  1. Skrip banding v4 HILANG (/tmp/jev-v4 terhapus, tidak ada runner
     dengan saklar model di repo) — tidak bisa diverifikasi cara
     kerjanya. Skrip ini dibangun ulang dari nol, di-commit ke repo.
  2. CACAT KRITIS yang ditemukan audit: `satpam.tanya_bebas_mutu`
     (satu-satunya jalur peta ke Jev) memanggil `jev.tanya` TANPA
     argumen model, jadi model SELALU `jev.MODEL_DEFAULT` (1.13).
     Env `EDUAI_SATPAM_MODEL` / `satpam.MODEL` HANYA dipakai fungsi
     mati `_tanya_bebas_lama` — menyetel env itu TIDAK mengganti model
     peta sama sekali. Bila probe v4 memakai env itu, "run 1.14"-nya
     diam-diam masih 1.13, dan selisih goyang 31 vs 49 hanyalah
     variansi antar-run 1.13. Skrip ini mengganti model di tempat
     yang BENAR: `app.jev.MODEL_DEFAULT` (dipakai semua jalur:
     gelombang surveyor, stitch, hakim).
  3. BUKTI MODEL DILAYANI: sebelum tiap run, probe langsung ke
     jembatan dengan string model yang sama; rekam `model`,
     `satpam_jejak`, dan `satpam_penyedia` dari balasan mentah.
     Bila yang dilayani bukan model yang diminta → ABORT, jangan
     petakan (jangan buang panggilan Jev untuk banding palsu).
  4. Skrip A/B Okt mengukur "goyang" dari nilai FLOAT mentah
     (0,91 vs 0,92 dihitung berubah) — salah ukur menurut dokumen
     resmi (Noul adalah probabilitas; yang bermakna adalah
     KEPUTUSAN). Skrip ini membandingkan LABEL AKHIR per kandidat
     (keputusan), plus goyang internal peta (suara terbelah),
     plus jarak ke baseline Oktober (BAB 5, SUB-BAB 130,
     PARAGRAF 157).
  5. n=1 per model (sesuai tugas), skrip SAMA, pertanyaan SAMA,
     state SAMA (fid=81 yang sama dari DB), hanya model berbeda.
     Cache peta DIMATIKAN supaya run 1.14 tidak mengambil peta 1.13.
     DB hanya dibaca.

Jalankan di container:  python3 /tmp/jev-ab114/jalankan_ab114.py
Kode deploy /app tidak disentuh. Tidak merge, tidak deploy.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-ab114')
sys.path.insert(1, '/app')

import importlib.util
import json
import time
import urllib.request

_src = open('/tmp/jev-ab114/peta3_jev.py', encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src, 'sisa sys.path jev-v4 masih ada!'
spec = importlib.util.spec_from_loader('peta3_ab114', loader=None)
P = importlib.util.module_from_spec(spec)
exec(compile(_src, '/tmp/jev-ab114/peta3_jev.py', 'exec'), P.__dict__)

import app.jev as _J
import app.satpam as _S
import app.konversi as _K
import app.hakim_peta as _H

print('peta dari: /tmp/jev-ab114/peta3_jev.py', flush=True)
print('jev dari:', _J.__file__, '| satpam dari:', _S.__file__, flush=True)
print('konversi dari:', _K.__file__, '| hakim dari:', _H.__file__, flush=True)
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
assert 'v7' in P.RULE_VERSION, 'BUKAN kode v7!'
assert _J.__file__.startswith('/tmp/jev-ab114/'), 'jev BUKAN dari scratch!'
assert _S.__file__.startswith('/tmp/jev-ab114/'), 'satpam BUKAN dari scratch!'

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
BASELINE = {'bab': 5, 'subbab': 130, 'paragraf': 157}

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


def jalan_satu(model_str, nama):
    """Satu run petakan(fid=81) dengan model ini. Kembalikan ringkasan."""
    print(f'=== {nama}: model diminta {model_str} ===', flush=True)
    bukti = probe_model(model_str)
    print('  bukti layan:', json.dumps(bukti, ensure_ascii=False), flush=True)
    dilayani = (bukti.get('model_dilayani') or '')
    # jembatan resmi balas 'jev-1.14.0', openrouter balas 'typesafe/jev-1.14'
    versi = '1.14' if '1.14' in nama else '1.13'
    assert versi in dilayani, (
        f'MODEL SALAH DILAYANI: diminta {nama}, dilayani {dilayani!r} — ABORT')
    _J.MODEL_DEFAULT = model_str
    _S.MODEL = model_str
    print('  jev.MODEL_DEFAULT kini:', _J.MODEL_DEFAULT, flush=True)
    P._CACHE_PETA.clear()
    for k in hitung:
        hitung[k] = 0
    print('  sidik DB sebelum:', sidik(), flush=True)
    t0 = time.time()
    r = P.petakan(81)
    wall = round(time.time() - t0, 2)
    pgl = dict(hitung)
    lab = {}
    for v in r['label'].values():
        lab[v] = lab.get(v, 0) + 1
    bab_judul = []
    for i, v in sorted(r['label'].items()):
        if v == 'bab':
            b = r['baris']
            t = b.get(i, '') if isinstance(b, dict) else ''
            bab_judul.append(t.strip()[:90])
    print(f'  wall: {wall} dtk | panggilan: {pgl} '
          f'(total {sum(pgl.values())})', flush=True)
    print(f'  kandidat: {r["kand_jml"]} | gelombang: {r["gelombang"]} '
          f'| tanya-ulang: {r.get("tanya_ulang_jml")} '
          f'| gabung: {len(r["gabung"])} | buang: {len(r["buang"])} '
          f'| gagal: {r["gagal"]}', flush=True)
    print(f'  label: {lab} | goyang: {len(r["goyang"])}', flush=True)
    print(f'  judul BAB: {bab_judul}', flush=True)
    print('  sidik DB sesudah:', sidik(), flush=True)
    return {'model_diminta': model_str, 'bukti_layan': bukti,
            'wall': wall, 'panggilan': pgl,
            'panggilan_total': sum(pgl.values()),
            'kand_jml': r['kand_jml'], 'gelombang': r['gelombang'],
            'tanya_ulang': r.get('tanya_ulang_jml'),
            'gabung': len(r['gabung']), 'buang': len(r['buang']),
            'gagal': r['gagal'],
            'label': lab, 'goyang': len(r['goyang']),
            'bab_judul': bab_judul,
            'label_penuh': {str(i): v for i, v in r['label'].items()}}


hasil = {'kode': 'v7 (branch agen/wulan/optimalkan-jev-hakim-v5, b41392a)',
         'baseline_okt': BASELINE, 'fid': 81}
hasil['jev_1_13'] = jalan_satu('SATPAM/typesafe/jev-1.13', 'jev-1.13')
hasil['jev_1_14'] = jalan_satu('SATPAM/typesafe/jev-1.14', 'jev-1.14')

# ── banding keputusan (bukan float mentah) ──────────────────────────────
a = hasil['jev_1_13']['label_penuh']
b = hasil['jev_1_14']['label_penuh']
semua_idx = sorted(set(a) | set(b), key=lambda x: int(x))
beda = [(int(i), a.get(i), b.get(i)) for i in semua_idx
        if a.get(i) != b.get(i)]
dari_ke = {}
for _i, x, y in beda:
    dari_ke[f'{x}->{y}'] = dari_ke.get(f'{x}->{y}', 0) + 1
hasil['banding'] = {
    'kandidat_sama': len(semua_idx),
    'label_beda_jml': len(beda),
    'label_beda_arah': dari_ke,
    'label_beda_rinci': beda[:40],
    'jarak_ke_baseline': {
        m: {k: abs(hasil[m]['label'].get(k, 0) - v)
            for k, v in BASELINE.items()}
        for m in ('jev_1_13', 'jev_1_14')},
}
print('BANDING:', json.dumps(hasil['banding'], ensure_ascii=False), flush=True)

with open('/tmp/jev-ab114/hasil_ab114.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('HASIL JSON:', json.dumps(hasil, ensure_ascii=False), flush=True)
print('SELESAI')
