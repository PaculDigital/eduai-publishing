"""POLA PENULISAN — profiler pola dari peta surveyor (MURNI KODE, nol Jev).

Sumber kebenaran: RANCANGAN_PROFILER_POLA_09OKT2026.md (v3).

PERAN: pembaca peta, BUKAN penebak.
  - Surveyor (peta3_jev) sudah MEMUTUSKAN label tiap baris.
  - Modul ini HANYA membaca pola dari label itu (P7).
  - Kalau baris belum jelas labelnya → 'tidak_jelas' (jangan tebak).

KONSUMEN: hakim T4 (berurutan) + kontrak AI revisi (pola di titik yang direvisi).

JALAN:
    python3 -c "import app.pola_penulisan as pp; print(pp.profil_bab(...))"
"""
from __future__ import annotations

import re

# ── v4: cek "titik akhir" DIBUANG (terukur: 100% baris tak berakhir titik di Asih+Wulandari)
# ── v4: ambang panjang DIBUANG (terukur: p50 Wulandari = 1 kar/naskah PDF hancur)

# ── penanda butir (dipakai bersama; TIDAK memutuskan label, hanya bentuk)
BUTIR_RE = re.compile(r'^(?:[a-zA-Z]|\d+)[.)]\s|^[-•–]\s')

# ── skema nomor (DESKRIPTIF — §2.1 v3: num-dot DIPERTAHANKAN)
_POLA_DOTTED3 = re.compile(r'^\d+\.\d+\.\d+\b')
_POLA_DOTTED2 = re.compile(r'^\d+\.\d+\b')
_POLA_ALPHA = re.compile(r'^[A-Z]\.\s')
_POLA_PAREN = re.compile(r'^\d+\)\s')
_POLA_NUMDOT = re.compile(r'^\d+\.\s')
_POLA_BUKA_NOMOR = re.compile(r'^(?:\d+\.)+|^[A-Z]\.\s*|^\d+\)\s*')

_POLA_TABEL_CAPTION = re.compile(r'^\s*(?:Tabel|Gambar)\s+\d', re.IGNORECASE)


def _bersih(t: str) -> str:
    return ' '.join(str(t or '').split())


# ════════════════════════════════════════════════════════════════════════
# §3 — POLA PER BARIS (deterministik; label surveyor DIPERCAYA)
# ════════════════════════════════════════════════════════════════════════

def pola_baris(label: str, teks: str) -> str:
    """Peta label+teks → pola. TIDAK menebak ulang label surveyor (P7).

    Urutan (v4 — ambang panjang & titik-akhir DIBUANG, terbukti gagal di 2 naskah):
      1. judul (bab/subbab)               → 'judul_isi'
      2. sinyal struktur jelas (pipa/butir) → 'tabel' / 'butir'
      3. label DIKENALI surveyor           → DIPERCAYA
      4. label TAK DIKENAL                 → 'tidak_jelas' (belum diputuskan)
    """
    t = _bersih(teks)
    if label in ('bab', 'subbab'):
        return 'judul_isi'

    # Sinyal struktur jelas — berlaku untuk SEMUA label non-judul
    if t.count('|') >= 2:
        return 'tabel'
    if BUTIR_RE.match(t):
        return 'butir'

    # Label yang SUDAH DIPUTUSKAN surveyor → PERCAYA (P7: jangan tebak ulang)
    if label in ('paragraf', 'biasa'):
        return 'paragraf'

    # Label TAK DIKENAL ⇒ belum ada yang memutuskan ⇒ jangan tebak
    return 'tidak_jelas'


# ════════════════════════════════════════════════════════════════════════
# §2 — PROFIL PER BAB (deskriptif dari label surveyor)
# ════════════════════════════════════════════════════════════════════════

def skema_nomor(subbabs) -> str:
    """Skema penomoran sub-bab se-BAB. subbabs = [(i, teks), ...] label 'subbab'.

    v5 (koreksi BOS 09 Okt — "campuran" salah definisi):
      dotted-2 + dotted-3 dalam satu BAB = HIERARKI NORMAL, bukan campuran!
        "2.1" lalu "2.1.1" = wajar (induk lalu anaknya).
      `campuran` SEJATI hanya kalau DUA SISTEM BERBEDA bertabrakan:
        "2.1" (dotted) campur "A." (alpha) campur "1)" (paren).
      ⇒ Pagar P2 jangan salah tembak: jangan menolak renumber yang sebenarnya aman.
    """
    JENIS = {'dotted-2', 'dotted-3', 'alpha-dot', 'paren-num',
             'num-dot', 'tanpa-nomor'}
    hasil = []
    for _i, t in subbabs:
        s = _bersih(t)
        if _POLA_DOTTED3.match(s):
            hasil.append('dotted-3')
        elif _POLA_DOTTED2.match(s):
            hasil.append('dotted-2')
        elif _POLA_ALPHA.match(s):
            hasil.append('alpha-dot')
        elif _POLA_PAREN.match(s):
            hasil.append('paren-num')
        elif _POLA_NUMDOT.match(s):
            hasil.append('num-dot')      # v3: DIPERTAHANKAN (deskriptif)
        else:
            hasil.append('tanpa-nomor')
    unik = set(hasil)
    if not unik:
        return 'tanpa-nomor'
    if len(unik) == 1:
        return unik.pop()
    # v5: dotted-2 + dotted-3 = HIERARKI (normal) — bukan campuran
    if unik <= {'dotted-2', 'dotted-3'}:
        return 'dotted-hierarkis'
    return 'campuran'                     # campuran SEJATI: sistem berbeda


# v4 (Opsi A Bos): kata fungsi boleh kecil di dalam Title Case
_KATA_FUNGSI = {'dan', 'atau', 'di', 'ke', 'dari', 'pada', 'untuk', 'yang',
                'the', 'of', 'and', 'in', 'on', 'to', 'a', 'an', 'with'}


def _gaya_satu(s: str) -> str | None:
    """Gaya satu judul. v4 (Opsi A): DETERMINISTIK, definisi dipertegas.

    caps     = TIDAK ADA huruf kecil samasekali ("PENDAHULUAN")
    title    = SEMUA kata (kecuali kata fungsi) diawali huruf besar ("Landasan Teori")
    sentence = sisanya ("Latar belakang penelitian ini")
    """
    kata = [w for w in re.split(r'\s+', s) if w]
    if not kata:
        return None
    huruf = [c for c in s if c.isalpha()]
    if not huruf:
        return None
    if not any(c.islower() for c in huruf):
        return 'caps'                      # semua kapital — pasti
    # Title Case: semua kata BERISI HURUF wajib diawali besar,
    # kecuali kata fungsi yang bukan kata pertama
    salah = False
    for k, w in enumerate(kata):
        inti = [c for c in w if c.isalpha()]
        if not inti:
            continue
        if k > 0 and w.lower() in _KATA_FUNGSI:
            continue
        if not inti[0].isupper():
            salah = True
            break
    if not salah:
        return 'title'
    return 'sentence'


def gaya_judul(juduls) -> str:
    """Kapitalisasi judul se-BAB. juduls = [teks, ...]."""
    hasil = []
    for t in juduls:
        s = _POLA_BUKA_NOMOR.sub('', _bersih(t)).strip()
        g = _gaya_satu(s)
        if g:
            hasil.append(g)
    unik = set(hasil)
    if not unik:
        return 'tanpa-judul'
    return unik.pop() if len(unik) == 1 else 'campuran'


def butir_penanda(baris_biasa) -> str:
    """Penanda daftar di dalam bagian. baris_biasa = [teks, ...] label biasa/paragraf."""
    ada = set()
    for t in baris_biasa:
        s = _bersih(t)
        if re.match(r'^[a-z]\.\s', s):
            ada.add('alpha-dot')
        elif re.match(r'^\d+\.\s', s):
            ada.add('num-dot')
        elif t.startswith(('-', '•', '–')):
            ada.add('dash')
    if not ada:
        return 'tidak-ada'
    return ada.pop() if len(ada) == 1 else 'campuran'


def judul_curiga(subbabs) -> list[dict]:
    """Tanda CURIGA untuk HAKIM (bukan keputusan — hakim LAPOR, jangan BLOKIR).

    Sub-bab yang gaya judulnya 'sentence' (kalimat panjang berakhir biasa)
    atau tanpa nomor tapi panjang ⇒ diduga KALIMAT yang salah dilabeli judul.
    Terbukti nyata: Asih L000149 'Hasil pra-survei menunjukkan bahwa instrumen
    penelitian' — ini kalimat isi, bukan judul.

    Terkait heuristik Bos (§8.2 v3): baris berlabel subbab + awal '1.'/'2.' tunggal
    + diakhiri '?' ⇒ L000608 '1. Apakah…' (butir 1.2, bukan sub-bab).
    """
    curiga = []
    for item in subbabs:
        # terima (i, teks) ATAU (i, teks, sesuatu) — jangan meledak (bug 09 Okt)
        i, t = item[0], item[1] if isinstance(item, (tuple, list)) else (item, item)
        s = _POLA_BUKA_NOMOR.sub('', _bersih(t)).strip()
        alasan = []
        # v5b (09 Okt): 'gaya-kalimat' DIPERKETAT — jangan tuduh judul yang BENAR.
        #   `_gaya_satu` bilang 'sentence' untuk 'Uji heteroskedastisitas' padahal
        #   itu JUDUL sah. Jadi 'sentence' saja TIDAK CUKUP.
        #   Sinyal NYATA bukan-judul: (a) diakhiri titik/bukan-tanya ⇒ kelanjutan
        #   kalimat; (b) diawali sitasi '(Nama, thn)' ⇒ potongan isi; (c) >60 kar.
        # v5c (09 Okt) — DIPERKETAT KE 2 SINYAL YANG TIDAK PERNAH SALAH.
        #   TERUKUR 2× gagal (Wulan STOP, maks 2 percobaan):
        #     · ambang 60 kar   → 12 salah tuduh ('Uji heteroskedastisitas' = judul SAH)
        #     · ambang 6 kata   → 29 salah tuduh ('Uji Validitas Variabel X1' = judul SAH)
        #   AKAR: panjang/kata/kapitalisasi TIDAK memisahkan judul vs kalimat
        #   akademik — persis kata Bos: "mesin tidak bisa mengenali bentuk naskah".
        #   ⇒ SISAKAN hanya 2 sinyal yang PASTI, jangan tebak yang tidak pasti.
        if re.match(r'^\([^)]{2,40}\)\s*$', s) or re.match(r'^\([^)]{2,40}\)', s):
            alasan.append('awal-sitasi')              # '(Nama, thn)' = potongan isi
        if re.match(r'^\d+[.)]\s', _bersih(t)) and s.endswith('?'):
            alasan.append('butir-bertanya')           # heuristik Bos §8.2 — PASTI
        if re.match(r'^\d+[.)]\s', _bersih(t)) and s.endswith('?'):
            alasan.append('butir-bertanya')          # heuristik Bos §8.2
        if alasan:
            curiga.append({'i': i, 'teks': _bersih(t), 'alasan': alasan})
    return curiga


def nomor_terakhir(subbabs) -> dict:
    """Nomor berikutnya per induk. {'2': '2.5', '2.1': '2.1.4', ...}"""
    maks: dict[str, int] = {}
    for _i, t in subbabs:
        s = _bersih(t)
        m = re.match(r'^(\d+(?:\.\d+)*)\.?\s', s)
        if not m:
            continue
        bagian = m.group(1).split('.')
        if len(bagian) >= 2:
            induk = '.'.join(bagian[:-1])
            try:
                n = int(bagian[-1])
            except ValueError:
                continue
            maks[induk] = max(maks.get(induk, 0), n)
    keluar = {}
    for induk, n in maks.items():
        keluar[induk] = '%s.%d' % (induk, n + 1)
    return keluar


def ada_tabel(baris: list[str]) -> bool:
    for t in baris:
        s = _bersih(t)
        if s.count('|') >= 2 or _POLA_TABEL_CAPTION.match(s):
            return True
    return False


def rentang_bab(peta) -> list[dict]:
    """Potong peta jadi daftar BAB ASLI.

    v4 (BUG WULAN DIPERBAIKI — terukur): label 'bab' di peta3_jev BISA berisi
    baris DAFTAR ISI (anggota `sistematika`), bukan BAB asli!
      ASIH      : label bab [191,195,199,203,207] = SEMUA sistematika
                  → BAB ASLI ada di `gabung` {0,211,385,607,833}
      WULANDARI : label bab [459,468]           = sistematika
                  → BAB ASLI ada di `gabung` {0,471,7927,8141}

    ⇒ SUMBER BENAR = `gabung` (BAB asli) + label 'bab' yang BUKAN sistematika
      (lihat memory: "BAB ASLI = len(gabung) + label 'bab' non-sistematika").
    """
    baris = peta['baris']
    label = peta['label']
    sistematika = set(peta.get('sistematika') or [])
    gabung = peta.get('gabung') or {}

    idx_bab = [i for i in gabung if i < len(baris)]
    idx_bab += [i for i, l in label.items()
                if l == 'bab' and i not in sistematika and i < len(baris)]
    idx_bab = sorted(set(idx_bab))
    if not idx_bab:
        return []

    keluar = []
    for k, i in enumerate(idx_bab):
        akhir = idx_bab[k + 1] - 1 if k + 1 < len(idx_bab) else len(baris) - 1
        keluar.append({'mulai': i, 'akhir': akhir, 'judul': baris[i],
                       'nomor': None})
    return keluar


def profil_bab(peta) -> list[dict]:
    """Profil per BAB (5 field, §2). Nol panggilan Jev (P1)."""
    baris = peta['baris']
    label = peta['label']
    keluar = []
    for b in rentang_bab(peta):
        window = range(b['mulai'], b['akhir'] + 1)
        subbabs = [(i, baris[i]) for i in window if label.get(i) == 'subbab']
        # v4: gaya_judul HANYA dari SUB-BAB (jangan campur judul BAB "BAB I"
        #     yang selalu CAPS ⇒ bikin selalu 'campuran' — bug logika)
        juduls = [baris[i] for i in window if label.get(i) == 'subbab']
        biasa = [baris[i] for i in window
                 if label.get(i) in ('biasa', 'paragraf', None)]
        keluar.append({
            'mulai': b['mulai'],
            'akhir': b['akhir'],
            'judul': b['judul'],
            'skema_nomor': skema_nomor(subbabs),
            'gaya_judul': gaya_judul(juduls),
            'butir': butir_penanda(biasa),
            'nomor_terakhir': nomor_terakhir(subbabs),
            'ada_tabel': ada_tabel([baris[i] for i in window]),
            # v5: sinyal CURIGA untuk hakim (bukan keputusan — hakim LAPOR)
            'curiga': judul_curiga(subbabs),
        })
    return keluar


def profil_bab_terdekat(peta, posisi: int):
    """Profil BAB yang memuat `posisi` (atau BAB terdekat sebelumnya)."""
    kandidat = None
    for p in profil_bab(peta):
        if p['mulai'] <= posisi <= p['akhir']:
            return p
        if p['mulai'] <= posisi:
            kandidat = p
    return kandidat


# ════════════════════════════════════════════════════════════════════════
# §3b — POLA BERTETANGGA (lewati 'tidak_jelas')
# ════════════════════════════════════════════════════════════════════════

def pola_pada(peta, posisi: int):
    """Pola baris di `posisi` (dari label+teks). None kalau di luar rentang."""
    baris = peta['baris']
    label = peta['label']
    if posisi < 0 or posisi >= len(baris):
        return None
    return pola_baris(label.get(posisi), baris[posisi])


def _pola_sah(peta, posisi: int):
    """Pola yang BUKAN 'tidak_jelas' (v3 §8.3)."""
    p = pola_pada(peta, posisi)
    return None if p in (None, 'tidak_jelas') else p


def pola_tetangga(peta, posisi: int, jendela: int = 1):
    """Pola bagian sebelum & sesudah (bukan isinya). Lewati 'tidak_jelas'."""
    kiri = _pola_sah(peta, posisi - jendela)
    kanan = _pola_sah(peta, posisi + jendela)
    if kiri and kiri == kanan:
        return kiri
    if kiri:
        return kiri
    if kanan:
        return kanan
    return None


# ════════════════════════════════════════════════════════════════════════
# §5 — INTEGRASI (Opsi C; susunan 5 tingkat v3)
# ════════════════════════════════════════════════════════════════════════

PROFIL_DEFAULT = 'paragraf'


def pola_untuk_titik(peta, posisi: int, permintaan_pembimbing: dict | None = None):
    """Tentukan pola untuk titik revisi. Susunan 5 tingkat (v3 §5)."""
    if permintaan_pembimbing and permintaan_pembimbing.get('pola'):
        return permintaan_pembimbing['pola']        # ① PEMBIMBING menimpa
    sendiri = pola_pada(peta, posisi)
    if sendiri == 'tidak_jelas':
        return 'tidak_jelas'                        # ② TARGET tak pasti ⇒ LARANG
    if sendiri:
        return sendiri                              #    target sendiri sudah pasti
    tetangga = pola_tetangga(peta, posisi)          # ③ TETANGGA (lewati tidak_jelas)
    if tetangga:
        return tetangga
    profil = profil_bab_terdekat(peta, posisi)
    if profil and profil.get('skema_nomor') not in (None, 'campuran'):
        return profil                               # ④ PROFIL BAB
        # v5: 'dotted-hierarkis' LOLOS (hierarki normal) — hanya 'campuran'
        #     SEJATI yang ditolak
    return PROFIL_DEFAULT                           # ⑤ aman
