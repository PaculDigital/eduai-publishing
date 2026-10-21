"""UKUR: 2 bab BERURUTAN vs BERSAMAAN — berapa detik benar-benar dihemat.

ACC Bos 19 Okt 2026. AI DIPALSUKAN dengan jeda tetap ⇒ mengukur STRUKTUR
(apakah benar bersamaan), bukan kecepatan model.

CARA BACA:
  Kalau `bersamaan` jauh lebih cepat dari `berurutan`, paralel BEKERJA.
  Kalau hampir sama, paralel TIDAK bekerja (ada yang mengunci diam-diam).
"""
import sys
import tempfile
import time
import shutil

sys.path.insert(0, '/opt/data')

JEDA = 0.30          # tiru tiap panggilan AI butuh 0,30 dtk


def _palsukan(P):
    def call_palsu(prompt, *a, **kw):
        p = prompt or ''
        time.sleep(JEDA)
        if 'Skeptic' in p:
            return 'Kritik: paragraf panjang.'
        if 'Pragmatist' in p:
            return 'Saran: pecah paragraf.'
        if 'Buat ringkasan 200 kata' in p or 'TOKOH UTAMA' in p:
            return 'TOKOH UTAMA: x\nKONSEP INTI: y'
        return ('Isi bab. ' + 'Kalimat penjelas cukup panjang. ' * 30
                + '(Penulis, 2020)')

    P.call_llm = call_palsu
    P.search_real_references = lambda *a, **kw: [
        {'title': 'Buku Uji', 'authors': ['P'], 'year': 2020,
         'publisher': 'A', 'type': 'book'}]
    P.verify_text_citations = lambda t, r: {'clean_text': t, 'unverified': []}
    P.render_html_to_png = lambda h, p: p
    P.generate_ilustrasi_api = lambda *a, **kw: []
    P.MIN_SITASI = 0


def _outline():
    return {'_judul': 'Ukur', 1: {'title': 'Bab Satu', 'subs': [
        ('1.1', 'A', 'p'), ('1.2', 'B', 'p')]},
        2: {'title': 'Bab Dua', 'subs': [('2.1', 'C', 'p'), ('2.2', 'D', 'p')]}}


def main():
    import buku_umum_pipeline as P
    import penyusun_buku as PB
    _palsukan(P)

    batas_asli = PB._BATAS_BAB

    # 1) BERURUTAN (batas 1)
    PB._BATAS_BAB = 1
    d1 = tempfile.mkdtemp(prefix='ukur_seq_')
    t0 = time.time()
    PB.susun_buku('Ukur', _outline(), jenis='umum', keluar_dir=d1,
                  batas_bab=2, lapor=lambda s: None)
    berurutan = time.time() - t0

    # 2) BERSAMAAN (batas 2)
    PB._BATAS_BAB = 2
    d2 = tempfile.mkdtemp(prefix='ukur_par_')
    t0 = time.time()
    PB.susun_buku('Ukur', _outline(), jenis='umum', keluar_dir=d2,
                  batas_bab=2, lapor=lambda s: None)
    bersamaan = time.time() - t0

    PB._BATAS_BAB = batas_asli
    shutil.rmtree(d1, ignore_errors=True)
    shutil.rmtree(d2, ignore_errors=True)

    hemat = berurutan - bersamaan
    persen = (hemat / berurutan * 100) if berurutan else 0
    print(f'\n{"=" * 58}')
    print(f'  BERURUTAN (batas 1) : {berurutan:6.2f} dtk')
    print(f'  BERSAMAAN (batas 2) : {bersamaan:6.2f} dtk')
    print(f'  HEMAT               : {hemat:6.2f} dtk  ({persen:.0f}%)')
    print(f'  PERCEPATAN          : {berurutan / bersamaan:.2f}×' if bersamaan else '')
    print(f'{"=" * 58}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
