#!/usr/bin/env python3
"""GERBANG TAHAP 1 KONVERSI — KUOTA (07 Okt 2026).

WAJIB dijalankan dari DALAM container `eduai-app` (host tak punya httpx/DB):
    docker cp _gerbang_konversi_kuota.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_konversi_kuota.py

YANG DIUJI (3 hal, sesuai risiko R2 = kebocoran uang):
  1. JATAH BENAR  — paket + AddOn − terpakai, tak ada yang luput
  2. POTONG BENAR — baris pelacak tercatat, klik dobel DITOLAK
  3. HABIS → TOLAK + tawaran (tak ada jalur gratis)

⛔ ATURAN: gerbang ini HARUS BERGIGI. Kalau bisa lulus padahal kode dirusak,
   gerbangnya palsu. Uji gigi dengan cara disuntik (lihat --gigit).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, '/app')

from sqlalchemy import create_engine, select                      # noqa: E402
from sqlalchemy.orm import sessionmaker                            # noqa: E402

from app import kuota                                              # noqa: E402
from app.models import (Base, FileBerkas, KonversiNaskah,          # noqa: E402
                        PembelianAddon, User)

LULUS = 0
GAGAL = 0


def cek(nama: str, benar: bool, bukti: str = '') -> None:
    global LULUS, GAGAL
    if benar:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def _db_sementara():
    """DB SQLite sementara di memori-disk (/tmp) — TIDAK menyentuh DB asli."""
    berkas = '/tmp/gerbang_konversi_kuota.sqlite'
    if os.path.exists(berkas):
        os.remove(berkas)
    eng = create_engine(f'sqlite:///{berkas}')
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def _user(db, paket: str, email: str) -> User:
    #  ⚠️ password_hash WAJIB (kolom NOT NULL) — gerbang ini tidak menguji sandi,
    #  jadi diisi penanda saja. Pelajaran: gerbang kedua gagal karena ini.
    u = User(nama='Uji', email=email, paket=paket, password_hash='x-gerbang')
    db.add(u)
    db.commit()
    return u


def _naskah(db, uid: int, nama: str) -> FileBerkas:
    #  ⚠️ FileBerkas punya kolom WAJIB: nama_simpan, ukuran, tipe (nullable=False).
    f = FileBerkas(user_id=uid, nama=nama, nama_simpan=nama,
                   ukuran=1234, tipe='application/docx')
    db.add(f)
    db.commit()
    return f


def main() -> int:
    print('══ GERBANG TAHAP 1 KONVERSI — KUOTA ══')
    db = _db_sementara()

    #  ── 1. JATAH: paket + AddOn − terpakai ─────────────────────────────
    print('\n[1] JATAH — paket + AddOn − terpakai')
    u = _user(db, 'peneliti', 'a@uji.id')             # peneliti = konversi 1
    j = kuota.jatah_konversi(db, u)
    cek('peneliti: jatah_paket = 1', j['jatah_paket'] == 1, str(j))
    cek('peneliti: sisa = 1', j['sisa'] == 1, str(j))
    cek('peneliti: boleh = True', j['boleh'] is True, str(j))

    u2 = _user(db, 'gratis', 'b@uji.id')              # gratis = konversi 0
    j2 = kuota.jatah_konversi(db, u2)
    cek('gratis: jatah_paket = 0', j2['jatah_paket'] == 0, str(j2))
    cek('gratis: boleh = False', j2['boleh'] is False, str(j2))

    u3 = _user(db, 'penerbit', 'c@uji.id')            # penerbit = konversi 2
    j3 = kuota.jatah_konversi(db, u3)
    cek('penerbit: jatah_paket = 2', j3['jatah_paket'] == 2, str(j3))

    #  AddOn menambah jatah
    db.add(PembelianAddon(user_id=u3.id, jenis='konversi',
                          sisa_kuota=1, harga=100_000))
    db.commit()
    j3b = kuota.jatah_konversi(db, u3)
    cek('penerbit + AddOn: jatah_addon = 1', j3b['jatah_addon'] == 1, str(j3b))
    cek('penerbit + AddOn: total = 3', j3b['total'] == 3, str(j3b))
    cek('penerbit + AddOn: sisa = 3', j3b['sisa'] == 3, str(j3b))

    #  ── 2. POTONG: catat baris + tolak dobel ───────────────────────────
    print('\n[2] POTONG — catat baris + tolak klik dobel')
    f1 = _naskah(db, u.id, 'skripsi-uji.docx')
    ok, pesan = kuota.potong_konversi(db, u, f1.id)
    cek('potong pertama → ok', ok is True, pesan)
    cek('baris pelacak TERCATAT', db.query(KonversiNaskah).count() == 1,
        f'jumlah baris = {db.query(KonversiNaskah).count()}')
    baris = db.query(KonversiNaskah).first()
    cek("status baris = 'proses'", baris.status == 'proses', baris.status)

    #  jatah ikut berkurang
    j_after = kuota.jatah_konversi(db, u)
    cek('setelah potong: sisa = 0', j_after['sisa'] == 0, str(j_after))
    cek('setelah potong: boleh = False', j_after['boleh'] is False, str(j_after))

    #  klik dobel pada naskah SAMA (masih 'proses') → TOLAK
    ok2, pesan2 = kuota.potong_konversi(db, u, f1.id)
    cek('potong dobel naskah sama → TOLAK', ok2 is False, pesan2)
    cek('baris TIDAK bertambah', db.query(KonversiNaskah).count() == 1,
        f'jumlah baris = {db.query(KonversiNaskah).count()}')

    #  ── 3. HABIS → TOLAK + jalan keluar ────────────────────────────────
    print('\n[3] HABIS — tolak + tawaran (tak ada jalur gratis)')
    f2 = _naskah(db, u.id, 'skripsi-kedua.docx')
    ok3, pesan3 = kuota.potong_konversi(db, u, f2.id)
    cek('jatah habis → TOLAK', ok3 is False, pesan3)
    cek('pesan menyebut AddOn', 'AddOn' in pesan3, pesan3)

    f3 = _naskah(db, u2.id, 'skripsi-gratis.docx')
    ok4, pesan4 = kuota.potong_konversi(db, u2, f3.id)
    cek('gratis → TOLAK', ok4 is False, pesan4)
    cek('pesan menyebut naikkan paket', 'paket' in pesan4.lower(), pesan4)

    #  ── 4. GAGAL TEKNIS → jatah KEMBALI ────────────────────────────────
    print('\n[4] GAGAL TEKNIS — jatah kembali (user TIDAK dirugikan)')
    u4 = _user(db, 'peneliti', 'd@uji.id')
    f4 = _naskah(db, u4.id, 'skripsi-gagal.docx')
    ok5, _ = kuota.potong_konversi(db, u4, f4.id)
    cek('potong → ok', ok5 is True)
    j_gagal1 = kuota.jatah_konversi(db, u4)
    cek('sebelum gagal: sisa = 0', j_gagal1['sisa'] == 0, str(j_gagal1))

    kuota.kembalikan_konversi(db, u4.id, f4.id, galat='AI timeout')
    j_gagal2 = kuota.jatah_konversi(db, u4)
    cek('setelah gagal: sisa = 1 (KEMBALI)', j_gagal2['sisa'] == 1, str(j_gagal2))
    baris_g = db.query(KonversiNaskah).filter(
        KonversiNaskah.file_id == f4.id).first()
    cek("status baris = 'gagal'", baris_g.status == 'gagal', baris_g.status)
    cek('jejak galat tersimpan', 'timeout' in (baris_g.galat or ''), baris_g.galat)

    #  bisa potong lagi (karena gagal, jatah kembali)
    ok6, pesan6 = kuota.potong_konversi(db, u4, f4.id)
    cek('setelah gagal: boleh potong LAGI', ok6 is True, pesan6)

    #  ── 5. SELESAI → hasil tersimpan + tidak kembali ───────────────────
    print('\n[5] SELESAI — hasil tersimpan, jatah TIDAK kembali')
    u5 = _user(db, 'peneliti', 'e@uji.id')
    f5 = _naskah(db, u5.id, 'skripsi-beres.docx')
    kuota.potong_konversi(db, u5, f5.id)
    kuota.selesaikan_konversi(db, u5.id, f5.id,
                              hasil={'artikel': {'abstrak': 'x'}},
                              jenis='kuantitatif', token_dipotong=0)
    j5 = kuota.jatah_konversi(db, u5)
    cek('setelah selesai: sisa = 0 (TIDAK kembali)', j5['sisa'] == 0, str(j5))
    b5 = db.query(KonversiNaskah).filter(KonversiNaskah.file_id == f5.id).first()
    cek("status = 'beres'", b5.status == 'beres', b5.status)
    cek('jenis tersimpan', b5.jenis == 'kuantitatif', b5.jenis)
    cek('hasil tersimpan (bukan {})', b5.hasil_json not in ('', '{}'), b5.hasil_json)

    #  ── 6. RINGKASAN (tutup R1) ────────────────────────────────────────
    print('\n[6] RINGKASAN — kuota.konversi kirim SISA (dulu tidak)')
    r = kuota.ringkasan_kuota(db, u5)
    cek("ringkasan punya kunci 'konversi'", 'konversi' in r, str(sorted(r)))
    konv = r.get('konversi', {})
    cek("ringkasan['konversi'] punya 'sisa'", 'sisa' in konv, str(konv))
    cek("ringkasan['konversi'] punya 'dipakai'", 'dipakai' in konv, str(konv))
    cek("ringkasan['konversi'] punya 'jatah_addon'", 'jatah_addon' in konv, str(konv))
    cek('nilai sisa benar = 0', konv.get('sisa') == 0, str(konv))

    #  ── 7. MILIK ORANG LAIN → TOLAK ────────────────────────────────────
    print('\n[7] PAGAR — naskah bukan miliknya → TOLAK')
    u6 = _user(db, 'peneliti', 'f@uji.id')
    f_orang = _naskah(db, u5.id, 'punya-orang-lain.docx')
    ok7, pesan7 = kuota.potong_konversi(db, u6, f_orang.id)
    cek('naskah orang lain → TOLAK', ok7 is False, pesan7)
    cek('pesan: bukan milikmu', 'bukan milikmu' in pesan7.lower(), pesan7)

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
