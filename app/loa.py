"""Mesin Letter of Acceptance (LoA) JEMT — EduAi.

PUTUSAN BOS 16 Okt 2026 (lihat PUTUSAN_FITUR_LOA_16OKT2026.md):
  · LoA DICETAK EduAi (OJS tidak punya fitur LoA — terbukti dari sumber OJS)
  · Nomor LoA = <volume>.<nomor_artikel>, contoh 1.001
  · Nomor artikel NAIK TERUS; VOLUME naik hanya kalau diubah manual
  · Volume + Nomor terbitan (isi surat) DIAMBIL DARI TRIDARMA
  · Tridarma kosong ⇒ **LoA TIDAK TERBIT** (putusan opsi B)
  · NOL mesin baru: pakai weasyprint + qrcode yang SUDAH ADA

Pola simpan setelan meniru `app/kunci_layanan.py` (berkas JSON di `data/`,
bind-mount ⇒ tahan restart). Bukan tabel baru, bukan mekanisme baru.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

DIR_TEMPLATE = Path(__file__).parent / 'templates' / 'loa'
DIR_DATA = Path(os.getenv('EDUAI_DATA_DIR') or '/app/data')
BERKAS_SETELAN = DIR_DATA / 'setelan-loa.json'

TEMPLATE_JEMT = DIR_TEMPLATE / 'loa-jemt.html'

ROMAWI = ['', 'I', 'II', 'III', 'IV', 'V', 'VI',
          'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

#  ── Setelan bawaan LoA (boleh diubah dari halaman pengaturan) ────────────
SETELAN_BAWAAN = {
    'volume': 1,               # dinaikkan HANYA manual oleh admin
    'nomor_artikel': 0,        # naik otomatis tiap LoA terbit
    'editor_name': 'Chief Editor JEMT',
    'issue_place': 'Bekasi',
    'contact_email': 'admin@tridarma.id',
    'contact_wa': '0851-7813-8514',
}

TOKEN = re.compile(r'\{\{([a-z_]+)\}\}')


# ══════════════════════════════════════════════════════════════════════════
#  SETELAN — pola sama dengan `kunci_layanan.py` (berkas JSON di data/)
# ══════════════════════════════════════════════════════════════════════════
def _muat() -> dict:
    hasil = dict(SETELAN_BAWAAN)
    try:
        if BERKAS_SETELAN.exists():
            isi = json.loads(BERKAS_SETELAN.read_text(encoding='utf-8'))
            if isinstance(isi, dict):
                hasil.update({k: v for k, v in isi.items()
                              if k in SETELAN_BAWAAN})
    except Exception:
        pass
    return hasil


def _simpan(isi: dict) -> None:
    BERKAS_SETELAN.parent.mkdir(parents=True, exist_ok=True)
    BERKAS_SETELAN.write_text(json.dumps(isi, indent=1, ensure_ascii=False),
                              encoding='utf-8')


def setelan() -> dict:
    """Baca setelan LoA (volume, nomor terakhir, editor, kontak)."""
    return _muat()


def simpan_setelan(baru: dict) -> dict:
    """Simpan setelan LoA; hanya kunci yang dikenal yang diterima."""
    kini = _muat()
    for k, v in (baru or {}).items():
        if k in SETELAN_BAWAAN and v not in (None, ''):
            kini[k] = v
    _simpan(kini)
    return kini


# ══════════════════════════════════════════════════════════════════════════
#  NOMOR LoA — <volume>.<nomor_artikel>
# ══════════════════════════════════════════════════════════════════════════
def nomor_berikut(s: dict = None) -> str:
    """Nomor LoA berikutnya tanpa menaikkan (untuk ditampilkan)."""
    s = s or _muat()
    vol = int(s.get('volume') or 1)
    no = int(s.get('nomor_artikel') or 0) + 1
    return f'{vol}.{no:03d}'


def ambil_nomor() -> str:
    """Ambil nomor LoA berikutnya SEKALI PAKAI + simpan kenaikannya."""
    s = _muat()
    nomor = nomor_berikut(s)
    s['nomor_artikel'] = int(s.get('nomor_artikel') or 0) + 1
    _simpan(s)
    return nomor


def nomor_surat(nomor: str, tanggal: datetime = None) -> str:
    """Nomor lengkap untuk surat: 1.001/LOA/JEMT/X/2026."""
    from datetime import date
    t = tanggal or date.today()
    bulan = ROMAWI[t.month] if 1 <= t.month <= 12 else 'I'
    return f'{nomor}/LOA/JEMT/{bulan}/{t.year}'


# ══════════════════════════════════════════════════════════════════════════
#  SYARAT TERBIT — putusan Bos: Tridarma kosong ⇒ TIDAK terbit
# ══════════════════════════════════════════════════════════════════════════
DITERIMA = ('diterima', 'terbit', 'published', 'accepted')


def periksa_syarat(status: dict) -> dict:
    """Boleh terbit LoA? Butuh: status DITERIMA + Volume & Nomor dari Tridarma."""
    status = status or {}
    if not status.get('ok'):
        return {'boleh': False, 'basis': 'status',
                'sebab': 'Status artikel belum bisa dibaca dari Tridarma.'}

    tahap = str(status.get('status') or '').strip().lower()
    if tahap not in DITERIMA:
        return {'boleh': False, 'basis': 'status',
                'sebab': f'Artikel belum dinyatakan diterima '
                         f'(status: {status.get("status") or "tidak diketahui"}).'}

    vol = str(status.get('volume') or '').strip()
    no = str(status.get('nomor') or '').strip()
    if not vol or not no:
        return {'boleh': False, 'basis': 'terbitan',
                'sebab': 'Tridarma belum menetapkan Volume/Nomor terbitan '
                         'untuk artikel ini. LoA akan terbit setelah jurnal '
                         'menerbitkannya.'}

    return {'boleh': True, 'basis': '', 'sebab': '',
            'volume': vol, 'nomor': no}


# ══════════════════════════════════════════════════════════════════════════
#  ISI TEMPLATE
# ══════════════════════════════════════════════════════════════════════════
def isi_template(data: dict, template: Path = None) -> str:
    """Ganti semua {{token}}. Ada yang kosong ⇒ BERHENTI (jangan LoA cacat)."""
    tpl = (template or TEMPLATE_JEMT).read_text(encoding='utf-8')

    def ganti(m):
        k = m.group(1)
        return str(data.get(k, m.group(0)))

    hasil = TOKEN.sub(ganti, tpl)
    sisa = sorted(set(TOKEN.findall(hasil)))
    if sisa:
        raise ValueError('Token belum diisi: ' +
                         ', '.join('{{' + s + '}}' for s in sisa))
    return hasil


def susun_data(status: dict, artikel: dict, s: dict, nomor: str,
               url_verifikasi: str = '') -> dict:
    """Rakit 14 isian LoA: status Tridarma + data artikel + setelan EduAi."""
    s = s or _muat()
    artikel = artikel or {}
    kini = datetime.now()
    return {
        'loa_number': nomor_surat(nomor, kini),
        'article_title': artikel.get('judul') or status.get('judul') or '',
        'authors': artikel.get('penulis') or status.get('authors') or '',
        'affiliation': artikel.get('afiliasi') or status.get('affiliation') or '',
        'submission_id': str(status.get('submission_id') or
                             artikel.get('id_ojs') or ''),
        'acceptance_date': status.get('tanggal_diterima') or '',
        'volume': str(status.get('volume') or ''),
        'issue': str(status.get('nomor') or ''),
        'publication_date': status.get('tanggal_terbit') or '',
        'editor_name': s.get('editor_name') or '',
        'issue_place': s.get('issue_place') or '',
        'issue_date': _tanggal_indo(kini),
        'contact_email': s.get('contact_email') or '',
        'contact_wa': s.get('contact_wa') or '',
        'verify_url': url_verifikasi,
    }


BULAN_ID = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
            'Agustus', 'September', 'Oktober', 'November', 'Desember']


def _tanggal_indo(t: datetime) -> str:
    return f'{t.day} {BULAN_ID[t.month]} {t.year}'


# ══════════════════════════════════════════════════════════════════════════
#  QR + PDF
# ══════════════════════════════════════════════════════════════════════════
def bikin_qr(tautan: str, keluar: Path) -> Path:
    """QR verifikasi (pakai `qrcode` yang sudah ada di requirements)."""
    import qrcode
    qr = qrcode.QRCode(box_size=8, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(tautan)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#16263D', back_color='white')
    keluar.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(keluar))
    return keluar


def cetak_pdf(html: str, keluar: Path) -> Path:
    """Cetak HTML LoA → PDF (weasyprint = mesin yang sudah dipakai app)."""
    from weasyprint import HTML
    keluar.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(DIR_TEMPLATE)).write_pdf(str(keluar))
    return keluar


# ══════════════════════════════════════════════════════════════════════════
#  DAFTAR LoA TERBIT + VERIFIKASI  (halaman qr.tridarma.id)
# ══════════════════════════════════════════════════════════════════════════
BERKAS_TERBIT = DIR_DATA / 'loa-terbit.json'


def _muat_terbit() -> dict:
    """Baca daftar LoA yang sudah terbit (kunci = nomor LoA pendek, mis. '1.001')."""
    try:
        if BERKAS_TERBIT.exists():
            isi = json.loads(BERKAS_TERBIT.read_text(encoding='utf-8'))
            if isinstance(isi, dict):
                return isi
    except Exception:
        pass
    return {}


def catat_terbit(nomor: str, data: dict) -> None:
    """Simpan LoA yang baru dicetak supaya bisa diverifikasi publik."""
    isi = _muat_terbit()
    isi[str(nomor)] = {
        'nomor': str(nomor),
        'nomor_surat': data.get('loa_number') or '',
        'judul': data.get('article_title') or '',
        'penulis': data.get('authors') or '',
        'afiliasi': data.get('affiliation') or '',
        'id_ojs': data.get('submission_id') or '',
        'tanggal_diterima': data.get('acceptance_date') or '',
        'terbit': _ringkas_terbit(data),
        'editor': data.get('editor_name') or '',
        'diterbitkan_pada': datetime.now().strftime('%d %B %Y').replace(
            'January', 'Januari').replace('February', 'Februari').replace(
            'March', 'Maret').replace('May', 'Mei').replace('June', 'Juni').replace(
            'July', 'Juli').replace('August', 'Agustus').replace(
            'October', 'Oktober').replace('December', 'Desember'),
    }
    BERKAS_TERBIT.parent.mkdir(parents=True, exist_ok=True)
    BERKAS_TERBIT.write_text(json.dumps(isi, indent=1, ensure_ascii=False),
                             encoding='utf-8')


def _ringkas_terbit(data: dict) -> str:
    vol = str(data.get('volume') or '').strip()
    no = str(data.get('issue') or '').strip()
    tgl = str(data.get('publication_date') or '').strip()
    bagian = [b for b in (f'Volume {vol}' if vol else '',
                          f'Nomor {no}' if no else '') if b]
    inti = ', '.join(bagian)
    return f'{inti} — {tgl}' if (inti and tgl) else (inti or tgl)


def cek_nomor(nomor: str) -> dict:
    """Cari LoA berdasarkan nomor (terima '1.001' atau nomor surat lengkap)."""
    n = (nomor or '').strip()
    if not n:
        return {}
    isi = _muat_terbit()
    if n in isi:
        return isi[n]
    # cocokkan juga kalau user mengetik nomor surat lengkap (1.001/LOA/JEMT/X/2026)
    for _, d in isi.items():
        if d.get('nomor_surat') and d['nomor_surat'].lower() == n.lower():
            return d
    return {}


def terbitkan(status: dict, artikel: dict, keluar: Path) -> dict:
    """TERBITKAN LoA: cek syarat -> ambil nomor -> isi template -> QR -> PDF.

    Mengembalikan {ok, nomor, nomor_surat, pdf, sebab}.
    Nomor HANYA naik kalau LoA benar-benar berhasil dicetak.
    """
    cek = periksa_syarat(status)
    if not cek.get('boleh'):
        return {'ok': False, 'sebab': cek.get('sebab') or 'Syarat belum terpenuhi.'}

    nomor = ambil_nomor()
    url = f'https://qr.tridarma.id/verifikasi-loa?no={nomor}'
    data = susun_data(status, artikel, setelan(), nomor, url)

    try:
        html = isi_template(data)
    except ValueError as e:
        return {'ok': False, 'sebab': f'Template LoA belum lengkap: {e}'}

    # QR ditulis SEJAJAR template (WeasyPrint mencari aset di DIR_TEMPLATE)
    bikin_qr(url, DIR_TEMPLATE / 'qr-verifikasi.png')
    cetak_pdf(html, keluar)

    # catat supaya bisa diverifikasi publik
    catat_terbit(nomor, data)
    return {'ok': True, 'nomor': nomor, 'nomor_surat': data['loa_number'],
            'pdf': str(keluar), 'url': url}


def unduh_untuk_user(status: dict, artikel: dict, folder: Path) -> dict:
    """Bungkus `terbitkan` untuk rute web: simpan PDF di folder data user."""
    folder = Path(folder)
    nomor_kira = nomor_berikut()
    keluar = folder / f'LoA-{nomor_kira.replace(".", "-")}.pdf'
    folder.mkdir(parents=True, exist_ok=True)
    return terbitkan(status, artikel, keluar)
