"""JALUR PENYUSUNAN BUKU — sambungan /buku/siapkan ke mesin (Lapis 3-4-5).

ATURAN YANG DIPATUHI (18 Okt 2026 + putusan token 07 Okt, diubah 29 Okt 2026):
  • KUOTA DIPOTONG SAAT GILIRAN PRODUKSI TIBA (`potong_banyak` lewat
    `on_mulai` di `susun_buku`) — tetap satu pintu di `susun()`, bukan
    di rute. Buku yang masih mengantre BELUM dipotong.
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
          kartu_jenis=None, outline_siaps=None, penulis=None, penelaah=None,
          tier=None):
    """Susun buku + potong kuota saat giliran tiba. Return dict hasil.

    Raise HTTPException 402/403 dari kuota kalau saldo kurang (tidak menyusun).

    outline_siaps: outline yang SUDAH disetujui user (Gate 1 referensi) —
    dipakai apa adanya (tetap divalidasi OB.periksa), tanpa membangun ulang.
    penulis: nama penulis pesanan (ganti nama profil bila diisi).
    penelaah: nama pakar penelaah (ditulis di Tentang Penulis + hasil).
    tier: paket Hemat/Normal/Full (None = perilaku lama); tier menang
    atas jumlah_bab untuk outline, dan diteruskan ke visuals.
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

    # ── KUOTA: DIPOTONG SAAT GILIRAN TIBA, bukan di depan ─────────────────
    #  Buku bisa mengantre (di antrean proses + antrean buku di mesin).
    #  Memotong di depan berarti token hangus menunggu — tidak adil.
    #  Jadi potong dititipkan ke `on_mulai`: dipanggil `susun_buku` TEPAT
    #  saat giliran tiba, sebelum satu kata ditulis. Tetap satu pintu di
    #  sini (bukan di rute). Gagal SEBELUM potong ⇒ tidak perlu refund.
    terpotong = False
    info_kotak = {}

    def _potong_saat_mulai():
        nonlocal terpotong
        info_kotak['info'] = kuota.potong_banyak(db, u, TOKEN_PER_BUKU)
        terpotong = True
        return info_kotak['info']

    fid = f"{int(time.time())}-{getattr(u, 'id', 0)}"
    keluar = folder_buku(fid)
    try:
        if lapor:
            lapor("Menyusun kerangka buku…")
        #  Outline disusun dari PILIHAN USER — bukan outline buku lain.
        if outline_siaps is not None:
            # Gate 1: outline yang SUDAH disetujui user di /buku/outline.
            # Tetap divalidasi OB.periksa di bawah (bentuk wajib sama).
            outline = outline_siaps
        elif kartu_jenis == 'buku-referensi':
            # Kerangka referensi TIDAK lewat OB (host tidak punya jenis
            # referensi): builder repo dengan 5 sub tetap N.1-N.5 per bab.
            from . import referensi_outline as _RO
            outline = _RO.susun_outline(judul, bidang, jumlah_bab, tier=tier)
        else:
            # Tier menang atas jumlah_bab (paket); tanpa tier, jumlah_bab lama dipakai.
            if tier:
                from tier_buku import jumlah_bab as _bab_dari_tier
                jumlah_bab = _bab_dari_tier(tier)
            outline = OB.susun_outline(judul, bidang, jenis,
                                       jumlah_bab=jumlah_bab)

        #  JANGAN mulai menulis kalau outline cacat — potong BELUM terjadi
        #  di titik ini (baru di `on_mulai` sesudah validasi), jadi gagal
        #  di sini tidak menyentuh token sama sekali.
        masalah = OB.periksa(outline)
        if masalah:
            raise ValueError(f"outline cacat: {masalah[:3]}")

        #  Cek awal point 1 (30 Okt 2026): OB memeriksa bentuk, cek_awal
        #  memeriksa struktur referensi (jumlah bab vs paket, 5 sub, kata
        #  kunci N.3/N.4, judul ganda). Potong BELUM terjadi di sini.
        try:
            from tier_buku import jumlah_bab as _bab_tier_susun
            _jumlah_harus_susun = _bab_tier_susun(tier) if tier else None
        except Exception:
            _jumlah_harus_susun = None
        from . import cek_awal as _CA
        _cek_outline = _CA.periksa_outline(outline, _jumlah_harus_susun)
        if not _cek_outline['lolos']:
            raise ValueError(
                'outline tidak lolos cek awal: '
                + '; '.join(_cek_outline['masalah'][:3]))

        if lapor:
            lapor(f"Menulis {len([k for k in outline if isinstance(k, int)])} bab…")
        #  Cek awal point 3 (30 Okt 2026): tiap bab dicek saat hasilnya
        #  terkumpul (hanya cek BARU R3/R4/surname; cek kata/sitasi/
        #  bentuk sudah di Lapisan 1). Hasilnya dipakai Lapisan 3c
        #  (repair) + dilapor langsung; gagal cek TIDAK menggagalkan
        #  buku di sini, gerbang final yang memutuskan.
        def _cek_bab(n, teks, folder_bab):
            try:
                from . import cek_awal as _CA_bab
                hasil_cek = _CA_bab.periksa_bab_awal(
                    n, teks, folder_bab, outline.get(n))
                if lapor:
                    for _m in hasil_cek['masalah']:
                        lapor(f'Cek awal {_m}')
                    for _c in hasil_cek['curiga'][:2]:
                        lapor(f'Catatan cek awal: {_c}')
                return hasil_cek
            except Exception as _e_cek:
                if lapor:
                    lapor(f'Cek awal BAB {n} dilewati: {_e_cek}')
                return {'masalah': [], 'curiga': []}

        hasil = S.susun_buku(judul, outline, jenis=jenis,
                             keluar_dir=keluar, lapor=lapor,
                             on_mulai=_potong_saat_mulai, tier=tier,
                             on_bab_selesai=_cek_bab)

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
        hasil['saldo'] = info_kotak.get('info')

        # ── RAKIT SATU .docx (ACC Bos 19 Okt 2026, opsi B) ────────────────
        #  Tanpa ini hasilnya cuma berkas bab terpisah — tidak bisa dibuka di
        #  OnlyOffice. Mesin assembly SUDAH ADA; ini PEMASANGAN, bukan mesin
        #  baru. Gagal rakit TIDAK membatalkan buku (bab sudah jadi & tersimpan):
        #  hasil tetap dikembalikan dengan `docx=None` + alasan jelas.
        if lapor:
            lapor("Merangkai buku jadi satu dokumen…")
        hasil['docx'] = None
        hasil['docx_alasan'] = ''
        # Glosarium + pustaka referensi disiapkan SEBELUM rakit (dipakai
        # juga blok sidecar di bawah untuk mengisi indeks). Jalur lain
        # tidak berubah: glosarium statis, pustaka dari rakit sendiri.
        glos, refs_rakit = {}, None
        if kartu_jenis == 'buku-referensi':
            # Gagal kumpul -> lanjut dengan glosarium/pustaka kosong;
            # gerbang referensi di bawah yang menilai jujur (bukan diam).
            try:
                from . import referensi_indeks as _RI
                glos, _diambil = _RI.kumpulkan_istilah(keluar, outline)
                refs_rakit = _RI.kumpulkan_pustaka(keluar, outline)
            except Exception:
                glos, refs_rakit = {}, None
        else:
            try:
                import buku_umum_pipeline as P
                glos = dict(getattr(P, 'GLOSARIUM', {}) or {})
            except Exception:
                glos = {}
        try:
            import buku_umum_assembly as ASM
            rakit = ASM.rakit(
                judul, keluar, outline,
                glosarium=glos,
                references=refs_rakit,
                penulis=(penulis or getattr(u, 'nama', '')
                         or getattr(u, 'nama_lengkap', '') or ''),
                institusi=(getattr(u, 'nama_kampus', '') or ''),
                penelaah=(penelaah or ''),
            )
            hasil['docx'] = rakit.get('docx')
            hasil['docx_hasil'] = rakit
            hasil['penelaah'] = penelaah or ''
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
                if kartu_jenis == 'buku-referensi':
                    # Indeks bernomor + gerbang referensi. Urutan sengaja:
                    # isi_nomor dulu (nomor TOC dari render), lalu teks
                    # halaman render ITU dipakai mengisi indeks, lalu
                    # gerbang membaca docx final. Gagal di sini = gagal
                    # teknis -> token kembali (pola except di bawah).
                    try:
                        from . import referensi_indeks as _RI
                        _hal = _sc.teks_halaman(hasil['docx'])
                        _nama_kandidat = _RI.kumpulkan_nama(refs_rakit)
                        _isi = _RI.isi_indeks(
                            hasil['docx'], _hal, glos,
                            _nama_kandidat)
                        if lapor:
                            lapor(f"Indeks terisi: { _isi['subjek']} subjek, "
                                  f"{_isi['nama']} nama "
                                  f"(kandidat {len(_nama_kandidat)}, "
                                  f"isi {_isi['isi_awal']}-{_isi['back_awal']})")
                            if _isi['nama'] == 0:
                                lapor("Peringatan indeks nama kosong "
                                      f"(kandidat {len(_nama_kandidat)})")
                            if _isi['subjek'] == 0:
                                lapor("Peringatan indeks subjek kosong "
                                      f"(glosarium {len(glos)})")
                    except Exception as e:
                        raise RuntimeError(f'indeks referensi gagal: {e}')
                    # Daftar Singkatan (29 Okt 2026): deterministik dari
                    # teks bab, ditulis bernomor halaman seperti indeks.
                    # Gagal di sini TIDAK menggagalkan buku (singkatan
                    # hanya peringatan gerbang Rw, bukan cek keras).
                    try:
                        from . import referensi_indeks as _RI
                        _sing = _RI.kumpulkan_singkatan(keluar, outline)
                        _n_sing = _RI.isi_singkatan(
                            hasil['docx'], _hal, _sing)
                        if lapor:
                            lapor(f"Daftar singkatan terisi: {_n_sing} "
                                  f"singkatan")
                    except Exception as e:
                        if lapor:
                            lapor(f"Daftar singkatan dilewati: {e}")
                    # Sapuan em dash sesudah singkatan (30 Okt 2026):
                    # entri singkatan disisipkan SESUDAH sapuan rakit(),
                    # sehingga 2 em dash di entri singkatan lolos di job
                    # 220. Sapuan di sini tidak fatal: bila gagal hanya
                    # dilapor, gerbang yang menilai hasil akhir.
                    try:
                        from docx import Document as _DocSapu
                        import buku_umum_assembly as _ASMSapu
                        _doc_sapu = _DocSapu(hasil['docx'])
                        _ASMSapu.bersihkan_em_dash_dokumen(_doc_sapu)
                        _doc_sapu.save(hasil['docx'])
                    except Exception as e:
                        if lapor:
                            lapor(f"Sapuan em dash dilewati: {e}")
                    #  Perbaiki dulu baru gagal (point 4, 30 Okt 2026):
                    #  gerbang gagal pada hal deterministik -> isi ulang
                    #  indeks + singkatan + sapuan sekali -> gerbang ulang.
                    #  _hal tetap sah: isi ulang hanya mengubah back matter.
                    #  Baru bila tetap gagal, buku gagal + refund seperti biasa.
                    def _gerbang_ref():
                        _sc.referensi(hasil['docx'])
                    def _perbaiki_ref():
                        from . import referensi_indeks as _RI_ref
                        _sing_ref = _RI_ref.kumpulkan_singkatan(keluar, outline)
                        _RI_ref.isi_indeks(hasil['docx'], _hal, glos, _nama_kandidat)
                        _RI_ref.isi_singkatan(hasil['docx'], _hal, _sing_ref)
                        from docx import Document as _DocRef
                        import buku_umum_assembly as _ASMRef
                        _doc_ref = _DocRef(hasil['docx'])
                        _ASMRef.bersihkan_em_dash_dokumen(_doc_ref)
                        _doc_ref.save(hasil['docx'])
                    from . import cek_awal as _CA_gate
                    _CA_gate.gerbang_dengan_perbaikan(_gerbang_ref, _perbaiki_ref, lapor=lapor)
                if kartu_jenis == 'book-chapter':
                    _sc.chapter(hasil['docx'])
                # Sukses: salinan pra-nomor tidak lagi diperlukan — hapus
                # supaya tidak menumpuk di disk (temuan review agen).
                # Gagal di atas (raise) membiarkannya tetap ada untuk
                # ditelusuri bersama _GAGAL.txt.
                try:
                    os.remove(hasil['docx'] + '.pra-nomor')
                except OSError:
                    pass  # pembersihan saja; buku sudah lolos
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
        #  HANYA refund kalau potong sudah terjadi (`terpotong`): gagal
        #  sebelum giliran (mis. saldo habis di `on_mulai`) tidak pernah
        #  memotong — refund di sana justru MEMBERI token gratis.
        if terpotong:
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
