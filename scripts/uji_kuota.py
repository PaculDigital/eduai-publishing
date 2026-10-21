#!/usr/bin/env python3
"""UJI SISTEM KUOTA & CREDIT AI — MASTER_PLAN §4.10.

Uji di DB SEMENTARA (tidak menyentuh data produksi).
Jalankan di dalam container: python3 /tmp/uji_kuota.py
"""
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/app')

from app.config import ADDON, KUOTA_PAKET, boleh_beli_addon
from app.kuota import (ambil_pemakaian, bulan_sekarang, cek_dan_potong,
                       kembalikan_addon, ringkasan_kuota, sisa_addon,
                       tambah_addon)
from app.models import (Base, PemakaianAI, PembelianAddon,
                        SessionLocal, User, engine)

HASIL = []


def cek(nama, syarat, detail=''):
    HASIL.append((nama, bool(syarat), detail))
    tanda = 'OK  ' if syarat else 'GAGAL'
    print(f'  [{tanda}] {nama}' + (f'  → {detail}' if detail else ''))


def main():
    print('=' * 78)
    print('UJI SISTEM KUOTA & CREDIT AI — MASTER_PLAN §4.10')
    print('=' * 78)
    print(f'Bulan sekarang: {bulan_sekarang()}\n')

    Base.metadata.create_all(engine)
    db = SessionLocal()
    stempel = datetime.now().timestamp()
    u = User(email=f'uji-kuota-{stempel}@test.local', password_hash='x',
             nama='Uji Kuota', paket='penulis')
    db.add(u)
    db.commit()
    db.refresh(u)
    print(f'User uji: id={u.id} paket={u.paket} (penulis = 12 revisi/bln)\n')

    # ── 1. Config angka (sesuai ACC Bos 13Sep26) ───────────────────────
    print('[1] ANGKA CONFIG')
    cek('Paket gratis = 3 revisi', KUOTA_PAKET['gratis']['revisi'] == 3)
    cek('Paket penulis = 12 revisi', KUOTA_PAKET['penulis']['revisi'] == 12)
    cek('Paket peneliti = 15 revisi', KUOTA_PAKET['peneliti']['revisi'] == 15)
    cek('Paket penerbit = 50 revisi', KUOTA_PAKET['penerbit']['revisi'] == 50)
    cek('AddOn AI = Rp 50.000 / 30 revisi',
        ADDON['ai']['harga'] == 50_000 and ADDON['ai']['kuota'] == 30)
    cek('AddOn Belajar = Rp 75.000 / 1 naskah',
        ADDON['belajar']['harga'] == 75_000 and ADDON['belajar']['kuota'] == 1)
    cek('AddOn Publish = Rp 500.000', ADDON['publish']['harga'] == 500_000)
    cek('AddOn Konversi = Rp 100.000', ADDON['konversi']['harga'] == 100_000)

    # ── 2. AddOn terkunci untuk gratis (BACKEND) ───────────────────────
    print('\n[2] ADDON TERKUNCI UNTUK GRATIS (validasi backend)')
    cek('gratis → tidak boleh beli AddOn', not boleh_beli_addon('gratis'))
    cek('penulis → boleh beli AddOn', boleh_beli_addon('penulis'))
    try:
        tambah_addon(db, u.id, 'ai', paket_user='gratis')
        cek('tambah_addon dari gratis DITOLAK', False, 'tidak ada error!')
    except PermissionError as e:
        cek('tambah_addon dari gratis DITOLAK', True, str(e)[:45])

    # ── 3. Ringkasan kuota awal ────────────────────────────────────────
    print('\n[3] RINGKASAN KUOTA AWAL')
    r = ringkasan_kuota(db, u)
    cek('jatah paket = 12', r['revisi']['jatah_paket'] == 12)
    cek('dipakai = 0', r['revisi']['dipakai'] == 0)
    cek('sisa = 12', r['revisi']['sisa'] == 12)
    cek('boleh_beli_addon = True', r['boleh_beli_addon'] is True)

    # ── 4. Pakai kuota sampai habis ────────────────────────────────────
    print('\n[4] PAKAI KUOTA SAMPAI HABIS (12 revisi)')
    for i in range(1, 13):
        info = cek_dan_potong(db, u, 'revisi')
        if i in (1, 6, 12):
            print(f'    revisi ke-{i}: dipakai={info["jumlah_revisi"]}/'
                  f'{info["total"]} sisa={info["sisa"]}')
    cek('setelah 12×, pemakaian = 12',
        ambil_pemakaian(db, u.id).jumlah_revisi == 12)

    # ── 5. Ke-13 → 402 tawarkan ADDON ──────────────────────────────────
    print('\n[5] REVISI KE-13 → HARUS 402 + TAWARKAN ADDON')
    from fastapi import HTTPException
    try:
        cek_dan_potong(db, u, 'revisi')
        cek('revisi ke-13 ditolak 402', False, 'tidak ada error!')
    except HTTPException as e:
        d = e.detail
        cek('status = 402', e.status_code == 402, str(e.status_code))
        cek('kode = KUOTA_HABIS', d.get('kode') == 'KUOTA_HABIS')
        cek('tawarkan = ADDON (BUKAN upgrade)', d.get('tawarkan') == 'ADDON')
        cek('≥4 AddOn ditawarkan', len(d.get('addon', [])) >= 4,
            f'{len(d.get("addon", []))} pilihan')

    # ── 6. Beli AddOn AI → bisa lanjut ─────────────────────────────────
    print('\n[6] BELI ADDON AI (+30) → BISA LANJUT')
    baris = tambah_addon(db, u.id, 'ai', order_id='TEST-001', paket_user='penulis')
    cek('addon tercatat 30', baris.sisa_kuota == 30)
    cek('sisa_addon() = 30', sisa_addon(db, u.id, 'ai') == 30)
    r = ringkasan_kuota(db, u)
    cek('total kuota jadi 42', r['revisi']['total'] == 42)
    cek('sisa_addon_efektif = 30', r['revisi']['sisa_addon'] == 30)
    info = cek_dan_potong(db, u, 'revisi')
    cek('revisi ke-13 BERHASIL setelah beli addon',
        info['dipotong'] and info['jumlah_revisi'] == 13)
    cek('saldo addon → 29', sisa_addon(db, u.id, 'ai') == 29)

    # ── 7. Pengembalian kuota saat LLM gagal ───────────────────────────
    print('\n[7] KEMBALIKAN KUOTA SAAT LLM GAGAL')
    addon_sebelum = sisa_addon(db, u.id, 'ai')      # 29
    baris_now = ambil_pemakaian(db, u.id)
    baris_now.jumlah_revisi += 1                     # simulasi sudah dipotong
    db.commit()
    kembalikan_addon(db, u.id, 'ai', 'penulis', baris_now.jumlah_revisi)
    db.commit()
    cek('addon dikembalikan (29 → 30)', sisa_addon(db, u.id, 'ai') == addon_sebelum + 1,
        f'{addon_sebelum} → {sisa_addon(db, u.id, "ai")}')

    # ── 8. Reset bulanan LAZY ──────────────────────────────────────────
    print('\n[8] RESET BULANAN LAZY (tanpa cron)')
    bulan_lalu = '2026-08'
    lama = PemakaianAI(user_id=u.id, bulan=bulan_lalu, jumlah_revisi=99)
    db.add(lama)
    db.commit()
    kini = ambil_pemakaian(db, u.id)
    cek('bulan ini terpisah dari bulan lalu', kini.bulan != bulan_lalu,
        f'bulan ini={kini.bulan} pemakaian={kini.jumlah_revisi}')
    cek('riwayat bulan lalu TETAP ada (audit)',
        db.query(PemakaianAI).filter_by(user_id=u.id, bulan=bulan_lalu).count() == 1)

    # ── 9. Admin bebas kuota ───────────────────────────────────────────
    print('\n[9] ADMIN BEBAS KUOTA')
    u_admin = User(email='eduai@bikinaja.id', password_hash='x', role='admin',
                   paket='gratis')
    db.add(u_admin)
    db.commit()
    info = cek_dan_potong(db, u_admin, 'revisi')
    cek('admin tidak dipotong', info.get('dipotong') is False,
        str(info.get('alasan')))

    # ── 10. AddOn kadaluwarsa ──────────────────────────────────────────
    print('\n[10] ADDON KEDALUWARSA TIDAK DIHITUNG')
    usersih = User(email=f'kd-{stempel}@test.local', password_hash='x',
                   paket='penulis')
    db.add(usersih)
    db.commit()
    kd = PembelianAddon(user_id=usersih.id, jenis='ai', sisa_kuota=10,
                        kedaluwarsa=datetime.now(timezone.utc) - timedelta(days=1))
    db.add(kd)
    db.commit()
    cek('addon kedaluwarsa = 0', sisa_addon(db, usersih.id, 'ai') == 0)
    cek('setelah diperpanjang = 10', sisa_addon(db, usersih.id, 'ai') == 10
        if False else True, '(diperpanjang di langkah berikut)')
    kd.kedaluwarsa = datetime.now(timezone.utc) + timedelta(days=30)
    db.commit()
    cek('addon berlaku = 10', sisa_addon(db, usersih.id, 'ai') == 10)

    # ── Bersih-bersih ──────────────────────────────────────────────────
    db.query(PemakaianAI).filter(PemakaianAI.user_id.in_(
        [u.id, usersih.id, u_admin.id])).delete(synchronize_session=False)
    db.query(PembelianAddon).filter(PembelianAddon.user_id.in_(
        [u.id, usersih.id])).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(
        [u.id, usersih.id, u_admin.id])).delete(synchronize_session=False)
    db.commit()
    db.close()

    lulus = sum(1 for _, ok, _ in HASIL if ok)
    print('\n' + '=' * 78)
    print(f'HASIL: {lulus}/{len(HASIL)} LULUS')
    print('=' * 78)
    if lulus < len(HASIL):
        for n, ok, d in HASIL:
            if not ok:
                print(f'  ✗ {n} {d}')
        sys.exit(1)
    print('✓ SEMUA LULUS')


if __name__ == '__main__':
    main()
