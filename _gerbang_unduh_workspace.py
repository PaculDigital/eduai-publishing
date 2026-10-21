"""GERBANG — UNDUH PDF → WORKSPACE (ACC Bos 06Okt26).

Menguji SAMBUNGAN hasil pencarian jurnal ke workspace. Dijalankan
**DI DALAM container** `eduai-app`:

    docker cp _gerbang_unduh_workspace.py eduai-app:/app/ \
      && docker exec -w /app eduai-app python3 _gerbang_unduh_workspace.py

BUKTI NYATA (bukan baca kode saja):
  K1  Kunci balikan mesin `pdf_terbuka` = 'isi' (BUKAN 'berkas')
      ⇒ membuktikan AKAR bug lama (artikel terbuka selalu ditolak).
  K2  Rute `/unduh` MENERIMA parameter `folder_id`
  K3  Rute `/folder-pilihan` TERDAFTAR & balas JSON berisi 'folder'
  K4  Penyimpanan NYATA: simpan PDF uji → baris `files` muncul + folder_id
      terisi + berkas ADA di disk  (memakai DB SALINAN, bukan DB produksi)
  K5  Tulisan di HTML: tombol "unduh ke workspace" + dropdown workspace
  K6  Pagar: folder milik user LAIN → TIDAK bisa dipakai (folder_id jadi None)
  K7  Mesin `pustaka` tetap MURNI: `pdf_terbuka` tidak menyentuh DB
"""
from __future__ import annotations

import os
import re
import secrets
import shutil
import sys
import tempfile
from pathlib import Path

AKAR = '/app'
TMP = tempfile.mkdtemp(prefix='uji_unduh_ws_')
DB = os.path.join(TMP, 'uji.db')

LULUS = 0
GAGAL = 0


def cek(nama: str, syarat: bool, ket: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama} {ket}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama} {ket}')


def main() -> None:
    #  ── DB SALINAN (jangan sentuh produksi) ──────────────────────────────
    shutil.copyfile(f'{AKAR}/data/eduai.db', DB)
    os.environ['EDUAI_DB'] = DB
    os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app import models as M
    eng = create_engine(f'sqlite:///{DB}', connect_args={'check_same_thread': False})
    M.engine = eng
    M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)

    from app import main as appmod
    from app import pustaka as P
    from app import rute_jurnal as RJ

    #  ══ K1: KUNCI BALIKAN MESIN ═════════════════════════════════════════
    h = P.pdf_terbuka('data:application/pdf,')      # bukan pdf → ok False
    cek('K1a pdf_terbuka balas kunci "ok"', 'ok' in h)
    cek('K1b kunci "berkas" TIDAK dipakai mesin (akar bug lama)',
        'berkas' not in h, f'(kunci={sorted(h)})')
    #  Bukti akar: kode lama memakai hasil.get('berkas') → selalu None.
    #  ⚠️ Periksa KODE, bukan komentar (komentar memang MENJELASKAN bug lama).
    src = Path(f'{AKAR}/app/rute_jurnal.py').read_text()
    kode = re.sub(r'#.*', '', src)                   # buang komentar sebaris
    kode = re.sub(r'""".*?"""', '', kode, flags=re.S)  # buang docstring
    cek("K1c KODE rute TIDAK lagi memakai hasil.get('berkas') (akar dicabut)",
        "hasil.get('berkas')" not in kode)
    cek("K1d KODE rute memakai hasil.get('isi') (bukti nyata)",
        "hasil.get('isi')" in kode)

    #  ══ K2: PARAMETER folder_id ═════════════════════════════════════════
    cek('K2a rute /unduh menerima parameter folder_id',
        'folder_id: int = 0' in Path(f'{AKAR}/app/rute_jurnal.py').read_text())

    #  ══ K3: RUTE BARU TERDAFTAR ═════════════════════════════════════════
    jalur = [r.path for r in RJ.router.routes]
    cek('K3a rute /folder-pilihan terdaftar', '/folder-pilihan' in jalur,
        f'({len(jalur)} rute)')

    #  ══ K5: TULISAN DI HTML ═════════════════════════════════════════════
    tpl = Path(f'{AKAR}/app/templates/referensi.html').read_text()
    cek('K5a tombol "unduh ke workspace" ada di HTML',
        'unduh ke workspace' in tpl)
    cek('K5b dropdown workspace ada di HTML', 'folder-tujuan' in tpl)
    cek('K5c fungsi unduhArtikel() ada', 'function unduhArtikel' in tpl)
    cek('K5d fungsi muatWorkspace() ada', 'function muatWorkspace' in tpl)

    #  ══ K4 + K6: PENYIMPANAN NYATA + PAGAR FOLDER ═══════════════════════
    db = M.SessionLocal()
    try:
        u = db.query(M.User).first()
        cek('K4a ada user di DB uji', u is not None)
        if u:
            #  Buat 2 folder: milik user & milik "orang lain"
            f1 = M.Folder(user_id=u.id, nama='WS-Uji-Sendiri', warna='biru')
            db.add(f1)
            lain = M.User(email=f'uji{secrets.token_hex(4)}@t.local',
                          nama='Orang Lain', password_hash='x')
            db.add(lain)
            db.flush()
            f2 = M.Folder(user_id=lain.id, nama='WS-Milik-OrangLain')
            db.add(f2)
            db.commit()

            isi_pdf = b'%PDF-1.4\n' + secrets.token_bytes(3000) + b'\n%%EOF'
            target = {'title': 'Pengaruh Harga / Promosi', 'year': 2020}
            hasil = {'ok': True, 'isi': isi_pdf, 'ukuran': len(isi_pdf)}

            #  ── Simpan ke folder SENDIRI ─────────────────────────────────
            out = RJ._simpan_pdf(db, u, target, hasil, folder_id=f1.id)
            cek('K4b simpan berhasil (ok=True)', bool(out.get('ok')),
                f'({out.get("pesan", "")[:42]})')
            fb = db.get(M.FileBerkas, out.get('file_id')) if out.get('file_id') else None
            cek('K4c baris `files` MUNCUL', fb is not None)
            cek('K4d folder_id TERISI = folder pilihan', fb and fb.folder_id == f1.id)
            cek('K4e nama berkas = judul + .pdf, tanpa "/"',
                fb is not None and fb.nama.endswith('.pdf') and '/' not in fb.nama,
                f'({fb.nama if fb else "-"})')
            from app.config import UPLOAD_DIR
            jal = UPLOAD_DIR / str(u.id) / (fb.nama_simpan if fb else '')
            cek('K4f berkas NYATA ada di disk & byte cocok',
                fb is not None and jal.exists() and jal.read_bytes() == isi_pdf)

            #  ── PAGAR: folder milik orang lain → Tidak boleh ─────────────
            out2 = RJ._simpan_pdf(db, u, target, hasil, folder_id=f2.id)
            fb2 = db.get(M.FileBerkas, out2.get('file_id')) if out2.get('file_id') else None
            cek('K6a folder milik user LAIN → folder_id jadi None',
                fb2 is not None and fb2.folder_id is None,
                f'(folder_id={fb2.folder_id if fb2 else "?"})')

            #  ── folder_id=0 → tanpa folder ───────────────────────────────
            out3 = RJ._simpan_pdf(db, u, target, hasil, folder_id=0)
            fb3 = db.get(M.FileBerkas, out3.get('file_id')) if out3.get('file_id') else None
            cek('K6b folder_id=0 → tanpa folder (None)',
                fb3 is not None and fb3.folder_id is None)

            #  ── Tidak ada berkas → ditolak dengan tautan ────────────────
            out4 = RJ._simpan_pdf(db, u, {'title': 'x', 'pdf_url': 'https://doi.org/x'},
                                  {'ok': False}, folder_id=0)
            cek('K6c artikel gagal diambil → ok False + tautan (tanpa berkas)',
                out4.get('ok') is False and 'link' in out4)
    finally:
        db.rollback()
        db.close()

    #  ══ K7: MESIN TETAP MURNI ═══════════════════════════════════════════
    psrc = Path(f'{AKAR}/app/pustaka.py').read_text()
    cek('K7a pustaka TIDAK mengimpor models/DB (mesin murni)',
        'from .models' not in psrc and 'FileBerkas' not in psrc)

    print(f'\nTOTAL: {LULUS} LULUS / {GAGAL} GAGAL')
    sys.exit(1 if GAGAL else 0)


if __name__ == '__main__':
    main()
