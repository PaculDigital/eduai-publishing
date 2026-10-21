"""UJI HTTP E2E — rute pakai-ulang antar bab (13Okt26).

Pola resmi proyek (`_gerbang_e2e_unduh_http.py`): DB SALINAN (JANGAN DB
produksi) + login lewat `dependency_overrides[wajib_login_api]`.

Jalankan: docker cp ke container, jalankan DI DALAM container.
"""
import os
import sys
import tempfile

sys.path.insert(0, '/app')

HASIL = {'lulus': 0, 'gagal': 0}


def cek(nama, benar, ket=''):
    HASIL['lulus' if benar else 'gagal'] += 1
    print(f'  {"LULUS" if benar else "GAGAL"}  {nama}{("  " + ket) if ket else ""}')


def main():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app import jurnal as J
    from app.auth import wajib_login_api
    from app.main import app
    from app.models import Base, ProfilDokumen, get_db

    #  ── DB SALINAN (di memori) — JANGAN DB PRODUKSI ──
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    eng = create_engine(f'sqlite:///{tmp.name}',
                        connect_args={'check_same_thread': False})
    Base.metadata.create_all(eng)
    Sesi = sessionmaker(bind=eng)

    with Sesi() as db:
        u = __import__('app.models', fromlist=['User']).User(
            nama='Uji Bab', email='uji-bab@eduai.test', password_hash='x')
        db.add(u)
        db.commit()
        db.refresh(u)
        fid = u.id

        berkas = __import__('app.models', fromlist=['FileBerkas']).FileBerkas(
            nama='uji.docx', nama_simpan='uji.docx', ukuran=1000, user_id=u.id)
        db.add(berkas)
        db.commit()
        db.refresh(berkas)

        prof = ProfilDokumen(file_id=berkas.id, user_id=u.id)
        db.add(prof)
        db.commit()

        #  isi 2 bab dgn artikel
        data = J.data_kosong()
        data = J.tambah(data, 'BAB III', [
            {'title': 'Keaslian Streamer', 'authors': 'Susanti, A.',
             'year': '2024', 'journal': 'JMR', 'doi': '10.1000/a',
             'doi_status': 'verified'}], asal='ai')
        data = J.tambah(data, 'BAB I', [
            {'title': 'Latar Belakang', 'authors': 'X', 'year': '2020',
             'journal': 'J', 'doi': '10.1000/b',
             'doi_status': 'verified'}], asal='ai')
        prof.jurnal_json = __import__('json').dumps(data, ensure_ascii=False)
        db.commit()

        uid, fid_berkas = u.id, berkas.id
        kunci = J.kunci(J.daftar(data, 'BAB III')[0])

    def _db_uji():
        d = Sesi()
        try:
            yield d
        finally:
            d.close()

    app.dependency_overrides[get_db] = _db_uji
    app.dependency_overrides[wajib_login_api] = lambda: type(
        'U', (), {'id': uid, 'email': 'uji-bab@eduai.test', 'nama': 'Uji Bab'})()

    klien = TestClient(app)

    #  ── 1. rute GET /pakai-di hidup ──
    r = klien.get(f'/api/ai/v1/jurnal/pakai-di?file_id={fid_berkas}'
                  f'&bab=BAB%20III&kunci={kunci}')
    cek('1. rute GET /pakai-di hidup', r.status_code == 200, f'({r.status_code})')
    j = r.json() if r.status_code == 200 else {}
    cek('2. balasan punya pilihan_bab', bool(j.get('pilihan_bab')),
        f'({len(j.get("pilihan_bab") or [])} bab)')

    #  ── 3. bab asal ditandai `asal` ──
    pilihan = j.get('pilihan_bab') or []
    asal = [b for b in pilihan if b.get('asal')]
    cek('3. bab asal ditandai (tidak bisa dicentang)', len(asal) == 1,
        f'({(asal[0].get("bab") if asal else "-")})')

    #  ── 4. rute POST /pakai-di: pakai di BAB I ──
    r2 = klien.post(f'/api/ai/v1/jurnal/pakai-di?file_id={fid_berkas}'
                    f'&bab=BAB%20III&kunci={kunci}&ke_bab=BAB%20I')
    cek('4. rute POST /pakai-di hidup', r2.status_code == 200, f'({r2.status_code})')
    j2 = r2.json() if r2.status_code == 200 else {}
    cek('5. balasan sebut bab yang dipakai',
        'BAB I' in (j2.get('dipakai_di') or []), f'({j2.get("dipakai_di")})')

    #  ── 6. tersimpan sungguhan di DB (bukan cuma balasan) ──
    with Sesi() as db2:
        p2 = db2.query(ProfilDokumen).filter_by(file_id=fid_berkas).first()
        d2 = J.baca(p2)
        ada = any(J.kunci(a) == kunci for a in J.daftar(d2, 'BAB I'))
        cek('6. TERSIMPAN di DB sungguhan (bukan balasan palsu)', ada)
        #  asal tetap ada
        tetap = any(J.kunci(a) == kunci for a in J.daftar(d2, 'BAB III'))
        cek('7. tetap ada di bab asal (tidak terhapus)', tetap)

    #  ── 8. kunci kosong → ditolak jujur ──
    r3 = klien.post(f'/api/ai/v1/jurnal/pakai-di?file_id={fid_berkas}'
                    f'&bab=BAB%20III&kunci=&ke_bab=BAB%20I')
    cek('8. kunci kosong ditolak (400)', r3.status_code == 400, f'({r3.status_code})')

    app.dependency_overrides.clear()
    os.unlink(tmp.name)

    print()
    print(f'HASIL: {HASIL["lulus"]} LULUS · {HASIL["gagal"]} GAGAL')
    return 1 if HASIL['gagal'] else 0


if __name__ == '__main__':
    sys.exit(main())
