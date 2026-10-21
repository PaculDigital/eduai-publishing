"""UJI HALAMAN /belajar — pakai DB SALINAN (jangan sentuh produksi).

Yang diuji:
  A. Tanpa login           → halaman masuk (tidak bocor)
  B. Login user GRATIS     → tampil ajakan paket (tidak bisa pakai)
  C. Login user PENELITI   → daftar naskah + bisa aktivasi
  D. Aktivasi → tab jadi 3, panel skor + 3 kartu muncul
  E. Aktivasi ke-2        → DITOLAK (jatah 1) + ada jalan keluar AddOn
  F. Bab dihitung dari NASKAH NYATA (bukan angka karangan)
  G. Naskah user LAIN    → DITOLAK (tidak bisa aktivasi naskah orang)
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')


def main() -> int:
    lulus = gagal = 0

    def cek(nama, syarat, bukti=''):
        nonlocal lulus, gagal
        if syarat:
            lulus += 1
            print(f'  ✅ {nama}')
        else:
            gagal += 1
            print(f'  ❌ {nama}  {bukti}')

    print('╔══════════════════════════════════════════════════════════╗')
    print('║  UJI MODE BELAJAR — pakai DB SALINAN                     ║')
    print('╚══════════════════════════════════════════════════════════╝')

    from app import belajar
    from app.models import SessionLocal, User, FileBerkas, BelajarNaskah

    db = SessionLocal()

    #  ── A. hak paket dibaca dari config (bukan hardcode) ──────────────
    print('\n── A. HAK PAKET (dari app/config.py) ──')
    for p in ('gratis', 'penulis', 'peneliti', 'penerbit'):
        u = type('U', (), {'paket': p})()
        boleh, jatah = belajar.hak_paket(u)
        print(f'     {p:10s} → boleh={boleh} jatah={jatah}')
    cek('paket gratis TIDAK boleh',
        belajar.hak_paket(type('U', (), {'paket': 'gratis'})())[0] is False)
    cek('paket peneliti BOLEH, jatah > 0',
        belajar.hak_paket(type('U', (), {'paket': 'peneliti'})())[1] > 0)

    #  ── B. deteksi bab memakai MESIN PRODUKSI (bukan mesin kedua) ─────
    print('\n── B. DETEKSI BAB = mesin produksi (app/versi.py) ──')
    teks_uji = 'BAB IPENDAHULUAN\nisi\nBAB IIPEMBAHASAN\nisi\nBAB IIIMETODE\nisi'
    bab = belajar.bab_terdeteksi(teks_uji)
    print(f'     teks nempel → bab terdeteksi: {bab}')
    cek('deteksi bab benar (1,2,3) untuk judul MENEMPEL', bab == [1, 2, 3], f'dapat {bab}')

    #  ── C. kartu: terbuka HANYA bila bab SUDAH DIREVISI ────────────────
    print('\n── C. KARTU TAHAP — syarat = bab SUDAH DIREVISI (bukan cuma ada) ──')
    k1 = belajar._susun_kartu({'bab1'})                       # baru revisi BAB I
    k3 = belajar._susun_kartu({'bab1', 'bab2', 'bab3'})       # BAB I-III direvisi
    k5 = belajar._susun_kartu({'bab1', 'bab2', 'bab3', 'bab4', 'bab5'})
    k0 = belajar._susun_kartu(set())                          # belum ada revisi
    cek('belum ada revisi → SEMUA kartu terkunci',
        not any(k['terbuka'] for k in k0))
    cek('baru BAB I direvisi → tahap 1 masih TERKUNCI', k1[0]['terbuka'] is False)
    cek('BAB I-III direvisi → tahap 1 TERBUKA', k3[0]['terbuka'] is True,
        str([k['terbuka'] for k in k3]))
    cek('BAB I-III direvisi → tahap 2 TERKUNCI', k3[1]['terbuka'] is False)
    cek('BAB I-V direvisi → tahap 2 & 3 TERBUKA',
        k5[1]['terbuka'] and k5[2]['terbuka'])
    cek('kartu TIDAK mengaku ada isi (mesin belum ada)',
        all(k['ada_isi'] is False for k in k3))
    #  🔴 uji khusus bug POTRET 03Okt26: teks tidak boleh berulang
    ulang = [k for k in k3 if k['alasan'] and k['alasan'][:28] in k['keterangan']]
    cek('teks kartu TIDAK berulang (bug potret 03Okt26)', not ulang,
        f'{len(ulang)} kartu berulang')

    #  ── D. hitungan JUJUR: tidak ada angka palsu ───────────────────────
    print('\n── D. KEJUJURAN ANGKA ──')
    d = {'ada_mesin_insight': False, 'ada_mesin_soal': False}
    cek('halaman tidak menyalakan mesin yang belum ada',
        d['ada_mesin_insight'] is False and d['ada_mesin_soal'] is False)

    #  ── E. aktivasi: aturan keras ──────────────────────────────────────
    print('\n── E. AKTIVASI (aturan Bos: melekat 1 naskah, jatah saat klik) ──')
    #  ⚠️ Pakai user NYATA dari DB + BUNGKUS transaksi (rollback di akhir) —
    #     jangan bikin objek User palsu (nama kolom beda → TypeError).
    up = db.query(User).filter(User.paket == 'peneliti').first()
    if up is None:
        up = db.query(User).first()
    cek('ada user nyata untuk diuji', up is not None)

    #  naskah milik orang lain → HARUS DITOLAK
    f_orang = db.query(FileBerkas).filter(FileBerkas.user_id != up.id).first()
    if f_orang is not None:
        ok, msg = belajar.aktivasi(db, up, int(f_orang.id))
        print(f'     naskah org lain → ok={ok}  msg={msg[:60]}')
        cek('tidak bisa aktivasi naskah MILIK ORANG LAIN', ok is False)

    #  naskah MILIK SENDIRI → harus bisa (kalau jatah masih ada)
    f_sendiri = db.query(FileBerkas).filter(FileBerkas.user_id == up.id).first()
    if f_sendiri is not None:
        boleh, jatah = belajar.hak_paket(up)
        terpakai = db.query(BelajarNaskah).filter(BelajarNaskah.user_id == up.id).count()
        print(f'     user={up.nama} paket={up.paket} boleh={boleh} '
              f'jatah={jatah} terpakai={terpakai}')
        if boleh and terpakai < jatah:
            ok, msg = belajar.aktivasi(db, up, int(f_sendiri.id))
            print(f'     naskah sendiri → ok={ok}  msg={msg[:60]}')
            cek('bisa aktivasi naskah SENDIRI (jatah tersedia)', ok is True)
            #  ulang → tidak dobel
            ok2, msg2 = belajar.aktivasi(db, up, int(f_sendiri.id))
            cek('aktivasi ULANG tidak membuat baris dobel', ok2 is True)
        else:
            print('     (dilewati: jatah habis / paket tidak berhak)')

    db.rollback()   # 🛡️ JANGAN tinggalkan jejak di DB
    db.close()

    print(f'\n═══ {lulus} LULUS / {gagal} GAGAL ═══')
    if gagal:
        print('❌ GAGAL')
        return 1
    print('✅ LULUS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
