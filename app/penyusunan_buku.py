"""JALUR PENYUSUNAN BUKU — sambungan /buku/siapkan ke mesin (Lapis 3-4-5).

ATURAN YANG DIPATUHI (Bos 18 Okt 2026 + putusan token 07 Okt):
  • KUOTA DIPOTONG DI DEPAN (`potong_banyak`), bukan setelah kerja.
  • GAGAL TEKNIS → token kembali UTUH (`kembalikan_banyak`).
    GAGAL MUTU (hasil jelek tapi jadi) → TIDAK kembali: itu hasil, bukan error.
  • HASIL JADI BERKAS DULU, layar cuma membaca. Tekan Back tidak menghilangkan
    hasil (anti-rugi, pola yang sama dengan konversi artikel).
  • NOL dompet baru, NOL mesin paralel: memakai `kuota` + `buku_umum_pipeline`
    yang sudah ada dan sudah bergerbang.

Dipakai oleh rute `POST /buku/mulai` (mode susun) di app/main.py.
"""
import os
import sys
import time
import shutil

#  Token per buku. SATU angka, jangan disebar — supaya gampang diaudit.
#  Alasan: 1 buku = 6 bab (umum) / 3 bab (anak) / 5 bab (pendidikan),
#  satu bab = ~6 menit LLM + 3 varian ilustrasi. Disamakan per BUKU, bukan
#  per bab, supaya user tidak dikejutkan hitungan berubah-ubah.
TOKEN_PER_BUKU = 1


def _pastikan_modul():
    """Modul mesin ada di /opt/data (host). Di container: /app."""
    for p in ('/opt/data', '/app'):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def _daftarkan_berkas(db, u, docx_path, judul) -> int:
    """Salin .docx ke folder user + daftar di tabel `files`. Return file_id.

    Pola SAMA dengan `app/dokumen_baru.py:87` (sumber: salin ke
    `UPLOAD_DIR/<user_id>/` dengan nama acak, lalu `FileBerkas(...)`).
    Dipakai supaya `/edit/{fid}` OnlyOffice bisa membuka hasil buku.

    ⚠️ Kenapa DISALIN, bukan dipindah: `docx_path` ada di folder hasil buku
    (dipakai user untuk melihat semua bab). Kalau dipindah, folder hasil
    kehilangan dokumennya. Kalau disalin, ada 2 berkas — ini disengaja:
    folder hasil = arsip kerja, tabel `files` = dokumen yang bisa diedit.
    """
    import secrets
    import shutil
    from app.config import UPLOAD_DIR
    from app.models import FileBerkas

    #  Nama tampil: dari JUDUL buku, bukan nama berkas teknis.
    #  ⚠️ JEBAKAN TERUKUR 19 Okt 2026: kolom `nama` = String(255), tetapi
    #     SQLite TIDAK menegakkan panjang kolom — nama 400 karakter MASUK
    #     tanpa galat. Di MySQL/Postgres itu akan ditolak (atau terpotong
    #     diam-diam). Jadi panjang WAJIB dijaga di kode, jangan bergantung DB.
    nama_asli = (judul or 'Buku').strip() or 'Buku'
    nama_asli = nama_asli.replace('/', '-').replace('\\', '-')[:120]
    if not nama_asli:
        nama_asli = 'Buku'
    if not nama_asli.lower().endswith('.docx'):
        nama_asli += '.docx'
    if len(nama_asli) > 255:
        raise ValueError(f'nama berkas terlalu panjang: {len(nama_asli)} karakter')

    dir_unggah = UPLOAD_DIR / str(u.id)
    dir_unggah.mkdir(parents=True, exist_ok=True)
    nama_simpan = f'{secrets.token_hex(8)}.docx'
    tujuan = dir_unggah / nama_simpan
    shutil.copyfile(docx_path, tujuan)

    fb = FileBerkas(
        user_id=u.id,
        nama=nama_asli,
        nama_simpan=nama_simpan,
        ukuran=tujuan.stat().st_size,
        tipe=('application/vnd.openxmlformats-officedocument'
              '.wordprocessingml.document'),
    )
    try:
        db.add(fb)
        db.commit()
        db.refresh(fb)
    except Exception:
        db.rollback()
        #  Jangan tinggalkan berkas yatim yang tidak tercatat di `files`.
        try:
            tujuan.unlink(missing_ok=True)
        except Exception:                                        # noqa: BLE001
            pass
        raise
    return int(fb.id)


def siap():
    """(bool, alasan) — jangan janjikan proses kalau mesin tidak ada."""
    _pastikan_modul()
    try:
        import penyusun_buku as S
    except Exception as e:
        return False, f"penyusun tidak bisa dimuat: {type(e).__name__}: {e}"
    return S.apakah_bisa()


def folder_buku(fid_unik):
    """Folder hasil per buku. SATU tempat, gampang dicari."""
    dasar = os.environ.get('BUKU_DIR', '/opt/data/buku_hasil')
    return os.path.join(dasar, str(fid_unik))


def susun(db, u, judul, bidang, untuk, jenis, jumlah_bab=None, lapor=None,
          kartu_jenis=None):
    """Susun buku + potong kuota di depan. Return dict hasil.

    Raise HTTPException 402/403 dari kuota kalau saldo kurang (tidak menyusun).
    """
    _pastikan_modul()
    import outline_buku as OB
    import penyusun_buku as S
    from . import kuota

    bisa, alasan = S.apakah_bisa()
    if not bisa:
        raise RuntimeError(alasan)

    if not (judul or '').strip():
        raise ValueError("Judul buku belum diisi")

    # ── GERBANG KUOTA: TOLAK DI DEPAN, sebelum satu kata ditulis ──────────
    info = kuota.potong_banyak(db, u, TOKEN_PER_BUKU)

    fid = f"{int(time.time())}-{getattr(u, 'id', 0)}"
    keluar = folder_buku(fid)
    try:
        if lapor:
            lapor("Menyusun kerangka buku…")
        #  Outline disusun dari PILIHAN USER — bukan outline buku lain.
        outline = OB.susun_outline(judul, bidang, jenis,
                                   jumlah_bab=jumlah_bab)

        #  JANGAN mulai menulis kalau outline cacat — token sudah dipotong,
        #  jadi cacat di sini WAJIB mengembalikan token.
        masalah = OB.periksa(outline)
        if masalah:
            raise ValueError(f"outline cacat: {masalah[:3]}")

        if lapor:
            lapor(f"Menulis {len([k for k in outline if isinstance(k, int)])} bab…")
        hasil = S.susun_buku(judul, outline, jenis=jenis,
                             keluar_dir=keluar, lapor=lapor)

        #  Hasil HARUS benar-benar ada di disk — bukan cuma diklaim.
        #
        #  🚨 AKAR NYATA 20 Okt 2026 (terbukti lewat uji jalur layar):
        #  `b['file']` cuma NAMA (`bab1.txt`), sedangkan `susun_buku()`
        #  menyimpannya di `bab{n}/bab{n}.txt` (di DALAM folder bab).
        #  Pemeriksaan lama mencari `…/bab1.txt` di akar folder buku ⇒ TIDAK
        #  PERNAH ketemu ⇒ buku yang SUDAH JADI (2.078 & 2.155 kata + diagram
        #  Jev + tabel + ilustrasi) DIBUANG dan dilaporkan "tidak satu pun
        #  berkas bab tersimpan". Salah ALAMAT, bukan mesin rusak.
        #
        #  Perbaikan: coba DUA kemungkinan (di dalam folder bab DULU), dan
        #  kembalikan path LENGKAP supaya pemanggil lain tak salah lagi.
        def _path_bab(n, b):
            nama = (b or {}).get('file') or f'bab{n}.txt'
            for calon in (os.path.join(keluar, f'bab{n}', nama),   # bentuk NYATA
                          os.path.join(keluar, nama)):              # bentuk lama
                if os.path.exists(calon):
                    return calon
            return None

        _ketemu = {n: _path_bab(n, b) for n, b in hasil['bab'].items()}
        bab_ada = [n for n, p in _ketemu.items() if p]
        if not bab_ada:
            raise RuntimeError(
                "tidak satu pun berkas bab tersimpan; dicari di: "
                + ", ".join(sorted({os.path.dirname(p or '')
                                    for p in _ketemu.values()}) or {'-'}))
        #  Simpan path LENGKAP — pemanggil tidak perlu menebak letaknya.
        for n in bab_ada:
            hasil['bab'][n]['path'] = _ketemu[n]
        hasil['bab_ada'] = bab_ada
        hasil['token'] = TOKEN_PER_BUKU
        hasil['saldo'] = info

        # ── RAKIT SATU .docx (ACC Bos 19 Okt 2026, opsi B) ────────────────
        #  Tanpa ini hasilnya cuma berkas bab terpisah — tidak bisa dibuka di
        #  OnlyOffice. Mesin assembly SUDAH ADA; ini PEMASANGAN, bukan mesin
        #  baru. Gagal rakit TIDAK membatalkan buku (bab sudah jadi & tersimpan):
        #  hasil tetap dikembalikan dengan `docx=None` + alasan jelas.
        if lapor:
            lapor("Merangkai buku jadi satu dokumen…")
        hasil['docx'] = None
        hasil['docx_alasan'] = ''
        try:
            import buku_umum_assembly as ASM
            glos = {}
            try:
                import buku_umum_pipeline as P
                glos = dict(getattr(P, 'GLOSARIUM', {}) or {})
            except Exception:
                glos = {}
            rakit = ASM.rakit(
                judul, keluar, outline,
                glosarium=glos,
                penulis=(getattr(u, 'nama', '') or getattr(u, 'nama_lengkap', '') or ''),
                institusi=(getattr(u, 'nama_kampus', '') or ''),
            )
            hasil['docx'] = rakit.get('docx')
            hasil['docx_hasil'] = rakit
            if lapor:
                lapor(f"Buku jadi: {os.path.basename(hasil['docx'])} "
                      f"({rakit.get('ukuran_byte', 0) // 1024} KB, "
                      f"{len(rakit.get('bab_dirakit', []))} bab)")
        except Exception as e:
            hasil['docx_alasan'] = f"{type(e).__name__}: {e}"
            if lapor:
                lapor(f"Bab sudah jadi, tapi perakitan dokumen gagal: {e}")

        # ── GERBANG PER BUKU VIA SIDECAR (Opsi B2, 28 Okt 2026) ──────────
        #  Buku web selama ini TIDAK diperiksa apa-apa. Sekarang, sesudah
        #  rakit dan SEBELUM didaftar ke files:
        #   1. isi_nomor_toc: PERBAIKAN — nomor TOC kosong diisi dari render
        #      nyata. Gagal total (exit 2) = gagal teknis -> token kembali
        #      (pola except di bawah). Sebagian hilang (exit 1) = lanjut
        #      dengan catatan (filler bukan gerbang penolak).
        #   2. ukur: judul bab HARUS tampil di rendernya sendiri; hilang =
        #      buku cacat -> gagal (raise -> token kembali).
        #   3. chapter gate: HANYA untuk kartu book-chapter.
        #  Sidecar mati/kunci salah = gagal teknis (buku tidak diterbitkan
        #  tanpa gerbang; token kembali). Gerbang jenis ISI penuh (aturan
        #  substansi v1.1) tetap di jalur operator — web tidak punya spec
        #  JSON, jadi yang diperiksa di sini adalah identitas kartu
        #  (di route: siap + id_dokumen + porsi_alat) + berkas jadi.
        if hasil.get('docx') and os.path.exists(hasil['docx']):
            from . import sidecar_buku as _sc
            try:
                bernomor, terisi, hilang_toc = _sc.isi_nomor(hasil['docx'])
                if hilang_toc:
                    hasil['toc_hilang'] = hilang_toc
                    if lapor:
                        lapor('Nomor TOC belum terisi: ' +
                              ', '.join(hilang_toc))
                os.replace(hasil['docx'], hasil['docx'] + '.pra-nomor')
                os.replace(bernomor, hasil['docx'])
                hasil['toc_terisi'] = terisi
                judul_bab = [outline[n]['title'] for n in outline
                             if isinstance(n, int) and outline[n].get('title')]
                _peta, hilang_ukur, _total = _sc.ukur(hasil['docx'],
                                                       judul_bab)
                if hilang_ukur:
                    raise RuntimeError(
                        'judul bab tidak tampil di render: ' +
                        ', '.join(hilang_ukur))
                hasil['ukur_peta'] = _peta
                if kartu_jenis == 'book-chapter':
                    _sc.chapter(hasil['docx'])
            except _sc.SidecarGagal as e:
                raise RuntimeError(f'gerbang buku gagal: {e}')

        # ── DAFTARKAN .docx KE TABEL `files` (ACC Bos 19 Okt 2026) ────────
        #  Tanpa ini dokumen ADA di disk tapi TIDAK bisa dibuka di OnlyOffice
        #  (`/edit/{fid}` mencari baris `FileBerkas`). Ini PEMASANGAN ke jalur
        #  yang sudah ada — pola SAMA dengan `app/dokumen_baru.py` (salin ke
        #  folder user + daftar di `files`), bukan mesin baru.
        #
        #  ⚠️ ATURAN: kalau pendaftaran gagal, JANGAN tinggalkan berkas yatim
        #     yang tidak tercatat (dokumennya sudah dihapus dari folder hasil
        #     supaya tidak jadi sampah ganda). Bab tetap aman di disk.
        hasil['file_id'] = None
        hasil['file_alasan'] = ''
        if hasil.get('docx') and os.path.exists(hasil['docx']):
            try:
                hasil['file_id'] = _daftarkan_berkas(db, u, hasil['docx'], judul)
            except Exception as e:
                hasil['file_alasan'] = f"{type(e).__name__}: {e}"
                if lapor:
                    lapor(f"Dokumen jadi, tapi gagal didaftarkan ke Naskah Saya: {e}")

        return hasil

    except Exception as e:
        # ── ANTI-RUGI: gagal TEKNIS → token kembali UTUH ──────────────────
        #  Folder setengah jadi TIDAK dihapus (biar bisa ditelusuri), tapi
        #  ditandai GAGAL supaya tidak dikira buku selesai.
        try:
            kuota.kembalikan_banyak(db, u, TOKEN_PER_BUKU)
        except Exception:
            pass
        try:
            os.makedirs(keluar, exist_ok=True)
            with open(os.path.join(keluar, '_GAGAL.txt'), 'w') as f:
                f.write(f"GAGAL: {type(e).__name__}: {e}\n")
        except Exception:
            pass
        raise
