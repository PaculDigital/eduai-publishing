"""UJI A: Jev menilai BARIS KOSONG — pemisah atau bukan (fid=104).

Masalah: fid=104 memisah TIAP baris dengan baris kosong ⇒ `_kandidat_sambung`
melewatinya (`if not a or not b: continue`) ⇒ 12.916 baris sampah tetap.

Rancangan (fakta POSITIF, 1 pertanyaan per pasangan, noul tanpa criteria):
  KODE kirim pasangan lintas-baris-kosong dengan FAKTA:
    · baris atas (teks + apakah berakhir tanda akhir kalimat)
    · baris bawah (teks)
  JEV jawab: apakah baris bawah MELANJUTKAN kalimat baris atas?

Ukur: berapa persen BENAR — bandingkan ke MATA MANUSIA (10 pasangan contoh).
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import jev                                              # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: E402
from app.models import FileBerkas                                # noqa: E402

FID = 104


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
    t = bersih(FID)
    baris = [(' '.join(x.split())) for x in t.split('\n')]

    #  KODE: cari pasangan yang DIPISAH TEPAT 1 baris kosong (L kosong di antaranya)
    pasangan = []
    for n in range(1, len(baris)):
        if baris[n] and baris[n - 1] == '' and n >= 2 and baris[n - 2]:
            pasangan.append(n)          # n = baris bawah; n-1 kosong; n-2 atas
    print(f'fid={FID}: pasangan lintas-baris-kosong = {len(pasangan)}')

    #  ambil 20 contoh
    contoh = pasangan[:20]
    print('\n=== KIRIM KE JEV (20 pasangan) ===')
    state_baris, tanya = [], {}
    for n in contoh:
        atas, bawah = baris[n - 2][:150], baris[n][:150]
        state_baris.append(f'L{n-2:05d}| {atas}')
        state_baris.append(f'L{n:05d}| {bawah}')
        tanya[f'L{n:05d}'] = {'instructions':
                              (f'Does line L{n:05d} pick up mid-sentence, continuing a '
                               f'sentence left unfinished at the end of line L{n-2:05d}?'),
                              'type': 'noul'}
    bahan = '\n'.join(state_baris)
    print(f'   state {len(bahan)} kar · {len(tanya)} pertanyaan')

    if not jev.cek_siap().get('siap'):
        print('   Jev TIDAK SIAP:', jev.cek_siap())
        return
    jawab = jev.tanya(bahan, tanya)
    if not jawab:
        print('   Jev tidak menjawab')
        return

    print('\n=== HASIL (nilai + teks; MANUSIA yang menilai benar/salah) ===')
    for n in contoh:
        key = f'L{n:05d}'
        v = (jawab.get(key) or {}).get('noul')
        print(f'   {key} noul={v}')
        print(f'      ATAS : {baris[n-2][:78]!r}')
        print(f'      BAWAH: {baris[n][:78]!r}')
        print()


if __name__ == '__main__':
    main()
