"""Tahap 3 — kumpulkan kandidat sengketa dari naskah BELAJAR saja.

Sumber (tanpa Jev, hanya dari run tersimpan + teks):
  A. Hakim curiga (semua)
  B. Hakim ragu (diutamakan label bab/subbab)
  C. Goyang yang melibatkan bab/subbab
  D. Goyang paragraf/biasa yang teksnya mirip judul (bernomor / CAPS pendek)
  E. Label yang bertentangan aturan deterministik (pemisah =====, salinan
     daftar isi, nomor romawi polos, huruf kecil awal, judul >300 kar)
Konteks tiap kandidat dicari di teks mentah (BOM dibersihkan saat cocok).
Keluaran: _sketsa/kandidat_sengketa.json (dengan konteks +-6 baris mentah).
"""
import json, re, os, sys, hashlib, glob, importlib.util, types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# --- muat peta3 dengan stub (pola tests/test_jev_hakim.py), untuk susun tanpa stitch ---
import tests.test_jev_hakim as _T  # noqa: F401  (memakai stub + fake satpam)
P = _T._muat_peta3()

PEMBAGIAN = json.load(open('pembagian.json'))
BELAJAR = set()
for b in PEMBAGIAN['bidang']:
    BELAJAR.update(b['belajar'])

all_e = {}
for g in [1, 2, 3, 4]:
    d = json.load(open(f'hasil_latih_grup{g}.json'))
    for e in d['entri']:
        all_e[e['kode']] = (g, e)

file_by_md5 = {}
for f in glob.glob('teks_latih/**/*.txt', recursive=True):
    file_by_md5[hashlib.md5(open(f, 'rb').read()).hexdigest()] = f
man4 = {}
m4 = json.load(open('teks_latih/manifest_grup4.json'))
for e in m4['entri']:
    man4[e['kode']] = e.get('teks_path')

def teks_path(kode, e):
    if e.get('berkas_teks'):
        p = os.path.join('teks_latih', e['berkas_teks'])
        if os.path.exists(p):
            return p
    if e.get('md5') and e['md5'] in file_by_md5:
        return file_by_md5[e['md5']]
    if man4.get(kode):
        return man4[kode]
    return None

def norm(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\ufeff', '')).strip()

def cari_konteks(teks_mentah, cuplikan, jml=6):
    """Cari cuplikan (dinormalisasi) di teks mentah; kembalikan (no_baris, konteks)."""
    baris = teks_mentah.split('\n')
    c = norm(cuplikan)
    if not c:
        return None, []
    if len(c) > 60:
        c = c[:60]
    for i, b in enumerate(baris):
        if c in norm(b):
            lo, hi = max(0, i - jml), min(len(baris), i + jml + 1)
            return i, baris[lo:hi]
    # fallback: kata-kata khas
    kata = [w for w in re.findall(r'[A-Za-z]{4,}', c)][:4]
    for i, b in enumerate(baris):
        nb = norm(b)
        if kata and sum(1 for w in kata if w in nb) >= max(1, len(kata) - 1):
            lo, hi = max(0, i - jml), min(len(baris), i + jml + 1)
            return i, baris[lo:hi]
    return None, []

def baris_rekon(teks):
    """Baris bersih deterministik (tanpa stitch Jev) — untuk idx grup3."""
    try:
        d = P._susun_dari_bersih(teks, pakai_stitch=False)
        return d['baris']
    except Exception as ex:
        print('  rekon gagal:', ex)
        return teks.split('\n')

POLA_PEMISAH = re.compile(r'^=+\s*BAB\s+[IVX0-9]+.*=+\s*$')
POLA_PEMISAH_ANY = re.compile(r'^=+\s*.+\s*=+$')

kandidat = []  # dict: kode, bidang, jenis, bukti, teks_cuplikan, idx_run

def tambah(kode, bidang, jenis, bukti, cuplikan, idx_run=None):
    kandidat.append({'kode': kode, 'bidang': bidang, 'jenis': jenis,
                     'bukti': bukti, 'cuplikan': (cuplikan or '')[:160],
                     'idx_run': idx_run})

for kode in sorted(BELAJAR):
    g, e = all_e[kode]
    bidang = e['bidang']
    p = teks_path(kode, e)
    teks = open(p, encoding='utf-8', errors='replace').read() if p else ''
    baris_r = None
    h = e.get('hakim') or {}
    # A. curiga + B. ragu
    ragu_items, curiga_items = [], []
    if g in (1, 2):
        for t, alasan in (h.get('curiga_contoh') or []):
            curiga_items.append((None, t, alasan))
        for t, alasan in (h.get('ragu_contoh') or []):
            ragu_items.append((None, t, alasan))
    elif g == 3:
        for it in (h.get('bagian_curiga') or []):
            curiga_items.append((it.get('i'), it.get('judul', ''), ['hakim-curiga']))
        for it in (h.get('bagian_ragu') or []):
            ragu_items.append((it.get('i'), it.get('judul', ''), ['hakim-ragu']))
    elif g == 4:
        for t, alasan in (e.get('hakim_curiga_contoh') or []):
            curiga_items.append((None, t, alasan))
        for t, alasan in (e.get('hakim_ragu_contoh') or []):
            ragu_items.append((None, t, alasan))
    for idx, t, alasan in curiga_items:
        tambah(kode, bidang, 'hakim_curiga', 'Hakim curiga: %s' % (alasan,), t, idx)
    for idx, t, alasan in ragu_items:
        tambah(kode, bidang, 'hakim_ragu', 'Hakim ragu: %s' % (alasan,), t, idx)
    # C+D. goyang
    for gy in (e.get('goyang') or []):
        idx = gy[0]
        labels = gy[1] if len(gy) > 1 else []
        teks_g = gy[2] if len(gy) > 2 else None
        if teks_g is None:
            if baris_r is None:
                baris_r = baris_rekon(teks)
            teks_g = baris_r[idx] if 0 <= idx < len(baris_r) else ''
        lab_set = set(labels)
        if 'bab' in lab_set or 'subbab' in lab_set:
            tambah(kode, bidang, 'goyang_bab_subbab',
                   'goyang %s' % ('/'.join(labels),), teks_g, idx)
        elif lab_set == {'paragraf', 'biasa'}:
            t = norm(teks_g)
            mirip_judul = bool(re.match(r'^(\d+(\.\d+)+\.?|[A-Z]\.)\s+\S', t)) or (
                len(t) <= 70 and t and t == t.upper() and not t.endswith(('.', ',', ';')))
            if mirip_judul:
                tambah(kode, bidang, 'goyang_paragraf_judul',
                       'goyang paragraf/biasa, teks mirip judul: %s' % ('/'.join(labels),), teks_g, idx)
    # E. label bertentangan deterministik (dari daftar judul bab)
    judul_bab = []
    for k in ('bab_gabung', 'bab_judul'):
        v = e.get(k)
        if isinstance(v, list):
            judul_bab += [str(x) for x in v]
    if g == 3:
        for t in (e.get('bab_judul_label') or []):
            judul_bab.append(str(t))
    for t in judul_bab:
        tn = norm(t)
        if POLA_PEMISAH.match(tn) or POLA_PEMISAH_ANY.match(tn):
            tambah(kode, bidang, 'deterministik_pemisah',
                   'pemisah gabungan terlabel bab', t)
        elif re.match(r'^-\s*BAB\s+[IVX0-9]+', tn):
            tambah(kode, bidang, 'deterministik_daftar_isi',
                   'salinan daftar isi terlabel bab', t)
        elif re.match(r'^[IVX]{1,4}$', tn) or tn in ('-', '--'):
            tambah(kode, bidang, 'deterministik_nomor_polos',
                   'nomor romawi / strip polos terlabel bab', t)
        elif re.match(r'^[IVX]{1,4}\.\s+TABLE', tn, re.I):
            tambah(kode, bidang, 'deterministik_tabel',
                   'keterangan tabel terlabel bab', t)
    # E2. grup3 label_penuh: bab/subbab yang teksnya melanggar aturan
    if g == 3:
        if baris_r is None:
            baris_r = baris_rekon(teks)
        for idx_s, lab in (e.get('label_penuh') or {}).items():
            idx = int(idx_s)
            if lab not in ('bab', 'subbab'):
                continue
            t = norm(baris_r[idx]) if 0 <= idx < len(baris_r) else ''
            if not t:
                continue
            if POLA_PEMISAH.match(t) or POLA_PEMISAH_ANY.match(t):
                tambah(kode, bidang, 'deterministik_pemisah',
                       'label_penuh %s pada pemisah' % lab, t, idx)
            elif t[:1].islower():
                tambah(kode, bidang, 'deterministik_huruf_kecil',
                       'label_penuh %s diawali huruf kecil (Aturan 5)' % lab, t, idx)
            elif lab == 'subbab' and len(t) > 300:
                tambah(kode, bidang, 'deterministik_judul_panjang',
                       'label_penuh subbab >300 kar (Aturan 2)', t, idx)

print('kandidat mentah:', len(kandidat))
# dedup: (teks ternormalisasi) — simpan semua kode yang berbagi teks
unik, lihat = [], {}
for k in kandidat:
    kunci = norm(k['cuplikan'])[:80]
    if kunci in lihat:
        lihat[kunci]['kode_lain'].append(k['kode'])
        continue
    k['kode_lain'] = []
    lihat[kunci] = k
    unik.append(k)
print('kandidat unik (teks):', len(unik))
per_bidang = {}
for k in unik:
    per_bidang.setdefault(k['bidang'], []).append(k)
for b in sorted(per_bidang):
    print(' ', b, len(per_bidang[b]), collections.Counter(x['jenis'] for x in per_bidang[b]) if (collections := __import__('collections')) else '')

# tambah konteks mentah
for k in unik:
    g, e = all_e[k['kode']]
    p = teks_path(k['kode'], e)
    teks = open(p, encoding='utf-8', errors='replace').read() if p else ''
    no, ctx = cari_konteks(teks, k['cuplikan'])
    k['no_baris_mentah'] = no
    k['konteks'] = ctx
    k['teks_path'] = p
print('tanpa konteks ditemukan:', sum(1 for k in unik if k['no_baris_mentah'] is None))
json.dump(unik, open('_sketsa/kandidat_sengketa.json', 'w'), ensure_ascii=False, indent=1)
print('tersimpan _sketsa/kandidat_sengketa.json')
