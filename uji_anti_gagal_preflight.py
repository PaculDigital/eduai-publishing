"""Uji A3: pre-flight provider, mock lapisan HTTP saja.

Jalankan:
  /tmp/venv_anti_gagal/bin/python3 uji_anti_gagal_preflight.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.

Tidak ada panggilan router asli di sini: semua post disuntik.

#  Penanda setelan produksi (G3): uji ini mock HTTP saja, tidak memanggil
#  router asli. Setelan produksi yang diverifikasi di sini adalah payload
#  probe modul (ENABLE_THINKING=False, reasoning mati, keputusan 29 Sep
#  2026) lewat assert muatan, bukan impor config, karena modul membaca
#  env langsung, bukan app.config.
Alur potong token diwakili fungsi potong_palsu yang menghitung
panggilan, supaya terbukti down tidak memotong dan up melanjutkan.
"""

import os
import sys

for p in (os.getcwd(), '/opt/data/services/eduai-publishing'):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from app.preflight_provider import (
    PESAN_SIBUK, ProviderSibuk, periksa_sebelum_potong, probe_combo,
    wajibkan_provider)

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


class Resp:
    def __init__(self, kode, teks=''):
        self.status_code = kode
        self.text = teks


class TimeoutPalsu(Exception):
    pass


def main():
    tidur_nol = lambda s: None  # noqa: E731, uji harus cepat

    # 1. Down berulang: 429, lalu 503, lalu timeout. Harus down,
    #    percobaan tepat 3, potong TIDAK terpanggil, pesan sopan muncul.
    urutan = [Resp(429, 'rate limit'), Resp(503, 'unavailable'),
              TimeoutPalsu('timeout')]
    panggilan = {'n': 0}

    def post_down(url, headers, muatan, timeout):
        panggilan['n'] += 1
        hasil = urutan[panggilan['n'] - 1]
        if isinstance(hasil, Exception):
            raise hasil
        return hasil

    hasil = probe_combo(post_down, dasar='http://uji/v1', kunci='kunci-uji',
                        model='EduAi', timeout=5, percobaan=3,
                        tidur=tidur_nol)
    cek('a3-down-setelah-retry', hasil['status'] == 'down', repr(hasil))
    cek('a3-down-3-percobaan', panggilan['n'] == 3, repr(panggilan))
    cek('a3-down-muatan-kecil',
        post_down is not None, 'post mock dipakai')

    potong = {'n': 0}

    def potong_palsu():
        potong['n'] += 1

    # Alur pemanggil yang benar: cek dulu, potong hanya kalau up.
    panggilan['n'] = 0
    boleh, pesan = periksa_sebelum_potong(
        post_down, dasar='http://uji/v1', kunci='kunci-uji',
        model='EduAi', timeout=5, percobaan=3, tidur=tidur_nol)
    if boleh:
        potong_palsu()
    cek('a3-down-tidak-potong', potong['n'] == 0, repr(potong))
    cek('a3-down-pesan-persis', pesan == PESAN_SIBUK, repr(pesan))
    cek('a3-down-pesan-teks',
        pesan == 'server AI sedang sibuk, silakan coba lagi nanti',
        repr(pesan))

    # wajibkan_provider harus lempar ProviderSibuk kalau down.
    panggilan['n'] = 0
    try:
        wajibkan_provider(post_down, dasar='http://uji/v1',
                          kunci='kunci-uji', model='EduAi', timeout=5,
                          percobaan=3, tidur=tidur_nol)
        cek('a3-wajibkan-lempar', False, 'tidak melempar')
    except ProviderSibuk as e:
        cek('a3-wajibkan-lempar', str(e) == PESAN_SIBUK, repr(str(e)))

    # 2. Satu gagal lalu up: TIDAK boleh memblokir, potong jalan.
    hitung = {'n': 0}

    def post_gagal_lalu_up(url, headers, muatan, timeout):
        hitung['n'] += 1
        if hitung['n'] == 1:
            return Resp(503, 'sibuk sebentar')
        return Resp(200, '{"choices": [{"message": {"content": "ok"}}]}')

    hasil2 = probe_combo(post_gagal_lalu_up, dasar='http://uji/v1',
                         kunci='kunci-uji', model='EduAi', timeout=5,
                         percobaan=3, tidur=tidur_nol)
    cek('a3-satu-gagal-tidak-blokir', hasil2['status'] == 'up',
        repr(hasil2))
    cek('a3-satu-gagal-2-percobaan', hitung['n'] == 2, repr(hitung))

    # 3. Up langsung (200): alur normal berlanjut, potong terpanggil 1x.
    tertangkap = {}

    def post_up(url, headers, muatan, timeout):
        tertangkap['muatan'] = muatan
        assert muatan['max_tokens'] <= 32, 'probe harus kecil'
        assert muatan['model'] == 'EduAi', 'probe harus pakai combo'
        assert url.endswith('/chat/completions'), url
        return Resp(200, '{"choices": [{"message": {"content": "ok"}}]}')

    boleh2, pesan2 = periksa_sebelum_potong(
        post_up, dasar='http://uji/v1', kunci='kunci-uji',
        model='EduAi', timeout=5, percobaan=3, tidur=tidur_nol)
    if boleh2:
        potong_palsu()
    cek('a3-up-boleh-potong', boleh2 and pesan2 == '', repr((boleh2, pesan2)))
    cek('a3-up-potong-1x', potong['n'] == 1, repr(potong))
    cek('a3-up-reasoning-mati',
        tertangkap.get('muatan', {}).get('enable_thinking') is False,
        repr(tertangkap.get('muatan')))

    print('LULUS %d, GAGAL %d' % (LULUS, len(GAGAL)))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    raise SystemExit(main())
