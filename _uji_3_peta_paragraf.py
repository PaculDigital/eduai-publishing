"""UJI 3 — PETA 1 PANGGILAN, SAMPAI PARAGRAF (butir 1 + 2).

TUJUAN (putusan Bos 08 Okt):
  "peta digabung SATU (bab + sub-bab + paragraf, satu panggilan Jev)" = YA
  "sampai paragraf (sangat presisi) = seperti duplikasi naskah asli"

HIPOTESIS:
  Satu panggilan Jev, tiap kandidat dapat pertanyaan PILIHAN (tipe choice):
     (a) awal BAB   (b) awal SUB-BAB   (c) awal PARAGRAF BARU   (d) biasa/lanjutan
  ⇒ satu jawaban bisa dipakai merakit SEMUA tingkat sekaligus.

CARA (pola resmi yang sudah terbukti di peta bab + peta halus):
  KODE : ID tiap baris → buang FAKTA pasti bukan judul → tiap kandidat dapat
         JENDELA (baris sebelumnya · tengah · sesudahnya)
  JEV  : 1 panggilan, tipe CHOICE per kandidat (1 pertanyaan, 4 pilihan)
  KODE : rakit 3 tingkat (bab / sub-bab / paragraf) dari jawaban

UJI: naskah Tesis 78 (fid=78), BATASI pada BAB I saja dulu (baris 354-665)
     supaya bisa dibandingkan dengan KUNCI yang sudah terbukti.

KUNCI (sudah terbukti dari uji sebelumnya):
  BAB  : 354 (BAB I)
  SUB  : 358 (1.1) · 606 (1.2) · 620 (1.3) · 638 (1.4)
"""
import sys, json, time
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

GELOMBANG = 8
BARIS_AWAL, BARIS_AKHIR = 354, 665        # BAB I saja
KUNCI_BAB = {354}
KUNCI_SUB = {358, 606, 620, 638}


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
        print(f'🎯 UJI: 1 PANGGILAN, 4 PILIHAN (bab/sub-bab/paragraf/biasa)')
        print(f'   Rentang uji = baris {BARIS_AWAL}-{BARIS_AKHIR} (BAB I)')

        # kandidat: SEMUA baris pendek dalam rentang (tanpa menebak bentuk)
        kand = []
        for i in range(BARIS_AWAL, min(BARIS_AKHIR, len(baris))):
            s = ' '.join(baris[i].split())
            if not s or len(s) > 70:
                continue
            kand.append((i, s))
        print(f'   Kandidat = {len(kand)} baris')

        hasil = {}
        t_total = time.time()
        for gel in range(0, len(kand), GELOMBANG):
            pakai = kand[gel:gel + GELOMBANG]
            paket, tanya = {}, {}
            for n, (i, _s) in enumerate(pakai):
                nm = f'c{n}'
                def _b(j):
                    if j < 0 or j >= len(baris):
                        return '(tepi naskah)'
                    return f'L{j:06d}| ' + ' '.join(baris[j].split())[:85]
                paket[nm] = {
                    'baris_sebelum': _b(i - 1),
                    'tengah': _b(i),
                    'baris_sesudah': _b(i + 1),
                    'baris_sesudah_2': _b(i + 2),
                }
                tanya[nm] = {
                    'type': 'choice',
                    'instructions': (
                        f'Baris `{nm}.tengah` ada di dalam naskah akademik. '
                        f'Baris tengah ini perannya apa?'),
                    'criteria': {
                        'bab': 'Awal BAB (mis. BAB I, BAB II)',
                        'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
                        'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
                        'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
                    },
                }
            try:
                jw = satpam.tanya_bebas_mutu(
                    json.dumps(paket, ensure_ascii=False)[:60000], tanya) or {}
            except Exception as e:                              # noqa: BLE001
                print(f'   ❌ gel.{gel//8+1} GAGAL: {type(e).__name__}: {e}')
                continue
            print(f'\nJEV gel.{gel//8+1}:')
            for n, (i, s) in enumerate(pakai):
                b = jw.get(f'c{n}') or {}
                ch = b.get('choice')
                p_ = None
                if isinstance(ch, dict):
                    ch = ch.get('id') or ch.get('label')
                if isinstance(b.get('bab'), (int, float)):
                    p_ = b['bab']
                pilih = ch if isinstance(ch, str) else str(ch)
                hasil[i] = pilih
                tanda = ''
                if i in KUNCI_SUB:
                    tanda = ' ✅SUB-BAB TEPAT' if pilih == 'subbab' else ' ❌melenceng'
                elif i in KUNCI_BAB:
                    tanda = ' ✅BAB TEPAT' if pilih == 'bab' else ' ❌melenceng'
                emo = {'bab': '🅱️', 'subbab': '🔷', 'paragraf': '📄', 'biasa': '·'}.get(pilih, '?')
                print(f'   {emo} L{i:06d} p={p_} | {pilih:8s} | {s[:44]}{tanda}')
        print(f'\n   ⏱️  total {time.time()-t_total:.1f} dtk')

        # RINGKASAN
        bab_ketemu = {i for i, v in hasil.items() if v == 'bab'}
        sub_ketemu = {i for i, v in hasil.items() if v == 'subbab'}
        par_ketemu = {i for i, v in hasil.items() if v == 'paragraf'}
        print(f'\n   ⇒ BAB     : {len(bab_ketemu)} (kunci {len(KUNCI_BAB)}) → ketemu {len(bab_ketemu & KUNCI_BAB)}')
        print(f'   ⇒ SUB-BAB : {len(sub_ketemu)} (kunci {len(KUNCI_SUB)}) → ketemu {len(sub_ketemu & KUNCI_SUB)}')
        print(f'   ⇒ PARAGRAF: {len(par_ketemu)}')
        lewat = KUNCI_SUB - sub_ketemu
        if lewat:
            print(f'   ⇒ SUB-BAB TERLEWAT: {[(i, hasil.get(i)) for i in sorted(lewat)]}')
        lewat_b = KUNCI_BAB - bab_ketemu
        if lewat_b:
            print(f'   ⇒ BAB TERLEWAT: {[(i, hasil.get(i)) for i in sorted(lewat_b)]}')
        print(f'\n   DAFTAR PARAGRAF TERDETEKSI (10 pertama):')
        for i in sorted(par_ketemu)[:10]:
            print(f'      L{i:06d} | {baris[i].strip()[:56]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
