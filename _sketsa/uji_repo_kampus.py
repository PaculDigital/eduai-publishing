#!/usr/bin/env python3
"""CARI REPOSITORY KAMPUS yang BISA diakses (05Okt26).

Neliti 403 & Garuda 000 → jatuh ke repository kampus. Skrip ini MENGUJI
banyak host repository: mana yang 200 (bisa diunduh) dan mana yang mati.
Hasilnya dipakai untuk memilih ladang unduh naskah nyata.
"""
import concurrent.futures as cf
import urllib.request

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/151.0.0.0 Safari/537.36')

HOST = [
    'https://repository.unhas.ac.id/',
    'http://repository.unmul.ac.id/',
    'https://repository.ugm.ac.id/',
    'https://etd.repository.ugm.ac.id/',
    'http://repository.unj.ac.id/',
    'https://repository.unair.ac.id/',
    'https://repository.unpad.ac.id/',
    'https://repository.ipb.ac.id/',
    'https://repository.undip.ac.id/',
    'https://repository.uny.ac.id/',
    'https://repository.uin-suska.ac.id/',
    'https://repository.usu.ac.id/',
    'https://digilib.uns.ac.id/',
    'https://repository.unand.ac.id/',
    'https://repository.unbraw.ac.id/',
    'https://lib.unnes.ac.id/',
    'https://eprints.ums.ac.id/',
    'https://eprints.walisongo.ac.id/',
    'https://repository.uinjkt.ac.id/',
    'https://scholar.unand.ac.id/',
    'https://repositori.usu.ac.id/',
    'https://repository.ub.ac.id/',
    'https://repo.unand.ac.id/',
    'https://jurnal.ugm.ac.id/',
    'https://ejournal.upi.edu/',
]


def uji(h: str) -> tuple:
    try:
        req = urllib.request.Request(h, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=18) as r:
            return (h, r.status, len(r.read(2000)))
    except Exception as e:                                     # noqa: BLE001
        kode = getattr(e, 'code', type(e).__name__)
        return (h, kode, 0)


with cf.ThreadPoolExecutor(max_workers=10) as ex:
    hasil = list(ex.map(uji, HOST))

print(f'  {"HOST":52s} {"KODE":>6s}  ISI')
hidup = []
for h, k, n in sorted(hasil, key=lambda x: str(x[1])):
    tanda = '✅' if k == 200 else '❌'
    if k == 200:
        hidup.append(h)
    print(f'  {tanda} {h:50s} {str(k):>6s}  {n}')
print(f'\n  HIDUP: {len(hidup)} dari {len(HOST)}')
with open('/tmp/repo_hidup.txt', 'w') as f:
    f.write('\n'.join(hidup))
