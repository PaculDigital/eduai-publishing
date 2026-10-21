"""VALIDASI SILANG — 14 KASUS dari DISERTASI-104 (naskah yang BELUM PERNAH dilihat).

Vonis Bos: "K5 disetel lewat iterasi K1→K5 di atas 12 kasus ini — 12/12 di set
latih berisiko overfit. Kunci K5, uji di kasus batas Disertasi yang belum pernah
dilihat. Itu validasi sesungguhnya. Tambah kasus POSITIF."

K5 TIDAK DIUBAH SAMA SEKALI (dikunci) — hanya diuji.
Tambahan: 5 kasus POSITIF (cabang `true` nyaris tak teruji sebelumnya).
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, '/app')

from app import ai, models, jev                           # noqa: E402
from app.ai import SessionLocal, UPLOAD_DIR               # noqa: E402

FID = 104

#  (CIRI unik, kunci, kategori, alasan-dibaca-dari-naskah)
KASUS = [
    # ══ POSITIF — judul licin (cabang true yang belum teruji) ══
    ('Patofisiologi Stunting', 'JUDUL', 'P1',
     'judul tanpa garis akhir, diikuti paragraf isi baru'),
    ('Epidemilogi Stunting', 'JUDUL', 'P2',
     'judul nomor polos + nama topik bahasan, diikuti paragraf baru'),
    ('Dampak stunting', 'JUDUL', 'P3',
     'judul nomor polos + nama topik, diikuti paragraf baru'),
    ('Manfaat ilmiah', 'JUDUL', 'P4',
     'judul butir manfaat — tapi bentuknya NAMA TOPIK (ilmiah/praktis/institusi)'),
    ('Manfaat institusi', 'JUDUL', 'P5',
     'judul butir manfaat — nama topik, sejajar dengan Manfaat ilmiah/praktis'),

    # ══ NEGATIF — butir pertanyaan penelitian ══
    ('1. Bagaimana pola spasial sebaran derajat', 'BUKAN', 'N1',
     'butir PERTANYAAN penelitian — bentuk kalimat tanya, lanjut baris berikutnya'),
    ('2. Bagaimana pengaruh determinan tingkat individu', 'BUKAN', 'N2',
     'butir pertanyaan penelitian — lanjut baris berikutnya'),
    ('4. Bagaimana peta proyeksi stunting', 'BUKAN', 'N3',
     'butir pertanyaan penelitian'),

    # ══ NEGATIF — daftar lampiran ══
    ('1. Surat Persetujuan Etik', 'BUKAN', 'N4',
     'butir daftar lampiran'),
    ('2. Surat Keterangan Serah Terima Data', 'BUKAN', 'N5',
     'butir daftar lampiran'),

    # ══ NEGATIF — isi tabel/angka ══
    ('2020', 'BUKAN', 'N6',
     'angka tahun berdiri sendiri — bagian tabel/halaman'),
    ('2000', 'BUKAN', 'N7',
     'angka tahun berdiri sendiri — bagian tabel/halaman'),
]


def baris_fid(fid: int) -> list[str]:
    db = SessionLocal()
    fb = db.get(models.FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (ai._teks_dari_berkas(p, fb.nama or '') or '').split('\n')


def main():
    b = baris_fid(FID)
    print(f'Disertasi fid={FID}: {len(b)} baris\n')

    kasus, lewat = [], []
    for ciri, kunci, kat, sebab in KASUS:
        idx = [j for j, s in enumerate(b) if s.strip() == ciri.strip()]
        if not idx:
            idx = [j for j, s in enumerate(b) if ciri in s]
        if not idx:
            lewat.append((kat, ciri))
            print(f'  ❌ TIDAK KETEMU {kat} {ciri[:44]!r}')
            continue
        i = idx[0]
        jendela = [f'L{j:06d}| {b[j][:80]}'
                   for j in range(max(0, i - 2), min(len(b), i + 3))]
        kasus.append({'fid': FID, 'i': i, 'kode': kat, 'teks': b[i][:80],
                      'jendela': jendela, 'kunci_asli': kunci, 'sebut': sebab})
        print(f'  ✅ {kat:<3} {kunci:<5} L{i:06d} {b[i].strip()[:48]!r}')

    print(f'\n{len(kasus)} kasus siap · lewat: {len(lewat)}')

    # ── K5 DIKUNCI — tidak diubah ──
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

    # ── 1 FAN-OUT: semua kasus 1 panggilan ──
    Q, potong = {}, []
    for n, k in enumerate(kasus):
        Q[f'c{n:02d}'] = {
            'type': 'noul',
            'instructions': ('Apakah baris tengah pada jendela ini adalah KEPALA '
                             f'BAGIAN naskah? Baris tengah = `{k["teks"]}`.'),
            'criteria': K5,
        }
        potong.append(f'### kasus c{n:02d}')
        potong.extend(k['jendela'])
    bahan = '\n'.join(potong)

    print('\nmenembak 1 fan-out ...')
    hasil = jev.tanya(bahan, Q) or {}

    print()
    print('kasus  kat  kunci   noul  vonis  benar')
    print('-' * 52)
    benar = 0
    for n, k in enumerate(kasus):
        x = (hasil.get(f'c{n:02d}') or {}).get('noul')
        if x is None:
            print(f'c{n:02d}  {k["kode"]:<3} {k["kunci_asli"]:<6}  ?     ?      ?')
            continue
        ya = x >= 0.5
        ok = (ya and k['kunci_asli'] == 'JUDUL') or \
             ((not ya) and k['kunci_asli'] == 'BUKAN')
        if ok:
            benar += 1
        print(f'c{n:02d}  {k["kode"]:<3} {k["kunci_asli"]:<6}  {x:.2f}  '
              f'{"JUDUL" if ya else "BUKAN":<5}  {"✅" if ok else "❌"}   '
              f'{k["teks"][:32]!r}')

    print()
    print(f'VALIDASI SILANG (K5 DIKUNCI, naskah ke-3): {benar}/{len(kasus)} '
          f'({100.0*benar/max(len(kasus),1):.0f}%)')

    # putus kunci: POSITIF vs NEGATIF
    pos = [k for k in kasus if k['kunci_asli'] == 'JUDUL']
    neg = [k for k in kasus if k['kunci_asli'] == 'BUKAN']
    bp = sum(1 for n, k in enumerate(kasus)
             if k['kunci_asli'] == 'JUDUL'
             and ((hasil.get(f'c{n:02d}') or {}).get('noul') or 0) >= 0.5)
    bn = sum(1 for n, k in enumerate(kasus)
             if k['kunci_asli'] == 'BUKAN'
             and ((hasil.get(f'c{n:02d}') or {}).get('noul') or 1) < 0.5)
    print(f'  POSITIF (judul): {bp}/{len(pos)}   NEGATIF: {bn}/{len(neg)}')

    json.dump({'kasus': kasus, 'jawaban': hasil,
               'benar': benar, 'positif': f'{bp}/{len(pos)}',
               'negatif': f'{bn}/{len(neg)}'},
              open('/app/HASIL_VALIDASI_DISERTASI.json', 'w'),
              ensure_ascii=False, indent=1)
    print('→ /app/HASIL_VALIDASI_DISERTASI.json')


if __name__ == '__main__':
    sys.exit(main())
