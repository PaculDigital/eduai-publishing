"""TAMBAH RUTE KERANGKA ke app/ai.py (di AKHIR berkas — pola aman).

Rute:
  POST /api/ai/v1/kerangka/rencana   → TAHAP 1+2 (GRATIS, 0 token)
  POST /api/ai/v1/kerangka/kerjakan  → TAHAP 3 (POTONG token, setelah setuju)
  GET  /api/ai/v1/kerangka/bab       → daftar bab yang tersedia
"""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/ai.py')
s = P.read_text()

if 'kerangka/rencana' in s:
    print('⚠️ rute kerangka SUDAH ADA — tidak ditambah')
    raise SystemExit(0)

RUTE = '''

# ══════════════════════════════════════════════════════════════════════════
#  KERANGKA PER BAB — TAHAP 1/2 (GRATIS) & TAHAP 3 (POTONG TOKEN)
#  26Sep26 · arahan Bos: "kerangka per bab... 15 token kredit bab I karena
#  kita juga mencari sitasi dan artikel... termasuk buat grafik dan tabel"
#  Putusan Bos: Q1 5 sub-bab 3-5 poin · Q2 panel dulu · Q3 artikel<5 tawaran
#  3 pilihan · Q4 BAB I dulu (kini semua bab) · Q5 gagal → token kembali.
# ══════════════════════════════════════════════════════════════════════════
@router.get('/v1/kerangka/bab')
async def kerangka_daftar_bab(u: User = Depends(wajib_login_api)):
    """Daftar bab yang punya kerangka (untuk tombol pemilih di tampilan)."""
    from . import kerangka_bab as kb
    return {'ok': True, 'bab': kb.daftar_bab()}


@router.post('/v1/kerangka/rencana')
async def kerangka_rencana(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TAHAP 1+2 — TANYA bila kurang + RENCANA (artikel nyata). GRATIS.

    ⚠️ PAGAR P1: endpoint ini TIDAK memotong Token Revisi sama sekali.
       Kuota tidak disentuh → user bebas mengulang/membatalkan.
    """
    body = await request.json()
    judul = (body.get('judul') or '').strip()
    bab = str(body.get('bab') or '1').strip() or '1'
    jenis_dok = (body.get('jenis_dokumen') or '').strip()
    jenis_pen = (body.get('jenis_penelitian') or '').strip()
    tema = (body.get('tema') or '').strip()

    #  Lapis 1: kalau jenis dokumen tak diketahui, coba deteksi dari file.
    if not jenis_dok and body.get('file_id'):
        try:
            teks, _fb, _err = _teks_dari_body(db, u, body)
            if teks and not _err:
                from .jenis import deteksi_jenis
                jenis_dok = ((deteksi_jenis(teks) or {}).get('jenis')
                             or '').strip()
        except Exception:                                     # noqa: BLE001
            jenis_dok = ''

    #  PAGAR P4 — tolak "buat utuh" sebelum apa pun dikerjakan.
    from . import kerangka as _k
    tolak = _k.tolak_buat_utuh(body.get('permintaan') or judul)
    if tolak:
        return tolak

    tanya = _k.perlu_tanya(jenis_dok, judul, jenis_pen)
    if tanya['perlu_tanya']:
        return {'ok': True, 'tahap': 'tanya', 'token_dipotong': False,
                'perlu_tanya': True, 'kurang': tanya['kurang'],
                'daftar_pertanyaan': tanya['daftar_pertanyaan']}

    rencana = _k.susun_rencana(judul=judul, bab=bab, jenis_dok=jenis_dok,
                               jenis_penelitian=jenis_pen, tema=tema)
    rencana['tahap'] = 'rencana'
    rencana['token_dipotong'] = False          # pagar P1 (buktikan di luar)
    return rencana


@router.post('/v1/kerangka/kerjakan')
async def kerangka_kerjakan(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TAHAP 3 — KERJAKAN. Di sinilah Token Revisi dipotong (setelah user
    menekan [Setuju & Kerjakan] di panel rencana) — pagar P1.

    Body: judul, bab, jenis_dokumen, jenis_penelitian, tema, setuju=True
    """
    body = await request.json()

    #  ── Pagar P1: WAJIB ada tanda setuju ──
    if not bool(body.get('setuju')):
        raise HTTPException(409, detail={
            'ok': False, 'kode': 'butuh_setuju',
            'pesan': ('Lihat rencananya dulu ya. Kerangka baru dikerjakan '
                      'setelah kamu menekan "Setuju & Kerjakan".'),
        })

    judul = (body.get('judul') or '').strip()
    if not judul:
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': '`judul` wajib diisi.'})
    bab = str(body.get('bab') or '1').strip() or '1'
    jenis_dok = (body.get('jenis_dokumen') or '').strip()
    jenis_pen = (body.get('jenis_penelitian') or '').strip()
    tema = (body.get('tema') or '').strip()

    #  ── PAGAR P4 lagi (tidak boleh dilewati lewat endpoint ini) ──
    from . import kerangka as _k
    tolak = _k.tolak_buat_utuh(body.get('permintaan') or judul)
    if tolak:
        return tolak

    #  ── POTONG TOKEN (gerbang biaya — pola SAMA seperti ai_revisi) ──
    #     Jumlah token diambil dari config (SATU SUMBER, jangan hardcode).
    from .config import TOKEN_KERANGKA_BAB
    terkumpul = []
    try:
        for _ in range(int(TOKEN_KERANGKA_BAB)):
            terkumpul.append(cek_dan_potong(db, u, 'revisi'))
    except HTTPException:
        for ip in terkumpul:                    # gagal di tengah → kembalikan
            _kembalikan_kuota(db, u, ip)
        raise

    #  ── KERJAKAN ──
    try:
        h = _k.bangun_isi(judul=judul, bab=bab, jenis_dok=jenis_dok,
                          jenis_penelitian=jenis_pen, tema=tema)
    except Exception as e:                                    # noqa: BLE001
        for ip in terkumpul:                    # PAGAR P2 — token kembali
            _kembalikan_kuota(db, u, ip)
        log.error('[kerangka] TAHAP 3 gagal: %s', e)
        raise HTTPException(503, detail={
            'ok': False, 'pesan': (f'Gagal menyusun kerangka: {e}. '
                                   'Token Revisi kamu sudah dikembalikan.'),
            'kuota_dikembalikan': True})

    #  ── PAGAR P2: hasil kosong = gagal = token kembali ──
    if not h.get('ok') or not h.get('kerangka'):
        for ip in terkumpul:
            _kembalikan_kuota(db, u, ip)
        return {'ok': False, 'kode': 'hasil_kosong',
                'pesan': ('Kerangka tidak bisa disusun dari bahan yang ada. '
                          'Token Revisi kamu sudah dikembalikan — coba ubah '
                          'judul atau kata kuncinya.'),
                'kuota_dikembalikan': True}

    h['tahap'] = 'selesai'
    h['token_dipotong'] = int(TOKEN_KERANGKA_BAB)
    h['pesan_hasil'] = ('Kerangka siap. Baca dulu — kalau sudah cocok, tekan '
                        '"Masukkan ke naskah".')
    return h
'''

s = s.rstrip() + '\n' + RUTE
P.write_text(s)
print('✅ rute kerangka ditambahkan ke ai.py')
