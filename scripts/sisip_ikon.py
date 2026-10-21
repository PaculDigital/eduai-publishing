"""Sisipkan sprite ikon + CSS ke SEMUA template (sekali jalan, aman diulang).

Yang dilakukan tiap template:
  1. Tambah <link rel="stylesheet" href="/static/ikon.css"> sebelum </head>
     (kalau belum ada).
  2. Tambah {{ ikon_sprite() }} tepat setelah <body...> (kalau belum ada).

Aman dijalankan BERULANG: kalau penanda sudah ada, tidak ditambah lagi.
"""
import re
import sys
from pathlib import Path

TPL = Path('/opt/data/services/eduai-publishing/app/templates')
LINK = '<link rel="stylesheet" href="/static/ikon.css">'
SPRITE = '{{ ikon_sprite() }}'
PENANDA = '<!-- IKON: sprite Lucide (ACC Bos 15Sep26) -->'

# _topup_popup.html adalah POTONGAN (bukan halaman penuh) — hanya dapat link CSS
POTONGAN = {'_topup_popup.html'}


def main() -> int:
    berubah, dilewat = [], []
    for f in sorted(TPL.glob('*.html')):
        t = f.read_text(encoding='utf-8')
        asli = t
        penuh = f.name not in POTONGAN

        # 1) CSS ikon — masuk sebelum </head> kalau ada, kalau tidak di paling atas
        if '/static/ikon.css' not in t:
            if '</head>' in t:
                t = t.replace('</head>', LINK + '\n</head>', 1)
            else:
                t = LINK + '\n' + t

        # 2) sprite — tepat setelah <body> (hanya untuk halaman penuh)
        if penuh and 'ikon_sprite()' not in t:
            m = re.search(r'<body[^>]*>', t)
            if m:
                t = (t[:m.end()] + '\n' + PENANDA + '\n' + SPRITE
                     + '\n' + t[m.end():])

        if t != asli:
            f.write_text(t, encoding='utf-8')
            berubah.append(f.name)
        else:
            dilewat.append(f.name)

    print('  ✓ disisipi :', ', '.join(berubah) if berubah else '(tidak ada)')
    print('  · dilewat  :', ', '.join(dilewat) if dilewat else '(tidak ada)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
