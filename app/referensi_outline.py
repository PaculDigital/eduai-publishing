"""Outline builder buku referensi (mesin referensi web, 28 Okt 2026).

Kenapa ada builder sendiri, bukan OB.susun_outline (host)?
- Host outline_buku TIDAK mengenal jenis 'referensi' (0 kemunculan) —
  outlinenya berbentuk umum, bukan struktur baku referensi.
- Struktur baku referensi (skill buku-referensi): per bab N.1 Definisi,
  N.2 Perkembangan, N.3 Perbandingan Kritis (judul WAJIB mengandung
  'Perbandingan Kritis'), N.4 Posisi dan Sintesis Penulis (judul WAJIB
  mengandung 'Posisi'/'Sintesis'), N.5 Implikasi. N.0 (Peta Bab) = intro
  per bab (generate_bab memanggil architect is_intro), Ringkasan Bab =
  penutup per bab (architect is_closing, cabang referensi = formal).

Bentuk keluar = bentuk yang diterima OB.periksa + host susun_buku:
    {n: {'title': str, 'subs': [(nomor, judul, key_points), ...]},
     }

Kontrak kunci: HANYA int (nomor bab). Kunci meta teks DILARANG — lihat
catatan di akhir susun_outline().
(nomor sub = string 'N.M'; OB.periksa hanya menuntut tiap sub beranggota
>=3 dengan judul + key_points tidak kosong.)

TIDAK mengimpor modul host (outline_buku) — hanya json/re + call_llm
dari buku_umum_pipeline (file repo, ada di image).
"""

import json
import re

SUB_TETAP = [
    ('{n}.1', 'Definisi dan Konsep Kunci'),
    ('{n}.2', 'Perkembangan Teori dan Kajian'),
    ('{n}.3', 'Perbandingan Kritis'),
    ('{n}.4', 'Posisi dan Sintesis Penulis'),
    ('{n}.5', 'Implikasi'),
]


def prompt_outline(judul, bidang, jumlah_bab):
    subs = '\n'.join(
        f'- {nomor.format(n="N")}: {nama}' for nomor, nama in SUB_TETAP)
    return f"""Kamu penyusun outline BUKU REFERENSI ilmiah (bukan buku umum,
bukan buku ajar). Buku ini akan menjadi RUJUKAN otoritatif di bidangnya:
pembaca membukanya untuk merujuk definisi baku, peta teori, dan posisi
penulis — bukan untuk dibacakan cerita.

Judul buku: {judul}
Bidang: {bidang or '(sesuai judul)'}
Jumlah bab: {jumlah_bab} (tidak kurang, tidak lebih)

ATURAN STRUKTUR (WAJIB):
- Setiap bab punya PERSIS 5 sub-bab berikut (judul boleh diperpanjang
  dengan topik bab, TAPI kata kuncinya wajib ada):
{subs}
  Contoh judul sub yang sah: '3.3 Perbandingan Kritis Teori Belajar
  Bermakna dan Teori Kognitif', '3.4 Posisi dan Sintesis Penulis atas
  Teori Belajar Bermakna'.
- Cakupan antar bab TIDAK BOLEH tumpang tindih; alur logis (umum ke
  khusus, atau kronologis).
- key_points tiap sub: 1-2 kalimat SUBSTANTIF (sudut pandang konkret
  yang harus dibahas), BUKAN kalimat generik ('membahas teori secara
  umum') dan BUKAN kosong.
- Bab 1 = pendahuluan bidang (ruang lingkup, batasan, istilah kunci,
  struktur buku). Bab terakhir = sintesis lintas bab + agenda riset.
- Bahasa Indonesia EYD. 0 markdown di dalam nilai JSON.

KELUARAN — HANYA JSON ini, tanpa teks lain:
{{"bab": [{{"title": "Judul Bab", "subs": [{{"nomor": "1.1", "judul": "Definisi dan Konsep Kunci ...", "key_points": "..."}}, ...]}}], ...]}}

⚠️ `judul` sub-bab TIDAK boleh diawali nomornya. Jangan tulis
"1.1 Definisi ..." — cukup "Definisi ...". Nomor sudah ada di field
`nomor` dan ditampilkan terpisah; menuliskannya di judul membuat nomor
tampil DOBEL.
"""


def _periksa_bentuk(babs):
    """Aturan yang sama dengan OB.periksa + aturan judul N.3/N.4."""
    masalah = []
    if not isinstance(babs, list) or not babs:
        return ['tidak ada bab']
    for i, b in enumerate(babs, 1):
        if not isinstance(b, dict) or not (b.get('title') or '').strip():
            masalah.append(f'bab {i}: judul kosong')
            continue
        subs = b.get('subs') or []
        if len(subs) != 5:
            masalah.append(f'bab {i}: harus 5 sub-bab, dapat {len(subs)}')
        for s in subs:
            if not isinstance(s, dict):
                masalah.append(f'bab {i}: bentuk sub-bab salah')
                continue
            if not (s.get('judul') or '').strip():
                masalah.append(f'bab {i}: judul sub kosong')
            if not (s.get('key_points') or '').strip():
                masalah.append(f'bab {i}/{s.get("nomor")}: key_points kosong')
        judul_sub = ' '.join(str(s.get('judul', '')) for s in subs).lower()
        if 'perbandingan kritis' not in judul_sub and 'komparasi' not in judul_sub:
            masalah.append(f'bab {i}: tidak ada sub Perbandingan Kritis')
        if 'posisi' not in judul_sub and 'sintesis' not in judul_sub:
            masalah.append(f'bab {i}: tidak ada sub Posisi/Sintesis Penulis')
    return masalah


def parse_outline(teks):
    """Teks LLM -> outline bentuk OB. Raise ValueError berisi masalah."""
    m = re.search(r'\{.*\}', teks, re.DOTALL)
    if not m:
        raise ValueError('outline: tidak ada JSON dalam jawaban')
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f'outline: JSON tidak valid ({e})')
    babs = data.get('bab') if isinstance(data, dict) else None
    masalah = _periksa_bentuk(babs)
    if masalah:
        raise ValueError('outline cacat: ' + '; '.join(masalah[:3]))
    outline = {}
    for i, b in enumerate(babs, 1):
        subs = []
        for j, s in enumerate(b['subs'], 1):
            nomor = (s.get('nomor', '') or '').strip() or f'{i}.{j}'
            judul_sub = s['judul'].strip()
            #  Jaring: LLM kadang menyalin nomor ke dalam judul walau contoh
            #  prompt sudah bersih ("1.1 Definisi ..."). Buang awalan nomor
            #  itu supaya tidak tampil dobel (nomor + judul bernomor).
            while judul_sub.startswith(nomor):
                judul_sub = judul_sub[len(nomor):].lstrip(' .–—-\t')
            if not judul_sub:
                raise ValueError(
                    f'outline cacat: bab {i} sub {nomor} judul kosong '
                    'sesudah nomor dibuang')
            subs.append((nomor, judul_sub, s['key_points'].strip()))
        outline[i] = {'title': b['title'].strip(), 'subs': subs}
    return outline


def susun_outline(judul, bidang, jumlah_bab=8, tier=None):
    """Bangun outline referensi via LLM (maks 2 percobaan, lalu raise).

    Percobaan ke-2 membawa daftar masalah percobaan ke-1 sebagai perintah
    perbaikan — bukan pengulangan buta.
    """
    import buku_umum_pipeline as P
    if tier is not None:
        from tier_buku import jumlah_bab as _bab_dari_tier
        jumlah_bab = _bab_dari_tier(tier)
    jumlah_bab = max(1, min(12, int(jumlah_bab or 8)))
    prompt = prompt_outline(judul, bidang, jumlah_bab)
    masalah = ''
    for percobaan in range(2):
        teks = P.call_llm(
            (prompt + f'\n\nPERBAIKI KESALAHAN SEBELUMNYA: {masalah}'
             if masalah else prompt),
            max_tokens=6000, timeout=180)
        try:
            outline = parse_outline(teks)
        except ValueError as e:
            masalah = str(e)
            continue
        #  ⚠️ JANGAN menyisipkan kunci meta ('_judul', '_bidang', '_jenis',
        #  '_sumber') ke dalam dict ini. Kontraknya: kunci = nomor bab (int),
        #  nilai = {'title': str, 'subs': [...]}. Kunci teks di dalamnya
        #  merusak SEMUA pembaca hilir:
        #    - `sorted(outline.items())` -> TypeError str vs int (HTTP 500)
        #    - `outline_dari_json()` -> 'kunci outline bukan nomor bab'
        #  Tidak ada satu pun pembaca kunci meta di jalur web (hanya
        #  outline_buku.py lama & _arsip/). Data yang dibutuhkan (judul,
        #  bidang) sudah tersimpan di pesanan/pending.
        return outline
    raise ValueError(f'outline referensi gagal 2x: {masalah}')
