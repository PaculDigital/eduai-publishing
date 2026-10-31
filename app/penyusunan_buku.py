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



#  -- RETRY PER BAB A1 (30 Okt 2026, job 221) ------------------------------
#  Latar: provider kosong membuat teks bab None, lalu word_count(None)
#  crash AttributeError dan job gagal total padahal bab lain sudah jadi.
#  Aturan baru, hanya di wilayah loop bab ini:
#    1. Satu bab gagal (exception atau teks None/kosong) diulang BAB ITU
#       SAJA, bukan dari bab 1.
#    2. Maksimal 3 pengulangan per bab, jadi total 4 percobaan.
#       Backoff antar percobaan: 5 detik, 15 detik, 30 detik.
#       Urutan backoff sengaja membesar supaya provider yang sedang
#       kosong punya waktu pulih, tanpa menunggu berjam-jam.
#    3. Bab None atau kosong adalah percobaan GAGAL yang bisa di-retry,
#       bukan crash dan bukan lolos diam-diam.
#    4. Resume dari checkpoint: bab yang sudah tercatat selesai di
#       checkpoint.json dilewati, eksekutornya tidak dipanggil lagi.
#  Catatan jujur: loop paralel nyata tetap di modul host penyusun_buku
#  (di luar repo git ini). Di repo ini, retry produksi diwujudkan oleh
#  loop di susun() di bawah: pemanggilan ulang S.susun_buku dengan
#  ulang=1 memakai checkpoint host yang sama, sehingga bab yang sudah
#  selesai dilewati host dan hanya bab yang belum selesai yang
#  dieksekusi lagi. Helper di bawah ini adalah logika murni yang sama,
#  dipakai uji mock tanpa LLM. Helper berjalan berurutan, bukan paralel,
#  karena tujuannya membuktikan semantik retry dan resume, bukan
#  kecepatan paralel.
RETRY_BAB_BACKOFF_DETIK = (5, 15, 30)
RETRY_BAB_ULANG_MAKS = 3
RETRY_BAB_PERCOBAAN_MAKS = 1 + RETRY_BAB_ULANG_MAKS


class BabGagal(RuntimeError):
    """Gagal bersih per bab sesudah semua percobaan habis.

    Subclass RuntimeError supaya jalur except refund yang sudah ada di
    susun() menangkapnya sebagai gagal teknis, bukan sebagai crash
    mentah seperti AttributeError.
    """


def hitung_kata_aman(teks):
    """Hitung kata tanpa pernah crash pada teks None.

    Penjaga .split(): teks yang bukan str (termasuk None) dihitung 0
    kata. Pemanggil yang memakai fungsi ini tidak perlu try AttributeError.
    """
    if not isinstance(teks, str):
        return 0
    return len(teks.split())


def periksa_teks_bab(n, teks):
    """Validasi hasil satu percobaan bab. Return jumlah kata.

    Raise BabGagal bila teks None atau kosong. Ini yang membuat None
    menjadi retryable, bukan crash dan bukan lolos diam-diam.
    """
    if teks is None or (isinstance(teks, str) and not teks.strip()):
        raise BabGagal(
            'BAB %s kosong (teks None atau kosong dari provider)' % n)
    if not isinstance(teks, str):
        raise BabGagal(
            'BAB %s hasil bukan teks: %s' % (n, type(teks).__name__))
    return hitung_kata_aman(teks)


def baca_checkpoint_selesai(folder):
    """Nomor bab yang sudah selesai menurut checkpoint.json di folder.

    Format checkpoint host: {'babs': {'1': {'status': 'done',
    'words': 123}, ...}}. Kunci str dan int sama-sama diterima. Hanya
    status done dengan words > 0 yang dilewati, sama seperti logika
    lewati di modul host. Berkas hilang, rusak, atau bentuk lain
    menghasilkan set kosong, bukan crash, supaya run tetap jalan dari
    awal.
    """
    import json
    selesai = set()
    if not folder:
        return selesai
    path = os.path.join(folder, 'checkpoint.json')
    try:
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        return selesai
    babs = data.get('babs') if isinstance(data, dict) else None
    if not isinstance(babs, dict):
        return selesai
    for kunci, info in babs.items():
        try:
            n = int(kunci)
        except (TypeError, ValueError):
            continue
        if isinstance(info, dict) and info.get('status') == 'done':
            try:
                kata = info.get('words', 0) or 0
            except Exception:
                kata = 0
            if kata > 0:
                selesai.add(n)
    return selesai


def jalankan_bab_dengan_retry(n, eksekutor, tidur=None, lapor=None):
    """Jalankan satu bab dengan retry. Return teks bab yang lolos.

    eksekutor(n) mengembalikan teks bab, atau raise exception, atau
    mengembalikan None. None, teks kosong, dan exception apa pun
    (termasuk AttributeError dari .split() atas None di jalur lama)
    dihitung satu percobaan gagal. Sesudah percobaan terakhir, raise
    BabGagal bersih yang menyebut galat terakhir, bukan galat mentah.
    tidur: fungsi(detik), default time.sleep. Uji mock menyuntik
    perekam supaya tidak menunggu betulan.
    """
    if tidur is None:
        tidur = time.sleep
    galat_terakhir = None
    for percobaan in range(1, RETRY_BAB_PERCOBAAN_MAKS + 1):
        try:
            teks = eksekutor(n)
            periksa_teks_bab(n, teks)
            return teks
        except BabGagal as e:
            galat_terakhir = e
        except Exception as e:
            galat_terakhir = e
        if percobaan >= RETRY_BAB_PERCOBAAN_MAKS:
            break
        jeda = RETRY_BAB_BACKOFF_DETIK[percobaan - 1]
        if lapor:
            try:
                lapor('BAB %s percobaan %s gagal (%s), ulang sesudah %s detik'
                      % (n, percobaan, galat_terakhir, jeda))
            except Exception:
                pass
        tidur(jeda)
    nama_galat = type(galat_terakhir).__name__ if galat_terakhir is not None else 'tanpa galat'
    raise BabGagal(
        'BAB %s gagal sesudah %s percobaan, galat terakhir: %s: %s'
        % (n, RETRY_BAB_PERCOBAAN_MAKS, nama_galat, galat_terakhir))


def jalankan_semua_bab(nomor_bab, eksekutor, folder_checkpoint=None,
                       tidur=None, lapor=None):
    """Jalankan daftar bab berurutan dengan retry per bab dan resume.

    Bab yang tercatat selesai di checkpoint dilewati tanpa memanggil
    eksekutornya. Bab lain dijalankan lewat jalankan_bab_dengan_retry,
    sehingga gagal 2x lalu berhasil tidak mengulang bab lain, dan bab
    yang gagal total menggagalkan run dengan BabGagal bersih pada bab
    itu (pemanggil di atas yang memutuskan refund).
    Return dict {nomor: teks} hanya untuk bab yang dijalankan di run ini.
    """
    selesai = baca_checkpoint_selesai(folder_checkpoint)
    hasil = {}
    for n in nomor_bab:
        if n in selesai:
            if lapor:
                try:
                    lapor('BAB %s sudah ada di checkpoint, dilewati' % n)
                except Exception:
                    pass
            continue
        hasil[n] = jalankan_bab_dengan_retry(n, eksekutor, tidur=tidur,
                                             lapor=lapor)
    return hasil


def _peta_sumber_pustaka(db, job_kode, outline):
    """Bangun {teks_pustaka: [sumber]} dari snapshot beku pra-panen.

    Dipakai tag [Sumber: X] di Daftar Pustaka DOCX. Fail-soft: bila
    DB atau snapshot gagal dibaca, kembalikan {} (tanpa tag, tanpa
    gagal), supaya perakitan buku tidak pernah gagal hanya karena
    tag sumber. Casing sumber disimpan apa adanya dari DB (tidak
    dinormalisasi di sini).
    """
    try:
        from . import pra_panen as _PP
        import verifikasi_sitasi as _VS
        _peta = {}
        for _n in sorted(n for n in (outline or {}) if isinstance(n, int)):
            for _row in _PP.ambil_snapshot(db, job_kode, _n):
                _sumber = (_row.get("sumber") or
                           (_row.get("ref_dict") or {}).get("source") or "").strip()
                if not _sumber:
                    continue
                _teks = _VS.format_apa(_row.get("ref_dict") or {})
                if not _teks:
                    continue
                _daftar = _peta.setdefault(_teks, [])
                if _sumber not in _daftar:
                    _daftar.append(_sumber)
        return _peta
    except Exception:
        return {}


def susun(db, u, judul, bidang, untuk, jenis, jumlah_bab=None, lapor=None,
          kartu_jenis=None, outline_siaps=None, penulis=None, penelaah=None,
          tier=None, kode=None):
    """Susun buku + potong kuota saat giliran tiba. Return dict hasil.

    Raise HTTPException 402/403 dari kuota kalau saldo kurang (tidak menyusun).

    outline_siaps: outline yang SUDAH disetujui user (Gate 1 referensi) —
    dipakai apa adanya (tetap divalidasi OB.periksa), tanpa membangun ulang.
    penulis: nama penulis pesanan (ganti nama profil bila diisi).
    penelaah: nama pakar penelaah (ditulis di Tentang Penulis + hasil).
    tier: paket Hemat/Normal/Full (None = perilaku lama); tier menang
    atas jumlah_bab untuk outline, dan diteruskan ke visuals.
    kode: kode proses (untuk job_kode snapshot pra-panen). Bila None
    (pemanggil lama), dipakai fid folder sebagai job_kode.
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
    _job_kode = kode or fid
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

        # Pra-panen Fase 1 (31 Okt 2026): hanya buku-referensi.
        # Panen TIDAK jalan di sini (sebelum antrean host), supaya
        # token tidak dipotong selagi mengantre. Panen jalan di
        # on_mulai (_mulai_dan_panen), tepat saat giliran tiba:
        # potong dulu, lalu panen, lalu bekukan. Gagal gerbang
        # adalah ValueError (subclass GagalPraPanen), jadi loop
        # retry di bawah TIDAK mengulanginya, dan except di bawah
        # mengembalikan token lewat jalur refund yang sudah ada.
        _is_referensi = (kartu_jenis == 'buku-referensi'
                         or jenis == 'referensi')
        _refs_holder = {}

        def _mulai_dan_panen():
            _potong_saat_mulai()
            from . import pra_panen as _PP
            _refs_holder['refs'] = _PP.panen_semua(
                db, _job_kode, bidang, outline, lapor=lapor)
            # Gas 31 Okt 2026 12:03, butir 1: baris snapshot per bab
            # dibaca dari DB sesudah panen dan dibekukan di holder,
            # supaya penulis membaca daftar yang sama dengan gerbang
            # final, bukan daftar yang berubah selama menulis.
            # Gagal baca di sini tidak menggagalkan panen, pipeline
            # menurunkan baris dari refs bila holder kosong.
            try:
                _snapshot_rows = {}
                for _n_snap in (n for n in outline
                                if isinstance(n, int)):
                    _snapshot_rows[_n_snap] = _PP.ambil_snapshot(
                        db, _job_kode, _n_snap)
                _refs_holder['snapshot_rows'] = _snapshot_rows
            except Exception:
                _refs_holder['snapshot_rows'] = {}

        if lapor:
            lapor(f"Menulis {len([k for k in outline if isinstance(k, int)])} bab…")
        #  Cek awal point 3 (30 Okt 2026): tiap bab dicek saat hasilnya
        #  terkumpul (hanya cek BARU R3/R4/surname; cek kata/sitasi/
        #  bentuk sudah di Lapisan 1). Hasilnya dipakai perbaikan
        #  bedah struktural + dilapor langsung; gagal cek TIDAK
        #  menggagalkan buku di sini, gerbang final yang memutuskan.
        def _cek_bab(n, teks, folder_bab):
            try:
                from . import cek_awal as _CA_bab
                #  Penjaga None A1: teks None diperlakukan sebagai teks
                #  kosong oleh cek, bukan crash .split() di jalur cek.
                #  Gas 31 Okt 2026 12:03, butir 4: buku-referensi
                #  mengoper baris snapshot bab itu, supaya metrik
                #  cek per bab sama dengan gerbang final (per baris
                #  snapshot, bukan per kata surname). Gagal baca
                #  snapshot jatuh ke None, metode kata lama dipakai,
                #  cek tidak pernah crash karena snapshot.
                _snapshot_rows_cek = None
                if _is_referensi:
                    try:
                        from . import pra_panen as _PP_cek
                        _snapshot_rows_cek = _PP_cek.ambil_snapshot(
                            db, _job_kode, n)
                    except Exception:
                        _snapshot_rows_cek = None
                hasil_cek = _CA_bab.periksa_bab_awal(
                    n, teks or '', folder_bab, outline.get(n),
                    snapshot_rows=_snapshot_rows_cek)
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

        #  Retry A1 di wilayah loop bab: gagal eksekusi bab (exception
        #  dari S.susun_buku, termasuk crash None dari provider) TIDAK
        #  langsung menggagalkan job. Pemanggilan diulang maksimal 3x
        #  dengan backoff RETRY_BAB_BACKOFF_DETIK, dan percobaan ulang
        #  memakai ulang=1 supaya checkpoint host dilewati bab yang
        #  sudah selesai, jadi hanya bab yang belum selesai yang
        #  dieksekusi lagi. Token TIDAK dipotong ulang: percobaan ulang
        #  memakai on_mulai=None bila potong sudah terjadi, dan memakai
        #  pemotong asli bila percobaan pertama gagal sebelum potong.
        #  Galat kuota (HTTPException) dan galat validasi (ValueError,
        #  PermissionError) TIDAK di-retry dan dilempar apa adanya,
        #  supaya pesan saldo dan outline tidak berubah menjadi gagal
        #  teknis. Sesudah percobaan terakhir, raise RuntimeError bersih
        #  (bukan galat mentah) supaya jalur except refund di bawah
        #  menangkap sebagai gagal teknis.
        hasil = None
        _galat_susun = None
        for _percobaan_susun in range(1, RETRY_BAB_PERCOBAAN_MAKS + 1):
            try:
                hasil = S.susun_buku(
                    judul, outline, jenis=jenis,
                    keluar_dir=keluar, lapor=lapor,
                    on_mulai=((_mulai_dan_panen if _is_referensi
                               else _potong_saat_mulai)
                              if not terpotong else None),
                    tier=tier, on_bab_selesai=_cek_bab,
                    ulang=(1 if _percobaan_susun > 1 else 0),
                    refs_holder=(_refs_holder if _is_referensi else None),
                    dari_snapshot=_is_referensi)
                break
            except Exception as _e_susun:
                if type(_e_susun).__name__ == 'HTTPException' or isinstance(
                        _e_susun, (ValueError, PermissionError)):
                    raise
                _galat_susun = _e_susun
                if _percobaan_susun >= RETRY_BAB_PERCOBAAN_MAKS:
                    break
                _jeda_susun = RETRY_BAB_BACKOFF_DETIK[_percobaan_susun - 1]
                if lapor:
                    try:
                        lapor(
                            'Penyusunan bab gagal percobaan %s (%s: %s), '
                            'diulang sesudah %s detik, bab yang sudah selesai '
                            'tidak diulang' % (_percobaan_susun,
                                               type(_e_susun).__name__, _e_susun,
                                               _jeda_susun))
                    except Exception:
                        pass
                time.sleep(_jeda_susun)
        if hasil is None:
            raise RuntimeError(
                'penyusunan bab gagal sesudah %s percobaan, galat terakhir: '
                '%s: %s' % (RETRY_BAB_PERCOBAAN_MAKS,
                            type(_galat_susun).__name__, _galat_susun))

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

        #  A2/G4 Path B (30 Okt 2026): pass sitasi deterministik sesudah
        #  bab selesai dan SEBELUM rakit, supaya DOCX memakai teks yang
        #  sudah diperbaiki. Hanya buku-referensi (tipe lain tidak punya
        #  refs per bab). Gagal di sini raise di dalam try susun(),
        #  sehingga except di bawah mengembalikan token + pesan manusia.
        #  panggil_llm=None: repair deterministik saja, tanpa biaya LLM.
        if kartu_jenis == 'buku-referensi':
            import json as _json_sg
            from . import sitasi_anti_gagal as _SG

            def _gate_sitasi_detailed(n, teks_bab, rows_snap, refs_bab):
                # Gas 31 Okt 2026 12:03, butir 3: gerbang di bawah
                # sudah mencetak [GERBANG-SITASI] ke log sebelum
                # raise, jadi di sini tidak ada print lagi. Yang
                # dibungkus di sini adalah galat DB: GagalSitasi
                # default hanya memuat pesan umum, pembungkus ini
                # membangun galat detail (nomor bab, cakupan
                # pembilang dan penyebut, sitasi snapshot, pesan
                # manusia plus Token sudah kembali), supaya
                # proses.tandai_gagal menyimpan rincian itu di DB
                # dan pekerja proses mencatatnya di log.
                try:
                    if rows_snap:
                        return _SG.periksa_dan_perbaiki_bab_snapshot(
                            n, teks_bab, rows_snap, gagal_keras=True)
                    return _SG.periksa_dan_perbaiki_bab(
                        n, teks_bab, refs_bab, panggil_llm=None,
                        gagal_keras=True)
                except _SG.GagalSitasiBersih as _e_sg:
                    _detail = _SG.detail_galat_sitasi(
                        n, _e_sg.cakupan,
                        inisial_sisa=_e_sg.inisial_tersisa)
                    raise _SG.GagalSitasiBersih(
                        nomor_bab=n, masalah=_e_sg.masalah,
                        inisial_tersisa=_e_sg.inisial_tersisa,
                        cakupan=_e_sg.cakupan,
                        detail_text=_detail) from _e_sg

            for _n in sorted(n for n in outline if isinstance(n, int)):
                _p_bab = _path_bab(
                    _n, hasil['bab'].get(_n) or hasil['bab'].get(str(_n)) or {})
                if not _p_bab:
                    continue
                with open(_p_bab, encoding='utf-8') as _f:
                    _teks_bab = _f.read()
                # Snapshot dulu (pra-panen): bila ada, checker
                # membaca kunci dari snapshot, bukan parse ulang
                # string JSON. Bila tidak ada (job lama, jalur
                # non-pra-panen), jatuh kembali ke JSON seperti dulu.
                _rows_snap = []
                try:
                    from . import pra_panen as _PP_sg
                    _rows_snap = _PP_sg.ambil_snapshot(db, _job_kode, _n)
                except Exception:
                    _rows_snap = []
                if _rows_snap:
                    _hasil_sg = _gate_sitasi_detailed(
                        _n, _teks_bab, _rows_snap, [])
                    if _hasil_sg['teks_baru'] != _teks_bab:
                        with open(_p_bab, 'w', encoding='utf-8') as _f:
                            _f.write(_hasil_sg['teks_baru'])
                        if lapor:
                            lapor('Sitasi bab %s diperbaiki' % _n)
                    continue
                _folder_bab = os.path.dirname(_p_bab)
                _refs_bab = []
                for _calon_ref in (
                        os.path.join(_folder_bab, 'visual',
                                     'refs_bab%d.json' % _n),
                        os.path.join(_folder_bab,
                                     'refs_bab%d.json' % _n),
                        os.path.join(keluar, 'visual',
                                     'refs_bab%d.json' % _n),
                        os.path.join(keluar, 'refs_bab%d.json' % _n)):
                    try:
                        with open(_calon_ref, encoding='utf-8') as _fr:
                            _coba = _SG.refs_dari_data(_json_sg.load(_fr))
                    except Exception:
                        continue
                    if _coba:
                        _refs_bab = _coba
                        break
                _hasil_sg = _gate_sitasi_detailed(
                    _n, _teks_bab, [], _refs_bab)
                if _hasil_sg['teks_baru'] != _teks_bab:
                    with open(_p_bab, 'w', encoding='utf-8') as _f:
                        _f.write(_hasil_sg['teks_baru'])
                    if lapor:
                        lapor('Sitasi bab %s diperbaiki' % _n)

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
        #  A2/G4: konsolidasi pustaka (30 Okt 2026), gabungan sitasi
        #  badan (teks bab sesudah repair Path B di atas) + refs panen,
        #  bukan panen saja. Di luar try/except kumpul di atas supaya
        #  gagal konsolidasi tidak ditelan menjadi pustaka kosong.
        if kartu_jenis == 'buku-referensi':
            from . import sitasi_anti_gagal as _SG
            _teks_per_bab = {}
            for _n in sorted(n for n in outline if isinstance(n, int)):
                _p_bab2 = _path_bab(
                    _n, hasil['bab'].get(_n) or hasil['bab'].get(str(_n)) or {})
                if _p_bab2:
                    with open(_p_bab2, encoding='utf-8') as _f2:
                        _teks_per_bab[_n] = _f2.read()
            refs_rakit = _SG.gabung_pustaka(_teks_per_bab, refs_rakit or [])
        _peta_sumber = None
        if kartu_jenis == 'buku-referensi':
            _peta_sumber = _peta_sumber_pustaka(db, _job_kode, outline)
        try:
            import buku_umum_assembly as ASM
            rakit = ASM.rakit(
                judul, keluar, outline,
                glosarium=glos,
                references=refs_rakit,
                peta_sumber=_peta_sumber,
                penulis=(penulis or getattr(u, 'nama', '')
                         or getattr(u, 'nama_lengkap', '') or ''),
                institusi=(getattr(u, 'nama_kampus', '') or ''),
                penelaah=(penelaah or ''),
                tier=tier,
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
                    #  G5 urutan (30 Okt 2026): isi_nomor pertama jalan
                    #  SEBELUM indeks + singkatan disisipkan, sehingga
                    #  nomor TOC bisa bergeser sesudah penyisipan. Pass
                    #  kedua di sini (sesudah semua sisipan, sebelum
                    #  gerbang) menyegarkan nomor TOC + total halaman
                    #  untuk dokumen final, lalu Pages metadata diisi
                    #  dari total ukur final. Pass ini best-effort:
                    #  bila gagal, lanjut dengan nomor pass pertama
                    #  dan tanpa Pages (bukan gagal buku), kecuali
                    #  berkas docx hilang (itu gagal, fail-closed).
                    try:
                        _bernomor2, _terisi2, _hilang2 = _sc.isi_nomor(
                            hasil['docx'])
                        if _hilang2:
                            hasil['toc_hilang'] = _hilang2
                            if lapor:
                                lapor('Nomor TOC belum terisi (pass 2): ' +
                                      ', '.join(_hilang2))
                        os.replace(hasil['docx'],
                                   hasil['docx'] + '.pra-nomor')
                        try:
                            os.replace(_bernomor2, hasil['docx'])
                        except Exception:
                            os.replace(hasil['docx'] + '.pra-nomor',
                                       hasil['docx'])
                            raise
                        hasil['toc_terisi'] = _terisi2
                        _peta2, hilang_ukur2, _total2 = _sc.ukur(
                            hasil['docx'], judul_bab)
                        if hilang_ukur2:
                            raise RuntimeError(
                                'judul bab tidak tampil di render (pass 2): ' +
                                ', '.join(hilang_ukur2))
                        hasil['ukur_peta'] = _peta2
                        import buku_umum_assembly as _ASMhal
                        _ASMhal.isi_halaman_docx(hasil['docx'], int(_total2))
                    except Exception as _e2:
                        if lapor:
                            lapor('Penyegaran nomor TOC pass 2 dilewati: %s'
                                  % _e2)
                        if not os.path.exists(hasil['docx']):
                            raise RuntimeError(
                                'docx hilang sesudah pass 2: %s' % _e2)
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
