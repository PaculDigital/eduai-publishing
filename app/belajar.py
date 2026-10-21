"""Mode Belajar EduAi — LANGKAH 1: halaman + hitungan JUJUR.

⚠️ ATURAN KERAS (Bos 03Okt26):
   JANGAN menampilkan angka/skor yang belum benar-benar dihitung mesin.
   Kalau mesin belum ada → tampilkan keadaan APA ADANYA ("Belum terbuka"),
   BUKAN 0 palsu yang seolah "sudah dinilai dan dapat nol".

CARA PAKAI:
    from app import belajar
    data = belajar.ringkasan(db, user)          # untuk SEMUA naskahnya
    data = belajar.ringkasan(db, user, fid=12)  # untuk satu naskah

TABEL: `belajar_naskah` (SUDAH ADA — kolom siap dipakai):
    file_id · user_id · status · insight_json · soal_json · bab_selesai
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from inspect import isclass

from sqlalchemy import select

#  ── Tahapan (dari MASTER_PLAN §4.8, ACC 13Sep26) ──────────────────────
TAHAP = (
    (1, 'Siap Proposal', 'Insight BAB I–III + soal latihan ujian proposal.',
     ('bab1', 'bab2', 'bab3')),
    (2, 'Siap Hasil', 'Insight BAB IV + soal pendalaman hasil penelitian.',
     ('bab4',)),
    (3, 'Siap Sidang', 'Insight lanjutan + soal latihan ujian skripsi.',
     ('bab5',)),
)

#  Naskah harus punya bab INI dulu supaya tahap 1 dianggap terbuka
BAB_MINIM_PROPOSAL = 3


BATAS_BAB = 20
"""Batas bab tertinggi yang dikenali.

⚠️ AKAR BUG DIPERBAIKI 15Okt26: dulu batasnya **5** (di `_angka_romawi`) dan
**9** (di `_nomor_bab_dari_section` + `_romawi_ke_angka`). Akibatnya:
  · Disertasi 7 bab  → label bab 6 jadi 'BAB 6' (SALAH; naskah pakai 'BAB VI')
    → `_label_bab()` tak ketemu bab → Mode Belajar bab 6-8 MATI.
  · Naskah 10 bab    → 'BAB X' DITOLAK SENYAP (dibalas None).
Kenapa 20: jenjang tertinggi (disertasi) praktis 6-8 bab; 20 = lega, dan
sama dengan jangkauan `parser.py`. JANGAN dipatok lebih kecil lagi."""


def _angka_romawi(n: int) -> str:
    """6 → 'VI' (BUKAN '6'). Tak terbatas sampai BATAS_BAB."""
    peta = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX',
            'XX')
    if isinstance(n, int) and 1 <= n <= len(peta):
        return peta[n - 1]
    return str(n)


def bab_terdeteksi(teks: str) -> list[int]:
    """Nomor bab yang benar-benar ADA di naskah (pakai mesin produksi).

    Memakai app.versi.deteksi_bab — mesin yang SAMA dengan AI & peta bab,
    supaya tidak ada dua kebenaran (pelajaran pola kembar 03Okt26).
    """
    try:
        from .versi import deteksi_bab
        return sorted({int(b['nomor']) for b in deteksi_bab(teks or '')
                       if b.get('nomor')})
    except Exception:
        return []


def hak_paket(user) -> tuple[bool, int]:
    """Apakah user berhak Mode Belajar + berapa naskah.

    Sumber: app/config.py KUOTA_PAKET — SATU sumber kuota (jangan hardcode).
    ⚠️ 03Okt26: pertama kali Wulan SALAH baca `PAKET` (itu harga/MB, bukan
    kuota) → semua paket balas 0. Kuota ada di `KUOTA_PAKET`.
    """
    try:
        from .config import KUOTA_PAKET
        p = KUOTA_PAKET.get(getattr(user, 'paket', '') or '', {}) or {}
        jatah = int(p.get('belajar_naskah', 0) or 0)
        return (jatah > 0), jatah
    except Exception:
        return False, 0


def _terpakai(db, user_id: int) -> int:
    """Berapa naskah yang SUDAH diaktifkan Mode Belajar."""
    try:
        from .models import BelajarNaskah
        return int(db.execute(
            select(__import__('sqlalchemy').func.count())
            .select_from(BelajarNaskah)
            .where(BelajarNaskah.user_id == user_id)
        ).scalar() or 0)
    except Exception:
        return 0


def _aktif_untuk(db, user_id: int) -> dict:
    """Peta file_id → baris belajar_naskah yang sudah aktif."""
    try:
        from .models import BelajarNaskah
        rows = db.execute(
            select(BelajarNaskah).where(BelajarNaskah.user_id == user_id)
        ).scalars().all()
        out = {}
        for r in rows:
            out[int(r.file_id)] = {
                'status': (r.status or '').strip().lower(),
                'insight': _muat(r.insight_json),
                'soal': _muat(r.soal_json),
                'bab_selesai': _muat(r.bab_selesai),
            }
        return out
    except Exception:
        return {}


def _muat(s):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def ringkasan(db, user, fid: int | None = None) -> dict:
    """Bangun data halaman /belajar — SEMUA angka dari kenyataan.

    Mengembalikan dict yang siap dipakai template. Kunci penting:
        boleh           → user pakai paket yang punya jatah
        jatah / terpakai / sisa
        naskah          → daftar naskah yang SUDAH diaktifkan (kalau fid=None)
        kartu           → 3 tahap + status terbuka/terkunci
        aksi            → apa yang user harus lakukan sekarang
    """
    boleh, jatah = hak_paket(user)
    terpakai = _terpakai(db, int(getattr(user, 'id', 0)))

    hasil = {
        'boleh': boleh,
        'jatah': jatah,
        'terpakai': terpakai,
        'sisa': max(0, jatah - terpakai),
        'aktif': _aktif_untuk(db, int(getattr(user, 'id', 0))),
        'naskah': [],
        'kartu': [],
        'pilih': None,
        'ada_mesin_insight': False,   # belum dibangun → jujur
        'ada_mesin_soal': False,      # belum dibangun → jujur
    }

    #  ── daftar naskah milik user yang bisa dipilih ─────────────────────
    try:
        from .models import FileBerkas
        rows = db.execute(
            select(FileBerkas).where(FileBerkas.user_id == int(getattr(user, 'id', 0)))
        ).scalars().all()
        for f in rows:
            hasil['naskah'].append({
                'id': int(f.id),
                'nama': (getattr(f, 'nama', '') or f'naskah-{f.id}'),
                'aktif': int(f.id) in hasil['aktif'],
            })
    except Exception:
        pass

    #  ── kalau fid diberikan: bangun kartu untuk naskah itu ─────────────
    if fid:
        bab_ada = []
        try:
            from .models import FileBerkas
            f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
            if f is not None:
                bab_ada = _bab_dari_berkas(f)
                hasil['pilih'] = {
                    'id': int(fid),
                    'nama': (getattr(f, 'nama', '') or f'naskah-{fid}'),
                    'bab': [_angka_romawi(n) for n in bab_ada],
                    'bab_jumlah': len(bab_ada),
                }
        except Exception:
            pass

        #  🔑 SYARAT TERBUKA = bab SUDAH DIREVISI (bukan sekadar ADA).
        #     Sumber: section_state.kategori 'bab1'…'bab5'.
        #  🚨 TIDAK ADA JALUR MUNDUR. Wulan sempat menambah "kalau belum ada
        #     catatan revisi → pakai syarat 'ada bab'" — ITU SALAH (mengarang
        #     hak: S1 dengan 5 bab langsung terbuka semua padahal belum
        #     direvisi). Sudah dibuang sesuai keputusan Bos 03Okt26.
        bab_revisi = bab_sudah_direvisi(db, user, fid)

        hasil['kartu'] = _susun_kartu(bab_revisi)
        hasil['dasar'] = 'revisi'
        hasil['bab_revisi'] = sorted(bab_revisi)

    return hasil


def _bab_dari_berkas(f) -> list[int]:
    """Baca naskah dari penyimpanan lalu deteksi bab.

    Nonaktif berat: dibaca dari /app/uploads/<user_id>/<nama_simpan>.
    Kalau gagal → kembalikan [] (JUJUR: tidak tahu, bukan menebak).
    """
    import os
    import zipfile
    import re as _re
    import html as _html
    try:
        uid = getattr(f, 'user_id', None)
        simpan = getattr(f, 'nama_simpan', None)
        if not uid or not simpan:
            return []
        p = f'/app/uploads/{uid}/{simpan}'
        if not os.path.exists(p) or not p.lower().endswith('.docx'):
            return []
        with zipfile.ZipFile(p) as z:
            xml = z.read('word/document.xml').decode('utf-8', 'replace')
        xml = _re.sub(r'</w:p>', '\n', xml)
        xml = _re.sub(r'<[^>]+>', '', xml)
        return bab_terdeteksi(_html.unescape(xml))
    except Exception:
        return []


def _susun_kartu(bab_revisi: set) -> list[dict]:
    """3 kartu tahap — terbuka HANYA kalau bab-nya SUDAH DIREVISI.

    ⚠️ SUMBER KEBENARAN (dicek 03Okt26, jangan menebak):
        `revisi_history` (file_id, section_id, intent) +
        `section_state.kategori` = 'bab1'…'bab5'
    ⇒ yang menentukan TERBUKA bukan "naskah punya bab", tapi
      "bab itu sudah direvisi lewat EduAi".

    🔴 BUG FIX 03Okt26 (temuan POTRET): sebelumnya hanya cek "ada bab" →
       S1 dengan 5 bab langsung TERBUKA SEMUA padahal belum direvisi.

    ⚠️ BUG FIX 03Okt26 ke-2: kartu 2 & 3 dulu mencetak kalimat syarat DUA
       KALI (keterangan + alasan isinya sama) → keterangan kini hanya manfaat.
    """
    kartu = []
    for no, judul, ket, wajib in TAHAP:
        ada = [k for k in wajib if k in bab_revisi]
        terbuka = len(ada) == len(wajib)
        kurang = [k.replace('bab', 'BAB ') for k in wajib if k not in bab_revisi]
        if terbuka:
            alasan = ''
        elif no == 1:
            alasan = ('Terbuka setelah revisi lewat EduAi selesai: '
                      + ', '.join(kurang) + '.')
        else:
            alasan = f'Terbuka saat {kurang[0]} selesai kamu revisi.'
        kartu.append({
            'nomor': no, 'judul': judul, 'keterangan': ket,
            'terbuka': terbuka, 'alasan': alasan,
            #  bab pertama yang dibuka saat "Mulai Belajar" diklik (LANGKAH 2)
            'bab_pertama': int(wajib[0][3:]),
            #  mesin insight sudah ada (LANGKAH 2, 04Okt26) — kartu yang
            #  terbuka BENAR-BENAR punya isi sekarang
            'ada_isi': True,
        })
    return kartu


def bab_sudah_direvisi(db, user, fid: int) -> set:
    """Kategori bab yang SUDAH direvisi user ini pada naskah ini.

    Sumber: `section_state.kategori` untuk file+user itu.
    ⚠️ Jangan tebak: kalau tabel kosong → set() kosong (artinya belum ada).

    🚨 04Okt26 (ACC Bos, Opsi A) — DUA BENTUK KATEGORI, JANGAN LUPA:
      (a) revisi per SUB-BAB  → kategori 'bab1'…'bab5'  (state.deteksi_subbab)
      (b) revisi per BAB BESAR → kategori 'bab'          (state.deteksi_bab_besar)
    Mahasiswa wajar memilih (b) — di editor tertulis "Revisi BAB I". Dulu
    bentuk (b) DITOLAK di sini → mahasiswa bayar token, tapi Mode Belajar
    tetap terkunci ("belum direvisi" padahal sudah). Terbukti di produksi:
    naskah Asih file 81 → kategori='bab', section_id='BAB I' → set() kosong.
    ⇒ 'bab' dipetakan dari `section_id` ('BAB I' → bab1). TIDAK mengubah
      mesin catatan/AI (state.py) — cukup disambungkan di sini.
    """
    hasil = set()
    try:
        from .models import SectionState
        baris = (db.query(SectionState)
                 .filter(SectionState.file_id == int(fid),
                         SectionState.user_id == getattr(user, 'id', None))
                 .all())
        for r in baris:
            k = (getattr(r, 'kategori', '') or '').strip().lower()
            if k.startswith('bab') and k[3:].isdigit():
                hasil.add(k)
            elif k == 'bab':
                #  BAB BESAR → nomor dari section_id ('BAB I' / '2.1.3' / 'BAB 3')
                n = _nomor_bab_dari_section(getattr(r, 'section_id', '') or '')
                if n:
                    hasil.add(f'bab{n}')
    except Exception:
        return set()
    return hasil


def _nomor_bab_dari_section(section_id: str) -> int | None:
    """'BAB I' → 1 · 'BAB 3' → 3 · '2.1.3' → 2 · '' → None.

    Dipakai HANYA untuk bab besar (kategori 'bab'). Romawi & angka dua-duanya
    diterima; kalau tidak yakin → None (jujur, jangan menebak).
    """
    s = (section_id or '').strip().upper()
    if not s:
        return None
    m = re.match(r'^BAB\s+([IVXLC]{1,5})\b', s)
    if m:
        return _romawi_ke_angka(m.group(1))
    m = re.match(r'^BAB\s+(\d{1,2})\b', s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= BATAS_BAB else None
    m = re.match(r'^(\d{1,2})(?:\.|$)', s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= BATAS_BAB else None
    return None


def _romawi_ke_angka(romawi: str) -> int | None:
    """'IV' → 4. Salah tulis → None. Sampai BATAS_BAB (bukan cuma 9)."""
    peta = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    s = (romawi or '').strip().upper()
    if not s or any(c not in peta for c in s):
        return None
    total, lama = 0, 0
    for c in reversed(s):
        n = peta[c]
        total += -n if n < lama else n
        lama = max(lama, n)
    return total if 1 <= total <= BATAS_BAB else None


# ═══════════════════════════════════════════════════════════════════════
#  LANGKAH 2 — MESIN MINI INSIGHT (04Okt26, ACC Bos: Q1=A paket, Q2=A naskah)
#
#  PRINSIP HEMAT (§4.8 — wajib):
#    · Sumber isi = baca naskah SEKALI lewat fungsi yang SUDAH ADA
#      (`ai._teks_dari_berkas` + `versi.ambil_bab`) — TIDAK bikin pembaca baru
#    · Hitung PER BAB (kecil), bukan seluruh naskah sekaligus
#    · SIMPAN di `belajar_naskah.insight_json` → buka lagi = 0 token
#    · Biaya DITANGGUNG PAKET (putusan Bos Q1=A) → tidak potong saldo user
# ═══════════════════════════════════════════════════════════════════════

#  aturan isi insight: 3 butir PER BAB (konsisten supaya bisa diuji)
INSIGHT_PER_BAB = 3
SOAL_PER_BAB = 4   # L2 Bank Soal: 1 pertanyaan tiap level (dasar/menengah/tajam/jebakan)


def _label_bab(n: int) -> str:
    """'bab3' → 'BAB III' (label yang dipakai deteksi bab produksi)."""
    return f'BAB {_angka_romawi(n)}'


def naskah_milik(db, user, fid) -> int | None:
    """Balas id naskah KALAU milik user ini; kalau bukan → None.

    ⚠️ Pagar wajib: jangan sampai user A bisa lihat insight naskah user B.
    """
    try:
        from .models import FileBerkas
        f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
        if f is None or getattr(f, 'user_id', None) != getattr(user, 'id', None):
            return None
        return int(fid)
    except Exception:
        return None


def naskah_sudah_aktif(db, user, fid) -> dict | None:
    """Balas info naskah KALAU sudah diaktifkan Mode Belajar; kalau belum → None.

    ⚠️ 04Okt26 BUG UJI: kunci asli dari `_aktif_untuk()` = `'status'`
    (BUKAN `'aktif'`) — Wulan sempat menebak `n.get('aktif')` → SELALU False
    walau barisnya ada. Sekarang pakai kunci yang BENAR + sertakan nama naskah.
    """
    try:
        info = _aktif_untuk(db, getattr(user, 'id', None)).get(int(fid))
        if not info:
            return None
        if (info.get('status') or '') != 'aktif':
            return None
        from .models import FileBerkas
        f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
        return {'id': int(fid), 'nama': getattr(f, 'nama', '') or ''}
    except Exception:
        return None


def teks_bab(db, u, fid: int, n: int) -> str:
    """Isi TEKS satu bab dari naskah — pakai fungsi produksi yang sudah ada.

    ⚠️ 04Okt26: `section_state.isi_teks` TIDAK menyimpan isi bab utuh
    (isinya 'dokumen' + sub-bab saja) ⇒ WAJIB baca naskah.
    Jalur: `ai._teks_dari_berkas(path, nama)` → `versi.ambil_bab(teks, label)`.

    🚨 JEBAKAN YANG TERBUKTI (uji 04Okt26): `versi.ambil_bab()` baris terakhir
    `return '', teks, ''` — kalau label TIDAK DITEMUKAN, ia membalas SELURUH
    naskah (bukan ''). Akibatnya label palsu (mis. BAB 9) dianggap ada dan
    insight dibuat dari dokumen UTUH (boros token + HALUSINASI topik).
    ⇒ WAJIB periksa dulu labelnya BENAR-BENAR ADA, pakai detektor yang SAMA
      dengan produksi (`versi.deteksi_bab` / `_deteksi_bagian`) — persis pola
      `ai._label_ada()`. Tidak ada label → balas '' (JANGAN mengarang).
    """
    try:
        from .models import FileBerkas
        from .ai import _teks_dari_berkas, UPLOAD_DIR
        from .versi import ambil_bab, deteksi_bab, _deteksi_bagian

        f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
        if f is None:
            return ''
        p = UPLOAD_DIR / str(f.user_id) / (getattr(f, 'nama_simpan', '') or '')
        if not p.exists():
            return ''
        naskah = _teks_dari_berkas(p, getattr(f, 'nama', '') or '').strip()
        if not naskah:
            return ''

        label = _label_bab(n)
        #  label harus BENAR-BENAR ada (kalau tidak → JANGAN balas seluruh naskah)
        daftar = None
        for coba in (_deteksi_bagian(naskah), deteksi_bab(naskah)):
            if any(str(b.get('label') or '').strip().upper() == label for b in coba):
                daftar = coba
                break
        if daftar is None:
            return ''

        #  🚨 JEBAKAN: `ambil_bab` balas SELURUH naskah kalau label TAK ketemu.
        #     Tapi di naskah PROPOSAL, "BAB I" memang satu-satunya bab → isinya
        #     WAJAR panjang (mis. 87% naskah). Jadi JANGAN pakai ambang 85%
        #     buta: pakai beda label benar-benar ada / tidak -> itu sudah dijaga
        #     di atas. Pengaman kedua di sini hanya untuk kasus label TIDAK ADA
        #     tapi tetap dibalas semua (seharusnya mustahil setelah cek di atas).
        sebelum, isi, sesudah = ambil_bab(naskah, label)
        isi = (isi or '').strip()
        if not isi:
            return ''
        #  kalau yang dibalas = NASKAH UTUH (tanpa potongan sama sekali),
        #  berarti label tidak dikenali ambil_bab → jangan kirim dokumen penuh
        if abs(len(isi) - len(naskah)) < 50:
            return ''
        return isi
    except Exception:
        return ''


def baca_insight(db, u, fid: int) -> dict:
    """Insight yang SUDAH tersimpan (0 token). {'bab1': [butir, …], …}."""
    try:
        from .models import BelajarNaskah
        import json as _json
        bn = (db.query(BelajarNaskah)
              .filter(BelajarNaskah.file_id == int(fid),
                      BelajarNaskah.user_id == getattr(u, 'id', None)).first())
        if bn is None or not bn.insight_json:
            return {}
        d = _json.loads(bn.insight_json)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _simpan_insight(db, u, fid: int, n: int, butir: list) -> None:
    """Simpan butir insight bab `n` → belajar_naskah.insight_json (permanen)."""
    import json as _json
    from .models import BelajarNaskah
    bn = (db.query(BelajarNaskah)
          .filter(BelajarNaskah.file_id == int(fid),
                  BelajarNaskah.user_id == getattr(u, 'id', None)).first())
    if bn is None:
        bn = BelajarNaskah(file_id=int(fid), user_id=getattr(u, 'id', None),
                           status='aktif', insight_json='{}')
        db.add(bn)
        db.flush()
    try:
        d = _json.loads(bn.insight_json or '{}')
        if not isinstance(d, dict):
            d = {}
    except Exception:
        d = {}
    d[f'bab{n}'] = butir
    bn.insight_json = _json.dumps(d, ensure_ascii=False)
    db.commit()


PROMPT_INSIGHT = """Kamu membantu mahasiswa memahami naskahnya sendiri.

TUGAS: baca potongan bab di bawah, lalu tulis TEPAT {jml} butir pemahaman.

ATURAN WAJIB (jangan dilanggar):
1. Setiap butir WAJIB menyertakan KUTIPAN SINGKAT dari naskah (maks 12 kata,
   ambil apa adanya) sebagai bukti — jangan mengarang kutipan.
2. Bahasa Indonesia sederhana, seperti kakak tingkat menjelaskan ke adik.
3. JANGAN menilai bagus/jelek. JANGAN menyarankan perbaikan. Cukup bantu PAHAM.
4. Jangan pakai kata menakutkan (salah, gagal, bahaya). Nada tenang & hangat.
5. Format BALASAN PERSIS begini, tanpa pembuka/penutup lain:

BUTIR 1
tema: <3-5 kata>
isi: <1-2 kalimat penjelasan>
kutipan: <potongan asli dari naskah>

BUTIR 2
tema: ...
isi: ...
kutipan: ...

{dari_berkas}

ISI {label}:
\"\"\"
{isi}
\"\"\"
"""


def _urai_butir(teks: str, jml: int) -> list:
    """Urai balasan model → daftar {tema, isi, kutipan}. Tahan bentuk aneh."""
    import re as _re
    blok = _re.split(r'(?im)^\s*BUTIR\s*\d+\s*$', teks or '')
    butir = []
    for b in blok[1:]:
        tema = isi = kutip = ''
        for baris in (b or '').splitlines():
            s = baris.strip()
            low = _re.sub(r'^\*+|[*_]+$', '', s).strip()
            for kunci, simpan in (('tema:', 't'), ('isi:', 'i'), ('kutipan:', 'k')):
                if low.lower().startswith(kunci):
                    nilai = low[len(kunci):].strip().strip('"“”')
                    if simpan == 't':
                        tema = nilai
                    elif simpan == 'i':
                        isi = nilai
                    else:
                        kutip = nilai
        if tema or isi:
            butir.append({'tema': tema or 'Inti bab', 'isi': isi,
                          'kutipan': kutip})
        if len(butir) >= jml:
            break
    return butir


async def hitung_insight(db, u, fid: int, n: int) -> dict:
    """Hitung insight satu bab lalu SIMPAN permanen. Balas {'butir': […], 'baru': bool}.

    ⚠️ PAGAR HEMAT: kalau insight bab itu SUDAH ada di DB → pakai yang
       tersimpan, JANGAN panggil AI lagi (0 token). Ini yang diuji.
    """
    from .models import FileBerkas
    from .ai import _panggil_9router

    #  1. sudah ada? → pakai simpanan (0 token)
    tersimpan = baca_insight(db, u, fid)
    kunci = f'bab{n}'
    if tersimpan.get(kunci):
        return {'butir': tersimpan[kunci], 'baru': False}

    #  2. ambil isi bab (dari naskah — fungsi produksi yang sudah ada)
    isi = teks_bab(db, u, fid, n)
    if not isi:
        return {'butir': [], 'baru': False, 'pesan':
                'Bab ini belum bisa dibaca. Simpan dulu naskahnya di editor, lalu coba lagi.'}

    #  3. sebut nama berkas (jujur, biar user tahu bahan mana yang dibaca)
    try:
        f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
        dari = f'SUMBER: {getattr(f, "nama", "") or "naskah"}'
    except Exception:
        dari = ''

    prompt = PROMPT_INSIGHT.format(jml=INSIGHT_PER_BAB, label=_label_bab(n),
                                   isi=isi[:12000], dari_berkas=dari)
    konten, _info = await _panggil_9router(prompt, timeout=180.0)
    butir = _urai_butir(konten, INSIGHT_PER_BAB)
    if butir:
        _simpan_insight(db, u, fid, n, butir)
    return {'butir': butir, 'baru': True}


def baca_soal(db, u, fid: int) -> dict:
    """Bank soal yang SUDAH tersimpan (0 token). {'bab1': {...}, …}."""
    try:
        from .models import BelajarNaskah
        import json as _json
        bn = (db.query(BelajarNaskah)
              .filter(BelajarNaskah.file_id == int(fid),
                      BelajarNaskah.user_id == getattr(u, 'id', None)).first())
        if bn is None or not bn.soal_json:
            return {}
        d = _json.loads(bn.soal_json)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _simpan_soal(db, u, fid: int, n: int, soal: dict) -> None:
    """Simpan bank soal bab `n` → belajar_naskah.soal_json (permanen).

    ⚠️ `soal_json` SUDAH ADA di tabel belajar_naskah semenjak awal (kolom
       menunggu dipakai). JANGAN bikin tabel baru — titipkan di sini.
    """
    import json as _json
    from .models import BelajarNaskah
    bn = (db.query(BelajarNaskah)
          .filter(BelajarNaskah.file_id == int(fid),
                  BelajarNaskah.user_id == getattr(u, 'id', None)).first())
    if bn is None:
        bn = BelajarNaskah(file_id=int(fid), user_id=getattr(u, 'id', None),
                           status='aktif', soal_json='{}')
        db.add(bn)
        db.flush()
    try:
        d = _json.loads(bn.soal_json or '{}')
        if not isinstance(d, dict):
            d = {}
    except Exception:
        d = {}
    d[f'bab{n}'] = soal
    bn.soal_json = _json.dumps(d, ensure_ascii=False)
    db.commit()


PROMPT_SOAL = """Kamu membantu mahasiswa SIAP menghadapi ujian naskahnya sendiri.

TUGAS: dari potongan bab di bawah, susun pertanyaan yang BIASA DITANYAKAN
PENGUJI saat sidang. Buat TEPAT {jml_jenis} pertanyaan, satu untuk tiap
tingkat kesulitan berikut:

  dasar    → pertanyaan pembuka, menguji pemahaman istilah/inti bab
  menengah → menguji alasan & hubungan antar bagian dalam bab
  tajam    → menguji kelemahan/batas/keterbatasan pilihan penulis
  jebakan  → pertanyaan yang mudah dijawab SALAH bila mahasiswa tak teliti

ATURAN WAJIB (jangan dilanggar):
1. Pertanyaan WAJIB bertumpu pada ISI NASKAH di bawah — bukan pertanyaan
   umum yang bisa ditanyakan ke naskah apa pun. Sebut istilah/angka/konsep
   yang BENAR-BENAR ada di potongan itu.
2. Setiap pertanyaan WAJIB disertai KUTIPAN SINGKAT dari naskah (maks 12 kata,
   ambil apa adanya) sebagai titik tumpu — jangan mengarang kutipan.
3. Setiap pertanyaan disertai "kunci": 1-2 kalimat arah jawaban yang BENAR
   (bukan jawaban penuh) sebagai bahan penilaian.
4. Bahasa Indonesia sederhana, nada tenang & hangat. JANGAN menakut-nakuti.
5. Format BALASAN PERSIS begini, tanpa pembuka/penutup lain:

SOAL 1
level: dasar
tanya: <pertanyaan>
tumpu: <potongan asli dari naskah>
kunci: <1-2 kalimat arah jawaban>

SOAL 2
level: menengah
tanya: ...

{dari_berkas}

ISI {label}:
\"\"\"
{isi}
\"\"\"
"""


def _urai_soal(teks: str, jml: int) -> list:
    """Urai balasan model → daftar {level, tanya, tumpu, kunci}. Tahan bentuk aneh."""
    import re as _re
    blok = _re.split(r'(?im)^\s*SOAL\s*\d+\s*$', teks or '')
    soal = []
    sah = ('dasar', 'menengah', 'tajam', 'jebakan')
    for b in blok[1:]:
        level = tanya = tumpu = kunci = ''
        for baris in (b or '').splitlines():
            s = baris.strip()
            low = _re.sub(r'^[*_#]+|[*_]+$', '', s).strip()
            for k, simpan in (('level:', 'l'), ('tanya:', 't'),
                              ('tumpu:', 'p'), ('kunci:', 'k')):
                if low.lower().startswith(k):
                    nilai = low[len(k):].strip().strip('"“”')
                    if simpan == 'l':
                        level = nilai
                    elif simpan == 't':
                        tanya = nilai
                    elif simpan == 'p':
                        tumpu = nilai
                    else:
                        kunci = nilai
        level = (level or '').lower().strip()
        if level not in sah:
            level = sah[len(soal) % len(sah)]
        if tanya:
            soal.append({'level': level, 'tanya': tanya,
                         'tumpu': tumpu, 'kunci': kunci})
        if len(soal) >= jml:
            break
    return soal


async def hitung_soal(db, u, fid: int, n: int) -> dict:
    """Susun bank soal satu bab lalu SIMPAN permanen.

    Balas {'soal': […], 'baru': bool}.

    ⚠️ PAGAR HEMAT (sama seperti `hitung_insight`): kalau bank soal bab itu
       SUDAH ada → pakai simpanan, JANGAN panggil AI lagi (0 token).
    """
    from .models import FileBerkas
    from .ai import _panggil_9router

    tersimpan = baca_soal(db, u, fid)
    kunci = f'bab{n}'
    lama = tersimpan.get(kunci) or {}
    if lama.get('soal'):
        return {'soal': lama['soal'], 'baru': False}

    isi = teks_bab(db, u, fid, n)
    if not isi:
        return {'soal': [], 'baru': False, 'pesan':
                'Bab ini belum bisa dibaca. Simpan dulu naskahnya di editor, lalu coba lagi.'}

    try:
        f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
        dari = f'SUMBER: {getattr(f, "nama", "") or "naskah"}'
    except Exception:
        dari = ''

    prompt = PROMPT_SOAL.format(jml_jenis=SOAL_PER_BAB, label=_label_bab(n),
                                isi=isi[:12000], dari_berkas=dari)
    konten, _info = await _panggil_9router(prompt, timeout=180.0)
    soal = _urai_soal(konten, SOAL_PER_BAB)
    if soal:
        _simpan_soal(db, u, fid, n, {'soal': soal})
    return {'soal': soal, 'baru': True}


def baca_uji(db, u, fid: int) -> dict:
    """Simulasi yang SUDAH tersimpan (0 token). {'bab1': {'jawaban': {...}}}."""
    return _isi_bab_selesai(db, u, fid, 'uji')


def _isi_bab_selesai(db, u, fid: int, bagian: str) -> dict:
    """Ambil SATU bagian dari belajar_naskah.bab_selesai (JSON per bab).

    ⚠️ `bab_selesai` SUDAH ADA di tabel sejak awal (kolom menunggu dipakai).
       Isinya: {'bab1': {'uji': {...}}, 'bab2': {'uji': {...}}} — README
       agar tidak perlu kolom baru untuk simulasi & skor.
    """
    try:
        import json as _json
        from .models import BelajarNaskah
        bn = (db.query(BelajarNaskah)
              .filter(BelajarNaskah.file_id == int(fid),
                      BelajarNaskah.user_id == getattr(u, 'id', None)).first())
        if bn is None or not bn.bab_selesai:
            return {}
        d = _json.loads(bn.bab_selesai)
        if not isinstance(d, dict):
            return {}
        keluar = {}
        for k, v in d.items():
            if isinstance(v, dict) and bagian in v:
                keluar[k] = v[bagian]
        return keluar
    except Exception:
        return {}


def _tulis_bab_selesai(db, u, fid: int, n: int, bagian: str, nilai) -> None:
    """Tulis SATU bagian (mis. 'uji') untuk satu bab → bab_selesai.bab<n>."""
    import json as _json
    from .models import BelajarNaskah
    bn = (db.query(BelajarNaskah)
          .filter(BelajarNaskah.file_id == int(fid),
                  BelajarNaskah.user_id == getattr(u, 'id', None)).first())
    if bn is None:
        bn = BelajarNaskah(file_id=int(fid), user_id=getattr(u, 'id', None),
                           status='aktif', bab_selesai='{}')
        db.add(bn)
        db.flush()
    try:
        d = _json.loads(bn.bab_selesai or '{}')
        if not isinstance(d, dict):
            d = {}
    except Exception:
        d = {}
    k = f'bab{n}'
    if not isinstance(d.get(k), dict):
        d[k] = {}
    d[k][bagian] = nilai
    bn.bab_selesai = _json.dumps(d, ensure_ascii=False)
    db.commit()


PROMPT_NILAI = """Kamu PENGUJI yang ramah dalam sidang naskah akademik. Kamu menilai
JAWABAN MAHASISWA atas satu pertanyaan, berdasarkan naskahnya sendiri.

PERTANYAAN:
{tanya}

ARAH JAWABAN YANG BENAR (bahan penilaian, jangan ditampilkan mentah):
{kunci}

KUTIPAN NASKAH:
{tumpu}

JAWABAN MAHASISWA:
\"\"\"
{jawaban}
\"\"\"

ATURAN WAJIB (jangan dilanggar):
1. Nilai JUJUR dari 0-100 sesuai seberapa dekat jawaban dengan naskah.
   - 80-100: inti benar & lengkap
   - 60-79 : inti benar, ada bagian kurang
   - 40-59 : sebagian benar, bagian penting belum tersentuh
   - 0-39  : belum menangkap inti, atau jawaban di luar naskah
2. WAJIB menyebut isi NASKAH (kutipan di atas) saat menjelaskan penilaian.
   DILARANG menilai di luar isi naskah. DILARANG mengarang fakta baru.
3. Nada HANGAT & MENENANGKAN — seperti pembimbing yang membantu, bukan menghakimi.
4. DILARANG memakai kata: salah, gagal, buruk, bodoh, mengecewakan, habis.
   Kalau kurang tepat, katakan "bisa ditambah" / "belum tersentuh" dengan halus.
5. Format BALASAN PERSIS begini, tanpa pembuka/penutup lain:

nilai: <angka 0-100>
judul: <2-4 kata, mis. "Sudah dekat" / "Perlu dibaca lagi">
tepat: <1-2 kalimat: apa yang SUDAH tepat dari jawabannya>
tambah: <1-2 kalimat: apa yang bisa ditambah, rujuk isi naskah>
"""


def _urai_nilai(teks: str) -> dict:
    """Urai balasan model → {'nilai': int, 'judul', 'tepat', 'tambah'}."""
    import re as _re
    keluar = {'nilai': None, 'judul': '', 'tepat': '', 'tambah': ''}
    for baris in (teks or '').splitlines():
        s = baris.strip()
        low = _re.sub(r'^[*_#]+|[*_]+$', '', s).strip()
        for k, simpan in (('nilai:', 'n'), ('judul:', 'j'),
                          ('tepat:', 't'), ('tambah:', 'b')):
            if low.lower().startswith(k):
                v = low[len(k):].strip().strip('"“”')
                if simpan == 'n':
                    m = _re.search(r'\d+', v)
                    if m:
                        keluar['nilai'] = max(0, min(100, int(m.group(0))))
                elif simpan == 'j':
                    keluar['judul'] = v
                elif simpan == 't':
                    keluar['tepat'] = v
                else:
                    keluar['tambah'] = v
    if keluar['nilai'] is None:
        m = _re.search(r'\b(\d{1,3})\b', teks or '')
        if m:
            keluar['nilai'] = max(0, min(100, int(m.group(1))))
    if not keluar['judul']:
        n = keluar['nilai']
        keluar['judul'] = ('Sudah dekat' if n is not None and n >= 75 else
                           'Perlu dibaca lagi' if n is not None and n >= 45 else
                           'Ayo lihat naskahnya lagi')
    return keluar


async def nilai_jawaban(db, u, fid: int, n: int, soal_ke: int, jawaban: str) -> dict:
    """Nilai SATU jawaban mahasiswa terhadap soal ke-`soal_ke` (0-based).

    Balas dict nilai + disimpan di bab_selesai.bab<n>.uji (permanen).
    """
    from .ai import _panggil_9router

    jawaban = (jawaban or '').strip()
    if len(jawaban) < 5:
        return {'ok': False, 'pesan': 'Tulis dulu jawabanmu, walaupun singkat.'}

    bank = (baca_soal(db, u, fid).get(f'bab{n}') or {}).get('soal') or []
    if not (0 <= soal_ke < len(bank)):
        return {'ok': False, 'pesan': 'Soal itu tidak ditemukan.'}
    s = bank[soal_ke]

    prompt = PROMPT_NILAI.format(tanya=s.get('tanya', ''),
                                 kunci=s.get('kunci', ''),
                                 tumpu=s.get('tumpu', ''),
                                 jawaban=jawaban[:4000])
    konten, _info = await _panggil_9router(prompt, timeout=180.0)
    hasil = _urai_nilai(konten)
    hasil['soal_ke'] = soal_ke
    hasil['level'] = s.get('level', '')
    hasil['jawaban'] = jawaban[:2000]
    hasil['tanya'] = s.get('tanya', '')
    hasil['kunci'] = s.get('kunci', '')
    hasil['tumpu'] = s.get('tumpu', '')

    uji = baca_uji(db, u, fid)
    lama = (uji.get(f'bab{n}') or {}).get('jawaban') or {}
    if not isinstance(lama, dict):
        lama = {}
    lama[str(soal_ke)] = hasil
    _tulis_bab_selesai(db, u, fid, n, 'uji',
                       {'jawaban': lama, 'diubah': datetime.utcnow().isoformat()})
    return {'ok': True, 'hasil': hasil}


def skor_bab(db, u, fid: int, n: int) -> dict:
    """L4 — skor penguasaan satu bab (dihitung dari jawaban yang SUDAH dinilai)."""
    uji = (baca_uji(db, u, fid).get(f'bab{n}') or {}).get('jawaban') or {}
    bank = (baca_soal(db, u, fid).get(f'bab{n}') or {}).get('soal') or []
    if not isinstance(uji, dict) or not uji:
        return {'ada': False, 'terjawab': 0, 'total': len(bank), 'skor': None,
                'per_level': {}}
    nilai = [v.get('nilai') for v in uji.values()
             if isinstance(v, dict) and isinstance(v.get('nilai'), int)]
    per_level = {}
    for v in uji.values():
        if not isinstance(v, dict) or not isinstance(v.get('nilai'), int):
            continue
        per_level.setdefault(v.get('level') or 'lain', []).append(v['nilai'])
    per_level = {k: round(sum(x) / len(x)) for k, x in per_level.items()}
    skor = round(sum(nilai) / len(nilai)) if nilai else None
    return {'ada': bool(nilai), 'terjawab': len(nilai), 'total': len(bank),
            'skor': skor, 'per_level': per_level}


def skor_naskah(db, u, fid: int) -> dict:
    """L4 ringkas — rata-rata skor seluruh bab yang sudah diuji (bahan pembimbing)."""
    bab = sorted(int(k[3:]) for k in bab_sudah_direvisi(db, u, fid)
                 if str(k).startswith('bab') and str(k[3:]).isdigit())
    rinci = []
    for n in bab:
        s = skor_bab(db, u, fid, n)
        if s['ada']:
            rinci.append({'bab': n, 'label': _label_bab(n), **s})
    if not rinci:
        return {'ada': False, 'rinci': [], 'skor': None}
    skor = round(sum(r['skor'] for r in rinci) / len(rinci))
    return {'ada': True, 'rinci': rinci, 'skor': skor}


def aktivasi(db, user, fid: int):
    """Aktifkan Mode Belajar untuk SATU naskah.

    ATURAN (ACC Bos 03Okt26):
      · melekat pada 1 naskah, TIDAK bisa ganti
      · jatah terpakai SAAT KLIK (opsi A)
      · naskah WAJIB milik user sendiri
      · jatah habis → tolak dengan jalan keluar (AddOn Rp 75.000)
    Mengembalikan (ok: bool, pesan: str).
    """
    from .models import BelajarNaskah, FileBerkas
    from sqlalchemy import func

    uid = int(getattr(user, 'id', 0))
    boleh, jatah = hak_paket(user)
    if not boleh:
        return False, ('Mode Belajar tersedia mulai paket Peneliti. '
                       'Naikkan paket untuk membukanya.')

    f = db.execute(select(FileBerkas).where(FileBerkas.id == int(fid))).scalars().first()
    if f is None or int(getattr(f, 'user_id', 0)) != uid:
        return False, 'Naskah itu bukan milikmu.'

    sudah = db.execute(
        select(BelajarNaskah).where(BelajarNaskah.user_id == uid,
                                    BelajarNaskah.file_id == int(fid))
    ).scalars().first()
    if sudah is not None:
        return True, 'Naskah ini sudah aktif.'

    terpakai = int(db.execute(
        select(func.count()).select_from(BelajarNaskah)
        .where(BelajarNaskah.user_id == uid)
    ).scalar() or 0)
    if terpakai >= jatah:
        sisa_addon = 'Tambah AddOn Mode Belajar untuk naskah berikutnya.'
        return False, f'Jatah Mode Belajar untuk naskah ini sudah dipakai. {sisa_addon}'

    baris = BelajarNaskah(
        file_id=int(fid), user_id=uid, status='aktif',
        dibuat=datetime.utcnow(), diubah=datetime.utcnow(),
    )
    db.add(baris)
    db.commit()
    return True, 'Mode Belajar diaktifkan untuk naskah ini.'
