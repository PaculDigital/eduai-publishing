"""SATU KANTONG SALDO TOKEN + POTONG BANYAK SEKALIGUS  (26Sep26).

📌 ATURAN BOS (verbatim):
   "jatah paket itu sama dengan penambahan token posisinya. Misal mau bikin
    kerangka 15 token, paket penulis 12 harus beli addon 30 token jadi total
    45 token. Tidak ada token paket di habiskan dulu itu tidak ada. Berapapun
    sisa saldo token baik berasal dari paket atau AddOn itu sama nilainya.
    Jadi sebelum user klik kerjakan jika saldo token kurang harus beli addon
    dulu. Dan tidak bisa di eksekusi"

⇒ SALDO = sisa jatah paket + sisa AddOn  → SATU ANGKA, nilai SAMA.
⇒ Sebelum eksekusi: SALDO < kebutuhan → TOLAK + arahkan beli AddOn.
⇒ Kalau cukup: potong SEKALIGUS, tidak boleh gagal di tengah.

🔴 AKAR YANG DITUTUP (terukur 26Sep26):
   Kode lama: `total = jatah_paket + sisa_addon` dihitung ULANG tiap
   potongan, sedangkan `sisa_addon` MENYUSUT selama loop →
   potongan ke-N menilai total yang sudah berkurang → 402 palsu
   ("KUOTA HABIS" padahal saldo masih banyak). Fitur kerangka (15 token
   sekaligus) adalah yang PERTAMA memunculkan bug ini; revisi biasa (1
   token) tidak pernah kelihatan.

⚠️ Fungsi LAMA (`cek_dan_potong`) TIDAK diubah — masih dipakai 3 jalur
   revisi (1 token). Fungsi BARU di bawah menyambung ke saldo yang sama.
"""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/kuota.py')
s = P.read_text()

if 'def saldo_token(' in s:
    print('⚠️ fungsi saldo_token SUDAH ADA — tidak ditambah')
    raise SystemExit(0)

TAMBAHAN = '''

# ══════════════════════════════════════════════════════════════════════════
#  🪙 SATU KANTONG SALDO TOKEN (26Sep26) — aturan Bos
#     "Berapapun sisa saldo token baik berasal dari paket atau AddOn itu
#      sama nilainya."
# ══════════════════════════════════════════════════════════════════════════
def saldo_token(db: Session, u: User, jenis_addon: str = 'ai') -> dict:
    """SALDO TOKEN user = sisa jatah paket + sisa AddOn. Satu angka.

    ⚠️ JANGAN pakai `jatah_paket + sisa_addon` lalu bandingkan dengan
    `jumlah_revisi` (cara lama) — itu yang bikin 402 palsu.
    Cara benar: hitung SISA, bukan total.
    """
    paket = u.paket or 'gratis'
    jatah = KUOTA_PAKET.get(paket, {}).get('revisi', 0)
    pakai = ambil_pemakaian(db, u.id).jumlah_revisi
    sisa_paket = max(0, jatah - pakai)
    addon = sisa_addon(db, u.id, jenis_addon)
    return {
        'saldo': sisa_paket + addon,
        'sisa_paket': sisa_paket,
        'jatah_paket': jatah,
        'terpakai': pakai,
        'addon': addon,
        'paket': paket,
        'boleh_beli_addon': bool(boleh_beli_addon(paket)),
    }


def potong_banyak(db: Session, u: User, butuh: int,
                  jenis_addon: str = 'ai') -> dict:
    """Potong `butuh` token SEKALIGUS dari SATU KANTONG saldo.

    ATURAN BOS: kalau saldo < butuh → TOLAK (jangan eksekusi), arahkan
    beli AddOn. Admin dikecualikan (tidak dipotong).

    Raise HTTPException 402 + tawaran AddOn kalau kurang.
    Return {'saldo_sebelum', 'saldo_sesudah', 'butuh', 'dipotong'}.
    """
    butuh = int(butuh)
    if butuh <= 0:
        return {'butuh': 0, 'dipotong': 0, 'saldo_sebelum': None,
                'saldo_sesudah': None}

    if _admin(u):
        return {'butuh': butuh, 'dipotong': 0, 'admin': True,
                'saldo_sebelum': None, 'saldo_sesudah': None}

    info = saldo_token(db, u, jenis_addon)
    saldo = info['saldo']

    #  ── GERBANG: saldo kurang → TOLAK di DEPAN (tidak boleh eksekusi) ──
    if saldo < butuh:
        kurang = butuh - saldo
        detail = _pesan_addon_habis(jenis_addon)
        if isinstance(detail, dict):
            detail = dict(detail)
            detail['kode'] = 'SALDO_KURANG'
            detail['butuh'] = butuh
            detail['saldo'] = saldo
            detail['kurang'] = kurang
            if not detail.get('pesan'):
                detail['pesan'] = (
                    f'Untuk ini perlu {butuh} Token Revisi, sedangkan saldo '
                    f'kamu {saldo}. Tambah AddOn dulu ya — AddOn tidak '
                    'hangus di akhir bulan.')
            else:
                detail['pesan'] = (
                    f'Untuk ini perlu {butuh} Token Revisi, sedangkan saldo '
                    f'kamu {saldo} (kurang {kurang}). ' + str(detail['pesan']))
        else:
            detail = {'ok': False, 'kode': 'SALDO_KURANG', 'butuh': butuh,
                      'saldo': saldo, 'kurang': kurang,
                      'pesan': (f'Untuk ini perlu {butuh} Token Revisi, '
                                f'sedangkan saldo kamu {saldo}.')}
        raise HTTPException(402, detail=detail)

    #  ── POTONG SEKALIGUS: pakai jatah paket dulu (hangus tgl 1), sisa AddOn
    #     KEPUTUSAN: urutan potong tetap paket-dulu (bukan aturan bisnis,
    #     hanya teknis — karena jatah paket hangus tiap bulan, jadi adil bagi
    #     user untuk dihabiskan lebih dulu). SALDO TETAP SATU ANGKA.
    pakai = ambil_pemakaian(db, u.id)
    sisa_paket = max(0, info['jatah_paket'] - pakai.jumlah_revisi)
    dari_paket = min(butuh, sisa_paket)
    dari_addon = butuh - dari_paket

    pakai.jumlah_revisi += butuh                  # catatan total
    if dari_addon > 0:
        _potong_addon_n(db, u.id, jenis_addon, dari_addon)
    db.commit()

    sesudah = saldo_token(db, u, jenis_addon)
    log.info('[kuota] potong_banyak user=%s butuh=%d (paket=%d addon=%d) '
             'saldo %s → %s', u.id, butuh, dari_paket, dari_addon,
             saldo, sesudah['saldo'])

    #  🔔 notifikasi (pola sama dengan cek_dan_potong)
    try:
        from .notifikasi import periksa_dan_catat
        from .models import SessionLocal as _Sesi
        _db2 = _Sesi()
        try:
            periksa_dan_catat(_db2, u.id, sisa_kuota=sesudah['saldo'],
                              sisa_addon=sesudah['addon'])
        finally:
            _db2.close()
    except Exception:                                     # noqa: BLE001
        pass

    return {'butuh': butuh, 'dipotong': butuh,
            'dari_paket': dari_paket, 'dari_addon': dari_addon,
            'saldo_sebelum': saldo, 'saldo_sesudah': sesudah['saldo']}


def _potong_addon_n(db: Session, uid: int, jenis: str, n: int) -> None:
    """Potong `n` saldo AddOn (paling lama kedaluwarsa dipakai dulu)."""
    now = datetime.now(timezone.utc)
    baris = db.execute(
        select(PembelianAddon).where(
            PembelianAddon.user_id == uid,
            PembelianAddon.jenis == jenis,
            PembelianAddon.sisa_kuota > 0,
        ).order_by(PembelianAddon.dibuat)
    ).scalars().all()
    sisa = int(n)
    for b in baris:
        if sisa <= 0:
            break
        if b.kedaluwarsa is not None:
            kd = b.kedaluwarsa
            if kd.tzinfo is None:
                kd = kd.replace(tzinfo=timezone.utc)
            if kd < now:
                continue
        ambil = min(sisa, b.sisa_kuota)
        b.sisa_kuota -= ambil
        sisa -= ambil
    if sisa > 0:
        #  TIDAK BOLEH TERJADI: saldo sudah dicek di depan. Kalau sampai
        #  kesini, ada selisih antara saldo_token() dan baris AddOn →
        #  lebih baik BERISIK di log daripada diam-diam merugi.
        log.error('[kuota] _potong_addon_n KURANG %d (uid=%s) — saldo '
                  'dihitung sebelum potong!', sisa, uid)


def kembalikan_banyak(db: Session, u: User, jumlah: int,
                      jenis_addon: str = 'ai') -> dict:
    """Kembalikan `jumlah` token (pagar P2 — gagal di tengah → saldo utuh).

    Dipakai kalau fitur gagal SETELAH token dipotong.
    """
    jumlah = int(jumlah)
    if jumlah <= 0 or _admin(u):
        return {'dikembalikan': 0}
    paket = u.paket or 'gratis'
    jatah = KUOTA_PAKET.get(paket, {}).get('revisi', 0)
    pakai = ambil_pemakaian(db, u.id)
    #  Sisa jatah paket SEBELUM pengembalian (dipakai untuk menghitung
    #  berapa yang tadi diambil dari jatah paket vs dari AddOn).
    sisa_paket_lama = max(0, jatah - pakai.jumlah_revisi)
    dari_paket = min(jumlah, sisa_paket_lama)
    dari_addon = max(0, jumlah - dari_paket)
    pakai.jumlah_revisi = max(0, pakai.jumlah_revisi - jumlah)
    if dari_addon > 0:
        now = datetime.now(timezone.utc)
        baris = db.execute(
            select(PembelianAddon).where(
                PembelianAddon.user_id == u.id,
                PembelianAddon.jenis == jenis_addon,
            ).order_by(PembelianAddon.dibuat.desc())
        ).scalars().all()
        sisa = dari_addon
        for b in baris:
            if sisa <= 0:
                break
            b.sisa_kuota += 1
            sisa -= 1
    db.commit()
    log.info('[kuota] kembalikan_banyak user=%s jumlah=%d (paket=%d addon=%d)',
             u.id, jumlah, dari_paket, dari_addon)
    return {'dikembalikan': jumlah, 'dari_paket': dari_paket,
            'dari_addon': dari_addon}
'''

s = s.rstrip() + '\n' + TAMBAHAN
P.write_text(s)
print('✅ saldo_token + potong_banyak + _potong_addon_n + kembalikan_banyak')
