#!/usr/bin/env python3
"""UJI NASKAH ASIH (skripsi nyata, fid=81) — mesin konversi end-to-end (mesin).

WAJIB dari DALAM container:
    docker cp _uji_naskah_asih.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _uji_naskah_asih.py

Naskah: SKRIPSI-Asih-Susanti-Putri.docx (2,3 MB) di /app/uploads/8/.
Menguji SELURUH urutan pagar ①②③ + deteksi jenis + peta bab + pemeriksa hasil
+ simpan/gagal kuota — TANPA memanggil AI (hemat token).

⚠️ PENTING: nama+email HARUS ada di naskah (putusan Bos no.5). Kalau naskah
Asih tidak memuatnya → ini BUKTI pagar bekerja, BUKAN kegagalan uji.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import konversi, kuota                                         # noqa: E402
from app.models import Base, FileBerkas, KonversiNaskah, User           # noqa: E402

LULUS = 0
GAGAL = 0
BERKAS = Path('/app/uploads/8/3dbd8babe72c6098.docx')


def cek(nama, benar, bukti=''):
    global LULUS, GAGAL
    if benar:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def teks_docx(jalur: Path) -> str:
    with zipfile.ZipFile(jalur) as z:
        x = z.read('word/document.xml').decode('utf-8', 'ignore')
    t = x.replace('</w:p>', '\n')
    import re
    t = re.sub(r'<[^>]+>', ' ', t)
    import re as _re
    t = _re.sub(r'[ \t]{2,}', ' ', t)
    return t


def main() -> int:
    print('══ UJI NASKAH ASIH (SKRIPSI NYATA) — MESIN KONVERSI ══')

    if not BERKAS.is_file():
        print(f'❌ berkas tidak ada: {BERKAS}')
        return 2
    print(f'berkas : {BERKAS}')
    print(f'ukuran : {BERKAS.stat().st_size/1024/1024:.2f} MB')

    #  ── PAGAR ① berkas aman ──────────────────────────────────────────
    print('\n[①] PAGAR BERKAS & MAKRO')
    aman, pesan = konversi.periksa_berkas_aman(BERKAS.name, BERKAS)
    cek('berkas .docx asli → LOLOS', aman is True, pesan[:80])

    t = teks_docx(BERKAS)
    print(f'     teks terbaca: {len(t):,} karakter')
    cek('teks terbaca (>5.000 kar)', len(t) > 5000, f'{len(t)} kar')

    #  ── PAGAR ② nama + email ────────────────────────────────────────
    print('\n[②] PAGAR NAMA + EMAIL (putusan Bos no.5)')
    ident = konversi.cari_identitas(t)
    kurang = konversi.lengkapi_identitas(ident)
    print(f'     nama  = {ident["nama"]!r}')
    print(f'     email = {ident["email"]!r}')
    print(f'     kurang= {kurang}')
    if kurang:
        print('     ⚠️  NASKAH INI TIDAK MEMUAT ' + ' + '.join(kurang).upper())
        print('     ⇒ Mesin AKAN BERHENTI & minta user lengkapi = SESUAI PUTUSAN BOS.')
    else:
        print('     ⇒ Naskah memuat identitas lengkap → boleh lanjut konversi.')
    cek('pagar② mengambil keputusan (tidak error)', isinstance(kurang, list), '')

    #  ── DETEKSI JENIS ────────────────────────────────────────────────
    print('\n[④] DETEKSI JENIS')
    j = konversi.deteksi_jenis(t)
    print(f'     jenis={j["jenis"]} yakin={j["yakin"]} skor={j["skor"]}')
    cek('jenis terdeteksi', j['jenis'] in konversi.SEMUA_JENIS, str(j['jenis']))
    cek('keyakinan wajar (0,30–0,95)', 0.30 <= j['yakin'] <= 0.95, str(j['yakin']))

    #  ── PETA BAB + KELENGKAPAN ───────────────────────────────────────
    print('\n[③] PETA BAB & KELENGKAPAN')
    from app import state
    peta = state.petakan(t) or []
    print(f'     peta: {len(peta)} bagian')
    kat = sorted({str(p.get('kategori') or '') for p in peta if isinstance(p, dict)})
    print(f'     kategori: {kat}')
    cek('peta bab TIDAK kosong', len(peta) > 0, f'{len(peta)}')
    kel = konversi.cek_kelengkapan({'teks': t}, peta)
    print(f'     kurang: {kel["kurang"]}')
    cek('pagar③ TIDAK salah menuduh bab inti',
        not (set(kel['kurang']) & {'latar_belakang', 'metode', 'kesimpulan'}),
        str(kel['kurang']))

    #  ── PEMERIKSA HASIL (lapis 1) ────────────────────────────────────
    print('\n[⑤] PEMERIKSA HASIL (lapis mesin)')
    hasil_kosong = konversi.periksa_hasil({})
    cek('hasil kosong → TIDAK lolos', hasil_kosong['lolos'] is False, '')
    cek('deteksi 11 elemen hilang', len(hasil_kosong['elemen_hilang']) == 11,
        str(len(hasil_kosong['elemen_hilang'])))

    #  ── KUOTA: potong → simpan / gagal ───────────────────────────────
    print('\n[⑥] KUOTA — potong · simpan · gagal-kembalikan')
    eng = create_engine('sqlite:////tmp/uji_asih.sqlite')
    if Path('/tmp/uji_asih.sqlite').exists():
        Path('/tmp/uji_asih.sqlite').unlink()
    eng = create_engine('sqlite:////tmp/uji_asih.sqlite')
    Base.metadata.create_all(eng)
    db = sessionmaker(bind=eng)()
    u = User(nama='Asih Uji', email='asih.uji@eduai.test', paket='penerbit',
             password_hash='x')
    db.add(u); db.commit()
    f = FileBerkas(user_id=u.id, nama=BERKAS.name, nama_simpan='uji.docx',
                   ukuran=BERKAS.stat().st_size, tipe='application/docx')
    db.add(f); db.commit()

    jatah0 = kuota.jatah_konversi(db, u)
    print(f'     jatah awal: {jatah0}')
    cek('penerbit punya jatah 2× konversi', jatah0['sisa'] == 2, str(jatah0))

    ok, info = kuota.potong_konversi(db, u, f.id)
    cek('potong_konversi berhasil', ok is True, str(info))
    cek('jatah setelah potong = 1',
        kuota.jatah_konversi(db, u)['sisa'] == 1, '')
    baris = db.query(KonversiNaskah).filter(KonversiNaskah.file_id == f.id).first()
    cek("baris konversi status 'proses'", baris and baris.status == 'proses',
        baris.status if baris else 'TIDAK ADA')

    #  gagal teknis → jatah kembali
    konversi.gagalkan(db, u, f.id, 'AI timeout (uji)')
    cek('gagal teknik → jatah KEMBALI = 2',
        kuota.jatah_konversi(db, u)['sisa'] == 2, '')
    db.close()

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
