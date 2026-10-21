"""UJI 9 — ISOLASI AKAR 503: mana yang memicu?

Fakta:
  ✅ BERHASIL: 156 tanya, jendela {'sebelum','tengah','sesudah'} 60 kar = 20.876 kar
  ❌ GAGAL   : 20-255 tanya, jendela 3 kunci beda' = mulai 503
  ✅ BERHASIL: 1 tanya, bahan 'L000354| BAB I' (polos, tanpa kunci)

Uji ini: naikkan bertahap 1/5/10/20/40/80 tanya dengan bentuk SAMA seperti uji 6
(sebelum/tengah/sesudah, 60 kar) → cari titik gagalnya PERSIS.
"""
import sys, json, time
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

BARIS_AWAL, BARIS_AKHIR = 354, 665
UJI_N = [1, 5, 10, 20, 40, 80, 120, 156]


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        idxs = [i for i in range(BARIS_AWAL, min(BARIS_AKHIR, len(baris)))
                if baris[i].strip()]
        print('═' * 70)
        print(f'📄 fid={fid} · UJI 9: ISOLASI AKAR 503')

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58]

        for n_uji in UJI_N:
            paket, tanya = {}, {}
            for n, i in enumerate(idxs[:n_uji]):
                nm = f'c{n}'
                paket[nm] = {'sebelum': _b(i - 1), 'tengah': _b(i), 'sesudah': _b(i + 1)}
                tanya[nm] = {
                    'type': 'choice',
                    'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah '
                                     f'akademik. Baris tengah ini perannya apa?'),
                    'criteria': {
                        'bab': 'Awal BAB (mis. BAB I)',
                        'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3)',
                        'paragraf': 'Awal PARAGRAF BARU',
                        'biasa': 'Lanjutan/biasa',
                    },
                }
            bahan = json.dumps(paket, ensure_ascii=False)[:58000]
            t0 = time.time()
            try:
                jw = satpam.tanya_bebas_mutu(bahan, tanya)
            except Exception as e:                              # noqa: BLE001
                print(f'   {n_uji:4d} tanya · {len(bahan):6,} kar → ❌ {type(e).__name__}')
                continue
            dtk = time.time() - t0
            if jw:
                n_jwb = len([v for v in jw.values() if v])
                print(f'   {n_uji:4d} tanya · {len(bahan):6,} kar → ✅ {dtk:5.1f} dtk · {n_jwb}/{n_uji}')
            else:
                print(f'   {n_uji:4d} tanya · {len(bahan):6,} kar → ❌ KOSONG ({dtk:.2f} dtk)')
            time.sleep(1.0)
    finally:
        db.close()


if __name__ == '__main__':
    main()
