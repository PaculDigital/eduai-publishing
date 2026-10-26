#!/usr/bin/env python3
"""GERBANG JENIS BUKU v1 — dipasang atas Gas Boss 26 Okt 2026.

Masalah yang ditutup: mesin selama ini hanya tahu "bikin buku", bukan
"bikin buku APA". Akibatnya (analisa 10 contoh buku, 26 Okt 2026):
buku ajar/monograf berlabel "referensi" lolos, panduan praktis berlabel
"buku ajar" lolos, monograf tanpa penelitian/temuan/simpulan lolos.
Gerbang ini membalik arahnya: JENIS DITENTUKAN DARI ISI, BUKAN DARI LABEL.

Cara kerja:
  1. Spec JSON WAJIB menyatakan "jenis" (kolom baru). Tanpa jenis,
     gerbang GAGAL — mesin tidak boleh menebak jenis dari judul.
  2. Setiap jenis punya unsur WAJIB yang diperiksa dari isi spec
     (judul bab, judul sub-bab, teks, tabel, dan kolom khusus seperti
     indeks). Satu unsur wajib hilang = GAGAL (exit 1).
  3. Kalau jenis yang diklaim gagal TAPI jenis lain lolos penuh,
     gerbang mencetak "Diduga jenis sebenarnya: ..." — supaya label
     bisa diperbaiki, bukan sekadar ditolak.
  4. PERINGATAN tidak menggagalkan. Ia menandai utang yang harus
     ditutup di versi berikutnya (mis. bab Penutup monograf, kunci
     jawaban buku ajar) — sengaja belum fatal di v1 supaya contoh
     yang sudah berjalan tidak patah mendadak oleh satu format.

Sumber aturan (bukan karangan):
  - unsur_wajib profil per jenis di branch agen/wulan/fase1-ssot
    (template-buku-resmi/jenis/*/profil.json): referensi menuntut
    indeks subjek + indeks nama + tabel komparasi + posisi penulis;
    ajar menuntut TIU/TIK + latihan + checklist + rangkuman per bab;
    monograf menuntut pernyataan novelty + keterbatasan.
  - skill buku-referensi: bab tanpa posisi penulis = bab gagal;
    indeks subjek + indeks nama adalah pembeda utama referensi.
  - analisa 10 contoh 26 Okt 2026: tanpa gerbang ini, 0/5 monograf
    lolos uji penutup/metode, 0/10 buku lolos uji indeks referensi,
    dan 1 buku ajar lolos hanya karena perangkatnya dirancang penuh.

Pakai:
    python3 periksa_jenis_buku.py spec.json
    python3 periksa_jenis_buku.py --jenis buku-ajar spec.json
    python3 periksa_jenis_buku.py --dugaan spec.json   # + saran jenis lain

EXIT 0 = LULUS (jenis cocok dengan isi), EXIT 1 = GAGAL.
Stdlib murni; inputnya spec JSON buat_buku.py (bukan .docx), supaya
kesalahan jenis tertangkap SEBELUM buku ditulis, bukan sesudah jadi.
"""

import json
import re
import sys
from pathlib import Path

JENIS_ALIAS = {
    'buku-referensi': 'buku-referensi', 'referensi': 'buku-referensi',
    'buku-ajar': 'buku-ajar', 'buku-ajar-obe': 'buku-ajar',
    'ajar': 'buku-ajar',
    'monograf': 'monograf',
    'buku-umum': 'buku-umum', 'umum': 'buku-umum',
    'buku-anak': 'buku-anak', 'anak': 'buku-anak',
    'panduan-praktis': 'panduan-praktis', 'panduan': 'panduan-praktis',
    'book-chapter': 'book-chapter', 'chapter': 'book-chapter',
}

LULUS = GAGAL = 0
MASALAH = []
PERINGATAN = []


def ok(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  -> {info}' if info else ''))
        MASALAH.append(f'{nama}: {info}')


def ingatkan(nama, syarat, info=''):
    if syarat:
        print(f'  OK     {nama}')
    else:
        print(f'  PERINGATAN  {nama}' + (f'  -> {info}' if info else ''))
        PERINGATAN.append(f'{nama}: {info}')


def kumpulkan_teks(obj, keluar=None):
    """Semua string di dalam spec, dinormalisasi ke huruf kecil."""
    if keluar is None:
        keluar = []
    if isinstance(obj, str):
        keluar.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            kumpulkan_teks(v, keluar)
    elif isinstance(obj, list):
        for v in obj:
            kumpulkan_teks(v, keluar)
    return keluar


def teks_penuh(spec):
    return '\n'.join(kumpulkan_teks(spec)).lower()


def judul_tabel(spec):
    """Judul semua blok tabel di dalam spec."""
    hasil = []
    if isinstance(spec, dict):
        for k, v in spec.items():
            if k == 'tabel' and isinstance(v, dict):
                hasil.append(str(v.get('judul', '')))
            else:
                hasil.extend(judul_tabel(v))
    elif isinstance(spec, list):
        for v in spec:
            hasil.extend(judul_tabel(v))
    return hasil


def bab_dari_spec(spec):
    return spec.get('bab', []) if isinstance(spec, dict) else []


def teks_bab(bab):
    return '\n'.join(kumpulkan_teks(bab)).lower()


def ada_indeks(spec, kunci, label):
    """Indeks lolos bila kolom khusus non-kosong, ATAU ada bab/sub-bab
    berjudul Indeks <label> (untuk spec yang menyisipkan indeks sebagai
    bab). Kolom kosong = gagal: indeks yang dijanjikan tapi kosong
    sama buruknya dengan tidak ada."""
    nilai = spec.get(kunci)
    if isinstance(nilai, list) and len(nilai) > 0:
        return True
    if isinstance(nilai, dict) and len(nilai) > 0:
        return True
    if isinstance(nilai, str) and nilai.strip():
        return True
    for b in bab_dari_spec(spec):
        if label in str(b.get('judul', '')).lower():
            return True
        for s in b.get('sub', []) or []:
            if label in str(s.get('judul', '')).lower():
                return True
    return False


def periksa_struktur_umum(spec, teks):
    print('-- struktur umum (berlaku untuk semua jenis) --')
    ok('U1 judul + penulis terisi',
       bool(str(spec.get('judul', '')).strip())
       and bool(str(spec.get('penulis', '')).strip()),
       'judul/penulis kosong')
    ok('U2 kata pengantar terisi',
       bool(kumpulkan_teks(spec.get('kata_pengantar', ''))),
       'kata_pengantar kosong/tidak ada')
    ok('U3 tentang penulis terisi',
       bool(kumpulkan_teks(spec.get('tentang_penulis', ''))),
       'tentang_penulis kosong/tidak ada')
    ok('U4 daftar pustaka tidak kosong',
       isinstance(spec.get('daftar_pustaka'), list)
       and len(spec.get('daftar_pustaka')) > 0,
       'daftar_pustaka kosong/tidak ada')
    ok('U5 minimal 1 bab',
       len(bab_dari_spec(spec)) >= 1, 'daftar bab kosong')


def periksa_referensi(spec, teks):
    print('-- buku referensi: harus bisa DIRUJUK, bukan dibaca berurutan --')
    ok('R1 indeks subjek ada dan tidak kosong',
       ada_indeks(spec, 'indeks_subjek', 'indeks subjek'),
       'tanpa indeks subjek, pembaca tidak bisa mencari topik — ini bukan buku referensi')
    ok('R2 indeks nama ada dan tidak kosong',
       ada_indeks(spec, 'indeks_nama', 'indeks nama'),
       'tanpa indeks nama, tokoh/penulis tidak bisa dilacak — ini bukan buku referensi')
    tabel = ' '.join(judul_tabel(spec)).lower()
    sub_judul = ' '.join(
        str(s.get('judul', '')) for b in bab_dari_spec(spec)
        for s in b.get('sub', []) or []).lower()
    per_bab = True
    for b in bab_dari_spec(spec):
        tb = ' '.join(judul_tabel(b)).lower()
        sj = ' '.join(str(s.get('judul', ''))
                      for s in b.get('sub', []) or []).lower()
        if 'komparasi' not in tb and 'perbandingan' not in tb \
                and 'komparasi' not in sj and 'perbandingan' not in sj:
            per_bab = False
    ok('R3 tabel komparasi / perbandingan di tiap bab',
       per_bab and len(bab_dari_spec(spec)) > 0,
       'bab tanpa perbandingan kritis antar teori = kumpulan teori, bukan referensi')
    ok('R4 posisi penulis eksplisit',
       any(f in teks for f in ('posisi penulis', 'pandangan penulis',
                               'sintesis penulis', 'penulis berpendapat',
                               'penulis berpendirian')),
       'tanpa posisi penulis yang dinyatakan, bab hanya merangkum teori orang lain')
    ingatkan('Rw glosarium ada',
             'glosarium' in teks or bool(spec.get('glosarium')),
             'glosarium sangat dianjurkan untuk referensi (wajib bila >20 istilah teknis)')
    ingatkan('Rw daftar singkatan ada',
             'daftar singkatan' in teks,
             'daftar singkatan wajib untuk buku referensi menurut skill')


def periksa_ajar(spec, teks):
    print('-- buku ajar: tiap bab harus bisa MENGAJAR, bukan sekadar dibaca --')
    for i, b in enumerate(bab_dari_spec(spec), 1):
        tb = teks_bab(b)
        judul = b.get('judul', f'bab {i}')
        punya_tujuan = (
            ('tujuan instruksional umum' in tb
             and 'tujuan instruksional khusus' in tb)
            or 'capaian pembelajaran' in tb)
        ok(f'A1 bab {i} ({judul}): tujuan pembelajaran',
           punya_tujuan,
           'bab tidak dibuka dengan TIU/TIK atau Capaian Pembelajaran')
        ok(f'A2 bab {i} ({judul}): latihan',
           'latihan' in tb, 'bab tanpa latihan = murid tidak pernah diuji')
        ok(f'A3 bab {i} ({judul}): rangkuman',
           'rangkuman' in tb, 'bab tanpa rangkuman')
        ok(f'A4 bab {i} ({judul}): checklist pemahaman',
           'checklist' in tb, 'bab tanpa checklist pemahaman')
    ingatkan('Aw kunci jawaban / pembahasan latihan ada',
             'kunci jawaban' in teks or 'pembahasan latihan' in teks,
             'tanpa kunci jawaban, murid tidak mendapat umpan balik')
    ingatkan('Aw bab penutup / sintesis ada',
             any('penutup' in str(b.get('judul', '')).lower()
                 or 'simpulan' in str(b.get('judul', '')).lower()
                 or 'kesimpulan' in str(b.get('judul', '')).lower()
                 for b in bab_dari_spec(spec)),
             'bab terakhir sebaiknya sintesis, bukan sekadar topik terakhir')
    ingatkan('Aw CPL/CPMK dinyatakan',
             'cpl' in teks or 'cpmk' in teks,
             'profil ajar-OBE menuntut halaman CPL/CPMK di buku final')


def periksa_monograf(spec, teks):
    print('-- monograf: harus ada PENELITIAN penulis sendiri --')
    ok('M1 pernyataan kebaruan / novelty',
       'kebaruan' in teks or 'novelty' in teks,
       'tanpa kebaruan yang dinyatakan, buku ini hanya rangkuman literatur')
    ok('M2 keterbatasan penelitian dinyatakan',
       'keterbatasan' in teks,
       'penelitian yang tidak menyebut keterbatasannya tidak bisa dipercaya')
    ok('M3 metode penelitian penulis sendiri',
       any(f in teks for f in ('metode penelitian', 'metodologi penelitian',
                               'desain penelitian', 'pendekatan penelitian')),
       'bab berjudul "metodologi" yang isinya prinsip umum TIDAK cukup — harus ada metode penelitian buku ini')
    ok('M4 bab hasil / pembahasan ada',
       any('hasil' in str(b.get('judul', '')).lower()
           for b in bab_dari_spec(spec)),
       'tanpa bab hasil, tidak ada temuan yang dilaporkan')
    ingatkan('Mw pertanyaan penelitian / rumusan masalah eksplisit',
             any(f in teks for f in ('pertanyaan penelitian',
                                     'rumusan masalah', 'fokus penelitian')),
             'monograf sebaiknya menyatakan pertanyaan yang dijawabnya di Bab 1')
    ingatkan('Mw bab penutup / simpulan ada',
             any('penutup' in str(b.get('judul', '')).lower()
                 or 'simpulan' in str(b.get('judul', '')).lower()
                 or 'kesimpulan' in str(b.get('judul', '')).lower()
                 for b in bab_dari_spec(spec)),
             'tanpa penutup, pembaca tidak tahu apa temuan akhirnya')
    ingatkan('Mw indeks ada (sangat dianjurkan untuk monograf tebal)',
             ada_indeks(spec, 'indeks_subjek', 'indeks')
             or ada_indeks(spec, 'indeks_nama', 'indeks'),
             'monograf tebal tanpa indeks sulit dipakai sebagai rujukan')


def periksa_panduan(spec, teks):
    print('-- panduan praktis: harus bisa DIPRAKTIKKAN, bukan dihafal --')
    ok('P1 contoh / langkah praktis ada',
       'contoh' in teks and any(f in teks for f in ('langkah', 'praktik',
                                                    'cara ')),
       'panduan tanpa contoh dan langkah = uraian teori, bukan panduan')
    ingatkan('Pw lampiran praktis (cheat-sheet / daftar perintah) ada',
             'lampiran' in teks,
             'lampiran praktis sangat membantu panduan, tapi tidak wajib di v1')


def periksa_umum_buku(spec, teks):
    print('-- buku umum / anak: struktur utuh sudah cukup di v1 --')
    ingatkan('Uw ilustrasi / gambar ada (untuk buku anak: wajib di versi final)',
             'gambar' in teks or any(
                 isinstance(v, dict) and 'gambar' in v
                 for b in bab_dari_spec(spec)
                 for s in b.get('sub', []) or []
                 for v in (s.get('paragraf', []) or [])),
             'buku anak tanpa gambar akan ditolak di gerbang visual, bukan di sini')


PERIKSA = {
    'buku-referensi': periksa_referensi,
    'buku-ajar': periksa_ajar,
    'monograf': periksa_monograf,
    'buku-umum': periksa_umum_buku,
    'buku-anak': periksa_umum_buku,
    'panduan-praktis': periksa_panduan,
}


def periksa_chapter(spec, teks):
    print('-- book chapter: format section, bukan bab --')
    sections = spec.get('section', []) if isinstance(spec, dict) else []
    ok('C1 section pertama = Pendahuluan dengan tujuan',
       len(sections) >= 1
       and 'pendahuluan' in str(sections[0].get('judul', '')).lower()
       and bool(sections[0].get('tujuan')),
       'chapter wajib dibuka Pendahuluan + Tujuan Pembelajaran')
    ok('C2 referensi tidak kosong',
       isinstance(spec.get('referensi'), list)
       and len(spec.get('referensi')) > 0,
       'referensi kosong')
    ok('C3 glosarium tidak kosong',
       isinstance(spec.get('glosarium'), list)
       and len(spec.get('glosarium')) > 0,
       'glosarium chapter kosong (format tabel 2 kolom)')
    ok('C4 CV penulis ada',
       bool(spec.get('cv')),
       'CV penulis tidak ada')


def jalankan(spec, jenis, diam=False):
    """Jalankan semua cek untuk satu jenis; kembalikan (lulus, gagal)."""
    global LULUS, GAGAL, MASALAH, PERINGATAN
    LULUS = GAGAL = 0
    MASALAH, PERINGATAN = [], []
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        teks = teks_penuh(spec)
        if jenis == 'book-chapter':
            periksa_chapter(spec, teks)
        else:
            periksa_struktur_umum(spec, teks)
            PERIKSA[jenis](spec, teks)
    if not diam:
        print(buf.getvalue(), end='')
    return LULUS, GAGAL


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    paksa_jenis = None
    tampilkan_dugaan = False
    for a in sys.argv[1:]:
        if a.startswith('--jenis='):
            paksa_jenis = a.split('=', 1)[1]
        elif a == '--dugaan':
            tampilkan_dugaan = True
    if len(argv) != 1:
        sys.exit(__doc__)
    try:
        spec = json.loads(Path(argv[0]).read_text(encoding='utf-8'))
    except Exception as e:
        print(f'GAGAL membaca spec: {e}')
        return 1
    mentah = paksa_jenis or spec.get('jenis', '')
    jenis = JENIS_ALIAS.get(str(mentah).strip().lower())
    print(f'Jenis yang diklaim: {mentah!r} -> {jenis}')
    if not jenis:
        print('GAGAL  jenis belum dinyatakan atau tidak dikenal.')
        print('  -> spec WAJIB berisi kolom "jenis", salah satu dari: '
              + ', '.join(sorted(set(JENIS_ALIAS.values()))))
        print('  -> mesin tidak boleh menebak jenis dari judul.')
        return 1
    lulus, gagal = jalankan(spec, jenis)
    print(f'\nHasil gerbang jenis ({jenis}): {lulus} LULUS, {gagal} GAGAL'
          + (f', {len(PERINGATAN)} peringatan' if PERINGATAN else ''))
    if gagal == 0:
        print('LULUS — jenis cocok dengan isi.')
        return 0
    print('GAGAL — jenis yang diklaim TIDAK cocok dengan isi. '
          'Buku ini tidak boleh diserahkan dengan label ini.')
    if tampilkan_dugaan:
        print('\n-- dugaan jenis lain (dihitung dari isi, bukan label) --')
        for lain in sorted(set(JENIS_ALIAS.values())):
            if lain == jenis:
                continue
            l2, g2 = jalankan(spec, lain, diam=True)
            if g2 == 0:
                print(f'  Diduga jenis sebenarnya: {lain} '
                      f'(lolos penuh: {l2} cek)')
    return 1


if __name__ == '__main__':
    sys.exit(main())
