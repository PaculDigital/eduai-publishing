"""Uji retry per bab A1 (30 Okt 2026, job 221), tanpa LLM/API/DB.

Jalankan dari checkout:
  PYTHONPATH=/opt/data/services/eduai-publishing /opt/hermes/.venv/bin/python3 uji_anti_gagal_retry.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.

Yang dibuktikan (eksekutor bab di-mock, tidur di-mock supaya uji tidak
menunggu 5/15/30 detik betulan):
  1. eksekutor gagal 2x lalu berhasil: bab selesai tanpa restart job
     dan tanpa mengulang bab lain (jumlah panggilan per bab dibuktikan).
  2. eksekutor mengembalikan None (dan varian AttributeError .split()
     atas None di jalur lama): di-retry, tidak crash.
  3. checkpoint berisi bab 1-2 selesai: run dimulai dari bab 3,
     eksekutor bab 1-2 TIDAK terpanggil.
  4. gagal pada semua percobaan: gagal bersih BabGagal (subclass
     RuntimeError, jalur refund), bukan AttributeError mentah, dengan
     backoff tercatat 5, 15, 30 detik dan total 4 percobaan (1 awal
     plus 3 pengulangan).
"""

import json
import os
import sys
import tempfile

for p in (os.getcwd(), '/opt/data/services/eduai-publishing', '/app'):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from app import penyusunan_buku as PB

LULUS = 0
GAGAL = []


def cek(nama, ok, info=''):
    global LULUS
    if ok:
        LULUS += 1
        print('  LULUS %s' % nama)
    else:
        GAGAL.append(nama)
        print('  GAGAL %s %s' % (nama, info))


TEKS = ('Bab ini membahas teori dan praktik dengan contoh konkret '
        'yang mudah dipahami dan bisa langsung dipakai pembaca. ') * 5


class PerekamTidur:
    def __init__(self):
        self.jeda = []

    def __call__(self, detik):
        self.jeda.append(detik)


def test_gagal_2x_lalu_berhasil():
    panggilan = {}

    def eksekutor(n):
        panggilan[n] = panggilan.get(n, 0) + 1
        if n == 2 and panggilan[n] <= 2:
            raise RuntimeError('provider kosong percobaan %s' % panggilan[n])
        return TEKS

    tidur = PerekamTidur()
    hasil = PB.jalankan_semua_bab([1, 2, 3], eksekutor, tidur=tidur)
    cek('retry-gagal-2x-lalu-berhasil',
        hasil == {1: TEKS, 2: TEKS, 3: TEKS}
        and panggilan == {1: 1, 2: 3, 3: 1}
        and tidur.jeda == [5, 15],
        'panggilan=%r jeda=%r' % (panggilan, tidur.jeda))


def test_none_di_retry_tanpa_crash():
    panggilan = {'n': 0}

    def eksekutor_none(n):
        panggilan['n'] += 1
        if panggilan['n'] == 1:
            return None
        return TEKS

    tidur = PerekamTidur()
    hasil = PB.jalankan_bab_dengan_retry(1, eksekutor_none, tidur=tidur)
    ok_none = hasil == TEKS and panggilan['n'] == 2 and tidur.jeda == [5]
    cek('retry-none-tanpa-crash', ok_none,
        'panggilan=%r jeda=%r' % (panggilan, tidur.jeda))

    def eksekutor_split(n):
        raise AttributeError("'NoneType' object has no attribute 'split'")

    # Varian crash jalur lama: AttributeError harus diubah jadi
    # percobaan gagal, dan sesudah habis jadi BabGagal bersih.
    tidur2 = PerekamTidur()
    try:
        PB.jalankan_bab_dengan_retry(1, eksekutor_split, tidur=tidur2)
        ok_split = False
        info = 'tidak raise'
    except AttributeError as e:
        ok_split = False
        info = 'masih AttributeError mentah: %s' % e
    except PB.BabGagal:
        ok_split = tidur2.jeda == [5, 15, 30]
        info = 'jeda=%r' % (tidur2.jeda,)
    except Exception as e:
        ok_split = False
        info = 'tipe salah: %s: %s' % (type(e).__name__, e)
    cek('retry-attributeerror-jadi-babgagal', ok_split, info)


def test_checkpoint_lewati_bab_selesai():
    with tempfile.TemporaryDirectory() as tmp:
        ckpt = {'judul': 'Uji', 'jenis': 'umum', 'babs': {
            '1': {'status': 'done', 'words': 500, 'file': 'bab1.txt'},
            '2': {'status': 'done', 'words': 400, 'file': 'bab2.txt'},
            '3': {'status': 'gagal', 'words': 0},
        }}
        with open(os.path.join(tmp, 'checkpoint.json'), 'w',
                  encoding='utf-8') as fh:
            json.dump(ckpt, fh)
        panggilan = []

        def eksekutor(n):
            panggilan.append(n)
            return TEKS

        hasil = PB.jalankan_semua_bab([1, 2, 3, 4], eksekutor,
                                      folder_checkpoint=tmp,
                                      tidur=PerekamTidur())
        cek('resume-checkpoint-lewati-1-2',
            panggilan == [3, 4] and hasil == {3: TEKS, 4: TEKS},
            'panggilan=%r hasil=%r' % (panggilan, sorted(hasil)))


def test_gagal_total_bersih():
    tidur = PerekamTidur()
    panggilan = {'n': 0}

    def eksekutor_hitung(n):
        panggilan['n'] += 1
        raise RuntimeError('provider kosong terus')

    try:
        PB.jalankan_bab_dengan_retry(1, eksekutor_hitung, tidur=tidur)
        ok = False
        info = 'tidak raise'
    except PB.BabGagal as e:
        ok = (panggilan['n'] == 4 and tidur.jeda == [5, 15, 30]
              and isinstance(e, RuntimeError)
              and '4 percobaan' in str(e))
        info = 'panggilan=%r jeda=%r pesan=%s' % (panggilan['n'], tidur.jeda, e)
    except Exception as e:
        ok = False
        info = 'tipe salah: %s: %s' % (type(e).__name__, e)
    cek('gagal-total-bersih-babgagal', ok, info)

    # Varian None terus-menerus juga harus berakhir BabGagal, bukan crash.
    def eksekutor_none_terus(n):
        return None

    try:
        PB.jalankan_bab_dengan_retry(1, eksekutor_none_terus,
                                     tidur=PerekamTidur())
        ok_none = False
        info_none = 'tidak raise'
    except PB.BabGagal:
        ok_none = True
        info_none = ''
    except Exception as e:
        ok_none = False
        info_none = 'tipe salah: %s' % type(e).__name__
    cek('gagal-total-none-jadi-babgagal', ok_none, info_none)


def test_penjaga_split_dan_checkpoint_rusak():
    cek('hitung-kata-aman-none-0', PB.hitung_kata_aman(None) == 0, '')
    cek('hitung-kata-aman-teks',
        PB.hitung_kata_aman('satu dua tiga') == 3, '')
    try:
        PB.periksa_teks_bab(1, None)
        cek('periksa-none-raise', False, 'tidak raise')
    except PB.BabGagal:
        cek('periksa-none-raise', True, '')
    except Exception as e:
        cek('periksa-none-raise', False, 'tipe salah: %s' % type(e).__name__)
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, 'checkpoint.json'), 'w',
                  encoding='utf-8') as fh:
            fh.write('{bukan json rusak')
        cek('checkpoint-rusak-tidak-crash',
            PB.baca_checkpoint_selesai(tmp) == set(), '')
        cek('checkpoint-hilang-set-kosong',
            PB.baca_checkpoint_selesai(os.path.join(tmp, 'tidak-ada')) == set(),
            '')
    cek('konstanta-backoff',
        PB.RETRY_BAB_BACKOFF_DETIK == (5, 15, 30)
        and PB.RETRY_BAB_ULANG_MAKS == 3
        and PB.RETRY_BAB_PERCOBAAN_MAKS == 4,
        '%r %r %r' % (PB.RETRY_BAB_BACKOFF_DETIK, PB.RETRY_BAB_ULANG_MAKS,
                      PB.RETRY_BAB_PERCOBAAN_MAKS))


if __name__ == '__main__':
    print('Uji retry per bab A1:')
    test_gagal_2x_lalu_berhasil()
    test_none_di_retry_tanpa_crash()
    test_checkpoint_lewati_bab_selesai()
    test_gagal_total_bersih()
    test_penjaga_split_dan_checkpoint_rusak()
    print('LULUS %s, GAGAL %s: %s' % (LULUS, len(GAGAL), GAGAL))
    sys.exit(1 if GAGAL else 0)
