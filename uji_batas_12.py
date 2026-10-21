"""UJI ①c — 3 KALIMAT `criteria`, 12 KASUS BATAS, 1 FAN-OUT.

Tujuan (vonis Bos): ukur apakah kalimat criteria yang BAIK **MEMBALIK vonis**
pada kasus batas dengan benar — bukan sekadar menggeser skor.

Pola resmi: true/false mendeskripsikan CIRI TERAMATI pada isi, bukan vonis
("Ini judul"/"Ini bukan judul" = melingkar).

KALIMAT YANG DIUJI:
  K0 (dasar)   : tanpa criteria — pembanding
  K1 (melingkar): true="Baris ini judul asli." false="Baris ini bukan judul asli."
  K2 (ciri)    : true=ciri judul teramati · false=ciri pecahan/tabel/sitasi/butir
  K3 (ciri+)   : K2 diperkuat pembeda kategori (tabel vs kepala bagian)
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, '/app')

from app import jev                                       # noqa: E402

Q_TANYA = 'Apakah baris tengah pada jendela ini adalah KEPALA BAGIAN naskah?'

K1 = {
    'true': 'Baris ini judul asli.',
    'false': 'Baris ini bukan judul asli.',
}

K2 = {
    'true': ('Baris berdiri sendiri sebagai kepala bagian: pendek, tanpa titik di '
             'akhir, dan kalimat sesudahnya adalah paragraf isi baru yang '
             'menjelaskan bagian itu.'),
    'false': ('Baris adalah pecahan isi: bagian dari tabel (deret angka, kolom '
              'dipisah garis tegak), fragmen kutipan atau nama sumber dalam '
              'kurung, butir daftar, keterangan gambar/tabel, atau lanjutan '
              'kalimat yang sedang berjalan.'),
}

K5 = {
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

K4 = {
    'true': ('Baris adalah NAMA BAGIAN yang berdiri sendiri sebagai kepala '
             'tulisan: maksimum satu baris pendek, TIDAK diawali nomor langkah '
             'atau nomor butir, dan baris berikutnya mulai dengan paragraf '
             'penjelasan baru. Judul boleh memuat nomor bertingkat bagian '
             '(contoh 2.1 atau 2.1.3) yang menandai kedudukannya dalam '
             'kerangka naskah.'),
    'false': ('Baris BUKAN kepala tulisan, melainkan bagian dari sesuatu yang '
              'lebih besar: satu baris di dalam tabel (angka, kolom, sel), '
              'KETERANGAN benama di atas tabel atau gambar (biasanya diawali '
              'kata Tabel/Gambar), potongan kutipan wawancara, nama sumber '
              'dalam kurung, LANGKAH dalam daftar cara kerja yang mungkin '
              'bernomor, atau sambungan kalimat sebelumnya yang belum selesai.'),
}

K3 = {
    'true': ('Baris adalah LABEL PENDEK yang memperkenalkan bagian baru: '
             'maksimum sekitar satu baris, tanpa tanda baca akhir, dan baris '
             'berikutnya mulai dengan paragraf penjelasan baru yang mandiri.'),
    'false': ('Baris adalah ISI dari sesuatu yang lebih besar: satu baris di '
              'dalam tabel (angka, kolom, sel), potongan kutipan wawancara, '
              'nama sumber, butir dalam sebuah daftar langkah, atau sambungan '
              'kalimat sebelumnya yang belum selesai.'),
}


def main():
    kasus = json.load(open('/app/BATAS_12.json'))
    print(f'{len(kasus)} kasus batas · cek_siap={jev.cek_siap()["siap"]}\n')

    # ── 1 panggilan per VARIAN (fan-out semua kasus sekaligus) ──
    def ukur(nama, criteria):
        """1 panggilan untuk SEMUA kasus."""
        Q, bahan_ok = {}, []
        for n, k in enumerate(kasus):
            q = {'type': 'noul', 'instructions': (
                f'{Q_TANYA} Baris tengah = `{k["teks"]}`.')}
            if criteria:
                q['criteria'] = criteria
            Q[f'c{n:02d}'] = q
        # bahan = semua jendela digabung (ID baris unik per kasus)
        potong = []
        for n, k in enumerate(kasus):
            potong.append(f'### kasus c{n:02d}')
            potong.extend(k['jendela'])
        bahan = '\n'.join(potong)
        hasil = jev.tanya(bahan, Q)
        return hasil or {}

    semua = {}
    for nama, crit in (('K0-tanpa', None), ('K1-melingkar', K1),
                       ('K2-ciri', K2), ('K3-ciri+', K3), ('K4-ciri++', K4), ('K5-tegas', K5)):
        h = ukur(nama, crit)
        semua[nama] = h
        print(f'{nama}: {len(h)} jawaban')

    # ── TABEL ──
    print()
    print('kasus  kat kunci  K0    K1    K2    K3    K4    | K2 K3 K4')
    print('-' * 72)
    benar = {k: 0 for k in semua}
    for n, k in enumerate(kasus):
        nama_q = f'c{n:02d}'
        noul = {v: (semua[v].get(nama_q) or {}).get('noul') for v in semua}
        baris = f'{nama_q}  {k["kode"]:<3} {k["kunci_asli"]:<5}'
        for v in ('K0-tanpa', 'K1-melingkar', 'K2-ciri', 'K3-ciri+', 'K4-ciri++', 'K5-tegas'):
            x = noul.get(v)
            baris += f' {x if x is None else round(x, 2):<5}'
        # benar = JUDUL ⇒ noul tinggi (>=0,5) · BUKAN ⇒ noul rendah (<0,5)
        cek = {}
        for v in ('K2-ciri', 'K3-ciri+', 'K4-ciri++', 'K5-tegas'):
            x = noul.get(v)
            if x is None:
                cek[v] = '?'
            else:
                ya = x >= 0.5
                ok = (ya and k['kunci_asli'] == 'JUDUL') or \
                     ((not ya) and k['kunci_asli'] == 'BUKAN')
                cek[v] = '✅' if ok else '❌'
                if ok:
                    benar[v] += 1
        baris += (f'  | {cek["K2-ciri"]}     {cek["K3-ciri+"]}'
                  f'     {cek["K4-ciri++"]}     {cek["K5-tegas"]}')
        print(baris + f'   {k["teks"][:34]!r}')

    print()
    print('RINGKASAN KEBENARAN (vonis, ambang 0,5):')
    for v in semua:
        print(f'  {v:<14}: {benar[v]}/{len(kasus)} '
              f'({100.0*benar[v]/len(kasus):.0f}%)')

    json.dump({'kasus': kasus, 'jawaban': semua},
              open('/app/HASIL_BATAS_12.json', 'w'), ensure_ascii=False, indent=1)
    print('\n→ /app/HASIL_BATAS_12.json')


if __name__ == '__main__':
    sys.exit(main())
