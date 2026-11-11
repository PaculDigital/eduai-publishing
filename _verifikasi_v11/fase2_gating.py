"""Fase B — ukur rantai gating-Hakim v13 di 279 baris label manusia.

NOL panggilan Jev. Agen kedua (Gemini 2.5 Flash PINNED via OpenRouter)
dipanggil HANYA untuk baris yang ditandai Hakim (ragu/curiga), ditentukan
dari data tersimpan tahap 5 (bukan dari run ulang):
  - curiga: audit struktural Hakim Source-1, dihitung ulang deterministik
    dari peta final tersimpan (cocok dengan total curiga tahap 5 = 10).
  - ragu: kandidat tanya-Jev yang Jev jawab ragu di tahap 5 — ditentukan
    dari ragu_contoh tersimpan (lengkap bila jumlah_ragu <= 5, karena
    contoh dibatasi 5) atau jumlah_ragu == jumlah kandidat (semua ragu).
Baris lain: label rantai = label v11 final.
Baris gabung-saja (26, tanpa label per baris): label v11 efektifnya
diambil dari `bukti_run` TSV ('bab' bila teksnya bagian dari judul
`bab_gabung` — metode yang sama dengan skor v11 136/279 yang sudah
dilaporkan); baris itu bukan kandidat Hakim, jadi label rantai = label
v11 efektifnya.

Suara Jev = label v11 FINAL (label pra-koreksi tidak tersimpan; baris
yang label finalnya tidak ada di suara goyang dicatat sebagai
'koreksi-mengubah-suara'). Conf dirancang supaya label teratas ==
label v11 (0,9 untuk label v11, 0,6 untuk suara lain) — di mode
'agen-kedua' hanya label teratas yang dipakai putusan, bukan nilai conf.

Koreksi deterministik pasca-Lapis 2 (ATURAN 2/4/5, v6 batas) diterapkan
hanya pada label yang BERBALIK (pola pilot fase 2); label 'tetap' sudah
final dari v11. kode_label tidak tersimpan tahap 5, jadi tidak dipakai
di sini (dicatat sebagai caveat; run live AC2 menutupnya end-to-end).

Jawaban agen kedua yang sudah direkam dipakai ulang bila skrip
dijalankan lagi (tidak ada panggilan ganda).

Keluaran: _verifikasi_v11/hasil_rantai_gating.json (per baris) + ringkasan
dicetak; skor juga ditulis ke hasil_verifikasi_v11.json (kunci baru).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import sys
import types
from collections import Counter
from pathlib import Path

os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '1'   # ukur di VM saja, bukan produksi

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

KELUAR = ROOT / '_verifikasi_v11' / 'hasil_rantai_gating.json'


class FakeSatpam:
    def tanya_bebas_mutu(self, bahan, pertanyaan):
        raise RuntimeError('FakeSatpam: tidak dipakai di fase B')


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
        '_peta3_faseB', str(ROOT / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _muat_peta3()
import app.agen_kedua as AK
from agen_kedua_openrouter import buat_penanya

assert P.RULE_VERSION == 'jev-peta-v13', P.RULE_VERSION

# ── koreksi deterministik pasca-Lapis 2 (salinan pola pilot fase 2) ─────────
_KATA_GANTUNG = P._KATA_GANTUNG
_AKHIR_LANJUT = (',', ';', '(', '-', '\u2013', '\u2014')


def _norm(s):
    return ' '.join(str(s or '').split())


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
    """ATURAN 2/4/5 + v6 batas pada label pasca-L2 (tanpa kode_label:
    tidak tersimpan tahap 5). Mengembalikan (label_final, [jejak])."""
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

    tsv = list(csv.DictReader(
        open(ROOT / 'ground_truth' / 'ground_truth_uji112.tsv',
             encoding='utf-8'), delimiter='\t'))
    pem = json.load(open(ROOT / '_sketsa' / 'pemetaan_tsv_baris.json',
                         encoding='utf-8'))
    flag = json.load(open(ROOT / '_sketsa' / 'flag_hakim_35.json',
                          encoding='utf-8'))

    mentah, kelompok = {}, {}
    for f, tag in [('hasil_verifikasi_v11_A.json', 'TypeSafe'),
                   ('hasil_verifikasi_v11_B.json', 'TypeSafe'),
                   ('hasil_verifikasi_v11_OR1.json', 'OpenRouter'),
                   ('hasil_verifikasi_v11_OR2.json', 'OpenRouter'),
                   ('hasil_verifikasi_v11_OR3.json', 'OpenRouter'),
                   ('hasil_verifikasi_v11_OR4.json', 'OpenRouter'),
                   ('hasil_verifikasi_v11_OR5.json', 'OpenRouter')]:
        d = json.load(open(ROOT / '_verifikasi_v11' / f, encoding='utf-8'))
        for e in d.get('entri', []):
            mentah[e['kode']] = e
            kelompok[e['kode']] = tag

    # ── himpunan flag per naskah dari data tersimpan ──
    flag_set, flag_alasan = {}, {}
    for kode, e in mentah.items():
        fl = flag['naskah'].get(kode, {})
        curiga = set(fl.get('curiga_kode', []))
        kand = fl.get('tanya_kandidat', [])
        hk = e.get('hakim') or {}
        n_ragu = hk.get('jumlah_ragu', 0)
        baris = e.get('baris') or []
        ragu = set()
        if n_ragu >= len(kand):
            ragu = set(kand)          # semua kandidat dijawab ragu
        else:
            contoh = [(c[0] or '') for c in (hk.get('ragu_contoh') or [])]
            for i in kand:
                t = _norm(baris[i]) if i < len(baris) else ''
                if any(t.startswith(c) and c for c in contoh):
                    ragu.add(i)
        flag_set[kode] = curiga | ragu
        flag_alasan[kode] = {'curiga': sorted(curiga), 'ragu': sorted(ragu)}

    # ── jawaban agen kedua yang sudah direkam (hindari panggilan ulang) ──
    jw_lama = {}
    if KELUAR.exists():
        try:
            lama = json.load(open(KELUAR))
            for b in lama.get('baris') or []:
                if b.get('jawaban_agen_kedua'):
                    jw_lama[(b['naskah'], str(b['no']))] = b['jawaban_agen_kedua']
        except Exception:
            jw_lama = {}

    hasil = {'rule_version': P.RULE_VERSION,
             'kelompok': 'ukur rantai gating-Hakim v13 di 279 baris uji',
             'model_agen_kedua': 'google/gemini-2.5-flash',
             'transport_agen_kedua': 'openrouter',
             'panggilan_agen_kedua': 0,
             'panggilan_agen_kedua_dari_rekaman': 0,
             'baris': []}

    for r in tsv:
        kode, no = r['naskah'], r['no']
        e = mentah[kode]
        baris = e.get('baris') or []
        label_penuh = {int(k): v for k, v in
                       (e.get('label_penuh') or {}).items()}
        gabung_penuh = {int(k): v for k, v in
                        (e.get('gabung_penuh') or {}).items()}
        goyang = {int(g[0]): g[1] for g in (e.get('goyang') or [])}
        pm = pem.get('%s|%s' % (kode, no), {})
        idx = pm.get('idx')
        bar = {'naskah': kode, 'no': no, 'kelompok': kelompok[kode],
               'bidang': e.get('bidang'), 'bentuk': e.get('bentuk'),
               'jenis_sengketa': r['jenis_sengketa'],
               'teks_baris': r['teks_baris'],
               'label_benar': r['label_benar'],
               'idx_peta': idx, 'alasan_pemetaan': pm.get('alasan')}
        # Label v11 efektif: dari bukti_run TSV (sama dengan label_penuh
        # untuk baris terpetakan — diverifikasi 0 beda di 253 baris — dan
        # 'bab' untuk 26 baris gabung-saja yang teksnya bagian judul
        # bab_gabung; 'null' -> None).
        _m = re.search(r'v11=(\w+)', r['bukti_run'] or '')
        v11_bukti = _m.group(1) if _m else None
        if v11_bukti == 'null':
            v11_bukti = None
        v11 = label_penuh.get(idx) if idx is not None else v11_bukti
        if idx is not None and v11_bukti is not None \
                and v11_bukti != v11:
            bar['v11_bukti_vs_penuh_beda'] = True
        bar['label_v11'] = v11
        bar['v11_benar'] = (v11 == r['label_benar'])
        bar['ditandai_hakim'] = bool(
            idx is not None and idx in flag_set.get(kode, set()))
        bar['flag_alasan'] = ('curiga' if idx is not None and idx in
                              set(flag['naskah'].get(kode, {})
                                  .get('curiga_kode', []))
                              else ('ragu' if bar['ditandai_hakim'] else None))
        if not bar['ditandai_hakim']:
            bar['label_rantai'] = v11
            bar['rantai_benar'] = bar['v11_benar']
            bar['putusan_rantai'] = 'tidak-ditandai'
        else:
            # suara Jev: suara goyang bila label v11 ada di dalamnya,
            # selainnya suara tunggal label v11 (final).
            votes = goyang.get(idx)
            if votes and v11 in votes:
                suara = list(votes)
                bar['suara_dari'] = 'goyang'
            else:
                suara = [v11]
                bar['suara_dari'] = 'tunggal'
                if votes:
                    bar['koreksi_mengubah_suara'] = True
            p = [0.9 if v == v11 else 0.6 for v in suara]
            # konteks lebar (pola _konteks_lebar live)
            sebelum = [baris[k] for k in range(max(0, idx - 3), idx)]
            sesudah = [baris[k]
                       for k in range(idx + 1, min(len(baris), idx + 4))]
            judul = None
            for k in range(idx - 1, -1, -1):
                if k in gabung_penuh:
                    judul = ' '.join(gabung_penuh[k]).strip()
                    break
                if label_penuh.get(k) == 'bab':
                    judul = baris[k]
                    break
            konteks = {'sebelum': sebelum, 'sesudah': sesudah,
                       'judul_bab_terdekat': judul}
            bar['konteks'] = konteks
            bar['suara'] = suara
            kunci = (kode, str(no))
            if kunci in jw_lama:
                jawab = jw_lama[kunci]
                hasil['panggilan_agen_kedua_dari_rekaman'] += 1
                print('  (memakai jawaban agen kedua yang sudah direkam, '
                      '%s no %s)' % (kode, no), flush=True)
            else:
                jawab = fn(idx, r['teks_baris'], suara, p, konteks)
                hasil['panggilan_agen_kedua'] += 1
            bar['jawaban_agen_kedua'] = jawab
            if jawab is None:
                bar['putusan_rantai'] = 'antrean-manusia'
                bar['label_rantai'] = None
                bar['rantai_benar'] = False
                bar['alasan_putusan'] = 'agen kedua gagal -> antrean'
            else:
                bar['agen_kedua_benar'] = (jawab['label']
                                           == r['label_benar'])
                put = P.pendapat_kedua(idx, r['teks_baris'], suara, p,
                                       jawab, mode='agen-kedua')
                bar['putusan_rantai'] = put['putusan']
                bar['alasan_putusan'] = put['alasan']
                bar['label_rantai_l2'] = put['label']
                if put['putusan'] == 'tetap':
                    bar['label_rantai'] = v11
                    bar['koreksi_rantai'] = []
                elif put['putusan'] == 'berbalik':
                    # sistematika dihitung ulang deterministik dari peta final
                    kand = sorted((i, baris[i]) for i in label_penuh
                                  if i < len(baris))
                    sist = P._tandai_sistematika(baris, label_penuh, kand)
                    fin, jejak = terapkan_koreksi(
                        put['label'], r['teks_baris'], idx, sist, konteks,
                        set(e.get('bab_gabung') or []))
                    bar['label_rantai'] = fin
                    bar['koreksi_rantai'] = jejak
                else:  # antrean-manusia
                    bar['label_rantai'] = None
                    bar['koreksi_rantai'] = []
                bar['rantai_benar'] = (bar['label_rantai']
                                       == r['label_benar'])
        hasil['baris'].append(bar)
        print('%-5s no %-4s %-14s benar=%-8s v11=%-8s rantai=%-8s putusan=%s'
              % (kode, no, r['jenis_sengketa'], r['label_benar'],
                 bar.get('label_v11'), bar.get('label_rantai'),
                 bar.get('putusan_rantai')), flush=True)

    # ── skor ──
    b = hasil['baris']
    skor = {
        'n': len(b),
        'v11_benar': sum(1 for x in b if x['v11_benar']),
        'rantai_benar': sum(1 for x in b if x['rantai_benar']),
        'antrean': sum(1 for x in b
                       if x['putusan_rantai'] == 'antrean-manusia'),
        'ditandai': sum(1 for x in b if x['ditandai_hakim']),
        'berbalik': sum(1 for x in b
                        if x['putusan_rantai'] == 'berbalik'),
        'tetap': sum(1 for x in b if x['putusan_rantai'] == 'tetap'),
        'per_label_benar': {},
        'per_kelompok': {},
        'per_jenis': {},
        'flip': {'v11_salah_rantai_benar': 0, 'v11_benar_rantai_salah': 0},
    }
    for x in b:
        if x['v11_benar'] and not x['rantai_benar']:
            skor['flip']['v11_benar_rantai_salah'] += 1
        if not x['v11_benar'] and x['rantai_benar']:
            skor['flip']['v11_salah_rantai_benar'] += 1
    for kunci, grup in (('per_label_benar', 'label_benar'),
                        ('per_kelompok', 'kelompok'),
                        ('per_jenis', 'jenis_sengketa')):
        for g in sorted({x[grup] for x in b}):
            sub = [x for x in b if x[grup] == g]
            skor[kunci][g] = {
                'n': len(sub),
                'v11': sum(1 for x in sub if x['v11_benar']),
                'rantai': sum(1 for x in sub if x['rantai_benar']),
                'ditandai': sum(1 for x in sub if x['ditandai_hakim']),
                'antrean': sum(1 for x in sub
                               if x['putusan_rantai'] == 'antrean-manusia')}
    hasil['skor'] = skor
    json.dump(hasil, open(KELUAR, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\nSKOR: v11 %d/%d, rantai %d/%d, antrean %d, ditandai %d, '
          'panggilan agen kedua %d (rekaman %d)'
          % (skor['v11_benar'], skor['n'], skor['rantai_benar'], skor['n'],
             skor['antrean'], skor['ditandai'],
             hasil['panggilan_agen_kedua'],
             hasil['panggilan_agen_kedua_dari_rekaman']))
    print('flip: v11-salah->rantai-benar %d, v11-benar->rantai-salah %d'
          % (skor['flip']['v11_salah_rantai_benar'],
             skor['flip']['v11_benar_rantai_salah']))
    print('per label benar:', json.dumps(skor['per_label_benar'],
                                         ensure_ascii=False))
    print('per kelompok:', json.dumps(skor['per_kelompok'],
                                      ensure_ascii=False))


if __name__ == '__main__':
    main()
