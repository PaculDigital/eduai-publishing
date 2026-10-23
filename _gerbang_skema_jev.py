#!/usr/bin/env python3
"""GERBANG SKEMA JEV — penjaga supaya 503 SEMU tidak pernah terulang.

AKAR (07 Okt 2026): `criteria` salah bentuk ⇒ HTTP 400 Zod yang DISAMAR
jadi 503 oleh 9router ⇒ Wulan salah menyimpulkan "Jev rusak / skema tertutup".
Bahaya: Jev jadi dihindari, padahal Jev mampu.

GERBANG INI MENJAGA 4 HAL:
  [A] `_periksa_skema()` ADA & MENANGKAP semua bentuk salah
  [B] SEMUA pertanyaan di `satpam.TANYA` & `konversi.PERTANYAAN_PETA` SAH
  [C] `tanya_bebas()` & `tanya_bebas_mutu()` MEMANGGIL pagar itu
  [D] TIDAK ADA komentar/teks sumber yang mengklaim skema tertutup
      (klaim palsu "hanya 3 nama" / "2 tipe" / "Jev tidak stabil")

⚠️ WAJIB BERGIGI: uji ini menyuntikkan skema SALAH ke salinan `_periksa_skema`
   dan MEMBUKTIKAN ia menangkap. Kalau tidak menangkap ⇒ gerbang GAGAL.

WAJIB dijalankan DI DALAM container (docker exec -w /app eduai-app).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import konversi, satpam                                        # noqa: E402

DIR = Path('/app')
HASIL = {'lulus': 0, 'gagal': 0}


def cek(nama: str, syarat: bool, catatan: str = '') -> None:
    if syarat:
        HASIL['lulus'] += 1
        print(f'  ✅ {nama}')
    else:
        HASIL['gagal'] += 1
        print(f'  ❌ {nama}' + (f'  [{catatan}]' if catatan else ''))


def main() -> int:
    print('══ GERBANG SKEMA JEV — cegah 503 semu terulang ══\n')

    #  ── [A] pagar ADA & menangkap SEMUA bentuk salah ──────────────────
    print('[A] `_periksa_skema` ada & menangkap bentuk salah')
    cek('fungsi `_periksa_skema` ADA', hasattr(satpam, '_periksa_skema'))
    if not hasattr(satpam, '_periksa_skema'):
        print('\n(berhenti — pagar belum ada)')
        return 1
    periksa = satpam._periksa_skema

    SALAH = {
        'noul + criteria string': {'x': {'type': 'noul', 'instructions': 'a',
                                         'criteria': 'Ya bila ada.'}},
        'noul + criteria objek': {'x': {'type': 'noul', 'instructions': 'a',
                                        'criteria': {'yes': 'ada'}}},
        'noul + criteria array': {'x': {'type': 'noul', 'instructions': 'a',
                                        'criteria': ['a', 'b']}},
        'choice + criteria array': {'x': {'type': 'choice', 'instructions': 'a',
                                          'criteria': ['a', 'b']}},
        'choice tanpa criteria': {'x': {'type': 'choice', 'instructions': 'a'}},
        'choice + options': {'x': {'type': 'choice', 'instructions': 'a',
                                   'options': ['a', 'b']}},
        'score + criteria objek': {'x': {'type': 'score', 'instructions': 'a',
                                         'criteria': {'0': 'a', '1': 'b'}}},
        'score tanpa criteria': {'x': {'type': 'score', 'instructions': 'a'}},
        'score 1 tingkat': {'x': {'type': 'score', 'instructions': 'a',
                                  'criteria': ['hanya satu']}},
        'score 11 tingkat': {'x': {'type': 'score', 'instructions': 'a',
                                   'criteria': [f't{i}' for i in range(11)]}},
        'tipe karangan (text)': {'x': {'type': 'text', 'instructions': 'a'}},
        'tipe karangan (bool)': {'x': {'type': 'bool', 'instructions': 'a'}},
        'tipe kosong': {'x': {'instructions': 'a'}},
        'questions kosong': {},
    }
    for nama, q in SALAH.items():
        keluhan = periksa(q)
        cek(f'DITOLAK: {nama}', bool(keluhan),
            'seharusnya ditolak tapi LOLOS' if not keluhan else '')

    BENAR = {
        'noul polos': {'x': {'type': 'noul', 'instructions': 'Apakah ada ABSTRAK?'}},
        'choice + criteria objek': {'x': {'type': 'choice', 'instructions': 'Pilih.',
                                          'criteria': {'a': 'Aaa', 'b': 'Bbb'}}},
        'score + criteria 5 tingkat': {'x': {'type': 'score', 'instructions': 'Nilai.',
                                             'criteria': ['a', 'b', 'c', 'd', 'e']}},
        'score 2 tingkat (batas bawah)': {'x': {'type': 'score', 'instructions': 'N.',
                                                'criteria': ['a', 'b']}},
        'score 10 tingkat (batas atas)': {'x': {'type': 'score', 'instructions': 'N.',
                                                'criteria': [f't{i}' for i in range(10)]}},
        'campur 3 tipe': {
            'a': {'type': 'noul', 'instructions': 'x?'},
            'b': {'type': 'choice', 'instructions': 'y?', 'criteria': {'1': 'satu'}},
            'c': {'type': 'score', 'instructions': 'z?', 'criteria': ['a', 'b', 'c']}},
    }
    for nama, q in BENAR.items():
        keluhan = periksa(q)
        cek(f'DITERIMA: {nama}', not keluhan,
            f'ditolak palsu: {keluhan}' if keluhan else '')

    #  ── [B] pertanyaan yang SUNGGUH dipakai HARUS SAH ─────────────────
    print('\n[B] pertanyaan yang sungguh dipakai SAH (tidak akan 503)')
    k = periksa(satpam.TANYA)
    cek(f'satpam.TANYA ({len(satpam.TANYA)} pertanyaan)', not k, str(k))
    k = periksa(konversi.PERTANYAAN_PETA)
    cek(f'konversi.PERTANYAAN_PETA ({len(konversi.PERTANYAAN_PETA)})', not k, str(k))
    for nama in ('ELEMEN_MUTU', 'BAGIAN_WAJIB_JEV'):
        q = getattr(konversi, nama, None)
        cek(f'konversi.{nama} ADA', q is not None)
        if q:
            kk = periksa(q)
            cek(f'konversi.{nama} ({len(q)} pertanyaan) SAH', not kk, str(kk))

    #  ── [C] pagar DIPANGGIL di jalur tanya ────────────────────────────
    #  ⚠️ DIPERBARUI 12Okt26: pagar skema sudah DIPINDAH ke JALAN TOL
    #     (`app/jev.py:periksa_skema` + `tanya()` yang melempar `SkemaSalah`).
    #     `satpam.tanya_bebas_mutu()` sekarang hanya MEMANGGL `jev.tanya()`
    #     ⇒ memeriksa `_periksa_skema(` di dalam satpam = GAGAL PALSU.
    #     Yang BENAR: pastikan tiap pintu tanya berakhir di jalan tol
    #     yang PUNYA pagar. (Ditemukan 12Okt26 — gerbangnya yang basi.)
    print('\n[C] pagar skema aktif di JALAN TOL (jev.py) & dipakai tiap pintu')
    jev = (DIR / 'app/jev.py').read_text()
    cek('jev.py punya `periksa_skema`', 'def periksa_skema(' in jev)
    cek('jev.py punya kelas `SkemaSalah`', 'class SkemaSalah(' in jev)
    cek('jev.tanya() MEMANGGIL pagar', 'periksa_skema(pertanyaan)' in jev)
    cek('jev.tanya() MELEMPAR saat skema salah', 'raise SkemaSalah(' in jev)
    sumber = (DIR / 'app/satpam.py').read_text()
    for fn in ('tanya_bebas', 'tanya_bebas_mutu'):
        i = sumber.find(f'def {fn}(')
        j = sumber.find('\ndef ', i + 1)
        badan = sumber[i:j if j > 0 else len(sumber)]
        pakai_tol = ('_jev.tanya(' in badan or 'jev.tanya(' in badan
                     or '_periksa_skema(' in badan)
        cek(f'{fn}() lewat jalan tol berpagar', pakai_tol)
        gagal_cepat = ('raise' in badan or 'SkemaSalah' in badan
                       or 'ValueError' in badan)
        cek(f'{fn}() GAGAL-CEPAT saat skema salah', gagal_cepat)

    #  ── [D] tidak ada klaim palsu di kode ─────────────────────────────
    print('\n[D] tidak ada klaim palsu "skema tertutup" di kode')
    klaim_palsu = [
        r'skema\s+jev\s+tertutup',
        r'hanya\s+menerima\s+3\s+nama',
        r'hanya\s+2\s+tipe',
        r'hanya\s+dua\s+tipe',
        r'no\s+matching\s+discriminator',
        r'jev\s+(sedang\s+)?tidak\s+stabil',
        r'jev\s+flaky',
        r'hanya\s+3\s+pertanyaan.*sah',
    ]
    for f in ('app/satpam.py', 'app/konversi.py'):
        isi = (DIR / f).read_text()
        temuan = []
        for pola in klaim_palsu:
            for m in re.finditer(pola, isi, re.I):
                #  abaikan kalau barisnya menandai DIHAPUS/KELIRU (blok pelajaran)
                baris_awal = isi.rfind('\n', 0, m.start()) + 1
                baris = isi[baris_awal:isi.find('\n', m.start())]
                if re.search(r'dihapus|keliru|salah|jangan|⛔|❌|🔴', baris, re.I):
                    continue
                temuan.append(f'{m.group(0)} @ {baris.strip()[:60]}')
        cek(f'{f}: tidak ada klaim palsu', not temuan, str(temuan[:3]))

    #  ── [E] UJI BERGIGI: pagar BENAR-BENAR menangkap ──────────────────
    print('\n[E] UJI BERGIGI — pagar dilumpuhkan, HARUS ketahuan')
    asli = satpam._periksa_skema
    try:
        satpam._periksa_skema = lambda q: []          # pagar dilumpuhkan
        #  suntikan skema salah yang SEHARUSNYA ditolak
        jebakan = {'x': {'type': 'noul', 'instructions': 'a', 'criteria': 'Ya.'}}
        lolos = not satpam._periksa_skema(jebakan)
        cek('pagar dilumpuhkan ⇒ skema salah LOLOS (bukti gerbang bergigi)',
            lolos, 'gerbang ini TIDAK bisa gagal ⇒ tidak menjaga apa pun')
    finally:
        satpam._periksa_skema = asli

    #  ── HASIL ─────────────────────────────────────────────────────────
    print(f'\n══ HASIL: {HASIL["lulus"]} LULUS / {HASIL["gagal"]} GAGAL ══')
    return 0 if HASIL['gagal'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
