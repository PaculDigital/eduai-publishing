"""PETA 3 TINGKAT v2 — GELOMBANG (batch) supaya naskah besar TIDAK kena 503.

AKAR (terukur 08Okt26): 1.034 kandidat / 165.610 kar → 503.
   Batas aman terukur: 156 tanya / 20.622 kar.
   ⚠️ ATURAN BOS: 503 ⇒ JANGAN vonis "batas tetap"; ulangi dulu.
   Sudah diulang: 9router sehat (938 model) + Jev 1 tanya ✅ ⇒ 503 = BAHAN TERLALU BESAR.

OBAT (bukan menyempitkan Jev): bagi kandidat jadi GELOMBANG ≤ BATAS_AMAN tanya/kar,
   tiap gelombang 1 panggilan Jev (Jev tetap membaca KONTEKS LENGKAP tiap gelombang).

GELOMBANG: BATAS_TANYA = 120 · BATAS_KAR = 18.000 (di bawah batas aman 156/20.622).
"""
import sys, json, time, re
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam, state

BATAS_TANYA = 120
BATAS_KAR = 18000
AMBANG_CAPTION = 70
KRITERIA = {
    'bab': 'Awal BAB (mis. BAB I, BAB II)',
    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
POLA_BAB = re.compile(r'^BAB\s+([IVX]+)\s*$', re.I)
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')

# ── ATURAN 4 (SPSS): daftar TERTUTUP header output SPSS (huruf kecil semua).
#    Hanya exact-match ⇒ sub-bab Indonesia ("Uji Reliabilitas") tak akan cocok.
_SPSS_HEADER = {
    'reliability statistics',
    'item-total statistics',
    'item statistics',
    'scale statistics',
    'summary item statistics',
    'descriptive statistics',
    'correlations',
    'model summary',
    'anova',
    'coefficients',
    'variables entered/removed',
    'case processing summary',
    'total variance explained',
    'component matrix',
    'rotated component matrix',
}


def _spss_header(s):
    """Header output SPSS (Inggris) — bukan judul sub-bab skripsi."""
    t = s.strip().lower()
    if t in _SPSS_HEADER:
        return True
    # Sufiks footnote SPSS menempel langsung: 'Coefficientsa',
    # 'Model Summaryb' ⇒ kupas 1 huruf akhir, cek sisanya.
    return len(t) > 2 and t[-1].islower() and t[:-1] in _SPSS_HEADER


# ── ATURAN D1 (putusan Bos 09 Okt): BLOK SISTEMATIKA PENULISAN ────────────
#    Naskah skripsi sering memuat blok "SISTEMATIKA PENULISAN" yang menyebut
#    SEMUA judul bab berurutan rapat (BAB I..V, masing-masing diikuti satu
#    paragraf "Bab ini berisi…") ⇒ MENUTUPI bab asli & bikin 10 label BAB.
#    Deteksi DETERMINISTIK (tanpa AI): ≥3 penyebutan "BAB X" dalam ~30 baris
#    berurutan, yang masing-masing diikuti baris berawalan "Bab ini".
#    ⛔ AKSI = TANDAI, JANGAN BUANG (data, bukan sampah — pelajaran Uji 8).
def _tandai_sistematika(baris, label, kand):
    """Kembalikan himpunan indeks baris anggota blok SISTEMATIKA."""
    idx_kand = {i for i, _t in kand}
    calon = [i for i in sorted(idx_kand) if label.get(i) == 'bab']
    hasil = set()
    JENDELA = 30          # jarak maksimum antar 'BAB X' dalam satu blok
    MIN_BAB = 3           # minimal jumlah bab dalam blok
    n = len(calon)
    for a in range(n):
        blok, j = [], a
        while j < n and (not blok or calon[j] - blok[-1] <= JENDELA):
            i = calon[j]
            # baris sesudahnya (lewati kosong) harus mulai "Bab ini"
            k = i + 1
            while k < len(baris) and not baris[k].strip():
                k += 1
            if k < len(baris) and re.match(r'^\s*Bab\s+ini\b', baris[k].strip(), re.I):
                blok.append(i)
                j += 1
            else:
                # bukan anggota blok; kalau blok sudah penuh, hentikan
                if len(blok) >= MIN_BAB:
                    break
                j += 1
                if blok and calon[j - 1] - blok[-1] > JENDELA:
                    break
        if len(blok) >= MIN_BAB:
            hasil.update(blok)
    return hasil


def dibuang(s):
    # ATURAN 1 versi B (vonis Bos 09 Okt): baris TABEL.
    #   ≥2 pipa DAN ≤300 kar = PASTI tabel/keluaran SPSS ⇒ buang.
    #   ≥2 pipa tapi PANJANG (>300 kar) = paragraf asli yang pakai '|'
    #     sebagai pemisah biasa ⇒ JANGAN buang, biar Jev putuskan.
    #   Pagar panjang menyelamatkan ~9 paragraf asli di Asih
    #   (L001408 770 kar · L001516 908 kar · L001624 346 kar).
    #   1 pipa masih mungkin kalimat biasa ⇒ TIDAK dibuang.
    #   Batasan sadar: tabel 2 kolom (1 pipa) LOLOS.
    if len(s) <= 300 and s.count('|') >= 2:
        return True
    # ATURAN 3 (vonis Bos 09 Okt): judul KUESIONER PENELITIAN = isi LAMPIRAN,
    #   bukan struktur BAB I-V. Konsisten dengan kebijakan lampiran yang sudah
    #   jalan (LAMPIRAN 1-11, DAFTAR LAMPIRAN sudah dibuang).
    if re.match(r'^\s*KUESIONER\b', s, re.I):
        return True
    if _PEMBUANG.match(s) or _TITIK_ISI.search(s) or POLA_MARKER.match(s):
        return True
    if POLA_SUMBER.match(s):
        return True
    if POLA_CAPTION.match(s) and len(s) <= AMBANG_CAPTION:
        return True
    return False


def susun(fid, awal=None, akhir=None):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        bersih = state.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
        baris = bersih.split('\n')
        if awal is None or awal < 0:
            awal = 0
        if akhir is None or akhir > len(baris):
            akhir = len(baris)

        def _t(j):
            if 0 <= j < len(baris):
                return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58]
            return '(tepi)'

        kand, gabung, buang = [], {}, []
        i = awal
        while i < akhir:
            s = baris[i].strip()
            if not s:
                i += 1
                continue
            if dibuang(s):
                buang.append(i)
                i += 1
                continue
            m = POLA_BAB.match(s)
            if m:
                j = i + 1
                while j < akhir and not baris[j].strip():
                    j += 1
                if j < akhir:
                    s2 = baris[j].strip()
                    if s2 and s2 == s2.upper() and 4 < len(s2) < 70:
                        gabung[i] = (s, s2)
                        i = j + 1
                        continue
                # BAB tanpa judul menyusul → tetap bab
                gabung[i] = (s, '')
                i += 1
                continue
            kand.append((i, s))
            i += 1
        return {'baris': baris, 'kand': kand, 'gabung': gabung, 'buang': buang,
                'awal': awal, 'akhir': akhir, 'nama': fb.nama, 't': _t}
    finally:
        db.close()


def petakan(fid, awal=None, akhir=None, putaran=3):
    d = susun(fid, awal, akhir)
    baris, kand, _t = d['baris'], d['kand'], d['t']

    # ── bagi jadi gelombang ──
    gel, kini, kar = [], [], 0
    for n, (i, t) in enumerate(kand):
        pak = {'sebelum': _t(i - 1), 'tengah': ('L%06d| ' % i) + t[:70], 'sesudah': _t(i + 1)}
        skar = len(json.dumps(pak, ensure_ascii=False))
        if kini and (len(kini) >= BATAS_TANYA or kar + skar > BATAS_KAR):
            gel.append(kini)
            kini, kar = [], 0
        kini.append((n, i, pak))
        kar += skar
    if kini:
        gel.append(kini)

    semua = {i: [] for i, _t in kand}
    waktu, gagal = [], 0
    for gi, g in enumerate(gel):
        paket = {}
        tanya = {}
        for n, i, pak in g:
            nm = 'c%d' % n
            paket[nm] = pak
            tanya[nm] = {'type': 'choice',
                         'instructions': 'Baris `%s.tengah` ada di dalam naskah akademik. '
                                         'Baris tengah ini perannya apa?' % nm,
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        for k in range(putaran):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan, tanya) or {}
            waktu.append(time.time() - t0)
            if not jw:
                gagal += 1
            for n, i, _p in g:
                v = (jw.get('c%d' % n) or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                semua[i].append(v)
            time.sleep(0.7)

    label, goyang = {}, []
    for i, _t in kand:
        vs = [x for x in semua[i] if x]
        dari = {}
        for v in vs:
            dari[v] = dari.get(v, 0) + 1
        utama = max(dari, key=dari.get) if dari else None
        if len(dari) > 1:
            goyang.append((i, semua[i]))
            label[i] = 'biasa'
        else:
            label[i] = utama if utama in ('bab', 'subbab', 'paragraf') else 'biasa'

    # ── ATURAN 2 (vonis Bos 09 Okt) — KOREKSI LABEL, BUKAN SARINGAN BUANG.
    #    Judul sub-bab hampir selalu PENDEK. Kalau Jev bilang 'subbab' tapi
    #    barisnya PANJANG (>300 kar), itu paragraf asli ⇒ label diubah.
    #    ⛔ JANGAN dibuang: paragraf asli sering >300 kar (bencana Uji 8).
    koreksi = []
    for i, _t in kand:
        if label.get(i) == 'subbab' and len(baris[i].strip()) > 300:
            label[i] = 'paragraf'
            koreksi.append(i)

    # ── ATURAN 4 SPSS (vonis Bos 09 Okt) — KOREKSI LABEL, BUKAN BUANG.
    #    Header output SPSS (Inggris) bukan sub-bab skripsi. DIDEMOSI jadi
    #    'biasa', TIDAK dibuang. Daftar TERTUTUP (bukan whack-a-mole):
    #    sub-bab Indonesia ("Uji Reliabilitas") tak akan cocok sebab
    #    daftarnya Bahasa Inggris.
    koreksi_spss = []
    for i, _t in kand:
        if label.get(i) == 'subbab' and _spss_header(baris[i]):
            label[i] = 'biasa'
            koreksi_spss.append(i)

    # ── D1 (putusan Bos 09 Okt): TANDAI blok SISTEMATIKA — JANGAN BUANG.
    sistematika = _tandai_sistematika(baris, label, kand)
    asal = {}
    boleh = {}
    for i, _t in kand:
        if i in sistematika:
            asal[i] = 'sistematika'
            boleh[i] = False      # boleh dipakai fitur? TIDAK
        else:
            asal[i] = 'jev'
            boleh[i] = True

    return {'baris': baris, 'kand': kand, 'label': label, 'goyang': goyang,
            'koreksi_label': koreksi, 'koreksi_spss': koreksi_spss,
            'sistematika': sorted(sistematika), 'asal': asal, 'boleh_dipakai_fitur': boleh,
            'gabung': d['gabung'], 'buang': d['buang'], 'waktu': waktu, 'gagal': gagal,
            'gelombang': len(gel), 'semua': semua, 'awal': d['awal'], 'akhir': d['akhir'],
            'nama': d['nama'], 'kand_jml': len(kand)}


def main():
    fid = int(sys.argv[1])
    awal = int(sys.argv[2]) if len(sys.argv) > 2 else None
    akhir = int(sys.argv[3]) if len(sys.argv) > 3 else None
    jdl = sys.argv[4] if len(sys.argv) > 4 else 'NASKAH'
    sorot = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 5 else []
    r = petakan(fid, awal, akhir)
    emo = {'bab': 'B', 'subbab': 'S', 'paragraf': 'P', 'biasa': '.'}
    print('=' * 72)
    print('PETA 3 TINGKAT — %s (fid=%d) %s-%s' % (jdl, fid, r['awal'], r['akhir']))
    print('   kandidat %d · gelombang %d · gabung %d · buang %d · gagal %d'
          % (r['kand_jml'], r['gelombang'], len(r['gabung']), len(r['buang']), r['gagal']))
    print('   waktu: %s' % ' '.join('%.1f' % w for w in r['waktu']))
    print('   GOYANG: %d' % len(r['goyang']))
    for i, v in r['goyang'][:12]:
        print('      L%06d %s | %s' % (i, v, r['baris'][i].strip()[:40]))
    hitung = {}
    for i, v in r['label'].items():
        hitung[v] = hitung.get(v, 0) + 1
    print('   HITUNG: %s' % hitung)
    print('   LABEL (bukan biasa):')
    for i, v in sorted(r['label'].items()):
        if v != 'biasa':
            print('      [%s] L%06d %s' % (emo[v], i, r['baris'][i].strip()[:48]))
    if sorot:
        print('   SOROT BOS:')
        for t in sorot:
            if t in r['gabung']:
                print('      L%06d GABUNG: %s' % (t, ' '.join(r['gabung'][t])))
            elif t in r['buang']:
                print('      L%06d DIBUANG' % t)
            elif t in r['label']:
                print('      L%06d [%s] %s' % (t, emo[r['label'][t]], r['baris'][t].strip()[:44]))
            else:
                print('      L%06d tidak jadi kandidat' % t)


if __name__ == '__main__':
    main()
