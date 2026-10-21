"""UJI 4 — PETA SATU PANGGILAN (butir 1). SEMUA kandidat 1 kali kirim ke Jev.

UJI 3: 4 pilihan (bab/subbab/paragraf/biasa) → TEPAT semua, tapi 35,7 dtk
       = 7 panggilan (7 gelombang × 8 kandidat).
UJI 4: SEMUA kandidat BAB I (≈300 baris) dikirim DALAM SATU panggilan Jev.
       Pertanyaan: apakah tetap tepat? berapa lama? berapa biaya?

BENTUK: paket = {c0: {tengah, sebelum, sesudah}, c1: {...}, …}
        tanya = {c0: {type: choice, instructions: …, criteria: {…}}, c1: …}

PANGKAS: baris jendela dipotong supaya total bahan < 60.000 kar (batas panggilan).
"""
import sys, json, time
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

BARIS_AWAL, BARIS_AKHIR = 354, 665
KUNCI_BAB = {354}
KUNCI_SUB = {358, 606, 620, 638}
AMBANG_MUTU = 0.80


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        teks = _teks_dari_berkas(p, fb.nama or '') or ''
        baris = teks.split('\n')
        print('═' * 74)
        print(f'📄 fid={fid} {(fb.nama or "")[:46]}')
        print('🎯 UJI 4: SEMUA kandidat BAB I dalam SATU panggilan Jev')

        kand = []
        for i in range(BARIS_AWAL, min(BARIS_AKHIR, len(baris))):
            s = ' '.join(baris[i].split())
            if not s or len(s) > 70:
                continue
            kand.append((i, s))
        print(f'   Kandidat = {len(kand)} baris')

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return f'L{j:06d}| ' + ' '.join(baris[j].split())[:70]

        paket, tanya = {}, {}
        for n, (i, _s) in enumerate(kand):
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
        bahan = json.dumps(paket, ensure_ascii=False)
        print(f'   Bahan = {len(bahan):,} kar · pertanyaan = {len(tanya)}')
        if len(bahan) > 60000:
            print('   ⚠️ bahan > 60.000 kar — akan dipotong oleh satpam')

        t0 = time.time()
        try:
            jw = satpam.tanya_bebas_mutu(bahan[:60000], tanya) or {}
        except Exception as e:                                  # noqa: BLE001
            print(f'   ❌ GAGAL: {type(e).__name__}: {e}')
            return
        dtk = time.time() - t0

        hasil = {}
        print(f'\n   ✅ 1 panggilan selesai: {dtk:.1f} dtk')
        for n, (i, s) in enumerate(kand):
            b = jw.get(f'c{n}') or {}
            pilih = b.get('choice')
            if isinstance(pilih, dict):
                pilih = pilih.get('id') or pilih.get('label')
            hasil[i] = pilih
        bab_k = {i for i, v in hasil.items() if v == 'bab'}
        sub_k = {i for i, v in hasil.items() if v == 'subbab'}
        par_k = {i for i, v in hasil.items() if v == 'paragraf'}
        print(f'   ⇒ BAB     : {len(bab_k)} → kunci ketemu {len(bab_k & KUNCI_BAB)}/{len(KUNCI_BAB)}')
        print(f'   ⇒ SUB-BAB : {len(sub_k)} → kunci ketemu {len(sub_k & KUNCI_SUB)}/{len(KUNCI_SUB)}')
        print(f'   ⇒ PARAGRAF: {len(par_k)}')
        print(f'   ⇒ dijawab : {len([v for v in hasil.values() if v])}/{len(kand)}')
        if KUNCI_SUB - sub_k:
            print(f'   ⇒ SUB TERLEWAT: {[(i, hasil.get(i)) for i in sorted(KUNCI_SUB - sub_k)]}')
        print('\n   BARIS berlabel bab/subbab:')
        for i in sorted(set(bab_k) | set(sub_k)):
            print(f'      {"🅱️" if i in bab_k else "🔷"} L{i:06d} {hasil[i]:7s} | {baris[i].strip()[:52]}')
        print('\n   PARAGRAF (8 pertama):')
        for i in sorted(par_k)[:8]:
            print(f'      📄 L{i:06d} | {baris[i].strip()[:56]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
