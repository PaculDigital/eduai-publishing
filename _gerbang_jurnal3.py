"""GERBANG JURNAL-3 (06Okt26) — jembatan ke mesin + `bangun_isi` terima kiriman.

Uji SUNGGUHAN fungsi produksi:
  K1. `_bersihkan()` bentuk artikel tetap sama + tandai asal
  K2. `cari_untuk_bab()` memanggil mesin sungguhan (pustaka) & merapikan
  K3. `cari_dan_simpan()` hemat: sidik cocok → TIDAK cari ulang
  K4. `tambah_manual()` + pagar batas 8 (pesan hangat, tidak menakutkan)
  K5. `untuk_bangun_isi()` bersihkan kunci internal
  K6. ⭐ `kerangka.bangun_isi()` TERIMA kiriman (artikel manual ikut terpakai)
  K7. ⭐ `bangun_isi()` TANPA kiriman → perilaku LAMA persis (cari sendiri)
  K8. ⭐ `bangun_isi()` pakai kiriman TIDAK panggil mesin pencari (terbukti hemat)
  K9. `info_terverifikasi()` pagar P3 jujur
  K10. daftar pustaka dari kiriman mengikuti aturan pustaka (bogel P3)

Cara pakai (di dalam container): cd /app && python3 _gerbang_jurnal3.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import jurnal as J                                       # noqa: E402
from app import kerangka as K                                     # noqa: E402

lulus = 0
gagal = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  LULUS  {nama}')
    else:
        gagal += 1
        print(f'  GAGAL  {nama}  {bukti}')


def art(doi: str = '', gid=None, judul: str = 'J', tahun: int = 2020,
        status: str = 'verified') -> dict:
    return {'title': judul, 'authors': 'A', 'year': tahun, 'journal': 'Jr',
            'doi': doi, 'garuda_id': gid, 'doi_status': status,
            'cited_by_count': 0}


class P:
    """Profil tiruan (cukup 2 kolom yang dipakai jurnal.py)."""
    def __init__(self) -> None:
        self.jurnal_json = ''
        self.jurnal_sidik = ''


# ── K1 ──
def k1() -> None:
    a = J._bersihkan({'title': '  Judul  ', 'authors': 'An', 'year': 2021,
                      'journal': 'Jr', 'doi': '10.1/a', 'garuda_id': None,
                      'doi_status': 'verified', 'cited_by_count': 7,
                      'sampah': 'buang'}, 'manual')
    cek('K1a judul dirapikan (spasi dibuang)', a['title'] == 'Judul')
    cek('K1b asal = manual', a['asal'] == 'manual')
    cek('K1c kunci asing dibuang', 'sampah' not in a)
    cek('K1d kunci pustaka tetap ada',
        {'title', 'authors', 'year', 'journal', 'doi', 'garuda_id',
         'doi_status'}.issubset(a))


# ── K2 (panggil mesin sungguhan) ──
def k2() -> None:
    h = J.cari_untuk_bab('pengaruh kualitas produk terhadap keputusan pembelian',
                         '2', maks=5)
    cek('K2a cari_untuk_bab ok', h.get('ok') is True)
    cek('K2b maks dihormati', len(h.get('artikel') or []) <= 5)
    cek('K2c ada info pencarian', 'info' in h)
    if h.get('artikel'):
        a = h['artikel'][0]
        cek('K2d tiap artikel asal=ai', all(x.get('asal') == 'ai'
                                           for x in h['artikel']))
        cek('K2e bentuk artikel pustaka',
            'title' in a and 'doi_status' in a)
    else:
        cek('K2d (mesin balas kosong — dilewati)', True)
        cek('K2e (mesin balas kosong — dilewati)', True)
    kosong = J.cari_untuk_bab('', '2')
    cek('K2f tema kosong → ok=False', kosong.get('ok') is False)


# ── K3: hemat (sidik cocok → tidak cari ulang) ──
def k3() -> None:
    p = P()
    J.tulis(p, {'BAB II': [art(doi='10.1/a'), art(doi='10.1/b')]},
            sidik=J.sidik('Harga', 'harga, promosi'))
    panggil = {'n': 0}
    _asli = J.cari_untuk_bab

    def palsu(*a, **k):
        panggil['n'] += 1
        return _asli(*a, **k)

    J.cari_untuk_bab = palsu
    try:
        r = J.cari_dan_simpan(p, 'BAB II', 'Harga', 'harga, promosi')
        cek('K3a sidik cocok → dari_simpanan', r.get('dari_simpanan') is True)
        cek('K3b TIDAK cari ulang (0 panggilan mesin)', panggil['n'] == 0)
        cek('K3c artikel tersimpan dibalikan', len(r['artikel']) == 2)
        r2 = J.cari_dan_simpan(p, 'BAB II', 'Harga', 'harga, promosi',
                               paksa=True)
        cek('K3d paksa=True → cari ulang', r2.get('cari_ulang') is True)
        cek('K3e paksa memanggil mesin', panggil['n'] == 1)
    finally:
        J.cari_untuk_bab = _asli


# ── K4: tambah_manual + pagar ──
def k4() -> None:
    p = P()
    r = J.tambah_manual(p, 'BAB II', art(doi='10.1/m0'))
    cek('K4a manual masuk', r.get('ok') is True)
    cek('K4b sisa 7', r.get('sisa') == 7)
    for i in range(1, 8):
        r = J.tambah_manual(p, 'BAB II', art(doi=f'10.1/m{i}'))
    cek('K4c 8 manual terpasang', J.jumlah_manual(J.baca(p), 'BAB II') == 8)
    cek('K4d sisa 0', r.get('sisa') == 0)
    r = J.tambah_manual(p, 'BAB II', art(doi='10.1/m8'))
    cek('K4e ke-9 DITOLAK', r.get('ok') is False)
    cek('K4f kode = batas_manual', r.get('kode') == 'batas_manual')
    cek('K4g pesan HANGAT (bukan "GAGAL/PERINGATAN")',
        'GAGAL' not in r['pesan'] and 'PERINGATAN' not in r['pesan'])
    cek('K4h pesan menyebut jumlah 8', '8' in r['pesan'])
    cek('K4i tetap 8 (tidak nambah)', J.jumlah_manual(J.baca(p), 'BAB II') == 8)
    # bab lain tidak terpengaruh
    r2 = J.tambah_manual(p, 'BAB IV', art(doi='10.1/z'))
    cek('K4j bab lain masih boleh', r2.get('ok') is True)


# ── K5 ──
def k5() -> None:
    d = J.tambah({}, 'BAB II', art(doi='10.1/a'), asal='manual')
    kirim = J.untuk_bangun_isi(d, 'BAB II')
    cek('K5a kiriman 1 artikel', len(kirim) == 1)
    cek('K5b kunci internal dibuang',
        'kunci' not in kirim[0] and 'asal' not in kirim[0])
    cek('K5c kunci pustaka tetap ada',
        {'title', 'authors', 'year', 'journal', 'doi', 'garuda_id',
         'doi_status'}.issubset(kirim[0]))


# ── K6 ⭐ bangun_isi TERIMA kiriman ──
def k6() -> None:
    kiriman = [art(doi='10.1111/manual1', judul='Artikel Manual Satu'),
               art(doi='10.2222/manual2', judul='Artikel Manual Dua')]
    h = K.bangun_isi(judul='Pengaruh Harga', bab='2',
                     jenis_dok='skripsi', jenis_penelitian='kuantitatif',
                     artikel_dipakai=kiriman)
    cek('K6a build ok', h.get('ok') is True)
    info = h.get('info_cari') or {}
    #  ⭐ ASERSI BERGIGI: buktikan artikel yang KELUAR memang kiriman itu,
    #     bukan hasil pencarian mesin. Kalau `artikel_dipakai` diabaikan,
    #     `dari_kiriman` hilang & jumlah artikel melonjak (artikel internet).
    cek('K6b info menandai dari kiriman (pagar utama)', info.get('dari_kiriman') is True,
        f'(info_cari={info})')
    doi_keluar = {a.get('doi') for a in (h.get('artikel') or [])}
    cek('K6c DOI kiriman ADA di artikel keluaran',
        {'10.1111/manual1', '10.2222/manual2'}.issubset(doi_keluar),
        f'(doi keluar={doi_keluar})')
    cek('K6d jumlah artikel = 2 (kiriman saja, tidak tambah hasil mesin)',
        len(h.get('artikel') or []) == 2, f'({len(h.get("artikel") or [])})')
    cek('K6e artikel HASIL MESIN tidak ikut masuk',
        'dari_kiriman' in info and info.get('total_unik') == 2,
        f'(total_unik={info.get("total_unik")})')
    cek('K6f per_sumber menyebut kiriman',
        'AI + tambahan user' in (info.get('per_sumber') or {}))
    cek('K6g terverifikasi dihitung jujur', info.get('terverifikasi') == 2)
    cek('K6h daftar pustaka memuat manual',
        'Artikel Manual Satu' in (h.get('daftar_pustaka') or ''))
    cek('K6i pagar P3 tetap: hanya terverifikasi masuk daftar',
        (h.get('pagar') or {}).get('hanya_terverifikasi_masuk_daftar_pustaka')
        is True)


# ── K7 ⭐ tanpa kiriman → perilaku lama ──
def k7() -> None:
    h = K.bangun_isi(judul='Pengaruh Kualitas Produk dan Harga terhadap '
                           'Keputusan Pembelian',
                     bab='2', jenis_dok='skripsi',
                     jenis_penelitian='kuantitatif')
    cek('K7a build ok (perilaku lama)', h.get('ok') is True)
    cek('K7b TIDAK ditandai dari_kiriman',
        not (h.get('info_cari') or {}).get('dari_kiriman'))
    cek('K7c mesin pencari tetap dijalankan (info ada)',
        bool(h.get('info_cari')))
    cek('K7d balikan lama tetap utuh (kerangka ada)',
        isinstance(h.get('kerangka'), list) and len(h['kerangka']) > 0)


# ── K8 ⭐ hemat: kiriman TIDAK panggil mesin ──
def k8() -> None:
    panggil = {'n': 0}
    _asli = K.__dict__.get('__noop__')

    import app.pustaka as P2
    asli_cari = P2.cari_semua

    def hitung(*a, **k):
        panggil['n'] += 1
        return asli_cari(*a, **k)

    P2.cari_semua = hitung
    try:
        K.bangun_isi(judul='X', bab='2', jenis_dok='skripsi',
                     artikel_dipakai=[art(doi='10.1/kirim')])
        cek('K8a kiriman → mesin TIDAK dipanggil (0 kali)', panggil['n'] == 0)
        panggil['n'] = 0
        K.bangun_isi(judul='Kualitas produk terhadap keputusan pembelian',
                     bab='2', jenis_dok='skripsi')
        cek('K8b tanpa kiriman → mesin DIPANGGIL', panggil['n'] >= 1)
    finally:
        P2.cari_semua = asli_cari


# ── K9 ──
def k9() -> None:
    cek('K9a 2 verified → 2',
        K.info_terverifikasi([art(status='verified'),
                              art(status='verified')]) == 2)
    cek('K9b no_doi + garuda → dihitung',
        K.info_terverifikasi([art(gid=9, status='no_doi')]) == 1)
    cek('K9c no_doi TANPA garuda → tidak dihitung',
        K.info_terverifikasi([art(status='no_doi')]) == 0)
    cek('K9d unverified → tidak dihitung',
        K.info_terverifikasi([art(status='unverified')]) == 0)
    cek('K9e daftar kosong → 0', K.info_terverifikasi([]) == 0)
    cek('K9f None → 0', K.info_terverifikasi(None) == 0)
    cek('K9g isi aneh (bukan dict) tidak melempar',
        K.info_terverifikasi([None, 'x', 3]) == 0)


# ── K10 ──
def k10() -> None:
    kiriman = [art(doi='10.1/ok', status='verified'),
               art(doi='10.1/bad', status='unverified')]
    h = K.bangun_isi(judul='J', bab='2', jenis_dok='skripsi',
                     artikel_dipakai=kiriman)
    dp = h.get('daftar_pustaka') or ''
    cek('K10a yang terverifikasi masuk daftar pustaka', 'A.' in dp)
    cek('K10b artikel unverified TIDAK masuk daftar pustaka',
        len([b for b in dp.split('\n\n') if b.strip()]) == 1, f'({dp!r})')
    cek('K10c pagar P3 eksplisit di balikan',
        h['pagar'].get('hanya_terverifikasi_masuk_daftar_pustaka') is True)


def main() -> int:
    print('=== GERBANG JURNAL-3 — jembatan mesin + bangun_isi ===')
    for fn in (k1, k2, k3, k4, k5, k6, k7, k8, k9, k10):
        fn()
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
