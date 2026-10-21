"""Uji PENANDA PINTU (konteks_revisi) — Opsi 1, 28Sep26.

Tiga arah, SEMUA lewat endpoint NYATA https://eduai.bikinaja.id:

  A1 SEHAT Pintu A : `bab='1.1'` ADA di naskah   → 'sub_bab'
  A2 SEHAT Pintu B : body TANPA `bab`            → 'dokumen'
  A3 DIRUSAK       : `bab='9.99'` TIDAK ADA      → 'dokumen'
                     (jujur: yang dikirim memang naskah utuh, BUKAN
                      'sub_bab' walau klien mengklaim sub-bab)

Tanpa `file_id` (jalur `naskah` langsung) → TIDAK menyentuh berkas produksi.
Tiap panggilan = 1 job AI kecil (potong saldo user uji; isi dulu bila 0).
Jalankan dari container hermes. WAJIB User-Agent Chrome (Cloudflare 1010).

JALANKAN: python3 _sketsa/uji_penanda_pintu.py
"""
from __future__ import annotations

import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = 'UjiBayar123!'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

#  Naskah uji: ≥3 sub-bab supaya `state.petakan()` memakai sub-bab
#  (aturan: len(deteksi_subbab) >= 3, lihat app/state.py:731).
NASKAH = """SKRIPSI

BAB I PENDAHULUAN

1.1 Latar Belakang
Penelitian ini dilatarbelakangi oleh meningkatnya kebutuhan mahasiswa terhadap
bimbingan penulisan skripsi yang cepat dan terukur di era digital sekarang.

1.2 Rumusan Masalah
Berdasarkan latar belakang di atas, rumusan masalah dalam penelitian ini adalah
bagaimana pengaruh kualitas layanan terhadap kepuasan mahasiswa.

1.3 Tujuan Penelitian
Penelitian ini bertujuan untuk mengukur pengaruh kualitas layanan terhadap
kepuasan mahasiswa penulis skripsi.

BAB II KAJIAN PUSTAKA

2.1 Teori Kualitas Layanan
Kualitas layanan menurut Parasuraman didefinisikan sebagai kesesuaian antara
ekspektasi dan persepsi pelanggan terhadap jasa yang diterima.

2.2 Teori Kepuasan Pelanggan
Kepuasan pelanggan adalah kondisi perasaan pelanggan setelah membandingkan
kinerja jasa yang diterima dengan ekspektasinya.
"""

JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))

LULUS = 0
GAGAL = 0


def cek(nama: str, sukses: bool, ket: str = '') -> None:
    global LULUS, GAGAL
    if sukses:
        LULUS += 1
        print(f'  ✅ {nama}  {ket}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}  {ket}')


def kirim(path: str, data: dict | None = None, timeout: int = 120):
    body = None
    headers = {'User-Agent': UA}
    if data is not None:
        body = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + path, data=body, headers=headers,
                                 method='POST' if data is not None else 'GET')
    try:
        with OPENER.open(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def login() -> bool:
    data = urllib.parse.urlencode({'email': EMAIL, 'password': SANDI}).encode()
    req = urllib.request.Request(
        BASE + '/masuk', data=data,
        headers={'User-Agent': UA,
                 'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with OPENER.open(req, timeout=60) as r:
            r.read()
    except urllib.error.HTTPError as e:
        e.read()
    st, isi = kirim('/api/ai/v1/kuota')
    return st == 200


def tembak(nama: str, body: dict, harapkan: str, jeda: float = 15.0) -> None:
    st, isi = kirim('/api/ai/v1/revisi', body, timeout=180)
    j: dict = {}
    try:
        j = json.loads(isi)
    except Exception:                                          # noqa: BLE001
        pass
    #  Balasan titip latar belakang = dict datar; galat = {detail: {...}}
    if isinstance(j.get('detail'), dict):
        j = j['detail']
    jalur = j.get('konteks_revisi')
    print(f'  → {nama}: HTTP {st} · konteks_revisi={jalur!r} · '
          f'bab={body.get("bab")!r} · bagian={j.get("bagian")} · '
          f'kode={j.get("kode")!r}')
    if st == 402:
        print('    ⚠️ 402 KUOTA_HABIS — isi saldo user uji dulu: '
              'docker cp _sketsa/isi_saldo_uji6.py eduai-app:/tmp/ && '
              'docker exec eduai-app python3 /tmp/isi_saldo_uji6.py')
    cek(nama, st == 200 and jalur == harapkan,
        f'harap {harapkan!r} dapat {jalur!r} (HTTP {st})')
    time.sleep(jeda)   # jaga jendela rate-limit 6 req/menit/user


def main() -> int:
    print(f'── PENANDA PINTU ({BASE}) ──')
    if not login():
        print('  ❌ GAGAL login (cek sandi user uji / server)')
        return 1

    tembak('A1 sehat Pintu A (bab=1.1 ada) → sub_bab',
           {'naskah': NASKAH, 'komentar': ['Perjelas kalimat pertama.'],
            'bab': '1.1'}, 'sub_bab')

    tembak('A2 sehat Pintu B (tanpa bab) → dokumen',
           {'naskah': NASKAH, 'komentar': ['Perjelas kalimat pertama.']},
           'dokumen')

    tembak('A3 DIRUSAK (bab=9.99 tidak ada) → dokumen (jujur)',
           {'naskah': NASKAH, 'komentar': ['Perjelas kalimat pertama.'],
            'bab': '9.99'}, 'dokumen', jeda=0.0)

    print(f'\nHASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
