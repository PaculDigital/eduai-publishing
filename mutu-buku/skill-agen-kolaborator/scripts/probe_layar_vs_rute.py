#!/usr/bin/env python3
"""PROBE: layar (template HTML) vs rute (router) — dua arah selisih.

Menangkap kelas bug yang TIDAK BISA ditangkap uji Python:
  A. Layar memanggil endpoint yang TIDAK terdaftar  -> tombol 404
  B. Rute terdaftar tapi TIDAK pernah dipanggil layar -> fitur tak tampil

Terukur 21 Okt 2026 (EduAi Fase 3 BAB IV):
  layar panggil /api/bab4/kunci      -> rute sebenarnya /kunci-hasil   (404)
  layar panggil /api/bab4/olah       -> rute sebenarnya /olah-data     (404)
  layar panggil /api/bab4/pra        -> rute sebenarnya /pra-survei    (404)
  rute GET /hasil + GET /profil ada  -> NOL panggilan di layar         (tak tampil)

CARA PAKAI
    cd <repo-salinan>
    python3 probe_layar_vs_rute.py                 # auto-deteksi pasangan
    python3 probe_layar_vs_rute.py --kombinasi bab4
    python3 probe_layar_vs_rute.py --prefix /api/bab4

EXIT 0 = bersih, EXIT 1 = ada temuan.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path('.').resolve()
TPL_DIR = ROOT / 'app' / 'templates'
RUTE_GLOB = 'app/*_rute.py'


def rute_terdaftar(kombinasi: str | None, prefix: str | None) -> dict[str, list[str]]:
    """Kumpulkan endpoint dari setiap berkas rute.

    Mengembalikan {nama_kombinasi: [endpoint, ...]} dengan endpoint berawalan
    `/<prefix>` penuh, mis. '/api/bab4/hasil'.
    """
    hasil: dict[str, list[str]] = {}
    for berkas in ROOT.glob(RUTE_GLOB):
        isi = berkas.read_text(encoding='utf-8', errors='ignore')
        nama = berkas.stem.replace('_rute', '')
        if kombinasi and nama != kombinasi:
            continue
        # Prefix router: APIRouter(prefix="/api/bab4")  ATAU  include_router(..., prefix=...)
        m = re.search(r'APIRouter\([^)]*prefix\s*=\s*[\'"]([^\'"]+)', isi)
        pfx = m.group(1) if m else ''
        if prefix:
            pfx = prefix
        eps: list[str] = []
        for _metode, jalur in re.findall(r"@router\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)", isi):
            gabung = (pfx.rstrip('/') + '/' + jalur.lstrip('/')).replace('//', '/')
            eps.append(gabung)
        if eps:
            hasil[nama] = sorted(set(eps))
    return hasil


def dipanggil_layar(kombinasi: str, eps: list[str]) -> dict[str, set[str]]:
    """Cari setiap endpoint di seluruh template. Cocokkan pada batas kata."""
    semua_tpl = list(TPL_DIR.rglob('*.html')) if TPL_DIR.exists() else []
    dipakai: dict[str, set[str]] = {}
    teks_tpl: list[tuple[Path, str]] = [(p, p.read_text(encoding='utf-8', errors='ignore'))
                                        for p in semua_tpl]
    for ep in eps:
        # awalan '/api/bab4/olah' JANGAN dianggap cocok dengan '/api/bab4/olah-data'
        pola = re.compile(re.escape(ep) + r'(?![\w-])')
        kena = {str(p.relative_to(ROOT)) for p, isi in teks_tpl if pola.search(isi)}
        dipakai[ep] = kena
    return dipakai


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kombinasi', help='nama modul tanpa _rute (mis. bab4)')
    ap.add_argument('--prefix', help='paksa prefix, mis. /api/bab4')
    ap.add_argument('--abaikan-rute', default='',
                    help='endpoint yang memang tak perlu dipanggil layar, pisahkan koma '
                         '(mis. /api/bab4/ringkasan dipakai JS inline)')
    arg = ap.parse_args()

    abaikan = {x.strip() for x in arg.abaikan_rute.split(',') if x.strip()}
    terdaftar = rute_terdaftar(arg.kombinasi, arg.prefix)
    if not terdaftar:
        print(f'TIDAK ADA berkas rute cocok ({RUTE_GLOB}). Sesuaikan RUTE_GLOB.')
        return 1

    total_mati = 0
    total_liar = 0
    total_yatim = 0

    for kombinasi, eps in terdaftar.items():
        print(f'\n=== {kombinasi} — {len(eps)} rute terdaftar ===')
        dipakai = dipanggil_layar(kombinasi, eps)

        # B. rute ada tapi tak dipanggil layar
        yatim = [ep for ep, kena in dipakai.items() if not kena and ep not in abaikan]
        for ep in eps:
            kena = dipakai.get(ep, set())
            tanda = 'OK  ' if kena else 'YATIM'
            print(f'  {tanda} {ep:44} {"<- " + ", ".join(sorted(kena))[:60] if kena else "(tak dipanggil layar)"}')
        total_yatim += len(yatim)

        # A. endpoint di layar yang tak ada di router
        print(f'  --- endpoint di layar TANPA rute ---')
        tpl_relevan = [p for p in (TPL_DIR.rglob('*.html') if TPL_DIR.exists() else [])
                       if kombinasi in p.name or kombinasi in p.read_text(encoding='utf-8', errors='ignore')[:4000]]
        pola_umum = re.compile(r'[\'"`](/api/[A-Za-z0-9_/-]+)')
        semua_ada = set(eps)
        for tpl in tpl_relevan:
            isi = tpl.read_text(encoding='utf-8', errors='ignore')
            for ep in sorted(set(pola_umum.findall(isi))):
                if not ep.rstrip('/').startswith('/api/'):
                    continue
                # cocokkan longgar: buang query, bandingkan pada rute terdaftar kombinasi ini
                if ep in semua_ada or ep.rstrip('/') in semua_ada:
                    continue
                if not any(ep.startswith(x.rsplit('/', 1)[0]) for x in semua_ada):
                    continue  # beda modul, lewati
                # cari kandidat terdekat (nama terpotong)
                kandidat = [x for x in semua_ada if x.startswith(ep) and x != ep]
                total_mati += 1
                print(f'  MATI {ep:44} <- {tpl.relative_to(ROOT)}')
                if kandidat:
                    print(f'       kemungkinan maksud: {", ".join(kandidat)}')

        if yatim:
            print(f'  >>> {len(yatim)} rute tanpa layar: {", ".join(yatim)}')
        total_liar += 0

    print('\n=========== RINGKAS ===========')
    print(f'  endpoint layar TANPA rute (tombol 404) : {total_mati}')
    print(f'  rute TANPA pemanggil layar (tak tampil): {total_yatim}')
    if total_mati or total_yatim:
        print('\nCATATAN: rute yatim BUKAN selalu bug — endpoint internal/AI boleh ada.')
        print('         Pakai --abaikan-rute untuk daftar putih. Tombol 404 SELALU bug.')
        return 1
    print('  BERSIH')
    return 0


if __name__ == '__main__':
    sys.exit(main())
