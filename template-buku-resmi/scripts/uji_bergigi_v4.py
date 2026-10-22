#!/usr/bin/env python3
"""UJI BERGIGI v4: buktikan gerbang menangkap kerusakan DAFTAR PUSTAKA.

Basis = buku contoh hasil generator (memuat daftar pustaka 4 entri).
  D1 indentasi gantung entri dibuang semua       -> DP3 wajib menangkap
  D2 bagian pustaka dipindah SESUDAH Tentang     -> DP1 wajib menangkap
     Penulis
Kontrol: buku contoh utuh WAJIB lulus.
"""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GERBANG = HERE / 'periksa_buku_template.py'
GENERATOR = HERE / 'buat_buku.py'
CONTOH = HERE / 'contoh_buku.json'
RE_PARA = re.compile(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', re.S)
RE_T = re.compile(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>')


def jalankan(p):
    r = subprocess.run([sys.executable, str(GERBANG), str(p)],
                       capture_output=True, text=True)
    gagal = [ln.strip() for ln in r.stdout.splitlines() if 'GAGAL' in ln]
    return r.returncode, gagal


def muat(sumber):
    with zipfile.ZipFile(sumber) as z:
        return {n: z.read(n) for n in z.namelist()}


def simpan(tujuan, isi):
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for nm, bb in isi.items():
            z.writestr(nm, bb)


def teks(p):
    return ''.join(RE_T.findall(p)).strip()


def pisah(doc):
    """Pecah document.xml jadi (kepala, [antar], [paragraf], ekor) —
    segmen antar-paragraf (mis. tabel) dipertahankan pada posisinya."""
    cocok = list(RE_PARA.finditer(doc))
    kepala = doc[:cocok[0].start()]
    ekor = doc[cocok[-1].end():]
    antar, paras = [], []
    for i, m in enumerate(cocok):
        paras.append(m.group(0))
        if i + 1 < len(cocok):
            antar.append(doc[m.end():cocok[i + 1].start()])
    return kepala, antar, paras, ekor


def gabung(kepala, antar, paras, ekor):
    out = [kepala]
    for i, p in enumerate(paras):
        out.append(p)
        if i < len(antar):
            out.append(antar[i])
    out.append(ekor)
    return ''.join(out)


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    contoh = td / 'buku-contoh.docx'
    r = subprocess.run([sys.executable, str(GENERATOR), str(CONTOH), str(contoh),
                        '--tanpa-gerbang'], capture_output=True, text=True)
    assert r.returncode == 0, f'generator gagal: {r.stderr[-300:]}'
    kode, _ = jalankan(contoh)
    print(f'KONTROL  buku contoh utuh -> EXIT {kode} (harus 0)')
    assert kode == 0

    LULUS = GAGAL = 0

    # D1: buang indentasi gantung semua entri
    isi = muat(contoh)
    doc = isi['word/document.xml'].decode('utf-8')
    n = doc.count('<w:ind w:left="720" w:hanging="720"/>')
    isi['word/document.xml'] = doc.replace(
        '<w:ind w:left="720" w:hanging="720"/>', '').encode('utf-8')
    t1 = td / 'D1.docx'
    simpan(t1, isi)
    kode, gagal = jalankan(t1)
    ketemu = kode == 1 and any('DP3' in g for g in gagal)
    print(f"  {'LULUS' if ketemu else 'GAGAL'}  D1 indentasi gantung dibuang ({n}x) -> {gagal[0][:80] if gagal else 'TIDAK tertangkap'}")
    LULUS, GAGAL = LULUS + ketemu, GAGAL + (not ketemu)

    # D2: pindahkan blok pustaka ke sesudah judul Tentang Penulis
    isi = muat(contoh)
    doc = isi['word/document.xml'].decode('utf-8')
    kepala, antar, paras, ekor = pisah(doc)
    i_dp = next(i for i, p in enumerate(paras) if teks(p) == 'DAFTAR PUSTAKA')
    i_pen = next(i for i, p in enumerate(paras)
                 if teks(p).upper().startswith('TENTANG PENULIS'))
    assert i_dp < i_pen
    blok = paras[i_dp:i_pen]
    sisa = paras[:i_dp] + paras[i_pen:]
    # posisi Tentang Penulis di daftar sisa
    j_pen = next(i for i, p in enumerate(sisa)
                 if teks(p).upper().startswith('TENTANG PENULIS'))
    paras_baru = sisa[:j_pen + 1] + blok + sisa[j_pen + 1:]
    # antar diselaraskan kasar: pakai antar asli sejauh muat, sisanya ''
    antar_baru = (antar + [''] * len(paras_baru))[:len(paras_baru) - 1]
    # PENTING: blok yang dipindah TIDAK boleh membawa/meninggalkan segmen
    # tabel — pustaka contoh tidak berisi tabel, aman untuk operasi ini.
    isi['word/document.xml'] = gabung(kepala, antar_baru, paras_baru, ekor).encode('utf-8')
    t2 = td / 'D2.docx'
    simpan(t2, isi)
    kode, gagal = jalankan(t2)
    ketemu = kode == 1 and any('DP1' in g for g in gagal)
    print(f"  {'LULUS' if ketemu else 'GAGAL'}  D2 pustaka dipindah sesudah Tentang Penulis -> {gagal[0][:80] if gagal else 'TIDAK tertangkap'}")
    LULUS, GAGAL = LULUS + ketemu, GAGAL + (not ketemu)

print('\n' + '=' * 66)
print(f'RINGKAS UJI BERGIGI v4: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
