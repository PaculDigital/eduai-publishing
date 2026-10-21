"""UJI 15 — ① BERPAGAR + ④ + ⑤ (semua KODE, dengan pagar huruf kecil).

Masalah uji 14: ① menyambung baris BERIKUTNYA yang ternyata JUDUL
   "…dengan" → "1.4.2 Kegunaan Praktis" ikut tersambung (padahal judul!)
   "…yang"   → "dengan penelitian ini." jadi tanggungan → Jev bingung

PAGAR ① (usul Bos: huruf kecil):
   Sambung HANYA KALAU baris berikutnya:
      ✅ DIAWALI HURUF KECIL (bukan HURUF BESAR SEMUA)
      ✅ BUKAN judul bernomor bertingkat (1.4.2 / 2.1.3)
      ✅ BUKAN penanda bab (BAB I / BAB II)
      ✅ BUKAN caption (Tabel/Gambar + nomor)
   ⇒ kalau salah satu dilanggar: JANGAN sambung (biar Jev yang putuskan)

Uji: Tesis 78 BAB I (354-665) + Asih (300-420).
"""
import sys, json, time, re
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

PUTARAN = 3
KRITERIA = {
    'bab': 'Awal BAB (mis. BAB I, BAB II)',
    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}
GANTUNG = {'pada', 'antara', 'dan', 'yang', 'dengan', 'di', 'ke', 'untuk', 'dari',
           'atau', 'karena', 'sedangkan', 'yaitu', 'adalah', 'oleh', 'ini', 'itu',
           'juga', 'serta', 'agar', 'supaya', 'bila', 'jika', 'seperti', 'dalam',
           'terhadap', 'melalui', 'akan', 'telah', 'sudah', 'masih', 'dapat',
           'tidak', 'lebih', 'para', 'suatu', 'sebuah'}
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
POLA_BAB = re.compile(r'^BAB\s+([IVX]+)\s*$', re.I)
# penanda daftar (FAKTA, sama seperti peta_halus_jev.py resmi)
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')
POLA_JUDUL_NOMOR = re.compile(r'^\d+\.\d+(\.\d+)*[.\s]')     # 1.4.2 / 2.1.3


def boleh_disambung(s):
    """PAGAR (usul Bos): apakah baris ini BOLEH jadi tanggungan sambungan?"""
    if not s:
        return False
    if POLA_JUDUL_NOMOR.match(s):          # 1.4.2 Kegunaan Praktis = JUDUL
        return False
    if POLA_BAB.match(s):                  # BAB II
        return False
    if POLA_CAPTION.match(s) or POLA_SUMBER.match(s) or POLA_MARKER.match(s):
        return False
    if s[:1].isupper() and s == s.upper():  # HURUF BESAR SEMUA = judul/penanda
        return False
    return True                             # sisanya (diawali huruf kecil) = lanjutan


def bersihkan(baris, awal, akhir):
    out, nyambung, tolak = [], [], []
    i = awal
    while i < akhir:
        s = baris[i].strip()
        if not s:
            i += 1
            continue
        gab, asal = s, [i]
        while True:
            kata = re.sub(r'[.,;:!?"”’]+$', '', gab).split()[-1].lower() if gab.strip() else ''
            if kata in GANTUNG and i + 1 < akhir:
                j = i + 1
                while j < akhir and not baris[j].strip():
                    j += 1
                if j < akhir and boleh_disambung(baris[j].strip()):
                    gab = gab.rstrip() + ' ' + baris[j].strip()
                    asal.append(j)
                    nyambung.append(i)
                    i = j
                    continue
                elif j < akhir:
                    tolak.append((i, baris[j].strip()[:40]))
            break
        out.append((asal[0], gab, asal))
        i += 1
    return out, nyambung, tolak


def saring(bersih):
    keluar, gabung, buang = [], {}, []
    k, n = 0, len(bersih)
    while k < n:
        i, t, asal = bersih[k]
        if (POLA_CAPTION.match(t) or POLA_SUMBER.match(t) or POLA_MARKER.match(t)
                or _PEMBUANG.match(t) or _TITIK_ISI.search(t)):
            buang.append(i)
            k += 1
            continue
        m = POLA_BAB.match(t)
        if m and k + 1 < n:
            i2, t2, asal2 = bersih[k + 1]
            if t2 and t2 == t2.upper() and len(t2) > 4 and not POLA_CAPTION.match(t2):
                keluar.append((i, f'{t} {t2}', asal + asal2))
                gabung[i] = (t, t2)
                k += 2
                continue
        keluar.append((i, t, asal))
        k += 1
    return keluar, gabung, buang


def uji(fid, awal, akhir, judul, sorot):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        akhir = min(akhir, len(baris))
        bersih, nyambung, tolak = bersihkan(baris, awal, akhir)
        kand, gabung, buang = saring(bersih)
        print('═' * 72)
        print(f'📄 UJI 15: fid={fid} {judul} · {awal}-{akhir}')
        print(f'   ① disambung {len(nyambung)} · ⛔ DITOLAK pagar {len(tolak)} · '
              f'④ gabung {len(gabung)} · ⑤ buang {len(buang)}')
        for i, t in tolak[:6]:
            print(f'      ⛔ L{i:06d} berakhir kata menggantung TAPI tidak disambung '
                  f'(baris berikut judul): "{t}"')
        print(f'   kandidat {len(kand)}')

        def _t(j):
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58] \
                if 0 <= j < len(baris) else '(tepi)'

        alamat, paket, tanya = [], {}, {}
        for n, (i, t, asal) in enumerate(kand):
            nm = f'c{n}'
            alamat.append((nm, i, asal))
            paket[nm] = {'sebelum': _t(asal[0] - 1), 'tengah': ('L%06d| ' % i) + t[:70],
                         'sesudah': _t(max(asal) + 1)}
            tanya[nm] = {'type': 'choice',
                         'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah '
                                          f'akademik. Baris tengah ini perannya apa?'),
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        print(f'   bahan {len(bahan):,} kar')

        putaran = []
        for k in range(PUTARAN):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan[:58000], tanya) or {}
            print(f'   ▶ putaran {k+1}: {time.time()-t0:.1f} dtk '
                  f'({len([v for v in jw.values() if v])}/{len(kand)})')
            putaran.append(jw)
            time.sleep(1.0)

        hasil = {}
        for nm, i, _asal in alamat:
            vs = []
            for jw in putaran:
                v = (jw.get(nm) or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                vs.append(v)
            hasil[i] = vs
        goyang = [(i, v) for i, v in hasil.items() if len(set(v)) > 1]
        # ATURAN AMAN (Bos pilih A): goyang / kosong ⇒ JANGAN tandai
        for i, v in goyang:
            hasil[i] = ['biasa']
        for i in list(hasil):
            if any(x is None for x in hasil[i]):
                hasil[i] = ['biasa']
        print(f'   🎯 GOYANG: {len(goyang)} dari {len(hasil)} '
              f'({100*len(goyang)/max(1,len(hasil)):.1f}%)')
        for i, v in goyang:
            print(f'      L{i:06d} {v} | {baris[i].strip()[:44]}')

        if sorot:
            print('   🔍 BARIS YANG BOS SOROT:')
            for t in sorot:
                if t in gabung:
                    print(f'      L{t:06d} ✅ DIGABUNG: "{gabung[t][0]} {gabung[t][1]}"')
                elif t in buang:
                    print(f'      L{t:06d} ✅ DIBUANG (caption)')
                elif t in hasil:
                    gy = '⚠️GOYANG' if len(set(hasil[t])) > 1 else 'stabil'
                    print(f'      L{t:06d} [{gy}] {hasil[t]} | {baris[t].strip()[:40]}')
                else:
                    ny = any(t in a for _i, _t, a in kand)
                    print(f'      L{t:06d} {"disambung" if ny else "tidak jadi kandidat"}')
        print('   🔎 label judul:')
        for i in sorted(hasil):
            v = hasil[i][0]
            if v in ('bab', 'subbab'):
                emo = '🅱️' if v == 'bab' else '🔷'
                print(f'      {emo} L{i:06d} {v:7s} | {baris[i].strip()[:44]}')
    finally:
        db.close()


if __name__ == '__main__':
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    awa = int(sys.argv[2]) if len(sys.argv) > 2 else 354
    akh = int(sys.argv[3]) if len(sys.argv) > 3 else 665
    jdl = sys.argv[4] if len(sys.argv) > 4 else 'TESIS78'
    srt = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 5 else []
    uji(fid, awa, akh, jdl, srt)
