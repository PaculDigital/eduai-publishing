"""UJI 6 — APAKAH JEV GOYANG? (input SAMA, dijalankan 3×)

Bos: "Coba jalankan 2-3 kali untuk input yang sama; kalau hasilnya goyang,
      boundary keputusannya belum stabil."

⇒ Kirim bahan PERSIS SAMA 3× ke Jev, catat jawaban per baris, hitung
   berapa baris yang jawabannya BEDA antar putaran.
"""
import sys, json, time
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

BARIS_AWAL, BARIS_AKHIR = 354, 665
PUTARAN = 3


def jalankan(paket, tanya):
    try:
        jw = satpam.tanya_bebas_mutu(json.dumps(paket, ensure_ascii=False)[:58000], tanya) or {}
        out = {}
        for nm in paket:
            v = (jw.get(nm) or {}).get('choice')
            if isinstance(v, dict):
                v = v.get('id') or v.get('label')
            out[nm] = v
        return out
    except Exception as e:                                      # noqa: BLE001
        print(f'   ❌ GAGAL: {type(e).__name__}: {e}')
        return {}


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        awal, akhir = BARIS_AWAL, min(BARIS_AKHIR, len(baris))
        print('═' * 74)
        print(f'📄 fid={fid} · UJI 6: JEV GOYANG? ({PUTARAN}× input SAMA)')

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return f'L{j:06d}| ' + ' '.join(baris[j].split())[:60]

        kand = [i for i in range(awal, akhir) if baris[i].strip()]
        paket, tanya = {}, {}
        for n, i in enumerate(kand):
            nm = f'c{n}'
            paket[nm] = {'sebelum': _b(i - 1), 'tengah': _b(i), 'sesudah': _b(i + 1)}
            tanya[nm] = {
                'type': 'choice',
                'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah akademik. '
                                 f'Baris tengah ini perannya apa?'),
                'criteria': {
                    'bab': 'Awal BAB (mis. BAB I, BAB II)',
                    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
                    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
                    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
                },
            }
        print(f'   Kandidat = {len(kand)} · bahan = {len(json.dumps(paket, ensure_ascii=False)):,} kar')

        putaran = []
        for k in range(PUTARAN):
            t0 = time.time()
            h = jalankan(paket, tanya)
            dtk = time.time() - t0
            putaran.append(h)
            n_jwb = len([v for v in h.values() if v])
            print(f'   ▶ putaran {k+1}: {dtk:.1f} dtk · dijawab {n_jwb}/{len(kand)}')

        # banding
        goyang = []
        for n, i in enumerate(kand):
            nm = f'c{n}'
            vs = [pu.get(nm) for pu in putaran]
            if len(set(vs)) > 1:
                goyang.append((i, vs, ' '.join(baris[i].split())[:52]))
        print(f'\n   {"="*66}')
        print(f'   🎯 GOYANG: {len(goyang)} dari {len(kand)} baris '
              f'({100*len(goyang)/max(1,len(kand)):.0f}%) jawabannya BEDA antar putaran')
        for i, vs, s in goyang:
            print(f'      L{i:06d} {" | ".join(str(v) for v in vs)}')
            print(f'               "{s}"')
        # rinci: khusus baris yang Bos nilai
        print(f'\n   🔍 BARIS YANG BOS SOROT:')
        for target in (356, 570, 602, 608, 662):
            if target in kand:
                n = kand.index(target)
                vs = [pu.get(f'c{n}') for pu in putaran]
                tanda = '⚠️ GOYANG' if len(set(vs)) > 1 else 'stabil'
                print(f'      L{target:06d} [{tanda}] {vs} | {baris[target].strip()[:44]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
