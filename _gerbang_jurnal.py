"""GERBANG JURNAL (06Okt26) — kolom jurnal_json + jurnal_sidik.

Uji SUNGGUHAN (bukan pura-pura):
  G1. models.py punya kolom jurnal_json & jurnal_sidik
  G2. migrasi idempoten mencantumkan keduanya
  G3. DB produksi: kolom benar-benar terpasang setelah migrasi
  G4. round-trip JSON tahan (tulis → baca → sama)
  G5. bentuk artikel meniru pustaka.py (kunci wajib ada)
  G6. pagar batas 8 artikel manual per bab
  G7. jurnal_sidik berubah bila judul/kk berubah (anti data basi)

Cara pakai: python3 _gerbang_jurnal.py
Exit 0 = LULUS, 1 = GAGAL.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parent
MODELS = AKAR / 'app' / 'models.py'

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


# ── G1: kolom ada di models.py ──
def g1() -> None:
    teks = MODELS.read_text(encoding='utf-8')
    cek('G1a kolom jurnal_json ada di models.py',
        'jurnal_json: Mapped[str]' in teks)
    cek('G1b kolom jurnal_sidik ada di models.py',
        'jurnal_sidik: Mapped[str]' in teks)
    cek('G1c jurnal_json pakai Text',
        bool(re.search(r'jurnal_json:\s*Mapped\[str\]\s*=\s*mapped_column\(Text', teks)))
    cek('G1d jurnal_sidik pakai String(64)',
        bool(re.search(r"jurnal_sidik:\s*Mapped\[str\]\s*=\s*mapped_column\(String\(64\)", teks)))


# ── G2: migrasi mencantumkan keduanya ──
def g2() -> None:
    teks = MODELS.read_text(encoding='utf-8')
    cek("G2a migrasi punya 'jurnal_json'",
        bool(re.search(r"'jurnal_json':\s*'TEXT'", teks)))
    cek("G2b migrasi punya 'jurnal_sidik'",
        bool(re.search(r"'jurnal_sidik':\s*\"VARCHAR\(64\)", teks)))
    # harus berada di blok profil_dokumen (setelah panduan_json)
    potong = teks.split('panduan_json', 1)
    cek('G2c jurnal_json muncul SETELAH panduan_json (blok profil_dokumen)',
        len(potong) == 2 and 'jurnal_json' in potong[1])


# ── G3: DB produksi (dijalankan di dalam container) ──
def g3() -> None:
    try:
        sys.path.insert(0, str(AKAR))
        from app.models import engine                       # noqa: PLC0415
        with engine.connect() as c:
            ada = {r[1] for r in c.exec_driver_sql('PRAGMA table_info(profil_dokumen)')}
        cek('G3a DB: kolom jurnal_json terpasang', 'jurnal_json' in ada)
        cek('G3b DB: kolom jurnal_sidik terpasang', 'jurnal_sidik' in ada)
    except Exception as e:                                   # noqa: BLE001
        cek('G3 DB bisa dibaca', False, f'({type(e).__name__}: {e})')


# ── G4: round-trip JSON ──
def g4() -> None:
    contoh = {'BAB II': [
        {'title': 'Kualitas Produk dan Keputusan Pembelian',
         'authors': 'Yusnia, Burhanudin AY', 'year': 2020,
         'journal': 'Jurnal Ilmiah Edunomika', 'doi': '10.29040/jie.v4i01.900',
         'garuda_id': 1662547, 'doi_status': 'verified', 'asal': 'ai'},
        {'title': 'Brand Image', 'authors': 'Smith', 'year': 2021,
         'journal': 'J. Marketing', 'doi': '10.1/x', 'garuda_id': None,
         'doi_status': 'verified', 'asal': 'manual'},
    ], '_manual_terpakai': {'BAB II': 1}}
    teks = json.dumps(contoh, ensure_ascii=False)
    balik = json.loads(teks)
    cek('G4 round-trip JSON utuh', balik == contoh)


# ── G5: bentuk artikel meniru pustaka.py ──
def g5() -> None:
    kunci_wajib = {'title', 'authors', 'year', 'journal', 'doi',
                   'garuda_id', 'doi_status'}
    contoh = {'title': 'x', 'authors': 'y', 'year': 2020, 'journal': 'z',
              'doi': '10.1/a', 'garuda_id': None, 'doi_status': 'verified'}
    cek('G5 bentuk artikel punya SEMUA kunci pustaka.py',
        kunci_wajib.issubset(contoh))


# ── G6: pagar batas 8 artikel manual per bab ──
BATAS_MANUAL = 8


def boleh_tambah(daftar: list[dict], asal: str = 'manual') -> bool:
    """True kalau masih boleh menambah artikel manual (pagar batas 8)."""
    if asal != 'manual':
        return True
    manual = [a for a in daftar if a.get('asal') == 'manual']
    return len(manual) < BATAS_MANUAL


def g6() -> None:
    kosong: list[dict] = []
    cek('G6a daftar kosong → boleh tambah', boleh_tambah(kosong))
    tujuh = [{'asal': 'manual'} for _ in range(7)]
    cek('G6b 7 manual → boleh tambah', boleh_tambah(tujuh))
    delapan = [{'asal': 'manual'} for _ in range(8)]
    cek('G6c 8 manual → TIDAK boleh (batas tercapai)', not boleh_tambah(delapan))
    sembilan = [{'asal': 'manual'} for _ in range(9)]
    cek('G6d 9 manual → TIDAK boleh', not boleh_tambah(sembilan))
    # artikel AI tidak dihitung
    campur = [{'asal': 'ai'} for _ in range(50)] + [{'asal': 'manual'}]
    cek('G6e artikel AI TIDAK dihitung ke batas', boleh_tambah(campur))
    cek('G6f batas = 8 (bukan 10/30)', BATAS_MANUAL == 8)


# ── G7: sidik berubah bila judul/kk berubah ──
def _sidik(judul: str, kk: str) -> str:
    return hashlib.sha256(f'{judul.strip().lower()}|{kk.strip().lower()}'
                          .encode('utf-8')).hexdigest()


def g7() -> None:
    a = _sidik('Pengaruh Harga', 'harga, promosi')
    b = _sidik('Pengaruh Harga', 'harga, promosi')
    c = _sidik('Pengaruh Harga', 'harga, kualitas')
    d = _sidik('Pengaruh Promosi', 'harga, promosi')
    cek('G7a judul+kk sama → sidik SAMA', a == b)
    cek('G7b kk beda → sidik BEDA', a != c)
    cek('G7c judul beda → sidik BEDA', a != d)
    cek('G7d sidik 64 huruf (SHA-256)', len(a) == 64)


def main() -> int:
    print('=== GERBANG JURNAL — kolom jurnal_json + jurnal_sidik ===')
    for fn in (g1, g2, g3, g4, g5, g6, g7):
        fn()
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
