"""UJI 13 — SARINGAN KODE (⑤ caption + ④ judul bab) — MUSTAHIL whack-a-mole.

Bos pilih A: terapkan 2 saringan KODE (bukan aturan ke Jev):
  ⑤ CAPTION  : baris diawali 'Tabel'/'Gambar' + nomor ⇒ BUKAN kandidat judul (fakta)
  ④ JUDUL BAB: baris HURUF BESAR SEMUA tepat sesudah 'BAB <romawi>' ⇒ KODE gabung
               jadi satu judul bab (Jev TIDAK ditanya)

Uji ulang di DUA naskah: Asih (fid=81, 300-420) + Tesis 78 BAB I (354-665).
Banding: sebelum (uji 12 & 6) vs sesudah.
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
# ── ⑤ caption: fakta, bukan tebakan bentuk ──
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
# ── ④ judul bab: BAB <romawi> diikuti judul HURUF BESAR ──
POLA_BAB = re.compile(r'^BAB\s+([IVX]+)\s*$', re.I)
POLA_BAB_NEMPEL = re.compile(r'^BAB\s+([IVX]+)\s*[A-Z][A-Z\s\-]+$')


def bangun(baris, awal, akhir):
    """Kandidat + gabungan judul bab (④) & buang caption (⑤)."""
    keluar, gabung = [], {}
    i = awal
    while i < akhir:
        s = baris[i].strip()
        if not s:
            i += 1
            continue
        # ⑤ buang caption/sumber/penanda (fakta)
        if POLA_CAPTION.match(s) or POLA_SUMBER.match(s) or POLA_MARKER.match(s):
            i += 1
            continue
        # ④ BAB <romawi> → cek baris berikutnya judul HURUF BESAR
        m = POLA_BAB.match(s)
        if m:
            j = i + 1
            while j < akhir and not baris[j].strip():
                j += 1
            if j < akhir:
                s2 = baris[j].strip()
                if s2 and s2 == s2.upper() and len(s2) > 4 and not POLA_CAPTION.match(s2):
                    keluar.append((i, f'{s} {s2}', [i, j]))     # digabung, Jev tak ditanya judul
                    gabung[i] = (s, s2)
                    i = j + 1
                    continue
        keluar.append((i, s, [i]))
        i += 1
    return keluar, gabung


def uji(fid, awal, akhir, judul, ganti):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        akhir = min(akhir, len(baris))
        kand, gabung = bangun(baris, awal, akhir)
        print('═' * 72)
        print(f'📄 UJI 13: fid={fid} {judul} · {awal}-{akhir}')
        print(f'   ⑤ buang caption/sumber · ④ judul bab digabung di KODE: {len(gabung)}')

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
        print(f'   kandidat {len(kand)} · bahan {len(bahan):,} kar')

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
        print(f'   🎯 GOYANG: {len(goyang)} dari {len(hasil)}')
        for i, v in goyang:
            print(f'      L{i:06d} {v} | {baris[i].strip()[:44]}')

        if ganti:
            print('   🔍 BARIS YANG DIPERIKSA:')
            for t in ganti:
                if t in gabung:
                    print(f'      L{t:06d} ✅ DIGABUNG di kode → tidak ditanya Jev')
                elif t in hasil:
                    print(f'      L{t:06d} {hasil[t]} | {baris[t].strip()[:42]}')
                else:
                    print(f'      L{t:06d} — TIDAK jadi kandidat (dibuang/digabung)')
        print('   🔎 label judul (bab/subbab):')
        for i in sorted(hasil):
            v = hasil[i][0]
            if v in ('bab', 'subbab'):
                emo = '🅱️' if v == 'bab' else '🔷'
                print(f'      {emo} L{i:06d} {v:7s} | {baris[i].strip()[:44]}')
    finally:
        db.close()


if __name__ == '__main__':
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 81
    awa = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    akh = int(sys.argv[3]) if len(sys.argv) > 3 else 420
    jdl = sys.argv[4] if len(sys.argv) > 4 else 'ASIH'
    gnt = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 5 else []
    uji(fid, awa, akh, jdl, gnt)
