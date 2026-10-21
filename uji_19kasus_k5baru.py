"""UKUR ULANG — 19 KASUS (12 lama + 7 baru dari putusan Bos) vs 3 KALIMAT K5.

Protokol Bos: "Wulan setujui — dengan syarat protokol pengukurannya sama ketatnya
(12 kasus + validasi silang, bukan tempel-buta). Itu bukan menambal; itu
menambah sinyal terukur."

Tujuan:
  (a) REGRESI: K5-baru tidak boleh merusak 12 kasus lama (Asih+Wulandari)
  (b) BARU: K5-baru memperbaiki 7 baris putusan Bos (khususnya 4× N. Informan)

3 kalimat diuji (SEMUA pakai `criteria`, pagar sudah dibuka 09 Okt):
  K5-LAMA  : kalimat yang SEKARANG terpasang (dikunci)
  K5-BARU  : + D-A (kepala tabel BUKAN kepala naskah)
             + D-B (butir di tengah deret tanpa anak)
             + D-C (anak bernomor = syarat CUKUP, DISJUNGTIF)
  K5-KETAT : K5-BARU tetapi anak-bernomor ditulis seolah syarat PERLU
             (untuk membuktikan catatan Bos: definisi ketat = MENGGUGURKAN)
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, '/app')

from app import jev                                        # noqa: E402
import peta3_jev as P                                       # noqa: E402

# ── K5-LAMA (yang sekarang terpasang) ──
K5_LAMA = {
    'true': ('Baris adalah JUDUL BAGIAN dari kerangka naskah. Ciri: berisi nama '
             'topik bahasan (bukan nama kegiatan/langkah), nomornya menandai '
             'kedudukan bagian dalam kerangka tulisan seperti 2.1 atau BAB II '
             'atau nomor polos tanpa titik yang sejajar dengan judul bab lain '
             'di dokumen ini, dan baris berikutnya mulai dengan paragraf '
             'penjelasan baru.'),
    'false': ('Baris adalah SATU LANGKAH KEGIATAN atau SATU BUTIR dari sebuah '
              'daftar cara kerja, atau bagian lain yang bukan kepala tulisan: '
              'deret angka di dalam tabel, sel dan kolom, keterangan bernama '
              'di atas tabel atau gambar, potongan kutipan wawancara, nama '
              'sumber, atau sambungan kalimat sebelumnya yang belum selesai.'),
}

# ── K5-BARU (D-A + D-B + D-C disjungtif) ──
K5_BARU = {
    'true': ('Baris adalah JUDUL BAGIAN dari kerangka naskah. Ciri: berisi nama '
             'topik bahasan (bukan nama kegiatan/langkah), nomornya menandai '
             'kedudukan bagian dalam kerangka tulisan seperti 2.1 atau BAB II '
             'atau nomor polos tanpa titik yang sejajar dengan judul bab lain '
             'di dokumen ini, dan baris berikutnya mulai dengan paragraf '
             'penjelasan baru. Baris bernomor yang menaungi beberapa anak '
             'bernomor lagi (a., b., c.) juga termasuk judul bagian — ini '
             'SALAH SATU ciri, bukan satu-satunya, jadi judul yang tidak '
             'punya anak tetap sah.'),
    'false': ('Baris adalah SATU LANGKAH KEGIATAN atau SATU BUTIR dari sebuah '
              'daftar cara kerja, atau bagian lain yang bukan kepala tulisan: '
              'deret angka di dalam tabel, sel dan kolom, keterangan bernama '
              'di atas tabel atau gambar, potongan kutipan wawancara, nama '
              'sumber, atau sambungan kalimat sebelumnya yang belum selesai. '
              'Termasuk juga kepala kolom atau kepala kuadran yang berada di '
              'dalam sebuah tabel (misalnya Kekuatan, Kelemahan, Peluang, '
              'Ancaman di dalam tabel analisis SWOT) karena itu isi tabel, '
              'dan baris bernomor yang berdiri di tengah deret kegiatan '
              'sejenis tanpa menaungi anak apa pun.'),
}

# ── K5-KETAT (kontrol: anak bernomor ditulis seolah SYARAT PERLU) ──
K5_KETAT = {
    'true': ('Baris adalah JUDUL BAGIAN dari kerangka naskah, yaitu baris '
             'bernomor yang menaungi beberapa anak bernomor lagi (a., b., c.). '
             'Ciri: berisi nama topik bahasan, nomornya menandai kedudukan '
             'bagian dalam kerangka tulisan seperti 2.1 atau BAB II, dan baris '
             'berikutnya mulai dengan anak bernomor.'),
    'false': ('Baris adalah SATU LANGKAH KEGIATAN atau SATU BUTIR dari sebuah '
              'daftar cara kerja, deret angka di dalam tabel, sel dan kolom, '
              'potongan kutipan wawancara, nama sumber, sambungan kalimat '
              'sebelumnya, kepala kolom atau kepala kuadran di dalam tabel '
              '(misalnya Kekuatan/Kelemahan/Peluang/Ancaman di tabel SWOT), '
              'atau baris bernomor tanpa menaungi anak apa pun.'),
}

FID_BATAS = 115


def baris_fid(fid: int) -> list[str]:
    """Ambil daftar baris lewat SATU penggaris: `peta3_jev.susun()['baris']`.

    🚨 PELAJARAN c04 (09 Okt): ada 3 cara baca naskah — MENTAH (`split('\n')`,
    9.042 baris), SUSUN (`susun()['baris']`, 8.755 baris), BLOK (konversi).
    Indeks TIDAK bisa ditukar. Harness lama pakai MENTAH ⇒ mengukur baris
    daftar isi ⇒ skor palsu 0,10. Uji WAJIB pakai penggaris yang SAMA dengan
    mesin: `susun()`. (Keputusan peleburan 3 penggaris = urusan stitch nanti.)
    """
    d = P.susun(fid)
    b = (d.get('baris') if isinstance(d, dict) else d) or []
    if not b:
        raise RuntimeError(f'susun({fid}) tidak memberi baris — uji dibatalkan')
    return list(b)


def main():
    b = baris_fid(FID_BATAS)

    # ── 19 KASUS: 12 lama (dibaca ulang dari naskah by ISI) + 7 baru ──
    #  12 lama = pencarian ISI (seperti uji_batas_12.py)
    LAMA = [
        # (isi, kunci, kategori)
        ('2020', 'BUKAN', 'N-angka'),
        ('2000', 'BUKAN', 'N-angka2'),
        ('(Khoironi, 2023)', 'BUKAN', 'S-sitasi'),
        ('(David, 2010) dalam (Andika, 2020).', 'BUKAN', 'S-sitasi2'),
        ('2. Wawancara', 'BUKAN', 'B-butir-kegiatan'),
        ('3. Tinjauan Literatur', 'JUDUL', 'P-judul-nomor'),
        ('Kategori Hasil Kutipan Informan', 'BUKAN', 'H-header-tabel'),
        ('Tabel 4. 1 Tabel Analisis SWOT Hijab Tape AyuMeera', 'BUKAN', 'H-judul-tabel'),
        ('4. Threats (Ancaman)', 'JUDUL', 'P-butir-nomor-judul'),
    ]
    BARU = [
        ('Kekuatan (Strength)', 'BUKAN', 'D-A kepala kuadran tabel'),
        ('6 Sidang Skripsi', 'BUKAN', 'D-B butir di tengah deret'),
        ('1. Informan (Ulan – Pengelola AyuMeera)', 'JUDUL', 'D-C punya anak'),
        ('2. Informan (Regina – Div. AyuMeera)', 'JUDUL', 'D-C punya anak'),
        ('3. Informan (Anie – Div. Chemical)', 'JUDUL', 'D-C punya anak'),
        ('4. Informan (April – Konsumen)', 'JUDUL', 'D-C punya anak'),
        ('Hijab yang menjadi trend', 'BUKAN', 'butir lanjutan strip'),
        ('Threats (Decision-Making Theory).', 'BUKAN', 'fragmen narasi'),
    ]

    kasus = []
    for isi, kunci, kat in LAMA + BARU:
        idx = [j for j, s in enumerate(b) if s.strip() == isi.strip()]
        if not idx:
            idx = [j for j, s in enumerate(b) if isi in s]
        if not idx:
            print(f'  ❌ TIDAK KETEMU: {isi[:44]!r}')
            continue
        i = idx[0]
        kasus.append({
            'kode': kat, 'kunci': kunci, 'teks': isi[:60], 'i': i,
            'jendela': [f'L{j:06d}| {b[j][:78]}'
                        for j in range(max(0, i - 2), min(len(b), i + 3))],
        })
    print(f'{len(kasus)} kasus siap diuji\n')

    #  ⚠️ CACAT HARNESS (terukur 09 Okt, SELIDIK_C04): kunci sebaiknya TIDAK
    #  memakai '#' dan '-' — bentrok dengan penanda Jev. Pakai bentuk polos.
    KALIMAT = {'klama': K5_LAMA, 'kbaru': K5_BARU, 'kketat': K5_KETAT}
    Q, potong = {}, []
    for vn, K in KALIMAT.items():
        for n, k in enumerate(kasus):
            Q[f'{vn}c{n:02d}'] = {
                'type': 'noul',
                'instructions': (f'Apakah baris TENGAH untuk kandidat {vn}c{n:02d} '
                                 'di atas benar-benar KEPALA BAGIAN (judul) naskah?'),
                'criteria': K,
            }
        potong.append(f'### kelompok {vn}')
        for n, k in enumerate(kasus):
            potong.append(f'#### kandidat {vn}c{n:02d}')
            potong.extend(k['jendela'])
    bahan = '\n'.join(potong)
    #  🔎 DEBUG c04: cetak jendela yang benar-benar dikirim (bukan yang diduga).
    _c = kasus[4]
    print(f'DEBUG c04: i={_c["i"]} teks={_c["teks"]!r}')
    for _l in _c['jendela']:
        print('   DEBUG|', _l)
    print(f'menembak 1 fan-out ({len(Q)} pertanyaan) ...')
    hasil = jev.tanya(bahan, Q) or {}

    #  🚨 ASERSI KELENGKAPAN (pelajaran SELIDIK_C04): jawaban HILANG ≠ Jev salah.
    #  Wajib diperiksa sebelum membaca angka apa pun.
    kurang = [kk for kk in Q if kk not in hasil]
    print(f'jawaban diterima: {len(hasil)}/{len(Q)}')
    if kurang:
        print(f'⚠️ PERINGATAN: {len(kurang)} jawaban HILANG — angka TIDAK SAH.')
        print(f'   contoh hilang: {kurang[:5]}')

    for vn in KALIMAT:
        benar = salah = 0
        print(f'\n=== {vn} ===')
        for n, k in enumerate(kasus):
            x = (hasil.get(f'{vn}c{n:02d}') or {}).get('noul')
            if x is None:
                print(f'  ?  c{n:02d} {k["teks"][:36]!r}')
                continue
            ya = x >= 0.5
            ok = (ya and k['kunci'] == 'JUDUL') or \
                 ((not ya) and k['kunci'] == 'BUKAN')
            benar += 1 if ok else 0
            salah += 0 if ok else 1
            if not ok:
                print(f'  ❌ c{n:02d} {k["kode"]:<22} noul={x:.2f} '
                      f'kunci={k["kunci"]:<5} {k["teks"][:34]!r}')
        print(f'  ⇒ BENAR {benar}/{len(kasus)} '
              f'({100.0*benar/max(len(kasus),1):.0f}%) · SALAH {salah}')

    json.dump({'kasus': kasus, 'jawaban': hasil},
              open('/app/HASIL_UKUR_19KASUS.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.exit(main())
