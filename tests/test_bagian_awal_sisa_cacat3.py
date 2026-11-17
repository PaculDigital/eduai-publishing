#!/usr/bin/env python3
"""Uji putaran 3 sisa cacat uji live Bagian Awal di skripsi fid 81
(17 Nov 2026).

Sesudah deploy perbaikan putaran 2 (main a6598bb), uji live ulang
19:11-19:31 WIB membuktikan lima perbaikan LOLOS, TAPI satu GAGAL:
kolom Program Studi dan Fakultas di form MASIH KOSONG (hanya
placeholder), dan halaman Judul (hal. 2) serta Lembar Persetujuan
(hal. 4) MASIH menampilkan 'Program Studi :' dan 'Fakultas :' kosong,
padahal verifikasi offline putaran 2 mengklaim perbaikan ini jalan.

Akar (dibuktikan ulang pada salinan SEGAR docx live + rencana/data
tersimpan dari DB live, 17 Nov 19:15 WIB):
  Rencana dihitung dari data form MENTAH (prodi/fakultas kosong =
  data lama kosong, jadi 'tidak berubah'), lalu halaman Judul
  (di dalam XML sampul, tidak ada seksi 'judul' sendiri di baca) dan
  Persetujuan DIPERTAHANKAN kata per kata dari XML asli. Isian efektif
  dari naskah (prodi_fakultas_efektif_form) hanya mengalir ke
  susun_bagian, yaitu halaman yang DIBUAT ULANG, dan tidak pernah
  menyentuh XML yang dipertahankan maupun data form yang tersimpan.
  Tes putaran 2 hanya menegaskan susun_bagian (jalur dibuat ulang),
  bukan jalur dipertahankan, jadi lolos offline tapi gagal live.

Perbaikan (tiga lapis):
  1. _bangun_bagian_baru: baris label kosong ('Program Studi :',
     'Fakultas :') di XML halaman form yang dipertahankan diisi dari
     data efektif; hanya baris kosong yang diisi, baris berisi tidak
     disentuh (cermin sisipan nama di abstract).
  2. Halaman GET: data form ditampilkan sesudah isian efektif
     (judul sampul + prodi/fakultas dari naskah).
  3. Konfirmasi: isian efektif diterapkan SEBELUM simpan + rencana,
     supaya rencana melihat perubahan data dan nilai tersimpan.

Data uji = data ASLI fid 81 (segar):
  tests/fixtures/bagian_awal_sisa_cacat3/
    paragraf_fid81_segar.json   5136 paragraf docx live 17 Nov 19:15 WIB
    spans_depan_fid81_segar.json XML paragraf 0..308 (wilayah depan)
    setelan_fid81.json          data + rencana + hasil tersimpan (DB live)
  Peta dipakai ulang dari tests/fixtures/bagian_awal_sisa_cacat2/.

Jalankan `python3 tests/test_bagian_awal_sisa_cacat3.py`, keluar 0 bila
semua lulus. TIDAK ada panggilan AI dan TIDAK ada panggilan jaringan.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_sisa_cacat3_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import bagian_awal as BA  # noqa: E402
from app.rute_bagian_awal import _bangun_bagian_baru  # noqa: E402
from app.rute_bagian_awal import _xml_spans  # noqa: E402

FIX = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat3'
FIX2 = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat2'
PARAGRAF = json.loads(
    (FIX / 'paragraf_fid81_segar.json').read_text())
SPANS_DEPAN = json.loads(
    (FIX / 'spans_depan_fid81_segar.json').read_text())
SETELAN = json.loads((FIX / 'setelan_fid81.json').read_text())
PETA = json.loads((FIX2 / 'peta_fid81.json').read_text())
IDX_BAB1 = SETELAN['idx_bab1']
DATA_TERSIMPAN = SETELAN['data']
RENCANA_TERSIMPAN = SETELAN['rencana']
HASIL_TERSIMPAN = SETELAN['hasil']

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def _spans_penuh():
    """[(teks, xml)] selaras PARAGRAF; badan diisi ('', '') (tak dipakai
    jalur dipertahankan; gaya badan jadi '' dan aman)."""
    depan = [(PARAGRAF[i], SPANS_DEPAN[i]) for i in range(IDX_BAB1)]
    return depan + [('', '')] * (len(PARAGRAF) - IDX_BAB1)


def _teks_xml_list(xml_list):
    return [BA._teks_dari_xml(x) for x in (xml_list or [])]


def jalankan():
    # ── 0. Fixture segar ──────────────────────────────────────────
    cek('fixture segar: 5136 paragraf, Bab I di indeks 309',
        len(PARAGRAF) == 5136 and IDX_BAB1 == 309,
        f'{len(PARAGRAF)} / {IDX_BAB1}')
    cek('fixture segar: data tersimpan prodi/fakultas kosong (gejala live)',
        DATA_TERSIMPAN.get('prodi') == ''
        and DATA_TERSIMPAN.get('fakultas') == '',
        str(DATA_TERSIMPAN.get('prodi')) + '/'
        + str(DATA_TERSIMPAN.get('fakultas')))

    # ── 1. Ekstraksi pada docx segar jalan (bukan fixture basi) ───
    cek('prodi: dari dokumen segar = Manajemen / Ekonomi dan Bisnis',
        BA.prodi_fakultas_dari_dokumen(PARAGRAF)
        == {'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis'})
    cek('prodi: form kosong diisi, form terisi menang',
        BA.prodi_fakultas_efektif_form(
            {'prodi': '', 'fakultas': ''}, PARAGRAF)
        == {'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis'}
        and BA.prodi_fakultas_efektif_form(
            {'prodi': 'Akuntansi', 'fakultas': 'Ekonomi'}, PARAGRAF)
        == {'prodi': 'Akuntansi', 'fakultas': 'Ekonomi'})
    cek('judul: sampul mengisi form kosong, form terisi menang',
        BA.judul_efektif_form({'judul': ''}, PARAGRAF)['judul']
        .startswith('PENGARUH DIGITAL MARKETING')
        and BA.judul_efektif_form({'judul': 'Judul Lain'}, PARAGRAF)
        ['judul'] == 'Judul Lain')

    baca = BA.baca_bagian_awal(PARAGRAF)
    cek('baca segar: tidak ada seksi judul sendiri (Judul di XML sampul)',
        'judul' not in (baca.get('bagian', {}) or {})
        and 'sampul' in (baca.get('bagian', {}) or {}))
    cek('baca segar: sampul berisi baris Judul kosong',
        'Program Studi :' in (baca.get('bagian', {}).get('sampul') or [])
        and 'Fakultas :' in (baca.get('bagian', {}).get('sampul') or []))
    cek('baca segar: persetujuan berisi baris Prodi kosong',
        'Program Studi :' in
        (baca.get('bagian', {}).get('persetujuan') or []))
    cek('baca segar: pernyataan memang kosong (bukan cacat)',
        (baca.get('bagian', {}).get('pernyataan') or []) == ['', ''])

    # ── 2. Akar: rencana dari data mentah = jebakan ──────────────
    rencana_mentah = BA.rencana_update(
        DATA_TERSIMPAN, HASIL_TERSIMPAN.get('data') or {}, baca,
        HASIL_TERSIMPAN.get('sidik') or {},
        HASIL_TERSIMPAN.get('tahap') or 'final')

    def _nasib(r):
        return {k: sorted(d['kunci'] for d in r.get(k, []))
                for k in ('berubah', 'dipertahankan', 'dibuat_ulang',
                          'kembalikan')}
    cek('akar: rencana dari data mentah sama dengan rencana tersimpan',
        _nasib(rencana_mentah) == _nasib(RENCANA_TERSIMPAN),
        str(_nasib(rencana_mentah)))
    cek('akar: rencana mentah tidak mengubah apa pun (berubah kosong)',
        rencana_mentah.get('berubah') == [])
    cek('akar: judul + persetujuan dipertahankan di rencana mentah',
        'judul' in _nasib(rencana_mentah)['dipertahankan']
        and 'persetujuan' in _nasib(rencana_mentah)['dipertahankan'])

    # ── 3. Perbaikan inti: jalur dipertahankan terisi ────────────
    spans = _spans_penuh()
    bagian = _bangun_bagian_baru(
        RENCANA_TERSIMPAN, baca, spans, DATA_TERSIMPAN, 'final', PETA,
        PARAGRAF, None, None)
    peta_bagian = {b['kunci']: b for b in bagian}
    cek('bangun: judul tidak ada sebagai item (di dalam XML sampul)',
        'judul' not in peta_bagian)
    sampul_xml = _teks_xml_list(peta_bagian['sampul'].get('xml'))
    persetujuan_xml = _teks_xml_list(
        peta_bagian['persetujuan'].get('xml'))
    cek('bangun: sampul dipertahankan sebagai XML (bukan susun)',
        bool(peta_bagian['sampul'].get('xml')))
    cek('bangun: persetujuan dipertahankan sebagai XML (bukan susun)',
        bool(peta_bagian['persetujuan'].get('xml')))
    cek('bangun: sampul XML terisi Program Studi : Manajemen',
        'Program Studi : Manajemen' in sampul_xml, str(sampul_xml))
    cek('bangun: sampul XML terisi Fakultas : Ekonomi dan Bisnis',
        'Fakultas : Ekonomi dan Bisnis' in sampul_xml, str(sampul_xml))
    cek('bangun: persetujuan XML terisi Program Studi : Manajemen',
        'Program Studi : Manajemen' in persetujuan_xml,
        str(persetujuan_xml))
    cek('bangun: tidak ada lagi baris label kosong di sampul/persetujuan',
        'Program Studi :' not in sampul_xml
        and 'Fakultas :' not in sampul_xml
        and 'Program Studi :' not in persetujuan_xml)
    cek('bangun: baris sampul lain utuh (hanya 2 baris berubah)',
        [s for s in sampul_xml] == [
            s if s not in ('Program Studi :', 'Fakultas :') else
            ('Program Studi : Manajemen' if s == 'Program Studi :'
             else 'Fakultas : Ekonomi dan Bisnis')
            for s in (baca.get('bagian', {}).get('sampul') or [])])
    cek('bangun: pernyataan tidak disentuh (tetap kosong, tanpa Prodi)',
        [t.strip() for t in _teks_xml_list(
            peta_bagian['pernyataan'].get('xml')) if t.strip()]
        == ['PERNYATAAN KEASLIAN SKRIPSI']
        and not any('Program Studi' in t or 'Fakultas' in t
                    for t in _teks_xml_list(
                        peta_bagian['pernyataan'].get('xml'))),
        str(_teks_xml_list(peta_bagian['pernyataan'].get('xml'))))

    # ── 4. Ujung-ke-ujung: tulis ke salinan docx ─────────────────
    from docx import Document as _Docx
    docx_jalan = Path(TMP) / 'fid81_jalan.docx'
    d = _Docx()
    for teks in PARAGRAF[:IDX_BAB1]:
        d.add_paragraph(teks)
    d.add_paragraph('BAB I')
    d.add_paragraph('PENDAHULUAN')
    d.add_paragraph('Isi badan tetap utuh.')
    d.save(str(docx_jalan))
    tulis = BA.tulis_bagian_awal(docx_jalan, bagian)
    cek('tulis: ok', bool(tulis.get('ok')), str(tulis.get('sebab')))
    spans_baru = _xml_spans(docx_jalan)
    par_baru = [t for t, _ in spans_baru]
    baca_baru = BA.baca_bagian_awal(par_baru)
    cek('tulis: sampul terisi Manajemen / Ekonomi dan Bisnis',
        'Program Studi : Manajemen' in
        (baca_baru.get('bagian', {}).get('sampul') or [])
        and 'Fakultas : Ekonomi dan Bisnis' in
        (baca_baru.get('bagian', {}).get('sampul') or []))
    cek('tulis: persetujuan terisi Manajemen',
        'Program Studi : Manajemen' in
        (baca_baru.get('bagian', {}).get('persetujuan') or []))
    cek('tulis: tidak ada lagi label kosong di sampul/persetujuan',
        'Program Studi :' not in
        (baca_baru.get('bagian', {}).get('sampul') or [])
        and 'Fakultas :' not in
        (baca_baru.get('bagian', {}).get('sampul') or [])
        and 'Program Studi :' not in
        (baca_baru.get('bagian', {}).get('persetujuan') or []))
    cek('tulis: badan utuh (BAB I + isi tetap ada)',
        'BAB I' in par_baru and 'Isi badan tetap utuh.' in par_baru)
    cek('tulis: pernyataan tetap kosong',
        (baca_baru.get('bagian', {}).get('pernyataan') or []) == ['', ''])

    # ── 5. Rencana dengan data efektif (jalur konfirmasi) ────────
    data_efektif = BA.prodi_fakultas_efektif_form(
        BA.judul_efektif_form(DATA_TERSIMPAN, PARAGRAF), PARAGRAF)
    cek('efektif: data terisi Manajemen / Ekonomi dan Bisnis',
        data_efektif.get('prodi') == 'Manajemen'
        and data_efektif.get('fakultas') == 'Ekonomi dan Bisnis')
    rencana_efektif = BA.rencana_update(
        data_efektif, HASIL_TERSIMPAN.get('data') or {}, baca,
        HASIL_TERSIMPAN.get('sidik') or {},
        HASIL_TERSIMPAN.get('tahap') or 'final')
    nasib_efektif = _nasib(rencana_efektif)
    cek('efektif: rencana melihat perubahan (sampul/judul/persetujuan '
        'berubah)',
        'sampul' in nasib_efektif['berubah']
        and 'judul' in nasib_efektif['berubah']
        and 'persetujuan' in nasib_efektif['berubah'],
        str(nasib_efektif))
    bagian_efektif = _bangun_bagian_baru(
        rencana_efektif, baca, spans, data_efektif, 'final', PETA,
        PARAGRAF, None, None)
    peta_efektif = {b['kunci']: b for b in bagian_efektif}
    cek('efektif: sampul/judul/persetujuan dibuat ulang dari susun',
        peta_efektif['sampul'].get('xml') is None
        and peta_efektif['judul'].get('xml') is None
        and peta_efektif['persetujuan'].get('xml') is None)
    cek('efektif: sampul susun terisi fakultas/prodi di atas',
        (peta_efektif['sampul'].get('baris') or [])[:2]
        == ['Ekonomi dan Bisnis', 'Manajemen'],
        str((peta_efektif['sampul'].get('baris') or [])[:3]))
    cek('efektif: judul susun terisi Manajemen / Ekonomi dan Bisnis',
        'Program Studi : Manajemen' in
        (peta_efektif['judul'].get('baris') or [])
        and 'Fakultas : Ekonomi dan Bisnis' in
        (peta_efektif['judul'].get('baris') or []))
    cek('efektif: persetujuan susun terisi Manajemen',
        'Program Studi : Manajemen' in
        (peta_efektif['persetujuan'].get('baris') or []))
    # Persetujuan susun vs dipertahankan: hanya baris Prodi yang berubah
    # (susun menambahkan judul seksi di awal + baris kosong di ujung,
    # yang bukan isi).
    def _tanpa_ekor_kosong(x):
        x = [str(v or '').strip() for v in x]
        while x and not x[-1]:
            x.pop()
        return x
    susun_persetujuan = _tanpa_ekor_kosong([
        b for b in (peta_efektif['persetujuan'].get('baris') or [])
        if b != 'Program Studi : Manajemen'])
    kini_persetujuan = _tanpa_ekor_kosong([
        b for b in (baca.get('bagian', {}).get('persetujuan') or [])
        if b != 'Program Studi :'])
    cek('efektif: persetujuan susun sama dengan yang dipertahankan '
        'kecuali Prodi terisi',
        susun_persetujuan
        == ['LEMBAR PERSETUJUAN PEMBIMBING'] + kini_persetujuan,
        str(susun_persetujuan))

    # ── 6. Helper _isi_label_kosong_xml ──────────────────────────
    cek('helper: isi label kosong sederhana',
        BA._teks_dari_xml(BA._isi_label_kosong_xml(
            '<w:p><w:r><w:t xml:space="preserve">Program Studi : </w:t>'
            '</w:r></w:p>', 'Program Studi', 'Manajemen'))
        == 'Program Studi : Manajemen')
    cek('helper: label berisi tidak disentuh',
        BA._isi_label_kosong_xml(
            '<w:p><w:r><w:t>Program Studi : Akuntansi</w:t></w:r></w:p>',
            'Program Studi', 'Manajemen')
        == '<w:p><w:r><w:t>Program Studi : Akuntansi</w:t></w:r></w:p>')
    cek('helper: teks lain tidak disentuh',
        BA._isi_label_kosong_xml(
            '<w:p><w:r><w:t>Nama : Asih</w:t></w:r></w:p>',
            'Program Studi', 'Manajemen')
        == '<w:p><w:r><w:t>Nama : Asih</w:t></w:r></w:p>')
    cek('helper: nilai kosong tidak mengubah apa pun',
        BA._isi_label_kosong_xml(
            '<w:p><w:r><w:t>Program Studi : </w:t></w:r></w:p>',
            'Program Studi', '')
        == '<w:p><w:r><w:t>Program Studi : </w:t></w:r></w:p>')
    cek('helper: label terbelah dua w:t tetap terisi di w:t pertama',
        BA._teks_dari_xml(BA._isi_label_kosong_xml(
            '<w:p><w:r><w:t>Program</w:t></w:r>'
            '<w:r><w:t> Studi : </w:t></w:r></w:p>',
            'Program Studi', 'Manajemen'))
        == 'Program Studi : Manajemen')
    xml_rpr = ('<w:p><w:pPr><w:spacing w:before="0" w:line="360" '
               'w:lineRule="auto"/></w:pPr><w:r><w:rPr><w:b/>'
               '</w:rPr><w:t xml:space="preserve">Fakultas : </w:t>'
               '</w:r></w:p>')
    hasil_rpr = BA._isi_label_kosong_xml(xml_rpr, 'Fakultas',
                                         'Ekonomi dan Bisnis')
    cek('helper: pPr dan rPr asli tetap utuh',
        '<w:spacing w:before="0" w:line="360" w:lineRule="auto"/>' in
        hasil_rpr and '<w:b/>' in hasil_rpr
        and BA._teks_dari_xml(hasil_rpr)
        == 'Fakultas : Ekonomi dan Bisnis')


if __name__ == '__main__':
    jalankan()
    print(f'\nLULUS {len(LULUS)}  GAGAL {len(GAGAL)}')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
        sys.exit(1)
    print('SEMUANYA LULUS')
    shutil.rmtree(TMP, ignore_errors=True)
