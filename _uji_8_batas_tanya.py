"""UJI 8 — CARI BATAS: berapa JUMLAH PERTANYAAN maksimum yang diterima Jev?

Uji 6: 156 pertanyaan → BERHASIL (1,3 dtk)
Uji 7: 255 pertanyaan → 503 SELALU (walau bahan dikecilkan 43.000→39.209 kar)

⇒ dugaan: batasnya JUMLAH PERTANYAAN, bukan panjang bahan.
   Uji ini: naikkan perlahan 20/50/100/150/200/250 pertanyaan, lihat mana yang 503.
"""
import sys, json, time
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

BARIS_AWAL, BARIS_AKHIR = 354, 665
UJI_N = [20, 50, 100, 150, 200, 250]


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
        print(f'📄 fid={fid} · UJI 8: CARI BATAS JUMLAH PERTANYAAN')

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:55]

        for n_uji in UJI_N:
            pakai = idxs[:n_uji]
            paket, tanya = {}, {}
            for n, i in enumerate(pakai):
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
            bahan = json.dumps(paket, ensure_ascii=False)
            t0 = time.time()
            try:
                jw = satpam.tanya_bebas_mutu(bahan[:58000], tanya)
            except Exception as e:                              # noqa: BLE001
                print(f'   {n_uji:4d} tanya · {len(bahan):6,} kar → ❌ {type(e).__name__}')
                continue
            dtk = time.time() - t0
            if jw:
                n_jwb = len([v for v in jw.values() if v])
                print(f'   {n_uji:4d} tanya · {len(bahan):6,} kar → ✅ {dtk:5.1f} dtk '
                      f'· dijawab {n_jwb}/{n_uji}')
            else:
                print(f'   {n_uji:4d} tanya · {len(bahan):6,} kar → ❌ KOSONG ({dtk:.1f} dtk)')
            time.sleep(1.5)
    finally:
        db.close()


if __name__ == '__main__':
    main()
