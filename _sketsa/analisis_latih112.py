"""Analisis offline hasil latih 112 naskah (tahap 2-4) — NOL panggilan Jev.

Membangun tabel terpadu dari hasil_latih_grup{1..4}.json + teks_latih/:
- pemetaan kode -> berkas teks (grup1/2: berkas_teks; grup3: md5; grup4: manifest)
- duplikat (md5 mentah + md5 ternormalisasi BOM/spasi)
- profil bentuk deterministik per naskah (prototipe Lapis 1 v11)
- statistik per bidang: label bab, goyang, hakim ragu/curiga, anomali bab
- kandidat sengketa (hakim ragu/curiga + goyang bab/subbab + label_penuh grup3
  yang bertentangan aturan deterministik)
Keluaran: _sketsa/tabel_latih112.json, _sketsa/pola_bidang.json,
_sketsa/kandidat_sengketa.json
"""
import json, hashlib, os, re, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def md5_bytes(b):
    return hashlib.md5(b).hexdigest()

def md5_norm(teks):
    t = teks.replace('\ufeff', '')
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return hashlib.md5(t.encode('utf-8')).hexdigest()

# --- petakan berkas teks ---
file_by_md5 = {}
for f in glob.glob('teks_latih/**/*.txt', recursive=True):
    file_by_md5[md5_bytes(open(f, 'rb').read())] = f
man4 = {}
try:
    m4 = json.load(open('teks_latih/manifest_grup4.json'))
    for e in m4['entri']:
        man4[e['kode']] = e.get('teks_path')
except Exception as ex:
    print('manifest grup4 gagal:', ex)

entri = []
for g in [1, 2, 3, 4]:
    d = json.load(open(f'hasil_latih_grup{g}.json'))
    for e in d['entri']:
        e['_grup'] = g
        p = None
        if e.get('berkas_teks'):
            p = os.path.join('teks_latih', e['berkas_teks'])
        elif e.get('md5') and e['md5'] in file_by_md5:
            p = file_by_md5[e['md5']]
        elif man4.get(e.get('kode')):
            p = man4[e['kode']]
        e['_teks'] = p if p and os.path.exists(p) else None
        entri.append(e)
print('entri:', len(entri), 'tanpa teks:', [e['kode'] for e in entri if not e['_teks']])

# --- duplikat ---
by_raw, by_norm = collections.defaultdict(list), collections.defaultdict(list)
for e in entri:
    if not e['_teks']:
        continue
    raw = open(e['_teks'], 'rb').read()
    by_raw[md5_bytes(raw)].append(e['kode'])
    by_norm[md5_norm(raw.decode('utf-8', errors='replace'))].append(e['kode'])
print('DUPLIKAT md5 mentah:')
for h, ks in by_raw.items():
    if len(ks) > 1:
        print('  ', ks)
print('DUPLIKAT md5 ternormalisasi (BOM/spasi/huruf):')
for h, ks in by_norm.items():
    if len(ks) > 1:
        print('  ', ks)

# --- profil bentuk deterministik (prototipe v11) ---
POLA_BAB_ROMAWI = re.compile(r'^\s*(?:\d{1,3}\s+)?(?:\d+[.)]\s*)?BAB\s+([IVX]+)\b', re.I)
POLA_BAB_ARAB = re.compile(r'^\s*(?:\d{1,3}\s+)?(?:\d+[.)]\s*)?BAB\s+(\d+)\b', re.I)
POLA_CHAPTER = re.compile(r'^\s*(?:\d{1,3}\s+)?(?:\d+[.)]\s*)?CHAPTER\s+([IVX0-9]+)\b', re.I)
POLA_ROMAWI_TANPA_BAB = re.compile(r'^\s*([IVX]{1,4})[.]\s+[A-Z\u00C0-\u00DE][^.]{2,60}$')
POLA_PEMISAH = re.compile(r'^=+\s*BAB\s+[IVX0-9]+.*=+\s*$')

def profil(teks):
    baris = teks.split('\n')
    romawi, arab, chapter, romawi_tanpa = set(), set(), set(), 0
    pemisah = 0
    for b in baris:
        s = b.strip().replace('\ufeff', '')
        if POLA_PEMISAH.match(s):
            pemisah += 1
            continue
        m = POLA_BAB_ROMAWI.match(s)
        if m:
            romawi.add(m.group(1).upper()); continue
        m = POLA_BAB_ARAB.match(s)
        if m:
            arab.add(int(m.group(1))); continue
        m = POLA_CHAPTER.match(s)
        if m:
            chapter.add(m.group(1).upper()); continue
        if POLA_ROMAWI_TANPA_BAB.match(s):
            romawi_tanpa += 1
    kata = teks.split()
    n_kata = len(kata)
    inggris = sum(1 for w in kata if w.lower().strip('.,;:()') in
                  {'the', 'and', 'of', 'to', 'in', 'is', 'are', 'for', 'with', 'chapter', 'introduction'})
    tabel_baris = sum(1 for b in baris if b.count('|') >= 2)
    tabel_kata = len(re.findall(r'\bTabel\s+\d', teks)) + len(re.findall(r'\bTable\s+\d', teks))
    sistematika = bool(re.search(r'SISTEMATIKA\s+PENULISAN', teks, re.I))
    kti = bool(re.search(r'Karya Tulis Ilmiah|Ahli Madya', teks))
    huruf_berspasi = sum(1 for b in baris if re.search(r'(?:[A-Za-z]\s){4,}[A-Za-z]', b))
    nul = teks.count('\x00')
    bom = teks.count('\ufeff')
    n_bab = len(romawi | {str(a) for a in arab} | chapter)
    return {
        'bab_romawi': sorted(romawi), 'bab_arab': sorted(arab),
        'chapter': sorted(chapter), 'romawi_tanpa_bab_jml': romawi_tanpa,
        'pemisah_gabung_jml': pemisah, 'sistematika': sistematika,
        'tabel_baris_pipa': tabel_baris, 'tabel_kata_jml': tabel_kata,
        'rasio_inggris': round(inggris / max(1, n_kata), 4),
        'kti_d3': kti, 'jml_bab_terdeteksi': n_bab,
        'huruf_berspasi_jml': huruf_berspasi, 'nul_jml': nul, 'bom_jml': bom,
        'kata': n_kata, 'baris': len(baris),
    }

for e in entri:
    t = open(e['_teks'], encoding='utf-8', errors='replace').read() if e['_teks'] else ''
    e['_profil'] = profil(t)
    e['_teks_isi'] = t

# --- statistik per bidang ---
def label_counts(e):
    lab = e.get('label') or {}
    return {k: lab.get(k, 0) for k in ('bab', 'subbab', 'paragraf', 'biasa')}

def hakim_counts(e):
    h = e.get('hakim') or {}
    return (h.get('jumlah_sepakat', 0), h.get('jumlah_ragu', 0),
            h.get('jumlah_curiga', 0), h.get('jumlah_belum', 0))

def panggilan_total(e):
    if isinstance(e.get('panggilan_total'), int):
        return e['panggilan_total']
    if isinstance(e.get('panggilan_petakan_total'), int):
        return e['panggilan_petakan_total'] + e.get('panggilan_hakim_total', 0) + 1
    return None

per_bidang = {}
for e in entri:
    b = per_bidang.setdefault(e['bidang'], {'kode': [], 'bab': 0, 'subbab': 0,
        'paragraf': 0, 'biasa': 0, 'goyang': 0, 'ragu': 0, 'curiga': 0,
        'panggilan': 0, 'bab_nol': [], 'bentuk': []})
    b['kode'].append(e['kode'])
    lc = label_counts(e)
    for k in ('bab', 'subbab', 'paragraf', 'biasa'):
        b[k] += lc[k]
    b['goyang'] += e.get('goyang_jml', 0)
    _, r, c, _ = hakim_counts(e)
    b['ragu'] += r; b['curiga'] += c
    b['panggilan'] += panggilan_total(e) or 0
    if lc['bab'] == 0:
        b['bab_nol'].append(e['kode'])
    b['bentuk'].append({'kode': e['kode'], 'profil': e['_profil'],
                        'bab_label': lc['bab'], 'goyang': e.get('goyang_jml', 0),
                        'ragu': r, 'curiga': c})
json.dump({'per_bidang': per_bidang,
           'total_panggilan': sum(panggilan_total(e) or 0 for e in entri),
           'total_goyang': sum(e.get('goyang_jml', 0) for e in entri),
           'total_ragu': sum(hakim_counts(e)[1] for e in entri),
           'total_curiga': sum(hakim_counts(e)[2] for e in entri)},
          open('_sketsa/pola_bidang.json', 'w'), ensure_ascii=False, indent=1)
print('total panggilan(json):', sum(panggilan_total(e) or 0 for e in entri))
print('total goyang:', sum(e.get('goyang_jml', 0) for e in entri),
      'ragu:', sum(hakim_counts(e)[1] for e in entri),
      'curiga:', sum(hakim_counts(e)[2] for e in entri))
print('entri label bab=0:', [e['kode'] for e in entri if label_counts(e)['bab'] == 0])
print('entri chapter>0:', [(e['kode'], e['_profil']['chapter']) for e in entri if e['_profil']['chapter']])
print('entri romawi_tanpa_bab>0:', [(e['kode'], e['_profil']['romawi_tanpa_bab_jml']) for e in entri if e['_profil']['romawi_tanpa_bab_jml'] > 0])
print('entri pemisah>0:', [(e['kode'], e['_profil']['pemisah_gabung_jml']) for e in entri if e['_profil']['pemisah_gabung_jml'] > 0])
print('entri rasio_inggris>=0.02:', [(e['kode'], e['_profil']['rasio_inggris']) for e in entri if e['_profil']['rasio_inggris'] >= 0.02])
print('entri kti_d3:', [e['kode'] for e in entri if e['_profil']['kti_d3']])
print('entri jml_bab==4:', [(e['kode'], e['_profil']['bab_romawi'], e['_profil']['bab_arab']) for e in entri if e['_profil']['jml_bab_terdeteksi'] == 4])
print('entri jml_bab==0:', [e['kode'] for e in entri if e['_profil']['jml_bab_terdeteksi'] == 0])
print('entri NUL>0:', [(e['kode'], e['_profil']['nul_jml']) for e in entri if e['_profil']['nul_jml'] > 0])
print('entri huruf_berspasi>20:', [(e['kode'], e['_profil']['huruf_berspasi_jml']) for e in entri if e['_profil']['huruf_berspasi_jml'] > 20])
print('entri tabel_baris>100:', [(e['kode'], e['_profil']['tabel_baris_pipa']) for e in entri if e['_profil']['tabel_baris_pipa'] > 100])
print('entri sistematika:', [e['kode'] for e in entri if e['_profil']['sistematika']])

# --- tabel ringkas untuk pembagian ---
json.dump([{'kode': e['kode'], 'grup': e['_grup'], 'bidang': e['bidang'],
            'nama': e.get('nama'), 'teks': e['_teks'],
            'panggilan': panggilan_total(e), 'goyang': e.get('goyang_jml', 0),
            'label': label_counts(e), 'hakim_ragu': hakim_counts(e)[1],
            'hakim_curiga': hakim_counts(e)[2], 'profil': e['_profil']}
           for e in entri],
          open('_sketsa/tabel_latih112.json', 'w'), ensure_ascii=False, indent=1)
print('tabel tersimpan')
