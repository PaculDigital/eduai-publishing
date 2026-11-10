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
                # ── v6.4: penanda JEV-BAB — fake melabel 'bab' untuk
                #    menguji demosi deterministik (tanpa penanda BAB asli).
                if 'JEV-BAB' in tengah:
                    label = 'bab'
                # ── v6.3: penanda GOYANG-PB — suara terbelah paragraf/biasa
                #    antar gelombang (panggilan 1: paragraf 0,3 → tanya-ulang
                #    karena p rendah; panggilan 2: biasa 0,9 → goyang PB;
                #    panggilan 3: paragraf 0,9 → tanya-ulang batas goyang).
                if 'GOYANG-PB' in tengah:
                    n = sum(1 for b, _ in self.panggilan if tengah in b)
                    if n <= 1:
                        label, conf = 'paragraf', 0.3
                    elif n == 2:
                        label, conf = 'biasa', 0.9
                    else:
                        label, conf = 'paragraf', 0.9
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
            # cerminan pagar asli (app/sambung_kode v6): judul BAB tidak
            # disambung ke kalimat sesudahnya yang diawali huruf kecil.
            _bab = bool(re.match(
                r'^(?:\d{1,3}\s+)?(?:\d+[.)]\s*)?BAB\s+[IVX0-9]+\b',
                blok[-1]['text'], re.I)) if blok and not kosong else False
            _lanjut_kalimat = bool(b[:1].islower() or re.match(
                r'^(bab|bagian)\s+ini\b', b, re.I)) if b else False
            if (blok and not kosong and not blok[-1]['kosong']
                    and len(blok[-1]['text']) <= 60 and len(b) <= 60
                    and b[:1].islower() and not (_bab and _lanjut_kalimat)):
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


def _muat_asli(nama, jalur):
    """Muat modul ASLI (satpam/konversi) dengan nama berbeda — modulnya
    hanya impor stdlib di tingkat atas, jadi aman dimuat meski `app.*`
    di-stub untuk peta3_jev."""
    spec = importlib.util.spec_from_file_location(nama, str(jalur))
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

    # ── 2b. TANYA-ULANG BERGELOMBANG (v5) ────────────────────────────────
    #    130 kandidat ragu (> cap 120): v4 hanya menanya 120 pertama,
    #    v5 menanya semua dalam 2 gelombang (120 + 10).
    FakeKonversi.mode = 'normal'
    FAKE_SATPAM.panggilan.clear()
    FAKE_SATPAM.rendah = {'RAGU'}
    banyak = '\n'.join(
        'Paragraf isi RAGU nomor %03d tentang pemasaran digital dan kinerja bisnis usaha kecil di Indonesia.'
        % n for n in range(130))
    peta_b = P.petakan_dari_teks(banyak, putaran=1)
    cek('tanya-ulang bergelombang: 130 ragu ditanya semua',
        peta_b.get('tanya_ulang_jml') == 130, f"dapat {peta_b.get('tanya_ulang_jml')}")
    cek('tanya-ulang bergelombang: 2 gelombang (120 + 10)',
        peta_b.get('tanya_ulang_gelombang') == 2, f"dapat {peta_b.get('tanya_ulang_gelombang')}")
    cek('tanya-ulang bergelombang: sesudah tanya ulang p membaik',
        all((peta_b['p'].get(i) or 0) >= 0.5 for i in peta_b['label']))
    # cap gelombang via env: maks 1 gelombang -> hanya 120 yang ditanya
    os.environ['EDUAI_JEV_TANYA_ULANG_MAKS_GELOMBANG'] = '1'
    P._CACHE_PETA.clear()
    FAKE_SATPAM.panggilan.clear()
    peta_c = P.petakan_dari_teks(banyak, putaran=1)
    cek('tanya-ulang bergelombang: env maks 1 gelombang -> 120 saja',
        peta_c.get('tanya_ulang_jml') == 120
        and peta_c.get('tanya_ulang_gelombang') == 1,
        f"dapat {peta_c.get('tanya_ulang_jml')}/{peta_c.get('tanya_ulang_gelombang')}")
    os.environ.pop('EDUAI_JEV_TANYA_ULANG_MAKS_GELOMBANG', None)
    FAKE_SATPAM.rendah = set()

    # ── 2c. PISAH JUDUL MENEMPEL (v5) ────────────────────────────────────
    FakeKonversi.mode = 'normal'
    menempel = ('58 BAB III METODOLOGI PENELITIAN 3.1 Jenis Penelitian '
                '3.2 Metode Penelitian')
    d = P._susun_dari_bersih(menempel)
    cek('pisah judul: satu baris jadi 3 baris',
        d.get('pisah_judul_jml') == 2, f"dapat {d.get('pisah_judul_jml')}")
    cek('pisah judul: BAB III dikenali sebagai bab satu baris',
        any(v[0].upper().startswith('BAB III') for v in d.get('gabung', {}).values()))
    cek('pisah judul: 3.1/3.2 diputuskan kode (bukan Jev)',
        d.get('kode_label', {}).get(
            next(i for i, b in enumerate(d['baris']) if b.strip() == '3.1 Jenis Penelitian')) == 'subbab'
        and d.get('kode_label', {}).get(
            next(i for i, b in enumerate(d['baris']) if b.strip() == '3.2 Metode Penelitian')) == 'subbab')
    kalimat_bab = 'Seperti dijelaskan pada BAB II dan 2.1 Tinjauan Pustaka sebelumnya.'
    cek('pisah judul: kalimat biasa menyebut BAB tidak terpisah',
        P._pisah_judul_menempel(kalimat_bab) == [kalimat_bab])
    cek('pisah judul: "3.1 kali lipat" di kalimat tidak terpisah',
        P._pisah_judul_menempel(
            'Hasil penelitian menunjukkan 3.1 kali lipat dari sebelumnya.') == [
                'Hasil penelitian menunjukkan 3.1 kali lipat dari sebelumnya.'])
    satu_bab = P._susun_dari_bersih('BAB II TINJAUAN PUSTAKA\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.')
    cek('bab satu baris: "BAB II TINJAUAN PUSTAKA" masuk gabung',
        any(v[1] == 'TINJAUAN PUSTAKA' for v in satu_bab.get('gabung', {}).values()))
    bukan_bab = P._susun_dari_bersih('BAB III membahas metode penelitian ini.\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.')
    cek('bab satu baris: kalimat "BAB III membahas..." BUKAN gabung',
        not any(v[0].upper().startswith('BAB III') for v in bukan_bab.get('gabung', {}).values()))

    # ── 2d. TEKS PECAH PER HURUF (v5) ────────────────────────────────────
    from app.sambung_kode import perbaiki_spasi_huruf as _psh
    _baru, _j = _psh('D i n a m i k a P a s a r')
    cek('spasi huruf: "D i n a m i k a P a s a r" -> "Dinamika Pasar"',
        _baru == 'Dinamika Pasar', f'dapat {_baru!r}')
    _baru, _j = _psh('B A B I P E N D A H U L U A N')
    cek('spasi huruf: "B A B I ..." -> "BAB I PENDAHULUAN"',
        _baru == 'BAB I PENDAHULUAN', f'dapat {_baru!r}')
    _baru, _j = _psh('58 B A B I I I M E T O D O L O G I P E N E L I T I A N')
    cek('spasi huruf: "B A B I I I ..." -> "58 BAB III METODOLOGI PENELITIAN"',
        _baru == '58 BAB III METODOLOGI PENELITIAN', f'dapat {_baru!r}')
    _baru, _j = _psh('S P S S dan A B C D tetap utuh')
    cek('spasi huruf: "S P S S" digabung, "A B C D" dibiarkan',
        _baru == 'SPSS dan A B C D tetap utuh', f'dapat {_baru!r}')
    _baru, _j = _psh('Hasil penelitian ini biasa saja tanpa spasi huruf.')
    cek('spasi huruf: kalimat biasa tidak berubah',
        _baru == 'Hasil penelitian ini biasa saja tanpa spasi huruf.' and _j == 0)
    _baru, _j = _psh('1.1 L a t a r B e l a k a n g')
    cek('spasi huruf: "1.1 L a t a r ..." -> "1.1 Latar Belakang"',
        _baru == '1.1 Latar Belakang', f'dapat {_baru!r}')
    d = P._susun_dari_bersih('B A B I I I M E T O D O L O G I P E N E L I T I A N 3.1 J e n i s P e n e l i t i a n')
    cek('spasi huruf + pisah judul: satu baris pecah jadi BAB III + 3.1',
        d.get('spasi_huruf_jml', 0) >= 1 and d.get('pisah_judul_jml', 0) >= 1
        and any(v[0].upper().startswith('BAB III') for v in d.get('gabung', {}).values()),
        f"spasi={d.get('spasi_huruf_jml')} pisah={d.get('pisah_judul_jml')}")

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

    # ── 6. SELARAS DOKUMEN RESMI TYPESAFE (v5.4) ─────────────────────────
    #    Sumber: https://docs.typesafe.ai/primitives (+ /choice, /noul,
    #    /confidence, /cookbooks/autoformat) — dibaca 10 Nov 2026.
    S = _muat_asli('app.satpam_asli', ROOT / 'app' / 'satpam.py')
    cek('dokumen: noul TANPA criteria sah',
        S._periksa_skema({'q': {'type': 'noul', 'instructions': 'x'}}) == [])
    cek('dokumen: noul + criteria OBJEK {true,false} sah (dulu ditolak)',
        S._periksa_skema({'q': {'type': 'noul', 'instructions': 'x',
                                'criteria': {'true': 'ya, sambung',
                                             'false': 'tidak, putus'}}}) == [])
    cek('dokumen: noul + criteria STRING tetap ditolak (akar 503 semu 07 Okt)',
        len(S._periksa_skema({'q': {'type': 'noul', 'instructions': 'x',
                                   'criteria': 'Ya bila sambung'}})) == 1)
    cek('dokumen: noul + criteria LIST ditolak',
        len(S._periksa_skema({'q': {'type': 'noul', 'instructions': 'x',
                                   'criteria': ['ya', 'tidak']}})) == 1)
    cek('dokumen: noul + criteria OBJEK tanpa true/false ditolak',
        len(S._periksa_skema({'q': {'type': 'noul', 'instructions': 'x',
                                   'criteria': {'ya': 'sambung'}}})) == 1)
    cek('dokumen: choice TANPA criteria tetap ditolak',
        len(S._periksa_skema({'q': {'type': 'choice',
                                   'instructions': 'x'}})) == 1)
    cek('dokumen: choice + criteria OBJEK sah',
        S._periksa_skema({'q': {'type': 'choice', 'instructions': 'x',
                                'criteria': {'a': 'opsi A'}}}) == [])

    K = _muat_asli('app.konversi_asli', ROOT / 'app' / 'konversi.py')
    _tq = K._tanya_sambung(5, 'Latar belakang penelitian ini',
                          'membahas pemasaran digital.')
    cek('dokumen: pertanyaan stitch mengutip KEDUA baris (bukan hanya ID)',
        _tq['type'] == 'noul'
        and 'Latar belakang penelitian ini' in _tq['instructions']
        and 'membahas pemasaran digital.' in _tq['instructions'])
    H._TANYA_FN = lambda bahan, tanya: {k: {'noul': 0.6} for k in tanya}
    lap = H.periksa_peta(kalimat)
    cek('dokumen: Hakim noul 0,6 (pita tengah 0,3-0,7) -> ragu, bukan sepakat',
        lap['jumlah_ragu'] == 1 and lap['bagian'][1]['status'] == 'ragu')
    H._TANYA_FN = lambda bahan, tanya: {k: {'noul': 0.9} for k in tanya}
    lap = H.periksa_peta(kalimat)
    cek('dokumen: Hakim noul 0,9 (>= 0,7) tetap sepakat',
        lap['jumlah_sepakat'] == 2)
    H._TANYA_FN = None
    cek('dokumen: criteria bab/subbab bentuk OBJEK what/not_for',
        isinstance(P.KRITERIA.get('bab'), dict)
        and set(P.KRITERIA['bab']) >= {'what', 'not_for'}
        and isinstance(P.KRITERIA.get('subbab'), dict)
        and set(P.KRITERIA['subbab']) >= {'what', 'not_for'})
    cek('dokumen: criteria tetap 4 opsi, paragraf/biasa satu baris',
        set(P.KRITERIA) == {'bab', 'subbab', 'paragraf', 'biasa'}
        and isinstance(P.KRITERIA['paragraf'], str)
        and isinstance(P.KRITERIA['biasa'], str))

    # ── 7. v6.1: SEGMENTASI SESUDAH STITCH ───────────────────────────────
    #    Teks pecah per huruf hidup satu huruf per BARIS — pra-stitch tidak
    #    bisa cocok lintas baris; stitch menyambungnya jadi "D i n a m i k a".
    teks_huruf = (
        'BAB I\nPENDAHULUAN\n'
        'D\ni\nn\na\nm\ni\nk\na\n\n'
        'M\ne\nm\nb\na\nh\na\ns\n\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    FakeKonversi.mode = 'normal'
    d_huruf = P._susun_dari_bersih(teks_huruf)
    cek('v6.1: huruf per baris jadi kata utuh sesudah stitch ("Dinamika")',
        any('Dinamika' in b for b in d_huruf['baris']))
    cek('v6.1: kata kamus baru ikut diperbaiki ("Membahas")',
        any('Membahas' in b for b in d_huruf['baris']))
    cek('v6.1: baris berspasi sebelum perbaikan = 2',
        d_huruf.get('huruf_berspasi_sebelum') == 2,
        str(d_huruf.get('huruf_berspasi_sebelum')))
    cek('v6.1: baris berspasi sesudah perbaikan = 0',
        d_huruf.get('huruf_berspasi_sesudah') == 0,
        str(d_huruf.get('huruf_berspasi_sesudah')))
    cek('v6.1: jumlah rangkaian diperbaiki sesudah stitch = 2',
        d_huruf.get('spasi_huruf_sesudah_stitch') == 2,
        str(d_huruf.get('spasi_huruf_sesudah_stitch')))
    teks_asing = (
        'BAB I\nPENDAHULUAN\n'
        'Q\nw\ne\nr\nt\ny\n\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    d_asing = P._susun_dari_bersih(teks_asing)
    cek('v6.1: rangkaian tak dikenal dibiarkan berspasi (tidak dikarang)',
        any('Q w e r t y' in b for b in d_asing['baris']))
    cek('v6.1: rangkaian tak dikenal tidak dihitung diperbaiki',
        d_asing.get('spasi_huruf_sesudah_stitch') == 0,
        str(d_asing.get('spasi_huruf_sesudah_stitch')))

    # ── 8. v6.2: PISAH "BAB + JUDUL + KOMA + KALIMAT" ────────────────────
    cek('v6.2: "3. BAB III ..., bagian ini ..." dipisah jadi judul + ekor',
        P._pisah_bab_ekor(
            '3. BAB III METODOLOGI PENELITIAN, bagian ini menjelaskan tentang')
        == ['3. BAB III METODOLOGI PENELITIAN',
            'bagian ini menjelaskan tentang'])
    cek('v6.2: "5. BAB V PENUTUP, pada bab ini ..." dipisah',
        P._pisah_bab_ekor(
            '5. BAB V PENUTUP, pada bab ini penulis akan menjelaskan mengenai')
        == ['5. BAB V PENUTUP',
            'pada bab ini penulis akan menjelaskan mengenai'])
    cek('v6.2: judul yang ekornya huruf BESAR tidak dipisah',
        P._pisah_bab_ekor(
            'BAB II TINJAUAN PUSTAKA, KERANGKA PEMIKIRAN DAN HIPOTESIS')
        == ['BAB II TINJAUAN PUSTAKA, KERANGKA PEMIKIRAN DAN HIPOTESIS'])
    cek('v6.2: judul tanpa koma tidak disentuh',
        P._pisah_bab_ekor('BAB I PENDAHULUAN') == ['BAB I PENDAHULUAN'])
    cek('v6.2: BAB di tengah kalimat tidak dipisah',
        P._pisah_bab_ekor('Penelitian ini membahas BAB II, bagian ini menjelaskan')
        == ['Penelitian ini membahas BAB II, bagian ini menjelaskan'])
    # ujung-ke-ujung: judul + ekor terpisah di baris akhir (stitch fake
    # sempat menyambung kembali — pisah sesudah stitch yang memisahkan).
    teks_ekor = (
        'BAB I\nPENDAHULUAN\n'
        '3. BAB III METODOLOGI PENELITIAN, bagian ini menjelaskan tentang metode.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    d_ekor = P._susun_dari_bersih(teks_ekor)
    cek('v6.2: judul BAB bersih tanpa ekor di baris akhir',
        any(b.strip() == '3. BAB III METODOLOGI PENELITIAN'
            for b in d_ekor['baris']),
        str(d_ekor['baris']))
    cek('v6.2: ekor kalimat jadi baris sendiri',
        any(b.strip().startswith('bagian ini menjelaskan')
            for b in d_ekor['baris']))
    cek('v6.2: jumlah pisahan ekor tercatat',
        d_ekor.get('pisah_bab_ekor_jml', 0) >= 1,
        str(d_ekor.get('pisah_bab_ekor_jml')))
    # pagar stitch: judul BAB + ekor lintas baris-kosong tidak disambung
    # meski Jev bilang sambung (ekor ada di JOIN_SET fake).
    from app.sambung_kode import sambung_kode as _sk6
    cek('v6.2: sambung_kode tolak judul BAB + "bagian ini..."',
        _sk6('BAB III METODOLOGI PENELITIAN',
             'bagian ini menjelaskan tentang') is False)
    cek('v6.2: sambung_kode tolak judul BAB + "Bab ini..."',
        _sk6('BAB III METODOLOGI PENELITIAN',
             'Bab ini menjelaskan tentang') is False)
    cek('v6.2: sambung_kode tetap tanya lanjutan judul huruf besar',
        _sk6('BAB III Metodologi', 'Penelitian') is None)
    teks_lintas = (
        'BAB I\nPENDAHULUAN\n'
        'BAB III METODOLOGI PENELITIAN\n\n'
        'membahas pemasaran digital di Indonesia.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    hasil_lintas = P._stitch_baris(teks_lintas,
                                   tanya_fn=FAKE_SATPAM.tanya_bebas_mutu)
    cek('v6.2: stitch lintas-kosong tidak menelan judul BAB',
        'BAB III METODOLOGI PENELITIAN\n' in hasil_lintas
        and 'membahas pemasaran digital di Indonesia.' in hasil_lintas,
        hasil_lintas[:120])

    # ── 9. v6.3: STABILKAN BATAS PARAGRAF ────────────────────────────────
    #    (a) koreksi deterministik: 'paragraf' sesudah baris isi yang tidak
    #    berakhir tanda akhir kalimat = lanjutan -> 'biasa'.
    teks_batas = (
        'BAB I\nPENDAHULUAN\n'
        'Kalimat pertama yang berlanjut ke baris berikutnya dan masih panjang sekali\n'
        'ke baris berikutnya yang jadi kandidat.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    r_batas = P.petakan_dari_teks(teks_batas)
    lab_batas = {i: v for i, v in r_batas['label'].items()}
    cek('v6.3: lanjutan kalimat (baris sebelum tanpa titik) jadi biasa',
        lab_batas.get(3) == 'biasa', str(lab_batas))
    cek('v6.3: paragraf sesudah kalimat selesai tetap paragraf',
        lab_batas.get(4) == 'paragraf', str(lab_batas))
    cek('v6.3: paragraf pertama sesudah judul tetap paragraf',
        lab_batas.get(2) == 'paragraf', str(lab_batas))
    cek('v6.3: koreksi batas tercatat',
        r_batas.get('koreksi_batas_paragraf') == [3],
        str(r_batas.get('koreksi_batas_paragraf')))
    #    (b) judul sebelumnya mengecualikan koreksi.
    teks_judul = (
        'BAB I\nPENDAHULUAN\n'
        '1.1 Latar Belakang\n'
        'Isi paragraf pertama sesudah judul subbab ini.\n'
        'Isi paragraf kedua yang panjang dan tidak terbelah sama sekali.\n'
    )
    r_judul = P.petakan_dari_teks(teks_judul)
    cek('v6.3: paragraf sesudah subbab kode tidak didemosi',
        r_judul['label'].get(3) == 'paragraf'
        and r_judul.get('koreksi_batas_paragraf') == [],
        str({k: v for k, v in r_judul['label'].items() if v != 'biasa'}))
    #    (c) tanya-ulang batas goyang: suara terbelah paragraf/biasa
    #    sesudah gelombang 1 ditanya sekali lagi di gelombang 2.
    teks_pb = (
        'BAB I\nPENDAHULUAN\n'
        'Baris GOYANG-PB yang membuka paragraf baru.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    r_pb = P.petakan_dari_teks(teks_pb)
    cek('v6.3: batas goyang paragraf/biasa ditanya ulang sekali lagi',
        r_pb.get('tanya_ulang_goyang_pb_jml') == 1,
        str(r_pb.get('tanya_ulang_goyang_pb_jml')))
    cek('v6.3: tanya-ulang batas goyang memakai gelombang ke-2',
        r_pb.get('tanya_ulang_gelombang', 0) >= 2,
        str(r_pb.get('tanya_ulang_gelombang')))

    # ── 10. v6.4: DETEKSI BAB DETERMINISTIK ─────────────────────────────
    #    (a) penanda BAB dipaksa 'bab' oleh kode (fake melabel 'paragraf').
    teks_bab = (
        'BAB I\nPENDAHULUAN\n'
        '3. BAB III METODOLOGI PENELITIAN\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    r_bab = P.petakan_dari_teks(teks_bab)
    cek('v6.4: "3. BAB III ..." dipaksa bab oleh kode',
        r_bab['label'].get(2) == 'bab', str(r_bab['label']))
    cek('v6.4: bab dari kode tercatat + asal kode',
        r_bab.get('bab_kode') == [2] and r_bab.get('asal', {}).get(2) == 'kode',
        str((r_bab.get('bab_kode'), r_bab.get('asal'))))
    #    (b) nomor BAB yang sama 2x -> yang ke-2 jadi biasa.
    teks_ganda = (
        'BAB I\nPENDAHULUAN\n'
        '3. BAB III METODOLOGI PENELITIAN\n'
        '4. BAB III METODOLOGI PENELITIAN\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    r_ganda = P.petakan_dari_teks(teks_ganda)
    cek('v6.4: BAB ganda (nomor sama) -> kemunculan ke-2 jadi biasa',
        r_ganda['label'].get(2) == 'bab'
        and r_ganda['label'].get(3) == 'biasa'
        and r_ganda.get('bab_ganda') == [3],
        str((r_ganda['label'], r_ganda.get('bab_ganda'))))
    #    (c) "BAB 1" = "BAB I" (normalisasi angka).
    cek('v6.4: angka BAB dinormalisasi (BAB 1 = BAB I)',
        P._angka_bab('1') == 1 and P._angka_bab('I') == 1
        and P._angka_bab('III') == 3 and P._angka_bab('V') == 5)
    #    (d) label 'bab' Jev tanpa penanda didemosi.
    teks_demosi = (
        'BAB I\nPENDAHULUAN\n'
        'Kalimat JEV-BAB penutup yang panjang dan berakhir titik.\n'
        'Baris JEV-BAB tanpa titik akhir\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    r_demosi = P.petakan_dari_teks(teks_demosi)
    cek('v6.4: bab Jev tanpa penanda + titik akhir -> paragraf',
        r_demosi['label'].get(2) == 'paragraf', str(r_demosi['label']))
    cek('v6.4: bab Jev tanpa penanda + tanpa titik -> biasa',
        r_demosi['label'].get(3) == 'biasa', str(r_demosi['label']))
    cek('v6.4: demosi bab tercatat',
        r_demosi.get('bab_demosi') == [2, 3],
        str(r_demosi.get('bab_demosi')))
    #    (e) pengecualian: judul BAB tepat sesudah penanda BAB polos
    #    yang judulnya kosong tetap 'bab'.
    teks_judul_bab = (
        'BAB I\n'
        'Pendahuluan JEV-BAB\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
        'Isi paragraf kedua yang panjang dan tidak terbelah sama sekali.\n'
    )
    r_jb = P.petakan_dari_teks(teks_judul_bab)
    cek('v6.4: judul BAB sesudah penanda polos tetap bab',
        r_jb['label'].get(1) == 'bab', str(r_jb['label']))

    # ── 11. v6.5: PROFIL KAMPUS — ISTILAH + PENOMORAN ───────────────────
    cek('v6.5: istilah bawaan kuesioner = kuesioner + angket',
        PK.istilah().get('kuesioner') == ['kuesioner', 'angket'],
        str(PK.istilah()))
    cek('v6.5: penomoran bawaan judul_titik_akhir = False',
        PK.penomoran().get('judul_titik_akhir') is False,
        str(PK.penomoran()))
    cek('v6.5: Aturan 3 buang judul ANGKET (bawaan)',
        P.dibuang('ANGKET PENELITIAN') is True)
    cek('v6.5: Aturan 3 buang judul KUESIONER (bawaan)',
        P.dibuang('KUESIONER PENELITIAN') is True)
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump({'istilah': {'kuesioner': ['kuesioner', 'angket',
                                             'daftar pertanyaan']},
                   'penomoran': {'judul_titik_akhir': True},
                   'kampus': {'KampusX': {'penomoran': {'judul_titik_akhir': False}}}},
                  f)
        jalur = f.name
    os.environ['EDUAI_PROFIL_KAMPUS'] = jalur
    PK._cache.update({'jalur': None, 'mtime': None, 'isi': None})
    cek('v6.5: istilah kuesioner dari config (tanpa hardcode)',
        PK.istilah().get('kuesioner')
        == ['kuesioner', 'angket', 'daftar pertanyaan'],
        str(PK.istilah()))
    cek('v6.5: Aturan 3 buang sebutan config "daftar pertanyaan"',
        P.dibuang('DAFTAR PERTANYAAN PENELITIAN') is True)
    cek('v6.5: penomoran judul_titik_akhir dari config = True',
        PK.penomoran().get('judul_titik_akhir') is True)
    cek('v6.5: penomoran per kampus boleh mematikan lagi (False)',
        PK.penomoran('KampusX').get('judul_titik_akhir') is False)
    cek('v6.5: nomor bertitik "1.1. Latar Belakang" dibaca kode',
        P._nomor_bertindak_judul('1.1. Latar Belakang') is True)
    cek('v6.5: judul bertitik akhir dibaca kode bila config True',
        P._nomor_bertindak_judul('1.1. Latar Belakang.') is True)
    os.environ.pop('EDUAI_PROFIL_KAMPUS', None)
    PK._cache.update({'jalur': None, 'mtime': None, 'isi': None})
    cek('v6.5: sebutan config tidak berlaku sesudah config dilepas',
        P.dibuang('DAFTAR PERTANYAAN PENELITIAN') is False)
    cek('v6.5: judul bertitik akhir ditolak bila config bawaan (False)',
        P._nomor_bertindak_judul('1.1. Latar Belakang.') is False)
    cek('v6.5: nomor bertitik tetap dibaca kode dengan config bawaan',
        P._nomor_bertindak_judul('1.1. Latar Belakang') is True)
    cek('v6.5: huruf awal kecil terkupas dari nomor bertitik',
        P._huruf_awal_kecil('1.1. latar belakang') is True
        and P._huruf_awal_kecil('1.1. Latar Belakang') is False)

    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
        sys.exit(1)


if __name__ == '__main__':
    main()
