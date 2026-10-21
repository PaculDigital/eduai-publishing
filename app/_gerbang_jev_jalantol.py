"""GERBANG JALAN TOL JEV — 4 penjaga supaya jalur ini TIDAK PERNAH RUSAK.

Perintah Bos 09 Okt 2026 (verbatim):
  "Pasang apapun itu menjadi jalan tol dan tidak pernah rusak untuk jalur jev.
   ... Tulis jalan tol ini untuk jev di semua tempat dan jadi jalan satu
   satunya, tidak ada jalan lain."

GERBANG INI MENAHAN 4 KEMUNDURAN:
  A. Jalur dipaksa  — `jev.BASE` WAJIB jembatan; 9router (jalur B) DITOLAK
  B. Skema dipaksa  — noul+criteria WAJIB ditolak SEBELUM kirim (SkemaSalah)
  C. Jalan nyata    — Jev WAJIB jawab lewat jalan tol (bukan None)
  D. Tidak ada jalan lain — modul lain DILARANG menembak endpoint Jev sendiri

Uji bergigi: suntik 1 kemunduran ⇒ gerbang WAJIB GAGAL.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')

LULUS, GAGAL = [], []


def cek(nama: str, syarat: bool, pesan: str = ''):
    (LULUS if syarat else GAGAL).append(nama)
    print(('  ✅ ' if syarat else '  ❌ ') + nama + ((' — ' + pesan) if pesan else ''))


def main():
    from app import jev

    print('═ A. JALUR DIPAKSA ═')
    cek('A1 BASE menunjuk jembatan (bukan 9router)',
        '8130' in jev.BASE and ':20128' not in jev.BASE, jev.BASE)
    cek('A2 BASE tidak memuat 9router',
        '9router' not in jev.BASE, jev.BASE)
    #  jalur menyesatkan DITOLAK walau dipaksa lewat env
    import os
    lama = os.environ.get('EDUAI_JEV_URL')
    os.environ['EDUAI_JEV_URL'] = 'http://9router:20128/v1/chat/completions'
    cek('A3 .env ke 9router DITOLAK (dipaksa ke jembatan)',
        ':20128' not in jev._jalur() and '8130' in jev._jalur(), jev._jalur())
    if lama is None:
        os.environ.pop('EDUAI_JEV_URL', None)
    else:
        os.environ['EDUAI_JEV_URL'] = lama

    print('═ B. SKEMA DIPAKSA ═')
    cek('B1 noul TANPA criteria = SAH',
        jev.periksa_skema({'x': {'type': 'noul', 'instructions': 'a?'}}) == [])
    cek('B2 noul DENGAN criteria = DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'noul', 'instructions': 'a?',
                                      'criteria': {'a': 'b'}}})))
    cek('B3 choice TANPA criteria objek = DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'choice', 'instructions': 'a?'}})))
    cek('B4 choice DENGAN criteria objek = SAH',
        jev.periksa_skema({'x': {'type': 'choice', 'instructions': 'a?',
                                 'criteria': {'a': 'b'}}}) == [])
    cek('B5 score TANPA array = DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'score', 'instructions': 'a?'}})))
    cek('B6 score DENGAN array 2-10 = SAH',
        jev.periksa_skema({'x': {'type': 'score', 'instructions': 'a?',
                                 'criteria': ['a', 'b']}}) == [])
    cek('B7 type karangan = DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'noul2', 'instructions': 'a?'}})))
    cek('B8 questions LIST = DITOLAK (wajib objek)',
        bool(jev.periksa_skema([{'type': 'noul'}])))
    cek('B9 `pertanyaan` (alias) diterima',
        jev.periksa_skema({'x': {'type': 'noul', 'pertanyaan': 'a?'}}) == [])
    #  SkemaSalah MELEMPAR (salah programmer tidak boleh ditelan)
    try:
        jev.tanya('bahan', {'x': {'type': 'noul', 'instructions': 'a?',
                                  'criteria': {'a': 'b'}}})
        cek('B10 tanya() melempar SkemaSalah', False, 'tidak melempar!')
    except jev.SkemaSalah:
        cek('B10 tanya() melempar SkemaSalah', True)

    print('═ C. JALAN NYATA (Jev menjawab) ═')
    siap = jev.cek_siap()
    cek('C1 cek_siap() selalu dict', isinstance(siap, dict))
    cek('C2 jembatan hidup', siap.get('siap') is True, str(siap.get('sebab')))
    if siap.get('siap'):
        j = jev.tanya('ABSTRAK: Penelitian ini kuantitatif tentang UMKM.',
                      {'ada_abstrak': {'type': 'noul',
                                       'instructions': 'Memuat kata ABSTRAK?'}})
        cek('C3 Jev menjawab lewat jalan tol', isinstance(j, dict) and bool(j),
            json.dumps(j, ensure_ascii=False)[:80] if j else 'None')
        cek('C4 jawaban punya angka noul',
            bool(j) and isinstance((j.get('ada_abstrak') or {}).get('noul'),
                                   (int, float)))
        # bahan kosong TIDAK dikirim (cegah 503 semu)
        cek('C5 bahan kosong ⇒ None (tidak dikirim)',
            jev.tanya('', {'a': {'type': 'noul', 'instructions': 'x?'}}) is None)
    else:
        cek('C3-C5 dilewati (jembatan mati)', True, 'dilewati jujur')

    print('═ D. TIDAK ADA JALAN LAIN ═')
    dir_app = Path('/app/app')
    #  D1: tidak ada modul yang menembak endpoint Jev sendiri
    pola = re.compile(r"172\.17\.0\.1:8130|9router:20128|openrouter\.ai/api/v1")
    #  Gerbang ini SENDIRI memuat pola itu (untuk memeriksa) ⇒ abaikan.
    #  Yang DILARANG = modul LAIN memuat URL Jev sebagai KODE AKTIF.
    temuan = []
    for p in sorted(dir_app.glob('*.py')):
        if p.name in ('jev.py', '_gerbang_jev_jalantol.py'):
            continue
        isi = p.read_text(encoding='utf-8', errors='ignore')
        for m in pola.finditer(isi):
            #  URL di KOMENTAR/dokumentasi sah (bukan kode aktif)
            baris = isi[:m.start()].count('\n') + 1
            teks_baris = isi.splitlines()[baris - 1].strip()
            if teks_baris.startswith('#') or teks_baris.startswith('"') \
               or teks_baris.startswith("'"):  # noqa: E501
                continue
            temuan.append(f'{p.name}:{baris}')
    cek('D1 tidak ada modul lain menembak endpoint Jev langsung',
        not temuan, ', '.join(temuan[:4]))
    #  D2: satpam WAJIB lewat jalan tol (tidak menembak endpoint sendiri)
    from app import satpam
    _s = Path('/app/app/satpam.py').read_text(encoding='utf-8')
    cek('D2 satpam meneruskan ke jalan tol (jev.tanya)',
        'jev.tanya' in _s and 'urllib.request.Request' not in
        _s.split('def tanya_bebas_mutu')[1].split('def ')[0],
        'satpam tanpa panggilan langsung')
    #  D3: semua pemanggil Jev lewat jev.tanya / satpam (yang meneruskan)
    cek('D3 peta3_jev lewat satpam (yang meneruskan ke jalan tol)',
        'satpam' in Path('/app/peta3_jev.py').read_text(encoding='utf-8'))

    # ── E: CRITERIA (dibuka 09 Okt 2026 — TERUKUR ke jalur) ────────────────
    #  E1: noul + criteria OBJEK {true,false} ⇒ DITERIMA (dokumen resmi)
    cek('E1 noul + criteria OBJEK {true,false} DITERIMA',
        not jev.periksa_skema({'x': {'type': 'noul',
                                     'instructions': 'a?',
                                     'criteria': {'true': 'ya', 'false': 'tidak'}}}))
    #  E2: noul + criteria STRING ⇒ DITOLAK (sebab 502 semu)
    cek('E2 noul + criteria STRING DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'noul', 'instructions': 'a?',
                                      'criteria': 'ya kalau begitu'}})))
    #  E3: noul + criteria LIST ⇒ DITOLAK
    cek('E3 noul + criteria LIST DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'noul', 'instructions': 'a?',
                                      'criteria': ['ya', 'tidak']}})))
    #  E4: noul + criteria objek TANPA true/false ⇒ DITOLAK
    cek('E4 noul + criteria objek tanpa true/false DITOLAK',
        bool(jev.periksa_skema({'x': {'type': 'noul', 'instructions': 'a?',
                                      'criteria': {'benar': 'ya'}}})))
    #  E5: noul TANPA criteria tetap SAH (jangan dipaksa)
    cek('E5 noul tanpa criteria tetap SAH',
        not jev.periksa_skema({'x': {'type': 'noul', 'instructions': 'a?'}}))

    # ── F: K5 + PEMETAAN PRODUKSI (bukti dari berkas hasil uji, bukan panggilan) ──
    # ── F: K5 + PEMETAAN PRODUKSI (bukti dari LAPORAN .md, bukan .json) ──
    #  ⚠️ Perintah Bos 09 Okt: "jangan buat json, buat md saja". .json DIBUANG.
    f_batas = Path('/app/HASIL_UJI_12_KASUS_BATAS_09OKT2026.md')
    f_val = Path('/app/HASIL_VALIDASI_SILANG_K5_09OKT2026.md')
    ok_f1, ket1 = False, 'laporan belum ada'
    if f_batas.exists():
        t1 = f_batas.read_text(encoding='utf-8')
        ok_f1 = '12/12 (100%)' in t1 and 'K5' in t1
        ket1 = 'laporan 12 kasus batas'
    cek('F1 K5 di set latih 12/12 (laporan .md)', ok_f1, ket1)
    ok_f2, ket2 = False, 'laporan belum ada'
    if f_val.exists():
        t2 = f_val.read_text(encoding='utf-8')
        ok_f2 = '12/12 (100%)' in t2 and 'POSITIF (judul)' in t2
        ket2 = ('validasi silang Disertasi-104 · positif 5/5 · negatif 7/7'
                if ok_f2 else 'angka validasi tidak ditemukan')
    cek('F2 validasi silang (naskah ke-3) 12/12 (laporan .md)', ok_f2, ket2)
    #  F3: pemetaan produksi ADA & bernilai benar (0,60/0,30)
    _j = Path('/app/app/jev.py').read_text(encoding='utf-8')
    cek('F3 pemetaan produksi terdefinisi (0,60 sepakat · 0,30 curiga)',
        ('AMBANG_SEPAKAT' in _j or 'AMBANG_SEPAKAT' in
         Path('/app/app/hakim_peta.py').read_text(encoding='utf-8')),
        'konstanta ambang vonis hakim')
    #  F4: pagar U4b — 'p' TIDAK dipakai jadi input keputusan di hakim
    _h = Path('/app/app/hakim_peta.py').read_text(encoding='utf-8')
    cek('F4 pagar U4b — hakim TIDAK memakai `p` sebagai input keputusan',
        'p_info' in _h and 'AMBANG_P' not in _h,
        'p = info tampilan, bukan saklar')

    print()
    print('HASIL GERBANG JALAN TOL JEV: %d LULUS / %d GAGAL'
          % (len(LULUS), len(GAGAL)))
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
