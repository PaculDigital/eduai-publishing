"""JURNAL — simpan/baca daftar artikel per BAB + pagar batas 8 (06Okt26).

📌 ACC Bos 06Okt26 (Opsi A): TIDAK bikin tabel baru. Data dititipkan di
   kolom yang SUDAH ADA di tabel `profil_dokumen`:
       · jurnal_json  (TEXT)      — daftar artikel per bab (JSON)
       · jurnal_sidik (VARCHAR64) — sidik judul+kk (anti pakai data basi)
   Pola ini MENIRU `peta_json` + `peta_sidik` yang SUDAH TERBUKTI di produksi.

📌 PEMISAHAN TUGAS (sengaja):
   · `app/pustaka.py`  = MESIN PENCARI (murni hitung, tidak simpan apa pun)
   · `app/jurnal.py`   = INGATAN  (simpan/baca/hitung) ← berkas ini
   ⇒ Tidak mengubah pustaka.py sama sekali.

📌 PUTUSAN BOS yang dipegang modul ini:
   · Batas artikel MANUAL = 8 SELALU per bab (bukan 30%, bukan tergantung AI)
   · Artikel boleh DIPAKAI ULANG di bab lain tanpa hitung dobel
   · Artikel terverifikasi = yang `doi_status` in ('verified','no_doi')
     (aturan yang SAMA dengan pustaka.daftar_pustaka_apa7 — pagar P3)

📌 BENTUK jurnal_json:
   {
     "BAB II": [ {artikel...}, ... ],           # daftar per bab
     "_manual": { "BAB II": ["<kunci>", ...] }  # kunci artikel manual per bab
   }
   Kunci artikel = dipakai untuk dedup + "dipakai ulang" antar bab.
   Tiap artikel BENTUKNYA SAMA dengan app/pustaka.py (title/authors/year/
   journal/doi/garuda_id/doi_status) + tambahan `asal` ('ai'|'manual').
"""
from __future__ import annotations

import hashlib
import json
import logging

log = logging.getLogger('eduai.jurnal')

#  ── Putusan Bos 06Okt26: batas artikel manual per bab ──
BATAS_MANUAL_PER_BAB = 8

#  ── Kunci artikel yang dianggap terverifikasi (sama dgn pustaka P3) ──
STATUS_OK = ('verified', 'no_doi')


# ══════════════════════════════════════════════════════════════════════
#  BACA / TULIS (aman terhadap JSON rusak & kolom kosong)
# ══════════════════════════════════════════════════════════════════════
def baca(prof) -> dict:
    """Baca jurnal_json jadi dict. Kolom kosong / JSON rusak → {}."""
    if prof is None:
        return {}
    mentah = getattr(prof, 'jurnal_json', '') or ''
    if not mentah.strip():
        return {}
    try:
        d = json.loads(mentah)
        return d if isinstance(d, dict) else {}
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] jurnal_json rusak (%s) → dianggap kosong',
                    type(e).__name__)
        return {}


def tulis(prof, data: dict, sidik: str = '') -> None:
    """Tulis daftar ke kolom. TIDAK commit — pemanggil yang commit.

    (Sama seperti pola peta_json: simpan di fungsi, commit di pemanggil,
    supaya bisa digabung dengan perubahan lain dalam 1 transaksi.)
    """
    if prof is None:
        return
    prof.jurnal_json = json.dumps(data or {}, ensure_ascii=False)
    if sidik:
        prof.jurnal_sidik = sidik


# ══════════════════════════════════════════════════════════════════════
#  SIDIK — anti "pakai data basi" (pola peta_sidik)
# ══════════════════════════════════════════════════════════════════════
def sidik(judul: str, kata_kunci: str = '') -> str:
    """SHA-256 dari judul + kata kunci (dinormalkan).

    Kalau user mengubah JUDUL atau KATA KUNCI, sidiknya berubah ⇒ hasil
    pencarian lama TIDAK dipakai ulang (harus cari baru).
    """
    bahan = f'{(judul or "").strip().lower()}|{(kata_kunci or "").strip().lower()}'
    return hashlib.sha256(bahan.encode('utf-8')).hexdigest()


def sidik_cocok(prof, judul: str, kata_kunci: str = '') -> bool:
    """True kalau hasil tersimpan masih SEKUKUH judul+kk yang diminta."""
    if prof is None:
        return False
    lama = getattr(prof, 'jurnal_sidik', '') or ''
    return bool(lama) and lama == sidik(judul, kata_kunci)


# ══════════════════════════════════════════════════════════════════════
#  KUNCI & DEDUP
# ══════════════════════════════════════════════════════════════════════
def kunci(a: dict) -> str:
    """Kunci unik sebuah artikel — dipakai untuk dedup & pakai-ulang.

    Urutan prioritas: DOI → garuda_id → judul+tahun. Huruf kecil semua.
    """
    doi = (a.get('doi') or '').strip().lower()
    if doi:
        for pre in ('https://doi.org/', 'http://dx.doi.org/'):
            if doi.startswith(pre):
                doi = doi[len(pre):]
        return f'doi:{doi}'
    gid = a.get('garuda_id')
    if gid:
        return f'garuda:{gid}'
    judul = (a.get('title') or '').strip().lower()
    th = a.get('year') or 0
    return f'judul:{judul}|{th}'


def _semua_bab(data: dict) -> dict[str, list[dict]]:
    """Bab yang berisi DAFTAR artikel (lewati kunci bantu seperti '_manual')."""
    return {k: v for k, v in (data or {}).items()
            if not k.startswith('_') and isinstance(v, list)}


def daftar(data: dict, bab: str) -> list[dict]:
    """Daftar artikel satu bab."""
    return list(_semua_bab(data).get(str(bab)) or [])


# ══════════════════════════════════════════════════════════════════════
#  TAMBAH / HAPUS (dengan pagar batas 8)
# ══════════════════════════════════════════════════════════════════════
def jumlah_manual(data: dict, bab: str) -> int:
    """Berapa artikel MANUAL tercatat untuk bab ini (hitungan per bab)."""
    return len(((data or {}).get('_manual') or {}).get(str(bab)) or [])


def boleh_tambah_manual(data: dict, bab: str) -> bool:
    """Pagar Bos: maks 8 artikel manual per bab."""
    return jumlah_manual(data, bab) < BATAS_MANUAL_PER_BAB


def sisa_slot_manual(data: dict, bab: str) -> int:
    """Sisa slot manual bab ini (untuk ditampilkan ke user)."""
    return max(0, BATAS_MANUAL_PER_BAB - jumlah_manual(data, bab))


def tambah(data: dict, bab: str, artikel: list[dict] | dict,
           asal: str = 'ai') -> dict:
    """Tambah artikel ke satu bab. Dedup otomatis. Pagar batas utk 'manual'.

    Return data BARU (tidak mengubah input). Kunci: tambahkan pemanggil
    memeriksa `boleh_tambah_manual()` lebih dulu bila asal='manual'.
    """
    data = dict(data or {})
    bab = str(bab)
    if not isinstance(artikel, list):
        artikel = [artikel]

    sekarang = list(_semua_bab(data).get(bab) or [])
    sudah = {kunci(a) for a in sekarang}
    manual = list(((data.get('_manual') or {}).get(bab)) or [])
    diset_manual = set(manual)

    for a in artikel:
        if not isinstance(a, dict):
            continue
        k = kunci(a)
        if k in sudah:
            continue                        # dedup — tidak dobel
        a2 = {**a, 'kunci': k, 'asal': (a.get('asal') or asal)}
        #  pagar: artikel manual tidak boleh melewati batas
        if a2.get('asal') == 'manual':
            if len(manual) >= BATAS_MANUAL_PER_BAB:
                log.info('[jurnal] batas %d manual bab %s tercapai — dilewati',
                         BATAS_MANUAL_PER_BAB, bab)
                continue
            manual.append(k)
            diset_manual.add(k)
        sekarang.append(a2)
        sudah.add(k)

    data[bab] = sekarang
    _m = dict(data.get('_manual') or {})
    _m[bab] = manual
    data['_manual'] = _m
    return data


def hapus(data: dict, bab: str, k: str) -> dict:
    """Buang 1 artikel (berdasarkan kunci) dari sebuah bab."""
    data = dict(data or {})
    bab = str(bab)
    sekarang = [a for a in (_semua_bab(data).get(bab) or [])
                if kunci(a) != k]
    data[bab] = sekarang
    _m = dict(data.get('_manual') or {})
    _m[bab] = [x for x in (_m.get(bab) or []) if x != k]
    data['_manual'] = _m
    return data


# ══════════════════════════════════════════════════════════════════════
#  PAKAI ULANG ANTAR BAB (putusan Bos: tanpa hitung dobel)
# ══════════════════════════════════════════════════════════════════════
def sudah_dipakai_di(data: dict, k: str) -> list[str]:
    """Daftar bab yang memakai artikel berkunci `k` (untuk info ke user)."""
    return [b for b, lst in _semua_bab(data).items()
            if any(kunci(a) == k for a in lst)]


def pakai_di(data: dict, dari_bab: str, ke_bab: str, k: str) -> dict:
    """Pakai ulang artikel dari satu bab ke bab lain.

    ⚠️ TIDAK menambah hitungan manual di bab tujuan (putusan Bos: pakai
    ulang tidak dihitung dobel) — supaya user tidak dihukum karena
    memakai artikel yang sama di bab berbeda.
    """
    data = dict(data or {})
    sumber = [a for a in daftar(data, dari_bab) if kunci(a) == k]
    if not sumber:
        return data
    ke = str(ke_bab)
    sekarang = list(_semua_bab(data).get(ke) or [])
    sudah = {kunci(a) for a in sekarang}
    if k in sudah:
        return data                          # sudah ada di bab tujuan
    baru = {**sumber[0], 'dipakai_juga_di': sorted(
        set((sumber[0].get('dipakai_juga_di') or []) + [str(dari_bab)]))}
    sekarang.append(baru)
    data[ke] = sekarang
    return data


def pilihan_bab_tujuan(data: dict, bab_asal: str,
                       sudah: list[str] | None = None,
                       baku: list[str] | None = None) -> list[dict]:
    """Daftar bab yang bisa dipilih untuk MEMAKAI ULANG sebuah artikel.

    ⚠️ MURNI (tanpa DB/jaringan) supaya bisa diuji perilakunya.

    WAJIB memuat SEMUA bab baku naskah — BUKAN hanya bab yang sudah
    berisi artikel. Sebab inti permintaan Bos (13Okt26): artikel BAB III
    dipakai di BAB II yang MASIH KOSONG.

    🚨 BUG yang ditemukan 13Okt26 lewat uji klik produksi: dulu rutenya
       `for b in bab_terisi(data)` SAJA ⇒ BAB II tidak pernah muncul
       sebagai pilihan karena belum berisi. Gerbang yang hanya memeriksa
       TEKS KODE tidak menangkapnya (tetap lulus saat disuntik).

    Setiap entri: {'bab', 'jumlah', 'asal', 'sudah'}
      asal  = True bila ini bab yang sedang dibuka (tidak boleh dicentang)
      sudah = True bila artikel sudah dipakai di bab itu
    """
    sudah = list(sudah or [])
    baku = list(baku or ['BAB I', 'BAB II', 'BAB III'])
    terisi: dict[str, int] = {}
    for b in bab_terisi(data):
        nama = (b or {}).get('bab') or ''
        if nama:
            terisi[nama] = (b or {}).get('jumlah') or 0

    urut, dilihat = [], set()
    for nama in baku + sorted(terisi):
        if nama in dilihat:
            continue
        dilihat.add(nama)
        urut.append(nama)

    return [{
        'bab': nama,
        'jumlah': terisi.get(nama, 0),
        'asal': nama == str(bab_asal),
        'sudah': nama in sudah,
    } for nama in urut]


def pakai_di_banyak(data: dict, dari_bab: str, ke_bab: list[str], k: str) -> dict:
    """Centang BANYAK bab sekaligus (putusan Bos 13Okt26: "2. Bisa 2 2nya").

    Beda dengan `pakai_di()` yang satu-satu, ini menerima DAFTAR bab tujuan
    supaya user cukup mencentang lalu tekan Simpan SEKALI.

    ⚠️ Sama seperti `pakai_di()`: TIDAK menambah hitungan manual, TIDAK
    menggandakan entri daftar pustaka, dan TIDAK menghapus dari bab asal.
    Bab asal dilewati (tidak mungkin dobel dengan dirinya sendiri).
    """
    for ke in (ke_bab or []):
        ke = str(ke or '').strip()
        if not ke or ke == str(dari_bab):
            continue
        data = pakai_di(data, dari_bab, ke, k)
    return data


def lepas_dari(data: dict, bab: str, k: str) -> dict:
    """Lepas artikel (berkunci `k`) HANYA dari satu bab.

    ⚠️ Putusan Bos 13Okt26: membuang di satu bab TIDAK menghapus di bab
    lain — yang dihapus cuma yang ditunjuk. Dipakai untuk membatalkan
    "pakai ulang" tanpa menghapus artikel aslinya.
    """
    return hapus(data, bab, k)


# ══════════════════════════════════════════════════════════════════════
#  UNTUK DAFTAR PUSTAKA & SITASI (pagar P3 dipertahankan)
# ══════════════════════════════════════════════════════════════════════
def terverifikasi(a: dict) -> bool:
    """True hanya kalau artikel lolos audit (aturan SAMA dgn pustaka P3)."""
    st = (a.get('doi_status') or '').strip()
    if st == 'verified':
        return True
    if st == 'no_doi' and a.get('garuda_id'):
        return True
    return False


def semua_artikel(data: dict) -> list[dict]:
    """Semua artikel dari SEMUA bab, sudah dibuang kembar (untuk daftar pustaka)."""
    lihat: dict[str, dict] = {}
    for _b, lst in _semua_bab(data).items():
        for a in lst:
            k = a.get('kunci') or kunci(a)
            if k not in lihat:
                lihat[k] = a
    return list(lihat.values())


def layak_sitasi(data: dict) -> list[dict]:
    """Artikel yang BOLEH dipakai sitasi + masuk daftar pustaka."""
    return [a for a in semua_artikel(data) if terverifikasi(a)]


def tidak_layak(data: dict) -> list[dict]:
    """Artikel yang BELUM terverifikasi — ditampilkan jujur, TIDAK dipakai."""
    return [a for a in semua_artikel(data) if not terverifikasi(a)]


# ══════════════════════════════════════════════════════════════════════
#  JEMBATAN KE MESIN PENCARIAN (ACC Bos 06Okt26)
# ══════════════════════════════════════════════════════════════════════
def _bersihkan(a: dict, asal: str) -> dict:
    """Ambil HANYA kunci yang dikenal + tandai asal. Bentuk tetap sama."""
    return {
        'title': (a.get('title') or '').strip(),
        'authors': (a.get('authors') or '').strip(),
        'year': a.get('year') or 0,
        'journal': (a.get('journal') or '').strip(),
        'doi': (a.get('doi') or '').strip(),
        'garuda_id': a.get('garuda_id'),
        'doi_status': (a.get('doi_status') or '').strip(),
        'cited_by_count': a.get('cited_by_count') or 0,
        'asal': asal,
    }


def cari_untuk_bab(judul: str, bab: str = '1', kata_kunci: str = '',
                   maks: int = 20, pakai_ai: bool = False) -> dict:
    """Panggil MESIN PENCARI (pustaka.cari_semua) lalu rapikan hasilnya.

    TIDAK menyimpan apa pun — pengembalian siap dipakai `tambah()`.
    Bab ikut dipertimbangkan: bab ganjil/genap tidak mengubah pencarian,
    tapi disertakan supaya pemanggil tidak perlu menyusun ulang.

    ⭐ 13Okt26 (putusan Bos 2A): `pakai_ai=True` ⇒ kalau KAMUS tidak
    mengenali judul, AI memetakan kata kunci (1 panggilan). Hasil kosong
    WAJIB dilaporkan jujur lewat `belum_dipetakan` / `sumber_kata_kunci`.

    ⚠️ Jalur AI di sini SINKRON. Dari RUTE (event loop hidup) pakai
    `cari_untuk_bab_konsep()` setelah memetakan lewat
    `pustaka.kata_kunci_ai_async()` — kalau tidak, `asyncio.run` meledak.
    """
    from . import pustaka as _pustaka
    tema = (kata_kunci or judul or '').strip()
    if not tema:
        return {'ok': False, 'pesan': 'judul/kata kunci kosong', 'artikel': []}
    h = _pustaka.cari_semua(tema, pakai_ai=pakai_ai)
    return _rapikan(h, tema, bab, maks)


def cari_untuk_bab_konsep(kw: dict, tema: str, bab: str = '1',
                          maks: int = 20) -> dict:
    """⭐ Jalur RUTE (13Okt26): pakai kata kunci yang SUDAH dipetakan.

    Dipakai `rute_jurnal.cari_ai` — kata kuncinya dipetakan lebih dulu
    lewat `pustaka.kata_kunci_ai_async()` (await, tanpa asyncio.run),
    lalu mesin pencari dijalankan di sini (sinkron, tidak butuh event loop).
    """
    from . import pustaka as _pustaka
    h = _pustaka.cari_semua_dengan_konsep(kw, tema)
    return _rapikan(h, tema, bab, maks)


def _rapikan(h: dict, tema: str, bab: str, maks: int) -> dict:
    """Samakan bentuk keluaran mesin → bentuk yang dipakai layar."""
    mentah = h.get('artikel') or []
    bersih = [_bersihkan(a, 'ai') for a in mentah[:maks] if isinstance(a, dict)]
    return {
        'ok': True, 'bab': str(bab), 'tema': tema,
        'artikel': bersih,
        #  ⭐ 13Okt26: jejak kata kunci (kamus/ai) + penanda "belum bisa
        #     dipetakan" supaya LAYAR bisa jujur, bukan diam-diam kosong.
        'sumber_kata_kunci': h.get('sumber_kata_kunci', ''),
        'belum_dipetakan': bool(h.get('belum_dipetakan')),
        'info': {'per_sumber': h.get('jumlah_per_sumber') or {},
                 'total_unik': h.get('total_unik') or 0,
                 'terverifikasi': h.get('terverifikasi') or 0},
    }


def cari_dan_simpan(prof, bab: str, judul: str, kata_kunci: str = '',
                    maks: int = 20, paksa: bool = False) -> dict:
    """LENGKAP: cek sidik → cari (kalau perlu) → simpan ke jurnal_json.

    Kalau hasil tersimpan masih SEKUKUH judul+kk (sidik cocok) dan tidak
    dipaksa → TIDAK cari ulang (hemat; pakai `simpanan=True`).
    Pemanggil WAJIB commit sendiri.
    """
    sid = sidik(judul, kata_kunci)
    if not paksa and sidik_cocok(prof, judul, kata_kunci):
        data = baca(prof)
        return {'ok': True, 'dari_simpanan': True, 'bab': str(bab),
                'artikel': daftar(data, bab), 'cari_ulang': False}

    hasil = cari_untuk_bab(judul, bab, kata_kunci, maks)
    if not hasil.get('ok'):
        return {'ok': False, 'pesan': hasil.get('pesan'), 'cari_ulang': True}

    data = tambah(baca(prof), bab, hasil['artikel'], asal='ai')
    tulis(prof, data, sid)
    return {'ok': True, 'dari_simpanan': False, 'bab': str(bab),
            'artikel': daftar(data, bab), 'info': hasil.get('info'),
            'cari_ulang': True}


def tambah_manual(prof, bab: str, artikel: list[dict] | dict) -> dict:
    """Tambah artikel MANUAL (sudah diaudit pemanggil) + pagar batas 8.

    Return {'ok', 'pesan', 'sisa', 'artikel'} — TIDAK commit.
    """
    data = baca(prof)
    if not boleh_tambah_manual(data, bab):
        return {'ok': False, 'kode': 'batas_manual',
                'pesan': (f'Kamu sudah menambahkan {BATAS_MANUAL_PER_BAB} artikel '
                          'untuk bab ini. Bagian ini sudah cukup ya — sisanya '
                          'dari pilihan EduAi supaya pembahasan tetap fokus.'),
                'sisa': 0, 'artikel': daftar(data, bab)}
    masuk = artikel if isinstance(artikel, list) else [artikel]
    bersih = [_bersihkan(a, 'manual') for a in masuk if isinstance(a, dict)]
    data = tambah(data, bab, bersih, asal='manual')
    tulis(prof, data)
    return {'ok': True, 'sisa': sisa_slot_manual(data, bab),
            'artikel': daftar(data, bab)}


def untuk_bangun_isi(data: dict, bab: str) -> list[dict]:
    """Daftar artikel satu bab, SIAP dikirim ke `kerangka.bangun_isi()`.

    Bentuknya dikembalikan ke bentuk pustaka (tanpa kunci internal `kunci`/
    `asal`) supaya `daftar_pustaka_apa7()` tetap bisa membacanya.
    """
    keluar = []
    for a in daftar(data, bab):
        bersih = {k: v for k, v in a.items()
                  if k not in ('kunci', 'asal', 'dipakai_juga_di')}
        keluar.append(bersih)
    return keluar


def data_kosong() -> dict:
    """Bentuk data saat belum ada apa pun (dipakai rute `lihat`)."""
    return {'bab': {}, 'sidik': ''}


def bab_terisi(data: dict) -> list[dict]:
    """Ringkas bab mana saja yang sudah punya artikel (untuk tab)."""
    keluar = []
    for nama, isi in _semua_bab(data).items():
        if not nama:
            continue
        keluar.append({
            'bab': nama, 'jumlah': len(isi or []),
            'jumlah_manual': jumlah_manual(data, nama),
            'sisa_slot_manual': sisa_slot_manual(data, nama),
        })
    keluar.sort(key=lambda r: r['bab'])
    return keluar


def audit_isi_manual(doi: str) -> dict:
    """Audit artikel manual yang ditempel LEWAT DOI (pagar anti-halusinasi).

    Kembalikan {'doi_status', 'sebab'} — `doi_status` HANYA hasil mesin,
    user TIDAK pernah bisa mengisinya. Pola meniru `pustaka.audit_doi()`.

    'verified'  = DOI benar-benar ada di CrossRef
    ''          = tidak terverifikasi (tetap ditampilkan + tanda ⚠️,
                  user bisa membetulkan sendiri — putusan Bos 06Okt26)
    """
    d = (doi or '').strip()
    if not d:
        return {'doi_status': '', 'sebab': 'tanpa DOI'}
    from . import pustaka as _pustaka
    try:
        ada = bool(_pustaka.audit_doi(d))
    except Exception:                                         # noqa: BLE001
        return {'doi_status': '', 'sebab': 'mesin audit tidak menjawab'}
    return {'doi_status': 'verified' if ada else '',
            'sebab': 'CrossRef' if ada else 'tidak ditemukan di CrossRef'}
