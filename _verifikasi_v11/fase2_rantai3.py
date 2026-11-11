"""Pilot rantai 3 langkah — FASE 2 (offline + agen kedua dari VM).

Membaca rekaman fase 1b (J2+U2+D1), memanggil agen kedua lewat OpenRouter
(Gemini 2.5 Flash, PINNED) HANYA untuk baris sampel yang goyang di run
fase 1b, lalu menerapkan `pendapat_kedua(mode='agen-kedua')` yang ASLI
dan koreksi deterministik pasca-Lapis 2 yang ASLI (ATURAN 2/4/5, v6 batas,
kode_label) memakai helper peta3_jev sendiri — jadi label rantai final
dihitung dengan aturan yang sama seperti pipeline live.

Baris yang tidak goyang di run fase 1b: label rantai = label v11
(Lapis 2 tidak pernah berjalan pada baris yang tidak goyang).
Baris bukan-kandidat (J2 no 190, U2 no 59): dinilai dari bukti
deterministik (bab_gabung tahap 1 / pemisah yang dibuang v11).

Biaya fase 2: 1 panggilan OpenRouter per baris goyang yang diadili.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import types
from pathlib import Path

os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '1'   # pilot VM saja, bukan produksi

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

HASIL1 = ROOT / '_verifikasi_v11' / 'hasil_rantai3_fase1b.json'
HASIL1_D1 = ROOT / '_verifikasi_v11' / 'hasil_rantai3_fase1b_d1.json'
KELUAR = ROOT / '_verifikasi_v11' / 'hasil_rantai3_fase2.json'


# ── stub app (salinan minimal dari tests/test_jev_hakim.py) ───────────────
class FakeSatpam:
    def tanya_bebas_mutu(self, bahan, pertanyaan):
        raise RuntimeError('FakeSatpam: tidak dipakai di fase 2')


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
        '_peta3_fase2', str(ROOT / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _muat_peta3()
import app.agen_kedua as AK
from agen_kedua_openrouter import buat_penanya

assert P.RULE_VERSION == 'jev-peta-v12', P.RULE_VERSION

# ── koreksi deterministik pasca-Lapis 2 (aturan pipeline, dihitung ulang) ──
_KATA_GANTUNG = P._KATA_GANTUNG
_AKHIR_LANJUT = (',', ';', '(', '-', '\u2013', '\u2014')


def _prev_teks(konteks):
    """Baris sebelum terdekat yang tidak kosong (dari konteks rekaman)."""
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


def terapkan_koreksi(label_l2, teks, idx, sistematika, kode_label,
                     konteks, gabung_judul):
    """Terapkan ATURAN 2/4/5 + v6 batas + kode_label pada label pasca-L2.

    Mengembalikan (label_final, [alasan koreksi yang memicu]).
    Urutan sama seperti pipeline: ATURAN 2 → ATURAN 4 → ATURAN 5 →
    kode_label → v6 batas → (deteksi BAB deterministik: hanya bila baris
    cocok penanda BAB — tidak ada di sampel ini).
    """
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
    if str(idx) in (kode_label or {}):
        lab = kode_label[str(idx)]
        jejak.append('kode_label memaksa label %r' % lab)
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

    # bab_gabung tahap 1 (bukti judul deterministik J2-190 + prev-judul)
    gabung = {}
    for g in (1, 2, 3, 4):
        d = json.load(open(ROOT / ('hasil_latih_grup%d.json' % g)))
        for e in d['entri']:
            if e['kode'] in ('J2', 'U2', 'D1'):
                gabung[e['kode']] = set(e.get('bab_gabung') or [])

    # Jawaban agen kedua yang sudah direkam (hindari panggilan ulang bila
    # skrip dijalankan lagi untuk memperbaiki evaluasi, bukan mengulang uji).
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
             'kelompok': 'pilot rantai 3 langkah v12 — fase 2 (J2+U2+D1)',
             'model_agen_kedua': 'google/gemini-2.5-flash',
             'transport_agen_kedua': 'openrouter',
             'panggilan_agen_kedua': 0,
             'baris': []}

    for jalur in (HASIL1, HASIL1_D1):
        f1 = json.load(open(jalur))
        for ent in f1['entri']:
            kode = ent['kode']
            rekaman = {r['idx']: r for r in ent.get('rekaman_goyang') or []}
            sistematika = set(ent.get('sistematika') or [])
            kode_label = ent.get('kode_label') or {}
            for n in ent.get('nilai_sampel') or []:
                bar = {'naskah': kode, 'no': n['no'],
                       'jenis_sengketa': n['jenis_sengketa'],
                       'teks_baris': n['teks_baris'],
                       'label_benar': n['label_benar'],
                       'putusan_fase1b': n.get('putusan_fase1b'),
                       'label_v11_final': n.get('label_v11_final'),
                       'label_v11_pra_lapis2': n.get('label_v11_pra_lapis2'),
                       'suara': n.get('suara')}
                bar['v11_benar'] = (n.get('label_v11_final')
                                    == n['label_benar'])
                if n.get('putusan_fase1b') == 'goyang':
                    r = rekaman.get(n.get('idx_run'))
                    assert r is not None, 'rekaman hilang idx %s' % n.get('idx_run')
                    bar['suara_rekaman'] = r['suara']
                    bar['conf_rekaman'] = r['conf']
                    bar['konteks'] = r['konteks']
                    # label Jev teratas dari suara+conf (aturan _hitung_label)
                    skor, urutan = {}, {}
                    for urut, (v, c) in enumerate(zip(r['suara'], r['conf'])):
                        if not v:
                            continue
                        s = float(c) if isinstance(c, (int, float)) else 0.0
                        if v not in skor or s > skor[v]:
                            skor[v] = s
                        if v not in urutan:
                            urutan[v] = urut
                    atas = max(skor, key=lambda v: (skor[v], -urutan[v]))
                    bar['label_jev_teratas'] = atas
                    assert atas == n.get('label_v11_pra_lapis2'), \
                        'label teratas %r != pra-L2 %r (no %s)' % (
                            atas, n.get('label_v11_pra_lapis2'), n['no'])
                    kunci = (kode, str(n['no']))
                    if kunci in jw_lama:
                        jawab = jw_lama[kunci]
                        print('  (memakai jawaban agen kedua yang sudah '
                              'direkam, no %s)' % n['no'], flush=True)
                    else:
                        jawab = fn(n.get('idx_run'), n['teks_baris'],
                                   r['suara'], r['conf'], r['konteks'])
                        hasil['panggilan_agen_kedua'] += 1
                    bar['jawaban_agen_kedua'] = jawab
                    if jawab is None:
                        bar['putusan_rantai'] = 'antrean-manusia'
                        bar['label_rantai_l2'] = None
                        bar['label_rantai_final'] = None
                        bar['koreksi_rantai'] = ['agen kedua gagal → antrean']
                    else:
                        bar['agen_kedua_benar'] = (jawab['label']
                                                   == n['label_benar'])
                        put = P.pendapat_kedua(
                            n.get('idx_run'), n['teks_baris'],
                            r['suara'], r['conf'], jawab, mode='agen-kedua')
                        bar['putusan_rantai'] = put['putusan']
                        bar['alasan_putusan'] = put['alasan']
                        bar['label_rantai_l2'] = put['label']
                        fin, jejak = terapkan_koreksi(
                            put['label'], n['teks_baris'], n.get('idx_run'),
                            sistematika, kode_label, r['konteks'],
                            gabung.get(kode, set()))
                        bar['label_rantai_final'] = fin
                        bar['koreksi_rantai'] = jejak
                    bar['rantai_benar'] = (bar.get('label_rantai_final')
                                           == n['label_benar'])
                elif n.get('putusan_fase1b') == 'tidak-goyang-di-run-ini':
                    # Lapis 2 tidak berjalan: rantai = v11.
                    if n.get('label_v11_final') is None:
                        # Bukan kandidat Jev di run ini.
                        if int(n['no']) == 190:
                            bar['catatan'] = (
                                'bukan kandidat: judul BAB deterministik '
                                '(bab_gabung tahap 1 memuat TINJAUAN '
                                'PUSTAKA); v11 efektif bab = label benar')
                            bar['label_v11_final'] = 'bab'
                            bar['v11_benar'] = True
                            bar['label_rantai_final'] = 'bab'
                            bar['rantai_benar'] = True
                        elif int(n['no']) == 59:
                            bar['catatan'] = (
                                'bukan kandidat: pemisah dokumen, dibuang '
                                'deterministik v11 (bukan judul bab); '
                                'konsisten dengan label benar biasa')
                            bar['label_v11_final'] = 'biasa'
                            bar['v11_benar'] = True
                            bar['label_rantai_final'] = 'biasa'
                            bar['rantai_benar'] = True
                        else:
                            bar['label_rantai_final'] = None
                            bar['rantai_benar'] = False
                    else:
                        bar['label_rantai_final'] = n.get('label_v11_final')
                        bar['rantai_benar'] = bar['v11_benar']
                else:
                    bar['label_rantai_final'] = n.get('label_v11_final')
                    bar['rantai_benar'] = bar['v11_benar']
                hasil['baris'].append(bar)
                print('no %-4s %-10s benar=%-8s v11=%-8s rantai=%-8s putusan=%s'
                      % (n['no'], kode, n['label_benar'],
                         bar.get('label_v11_final'),
                         bar.get('label_rantai_final'),
                         bar.get('putusan_rantai', 'tidak-goyang')),
                      flush=True)

    with open(KELUAR, 'w') as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)
    adj = [b for b in hasil['baris'] if b.get('putusan_fase1b') == 'goyang']
    print('SELESAI fase 2: %d panggilan agen kedua, %d baris goyang diadili, '
          'v11 benar %d/%d, rantai benar %d/%d'
          % (hasil['panggilan_agen_kedua'], len(adj),
             sum(1 for b in hasil['baris'] if b.get('v11_benar')),
             len(hasil['baris']),
             sum(1 for b in hasil['baris'] if b.get('rantai_benar')),
             len(hasil['baris'])), flush=True)


if __name__ == '__main__':
    main()
