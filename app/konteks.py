"""Konteks Tetangga — obat "kata tidak nyambung" antar bagian naskah.

=== SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
Asal: /opt/data/services/penelitian-bot/telegram-bot/agents/orchestrator.js
      baris 1108-1110:
        const bab1Text = (bab1Blocks||[]).map(b => b.text||'').join('\n').slice(0, 2000);
        const prevText = (previousBlocks||[]).map(b => b.text||'').join('\n').slice(0, 1000);
      baris 1112-1126 (bentuk prompt):
        BAB I (konteks):
        {bab1Text}

        BAGIAN SEBELUMNYA (konteks):
        {prevText}

        TUGAS SAAT INI:
        Hasilkan HANYA bagian **{config.label}** — {config.desc}

MASALAH YANG DIPECAHKAN: AI merevisi satu sub-bab tanpa tahu isi bab lain
-> istilah gonta-ganti, klaim bertabrakan, alur putus. Dengan menyisipkan
BAB I + potongan bagian sebelumnya, AI "tahu konteks".

BEDA DENGAN penelitian-bot (ADAPTASI WAJIB):
  - penelitian-bot MENULIS bagian baru  -> konteks = bahan mentah.
  - EduAi MEREVISI naskah yang ADA       -> konteks = dokumen tetangga yang
    SUDAH ADA di naskah user, plus Research Brief sebagai kebenaran tunggal.
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# Batas potong — persis mengikuti penelitian-bot (orchestrator.js 1108-1110).
# KENAPA ada batas: prompt yang terlalu panjang menaikkan biaya token DAN
# menambah waktu antrian. penelitian-bot sudah menguji angka ini.
BATAS_BAB1 = 2000       # BAB I / bagian acuan — paling penting, jatah terbesar
BATAS_SEBELUM = 1000    # bagian tepat sebelum target
BATAS_SESUDAH = 600     # tambahan EduAi: bagian sesudah (naskah sudah jadi)
BATAS_BRIEF = 2500      # Research Brief — kebenaran tunggal


def _teks_dari_blok(blok: Any) -> str:
    """Ratakan blok/str menjadi teks — padanan .map(b => b.text).join('\\n').

    Aman terhadap: None, list of str, list of dict, dict tunggal.
    """
    if blok is None:
        return ''
    if isinstance(blok, str):
        return blok
    if isinstance(blok, dict):
        return str(blok.get('text') or blok.get('teks') or '')
    if isinstance(blok, (list, tuple)):
        return '\n'.join(_teks_dari_blok(b) for b in blok if b)
    return str(blok)


def _bersihkan(teks: str) -> str:
    """Buang spasi/baris ganda supaya potongan tidak terbuang percuma."""
    teks = re.sub(r'[ \t]+', ' ', teks or '')
    teks = re.sub(r'\n{3,}', '\n\n', teks)
    return teks.strip()


def potong(teks: str, batas: int) -> str:
    """Potong di batas KATA (bukan tengah kata) lalu tambah penanda.

    KENAPA di batas kata: potongan di tengah kata membingungkan AI
    ("...kepemim" / "pinan...").
    """
    teks = _bersihkan(teks)
    if len(teks) <= batas:
        return teks
    potong_awal = teks[:batas]
    spasi = potong_awal.rfind(' ')
    if spasi > batas * 0.7:            # jangan potong terlalu pendek
        potong_awal = potong_awal[:spasi]
    return potong_awal.rstrip() + ' …[dipotong]'


def dari_struktur(
    struktur: list[dict[str, Any]] | None,
    bagian_target: str,
) -> dict[str, str]:
    """Ambil BAB I + bagian sebelum & sesudah target dari daftar struktur.

    `struktur` = [{'nomor': 'BAB I', 'judul': 'PENDAHULUAN', 'isi': '...'}, ...]
    Bagian acuan (BAB I) diambil sesuai penelitian-bot; tetangga diambil dari
    dokumen NYATA user (adaptasi EduAi).
    """
    if not struktur:
        return {'bab1': '', 'sebelum': '', 'sesudah': ''}

    # Cari indeks bagian target (cocokkan nomor atau judul)
    idx = -1
    target = (bagian_target or '').strip().lower()
    for i, b in enumerate(struktur):
        nomor = str(b.get('nomor') or '').strip().lower()
        judul = str(b.get('judul') or '').strip().lower()
        if target and (target == nomor or target in judul or judul in target):
            idx = i
            break

    # BAB I = bagian acuan. Cari yang nomornya mengandung 'bab i' / 'i'
    bab1 = ''
    for b in struktur:
        nomor = str(b.get('nomor') or '').strip().lower()
        if nomor in ('bab i', 'i', '1', 'bab 1', 'pendahuluan'):
            bab1 = _teks_dari_blok(b.get('isi'))
            break
    if not bab1 and struktur:
        bab1 = _teks_dari_blok(struktur[0].get('isi'))

    sebelum = ''
    sesudah = ''
    if idx > 0:
        sebelum = _teks_dari_blok(struktur[idx - 1].get('isi'))
    elif idx < 0 and len(struktur) > 1:
        # target tak ketemu -> pakai bagian terakhir sebagai "sebelumnya"
        sebelum = _teks_dari_blok(struktur[-2].get('isi'))
    if 0 <= idx < len(struktur) - 1:
        sesudah = _teks_dari_blok(struktur[idx + 1].get('isi'))

    return {'bab1': bab1, 'sebelum': sebelum, 'sesudah': sesudah}


def dari_peta(
    peta: list[dict[str, Any]] | None,
    bagian_target: str,
) -> dict[str, str]:
    """JEMBATAN: terjemahkan keluaran `state.petakan()` → bentuk konteks.py.

    🔴 BUG NYATA ke-19 (24Sep26, ACC Bos) — KUNCI TIDAK COCOK.
    `state.petakan()` mengeluarkan:
        {'section_id','section_title','isi_teks','char_count','kategori'}
    sedangkan `dari_struktur()` di berkas ini minta:
        {'nomor','judul','isi'}
    NOL IRISAN → disambung apa adanya, konteks tetangga GAGAL SENYAP
    (bab1/sebelum/sesudah kosong, prompt cuma brief + target). Terukur
    24Sep26: prompt POTONG cuma 676 karakter padahal target 367 karakter
    → AI hampir TANPA konteks; itu BAHAYA (bisa mengarang), bukan hemat.

    PERBAIKAN: (1) terjemahkan nama kunci; (2) cari BAB INDUK dari nomor
    sub-bab — '1.2' → BAB I, '2.1' → BAB II. Ini WAJIB supaya "BAB I
    (konteks)" benar-benar terisi walau target berupa sub-bab.

    KENAPA di sini (bukan di ai.py): aturan Bos — `app/ai.py` DILARANG
    disentuh tanpa ACC. Jembatan ditempatkan di sisi konteks.py supaya
    perubahan TERISOLASI dan `dari_struktur()` yang sudah terbukti tetap
    utuh (dipakai uji lama).
    """
    if not peta:
        return {'bab1': '', 'sebelum': '', 'sesudah': '', 'induk': ''}

    # (1) terjemahkan nama kunci petakan() → kunci konteks.py
    struktur: list[dict[str, Any]] = []
    for b in peta:
        if not isinstance(b, dict):
            continue
        struktur.append({
            'nomor': str(b.get('section_id') or b.get('nomor') or '').strip(),
            'judul': str(b.get('section_title') or b.get('judul') or '').strip(),
            'isi': b.get('isi_teks') if b.get('isi_teks') is not None else b.get('isi', ''),
            'kategori': str(b.get('kategori') or '').strip(),
        })
    if not struktur:
        return {'bab1': '', 'sebelum': '', 'sesudah': '', 'induk': ''}

    hasil = dari_struktur(struktur, bagian_target)

    # (2) cari BAB INDUK kalau yang dicari adalah sub-bab ('1.2' → '1').
    #     KENAPA: `dari_struktur()` hanya mengenal nomor ('bab i','i','1',…)
    #     sehingga '1.2' TIDAK dianggap anak BAB I → blok "BAB I (konteks)"
    #     kosong. Padahal justru itu konteks PALING PENTING (kata Bos:
    #     "bab sebelum dan sesudah, sub bab yang terkait").
    induk = ''
    nomor_target = str(bagian_target or '').strip()
    m = re.match(r'^\s*([1-9]|1[0-9]|2[0-9])\s*[.]', nomor_target)
    if m:
        nomor_induk = m.group(1)                     # '1.2' → '1'
        for b in struktur:
            n = str(b.get('nomor') or '').strip()
            nl = n.lower()
            if (n == nomor_induk
                    or nl in (f'bab {nomor_induk}', f'bab {nomor_induk.lower()}',
                              f'bab {_ROMAWI.get(nomor_induk, "")}'.lower())
                    or nl == _ROMAWI.get(nomor_induk, '').lower()):
                induk = _teks_dari_blok(b.get('isi'))
                break
        # jaring kedua: bagian kategori 'babN' (dari petakan)
        if not induk:
            for b in struktur:
                if str(b.get('kategori') or '').lower() in (f'bab{nomor_induk}', f'bab{nomor_induk} '):
                    induk = _teks_dari_blok(b.get('isi'))
                    break
        # jaring ketiga: judul mengandung kata kunci bab itu
        if not induk:
            kunci = {'1': 'pendahuluan', '2': 'tinjauan', '3': 'metode',
                     '4': 'hasil', '5': 'kesimpulan'}.get(nomor_induk)
            if kunci:
                for b in struktur:
                    if kunci in str(b.get('judul') or '').lower():
                        induk = _teks_dari_blok(b.get('isi'))
                        break

    #  Kalau target memang BAB (bukan sub-bab), 'bab1' dari dari_struktur()
    #  sudah benar — jangan ditimpa.
    hasil['induk'] = induk
    return hasil


_ROMAWI = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V',
           '6': 'VI', '7': 'VII', '8': 'VIII'}


def bangun_prompt(
    *,
    bagian_target: str,
    struktur: list[dict[str, Any]] | None = None,
    brief_ringkas: str = '',
    isi_saat_ini: str = '',
    komentar: str = '',
    peta: list[dict[str, Any]] | None = None,
) -> str:
    """Susun blok konteks untuk disisipkan ke prompt revisi.

    Bentuknya mengikuti penelitian-bot baris 1112-1126, dengan tambahan
    Research Brief (kebenaran tunggal) + bagian SESUDAH (naskah sudah jadi).

    `peta` (BARU, 24Sep26) = keluaran langsung `state.petakan()`. Kalau
    diberikan, nama kunci diterjemahkan otomatis lewat `dari_peta()`
    sehingga pemanggil TIDAK perlu tahu bentuk `konteks.py`.
    """
    if peta is not None and struktur is None:
        tetangga = dari_peta(peta, bagian_target)
    else:
        tetangga = dari_struktur(struktur, bagian_target)
        tetangga.setdefault('induk', '')
    bagian: list[str] = []

    #  ══ LAPIS BARU (Alternatif 5, 25Sep26) ══════════════════════════════
    #  JUDUL BAB & SUB-BAB: AI tahu SEDANG membahas apa.
    #  KALIMAT TERAKHIR sebelumnya + KALIMAT PERTAMA sesudahnya:
    #     benang masuk & keluar → hasil tidak "menggantung".
    #  Semua ini HANYA MENAMBAH INFO — tidak mengubah cara potong.
    kepala_peta = _peta_bagian(peta, bagian_target) if peta else ''
    if kepala_peta:
        bagian.append(kepala_peta)

    if brief_ringkas:
        bagian.append(f"=== KEBENARAN TUNGGAL PENELITIAN (WAJIB DIPATUHI) ===\n"
                      f"{potong(brief_ringkas, BATAS_BRIEF)}")

    # BAB acuan: pakai 'bab1' kalau ada; kalau target sub-bab → pakai 'induk'.
    acuan = tetangga.get('bab1') or tetangga.get('induk') or ''
    if acuan:
        label = ('BAB I (konteks)' if tetangga.get('bab1')
                 else f'BAB INDUK dari {bagian_target} (konteks)')
        bagian.append(f"=== {label} ===\n{potong(acuan, BATAS_BAB1)}")

    if tetangga['sebelum']:
        bagian.append(f"=== BAGIAN SEBELUMNYA (konteks) ===\n"
                      f"{potong(tetangga['sebelum'], BATAS_SEBELUM)}")

    if tetangga['sesudah']:
        bagian.append(f"=== BAGIAN SESUDAHNYA (konteks) ===\n"
                      f"{potong(tetangga['sesudah'], BATAS_SESUDAH)}")

    if isi_saat_ini:
        bagian.append(f"=== ISI BAGIAN YANG DIREVISI (saat ini) ===\n{isi_saat_ini}")

    if komentar:
        bagian.append(f"=== KOMENTAR/MASUKAN ===\n{komentar}")

    bagian.append(
        f"=== TUGAS SAAT INI ===\n"
        f"Revisi HANYA bagian **{bagian_target}**. "
        f"Jangan menulis ulang bagian lain. "
        f"Seluruh istilah dan variabel WAJIB sama dengan yang di atas."
    )

    hasil = '\n\n'.join(bagian)
    log.debug('[konteks] prompt konteks %s: %d karakter', bagian_target, len(hasil))
    return hasil


#  ═══════════════════════════════════════════════════════════════════════════
#  ALTERNATIF 5 (25Sep26) — RANTAI KONTEKS: 4 LAPIS TAMBAHAN
#  Usul Wulan, ACC Bos: "Opsi A, 5 - 1 - 2".
#
#  MASALAH YANG DIPECAHKAN: hasil revisi potongan bisa terasa "menggantung"
#  saat dibaca berurutan dengan tetangganya. Penyebabnya AI tidak tahu:
#     (a) sedang membahas sub-bab apa  → bisa salah nada/istilah
#     (b) kalimat terakhir sebelum dia → benang masuk hilang
#     (c) kalimat pertama sesudah dia  → benang keluar hilang
#
#  KEAMANAN: fungsi ini HANYA MEMBACA peta & MENAMBAH teks. Tidak mengubah
#  cara potong, tidak menyentuh ai.py. Kalau gagal → kembalikan '' (prompt
#  tetap jalan seperti sebelumnya).
#  ═══════════════════════════════════════════════════════════════════════════

_BATAS_BENANG = 300        # karakter kalimat benang (masuk/keluar)


def _isi_peta(blok: Any) -> str:
    """Ambil ISI dari satu butir PETA (`state.petakan()`), bukan struktur.

    🔴 KENAPA FUNGSI INI ADA (25Sep26): `_teks_dari_blok()` dibuat untuk
    bentuk STRUKTUR (kunci 'teks'/'text'/'isi'), sedangkan butir peta
    menyimpan isi di kunci **`isi_teks`**. Salah pakai → teks kosong →
    benang masuk/keluar TIDAK PERNAH muncul. Terbukti: 3 uji GAGAL.
    Urutan kunci di bawah ini sengaja: `isi_teks` DULU (peta), baru
    kunci lain (kalau suatu saat peta berubah bentuk).
    """
    if not isinstance(blok, dict):
        return ''
    for kunci in ('isi_teks', 'isi', 'teks', 'text', 'content', 'body'):
        v = blok.get(kunci)
        if isinstance(v, str) and v.strip():
            return v
    return ''


def _peta_bagian(peta: list[dict[str, Any]] | None,
                 bagian_target: str) -> str:
    """Susun blok 'PETA BAGIAN' — 4 lapis rantai konteks (Alternatif 5).

    Isi:
      · JUDUL BAB INDUK + JUDUL SUB-BAB TARGET  (sedang membahas apa)
      · POSISI: bagian ke-N dari M               (tahu awal/tengah/akhir)
      · KALIMAT TERAKHIR bagian SEBELUM (benang MASUK)
      · KALIMAT PERTAMA bagian SESUDAH  (benang KELUAR)
      · ISTILAH KUNCI dari brief/peta            (biar tidak ganti istilah)

    Return '' kalau peta kosong / target tidak ketemu (jujur, tidak menebak).
    """
    if not peta:
        return ''
    try:
        idx = None
        for i, x in enumerate(peta):
            if str(x.get('section_id', '')).strip() == str(bagian_target).strip():
                idx = i
                break
        if idx is None:
            return ''

        kini = peta[idx]
        judul_target = str(kini.get('section_title')
                           or kini.get('judul') or bagian_target).strip()
        judul_induk = str(kini.get('bab_judul')
                          or kini.get('induk_judul') or '').strip()

        baris: list[str] = ['=== PETA BAGIAN (konteks posisi) ===']
        if judul_induk:
            baris.append(f'BAB INDUK   : {judul_induk}')
        baris.append(f'SUB-BAB INI : {bagian_target} — {judul_target}')
        baris.append(f'POSISI      : bagian ke-{idx + 1} dari {len(peta)}')

        #  ── benang MASUK: kalimat terakhir bagian sebelumnya ──
        #  🔴 PERBAIKAN 25Sep26: JANGAN pakai `_teks_dari_blok()` — fungsi itu
        #     untuk bentuk STRUKTUR (kunci 'teks'/'text'), BUKAN peta.
        #     Untuk peta, isi ada di kunci `isi_teks` (lihat state.petakan()).
        if idx > 0:
            sebelum = _isi_peta(peta[idx - 1])
            kal = _kalimat_terakhir(sebelum)
            if kal:
                sid_seb = str(peta[idx - 1].get('section_id', '')).strip()
                baris.append(f'BENANG MASUK (akhir {sid_seb}): "{kal}"')

        #  ── benang KELUAR: kalimat pertama bagian sesudahnya ──
        if idx + 1 < len(peta):
            sesudah = _isi_peta(peta[idx + 1])
            kal = _kalimat_pertama(sesudah)
            if kal:
                sid_ses = str(peta[idx + 1].get('section_id', '')).strip()
                baris.append(f'BENANG KELUAR (awal {sid_ses}): "{kal}"')

        baris.append('⇒ Sambung kalimat pertama & terakhir hasil revisi dengan '
                     'benang di atas. JANGAN mengulang kalimat benang itu.')
        return '\n'.join(baris)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konteks] peta bagian gagal (%s) → dilewati', e)
        return ''


#  ══════════════════════════════════════════════════════════════════════════
#  PENYARING SITASI / DAFTAR PUSTAKA (25Sep26)
#  🔴 CELAH NYATA YANG DITUTUP: pada naskah NYATA (44.782 kar, sub-bab 2.1–2.5)
#     BENANG MASUK yang terpilih = "(Aldo Febriananto Kurniawan, Yuli
#     Trisetyono, Dodik Pramono, 2016)" — itu EKOR DAFTAR PUSTAKA, bukan
#     kalimat isi. AI lalu menerima "kalimat sebelumnya" yang bukan kalimat
#     naskah → sambungan jadi tidak bermakna.
#     ⇒ Benang masuk/keluar WAJIB melewati baris seperti itu.
#  ══════════════════════════════════════════════════════════════════════════
_POLA_SITASI = re.compile(
    r'^\s*[\("\']?'                       # boleh diawali tanda kutip/kurung
    r'[^)]{0,160}?'                       # nama-nama
    r'\(?\s*(?:19|20)\d{2}\s*[a-z]?\s*\)?'  # tahun
    r'[^\w]{0,4}$',                       # ekor tanda baca
    re.UNICODE,
)
#  baris yang jelas bagian daftar pustaka / catatan kaki
_POLA_BARIS_PUSTAKA = re.compile(
    r'^\s*(?:DAFTAR\s+PUSTAKA|REFERENSI|RUJUKAN|KEPUSTAKAAN|'
    r'BIBLIOGRAFI|CATATAN\s+KAKI|FOOTNOTE)\s*$',
    re.IGNORECASE,
)
#  nama depan yang menempel ke tahun tanpa kalimat utuh — penanda sitasi
#  🔴 2 BENTUK yang WAJIB tertangkap (temuan uji 25Sep26):
#     · "Romi Mardela. dkk, 2015"   → ada titik di tengah + "dkk"
#     · "Menurut Sugiyono (2017)."  → diawali kata pengantar sitasi
_POLA_NAMA_TAHUN = re.compile(
    r'(?:'
    r'(?:Menurut|Sesuai|Berdasarkan|Dalam|Pada)\s+'   # kata pengantar
    r'(?:[A-Z][\w.\'-]*\s*){1,6}'
    r'|\(?\s*(?:[A-Z][\w.\'-]*\s*){1,8}'              # atau langsung nama
    r')'
    r'(?:dkk\.?|et\s+al\.?)?'                         # penanda jamak
    r'[,\s]*\(?\s*(?:19|20)\d{2}[a-z]?\s*\)?',
    re.UNICODE,
)


def _kelihatan_sitasi(kal: str) -> bool:
    """True kalau kalimat ini sebenarnya SITASI/DAFTAR PUSTAKA, bukan kalimat isi.

    Tanda (dipakai bersama-sama, bukan sendiri-sendiri):
      · memuat pola "Nama, 2016" / "Nama (2016)" / "Nama dkk., 2019"
      · TIDAK punya kata kerja/kalimat wajar (pendek, didominasi nama)
      · didahului baris judul "DAFTAR PUSTAKA" (dicek pemanggil)

    🔴 LARANGAN: jangan buang kalimat isi yang SEKADAR menyebut tahun
       (mis. "Penelitian pada 2016 menunjukkan peningkatan sebesar …").
       Karena itu kalimat harus: pendek (<160 kar) DAN isinya nyaris hanya
       nama-tahun (sisa kata ≤ 6 kata) baru dianggap sitasi.
    """
    k = (kal or '').strip()
    if not k:
        return True
    if len(k) > 160:
        return False                       # kalimat panjang = kalimat isi
    cocok = _POLA_NAMA_TAHUN.findall(k)
    if not cocok:
        return False
    #  sisa setelah nama-tahun dibuang → kalau hampir tidak ada kata, itu sitasi
    sisa = _POLA_NAMA_TAHUN.sub(' ', k)
    sisa = re.sub(r'[^\w\s]', ' ', sisa)
    kata_sisa = [x for x in sisa.split() if len(x) > 2]
    return len(kata_sisa) <= 6


def _kalimat_terakhir(teks: str) -> str:
    """Ambil KALIMAT utuh terakhir dari sebuah teks (bukan potongan kata).

    🔴 PERBAIKAN 25Sep26: JANGAN potong keras di tengah kalimat — kalimat
    terakhir yang lebih panjang dari batas HARUS tetap utuh (kalau dipotong,
    AI menerima benang yang menggantung seperti "…variabel konte").
    Batas hanya dipakai bila kalimat memang keterlaluan panjang (>2× batas).
    """
    t = _bersihkan(teks or '')
    if not t:
        return ''
    kal = [k.strip() for k in re.split(r'(?<=[.!?])\s+', t) if len(k.strip()) > 20]
    if not kal:
        return potong(t, _BATAS_BENANG)
    #  🔴 BUANG ekor sitasi/daftar pustaka (25Sep26): pada naskah nyata benang
    #     masuk terpilih "(Aldo Febriananto Kurniawan, …, 2016)" — bukan
    #     kalimat isi. Ambil kalimat ISI terakhir yang benar-benar kalimat.
    while kal and _kelihatan_sitasi(kal[-1]):
        kal.pop()
    if not kal:
        return ''
    terakhir = kal[-1]
    #  kalimat wajar → pakai utuh. Keterlaluan panjang → potong di batas.
    if len(terakhir) <= _BATAS_BENANG * 2:
        return terakhir
    return potong(terakhir, _BATAS_BENANG)


def _kalimat_pertama(teks: str) -> str:
    """Ambil KALIMAT utuh pertama dari sebuah teks.

    🔴 PERBAIKAN 25Sep26: buang baris JUDUL dahulu (mis. "1.6 Kesenjangan
    Penelitian (Research Gap)") — kalau tidak, judul ikut terbawa sebagai
    "kalimat pertama" dan AI menerima konteks yang aneh.
    """
    t = _bersihkan(teks or '')
    if not t:
        return ''
    #  buang baris yang kelihatan judul (pendek, tanpa titik akhir, ada nomor)
    baris = [b.strip() for b in t.split('\n') if b.strip()]
    bersih: list[str] = []
    for b in baris:
        #  judul: pendek (<120 kar) TANPA titik di akhir, dan mengandung
        #  nomor bab (1.6) ATAU huruf kapital di awal semua kata
        kelihatan_judul = (
            len(b) < 120
            and not b.rstrip().endswith(('.', '!', '?', ';'))
            and (re.match(r'^\d+\.\d+', b) is not None
                 or re.match(r'^(BAB|BAB\s+[IVX]+)', b, re.I) is not None)
        )
        if kelihatan_judul and not bersih:
            continue                       # lewati judul di awal
        bersih.append(b)
    t2 = ' '.join(bersih) if bersih else t
    kal = [k.strip() for k in re.split(r'(?<=[.!?])\s+', t2) if len(k.strip()) > 20]
    if not kal:
        return potong(t2, _BATAS_BENANG)
    pertama = kal[0]
    if len(pertama) <= _BATAS_BENANG * 2:
        return pertama
    return potong(pertama, _BATAS_BENANG)


#  ═══════════════════════════════════════════════════════════════════════════
#  ALTERNATIF 1 (25Sep26) — PETA PARAGRAF BERLABEL
#  ACC Bos: "Opsi A, 5 - 1 - 2" · langkah ke-2.
#
#  MASALAH: dengan naskah penuh AI tidak tahu bagian mana yang dimaksud →
#  memilih sendiri → MELESET. Dengan paragraf berlabel + tetangga paragraf,
#  AI hanya melihat 3 paragraf → tidak ada ruang untuk meleset.
#
#  KEAMANAN: semua fungsi di bawah HANYA MEMBACA & MENAMBAH teks. Tidak
#  mengubah cara potong kuota, tidak menyentuh ai.py. Gagal → '' (jujur).
#  ═══════════════════════════════════════════════════════════════════════════

_BATAS_PAR_PENDEK = 40      # paragraf lebih pendek dari ini dianggap sampah/daftar
_BATAS_PAR_TAMPIL = 1400    # batas tampil 1 paragraf di blok konteks
MAKS_PARAGRAF = 400         # pengaman: naskah raksasa jangan bikin lambat


#  ══ PENYARING JENIS PARAGRAF (25Sep26, ACC Bos "1. A") ════════════════════
#  MASALAH TERUKUR: 32 dari 168 paragraf (19%) sebenarnya JUDUL / keterangan
#  gambar / penanda mesin — bukan paragraf isi. Kalau AI "merevisi judul",
#  STRUKTUR naskah rusak (anak judul hilang, nomor hilang).
#  ⇒ Tandai JENIS tiap paragraf; `pilih_paragraf()` melompati non-isi
#    KECUALI penunjuk posisi user memang menunjuk ke situ.
#  Pola diambil dari aturan yang SUDAH ADA di `state.py::_POLA_SUBBAB`
#  (_POLA_SUBBAB/`_subbab_palsu`) — jangan bikin kamus kedua.

_RE_JUDUL_SUB = re.compile(r'^\s*\d{1,2}\.\d{1,2}(\.\d{1,2})?\.?\s+\S')
_RE_JUDUL_BAB = re.compile(r'^\s*BAB\s+[IVX]+\b', re.IGNORECASE)
_RE_JUDUL_BAGIAN = re.compile(
    r'^\s*(?:gambar|tabel|diagram|grafik|bagan|lampiran)\s+'
    r'(?:\d+\.\d+|[IVX]+|\d+)\b', re.IGNORECASE)
_RE_KETERANGAN = re.compile(
    r'^\s*(?:sumber|catatan|keterangan|source)\s*[:.]', re.IGNORECASE)
_RE_PENANDA = re.compile(r'^\s*\[\[\s*/?\s*(?:TABEL|GAMBAR)\s*-', re.IGNORECASE)

#  batas panjang: judul jarang > 120 karakter
_BATAS_JUDUL_KAR = 120


def jenis_paragraf(teks: str) -> str:
    """Klasifikasi satu paragraf: 'penanda' | 'judul' | 'keterangan' | 'isi'.

    Dipakai `peta_paragraf()` supaya mesin tahu mana yang BOLEH direvisi.
    """
    t = (teks or '').strip()
    if not t:
        return 'penanda'                       # baris kosong
    if _RE_PENANDA.match(t):
        return 'penanda'                       # [[TABEL-n]] / [[GAMBAR-n]]
    if _RE_KETERANGAN.match(t):
        return 'keterangan'                    # "Sumber: BPS…"
    if len(t) <= _BATAS_JUDUL_KAR:
        if (_RE_JUDUL_SUB.match(t) or _RE_JUDUL_BAB.match(t)
                or _RE_JUDUL_BAGIAN.match(t)):
            return 'judul'
    #  judul TANPA nomor: baris pendek, tanpa titik akhir, judul-kapital
    if len(t) <= 90 and not t.endswith('.') and t.count(' ') <= 12:
        kata = t.split()
        if kata and sum(1 for w in kata if w[:1].isupper()) >= max(2, len(kata) // 2):
            return 'judul'
    return 'isi'


def paragraf_boleh_direvisi(par: dict[str, Any]) -> bool:
    """Apakah paragraf ini boleh jadi SASARAN revisi?

    Penanda/tabel/gambar/keterangan/judul = TIDAK (dilindungi).
    """
    return par.get('jenis', 'isi') == 'isi'


__JENIS_SUDAH_ADA__ = True


def petakan_paragraf(teks: str) -> list[dict[str, Any]]:
    """Pecah teks jadi daftar paragraf BERLABEL.

    Return daftar butir:
        {'label': 'P-01', 'posisi': 1, 'teks': '…isi paragraf…',
         'awal': 1200, 'akhir': 1560}
    Label dipakai HANYA di dalam prompt (tidak pernah ditampilkan ke user).
    """
    t = teks or ''
    if not t.strip():
        return []
    #  pisah per baris kosong (pola naskah Word hasil ekstraksi)
    mentah = re.split(r'\n\s*\n', t)
    hasil: list[dict[str, Any]] = []
    ofs = 0
    for m in mentah:
        isi = m.strip()
        panjang_asli = len(m)
        if len(isi) >= _BATAS_PAR_PENDEK:
            hasil.append({
                'label': f'P-{len(hasil) + 1:02d}',
                'posisi': len(hasil) + 1,
                'teks': isi,
                #  🆕 25Sep26 (ACC Bos "1. A"): TANDAI JENIS paragraf.
                #  'judul'/'keterangan'/'penanda' = DILINDUNGI dari revisi,
                #  tapi TETAP ada di peta (penomoran & posisi tidak bergeser).
                'jenis': jenis_paragraf(isi),
                'awal': ofs,
                'akhir': ofs + panjang_asli,
            })
            if len(hasil) >= MAKS_PARAGRAF:
                break
        ofs += panjang_asli + 1
    return hasil


def pilih_paragraf(par_list: list[dict[str, Any]], komentar: str,
                   teks_asli: str = '') -> int | None:
    """Cari INDEKS paragraf yang paling cocok dengan komentar.

    Pakai `app/cari_bagian.py` yang SUDAH ADA (jangan bikin mesin baru).
    Return None kalau tidak ketemu (jujur — jangan menebak).

    ALTERNATIF 2 (25Sep26, langkah ke-3 ACC Bos "Opsi A, 5 - 1 - 2"):
    kalau komentar TIDAK menyebut isi paragraf (mis. "perbaiki bahasa"),
    JANGAN menyerah — pakai PENUNJUK POSISI yang dipahami orang:
        "paragraf kedua"   → indeks 1
        "paragraf 3"       → indeks 2
        "awal" / "pertama" → indeks 0
        "akhir" / "terakhir"/ "penutup" → indeks terakhir
        "tengah"           → paragraf tengah
    Ini Rp 0 (tanpa AI) dan langsung membuat perintah biasa pun bisa
    tepat sasaran.
    """
    if not par_list or not (komentar or '').strip():
        return None
    try:
        from .cari_bagian import cari_bagian
        gabung = '\n\n'.join(p['teks'] for p in par_list)
        hasil = cari_bagian(gabung, komentar, teks_asli or '')
        if hasil and hasil.get('ketemu'):
            #  🔴 PERBAIKAN 25Sep26: JANGAN potong kasar `kutipan[:60]` —
            #     kutipan dari cari_bagian digabung dengan SPASI (baris baru
            #     jadi spasi), sehingga potongan melintasi baris TIDAK COCOK.
            #     Pakai `dasar` (kunci yang MEMANG ketemu) + bentuk rapat.
            kandidat: list[str] = []
            for k in (hasil.get('dasar') or '',
                      (hasil.get('kutipan') or '').strip()):
                k = str(k).strip()
                if k:
                    kandidat += [k, k[:40], k[:25], ' '.join(k.split()[:4])]

            for kand in kandidat:
                if len(kand) < 8:
                    continue
                for i, p in enumerate(par_list):
                    if ' '.join(kand.split()) in ' '.join(p['teks'].split()):
                        #  🆕 25Sep26: kalau yang cocok justru JUDUL/penanda,
                        #     cari paragraf ISI terdekat di bawahnya —
                        #     jangan menyasar judul (struktur naskah rusak).
                        return _geser_ke_isi(par_list, i)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konteks] pilih paragraf gagal (%s) → coba penunjuk posisi', e)

    #  ── PENUNJUK POSISI (Alternatif 2) — dipakai bila teks tidak ketemu ──
    idx = _paragraf_dari_penunjuk(par_list, komentar)
    #  ⚠️ penunjuk posisi = permintaan EKSPLISIT user ("paragraf 3") →
    #     hormati apa adanya, JANGAN digeser walau itu judul.
    return idx


def _geser_ke_isi(par_list: list[dict[str, Any]], i: int) -> int:
    """Geser indeks dari paragraf NON-ISI (judul/keterangan/penanda) ke ISI.

    Dipakai saat pencocokan TEKS jatuh ke judul — kita tidak boleh merevisi
    judul (ACC Bos "1.A": 19% paragraf sebenarnya judul).
    Urutan: cari ISI ke BAWAH dulu (paragraf yang dijelaskan judul), lalu ke ATAS.
    Kalau tidak ada ISI sama sekali → kembalikan apa adanya (jujur).
    """
    if 0 <= i < len(par_list) and par_list[i].get('jenis', 'isi') == 'isi':
        return i
    for j in range(i + 1, len(par_list)):
        if par_list[j].get('jenis', 'isi') == 'isi':
            return j
    for j in range(i - 1, -1, -1):
        if par_list[j].get('jenis', 'isi') == 'isi':
            return j
    return i


#  ══ ALTERNATIF 2 — PENUNJUK POSISI (25Sep26) ═══════════════════════════════
#  Dibuat karena hasil uji menunjukkan: kalau komentar memakai kata ORANG
#  BIASA ("paragraf kedua", "bagian akhir"), mesin tidak tahu harus ke mana
#  → balik ke naskah besar → AI meleset. Peta kata ini Rp 0, tanpa AI.

_KATA_URUTAN = {
    'pertama': 1, 'kedua': 2, 'ketiga': 3, 'keempat': 4, 'kelima': 5,
    'keenam': 6, 'ketujuh': 7, 'kedelapan': 8, 'kesembilan': 9,
    'kesepuluh': 10, 'kesebelas': 11, 'keduabelas': 12,
}
#  🔴 BUG WULAN 25Sep26 (ketemu dari uji): pola `paragraf\s+ke-?\s*([a-z]+)`
#     MENELAN kata "kedua" jadi "dua" (karena `ke-?` opsional lalu `\s*`
#     nol karakter → cocok lewat "paragraf " + "dua"). Akibatnya kamus
#     tidak pernah kena untuk "kedua"/"kesepuluh".
#     PERBAIKAN: kata urutan HARUS dimulai "ke", dan "ke-2" bentuk baris
#     sendiri. Jadi: (a) coba angka dulu; (b) baru KATA yang berawalan 'ke'.
_KATA_URUTAN_SEMUA = _KATA_URUTAN


def _paragraf_dari_penunjuk(par_list: list[dict[str, Any]],
                            komentar: str) -> int | None:
    """Tentukan indeks paragraf dari kata penunjuk posisi (Rp 0, tanpa AI).

    Mengerti: "paragraf kedua", "paragraf ke-3", "paragraf 3",
              "awal/pertama/pembuka", "akhir/terakhir/penutup", "tengah".
    Return None kalau tidak ada penunjuk (biar pemanggil memakai jalur lain).
    """
    if not par_list or not (komentar or '').strip():
        return None
    k = ' ' + ' '.join(str(komentar).lower().split()) + ' '
    n = len(par_list)

    #  1) "paragraf ke-3" — bentuk bersuku kata dgn tanda hubung (paling tegas)
    m = re.search(r'paragraf\s+ke-(\d{1,3})\b', k)
    if m:
        return _idx_am(panjang=n, no=int(m.group(1)))

    #  2) "paragraf 3" — angka tanpa "ke"
    m = re.search(r'paragraf\s+(\d{1,3})\b', k)
    if m:
        return _idx_am(n, int(m.group(1)))

    #  3) "paragraf kedua" — 🔴 WAJIB berawalan 'ke' supaya TIDAK telan 'dua'
    m = re.search(r'paragraf\s+(ke[a-z]{2,})\b', k)
    if m:
        kata = m.group(1)
        if kata in _KATA_URUTAN_SEMUA:
            return _idx_am(n, _KATA_URUTAN_SEMUA[kata])
        return None                     # "keseratus" dll → jujur, jangan tebak

    #  4) penunjuk posisi umum
    if re.search(r'\b(awal|pertama|pembuka)\b', k):
        return 0
    if re.search(r'\b(akhir|terakhir|penutup|ujung)\b', k):
        return n - 1
    if re.search(r'\b(tengah|pertengahan)\b', k):
        return n // 2
    return None


def _idx_am(panjang: int, no: int) -> int | None:
    """Terjemahkan nomor paragraf (1-basis) ke indeks (0-basis).

    Di luar batas → None (JUJUR — jangan menebak paragraf lain).
    """
    if 1 <= no <= panjang:
        return no - 1
    return None


def blok_paragraf(par_list: list[dict[str, Any]], idx: int,
                  jml_tetangga: int = 1) -> str:
    """Susun blok PARAGRAF SASARAN + tetangga (sebelum & sesudah).

    Return '' kalau idx di luar batas / data tidak cukup.
    """
    if not par_list or not isinstance(idx, int):
        return ''
    if idx < 0 or idx >= len(par_list):
        return ''
    try:
        baris: list[str] = ['=== PETA PARAGRAF (sasaran jelas) ===']
        baris.append(f'Paragraf SASARAN: {par_list[idx]["label"]} '
                     f'(ke-{par_list[idx]["posisi"]} dari {len(par_list)})')

        for j in range(max(0, idx - jml_tetangga), idx):
            p = par_list[j]
            baris.append(f'\n--- {p["label"]} (SEBELUMNYA, jangan diubah) ---\n'
                         f'{potong(p["teks"], _BATAS_PAR_TAMPIL)}')

        p = par_list[idx]
        baris.append(f'\n--- {p["label"]} (SASARAN — kerjakan HANYA ini) ---\n'
                     f'{potong(p["teks"], _BATAS_PAR_TAMPIL)}')

        for j in range(idx + 1, min(len(par_list), idx + 1 + jml_tetangga)):
            p = par_list[j]
            baris.append(f'\n--- {p["label"]} (SESUDAHNYA, jangan diubah) ---\n'
                         f'{potong(p["teks"], _BATAS_PAR_TAMPIL)}')

        baris.append(f'\n⇒ KERJAKAN HANYA {par_list[idx]["label"]}. '
                     f'Paragraf berlabel lain HANYA konteks — JANGAN diubah, '
                     f'JANGAN diulang isinya.')
        return '\n'.join(baris)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konteks] blok paragraf gagal (%s) → dilewati', e)
        return ''


def isi_paragraf(par_list: list[dict[str, Any]], idx: int) -> str:
    """Isi teks paragraf sasaran (untuk `isi_saat_ini`)."""
    if not par_list or idx is None or idx < 0 or idx >= len(par_list):
        return ''
    return str(par_list[idx].get('teks') or '')
