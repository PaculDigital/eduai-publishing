"""UJI 5 — SEMUA BARIS jadi kandidat (butir 2: paragraf harus ketemu SEMUA).

Uji 4: 1 panggilan 8,0 dtk, bab/subbab TEPAT, tapi PARAGRAF cuma 6 →
       sebab: kandidat dibatasi baris ≤70 kar; awal paragraf sering baris
       panjang / baris setelah baris kosong TIDAK masuk.

UJI 5: KANDIDAT = SEMUA baris (tanpa batas panjang) pada BAB I.
       Pertanyaan Jev TETAP 4 pilihan (bab/subbab/paragraf/biasa).
       Ukur: apakah paragraf ketemu lebih banyak? berapa waktu/bahan?
       Cek juga: apakah BAB/SUB-BAB tetap tepat (tidak rusak karena kandidat banyak).
"""
import sys, json, time, re
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

BARIS_AWAL, BARIS_AKHIR = 354, 665
KUNCI_BAB = {354}
KUNCI_SUB = {358, 606, 620, 638}
MAKS_BAHAN = 58000


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
        print('🎯 UJI 5: SEMUA baris jadi kandidat (paragraf harus ketemu)')

        # kandidat = SEMUA baris berisi (tanpa batas panjang) — TANPA menebak
        kand = []
        for i in range(BARIS_AWAL, min(BARIS_AKHIR, len(baris))):
            s = baris[i].strip()
            if not s:
                continue
            # buang yang PASTI bukan awal apa pun (fakta, bukan tebakan bentuk)
            if re.match(r'^\[\[.*\]\]$', s):            # penanda internal
                continue
            if re.match(r'^(Tabel|Gambar)\s+\d', s, re.I):
                continue
            if re.match(r'^Sumber\s*:', s, re.I):
                continue
            if s.count('.') >= 5 and ' ' not in s[:20]:  # titik-pengarah daftar isi
                continue
            kand.append((i, s))
        print(f'   Kandidat = {len(kand)} baris (SEBELUMNYA hanya 50)')

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return f'L{j:06d}| ' + ' '.join(baris[j].split())[:60]

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
        if len(bahan) > MAKS_BAHAN:
            print(f'   ⚠️ bahan {len(bahan):,} > {MAKS_BAHAN:,} → dipotong di ujung')

        t0 = time.time()
        try:
            jw = satpam.tanya_bebas_mutu(bahan[:MAKS_BAHAN], tanya) or {}
        except Exception as e:                                  # noqa: BLE001
            print(f'   ❌ GAGAL: {type(e).__name__}: {e}')
            return
        dtk = time.time() - t0
        hasil = {}
        for n, (i, _s) in enumerate(kand):
            b = jw.get(f'c{n}') or {}
            v = b.get('choice')
            if isinstance(v, dict):
                v = v.get('id') or v.get('label')
            hasil[i] = v
        bab_k = {i for i, v in hasil.items() if v == 'bab'}
        sub_k = {i for i, v in hasil.items() if v == 'subbab'}
        par_k = {i for i, v in hasil.items() if v == 'paragraf'}
        print(f'\n   ✅ 1 panggilan: {dtk:.1f} dtk · dijawab {len([v for v in hasil.values() if v])}/{len(kand)}')
        print(f'   ⇒ BAB     : {len(bab_k)} → kunci {len(bab_k & KUNCI_BAB)}/{len(KUNCI_BAB)}')
        print(f'   ⇒ SUB-BAB : {len(sub_k)} → kunci {len(sub_k & KUNCI_SUB)}/{len(KUNCI_SUB)}')
        print(f'   ⇒ PARAGRAF: {len(par_k)}   (uji 4 hanya 6)')
        if KUNCI_SUB - sub_k:
            print(f'   ⚠️ SUB TERLEWAT: {[(i, hasil.get(i)) for i in sorted(KUNCI_SUB - sub_k)]}')
        print('\n   🅱️/🔷 bab & sub-bab:')
        for i in sorted(set(bab_k) | set(sub_k)):
            print(f'      {"🅱️" if i in bab_k else "🔷"} L{i:06d} {hasil[i]:7s} | {baris[i].strip()[:50]}')
        print('\n   📄 PARAGRAF (semua):')
        for i in sorted(par_k):
            print(f'      L{i:06d} | {baris[i].strip()[:60]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
