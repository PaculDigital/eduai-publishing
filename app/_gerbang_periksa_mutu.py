"""GERBANG PERIKSA MUTU NASKAH — kode saja, TANPA Jev, GRATIS.

Putusan Bos 10 Okt 2026 (pilihan "A"):
  · mutu naskah diperiksa KODE (fakta angka), Jev TIDAK dilibatkan;
  · biaya Rp 0 (tidak ada panggilan Jev);
  · sifat TAHU + TAWAR, bukan blokir.

Angka acuan (TERUKUR 10 Okt 2026):
  Asih (sehat)        : huruf_tunggal 1      · ≤2 kar 0%  · median 37
  Wulandari-PDF(rusak): huruf_tunggal 4.989  · ≤2 kar 64% · median 1
  Disertasi(pendek)   : huruf_tunggal 1      · ≤2 kar 3%  · median 15

Jalankan DI DALAM container eduai-app.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

LULUS = 0
GAGAL = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {bukti}')


def naskah_sehat() -> str:
    """Baris ~65 kar, tanpa huruf tunggal."""
    return '\n'.join(
        'Pendidikan merupakan salah satu faktor penting dalam pembangunan '
        'sumber daya manusia yang berkualitas dan berdaya saing tinggi'
        for _ in range(30))


def naskah_rusak() -> str:
    """Naskah pecah per-HURUF (gejala konversi PDF)."""
    tulisan = ('Dina Alna Helmania Putri melakukan penelitian tentang '
               'stunting pada balita di wilayah kerja puskesmas')
    b = [c for kata in tulisan.split() for c in kata]      # pecah per huruf
    return '\n'.join(b * 3)


def naskah_baris_pendek() -> str:
    return '\n'.join('hasil uji menunjukkan angka yang cukup berbeda tiap '
                     'kelompok responden di desa itu sekarang juga'[:15]
                     for _ in range(40))


def main():
    from app.periksa_mutu import periksa

    print('── UJI 1: PUTUSAN TINGKAT (memisahkan 3 jenis naskah) ──')
    h = periksa(naskah_sehat())
    cek('naskah SEHAT ⇒ tingkat "sehat"', h['tingkat'] == 'sehat',
        f'(dapat {h["tingkat"]} · huruf_tunggal {h["huruf_tunggal"]})')

    r = periksa(naskah_rusak())
    cek('naskah RUSAK (per-huruf) ⇒ tingkat "rusak_konversi"',
        r['tingkat'] == 'rusak_konversi',
        f'(dapat {r["tingkat"]} · huruf_tunggal {r["huruf_tunggal"]})')
    cek('  saran = ganti_ke_docx (arahkan, bukan blokir)',
        r['saran'] == 'ganti_ke_docx', f'(dapat {r["saran"]})')

    p = periksa(naskah_baris_pendek())
    cek('naskah BARIS PENDEK ⇒ tingkat "baris_pendek"',
        p['tingkat'] == 'baris_pendek',
        f'(dapat {p["tingkat"]} · median {p["median"]})')

    print()
    print('── UJI 2: TIDAK MEMBLOKIR (sifat "tahu + tawar") ──')
    cek('naskah rusak TETAP punya pesan (user diberi tahu)',
        bool(r.get('pesan')))
    cek('tidak ada kunci "blokir"/"tolak" di hasil',
        'blokir' not in r and 'tolak' not in r)

    print()
    print('── UJI 3: TIDAK MEMANGGIL Jev (GRATIS) ──')
    import inspect
    import re as _re
    import app.periksa_mutu as pm
    src = inspect.getsource(pm)
    #  ⚠️ Periksa KODE, bukan KOMENTAR (pelajaran EduAi: gerbang pernah GAGAL
    #  PALSU karena teks bug lama masih ada di komentar). Modul ini MEMANG
    #  menyebut "Jev" di penjelasan — itu sah, yang dilarang = MEMANGGILNYA.
    kode = _re.sub(r'""".*?"""', '', src, flags=_re.S)
    kode = _re.sub(r'(?m)^\s*#.*$', '', kode)
    cek('KODE periksa_mutu tidak mengimpor/memanggil jev·satpam·http',
        not _re.search(r'\b(import\s+\w*jev|from\s+\S*jev|satpam|httpx|requests)\b',
                       kode))
    cek('modul TIDAK mengimpor httpx (tidak ada panggilan jaringan)',
        'httpx' not in kode)

    print()
    print('── UJI 4: TITIP DI PINTU YANG SUDAH ADA (bukan rute baru) ──')
    import pathlib
    ra = pathlib.Path('/app/app/rute_alur.py').read_text(encoding='utf-8')
    cek('alur_petakan memanggil periksa_mutu',
        'periksa_mutu' in ra)
    cek('hasil periksa ditempel ke kunci "mutu"',
        "hasil['mutu']" in ra)
    tl = pathlib.Path('/app/app/templates/mulai.html').read_text(encoding='utf-8')
    cek('layar deteksi punya kotak mutu (det-mutu)', 'det-mutu' in tl)
    cek('tombol arahkan .docx ada (det-mutu-docx)', 'det-mutu-docx' in tl)

    #  ⚠️ BERGIGI (temuan 10 Okt): gerbang versi-awal cuma memeriksa 3 warna
    #  (`--merah-muda` dll) — LOLOS, padahal kotak mutu memakai `var(--bg)`
    #  yang TIDAK ADA di :root ⇒ latar kotak kosong. Pelajarannya: periksa
    #  SEMUA variabel CSS yang BENAR-BENAR dipakai blok mutu, bukan daftar
    #  warna yang kita ingat. Ambil otomatis dari blok #det-mutu.
    import re as _re2
    blok_mutu = _re2.search(r'id="det-mutu".*?</div>', tl, _re2.S)
    dipakai = set(_re2.findall(r'var\(\s*(--[a-z0-9-]+)\s*\)', blok_mutu.group(0) if blok_mutu else ''))
    dipakai |= set(_re2.findall(r'var\(\s*(--[a-z0-9-]+)\s*\)',
                                tl[tl.find('function tampilMutu'):][:1400]))
    didefinisi = set(_re2.findall(r'(--[a-z0-9-]+)\s*:', tl))
    hilang = sorted(dipakai - didefinisi)
    cek('SEMUA var CSS yang dipakai kotak mutu ADA di :root',
        not hilang, f'(HILANG: {hilang})')
    cek('kotak mutu memakai var CSS bernama (bukan karangan)',
        'det-mutu' in tl and bool(dipakai), f'(dipakai: {sorted(dipakai)})')

    #  JS: `el()` dipakai `tampilMutu` ⇒ WAJIB ada (bisa `const el =` bentuk
    #  panah, bukan cuma `function el`) — gerbang tak boleh buta bentuk.
    cek('fungsi/konstanta el() ADA (dipakai tampilMutu)',
        bool(_re2.search(r'(function|const|let)\s+el\s*[=(]', tl)))
    cek('kelas .sembunyi ADA (dipakai menyembunyikan kotak)',
        '.sembunyi' in tl)

    print()
    print('── UJI 5: TAHAN NASKAH KOSONG (jangan crash) ──')
    k = periksa('')
    cek('teks kosong ⇒ tingkat "kosong" (tidak melempar galat)',
        k['tingkat'] == 'kosong')
    k2 = periksa('\n\n\n   \n')
    cek('teks hanya baris kosong ⇒ "kosong"', k2['tingkat'] == 'kosong')

    print()
    print('── UJI 6: PESAN TIDAK MENGULANG JUDUL (bug nyata 11Okt26) ──')
    # Judul dipasang LAYAR dari `tingkat`; kalau `pesan` juga memuat judul,
    # teks terbaca DUA KALI di kotak (terbukti lewat potret + MATA 11Okt26).
    judul = {
        'sehat': 'Naskah terbaca baik',
        'rusak_konversi': 'Naskah ini rusak akibat konversi',
        'baris_pendek': 'Naskah terbaca, tapi barisnya pendek-pendek',
        'kosong': 'Tidak ada teks yang terbaca',
    }
    contoh = {
        'kosong': '',
        'rusak_konversi': '\n'.join(['a'] * 300 + ['kata normal satu dua tiga'] * 5),
        'baris_pendek': '\n'.join(['ok'] * 60),
        'sehat': '\n'.join([
            'Pendidikan memiliki peran yang sangat penting dalam membentuk karakter.',
        ] * 40),
    }
    for tingkat, jd in judul.items():
        h = periksa(contoh[tingkat])
        p = (h.get('pesan') or '').strip()
        cek(f'[{tingkat}] pesan TIDAK diawali judul (tidak terulang)',
            not p.lower().startswith(jd.lower()[:25]),
            repr(p[:45]))
        cek(f'[{tingkat}] pesan tidak kosong', bool(p))
    # gerbang LAYAR: judul memang datang dari JS, bukan dari mesin
    cek('LAYAR memasang judul dari `tingkat` (tanda + judul[...])',
        'judul[m.tingkat]' in tl and 'tanda[m.tingkat]' in tl)

    print()
    print('── UJI 7: TIDAK ADA KATA RAGU DI TAMPILAN (permintaan Bos 11Okt26) ──')
    # Kata ragu membuat mesin terdengar menebak, padahal ia MEMBACA naskah.
    # Terlarang di SELURUH berkas mesin + tampilan (bukan cuma 1 kalimat).
    import pathlib
    _DIR = pathlib.Path(__file__).resolve().parent
    _BERKAS = [
        _DIR / 'periksa_mutu.py',
        _DIR / 'alur_awal.py',
        _DIR / 'rute_pembimbing.py',
        _DIR / 'templates' / 'mulai.html',
        _DIR / 'templates' / 'naskah.html',
    ]
    _RAGU = ['sepertinya', 'tampaknya', 'nampaknya']
    _pelanggar = []
    for b in _BERKAS:
        if not b.is_file():
            continue
        isi_berkas = b.read_text(encoding='utf-8', errors='replace')
        for i, baris in enumerate(isi_berkas.split('\n'), 1):
            s = baris.strip()
            # lewati KOMENTAR kode — tidak pernah dibaca user
            if s.startswith('#') or s.startswith('//'):
                continue
            # lewati baris yg memuat teks asli user/temuan (bukan kalimat mesin)
            for kata in _RAGU:
                if kata in baris.lower():
                    _pelanggar.append('%s:%d %s' % (b.name, i, s[:60]))
    cek('TIDAK ada kata ragu (sepertinya/tampaknya/nampaknya) di teks yang dibaca user',
        not _pelanggar, ' | '.join(_pelanggar[:3]))
    cek('kalimat pengganti "Terdeteksi" ADA di alur_awal',
        'Terdeteksi' in (_DIR / 'alur_awal.py').read_text(encoding='utf-8'))

    print()
    print(f'HASIL GERBANG PERIKSA MUTU: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
