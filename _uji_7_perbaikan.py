"""UJI 7 — PERBAIKAN ①+② (BELUM SENTUH APP, cuma di skrip uji).

PERBAIKAN ① SAMBUNG BARIS TERPOTONG (pembersih bahan, FAKTA bukan tebakan):
   Baris yang berakhir dengan kata sambung / tanda yang belum selesai
   ("Pada", "antara", "dan", "yang", "dengan", "di", "ke", "untuk", "dari",
    "atau", "karena", "sedangkan", "yaitu", "adalah", ":" ) ⇒ BELUM SELESAI
   ⇒ disambung ke baris berikutnya SEBELUM dikirim ke Jev.
   Ini membersihkan BAHAN (patahan ekstraksi PDF), bukan menyelesaikan tugas Jev.

PERBAIKAN ② PERTAJAM DEFINISI (bukan larangan — keterangan):
   criteria diperjelas:
     bab      : "Awal BAB (BAB I, BAB II) ATAU judul bab di baris terpisah
                 (PENDAHULUAN, TINJAUAN PUSTAKA, METODE PENELITIAN)"
     subbab   : "Awal SUB-BAB = bagian BERNOMOR (1.1, 2.1.3). JANGAN butir
                 bernomor (1. 2. 3.) di bawah Rumusan Masalah/Tujuan/Hipotesis"

BANDING: sebelum (uji 6) vs sesudah perbaikan. Cek 4 kesalahan Bos + goyang.
"""
import sys, json, time, re
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

BARIS_AWAL, BARIS_AKHIR = 354, 665
PUTARAN = 3
MAKS_KANDIDAT = 120   # jaga panggilan tetap ringan
# kata yang menandakan baris BELUM selesai (FAKTA, bukan tebakan)
GANTUNG = {'pada', 'antara', 'dan', 'yang', 'dengan', 'di', 'ke', 'untuk', 'dari',
           'atau', 'karena', 'sedangkan', 'yaitu', 'adalah', 'oleh', 'ini', 'itu',
           'juga', 'serta', 'agar', 'supaya', 'bila', 'jika', 'seperti', 'dalam',
           'terhadap', 'pengaruh', 'hubungan', 'melalui', 'yaitu:', 'adalah:'}
KRITERIA = {
    'bab': ('Awal BAB (BAB I, BAB II) ATAU JUDUL BAB di baris terpisah '
            '(PENDAHULUAN, TINJAUAN PUSTAKA, METODE PENELITIAN)'),
    'subbab': ('Awal SUB-BAB = bagian BERNOMOR di dalam bab (1.1, 2.1.3) atau '
               'judul bagian yang berdiri sendiri. BUKAN butir bernomor '
               '(1. 2. 3.) di bawah Rumusan Masalah/Tujuan/Hipotesis'),
    'paragraf': ('Awal PARAGRAF BARU = kalimat pertama paragraf. Baris LANJUTAN '
                 'dari kalimat sebelumnya BUKAN awal paragraf'),
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}
BOS_SOROT = {356: 'judul bab?', 570: 'lanjutan (Pada)', 602: 'lanjutan (antara)',
             608: 'butir 1.2', 662: 'judul bab'}


def bersihkan(baris, awal, akhir):
    """Sambung baris yang berakhir kata menggantung (FAKTA)."""
    out, nyambung = [], 0
    i = awal
    while i < akhir:
        s = baris[i].strip()
        if not s:
            out.append((i, ''))
            i += 1
            continue
        gab = s
        asal = [i]
        while True:
            kata = gab.rstrip().rstrip('.,;:').split()[-1].lower() if gab.strip() else ''
            if kata in GANTUNG and i + 1 < akhir:
                j = i + 1
                while j < akhir and not baris[j].strip():
                    j += 1
                if j < akhir:
                    gab = gab.rstrip() + ' ' + baris[j].strip()
                    asal.append(j)
                    nyambung += 1
                    i = j
                    continue
            break
        out.append((asal[0], gab))
        i += 1
    return out, nyambung


def jalankan(paket, tanya, alamat):
    try:
        jw = satpam.tanya_bebas_mutu(json.dumps(paket, ensure_ascii=False)[:58000], tanya) or {}
    except Exception as e:                                      # noqa: BLE001
        print(f'   ❌ GAGAL: {type(e).__name__}: {e}')
        return {}
    out = {}
    for nm, _a in alamat:
        v = (jw.get(nm) or {}).get('choice')
        if isinstance(v, dict):
            v = v.get('id') or v.get('label')
        out[nm] = v
    return out


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        awal, akhir = BARIS_AWAL, min(BARIS_AKHIR, len(baris))
        print('═' * 74)
        print(f'📄 fid={fid} · UJI 7: PERBAIKAN ①+② ({PUTARAN}× putaran)')

        bersih, nyambung = bersihkan(baris, awal, akhir)
        bersih = bersih[:MAKS_KANDIDAT]   # batasi supaya panggilan ringan
        print(f'   ① Baris disambung: {nyambung} (patahan ekstraksi)')
        print(f'      sebelum {akhir-awal} baris → sesudah {len(bersih)} bahan')

        # alamat: nama → (baris_asli, teks)
        alamat = [(f'c{n}', (i, t)) for n, (i, t) in enumerate(bersih)]
        paket, tanya = {}, {}
        idx = {i: t for i, t in bersih}
        for nm, (i, t) in alamat:
            def _g(j):
                return f'L{j:06d}| ' + (idx.get(j) or ' '.join(baris[j].split()))[:60] \
                    if 0 <= j < len(baris) else '(tepi)'
            paket[nm] = {'sebelum': _g(i - 2)[:60], 'tengah': ('L%06d| ' % i) + t[:60],
                         'sesudah': _g(i + 1)[:60]}
            tanya[nm] = {
                'type': 'choice',
                'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah akademik. '
                                 f'Baris tengah ini perannya apa?'),
                'criteria': dict(KRITERIA),
            }
        print(f'   Kandidat = {len(alamat)} · bahan = {len(json.dumps(paket, ensure_ascii=False)):,} kar')

        hasil = {}
        for k in range(PUTARAN):
            t0 = time.time()
            h = jalankan(paket, tanya, alamat)
            dtk = time.time() - t0
            for nm, (i, _t) in alamat:
                hasil.setdefault(i, []).append(h.get(nm))
            print(f'   ▶ putaran {k+1}: {dtk:.1f} dtk')

        goyang = [(i, v) for i, v in hasil.items() if len(set(v)) > 1]
        print(f'\n   🎯 GOYANG sesudah perbaikan: {len(goyang)} baris '
              f'(sebelumnya 5)')
        for i, v in goyang:
            print(f'      L{i:06d} {"|".join(str(x) for x in v)} | {baris[i].strip()[:44]}')

        print(f'\n   🔍 4 BARIS YANG BOS SOROT SESUDAH PERBAIKAN:')
        for t, ket in BOS_SOROT.items():
            v = hasil.get(t)
            if v:
                tanda = '⚠️ GOYANG' if len(set(v)) > 1 else ('stabil')
                print(f'      L{t:06d} [{tanda}] {v} | {ket} | {baris[t].strip()[:36]}')

        # ringkas label
        from collections import Counter
        final = {i: (v[0] if v else None) for i, v in hasil.items()}
        print(f'\n   label akhir: {dict(Counter(final.values()))}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
