"""PETA HALUS — rekomendasi AI per BAB + SUB-BAB (ACC Bos 26Sep26).

=== APA INI ===
Setelah EduAi membaca naskah (Jalur B) atau selesai menulis 1 bab
(Jalur A), EduAi memberi DAFTAR REKOMENDASI yang sifatnya **tidak
memaksa** — user yang memilih mana yang dikerjakan (tiap rekomendasi
yang dikerjakan = 1 Token Revisi).

=== 2 MODE (putusan ⑳ Bos 26Sep26) ===
  1. `peta_awal`  → naskah dibaca PERTAMA kali.
        SELALU ≥5 rekomendasi (putusan Bos: "minimal 5 rekomendasi").
        Tujuan bisnis (kata Bos): user punya cukup pilihan supaya
        3 token GRATIS-nya terpakai habis → upgrade → beli AddOn.
        NADA: seperti DOSEN membaca & menandai, BUKAN seperti penjual.
  2. `revisi`     → naskah sudah berjalan (revisi biasa).
        Aturan LAMA (ACC 17Sep26): MAX 3, ACAK 0-3 (boleh 0 = DIAM).
        Supaya terasa natural — user tidak selalu "dijualan".

=== PAGAR (ACC 17Sep26 — wajib, jangan dilanggar) ===
  (C1) Bagian yang BARU dikerjakan EduAi DILARANG ditawarkan lagi.
  (C2) Sidik jari (hash) naskah: kalau naskah TIDAK berubah sejak
       peta dibuat → peta lama dipakai ulang (tidak panggil AI lagi).
  (C3) Temuan yang sudah PERNAH DITOLAK user JANGAN diulang.
  (C4) Kalau bersih → katakan baik-baik ("sudah bagus"), jangan diam saja.

=== BENTUK SATU REKOMENDASI ===
  {
    'id'       : 'B1.2-01',        # unik: bab.subbab-urut
    'bab'      : '1',
    'subbab'   : '1.2',
    'judul_bab': 'PENDAHULUAN',
    'sub_judul': 'Latar Belakang',
    'masalah'  : 'Fenomena belum tajam…',   # apa yang kurang (fakta)
    'saran'    : 'Tajamkan dengan data…',   # usulan perbaikan
    'berat'    : 'ringan'|'sedang'|'berat', # untuk nada & urutan
  }

=== PENTING: MESIN INI TIDAK MENULIS ===
Tugasnya HANYA menyusun DAFTAR. Yang mengerjakan rekomendasi tetap
`app/ai.py` (`_revisi_kerja`) dengan pagar yang sudah ada.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

# ── ATURAN JUMLAH (putusan ⑳) ────────────────────────────────────────────
PETA_AWAL_MIN = 5          # peta awal: minimal 5 rekomendasi
PETA_AWAL_MAKS = 12        # dibatasi supaya user tidak kebanjiran
REVISI_MAKS = 3            # revisi biasa: maks 3 (aturan lama)
REVISI_PELUANG_DIAM = 0.25  # 25% peluang DIAM (0 temuan) → natural

# ── 5 JENIS TEMUAN YANG BOLEH DITAWARKAN (ACC 17Sep26) ───────────────────
# DILARANG: sinonim, gaya bahasa yang sudah benar, ejaan ringan (itu EGD).
JENIS_TEMUAN = (
    'paragraf_tidak_nyambung',
    'klaim_tanpa_bukti',
    'alur_melompat',
    'bertentangan_antar_bab',
    'paragraf_kacau',
)

# ── PERAN BAB → apa yang paling sering kurang (untuk nada & fokus) ───────
_FOKUS_BAB: dict[str, list[str]] = {
    '1': ['latar belakang belum menajamkan fenomena',
          'rumusan masalah belum sinkron dengan tujuan',
          'tujuan belum terukur',
          'manfaat belum menyebut pihak yang menerima',
          'batasan masalah belum jelas'],
    '2': ['teori belum jadi dasar, masih daftar ringkasan',
          'penelitian terdahulu belum dibandingkan',
          'kerangka pikir belum tergambar alurnya',
          'hipotesis belum turun dari teori',
          'definisi operasional belum seragam istilahnya'],
    '3': ['jenis & pendekatan belum dinyatakan eksplisit',
          'populasi/sampel: teknik pengambilan belum disebut',
          'instrumen: kisi-kisi belum lengkap',
          'teknik analisis belum sinkron dengan hipotesis',
          'waktu & tempat penelitian belum tegas'],
    '4': ['hasil belum dijawab sesuai rumusan masalah',
          'pembahasan belum membandingkan dengan penelitian terdahulu',
          'tabel/grafik belum ditafsirkan (hanya disajikan)',
          'uji prasyarat belum dilaporkan',
          'simpulan sub-bab belum menjawab hipotesis'],
    '5': ['simpulan belum menjawab semua rumusan masalah',
          'saran belum mengarah ke pihak tertentu',
          'keterbatasan penelitian belum disebut',
          'implikasi teoretis/praktis belum dipisah'],
    '6': ['daftar pustaka belum konsisten gaya penulisannya',
          'ada sitasi yang belum muncul di daftar pustaka',
          'rentang tahun sumber terlalu tua untuk topik ini'],
}


def _sidik(teks: str) -> str:
    """Sidik jari naskah — pagar C2 (deteksi naskah berubah / tidak)."""
    return hashlib.sha256((teks or '').encode('utf-8')).hexdigest()


def sidik_naskah(teks: str) -> str:
    return _sidik(teks)


def boleh_pakai_ulang(peta_sidik: str, teks_kini: str) -> bool:
    """Pagar C2: peta lama masih sah? (naskah belum berubah)."""
    if not peta_sidik:
        return False
    return peta_sidik == _sidik(teks_kini)


def _urutkan(bab: str, sub: str, no: int) -> str:
    return f'B{bab}.{sub}-{no:02d}'


def susun(
    bab_terdeteksi: list[dict[str, Any]] | None = None,
    mode: str = 'peta_awal',
    sudah_ditawarkan: set[str] | None = None,
    sudah_ditolak: set[str] | None = None,
    bibit_acak: int | None = None,
) -> dict[str, Any]:
    """Susun DAFTAR REKOMENDASI (tidak menulis naskah).

    bab_terdeteksi : hasil `app.state.deteksi_bab_besar()` —
                     [{'bab': '1', 'judul': 'PENDAHULUAN'}, …]
    mode           : 'peta_awal' (≥5) | 'revisi' (acak 0-3)
    sudah_ditawarkan: id yang sudah pernah ditawarkan (pagar C1)
    sudah_ditolak  : id yang pernah ditolak user (pagar C3)
    bibit_acak     : untuk uji — biar hasil bisa diulang (deterministik)

    Kembalikan:
      {'mode', 'jumlah', 'daftar': [...], 'pesan', 'diam': bool}
    """
    #  PAGAR INPUT (26Sep26): pemanggil bisa saja mengirim bentuk salah
    #  (string, None, dict). JANGAN meledak — perlakukan sebagai kosong,
    #  supaya fitur tetap jalan dan user tidak melihat galat.
    if not isinstance(bab_terdeteksi, (list, tuple)):
        bab_terdeteksi = []
    bab_terdeteksi = [b for b in bab_terdeteksi if isinstance(b, dict)]
    dipakai = set(sudah_ditawarkan or ())
    ditolak = set(sudah_ditolak or ())
    rng = random.Random(bibit_acak)

    # ── Mode REVISI: peluang DIAM (natural, pagar C3) ────────────────────
    if mode == 'revisi':
        if rng.random() < REVISI_PELUANG_DIAM:
            return {'mode': 'revisi', 'jumlah': 0, 'daftar': [],
                    'diam': True,
                    'pesan': 'Sudah bagus, tidak ada yang perlu diubah.'}
        maks = REVISI_MAKS
    else:
        maks = PETA_AWAL_MAKS

    daftar: list[dict[str, Any]] = []
    for b in bab_terdeteksi:
        bab = str(b.get('bab') or '').strip()
        if not bab:
            continue
        judul_bab = (b.get('judul') or '').strip()
        kandidat = _FOKUS_BAB.get(bab) or []
        # sub-bab: pakai yang terdeteksi kalau ada, kalau tidak pakai bab-nya
        subs = b.get('sub_bab') or []
        sub_untuk = [str(s.get('subbab') or s.get('nomor') or '').strip()
                     for s in subs if (s.get('subbab') or s.get('nomor'))]
        sub_untuk = [x for x in sub_untuk if x] or ['']

        for i, masalah in enumerate(kandidat):
            sub = sub_untuk[i % len(sub_untuk)]
            no = i + 1
            rid = _urutkan(bab, sub or '0', no)
            if rid in dipakai or rid in ditolak:      # pagar C1 & C3
                continue
            daftar.append({
                'id': rid, 'bab': bab, 'subbab': sub,
                'judul_bab': judul_bab,
                'sub_judul': '',
                'masalah': masalah,
                'saran': '',
                'berat': 'sedang',
            })
            if len(daftar) >= maks:
                break
        if len(daftar) >= maks:
            break

    # ── Peta awal: pastikan MINIMAL 5 (putusan Bos) ──────────────────────
    if mode != 'revisi' and len(daftar) < PETA_AWAL_MIN:
        # kurang bab terdeteksi → lengkapi dari peran bab standar
        for bab in ('1', '2', '3', '4', '5'):
            if len(daftar) >= PETA_AWAL_MIN:
                break
            if any(d['bab'] == bab for d in daftar):
                continue
            masalah = (_FOKUS_BAB.get(bab) or ['perlu diperiksa'])[0]
            rid = _urutkan(bab, '0', 1)
            if rid in dipakai or rid in ditolak:
                continue
            daftar.append({'id': rid, 'bab': bab, 'subbab': '',
                           'judul_bab': '', 'sub_judul': '',
                           'masalah': masalah, 'saran': '', 'berat': 'sedang'})

    # ── Urutkan: bab kecil dulu (mudah → sulit), sesuai kaidah menulis ───
    daftar.sort(key=lambda d: (str(d['bab']), str(d['subbab'])))

    # ── Mode revisi: ACak urutan + potong maks 3 (aturan lama) ───────────
    if mode == 'revisi':
        rng.shuffle(daftar)
        daftar = daftar[:REVISI_MAKS]

    pesan = ('EduAi sudah membaca naskahmu. Ini yang bisa dirapikan — '
             'pilih yang kamu mau, tidak wajib semuanya.'
             if mode != 'revisi' else '')

    return {'mode': mode, 'jumlah': len(daftar), 'daftar': daftar,
            'diam': len(daftar) == 0, 'pesan': pesan}


def ringkas(hasil: dict[str, Any]) -> str:
    """Bentuk teks peta — untuk diuji / ditampilkan di CLI."""
    if hasil.get('diam'):
        return hasil.get('pesan') or '(diam)'
    baris = [f"PETA ({hasil['mode']}) — {hasil['jumlah']} rekomendasi"]
    bab_kini = None
    for d in hasil['daftar']:
        if d['bab'] != bab_kini:
            bab_kini = d['bab']
            baris.append(f"  BAB {d['bab']} — {d['judul_bab']}".rstrip(' —'))
        sub = f" [{d['subbab']}]" if d['subbab'] else ''
        baris.append(f"    ·{sub} {d['masalah']}")
    return '\n'.join(baris)

# ── JEMBATAN dari `app.state.deteksi_bab_besar()` (26Sep26) ───────────────
# Bentuk state  : {'section_id': 'BAB I', 'section_title': 'PENDAHULUAN', …}
# Bentuk peta   : {'bab': '1', 'judul': 'PENDAHULUAN', 'sub_bab': [...]}
# ⇒ adaptor ini menyambung keduanya TANPA mengubah state.py (dipakai
#   banyak tempat lain — jangan disentuh).
_ROMAWI = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6',
           'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10'}


def dari_state(bab_state: list[dict[str, Any]] | None,
               sub_state: list[dict[str, Any]] | None = None) -> list[dict]:
    """Ubah hasil `state.deteksi_bab_besar()` + `deteksi_subbab()` → bentuk peta.

    sub_state dipakai untuk mengisi `sub_bab` per bab (peta halus sampai
    sub-bab — putusan ㉑ Bos).
    """
    sub_state = sub_state or []

    # kelompokkan sub-bab per bab induknya
    per_bab: dict[str, list[dict]] = {}
    for s in sub_state:
        if not isinstance(s, dict):
            continue
        induk = str(s.get('bab') or s.get('bab_induk') or '').strip()
        nomor = str(s.get('section_id') or s.get('nomor') or '').strip()
        if induk:
            per_bab.setdefault(induk.lstrip('0') or induk, []).append(
                {'subbab': nomor})

    keluar: list[dict] = []
    for b in (bab_state or []):
        if not isinstance(b, dict):
            continue
        sid = str(b.get('section_id') or '').strip()       # 'BAB I'
        angka = sid.upper().replace('BAB', '').strip()
        bab = _ROMAWI.get(angka, angka)
        if not bab.isdigit():
            continue
        keluar.append({
            'bab': bab,
            'judul': (b.get('section_title') or '').strip(),
            'sub_bab': per_bab.get(bab, []),
        })
    return keluar

# ══════════════════════════════════════════════════════════════════════════
#  MODE AI SUNGGUHAN — EduAi BACA naskah → susun peta (ACC Bos 26Sep26)
#
#  KENAPA dipisah dari `susun()`: `susun()` = PETA CEPAT (Rp 0, berbasis
#  peran bab). Fungsi di bawah = peta yang BENAR-BENAR membaca isi naskah
#  (1 panggilan AI). Dipakai saat naskah diunggah / bab selesai.
#
#  PAGAR:
#   · BACA = GRATIS (putusan ⑬ Bos) — tidak menyentuh saldo token.
#   · Nada = DOSEN MENANDAI, bukan penjual (jangan menyebut harga).
#   · Peta awal: MINIMAL 5 rekomendasi (putusan ⑳).
#   · Revisi biasa: maks 3, boleh 0 (ACAK) supaya natural.
#   · Kalau tidak ada temuan → katakan baik-baik (pagar C4).
# ══════════════════════════════════════════════════════════════════════════

_ATURAN_PROMPT = """Kamu adalah EduAi, pendamping penulisan skripsi/tesis/disertasi.
TUGAS: membaca naskah lalu MEMBERI CATATAN (rekomendasi) per BAB dan SUB-BAB.
Kamu TIDAK menulis ulang naskah. Kamu hanya menandai apa yang bisa diperbaiki.

ATURAN WAJIB:
1. Nada = seperti DOSEN MEMBACA & MENANDAI. Bukan penjual, bukan pemasar.
   JANGAN menyebut harga, token, biaya, atau ajakan membeli apa pun.
2. Sifatnya USULAN, bukan perintah. Bahasa halus: "bisa dipertajam",
   "sebaiknya dilengkapi", bukan "SALAH" / "HARUS".
3. HANYA tandai 5 jenis masalah ini (jenis lain DILARANG):
   paragraf_tidak_nyambung · klaim_tanpa_bukti · alur_melompat ·
   bertentangan_antar_bab · paragraf_kacau
   DILARANG menandai: pilihan sinonim, gaya bahasa yang sudah benar,
   ejaan ringan, atau selera penulisan.
4. {jml} rekomendasi. {mode_ket}
5. Kalau kamu menemukan bahwa bagian itu SUDAH BAIK, jangan dipaksa
   menandai — lebih baik jumlahnya lebih sedikit (jujur) daripada mengarang.
6. METODE PENELITIAN MILIK PENULIS: DILARANG mengusulkan mengubah
   jumlah sampel, teknik sampling, instrumen, skala, teknik analisis,
   definisi operasional, atau model penelitian. Kalau ada yang menurutmu
   kurang lazim, sebutkan sebagai CATATAN/KETERBATASAN saja.
7. Gaya sitasi yang berbeda dari APA 7: sebut "menurut standar APA 7",
   JANGAN sebut "salah" — biar penulis memutuskan.
8. Untuk tiap keadaan, tulis lokasi yang jelas (bab + sub-bab kalau ada).

BENTUK JAWABAN (HANYA JSON, tanpa penjelasan di luar JSON):
{{"rekomendasi": [
  {{"bab": "1", "subbab": "1.2", "judul_bab": "PENDAHULUAN",
    "sub_judul": "Latar Belakang", "jenis": "klaim_tanpa_bukti",
    "masalah": "satu kalimat: apa yang kurang", 
    "saran": "satu kalimat: usulan singkat"}}
]}}
"""


def bangun_prompt(teks_peta: str, mode: str = 'peta_awal') -> str:
    """Susun prompt EduAi untuk membuat peta (tanpa memanggil AI)."""
    if mode == 'revisi':
        jml = 'maksimal 3 (boleh 0 kalau memang tidak ada)'
        mode_ket = ('Kalau tidak ada temuan, balas dengan daftar KOSONG '
                    '— itu jawaban yang SAH dan bagus.')
    else:
        jml = 'MINIMAL 5'
        mode_ket = ('Naskah ini baru pertama kali dibaca: berikan gambaran '
                    'MENYELURUH per bab & sub-bab (peta halus).')
    aturan = _ATURAN_PROMPT.format(jml=jml, mode_ket=mode_ket)
    return (aturan + '\n\n=== NASKAH (dengan peta bab) ===\n' + teks_peta + '\n')


def _ambil_json(jawab: str) -> dict[str, Any]:
    """Ambil JSON dari jawaban AI (tahan pagar ``` dan teks pembuka)."""
    import json as _json
    import re as _re
    t = (jawab or '').strip()
    t = _re.sub(r'^```(?:json)?\s*|```$', '', t, flags=_re.M).strip()
    i, j = t.find('{'), t.rfind('}')
    if i < 0 or j <= i:
        return {}
    try:
        return _json.loads(t[i:j + 1])
    except Exception:                                          # noqa: BLE001
        return {}


def rapikan_hasil_ai(data: dict[str, Any], mode: str = 'peta_awal',
                     sudah_ditawarkan: set[str] | None = None,
                     sudah_ditolak: set[str] | None = None) -> dict[str, Any]:
    """Bersihkan balasan AI → bentuk peta yang siap dipakai aplikasi."""
    dipakai = set(sudah_ditawarkan or ())
    ditolak = set(sudah_ditolak or ())
    mentah = data.get('rekomendasi') if isinstance(data, dict) else None
    if not isinstance(mentah, list):
        mentah = []

    daftar: list[dict[str, Any]] = []
    for i, d in enumerate(mentah, 1):
        if not isinstance(d, dict):
            continue
        bab = str(d.get('bab') or '').strip()
        sub = str(d.get('subbab') or '').strip()
        masalah = str(d.get('masalah') or '').strip()
        if not bab or not masalah:
            continue
        rid = _urutkan(bab, sub or '0', i)
        if rid in dipakai or rid in ditolak:
            continue
        jenis = str(d.get('jenis') or '').strip()
        if jenis and jenis not in JENIS_TEMUAN:
            jenis = ''            # jenis di luar daftar → dibuang (pagar)
        daftar.append({
            'id': rid, 'bab': bab, 'subbab': sub,
            'judul_bab': str(d.get('judul_bab') or '').strip(),
            'sub_judul': str(d.get('sub_judul') or '').strip(),
            'jenis': jenis,
            'masalah': masalah,
            'saran': str(d.get('saran') or '').strip(),
            'berat': 'sedang',
        })

    # batasi jumlah sesuai mode (jangan percaya AI berlebihan)
    if mode == 'revisi':
        daftar = daftar[:REVISI_MAKS]
    else:
        daftar = daftar[:PETA_AWAL_MAKS]

    daftar.sort(key=lambda x: (str(x['bab']), str(x['subbab'])))

    diam = len(daftar) == 0
    if diam:
        pesan = ('Naskahmu sudah bagus — tidak ada yang perlu diubah.')
    elif mode == 'revisi':
        pesan = ''
    else:
        pesan = ('EduAi sudah membaca naskahmu. Ini yang bisa dirapikan — '
                 'pilih yang kamu mau, tidak wajib semuanya.')
    return {'mode': mode, 'jumlah': len(daftar), 'daftar': daftar,
            'diam': diam, 'pesan': pesan}
