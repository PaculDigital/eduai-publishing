"""Pre-flight provider sebelum potong token (A3, 30 Okt 2026).

Masalah yang diatasi: order buku memotong token di dalam susun()
(app/penyusunan_buku.py, lewat on_mulai) sesudah validasi outline,
lalu bab pertama memanggil combo EduAi. Kalau combo sedang down
(429, 503, timeout, atau 9router tidak menjawab), token sudah
terpotong padahal buku belum tentu jadi.

Aturan modul ini:
  1. Probe memakai jalur HTTP yang SAMA dengan pipeline teks, yaitu
     POST {ROUTER_BASE}/chat/completions dengan header Bearer yang
     sama dan model combo yang sama (app/ai.py, _panggil_9router).
     Bedanya hanya muatan: max_tokens kecil dan prompt pendek,
     jadi probe murah dan cepat.
  2. Satu gagal TIDAK memblokir. Probe mengulang sampai percobaan
     habis dengan backoff. Baru down sesudah semua percobaan gagal
     yang boleh menunda order.
  3. Probe TIDAK PERNAH memotong token dan TIDAK PERNAH memanggil
     kuota. Ia hanya mengembalikan status. Keputusan menunda ada
     di pemanggil.
  4. Probe TIDAK PERNAH melempar karena gagal jaringan. Kegagalan
     diubah jadi status down dengan alasan, supaya pemanggil bisa
     memilih menunda sopan, bukan crash.

Penerapan di pemanggil (lihat laporan G2/A3 untuk cuplikan lengkap):
  hasil = probe_combo()
  kalau hasil['status'] != 'up', pemanggil menunda SOPAN tanpa
  potong token dengan pesan PESAN_SIBUK, bukan halaman gagal.

Catatan: susun() itu sinkron, jadi probe ini sinkron (httpx.Client).
Pipeline teks memakai httpx.AsyncClient, tapi URL, header, model,
dan bentuk muatan sama, jadi probe menguji jalur yang sama.
"""

import os
import time

import httpx

PESAN_SIBUK = "server AI sedang sibuk, silakan coba lagi nanti"

_TIMEOUT_DEFAULT = 10.0
_PERCOBAAN_DEFAULT = 3


class ProviderSibuk(Exception):
    """Provider down sesudah retry. Pesan user-facing ada di PESAN_SIBUK."""

    def __init__(self, pesan: str = PESAN_SIBUK):
        super().__init__(pesan)
        self.pesan = pesan


def _angka_env(nama: str, default: float) -> float:
    try:
        return float(os.getenv(nama, '') or default)
    except (TypeError, ValueError):
        return default


def _konfigurasi(dasar=None, kunci=None, model=None):
    """Ambil konfigurasi dari argumen, kalau kosong dari environment.

    Default sama dengan app/config.py: dasar 9router lokal dan model
    combo EduAi. Kunci dibaca dari EDUAI_ROUTER_KEY, tidak di-hardcode.
    """
    if dasar is None:
        dasar = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
    if kunci is None:
        kunci = os.getenv('EDUAI_ROUTER_KEY', '')
    if model is None:
        model = os.getenv('EDUAI_AI_MODEL', 'EduAi')
    return str(dasar).rstrip('/'), str(kunci or ''), str(model or 'EduAi')


def _post_httpx(url, headers, muatan, timeout):
    """Post sinkron bawaan, dipakai kalau pemanggil tidak menyuntik post."""
    with httpx.Client(timeout=timeout) as klien:
        return klien.post(url, headers=headers, json=muatan)


def probe_combo(post=None, *, dasar=None, kunci=None, model=None,
                timeout=None, percobaan=None, backoff_dasar=1.0,
                tidur=time.sleep) -> dict:
    """Probe combo EduAi. Kembalikan dict status up atau down.

    post: callable opsional untuk uji, signature
      post(url, headers, muatan, timeout) dan kembalikan objek dengan
      atribut status_code dan text. Kalau None, pakai httpx.Client.
    timeout: detik per percobaan, default 10 atau EDUAI_PREFLIGHT_TIMEOUT.
    percobaan: jumlah percobaan, default 3 atau EDUAI_PREFLIGHT_PERCOBAAN.
    backoff_dasar: jeda sebelum percobaan ulang = backoff_dasar * nomor
      percobaan yang baru gagal (1x, 2x, dan seterusnya). Uji menyuntik
      tidur=lambda s: None supaya cepat.
    Hasil: {'status': 'up' atau 'down', 'alasan': str,
            'percobaan': int, 'http': int atau None}.
    Up hanya kalau HTTP 200 dan isi respons tidak kosong.
    """
    if timeout is None:
        timeout = _angka_env('EDUAI_PREFLIGHT_TIMEOUT', _TIMEOUT_DEFAULT)
    if percobaan is None:
        percobaan = int(_angka_env('EDUAI_PREFLIGHT_PERCOBAAN',
                                   _PERCOBAAN_DEFAULT))
    percobaan = max(1, int(percobaan))
    dasar_fix, kunci_fix, model_fix = _konfigurasi(dasar, kunci, model)
    if not kunci_fix:
        return {'status': 'down', 'alasan': 'kunci router belum diset',
                'percobaan': 0, 'http': None}
    url = dasar_fix + '/chat/completions'
    headers = {'Authorization': 'Bearer ' + kunci_fix}
    muatan = {
        'model': model_fix,
        'messages': [
            {'role': 'system', 'content': 'Jawab singkat.'},
            {'role': 'user', 'content': 'ping'},
        ],
        'max_tokens': 16,
        'temperature': 0.2,
        'enable_thinking': False,
    }
    kirim = post or _post_httpx
    alasan = ''
    http_kode = None
    for upaya in range(1, percobaan + 1):
        try:
            resp = kirim(url, headers, muatan, timeout)
            http_kode = int(getattr(resp, 'status_code', 0) or 0)
            isi = getattr(resp, 'text', '') or ''
            if http_kode == 200 and isi.strip():
                return {'status': 'up', 'alasan': '',
                        'percobaan': upaya, 'http': 200}
            alasan = 'HTTP %s' % http_kode
        except Exception as e:  # noqa: BLE001, probe tidak boleh melempar
            http_kode = None
            alasan = '%s: %s' % (type(e).__name__, str(e)[:200])
        if upaya < percobaan:
            tidur(backoff_dasar * upaya)
    return {'status': 'down', 'alasan': alasan,
            'percobaan': percobaan, 'http': http_kode}


def periksa_sebelum_potong(*args, **kwargs) -> tuple[bool, str]:
    """Pembungkus pemanggil: (boleh_potong, pesan_sopan).

    Boleh potong True dan pesan kosong kalau probe up. Kalau down,
    boleh potong False dan pesan persis PESAN_SIBUK, untuk ditampilkan
    sebagai penundaan sopan tanpa potong token, bukan halaman gagal.
    """
    hasil = probe_combo(*args, **kwargs)
    if hasil['status'] == 'up':
        return True, ''
    return False, PESAN_SIBUK


def wajibkan_provider(*args, **kwargs) -> None:
    """Probe lalu lempar ProviderSibuk kalau down sesudah retry.

    Dipakai di titik potong token yang bisa menangkap ProviderSibuk
    dan mengubahnya jadi penundaan sopan. Jangan dipakai di titik
    yang mengubah setiap exception jadi halaman gagal tanpa filter.
    """
    hasil = probe_combo(*args, **kwargs)
    if hasil['status'] != 'up':
        raise ProviderSibuk()
