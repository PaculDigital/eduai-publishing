"""UJI A LANJUTAN: Jev menilai baris-kosong untuk SELURUH fid=104.

Ukur (bukan contoh): berapa pasangan, berapa gelombang, waktu, dan
SEBARAN nilai noul — apakah ambang 0,5 memisahkan bersih?
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, '/app')

from app import jev                                              # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: E402
from app.models import FileBerkas                                # noqa: E402

GAL = 120


def bersih(fid: int) -> str:
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        import app.state as S
        return S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
    finally:
        db.close()


def main():
    t0 = time.time()
    t = bersih(104)
    baris = [' '.join(x.split()) for x in t.split('\n')]

    pasangan = [n for n in range(2, len(baris))
                if baris[n] and baris[n - 1] == '' and baris[n - 2]]

    #  TAPI: 104 juga punya baris-kosong yang BERARTI (jarak >1 baris kosong?)
    #  KODE hitung FAKTA: jarak kosong & baris atas berakhir tanda akhir
    print(f'pasangan (persis 1 baris kosong): {len(pasangan)}')
    print(f'waktu persiapan: {time.time()-t0:.1f} dtk')

    semua = {}
    gel = 0
    t1 = time.time()
    for mulai in range(0, len(pasangan), GAL):
        sub = pasangan[mulai:mulai + GAL]
        perlu = sorted({n - 2 for n in sub} | set(sub))
        state = '\n'.join(f'L{n:05d}| {baris[n][:180]}' for n in perlu)
        tanya = {f'L{n:05d}': {'instructions':
                 (f'Does line L{n:05d} pick up mid-sentence, continuing a sentence '
                  f'left unfinished at the end of line L{n-2:05d}?'), 'type': 'noul'}
                 for n in sub}
        jawab = jev.tanya(state, tanya)
        gel += 1
        if jawab:
            semua.update(jawab)
        if gel % 20 == 0:
            print(f'   gelombang {gel}/{(len(pasangan)+GAL-1)//GAL} · '
                  f'{time.time()-t1:.0f} dtk · terjawab {len(semua)}')
    print(f'\nSELESAI: {gel} gelombang · {time.time()-t1:.0f} dtk · '
          f'terjawab {len(semua)}/{len(pasangan)}')

    #  sebaran
    nilai = []
    for n in pasangan:
        v = (semua.get(f'L{n:05d}') or {}).get('noul')
        if v is not None:
            nilai.append(v)
    print(f'nilai terkumpul: {len(nilai)}')
    if nilai:
        nl = sorted(nilai)
        n_ = len(nl)
        print(f'   min {nl[0]:.2f} · p25 {nl[n_//4]:.2f} · median {nl[n_//2]:.2f} '
              f'· p75 {nl[3*n_//4]:.2f} · maks {nl[-1]:.2f}')
        for amb in (0.2, 0.5, 0.7):
            sambung = sum(1 for v in nilai if v >= amb)
            print(f'   ambang {amb}: {sambung} disambung '
                  f'({100*sambung/len(nilai):.0f}%) · '
                  f'{len(nilai)-sambung} dibiarkan')


if __name__ == '__main__':
    main()
