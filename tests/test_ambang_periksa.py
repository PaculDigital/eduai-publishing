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
  5. hemat: teks sama -> 'pakai_ulang', 0 panggilan Jev; ganti kata di
     paragraf panjang -> saringan lewati Jev (0 panggilan); judul diubah
     -> saringan menolak, Jev jalan.
  6. ringkas_peta + bangun_baris_antrean (murni).
  7. struktural kecil vs besar (optimasi 15 Nov 2026): tambah 1 subbab
     -> hemat + otomatis MATI; tambah 5 subbab / >25% baris -> penuh.
  8. saringan deterministik + audit tunggal: ganti kata saja -> Jev 0x,
     tanya Hakim 0x, agen kedua 0; hemat non-saringan -> audit 1x.
  9. batas laju otomatis 24 jam (boleh_otomatis_jalan).
  10. fail-open perbandingan: gagal membandingkan -> tombol aktif,
      otomatis tetap mati.
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


def peta_dengan_audit(lines, rh):
    """Peta tersimpan DENGAN jejak audit Hakim (seperti produksi): semua
    judul berlabel 'sepakat', supaya jalur lewati-Jev bisa memakai ulang
    audit lama (tanpa jejak, audit penuh jalan sebagai cadangan)."""
    surv = surveyor_dari_baris(lines)
    bagian = [{'i': i, 'label': lab, 'judul': lines[i][:60], 'p_info': None,
               'status': 'sepakat', 'alasan': []}
              for i, lab in sorted(surv['label'].items())
              if lab in ('bab', 'subbab')]
    audit = {'ok': True, 'keputusan': 'lolos', 'bagian': bagian,
             'jumlah_sepakat': len(bagian), 'jumlah_ragu': 0,
             'jumlah_curiga': 0, 'jumlah_belum': 0, 'alasan': 'audit uji'}
    hasil = {'ok': True, 'gratis': True, 'mode': 'peta_awal', 'jumlah': 1,
             'daftar': [], 'diam': False, 'pesan': '', 'peta_dari': 'jev',
             'peta_alasan': '', 'bab_terdeteksi': [],
             'hakim': {'jumlah_sepakat': len(bagian), 'jumlah_ragu': 0,
                       'jumlah_curiga': 0, 'jumlah_belum': 0,
                       'alasan': 'audit uji', 'bagian_curiga': []}}
    return rh.siapkan_simpan(hasil, surv, audit)


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
    # Pencatat panggilan tanya-Jev Hakim (untuk uji audit tunggal + lewati).
    tanya_jml = []
    _tanya_asli = H._TANYA_FN

    def _tanya_hitung(bahan, tanya):
        tanya_jml.append(len(tanya))
        return _tanya_asli(bahan, tanya)

    H._TANYA_FN = _tanya_hitung

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
        # Palsu yang REALISTIS: judul tetap berlabel judul (seperti
        # pipeline asli: kode_label + Jev melabel judul dengan benar),
        # paragraf 'biasa'. Palsu yang mengembalikan 'biasa' untuk semua
        # baris merusak peta gabungan (BAB hilang -> subbab jadi yatim).
        baris_teks = [b for b in (teks_bersih or '').split('\n')
                      if b.strip()]
        label = {}
        for i in range(awal, akhir):
            t = baris_teks[i] if 0 <= i < len(baris_teks) else ''
            if t.startswith('BAB '):
                label[str(i)] = 'bab'
            elif t.split(' ')[0][0:1].isdigit() \
                    and '.' in t.split(' ')[0]:
                label[str(i)] = 'subbab'
            else:
                label[str(i)] = 'biasa'
        return {'label': label, 'goyang': [], 'p': {}, 'semua': {}}

    h = rh.periksa_hemat(teks_kecil2, peta_kecil, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    cek('hemat: teks sama -> pakai_ulang, 0 panggilan Jev',
        h is not None and h.get('jalan') == 'pakai_ulang'
        and len(panggilan) == 0)
    # Ubah 1 baris paragraf di bagian tengah (baris 14 = paragraf bagian 4).
    # (15 Nov 2026, optimasi) Ganti kata di dalam paragraf PANJANG tidak
    # bisa mengubah label -> saringan deterministik melewati Jev (0
    # panggilan), label lama dipakai ulang. Dulu: Jev dipanggil 1x.
    ubah1 = list(kecil)
    ubah1[14] = ' '.join(f'baru14_{j}' for j in range(20))
    panggilan.clear()
    h = rh.periksa_hemat('\n'.join(ubah1), peta_kecil, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    ok_hemat = h is not None and h.get('jalan') == 'hemat'
    cek('hemat: ganti kata di paragraf panjang -> jalan hemat, Jev 0x (saringan)',
        ok_hemat and len(panggilan) == 0
        and (h.get('hasil') or {}).get('revisi_hemat', {}).get('lewati_jev')
        is True)
    if ok_hemat:
        label_lama = peta_kecil.get('peta_surveyor', {}).get('label') or {}
        label_baru = (h.get('simpan') or {}).get(
            'peta_surveyor', {}).get('label') or {}
        cek('hemat: label sesudah saringan identik dengan label lama',
            label_baru == label_lama)
        cek('hemat: hasil menyimpan peta baru + sidik diperbarui',
            bool(h.get('simpan')) and
            h['simpan'].get('sidik_bagian'))
    # Ubah JUDUL subbab (baris 13 = '1.4 ...', label lama 'subbab'):
    # saringan MENOLAK (judul diedit -> label bisa berubah) -> Jev jalan.
    ubah_judul = list(kecil)
    ubah_judul[13] = '1.4 Judul Bagian Empat'
    panggilan.clear()
    h = rh.periksa_hemat('\n'.join(ubah_judul), peta_kecil, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    ok_hemat = h is not None and h.get('jalan') == 'hemat'
    cek('hemat: judul subbab diubah -> saringan menolak, Jev dipanggil 1x',
        ok_hemat and len(panggilan) == 1)
    if ok_hemat and panggilan:
        awal, akhir = panggilan[0]
        # Judul di awal bagian: baris pengganti ikut rentang bagian
        # SEBELUMNYA juga (peta_posisi: baris lama yang diganti runtuh ke
        # titik sisipan) -> 2 bagian berubah + tetangga = 16 baris.
        cek('hemat: rentang mencakup baris yang berubah saja + tetangga',
            (awal, akhir) == (5, 21) and (akhir - awal) < len(kecil))

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

    # ── 7. STRUKTURAL KECIL vs BESAR (15 Nov 2026, optimasi) ────────────
    #    Tambah 1 subbab dulu memaksa baca penuh (~22 panggilan Jev) +
    #    otomatis ikut jalan. Sekarang: kecil -> hemat, otomatis MATI,
    #    tombol manual yang memutuskan.
    lines40 = buat_baris(40)
    teks40 = '\n'.join(lines40)
    peta40 = peta_tersimpan_dari_baris(lines40, rh)
    # 7a. tambah 1 subbab di akhir (1.41 + 1 paragraf panjang).
    tambah1 = list(lines40) + [
        '1.41 Judul Bagian Baru',
        ' '.join(f'baru41_{j}' for j in range(20))]
    susun_t1 = susun_palsu('\n'.join(tambah1))
    renc = rh.rencanakan(peta40, susun_t1['baris'])
    cek('struktural kecil: tambah 1 subbab -> jalan hemat, bukan penuh',
        renc.get('jalan') == 'hemat' and renc.get('struktural_kecil') is True)
    d = amb.bandingkan_perubahan(peta40, '\n'.join(tambah1), susun_palsu)
    cek('struktural kecil: tombol aktif, otomatis MATI',
        d['berubah_berarti'] and not d['berubah_besar']
        and d.get('otomatis') is False and d.get('struktural_kecil') is True)
    g = st.nilai_gerbang(peta_json=peta40, peta_sidik=sidik(teks40),
                         sidik_kini=sidik('\n'.join(tambah1)),
                         teks_kini_bersih='\n'.join(tambah1),
                         fn_susun_teks=susun_palsu)
    cek('struktural kecil: gerbang bisa periksa, otomatis False',
        g['bisa_periksa'] and not g['otomatis'])
    panggilan.clear()
    h = rh.periksa_hemat('\n'.join(tambah1), peta40, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    cek('struktural kecil: hemat, Jev dipanggil 1x (bukan baca penuh ~22x)',
        h is not None and h.get('jalan') == 'hemat'
        and len(panggilan) == 1)
    # 7b. tambah 5 subbab sekaligus (>3 judul) -> BESAR -> baca penuh.
    tambah5 = list(lines40)
    for s in range(41, 46):
        tambah5 += [f'1.{s} Judul Bagian Baru {s}',
                    ' '.join(f'baru{s}_{j}' for j in range(20))]
    susun_t5 = susun_palsu('\n'.join(tambah5))
    renc = rh.rencanakan(peta40, susun_t5['baris'])
    cek('struktural besar: tambah 5 subbab -> jalan penuh',
        renc.get('jalan') == 'penuh')
    d = amb.bandingkan_perubahan(peta40, '\n'.join(tambah5), susun_palsu)
    cek('struktural besar: vonis besar tapi otomatis tetap MATI',
        d['berubah_besar'] and d.get('otomatis') is False
        and d.get('struktural') is True)
    cek('struktural besar: perlu_periksa_otomatis False',
        amb.perlu_periksa_otomatis(
            peta40, '\n'.join(tambah5), susun_palsu)[0] is False)
    g = st.nilai_gerbang(peta_json=peta40, peta_sidik=sidik(teks40),
                         sidik_kini=sidik('\n'.join(tambah5)),
                         teks_kini_bersih='\n'.join(tambah5),
                         fn_susun_teks=susun_palsu)
    cek('struktural besar: tombol aktif (manual boleh), otomatis False',
        g['bisa_periksa'] and not g['otomatis'])
    # 7c. ubah >25% baris (tulis ulang 50 dari 161 baris) -> penuh.
    ubah_banyak = list(lines40)
    for i in range(2, 52):
        ubah_banyak[i] = ' '.join(f'rombak{i}_{j}' for j in range(20))
    susun_b = susun_palsu('\n'.join(ubah_banyak))
    renc = rh.rencanakan(peta40, susun_b['baris'])
    cek('struktural besar: >25% baris berubah -> jalan penuh',
        renc.get('jalan') == 'penuh')

    # ── 8. SARINGAN DETERMINISTIK + AUDIT TUNGGAL (15 Nov 2026) ─────────
    #    Fixture 8 bagian dengan SATU judul panjang (120-300 kar) supaya
    #    Hakim bertanya ke Jev — tanpa itu, tanya-Jev Hakim 0 dan uji
    #    audit-tunggal tidak bisa membedakan 1x vs 2x.
    lines8 = buat_baris(8)
    judul_panjang = ('1.3 Latar Belakang Masalah Penelitian tentang '
                     'Pengaruh Media Sosial terhadap Minat Beli Konsumen '
                     'di Kalangan Mahasiswa Manajemen Universitas Pelita '
                     'Bangsa')
    lines8[9] = judul_panjang
    cek('saringan: judul panjang 120-300 kar (Hakim bertanya ke Jev)',
        120 < len(judul_panjang) <= 300)
    peta8 = peta_dengan_audit(lines8, rh)
    # 8a. ganti kata di 1 paragraf panjang -> 0 Jev, 0 tanya-Hakim.
    ubah_p = list(lines8)
    ubah_p[14] = ' '.join(f'baru14_{j}' for j in range(20))
    panggilan.clear()
    tanya_jml.clear()
    h = rh.periksa_hemat('\n'.join(ubah_p), peta8, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    ok8 = h is not None and h.get('jalan') == 'hemat'
    cek('saringan: ganti kata saja -> Jev 0x, tanya Hakim 0x, agen kedua 0',
        ok8 and len(panggilan) == 0 and len(tanya_jml) == 0
        and (h.get('hasil') or {}).get('revisi_hemat', {}).get(
            'agen_kedua_jml') == 0
        and (h.get('hasil') or {}).get('revisi_hemat', {}).get(
            'lewati_jev') is True)
    if ok8:
        cek('saringan: jumlah Hakim dipakai ulang dari audit lama',
            (h.get('hasil') or {}).get('hakim', {}).get('jumlah_sepakat')
            == 9)
        label_lama = peta8.get('peta_surveyor', {}).get('label') or {}
        label_baru = (h.get('simpan') or {}).get(
            'peta_surveyor', {}).get('label') or {}
        cek('saringan: label sesudah lewati identik dengan label lama',
            label_baru == label_lama)
    # 8b. audit penuh langsung pada peta gabungan bertanya 1x (pembanding:
    #     tanpa saringan, Hakim bertanya untuk judul panjang itu).
    tanya_jml.clear()
    _surv8 = {'baris': list(lines8),
              'label': {i: ('bab' if b.startswith('BAB ') else
                            'subbab' if b.split(' ')[0][0].isdigit() else
                            'biasa')
                        for i, b in enumerate(lines8)},
              'goyang': [], 'p': {}, 'gabung': {}, 'sistematika': [],
              'boleh_dipakai_fitur': {}}
    _aud = H.periksa_peta(_surv8)
    cek('saringan: audit penuh bertanya Jev 1x untuk judul panjang',
        len(tanya_jml) == 1 and _aud.get('ok') is True)
    # 8c. hemat NON-saringan (ubah judul) -> audit jalan SEKALI (dulu 2x:
    #     audit + tandai_ragu_curiga).
    ubah_j = list(lines8)
    ubah_j[5] = '1.2 Judul Bagian Dua'
    panggilan.clear()
    tanya_jml.clear()
    h = rh.periksa_hemat('\n'.join(ubah_j), peta8, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    cek('saringan: hemat non-saringan -> Jev 1x, tanya Hakim 1x (bukan 2x)',
        h is not None and h.get('jalan') == 'hemat'
        and len(panggilan) == 1 and len(tanya_jml) == 1)
    # 8d. tambah 1 baris paragraf baru (panjang) -> saringan menolak.
    tambah_baris = list(lines8)
    tambah_baris.insert(
        15, ' '.join(f'sisip15_{j}' for j in range(20)))
    panggilan.clear()
    h = rh.periksa_hemat('\n'.join(tambah_baris), peta8, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    cek('saringan: tambah baris -> saringan menolak, Jev dipanggil 1x',
        h is not None and h.get('jalan') == 'hemat'
        and len(panggilan) == 1)
    # 8e. paragraf dipendekkan (20 kata -> 3 kata) -> saringan menolak.
    pendek = list(lines8)
    pendek[14] = 'tiga kata saja'
    panggilan.clear()
    h = rh.periksa_hemat('\n'.join(pendek), peta8, mode='peta_awal',
                         fn_petakan_teks=petakan_palsu,
                         fn_susun_teks=susun_palsu,
                         fn_pendapat_kedua=None)
    cek('saringan: paragraf dipendekkan -> saringan menolak, Jev 1x',
        h is not None and h.get('jalan') == 'hemat'
        and len(panggilan) == 1)

    # ── 9. BATAS LAJU OTOMATIS 24 JAM (15 Nov 2026) ─────────────────────
    from datetime import datetime, timedelta, timezone
    _kini = datetime.now(timezone.utc)
    cek('batas laju: belum pernah diperiksa -> boleh',
        amb.boleh_otomatis_jalan(None)[0] is True)
    cek('batas laju: 1 jam lalu -> tidak boleh',
        amb.boleh_otomatis_jalan(_kini - timedelta(hours=1))[0] is False)
    cek('batas laju: 23 jam lalu -> tidak boleh',
        amb.boleh_otomatis_jalan(_kini - timedelta(hours=23))[0] is False)
    cek('batas laju: 25 jam lalu -> boleh',
        amb.boleh_otomatis_jalan(_kini - timedelta(hours=25))[0] is True)
    cek('batas laju: waktu naive (dari SQLite) 25 jam lalu -> boleh',
        amb.boleh_otomatis_jalan(
            (_kini - timedelta(hours=25)).replace(tzinfo=None))[0] is True)
    cek('batas laju: konstanta = 24 jam',
        amb.BATAS_OTOMATIS_JAM == 24)

    # ── 10. FAIL-OPEN PERBANDINGAN (bug: docstring vs kode) ─────────────
    #     Dulu gagal membandingkan -> tombol MATI (fail-closed), padahal
    #     docstring bilang fail-open manual. Sekarang: tombol aktif,
    #     otomatis tetap mati.
    def _susun_gagal(teks):
        raise RuntimeError('susun rusak')

    d = amb.bandingkan_perubahan(peta, teks, _susun_gagal)
    cek('fail-open: gagal membandingkan -> tombol aktif, otomatis mati',
        d['berubah_berarti'] and not d['berubah_besar']
        and d.get('otomatis') is False)

    print(f'\n{len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL:')
        for g in GAGAL:
            print('  - ' + g)
        sys.exit(1)


if __name__ == '__main__':
    main()
