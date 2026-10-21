"""PASANG Langkah A+B ke app/ai.py DENGAN AMAN (ACC Bos 16Sep26).

Kenapa pakai skrip, bukan patch manual: percobaan patch manual tadi MERUSAK
docstring & indentasi (SyntaxError). Skrip ini:
  1. baca app/ai.py
  2. pastikan pola yang dicari ADA (kalau tidak → BERHENTI, jangan tulis)
  3. sisipkan perubahan
  4. periksa sintaks hasilnya SEBELUM menulis ke disk
  5. simpan cadangan .bak

Jalankan:  python3 _pasang_langkahab.py
"""
import ast
import re
import shutil
import sys
from pathlib import Path

P = Path('app/ai.py')
SRC = P.read_text()
ASAL = SRC

# ══════════════════════════════════════════════════════════════════════════
# 1. IMPOR modul proses
# ═════════════════════════════════════════════════════════════════════════
IMPOR_LAMA = "from .catatan_ai import catat_revisi, ringkasan_untuk_ai"
IMPOR_BARU = """from .catatan_ai import catat_revisi, ringkasan_untuk_ai
# LANGKAH A+B (16Sep26, ACC Bos): PROSES LATAR BELAKANG. Akar masalah yang
# ditutup: Cloudflare memutus koneksi di ~125 detik pada naskah besar (HTTP
# 524) → kuota hangus padahal hasil tidak tersimpan. Sekarang pekerjaan
# dititipkan, request dibalas pendek. Rancangan: MASTER_PLAN §4.12 poin F.
from . import proses as proses_mod"""
if IMPOR_LAMA not in SRC:
    sys.exit('❌ BERHENTI: baris impor catatan_ai tidak ditemukan.')
SRC = SRC.replace(IMPOR_LAMA, IMPOR_BARU, 1)

# ══════════════════════════════════════════════════════════════════════════
# 2. UBAH nama fungsi revisi → `_revisi_kerja` (inti pekerjaan)
#    + pisahkan BLOK PERSETUJUAN (409) ke endpoint pembungkus.
# ══════════════════════════════════════════════════════════════════════════
KEPALA = """@router.post('/v1/revisi')
async def ai_revisi(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):"""

if KEPALA not in SRC:
    sys.exit('❌ BERHENTI: kepala endpoint /v1/revisi tidak ditemukan.')

# 2a. Balikkan dulu urutannya: blok PERSETUJUAN + KUOTA perlu dipindah.
#     Kita ganti kepala fungsi dengan kepala baru `_revisi_kerja`.
SRC = SRC.replace(
    KEPALA,
    "async def _revisi_kerja(\n"
    "    request: Request,\n"
    "    u: User,\n"
    "    db: Session,\n"
    "):",
    1,
)

# 2b. Sesudah tanda tangan tadi, sisipkan docstring inti.
DOC_ANCHOR = "):\n    # 1) member?"
if DOC_ANCHOR not in SRC:
    sys.exit('❌ BERHENTI: penanda awal badan fungsi tidak ditemukan.')
SRC = SRC.replace(
    DOC_ANCHOR,
    '''):
    """INTI PEKERJAAN REVISI (dipanggil oleh endpoint & oleh utas latar belakang).

    ⚠️ Fungsi ini TIDAK memeriksa gerbang biaya sendiri — pemeriksaan itu ada
    di `ai_revisi()` (endpoint). Sengaja dipisah supaya:
      - gerbang biaya tetap SATU TEMPAT (mudah diaudit, tidak bisa dilewati);
      - utas latar belakang memakai fungsi yang SAMA (jangan ada jalur kedua).
    """
    # 1) member?''',
    1,
)

# 2c. Buang pemeriksaan gerbang dari inti (sudah dilakukan endpoint).
GERBANG = """    # 1) member?
    if not _member_berbayar(db, u):
        raise HTTPException(
            403,
            detail={
                'ok': False,
                'pesan': 'Fitur AI hanya untuk member berbayar. Upgrade paket dulu ya.',
            },
        )
    # 2) rate limit
    _cek_ratelimit(u.id)
"""
GERBANG_BARU = """    # 1) member? → SUDAH diperiksa endpoint (gerbang biaya satu pintu).
    # 2) rate limit → SUDAH diperiksa endpoint.
"""
if GERBANG not in SRC:
    sys.exit('❌ BERHENTI: blok gerbang biaya tidak ditemukan.')
SRC = SRC.replace(GERBANG, GERBANG_BARU, 1)

# ══════════════════════════════════════════════════════════════════════════
# 3. PISAHKAN blok PERSETUJUAN (409 "butuh_izin")
#    Keluar dari inti → masuk endpoint pembungkus, karena persetujuan harus
#    dijawab LANGSUNG ke user (bukan di dalam pekerjaan latar belakang).
# ═════════════════════════════════════════════════════════════════════════
MULAI_SETUJU = "    setuju = bool(body.get('setuju_bagian'))"
if MULAI_SETUJU not in SRC:
    sys.exit('❌ BERHENTI: penanda setuju_bagian tidak ditemukan.')
SRC = SRC.replace(MULAI_SETUJU, "    # (blok persetujuan DIPINDAH ke endpoint)", 1)

# hapus blok 409 yang lama
POLA_409 = re.compile(
    r"    if jml_bagian > 1 and not setuju:\n"
    r"        raise HTTPException\(\n"
    r"            409,\n"
    r"            detail=\{.*?\n"
    r"        \)\n",
    re.S,
)
SRC, n409 = POLA_409.subn('', SRC, count=1)
if n409 != 1:
    sys.exit('❌ BERHENTI: blok 409 butuh_izin tidak terpotong rapi.')

# ═════════════════════════════════════════════════════════════════════════
# 4. TAMBAH LAPORAN TAHAP NYATA (ACC Bos: tahap, bukan persen karangan)
# ═════════════════════════════════════════════════════════════════════════
LOOP_LAMA = "    for idx, potongan in enumerate(bagian_naskah, start=1):"
LOOP_BARU = """    # LANGKAH A (16Sep26): laporkan TAHAP NYATA ke halaman — MASTER_PLAN
    # §4.12: "Progress: pakai TAHAP NYATA, jangan persentase karangan".
    # `_lapor` bernilai None kalau dipanggil langsung (mode tunggu) → aman.
    if _lapor is not None:
        try:
            _lapor.tahap(proses_mod.TAHAP_MENYUSUN)
        except Exception:                                     # noqa: BLE001
            pass
    for idx, potongan in enumerate(bagian_naskah, start=1):"""
if LOOP_LAMA not in SRC:
    sys.exit('❌ BERHENTI: loop bagian tidak ditemukan.')
SRC = SRC.replace(LOOP_LAMA, LOOP_BARU, 1)

# lapor sebelum tiap bagian dikerjakan
TRY_LAMA = """        try:
            konten, model_terakhir, info = await _revisi_dengan_failover(
                user_msg, len(komentar))"""
TRY_BARU = """        if _lapor is not None:
            try:
                _lapor.menulis(idx, jml_bagian)
            except Exception:                                 # noqa: BLE001
                pass
        try:
            konten, model_terakhir, info = await _revisi_dengan_failover(
                user_msg, len(komentar))"""
if TRY_LAMA not in SRC:
    sys.exit('❌ BERHENTI: pemanggilan _revisi_dengan_failover tidak ditemukan.')
SRC = SRC.replace(TRY_LAMA, TRY_BARU, 1)

# lapor sebelum memeriksa hasil
INS_LAMA = "    info_akhir = info_potong[-1] if info_potong else {}"
INS_BARU = """    if _lapor is not None:
        try:
            _lapor.tahap(proses_mod.TAHAP_MEMERIKSA)
        except Exception:                                     # noqa: BLE001
            pass
    info_akhir = info_potong[-1] if info_potong else {}"""
if INS_LAMA not in SRC:
    sys.exit(' BERHENTI: penanda info_akhir tidak ditemukan.')
SRC = SRC.replace(INS_LAMA, INS_BARU, 1)

# ═════════════════════════════════════════════════════════════════════════
# 5. SISIPKAN parameter `_lapor` pada tanda tangan inti
# ══════════════════════════════════════════════════════════════════════════
TTD_LAMA = """async def _revisi_kerja(
    request: Request,
    u: User,
    db: Session,
):"""
TTD_BARU = """async def _revisi_kerja(
    request: Request,
    u: User,
    db: Session,
    _lapor=None,
):"""
if TTD_LAMA not in SRC:
    sys.exit('❌ BERHENTI: tanda tangan _revisi_kerja tidak ditemukan.')
SRC = SRC.replace(TTD_LAMA, TTD_BARU, 1)

# ══════════════════════════════════════════════════════════════════════════
# 6. TAMBAH ENDPOINT PEMBUNGKUS di AKHIR file
# ═════════════════════════════════════════════════════════════════════════
EKOR = '''

# ══════════════════════════════════════════════════════════════════════════
#  LANGKAH A+B (16Sep26, ACC Bos) — ENDPOINT TITIP PEKERJAAN & PANTAU STATUS
# ══════════════════════════════════════════════════════════════════════════

async def _tidur_sebentar():
    """Beri kesempatan halaman membaca status 'jalan' sebelum kerja dimulai."""
    import asyncio as _a
    await _a.sleep(0.01)


@router.post('/v1/revisi')
async def ai_revisi(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TITIPKAN REVISI → balas cepat. Halaman memantau lewat /v1/proses/{kode}.

    ══ KENAPA (akar masalah, TERUKUR 16Sep26 — jangan diubah tanpa alasan) ═══
    Dulu endpoint ini MENUNGGU AI sampai selesai. Bukti nyata lewat domain
    publik: naskah 65.932 karakter = 2 bagian → Cloudflare memutus koneksi di
    **125 detik** (HTTP 524) → mahasiswa lihat "error code: 524", padahal:
         pemakaian_ai  : 9 → 7   (kuota SUDAH dipotong)
         revisi_history: 0 baris (hasil TIDAK tersimpan)
         versi_dokumen : tidak bertambah
    ⇒ MAHASISWA BAYAR TAPI TIDAK DAPAT HASIL.

    Menaikkan AI_TIMEOUT_DETIK=420 TIDAK menolong: yang memutus Cloudflare,
    bukan aplikasi. Batas Cloudflare hanya bisa dinaikkan sampai 100 detik,
    dan selalu ada naskah yang lebih besar.

    ═══ SOLUSI (RANCANGAN BOS SENDIRI — MASTER_PLAN §4.12 poin F) ═══
    Bos menulis: "KEDUANYA (skeleton jika ditunggui + boleh ditinggal, proses
    jalan di server, hasil disimpan + notifikasi)."

      request pendek → Cloudflare tidak pernah memutus
      pekerjaan jalan di utas (threading stdlib — TANPA dependency baru)
      halaman pantau /v1/proses/{kode} → TAHAP NYATA (§4.12)
      selesai → dokumen ditulis (auto-save OnlyOffice) + LONCENG menyala

    ═══ YANG DIPERTAHANKAN (gerbang biaya TIDAK diubah) ═══
      member berbayar → rate limit → cek storage → potong kuota SEBELUM
      kerja → rumus Token Revisi ÷10.000 → versi dokumen & riwayat.
      Body `{"tunggu": true}` = perilaku LAMA (menunggu selesai), dipakai
      API/skrip uji yang butuh jawaban langsung.
    """
    #  1. Gerbang biaya (URUTAN WAJIB: validasi dulu, baru potong kuota) 
    if not _member_berbayar(db, u):
        raise HTTPException(403, detail={
            'ok': False,
            'pesan': 'Fitur AI hanya untuk member berbayar. Upgrade paket dulu ya.',
        })
    _cek_ratelimit(u.id)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail={'ok': False, 'pesan': 'Body JSON tidak valid.'})
    mode_tunggu = str(body.get('tunggu') or '').lower() in ('1', 'true', 'ya')

    # Ambil naskah (bisa dari file_id) + peta bab — dipakai untuk menghitung
    # jumlah bagian (dasar persetujuan & potongan kuota).
    naskah_panjang, fb, err = _teks_dari_body(db, u, body)
    if err:
        raise err
    if not naskah_panjang:
        raise HTTPException(400, detail={'ok': False, 'pesan': '`naskah` wajib diisi.'})
    komentar_isi = body.get('komentar') or []
    if not isinstance(komentar_isi, list) or not komentar_isi:
        raise HTTPException(400, detail={
            'ok': False, 'pesan': '`komentar` wajib diisi (minimal 1).'})

    bab = (body.get('bab') or '').strip() or BAB_SELURUH
    naskah_kerja = naskah_panjang
    if bab != BAB_SELURUH:
        _s, isi_bab, _e = ambil_bab(naskah_panjang, bab)
        if isi_bab:
            naskah_kerja = isi_bab
        else:
            bab = BAB_SELURUH
    bagian = potong_cerdas(naskah_kerja)
    jml = len(bagian)

    # ─ 2. PERSETUJUAN (dulu di dalam fungsi inti; DIPINDAH ke sini karena
    #      user harus menjawab LANGSUNG — tidak boleh terjadi di latar
    #      belakang, supaya kuota tidak terpotong tanpa izin) ─
    if jml > 1 and not bool(body.get('setuju_bagian')):
        raise HTTPException(409, detail={
            'ok': False,
            'kode': 'butuh_izin',
            'bagian': jml,
            'panjang': len(naskah_kerja),
            'pesan': (f'Dokumen {len(naskah_kerja):,} karakter — akan diproses '
                      f'{jml} bagian dan memakai {jml} kuota revisi. '
                      'Setujui dulu untuk melanjutkan.').replace(',', '.'),
        })

    # ─ 3. Member berbayar + data dokumen + kuota storage (SAMA seperti dulu) ─
    _cek_storage_untuk_revisi(db, u, fb)

    #  4. POTONG KUOTA (gerbang biaya — urutan TIDAK diubah) ─
    info_potong = []
    for _ in range(jml):
        try:
            info_potong.append(cek_dan_potong(db, u, 'revisi'))
        except HTTPException:
            for ip in info_potong:
                _kembalikan_kuota(db, u, ip)
            raise

    jenis_dok = ''
    try:
        if fb is not None:
            from .jenis import deteksi_jenis
            jenis_dok = (deteksi_jenis(naskah_kerja) or {}).get('jenis', '') or ''
    except Exception:                                         # noqa: BLE001
        jenis_dok = ''

    # ─ 5. MODE TUNGGU (perilaku LAMA) — dipakai API/skrip uji ─
    if mode_tunggu:
        try:
            return await _revisi_kerja(request, u, db)
        except HTTPException:
            for ip in info_potong:
                _kembalikan_kuota(db, u, ip)
            raise
        except Exception as e:                                # noqa: BLE001
            for ip in info_potong:
                _kembalikan_kuota(db, u, ip)
            log.error('[ai] revisi mode tunggu gagal: %s', e)
            raise HTTPException(503, detail={
                'ok': False, 'pesan': f'Gagal memproses revisi: {e}'})

    # ─ 6. TITIPKAN KE LATAR BELAKANG → balas CEPAT (inti perbaikan) ─
    p = proses_mod.mulai(
        db, user_id=u.id, file_id=(fb.id if fb is not None else None),
        komentar=[k for k in komentar_isi if isinstance(k, str) and k.strip()],
        jenis_dokumen=jenis_dok, jumlah_bagian=jml, panjang=len(naskah_kerja),
    )
    body['file_id'] = (fb.id if fb is not None else None)

    async def _kerja(lapor):
        """Dijalankan di UTAS. Sesi DB BARU (sesi request akan ditutup)."""
        d2 = proses_mod._sesi_baru()
        try:
            req2 = _RequestTiruan(body)
            hasil = await _revisi_kerja(req2, u, d2, _lapor=lapor)
            proses_mod.tandai_selesai(
                p.kode,
                hasil=hasil.get('jawaban', ''),
                model_ai=hasil.get('model', ''),
                token_revisi=hasil.get('token_revisi', 0),
            )
        except Exception as e:                                # noqa: BLE001
            log.error('[ai] proses latar belakang %s gagal: %s', p.kode, e)
            proses_mod.tandai_gagal(p.kode, f'{type(e).__name__}: {e}')
            # ⚠️ KUOTA DIKEMBALIKAN karena proses GAGAL. Di alur lama,
            #    pengembalian hanya jalan pada `except HTTPException` —
            #    koneksi putus/utas mati TIDAK tertangkap → kuota hangus
            #    (bukti 16Sep26: 9→7 padahal revisi_history=0).
            for ip in info_potong:
                try:
                    _kembalikan_kuota(d2, u, ip)
                except Exception as e2:                       # noqa: BLE001
                    log.warning('[ai] gagal kembalikan kuota: %s', e2)
        finally:
            d2.close()

    proses_mod.jalankan(p.kode, _kerja)

    return {
        'ok': True,
        'latar_belakang': True,
        'kode': p.kode,
        'tahap': p.tahap,
        'status': p.status,
        'bagian': jml,
        'panjang': len(naskah_kerja),
        'pesan': (f'Revisi {jml} bagian sedang diproses. Boleh Anda tinggalkan — '
                  'prosesnya jalan terus dan dokumen akan terisi otomatis.'),
        'kuota': ringkasan_kuota(db, u).get('revisi'),
    }


class _RequestTiruan:
    """Peniru `Request` untuk pekerjaan latar belakang.

    KENAPA: `_revisi_kerja()` menerima `Request` dan memanggil `.json()`.
    Di utas, objek Request asli MEMBACA STREAM yang sudah habis (dibaca
    endpoint) → error "Stream consumed". Jadi kita beri objek kecil yang
    mengembalikan body yang SUDAH dibaca endpoint. Body-nya sama persis,
    jadi perilaku kerja identik dengan jalur lama.
    """

    def __init__(self, body: dict):
        self._body = dict(body or {})

    async def json(self) -> dict:
        return self._body


@router.get('/v1/proses/{kode}')
async def ai_proses_status(
    kode: str,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """STATUS proses di latar belakang. Dipantau halaman (bukan persen karangan).

    Tahap ditampilkan APA ADANYA: Menunggu antrean → Membaca naskah →
    Menyusun rencana revisi → Menulis bagian ke-N dari M → Memeriksa hasil
    → Selesai. (MASTER_PLAN §4.12: "Progress: pakai TAHAP NYATA".)
    """
    p = proses_mod.ambil(db, kode, u.id)
    if p is None:
        raise HTTPException(404, detail={'ok': False, 'pesan': 'Proses tidak ditemukan.'})
    out = proses_mod.ringkas(p)
    out['ok'] = True
    return out


@router.get('/v1/proses/{kode}/hasil')
async def ai_proses_hasil(
    kode: str,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """Ambil HASIL proses selesai + tandai sudah dibaca (lonceng padam).

    Hasil dipisah dari endpoint status supaya halaman tidak mengunduh naskah
    besar berulang kali saat memantau (hemat kuota ponsel mahasiswa).
    """
    p = proses_mod.ambil(db, kode, u.id)
    if p is None:
        raise HTTPException(404, detail={'ok': False, 'pesan': 'Proses tidak ditemukan.'})
    if p.status != 'selesai':
        raise HTTPException(409, detail={
            'ok': False, 'pesan': 'Proses belum selesai.', 'status': p.status})
    proses_mod.tandai_dibaca(db, kode, u.id)
    return {
        'ok': True, 'kode': p.kode, 'status': p.status,
        'model': p.model_ai, 'token_revisi': p.token_revisi,
        'jawaban': p.hasil,
    }


@router.get('/v1/proses')
async def ai_proses_daftar(
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """Daftar proses: yang SEDANG JALAN + yang SELESAI BELUM DIBACA (LONCENG).

    ACC Bos 16Sep26: notifikasi lewat LONCENG di web (WhatsApp nanti saja).
    Juga dipakai halaman untuk MENYAMBUNG lagi kalau user menutup lalu
    membuka tab (rancangan §4.12: "boleh ditinggal").
    """
    return {
        'ok': True,
        'jalan': [proses_mod.ringkas(x) for x in proses_mod.yang_sedang_jalan(db, u.id)],
        'belum_dibaca': [proses_mod.ringkas(x) for x in proses_mod.belum_dibaca(db, u.id)],
    }
'''

SRC = SRC.rstrip() + EKOR

# ══════════════════════════════════════════════════════════════════════════
# 7. PERIKSA SINTAKS sebelum menulis (pelajaran dari patch manual yang rusak)
# ═════════════════════════════════════════════════════════════════════════
try:
    ast.parse(SRC)
except SyntaxError as e:
    sys.exit(f' BERHENTI: sintaks hasil rusak di baris {e.lineno}: {e.msg}\n'
             f'   app/ai.py TIDAK diubah.')

shutil.copy2(P, P.with_suffix('.py.bak-langkahab'))
P.write_text(SRC)
print('✅ app/ai.py DIPERBARUI — syntax OK')
print(f'   ukuran: {len(ASAL)} → {len(SRC)} byte')
print('   cadangan: app/ai.py.bak-langkahab')