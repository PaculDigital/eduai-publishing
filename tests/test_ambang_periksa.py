#!/usr/bin/env python3
"""Uji gerbang Periksa Struktur (15 Nov 2026): ambang, tombol, hemat, antrean.

Konvensi sama seperti tests/test_jev_hakim.py: skrip mandiri, jalankan
`python3 tests/test_ambang_periksa.py`, keluar 0 bila semua lulus.
Modul berat (app.ai, app.models) di-stub; modul yang diuji dimuat asli.

Yang diuji:
  1. normalisasi: titik/spasi/kapital saja bukan perubahan.
  2. ambang manual (>50 kata/bagian ATAU 5% bagian) dan otomatis (20%).
  3. keadaan tombol (belum/sudah/berubah).
  4. SATU garis awal (perintah Bos 08:41): manual + otomatis berbagi
     penghitung sejak pemeriksaan terakhir; tekan tombol ATAU jalan
     otomatis mengatur ulang; tidak ada perubahan yang diperiksa 2x.
  5. hemat: teks sama -> 'pakai_ulang', 0 panggilan Jev; 1 bagian berubah
     -> hanya bagian itu + tetangga yang dipetakan ulang.
  6. ringkas_peta + bangun_baris_antrean (murni).
"""
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LULUS = []
GAGAL = []


def cek(nama, benar):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama)


class _SatpamPalsu:
    def tanya_bebas_mutu(self, *a, **k):
        return {}
    def tanya(self, *a, **k):
        return {}


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
    sys.modules['app.satpam'] = _SatpamPalsu()
    state = types.ModuleType('app.state')
    state.buang_daftar_isi = lambda t: t
    state.title_for = lambda *a, **k: ''
    state.get_category_for = lambda *a, **k: ''
    sys.modules['app.state'] = state
    konversi = types.ModuleType('app.konversi')
    sys.modules['app.konversi'] = konversi


def _muat(nama_modul):
    import importlib
    return importlib.import_module(nama_modul)


# ── Pembantu naskah palsu ────────────────────────────────────────────────

def susun_palsu(teks):
    """Susun palsu: baris = baris tak kosong (tanpa Jev)."""
    return {'baris': [b for b in (teks or '').split('\n') if b.strip()],
            'kand': [], 'gabung': {}, 'kode_label': {},
            'sistematika': [], 'buang': []}


def buat_baris(n_bagian, baris_per_bagian=3, kata_per_baris=20):
    """Naskah palsu: 1 baris BAB + tiap bagian = judul subbab + paragraf.

    Tiap paragraf = 1 baris berisi `kata_per_baris` kata berbeda, supaya
    diff kata terukur dan diff baris tidak menyatu antar bagian.
    """
    lines = ['BAB I PENDAHULUAN']
    for s in range(n_bagian):
        lines.append(f'1.{s + 1} Judul Bagian {s + 1}')
        for p in range(baris_per_bagian):
            lines.append(' '.join(
                f'kata{s}_{p}_{j}' for j in range(kata_per_baris)))
    return lines


def surveyor_dari_baris(lines):
    label = {}
    for i, b in enumerate(lines):
        if b.startswith('BAB '):
            label[i] = 'bab'
        elif b.startswith('1.'):
            label[i] = 'subbab'
        else:
            label[i] = 'biasa'
    return {'baris': list(lines), 'label': label, 'goyang': [], 'p': {},
            'gabung': {}, 'kode_label': {}, 'sistematika': [],
            'boleh_dipakai_fitur': {}}


def peta_tersimpan_dari_baris(lines, rh):
    surv = surveyor_dari_baris(lines)
    hasil = {'ok': True, 'gratis': True, 'mode': 'peta_awal', 'jumlah': 1,
             'daftar': [], 'diam': False, 'pesan': '', 'peta_dari': 'jev',
             'peta_alasan': '', 'bab_terdeteksi': [], 'hakim': {}}
    return rh.siapkan_simpan(hasil, surv, {'bagian': []})


def sidik(teks):
    return hashlib.sha256(teks.encode('utf-8')).hexdigest()


def ubah_baris(lines, idx, kata_baru):
    out = list(lines)
    out[idx] = kata_baru
    return out


def main():
    _stub_app()
    amb = _muat('app.ambang_periksa')
    st = _muat('app.struktur')
    rh = _muat('app.revisi_hemat')
    an = _muat('app.antrean')
    import app.hakim_peta as H
    H._TANYA_FN = lambda bahan, tanya: {k: {'noul': 0.9} for k in tanya}

    # ── 1. NORMALISASI ──────────────────────────────────────────────────
    cek('normalisasi: titik di akhir bukan perubahan',
        amb.normalisasi_teks('Bab 5.') == amb.normalisasi_teks('Bab 5'))
    cek('normalisasi: spasi ganda + kapital bukan perubahan',
        amb.normalisasi_teks('Saya,  pergi.') ==
        amb.normalisasi_teks('saya pergi'))
    cek('normalisasi: kata berbeda tetap terlihat',
        amb.normalisasi_teks('saya pergi') !=
        amb.normalisasi_teks('saya pulang'))

    # ── 2. AMBANG (40 bagian: 1 BAB + 39 subbab... pakai 40 subbab) ─────
    #    total bagian = 1 (BAB) + 40 (subbab) = 41.
    n = 40
    lines = buat_baris(n)
    teks = '\n'.join(lines)
    peta = peta_tersimpan_dari_baris(lines, rh)
    total = 1 + n

    # 2a. tambah titik saja -> 0 kata, tombol tetap nonaktif, 0 panggilan.
    t_titik = teks + '.'
    d = amb.bandingkan_perubahan(peta, t_titik, susun_palsu)
    cek('ambang: tambah titik saja -> tidak berarti, tidak besar',
        not d['berubah_berarti'] and not d['berubah_besar']
        and d['kata_berubah'] == 0 and d['bagian_berubah'] == 0)

    # 2b. ubah 3 kata di 1 baris paragraf bagian ke-2 (dari 41 bagian).
    ubah3 = ubah_baris(lines, 6, ' '.join(
        ['kata_baru_a', 'kata_baru_b', 'kata_baru_c']
        + lines[6].split()[3:]))
    d = amb.bandingkan_perubahan(peta, '\n'.join(ubah3), susun_palsu)
    cek('ambang: 3 kata di 1/41 bagian -> tidak berarti, tidak besar',
        not d['berubah_berarti'] and not d['berubah_besar']
        and d['kata_berubah'] == 6 and d['bagian_berubah'] == 1)

    # 2c. ubah 1 paragraf penuh (60 kata) di 1 bagian -> > 50 kata.
    ubah60 = list(lines)
    for p in range(3):
        idx = 2 + p  # 3 baris paragraf bagian pertama (subbab 1.1)
        ubah60[idx] = ' '.join(f'ganti1_{p}_{j}' for j in range(20))
    d = amb.bandingkan_perubahan(peta, '\n'.join(ubah60), susun_palsu)
    cek('ambang: 1 bagian diganti penuh (60+60 kata) -> berarti, bukan besar',
        d['berubah_berarti'] and not d['berubah_besar']
        and d['kata_maks_per_bagian'] == 120 and d['bagian_berubah'] == 1)

    # 2d. ubah 1 baris (20 kata) di 2 bagian (2/41 = 4,9% < 5%) -> belum.
    ubah2 = list(lines)
    for s in (0, 1):
        idx = 2 + s * 4  # baris paragraf pertama tiap bagian
        ubah2[idx] = ' '.join(f'ganti{s}_{j}' for j in range(20))
    d = amb.bandingkan_perubahan(peta, '\n'.join(ubah2), susun_palsu)
    cek('ambang: 2/41 bagian (4,9%), 20 kata diganti/bagian -> belum berarti',
        not d['berubah_berarti'] and d['bagian_berubah'] == 2
        and d['kata_maks_per_bagian'] == 40)

    # 2e. ubah 1 baris (20 kata) di 3 bagian (3/41 = 7,3% >= 5%) -> berarti.
    ubah3b = list(ubah2)
    ubah3b[2 + 2 * 4] = ' '.join(f'ganti2_{j}' for j in range(20))
    d = amb.bandingkan_perubahan(peta, '\n'.join(ubah3b), susun_palsu)
    cek('ambang: 3/41 bagian (7,3%), 20 kata diganti/bagian -> berarti, bukan besar',
        d['berubah_berarti'] and not d['berubah_besar']
        and d['bagian_berubah'] == 3 and d['kata_maks_per_bagian'] == 40)

    # 2f. ubah 1 baris (20 kata) di 10 bagian (10/41 = 24% >= 20%) -> besar.
    ubah10 = list(lines)
    for s in range(10):
        idx = 2 + s * 4
        ubah10[idx] = ' '.join(f'ganti{s}_{j}' for j in range(20))
    d = amb.bandingkan_perubahan(peta, '\n'.join(ubah10), susun_palsu)
    cek('ambang: 10/41 bagian (24%) -> besar (otomatis)',
        d['berubah_berarti'] and d['berubah_besar']
        and d['bagian_berubah'] == 10 and d['kata_maks_per_bagian'] == 40)

    # 2g. konstanta: otomatis HARUS lebih besar dari manual.
    cek('ambang: otomatis (20%) > manual (5%)',
        amb.AMBANG_PERIKSA_OTOMATIS['persen_bagian'] >
        amb.AMBANG_PERIKSA_ULANG['persen_bagian'])
    cek('ambang: nilai manual = 50 kata / 5%',
        amb.AMBANG_PERIKSA_ULANG == {'kata_per_bagian': 50,
                                     'persen_bagian': 0.05})
    cek('ambang: nilai otomatis = 20%',
        amb.AMBANG_PERIKSA_OTOMATIS == {'persen_bagian': 0.20})

    # ── 3. KEADAAN TOMBOL ───────────────────────────────────────────────
    cek('tombol: belum pernah -> aktif "Periksa Struktur"',
        st.keadaan_tombol(False, False) ==
        {'keadaan': 'belum', 'aktif': True, 'label': 'Periksa Struktur'})
    cek('tombol: sudah + tanpa perubahan -> nonaktif "Sudah Diperiksa"',
        st.keadaan_tombol(True, False) ==
        {'keadaan': 'sudah', 'aktif': False, 'label': 'Sudah Diperiksa'})
    cek('tombol: sudah + berubah berarti -> aktif "Periksa Lagi"',
        st.keadaan_tombol(True, True) ==
        {'keadaan': 'berubah', 'aktif': True, 'label': 'Periksa Lagi'})

    # ── 4. SATU GARIS AWAL (skenario ujung-ke-ujung, perintah Bos 08:41) ─
    #    Baseline = peta + sidik saat pemeriksaan terakhir. "Tekan tombol"
    #    dan "jalan otomatis" sama-sama memperbarui baseline itu.
    g = st.nilai_gerbang(peta_json=None, peta_sidik='', sidik_kini=sidik(teks),
                         teks_kini_bersih=teks, fn_susun_teks=susun_palsu)
    cek('garis awal: tanpa peta -> keadaan belum, bisa periksa',
        g['keadaan'] == 'belum' and g['bisa_periksa'] and not g['otomatis'])
    g = st.nilai_gerbang(peta_json=peta, peta_sidik=sidik(teks),
                         sidik_kini=sidik(teks), teks_kini_bersih=teks,
                         fn_susun_teks=susun_palsu)
    cek('garis awal: sidik sama -> sudah, tombol nonaktif, 0 panggilan',
        g['keadaan'] == 'sudah' and not g['bisa_periksa']
        and not g['otomatis'])
    # Tekan tombol (simulasi: baseline diperbarui ke teks baru) lalu ubah 24%.
    teks_baru = '\n'.join(ubah10)
    peta_baru = peta_tersimpan_dari_baris(ubah10, rh)
    g = st.nilai_gerbang(peta_json=peta, peta_sidik=sidik(teks),
                         sidik_kini=sidik(teks_baru),
                         teks_kini_bersih=teks_baru,
                         fn_susun_teks=susun_palsu)
    cek('garis awal: ubah 25% -> berubah + otomatis jalan',
        g['keadaan'] == 'berubah' and g['bisa_periksa'] and g['otomatis'])
    # Jalan otomatis (simulasi: baseline diperbarui) -> diam lagi.
    g = st.nilai_gerbang(peta_json=peta_baru, peta_sidik=sidik(teks_baru),
                         sidik_kini=sidik(teks_baru),
                         teks_kini_bersih=teks_baru,
                         fn_susun_teks=susun_palsu)
    cek('garis awal: sesudah otomatis -> sudah, otomatis diam, tombol nonaktif',
        g['keadaan'] == 'sudah' and not g['bisa_periksa']
        and not g['otomatis'])
    # Ubah sedikit di bawah ambang kecil -> tetap nonaktif.
    teks_kecil = teks_baru + '.'
    g = st.nilai_gerbang(peta_json=peta_baru, peta_sidik=sidik(teks_baru),
                         sidik_kini=sidik(teks_kecil),
                         teks_kini_bersih=teks_kecil,
                         fn_susun_teks=susun_palsu)
    cek('garis awal: ubah titik sesudah otomatis -> tetap sudah, 0 panggilan',
        g['keadaan'] == 'sudah' and not g['bisa_periksa']
        and not g['otomatis'])
    # Tanpa perubahan baru sesudah tekan tombol manual -> otomatis diam.
    g = st.nilai_gerbang(peta_json=peta_baru, peta_sidik=sidik(teks_baru),
                         sidik_kini=sidik(teks_baru),
                         teks_kini_bersih=teks_baru,
                         fn_susun_teks=susun_palsu)
    cek('garis awal: tanpa perubahan baru -> otomatis tidak jalan 2x',
        not g['otomatis'] and g['keadaan'] == 'sudah')

    # ── 5. HEMAT (hitung panggilan Jev) ─────────────────────────────────
    kecil = buat_baris(8)
    teks_kecil2 = '\n'.join(kecil)
    peta_kecil = peta_tersimpan_dari_baris(kecil, rh)
    panggilan = []

    def petakan_palsu(teks_bersih, awal, akhir, pendapat_kedua_fn=None,
                      hakim_tandai_fn=None):
        panggilan.append((awal, akhir))
        label = {str(i): 'biasa' for i in range(awal, akhir)}
        return {'label': label, 'goyang': [], 'p': {}, 'semua': {}}

    h = rh.periksa_hemat(teks_kecil2, peta_kecil, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    cek('hemat: teks sama -> pakai_ulang, 0 panggilan Jev',
        h is not None and h.get('jalan') == 'pakai_ulang'
        and len(panggilan) == 0)
    # Ubah 1 baris paragraf di bagian tengah (baris 14 = paragraf bagian 4).
    ubah1 = list(kecil)
    ubah1[14] = ' '.join(f'baru14_{j}' for j in range(20))
    panggilan.clear()
    h = rh.periksa_hemat('\n'.join(ubah1), peta_kecil, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    ok_hemat = h is not None and h.get('jalan') == 'hemat'
    cek('hemat: 1 bagian berubah -> jalan hemat, Jev dipanggil 1x',
        ok_hemat and len(panggilan) == 1)
    if ok_hemat and panggilan:
        awal, akhir = panggilan[0]
        cek('hemat: rentang mencakup baris yang berubah saja + tetangga',
            awal <= 14 < akhir and (akhir - awal) < len(kecil)
            and akhir - awal <= 12)
        cek('hemat: hasil menyimpan peta baru + sidik diperbarui',
            bool(h.get('simpan')) and
            h['simpan'].get('sidik_bagian'))

    # ── 6. RINGKAS PETA + ANTREAN (murni) ───────────────────────────────
    peta_tampil = {
        'peta_surveyor': {
            'baris': ['BAB I PENDAHULUAN', 'Isi pendahuluan.',
                      '1.1 Latar Belakang', 'Isi latar.',
                      'BAB II TINJAUAN PUSTAKA'],
            'label': {'0': 'bab', '1': 'paragraf', '2': 'subbab',
                      '3': 'paragraf', '4': 'bab'}},
        'hakim': {'jumlah_ragu': 1, 'jumlah_curiga': 0}}
    r = st.ringkas_peta(peta_tampil, menunggu_idx={2})
    cek('ringkas: pohon bab/subbab terbentuk',
        len(r['bab']) == 2 and len(r['bab'][0]['subbab']) == 1
        and r['bab'][0]['subbab'][0]['teks'] == '1.1 Latar Belakang')
    cek('ringkas: baris menunggu ditandai sedang diperiksa',
        r['bab'][0]['subbab'][0]['diperiksa'] is False
        and r['jumlah_menunggu'] == 1)
    cek('ringkas: peta kosong tidak meledak',
        st.ringkas_peta(None)['bab'] == [])

    audit = [
        {'i': 0, 'label': 'bab', 'status': 'sepakat', 'alasan': []},
        {'i': 2, 'label': 'subbab', 'status': 'ragu',
         'alasan': ['judul meragukan']},
        {'i': 4, 'label': 'bab', 'status': 'curiga',
         'alasan': ['bukan judul bab']} ]
    baris = ['BAB I PENDAHULUAN', 'Isi.', '1.1 Latar Belakang', 'Isi.',
             'BAB II TINJAUAN PUSTAKA']
    label_akhir = {0: 'bab', 2: 'subbab', 4: 'bab'}
    rows = an.bangun_baris_antrean(
        audit_bagian=audit, baris=baris, label_akhir=label_akhir,
        file_id=81, user_id=7, peta_sidik='abc123')
    cek('antrean: hanya ragu/curiga masuk (2 dari 3)',
        len(rows) == 2 and {r['baris_idx'] for r in rows} == {2, 4})
    cek('antrean: tetangga atas/bawah terisi',
        rows[0]['tetangga']['atas'] == 'Isi.'
        and rows[0]['tetangga']['bawah'] == 'Isi.')
    cek('antrean: label Jev + label akhir + alasan terekam',
        rows[0]['label_jev'] == 'subbab' and rows[0]['label_akhir'] == 'subbab'
        and rows[0]['alasan'] == ['judul meragukan']
        and rows[0]['status_hakim'] == 'ragu')
    cek('antrean: keputusan sah = bab/subbab/paragraf/biasa/lewati',
        an.KEPUTUSAN_SAH == ('bab', 'subbab', 'paragraf', 'biasa', 'lewati'))

    print(f'\n{len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL:')
        for g in GAGAL:
            print('  - ' + g)
        sys.exit(1)


if __name__ == '__main__':
    main()
