"""Fase 2 run live AC2 — adjudikasi offline dari VM (agen kedua OpenRouter).

Membaca rekaman fase 1 (_verifikasi_v11/hasil_gating_ac2.json: 14 baris
ditandai Hakim yang direkam perekam di container), memanggil agen kedua
(Gemini 2.5 Flash PINNED) untuk tiap baris, menerapkan
`pendapat_kedua(mode='agen-kedua')` yang ASLI + koreksi deterministik
pasca-Lapis 2 (pola pilot fase 2; sistematika diambil dari peta AC2
tersimpan tahap 5 sebagai hampiran — pelari live tidak menyimpan baris,
dicatat sebagai caveat).

Jawaban agen kedua yang sudah direkam dipakai ulang bila skrip
dijalankan lagi.
Keluaran: _verifikasi_v11/hasil_gating_ac2_fase2.json.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import sys
import types
from pathlib import Path

os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '1'   # ukur di VM saja, bukan produksi

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

MASUK = ROOT / '_verifikasi_v11' / 'hasil_gating_ac2.json'
KELUAR = ROOT / '_verifikasi_v11' / 'hasil_gating_ac2_fase2.json'


class FakeSatpam:
    def tanya_bebas_mutu(self, bahan, pertanyaan):
        raise RuntimeError('FakeSatpam: tidak dipakai di fase 2 AC2')


FAKE_SATPAM = FakeSatpam()


class FakeKonversi:
    mode = 'normal'

    @classmethod
    def _pecah_blok(cls, teks):
        return [{'text': b, 'lines': [n], 'kosong': not b}
                for n, b in enumerate((teks or '').split('\n'))]


def _stub_app():
    app = types.ModuleType('app')
    app.__path__ = [str(ROOT / 'app')]
    sys.modules['app'] = app
    ai = types.ModuleType('app.ai')
    ai.SessionLocal = object
    ai._teks_dari_berkas = lambda *a, **k: ''
    ai.UPLOAD_DIR = Path('/tmp')
    sys.modules['app.ai'] = ai
    models = types.ModuleType('app.models')
    models.FileBerkas = object
    sys.modules['app.models'] = models
    sys.modules['app.satpam'] = FAKE_SATPAM
    state = types.ModuleType('app.state')
    state.buang_daftar_isi = lambda t: t
    sys.modules['app.state'] = state
    sys.modules['app.konversi'] = FakeKonversi


def _muat_peta3():
    _stub_app()
    spec = importlib.util.spec_from_file_location(
        '_peta3_fase2ac2', str(ROOT / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _muat_peta3()
import app.agen_kedua as AK
from agen_kedua_openrouter import buat_penanya

assert P.RULE_VERSION == 'jev-peta-v13', P.RULE_VERSION

_KATA_GANTUNG = P._KATA_GANTUNG
_AKHIR_LANJUT = (',', ';', '(', '-', '\u2013', '\u2014')


def _prev_teks(konteks):
    for b in reversed(konteks.get('sebelum') or []):
        if (b or '').strip():
            return b.strip()
    return ''


def _prev_lanjut(prev):
    if not prev:
        return False
    if prev.endswith(_AKHIR_LANJUT):
        return True
    kata = prev.split()
    if not kata:
        return False
    akhir = re.sub(r'[^A-Za-z]+$', '', kata[-1].lower())
    return akhir in _KATA_GANTUNG


def terapkan_koreksi(label_l2, teks, idx, sistematika, konteks, gabung_judul):
    lab = label_l2
    jejak = []
    if lab is None:
        return None, ['tidak ada label L2 (antrean)']
    t = (teks or '').strip()
    if lab == 'subbab' and len(t) > P._ambang('judul_maks_kar', 300):
        lab = 'paragraf'
        jejak.append('ATURAN 2: subbab >300 kar jadi paragraf')
    if lab == 'subbab' and P._spss_header(t):
        lab = 'biasa'
        jejak.append('ATURAN 4: header SPSS jadi biasa')
    if lab in ('bab', 'subbab') and P._huruf_awal_kecil(t) \
            and idx not in sistematika:
        lab = 'biasa'
        jejak.append('ATURAN 5: bab/subbab diawali huruf kecil jadi biasa')
    if lab == 'paragraf' and idx not in sistematika:
        prev = _prev_teks(konteks or {})
        prev_judul = prev in (gabung_judul or set()) \
            or bool(re.match(r'^\d+[.)]\s+\S', prev)) \
            or (prev == prev.upper() and len(prev) <= 60 and bool(prev))
        if not prev_judul and (t[:1].islower() or _prev_lanjut(prev)):
            lab = 'biasa'
            jejak.append('v6 batas: paragraf diawali huruf kecil / '
                         'baris sebelumnya bersambung')
    if re.match(r'^(?:\d{1,3}\s+)?(?:\d+[.)]\s*)?BAB\s+[IVX0-9]+\b',
                t, re.I):
        lab = 'bab'
        jejak.append('v6 deteksi BAB deterministik')
    return lab, jejak


def main():
    penanya = buat_penanya()  # google/gemini-2.5-flash, PINNED
    fn = AK.buat_pendapat_kedua_fn(penanya=penanya)
    assert fn is not None, 'pabrik fn mengembalikan None (saklar mati?)'

    run = json.load(open(MASUK, encoding='utf-8'))
    label_live = {int(k): v for k, v in run['label'].items()}
    gabung_judul = set(run.get('bab_label') or [])

    # Sistematika hampiran dari peta AC2 tersimpan tahap 5.
    import glob
    mentah = None
    for f in glob.glob(str(ROOT / '_verifikasi_v11' / 'hasil_verifikasi_v11_*.json')):
        d = json.load(open(f, encoding='utf-8'))
        for e in d.get('entri', []):
            if e['kode'] == 'AC2':
                mentah = e
    baris5 = mentah['baris']
    label5 = {int(k): v for k, v in mentah['label_penuh'].items()}
    gabung5 = {int(k): v for k, v in mentah['gabung_penuh'].items()}
    kand5 = sorted((i, baris5[i]) for i in label5 if i < len(baris5))
    sist5 = P._tandai_sistematika(baris5, label5, kand5)

    # Label manusia untuk baris AC2 di TSV (hanya no 174 yang ditandai).
    tsv = list(csv.DictReader(
        open(ROOT / 'ground_truth' / 'ground_truth_uji112.tsv',
             encoding='utf-8'), delimiter='\t'))
    pem = json.load(open(ROOT / '_sketsa' / 'pemetaan_tsv_baris.json',
                         encoding='utf-8'))
    benar_ac2 = {}
    for r in tsv:
        if r['naskah'] != 'AC2':
            continue
        pm = pem.get('AC2|%s' % r['no'], {})
        if pm.get('idx') is not None:
            benar_ac2[pm['idx']] = (r['no'], r['label_benar'],
                                    r['jenis_sengketa'])

    jw_lama = {}
    if KELUAR.exists():
        try:
            lama = json.load(open(KELUAR))
            for b in lama.get('baris') or []:
                if b.get('jawaban_agen_kedua'):
                    jw_lama[b['idx']] = b['jawaban_agen_kedua']
        except Exception:
            jw_lama = {}

    hasil = {'kode': 'AC2', 'rule_version': P.RULE_VERSION,
             'model_agen_kedua': 'google/gemini-2.5-flash',
             'transport_agen_kedua': 'openrouter',
             'panggilan_agen_kedua': 0,
             'panggilan_agen_kedua_dari_rekaman': 0,
             'catatan_sistematika': ('sistematika dari peta AC2 tersimpan '
                                     'tahap 5 (hampiran; pelari live tidak '
                                     'menyimpan baris)'),
             'baris': []}
    for rec in run['rekaman']:
        idx = rec['idx']
        bar = {'idx': idx, 'teks': rec['teks'], 'suara': rec['suara'],
               'conf': rec['conf'], 'konteks': rec['konteks'],
               'label_live_v11': label_live.get(idx)}
        if idx in benar_ac2:
            no, benar, jenis = benar_ac2[idx]
            bar['tsv_no'] = no
            bar['label_benar'] = benar
            bar['jenis_sengketa'] = jenis
            bar['v11_benar'] = (label_live.get(idx) == benar)
        if idx in jw_lama:
            jawab = jw_lama[idx]
            hasil['panggilan_agen_kedua_dari_rekaman'] += 1
            print('  (memakai jawaban agen kedua yang sudah direkam, '
                  'idx %d)' % idx, flush=True)
        else:
            jawab = fn(idx, rec['teks'], rec['suara'], rec['conf'],
                       rec['konteks'])
            hasil['panggilan_agen_kedua'] += 1
        bar['jawaban_agen_kedua'] = jawab
        if jawab is None:
            bar['putusan_rantai'] = 'antrean-manusia'
            bar['label_rantai'] = None
        else:
            bar['agen_kedua_label'] = jawab['label']
            put = P.pendapat_kedua(idx, rec['teks'], rec['suara'],
                                   rec['conf'], jawab, mode='agen-kedua')
            bar['putusan_rantai'] = put['putusan']
            bar['alasan_putusan'] = put['alasan']
            bar['label_rantai_l2'] = put['label']
            if put['putusan'] == 'tetap':
                bar['label_rantai'] = label_live.get(idx)
                bar['koreksi_rantai'] = []
            elif put['putusan'] == 'berbalik':
                fin, jejak = terapkan_koreksi(
                    put['label'], rec['teks'], idx, sist5, rec['konteks'],
                    gabung_judul)
                bar['label_rantai'] = fin
                bar['koreksi_rantai'] = jejak
            else:
                bar['label_rantai'] = None
                bar['koreksi_rantai'] = []
        if 'label_benar' in bar:
            bar['rantai_benar'] = (bar['label_rantai'] == bar['label_benar'])
        hasil['baris'].append(bar)
        print('idx %-4d suara=%-22s v11=%-8s agen2=%-8s putusan=%-15s '
              'rantai=%-8s benar=%s'
              % (idx, bar['suara'], bar['label_live_v11'],
                 (jawab or {}).get('label'), bar['putusan_rantai'],
                 bar['label_rantai'], bar.get('label_benar')), flush=True)

    putusan = {}
    for b in hasil['baris']:
        putusan[b['putusan_rantai']] = putusan.get(b['putusan_rantai'], 0) + 1
    hasil['ringkasan_putusan'] = putusan
    json.dump(hasil, open(KELUAR, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\nRINGKASAN AC2 live: %d baris diadili, panggilan agen kedua %d '
          '(rekaman %d), putusan %s'
          % (len(hasil['baris']), hasil['panggilan_agen_kedua'],
             hasil['panggilan_agen_kedua_dari_rekaman'], putusan))
    for b in hasil['baris']:
        if 'label_benar' in b:
            print('baris TSV no %s: benar=%s v11=%s rantai=%s '
                  '(v11_benar=%s rantai_benar=%s)'
                  % (b['tsv_no'], b['label_benar'], b['label_live_v11'],
                     b['label_rantai'], b['v11_benar'], b['rantai_benar']))


if __name__ == '__main__':
    main()
