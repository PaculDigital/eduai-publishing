"""Cek konsistensi antar bab (19 Nov 2026, Gas Boss).

Menilai apakah rumusan masalah, tujuan, hipotesis, metode, hasil, dan
kesimpulan nyambung satu sama lain. GRATIS untuk mahasiswa (Boss yang
tanggung biayanya, dari saldo Apinex, sama seperti Jev/Hakim).

BEDA dengan app/konsistensi.py (Fase 5, penjaga revisi AI tetap nyambung
dengan Research Brief): modul ini menilai rantai antar bab naskah
skripsi, memakai LLM sekali untuk 5 sambungan.

MURNI (stdlib + json saja, tanpa DB, tanpa jaringan) supaya gampang
diuji. Pemanggil yang memanggil LLM (`_panggil_router`) dan yang
menyimpan hasil ke Setelan.

Alur:
  1. `ekstrak_bagian(peta_json)`: 6 pernyataan dari peta Jev
     (deterministik, tanpa LLM).
  2. `susun_prompt(bagian)`: satu prompt untuk 5 sambungan.
  3. LLM menjawab JSON: tiap sambungan `nyambung` / `putus` / `ragu`
     + satu kalimat alasan.
  4. `urai_jawaban(teks)`: parse jawaban jadi 5 vonis.
  5. `ragu` TIDAK divonis: tampil "Perlu diperiksa", mahasiswa cek ke
     pembimbing. Mesin tidak menghalangi dan tidak berpura-pura tahu.
"""
from __future__ import annotations

import json
import re

# 5 sambungan yang dinilai (dari, ke, label tampil).
SAMBUNGAN = [
    ('masalah', 'tujuan', 'Masalah ke Tujuan'),
    ('tujuan', 'hipotesis', 'Tujuan ke Hipotesis'),
    ('hipotesis', 'metode', 'Hipotesis ke Metode'),
    ('metode', 'hasil', 'Metode ke Hasil'),
    ('hasil', 'kesimpulan', 'Hasil ke Kesimpulan'),
]

# Judul subbab yang dicari tiap bagian (dinormalisasi, tanpa nomor).
# 'metode' mengambil desain + analisis + regresi + uji hipotesis
# supaya LLM tahu teknik ujinya, bukan cuma pendekatannya. 'hasil'
# mengambil analisis + uji hipotesis + pembahasan 'Pengaruh...' (di
# sanalah kesimpulan uji ditulis), karena subbab 'Hasil Penelitian'
# sering hanya wadah tanpa paragraf langsung.
BAGIAN_POLAA = {
    'masalah': ['rumusan masalah', 'pertanyaan penelitian'],
    'tujuan': ['tujuan penelitian'],
    'hipotesis': ['hipotesis'],
    'metode': ['jenis dan desain penelitian', 'desain penelitian',
               'metode analisis', 'analisis regresi', 'uji hipotesis'],
    'hasil': ['hasil penelitian', 'hasil analisis data', 'uji hipotesis',
              'pengaruh'],
    'kesimpulan': ['kesimpulan'],
}

# Bab yang diharapkan tiap bagian (dipakai membuang gema dari Bab I
# Sistematika Penulisan yang menyebut bab lain sebagai paragraf).
BAGIAN_BAB = {
    'masalah': 1, 'tujuan': 1, 'hipotesis': 2,
    'metode': 3, 'hasil': 4, 'kesimpulan': 5,
}

MAKS_KARAKTER_BAGIAN = 4000

# Maksimal subbab yang digabung per bagian (subbab wadah tanpa paragraf
# langsung dilewati, jadi 'hasil' butuh 6: analisis + uji t + uji F +
# 3 pembahasan 'Pengaruh...').
MAKS_SUBBAB_PER_BAGIAN = 6
MAKS_KARAKTER_GABUNG = 10000

VONIS_SAH = ('nyambung', 'putus', 'ragu')


def _normal(teks: str) -> str:
    """Judul dinormalisasi: kecil, spasi tunggal, tanpa nomor seksi."""
    s = ' '.join(str(teks or '').split()).strip().lower()
    s = re.sub(r'^\d+(\.\d+)*\s*', '', s)
    s = re.sub(r'^bab\s+(?:[ivx]+|\d+)[\s.]*', '', s)
    return s.strip()


def _nomor_bab_telanjang(teks: str) -> int | None:
    """Angka bab dari penanda telanjang ('BAB II') atau None."""
    romawi = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
    s = ' '.join(str(teks or '').split()).strip()
    m = re.fullmatch(r'BAB\s+([IVX]+|\d+)', s, re.IGNORECASE)
    if not m:
        return None
    t = m.group(1).upper()
    if t in romawi:
        return romawi[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def _nomor_dari_judul_bab(teks: str) -> int | None:
    """Angka bab dari judul berlabel ('BAB II TINJAUAN PUSTAKA')."""
    romawi = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
    s = ' '.join(str(teks or '').split())
    m = re.match(r'^\s*BAB\s+([IVX]+|\d+)\b', s, re.IGNORECASE)
    if not m:
        return None
    t = m.group(1).upper()
    if t in romawi:
        return romawi[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def ekstrak_bagian(peta_json) -> dict:
    """Ekstrak 6 pernyataan dari peta Jev (deterministik).

    Tiap bagian: cari subbab pertama yang judulnya cocok pola DAN
    berada di bab yang diharapkan, lalu ambil paragraf di bawahnya
    sampai subbab/bab berikut (maks 1500 karakter). Bagian yang tidak
    ketemu berisi '' (sambungan yang melibatkannya dinilai 'ragu').
    Kembalikan dict {nama: teks}.
    """
    keluar = {nama: '' for nama in BAGIAN_POLAA}
    try:
        peta = json.loads(peta_json) if isinstance(peta_json, str) \
            else (peta_json or {})
    except Exception:                                       # noqa: BLE001
        return keluar
    surveyor = peta.get('peta_surveyor') or {}
    baris = [str(x) for x in (surveyor.get('baris') or [])]
    label = surveyor.get('label') or {}
    # Bab tiap baris. HANYA penanda telanjang ('BAB II') dan baris
    # berlabel 'bab' yang mengubah bab: baris Sistematika Penulisan di
    # Bab I menyebut 'BAB III METODE PENELITIAN' sebagai teks biasa dan
    # TIDAK boleh menggeser bab.
    bab_baris: list[int | None] = []
    bab_kini: int | None = None
    for i, teks in enumerate(baris):
        s = ' '.join(teks.split()).strip()
        n = _nomor_bab_telanjang(s)
        if n is None and (label.get(str(i)) or label.get(i) or '') == 'bab':
            n = _nomor_dari_judul_bab(s)
        if n is not None:
            bab_kini = n
        bab_baris.append(bab_kini)
    # Tiap bagian: kumpulkan subbab yang cocok di bab yang benar, lewati
    # subbab wadah tanpa paragraf langsung, gabung sampai 3 subbab.
    for nama, pola in BAGIAN_POLAA.items():
        bab_harap = BAGIAN_BAB[nama]
        potong = []
        for i, teks in enumerate(baris):
            lab = label.get(str(i)) or label.get(i) or ''
            if lab != 'subbab':
                continue
            if bab_baris[i] is not None and bab_baris[i] != bab_harap:
                continue
            judul = _normal(teks)
            if not any(p in judul for p in pola):
                continue
            isi = []
            for j in range(i + 1, len(baris)):
                lab2 = label.get(str(j)) or label.get(j) or ''
                if lab2 in ('subbab', 'bab'):
                    break
                if lab2 in ('paragraf', 'biasa'):
                    t = ' '.join(str(baris[j]).split()).strip()
                    if t:
                        isi.append(t)
                if sum(len(x) for x in isi) >= MAKS_KARAKTER_BAGIAN:
                    break
            teks_isi = ' '.join(isi)
            if teks_isi:
                potong.append(teks_isi[:MAKS_KARAKTER_BAGIAN])
            if len(potong) >= MAKS_SUBBAB_PER_BAGIAN:
                break
        keluar[nama] = '\n'.join(potong)[:MAKS_KARAKTER_GABUNG]
    return keluar


def susun_prompt(bagian: dict) -> str:
    """Satu prompt untuk 5 sambungan (Bahasa Indonesia, tanpa jargon)."""
    nama_tampil = {
        'masalah': 'Rumusan Masalah',
        'tujuan': 'Tujuan Penelitian',
        'hipotesis': 'Hipotesis',
        'metode': 'Metode',
        'hasil': 'Hasil Penelitian',
        'kesimpulan': 'Kesimpulan',
    }
    isi = []
    for nama in ('masalah', 'tujuan', 'hipotesis', 'metode', 'hasil',
                 'kesimpulan'):
        teks = (bagian.get(nama) or '').strip()
        isi.append(f"## {nama_tampil[nama]}\n"
                   f"{teks if teks else '(tidak ditemukan di naskah)'}")
    badan = '\n\n'.join(isi)
    return (
        "Kamu penilai skripsi. Nilai apakah 5 sambungan di bawah ini "
        "nyambung atau putus. Jawab HANYA dengan JSON, tanpa teks lain.\n\n"
        f"{badan}\n\n"
        "Nilai tiap sambungan:\n"
        "1. masalah_tujuan: apakah Tujuan menjawab Rumusan Masalah?\n"
        "2. tujuan_hipotesis: apakah Hipotesis menguji Tujuan?\n"
        "3. hipotesis_metode: apakah Metode menguji Hipotesis?\n"
        "4. metode_hasil: apakah Hasil menjawab yang diuji Metode?\n"
        "5. hasil_kesimpulan: apakah Kesimpulan mengikuti Hasil?\n\n"
        "Format jawaban (JSON saja):\n"
        '{"sambungan": ['
        '{"nama": "masalah_tujuan", "vonis": "nyambung", "alasan": "..."}, '
        '{"nama": "tujuan_hipotesis", "vonis": "putus", "alasan": "..."}, '
        "...]}\n\n"
        'Vonis hanya boleh "nyambung", "putus", atau "ragu". '
        '"ragu" bila bukti di naskah tidak cukup untuk memutuskan. '
        'Alasan SATU kalimat Bahasa Indonesia, sebut kalimat yang tidak '
        'nyambung bila vonis "putus". Bila satu bagian "(tidak ditemukan '
        'di naskah)", sambungan yang melibatkannya WAJIB "ragu".'
    )


def urai_jawaban(teks: str) -> list[dict]:
    """Parse jawaban LLM jadi 5 vonis (gagal parse -> semua 'ragu').

    Tiap vonis: {'nama', 'label', 'vonis', 'alasan'}. 'nama' kunci
    mesin (masalah_tujuan, ...), 'label' nama tampil. Vonis di luar
    tiga yang sah dianggap 'ragu'. Alasan kosong diganti kalimat baku.
    """
    baku = {f'{d}_{k}': 'Belum bisa diputuskan dari naskah.'
            for d, k, _ in SAMBUNGAN}
    hasil: list[dict] = []
    data = None
    try:
        awal = teks.index('{')
        akhir = teks.rindex('}') + 1
        data = json.loads(teks[awal:akhir])
    except Exception:                                       # noqa: BLE001
        data = None
    peta_jawaban = {}
    if isinstance(data, dict):
        for item in (data.get('sambungan') or []):
            if not isinstance(item, dict):
                continue
            nama = str(item.get('nama') or '').strip()
            vonis = str(item.get('vonis') or '').strip().lower()
            if vonis not in VONIS_SAH:
                vonis = 'ragu'
            alasan = ' '.join(str(item.get('alasan') or '').split())
            peta_jawaban[nama] = {'vonis': vonis, 'alasan': alasan}
    for dari, ke, label in SAMBUNGAN:
        nama = f'{dari}_{ke}'
        vonis = peta_jawaban.get(nama, {}).get('vonis', 'ragu')
        alasan = peta_jawaban.get(nama, {}).get('alasan', '') or baku[nama]
        hasil.append({'nama': nama, 'label': label,
                      'vonis': vonis, 'alasan': alasan})
    return hasil


def langkah_berikut(vonis: list[dict]) -> str | None:
    """Satu baris 'Langkah berikut' untuk ceklist konsistensi.

    - Ada yang putus -> perbaiki sambungan yang putus (sebut yang
      pertama).
    - Ada yang ragu -> cek ke pembimbing.
    - Semua nyambung -> None (baris tidak tampil).
    """
    for v in vonis or []:
        if v.get('vonis') == 'putus':
            return f"Perbaiki sambungan {v.get('label', '')}."
    for v in vonis or []:
        if v.get('vonis') == 'ragu':
            return 'Cek sambungan yang belum bisa diputuskan ke pembimbing.'
    return None
