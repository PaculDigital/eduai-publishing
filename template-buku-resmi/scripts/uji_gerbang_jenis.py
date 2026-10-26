#!/usr/bin/env python3
"""UJI BERGIGI gerbang jenis (Gas Boss 26 Okt 2026).

Prinsip uji bergigi: setiap gerbang WAJIB dibuktikan BISA gagal.
Uji ini memakai spec sintetis kecil (bukan contoh fase1-ssot, supaya
uji jalan di cabang mana pun), lalu menegaskan exit code gerbang:
  - spec yang unsurnya lengkap untuk jenisnya HARUS lolos (exit 0)
  - spec yang satu unsurnya dicabut HARUS gagal (exit 1)
  - spec tanpa jenis / jenis tidak dikenal HARUS gagal
  - spec salah label HARUS gagal, dan --dugaan HARUS menunjuk jenis
    lain yang lolos penuh

Pakai:  python3 uji_gerbang_jenis.py
EXIT 0 = semua kasus uji sesuai harapan, EXIT 1 = ada yang meleset.
"""

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GERBANG = HERE / 'periksa_jenis_buku.py'


def dasar(jenis, bab):
    return {
        'jenis': jenis,
        'judul': 'Buku Uji Gerbang Jenis',
        'penulis': 'Penulis Uji',
        'kata_pengantar': ['Kata pengantar uji.'],
        'tentang_penulis': ['Tentang penulis uji.'],
        'daftar_pustaka': ['Penulis, A. (2020). Buku uji. Penerbit Uji.'],
        'bab': bab,
    }


def bab(judul, teks_sub):
    """Satu bab dengan satu sub-bab berisi teks yang diberikan."""
    return {'judul': judul, 'romawi': 'I',
            'sub': [{'judul': 'Sub-bab uji', 'paragraf': [teks_sub]}]}


AJAR = dasar('buku-ajar', [
    bab('Konsep Dasar', 'Tujuan Instruksional Umum (TIU): sesudah bab ini '
        'pembaca mampu menjelaskan konsep. Tujuan Instruksional Khusus '
        '(TIK): pembaca mampu memberi contoh. Latihan 1: kerjakan soal '
        'berikut. Rangkuman: bab ini menegaskan konsep dasar. '
        'Checklist pemahaman bab ini: saya dapat menjelaskan konsep.'),
])

REFERENSI = dasar('buku-referensi', [
    {'judul': 'Peta Teori', 'romawi': 'I',
     'sub': [{'judul': 'Perbandingan Kritis', 'paragraf': [
         'Posisi penulis dalam perdebatan ini jelas: teori A lebih '
         'menjelaskan daripada teori B pada konteks ini.',
         {'tabel': {'judul': 'Tabel 1.1 Perbandingan Teori A dan B',
                    'kolom': ['Teori', 'Fokus'],
                    'baris': [['A', 'Struktur'], ['B', 'Manusia']]}},
     ]}]},
    {'judul': 'Perbandingan Antar Aliran', 'romawi': 'II',
     'sub': [{'judul': 'Tabel Komparasi', 'paragraf': [
         'Posisi penulis: sintesis penulis menengahi dua kutub.',
         {'tabel': {'judul': 'Tabel 2.1 Komparasi Aliran',
                    'kolom': ['Aliran', 'Fokus'],
                    'baris': [['Klasik', 'Aturan']]}},
     ]}]},
])
REFERENSI['indeks_subjek'] = [['Teori organisasi', '12']]
REFERENSI['indeks_nama'] = [['Weber', '12']]

MONOGRAF = dasar('monograf', [
    bab('Pendahuluan', 'Pertanyaan penelitian buku ini: apakah X '
        'berpengaruh pada Y? Latar belakang penelitian ini jelas.'),
    bab('Metode Penelitian', 'Metode penelitian yang dipakai adalah '
        'studi kasus dengan informan terpilih dan analisis tematik.'),
    bab('Hasil dan Pembahasan', 'Kebaruan penelitian ini terletak pada '
        'gabungan dua pendekatan yang belum pernah diuji bersama. '
        'Temuan utama dibahas di sini.'),
    bab('Simpulan', 'Keterbatasan penelitian ini: cakupan wilayah '
        'terbatas, sehingga generalisasi harus hati-hati.'),
])

PANDUAN = dasar('panduan-praktis', [
    bab('Memulai', 'Contoh praktis: ikuti langkah berikut satu per satu '
        'untuk membuat basis data pertama Anda. Cara ini sudah dicoba '
        'pada contoh nyata.'),
])

CHAPTER = {
    'jenis': 'book-chapter',
    'judul': 'Bab Uji',
    'section': [{'judul': 'Pendahuluan',
                 'tujuan': ['Menjelaskan konsep dasar.'],
                 'paragraf': ['Pendahuluan chapter uji.']}],
    'referensi': ['Penulis, A. (2020). Buku uji. Penerbit.'],
    'glosarium': [['Data', 'Fakta yang dikumpulkan.']],
    'cv': {'nama': 'Penulis Uji', 'bio': ['Dosen uji.']},
}


def jalankan(spec, extra=None):
    with tempfile.NamedTemporaryFile('w', suffix='.json',
                                     delete=False, encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False)
        jalan = f.name
    cmd = [sys.executable, str(GERBANG)] + (extra or []) + [jalan]
    r = subprocess.run(cmd, capture_output=True, text=True)
    Path(jalan).unlink(missing_ok=True)
    return r.returncode, r.stdout


KASUS = []


def kasus(nama, spec, harap_lolos, extra=None, harap_dugaan=None):
    KASUS.append((nama, spec, harap_lolos, extra, harap_dugaan))


kasus('ajar lengkap lolos', AJAR, True)
kasus('referensi lengkap lolos', REFERENSI, True)
kasus('monograf lengkap lolos', MONOGRAF, True)
kasus('panduan lengkap lolos', PANDUAN, True)
kasus('chapter lengkap lolos', CHAPTER, True)

_ref_tanpa_indeks = copy.deepcopy(REFERENSI)
del _ref_tanpa_indeks['indeks_subjek']
kasus('referensi tanpa indeks subjek GAGAL', _ref_tanpa_indeks, False)

_ref_tanpa_posisi = copy.deepcopy(REFERENSI)
_ref_tanpa_posisi['bab'][0]['sub'][0]['paragraf'][0] = \
    'Teori A dan teori B sama-sama punya kelebihan.'
_ref_tanpa_posisi['bab'][1]['sub'][0]['paragraf'][0] = \
    'Perbandingan berikut merangkum perbedaan antar aliran.'
kasus('referensi tanpa posisi penulis GAGAL', _ref_tanpa_posisi, False)

_ajar_tanpa_latihan = copy.deepcopy(AJAR)
_ajar_tanpa_latihan['bab'][0]['sub'][0]['paragraf'][0] = \
    _ajar_tanpa_latihan['bab'][0]['sub'][0]['paragraf'][0].replace(
        'Latihan 1: kerjakan soal berikut. ', '')
kasus('ajar tanpa latihan GAGAL', _ajar_tanpa_latihan, False)

_mono_tanpa_batas = copy.deepcopy(MONOGRAF)
_mono_tanpa_batas['bab'][3]['sub'][0]['paragraf'][0] = \
    'Simpulan penelitian ini menegaskan temuan utama.'
kasus('monograf tanpa keterbatasan GAGAL', _mono_tanpa_batas, False)

_mono_tanpa_metode = copy.deepcopy(MONOGRAF)
_mono_tanpa_metode['bab'][1] = bab(
    'Tinjauan Pustaka', 'Teori-teori terdahulu dirangkum di sini.')
kasus('monograf tanpa metode GAGAL', _mono_tanpa_metode, False)

_tanpa_jenis = copy.deepcopy(AJAR)
del _tanpa_jenis['jenis']
kasus('spec tanpa jenis GAGAL', _tanpa_jenis, False)

_tanpa_pustaka = copy.deepcopy(AJAR)
del _tanpa_pustaka['daftar_pustaka']
kasus('ajar tanpa daftar pustaka GAGAL (cek struktur umum)',
      _tanpa_pustaka, False)

_jenis_asing = copy.deepcopy(AJAR)
_jenis_asing['jenis'] = 'buku-misteri'
kasus('jenis tidak dikenal GAGAL', _jenis_asing, False)

_panduan_diklaim_ajar = copy.deepcopy(PANDUAN)
_panduan_diklaim_ajar['jenis'] = 'buku-ajar'
kasus('panduan diklaim buku ajar GAGAL + dugaan panduan',
      _panduan_diklaim_ajar, False,
      extra=['--dugaan'], harap_dugaan='panduan-praktis')

_ajar_diklaim_mono = copy.deepcopy(AJAR)
_ajar_diklaim_mono['jenis'] = 'monograf'
kasus('ajar diklaim monograf GAGAL', _ajar_diklaim_mono, False)


def main():
    gagal_uji = 0
    for nama, spec, harap_lolos, extra, harap_dugaan in KASUS:
        kode, keluar = jalankan(spec, extra)
        lolos = (kode == 0)
        ok = (lolos == harap_lolos)
        if harap_dugaan:
            ok = ok and (f'Diduga jenis sebenarnya: {harap_dugaan}'
                         in keluar)
        print(f'{"PASS" if ok else "FAIL"}  {nama} '
              f'(gerbang exit {kode}, harap {"0" if harap_lolos else "1"})')
        if not ok:
            gagal_uji += 1
            print('  --- keluaran gerbang ---')
            print(keluar)
    print(f'\n{len(KASUS) - gagal_uji}/{len(KASUS)} kasus uji sesuai harapan.')
    return 1 if gagal_uji else 0


if __name__ == '__main__':
    sys.exit(main())
