"""KUNCI LAYANAN — kelola kunci/token layanan luar dari halaman admin.

═══════════ KENAPA ADA ═══════════
Sebelumnya ganti kunci Scopus / OpenAlex / Scite WAJIB lewat `.env` +
deploy (butuh Wulan, butuh restart container). Bos minta bisa sendiri
dari browser (13Okt26: "harusnya di dashboard admin ada manajemen atur
ini semua... jadi saya bisa masukkin yang baru dan tinggal klik sudah
tersambung").

═══════════ POLA (MENGIKUTI `setelan.py` YANG SUDAH ADA) ═══════════
Urutan prioritas: DB (tabel `setelan`) > .env > default.
NOL tabel baru — menumpang tabel `setelan` + `setelan_riwayat` yang
sudah dipakai halaman /pengaturan. Sesuai aturan Bos: "jangan buat
baru, optimal kan yang sudah ada".

═══════════ 2 JENIS KUNCI (BEDA SIFAT — WAJIB DIBEDAKAN DI LAYAR) ═══════════
1. KUNCI MATI (Scopus, OpenAlex) — tempel sekali, jalan selamanya.
2. TOKEN HIDUP (Scite) — berlaku 15 menit, disegarkan otomatis lewat
   refresh_token. Ganti akun = login ulang (perlu bantuan terowongan).

═══════════ NILAI SENSITIF ═══════════
Nilai kunci DISIMPAN di tabel `setelan` (kolom `nilai` panjang 120 —
cukup untuk Scite 507 kar? TIDAK). ⇒ kunci panjang disimpan di tabel
`setelan` dengan kolom nilai yang diperlebar lewat migrasi, ATAU di
berkas `data/kunci-layanan.json` (bind-mount, bukan image).

PILIHAN: berkas `data/kunci-layanan.json` — sebab:
(a) tidak menyentuh skema tabel lama (aman untuk 26 gerbang),
(b) `data/` = bind-mount ⇒ bertahan antar-restart,
(c) tidak ikut ke image ⇒ kunci tidak bocor ke build.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

#  ── di mana kunci disimpan (bind-mount, bukan image) ──
DIR_DATA = Path(os.getenv('EDUAI_DATA_DIR') or '/app/data')
#  ⚠️ `EDUAI_KUNCI_DIR`: HANYA untuk GERBANG UJI. Berkas ini bind-mount
#     ke produksi ⇒ gerbang yang menyimpan kunci palsu akan MENIMPA
#     kunci asli (kunci admin menang atas `.env`) ⇒ Scopus 401.
#     Terukur 13Okt26: gerbang meninggalkan `"scopus": "abc"` di produksi.
BERKAS = (Path(os.getenv('EDUAI_KUNCI_DIR') or DIR_DATA)
          / 'kunci-layanan.json')

#  ── definisi layanan: kunci → keterangan ──
LAYANAN = {
    'scopus': {
        'label': 'Scopus',
        'env': 'EDUAI_SCOPUS_KEY',
        'sifat': 'mati',
        'catatan': 'Kunci mati — tempel sekali, jalan terus.',
        'cara': 'Ambil di dev.elsevier.com → API Key.',
    },
    'openalex': {
        'label': 'OpenAlex',
        'env': 'EDUAI_OPENALEX_KEY',
        'sifat': 'mati',
        'catatan': 'Kunci mati — tempel sekali, jalan terus.',
        'cara': 'Ambil di openalex.org/settings/api.',
    },
    'scite': {
        'label': 'Scite',
        'env': 'EDUAI_SCITE_TOKEN',
        'sifat': 'hidup',
        'catatan': 'Token hidup (15 menit) — disegarkan otomatis.',
        'cara': 'Login akun Scite (tombol Ganti Akun).',
    },
}


def _muat() -> dict:
    """Baca berkas kunci. Rusak/tidak ada → kamus kosong (jangan meledak)."""
    try:
        if BERKAS.exists():
            return json.loads(BERKAS.read_text())
    except Exception as e:                                    # noqa: BLE001
        log.warning('[kunci] berkas rusak, diabaikan: %s', e)
    return {}


def _simpan(isi: dict) -> None:
    BERKAS.parent.mkdir(parents=True, exist_ok=True)
    BERKAS.write_text(json.dumps(isi, indent=1))
    try:
        os.chmod(BERKAS, 0o600)          # hanya pemilik yang bisa baca
    except OSError:
        pass


def ambil(nama: str) -> str:
    """Kunci yang BERLAKU: berkas (DB) → .env → ''. 

    Dipakai mesin pustaka supaya urutan prioritasnya sama dengan
    pola `setelan.py` dan bisa diubah admin tanpa deploy.
    """
    info = LAYANAN.get(nama)
    if not info:
        return ''
    v = str(_muat().get(nama) or '').strip()
    if v:
        return v
    return str(os.getenv(info['env']) or '').strip()


def pasang(nama: str, nilai: str, oleh: str = '') -> tuple[bool, str]:
    """Simpan kunci baru. Kembalikan (berhasil, pesan)."""
    info = LAYANAN.get(nama)
    if not info:
        return False, f'Layanan "{nama}" tidak dikenal.'
    nilai = str(nilai or '').strip()
    if len(nilai) < 8:
        return False, 'Kunci terlalu pendek — periksa lagi (minimal 8 huruf).'
    isi = _muat()
    isi[nama] = nilai
    if oleh:
        isi[nama + '_oleh'] = oleh
    _simpan(isi)
    log.info('[kunci] %s diganti oleh %s (%d karakter)',
             nama, oleh or 'admin', len(nilai))
    return True, f'Kunci {info["label"]} tersimpan.'


def hapus(nama: str) -> tuple[bool, str]:
    """Hapus kunci berkas → kembali ke .env."""
    info = LAYANAN.get(nama)
    if not info:
        return False, f'Layanan "{nama}" tidak dikenal.'
    isi = _muat()
    isi.pop(nama, None)
    isi.pop(nama + '_oleh', None)
    _simpan(isi)
    return True, f'Kunci {info["label"]} dikembalikan ke setelan bawaan.'


def samar(nilai: str) -> str:
    """Samarkan kunci untuk ditampilkan: hanya 6 huruf terakhir.

    JANGAN pernah menampilkan kunci utuh di layar — halaman bisa
    dipotret / dibocorkan.
    """
    if not nilai:
        return ''
    if len(nilai) <= 6:
        return '•' * len(nilai)
    return '•' * 8 + nilai[-6:]


def status(nama: str) -> dict:
    """Ringkas untuk layar: ada/tidak, dari mana, tersamar."""
    info = LAYANAN.get(nama)
    if not info:
        return {}
    nilai = ambil(nama)
    elif_env = str(os.getenv(info['env']) or '').strip()
    if nilai == elif_env and nilai:
        asal = '.env'
    elif nilai:
        asal = 'diatur admin'
    else:
        asal = 'belum ada'
    return {
        'nama': nama,
        'label': info['label'],
        'sifat': info['sifat'],
        'catatan': info['catatan'],
        'cara': info['cara'],
        'ada': bool(nilai),
        'panjang': len(nilai),
        'tersamar': samar(nilai),
        'asal': asal,
        'oleh': str(_muat().get(nama + '_oleh') or ''),
    }


def status_semua() -> list[dict]:
    return [status(k) for k in LAYANAN]
