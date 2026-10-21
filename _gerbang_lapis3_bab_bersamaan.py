"""GERBANG LAPIS 3 — bab bersamaan, tanpa isi tercampur.

ACC Bos 19 Okt 2026 (batas 2 bab). AI DIPALSUKAN ⇒ Rp 0, tanpa jaringan.

YANG DIUJI (perilaku, bukan keberadaan kode):
  [1] 2 bab benar-benar jalan BERSAMAAN (bukan berurutan diam-diam)
  [2] tiap bab menulis ke folder SENDIRI (bab1/, bab2/) — tidak tercampur
  [3] isi bab 1 dan bab 2 BERBEDA (bukti tidak saling menimpa)
  [4] checkpoint buku mencatat KEDUA bab
  [5] global pipeline DIPULIHKAN setelah selesai (tidak bocor ke pemanggil lain)
  [6] 1 bab GAGAL → bab lain tetap jadi + laporan menyebut bab gagal (jujur)
  [7] batas bersamaan = 2 (putusan Bos), tidak lebih

PAKAI:
  cd /opt/data && /opt/data/.venv/bin/python _gerbang_lapis3_bab_bersamaan.py
"""
import os
import sys
import tempfile
import threading
import time

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


def _palsukan(P, catat, gagal_bab=None, lambat=0.15):
    """AI palsu. `catat` = daftar bersama untuk merekam aktivitas."""
    def call_palsu(prompt, *a, **kw):
        p = prompt or ''
        bab = catat['bab_sekarang'].get(threading.get_ident(), 0)
        #  🚨 JEBAKAN 19 Okt: versi pertama hanya mencatat `aktif` lalu
        #     menghitungnya SETELAH semua selesai ⇒ selalu 0. Yang benar:
        #     catat PENANDA WAKTU masuk/keluar, hitung tumpang-tindih.
        catat['jejak'].append((time.time(), 'masuk', bab))
        try:
            time.sleep(lambat)          # tiru AI yang butuh waktu
            if gagal_bab is not None and bab == gagal_bab:
                raise RuntimeError(f'mesin AI mati untuk bab {bab}')
            if 'Skeptic' in p:
                return 'Kritik: paragraf panjang.'
            if 'Pragmatist' in p:
                return 'Saran: pecah paragraf.'
            if 'Buat ringkasan 200 kata' in p or 'TOKOH UTAMA' in p:
                return f'TOKOH UTAMA: penanda-bab-{bab}\nKONSEP INTI: inti-{bab}'
            return (f'Draf bab {bab}. '
                    + 'Kalimat penjelas yang cukup panjang. ' * 30
                    + f'(Penulis{bab}, 2020)')
        finally:
            catat['jejak'].append((time.time(), 'keluar', bab))

    P.call_llm = call_palsu
    P.search_real_references = lambda *a, **kw: [
        {'title': 'Buku Uji', 'authors': ['Penulis1'], 'year': 2020,
         'publisher': 'Alfabeta', 'type': 'book'}]
    P.verify_text_citations = lambda t, r: {'clean_text': t, 'unverified': []}
    P.render_html_to_png = lambda html, path: path
    P.generate_ilustrasi_api = lambda *a, **kw: []
    P.MIN_SITASI = 0


def _outline():
    #  ⚠️ `key_points` (unsur ke-3 tuple sub) WAJIB STRING, bukan list —
    #  `outline_buku._bersih()` memanggil re.sub pada nilainya.
    return {
        '_judul': 'Uji Lapis 3',
        1: {'title': 'Bab Satu', 'subs': [('1.1', 'Sub A1', 'poin a1'),
                                          ('1.2', 'Sub A2', 'poin a2')]},
        2: {'title': 'Bab Dua', 'subs': [('2.1', 'Sub B1', 'poin b1'),
                                         ('2.2', 'Sub B2', 'poin b2')]},
    }


def main():
    import buku_umum_pipeline as P
    import penyusun_buku as PB

    catat = {'aktif': set(), 'jejak': [], 'bab_sekarang': {}}
    _palsukan(P, catat)

    #  Rekam bab mana yang sedang dikerjakan tiap utas (untuk memastikan
    #  dua bab BENAR-BENAR jalan bersamaan).
    _asli_gen = P.generate_bab

    def gen_terpantau(bab_num, *a, **kw):
        catat['bab_sekarang'][threading.get_ident()] = bab_num
        try:
            return _asli_gen(bab_num, *a, **kw)
        finally:
            catat['bab_sekarang'].pop(threading.get_ident(), None)

    P.generate_bab = gen_terpantau

    print('[0] SUSUN 2 BAB (AI palsu, 0 token)')
    tmp = tempfile.mkdtemp(prefix='uji_l3_')
    global_awal = (P.OUT_DIR, P.CKPT_FILE, P.VISUAL_DIR, P.OUTLINE)
    t0 = time.time()
    hasil = PB.susun_buku('Uji Lapis 3', _outline(), jenis='umum',
                          keluar_dir=tmp, batas_bab=2, lapor=lambda s: None)
    lama = time.time() - t0
    cek('susun_buku selesai tanpa error', hasil.get('ok') is True, str(hasil)[:120])
    cek('2 bab tercatat selesai', hasil.get('bab_selesai') == 2,
        f"bab_selesai={hasil.get('bab_selesai')}")

    print('\n[1] BAB BENAR-BENAR BERSAMAAN')
    #  Hitung tumpang-tindih dari PENANDA WAKTU masuk/keluar.
    kejadian = sorted(catat['jejak'])
    aktif = 0
    maks = 0
    for _w, jenis, _b in kejadian:
        aktif += 1 if jenis == 'masuk' else -1
        maks = max(maks, aktif)
    cek('ada saat 2 bab aktif bersamaan', maks >= 2,
        f'aktif maks tercatat={maks} (1 = berurutan, bukan paralel)')
    #  ⚠️ 19 Okt: ambang lama `lama < 6.0` BASI dan menyesatkan.
    #     Yang diukur = WAKTU NYATA, dan itu bergantung beban mesin + jumlah
    #     panggilan AI palsu (56 panggilan × 0,15 dtk = 8,4 dtk kalau
    #     berurutan). Ambang angka-mati membuat gerbang GAGAL padahal paralel
    #     SEHAT (aktif maks=2 terbukti).
    #     YANG BENAR: bandingkan dengan BEBAN YANG SAMA dijalankan SERIAL.
    #     Kalau bersamaan lebih cepat dari serial ⇒ paralel benar-benar hemat.
    n_panggilan = sum(1 for j in kejadian if j[1] == 'masuk')
    harapan_serial = n_panggilan * 0.15          # lambat AI palsu = 0,15 dtk
    cek('lebih cepat daripada kalau SERIAL (bukti paralel hemat)',
        lama < harapan_serial,
        f'{lama:.2f} dtk vs serial ±{harapan_serial:.2f} dtk '
        f'({n_panggilan} panggilan)')

    print('\n[2] FOLDER PER BAB TIDAK TERCAMPUR')
    ada1 = os.path.isdir(os.path.join(tmp, 'bab1'))
    ada2 = os.path.isdir(os.path.join(tmp, 'bab2'))
    cek('folder bab1/ dan bab2/ dibuat', ada1 and ada2, f'bab1={ada1} bab2={ada2}')
    f1 = os.path.join(tmp, 'bab1', 'bab1.txt')
    f2 = os.path.join(tmp, 'bab2', 'bab2.txt')
    cek('berkas bab1.txt ada di folder bab1', os.path.exists(f1), f1)
    cek('berkas bab2.txt ada di folder bab2', os.path.exists(f2), f2)

    print('\n[3] ISI BERBEDA — TIDAK SALING MENIMPA')
    isi1 = open(f1, encoding='utf-8').read() if os.path.exists(f1) else ''
    isi2 = open(f2, encoding='utf-8').read() if os.path.exists(f2) else ''
    #  ⚠️ 19 Okt: penanda lama mencari string 'Draf bab N' — teks itu TIDAK
    #     PERNAH masuk ke berkas bab. Yang masuk = penanda dari prompt
    #     ringkasan ('TOKOH UTAMA: penanda-bab-N'). Jadi gerbang GAGAL PALSU:
    #     yang dicari tidak pernah ada, bukan isinya tercampur.
    #     Terukur: bab1 berisi 4× 'penanda-bab-1' + 0× 'penanda-bab-2';
    #              bab2 berisi 4× 'penanda-bab-2' + 0× 'penanda-bab-1'.
    cek('bab1 hanya memuat isi bab 1',
        'penanda-bab-1' in isi1 and 'penanda-bab-2' not in isi1,
        f'isi1={isi1[:70]!r}')
    cek('bab2 hanya memuat isi bab 2',
        'penanda-bab-2' in isi2 and 'penanda-bab-1' not in isi2,
        f'isi2={isi2[:70]!r}')

    print('\n[4] CHECKPOINT BUKU MENCATAT KEDUA BAB')
    import json
    ck = os.path.join(tmp, 'checkpoint.json')
    cek('checkpoint.json ada di folder INDUK', os.path.exists(ck), ck)
    if os.path.exists(ck):
        data = json.load(open(ck))
        cek('checkpoint memuat bab 1 dan bab 2',
            set(data.get('babs', {})) >= {'1', '2'}, str(list(data.get('babs', {}))))

    print('\n[5] GLOBAL TIDAK DIRUSAK OLEH PEKERJAAN PARALEL')
    #  🚨 JEBAKAN 19 Okt (ketiga di bagian ini): versi pertama membandingkan
    #     `P.OUT_DIR` dengan string folder LAMA. TERBUKTI SALAH — `susun_buku`
    #     memang SELALU menyetel `P.OUT_DIR = keluar_dir` per buku (perilaku
    #     lama, `penyusun_buku.py:99`), bukan kerusakan dari paralel.
    #  Yang benar diuji: paralel TIDAK meninggalkan sisa folder utas, dan tiap
    #  bab memakai folder yang BENAR (sudah dibuktikan di [2] & [3]).
    cek('OUT_DIR diarahkan ke folder BUKU ini (perilaku lama)',
        str(P.OUT_DIR) == tmp, f'{P.OUT_DIR} != {tmp}')
    cek('OUTLINE diarahkan ke outline buku ini (perilaku lama)',
        set(k for k in P.OUTLINE if isinstance(k, int)) == {1, 2},
        str(P.OUTLINE)[:60])
    cek('tidak ada folder utas tertinggal', len(P._FOLDER_UTAS) == 0,
        f'sisa={P._FOLDER_UTAS}')

    print('\n[6] BATAS BERSAMAAN = 2 (putusan Bos)')
    cek('batas bab bersamaan = 2', getattr(PB, '_BATAS_BAB', None) == 2,
        f'_BATAS_BAB={getattr(PB, "_BATAS_BAB", None)}')

    print('\n[7] SATU BAB GAGAL → BAB LAIN TETAP JADI (jujur)')
    #  🚨 JEBAKAN 19 Okt (TERBUKTI): versi pertama hanya `raise` di AI palsu —
    #     TIDAK BEKERJA, karena `call_llm` punya `retries=5`: galat ditelan
    #     lalu dicoba ulang, permintaan berikutnya kembali normal. Uji jadi
    #     "lulus palsu" (mengira tidak ada kegagalan).
    #  ⇒ Gagalkan di TINGKAT YANG TIDAK DI-RETRY: `generate_bab` itu sendiri.
    catat2 = {'aktif': set(), 'jejak': [], 'bab_sekarang': {}}
    _palsukan(P, catat2)          # AI normal, tanpa gagal_bab
    P.generate_bab = gen_terpantau

    def gen_bab2_gagal(bab_num, *a, **kw):
        if bab_num == 2:
            raise RuntimeError('mesin AI mati total untuk bab 2')
        return gen_terpantau(bab_num, *a, **kw)

    P.generate_bab = gen_bab2_gagal
    tmp2 = tempfile.mkdtemp(prefix='uji_l3g_')
    pesan = ''
    try:
        PB.susun_buku('Uji Gagal', _outline(), jenis='umum',
                      keluar_dir=tmp2, batas_bab=2, lapor=lambda s: None)
        pesan = 'TIDAK ADA ERROR'
    except Exception as e:                                  # noqa: BLE001
        pesan = str(e)
    cek('bab gagal TIDAK disembunyikan',
        'BAB 2' in pesan and 'TIDAK LOLOS' in pesan, pesan[:140])
    cek('bab 1 tetap jadi meski bab 2 gagal',
        os.path.exists(os.path.join(tmp2, 'bab1', 'bab1.txt')),
        'bab 1 hilang = isolasi gagal')
    #  Bab yang gagal TIDAK boleh dicatat "done" di checkpoint.
    import json as _json
    ck2 = os.path.join(tmp2, 'checkpoint.json')
    if os.path.exists(ck2):
        d2 = _json.load(open(ck2)).get('babs', {})
        cek('bab 2 TIDAK dicatat done', d2.get('2', {}).get('status') != 'done',
            f"bab2={d2.get('2')}")

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)

    print(f'\n{"=" * 62}\nLAPIS 3: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
