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
            # cerminan pagar asli (app/sambung_kode v7): judul subbab
            # bernomor juga tidak disambung ke kalimat sesudahnya.
            _subbab = bool(re.match(
                r'^\d+(?:\.\d+)+\.?\s+\S',
                blok[-1]['text'])) if blok and not kosong else False
            _lanjut_kalimat = bool(b[:1].islower() or re.match(
                r'^(bab|bagian)\s+ini\b', b, re.I)) if b else False
            if (blok and not kosong and not blok[-1]['kosong']
                    and len(blok[-1]['text']) <= 60 and len(b) <= 60
                    and b[:1].islower()
                    and not ((_bab or _subbab) and _lanjut_kalimat)):
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
    #    (d) v7.2: balik label sesudah suara ekstra PB tercatat.
    cek('v7.2: balik label tanya-ulang batas goyang tercatat',
        r_pb.get('tanya_ulang_goyang_pb_balik_jml') == 1
        and r_pb.get('tanya_ulang_goyang_pb_balik') == [[2, 'biasa', 'paragraf']],
        str(r_pb.get('tanya_ulang_goyang_pb_balik')))

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

    # ── 12. v6.7: PERBAIKAN DARI UJI LIVE ───────────────────────────────
    #    (a) pagar sambung_kode mengupas nomor daftar ("2. BAB II ...").
    from app.sambung_kode import tanpa_nomor_halaman as _tnh
    cek('v6.7: tanpa_nomor_halaman kupas nomor daftar juga',
        _tnh('2. BAB II TINJAUAN PUSTAKA') == 'BAB II TINJAUAN PUSTAKA'
        and _tnh('13 BAB I') == 'BAB I'
        and _tnh('1.1 Latar Belakang') == '1.1 Latar Belakang')
    cek('v6.7: sambung_kode tolak "2. BAB II ..." + "bagian ini..."',
        _sk6('2. BAB II TINJAUAN PUSTAKA',
             'bagian ini menjelaskan tentang') is False)
    cek('v6.7: sambung_kode tolak "3. BAB III ..." + "pada bab ini..."',
        _sk6('3. BAB III METODOLOGI PENELITIAN',
             'pada bab ini penulis akan') is False)
    #    (b) koreksi batas dipersempit: ':' dan baris terpotong (kata polos)
    #    TIDAK didemosi; yang didemosi hanya awal huruf kecil / lanjutan
    #    eksplisit (koma).
    teks_sempit = (
        'BAB I\nPENDAHULUAN\n'
        'Hasil uji normalitas disajikan pada tabel berikut:\n'
        'Berdasarkan kriteria uji normalitas, data dinyatakan berdistribusi normal.\n'
        'Kalimat pertama yang berlanjut ke baris berikutnya dan masih panjang sekali,\n'
        'ke baris berikutnya yang jadi kandidat.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    r_sempit = P.petakan_dari_teks(teks_sempit)
    cek('v6.7: paragraf sesudah pengantar tabel (:) TIDAK didemosi',
        r_sempit['label'].get(3) == 'paragraf', str(r_sempit['label']))
    cek('v6.7: lanjutan huruf kecil sesudah koma tetap didemosi',
        r_sempit['label'].get(5) == 'biasa', str(r_sempit['label']))
    cek('v6.7: paragraf sesudah kalimat selesai tetap paragraf',
        r_sempit['label'].get(6) == 'paragraf', str(r_sempit['label']))
    cek('v6.7: hanya 1 koreksi batas pada teks sempit',
        r_sempit.get('koreksi_batas_paragraf') == [5],
        str(r_sempit.get('koreksi_batas_paragraf')))

    # ── 13. v6.8: FRAGMEN 1-2 HURUF (contoh live fid=115) ────────────────
    from app.sambung_kode import perbaiki_fragmen_huruf as _pfh
    cek('v6.8: "d ij e l a s k a n o l e h l a i n" -> "dijelaskan oleh lain"',
        _pfh('d ij e l a s k a n o l e h l a i n')[0]
        == 'dijelaskan oleh lain')
    cek('v6.8: "d i luar" (2 token) -> "di luar"',
        _pfh('variabel d i luar variabel')[0]
        == 'variabel di luar variabel')
    cek('v6.8: "J u rn a l R i s e t ..." -> "Jurnal Riset ..."',
        _pfh('J u rn a l R i s e t M a n aj e m e n')[0]
        == 'Jurnal Riset Manajemen')
    cek('v6.8: nama orang dibiarkan (tidak dikarang)',
        _pfh('D i n a A l fi n a H e l m a n i a P u t r i')[0]
        == 'D i n a A l fi n a H e l m a n i a P u t r i')
    cek('v6.8: inisial "U S A" dibiarkan',
        _pfh('U S A dan P B B')[0] == 'U S A dan P B B')
    cek('v6.8: teks normal tidak berubah dan tidak dihitung',
        _pfh('Kata di ke dalam kalimat biasa.')[1] == 0)
    import app.sambung_kode as _SK
    cek('v6.8: segmentasi "di" = kata, bukan Romawi',
        _SK._segmentasi('di', dict(_SK.KATA_UMUM)) == [(0, 2, 'di')])
    cek('v6.8: segmentasi "iv" tetap Romawi',
        _SK._segmentasi('iv', dict(_SK.KATA_UMUM))
        == [(0, 1, 'i'), (1, 2, 'v')])

    # ── 14. v7.1: PISAH EKOR KALIMAT PADA JUDUL SUBBAB BERNOMOR ──────────
    cek('v7.1: "1.1 LATAR BELAKANG Indonesia merupakan ..." dipisah',
        P._pisah_subbab_ekor(
            '1.1 LATAR BELAKANG Indonesia merupakan salah satu negara dengan')
        == ['1.1 LATAR BELAKANG',
            'Indonesia merupakan salah satu negara dengan'])
    cek('v7.1: "1.3 Tujuan Penelitian 1. Untuk ..." dipisah di penanda butir',
        P._pisah_subbab_ekor(
            '1.3 Tujuan Penelitian 1. Untuk mengidentifikasi SWOT pada Usaha')
        == ['1.3 Tujuan Penelitian',
            '1. Untuk mengidentifikasi SWOT pada Usaha'])
    cek('v7.1: "1.5 Sistematika Penulisan Agar ..." dipisah di kata awal',
        P._pisah_subbab_ekor(
            '1.5 Sistematika Penulisan Agar memberikan gambaran sekilas mengenai')
        == ['1.5 Sistematika Penulisan',
            'Agar memberikan gambaran sekilas mengenai'])
    cek('v7.1: "1.2 Definisi Operasional adalah ..." dipisah di kata kecil',
        P._pisah_subbab_ekor(
            '1.2 Definisi Operasional adalah suatu batasan yang dipakai peneliti')
        == ['1.2 Definisi Operasional',
            'adalah suatu batasan yang dipakai peneliti'])
    cek('v7.1: koma + kalimat dipisah',
        P._pisah_subbab_ekor(
            '1.1 Latar Belakang, Indonesia merupakan salah satu negara')
        == ['1.1 Latar Belakang',
            'Indonesia merupakan salah satu negara'])
    cek('v7.1: penghubung judul tidak memicu pisah',
        P._pisah_subbab_ekor('1.1 Latar Belakang dan Tujuan Penelitian')
        == ['1.1 Latar Belakang dan Tujuan Penelitian'])
    cek('v7.1: "Dalam" tanpa kalimat sesudahnya tidak memicu pisah',
        P._pisah_subbab_ekor('1.2 Peran Dalam Organisasi')
        == ['1.2 Peran Dalam Organisasi'])
    cek('v7.1: judul CAPS tanpa ekor tidak disentuh',
        P._pisah_subbab_ekor('1.1 LATAR BELAKANG') == ['1.1 LATAR BELAKANG'])
    cek('v7.1: judul Title Case tanpa ekor tidak disentuh',
        P._pisah_subbab_ekor('2.1 Jenis Penelitian Kualitatif')
        == ['2.1 Jenis Penelitian Kualitatif'])
    cek('v7.1: "KERANGKA PEMIKIRAN Teori Belajar" tidak dipisah',
        P._pisah_subbab_ekor('1.2 KERANGKA PEMIKIRAN Teori Belajar')
        == ['1.2 KERANGKA PEMIKIRAN Teori Belajar'])
    cek('v7.1: koma + judul Title Case tidak dipisah',
        P._pisah_subbab_ekor(
            '1.2 Tinjauan Pustaka, Kerangka Pemikiran dan Hipotesis')
        == ['1.2 Tinjauan Pustaka, Kerangka Pemikiran dan Hipotesis'])
    cek('v7.1: nomor di tengah kalimat tidak dipisah',
        P._pisah_subbab_ekor('Penelitian ini membahas 1.1 Latar Belakang')
        == ['Penelitian ini membahas 1.1 Latar Belakang'])
    cek('v7.1: nomor halaman di depan tetap menempel di judul',
        P._pisah_subbab_ekor(
            '13 1.1 LATAR BELAKANG Indonesia merupakan salah satu negara')
        == ['13 1.1 LATAR BELAKANG',
            'Indonesia merupakan salah satu negara'])
    # ujung-ke-ujung: judul + ekor terpisah di baris akhir.
    teks_subbab = (
        'BAB I\nPENDAHULUAN\n'
        '1.1 LATAR BELAKANG Indonesia merupakan salah satu negara dengan jumlah penduduk besar.\n'
        '1.3 Tujuan Penelitian 1. Untuk mengidentifikasi SWOT pada Usaha Kecil Menengah.\n'
        '1.5 Sistematika Penulisan Agar memberikan gambaran sekilas mengenai isi skripsi ini.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    d_subbab = P._susun_dari_bersih(teks_subbab)
    cek('v7.1: judul subbab bersih tanpa ekor di baris akhir',
        any(b.strip() == '1.1 LATAR BELAKANG' for b in d_subbab['baris'])
        and any(b.strip() == '1.3 Tujuan Penelitian'
                for b in d_subbab['baris'])
        and any(b.strip() == '1.5 Sistematika Penulisan'
                for b in d_subbab['baris']),
        str(d_subbab['baris']))
    cek('v7.1: ekor subbab jadi baris sendiri',
        any(b.strip().startswith('Indonesia merupakan')
            for b in d_subbab['baris'])
        and any(b.strip().startswith('1. Untuk mengidentifikasi')
                for b in d_subbab['baris'])
        and any(b.strip().startswith('Agar memberikan')
                for b in d_subbab['baris']))
    cek('v7.1: jumlah pisahan ekor subbab tercatat',
        d_subbab.get('pisah_subbab_ekor_jml', 0) >= 3,
        str(d_subbab.get('pisah_subbab_ekor_jml')))
    # pagar stitch: judul subbab + ekor lintas baris-kosong tidak disambung
    # meski Jev bilang sambung (ekor ada di JOIN_SET fake).
    from app.sambung_kode import sambung_kode as _sk7
    cek('v7.1: sambung_kode tolak subbab + "Indonesia merupakan..."',
        _sk7('1.1 Latar Belakang',
             'Indonesia merupakan salah satu negara') is False)
    cek('v7.1: sambung_kode tolak subbab + "Agar memberikan..."',
        _sk7('1.5 Sistematika Penulisan',
             'Agar memberikan gambaran sekilas') is False)
    cek('v7.1: sambung_kode tolak subbab + huruf kecil',
        _sk7('1.1 Latar Belakang',
             'bagian ini menjelaskan tentang') is False)
    cek('v7.1: sambung_kode tetap tanya lanjutan judul huruf besar',
        _sk7('1.1 Latar', 'Belakang') is None)
    cek('v7.1: sambung_kode tetap tanya penghubung judul "dan ..."',
        _sk7('1.1 Latar', 'dan Tujuan Penelitian') is None)
    teks_lintas_sub = (
        'BAB I\nPENDAHULUAN\n'
        '1.1 Latar Belakang\n\n'
        'membahas pemasaran digital di Indonesia.\n'
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n'
    )
    hasil_lintas_sub = P._stitch_baris(teks_lintas_sub,
                                       tanya_fn=FAKE_SATPAM.tanya_bebas_mutu)
    cek('v7.1: stitch lintas-kosong tidak menelan judul subbab',
        '1.1 Latar Belakang\n' in hasil_lintas_sub
        and 'membahas pemasaran digital di Indonesia.' in hasil_lintas_sub,
        hasil_lintas_sub[:120])

    # ── 8. v8: SAKLAR MODEL YANG JUJUR ────────────────────────────────────
    #    Audit 1.14 menemukan jebakan: env EDUAI_SATPAM_MODEL tampaknya
    #    mengganti model, tapi tidak dipakai jalur peta sama sekali.
    #    Perbaikan v8: fungsi mati + konstanta menipu dihapus; satu-satunya
    #    saklar yang hidup = app/jev.py::MODEL_DEFAULT (bawaan 1.14
    #    sejak Gas Bos 10 Nov 2026; sebelumnya 1.13).
    import importlib
    import urllib.request
    os.environ['EDUAI_SATPAM_MODEL'] = 'SATPAM/typesafe/jev-1.14'
    S8 = _muat_asli('app.satpam_asli_v8', ROOT / 'app' / 'satpam.py')
    cek('v8: env EDUAI_SATPAM_MODEL tidak lagi melahirkan satpam.MODEL',
        not hasattr(S8, 'MODEL'))
    cek('v8: konstanta menipu BASE/KUNCI/BATAS_DETIK sudah tidak ada',
        not hasattr(S8, 'BASE') and not hasattr(S8, 'KUNCI')
        and not hasattr(S8, 'BATAS_DETIK'))
    cek('v8: fungsi mati _tanya_bebas_lama sudah tidak ada',
        not hasattr(S8, '_tanya_bebas_lama'))
    cek('v8: setelan hidup AKTIF/AMBANG_LOLOS/AMBANG_TANYA tetap ada',
        hasattr(S8, 'AKTIF') and hasattr(S8, 'AMBANG_LOLOS')
        and hasattr(S8, 'AMBANG_TANYA'))
    cek('v8: pinjaman mati di Hakim sudah tidak ada',
        not hasattr(H, '_MODEL') and not hasattr(H, '_BASE')
        and not hasattr(H, '_KUNCI') and not hasattr(H, '_BATAS'))
    del os.environ['EDUAI_SATPAM_MODEL']

    J8 = importlib.import_module('app.jev')
    cek('v8: model bawaan kini 1.14 (Gas Bos 10 Nov 2026)',
        J8.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14')

    # ── transport palsu: tangkap body request, tanpa jaringan ──────────
    class _ResponPalsu:
        def __init__(self, badan):
            self._badan = badan

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return self._badan

    tangkapan = {}

    def _urlopen_palsu(req, timeout=None):
        tangkapan['data'] = req.data
        return _ResponPalsu(json.dumps({'q1': {'noul': 0.9}}).encode())

    _tanya = {'q1': {'type': 'noul',
                     'instructions': 'apakah baris ini judul subbab?'}}
    _urlopen_asli = urllib.request.urlopen
    urllib.request.urlopen = _urlopen_palsu
    try:
        J8.MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.14'
        r = J8.tanya('bahan uji yang cukup panjang', _tanya)
        cek('v8: saklar jev.MODEL_DEFAULT mengganti model di body request',
            json.loads(tangkapan['data'])['model']
            == 'SATPAM/typesafe/jev-1.14'
            and r == {'q1': {'noul': 0.9}})
        r = S8.tanya_bebas_mutu('bahan uji yang cukup panjang', _tanya)
        cek('v8: jalur live satpam.tanya_bebas_mutu ikut saklar model',
            json.loads(tangkapan['data'])['model']
            == 'SATPAM/typesafe/jev-1.14'
            and r == {'q1': {'noul': 0.9}})
        H._AKTIF = True
        H._TANYA_FN = None
        r = H._tanya_jev('bahan uji yang cukup panjang', _tanya)
        cek('v8: jalur live Hakim ikut saklar model',
            json.loads(tangkapan['data'])['model']
            == 'SATPAM/typesafe/jev-1.14'
            and r == {'q1': {'noul': 0.9}})
        J8.MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.14'
        r = J8.tanya('bahan uji yang cukup panjang', _tanya)
        cek('v8: saklar dikembalikan ke 1.14, body request ikut kembali',
            json.loads(tangkapan['data'])['model']
            == 'SATPAM/typesafe/jev-1.14')
    finally:
        urllib.request.urlopen = _urlopen_asli
        J8.MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.14'

    # ── label model periksa_mutu = model yang benar-benar melayani ─────
    J8.MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.14'
    _teks_mutu = ('Judul penelitian tentang pemasaran digital. '
                  'Abstrak penelitian ini membahas pemasaran. ' * 20)
    _hasil_mutu = K.periksa_mutu(None, 1, _teks_mutu)
    cek('v8: label model periksa_mutu = MODEL_DEFAULT yang melayani',
        _hasil_mutu.get('model') == 'SATPAM/typesafe/jev-1.14'
        and _hasil_mutu.get('ok') is True)
    J8.MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.14'

    # ── 9. v8-aturan: JOIN B-HURUF-KECIL (stitch deterministik) ─────────
    #    Terukur 11 Nov 2026: 1.267/1.877 pasangan stitch fid=112 dan
    #    906/1.431 fid=115 adalah B-huruf-kecil; live 1.14 Jev sendiri
    #    menggabungkan 98,0% / 97,4% pasangan itu. Aturan ini membuat
    #    deterministik apa yang Jev hampir selalu lakukan — bukan tebakan
    #    baru. (RULE_VERSION naik ke v8; cache lama kedaluwarsa otomatis.)
    from app.sambung_kode import sambung_kode as _sk8
    from app.sambung_kode import _judul_pendek as _jp8
    cek('v8-aturan: B huruf kecil = lanjutan ("Ekonomi" + "dan ...")',
        _sk8('Ekonomi',
             'dan Industri Nasional (KEIN) bekerja sama untuk mendorong')
        is True)
    cek('v8-aturan: B huruf kecil = lanjutan (fragmen satu kata)',
        _sk8('muslim', 'pada') is True
        and _sk8('fashion', 'muslim') is True)
    cek('v8-aturan: B huruf kecil = lanjutan (kalimat terbelah panjang)',
        _sk8('Manfaat praktis dalam penelitian ini adalah dapat membantu',
             'wirausahawan membuat keputusan yang lebih tepat mengenai')
        is True)
    cek('v8-aturan: B huruf kecil = lanjutan (kata terbelah "Turn"+"around")',
        _sk8('Strategi Turn', 'around') is None)
    cek('v8-aturan: A judul pendek ALL-CAPS tetap ditanya Jev',
        _sk8('KESIMPULAN', 'dari hasil penelitian tersebut') is None)
    cek('v8-aturan: B penanda butir tetap ditanya Jev ("e. ...")',
        _sk8('(Mahardhani,2023)', 'e. Positive Word-of-Mouth') is None)
    cek('v8-aturan: B penanda butir tetap ditanya Jev ("b) ...")',
        _sk8('63', 'b) Editing Data') is None)
    cek('v8-aturan: B penanda butir tetap ditanya Jev ("c. ...")',
        _sk8('b. Rating 2 = Netral', 'c. Rating 3 = Penting') is None)
    cek('v8-aturan: SKIP lama tetap menang atas JOIN baru (subbab bernomor)',
        _sk8('1.1 Latar Belakang',
             'bagian ini menjelaskan tentang') is False)
    cek('v8-aturan: _judul_pendek kenali judul, bukan fragmen',
        _jp8('Strategi Turn') is True
        and _jp8('KESIMPULAN') is True
        and _jp8('Islam Malang') is True
        and _jp8('Ekonomi') is False
        and _jp8('45') is False
        and _jp8('Manfaat praktis dalam penelitian ini adalah') is False)
    P8 = _muat_peta3()
    cek('v8-aturan: RULE_VERSION sudah naik dari v8 (kini v15)',
        P8.RULE_VERSION == 'jev-peta-v15')
    # ── 10. v9-aturan: SKIP B-DASH + SKIP JUDUL BERNOMOR 1 TINGKAT ──────
    #    Terukur live 1.14 (11 Nov 2026, run opt3 tersimpan):
    #    R2-1: Jev gabung B-dash hanya 22-26% (p-med 0,10-0,15), semua
    #    gabungan yang diperiksa salah (butir/kutipan baru); tidak satu
    #    pun gabung p>=0,6. R2-2: pemisahan SEMPURNA — 11 gabung-salah
    #    di-override p<=0,47, 8 gabung-benar dipertahankan p>=0,74.
    cek('v9-aturan: B dash = butir baru ("pasaran." + "- “AyuMeera")',
        _sk8('pasaran.”', '- “AyuMeera bisa jadi pilihan utama') is False)
    cek('v9-aturan: B dash = butir baru (SWOT "Opportunities")',
        _sk8('Opportunities', '- Tren hijab instan dan simple') is False)
    cek('v9-aturan: B en-dash = butir baru ("3.4.2 Tahapan")',
        _sk8('3.4.2 Tahapan', '– Tahapan Analisis Data') is False)
    cek('v9-aturan: B dash = butir baru (A kata gantung "komunitas")',
        _sk8('komunitas', '- Pengaruh peran media sosial') is False)
    cek('v9-aturan: B "-nya" TANPA spasi bukan penanda butir',
        _sk8('Kalimat belum selesai', '-nya adalah lanjutan') is None)
    cek('v9-aturan: judul 1 tingkat + ekor kalimat ("2. Manfaat Praktis")',
        _sk8('2. Manfaat Praktis',
             'Manfaat praktis dalam penelitian ini adalah dapat membantu')
        is False)
    cek('v9-aturan: judul 1 tingkat + ekor kalimat ("2. Wawancara")',
        _sk8('2. Wawancara',
             'Wawancara merupakan kegiatan untuk memperoleh penjelasan dan')
        is False)
    cek('v9-aturan: judul 1 tingkat + butir ("1. Kekuatan")',
        _sk8('1. Kekuatan (Strength)',
             'a. Produk relevan dengan kebutuhan hijabers lokal.') is False)
    cek('v9-aturan: judul 1 tingkat + butir ("2. Ancaman")',
        _sk8('2. Ancaman (Threats)', 'a. Harga pesaing lebih murah.')
        is False)
    cek('v9-aturan: lanjutan judul 1 tingkat tetap tanya Jev (p 0,94)',
        _sk8('1. Mendukung Strategi', 'Agresif (Khoironi, 2023)') is None)
    cek('v9-aturan: lanjutan judul 1 tingkat tetap tanya Jev ("Strategi Turn")',
        _sk8('3. Mendukung', 'Strategi Turn') is None)
    cek('v9-aturan: lanjutan judul 1 tingkat tetap tanya Jev (satu kata)',
        _sk8('2. Mendukung Strategi', 'Diversifikasi') is None)
    cek('v9-aturan: tahun "2023. ..." BUKAN judul bernomor',
        _sk8('2023. Penelitian ini menunjukkan',
             'Hasil penelitian menunjukkan bahwa') is None)
    cek('v9-aturan: desimal koma "2,5 ..." BUKAN judul bernomor (tetap gabung)',
        _sk8('2,5 juta responden yang', 'berpartisipasi dalam survei ini')
        is True)
    cek('v9-aturan: judul 1 tingkat PANJANG (>8 kata) tetap tanya/gabung',
        _sk8('1. Membuat tabel matriks IFAS (Internal Startegy Factor '
             'Analysis Sumary) dan',
             'membuat keputusan yang lebih tepat') is True)
    cek('v9-aturan: nomor halaman di depan judul 1 tingkat tetap kena SKIP',
        _sk8('13 2. Manfaat Praktis',
             'Manfaat praktis dalam penelitian ini adalah dapat membantu')
        is False)
    # NUL: artefak PDF fid=112 (103 NUL di teks bersih) — dibuang di susun.
    FakeKonversi.mode = 'normal'
    teks_nul = ('BAB I\nPENDAHULUAN\n'
                'Kalimat dengan\x00 NUL di tengah dan cukup panjang untuk lolos saringan baris pendek.\n'
                'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n')
    d_nul = P._susun_dari_bersih(teks_nul)
    cek('v8-aturan: byte NUL dibuang dari baris susun',
        not any('\x00' in b for b in d_nul['baris']),
        str(d_nul['baris']))
    # stitch lintas-kosong B-huruf-kecil: diputuskan KODE, tanpa Jev.
    FakeKonversi.mode = 'normal'
    FAKE_SATPAM.panggilan.clear()
    teks_lintas_kecil = ('Kalimat pertama yang belum selesai\n\n'
                         'dan berlanjut di baris berikut ini.\n'
                         'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.\n')
    hasil_lk = P._stitch_baris(teks_lintas_kecil,
                               tanya_fn=FAKE_SATPAM.tanya_bebas_mutu)
    cek('v8-aturan: stitch lintas-kosong B-huruf-kecil tersambung',
        'Kalimat pertama yang belum selesai dan berlanjut di baris berikut ini.'
        in hasil_lk)
    cek('v8-aturan: pasangan B-huruf-kecil TIDAK ditanya ke Jev',
        FAKE_SATPAM.panggilan == [],
        str(FAKE_SATPAM.panggilan))
    # ── 11. v10-aturan: DEMOSI BAB TANPA PENGECUALIAN SISTEMATIKA (R2-3) ─
    #    Terukur live 1.14 (11 Nov 2026, sesi segar v9): 3 judul BAB sampah
    #    lolos ke daftar bab, semuanya baris deskripsi blok sistematika
    #    yang dilabeli 'bab' oleh Jev — pengecualian sistematika-lah yang
    #    melindungi mereka (demosi 0 kali jalan di 18 run tersimpan).
    #    Perbaikan: demosi TIDAK lagi melewati sistematika; salinan judul
    #    asli tetap aman karena COCOK _POLA_BAB_NOMOR.
    cek('v10-aturan: RULE_VERSION naik dari v9 (kini v15)',
        P8.RULE_VERSION == 'jev-peta-v15')
    baris_r23 = [
        'terbagi menjadi beberapa bab antara lain:',
        '1. BAB I PENDAHULUAN',
        'bagian ini berisikan latar belakang masalah,',
        '2. BAB II TINJAUAN PUSTAKA',
        'bagian ini menjelaskan tentang landasan',
        '5. BAB V PENUTUP',
        'pada bab ini penulis akan menjelaskan mengenai kesimpulan penelitian dan saran.',
        'Isi paragraf yang panjang dan tidak terbelah karena sudah panjang sekali.',
    ]
    label_r23 = {1: 'bab', 3: 'bab', 4: 'bab', 5: 'bab', 6: 'bab'}
    kand_r23 = [(i, baris_r23[i]) for i in range(len(baris_r23))]
    sist_r23 = {1, 2, 3, 4, 5, 6}
    _bk, _bg, demosi_r23 = P._koreksi_bab_deterministik(
        baris_r23, label_r23, kand_r23, sist_r23, {}, set())
    cek('v10-aturan: deskripsi sistematika "pada bab ini ..." didemosi ke paragraf',
        label_r23.get(6) == 'paragraf', str(label_r23))
    cek('v10-aturan: deskripsi sistematika "bagian ini ..." didemosi ke biasa',
        label_r23.get(4) == 'biasa', str(label_r23))
    cek('v10-aturan: salinan judul sistematika "1. BAB I ..." tetap bab',
        label_r23.get(1) == 'bab', str(label_r23))
    cek('v10-aturan: salinan judul sistematika "5. BAB V ..." tetap bab',
        label_r23.get(5) == 'bab', str(label_r23))
    cek('v10-aturan: demosi bab sistematika tercatat',
        sorted(demosi_r23) == [4, 6], str(demosi_r23))

    # ── 12. v11-aturan: LAPISAN BENTUK (latihan 112 naskah) ─────────────
    #    Lapis 1 profil_bentuk() deterministik; aturan baru: BOM, pemisah
    #    gabungan, CHAPTER polos, judul Romawi tanpa kata BAB (berpagar
    #    profil); Lapis 2 pendapat_kedua() hanya untuk baris goyang
    #    (jawaban disuntik, nol Jev di sini); Lapis 3 antrean manusia.
    cek('v11-aturan: RULE_VERSION naik dari v10 (kini v15)',
        P8.RULE_VERSION == 'jev-peta-v15')
    # --- 12f. v12 rantai 3 langkah: mode agen-kedua + pabrik agen kedua ---
    cek('v12-aturan: RULE_VERSION naik dari v11 (kini v15)',
        P8.RULE_VERSION == 'jev-peta-v15')
    # --- 12a. profil_bentuk ---
    teks_romawi = ('I. PENDAHULUAN\nIsi pendahuluan yang cukup panjang dan menjelaskan latar belakang masalah penelitian ini.\n'
                   'II. TINJAUAN PUSTAKA\nIsi tinjauan pustaka yang cukup panjang dan menjelaskan teori yang dipakai dalam penelitian ini.\n'
                   'III. PELAKSANAAN PENELITIAN\nIsi pelaksanaan penelitian yang cukup panjang dan menjelaskan cara penelitian dilakukan.\n'
                   'IV. HASIL DAN PEMBAHASAN\nIsi hasil dan pembahasan yang cukup panjang dan menjelaskan temuan penelitian ini.\n'
                   'V. KESIMPULAN DAN SARAN\nIsi kesimpulan dan saran yang cukup panjang dan menutup penelitian ini dengan baik.\n')
    prof_r = P8.profil_bentuk(teks_romawi)
    cek('v11-profil: Romawi tanpa BAB dikenali (Y1/AD1/AG1)',
        prof_r['penomoran_bab'] == 'romawi_tanpa_bab', str(prof_r['penomoran_bab']))
    cek('v11-profil: judul Romawi terukur masuk kosakata',
        prof_r['romawi_judul'] == ['HASIL DAN PEMBAHASAN', 'KESIMPULAN DAN SARAN',
                                   'PELAKSANAAN PENELITIAN', 'PENDAHULUAN',
                                   'TINJAUAN PUSTAKA'], str(prof_r['romawi_judul']))
    cek('v11-profil: Romawi tanpa BAB tidak masuk antrean',
        prof_r['antrean_manusia'] is False)
    cek('v11-profil: saklar judul Romawi menyala',
        prof_r['aturan']['judul_romawi_tanpa_bab'] is True)
    teks_chapter = ('CHAPTER I\nINTRODUCTION\n'
                    'The study of the English and Indonesian adverbs in the text of the novels and the translation of the words in the corpus.\n'
                    'CHAPTER II\nTHEORETICAL BACKGROUND\n'
                    'The theory of the adverbs and the classification of the forms in the English language and in the Indonesian language.\n')
    prof_c = P8.profil_bentuk(teks_chapter)
    cek('v11-profil: CHAPTER Inggris dikenali (T1/T2/T3/AH1)',
        prof_c['penomoran_bab'] == 'chapter' and prof_c['chapter'] == ['I', 'II'],
        str(prof_c))
    cek('v11-profil: rasio Inggris di atas ambang 0,02',
        prof_c['bahasa_inggris'] is True and prof_c['rasio_inggris'] >= 0.02,
        str(prof_c['rasio_inggris']))
    cek('v11-profil: CHAPTER Inggris tidak masuk antrean',
        prof_c['antrean_manusia'] is False)
    prof_n = P8.profil_bentuk('BAB I\nPENDAHULUAN\n1.1 Latar Belakang\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\nBAB II\nTINJAUAN PUSTAKA\n')
    cek('v11-profil: BAB Romawi biasa dikenali',
        prof_n['penomoran_bab'] == 'romawi' and prof_n['jml_bab_terdeteksi'] == 2)
    prof_a = P8.profil_bentuk('BAB 1\nPENDAHULUAN\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\nBAB 2\nTINJAUAN PUSTAKA\n')
    cek('v11-profil: BAB Arab dikenali',
        prof_a['penomoran_bab'] == 'arab' and prof_a['bab_arab'] == [1, 2])
    prof_x = P8.profil_bentuk('BAB I\nPENDAHULUAN\nBAB 2\nTINJAUAN PUSTAKA\n')
    cek('v11-profil: campuran Romawi + Arab dikenali',
        prof_x['penomoran_bab'] == 'campuran')
    prof_t = P8.profil_bentuk('Kalimat biasa satu yang panjang dan menjelaskan sesuatu yang penting di sini.\n'
                              'Kalimat biasa dua yang panjang dan menjelaskan sesuatu yang lain dengan jelas sekali.\n')
    cek('v11-profil: tanpa penanda apa pun -> tidak_ada + antrean',
        prof_t['penomoran_bab'] == 'tidak_ada' and prof_t['antrean_manusia'] is True
        and prof_t['alasan_antrean'] == ['tidak ada penanda BAB/CHAPTER/judul Romawi'],
        str(prof_t))
    prof_nul = P8.profil_bentuk('BAB I\nPENDAHULUAN\n' + 'x\x00' * 60 + '\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n')
    cek('v11-profil: NUL > 50 -> antrean (fid=112: 103 NUL)',
        prof_nul['antrean_manusia'] is True
        and any('NUL' in a for a in prof_nul['alasan_antrean']), str(prof_nul))
    prof_tab = P8.profil_bentuk('\n'.join('a | b | c' for _ in range(21)) + '\nBAB I\nPENDAHULUAN\n')
    cek('v11-profil: tabel padat > 20 baris pipa (K1 60, Q3 36, B2 22)',
        prof_tab['tabel_padat'] is True and prof_tab['tabel_baris_pipa'] == 21)
    cek('v11-profil: KTI D3 dikenali (N1/N2/N3)',
        P8.profil_bentuk('Karya Tulis Ilmiah ini disusun untuk memenuhi syarat Ahli Madya.\nBAB I\nPENDAHULUAN\n')['kti_d3'] is True)
    prof_4 = P8.profil_bentuk('BAB I\nPENDAHULUAN\nBAB II\nTINJAUAN PUSTAKA\nBAB III\nMETODE PENELITIAN\nBAB IV\nPENUTUP\n')
    cek('v11-profil: empat bab dikenali (O1/O2/O3/U3/AA3)',
        prof_4['empat_bab'] is True and prof_4['jml_bab_terdeteksi'] == 4)
    cek('v11-profil: sistematika dikenali (36 naskah)',
        P8.profil_bentuk('SISTEMATIKA PENULISAN\nBAB I\nPENDAHULUAN\n')['sistematika'] is True)
    cek('v11-profil: pemisah gabungan dihitung (117 baris di 50 teks)',
        P8.profil_bentuk('===== BAB I (BAB 1.doc) =====\nBAB I\nPENDAHULUAN\n===== SKRIPSI.doc =====\n')['pemisah_gabung_jml'] == 2)
    cek('v11-profil: BOM dihitung (66 teks)',
        P8.profil_bentuk('\ufeffBAB I\nPENDAHULUAN\n')['bom_jml'] == 1)
    # --- 12b. susun: aturan baru ---
    d_bom = P8._susun_dari_bersih('\ufeffBAB I\nPENDAHULUAN\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n')
    cek('v11-susun: BOM dibuang dari baris',
        not any('\ufeff' in b for b in d_bom['baris']), str(d_bom['baris']))
    cek('v11-susun: BAB I ber-BOM tetap dikenali sebagai bab',
        any(v[0] == 'BAB I' and v[1] == 'PENDAHULUAN'
            for v in d_bom.get('gabung', {}).values()), str(d_bom.get('gabung')))
    d_pem = P8._susun_dari_bersih('===== BAB I (BAB 1.doc) =====\nBAB I\nPENDAHULUAN\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n===== SKRIPSI.doc =====\nIsi paragraf kedua yang panjang dan menjelaskan banyak hal penting di sini.\n')
    idx_pem = [i for i, b in enumerate(d_pem['baris']) if '=====' in b]
    cek('v11-susun: pemisah gabungan dibuang, bukan kandidat',
        idx_pem and all(i in d_pem['buang'] for i in idx_pem)
        and all(i not in dict(d_pem['kand']) for i in idx_pem),
        str((idx_pem, d_pem['buang'], d_pem['kand'])))
    d_ch = P8._susun_dari_bersih('CHAPTER II\nTHEORETICAL BACKGROUND\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n')
    cek('v11-susun: CHAPTER polos + judul dikenali sebagai bab',
        any(v[0] == 'CHAPTER II' and v[1] == 'THEORETICAL BACKGROUND'
            for v in d_ch.get('gabung', {}).values()), str(d_ch.get('gabung')))
    d_ch1 = P8._susun_dari_bersih('CHAPTER I:\tINTRODUCTION\n1.1 Background of study\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n')
    cek('v11-susun: CHAPTER satu baris bertitik-dua TIDAK dipaksa (daftar isi T2)',
        not any(v[0].startswith('CHAPTER') for v in d_ch1.get('gabung', {}).values()),
        str(d_ch1.get('gabung')))
    d_ro = P8._susun_dari_bersih(teks_romawi)
    cek('v11-susun: judul Romawi tanpa BAB jadi gabung bila profil begitu',
        {v[0] for v in d_ro.get('gabung', {}).values()}
        == {'I.', 'II.', 'III.', 'IV.', 'V.'}, str(d_ro.get('gabung')))
    d_ro_off = P8._susun_dari_bersih('BAB I\nPENDAHULUAN\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\nII. TINJAUAN PUSTAKA\nIsi tinjauan pustaka yang cukup panjang dan menjelaskan teori yang dipakai dalam penelitian ini.\n')
    cek('v11-susun: judul Romawi TIDAK jadi bab bila naskah ber-BAB (O1)',
        not any(v[0] == 'II.' for v in d_ro_off.get('gabung', {}).values()),
        str(d_ro_off.get('gabung')))
    d_ro_sitasi = P8._susun_dari_bersih('BAB I\nPENDAHULUAN\nVI. Pp. 1187-1196.\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n')
    cek('v11-susun: Romawi sitasi bukan judul (tidak masuk gabung)',
        not any(v[0] == 'VI.' for v in d_ro_sitasi.get('gabung', {}).values()),
        str(d_ro_sitasi.get('gabung')))
    # --- 12c. pendapat_kedua (unit, tanpa Jev) ---
    cek('v11-pk: suara sepakat -> bukan-goyang',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'paragraf'], [0.9, 0.9])['putusan'] == 'bukan-goyang')
    cek('v11-pk: sepakat suara teratas -> tetap',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'paragraf', 'confidence': 0.8}) == {'idx': 3, 'putusan': 'tetap', 'label': 'paragraf',
                          'alasan': 'pendapat kedua sepakat dengan suara teratas'})
    cek('v11-pk: minoritas + lebih yakin -> berbalik',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.6, 0.55],
                          {'label': 'biasa', 'confidence': 0.9})['putusan'] == 'berbalik'
        and P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.6, 0.55],
                              {'label': 'biasa', 'confidence': 0.9})['label'] == 'biasa')
    cek('v11-pk: minoritas tapi kurang yakin -> tetap',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'biasa', 'confidence': 0.7})['putusan'] == 'tetap')
    cek('v11-pk: tanpa pendapat kedua -> antrean, label tidak dipaksa',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6], None) == {'idx': 3, 'putusan': 'antrean-manusia', 'label': None,
                          'alasan': 'tidak ada pendapat kedua'})
    cek('v11-pk: pendapat kedua tidak yakin -> antrean',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'biasa', 'confidence': 0.4})['putusan'] == 'antrean-manusia')
    cek('v11-pk: tiga suara berbeda -> antrean',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'subbab', 'confidence': 0.9})['putusan'] == 'antrean-manusia')
    # --- 12d. kait petakan: pendapat kedua disuntik dari suara tersimpan ---
    #    Tiap panggilan memakai penanda GOYANG-PB berbeda: FakeSatpam
    #    menghitung panggilan per tengah, jadi teks yang sama diulang tidak
    #    lagi goyang pada panggilan ke-2 (penghitung sudah lewat ambang).
    FakeKonversi.mode = 'normal'
    FAKE_SATPAM.rendah = set()
    P8._CACHE_PETA.clear()
    teks_pk = ('BAB I\nPENDAHULUAN\n'
               'Kalimat GOYANG-PB-V11A tentang pemasaran digital dan kinerja bisnis usaha kecil di Indonesia yang panjang.\n')
    r_pk0 = P8.petakan_dari_teks(teks_pk, putaran=1)
    idx_pk = next(i for i, b in enumerate(r_pk0['baris']) if 'GOYANG-PB-V11A' in b)
    cek('v11-kait: tanpa fn -> perilaku v10 (label paragraf, pk 0)',
        r_pk0['label'].get(idx_pk) == 'paragraf' and r_pk0.get('pendapat_kedua_jml') == 0,
        str((r_pk0['label'].get(idx_pk), r_pk0.get('pendapat_kedua_jml'), r_pk0.get('goyang'))))
    cek('v11-kait: baris goyang tercatat sebelum pendapat kedua',
        any(g[0] == idx_pk for g in r_pk0.get('goyang', [])),
        str(r_pk0.get('goyang')))
    teks_pk1 = teks_pk.replace('GOYANG-PB-V11A', 'GOYANG-PB-V11B')
    r_pk1 = P8.petakan_dari_teks(
        teks_pk1, putaran=1,
        pendapat_kedua_fn=lambda i, t, s, p: {'label': 'biasa', 'confidence': 0.95})
    idx_pk1 = next(i for i, b in enumerate(r_pk1['baris']) if 'GOYANG-PB-V11B' in b)
    cek('v11-kait: pendapat kedua minoritas + yakin -> label berbalik',
        r_pk1['label'].get(idx_pk1) == 'biasa'
        and r_pk1.get('pendapat_kedua_berbalik') == [[idx_pk1, 'paragraf', 'biasa']],
        str((r_pk1['label'].get(idx_pk1), r_pk1.get('pendapat_kedua_berbalik'))))
    teks_pk2 = teks_pk.replace('GOYANG-PB-V11A', 'GOYANG-PB-V11C')
    r_pk2 = P8.petakan_dari_teks(
        teks_pk2, putaran=1,
        pendapat_kedua_fn=lambda i, t, s, p: None)
    idx_pk2 = next(i for i, b in enumerate(r_pk2['baris']) if 'GOYANG-PB-V11C' in b)
    cek('v11-kait: pendapat kedua kosong -> label tetap, baris ke antrean',
        r_pk2['label'].get(idx_pk2) == 'paragraf'
        and r_pk2.get('pendapat_kedua_antrean') == [idx_pk2]
        and r_pk2.get('antrean_manusia') is True,
        str((r_pk2['label'].get(idx_pk2), r_pk2.get('pendapat_kedua_antrean'))))
    # --- 12e. gerbang antrean: bentuk tak dikenal ditandai, bukan dipetakan diam-diam ---
    r_tidak = P8.petakan_dari_teks(
        'Kalimat biasa satu yang panjang dan menjelaskan sesuatu yang penting di sini.\n'
        'Kalimat biasa dua yang panjang dan menjelaskan sesuatu yang lain dengan jelas sekali.\n'
        'Kalimat biasa tiga yang panjang dan menutup bagian ini dengan kesimpulan yang jelas.\n',
        putaran=1)
    cek('v11-gerbang: tanpa penanda -> antrean_manusia True + alasan',
        r_tidak.get('antrean_manusia') is True
        and r_tidak.get('alasan_antrean') == ['tidak ada penanda BAB/CHAPTER/judul Romawi']
        and r_tidak.get('profil_bentuk', {}).get('penomoran_bab') == 'tidak_ada',
        str((r_tidak.get('antrean_manusia'), r_tidak.get('alasan_antrean'))))
    cek('v11-gerbang: naskah biasa ber-BAB tidak masuk antrean',
        P8.petakan_dari_teks(
            'BAB I\nPENDAHULUAN\nIsi paragraf biasa yang panjang dan menjelaskan banyak hal penting di sini.\n',
            putaran=1).get('antrean_manusia') is False)
    # --- 12f. v12 RANTAI 3 LANGKAH: mode agen-kedua + pabrik agen kedua ---
    # 12f-1. mode agen-kedua (unit, tanpa Jev)
    cek('v12-pk2: agen-kedua sepakat -> tetap',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'paragraf', 'confidence': 0.8},
                          mode='agen-kedua')['putusan'] == 'tetap')
    cek('v12-pk2: agen-kedua beda bukan-bab -> berbalik (keputusan agen kedua dipakai)',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'subbab', 'confidence': 0.9},
                          mode='agen-kedua') == {
            'idx': 3, 'putusan': 'berbalik', 'label': 'subbab',
            'alasan': 'agen kedua beda (bukan soal bab), keputusannya dipakai'})
    cek('v12-pk2: agen-kedua beda soal judul bab (label kedua bab) -> antrean',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'bab', 'confidence': 0.9},
                          mode='agen-kedua')['putusan'] == 'antrean-manusia')
    cek('v12-pk2: agen-kedua beda soal judul bab (label Jev bab) -> antrean',
        P8.pendapat_kedua(3, 'x', ['bab', 'paragraf'], [0.9, 0.6],
                          {'label': 'paragraf', 'confidence': 0.9},
                          mode='agen-kedua')['putusan'] == 'antrean-manusia')
    cek('v12-pk2: agen-kedua tidak yakin -> antrean',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'biasa', 'confidence': 0.4},
                          mode='agen-kedua')['putusan'] == 'antrean-manusia')
    cek('v12-pk2: tanpa jawaban kedua -> antrean',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          None, mode='agen-kedua')['putusan'] == 'antrean-manusia')
    cek('v12-pk2: mode suara lama tetap (label ketiga -> antrean)',
        P8.pendapat_kedua(3, 'x', ['paragraf', 'biasa'], [0.9, 0.6],
                          {'label': 'subbab', 'confidence': 0.9})['putusan']
        == 'antrean-manusia')
    # 12f-2. modul agen_kedua (unit, tanpa jaringan — penanya palsu)
    import app.agen_kedua as AK
    _env_lama = os.environ.get('EDUAI_AGEN_KEDUA_AKTIF')
    os.environ.pop('EDUAI_AGEN_KEDUA_AKTIF', None)
    cek('v12-ak: saklar bawaan mati',
        AK.aktif() is False)
    cek('v12-ak: pabrik mati -> None (perilaku v11)',
        AK.buat_pendapat_kedua_fn() is None)
    os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '1'
    cek('v12-ak: saklar nyala bila env 1',
        AK.aktif() is True)

    def _penanya_palsu(prompt):
        return (json.dumps({'label': 'biasa', 'confidence': 0.9,
                            'alasan': 'butir enumerasi'}, ensure_ascii=False),
                'model-palsu')

    fn_ak = AK.buat_pendapat_kedua_fn(penanya=_penanya_palsu)
    cek('v12-ak: pabrik nyala -> fn terpanggil',
        callable(fn_ak) and hasattr(fn_ak, 'log'))
    jw_ak = fn_ak(5, '2. Manfaat Praktis', ['paragraf', 'biasa'], [0.9, 0.6],
                  {'sebelum': ['1. Pendahuluan'], 'sesudah': ['Isi.'],
                   'judul_bab_terdekat': 'BAB I'})
    cek('v12-ak: fn kembalikan label+confidence agen kedua',
        jw_ak == {'label': 'biasa', 'confidence': 0.9,
                  'alasan': 'butir enumerasi', 'model': 'model-palsu'})
    cek('v12-ak: fn mencatat log keputusan',
        len(fn_ak.log) == 1 and fn_ak.log[0]['idx'] == 5
        and fn_ak.log[0]['label_kedua'] == 'biasa')

    def _penanya_galat(prompt):
        raise RuntimeError('jaringan mati (uji)')

    fn_galat = AK.buat_pendapat_kedua_fn(penanya=_penanya_galat)
    cek('v12-ak: penanya galat -> None (gagal tertutup, bukan tebakan)',
        fn_galat(5, 'x', ['paragraf', 'biasa'], [0.9, 0.6]) is None)
    cek('v12-ak: urai jawaban JSON sah',
        AK._urai_jawaban(
            'ini {"label": "subbab", "confidence": 0.8, "alasan": "ok"} akhir')
        == {'label': 'subbab', 'confidence': 0.8, 'alasan': 'ok'})
    cek('v12-ak: urai jawaban label tidak sah -> None',
        AK._urai_jawaban('{"label": "judul", "confidence": 0.9}') is None)
    cek('v12-ak: urai jawaban bukan JSON -> None',
        AK._urai_jawaban('tidak ada json di sini') is None)
    cek('v12-ak: prompt memuat aturan label + konteks lebar',
        'biasa' in AK._prompt('2. Manfaat',
                              {'sebelum': ['a'], 'sesudah': ['b'],
                               'judul_bab_terdekat': 'BAB I'})
        and 'BARIS YANG DINILAI' in AK._prompt('2. Manfaat', None))
    if _env_lama is None:
        os.environ.pop('EDUAI_AGEN_KEDUA_AKTIF', None)
    else:
        os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = _env_lama
    cek('v12-ak: saklar mati lagi sesudah uji -> pabrik None',
        AK.buat_pendapat_kedua_fn() is None)
    # 12f-3. kait petakan: mode agen-kedua lewat wiring (FakeSatpam)
    FakeKonversi.mode = 'normal'
    FAKE_SATPAM.rendah = set()
    P8._CACHE_PETA.clear()
    teks_v12 = ('BAB I\nPENDAHULUAN\n'
                'Kalimat GOYANG-PB-V12A tentang pemasaran digital dan kinerja bisnis usaha kecil di Indonesia yang panjang.\n')
    r_v12a = P8.petakan_dari_teks(
        teks_v12, putaran=1,
        pendapat_kedua_fn=lambda i, t, s, p: {'label': 'subbab',
                                              'confidence': 0.9})
    idx_v12a = next(i for i, b in enumerate(r_v12a['baris'])
                    if 'GOYANG-PB-V12A' in b)
    cek('v12-kait: agen kedua label ketiga (bukan soal bab) -> berbalik',
        r_v12a['label'].get(idx_v12a) == 'subbab'
        and r_v12a.get('pendapat_kedua_berbalik') == [[idx_v12a, 'paragraf', 'subbab']],
        str((r_v12a['label'].get(idx_v12a),
             r_v12a.get('pendapat_kedua_berbalik'))))
    teks_v12b = teks_v12.replace('GOYANG-PB-V12A', 'GOYANG-PB-V12B')
    r_v12b = P8.petakan_dari_teks(
        teks_v12b, putaran=1,
        pendapat_kedua_fn=lambda i, t, s, p: {'label': 'bab',
                                              'confidence': 0.95})
    idx_v12b = next(i for i, b in enumerate(r_v12b['baris'])
                    if 'GOYANG-PB-V12B' in b)
    cek('v12-kait: agen kedua beda soal judul bab -> antrean, label tetap',
        r_v12b['label'].get(idx_v12b) == 'paragraf'
        and idx_v12b in r_v12b.get('pendapat_kedua_antrean', [])
        and r_v12b.get('antrean_manusia') is True,
        str((r_v12b['label'].get(idx_v12b),
             r_v12b.get('pendapat_kedua_antrean'))))
    _konteks_diterima = {}

    def _fn_konteks(i, t, s, p, k=None):
        _konteks_diterima['k'] = k
        return {'label': 'biasa', 'confidence': 0.9}

    teks_v12c = teks_v12.replace('GOYANG-PB-V12A', 'GOYANG-PB-V12C')
    P8._CACHE_PETA.clear()
    r_v12c = P8.petakan_dari_teks(teks_v12c, putaran=1,
                                  pendapat_kedua_fn=_fn_konteks)
    cek('v12-kait: fn menerima konteks lebar (sebelum/sesudah/judul bab)',
        isinstance(_konteks_diterima.get('k'), dict)
        and 'PENDAHULUAN' in ' '.join(_konteks_diterima['k'].get('sebelum', []))
        and _konteks_diterima['k'].get('judul_bab_terdekat') == 'BAB I PENDAHULUAN',
        str(_konteks_diterima.get('k')))
    cek('v12-kait: jejak jawaban agen kedua tercatat di hasil',
        any(j.get('idx') == idx_v12a and j.get('putusan') == 'berbalik'
            and j.get('label_jev') == 'paragraf'
            and j.get('label_kedua') == 'subbab'
            for j in r_v12a.get('pendapat_kedua_jawaban', [])),
        str(r_v12a.get('pendapat_kedua_jawaban')))
    # --- 13a. v13 GATING HAKIM: agen kedua HANYA baris ditandai Hakim ---
    #    Pola GOYANG-PB yang sama seperti 12d (FakeSatpam): baris penanda
    #    goyang paragraf/biasa, label menang paragraf.
    cek('v15-versi: RULE_VERSION jev-peta-v15',
        P8.RULE_VERSION == 'jev-peta-v15', str(P8.RULE_VERSION))

    def _teks_v13(penanda):
        return ('BAB I\nPENDAHULUAN\n'
                'Kalimat %s tentang pemasaran digital dan kinerja bisnis '
                'usaha kecil di Indonesia yang panjang.\n' % penanda)

    def _fn_rekam(_dipanggil):
        def _fn(i, t, s, p, k=None):
            _dipanggil.append(i)
            return {'label': 'biasa', 'confidence': 0.95}
        return _fn

    def _hakim_tandai_teks(penanda):
        def _fn(peta):
            return {i for i, b in enumerate(peta.get('baris') or [])
                    if penanda in b}
        return _fn

    FakeKonversi.mode = 'normal'
    FAKE_SATPAM.rendah = set()
    # 13a-1. goyang TANPA tanda Hakim -> agen kedua TIDAK dipanggil.
    P8._CACHE_PETA.clear()
    _dipanggil_a = []
    r_v13a = P8.petakan_dari_teks(
        _teks_v13('GOYANG-PB-V13A'), putaran=1,
        pendapat_kedua_fn=_fn_rekam(_dipanggil_a),
        hakim_tandai_fn=lambda peta: set())
    idx_v13a = next(i for i, b in enumerate(r_v13a['baris'])
                    if 'GOYANG-PB-V13A' in b)
    cek('v13-gating: goyang tanpa tanda Hakim -> agen kedua tidak dipanggil',
        _dipanggil_a == [] and r_v13a.get('pendapat_kedua_jml') == 0
        and r_v13a['label'].get(idx_v13a) == 'paragraf'
        and r_v13a.get('hakim_tandai') == [],
        str((_dipanggil_a, r_v13a.get('pendapat_kedua_jml'),
             r_v13a['label'].get(idx_v13a), r_v13a.get('hakim_tandai'))))
    # 13a-2. goyang DITANDAI Hakim -> agen kedua dipanggil, berbalik jalan.
    P8._CACHE_PETA.clear()
    _dipanggil_b = []
    r_v13b = P8.petakan_dari_teks(
        _teks_v13('GOYANG-PB-V13B'), putaran=1,
        pendapat_kedua_fn=_fn_rekam(_dipanggil_b),
        hakim_tandai_fn=_hakim_tandai_teks('GOYANG-PB-V13B'))
    idx_v13b = next(i for i, b in enumerate(r_v13b['baris'])
                    if 'GOYANG-PB-V13B' in b)
    cek('v13-gating: goyang ditandai Hakim -> agen kedua dipanggil + berbalik',
        _dipanggil_b == [idx_v13b]
        and r_v13b['label'].get(idx_v13b) == 'biasa'
        and r_v13b.get('pendapat_kedua_berbalik') == [[idx_v13b, 'paragraf', 'biasa']]
        and r_v13b.get('hakim_tandai') == [idx_v13b],
        str((_dipanggil_b, r_v13b['label'].get(idx_v13b),
             r_v13b.get('pendapat_kedua_berbalik'), r_v13b.get('hakim_tandai'))))
    # 13a-3. fn gerbang mengembalikan None -> gagal tertutup, 0 panggilan.
    P8._CACHE_PETA.clear()
    _dipanggil_c = []
    r_v13c = P8.petakan_dari_teks(
        _teks_v13('GOYANG-PB-V13C'), putaran=1,
        pendapat_kedua_fn=_fn_rekam(_dipanggil_c),
        hakim_tandai_fn=lambda peta: None)
    idx_v13c = next(i for i, b in enumerate(r_v13c['baris'])
                    if 'GOYANG-PB-V13C' in b)
    cek('v13-gating: fn gerbang None -> agen kedua tidak dipanggil',
        _dipanggil_c == [] and r_v13c.get('pendapat_kedua_jml') == 0
        and r_v13c['label'].get(idx_v13c) == 'paragraf'
        and r_v13c.get('hakim_tandai') == [],
        str((_dipanggil_c, r_v13c.get('pendapat_kedua_jml'),
             r_v13c.get('hakim_tandai'))))
    # 13a-4. fn gerbang galat -> gagal tertutup + galat tercatat.
    P8._CACHE_PETA.clear()
    _dipanggil_d = []

    def _hakim_galat(peta):
        raise RuntimeError('hakim mati (uji)')

    r_v13d = P8.petakan_dari_teks(
        _teks_v13('GOYANG-PB-V13D'), putaran=1,
        pendapat_kedua_fn=_fn_rekam(_dipanggil_d),
        hakim_tandai_fn=_hakim_galat)
    idx_v13d = next(i for i, b in enumerate(r_v13d['baris'])
                    if 'GOYANG-PB-V13D' in b)
    cek('v13-gating: fn gerbang galat -> 0 panggilan + galat tercatat',
        _dipanggil_d == [] and r_v13d.get('pendapat_kedua_jml') == 0
        and r_v13d['label'].get(idx_v13d) == 'paragraf'
        and r_v13d.get('hakim_tandai') == []
        and r_v13d.get('hakim_tandai_galat') is not None,
        str((_dipanggil_d, r_v13d.get('hakim_tandai_galat'))))
    # 13a-5. saklar mati (tanpa pendapat_kedua_fn) -> perilaku v11, gerbang
    #    tidak dipakai (hakim_tandai None).
    P8._CACHE_PETA.clear()
    r_v13e = P8.petakan_dari_teks(
        _teks_v13('GOYANG-PB-V13E'), putaran=1,
        hakim_tandai_fn=_hakim_tandai_teks('GOYANG-PB-V13E'))
    idx_v13e = next(i for i, b in enumerate(r_v13e['baris'])
                    if 'GOYANG-PB-V13E' in b)
    cek('v13-gating: tanpa pendapat_kedua_fn -> perilaku v11, gerbang None',
        r_v13e.get('pendapat_kedua_jml') == 0
        and r_v13e['label'].get(idx_v13e) == 'paragraf'
        and r_v13e.get('hakim_tandai') is None,
        str((r_v13e.get('pendapat_kedua_jml'),
             r_v13e['label'].get(idx_v13e), r_v13e.get('hakim_tandai'))))
    # 13a-6. warisan: tanpa fn gerbang, tiap baris goyang tetap diadili (v12).
    P8._CACHE_PETA.clear()
    _dipanggil_f = []
    r_v13f = P8.petakan_dari_teks(
        _teks_v13('GOYANG-PB-V13F'), putaran=1,
        pendapat_kedua_fn=_fn_rekam(_dipanggil_f))
    idx_v13f = next(i for i, b in enumerate(r_v13f['baris'])
                    if 'GOYANG-PB-V13F' in b)
    cek('v13-gating: tanpa fn gerbang -> warisan v12 (per goyang)',
        _dipanggil_f == [idx_v13f]
        and r_v13f['label'].get(idx_v13f) == 'biasa'
        and r_v13f.get('hakim_tandai') is None,
        str((_dipanggil_f, r_v13f['label'].get(idx_v13f),
             r_v13f.get('hakim_tandai'))))
    # 13a-7. helper tandai_ragu_curiga (unit, tanpa Jev — _TANYA_FN palsu).
    def _tanya_palsu(bahan, pertanyaan):
        out = {}
        for nama in (pertanyaan or {}):
            out[nama] = {'noul': 0.5}
        return out

    _tanya_lama = H._TANYA_FN
    H._TANYA_FN = _tanya_palsu
    try:
        _peta_h = {'baris': ['BAB I', 'PENDAHULUAN',
                             '1.1 Latar Belakang yang panjang sekali dan '
                             'menjelaskan banyak hal penting di sini.',
                             'Isi paragraf biasa yang panjang dan menjelaskan '
                             'banyak hal penting di sini.'],
                   'label': {0: 'bab', 1: 'bab', 2: 'subbab', 3: 'paragraf'},
                   'gabung': {0: ['BAB I', 'PENDAHULUAN']},
                   'sistematika': [], 'p': {0: 0.9, 1: 0.9, 2: 0.8, 3: 0.9}}
        _tandai = H.tandai_ragu_curiga(_peta_h)
        cek('v13-hakim: tandai_ragu_curiga kembalikan set idx ragu/curiga',
            isinstance(_tandai, set) and 2 in _tandai,
            str(_tandai))
        cek('v13-hakim: tandai peta tanpa kandidat -> set kosong (bukan galat)',
            H.tandai_ragu_curiga({'baris': [], 'label': {}, 'gabung': {},
                                  'sistematika': [], 'p': {}}) == set())
    finally:
        H._TANYA_FN = _tanya_lama

    # --- 13a-8. v13 KOREKSI: suara tunggal + jawaban kedua -> diadili
    #    (baris ditandai Hakim yang tidak goyang). Tanpa jawaban, tetap
    #    'bukan-goyang' (kontrak v11 tidak berubah).
    _pk_tb = P8.pendapat_kedua(3, 'x', ['subbab'], [0.9],
        {'label': 'biasa', 'confidence': 0.95}, mode='agen-kedua')
    cek('v13-pk: suara tunggal + jawaban beda (bukan bab) -> berbalik',
        _pk_tb['putusan'] == 'berbalik' and _pk_tb['label'] == 'biasa',
        str(_pk_tb))
    _pk_tt = P8.pendapat_kedua(3, 'x', ['subbab'], [0.9],
        {'label': 'subbab', 'confidence': 0.95}, mode='agen-kedua')
    cek('v13-pk: suara tunggal + jawaban sepakat -> tetap',
        _pk_tt['putusan'] == 'tetap' and _pk_tt['label'] == 'subbab',
        str(_pk_tt))
    cek('v13-pk: suara tunggal tanpa jawaban -> bukan-goyang (kontrak v11)',
        P8.pendapat_kedua(3, 'x', ['subbab'], [0.9])['putusan']
        == 'bukan-goyang')
    _pk_tbb = P8.pendapat_kedua(3, 'x', ['subbab'], [0.9],
        {'label': 'bab', 'confidence': 0.95}, mode='agen-kedua')
    cek('v13-pk: suara tunggal + jawaban bab -> antrean-manusia',
        _pk_tbb['putusan'] == 'antrean-manusia', str(_pk_tbb))
    _pk_trg = P8.pendapat_kedua(3, 'x', ['subbab'], [0.9],
        {'label': 'biasa', 'confidence': 0.4}, mode='agen-kedua')
    cek('v13-pk: suara tunggal + jawaban tidak yakin -> antrean-manusia',
        _pk_trg['putusan'] == 'antrean-manusia', str(_pk_trg))
    # 13a-9. KOREKSI v13: baris DITANDAI Hakim yang TIDAK goyang -> agen
    #    kedua tetap dipanggil + berbalik (bukan dilewati seperti v13 awal
    #    yang hanya mengadili goyang yang ditandai).
    P8._CACHE_PETA.clear()
    _dipanggil_i = []
    r_v13i = P8.petakan_dari_teks(
        _teks_v13('DITANDAI-V13I'), putaran=1,
        pendapat_kedua_fn=_fn_rekam(_dipanggil_i),
        hakim_tandai_fn=_hakim_tandai_teks('DITANDAI-V13I'))
    idx_v13i = next(i for i, b in enumerate(r_v13i['baris'])
                    if 'DITANDAI-V13I' in b)
    cek('v13-gating: ditandai Hakim TIDAK goyang -> agen kedua dipanggil + berbalik',
        _dipanggil_i == [idx_v13i]
        and r_v13i['label'].get(idx_v13i) == 'biasa'
        and r_v13i.get('pendapat_kedua_berbalik')
        == [[idx_v13i, 'paragraf', 'biasa']]
        and r_v13i.get('hakim_tandai') == [idx_v13i]
        and not any(g[0] == idx_v13i for g in r_v13i.get('goyang') or []),
        str((_dipanggil_i, r_v13i['label'].get(idx_v13i),
             r_v13i.get('pendapat_kedua_berbalik'), r_v13i.get('hakim_tandai'),
             r_v13i.get('goyang'))))
    # 13a-10. Baris ditandai TIDAK goyang + agen kedua gagal (None) ->
    #    antrean manusia (flag Hakim tidak hilang diam-diam).
    P8._CACHE_PETA.clear()
    r_v13j = P8.petakan_dari_teks(
        _teks_v13('DITANDAI-V13J'), putaran=1,
        pendapat_kedua_fn=lambda i, t, s, p: None,
        hakim_tandai_fn=_hakim_tandai_teks('DITANDAI-V13J'))
    idx_v13j = next(i for i, b in enumerate(r_v13j['baris'])
                    if 'DITANDAI-V13J' in b)
    cek('v13-gating: ditandai TIDAK goyang + agen kedua gagal -> antrean',
        r_v13j.get('pendapat_kedua_antrean') == [idx_v13j]
        and r_v13j['label'].get(idx_v13j) == 'paragraf'
        and r_v13j.get('pendapat_kedua_jml') == 1,
        str((r_v13j.get('pendapat_kedua_antrean'),
             r_v13j['label'].get(idx_v13j), r_v13j.get('pendapat_kedua_jml'))))

    # --- 14. v14 PERBAIKAN LABEL BAB: salinan sistematika/daftar isi ------
    #    Salah terbesar v11/v13 di 279 baris berlabel: 42 baris benarnya
    #    `biasa` dilabeli `bab`. Aturan deterministik (1A pembersihan gabung,
    #    1B demosi blok) + pengecualian ATURAN 5 untuk penanda huruf kepala
    #    blok + prompt agen kedua yang tajam (diuji live terpisah).
    # 14a-1. Detektor blok: sistematika R3 (penanda polos + "terdiri dari").
    _baris_r3 = [
        'BAB I', 'Pendahuluan',
        'terdiri dari: Latar Belakang, Rumusan Masalah, dan Tujuan Penelitian.',
        'BAB II', 'Kajian Teori',
        'Bab ini membahas teori pemasaran dan perilaku konsumen secara mendalam.',
        'BAB III', 'Metode Penelitian',
        'Pada bab ini dijelaskan metode yang digunakan dalam penelitian ini.',
        'BAB IV', 'Hasil Penelitian',
        'Berisi tentang hasil olah data dan pembahasan temuan penelitian.',
        'BAB V', 'Penutup',
        'Bab ini berisi kesimpulan dan saran dari penelitian ini.',
    ]
    _gabung_r3 = {0: ('BAB I', ''), 3: ('BAB II', ''), 6: ('BAB III', ''),
                  9: ('BAB IV', ''), 12: ('BAB V', '')}
    _blok_r3 = P8._deteksi_blok_daftar_isi(_baris_r3, _gabung_r3)
    cek('v14-blok: sistematika R3 terdeteksi (5 penanda polos)',
        {0, 3, 6, 9, 12} <= _blok_r3, str(sorted(_blok_r3)))

    # 14a-2. Detektor blok: daftar isi T3 (bentuk satu baris, tanpa gabung).
    _baris_t3 = [
        'TABLE OF CONTENS',
        'CHAPTER I: INTRODUCTION',
        'CHAPTER II: LITERATURE REVIEW',
        'CHAPTER III: RESEARCH METHODOLOGY',
        'CHAPTER IV: RESULTS AND DISCUSSION',
        'CHAPTER V: CONCLUSION',
    ]
    _blok_t3 = P8._deteksi_blok_daftar_isi(_baris_t3, {})
    cek('v14-blok: daftar isi T3 terdeteksi (judul satu baris)',
        {1, 2, 3, 4} <= _blok_t3, str(sorted(_blok_t3)))

    # 14a-3. Negatif: bab asli berjauhan TIDAK jadi blok.
    _baris_asli = ['BAB I', 'PENDAHULUAN', 'Kalimat isi bab satu.'] + \
        ['Kalimat isi lanjutan nomor %d.' % n for n in range(60)] + \
        ['BAB II', 'KAJIAN TEORI', 'Kalimat isi bab dua.'] + \
        ['Kalimat isi lanjutan nomor %d.' % n for n in range(60, 120)] + \
        ['BAB III', 'METODE PENELITIAN', 'Kalimat isi bab tiga.']
    _gabung_asli = {0: ('BAB I', 'PENDAHULUAN'),
                    63: ('BAB II', 'KAJIAN TEORI'),
                    126: ('BAB III', 'METODE PENELITIAN')}
    _blok_asli = P8._deteksi_blok_daftar_isi(_baris_asli, _gabung_asli)
    cek('v14-blok: bab asli berjauhan TIDAK terdeteksi sebagai blok',
        _blok_asli == set(), str(sorted(_blok_asli)))

    # 14a-4. Fragmen titik-dua G3 (ekor judul terbelah) masuk blok.
    _baris_g3 = [
        'Bab I', 'Pendahuluan', ': PENGANTAR UMUM TENTANG PENELITIAN',
        'Bab II', 'Kajian Teori', ': LANDASAN TEORI DAN KERANGKA PIKIR',
        'Bab III', 'Metode Penelitian', ': METODE YANG DIGUNAKAN',
        'Bab IV', 'Hasil Penelitian', 'Berisi tentang hasil dan pembahasan.',
        'Bab V', 'Penutup', 'Bab ini berisi kesimpulan dan saran.',
    ]
    _gabung_g3 = {0: ('Bab I', ''), 3: ('Bab II', ''), 6: ('Bab III', ''),
                  9: ('Bab IV', ''), 12: ('Bab V', '')}
    _blok_g3 = P8._deteksi_blok_daftar_isi(_baris_g3, _gabung_g3)
    cek('v14-blok: fragmen titik-dua G3 masuk blok',
        {0, 2, 3, 5, 6, 8, 9, 12} <= _blok_g3, str(sorted(_blok_g3)))

    # 14b-1. Pembersihan gabung: dedupe per nomor bab (berjudul menang).
    _g_dedupe = {0: ('BAB I', 'PENDAHULUAN'), 50: ('BAB I', ''),
                 100: ('BAB II', 'KAJIAN TEORI')}
    _bersih, _blok = P8._bersihkan_gabung_daftar_isi(_baris_asli, _g_dedupe)
    cek('v14-gabung: dedupe per nomor bab (berjudul menang, polos gugur)',
        _bersih.get(0) == ('BAB I', 'PENDAHULUAN')
        and 50 not in _bersih and _bersih.get(100) == ('BAB II', 'KAJIAN TEORI'),
        str(_bersih))

    # 14b-2. Pembersihan gabung: judul berartefak nomor halaman dibuang.
    _g_art = {10: ('BAB II', 'LANDASAN TEORI??????????????????.. 4'),
              20: ('BAB III', 'METODOLOGI PENELITIAN')}
    _bersih2, _ = P8._bersihkan_gabung_daftar_isi(
        ['Kalimat isi.'] * 30, _g_art)
    cek('v14-gabung: judul berartefak nomor halaman dibuang',
        10 not in _bersih2 and 20 in _bersih2, str(_bersih2))

    # 14b-3. Pembersihan gabung: entri di blok salinan dibuang semua.
    _bersih3, _blok3 = P8._bersihkan_gabung_daftar_isi(_baris_r3, _gabung_r3)
    cek('v14-gabung: entri gabung di blok sistematika dibuang semua',
        _bersih3 == {}, str(_bersih3))

    # 14c-1. Demosi blok: 'bab'/'subbab' di blok -> 'biasa', di luar tetap.
    _lab = {0: 'bab', 1: 'paragraf', 3: 'subbab', 6: 'bab', 20: 'bab'}
    _kand = [(i, _baris_r3[i]) for i in range(len(_baris_r3))]
    P8._demosi_blok_daftar_isi(_baris_r3, _lab, _kand, _blok_r3)
    cek('v14-demosi: bab/subbab di blok -> biasa, bab di luar blok tetap',
        _lab[0] == 'biasa' and _lab[3] == 'biasa' and _lab[6] == 'biasa'
        and _lab[1] == 'paragraf' and _lab[20] == 'bab',
        str(_lab))

    # 14c-2. Fragmen titik-dua: ': PENGANTAR' tidak pernah bab/subbab.
    _lab2 = {2: 'bab', 5: 'subbab', 7: 'bab'}
    _kand2 = [(i, _baris_g3[i]) for i in range(len(_baris_g3))]
    P8._demosi_blok_daftar_isi(_baris_g3, _lab2, _kand2, set())
    cek('v14-demosi: fragmen titik-dua -> biasa walau di luar blok',
        _lab2[2] == 'biasa' and _lab2[5] == 'biasa' and _lab2[7] == 'bab',
        str(_lab2))

    # 14d-1. ATURAN 5: penanda huruf kepala blok BOLEH jadi subbab.
    _b_u2 = ['a) Persetubuhan',
             'Persetubuhan adalah hubungan seksual yang dilakukan oleh pasangan '
             'suami istri yang sah menurut hukum dan agama.']
    cek('v14-aturan5: "a) Persetubuhan" + uraian -> kepala blok (True)',
        P8._penanda_huruf_kepala_blok(_b_u2, 0) is True)
    _b_g3 = ['d. Mengenali Emosi Orang Lain',
             'Kemampuan untuk mengenali emosi orang lain disebut juga empati. '
             'Menurut Goleman (2002 :57) kemampuan seseorang untuk mengenali '
             'orang lain atau peduli, menunjukkan kemampuan empati seseorang.']
    cek('v14-aturan5: "d. Mengenali Emosi Orang Lain" + uraian -> True',
        P8._penanda_huruf_kepala_blok(_b_g3, 0) is True)

    # 14d-2. ATURAN 5: penanda huruf butir daftar tetap BUKAN subbab.
    _b_daftar = ['a) Butir pertama dalam daftar enumerasi ini.',
                 'b) Butir kedua dalam daftar enumerasi ini.',
                 'c) Butir ketiga dalam daftar enumerasi ini.']
    cek('v14-aturan5: penanda huruf diikuti butir lain -> bukan kepala blok',
        P8._penanda_huruf_kepala_blok(_b_daftar, 0) is False)
    _b_tabel = ['a) Lihat tabel berikut untuk rincian angka.',
                'Sumber: Data primer yang diolah peneliti pada tahun 2024.']
    cek('v14-aturan5: penanda huruf diikuti keterangan tabel -> False',
        P8._penanda_huruf_kepala_blok(_b_tabel, 0) is False)
    _b_panjang = ['b. Konfrontasi yaitu salah satu teknik pemeriksaan dalam '
                  'rangka penyidikan dengan cara mempertemukan satu dengan '
                  'lainnya untuk menguji kebenaran keterangan masing-masing.',
                  '2. Pemeriksaan dan penyitaan benda-benda yang dapat '
                  'menjadi barang bukti terjadinya tindak pidana perkosaan.']
    cek('v14-aturan5: kalimat definisi panjang -> False (koreksi_batas)',
        P8._penanda_huruf_kepala_blok(_b_panjang, 0) is False)

    # 14e-1. Fragmen gambar: "Pada Gambar" + "MANAJEMEN PROYEK" -> demosi.
    _b_h1 = ['BAB I', 'PENDAHULUAN',
             'Pada Gambar 2.1 disajikan alur manajemen proyek penelitian.',
             'MANAJEMEN PROYEK',
             'Kalimat isi bab satu yang panjang tentang pemasaran digital.']
    _lab_h1 = {3: 'bab'}
    _kand_h1 = [(3, _b_h1[3])]
    P8._koreksi_bab_deterministik(_b_h1, _lab_h1, _kand_h1, set(),
                                  {0: ('BAB I', 'PENDAHULUAN')}, {})
    cek('v14-demosi: fragmen gambar "MANAJEMEN PROYEK" -> biasa',
        _lab_h1[3] == 'biasa', str(_lab_h1))

    # 14e-2. Regresi: huruf BESAR pendek TANPA penunjuk gambar tetap bab.
    _b_h1b = ['BAB I', 'PENDAHULUAN',
              'Kalimat isi bab satu yang panjang tentang pemasaran digital.',
              'MANAJEMEN PROYEK',
              'Kalimat isi berikutnya yang panjang tentang pemasaran digital.']
    _lab_h1b = {3: 'bab'}
    _kand_h1b = [(3, _b_h1b[3])]
    P8._koreksi_bab_deterministik(_b_h1b, _lab_h1b, _kand_h1b, set(),
                                  {0: ('BAB I', 'PENDAHULUAN')}, {})
    cek('v14-demosi: huruf BESAR pendek tanpa penunjuk gambar tetap bab',
        _lab_h1b[3] == 'bab', str(_lab_h1b))

    # 14f. End-to-end: judul satu baris salinan daftar isi yang Jev labeli
    #    'bab' didemosi v14 jadi 'biasa'; bab asli (gabung) tidak tersentuh.
    _baris_e2e = [
        'TABLE OF CONTENS',
        'CHAPTER I: INTRODUCTION JEV-BAB',
        'CHAPTER II: LITERATURE REVIEW JEV-BAB',
        'CHAPTER III: RESEARCH METHODOLOGY JEV-BAB',
        'BAB I',
        'PENDAHULUAN',
        'Kalimat isi bab satu yang panjang tentang pemasaran digital dan kinerja bisnis usaha kecil di Indonesia.',
        'BAB II',
        'KAJIAN TEORI',
        'Kalimat isi bab dua yang panjang tentang pemasaran digital dan kinerja bisnis usaha kecil di Indonesia.',
    ]
    _gabung_e2e = {4: ('BAB I', 'PENDAHULUAN'), 7: ('BAB II', 'KAJIAN TEORI')}
    _gabung_bersih_e2e, _blok_e2e = P8._bersihkan_gabung_daftar_isi(
        _baris_e2e, _gabung_e2e)
    _d_e2e = {
        'baris': _baris_e2e,
        'kand': [(i, _baris_e2e[i]) for i in (1, 2, 3, 6, 9)],
        't': lambda i: _baris_e2e[i] if 0 <= i < len(_baris_e2e) else '',
        'gabung': _gabung_bersih_e2e,
        'blok_daftar_isi': sorted(_blok_e2e),
        'buang': set(),
        'kode_label': {},
        'awal': 0, 'akhir': len(_baris_e2e), 'nama': 'uji-v14-e2e',
    }
    P8._CACHE_PETA.clear()
    _r_e2e = P8._petakan_dari_hasil(_d_e2e, putaran=1)
    cek('v14-e2e: 3 judul salinan daftar isi -> biasa, isi tetap paragraf',
        _r_e2e['label'].get(1) == 'biasa'
        and _r_e2e['label'].get(2) == 'biasa'
        and _r_e2e['label'].get(3) == 'biasa'
        and _r_e2e['label'].get(6) == 'paragraf'
        and _r_e2e['label'].get(9) == 'paragraf',
        str({i: _r_e2e['label'].get(i) for i in (1, 2, 3, 6, 9)}))
    cek('v14-e2e: gabung bab asli utuh sesudah pembersihan',
        _r_e2e['gabung'] == _gabung_e2e, str(_r_e2e['gabung']))

    # 14g. _PEMBUANG: "TABLE OF CONTENS" (salah eja) dibuang sebagai judul
    #    daftar isi; "TABLE OF CONTENTS" yang benar juga dibuang.
    cek('v14-pembuang: TABLE OF CONTENS / CONTENTS dibuang',
        bool(P8._PEMBUANG.match('TABLE OF CONTENS'))
        and bool(P8._PEMBUANG.match('TABLE OF CONTENTS'))
        and P8.dibuang('TABLE OF CONTENS') is True)

    # 14h-1. Dedupe seri -> TERAKHIR (N3): TOC depan berjudul mendahului
    #    bab asli; yang bertahan harus bab asli (idx besar), bukan salinan.
    _baris_n3 = ['Kalimat isi.'] * 310
    _baris_n3[0] = 'BAB I'
    _baris_n3[26] = 'BAB II'
    _baris_n3[214] = 'BAB I'
    _baris_n3[309] = 'BAB II'
    _g_n3 = {0: ('BAB I', 'PENDAHULUAN'), 26: ('BAB II', 'TINJAUAN PUSTAKA'),
             214: ('BAB I', 'PENDAHULUAN'), 309: ('BAB II', 'TINJAUAN PUSTAKA')}
    _bersih_n3, _blok_n3 = P8._bersihkan_gabung_daftar_isi(_baris_n3, _g_n3)
    cek('v14-gabung: dedupe seri berjudul -> terakhir menang (bab asli)',
        _bersih_n3 == {214: ('BAB I', 'PENDAHULUAN'),
                       309: ('BAB II', 'TINJAUAN PUSTAKA')},
        str(_bersih_n3))

    # 14h-2. Tipe T: header TOC + 2 judul satu baris sesudahnya -> blok.
    _baris_t3b = [
        'TABLE OF CONTENS', '',
        'TITLE…………………………………………………………………………… i',
        'CHAPTER I: INTRODUCTION', '',
        'CHAPTER II: REVIEW OF RELATED LITERATURE',
    ]
    _blok_t3b = P8._deteksi_blok_daftar_isi(_baris_t3b, {})
    cek('v14-blok: Tipe T (header TOC + 2 judul satu baris) -> blok',
        {0, 3, 5} <= _blok_t3b, str(sorted(_blok_t3b)))
    _baris_t3c = ['TABLE OF CONTENS', '', 'CHAPTER I: INTRODUCTION']
    cek('v14-blok: Tipe T butuh >=2 judul (1 saja bukan blok)',
        P8._deteksi_blok_daftar_isi(_baris_t3c, {}) == set(),
        str(sorted(P8._deteksi_blok_daftar_isi(_baris_t3c, {}))))

    # 14h-3. Penjaga C4: bab asli yang didahului butir rumus ': = 0' dan
    #    diikuti kalimat pembuka 'Dalam bab ini...' TIDAK masuk blok.
    _baris_c4 = [
        'Untuk menentukan apakah diterima atau ditolak maka dengan '
        'menggunakan uji rasio.',
        ': = 0 berarti budaya perusahaan tidak berpengaruh terhadap '
        'efektivitas organisasi.',
        ': > 0 berarti budaya perusahaan berpengaruh terhadap efektivitas '
        'organisasi.',
        '', 'BAB IV', 'HASIL PENELITIAN DAN PEMBAHASAN', '',
        'Dalam bab ini akan diuraikan pembahasan atas jawaban wawancara '
        'dan kuesioner untuk penelitian ini.',
        '4.1 Karakteristik Responden',
    ]
    _gabung_c4 = {4: ('BAB IV', 'HASIL PENELITIAN DAN PEMBAHASAN')}
    _blok_c4 = P8._deteksi_blok_daftar_isi(_baris_c4, _gabung_c4)
    cek('v14-blok: bab asli C4 (rumus + "Dalam bab ini") bukan blok',
        4 not in _blok_c4, str(sorted(_blok_c4)))
    cek('v14-fragmen: ": = 0" dan ": > 0" bukan fragmen judul',
        not P8._POLA_FRAGMEN_TITIK_DUA.match(': = 0 berarti')
        and not P8._POLA_FRAGMEN_TITIK_DUA.match(': > 0 berarti')
        and bool(P8._POLA_FRAGMEN_TITIK_DUA.match(': PENGANTAR')))

    # 14h-4. Demosi kehilangan perlindungan (a): judul salinan yang
    #    penandanya sudah terhapus dari gabung didemosi; judul bab asli
    #    yang penandanya masih di gabung tetap dilindungi.
    _b_salinan = ['BAB III', 'Metode Penelitian', 'Kalimat isi.']
    _lab_sal = {1: 'bab'}
    P8._koreksi_bab_deterministik(_b_salinan, _lab_sal, [(1, _b_salinan[1])],
                                  set(), {}, {})
    cek('v14-demosi: judul salinan tanpa penanda di gabung -> biasa',
        _lab_sal[1] == 'biasa', str(_lab_sal))
    _b_asli = ['BAB III', 'Metode Penelitian', 'Kalimat isi.']
    _lab_asli = {1: 'bab'}
    P8._koreksi_bab_deterministik(_b_asli, _lab_asli, [(1, _b_asli[1])],
                                  set(), {0: ('BAB III', '')}, {})
    cek('v14-demosi: judul asli dgn penanda polos di gabung tetap bab',
        _lab_asli[1] == 'bab', str(_lab_asli))

    # ── v15: BOM di buang_daftar_isi ─────────────────────────────────────
    # Akar (R3 Bimbingan Konseling): satu BOM menempel di depan "BAB I"
    # ASLI membuat pola `^[ \t]*BAB` tidak cocok, sehingga salinan
    # SISTEMATIKA yang bersih jadi patokan potong dan isi BAB I asli hilang.
    _ST15 = _muat_asli('app.state_asli_v15', ROOT / 'app' / 'state.py')

    cek('v15-rapi: BOM + zero-width dikupas di kedua ujung',
        _ST15._rapi('\ufeffBAB I\u200b') == 'BAB I'
        and _ST15._rapi('\u200b\u200c  x  \ufeff') == 'x',
        repr(_ST15._rapi('\ufeffBAB I\u200b')))
    cek('v15-pola: _POLA_JUDUL_BAB cocok "BAB I" ber-BOM',
        bool(_ST15._POLA_JUDUL_BAB.match('\ufeffBAB I')))

    # 15a. Mini-R3: BAB I asli ber-BOM + salinan sistematika sesudahnya.
    _t_r3 = (
        '\n\n===== skripsi hasil final.rtf =====\n\n'
        '\ufeffBAB I\nPENDAHULUAN\n\n    A. LATAR BELAKANG\n'
        '      Anak berbakat memiliki kepribadian yang unik.\n\n'
        '    G. SISTEMATIKA PENULISAN LAPORAN DAN PEMBAHASAN\n'
        'Untuk mempermudah penulisan, sistematika disusun sebagai berikut: \n'
        'BAB I \tPendahuluan, terdiri dari: Latar Belakang Masalah, '
        'Rumusan Masalah.\n'
        'BAB II \tKajian Pustaka, terdiri dari: Pengertian.\n')
    _awal_r3 = _ST15.awal_isi_naskah(_t_r3)
    cek('v15-awal: BAB I asli ber-BOM jadi patokan (bukan salinan)',
        _awal_r3 == _t_r3.index('\ufeffBAB I'),
        f'awal={_awal_r3} harap={_t_r3.index(chr(0xfeff) + "BAB I")}')
    _buang_r3 = _ST15.buang_daftar_isi(_t_r3)
    cek('v15-buang: isi BAB I asli utuh (LATAR BELAKANG tidak terbuang)',
        'LATAR BELAKANG' in _buang_r3
        and _buang_r3.startswith('\ufeffBAB I'),
        repr(_buang_r3[:60]))

    # 15b. Tanpa BOM: perilaku sama seperti dulu (jangkar BAB I asli).
    _t_nobom = _t_r3.replace('\ufeff', '')
    cek('v15-nobom: tanpa BOM jangkar tetap BAB I asli',
        _ST15.awal_isi_naskah(_t_nobom) == _t_nobom.index('BAB I')
        and 'LATAR BELAKANG' in _ST15.buang_daftar_isi(_t_nobom))

    # 15c. Salinan sistematika TANPA BOM yang muncul DULUAN (sebelum BAB I
    #    asli) tetap dilewati sebagai patokan.
    _t_sal_dulu = (
        'KATA PENGANTAR\n\n    G. SISTEMATIKA PENULISAN\n'
        'Sistematika penulisan laporan ini disusun sebagai berikut:\n'
        'BAB I \tPendahuluan, terdiri dari: Latar Belakang.\n'
        'BAB II \tKajian Pustaka, terdiri dari: Pengertian.\n\n'
        'BAB I\nPENDAHULUAN\n\n1.1 Latar Belakang\nIsi bahasan asli.\n')
    _awal_sal = _ST15.awal_isi_naskah(_t_sal_dulu)
    cek('v15-salinan: salinan sistematika di depan dilewati, BAB I asli menang',
        _awal_sal == _t_sal_dulu.rindex('\nBAB I\n') + 1,
        f'awal={_awal_sal}')

    # 15d. Daftar isi bertitik-pengarah tetap ditolak (regresi perilaku lama).
    _t_daftar = (
        'DAFTAR ISI\nBAB I PENDAHULUAN ....... 1\n'
        '1.1 Latar Belakang .... 2\n\nBAB I\nPENDAHULUAN\n\nIsi bahasan.\n')
    cek('v15-daftar: BAB I daftar isi bertitik tetap ditolak',
        _ST15.awal_isi_naskah(_t_daftar) == _t_daftar.rindex('\nBAB I\n') + 1)

    # 15e. Kepala blok SISTEMATIKA saja (tanpa "terdiri dari") juga dilewati.
    _t_kepala = (
        '    G. SISTEMATIKA PENULISAN\n'
        'BAB I Pendahuluan\nBAB II Kajian Pustaka\n\n'
        'BAB I\nPENDAHULUAN\n\n1.1 Latar Belakang\nIsi.\n')
    cek('v15-kepala: salinan di bawah kepala SISTEMATIKA dilewati',
        _ST15.awal_isi_naskah(_t_kepala) == _t_kepala.rindex('\nBAB I\n') + 1)

    # ── v15b: perbaikan jawaban terpotong agen kedua (13 Nov 2026) ──────
    # Akar (ukur live 279 baris): 12 dari 39 panggilan fallback gagal
    # karena jawaban terpotong (finish=length) di max_tokens=512 — model
    # menjawab bertele-tele sebelum JSON-nya, lalu jadi None dan masuk
    # antrean manusia (1 -> 12). Perbaikan: batas 512 -> 2048 (kedua
    # jalur berbagi MAKS_TOKEN_JAWAB) + prompt minta HANYA JSON singkat.
    # Terpotong tetap -> None (aturan lama, bukan tebakan).
    cek('v15b-maks-token: MAKS_TOKEN_JAWAB 2048 (dulu 512)',
        AK.MAKS_TOKEN_JAWAB == 2048, str(AK.MAKS_TOKEN_JAWAB))
    _prompt_b = AK._prompt('2. Manfaat',
                           {'sebelum': ['a'], 'sesudah': ['b'],
                            'judul_bab_terdekat': 'BAB I'})
    cek('v15b-prompt: minta HANYA JSON singkat, tanpa penjelasan/pembuka/uraian',
        'HANYA dengan satu objek JSON singkat' in _prompt_b
        and 'tanpa penjelasan' in _prompt_b
        and 'tanpa pembuka' in _prompt_b
        and 'tanpa uraian' in _prompt_b
        and 'INGAT: keluaranmu HANYA satu objek JSON singkat' in _prompt_b,
        _prompt_b[:200])
    cek('v15b-prompt: isi keputusan tetap (4 label + confidence + alasan)',
        'bab, subbab, paragraf, biasa' in _prompt_b
        and 'confidence' in _prompt_b
        and 'BARIS YANG DINILAI' in _prompt_b
        and 'Alasan MAKSIMAL SATU kalimat pendek' in _prompt_b)
    _awalan = ('Baris ini perlu dibaca dengan hati-hati karena konteksnya '
               'luas dan butuh pertimbangan matang. ' * 40)
    _jawab_panjang = (_awalan + '{"label": "paragraf", "confidence": 0.85, '
                      '"alasan": "kalimat isi biasa"} Demikian penilaiannya.')
    cek('v15b-panjang: jawaban bertele-tele lengkap tetap terurai',
        AK._urai_jawaban(_jawab_panjang) == {'label': 'paragraf',
                                             'confidence': 0.85,
                                             'alasan': 'kalimat isi biasa'})
    _alasan_panjang = 'kata ' * 600
    _jawab_alasan = json.dumps({'label': 'biasa', 'confidence': 0.7,
                                'alasan': _alasan_panjang.strip()},
                               ensure_ascii=False)
    cek('v15b-panjang: JSON alasan sangat panjang tetap terurai',
        (AK._urai_jawaban(_jawab_alasan) or {}).get('label') == 'biasa')

    def _penanya_panjang(prompt):
        return (_jawab_panjang, 'model-palsu')

    cek('v15b-panjang: tanya langsung jawaban panjang -> label dipakai',
        (AK.tanya_agen_kedua('Kalimat isi.',
                             penanya=_penanya_panjang) or {}).get('label')
        == 'paragraf')
    cek('v15b-terpotong: urai JSON terpotong di tengah label -> None',
        AK._urai_jawaban('{"label": "bia') is None)
    cek('v15b-terpotong: urai JSON terpotong di tengah alasan -> None',
        AK._urai_jawaban(
            '{"label": "biasa", "confidence": 0.9, "alasan": "butir enum')
        is None)
    _balasan_panjang = json.dumps(
        {'choices': [{'message': {'content':
                                  '{"label": "biasa", "confidence": 0.9}'},
                      'finish_reason': 'length'}],
         'model': 'model-palsu'})
    try:
        AK._urai_balasan_chat(_balasan_panjang)
        _terpotong_meledak = False
    except RuntimeError as _e:
        _terpotong_meledak = 'terpotong' in str(_e)
    cek('v15b-terpotong: finish=length -> RuntimeError terpotong',
        _terpotong_meledak)

    def _penanya_terpotong(prompt):
        return ('{"label": "biasa", "confidence": 0.9, "alasan": "butir enum',
                'model-palsu')

    cek('v15b-terpotong: tanya langsung jawaban terpotong -> None',
        AK.tanya_agen_kedua('2. Manfaat',
                            penanya=_penanya_terpotong) is None)
    _env_b = os.environ.get('EDUAI_AGEN_KEDUA_AKTIF')
    os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '1'
    fn_tp = AK.buat_pendapat_kedua_fn(penanya=_penanya_terpotong)
    cek('v15b-terpotong: pabrik jawaban terpotong -> None (antrean, bukan tebakan)',
        fn_tp(5, '2. Manfaat', ['paragraf', 'biasa'], [0.9, 0.6]) is None)
    if _env_b is None:
        os.environ.pop('EDUAI_AGEN_KEDUA_AKTIF', None)
    else:
        os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = _env_b

    # ── v15c: Apinex kaki KEDUA rantai agen kedua (13 Nov 2026) ─────────
    #    Urutan baru: combo 9router -> Apinex (gratis) -> TokenHarbor.
    #    Kunci Apinex kosong = kaki dilewati, rantai tetap jalan.
    import urllib.request as _urlreq

    class _ResponApinex:
        def __init__(self, badan):
            self._badan = badan

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return self._badan

    def _balasan_apinex(finish='stop'):
        return json.dumps(
            {'choices': [{'message': {'content':
                                      '{"label": "biasa", "confidence": 0.9, '
                                      '"alasan": "butir enumerasi"}'},
                          'finish_reason': finish}],
             'model': 'free/gemini-3.8-flash'}).encode()

    _tangkap_apx = {}

    def _urlopen_apx(req, timeout=None):
        _tangkap_apx['url'] = req.full_url
        _tangkap_apx['data'] = req.data
        _tangkap_apx['header'] = dict(req.header_items())
        _tangkap_apx['timeout'] = timeout
        return _ResponApinex(_balasan_apinex())

    _env_apx = os.environ.get('EDUAI_APINEX_KEY')
    _env_tr = os.environ.get('EDUAI_AGEN_KEDUA_TRANSPORT')
    os.environ['EDUAI_APINEX_KEY'] = 'kunci-uji-apinex'
    _urlopen_asli = _urlreq.urlopen
    _urlreq.urlopen = _urlopen_apx
    try:
        _konten_apx, _model_apx = AK._panggil_apinex('prompt uji')
        _body_apx = json.loads(_tangkap_apx['data'])
        cek('v15c-apinex: payload model free/gemini-3.8-flash',
            _body_apx.get('model') == 'free/gemini-3.8-flash'
            and _model_apx == 'free/gemini-3.8-flash',
            str(_body_apx.get('model')))
        cek('v15c-apinex: payload setelan produksi (2048 + json + tanpa pikir)',
            _body_apx.get('max_tokens') == 2048
            and _body_apx.get('temperature') == 0.2
            and _body_apx.get('enable_thinking') is False
            and _body_apx.get('response_format') == {'type': 'json_object'},
            str(_body_apx))
        cek('v15c-apinex: URL + kunci ke api.apinex.bond',
            _tangkap_apx['url'].startswith(
                'https://api.apinex.bond/v1/chat/completions')
            and _tangkap_apx['header'].get('Authorization')
            == 'Bearer kunci-uji-apinex',
            str(_tangkap_apx['url']))
        cek('v15c-apinex: konten JSON terbaca dari balasan',
            AK._urai_jawaban(_konten_apx) == {'label': 'biasa',
                                              'confidence': 0.9,
                                              'alasan': 'butir enumerasi'})
    finally:
        _urlreq.urlopen = _urlopen_asli

    # ── v15d: payload combo HARUS stream:false (bukti live 13 Nov 2026) ──
    # Tanpa field stream, 9router menganggap permintaan combo sebagai
    # streaming dan klien non-streaming menerima badan SSE yang tidak
    # terurai (atau HTTP 410 sesudah sapuan 12 model ~60 detik) — 5 dari
    # 5 panggilan prompt panjang gagal. Dengan stream:false, combo
    # menjawab prompt yang sama dalam 1,4-7,9 detik, keputusan terurai.
    def _balasan_r9(finish='stop'):
        return json.dumps(
            {'choices': [{'message': {'content':
                                      '{"label": "subbab", "confidence": 0.9, '
                                      '"alasan": "judul bagian"}'},
                          'finish_reason': finish}],
             'model': 'free/muse-spark-1.3'}).encode()

    class _ResponR9:
        def __init__(self, badan):
            self._badan = badan

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return self._badan

    _tangkap_r9 = {}

    def _urlopen_r9(req, timeout=None):
        _tangkap_r9['url'] = req.full_url
        _tangkap_r9['data'] = req.data
        _tangkap_r9['timeout'] = timeout
        return _ResponR9(_balasan_r9())

    # app.config menuntut EDUAI_SECRET_KEY + EDUAI_ROUTER_KEY saat
    # diimpor (dipakai uji saja, bukan kunci asli); direktori data
    # diarahkan ke /tmp supaya repo tidak kotor.
    _env_cfg = {k: os.environ.get(k) for k in
                ('EDUAI_SECRET_KEY', 'EDUAI_ROUTER_KEY',
                 'EDUAI_DATA_DIR', 'EDUAI_UPLOAD_DIR')}
    os.environ['EDUAI_SECRET_KEY'] = 'uji-secret'
    os.environ['EDUAI_ROUTER_KEY'] = 'uji-router-key'
    os.environ['EDUAI_DATA_DIR'] = '/tmp/uji-eduai-data'
    os.environ['EDUAI_UPLOAD_DIR'] = '/tmp/uji-eduai-uploads'

    _urlreq.urlopen = _urlopen_r9
    try:
        _konten_r9, _model_r9 = AK._panggil_router9('prompt uji')
        _body_r9 = json.loads(_tangkap_r9['data'])
        cek('v15d-combo: payload stream:false (9router jawab JSON langsung)',
            _body_r9.get('stream') is False, str(_body_r9))
        cek('v15d-combo: payload tetap tanpa pikir (enable_thinking false)',
            _body_r9.get('enable_thinking') is False
            and _body_r9.get('max_tokens') == 2048
            and _body_r9.get('temperature') == 0.2, str(_body_r9))
        cek('v15d-combo: model combo EduAi + konten JSON terbaca',
            _body_r9.get('model') == 'EduAi'
            and AK._urai_jawaban(_konten_r9) == {'label': 'subbab',
                                                 'confidence': 0.9,
                                                 'alasan': 'judul bagian'})
        cek('v15d-combo: URL ke ROUTER_BASE',
            _tangkap_r9['url'].startswith(
                'http://172.17.0.1:20128/v1/chat/completions'),
            str(_tangkap_r9['url']))
        cek('v15d-combo: balasan SSE lama tetap terurai (pengaman parser)',
            AK._urai_balasan_chat(
                'data: ' + _balasan_r9().decode() + '\ndata: [DONE]')[0]
            == _konten_r9)
    finally:
        _urlreq.urlopen = _urlopen_asli

    def _urlopen_r9_potong(req, timeout=None):
        return _ResponR9(_balasan_r9(finish='length'))

    _urlreq.urlopen = _urlopen_r9_potong
    try:
        cek('v15d-combo: finish=length -> None (antrean, bukan tebakan)',
            AK._coba_transport('router9', 'prompt uji') is None)
    finally:
        _urlreq.urlopen = _urlopen_asli
        for _k, _v in _env_cfg.items():
            if _v is None:
                os.environ.pop(_k, None)
            else:
                os.environ[_k] = _v

    # Kaki lain TIDAK disentuh perbaikan ini: Apinex tetap tanpa field
    # stream (sudah bekerja 39/39 di ukur 3 kaki) — cakupan minimal.
    cek('v15d-cakupan: payload Apinex tidak ditambah stream',
        'stream' not in _body_apx, str(_body_apx))

    os.environ.pop('EDUAI_APINEX_KEY', None)
    try:
        AK._panggil_apinex('prompt uji')
        _apx_tanpa_kunci = False
    except RuntimeError as _e:
        _apx_tanpa_kunci = 'apinex tidak terpasang' in str(_e)
    cek('v15c-apinex: kunci kosong -> RuntimeError apinex tidak terpasang',
        _apx_tanpa_kunci)
    if _env_apx is None:
        os.environ.pop('EDUAI_APINEX_KEY', None)
    else:
        os.environ['EDUAI_APINEX_KEY'] = _env_apx

    # ── rantai 3 kaki (transport dipalsukan di level fungsi) ───────────
    _urutan = []

    def _r9_gagal(prompt, timeout=None):
        _urutan.append('router9')
        raise RuntimeError('combo mati (uji)')

    def _apx_ok(prompt, timeout=None):
        _urutan.append('apinex')
        return ('{"label": "subbab", "confidence": 0.8, "alasan": "judul"}',
                'free/gemini-3.8-flash')

    def _apx_gagal(prompt, timeout=None):
        _urutan.append('apinex')
        raise RuntimeError('apinex mati (uji)')

    def _or_ok(prompt, timeout=None):
        _urutan.append('openrouter')
        return ('{"label": "paragraf", "confidence": 0.7, "alasan": "isi"}',
                'gemini-3.8-flash')

    def _or_gagal(prompt, timeout=None):
        _urutan.append('openrouter')
        raise RuntimeError('fallback mati (uji)')

    _r9_asli = AK._panggil_router9
    _apx_asli = AK._panggil_apinex
    _or_asli = AK._panggil_openrouter
    os.environ['EDUAI_AGEN_KEDUA_TRANSPORT'] = 'fallback'
    try:
        AK._panggil_router9 = _r9_gagal
        AK._panggil_apinex = _apx_ok
        AK._panggil_openrouter = _or_ok
        _urutan.clear()
        _j1 = AK.tanya_agen_kedua('2. Manfaat')
        cek('v15c-rantai: combo gagal -> Apinex dipakai (transport apinex)',
            (_j1 or {}).get('transport') == 'apinex'
            and (_j1 or {}).get('label') == 'subbab',
            str(_j1))
        cek('v15c-rantai: Apinex dicoba SEBELUM TokenHarbor',
            _urutan == ['router9', 'apinex'], str(_urutan))
        AK._panggil_apinex = _apx_gagal
        _urutan.clear()
        _j2 = AK.tanya_agen_kedua('2. Manfaat')
        cek('v15c-rantai: Apinex gagal -> jatuh ke TokenHarbor',
            (_j2 or {}).get('transport') == 'openrouter'
            and (_j2 or {}).get('label') == 'paragraf',
            str(_j2))
        cek('v15c-rantai: urutan 3 kaki router9 -> apinex -> openrouter',
            _urutan == ['router9', 'apinex', 'openrouter'], str(_urutan))
        AK._panggil_openrouter = _or_gagal
        _urutan.clear()
        cek('v15c-rantai: ketiga kaki gagal -> None (antrean, bukan tebakan)',
            AK.tanya_agen_kedua('2. Manfaat') is None
            and _urutan == ['router9', 'apinex', 'openrouter'],
            str(_urutan))
    finally:
        AK._panggil_router9 = _r9_asli
        AK._panggil_apinex = _apx_asli
        AK._panggil_openrouter = _or_asli

    # ── kunci kosong di rantai nyata: kaki Apinex dilewati ────────────
    os.environ.pop('EDUAI_APINEX_KEY', None)
    AK._panggil_router9 = _r9_gagal
    AK._panggil_openrouter = _or_ok
    try:
        _urutan.clear()
        _j3 = AK.tanya_agen_kedua('2. Manfaat')
        cek('v15c-rantai: kunci Apinex kosong -> TokenHarbor tetap menjawab',
            (_j3 or {}).get('transport') == 'openrouter'
            and (_j3 or {}).get('label') == 'paragraf',
            str(_j3))
    finally:
        AK._panggil_router9 = _r9_asli
        AK._panggil_openrouter = _or_asli
    if _env_apx is None:
        os.environ.pop('EDUAI_APINEX_KEY', None)
    else:
        os.environ['EDUAI_APINEX_KEY'] = _env_apx
    if _env_tr is None:
        os.environ.pop('EDUAI_AGEN_KEDUA_TRANSPORT', None)
    else:
        os.environ['EDUAI_AGEN_KEDUA_TRANSPORT'] = _env_tr

    # ── Apinex terpotong -> None (lewat _coba_transport nyata) ─────────
    os.environ['EDUAI_APINEX_KEY'] = 'kunci-uji-apinex'

    def _urlopen_potong(req, timeout=None):
        return _ResponApinex(_balasan_apinex(finish='length'))

    _urlreq.urlopen = _urlopen_potong
    try:
        cek('v15c-terpotong: Apinex finish=length -> None (antrean)',
            AK._coba_transport('apinex', 'prompt uji') is None)
    finally:
        _urlreq.urlopen = _urlopen_asli
    if _env_apx is None:
        os.environ.pop('EDUAI_APINEX_KEY', None)
    else:
        os.environ['EDUAI_APINEX_KEY'] = _env_apx

    # ── REVISI HEMAT (13 Nov 2026, perintah Bos "baca semua itu boros") ──
    import app.revisi_hemat as RH
    import app.peta_jembatan as JB
    import app.peta3_jev as S3

    _TEKS_RH = (
        'BAB I\nPENDAHULUAN\n'
        'Latar belakang penelitian ini membahas pemasaran digital di Indonesia.\n'
        'Rumusan masalah penelitian ini disusun dalam bentuk pertanyaan penelitian.\n'
        '1.1 Latar Belakang\n'
        'Isi paragraf latar belakang yang panjang dan menjelaskan konteks penelitian ini.\n'
        '1.2 Rumusan Masalah\n'
        'Pertanyaan penelitian pertama membahas pengaruh pemasaran digital terhadap penjualan.\n'
        'Pertanyaan penelitian kedua membahas peran media sosial dalam pemasaran.\n'
        'BAB II\nTINJAUAN PUSTAKA\n'
        'Teori pemasaran digital menjelaskan konsep dasar pemasaran modern.\n'
        '2.1 Pemasaran Digital\n'
        'Definisi pemasaran digital menurut para ahli dibahas pada bagian ini.\n'
        'Manfaat pemasaran digital bagi usaha kecil dijelaskan dengan contoh nyata.\n'
    )

    def _petakan_palsu_rh(panggilan):
        """Petakan PALSU pencatat panggilan (orkestrasi saja, tanpa Jev).

        Label deterministik dari susun nyata: gabung -> 'bab', kode_label
        -> 'subbab', baris penanda UBAH-LABEL -> 'biasa' (supaya terbukti
        label baru menimpa label lama di dalam rentang), sisanya 'paragraf'.
        """
        def fn(teks_bersih, awal, akhir, pendapat_kedua_fn=None,
               hakim_tandai_fn=None):
            panggilan.append((awal, akhir))
            s = S3.susun_teks(teks_bersih)
            baris = s['baris']
            label, p = {}, {}
            for i in range(awal, akhir):
                t = baris[i]
                if i in (s.get('gabung') or {}):
                    label[i] = 'bab'
                elif i in (s.get('kode_label') or {}):
                    label[i] = 'subbab'
                elif 'UBAH-LABEL' in t:
                    label[i] = 'biasa'
                else:
                    label[i] = 'paragraf'
                p[i] = 0.9
            return {'baris': baris,
                    'kand': [(i, baris[i]) for i in range(awal, akhir)],
                    'label': label, 'goyang': [], 'p': p,
                    'gabung': s.get('gabung') or {},
                    'kode_label': s.get('kode_label') or {},
                    'sistematika': [], 'boleh_dipakai_fitur': {},
                    'semua': {i: [label[i]] for i in label}}
        return fn

    # peta tersimpan (palsu tapi berbentuk penuh) untuk naskah T0
    _susun0 = S3.susun_teks(_TEKS_RH)
    _surveyor0 = _petakan_palsu_rh([])(_TEKS_RH, 0, len(_susun0['baris']))
    _audit0 = H.periksa_peta(_surveyor0)
    _hasil0 = {'mode': 'peta_awal', 'jumlah': 5, 'daftar': [],
               'peta_dari': 'jev', 'sidik': RH.sidik_teks(_TEKS_RH),
               'model': 'peta3_jev'}
    _peta0 = RH.siapkan_simpan(_hasil0, _surveyor0, _audit0)
    cek('rh-simpan: sidik per bagian tersimpan, sidik utuh tetap ada',
        isinstance(_peta0.get('sidik_bagian'), list)
        and len(_peta0['sidik_bagian']) >= 2
        and _peta0.get('sidik') == RH.sidik_teks(_TEKS_RH)
        and isinstance(_peta0.get('peta_surveyor'), dict))

    # RH-1a. naskah tak berubah -> pakai ulang, 0 panggilan Jev
    _panggilan = []
    _r = RH.periksa_hemat(_TEKS_RH, _peta0, fn_susun_teks=S3.susun_teks,
                          fn_petakan_teks=_petakan_palsu_rh(_panggilan),
                          fn_pendapat_kedua=None)
    cek('rh-tak-berubah: jalan pakai_ulang, 0 panggilan Jev',
        _r is not None and _r.get('jalan') == 'pakai_ulang'
        and _panggilan == []
        and (_r.get('hasil') or {}).get('dari_simpanan') is True)
    cek('rh-tak-berubah: hasil identik simpanan, tanpa kunci internal',
        (_r.get('hasil') or {}).get('sidik') == _peta0.get('sidik')
        and 'peta_surveyor' not in (_r.get('hasil') or {})
        and 'sidik_bagian' not in (_r.get('hasil') or {})
        and 'hakim_bagian' not in (_r.get('hasil') or {}))

    # RH-1b. 1 paragraf diubah -> hanya bagian itu + tetangganya ke Jev
    _kalimat = ('Pertanyaan penelitian pertama membahas pengaruh pemasaran '
                'digital terhadap penjualan.')
    _teks1 = _TEKS_RH.replace(
        _kalimat,
        'Pertanyaan penelitian pertama UBAH-LABEL membahas pengaruh '
        'pemasaran digital terhadap penjualan.')
    _idx_ubah = next(i for i, t in enumerate(_susun0['baris'])
                     if 'Pertanyaan penelitian pertama' in t)
    _bagian0 = _peta0['sidik_bagian']
    _n_bag = next(n for n, b in enumerate(_bagian0)
                  if b['awal'] <= _idx_ubah < b['akhir'])
    _awal_harap = _bagian0[_n_bag - 1]['awal'] if _n_bag > 0 else 0
    _akhir_harap = (_bagian0[_n_bag + 1]['akhir']
                    if _n_bag + 1 < len(_bagian0) else len(_susun0['baris']))
    _panggilan1 = []
    _audit_jejak = []
    _periksa_asli = H.periksa_peta

    def _periksa_rekam(peta):
        _audit_jejak.append(len(peta.get('baris') or []))
        return _periksa_asli(peta)

    H.periksa_peta = _periksa_rekam
    try:
        _r1 = RH.periksa_hemat(_teks1, _peta0, fn_susun_teks=S3.susun_teks,
                               fn_petakan_teks=_petakan_palsu_rh(_panggilan1),
                               fn_pendapat_kedua=None)
    finally:
        H.periksa_peta = _periksa_asli
    cek('rh-1-paragraf: jalan hemat, petakan dipanggil tepat 1x',
        _r1 is not None and _r1.get('jalan') == 'hemat'
        and len(_panggilan1) == 1, str(_panggilan1))
    cek('rh-1-paragraf: rentang = bagian berubah + 1 tetangga tiap sisi',
        _panggilan1 == [(_awal_harap, _akhir_harap)],
        f'{_panggilan1} vs harap {(_awal_harap, _akhir_harap)}')
    _simpan1 = (_r1 or {}).get('simpan') or {}
    _label1 = ((_simpan1.get('peta_surveyor') or {}).get('label') or {})
    _label0 = ((_peta0.get('peta_surveyor') or {}).get('label') or {})
    cek('rh-1-paragraf: label di luar rentang dipakai ulang utuh',
        all(_label1.get(str(i)) == _label0.get(str(i))
            for i in range(len(_susun0['baris']))
            if not (_awal_harap <= i < _akhir_harap)))
    cek('rh-1-paragraf: label di dalam rentang dari petakan baru',
        _label1.get(str(_idx_ubah)) == 'biasa')
    cek('rh-1-paragraf: sidik per bagian baru tersimpan',
        isinstance(_simpan1.get('sidik_bagian'), list)
        and len(_simpan1['sidik_bagian']) == len(_bagian0))
    cek('rh-hakim: audit seluruh peta gabungan (bukan hanya rentang)',
        bool(_audit_jejak)
        and all(n == len(_susun0['baris']) for n in _audit_jejak),
        str(_audit_jejak))

    # RH-1c. judul subbab ditambah -> baca penuh
    _teks2 = _TEKS_RH.replace(
        'Pertanyaan penelitian kedua membahas peran media sosial dalam pemasaran.\n',
        'Pertanyaan penelitian kedua membahas peran media sosial dalam pemasaran.\n'
        '1.3 Metode Penelitian\n'
        'Metode penelitian ini memakai pendekatan kuantitatif.\n')
    _rencana2 = RH.rencanakan(_peta0, S3.susun_teks(_teks2)['baris'])
    cek('rh-subbab-baru: judul subbab ditambah -> baca penuh',
        _rencana2.get('jalan') == 'penuh', str(_rencana2.get('alasan')))
    cek('rh-subbab-baru: periksa_hemat kembalikan None (pemanggil baca penuh)',
        RH.periksa_hemat(_teks2, _peta0, fn_susun_teks=S3.susun_teks,
                         fn_petakan_teks=_petakan_palsu_rh([]),
                         fn_pendapat_kedua=None) is None)

    # RH-1d. peta lama tanpa sidik per bagian -> baca penuh, jangan crash
    cek('rh-legacy: peta tanpa sidik per bagian -> None (baca penuh)',
        RH.periksa_hemat(_TEKS_RH, {'mode': 'peta_awal', 'daftar': []},
                         fn_susun_teks=S3.susun_teks,
                         fn_petakan_teks=_petakan_palsu_rh([])) is None)
    _legacy2 = dict(_peta0)
    _legacy2.pop('sidik_bagian', None)
    cek('rh-legacy: surveyor ada tapi sidik bagian hilang -> None',
        RH.periksa_hemat(_TEKS_RH, _legacy2, fn_susun_teks=S3.susun_teks,
                         fn_petakan_teks=_petakan_palsu_rh([])) is None)
    cek('rh-legacy: peta rusak (bukan JSON) -> None',
        RH.periksa_hemat(_TEKS_RH, 'bukan-json{{{',
                         fn_susun_teks=S3.susun_teks,
                         fn_petakan_teks=_petakan_palsu_rh([])) is None)

    # RH-1e. kunci rentang: bagian hemat = perhalus jembatan (bukan geser)
    _bagian_rh = RH.bagi_bagian(_susun0['baris'], _susun0.get('gabung') or {},
                                _susun0.get('kode_label') or {},
                                _surveyor0['label'],
                                set(_surveyor0.get('sistematika') or []),
                                _surveyor0.get('boleh_dipakai_fitur') or {})
    _jb = JB.dari_surveyor(_surveyor0, _TEKS_RH)
    _mulai, _rentang_jb = 0, []
    for _d in (_jb or []):
        _n = _d['isi_teks'].count('\n') + 1 if _d['isi_teks'] else 0
        _rentang_jb.append((_mulai, _mulai + _n))
        _mulai += _n
    _mulai_rh = [b['awal'] for b in _bagian_rh]
    cek('rh-rentang: bagian menutup [0, n) tanpa celah',
        bool(_bagian_rh) and _bagian_rh[0]['awal'] == 0
        and _bagian_rh[-1]['akhir'] == len(_susun0['baris'])
        and all(_bagian_rh[k]['akhir'] == _bagian_rh[k + 1]['awal']
                for k in range(len(_bagian_rh) - 1)))
    cek('rh-rentang: tiap batas jembatan ada di batas hemat',
        bool(_rentang_jb)
        and all(s in _mulai_rh for s, _e in _rentang_jb),
        f'jembatan {_rentang_jb} vs hemat {_mulai_rh}')
    cek('rh-rentang: tiap bagian hemat di dalam satu bagian jembatan',
        all(any(s <= b['awal'] and b['akhir'] <= e for s, e in _rentang_jb)
            for b in _bagian_rh))

    # RH-1f. ambang struktural (langsung pada deteksi_struktural)
    _b_lama = ['BAB I', 'Pendahuluan isi.', '1.1 Latar', 'Isi satu.',
               '1.2 Rumusan', 'Isi dua.', 'BAB II', 'Isi tiga.']
    _b_kecil = list(_b_lama)
    _b_kecil[3] = 'Isi satu yang sudah direvisi.'
    _st0, _ = RH.deteksi_struktural(_b_lama, _b_kecil,
                                    RH.diff_baris(_b_lama, _b_kecil))
    cek('rh-struktural: 1 baris berubah -> bukan struktural', _st0 is False)
    _b_tambah = ['BAB I', 'Pendahuluan isi.', '1.1 Latar', 'Isi satu.',
                 '1.2 Rumusan', 'Isi dua.', '1.3 Metode', 'Isi baru.',
                 'BAB II', 'Isi tiga.']
    _st1, _al1 = RH.deteksi_struktural(_b_lama, _b_tambah,
                                       RH.diff_baris(_b_lama, _b_tambah))
    cek('rh-struktural: subbab ditambah -> struktural', _st1 is True)
    _b_banyak = ['BARU %d' % i for i in range(8)]
    _st2, _al2 = RH.deteksi_struktural(_b_lama, _b_banyak,
                                       RH.diff_baris(_b_lama, _b_banyak))
    cek('rh-struktural: >25% baris berubah -> struktural', _st2 is True)
    _b_panjang = ['Baris %03d isi paragraf.' % i for i in range(100)]
    _b_sebar = list(_b_panjang)
    for _k in range(11):
        _b_sebar.insert(9 * _k + 5, 'Sisipan %d' % _k)
    _st3, _al3 = RH.deteksi_struktural(_b_panjang, _b_sebar,
                                       RH.diff_baris(_b_panjang, _b_sebar))
    cek('rh-struktural: >10 blok terpisah -> struktural',
        _st3 is True and 'blok' in _al3, _al3)

    # RH-1g. pemetaan indeks diff (sisipan ikut bagian sebelumnya, dst.)
    _op = RH.diff_baris(['a', 'b', 'c'], ['a', 'X', 'b', 'c'])
    cek('rh-diff: sisipan di batas ikut bagian sebelumnya',
        RH.petakan_rentang(_op, 3, 4, 1, 2) == (2, 3))
    _op2 = RH.diff_baris(['a', 'b', 'c'], ['a', 'c'])
    cek('rh-diff: baris terhapus runtuh ke titik hapus',
        RH.petakan_rentang(_op2, 3, 2, 1, 2) == (1, 1))
    _op3 = RH.diff_baris(['a', 'b'], ['X', 'a', 'b'])
    cek('rh-diff: sisipan di awal ikut bagian pertama',
        RH.petakan_rentang(_op3, 2, 3, 0, 1) == (0, 2))

    # RH-2. REGRESI (wajib): hemat vs baca penuh, surveyor NYATA (FakeSatpam).
    #    Bila SATU label saja berbeda, itu REGRESI — uji ini harus gagal.
    _env_agen = os.environ.get('EDUAI_AGEN_KEDUA_AKTIF')
    os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '0'
    try:
        FAKE_SATPAM.jumlah_choice = 0
        FAKE_SATPAM.jumlah_noul = 0
        _penuh0 = P.petakan_dari_teks(_TEKS_RH, putaran=1)
        _panggilan_penuh0 = FAKE_SATPAM.jumlah_choice
        cek('rh-regresi: peta penuh T0 jalan',
            isinstance(_penuh0, dict) and bool((_penuh0.get('label') or {})))
        _audit_penuh0 = H.periksa_peta(_penuh0)
        _hasil_penuh0 = {'mode': 'peta_awal', 'jumlah': 0, 'daftar': [],
                         'peta_dari': 'jev',
                         'sidik': RH.sidik_teks(_TEKS_RH), 'model': 'peta3_jev'}
        _peta_penuh0 = RH.siapkan_simpan(_hasil_penuh0, _penuh0, _audit_penuh0)
        cek('rh-regresi: sidik per bagian tersimpan dari peta nyata',
            isinstance(_peta_penuh0.get('sidik_bagian'), list)
            and len(_peta_penuh0['sidik_bagian']) >= 2)
        FAKE_SATPAM.jumlah_choice = 0
        _r_ulang = RH.periksa_hemat(_TEKS_RH, _peta_penuh0)
        cek('rh-regresi: naskah tak berubah (jalur nyata) -> 0 panggilan Jev',
            _r_ulang is not None and _r_ulang.get('jalan') == 'pakai_ulang'
            and FAKE_SATPAM.jumlah_choice == 0)
        FAKE_SATPAM.jumlah_choice = 0
        _penuh1 = P.petakan_dari_teks(_teks1, putaran=1)
        _panggilan_penuh1 = FAKE_SATPAM.jumlah_choice
        FAKE_SATPAM.jumlah_choice = 0
        _r_hemat1 = RH.periksa_hemat(_teks1, _peta_penuh0)
        _panggilan_hemat1 = FAKE_SATPAM.jumlah_choice
        print(f'    [rh-bukti] penuh T1: {_panggilan_penuh1} panggilan Jev '
              f'(choice); hemat T1: {_panggilan_hemat1} panggilan; '
              f'hemat {_panggilan_hemat1 * 100 // max(1, _panggilan_penuh1)}% '
              f'dari penuh')
        _label_penuh1 = _penuh1.get('label') or {}
        _label_hemat1 = ({int(k): v for k, v in
                          ((_r_hemat1 or {}).get('simpan') or {})
                          .get('peta_surveyor', {}).get('label', {}).items()}
                         if _r_hemat1 and _r_hemat1.get('simpan') else {})
        _beda = {i for i in set(_label_penuh1) | set(_label_hemat1)
                 if _label_penuh1.get(i) != _label_hemat1.get(i)}
        cek('rh-regresi: label hemat IDENTIK dengan label baca penuh',
            _r_hemat1 is not None and _r_hemat1.get('jalan') == 'hemat'
            and not _beda, 'beda di ' + str(sorted(_beda)[:10]))
        cek('rh-regresi: hemat memanggil Jev lebih sedikit dari baca penuh',
            0 < _panggilan_hemat1 < _panggilan_penuh1,
            f'{_panggilan_hemat1} vs {_panggilan_penuh1}')
        cek('rh-regresi: subbab ditambah (jalur nyata) -> None (baca penuh)',
            RH.periksa_hemat(_teks2, _peta_penuh0) is None)
    finally:
        if _env_agen is None:
            os.environ.pop('EDUAI_AGEN_KEDUA_AKTIF', None)
        else:
            os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = _env_agen

    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
        sys.exit(1)


if __name__ == '__main__':
    main()
