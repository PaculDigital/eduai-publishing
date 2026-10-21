"""UJI BERGIGI gerbang_keluhan_20okt.py — suntik kerusakan, HARUS GAGAL.

ATURAN (pelajaran Bos): gerbang yang tak bisa gagal = gerbang HIASAN.
Suntikan WAJIB di SALINAN di /tmp — DILARANG menyentuh berkas produksi.
"""
import os
import shutil
import sys

sys.path.insert(0, '/app')
import gerbang_keluhan_20okt as G   # noqa: E402

ASLI = '/app/diagram_buku.py'
SALIN = '/tmp/diagram_buku_rusak.py'


def uji(nama, suntik, pakai_brief=False):
    """Suntik kerusakan ke SALINAN, jalankan gerbang → HARUS GAGAL."""
    src = open(ASLI, encoding='utf-8').read()
    rusak = suntik(src)
    if rusak == src:
        return (nama, 'HIASAN', 'suntikan TIDAK mengubah apa pun')

    open(SALIN, 'w', encoding='utf-8').write(rusak)
    sys.path.insert(0, '/tmp')
    for m in ('diagram_buku_rusak',):
        sys.modules.pop(m, None)
    import diagram_buku_rusak as R    # noqa: E402

    lulus, gagal, rincian = G.jalankan(R, cetak=False)

    #  buktikan gerbang menangkap: HARUS ada kegagalan
    if gagal == 0:
        return (nama, 'HIASAN', 'gerbang tetap LULUS padahal dirusak')
    return (nama, 'BERGIGI', f'{gagal} gagal: {rincian[0][:70]}')


def suntik_justify(s):
    """Kembalikan cacat asli: text-align:justify (rata kiri-kanan)."""
    return s.replace('.judul { text-align:center;',
                     '.judul { text-align:justify;')


def suntik_kotak_lebar(s):
    """Kembalikan cacat asli: kotak melebar penuh."""
    return s.replace('.kartu { width:520px; }',
                     '.kartu { width:720px; }\n.alur .tahap { width:100%; }')


def suntik_krem(s):
    """Kembalikan cacat: latar krem."""
    return s.replace('body { background:#FFFFFF;',
                     'body { background:#F5E6C8;')


def suntik_hapus_center(s):
    """Hapus semua text-align:center — teks tidak lagi di tengah."""
    return s.replace('text-align:center', 'text-align:left')


def suntik_monoton(s):
    """Paksa semua bentuk jadi alur — variasi hilang."""
    return s.replace("def pilih_bentuk(judul, ket, tahap=None):",
                     "def pilih_bentuk(judul, ket, tahap=None):\n"
                     "    return 'alur'\n"
                     "def _mati(judul, ket, tahap=None):")


print('=== UJI BERGIGI: gerbang WAJIB menangkap kerusakan ===')
print()
hasil = [
    uji('text-align:justify dikembalikan', suntik_justify),
    uji('kotak melebar 720px + width:100%', suntik_kotak_lebar),
    uji('latar dikembalikan ke krem', suntik_krem),
    uji('semua text-align:center dihapus', suntik_hapus_center),
    uji('variasi bentuk dipaksa jadi alur', suntik_monoton),
]
print()
hiasan = 0
for nama, status, ket in hasil:
    tanda = 'OK ' if status == 'BERGIGI' else 'BURUK'
    if status != 'BERGIGI':
        hiasan += 1
    print(f'  {tanda} [{status}] {nama} — {ket}')

if os.path.exists(SALIN):
    os.remove(SALIN)

print()
print('=' * 60)
print({'bergigi': len(hasil) - hiasan, 'hiasan': hiasan})
sys.exit(0 if hiasan == 0 else 1)
