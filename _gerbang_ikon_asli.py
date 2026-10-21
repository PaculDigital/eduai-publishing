"""GERBANG KEASLIAN IKON (06Okt26) — OBRAL lawan halusinasi nama ikon.

KENAPA ADA (akar, bukan tambalan):

  Bos marah (06Okt26, verbatim): "kadang kamu masih pakai icon standar,
  contoh dulu pernah saya suruh ganti spark, eh yang kamu pasang spark icon
  standar setelah saya kasih link lucide iconnya baru kamu ganti, itu kan
  halusinasi kamu, terlalu menggampangkan perintah".

  AKAR: Wulan menulis nama ikon DARI INGATAN. Dulu `ikon('spark')` —
  nama itu TIDAK ADA di Lucide (yang benar `sparkles`), tapi template tetap
  jalan (makro mengembalikan kosong / bentuk lain) ⇒ tampak "sudah
  dikerjakan" padahal SALAH. Bos baru sadar setelah lihat sendiri.

  Tambalan = memeriksa satu-satu saat diminta. AKAR = periksa bentuk asli
  lawan Lucide RESMI, otomatis, tiap kali gerbang jalan.

CARA KERJA:
  1. Ambil seluruh nama ikon dari sprite.
  2. Ambil wujud RESMI tiap ikon dari unpkg/jsdelivr (Lucide asli).
  3. Bandingkan ANGKA path — kalau beda ⇒ sprite memuat ikon PALSU/karangan.
  4. Periksa juga: ada nama yang DIPAKAI template tapi TIDAK ADA di sprite.
  5. Periksa nama ikon yang TIDAK ADA di Lucide sama sekali.

MODE:
  python3 _gerbang_ikon_asli.py            → pakai simpanan (offline, cepat)
  python3 _gerbang_ikon_asli.py --online   → unduh ulang dari Lucide resmi

Simpanan: `_ikon-asli/<nama>.txt` (isi path resmi, ikut repo) supaya gerbang
tetap bisa jalan walau internet mati.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path('/app') if Path('/app/app').exists() else Path(__file__).resolve().parent
SPRITE = AKAR / 'app/static/ikon/lucide.svg'
SIMPANAN = AKAR / '_ikon-asli'
TPL = AKAR / 'app/templates'

SUMBER = ('https://unpkg.com/lucide-static@latest/icons/{n}.svg',
          'https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{n}.svg')

lulus = 0
gagal = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  LULUS  {nama}')
    else:
        gagal += 1
        print(f'  GAGAL  {nama}  {bukti}')


def angka(s: str) -> list[str]:
    """Ambil perintah path + angka — pembanding bentuk.

    ⚠️ JANGAN buang spasi antar-angka: "M20 6 9 17" → kalau spasi dibuang
    jadi "M206917" (angka 206917 palsu) → pembanding kacau & salah lapor.
    """
    return re.findall(r'[A-Za-z]|-?\d+\.?\d*', s or '')


def rapi(isi: str) -> str:
    """Rapikan isi symbol: buang atribut, sisakan perintah & angka BERSPASI."""
    #  buang komentar XML
    isi = re.sub(r'<!--.*?-->', '', isi, flags=re.S)
    #  ambil isi tiap elemen: path d="..." / circle cx=.. cy=.. r=.. / dll
    bagian = []
    for m in re.finditer(r'<(path|circle|rect|line|polyline|polygon|ellipse)\b([^>]*)>',
                         isi):
        tag, attrs = m.group(1), m.group(2)
        if tag == 'path':
            d = re.search(r'\bd="([^"]*)"', attrs)
            bagian.append('path:' + re.sub(r'\s+', ' ', d.group(1)).strip() if d else '')
        else:
            pas = re.findall(r'\b([a-z]+)="([^"]*)"', attrs)
            pas.sort()
            bagian.append(tag + ':' + ' '.join(f'{k}={v}' for k, v in pas))
    return '|'.join(bagian)


def isi_sprite() -> dict[str, str]:
    t = SPRITE.read_text(encoding='utf-8')
    hasil = {}
    for m in re.finditer(r'<symbol[^>]*id="ik-([^"]+)"[^>]*>(.*?)</symbol>',
                         t, flags=re.S):
        hasil[m.group(1)] = rapi(m.group(2))
    return hasil


def ambil_resmi(nama: str, online: bool) -> str | None:
    """Wujud resmi ikon — dari simpanan dulu, unduh kalau perlu."""
    f = SIMPANAN / f'{nama}.txt'
    if f.exists() and not online:
        return f.read_text(encoding='utf-8')
    for pola in SUMBER:
        try:
            s = urllib.request.urlopen(pola.format(n=nama), timeout=20).read().decode()
            s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
            dalam = re.search(r'<svg[^>]*>(.*?)</svg>', s, flags=re.S)
            if dalam:
                isi = rapi(dalam.group(1))
                SIMPANAN.mkdir(parents=True, exist_ok=True)
                f.write_text(isi, encoding='utf-8')
                return isi
        except urllib.error.HTTPError as e:                   # 404 = nama karangan
            if e.code == 404 and not online:
                continue          #  coba sumber kedua
            if e.code == 404:
                #  DITEGASKAN: nama ini TIDAK ADA di Lucide = KARANGAN
                SIMPANAN.mkdir(parents=True, exist_ok=True)
                f.write_text('__TIDAK_ADA_DI_LUCIDE__', encoding='utf-8')
                return '__TIDAK_ADA_DI_LUCIDE__'
        except Exception:                                     # noqa: BLE001
            continue
    return None


def nama_dipakai() -> set[str]:
    kumpul: set[str] = set()
    for f in TPL.glob('*.html'):
        t = f.read_text(encoding='utf-8')
        kumpul |= set(re.findall(r"ikon\(\s*'([a-z0-9-]+)'", t))
        kumpul |= set(re.findall(r"IKON\(\s*'([a-z0-9-]+)'", t))
        kumpul |= set(re.findall(r'href="#ik-([a-z0-9-]+)', t))
        for baris in t.splitlines():
            m = re.search(r"'#ik-' \+ ([A-Za-z_][A-Za-z0-9_]*)", baris)
            if m:
                for mm in re.finditer(r'var\s+' + re.escape(m.group(1)) + r'\s*=\s*([^;]+);', t):
                    kumpul |= set(re.findall(r"'([a-z0-9-]+)'", mm.group(1)))
    return kumpul


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--online', action='store_true',
                    help='unduh ulang wujud resmi dari Lucide (butuh internet)')
    arg = ap.parse_args()

    print('=== GERBANG KEASLIAN IKON (lawan halusinasi nama ikon) ===')
    if not SPRITE.exists():
        cek('sprite ada', False, f'({SPRITE})')
        print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
        return 1

    sprite = isi_sprite()
    cek('A1 sprite memuat ikon (>=20)', len(sprite) >= 20, f'({len(sprite)})')

    #  A2. setiap ikon dipakai template ADA di sprite (tangkap nama karangan)
    dipakai = nama_dipakai()
    hilang = sorted(dipakai - set(sprite) - {''})
    cek('A2 semua ikon yang dipakai template ADA di sprite',
        not hilang, f'(hilang: {hilang})')

    #  A3/A4. bandingkan wujud lawan Lucide resmi
    print(f'  ... memeriksa wujud {len(sprite)} ikon lawan Lucide resmi')
    hasil: list[tuple[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        fut = {ex.submit(ambil_resmi, nm, arg.online): nm for nm in sprite}
        for f in concurrent.futures.as_completed(fut):
            nm = fut[f]
            try:
                #  ⚠️ JANGAN `f.result() or ''` — itu mengubah None (nama
                #     KARANGAN) jadi '' (tak diperiksa) → uji buta.
                #     ambil_resmi balas None HANYA untuk nama tak ada di Lucide.
                hasil.append((nm, f.result()))
            except Exception:                                 # noqa: BLE001
                hasil.append((nm, None))

    beda, karangan, tanpa_sumber = [], [], []
    for nm, resmi in sorted(hasil):
        if resmi == '__TIDAK_ADA_DI_LUCIDE__':
            karangan.append(nm); continue
        if not resmi:
            tanpa_sumber.append(nm); continue
        if re.sub(r'\s+', ' ', sprite[nm]).strip() == re.sub(r'\s+', ' ', resmi).strip():
            continue
        beda.append(nm)

    cek('A3 setiap ikon COCOK bentuknya dgn Lucide resmi',
        not beda, f'(beda: {beda})')
    cek('A4 TIDAK ada ikon KARANGAN (nama tidak ada di Lucide)',
        not karangan, f'(karangan: {karangan})')
    cek('A5 semua ikon berhasil diperiksa (sumber tersedia)',
        not tanpa_sumber, f'(tak diperiksa: {tanpa_sumber} — jalankan --online)')
    print(f'         (cocok {len(hasil) - len(beda) - len(karangan) - len(tanpa_sumber)}'
          f' · beda {len(beda)} · karangan {len(karangan)}'
          f' · tanpa sumber {len(tanpa_sumber)})')

    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
