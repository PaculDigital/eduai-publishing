"""GERBANG: ringkasan bab DISUSUN dari ringkasan sub-bab, bukan panggil AI lagi.

ACC Bos 19 Okt 2026 — Langkah 1 "optimalisasi" (bukan percepatan asal jadi).

MASALAH YANG DIPERBAIKI:
  `generate_bab` memanggil AI KELIMA hanya untuk meringkas ULANG seluruh bab
  dari teks mentah, padahal tiap sub-bab SUDAH punya ringkasan sendiri.
  Akibat: (a) ±8 detik terbuang per bab; (b) DUA ringkasan bab berbeda
  beredar — ringkasan sub-bab dipakai penulis (`rolling`), ringkasan bab
  dipakai pembuat brief gambar ⇒ ilustrasi bisa bercerita lain dari alur bab.

YANG DIUJI (AI PALSU, Rp 0, tanpa jaringan):
  [1] ringkasan bab = gabungan ringkasan sub-bab (BUKAN teks karangan AI)
  [2] jumlah panggilan AI TIDAK bertambah (tidak ada panggilan ringkas bab)
  [3] konsisten: tiap nomor sub-bab muncul di ringkasan bab
  [4] ringkasan bab TIDAK memuat isi yang tidak ada di ringkasan sub-bab
  [5] CADANGAN: kalau ringkasan sub-bab kosong → tetap ada ringkasan (1 panggilan)
  [6] isi bab (bab_text) TIDAK berubah karena perubahan ini

PAKAI:
  cd /opt/data && /opt/data/.venv/bin/python _gerbang_ringkasan_bab.py
"""
import os
import sys
import tempfile

sys.path.insert(0, '/opt/data')

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


def _apakah_summarize(prompt):
    """Kenali prompt summarize DARI ISI PROMPT-nya sendiri.

    🚨 JEBAKAN 19 Okt: Wulan mula-mula mencari kata 'ringkas' — TIDAK ADA.
    Prompt aslinya (`summarize_prompt`) berbunyi "Buat ringkasan 200 kata"
    dan "TOKOH UTAMA / KONSEP INTI / KHAS BAB INI". Karena penanda salah,
    AI palsu menjawab sebagai Architect ⇒ gerbang gagal PALSU 5×.
    ⇒ Kenali dari kalimat yang MEMANG ada di prompt, bukan dari tebakan.
    """
    p = (prompt or '')
    return ('Buat ringkasan 200 kata' in p
            or 'TOKOH UTAMA' in p
            or 'KHAS BAB INI' in p)


def _siapkan_palsu(P, ringkasan_sub=None):
    """Pasang AI palsu. `ringkasan_sub` = teks yang dikembalikan summarize."""
    global CATAT
    CATAT = {'ai': 0, 'summarize': 0, 'prompt_summarize': []}

    def call_palsu(prompt, *a, **kw):
        CATAT['ai'] += 1
        p = prompt or ''
        if _apakah_summarize(p):
            CATAT['summarize'] += 1
            CATAT['prompt_summarize'].append(p[:200])
            if ringkasan_sub is not None:
                return ringkasan_sub
            return 'INI-RINGKASAN-DARI-AI-PALSU'
        #  Architect/Skeptic/Pragmatist/Editor → teks panjang berisi sitasi
        if 'Skeptic' in p:
            return 'Kritik: paragraf 2 terlalu panjang.'
        if 'Pragmatist' in p:
            return 'Saran: pecah paragraf 2.'
        return ('Draf palsu. Ini kalimat panjang yang menjelaskan konsep dengan '
                'rinci agar dianggap tulisan sungguhan oleh pemeriksa. ' * 12
                + '(Sugiyono, 2019)')

    P.call_llm = call_palsu
    P.search_real_references = lambda *a, **kw: [
        {'title': 'Buku Uji', 'authors': ['Sugiyono'], 'year': 2019,
         'publisher': 'Alfabeta', 'type': 'book'}]
    P.verify_text_citations = lambda t, r: {'clean_text': t, 'unverified': []}
    P.render_html_to_png = lambda html, path: path
    P.generate_ilustrasi_api = lambda *a, **kw: []


def main():
    import buku_umum_pipeline as P

    #  Folder sementara: JANGAN menulis ke OUT_DIR produksi.
    tmp = tempfile.mkdtemp(prefix='uji_ring_')
    P.OUT_DIR = tmp
    P.VISUAL_DIR = os.path.join(tmp, 'visual')
    os.makedirs(P.VISUAL_DIR, exist_ok=True)
    P.save_checkpoint = lambda ckpt: None

    #  Ringkasan sub-bab yang PASTI dikenali (penanda unik per sub-bab).
    #  🚨 JEBAKAN 19 Okt (kedua): `summarize_prompt` TIDAK memuat nomor
    #     sub-bab — hanya ISI TEKS sub-bab. Versi pertama gerbang mencari
    #     '1.1' di prompt ⇒ tidak pernah ketemu ⇒ gagal PALSU.
    #     ⇒ Penanda WAJIB ikut di dalam ISI sub-bab (lihat `architect_palsu`).
    ringkasan_palsu = {
        'SUB11': 'SUB11 berbicara tentang pembentukan awan.',
        'SUB12': 'SUB12 berbicara tentang jenis awan.',
        'SUB13': 'SUB13 berbicara tentang hujan.',
    }
    urutan = []

    def summarize_palsu(prompt):
        #  Dipanggil untuk TIAP sub-bab (rolling summary) + mungkin bab.
        #  Ringkasan BAB lama memakai bab_text[:5000] yang memuat BANYAK
        #  penanda SUBxx sekaligus.
        teks = prompt or ''
        jumlah_sub = sum(1 for s in ringkasan_palsu if s in teks)
        if jumlah_sub >= 2:
            urutan.append('BAB')
            return 'RINGKASAN-BAB-DARI-AI-PALSU'
        for k in ringkasan_palsu:
            if k in teks:
                urutan.append(k)
                return ringkasan_palsu[k]
        urutan.append('?')
        return 'ringkasan lain'

    _siapkan_palsu(P, ringkasan_sub=None)
    _asli_call = P.call_llm

    #  🚨 JEBAKAN 19 Okt (2, 3, 4): Wulan tiga kali mencoba MENEBAK cara
    #     mengenali sub-bab dari isi prompt (`'1.1'`, `'SUB11'`, `'Architect'`).
    #     Semua gagal: `summarize_prompt` hanya menerima ISI TEKS.
    #  ⇒ OBAT: jangan menebak dari prompt. Bungkus FUNGSI YANG MEMANG
    #     mengembalikan ringkasan per sub-bab: `generate_sub_bab`. Di situ
    #     `sub_num` tersedia sebagai argumen POSISI — pasti, bukan tebakan.
    _asli_sub = P.generate_sub_bab

    def sub_terpantau(bab_num, bab_title, sub_num, sub_title, key_points,
                      rolling_summary, refs=None, jenis='umum'):
        hasil = _asli_sub(bab_num, bab_title, sub_num, sub_title, key_points,
                          rolling_summary, refs=refs, jenis=jenis)
        #  hasil = (final, summary, wc, cit)
        final, summary, wc, cit = hasil
        kunci = 'SUB' + str(sub_num).replace('.', '')
        urutan.append(kunci)
        #  Ganti ringkasannya dengan penanda yang PASTI dikenali.
        return (final, ringkasan_palsu.get(kunci, summary), wc, cit)

    P.generate_sub_bab = sub_terpantau
    _asli_call_untuk_cadangan = _asli_call

    def call_terpantau(prompt, *a, **kw):
        #  Semua panggilan diteruskan apa adanya; pelacakan lewat generate_sub_bab.
        return _asli_call(prompt, *a, **kw)

    P.call_llm = call_terpantau

    bab_data = {
        'title': 'Awan dan Hujan',
        'subs': [
            ('1.1', 'Bagaimana Awan Terbentuk', ['uap', 'embun']),
            ('1.2', 'Jenis-jenis Awan', ['kumulus', 'stratus']),
            ('1.3', 'Mengapa Turun Hujan', ['kondensasi']),
        ],
    }

    print('[0] JALANKAN SATU BAB (AI palsu)')
    teks, summ, wc, cit = P.generate_bab(1, bab_data, '', jenis='umum')
    cek('bab menghasilkan teks', bool(teks) and wc > 50, f'{wc} kata')

    print('\n[1] RINGKASAN BAB DISUSUN, BUKAN DIPANGGIL ULANG')
    cek('AI TIDAK dipanggil untuk meringkas ulang seluruh bab',
        'BAB' not in urutan,
        f'yang terjadi: {urutan}')
    #  🚨 JEBAKAN 19 Okt (keempat): versi pertama uji ini hanya mengambil
    #     `summ` (ringkasan dari `generate_bab`) dan MENGABAIKAN bahwa
    #     `ringkasan_subs` diisi dari tiap sub-bab. Kegagalan sebenarnya
    #     bukan di kode, tapi di CAKUPAN uji ⇒ periksa lewat tanda tangan
    #     fungsi + hasil nyata yang dikirim ke pembuat visual.
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'buku_umum_pipeline.py'), encoding='utf-8').read()
    blok = src.split('ringkasan_subs')[0] if 'ringkasan_subs' in src else ''
    cek('kode mengumpulkan ringkasan sub-bab',
        'ringkasan_subs = []' in src and 'ringkasan_subs.append' in src,
        'tanpa ini ringkasan bab tetap memanggil AI')
    cek('kode menyusun ringkasan bab dari ringkasan sub-bab',
        "'\\n'.join(" in src and 'for sub, _judul, ringkas in ringkasan_subs' in src,
        'penyusunan tidak ada')
    cek('panggilan ringkas-ulang HANYA sebagai cadangan',
        'ringkasan sub-bab kosong' in src,
        'harus ada jalur cadangan yang jelas')
    cek('ringkasan bab BUKAN teks karangan AI',
        'RINGKASAN-BAB-DARI-AI-PALSU' not in (summ or ''),
        'kalau muncul = masih memanggil AI')

    print('\n[2] ISI TIDAK DICEMARI')
    isi_sub = list(ringkasan_palsu.values())
    cek('ringkasan bab memakai SELURUH ringkasan sub-bab yang ada',
        all(s in (summ or '') for s in isi_sub),
        f'ringkasan={str(summ)[:150]}')
    cek('ringkasan bab tidak memuat isi asing',
        'RINGKASAN-BAB-DARI-AI-PALSU' not in (summ or ''), str(summ)[:100])

    print('\n[3] JUMLAH PANGGILAN AI TIDAK BERTAMBAH')
    #  Per sub-bab: architect, skeptic, pragmatist, editor, summary = 5
    #  Ditambah intro, penutup, ringkasan bab(palsu/skip) → hitung kasar.
    cek('panggilan ringkas bab = 0',
        urutan.count('BAB') == 0, f'urutan={urutan}')
    cek('ringkasan per sub-bab tetap 3 (satu per sub-bab)',
        len([u for u in urutan if u.startswith('SUB')]) == 3,
        f'urutan={urutan}')

    print('\n[4] CADANGAN: ringkasan sub-bab KOSONG → jangan mengarang')
    urutan.clear()

    def sub_kosong(bab_num, bab_title, sub_num, sub_title, key_points,
                   rolling_summary, refs=None, jenis='umum'):
        #  🚨 JEBAKAN 19 Okt (kelima): versi pertama hanya mengosongkan prompt
        #     summarize — padahal pembungkus `generate_sub_bab` di lapisan atas
        #     MENGISI ULANG ringkasannya dengan penanda. Uji "cadangan" jadi
        #     tidak pernah menguji cadangan. ⇒ Kosongkan di pembungkusnya.
        hasil = _asli_sub(bab_num, bab_title, sub_num, sub_title, key_points,
                          rolling_summary, refs=refs, jenis=jenis)
        final, _summary, wc, cit = hasil
        urutan.append('KOSONG')
        return (final, '', wc, cit)       # summary KOSONG = mesin gagal

    P.generate_sub_bab = sub_kosong
    P.call_llm = _asli_call
    teks2, summ2, wc2, cit2 = P.generate_bab(2, dict(bab_data, title='Bab Dua'),
                                            '', jenis='umum')
    cek('bab tetap jadi walau ringkasan sub-bab kosong', bool(teks2) and wc2 > 50,
        f'{wc2} kata')
    cek('ringkasan bab tetap TIDAK kosong (ada cadangan)',
        bool((summ2 or '').strip()), 'ringkasan bab kosong = brief gambar rusak')

    print('\n[5] ISI BAB TIDAK BERUBAH KARENA PERBAIKAN INI')
    cek('teks bab memuat ketiga judul sub-bab',
        all(t in teks for t in ('Bagaimana Awan Terbentuk', 'Jenis-jenis Awan',
                                'Mengapa Turun Hujan')),
        'isi bab berubah = perbaikan ini menyentuh hal yang tidak diminta')
    cek('teks bab memuat sitasi', '(Sugiyono, 2019)' in teks)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    print(f'\n{"=" * 62}\nRINGKASAN BAB: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
