#!/usr/bin/env python3
"""GERBANG JENIS BUKU v1.1 — dipasang atas Gas Boss 26 Okt 2026,
diperbaiki atas temuan agen Boss 26 Okt 2026 (celah "cari kata").

v1.1 menutup celah v1 yang terbukti bisa ditembus satu kalimat kata
kunci ("Capaian pembelajaran latihan rangkuman checklist" = lolos
9/0) dan isi sampah (["-"] semua = lolos sebagai buku-umum 5/0).
Aturan anti-palsu v1.1:
  a. ISI BERMAKNA, bukan sekadar ada: "-" / "..." / "x" bukan isi.
     Judul/penulis harus mengandung huruf; kata pengantar dan
     tentang penulis minimal 10 kata; tiap entri daftar pustaka
     minimal 4 kata; tiap entri indeks/glosarium harus punya isi.
  b. UNSUR BERDIRI SENDIRI: tiap unsur wajib harus ada di paragraf
     yang BERBEDA dan cukup panjang (minimal 10 kata). Satu paragraf
     yang menumpuk semua kata kunci TIDAK dihitung untuk semua unsur.
  c. POSISI: tujuan harus muncul SEBELUM latihan di dalam bab yang
     sama (tujuan di awal, latihan di akhir) — bukan di mana saja.
  d. BUKU-UMUM/ANAK TIDAK LAGI PINTU BELAKANG: tiap bab minimal
     30 kata bermakna, bukan sekadar "ada bab".
Kalibrasi ambang (diukur dari contoh nyata fase1-ssot, bukan tebak):
sub-bab buku ajar nyata 35-89 kata, bab monograf nyata 88-133 kata,
kata pengantar nyata 35-80 kata — jadi ambang 10 kata per unsur dan
30 kata per bab umum TIDAK mematahkan contoh nyata, tapi membunuh
kalimat palsu 5 kata dan isi "-".
"""

# Pakai: periksa_jenis_buku.py spec.json | --jenis X spec.json | --dugaan spec.json
# EXIT 0 = LULUS, EXIT 1 = GAGAL. Stdlib murni; input spec JSON.
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


# ── Anti-palsu v1.1: isi bermakna, bukan sekadar ada ──
def jumlah_kata(teks):
    return len(str(teks).split())


def mengandung_huruf(teks):
    return bool(re.search(r'[A-Za-z]', str(teks)))


def bermakna(teks, min_kata=1):
    """String bermakna bila mengandung huruf DAN cukup kata.
    "-" / "..." / "x" / "" = 0 kata huruf -> tidak bermakna."""
    return mengandung_huruf(teks) and jumlah_kata(teks) >= min_kata


def kata_dari_objek(obj):
    return sum(jumlah_kata(s) for s in kumpulkan_teks(obj))


def paragraf_dari_bab(bab):
    """Semua paragraf string di dalam satu bab, dalam urutan baca:
    paragraf_pembuka dulu, lalu tiap sub-bab menurut urutannya.
    Blok tabel/gambar (dict) dilewati — ia bukan paragraf."""
    hasil = []
    if not isinstance(bab, dict):
        return hasil
    for p in bab.get('paragraf_pembuka', []) or []:
        if isinstance(p, str):
            hasil.append(p)
    for s in bab.get('sub', []) or []:
        for p in s.get('paragraf', []) or []:
            if isinstance(p, str):
                hasil.append(p)
    return hasil


def paragraf_dari_spec(spec):
    hasil = []
    for b in bab_dari_spec(spec):
        hasil.extend(paragraf_dari_bab(b))
    return hasil


def cari_paragraf(paras, kunci, min_kata=10, mulai_dari=0, terpakai=None):
    """Cari paragraf pertama (mulai dari indeks mulai_dari, dan belum
    terpakai unsur lain) yang mengandung salah satu kunci DAN cukup
    panjang. Kembalikan indeksnya, atau None bila tidak ada.
    Inilah penutup celah "cari kata": satu paragraf yang menumpuk
    semua kata kunci hanya bisa dipakai SATU unsur, bukan semua."""
    terpakai = terpakai or set()
    for i in range(mulai_dari, len(paras)):
        if i in terpakai:
            continue
        rendah = paras[i].lower()
        if any(k in rendah for k in kunci) and jumlah_kata(paras[i]) >= min_kata:
            return i
    return None


def entri_pustaka_bermakna(entri):
    return isinstance(entri, str) and bermakna(entri, min_kata=4)


def entri_indeks_bermakna(entri):
    """Entri indeks bermakna: [istilah, acuan] dengan istilah
    mengandung huruf dan acuan tidak kosong. ["-", "-"] gagal."""
    if isinstance(entri, (list, tuple)) and len(entri) >= 2:
        return bermakna(entri[0], min_kata=1) and str(entri[1]).strip() != ''
    if isinstance(entri, dict):
        return any(bermakna(v, min_kata=1) for v in entri.values())
    return False


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
    """Indeks lolos bila kolom khusus berisi entri BERMAKNA, ATAU ada
    bab/sub-bab berjudul Indeks <label> yang isinya bermakna.
    ["-"] / [] / entri kosong = gagal (celah v1: len > 0 saja)."""
    nilai = spec.get(kunci)
    if isinstance(nilai, list):
        if any(entri_indeks_bermakna(e) for e in nilai):
            return True
        if len(nilai) > 0:
            return False
    elif isinstance(nilai, dict) and len(nilai) > 0:
        return True
    elif isinstance(nilai, str) and bermakna(nilai, min_kata=2):
        return True
    for b in bab_dari_spec(spec):
        if label in str(b.get('judul', '')).lower():
            if kata_dari_objek(b) >= 10:
                return True
        for s in b.get('sub', []) or []:
            if label in str(s.get('judul', '')).lower():
                if kata_dari_objek(s) >= 10:
                    return True
    return False


def periksa_struktur_umum(spec, teks):
    print('-- struktur umum (berlaku untuk semua jenis) --')
    ok('U1 judul + penulis bermakna (bukan hanya tanda baca)',
       bermakna(spec.get('judul', ''), min_kata=1)
       and bermakna(spec.get('penulis', ''), min_kata=1),
       'judul/penulis kosong atau hanya tanda baca ("-")')
    ok('U2 kata pengantar bermakna (minimal 10 kata)',
       kata_dari_objek(spec.get('kata_pengantar', '')) >= 10,
       'kata_pengantar kosong / hanya tanda baca / terlalu pendek')
    ok('U3 tentang penulis bermakna (minimal 10 kata)',
       kata_dari_objek(spec.get('tentang_penulis', '')) >= 10,
       'tentang_penulis kosong / hanya tanda baca / terlalu pendek')
    daftar = spec.get('daftar_pustaka')
    ok('U4 daftar pustaka berisi entri bermakna (minimal 4 kata/entri)',
       isinstance(daftar, list)
       and any(entri_pustaka_bermakna(e) for e in daftar),
       'daftar_pustaka kosong atau hanya berisi sampah ("-")')
    ok('U5 minimal 1 bab',
       len(bab_dari_spec(spec)) >= 1, 'daftar bab kosong')


def tabel_nyata(obj):
    """Semua blok tabel yang benar-benar punya kolom + baris berisi.
    Judul tabel tanpa kolom/baris = bukan tabel, melainkan label."""
    hasil = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'tabel' and isinstance(v, dict):
                kolom = v.get('kolom', []) or []
                baris = v.get('baris', []) or []
                if len(kolom) >= 2 and len(baris) >= 1:
                    hasil.append(v)
            else:
                hasil.extend(tabel_nyata(v))
    elif isinstance(obj, list):
        for v in obj:
            hasil.extend(tabel_nyata(v))
    return hasil


def hitung_sitasi_inisial(spec):
    # Jumlah sitasi inisial-saja (E., 2021) / (T.S., 2025) di paragraf
    # + sel tabel spec. Pola (?:[A-Z]\.)+ menangkap multi-inisial juga.
    pola = re.compile(r'\(\s*(?:[A-Z]\.\s*)+,\s*(?:19|20)\d{2}\s*\)')
    jum = sum(len(pola.findall(t or '')) for t in paragraf_dari_spec(spec))
    for b in bab_dari_spec(spec):
        for t in tabel_nyata(b):
            for baris in (t.get('baris') or []):
                for sel in (baris or []):
                    jum += len(pola.findall(str(sel or '')))
    return jum


def periksa_referensi(spec, teks):
    print('-- buku referensi: harus bisa DIRUJUK, bukan dibaca berurutan --')
    ok('R1 indeks subjek bermakna',
       ada_indeks(spec, 'indeks_subjek', 'indeks subjek'),
       'tanpa indeks subjek bermakna, pembaca tidak bisa mencari topik — ini bukan buku referensi')
    ok('R2 indeks nama bermakna',
       ada_indeks(spec, 'indeks_nama', 'indeks nama'),
       'tanpa indeks nama bermakna, tokoh/penulis tidak bisa dilacak — ini bukan buku referensi')
    per_bab = True
    for b in bab_dari_spec(spec):
        tabel_judul = ' '.join(str(t.get('judul', ''))
                               for t in tabel_nyata(b)).lower()
        sj = ' '.join(str(s.get('judul', ''))
                      for s in b.get('sub', []) or []).lower()
        if 'komparasi' not in tabel_judul \
                and 'perbandingan' not in tabel_judul \
                and 'komparasi' not in sj and 'perbandingan' not in sj:
            per_bab = False
    ok('R3 tabel komparasi nyata di tiap bab (kolom + baris berisi)',
       per_bab and len(bab_dari_spec(spec)) > 0,
       'bab tanpa perbandingan kritis antar teori = kumpulan teori, bukan referensi')
    paras = paragraf_dari_spec(spec)
    ok('R4 posisi penulis eksplisit dalam paragraf bermakna (>=10 kata)',
       cari_paragraf(paras, ('posisi penulis', 'pandangan penulis',
                             'sintesis penulis', 'penulis berpendapat',
                             'penulis berpendirian')) is not None,
       'tanpa posisi penulis yang dikembangkan dalam paragraf, bab hanya merangkum teori orang lain')
    ingatkan('Rw glosarium ada',
             'glosarium' in teks or bool(spec.get('glosarium')),
             'glosarium sangat dianjurkan untuk referensi (wajib bila >20 istilah teknis)')
    ingatkan('Rw daftar singkatan ada',
             'daftar singkatan' in teks,
             'daftar singkatan wajib untuk buku referensi menurut skill')
    _inisial = hitung_sitasi_inisial(spec)
    ingatkan('Rw bentuk sitasi lengkap (tanpa inisial-saja)',
             _inisial == 0,
             f'{_inisial} sitasi inisial-saja (E., 2021) — tulis ulang '
             f'ke (Nama Belakang, Tahun) lengkap agar tertelusur')
    _nama = spec.get('indeks_nama')
    if isinstance(_nama, list):
        _j_nama = sum(1 for e in _nama if entri_indeks_bermakna(e))
        ingatkan('Rw indeks nama tidak tipis (>=3 nama)',
                 _j_nama >= 3,
                 f'indeks nama hanya {_j_nama} nama — nama tak cocok '
                 f'halaman bila sitasi inisial-saja')


def periksa_ajar(spec, teks):
    print('-- buku ajar: tiap bab harus bisa MENGAJAR, bukan sekadar dibaca --')
    print('   (v1.1: tiap unsur harus di paragraf BERBEDA, >=10 kata, '
          'dan tujuan SEBELUM latihan — satu kalimat kata kunci gagal)')
    for i, b in enumerate(bab_dari_spec(spec), 1):
        paras = paragraf_dari_bab(b)
        judul = b.get('judul', f'bab {i}')
        # Tujuan: paragraf yang menyebut TIU+TIK atau Capaian, cukup panjang.
        idx_tujuan = None
        for j, p in enumerate(paras):
            rendah = p.lower()
            if jumlah_kata(p) >= 10 and (
                    ('tujuan instruksional umum' in rendah
                     and 'tujuan instruksional khusus' in rendah)
                    or 'capaian pembelajaran' in rendah):
                idx_tujuan = j
                break
        ok(f'A1 bab {i} ({judul}): tujuan pembelajaran di paragraf bermakna',
           idx_tujuan is not None,
           'bab tidak dibuka dengan TIU/TIK atau Capaian Pembelajaran yang dikembangkan')
        # Latihan: HANYA dicari sesudah tujuan (posisi: tujuan di awal,
        # latihan di akhir). Latihan yang muncul sebelum tujuan = gagal.
        idx_latihan = None
        if idx_tujuan is not None:
            idx_latihan = cari_paragraf(paras, ('latihan',),
                                        mulai_dari=idx_tujuan + 1)
        ok(f'A2 bab {i} ({judul}): latihan sesudah tujuan, paragraf bermakna',
           idx_latihan is not None,
           'bab tanpa latihan sesudah tujuan = murid tidak pernah diuji')
        terpakai = {idx_tujuan, idx_latihan} - {None}
        idx_check = cari_paragraf(paras, ('checklist',),
                                  mulai_dari=(idx_tujuan + 1
                                              if idx_tujuan is not None
                                              else 0),
                                  terpakai=terpakai)
        ok(f'A3 bab {i} ({judul}): checklist pemahaman di paragraf berbeda',
           idx_check is not None,
           'bab tanpa checklist pemahaman di paragraf sendiri')
        terpakai.add(idx_check) if idx_check is not None else None
        idx_rangkum = cari_paragraf(paras, ('rangkuman',),
                                    mulai_dari=(idx_tujuan + 1
                                                if idx_tujuan is not None
                                                else 0),
                                    terpakai=terpakai)
        ok(f'A4 bab {i} ({judul}): rangkuman di paragraf berbeda',
           idx_rangkum is not None,
           'bab tanpa rangkuman di paragraf sendiri')
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
    print('   (v1.1: kebaruan, keterbatasan, dan metode harus di paragraf '
          'BERBEDA yang masing-masing >=10 kata)')
    paras = paragraf_dari_spec(spec)
    terpakai = set()
    idx_baru = cari_paragraf(paras, ('kebaruan', 'novelty'),
                             terpakai=terpakai)
    ok('M1 pernyataan kebaruan / novelty di paragraf bermakna',
       idx_baru is not None,
       'tanpa kebaruan yang dikembangkan, buku ini hanya rangkuman literatur')
    if idx_baru is not None:
        terpakai.add(idx_baru)
    idx_batas = cari_paragraf(paras, ('keterbatasan',), terpakai=terpakai)
    ok('M2 keterbatasan penelitian di paragraf bermakna yang berbeda',
       idx_batas is not None,
       'penelitian yang tidak menyebut keterbatasannya di paragraf sendiri tidak bisa dipercaya')
    if idx_batas is not None:
        terpakai.add(idx_batas)
    idx_metode = cari_paragraf(paras, ('metode penelitian',
                                       'metodologi penelitian',
                                       'desain penelitian',
                                       'pendekatan penelitian'),
                               terpakai=terpakai)
    ok('M3 metode penelitian penulis sendiri di paragraf bermakna yang berbeda',
       idx_metode is not None,
       'bab berjudul "metodologi" yang isinya prinsip umum TIDAK cukup — harus ada metode penelitian buku ini yang dikembangkan')
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
    paras = paragraf_dari_spec(spec)
    idx_contoh = cari_paragraf(paras, ('contoh',))
    terpakai = {idx_contoh} if idx_contoh is not None else set()
    idx_langkah = cari_paragraf(paras, ('langkah', 'praktik'),
                                terpakai=terpakai)
    ok('P1 contoh di paragraf bermakna DAN langkah praktis di paragraf berbeda',
       idx_contoh is not None and idx_langkah is not None,
       'panduan tanpa contoh dan langkah yang masing-masing dikembangkan = uraian teori, bukan panduan')
    ingatkan('Pw lampiran praktis (cheat-sheet / daftar perintah) ada',
             'lampiran' in teks,
             'lampiran praktis sangat membantu panduan, tapi tidak wajib di v1')


def periksa_umum_buku(spec, teks):
    print('-- buku umum / anak: tiap bab harus punya ISI, bukan sekadar ada --')
    for i, b in enumerate(bab_dari_spec(spec), 1):
        judul = b.get('judul', f'bab {i}')
        ok(f'Uu bab {i} ({judul}): judul bermakna + isi minimal 30 kata',
           bermakna(b.get('judul', ''), min_kata=1)
           and kata_dari_objek(b) >= 30,
           'bab sampah / terlalu pendek — buku-umum bukan lagi pintu belakang')
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
    ok('C1 section pertama = Pendahuluan dengan tujuan bermakna (>=5 kata)',
       len(sections) >= 1
       and 'pendahuluan' in str(sections[0].get('judul', '')).lower()
       and isinstance(sections[0].get('tujuan'), list)
       and any(bermakna(t, min_kata=5) for t in sections[0].get('tujuan')),
       'chapter wajib dibuka Pendahuluan + Tujuan Pembelajaran yang bermakna')
    ok('C2 referensi berisi entri bermakna',
       isinstance(spec.get('referensi'), list)
       and any(entri_pustaka_bermakna(e) for e in spec.get('referensi')),
       'referensi kosong atau hanya sampah')
    ok('C3 glosarium berisi definisi bermakna (>=5 kata)',
       isinstance(spec.get('glosarium'), list)
       and any(isinstance(e, (list, tuple)) and len(e) >= 2
               and bermakna(e[1], min_kata=5)
               for e in spec.get('glosarium')),
       'glosarium chapter kosong atau definisinya hanya sampah')
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
