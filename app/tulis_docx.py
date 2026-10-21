"""TULIS HASIL REVISI KE .DOCX — Langkah D (ACC Bos 16Sep26).

═══════════════════════════════════════════════════════════════════════════
KENAPA MODUL INI ADA (hasil ukur, bukan dugaan — 16Sep26)
═══════════════════════════════════════════════════════════════════════════
Sebelum modul ini, hasil revisi AI HANYA tersimpan di database (`versi_dokumen`
+ `proses_ai`) dan ditampilkan di panel. Berkas .docx mahasiswa TIDAK PERNAH
berubah. Bukti: `grep -n write_bytes app/*.py` → hanya 2 tempat (unggah &
callback simpan OnlyOffice) — tidak ada satu pun yang menulis hasil AI.

Akibatnya mahasiswa harus SALIN MANUAL ("Salin hasil") lalu tempel sendiri.
Untuk naskah 60.000 karakter, itu pekerjaan berat dan rawan salah tempel.

═══════════════════════════════════════════════════════════════════════════
3 LAPIS PENGUNCIAN (MASTER_PLAN §4.12 poin F) — modul ini Lapis 3
═══════════════════════════════════════════════════════════════════════════
Lapis 1 (UI)      : modal skeleton, dokumen terkunci  → editor.html
Lapis 2 (Server)  : tolak forcesave selama AI jalan   → app/main.py
Lapis 3 (ATOMIK)  : TULIS SEKALI DI AKHIR             → MODUL INI

Kenapa atomik: OnlyOffice punya auto-save. Kalau penulisan mengalir
sebagian-sebagian, user bisa menyimpan di tengah → editan user bercampur
hasil AI → dokumen KACAU dan `sidik_jari` tidak bisa membedakan milik siapa.
Jadi: rakit SELURUH isi baru di memori → tulis ke berkas sementara →
`os.replace()` (satu operasi atomik tingkat sistem berkas).

═══════════════════════════════════════════════════════════════════════════
ATURAN YANG DIPATUHI
═══════════════════════════════════════════════════════════════════════════
1. TANPA dependency baru — `zipfile` + `re` bawaan Python stdlib.
2. DOKUMEN ASLI DIBACKUP dulu (aturan Bos: jangan pernah kehilangan data).
3. Ganti HANYA paragraf milik bab yang direvisi; gambar/tabel/header/footer/
   styles TIDAK disentuh (paragraf di dalam `<w:tbl>` DILEWATI).
4. Kalau ragu (bab tidak ketemu / hasil kosong) → TOLAK dengan pesan jelas,
   JANGAN menulis. Lebih baik gagal terang-terangan daripada merusak naskah.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from .versi import BAB_SELURUH, deteksi_bab

log = logging.getLogger('eduai.tulis_docx')

# ── Pola XML Word (semua bawaan `re`, tidak perlu library) ────────────────
# `<w:p ...>...</w:p>` — paragraf TIDAK bisa bersarang, jadi non-greedy aman.
# Lookahead `(?=[\s>/])` WAJIB supaya `<w:pPr>` / `<w:pStyle>` tidak ikut.
_P = re.compile(r'<w:p(?=[\s>/])(?:[^>]*)>(?:(?!<w:p(?=[\s>/])).)*?</w:p>', re.S)
_TBL = re.compile(r'<w:tbl(?=[\s>/]).*?</w:tbl>', re.S)
_PPR = re.compile(r'<w:pPr>.*?</w:pPr>', re.S)
_RUN1 = re.compile(r'<w:r(?=[\s>/])[^>]*>(.*?)</w:r>', re.S)
_RPR = re.compile(r'<w:rPr>.*?</w:rPr>', re.S)
_T = re.compile(r'<w:t[^>]*>(.*?)</w:t>', re.S)
_HIGHLIGHT = re.compile(r'<w:highlight[^>]*/>')
_COLOR = re.compile(r'<w:color[^>]*/>')


def _escape(s: str) -> str:
    """Teks hasil AI → aman dimasukkan ke XML."""
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;'))


def _unescape(s: str) -> str:
    """Teks dari XML → teks biasa (kebalikannya)."""
    return (s.replace('&lt;', '<').replace('&gt;', '>')
             .replace('&quot;', '"').replace('&apos;', "'")
             .replace('&amp;', '&'))


def peta_paragraf(xml: str) -> list[dict]:
    """Daftar paragraf TINGKAT BADAN (bukan di dalam tabel) beserta posisinya.

    Mengembalikan [{awal, akhir, teks}] dengan `awal`/`akhir` = indeks karakter
    di dalam `xml`. Paragraf di dalam `<w:tbl>` DILEWATI supaya tabel
    (mis. tabel data penelitian) TIDAK rusak.
    """
    tabel = [(m.start(), m.end()) for m in _TBL.finditer(xml)]

    def di_dalam_tabel(pos: int) -> bool:
        return any(a <= pos < b for a, b in tabel)

    keluar = []
    for m in _P.finditer(xml):
        if di_dalam_tabel(m.start()):
            continue
        teks = ''.join(_unescape(t) for t in _T.findall(m.group(0))).strip()
        keluar.append({'awal': m.start(), 'akhir': m.end(), 'teks': teks})
    return keluar


def _pPr(par_xml: str) -> str:
    """Format paragraf (spasi/indentasi/style) dari paragraf lama."""
    m = _PPR.search(par_xml)
    return m.group(0) if m else ''


def _rPr_bersih(par_xml: str) -> str:
    """Format huruf dari run pertama paragraf lama.

    `highlight` & `color` DIBUANG: kalau tidak, teks hasil revisi ikut
    berwarna kuning (sisa penanda komentar) — terlihat seperti belum selesai.
    """
    m = _RUN1.search(par_xml)
    if not m:
        return ''
    m2 = _RPR.search(m.group(1))
    if not m2:
        return ''
    rpr = _HIGHLIGHT.sub('', m2.group(0))
    return _COLOR.sub('', rpr)


def _par_baru(teks: str, pPr: str, rPr: str) -> str:
    """Bangun satu `<w:p>` dari teks biasa."""
    if not teks.strip():
        return ''
    return (f'<w:p>{pPr}<w:r>{rPr}'
            f'<w:t xml:space="preserve">{_escape(teks)}</w:t></w:r></w:p>')


def _mirip_judul(baris: str, judul_bab: str) -> bool:
    """Apakah baris ini judul bab? (dipakai memilih format judul vs isi)."""
    b = (baris or '').strip()
    if not b:
        return False
    #  🔴 BUG FIX 03Okt26 (temuan skripsi S1 nyata): `\b` menolak judul
    #  MENEMPEL ("BAB IPENDAHULUAN") — padahal itu bentuk paling sering di
    #  naskah nyata (ekspor Word/Docs). Sebelumnya baris judul menempel tidak
    #  dikenali → dibuat format ISI, bukan format JUDUL (tampilan bab rusak).
    #  Pola baru = sepola app/state.py:203 (nomor romawi HURUF BESAR).
    #  ⭐ 05Okt26 (putusan Bos "A"): + angka Arab & romawi-titik — disamakan
    #  dengan app/state.py. Pelajaran 03Okt26: pola kembar yang tertinggal =
    #  bab terdeteksi tapi JUDULNYA rusak saat ditulis (format jadi ISI).
    if re.match(r'(?i:BAB)[ \t]+([IVXLC]{1,5}|\d{1,2})[ \t]*[A-Z]?', b):
        return True
    if re.match(r'^[ \t]*[IVXLC]{1,5}\.[ \t]+[A-Z][A-Z0-9 ,\-]{3,70}[ \t\r]*$',
                b):
        return True
    if judul_bab and b.lower().startswith(judul_bab.lower()[:25]):
        return True
    return False


def _sisip(teks_lama: str, awal: int, akhir: int, isi_baru: str) -> str:
    """Ganti satu rentang karakter dengan teks baru (aman untuk XML)."""
    return teks_lama[:awal] + isi_baru + teks_lama[akhir:]


def rakit(
    xml: str,
    teks_baru: str,
    bab_label: str = BAB_SELURUH,
    judul_bab: str = '',
) -> tuple[str, dict]:
    """Kembalikan (xml_baru, info). Tanpa menyentuh berkas sama sekali.

    `info` berisi jumlah paragraf lama yang diganti & paragraf baru — dipakai
    untuk laporan jujur ke user ("berapa yang benar-benar berubah").
    """
    par = peta_paragraf(xml)
    if not par:
        return '', {'ok': False,
                    'pesan': 'Dokumen ini tidak punya paragraf teks yang bisa diganti.'}

    baris_baru = [b for b in (teks_baru or '').split('\n')]
    while baris_baru and not baris_baru[-1].strip():
        baris_baru.pop()
    if not any(b.strip() for b in baris_baru):
        return '', {'ok': False, 'pesan': 'Hasil revisi kosong — tidak ada yang ditulis.'}

    # ── Tentukan paragraf mana yang diganti ─────────────────────────────
    if bab_label == BAB_SELURUH:
        idx_awal, idx_akhir = 0, len(par) - 1
    else:
        # Petakan rentang KARAKTER bab → indeks paragraf.
        teks_gabung = '\n'.join(p['teks'] for p in par)
        # Posisi karakter awal tiap paragraf di dalam teks gabungan.
        posisi = []
        kursor = 0
        for p in par:
            posisi.append(kursor)
            kursor += len(p['teks']) + 1          # +1 = '\n'
        target = None
        for b in deteksi_bab(teks_gabung):
            if b['label'] != bab_label:
                continue
            if judul_bab and b['judul'] != judul_bab:
                continue
            target = b
            break
        if target is None:
            return '', {'ok': False,
                        'pesan': (f'{bab_label} tidak ditemukan lagi di dokumen '
                                  'sekarang. Mungkin sudah Anda ubah — '
                                  'periksa dulu sebelum menerapkan.')}
        # Paragraf yang posisinya masuk rentang bab.
        idx_awal = idx_akhir = None
        for i, p0 in enumerate(posisi):
            akhir_p = p0 + len(par[i]['teks'])
            if idx_awal is None and akhir_p > target['posisi']:
                idx_awal = i
            if p0 < target['akhir']:
                idx_akhir = i
        if idx_awal is None or idx_akhir is None or idx_akhir < idx_awal:
            return '', {'ok': False,
                        'pesan': f'Batas {bab_label} tidak jelas — demi keamanan '
                                 'naskah, penerapan dibatalkan.'}

    # ── Format: judul pakai format paragraf pertama, isi pakai paragraf isi ──
    pPr_judul = _pPr(xml[par[idx_awal]['awal']:par[idx_awal]['akhir']])
    rPr_judul = _rPr_bersih(xml[par[idx_awal]['awal']:par[idx_awal]['akhir']])
    pPr_isi, rPr_isi = '', ''
    for p in par[idx_awal:idx_akhir + 1][1:]:
        potongan = xml[p['awal']:p['akhir']]
        if pPr_isi == '':
            kandidat = _pPr(potongan)
            if kandidat and 'Heading' not in kandidat:
                pPr_isi, rPr_isi = kandidat, _rPr_bersih(potongan)
    if pPr_isi == '':                       # fallback: pakai format isi seadanya
        pPr_isi, rPr_isi = pPr_judul, rPr_judul

    baru = []
    for i, b in enumerate(baris_baru):
        if not b.strip():
            baru.append('')
            continue
        pakai_judul = (i == 0 and _mirip_judul(b, judul_bab))
        baru.append(_par_baru(b, pPr_judul if pakai_judul else pPr_isi,
                              rPr_judul if pakai_judul else rPr_isi))
    isi_baru = ''.join(x for x in baru if x)

    xml_baru = _sisip(xml, par[idx_awal]['awal'], par[idx_akhir]['akhir'], isi_baru)
    return xml_baru, {
        'ok': True,
        'paragraf_diganti': idx_akhir - idx_awal + 1,
        'paragraf_baru': len([x for x in baru if x]),
        'karakter_baru': len(teks_baru or ''),
        'bab': bab_label,
        'dari_paragraf': idx_awal + 1,
        'sampai_paragraf': idx_akhir + 1,
    }


def _cek_xml_sehat(xml: str) -> tuple[bool, str]:
    """Pemeriksaan wajib SEBELUM berkas ditulis: XML harus utuh & bisa dibaca.

    Ini pengaman terakhir. Kalau XML cacat, dokumen mahasiswa jadi rusak dan
    TIDAK bisa dibuka di Word — jauh lebih buruk daripada tidak menerapkan.
    """
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(xml.encode('utf-8'))
    except Exception as e:                                    # noqa: BLE001
        return False, f'XML hasil tidak sehat: {type(e).__name__}: {e}'
    if '<w:body>' not in xml or '</w:body>' not in xml:
        return False, 'Struktur <w:body> hilang.'
    for tag in ('w:sectPr',):
        if xml.count(f'<{tag}') == 0 and f'<{tag} ' not in xml:
            pass                                # sectPr boleh tidak ada
    # paragraf harus berpasangan
    return True, ''


def terapkan_ke_berkas(
    path: Path,
    teks_baru: str,
    bab_label: str = BAB_SELURUH,
    judul_bab: str = '',
    backup_dir: Path | None = None,
) -> dict:
    """Tulis hasil revisi ke .docx — ATOMIK + BACKUP. Inti Langkah D.

    Urutan (jangan diubah):
      1. baca isi .docx (arsip ZIP) ke MEMORI
      2. rakit xml baru di MEMORI
      3. PERIKSA xml sehat (tolak kalau cacat)
      4. backup berkas asli
      5. tulis ke berkas SEMENTARA di folder yang sama
      6. `os.replace()` → atomik, tidak ada keadaan setengah jadi
    """
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'pesan': 'Berkas dokumen tidak ditemukan di server.'}

    try:
        with zipfile.ZipFile(path) as z:
            semua = {n: z.read(n) for n in z.namelist()}
        urutan = zipfile.ZipFile(path).namelist()
    except Exception as e:                                    # noqa: BLE001
        return {'ok': False, 'pesan': f'Dokumen tidak bisa dibaca: {e}'}

    if 'word/document.xml' not in semua:
        return {'ok': False, 'pesan': 'Bukan dokumen Word (.docx).'}

    xml_lama = semua['word/document.xml'].decode('utf-8', 'ignore')
    xml_baru, info = rakit(xml_lama, teks_baru, bab_label, judul_bab)
    if not info.get('ok'):
        return info

    sehat, alasan = _cek_xml_sehat(xml_baru)
    if not sehat:
        log.error('[tulis_docx] XML cacat, dibatalkan: %s', alasan)
        return {'ok': False, 'pesan': f'Dibatalkan demi keamanan naskah: {alasan}'}

    # ── BACKUP (aturan Bos: jangan pernah kehilangan data mahasiswa) ──
    jejak_backup = ''
    try:
        tempat = Path(backup_dir) if backup_dir else path.parent / '_cadangan_docx'
        tempat.mkdir(parents=True, exist_ok=True)
        cap = datetime.now().strftime('%Y%m%d_%H%M%S')
        tujuan = tempat / f'{path.stem}-SEBELUM-AI-{cap}{path.suffix}'
        shutil.copy2(path, tujuan)
        jejak_backup = str(tujuan)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[tulis_docx] backup gagal (lanjut, tapi dicatat): %s', e)

    semua['word/document.xml'] = xml_baru.encode('utf-8')

    # ── TULIS ATOMIK ──
    sementara = path.parent / f'.{path.name}.tmp-{os.getpid()}'
    try:
        with zipfile.ZipFile(sementara, 'w', zipfile.ZIP_DEFLATED) as z:
            for n in urutan:
                if n in semua:
                    z.writestr(n, semua[n])
            for n in semua:
                if n not in urutan:                # bagian baru (kalau ada)
                    z.writestr(n, semua[n])
        os.replace(sementara, path)                # ← SATU operasi atomik
    except Exception as e:                                    # noqa: BLE001
        try:
            sementara.unlink(missing_ok=True)
        except Exception:                                     # noqa: BLE001
            pass
        return {'ok': False, 'pesan': f'Gagal menulis dokumen: {e}'}

    info['ukuran'] = path.stat().st_size
    info['cadangan'] = jejak_backup
    log.info('[tulis_docx] %s: %s paragraf → %s paragraf (%s byte)',
             path.name, info['paragraf_diganti'], info['paragraf_baru'],
             info['ukuran'])
    return info

# ══════════════════════════════════════════════════════════════════════════
#  PENEMPEL PRESISI (25Sep26) — GANTI HANYA PARAGRAF YANG TERBUKTI
# ══════════════════════════════════════════════════════════════════════════
#  🔴 MENGAPA ADA (bug nyata, terukur):
#     `rakit()` di atas mengganti paragraf `idx_awal..idx_akhir`. Untuk
#     `bab_label = BAB_SELURUH` itu berarti **0 sampai paragraf terakhir**.
#     Sementara prompt (G7a) memerintahkan AI mengirim HANYA potongan kecil.
#
#     Uji 2 arah atas naskah nyata (76.803 kar / 303 paragraf):
#         masukan potongan 356 kar → hasil 3 paragraf (356 kar)
#         📉 naskah SUSUT 99,5% (76.447 kar hilang)
#
#     Itu persis yang membunuh `file_id=47`. Mahasiswa selama ini selamat
#     HANYA karena pagar C9 kebetulan menolak "hasil kosong" — bukan karena
#     sistem tahu cara menempelkan.
#
#  ✅ OBATNYA: pakai `app/pipa.py` — kutipan AI dicocokkan ke paragraf naskah,
#     lalu diganti SATU PER SATU. Paragraf lain TIDAK DISENTUH.
#
#  ⚠️ DILARANG: memakai Jalur B untuk bab (label selain BAB_SELURUH) tanpa
#     memeriksa ulang — lihat `terapkan_editan_ke_berkas()` di bawah.
# ══════════════════════════════════════════════════════════════════════════


def _par_gambar_word(png: bytes, rid: str = '',
                     cx: int = 5_486_400, cy: int = 3_200_400,
                     idx: int = 1) -> str:
    """Paragraf Word berisi 1 gambar (PNG bytes) — dipakai rakit_presisi().

    🔴 MEMAKAI ULANG pola OOXML yang SUDAH TERBUKTI di app/gambar.py
       (`sisip_gambar_docx`). JANGAN menulis pola baru — sudah 3 bug
       ditutup di sana (Content_Types dobel, namespace, tag w:document).
    """
    if not png or not rid:
        return ''
    pid = 910_000 + int(idx)
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pid}" name="Grafik{idx}"/>'
        '<a:graphic><a:graphicData '
        'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic>'
        f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="grafik_{idx}.png"/>'
        '<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
        '<a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing></w:r></w:p>'
    )


def rakit_presisi(
    xml: str,
    editan: list,
    semua_paragraf: list[str],
    gambar_di: dict | None = None,
) -> tuple[str, dict]:
    """Ganti HANYA paragraf yang ditunjuk `editan` (hasil `app/pipa.py`).

    Kembalikan (xml_baru, info). TIDAK menyentuh berkas sama sekali.

    Alasan tidak menyentuh berkas: pola yang SAMA seperti `rakit()` —
    uji harus bisa dijalankan atas teks tanpa risiko.
    """
    par = peta_paragraf(xml)
    if not par:
        return '', {'ok': False,
                    'pesan': 'Dokumen ini tidak punya paragraf teks yang bisa '
                             'diganti.'}

    #  Peta paragraf `tulis_docx` (XML) vs paragraf pipa (TEKS). Keduanya
    #  dihitung dari sumber yang sama, tapi pipa memecah dengan `\n{2,}`
    #  atas TEKS, sementara `peta_paragraf` membaca `<w:p>` XML. Jumlahnya
    #  bisa berbeda (paragraf kosong, diagram, tabel). Karena itu pencocokan
    #  dilakukan lewat ISI TEKS, bukan lewat indeks — indeks pipa hanya
    #  pertanda; yang menentukan adalah teksnya.
    def normal(t: str) -> str:
        import re
        t = (t or '').lower()
        t = re.sub(r'[\u2018\u2019\u201c\u201d]', '"', t)
        t = re.sub(r'[\u2013\u2014\u2212]', '-', t)
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'[^\w\s\-.,;:()/%"]', '', t)
        return t.strip()

    #  Rentang ganti dikumpulkan dulu, lalu diterapkan DARI BELAKANG
    #  supaya posisi karakter tidak bergeser saat disisipkan.
    ganti_rencana: list[dict] = []
    tak_ketemu: list[int] = []
    gambar_dipasang = 0          # 🆕 26Sep26 — jumlah paragraf gambar dipasang

    for e in editan:
        k = normal(e.kutip)
        if not k:
            tak_ketemu.append(e.nomor)
            continue
        kena = None
        for i, p in enumerate(par):
            if k in normal(p['teks']):
                if kena is not None:            # lebih dari satu → TOLAK
                    kena = None
                    tak_ketemu.append(e.nomor)
                    break
                kena = i
        if kena is None:
            if e.nomor not in tak_ketemu:
                tak_ketemu.append(e.nomor)
            continue

        p_lama = par[kena]
        pPr = _pPr(xml[p_lama['awal']:p_lama['akhir']])
        rPr = _rPr_bersih(xml[p_lama['awal']:p_lama['akhir']])
        if not pPr and not rPr:
            #  Paragraf aneh (mis. tanpa format) — pakai paragraf isi terdekat
            for q in par:
                if _pPr(xml[q['awal']:q['akhir']]):
                    pPr = _pPr(xml[q['awal']:q['akhir']])
                    rPr = _rPr_bersih(xml[q['awal']:q['akhir']])
                    break

        #  GANTI-JADI bisa berisi BEBERAPA baris → beberapa paragraf Word.
        baris = [b for b in (e.ganti or '').split('\n')]
        while baris and not baris[-1].strip():
            baris.pop()
        if not baris:
            tak_ketemu.append(e.nomor)
            continue
        #  🆕 26Sep26 (arahan Bos): baris `[[GAMBAR-PNG-n]]` BUKAN teks —
        #     diganti paragraf GAMBAR Word, supaya urutannya tetap
        #     pembuka → GRAFIK → keterangan DI DALAM bagian yang diganti.
        _peta_gambar = gambar_di or {}
        _potong: list[str] = []
        for b in baris:
            _m = re.match(r'^\s*\[\[GAMBAR-PNG-(\d+)\]\]\s*$', b)
            if _m:
                _nomor_g = int(_m.group(1))
                _png_g = _peta_gambar.get(_nomor_g)
                _rid_g = _peta_gambar.get(f'_rid{_nomor_g}', '')
                _par_g = _par_gambar_word(_png_g, _rid_g, idx=_nomor_g) \
                    if _png_g else ''
                if _par_g:
                    _potong.append(_par_g)
                    gambar_dipasang += 1
                continue                       # penanda JANGAN jadi teks
            if b.strip():
                _potong.append(_par_baru(b.strip(), pPr, rPr))
        isi_baru = ''.join(_potong)
        if not isi_baru:
            tak_ketemu.append(e.nomor)
            continue

        ganti_rencana.append({
            'paragraf': kena, 'awal': p_lama['awal'],
            'akhir': p_lama['akhir'], 'isi': isi_baru,
            'nomor': e.nomor, 'teks_lama': p_lama['teks'][:80],
        })

    if not ganti_rencana:
        return '', {'ok': False,
                    'pesan': ('Tidak ada paragraf naskah yang cocok dengan '
                              'perubahan yang diminta. Naskah TIDAK diubah.'),
                    'tak_ketemu': tak_ketemu}

    #  Terapkan dari BELAKANG supaya offset karakter tetap sahih.
    xml_baru = xml
    for g in sorted(ganti_rencana, key=lambda d: d['awal'], reverse=True):
        xml_baru = _sisip(xml_baru, g['awal'], g['akhir'], g['isi'])

    return xml_baru, {
        'ok': True,
        'paragraf_diganti': len(ganti_rencana),
        'paragraf_baru': len(ganti_rencana),
        'karakter_baru': sum(len(g['isi']) for g in ganti_rencana),
        'bab': BAB_SELURUH,
        'presisi': True,
        'paragraf_gambar': gambar_dipasang,
        'tak_ketemu': tak_ketemu,
        'rincian': [{'K': g['nomor'], 'paragraf': g['paragraf'] + 1,
                     'teks_lama': g['teks_lama']} for g in ganti_rencana],
    }


def terapkan_editan_ke_berkas(
    path: Path,
    editan: list,
    semua_paragraf: list[str],
    backup_dir: Path | None = None,
    gambar_di: dict | None = None,
) -> dict:
    """Tulis hasil revisi PRESISI ke .docx — ATOMIK + BACKUP.

    Ini JALUR UTAMA untuk revisi berbasis catatan pembimbing (25Sep26).
    `terapkan_ke_berkas()` (jalur lama) tetap ada untuk penggantian per-bab.

    `gambar_di` (BARU 26Sep26, arahan Bos): {nomor: png_bytes}. Dipakai
    untuk menaruh GRAFIK TEPAT di antara paragraf pembuka & keterangan
    (bukan di akhir dokumen). `ai.py` menyisipkan baris penanda
    `[[GAMBAR-PNG-n]]` ke dalam teks ganti; fungsi ini menyiapkan
    media + relationships-nya, lalu `rakit_presisi()` mengubah penanda
    itu menjadi paragraf gambar Word.

    Urutan (SAMA seperti jalur lama — jangan diubah):
      1. baca isi .docx ke MEMORI
      2. rakit xml baru di MEMORI (presisi)
      3. PERIKSA xml sehat
      4. backup berkas asli
      5. tulis ke berkas SEMENTARA
      6. `os.replace()` → atomik
    """
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'pesan': 'Berkas dokumen tidak ditemukan di server.'}
    if not editan:
        return {'ok': False, 'pesan': 'Tidak ada perubahan yang bisa diterapkan.'}

    try:
        with zipfile.ZipFile(path) as z:
            semua = {n: z.read(n) for n in z.namelist()}
        urutan = zipfile.ZipFile(path).namelist()
    except Exception as e:                                    # noqa: BLE001
        return {'ok': False, 'pesan': f'Dokumen tidak bisa dibaca: {e}'}

    if 'word/document.xml' not in semua:
        return {'ok': False, 'pesan': 'Bukan dokumen Word (.docx).'}

    xml_lama = semua['word/document.xml'].decode('utf-8', 'ignore')

    #  ── SIAPKAN GAMBAR (media + rel) SEBELUM rakit ──
    #  🔴 26Sep26 (arahan Bos: "gambar bukan di akhir, tapi pembuka → grafik
    #     → keterangan"). Animo: gambar harus jadi paragraf DI DALAM bagian
    #     yang diganti. Karena itu media + relationship disiapkan di sini,
    #     lalu nomor rId-nya dipakai `_par_gambar_word()`.
    media_ditulis: dict[str, bytes] = {}
    if gambar_di:
        _nama_dasar = set(semua)
        #  ⚠️ WAJIB: namespace wp/a/pic harus TERDAFTAR di <w:document>.
        #     Naskah tanpa gambar tidak punya deklarasi itu → XML hasil jadi
        #     "unbound prefix" (terbukti terukur 26Sep26; pagar xml menolaknya).
        #     Baca deklarasi yang SUDAH ADA, tambahkan hanya yang KURANG
        #     (pelajaran dari app/gambar.py — jangan pakai doc.find('>')).
        _m_tag = re.search(r'<w:document(?:\s+[\w:.-]+\s*=\s*"[^"]*")*\s*/?>',
                           xml_lama)
        if _m_tag:
            _tag = _m_tag.group(0)
            _ada = dict(re.findall(r'xmlns:([\w.-]+)\s*=\s*"([^"]*)"', _tag))
            _tambah = []
            if 'wp' not in _ada:
                _tambah.append('xmlns:wp="http://schemas.openxmlformats.org/'
                               'drawingml/2006/wordprocessingDrawing"')
            if 'a' not in _ada:
                _tambah.append('xmlns:a="http://schemas.openxmlformats.org/'
                               'drawingml/2006/main"')
            if 'pic' not in _ada:
                _tambah.append('xmlns:pic="http://schemas.openxmlformats.org/'
                               'drawingml/2006/picture"')
            if 'r' not in _ada:
                _tambah.append('xmlns:r="http://schemas.openxmlformats.org/'
                               'officeDocument/2006/relationships"')
            if _tambah:
                _tag_baru = (_tag[:-1] + ' ' + ' '.join(_tambah)
                             + ('/>' if _tag.endswith('/>') else '>'))
                xml_lama = xml_lama.replace(_tag, _tag_baru, 1)
        _rels = semua.get('word/_rels/document.xml.rels', b'').decode(
            'utf-8', 'ignore')
        _dipakai = [int(m) for m in re.findall(r'Id="rId(\d+)"', _rels)]
        _rid_awal = max(_dipakai) + 1 if _dipakai else 1
        _tipe = semua.get('[Content_Types].xml', b'').decode('utf-8', 'ignore')
        for _i, _no in enumerate(sorted(k for k in gambar_di
                                        if isinstance(k, int))):
            _png = gambar_di.get(_no)
            if not _png:
                continue
            _nm = (f'word/media/grafik_ai{_no if _no > 1 else ""}.png')
            _r = _rid_awal + _i
            _rid = f'rId{_r}'
            _rels = _rels.replace(
                '</Relationships>',
                f'<Relationship Id="{_rid}" Type="http://schemas.'
                f'openxmlformats.org/officeDocument/2006/relationships/image"'
                f' Target="media/{_nm.split("/")[-1]}"/></Relationships>')
            media_ditulis[_nm] = _png
            gambar_di[f'_rid{_no}'] = _rid
        if media_ditulis:
            semua['word/_rels/document.xml.rels'] = _rels.encode('utf-8')
            if 'png' not in _tipe:
                _tipe = _tipe.replace(
                    '</Types>',
                    '<Default Extension="png" ContentType="image/png"/>'
                    '</Types>')
                semua['[Content_Types].xml'] = _tipe.encode('utf-8')
            for _nm, _png in media_ditulis.items():
                semua[_nm] = _png
                if _nm not in urutan:
                    urutan.append(_nm)

    xml_baru, info = rakit_presisi(xml_lama, editan, semua_paragraf, gambar_di)
    if not info.get('ok'):
        return info

    #  ── PAGAR BENCANA (dari app/pipa.py — SATU SUMBER) ──
    try:
        from .pipa import cukup_panjang
        teks_lama = '\n\n'.join(p['teks'] for p in peta_paragraf(xml_lama))
        teks_br = '\n\n'.join(p['teks'] for p in peta_paragraf(xml_baru))
        aman, alasan = cukup_panjang(teks_lama, teks_br)
        if not aman:
            log.error('[tulis_docx] PAGAR PANJANG menolak: %s', alasan)
            return {'ok': False, 'pesan': alasan}
    except ImportError:
        pass                                  # pipa belum ada (mode lama)

    sehat, alasan = _cek_xml_sehat(xml_baru)
    if not sehat:
        log.error('[tulis_docx] XML cacat, dibatalkan: %s', alasan)
        return {'ok': False, 'pesan': f'Dibatalkan demi keamanan naskah: {alasan}'}

    # ── BACKUP ──
    jejak_backup = ''
    try:
        tempat = Path(backup_dir) if backup_dir else path.parent / '_cadangan_docx'
        tempat.mkdir(parents=True, exist_ok=True)
        cap = datetime.now().strftime('%Y%m%d_%H%M%S')
        tujuan = tempat / f'{path.stem}-SEBELUM-AI-{cap}{path.suffix}'
        shutil.copy2(path, tujuan)
        jejak_backup = str(tujuan)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[tulis_docx] backup gagal (lanjut, tapi dicatat): %s', e)

    semua['word/document.xml'] = xml_baru.encode('utf-8')

    sementara = path.parent / f'.{path.name}.tmp-{os.getpid()}'
    try:
        with zipfile.ZipFile(sementara, 'w', zipfile.ZIP_DEFLATED) as z:
            for n in urutan:
                if n in semua:
                    z.writestr(n, semua[n])
            for n in semua:
                if n not in urutan:
                    z.writestr(n, semua[n])
        os.replace(sementara, path)
    except Exception as e:                                    # noqa: BLE001
        try:
            sementara.unlink(missing_ok=True)
        except Exception:                                     # noqa: BLE001
            pass
        return {'ok': False, 'pesan': f'Gagal menulis dokumen: {e}'}

    info['ukuran'] = path.stat().st_size
    info['cadangan'] = jejak_backup
    log.info('[tulis_docx] PRESISI %s: %s paragraf diganti (%s byte)',
             path.name, info['paragraf_diganti'], info['ukuran'])
    return info
