#!/usr/bin/env python3
"""Verifikasi offline v11 pada 112 teks latih (NOL panggilan Jev).

Memuat peta3_jev.py dengan stub yang sama seperti tests/test_jev_hakim.py,
lalu:
  1. profil_bentuk() tiap teks dibandingkan dengan profil terukur di
     _sketsa/tabel_latih112.json (definisi sama, kecuali pemisah yang di
     v11 memakai pola LUAS '===== ... =====' — dilaporkan, bukan gagal).
  2. _susun_dari_bersih() pada 6 naskah Romawi-tanpa-BAB, 4 naskah CHAPTER,
     2 naskah pemisah (AM-2, AO-1), dan 1 naskah BOM (T1): aturan baru
     harus tampak di gabung/buang/baris.
Keluar 0 bila semua cocok.
"""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

DASAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DASAR))


class FakeSatpam:
    def __init__(self):
        self.panggilan = []

    def tanya_bebas_mutu(self, bahan, pertanyaan):
        self.panggilan.append((bahan, pertanyaan))
        return {nama: {'choice': 'paragraf', 'confidence': 0.9}
                for nama in (pertanyaan or {})}


class FakeKonversi:
    _SAMBUNG_GANTUNG = 0.2
    _SAMBUNG_AKHIR = 0.5
    mode = 'normal'

    @classmethod
    def _pecah_blok(cls, teks):
        baris = [(' '.join(m.split())) for m in (teks or '').split('\n')]
        return [{'text': b, 'lines': [n], 'kosong': not b}
                for n, b in enumerate(baris)]


FAKE_SATPAM = FakeSatpam()


def muat_peta3():
    app = types.ModuleType('app')
    app.__path__ = [str(DASAR / 'app')]
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
    spec = importlib.util.spec_from_file_location(
        '_peta3_verifikasi', str(DASAR / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def utama():
    P = muat_peta3()
    assert P.RULE_VERSION == 'jev-peta-v11', P.RULE_VERSION
    tabel = json.load(open(DASAR / '_sketsa' / 'tabel_latih112.json',
                           encoding='utf-8'))
    gagal = []
    cocok = 0
    pemisah_beda = []
    for entri in tabel:
        jalan = DASAR / entri['teks']
        teks = jalan.read_text(encoding='utf-8', errors='replace')
        prof = P.profil_bentuk(teks)
        lama = entri['profil']
        kunci = ['bab_romawi', 'bab_arab', 'chapter', 'romawi_tanpa_bab_jml',
                 'sistematika', 'tabel_baris_pipa', 'rasio_inggris',
                 'kti_d3', 'jml_bab_terdeteksi', 'huruf_berspasi_jml',
                 'nul_jml', 'bom_jml', 'kata', 'baris']
        beda = [k for k in kunci if prof[k] != lama[k]]
        if beda:
            gagal.append((entri['kode'], beda,
                          {k: (prof[k], lama[k]) for k in beda}))
        else:
            cocok += 1
        if prof['pemisah_gabung_jml'] != lama['pemisah_gabung_jml']:
            pemisah_beda.append((entri['kode'], prof['pemisah_gabung_jml'],
                                 lama['pemisah_gabung_jml']))
    print(f'profil cocok dgn tabel terukur: {cocok}/112')
    print(f'profil pemisah (pola LUAS v11 vs SEMPIT analisis): '
          f'{len(pemisah_beda)} beda (diharapkan: pola luas menangkap '
          f'pagar nama berkas non-BAB juga)')
    for kode, baru, lama in pemisah_beda[:8]:
        print(f'  {kode}: v11={baru} analisis={lama}')
    for kode, beda, nilai in gagal:
        print(f'GAGAL {kode}: {beda} {nilai}')
    # --- aturan susun pada naskah bentuk khusus ---
    def baca(kode):
        entri = next(e for e in tabel if e['kode'] == kode)
        return (DASAR / entri['teks']).read_text(
            encoding='utf-8', errors='replace')

    def cek(nama, syarat, info=''):
        print(('  LULUS ' if syarat else '  GAGAL ') + nama
              + (f' — {info}' if info and not syarat else ''))
        if not syarat:
            gagal.append((nama, info))

    for kode in ('Y1', 'Y2', 'AD1', 'AD2', 'AD3', 'AG1'):
        d = P._susun_dari_bersih(baca(kode))
        judul = sorted(v[1] for v in d['gabung'].values())
        cek(f'susun Romawi {kode}: judul bab di gabung',
            'PENDAHULUAN' in judul and 'KESIMPULAN DAN SARAN' in judul,
            str(judul))
        cek(f'susun Romawi {kode}: profil romawi_tanpa_bab',
            d['profil']['penomoran_bab'] == 'romawi_tanpa_bab')
    # Temuan jujur: T2 hanya punya 4 CHAPTER polos di BADAN (I-IV).
    # CHAPTER V hanya ada di DAFTAR ISI (baris 1039); badan Bab V dibuka
    # judul polos 'CONCLUSION AND SUGGESTION' (baris 525) tanpa penanda.
    # Jadi harapan 5 bab hanya benar untuk T1/T3/AH1. Klaim analisis
    # "chapter I-V terdeteksi 5 tiap naskah" menghitung sebutan daftar isi.
    harap_chapter = {'T1': ['CHAPTER I', 'CHAPTER II', 'CHAPTER III',
                            'CHAPTER IV', 'CHAPTER V'],
                     'T2': ['CHAPTER I', 'CHAPTER II', 'CHAPTER III',
                            'CHAPTER IV'],
                     'T3': ['CHAPTER I', 'CHAPTER II', 'CHAPTER III',
                            'CHAPTER IV', 'CHAPTER V'],
                     'AH1': ['CHAPTER I', 'CHAPTER II', 'CHAPTER III',
                             'CHAPTER IV', 'CHAPTER V']}
    for kode, harap in harap_chapter.items():
        d = P._susun_dari_bersih(baca(kode))
        bab = sorted(v[0] for v in d['gabung'].values()
                     if v[0].startswith('CHAPTER'))
        cek(f'susun CHAPTER {kode}: bab CHAPTER badan di gabung',
            bab == sorted(harap), str(bab))
    d = P._susun_dari_bersih(baca('T2'))
    cek('susun CHAPTER T2: CHAPTER V (hanya daftar isi) tidak dipaksa',
        not any(v[0] == 'CHAPTER V' for v in d['gabung'].values()))
    for kode in ('AM-2', 'AO-1'):
        d = P._susun_dari_bersih(baca(kode))
        pem = [i for i, b in enumerate(d['baris']) if '=====' in b]
        cek(f'susun pemisah {kode}: semua pemisah dibuang',
            bool(pem) and all(i in d['buang'] for i in pem),
            f'pemisah={len(pem)} buang={len(d["buang"])}')
        cek(f'susun pemisah {kode}: tidak ada pemisah di gabung',
            not any('=====' in ' '.join(v)
                    for v in d['gabung'].values()))
    d = P._susun_dari_bersih(baca('T1'))
    cek('susun BOM T1: tidak ada BOM di baris',
        not any('\ufeff' in b for b in d['baris']))
    print(f'\nGAGAL: {len(gagal)}')
    sys.exit(1 if gagal else 0)


if __name__ == '__main__':
    utama()
