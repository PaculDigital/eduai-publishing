#!/usr/bin/env python3
"""Unduh contoh dokumen NYATA (PDF dari repository kampus) lalu ubah ke DOCX.

KENAPA: EduAi memproses DOCX. Repositori kampus menyediakan PDF. Skrip ini
mengunduh yang NYATA (bukan karangan), mencatat sumbernya, lalu mengubahnya
ke DOCX memakai PyMuPDF + python-docx (venv VPS — container produksi TIDAK
ditambah dependensi).

Cara pakai:
    /opt/data/.venv/bin/python3 ambil_contoh_pdf.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parent
CONTOH = AKAR / '_arsip' / 'contoh-dokumen'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/121.0 Safari/537.36')

# Contoh NYATA dari repositori kampus TERBUKA (bukan karangan).
# Diverifikasi saat unduh: harus PDF sungguhan & punya teks (bukan scan).
#
# 🎯 ACC Bos 16Sep26: "lanjut training hadapi dokumen berbagai bidang studi".
# Jadi kandidat sengaja DISEBAR ke banyak rumpun ilmu + jenjang, karena tata
# tulis tiap bidang BEDA (Kedokteran pakai tabel statistik, Sastra tidak pakai
# hipotesis, Teknik pakai diagram, Pendidikan pakai instrumen, dll).
BIDANG = [
    'kedokteran/kesehatan', 'sastra/budaya', 'pendidikan', 'teknik',
    'ekonomi/bisnis', 'ilmu-sosial', 'pertanian', 'hukum',
]

KANDIDAT: list[dict] = [
    # ── KESEHATAN / KEDOKTERAN (sudah ada) ──
    {
        'jenis': 'skripsi-s1',
        'nama': 'SKRIPSI-S1-unhas-olahraga-menstruasi.docx',
        'url': ('https://repository.unhas.ac.id/id/eprint/16228/2/'
                'C011181512_skripsi_bab%201-2.pdf'),
        'sumber': ('Repository Universitas Hasanuddin — skripsi S1 Kedokteran, '
                   'bab 1-2, penulis: Annisa Al-maghfirah (2022)'),
        'bidang': 'kedokteran/kesehatan',
        'bab_min': 2,
    },
    # ── SASTRA / BUDAYA (sudah ada) ──
    {
        'jenis': 'tesis-s2',
        'nama': 'TESIS-S2-unhas-sastra-novel.docx',
        'url': ('https://repository.unhas.ac.id/id/eprint/24260/2/'
                'F032201007_tesis_15-09-2022%201-2.pdf'),
        'sumber': ('Repository Universitas Hasanuddin — tesis S2 Sastra, '
                   'bab 1-2, penulis: Risya Rizky Nurul Qurani (2022)'),
        'bidang': 'sastra/budaya',
        'bab_min': 2,
    },
    # ── PENDIDIKAN (baru) ──
    {
        'jenis': 'tesis-s2',
        'nama': 'TESIS-S2-unhas-pendidikan-bahasa.docx',
        'url': ('https://repository.unhas.ac.id/24250/2/'
                'F032191005_tesis_15-09-2022%201-2.pdf'),
        'sumber': ('Repository Universitas Hasanuddin — tesis S2 Pendidikan '
                   'Bahasa (psikolinguistik), bab 1-2, NIM F032191005 (2022)'),
        'bidang': 'pendidikan',
        'bab_min': 2,
    },
    # ── EKONOMI / BISNIS (baru) ──
    {
        'jenis': 'tesis-s2',
        'nama': 'TESIS-S2-unhas-manajemen-digital-marketing.docx',
        'url': ('https://repository.unhas.ac.id/27022/2/'
                'A012211003_tesis_07-06-2023%201-2.pdf'),
        'sumber': ('Repository Universitas Hasanuddin — tesis S2 Magister '
                   'Manajemen, penulis: Silvia Idris (2023) — memakai pola '
                   'daftar isi bertitik-titik + judul bab bergaya "BAB 1."'),
        'bidang': 'ekonomi/bisnis',
        'bab_min': 2,
    },
    # ── DISERTASI S3 (baru) ──
    {
        'jenis': 'disertasi-s3',
        'nama': 'DISERTASI-S3-unhas-kesehatan-stunting.docx',
        'url': ('https://repository.unhas.ac.id/855/4/'
                'P1000316303_disertasi_12-11-2020%28FILEminimizer%29.pdf'),
        'sumber': ('Repository Universitas Hasanuddin — disertasi S3 Ilmu '
                   'Kesehatan Masyarakat, "Variasi Spasial dan Determinan '
                   'Stunting pada Balita di Indonesia" (2020)'),
        'bidang': 'kedokteran/kesehatan',
        'bab_min': 2,
    },
]


def _unduh(url: str, tujuan: Path, batas_mb: int = 30) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read(batas_mb * 1024 * 1024 + 1)
            if len(data) > batas_mb * 1024 * 1024:
                return False, f'terlalu besar (>{batas_mb} MB)'
            if not data:
                return False, 'kosong'
            tujuan.write_bytes(data)
            return True, f'{len(data):,} byte'
    except urllib.error.HTTPError as e:
        return False, f'HTTP {e.code}'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def pdf_ke_docx(pdf: Path, docx: Path) -> tuple[bool, str]:
    """Ubah PDF → DOCX. HANYA PDF bertekstur (teks asli), bukan hasil scan."""
    import fitz                                  # PyMuPDF
    from docx import Document

    doc = fitz.open(str(pdf))
    halaman = doc.page_count
    teks_kotor = '\n'.join(p.get_text() for p in doc)
    doc.close()

    # Bersihkan: buang nomor halaman berdiri sendiri & rapikan spasi
    baris = []
    for b in teks_kotor.split('\n'):
        t = b.strip()
        if re.fullmatch(r'\d{1,3}', t):          # nomor halaman
            continue
        if not t:
            continue
        baris.append(t)
    teks = '\n'.join(baris)

    if len(teks) < 500:
        return False, f'hanya {len(teks)} kar — kemungkinan PDF hasil SCAN'

    d = Document()
    for b in teks.split('\n'):
        d.add_paragraph(b)
    d.save(str(docx))
    return True, f'{halaman} hal · {len(teks):,} kar teks'


def main() -> int:
    CONTOH.mkdir(parents=True, exist_ok=True)
    hasil = []
    for k in KANDIDAT:
        folder = CONTOH / k['jenis']
        folder.mkdir(parents=True, exist_ok=True)
        tujuan = folder / k['nama']
        pdf_sementara = Path('/tmp') / (k['nama'] + '.pdf')

        print(f"[{k['jenis']}] {k['nama']}")
        print(f"   sumber : {k['sumber']}")
        ok, ket = _unduh(k['url'], pdf_sementara)
        print(f"   unduh  : {'BERHASIL' if ok else 'GAGAL'} — {ket}")
        if not ok:
            hasil.append({**k, 'status': 'gagal_unduh', 'ket': ket})
            print()
            continue

        if pdf_sementara.read_bytes()[:4] != b'%PDF':
            print('   ⚠️  bukan PDF sungguhan → TOLAK')
            hasil.append({**k, 'status': 'bukan_pdf'})
            print()
            continue

        try:
            ok2, ket2 = pdf_ke_docx(pdf_sementara, tujuan)
        except Exception as e:
            ok2, ket2 = False, f'{type(e).__name__}: {e}'
        print(f"   docx   : {'OK' if ok2 else 'GAGAL'} — {ket2}")
        if ok2:
            sha = hashlib.sha256(tujuan.read_bytes()).hexdigest()[:16]
            print(f"   sha256 : {sha}")
        hasil.append({**k, 'status': 'ok' if ok2 else 'gagal_konversi', 'ket': ket2})
        pdf_sementara.unlink(missing_ok=True)
        print()
        time.sleep(1.5)

    catatan = CONTOH / 'SUMBER.json'
    lama = json.loads(catatan.read_text('utf-8')) if catatan.exists() else []
    catatan.write_text(json.dumps(lama + hasil, ensure_ascii=False, indent=2),
                       encoding='utf-8')
    print(f'Catatan sumber → {catatan}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
