"""PENGELOMPOKAN CATATAN PEMBIMBING PER BAB (Tahap 2.5, ACC Bos 24Sep26).

MASALAH YANG DIPECAHKAN (kata Bos):
    "Jadi nantinya akan banyak catatan dari pembimbing. Bagaimana cara
     mengelolanya agar mudah dan tidak berantakan... Catatan pembimbing
     pasti banyak, dengan ruang side bar yang terbatas di samping apakah
     nyaman."

KEPUTUSAN BOS:
  1. Desain A = KEPALA BAB — baris lipat (akordeon), mirip Log Revisi.
  2. Bab TERBUKA otomatis = paling banyak catatan BARU.
  3. Kotak "Bagian mana?" jadi DROPDOWN dari bab terdeteksi (bukan ketik).
  4. Dokumen TANPA bab (perjanjian/nota/dll) → dikelompokkan PER HARI.
  5. Catatan tanpa bab → kelompok terakhir "Belum disebut bab-nya".

PRINSIP (aturan Bos: "jangan bangun mesin baru, sambungkan yang ada"):
    Deteksi bab SUDAH ADA di `app/state.deteksi_bab_besar()` — modul ini
    TIDAK mendeteksi ulang, hanya MENGELOMPOKKAN hasilnya + catatan.

⚠️ Modul ini TIDAK menyentuh naskah, TIDAK memanggil AI, TIDAK mengubah
   tabel lama. Murni penyusun tampilan (Rp 0).
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

#  Kelompok kunci — dipakai template supaya tidak ada salah tulis.
KUNCI_TANPA_BAB = '__tanpa_bab__'
KUNCI_DOKUMEN_UMUM = '__umum__'


# ══════════════════════════════════════════════════════════════════════
# 1. NORMALISASI NAMA BAB
# ══════════════════════════════════════════════════════════════════════
#  KENAPA PERLU: pembimbing mengisi bab dengan KETIK BEBAS di catatan LAMA
#  (sebelum ada dropdown). Jadi "BAB 3", "bab iii", "BAB III — Metode",
#  dan "BAB III" semuanya HARUS masuk kelompok yang SAMA. Kalau tidak,
#  catatan lama akan terpecah jadi beberapa kelompok palsu.
_POLA_NOMOR_BAB = re.compile(r'^\s*(?:BAB)\s*([IVXLC]+|\d+)\b', re.IGNORECASE)
_ROMAWI = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
           'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
           'XIV': 14, 'XV': 15}


def nomor_bab(teks: str) -> int | None:
    """Ambil NOMOR bab dari tulisan bebas. None kalau bukan bab.

    'BAB III — Metode' → 3 · 'BAB 3' → 3 · 'bab iii' → 3 · 'Metode' → None
    """
    m = _POLA_NOMOR_BAB.match(teks or '')
    if not m:
        return None
    t = m.group(1).upper()
    if t.isdigit():
        return int(t)
    return _ROMAWI.get(t)


def _kunci_bab(teks: str) -> str:
    """Kunci pengelompok untuk satu tulisan bab.

    Bab bernomor → 'BAB 3' (angka) supaya semua ejaan menyatu.
    Selain itu (mis. 'PENDAHULUAN' untuk artikel jurnal) → huruf kecil.
    """
    t = (teks or '').strip()
    if not t:
        return KUNCI_TANPA_BAB
    n = nomor_bab(t)
    if n is not None:
        return f'BAB {n}'
    return t.lower()


def _urut_bab(kunci: str):
    """Urutan tampil kelompok: bab 1, 2, 3… dulu; sisanya di belakang."""
    if kunci == KUNCI_TANPA_BAB:
        return (3, 0, '')            # paling akhir
    n = nomor_bab(kunci)
    if n is not None:
        return (0, n, '')            # bab bernomor → urut angka
    return (1, 0, kunci)             # non-bab (artikel jurnal) → alfabet


# ══════════════════════════════════════════════════════════════════════
# 2. AMBIL DAFTAR BAB DARI NASKAH (untuk dropdown)
# ══════════════════════════════════════════════════════════════════════
#  🔴 3 PERBAIKAN PRESISI 24Sep26 (ACC Bos, uji pakai proposal tesis +
#  jurnal asli). Ketiganya dikerjakan DI FILE INI — sengaja TIDAK menyentuh
#  `app/state.py`, karena file itu dipakai MESIN REVISI AI. Menyentuhnya =
#  mempertaruhkan naskah mahasiswa demi halaman pembimbing. (Pelanggaran
#  tiang T1.)

#  (1) JUDUL BAB JANGAN KEBABLASAN.
#      Bukti nyata: proposal tesis Bos menulis "BAB II" lalu baris berikut
#      catatan pribadi ("Bab 2 kita bahas nanti setelah fokus di latar
#      belakang") → label jadi panjang & menyesatkan. Judul bab yang benar
#      itu SINGKAT (2–6 kata). Takar pakai jumlah kata, bukan panjang huruf.
_MAKS_KATA_JUDUL = 10

#  (2) JUDUL YANG DIAWALI "BAB" LAIN = nyangkut.
#      Bukti nyata: di naskah Bos tertulis "BAB III" lalu "BAB IV" berdampingan
#      → label jadi "BAB III — BAB IV". Judul bab TIDAK MUNGKIN diawali kata
#      "BAB" lagi.
_POLA_JUDUL_BAB = re.compile(r'^\s*BAB\s*([IVXLC]+|\d+)\b', re.IGNORECASE)

#  (3) ARTIKEL JURNAL TIDAK PAKAI KATA "BAB".
#      Bukti nyata: jurnal Fransiskha 25.135 kar → 0 bab → dropdown kosong.
#      Padahal bagiannya jelas: PENDAHULUAN / METODE / HASIL / KESIMPULAN.
#      ⚠️ Dicocokkan HANYA pada baris PENDEK yang isinya PERSIS nama bagian
#      (judul bagian berdiri sendiri), supaya kalimat biasa yang kebetulan
#      memuat kata "Hasil" TIDAK tertangkap.
_NAMA_BAGIAN_ARTIKEL = (
    'PENDAHULUAN', 'LATAR BELAKANG',
    'TINJAUAN PUSTAKA', 'KAJIAN PUSTAKA', 'LANDASAN TEORI', 'STUDI LITERATUR',
    'METODE PENELITIAN', 'METODOLOGI PENELITIAN', 'METODE',
    'HASIL DAN PEMBAHASAN', 'HASIL DAN DISKUSI', 'HASIL DAN PEMBAHASAN',
    'PEMBAHASAN', 'HASIL',
    'KESIMPULAN DAN SARAN', 'KESIMPULAN', 'SIMPULAN DAN SARAN', 'SIMPULAN',
    'PENUTUP', 'SARAN',
)
#  Hanya nomor bagian di depan yang boleh mendahului nama bagian
#  ("2. METODE PENELITIAN", "BAB III METODE", "III. HASIL"). Sengaja
#  memakai \W* (bukan daftar angka romawi) supaya TIDAK ada grup yang bisa
#  salah tutup — pelajaran dari kegagalan regex 24Sep26.
_POLA_AWAL_BAGIAN = re.compile(r'^\s*(?:BAB\s*)?[\dIVXLC]*\W*', re.IGNORECASE)


def _rapikan_judul(judul: str) -> str:
    """Rapikan judul bab hasil deteksi — perbaikan PRESISI #1 dan #2.

    Kosongkan (return '') kalau judul TIDAK LAYAK jadi label bab:
      · terlalu panjang (> _MAKS_KATA_JUDUL kata) → kemungkinan kebablasan
        menelan kalimat/paragraf berikutnya (bukti: proposal Bos)
      · diawali kata "BAB" lain → dua kepala bab yang nyangkut (bukti: "BAB III — BAB IV")
      · berakhir titik-titik daftar isi → itu baris daftar isi

    Judul yang dirapikan hanya tampil di HALAMAN INI (dropdown). NOMOR bab
    tetap benar, jadi pembimbing tidak kehilangan bagian mana pun.
    """
    t = ' '.join((judul or '').split())
    if not t:
        return ''
    if len(t.split()) > _MAKS_KATA_JUDUL:
        return ''
    if _POLA_JUDUL_BAB.match(t):
        return ''
    if t.endswith('.') and '....' in t:
        return ''
    return t


def _bab_artikel(naskah: str) -> list[dict]:
    """Cari bagian artikel jurnal (TANPA kata 'BAB') — perbaikan PRESISI #3.

    Dipakai HANYA kalau detektor bab resmi tidak menemukan apa pun, jadi
    naskah skripsi/tesis/proposal TIDAK terpengaruh sama sekali.

    Cara kerja: periksa baris satu per satu. Baris dianggap JUDUL BAGIAN
    kalau (a) pendek (maks 60 huruf) dan (b) setelah nomor depan dibuang,
    isinya PERSIS salah satu nama bagian. Kalimat biasa tidak lolos.
    """
    if not (naskah or '').strip():
        return []
    hasil, sudah = [], set()
    for baris in (naskah or '').splitlines():
        b = ' '.join(baris.split())
        if not b or len(b) > 60:
            continue
        bersih = _POLA_AWAL_BAGIAN.sub('', b).strip(' .:-–—').upper()
        if bersih in _NAMA_BAGIAN_ARTIKEL and bersih not in sudah:
            sudah.add(bersih)
            hasil.append({'section_id': bersih,
                          'section_judul': bersih,
                          'label': bersih})
    return hasil


def daftar_bab_naskah(teks: str, maks: int = 40) -> list[dict]:
    """Daftar bab naskah untuk isi DROPDOWN — pakai detektor yang SUDAH ADA.

    Return: [{'section_id':'BAB I', 'section_judul':'PENDAHULUAN', 'label':…}]

    ⚠️ Kalau naskah TIDAK punya bab sama sekali (perjanjian, nota, invoice,
    artikel jurnal tanpa kata 'BAB'), kembaliannya KOSONG. Itu BUKAN error —
    template WAJIB punya jalan lain (kotak ketik), jangan sampai pembimbing
    tidak bisa menulis bab sama sekali.
    """
    if not (teks or '').strip():
        return []
    try:
        from . import state
        bab = state.deteksi_bab_besar(teks)
    except Exception:                                          # noqa: BLE001
        bab = []
    hasil = []
    for x in (bab or [])[:maks]:
        sid = (x.get('section_id') or '').strip()
        jdl = _rapikan_judul(x.get('section_title') or '')
        if not sid:
            continue
        label = f'{sid} — {jdl}' if jdl and jdl.upper() != sid.upper() else sid
        hasil.append({'section_id': sid, 'section_judul': jdl or sid,
                      'label': label})
    #  (3) tidak ada bab sama sekali → coba bagian artikel jurnal
    if not hasil:
        hasil = _bab_artikel(teks)[:maks]
    return hasil


# ══════════════════════════════════════════════════════════════════════
# 3. KELOMPOKKAN CATATAN
# ══════════════════════════════════════════════════════════════════════
def _label_umum(kunci: str, hari_ini: date) -> str:
    """Label kelompok PER HARI untuk dokumen tanpa bab (putusan Bos).

    ⚠️ Tanggal rusak/tidak sah JANGAN dilabeli "Hari ini" — itu BOHONG dan
    menyesatkan (pembimbing mengira catatan baru, padahal tanggalnya tidak
    terbaca). Lebih baik jujur: "Tanggal tidak jelas".
    """
    if not kunci or kunci == '0000-00-00':
        return 'Tanggal tidak jelas'
    try:
        tgl = datetime.strptime(kunci, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return 'Tanggal tidak jelas'
    selisih = (hari_ini - tgl).days
    #  ⚠️ Tanggal di MASA DEPAN (jam server meleset / data uji) juga tidak
    #  boleh jadi "Hari ini" — selisih negatif bukan kemarin/hari ini.
    if selisih < 0:
        selisih = abs(selisih)
        bulan = ('Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des')
        return f'{tgl.day} {bulan[tgl.month - 1]} {tgl.year}'
    if selisih == 0:
        return 'Hari ini'
    if selisih == 1:
        return 'Kemarin'
    if 2 <= selisih <= 6:
        return f'{selisih} hari lalu'
    bulan = ('Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
             'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des')
    return f'{tgl.day} {bulan[tgl.month - 1]} {tgl.year}'


def kelompokkan(rantai: list[dict], ada_bab: bool,
                hari_ini: date | None = None) -> list[dict]:
    """Susun rantai catatan jadi KELOMPOK per bab (atau per hari).

    `rantai` = hasil `pembimbing.rangkai()` — {kepala, terbaru, anak, …}.
    `ada_bab` = True kalau naskah punya bab (hasil `daftar_bab_naskah`).

    Return daftar kelompok:
        [{kunci, label, jumlah, jumlah_baru, catatan: [...], buka: bool}]

    ATURAN PENTING (rintangan yang harus ditutup):
      · Catatan yang bab-nya KOSONG → kelompok terakhir "Belum disebut
        bab-nya". JANGAN dibuang — dulu pembimbing pernah menulis catatan
        tanpa bab, catatan itu tetap miliknya.
      · Kalau naskah TIDAK punya bab → SEMUA masuk kelompok PER HARI.
      · Yang `buka=True` HANYA SATU: kelompok dengan catatan BARU terbanyak
        (putusan Bos). Serialnya `buka` dipakai template untuk atribut.
    """
    hari_ini = hari_ini or date.today()
    peta: dict[str, dict] = {}

    for s in (rantai or []):
        kepala = s.get('kepala')
        terbaru = s.get('terbaru') or kepala
        if terbaru is None:
            continue
        judul = (getattr(kepala, 'section_judul', '') or '')

        if ada_bab:
            kunci = _kunci_bab(judul)
            n = nomor_bab(judul)
            if n is not None:
                label = f'BAB {n}'
                if judul.strip():
                    bersih = re.sub(r'^\s*BAB\s*[IVXLC\d]+\s*[—\-–:]?\s*', '',
                                    judul.strip(), flags=re.IGNORECASE).strip()
                    if bersih:
                        label = f'BAB {n} — {bersih}'
            else:
                #  ⚠️ Kunci internal JANGAN tampil ke layar — pembimbing
                #  harus membaca bahasa manusia, bukan nama variabel.
                label = (judul.strip() if judul.strip()
                         else 'Belum disebut bab-nya')
        else:
            #  Dokumen umum: kelompok PER HARI (putusan Bos).
            dibuat = getattr(terbaru, 'dibuat', None)
            kunci = dibuat.strftime('%Y-%m-%d') if dibuat else '0000-00-00'
            label = _label_umum(kunci, hari_ini)

        g = peta.setdefault(kunci, {'kunci': kunci, 'label': label,
                                    'catatan': [], 'jumlah': 0,
                                    'jumlah_baru': 0})
        g['catatan'].append(s)
        g['jumlah'] += 1
        #  "Baru" = warna kuning (catatan pembimbing yang BELUM
        #  ditindaklanjuti) — sama dengan arti kuning di legenda.
        if getattr(terbaru, 'warna', '') == 'kuning':
            g['jumlah_baru'] += 1

    hasil = sorted(peta.values(),
                   key=lambda g: _urut_bab(g['kunci']) if ada_bab
                   else (0, 0, g['kunci']),
                   reverse=(not ada_bab))       # per-hari: terbaru di atas

    #  Susun catatan dalam kelompok: yang TERBARU di atas.
    for g in hasil:
        g['catatan'].sort(
            key=lambda s: (getattr(s.get('terbaru'), 'dibuat', None)
                           or datetime.min), reverse=True)

    #  ⚠️ SATU kelompok terbuka saja = yang paling banyak catatan BARU
    #  (putusan Bos). Kalau tidak ada yang baru → tak ada yang dibuka.
    if hasil:
        untuk_buka = max(hasil, key=lambda g: g['jumlah_baru'])
        for g in hasil:
            g['buka'] = (g is untuk_buka) and untuk_buka['jumlah_baru'] > 0
    return hasil


def warna_kelompok(g: dict) -> str:
    """Warna pita kelompok (dipakai Desain A untuk lencana angka).

    'kuning' = masih ada yang perlu ditinjau · 'hijau' = semua sudah oke.
    """
    return 'kuning' if g.get('jumlah_baru', 0) > 0 else 'hijau'
