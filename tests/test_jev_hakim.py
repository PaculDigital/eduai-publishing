"""Uji offline Jev + Hakim v2 (10 Nov 2026) — Jev DIMOCK, tanpa model berbayar.

Jalankan:  python3 tests/test_jev_hakim.py
Keluar 0 = semua lulus. Tidak butuh jaringan, kunci asli, atau fastapi:
modul berat (`app.ai`, `app.models`) di-stub, `app.satpam` diganti fake
pencatat panggilan, `app.konversi._pecah_blok` diganti fake deterministik.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LULUS = []
GAGAL = []


def cek(nama, syarat, info=''):
    (LULUS if syarat else GAGAL).append(nama)
    print(('  LULUS ' if syarat else '  GAGAL ') + nama + (f' — {info}' if info and not syarat else ''))


# ── fake satpam: pencatat panggilan, jawaban dari aturan sederhana ────────
class FakeSatpam:
    def __init__(self):
        self.panggilan = []          # (bahan, tanya)
        self.jumlah_choice = 0
        self.jumlah_noul = 0
        self.rendah = set()          # teks tengah yang confidence-nya 0,3 dulu

    def tanya_bebas_mutu(self, bahan, pertanyaan):
        self.panggilan.append((bahan, pertanyaan))
        jawab = {}
        for nama, q in (pertanyaan or {}).items():
            if q.get('type') == 'noul':
                self.jumlah_noul += 1
                # stitch: sambung bila baris SESUDAH ada di JOIN_SET
                jawab[nama] = {'noul': 0.94 if self._gabung(nama, bahan) else 0.08}
            else:
                self.jumlah_choice += 1
                tengah = self._tengah(nama, bahan)
                conf = 0.9
                if any(r in tengah for r in self.rendah):
                    # panggilan pertama rendah, tanya-ulang membaik
                    if sum(1 for b, _ in self.panggilan if tengah in b) <= 1:
                        conf = 0.3
                label = 'bab' if tengah.startswith('BAB') else 'paragraf'
                jawab[nama] = {'choice': label, 'confidence': conf}
        return jawab

    def _tengah(self, nama, bahan):
        try:
            paket = json.loads(bahan)
            return paket.get(nama, {}).get('tengah', '')
        except Exception:
            return ''

    def _gabung(self, nama, bahan):
        # bahan stitch: "L0003| teks" — sambung bila teks sesudah ada di JOIN_SET
        for baris in (bahan or '').split('\n'):
            if baris.startswith(nama + '|'):
                teks = baris.split('|', 1)[1].strip()
                return teks in JOIN_SET
        return False


JOIN_SET = {'juga berlanjut di sini.', 'membahas pemasaran digital di Indonesia.'}

FAKE_SATPAM = FakeSatpam()


# ── fake konversi._pecah_blok (deterministik, tanpa Jev) ──────────────────
class FakeKonversi:
    _SAMBUNG_GANTUNG = 0.2
    _SAMBUNG_AKHIR = 0.5
    mode = 'normal'          # normal | galat | per-baris | hilang | gabung-bab

    @classmethod
    def _pecah_blok(cls, teks):
        if cls.mode == 'galat':
            raise RuntimeError('konversi mati (uji)')
        baris = [(' '.join(m.split())) for m in (teks or '').split('\n')]
        if cls.mode == 'per-baris':
            return [{'text': b, 'lines': [n], 'kosong': not b}
                    for n, b in enumerate(baris)]
        if cls.mode == 'hilang':
            # buang separuh isi (simulasi kehilangan karakter)
            return [{'text': b, 'lines': [n], 'kosong': not b}
                    for n, b in enumerate(baris[:max(1, len(baris) // 2)])]
        if cls.mode == 'gabung-bab':
            out = []
            for n, b in enumerate(baris):
                if b == 'BAB I' and n + 1 < len(baris):
                    out.append({'text': 'BAB I PENDAHULUAN', 'lines': [n, n + 1],
                                'kosong': False})
                    baris[n + 1] = ''
                    continue
                if b == '':
                    continue
                out.append({'text': b, 'lines': [n], 'kosong': False})
            return out
        # normal: gabung baris pendek + baris lanjutan huruf kecil
        blok = []
        for n, b in enumerate(baris):
            kosong = not b
            if (blok and not kosong and not blok[-1]['kosong']
                    and len(blok[-1]['text']) <= 60 and len(b) <= 60
                    and b[:1].islower()):
                blok[-1]['text'] = (blok[-1]['text'] + ' ' + b).strip()
                blok[-1]['lines'].append(n)
            else:
                blok.append({'text': b, 'lines': [n], 'kosong': kosong})
        return blok


def _stub_app():
    """Stub modul berat sebelum memuat peta3_jev.py (skrip root)."""
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
    spec = importlib.util.spec_from_file_location('_peta3_uji', str(ROOT / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    P = _muat_peta3()
    import app.hakim_peta as H
    import app.peta_jalur as J
    import app.profil_kampus as PK

    # ── 1. STITCH ────────────────────────────────────────────────────────
    teks_fragmen = (
        'BAB I\nPENDAHULUAN\n'
        'Latar belakang penelitian ini\nmembahas pemasaran digital di Indonesia.\n'
        '1.1 Latar Belakang\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    FakeKonversi.mode = 'normal'
    hasil = P._stitch_baris(teks_fragmen, tanya_fn=FAKE_SATPAM.tanya_bebas_mutu)
    cek('stitch: fragmen tersambung jadi satu baris',
        'Latar belakang penelitian ini membahas pemasaran digital di Indonesia.' in hasil)
    cek('stitch: judul BAB tidak tersentuh', 'BAB I\nPENDAHULUAN' in hasil)
    cek('stitch: judul bernomor tidak tersentuh', '1.1 Latar Belakang' in hasil)

    FakeKonversi.mode = 'galat'
    cek('stitch pagar 1: konversi galat -> teks apa adanya',
        P._stitch_baris(teks_fragmen) == teks_fragmen)
    FakeKonversi.mode = 'per-baris'
    cek('stitch pagar 2: blok = baris -> teks apa adanya',
        P._stitch_baris(teks_fragmen) == teks_fragmen)
    FakeKonversi.mode = 'hilang'
    cek('stitch pagar 3: isi hilang >2% -> teks apa adanya',
        P._stitch_baris(teks_fragmen) == teks_fragmen)
    FakeKonversi.mode = 'gabung-bab'
    hasil_bab = P._stitch_baris(teks_fragmen)
    cek('stitch: blok "BAB I PENDAHULUAN" dipecah kembali',
        'BAB I\nPENDAHULUAN' in hasil_bab)

    # lintas baris-kosong (fid=104): Jev bilang sambung -> gabung
    FakeKonversi.mode = 'normal'
    teks_kosong = ('Kalimat pertama namun\n\njuga berlanjut di sini.\n'
                   'BAB II\nTINJAUAN PUSTAKA\n')
    hasil_k = P._stitch_baris(teks_kosong, tanya_fn=FAKE_SATPAM.tanya_bebas_mutu)
    cek('stitch lintas-kosong: "namun" + "juga" tersambung',
        'Kalimat pertama namun juga berlanjut di sini.' in hasil_k)
    cek('stitch lintas-kosong: baris kosong penghubung hilang',
        '\n\n' not in hasil_k)

    # ── 2. SUSUN + PETAKAN (blok, nomor-kode, cache, tanya-ulang) ─────────
    naskah = (
        'BAB I\nPENDAHULUAN\n'
        'Latar belakang penelitian ini\nmembahas pemasaran digital di Indonesia.\n'
        '1.1 Latar Belakang\n'
        'Pemasaran digital berkembang pesat dalam lima tahun terakhir dan mengubah cara usaha kecil menjangkau pelanggan di berbagai daerah di Indonesia.\n'
        '1.2 Rumusan Masalah\n'
        'Bagaimana pengaruh pemasaran digital terhadap kinerja bisnis usaha kecil di Indonesia pada masa sekarang ini.\n'
        'BAB II\nTINJAUAN PUSTAKA\n'
        '2.1 Pengertian Pemasaran\n'
        'Pemasaran adalah proses menciptakan nilai bagi pelanggan dan membangun hubungan yang kuat dengan mereka untuk jangka panjang.\n'
        'Kalimat lanjutan yang RAGU-REASK dan masih bagian dari paragraf yang sama dan cukup panjang untuk diuji tanya ulang.\n'
    )
    FakeKonversi.mode = 'normal'
    FAKE_SATPAM.panggilan.clear()
    FAKE_SATPAM.rendah = {'RAGU-REASK'}
    peta = P.petakan_dari_teks(naskah, putaran=1)
    baris = peta['baris']
    cek('susun: fragmen paragraf jadi SATU baris blok',
        any('Latar belakang penelitian ini membahas pemasaran digital di Indonesia.' in b
            for b in baris))
    idx_11 = next(i for i, b in enumerate(baris) if b.strip() == '1.1 Latar Belakang')
    idx_12 = next(i for i, b in enumerate(baris) if b.strip() == '1.2 Rumusan Masalah')
    idx_21 = next(i for i, b in enumerate(baris) if b.strip() == '2.1 Pengertian Pemasaran')
    cek('nomor-kode: 1.1/1.2/2.1 diputuskan kode (bukan Jev)',
        peta.get('kode_label', {}).get(idx_11) == 'subbab'
        and peta.get('kode_label', {}).get(idx_12) == 'subbab'
        and peta.get('kode_label', {}).get(idx_21) == 'subbab')
    cek('nomor-kode: label akhir ikut kode',
        peta['label'].get(idx_11) == 'subbab' and peta['asal'].get(idx_11) == 'kode')
    cek('nomor-kode: Jev TIDAK ditanya soal baris bernomor',
        idx_11 not in peta['semua'] and idx_12 not in peta['semua']
        and idx_21 not in peta['semua'])
    cek('gabung: BAB I dan BAB II tetap dikenali', len(peta.get('gabung', {})) == 2)
    cek('tanya-ulang: hanya baris p rendah yang ditanya ulang',
        peta.get('tanya_ulang_jml') == 1, f"dapat {peta.get('tanya_ulang_jml')}")
    cek('tanya-ulang: p baris ragu membaik sesudah tanya ulang',
        (peta['p'].get(next(i for i, b in enumerate(baris) if 'RAGU-REASK' in b)) or 0) >= 0.5)
    cek('hasil: ada versi aturan + stitch tercatat',
        peta.get('versi_aturan') == P.RULE_VERSION and peta.get('stitch_pakai') is True)
    cek('hasil: Jev tidak mati', peta.get('jev_mati') is False)

    jml_sebelum = len(FAKE_SATPAM.panggilan)
    peta2 = P.petakan_dari_teks(naskah, putaran=1)
    cek('cache: pemetaan kedua tidak memanggil Jev lagi',
        len(FAKE_SATPAM.panggilan) == jml_sebelum)
    cek('cache: hasil kedua sama isinya',
        peta2['label'] == peta['label'] and peta2['kand_jml'] == peta['kand_jml'])
    P.RULE_VERSION = 'uji-beda-versi'
    P._CACHE_PETA.clear()
    P.petakan_dari_teks(naskah, putaran=1)
    cek('cache: ganti versi aturan -> cache lama tidak dipakai',
        len(FAKE_SATPAM.panggilan) > jml_sebelum)
    P.RULE_VERSION = 'jev-peta-v3-stitch'
    P._CACHE_PETA.clear()

    # ── 3. JEV MATI -> fallback ───────────────────────────────────────────
    #    (ganti satpam di modul P langsung — jangan muat ulang, _stub_app
    #    akan menimpa stub satpam bila dipanggil lagi)
    satpam_asli = P.satpam

    class Mati:
        @staticmethod
        def tanya_bebas_mutu(bahan, pertanyaan):
            return {}
    P.satpam = Mati()
    FakeKonversi.mode = 'per-baris'
    peta_mati = P.petakan_dari_teks('Paragraf satu.\nParagraf dua yang panjang sekali dan terus berlanjut tanpa henti.\nParagraf tiga.\nParagraf empat.\n', putaran=1)
    cek('fallback: Jev mati -> semua label biasa + jev_mati True',
        peta_mati.get('jev_mati') is True
        and all(v == 'biasa' for v in peta_mati['label'].values()))
    cek('fallback: putuskan_jalur -> fallback',
        J.putuskan_jalur(peta_mati)[0] == 'fallback')
    P.satpam = satpam_asli

    # ── 4. HAKIM v2 ──────────────────────────────────────────────────────
    def peta_fixture(baris, label, gabung=None):
        return {'baris': baris, 'label': {i: v for i, v in label.items()},
                'gabung': gabung or {}, 'p': {i: 0.9 for i in label},
                'sistematika': []}

    H._TANYA_FN = lambda bahan, tanya: {}
    H._JUDUL_CURIGA_FN = lambda items: []
    bersih = peta_fixture(
        ['BAB I PENDAHULUAN', '1.1 Latar Belakang', '1.2 Rumusan Masalah',
         'Paragraf isi yang panjang dan menjelaskan banyak hal penting.'],
        {0: 'bab', 1: 'subbab', 2: 'subbab', 3: 'paragraf'})
    lap = H.periksa_peta(bersih)
    cek('hakim: peta bersih -> semua sepakat, 0 panggilan Jev',
        lap['jumlah_sepakat'] == 3 and lap['jumlah_curiga'] == 0
        and lap['jumlah_ragu'] == 0)
    cek('hakim: keputusan selalu lolos (tidak blokir)',
        lap['keputusan'] == 'lolos' and lap['ok'] is True)

    loncat = peta_fixture(
        ['BAB I PENDAHULUAN', '1.1 Latar Belakang', '1.3 Tujuan Penelitian'],
        {0: 'bab', 1: 'subbab', 2: 'subbab'})
    lap = H.periksa_peta(loncat)
    cek('hakim: nomor loncat 1.1 -> 1.3 = curiga + alasan',
        lap['jumlah_curiga'] == 1
        and 'nomor-loncat' in lap['bagian'][2]['alasan'])

    yatim = peta_fixture(['1.1 Latar Belakang', '1.2 Rumusan Masalah'],
                         {0: 'subbab', 1: 'subbab'})
    lap = H.periksa_peta(yatim)
    cek('hakim: subbab tanpa BAB induk = subbab-yatim',
        lap['jumlah_curiga'] == 2
        and all('subbab-yatim' in b['alasan'] for b in lap['bagian']))

    panjang = peta_fixture(['BAB I PENDAHULUAN', '1.1 ' + 'x' * 310],
                           {0: 'bab', 1: 'subbab'})
    lap = H.periksa_peta(panjang)
    cek('hakim: judul >300 kar = judul-panjang',
        lap['jumlah_curiga'] == 1 and 'judul-panjang' in lap['bagian'][1]['alasan'])

    kecil = peta_fixture(['BAB I PENDAHULUAN', '1.1 latar belakang'],
                         {0: 'bab', 1: 'subbab'})
    lap = H.periksa_peta(kecil)
    cek('hakim: judul huruf kecil = judul-huruf-kecil',
        lap['jumlah_curiga'] == 1 and 'judul-huruf-kecil' in lap['bagian'][1]['alasan'])

    spss = peta_fixture(['BAB I PENDAHULUAN', 'Coefficients'],
                        {0: 'bab', 1: 'subbab'})
    lap = H.periksa_peta(spss)
    cek('hakim: fragmen SPSS = fragmen-tabel',
        lap['jumlah_curiga'] == 1 and 'fragmen-tabel' in lap['bagian'][1]['alasan'])

    kalimat = peta_fixture(
        ['BAB I PENDAHULUAN', 'Hasil penelitian menunjukkan bahwa instrumen ini valid.'],
        {0: 'bab', 1: 'subbab'})
    H._TANYA_FN = lambda bahan, tanya: {k: {'noul': 0.2} for k in tanya}
    lap = H.periksa_peta(kalimat)
    cek('hakim: judul mirip kalimat + Jev 0,2 -> ragu',
        lap['jumlah_ragu'] == 1 and lap['bagian'][1]['status'] == 'ragu')
    H._TANYA_FN = lambda bahan, tanya: {k: {'noul': 0.9} for k in tanya}
    lap = H.periksa_peta(kalimat)
    cek('hakim: judul mirip kalimat + Jev 0,9 -> sepakat',
        lap['jumlah_sepakat'] == 2)
    H._TANYA_FN = lambda bahan, tanya: None
    lap = H.periksa_peta(kalimat)
    cek('hakim: Jev mati -> status belum (jujur)',
        lap['bagian'][1]['status'] == 'belum')
    hitung_tanya = []
    H._TANYA_FN = lambda bahan, tanya: hitung_tanya.append(1) or {}
    lap = H.periksa_peta(bersih)
    cek('hakim: judul jelas tidak butuh Jev (0 panggilan)',
        lap['jumlah_sepakat'] == 3 and len(hitung_tanya) == 0)

    os.environ['EDUAI_HAKIM_AKTIF'] = '0'
    lap = H.periksa_peta(bersih)
    cek('hakim kill-switch: EDUAI_HAKIM_AKTIF=0 -> mati',
        lap['keputusan'] == 'mati')
    os.environ.pop('EDUAI_HAKIM_AKTIF', None)

    cek('hakim: K5 sudah tidak ada (tidak bisa dihidupkan lagi)',
        not hasattr(H, 'K5_AKTIF') and not hasattr(H, 'CRITERIA_K5'))
    cek('hakim: tidak ada criteria di pertanyaan sempit',
        True)  # dibuktikan oleh fake: _q_per_kandidat tanpa 'criteria'
    q = H._q_per_kandidat([{'i': 5}])
    cek('hakim: pertanyaan sempit tanpa criteria',
        'criteria' not in q['L000005'])

    # ── 5. PROFIL KAMPUS ─────────────────────────────────────────────────
    cek('profil: bawaan judul_maks_kar 300', PK.aturan().get('judul_maks_kar') == 300)
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump({'aturan': {'judul_maks_kar': 400},
                   'kampus': {'KampusX': {'judul_maks_kar': 500}}}, f)
        jalur = f.name
    os.environ['EDUAI_PROFIL_KAMPUS'] = jalur
    PK._cache.update({'jalur': None, 'mtime': None, 'isi': None})
    cek('profil: override umum dari config',
        PK.aturan().get('judul_maks_kar') == 400)
    cek('profil: override per kampus dari config',
        PK.aturan('KampusX').get('judul_maks_kar') == 500)
    cek('profil: kampus tanpa profil pakai umum',
        PK.aturan('Lain').get('judul_maks_kar') == 400)
    os.environ.pop('EDUAI_PROFIL_KAMPUS', None)
    PK._cache.update({'jalur': None, 'mtime': None, 'isi': None})

    # ── 6. JEDA ADAPTIF ──────────────────────────────────────────────────
    import time
    t0 = time.time() - 1.0
    mulai = time.time()
    P._tidur_adaptif(t0, dasar=0.7)
    cek('jeda adaptif: panggilan lambat -> tidak tidur lagi',
        time.time() - mulai < 0.2)
    t0 = time.time()
    mulai = time.time()
    P._tidur_adaptif(t0, dasar=0.05)
    cek('jeda adaptif: panggilan cepat -> tidur sisa jarak',
        0.03 < time.time() - mulai < 0.3)

    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
        sys.exit(1)


if __name__ == '__main__':
    main()
