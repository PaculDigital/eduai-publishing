"""Bangun paket label kebenaran dasar (ground truth) Jev/Hakim v7.

MEMBACA SAJA, tanpa panggilan Jev, tanpa tulis ke DB.
Sumber:
  - teks bersih 4 naskah (fid=81 dari _naskah_asih.txt lokal;
    fid=112/115/WULAN-1 dari /tmp/teks_gt_*.txt yang diambil dari
    container secara baca-saja),
  - hasil_v7_live.json (daftar judul BAB per run + hitungan label),
  - hasil_v7_live.log (baris curiga/ragu Hakim + nomor baris Lxxxxxx),
  - hasil_ab114_fid81.json (label_penuh 1.13 vs 1.14 + 21 baris beda).
Cara kerja:
  1. Rekonstruksi `baris` tiap naskah dengan _susun_dari_bersih v7,
     Jev dipalsukan -> {} (tidak ada panggilan). Verifikasi selaras
     dengan live lewat jangkar: jumlah kandidat + jumlah buang +
     teks baris pada nomor baris yang dikenal dari log live.
  2. Kumpulkan baris sengketa yang BISA dipulihkan dari artefak:
     a. BAB yang hilang di satu run (dari daftar BAB per run v7),
     b. judul BAB sampah (WULAN-1 run 2),
     c. baris curiga/ragu Hakim (dari log v7),
     d. fid=81: 21 baris yang label 1.13 dan 1.14 berbeda.
  3. Tulis satu TSV per naskah di ground_truth/ + README.
JUJUR: sengketa batas paragraf antar-run v7 TIDAK bisa dipulihkan
(per-line label v7 tidak pernah disimpan — hanya hitungan agregat).
Untuk itu ada skrip pelengkap buat_sengketa_paragraf.py yang
menjalankan 2 run live baru DENGAN simpan label per baris; biayanya
ditulis di README dan tidak dijalankan di sini.

Jalankan: python3 ground_truth/buat_paket_ground_truth.py
"""
import ast
import base64
import csv
import json
import re
import sys
import types
import importlib.util
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
GT = ROOT / 'ground_truth'
sys.path.insert(0, str(ROOT))

# ---------- muat peta3_jev v7 dengan stub (tanpa Jev, tanpa DB) ----------
ai = types.ModuleType('app.ai')
class _DummySession:
    def __enter__(self): return self
    def __exit__(self, *a): pass
ai.SessionLocal = lambda: _DummySession()
ai._teks_dari_berkas = lambda *a, **k: ''
ai.UPLOAD_DIR = Path('/tmp')
sys.modules['app.ai'] = ai
models = types.ModuleType('app.models')
models.FileBerkas = object
sys.modules['app.models'] = models

_src = open(ROOT / 'peta3_jev.py', encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src, 'sisa sys.path jev-v4 masih ada!'
spec = importlib.util.spec_from_loader('peta3_rekon_gt', loader=None)
P = importlib.util.module_from_spec(spec)
exec(compile(_src, str(ROOT / 'peta3_jev.py'), 'exec'), P.__dict__)

_mock = {'n': 0}
def _mock_tanya(bahan, pertanyaan, *a, **k):
    _mock['n'] += 1
    return {}
P.satpam.tanya_bebas_mutu = _mock_tanya

from app import state as _state

TEKS = {
    # Teks bersih disimpan PERSISTEN di _teks/ (bukan /tmp — /tmp pernah
    # dibersihkan di tengah kerja 10 Nov 2026). fid=81 dari _naskah_asih.txt
    # lokal (mentah -> buang_daftar_isi dulu); sisanya dari container,
    # diambil baca-saja lewat _teks/ambil_teks.py.
    '81': ('_naskah_asih.txt', True),   # mentah -> buang_daftar_isi dulu
    '112': ('ground_truth/_teks/teks_bersih_112.txt', False),
    '115': ('ground_truth/_teks/teks_bersih_115.txt', False),
    'WULAN-1': ('ground_truth/_teks/teks_bersih_WULAN-1.txt', False),
}
# jangkar live: (naskah, nomor_baris, teks_yang_diharapkan)
JANGKAR = [
    ('112', 670, '(David, 2010) dalam (Andika, 2020).'),
    ('112', 757, '(Mahardhani,2023)'),
    ('112', 1859, '(Ulan – Pengelola AyuMeera)'),
    ('115', 1817, '(Ulan – Pengelola AyuMeera)'),
    ('115', 1819, '(Divisi AyuMeera)'),
    ('115', 1849, '(Regina – Div AyuMeera)'),
]
# hitungan live v7 yang harus cocok (kand_jml, buang) — rentang antar-run.
# 112/115: stitch Jev TIDAK bisa direproduksi tanpa panggilan live, jadi
# kand/buang mock PASTI meleset (stitch tidak menyambung) — yang diverifikasi
# di sana adalah: semua teks jangkar DITEMUKAN lewat pencarian teks.
HARAPAN = {
    '81': {'kand': (486, 486), 'buang': (720, 720), 'mock_max': 0},
    '112': {'kand': (1667, 1673), 'buang': (76, 77), 'mock_max': 60},
    '115': {'kand': (1686, 1692), 'buang': (117, 117), 'mock_max': 60},
    'WULAN-1': {'kand': (427, 427), 'buang': (199, 199), 'mock_max': 10},
}


def rekonstruksi(naskah):
    sumber, mentah = TEKS[naskah]
    jalan = ROOT / sumber if not str(sumber).startswith('/') else Path(sumber)
    teks = open(jalan, encoding='utf-8').read()
    if mentah:
        teks = _state.buang_daftar_isi(teks)
    _mock['n'] = 0
    d = P._susun_dari_bersih(teks)
    info = {'baris': d['baris'], 'kand': [i for i, _ in d['kand']],
            'gabung': d['gabung'], 'kode_label': d['kode_label'],
            'buang': len(d['buang']), 'mock_jev': _mock['n']}
    return info


def cari_baris(baris, teks_cari, mulai=0):
    """Cari nomor baris yang teksnya mengandung teks_cari (normalisasi spasi)."""
    norm = ' '.join((teks_cari or '').split())
    for i in range(mulai, len(baris)):
        if norm and norm in ' '.join(baris[i].split()):
            return i
    return None


def konteks(baris, i):
    def _ambil(j):
        if 0 <= j < len(baris):
            return ' '.join(baris[j].split())[:200]
        return '(tepi)'
    sebelum, sesudah = '(kosong)', '(kosong)'
    j = i - 1
    while j >= 0 and not baris[j].strip():
        j -= 1
    if j >= 0:
        sebelum = _ambil(j)
    j = i + 1
    while j < len(baris) and not baris[j].strip():
        j += 1
    if j < len(baris):
        sesudah = _ambil(j)
    return sebelum, sesudah


def normal_bab(judul):
    """'2. BAB II TINJAUAN PUSTAKA' -> 'BAB II TINJAUAN PUSTAKA'."""
    return re.sub(r'^\d+\.\s*', '', (judul or '').strip())


def main():
    GT.mkdir(exist_ok=True)
    v7 = json.load(open(ROOT / 'hasil_v7_live.json', encoding='utf-8'))
    ab = json.load(open(ROOT / 'hasil_ab114_fid81.json', encoding='utf-8'))
    log = open(ROOT / 'hasil_v7_live.log', encoding='utf-8').read()

    # ---------- 1. rekonstruksi + verifikasi jangkar ----------
    data = {}
    selaras = {}
    print('== rekonstruksi baris (tanpa Jev) ==')
    for naskah in ('81', '112', '115', 'WULAN-1'):
        info = rekonstruksi(naskah)
        data[naskah] = info
        h = HARAPAN[naskah]
        ok_kand = h['kand'][0] <= len(info['kand']) <= h['kand'][1]
        ok_buang = h['buang'][0] <= info['buang'] <= h['buang'][1]
        # 81 dan WULAN-1: stitch nyaris tanpa Jev -> harus cocok persis.
        # 112/115: stitch Jev tidak direproduksi -> kand/buang meleset,
        # selaras dinilai dari jangkar teks (semua teks jangkar ditemukan).
        if naskah in ('81', 'WULAN-1'):
            selaras[naskah] = bool(ok_kand and ok_buang)
        else:
            selaras[naskah] = 'sebagian (teks)'
        print(f"  {naskah}: baris={len(info['baris'])} kand={len(info['kand'])} "
              f"(harapan {h['kand']}) buang={info['buang']} (harapan {h['buang']}) "
              f"mock_jev={info['mock_jev']} gabung_BAB={len(info['gabung'])} "
              f"-> {'SELARAS' if selaras[naskah] is True else selaras[naskah]}")
    print('== jangkar nomor baris dari log live ==')
    for naskah, idx, harap in JANGKAR:
        baris = data[naskah]['baris']
        dapat = ' '.join(baris[idx].split())[:120] if idx < len(baris) else '(DI LUAR)'
        cocok = harap in dapat
        print(f"  {naskah} L{idx:06d}: {'COCOK' if cocok else 'TIDAK COCOK'} "
              f"dapat={dapat!r} harap={harap!r}")
        if not cocok:
            alt = cari_baris(baris, harap)
            print(f"      teks ditemukan di baris {alt} (geser {alt - idx if alt is not None else '?'})")

    # ---------- 2. parse log v7: baris Hakim per naskah per run ----------
    hakim = {}  # (naskah, run) -> {'curiga': [(teks, alasan)], 'ragu': [...]}
    cur_naskah, cur_run = None, None
    for bar in log.split('\n'):
        m = re.match(r'=== (?:fid=)?(\S+) run (\d+) wall:', bar)
        if m:
            cur_naskah, cur_run = m.group(1), int(m.group(2))
            continue
        m2 = re.match(r'\[hakim_peta\] curiga (L\d+) \((.*)\): (\S+)', bar)
        if m2 and cur_naskah:
            hakim.setdefault((cur_naskah, cur_run), {'curiga': [], 'ragu': []})
            hakim[(cur_naskah, cur_run)]['curiga'].append(
                (m2.group(1), m2.group(2), m2.group(3)))
            continue
        m3 = re.match(r'\s+contoh (curiga|ragu): (\[.*\])\s*$', bar)
        if m3 and cur_naskah:
            try:
                isi = ast.literal_eval(m3.group(2))
            except Exception:
                continue
            hakim.setdefault((cur_naskah, cur_run), {'curiga': [], 'ragu': []})
            for teks, alasan in isi:
                hakim[(cur_naskah, cur_run)][m3.group(1)].append(
                    (None, teks, ','.join(alasan)))

    # ---------- 3. tulis TSV per naskah ----------
    KOLOM = ['no', 'jenis_sengketa', 'naskah', 'baris_no', 'teks_baris',
             'konteks_sebelum', 'konteks_sesudah', 'bukti_run',
             'label_benar', 'catatan_boss']
    ringkas = {}
    for naskah in ('81', '112', '115', 'WULAN-1'):
        baris = data[naskah]['baris']
        rows = []
        no = 0

        def tambah(jenis, idx, teks, bukti):
            nonlocal no
            no += 1
            if idx is None:
                sb, sd = '(tidak diketahui)', '(tidak diketahui)'
                teks_tampil = teks
            else:
                sb, sd = konteks(baris, idx)
                teks_tampil = ' '.join(baris[idx].split())[:300]
            rows.append({'no': no, 'jenis_sengketa': jenis, 'naskah': naskah,
                         'baris_no': '' if idx is None else idx,
                         'teks_baris': teks_tampil, 'konteks_sebelum': sb,
                         'konteks_sesudah': sd, 'bukti_run': bukti,
                         'label_benar': '', 'catatan_boss': ''})

        # -- a. BAB per run (dari JSON v7): yang hilang / yang sampah --
        runs = v7[naskah]
        daftar_bab = [normal_bab(b) for r in runs for b in r.get('bab', [])]
        # judul sampah = bukan pola BAB (kalimat panjang), pisahkan dari baseline
        bab_benar = sorted({b for b in daftar_bab if re.match(r'^BAB\s+[IVX0-9]+', b)})
        bab_sampah = sorted({b for b in daftar_bab if not re.match(r'^BAB\s+[IVX0-9]+', b)})
        for judul in bab_benar:
            hadir = []
            for r in runs:
                if judul in [normal_bab(b) for b in r.get('bab', [])]:
                    hadir.append(str(r['run']))
            if len(hadir) < 3:
                idx = cari_baris(baris, judul)
                tambah('bab_hilang', idx, judul,
                       'BAB ada di run %s, HILANG di run %s'
                       % (','.join(hadir) or '-',
                          ','.join(str(r['run']) for r in runs
                                   if str(r['run']) not in hadir)))
        for judul in bab_sampah:
            idx = cari_baris(baris, judul[:80])
            tambah('judul_bab_sampah', idx, judul,
                   'Dilabel BAB oleh Jev di salah satu run v7, padahal ini kalimat biasa')
        # Catatan posisi: untuk 112/115 nomor baris berasal dari rekonstruksi
        # tanpa Jev (stitch tidak direproduksi) — teks dan konteks benar,
        # nomor bisa geser dari nomor live. Untuk 81/WULAN-1 nomor = live.
        for r in rows:
            if r['jenis_sengketa'] in ('bab_hilang', 'judul_bab_sampah') \
                    and naskah in ('112', '115'):
                r['bukti_run'] += ('; nomor baris dari rekonstruksi '
                                   '(tanpa Jev), bisa geser dari nomor live')

        # -- b. Hakim curiga / ragu (dari log v7): gabung antar run --
        gabung_hakim = {}
        for (nk, run), isi in sorted(hakim.items()):
            if nk != naskah:
                continue
            for jenis in ('curiga', 'ragu'):
                for lid, teks, alasan in isi[jenis]:
                    kunci = teks.strip()
                    gabung_hakim.setdefault(kunci, {'jenis': jenis, 'alasan': set(),
                                                    'run': set(), 'lid': lid})
                    gabung_hakim[kunci]['alasan'].add(alasan)
                    gabung_hakim[kunci]['run'].add(run)
                    if lid and not gabung_hakim[kunci]['lid']:
                        gabung_hakim[kunci]['lid'] = lid
        for teks, g in sorted(gabung_hakim.items()):
            # Nomor baris yang ditulis = nomor LIVE (Lxxxxxx dari log) bila
            # ada; konteks diambil dari posisi hasil pencarian teks (untuk
            # 112/115 posisi rekonstruksi bisa geser karena stitch Jev
            # tidak direproduksi — teks dan konteksnya tetap benar).
            idx_konteks = cari_baris(baris, teks)
            no_live = None
            if g['lid']:
                try:
                    no_live = int(g['lid'][1:])
                except ValueError:
                    no_live = None
            if idx_konteks is None and no_live is not None:
                idx_konteks = no_live
            # tambah() memakai idx untuk konteks DAN nomor; bila ada nomor
            # live, tulis nomor live secara manual sesudahnya.
            n_sebelum = no
            tambah('hakim_%s' % g['jenis'], idx_konteks, teks,
                   'Hakim %s (%s) di run %s'
                   % (g['jenis'], ';'.join(sorted(g['alasan'])),
                      ','.join(str(r) for r in sorted(g['run']))))
            if no_live is not None:
                rows[-1]['baris_no'] = no_live
                if idx_konteks is not None and idx_konteks != no_live:
                    rows[-1]['bukti_run'] += ('; nomor live L%06d, posisi '
                                              'rekonstruksi %d (geser karena '
                                              'stitch)' % (no_live, idx_konteks))

        # -- c. fid=81: 21 baris beda label 1.13 vs 1.14 (AB114) --
        if naskah == '81':
            for idx, lab113, lab114 in ab['banding']['label_beda_rinci']:
                tambah('beda_model_113_114', idx, '',
                       '1.13: %s | 1.14: %s (baseline Okt: subbab 130, paragraf 157)'
                       % (lab113, lab114))

        jalan = GT / ('ground_truth_%s.tsv' % naskah)
        with open(jalan, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=KOLOM, delimiter='\t')
            w.writeheader()
            for r in rows:
                w.writerow(r)
        dari_jenis = {}
        for r in rows:
            dari_jenis[r['jenis_sengketa']] = dari_jenis.get(r['jenis_sengketa'], 0) + 1
        ringkas[naskah] = {'total': len(rows), 'per_jenis': dari_jenis}
        print(f'  {naskah}: {len(rows)} baris sengketa -> {jalan.name} {dari_jenis}')

    # ---------- 4. baseline gerbang (dari JSON v7; gabung kode HANYA bila perlu) --
    # Daftar 'bab' JSON v7 untuk fid=81 KOSONG (judul BAB di sana diputuskan
    # kode -> 'gabung', bukan label Jev). Untuk 81 saja, baseline diambil
    # dari judul gabung kode rekonstruksi — sah karena rekonstruksi 81
    # SELARAS persis dengan live (kand 486, buang 720, gabung 10, mock 0).
    # Untuk 112/115 gabung mock TIDAK dipakai: tanpa stitch Jev, mock
    # menemukan BAB I + BAB VI palsu dan kehilangan BAB IV + BAB V
    # (terbukti: mock gabung 112/115 = I, II, III, VI; live = II, III, IV, V).
    baseline = {}
    for naskah in ('81', '112', '115'):
        runs = v7[naskah]
        bab_union = {normal_bab(b) for r in runs for b in r.get('bab', [])
                     if re.match(r'^BAB\s+[IVX0-9]+', normal_bab(b))}
        if not bab_union:
            for _penanda, _judul in data[naskah]['gabung'].values():
                t = ('%s %s' % (_penanda, _judul)).strip()
                if re.match(r'^BAB\s+[IVX0-9]+', t):
                    bab_union.add(t)
        bab_union = sorted(bab_union)
        sub = sorted(r.get('subbab_jml', r.get('label', {}).get('subbab', 0))
                     for r in runs)
        baseline[naskah] = {
            'bab': bab_union,
            'subbab_per_run': sub,
            'subbab_median': sub[len(sub) // 2],
            'paragraf_per_run': sorted(r.get('label', {}).get('paragraf', 0)
                                       for r in runs),
            'sumber': 'hasil_v7_live.json (3 run per naskah, 10 Nov 2026)',
        }
    json.dump(baseline, open(GT / 'gerbang_baseline.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('baseline gerbang:', json.dumps(baseline, ensure_ascii=False))
    ringkas['_selaras_rekonstruksi'] = {k: str(v) for k, v in selaras.items()}
    ringkas['_catatan'] = (
        'fid=81 dan WULAN-1: rekonstruksi tanpa Jev SELARAS persis dengan live '
        '(kand dan buang sama; stitch nyaris tanpa Jev), jadi nomor baris = '
        'nomor live. fid=112/115: stitch Jev tidak bisa direproduksi tanpa '
        'panggilan live (kand mock ~2x live) — teks dan konteks tiap baris '
        'sengketa tetap benar (dicari lewat pencarian teks), tapi nomor baris '
        'bisa geser; untuk baris Hakim dipakai nomor live Lxxxxxx dari log. '
        'Sengketa batas paragraf antar-run v7 TIDAK ada di paket ini karena '
        'label per baris v7 tidak pernah disimpan; lihat buat_sengketa_paragraf.py.')
    json.dump(ringkas, open(GT / 'ringkasan_paket.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
