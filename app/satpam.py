"""SATPAM bab — penjaga keputusan di depan mesin deteksi bab.

PERAN: PENJAGA (bukan pengganti).
  · Mesin lama (state.petakan) TETAP dipakai — dia yang MENCARI
  · Satpam memanggil Jev lewat 9router untuk MEMUTUSKAN:
      peta yang ditemukan mesin lama itu BENAR atau tidak
  · Jawaban:
      LOLOS (confidence >= 0,80)  → pakai peta mesin lama
      TANYA (0,50-0,79)           → ragu, serahkan ke tanya-mahasiswa
      TOLAK (< 0,50)              → satpam menolak; jangan pakai peta

PAGAR (WAJIB):
  P1 SELALU ADA JALAN KELUAR — satpam mati/gagal → pakai mesin lama
  P2 SATPAM MATI TIDAK BOLEH MENGHENTIKAN APP — semua galat ditelan
  P3 HANYA MENILAI STRUKTUR — tidak menyentuh isi/layout naskah
  P4 TIDAK MENYEBUT AI/nama model di teks user
  P5 AMBANG 0,80 (putusan Bos)

Tidak menyentuh kode lama. Modul baru. Bisa dimatikan lewat .env.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

# ── setelan (dari .env; kalau tidak ada pakai nilai aman)
AKTIF = (os.getenv('EDUAI_SATPAM_AKTIF') or '1').strip() not in ('0', 'false', 'no')
#  🛣️ JALAN TOL JEV (perintah Bos 09 Okt 2026): SATU-SATUNYA jalur = `app/jev.py`.
#     Jalur B (endpoint sarat-umum) SUDAH DIHAPUS TOTAL — tidak ada lagi di
#     berkas ini, dan TIDAK BOLEH dikembalikan.
BASE = 'jalan tol'          # tidak dipakai lagi; pemanggilan lewat `jev.tanya()`
MODEL = (os.getenv('EDUAI_SATPAM_MODEL') or 'SATPAM/typesafe/jev-1.13').strip()
# kunci: pakai kunci 9router yang SUDAH dipakai app (jangan buat kunci baru)
KUNCI = (os.getenv('EDUAI_SATPAM_KEY') or os.getenv('EDUAI_ROUTER_KEY') or '').strip()
BATAS_DETIK = float(os.getenv('EDUAI_SATPAM_TIMEOUT') or '60')
AMBANG_LOLOS = float(os.getenv('EDUAI_SATPAM_AMBANG') or '0.80')
AMBANG_TANYA = 0.50

#  ── PERTANYAAN PETA BAB (rancangan 04Okt26)
#
#  ✅ SKEMA JEV YANG BENAR (terukur ke `openrouter.ai/api/v1/systemone`
#     langsung, 07 Okt 2026 — lihat skill `typesafe-jev`):
#
#     · **nama pertanyaan BEBAS** apa saja (tidak dikirim ke model)
#     · **TIPE hanya 3**: `noul` · `choice` · `score`
#     · **`criteria` WAJIB PER-TIPE — ini akar 503 semu 07 Okt 2026:**
#         noul   → ⛔ **TIDAK BOLEH ada `criteria`** (bentuk apa pun ⇒ 400)
#         choice → **OBJEK**  {'opsi': 'deskripsi opsi'}
#         score  → **ARRAY**  ['tingkat 0', 'tingkat 1', …]   (2–10 tingkat)
#
#  ❌ CARA LAMA (DIHAPUS — BAHAYA, JANGAN DIPAKAI LAGI):
#     `{'type': 'noul', 'instructions': '…', 'criteria': 'Ya bila …'}` ⇒
#     HTTP 400 Zod `invalid_union` / `expected object, received string`,
#     yang DISAMAR jadi **HTTP 503** oleh 9router sehingga tampak
#     "9router/Jev rusak". Pernah membuat Wulan salah menyimpulkan
#     "skema Jev tertutup, hanya 3 nama" — **ITU KELIRU**.
#
#  ⚠️ PELAJARAN (07 Okt 2026): kalau Jev membalas 503/400, JANGAN menuduh
#     Jev. **PERIKSA BENTUK `criteria` DULU**, lalu periksa BAHAN-nya.
#     Jev jawab "tidak ada" padahal ada ⇒ biasanya BAHAN kurang, bukan Jev salah.
TANYA = {
    'jumlah_bab': {
        'instructions': ('Berapa bab akademik yang BENAR-BENAR ada di naskah ini? '
                         'Jangan hitung daftar isi, jangan hitung ringkasan, '
                         'hitung hanya bab yang punya isi.'),
        'type': 'choice',
        'criteria': {'0': 'tidak ada bab', '1': 'satu bab', '2': 'dua bab',
                     '3': 'tiga bab', '4': 'empat bab', '5': 'lima bab',
                     '6': 'enam bab', '7': 'tujuh bab', '8': 'lebih dari tujuh'},
    },
    'semua_romawi_sah': {
        'instructions': ('Apakah semua nomor bab di naskah ini memakai angka romawi '
                         'yang SAH (I, II, III, IV, V) — tidak ada yang salah tulis '
                         'atau melompat?'),
        'type': 'noul',
    },
    'berurutan': {
        'instructions': ('Apakah bab-bab di naskah ini tersusun BERURUTAN tanpa '
                         'melompat atau kembali ke belakang?'),
        'type': 'noul',
    },
    # ⭐ 05Okt26 (putusan Bos "A"): pertanyaan KE-4 — KEDALAMAN sub-bab.
    #    Tujuan: Jev MEMERIKSA sedalam apa naskah ini benar-benar berlapis;
    #    mesin Python lalu memakai kedalaman itu (Jev = mata, bukan hakim).
    #    Kalau Jev mati/ragu → mesin jatuh ke pola LAMA (2 tingkat) persis.
    'kedalaman_subbab': {
        'instructions': ('Sedalam apa naskah ini memakai penomoran BERTINGKAT '
                         'di dalam bab? Contoh: "2.1 Latar Belakang" = 2 '
                         'tingkat; "2.1.1 Responden" di dalam 2.1 = 3 tingkat; '
                         '"2.1.1.1 Kuesioner" di dalam 2.1.1 = 4 tingkat. '
                         'ABAIKAN daftar isi, daftar tabel, dan daftar pustaka — '
                         'lihat PENOMORAN DI DALAM ISI NASKAH saja.'),
        'type': 'choice',
        'criteria': {
            '0': 'tidak ada penomoran bertingkat sama sekali',
            '2': 'sampai 2 tingkat (mis. 1.1)',
            '3': 'sampai 3 tingkat (mis. 1.1.1)',
            '4': 'sampai 4 tingkat (mis. 1.1.1.1)',
            '5': '5 tingkat atau lebih dalam (mis. 1.1.1.1.1)',
        },
    },
}


def _susun_state(teks: str, peta: list[dict[str, Any]]) -> str:
    """Bahan untuk Jev: daftar bab YANG DITEMUKAN + daftar sub-bab + cuplikan.

    ⭐ 05Okt26: keadaan HARUS memuat DUA-DUANYA (bab besar & sub-bab) supaya
    Jev bisa memutuskan mana yang lebih tepat jadi satuan pekerjaan.
    Sebelumnya hanya peta pilihan mesin yang dikirim → Jev tak bisa menilai.
    """
    baris = []
    #  ⭐ 05Okt26 (putusan Bos "B"): AKAR presisi Jev rendah = bahan terlalu
    #     sedikit. Dulu `isi[:400]` → naskah 200rb kar, tiap bab cuma dapat
    #     0,2% isi → Jev salah hitung (bukti: 6/18 salah, SKRIPSI-S1-unhas
    #     mesin 6 bab → Jev bilang 1).
    #     Jev menghitung BAB, bukan membaca isi → yang ia butuh = DAFTAR
    #     JUDUL seluruh bab + posisinya, bukan cuplikan paragraf.
    for b in peta[:12]:
        judul = str(b.get('section_title') or b.get('section_id') or '?')[:70]
        isi = str(b.get('isi_teks') or '')
        cuplik = ' '.join(isi[:400].split())
        baris.append(f'{b.get("section_id")} — {judul}\n   isi: {cuplik}')

    # daftar BAB besar & sub-bab (dari mesin deteksi yang sudah ADA)
    bagian = []
    try:
        from .state import deteksi_bab_besar, deteksi_subbab
        besar = deteksi_bab_besar(teks)
        kecil = deteksi_subbab(teks)
        if besar:
            bagian.append('BAGIAN BESAR "BAB" YANG ADA: '
                          + ', '.join(f'{b["section_id"]} {str(b["section_title"])[:34]}'
                                      for b in besar[:10]))
        if kecil:
            bagian.append('BAGIAN KECIL SUB-BAB YANG ADA: '
                          + ', '.join(b['section_id'] for b in kecil[:20]))
    except Exception:
        pass

    # ⭐ 05Okt26 (putusan Bos "A"): BAHAN KEDALAMAN.
    #    Jev harus MELIHAT baris penomoran BERTINGKAT apa adanya dari isi
    #    naskah — bukan hanya daftar sub-bab 2 tingkat. Daftar isi dibuang
    #    dulu supaya Jev tidak tertipu (pelajaran lama: daftar isi = 93%
    #    kandidat palsu).
    try:
        from .state import buang_daftar_isi
        import re as _re
        bersih = buang_daftar_isi(teks)
        _p = _re.compile(
            r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
            _re.MULTILINE)
        _kandidat: list[str] = []
        _dalam: set[int] = set()
        for m in _p.finditer(bersih):
            nomor = f'{m.group(1)}{m.group(2)}'
            d = len([x for x in nomor.strip('.').split('.') if x])
            _dalam.add(d)
            if len(_kandidat) < 14 and d >= 3:
                _kandidat.append(f'{nomor} {m.group(3).strip()[:48]}')
        if _kandidat:
            bagian.append(
                'CONTOH BARIS BERTINGKAT DI ISI NASKAH (sesudah daftar isi '
                'dibuang): ' + ' | '.join(_kandidat))
        if _dalam:
            bagian.append('KEDALAMAN YANG MESIN LIHAT: '
                          f'maks {max(_dalam)} tingkat '
                          f'({sorted(_dalam)})')

        #  ⭐ 05Okt26 (putusan Bos "B"): BAHAN PENENTU — daftar SEMUA judul
        #     bab BESERTA posisi (%). Jev menghitung bab dari SINI, bukan dari
        #     cuplikan 400 kar. Kalau blok ini hilang, Jev kembali menebak.
        if besar:
            pjg = max(len(bersih), 1)
            _ur = []
            for b in besar:
                try:
                    pos = bersih.find(str(b.get('section_title') or ''))
                except Exception:                              # noqa: BLE001
                    pos = -1
                persen = int(100 * pos / pjg) if pos > 0 else -1
                _ur.append(f'  {b["section_id"]} ({persen}%) '
                           f'{str(b.get("section_title"))[:60]} '
                           f'[{b.get("char_count", 0):,} kar]')
            bagian.append('DAFTAR LENGKAP BAB YANG MESIN TEMUKAN '
                          f'({len(besar)} bab, urut posisi):\n'
                          + '\n'.join(_ur))
    except Exception:
        pass

    return ('NASKAH AKADEMIK — PEMETAAN BAGIAN\n'
            + ('\n'.join(bagian) + '\n\n' if bagian else '')
            + f'PETA YANG SEDANG DIPAKAI MESIN ({len(peta)} bagian, '
              'tiap bagian disertai 400 karakter isi awalnya):\n\n'
            + '\n\n'.join(baris)
            + f'\n\n[panjang naskah: {len(teks):,} karakter]')


def periksa(teks: str, peta: list[dict[str, Any]]) -> dict[str, Any]:
    """Tanya Jev: apakah peta bab ini benar?

    SELALU mengembalikan dict. TIDAK PERNAH melempar galat (P1 & P2).
    Bentuk: {'ok': bool, 'keputusan': 'lolos'|'tanya'|'tolak'|'mati',
             'jumlah_bab': int|None, 'confidence': float, 'alasan': str, ...}
    """
    mati = {'ok': False, 'keputusan': 'mati', 'jumlah_bab': None,
            'jumlah_bab_mesin': len(peta or []),
            'confidence': 0.0, 'romawi_sah': None, 'berurutan': None,
            'alasan': 'satpam tidak aktif', 'mentah': None}
    if not AKTIF or not teks or not peta:
        return mati

    #  🛣️ JALAN TOL JEV: satu-satunya jalur. Kalau Jev mati ⇒ 'mati' + sebab.
    from . import jev as _jev
    siap = _jev.cek_siap()
    if not siap['siap']:
        log.warning('[satpam] Jev belum siap: %s', siap['sebab'])
        return {**mati, 'alasan': f"Jev belum siap: {siap['sebab']}"}
    t0 = time.time()
    jawab = _jev.tanya(_susun_state(teks, peta), TANYA)
    if jawab is None:
        log.warning('[satpam] balasan tidak terbaca / Jev gagal')
        return {**mati, 'alasan': 'balasan tidak terbaca'}

    try:
        bb = jawab.get('jumlah_bab') or {}
        jumlah = bb.get('choice')
        conf = float(bb.get('confidence') or 0)
        romawi = (jawab.get('semua_romawi_sah') or {}).get('noul')
        urut = (jawab.get('berurutan') or {}).get('noul')
        # ⭐ 05Okt26 (putusan Bos "A"): kedalaman sub-bab yang Jev LIHAT.
        #    `None` = Jev tidak menjawab bagian ini → mesin pakai pola LAMA.
        _dl = (jawab.get('kedalaman_subbab') or {})
        _dl_pil = _dl.get('choice')
        kedalaman_jev = int(_dl_pil) if str(_dl_pil).isdigit() else None
    except Exception as e:                                   # P2
        return {**mati, 'alasan': f'jawaban tidak berbentuk: {type(e).__name__}'}

    if conf >= AMBANG_LOLOS:
        keputusan = 'lolos'
    elif conf >= AMBANG_TANYA:
        keputusan = 'tanya'
    else:
        keputusan = 'tolak'

    # ⭐ 05Okt26 (putusan Bos B): satpam TIDAK memilih peta.
    #    BAB dipakai untuk KONTEKS AI & panel Belajar;
    #    sub-bab dipakai untuk HARGA. Dua-duanya sah, sesuai keperluan.
    #    Satpam hanya memastikan JUMLAHNYA benar + menandai keganjilan.
    return {
        'ok': True,
        'keputusan': keputusan,
        'jumlah_bab': int(jumlah) if str(jumlah).isdigit() else None,
        'jumlah_bab_mesin': len(peta),
        'confidence': conf,
        'romawi_sah': romawi,
        'berurutan': urut,
        # ⭐ 05Okt26 (putusan Bos "A"): kedalaman yang JEV LIHAT (0/2/3/4/5)
        #    None = tidak dijawab → pemanggil WAJIB pakai pola LAMA (2 tingkat).
        'kedalaman_subbab': kedalaman_jev,
        'detik': round(time.time() - t0, 3),
        'alasan': f'satpam {keputusan} (keyakinan {conf:.2f})',
        'mentah': jawab,
    }


def _urai_balasan(mentah: str) -> dict[str, Any] | None:
    """Urai balasan 9router → dict answers.

    🚨 JEBAKAN TERUKUR (05Okt26): 9router membalas DUA bentuk menyatu:
        {json chat.completion}data: [DONE]
       JSON + penanda stream MENEMPEL tanpa newline. Cara naif
       (`split('\\n')`) menjadikan string raksasa tak terurai.
       Jalan benar: potong di 'data:' lebih dulu, baru urai per bagian.

    Bentuk 1 : choices[0].message.content = STRING berisi JSON  ← Jev
    Bentuk 2 : choices[0].message.content = dict               (lain)
    Bentuk 3 : answers langsung
    """
    def _ambil(d: Any) -> dict[str, Any] | None:
        if not isinstance(d, dict):
            return None
        try:
            isi = d['choices'][0]['message']['content']
            if isinstance(isi, str):
                return json.loads(isi)
            if isinstance(isi, dict):
                return isi
        except Exception:
            pass
        if 'answers' in d and isinstance(d['answers'], dict):
            return d['answers']
        if 'jumlah_bab' in d:
            return d
        return None

    # ① potong pada penanda stream, lalu urai tiap potongan
    for potong in mentah.split('data:'):
        potong = potong.strip()
        if not potong or potong.startswith('[DONE]'):
            continue
        try:
            d = json.loads(potong)
        except Exception:
            d = _json_awal(potong)
        if d is None:
            continue
        hasil = _ambil(d)
        if hasil:
            return hasil

    # ② cadangan: kalau seluruh teks satu JSON utuh
    try:
        return _ambil(json.loads(mentah))
    except Exception:
        return None


def _json_awal(teks: str) -> Any:
    """Ambil objek JSON PERTAMA yang utuh di dalam teks (abaikan ekor sampah)."""
    try:
        obj, _ = json.JSONDecoder().raw_decode(teks.lstrip())
        return obj
    except Exception:
        return None


def _periksa_skema(pertanyaan: dict[str, Any]) -> list[str]:
    """PAGAR SKEMA JEV — cegah `criteria` salah bentuk masuk (07 Okt 2026).

    ATURAN (terukur ke `/systemone` langsung, sumber: skill `typesafe-jev`):
        noul   → ⛔ TIDAK BOLEH ada `criteria`
        choice → `criteria` WAJIB, bentuk OBJEK {'opsi': 'deskripsi'}
        score  → `criteria` WAJIB, bentuk ARRAY ['tkt0', 'tkt1', …] (2–10)
    Tipe lain → DILARANG. Nama & jumlah pertanyaan BEBAS.

    Balik: daftar keluhan (kosong = sah). Pemanggil WAJIB gagal-cepat
    (raise) supaya 503 semu tidak pernah terjadi lagi.
    """
    keluhan: list[str] = []
    if not isinstance(pertanyaan, dict) or not pertanyaan:
        return ['`questions` harus objek berisi minimal 1 pertanyaan']
    for nama, q in pertanyaan.items():
        if not isinstance(q, dict):
            keluhan.append(f'{nama}: pertanyaan harus objek')
            continue
        tipe = q.get('type')
        punya_criteria = 'criteria' in q
        if tipe == 'noul':
            if punya_criteria:
                keluhan.append(
                    f'{nama}: type noul TIDAK BOLEH punya `criteria` '
                    f'(dapat {type(q["criteria"]).__name__}) — inilah penyebab '
                    f'HTTP 503 semu. Hapus field `criteria`.')
        elif tipe == 'choice':
            if not punya_criteria:
                keluhan.append(f'{nama}: type choice WAJIB punya `criteria` '
                               f'(objek {{opsi: deskripsi}})')
            elif not isinstance(q['criteria'], dict):
                keluhan.append(f'{nama}: criteria choice harus OBJEK '
                               f'{{opsi: deskripsi}}, dapat '
                               f'{type(q["criteria"]).__name__}')
            elif not q['criteria']:
                keluhan.append(f'{nama}: criteria choice tidak boleh kosong')
        elif tipe == 'score':
            if not punya_criteria:
                keluhan.append(f'{nama}: type score WAJIB punya `criteria` '
                               f'(array tingkat)')
            elif not isinstance(q['criteria'], list):
                keluhan.append(f'{nama}: criteria score harus ARRAY tingkat, '
                               f'dapat {type(q["criteria"]).__name__}')
            elif not (2 <= len(q['criteria']) <= 10):
                keluhan.append(f'{nama}: criteria score harus 2–10 tingkat, '
                               f'dapat {len(q["criteria"])}')
        else:
            keluhan.append(f'{nama}: type {tipe!r} tidak dikenal — '
                           f'hanya noul/choice/score')
    return keluhan


def tanya_bebas(teks: str, peta: list[dict[str, Any]],
                pertanyaan: dict[str, Any]) -> dict[str, Any] | None:
    """Tanya Jev dengan PERTANYAAN BEBAS apa pun — MATA serbaguna.

    Dipakai pemanggil BARU (mis. `konversi.mata_jev()`) yang butuh peta bab +
    sub-bab + bagian wajib artikel, BUKAN 3 pertanyaan tetap `periksa()`.

    ⚠️ BEDA dengan `periksa()`: `periksa()` = pemeriksa PETA BAB (3 pertanyaan
    tetap). Fungsi ini = mata umum: kembalikan JAWABAN MENTAH Jev, dan
    PEMANGGIL yang menafsirkan. Jangan campur keduanya.

    SELALU balik dict atau None. TIDAK PERNAH melempar galat (P1 & P2).
    Bentuk balasan: {nama_pertanyaan: {'text'|'choice': ..., 'confidence': ...}}
    """
    if not AKTIF or not teks or not pertanyaan:
        return None
    #  🛡️ PAGAR SKEMA: tolak `criteria` salah bentuk SEBELUM dikirim.
    #  Tanpa pagar ini, bentuk salah ⇒ HTTP 503 semu dari 9router (07 Okt 2026).
    keluhan = _periksa_skema(pertanyaan)
    if keluhan:
        raise ValueError('Skema pertanyaan Jev salah — perbaiki dulu: '
                         + ' | '.join(keluhan))
    #  Bahan: pakai penyusun bahan yang SUDAH ADA (jangan bikin jalur baru).
    #  Jev menghitung/memeta STRUKTUR → ia butuh daftar judul + posisi,
    #  bukan cuplikan paragraf (jejak terukur 05Okt26).
    try:
        isi = _susun_state(teks, peta)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[satpam] tanya_bebas: _susun_state gagal: %s', e)
        return None

    #  🛣️ JALAN TOL JEV: kirim lewat `app/jev.py` — SATU-SATUNYA jalur.
    from . import jev as _jev
    return _jev.tanya(isi, pertanyaan)


def _bahan_mutu(teks: str) -> str:
    """Bahan untuk Jev PERIKSA MUTU — beda dari `_susun_state()` (peta bab).

    ⚠️ AKAR 07 Okt 2026: `_susun_state()` HANYA mengirim peta BAB + cuplikan
    400 kar tiap bab ⇒ ABSTRAK, DAFTAR PUSTAKA, HOOK (yang ada di depan/belakang
    naskah, di luar bab) TIDAK IKUT. Akibatnya Jev salah bilang "tidak ada
    abstrak" padahal ADA (naskah Asih: ABSTRAK 2×, tapi Jev bilang 0,10).

    ⇒ Untuk pertanyaan MUTU (ada/tidak bagian), yang dibutuhkan = AWAL naskah
    (judul+abstrak+hook) + AWAL tiap bab + AKHIR naskah (kesimpulan+pustaka).
    Naskah besar (529rb kar) tetap ringan karena dipotong.
    """
    t = teks or ''
    if len(t) <= 14000:
        return t
    kepala = t[:5000]                  # judul, abstrak, pendahuluan/hook
    ekor = t[-5000:]                   # kesimpulan, saran, daftar pustaka
    #  ambil awal tiap bab dari TENGAH supaya bab besar tetap terwakili
    tengah = t[5000:-5000]
    potong = tengah[:4000]
    return (f'{kepala}\n\n[...BAGIAN TENGAH NASKAH...]\n{potong}\n\n'
            f'[...AKHIR NASKAH...]\n{ekor}')


def tanya_bebas_mutu(bahan: str, pertanyaan: dict[str, Any]) -> dict[str, Any] | None:
    """🛣️ JALAN TOL JEV — lewat `app/jev.py` (SATU-SATUNYA jalur).

    Bahan dikirim APA ADANYA (tidak disusun ulang) — gunanya untuk bahan yang
    sudah Siap (mis. `_bahan_mutu()` / jendela baris ber-ID).

    Kalau Jev mati, jawab None dan `jev.cek_siap()` menjelaskan sebabnya.
    """
    from . import jev as _jev

    #  🔴 PAGAR DEGRADASI SENYAP: bahan kosong = percuma (dan bikin 503 semu)
    if not isinstance(bahan, str) or not bahan.strip():
        log.warning('[satpam] tanya_bebas_mutu: bahan KOSONG — tidak dikirim')
        return None
    try:
        return _jev.tanya(bahan, pertanyaan)
    except _jev.SkemaSalah as e:
        #  salah PROGRAMMER (bukan gangguan) ⇒ naikkan, jangan ditelan
        log.error('[satpam] tanya_bebas_mutu: %s', e)
        raise


def _tanya_bebas_lama(bahan: str, pertanyaan: dict[str, Any]) -> dict[str, Any] | None:
    """Tanya Jev dengan BAHAN SIAP (bukan naskah + peta). Dipakai mutu.

    ⚠️ BEDA dengan `tanya_bebas()`: yang itu menyusun bahan lewat
    `_susun_state()` (peta bab). Yang ini menerima bahan yang SUDAH disusun
    pemanggil (mis. `konversi._bahan_mutu()`).

    SELALU balik dict atau None. TIDAK PERNAH melempar galat.
    """
    if not AKTIF or not bahan or not pertanyaan:
        return None
    #  🛡️ PAGAR SKEMA (sama seperti `tanya_bebas`) — cegah 503 semu.
    keluhan = _periksa_skema(pertanyaan)
    if keluhan:
        raise ValueError('Skema pertanyaan Jev salah — perbaiki dulu: '
                         + ' | '.join(keluhan))

    body = {
        'model': MODEL,
        'messages': [{'role': 'user',
                      'content': json.dumps({'state': bahan,
                                             'questions': pertanyaan})}],
    }
    req = urllib.request.Request(
        BASE, data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KUNCI}',
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=BATAS_DETIK) as r:
            mentah = r.read().decode()
    except Exception as e:                                    # P1 + P2: telan galat
        log.warning('[satpam] tanya_bebas_mutu gagal: %s: %s', type(e).__name__, e)
        return None

    jawab = _urai_balasan(mentah)
    if jawab is None:
        log.warning('[satpam] tanya_bebas_mutu: balasan tak terbaca (%d byte)',
                    len(mentah))
    return jawab


# ────────────────────────── BLOK PROMPT ──────────────────────────
def blok_prompt(h: dict[str, Any], peta: list[dict[str, Any]]) -> str:
    """Blok yang DISISIPKAN ke prompt AI — memberi AI kesadaran atas peta bab.

    ATURAN TEKS (ACC 17Sep26): ke mahasiswa DILARANG menyebut AI/nama model.
    Blok ini masuk ke PROMPT (bukan layar mahasiswa) — aman.
    Satpam mati / ragu → '' (prompt tidak berubah).
    """
    if not h or not h.get('ok'):
        return ''
    keputusan = h.get('keputusan')
    conf = float(h.get('confidence') or 0)
    jumlah_jev = h.get('jumlah_bab')
    jumlah_mesin = h.get('jumlah_bab_mesin')

    if keputusan == 'lolos':
        baris = [f'PEMERIKSAAN STRUKTUR: struktur bab naskah ini SUDAH DIPERIKSA '
                 f'oleh pemeriksa keputusan (keyakinan {conf:.2f}).',
                 f'MESIN menemukan {jumlah_mesin} bagian; pemeriksa menilai '
                 f'{jumlah_jev} bab yang benar-benar ada.']
        if jumlah_jev is not None and jumlah_jev != jumlah_mesin:
            baris.append(
                f'PERHATIAN: jumlah berbeda karena mesin memetakan per satuan '
                f'lebih halus (sub-bab) sementara pemeriksa menghitung BAB utuh. '
                f'DUA-DUANYA SAH — bab utuh untuk konteks, sub-bab untuk satuan '
                f'kerja.')
        baris.append('Pakai peta di bawah sebagai acuan posisi bab. '
                     'JANGAN mengarang isi bagian yang tidak kamu terima.')
        return '\n'.join(baris)

    if keputusan == 'tanya':
        return (f'PEMERIKSAAN STRUKTUR: pemeriksa keputusan TIDAK YAKIN soal '
                f'struktur bab naskah ini (keyakinan {conf:.2f}). Mesin menemukan '
                f'{jumlah_mesin} bagian. '
                'SIKAP: JANGAN mengarang jumlah bab; kalau kamu perlu menyebut '
                'bab, sebut HANYA bab yang benar-benar kamu lihat di naskah yang '
                'kamu terima, dan KATAKAN bahwa urutannya perlu dipastikan '
                'bersama pengguna.')

    if keputusan == 'tolak':
        return (f'PEMERIKSAAN STRUKTUR: struktur bab naskah ini TIDAK BISA '
                f'dipastikan (keyakinan {conf:.2f}). '
                'SIKAP: jangan menyebut nomor bab sama sekali; kerjakan tugas '
                'pada bagian yang kamu terima apa adanya.')
    return ''


# ────────────────────────── CATATAN INTERNAL ──────────────────────────
def catat(db: Any, file_id: int, h: dict[str, Any],
          peta: list[dict[str, Any]]) -> None:
    """Catat keputusan satpam ke log — untuk audit, TANPA mengubah skema DB.

    ⚠️ TIDAK membuat tabel baru (aturan Bos: jangan bangun sistem paralel).
    Hanya log berkas. Kalau nanti Bos mau tampil di dashboard, baru dibahas.
    """
    try:
        log.info('[satpam] file=%s keputusan=%s keyakinan=%.2f '
                 'jumlah_bab_jev=%s jumlah_bagian_mesin=%s dtk=%s alasan=%s',
                 file_id, h.get('keputusan'), h.get('confidence') or 0,
                 h.get('jumlah_bab'), len(peta or []), h.get('detik'),
                 h.get('alasan'))
    except Exception:                                            # noqa: BLE001
        pass
