"""UJI NYATA: hemat token dengan NASKAH ASLI mahasiswa (15Okt26).

Pakai berkas nyata dari DB EduAi (bukan naskah buatan).
Hanya MENGUKUR — tidak memanggil AI, tidak memotong saldo.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from sqlalchemy import select                                    # noqa: E402
from app.models import BerkasPembimbingan, SessionLocal          # noqa: E402
from app import asisten as A                                     # noqa: E402
from app.rute_pembimbing import _isi_naskah                      # noqa: E402

print('═' * 74)
print('  UJI NYATA — HEMAT TOKEN DENGAN NASKAH ASLI MAHASISWA')
print('═' * 74)


class DB:
    """DB tiruan: giliran selalu dari 0 (tidak mengubah apa pun)."""
    def scalar(self, _s): return None
    def add(self, _o): pass


S = SessionLocal()
try:
    #  semua naskah yang benar-benar dipakai di kolaborasi
    berkas = list(S.scalars(select(BerkasPembimbingan).limit(40)))
    print(f'\n[i] {len(berkas)} naskah kolaborasi diperiksa\n')
    total_utuh = total_kirim = n_pecah = 0
    for bk in berkas:
        try:
            teks = _isi_naskah(S, bk)
        except Exception as e:                                   # noqa: BLE001
            print(f'  ⏭  #{bk.id}: tak terbaca ({type(e).__name__})')
            continue
        if not (teks or '').strip():
            continue

        kirim, pos = A._siapkan_kirim(DB(), type('B', (), {'id': bk.id})(), teks)
        judul = (getattr(bk, 'judul', '') or '')[:32]
        if pos < 0:
            print(f'  ➖ #{bk.id:<4} {judul:<32} {len(teks):>7} kar → UTUH')
            continue

        n_pecah += 1
        total_utuh += len(teks)
        total_kirim += len(kirim)
        persen = 100.0 * (len(teks) - len(kirim)) / max(1, len(teks))
        print(f'  ✅ #{bk.id:<4} {judul:<32} {len(teks):>7} → {len(kirim):>6} '
              f'(hemat {persen:>5.1f}%, bagian ke-{pos + 1})')

    print('\n' + '─' * 74)
    if total_utuh:
        print(f'  {n_pecah} naskah DIHEMAT: {total_utuh} kar → {total_kirim} kar '
              f'| HEMAT {100.0 * (total_utuh - total_kirim) / total_utuh:.1f}%')
    else:
        print('  (tak ada naskah yang perlu dipecah)')
finally:
    S.close()
print('═' * 74)
