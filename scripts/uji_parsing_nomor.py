"""UJI PARSING NOMOR HP — semua format yang mahasiswa ketik (27Sep26).

Format nyata dari lapangan: +62..., 08..., 62..., 8..., spasi, strip,
kurung, titik, WA link, huruf nyasar, kosong, nomor pendek, +62 (0)812.
Target: bersihkan_wa() JADI SATU-SATUNYA parser (app/wa.py memakainya).
"""
from app.pembimbing import bersihkan_wa

# (input mahasiswa, hasil yang diharapkan)
KASUS = [
    ('+6285720505555', '6285720505555'),
    ('085720505555', '6285720505555'),
    ('6285720505555', '6285720505555'),
    ('85720505555', '6285720505555'),
    ('0812-3456-7890', '6281234567890'),
    ('0812 3456 7890', '6281234567890'),
    ('+62 812-3456-7890', '6281234567890'),
    ('0812.3456.7890', '6281234567890'),
    ('(021) 5551234', '62215551234'),          # nomor kota — tetap dirapikan
    ('https://wa.me/6285720505555', '6285720505555'),
    ('', ''),
    ('   ', ''),
    ('abc', ''),
    ('08', ''),                                # terlalu pendek → ditolak
    ('123', ''),                               # terlalu pendek → ditolak
    ('+62 (0) 812-3456-7890', '6281234567890'),  # 0 sisa kode area dibuang
]


def main() -> int:
    ok = gagal = 0
    for masuk, harap in KASUS:
        dapat = bersihkan_wa(masuk)
        status = 'LULUS'
        if dapat != harap:
            status = f'BEDA (dapat {dapat!r})'
            gagal += 1
        else:
            ok += 1
        print(f'{status:24s} {masuk!r:36s} → {dapat!r}')
    print(f'\n{ok} LULUS / {gagal} BEDA (BEDA = temuan, bukan selalu salah)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
