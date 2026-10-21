#!/usr/bin/env python3
"""GERBANG TAHAP 2 KONVERSI — MESIN & PAGAR (07 Okt 2026).

WAJIB dijalankan dari DALAM container `eduai-app`:
    docker cp _gerbang_konversi_mesin.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_konversi_mesin.py

MENGUJI (tanpa memanggil AI — semua mesin/gratis):
  ① PAGAR makro & template : .dotm/.docm/.doc DITOLAK · .docx bersih LOLOS
  ② PAGAR nama+email       : tak ada → BLOKIR (henti) · ada → lolos
  ③ CEK KELENGKAPAN        : benar mendeteksi bab ada/tidak (beri tahu)
  ④ DETEKSI JENIS          : kuantitatif/kualitatif/review + keyakinan
  ⑤ PEMERIKSA HASIL        : bagian kurang & 11 elemen hilang terdeteksi
  ⑥ PROMPT                 : terbaca & memuat 11 elemen + aturan infografis
"""
from __future__ import annotations

import io
import sys
import zipfile

sys.path.insert(0, '/app')

from app import konversi                                              # noqa: E402

LULUS = 0
GAGAL = 0


def cek(nama, benar, bukti=''):
    global LULUS, GAGAL
    if benar:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def _docx_bersih(tmp='/tmp/gerbang_uji_bersih.docx', makro=False):
    """Bikin .docx palsu (zip) — dengan/tanpa vbaProject.bin."""
    with zipfile.ZipFile(tmp, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('word/document.xml', '<w:document>isi</w:document>')
        if makro:
            z.writestr('word/vbaProject.bin', b'\x00makro palsu')
    return tmp


def main() -> int:
    print('══ GERBANG TAHAP 2 KONVERSI — MESIN & PAGAR ══')

    #  ── ① PAGAR MAKRO & TEMPLATE ───────────────────────────────────────
    print('\n[1] PAGAR MAKRO & TEMPLATE (putusan Bos §N no.1 & no.3)')
    bersih = _docx_bersih()

    aman, _ = konversi.periksa_berkas_aman('naskah.docx', bersih)
    cek('.docx bersih → LOLOS', aman is True)

    for ekst in ('.dotm', '.docm', '.doc', '.dot'):
        aman, pesan = konversi.periksa_berkas_aman(f'jahat{ekst}', bersih)
        cek(f'{ekst} → DITOLAK', aman is False, pesan)

    ber_makro = _docx_bersih('/tmp/gerbang_uji_makro.docx', makro=True)
    aman, pesan = konversi.periksa_berkas_aman('bersih.docx', ber_makro)
    cek('.docx BERMAKRO (vbaProject.bin) → DITOLAK', aman is False, pesan)
    cek('  pesan menyebut MAKRO', 'MAKRO' in pesan.upper(), pesan)

    aman, pesan = konversi.periksa_berkas_aman('naskah.pdf', bersih)
    cek('.pdf → DITOLAK (bukan .docx)', aman is False, pesan)

    #  bukan docx sama sekali (zip kosong)
    with zipfile.ZipFile('/tmp/gerbang_uji_bukan.docx', 'w') as z:
        z.writestr('random.txt', 'bukan word')
    aman, pesan = konversi.periksa_berkas_aman('x.docx', '/tmp/gerbang_uji_bukan.docx')
    cek('zip tanpa word/document.xml → DITOLAK', aman is False, pesan)

    #  ── ② PAGAR NAMA + EMAIL (BLOKIR) ──────────────────────────────────
    print('\n[2] PAGAR NAMA + EMAIL — BLOKIR kalau tak ada (§N no.5)')
    naskah_kosong = 'BAB I PENDAHULUAN\nPenelitian ini membahas sesuatu.'
    ident = konversi.cari_identitas(naskah_kosong)
    cek('tanpa identitas → nama kosong', ident['nama'] == '', str(ident))
    cek('tanpa identitas → email kosong', ident['email'] == '', str(ident))
    kurang = konversi.lengkapi_identitas(ident)
    cek('kurang = [nama, email]', len(kurang) == 2, str(kurang))

    naskah_ada = ('JUDUL SKRIPSI SAYA\n\nNama: Budi Santoso\n'
                  'Email: budi.santoso@univ.ac.id\n\nBAB I PENDAHULUAN\n'
                  'Penelitian ini membahas sesuatu dengan regresi linear.')
    ident2 = konversi.cari_identitas(naskah_ada)
    cek('nama TERBACA dari naskah', ident2['nama'] == 'Budi Santoso', str(ident2))
    cek('email TERBACA dari naskah',
        ident2['email'] == 'budi.santoso@univ.ac.id', str(ident2))
    cek('lengkapi_identitas = kosong', konversi.lengkapi_identitas(ident2) == [],
        str(konversi.lengkapi_identitas(ident2)))

    #  label "Oleh"
    ident3 = konversi.cari_identitas('Oleh: Siti Aminah\nsiti@mail.com\nBAB I')
    cek('label "Oleh:" terbaca', ident3['nama'] == 'Siti Aminah', str(ident3))

    #  ── ③ CEK KELENGKAPAN (beri tahu, tidak memblokir) ─────────────────
    print('\n[3] CEK KELENGKAPAN BAGIAN — sebelum konversi (§N no.7)')
    peta_lengkap = [
        {'section_title': 'BAB I PENDAHULUAN'},
        {'section_title': 'BAB II TINJAUAN PUSTAKA'},
        {'section_title': 'BAB III METODE PENELITIAN'},
        {'section_title': 'BAB IV HASIL DAN PEMBAHASAN'},
        {'section_title': 'BAB V KESIMPULAN'},
        {'section_title': 'DAFTAR PUSTAKA'},
    ]
    k1 = konversi.cek_kelengkapan({}, peta_lengkap)
    cek('peta lengkap → kurang = []', k1['kurang'] == [], str(k1['kurang']))

    peta_kurang = [{'section_title': 'BAB I PENDAHULUAN'},
                   {'section_title': 'BAB II TINJAUAN PUSTAKA'}]
    k2 = konversi.cek_kelengkapan({}, peta_kurang)
    cek('peta kurang → deteksi metode/hasil/kesimpulan',
        'metode' in k2['kurang'] and 'hasil' in k2['kurang']
        and 'kesimpulan' in k2['kurang'], str(k2['kurang']))

    k3 = konversi.cek_kelengkapan({}, [])
    cek('peta kosong → ada_peta False', k3['ada_peta'] is False, str(k3))

    #  ── ④ DETEKSI JENIS ────────────────────────────────────────────────
    print('\n[4] DETEKSI JENIS — kuantitatif/kualitatif/review')
    d1 = konversi.deteksi_jenis(
        'Penelitian ini memakai kuesioner dengan skala likert. Uji hipotesis '
        'regresi linear berganda di SPSS, signifikansi p value, koefisien beta.')
    cek('kuantitatif terdeteksi', d1['jenis'] == konversi.JENIS_KUANTITATIF,
        str(d1['jenis']))
    cek('kuantitatif: yakin tinggi', d1['yakin'] >= 0.60, str(d1['yakin']))

    d2 = konversi.deteksi_jenis(
        'Wawancara mendalam dengan informan dilakukan secara purposive. '
        'Analisis tematik dan triangulasi, catatan lapangan, member check.')
    cek('kualitatif terdeteksi', d2['jenis'] == konversi.JENIS_KUALITATIF,
        str(d2['jenis']))

    d3 = konversi.deteksi_jenis(
        'Systematic review mengikuti PRISMA. Kriteria inklusi dan eksklusi '
        'ditetapkan, tinjauan sistematis terhadap literature review.')
    cek('review terdeteksi', d3['jenis'] == konversi.JENIS_REVIEW, str(d3['jenis']))

    d4 = konversi.deteksi_jenis('Ini dokumen tanpa penanda apa pun.')
    cek('tanpa bukti → keyakinan RENDAH', d4['yakin'] <= 0.40, str(d4['yakin']))
    cek('tanpa bukti → ada alasan', len(d4['alasan']) > 0, str(d4['alasan']))

    #  ── ⑤ PEMERIKSA HASIL (2 lapis · lapis 1 mesin) ────────────────────
    print('\n[5] PEMERIKSA HASIL — bagian & 11 elemen (lapis mesin, gratis)')
    artikel_buruk = {'pendahuluan': 'pendek', 'penulis': [{}]}
    h1 = konversi.periksa_hasil(artikel_buruk)
    cek('artikel kosong → TIDAK lolos', h1['lolos'] is False, str(h1['temuan']))
    cek('deteksi bagian kurang', len(h1['kurang_bagian']) >= 3,
        str(h1['kurang_bagian']))
    cek('deteksi 11 elemen hilang', len(h1['elemen_hilang']) == 11,
        str(len(h1['elemen_hilang'])))

    elemen_penuh = {k: f'kutipan {k}' for k, _l, _t in konversi.ELEMEN_11}
    panjang = 'x' * 500
    artikel_baik = {
        'pendahuluan': panjang, 'metode': panjang,
        'hasil_pembahasan': panjang, 'kesimpulan': panjang,
        'abstrak_id': 'a' * 400, 'abstract_en': 'b' * 400,
        'penulis': [{'nama': 'Budi', 'email': 'b@x.id'}],
        'elemen': elemen_penuh,
    }
    h2 = konversi.periksa_hasil(artikel_baik)
    cek('artikel lengkap → LOLOS', h2['lolos'] is True, str(h2['temuan']))
    cek('11 elemen terdeteksi', h2['jumlah_elemen'] == 11, str(h2['jumlah_elemen']))

    #  elemen null TIDAK dihitung (anti-karangan)
    el_null = dict(elemen_penuh)
    el_null['hook'] = ''
    h3 = konversi.periksa_hasil({**artikel_baik, 'elemen': el_null})
    cek('elemen kosong dihitung HILANG', h3['jumlah_elemen'] == 10,
        str(h3['jumlah_elemen']))
    cek('  hook masuk daftar hilang',
        any(e['kunci'] == 'hook' for e in h3['elemen_hilang']), str(h3['elemen_hilang']))

    #  ── ⑥ PROMPT ───────────────────────────────────────────────────────
    print('\n[6] PROMPT ARTIKEL — terbaca & memuat aturan wajib')
    p = konversi.muat_prompt()
    cek('prompt terbaca (tidak kosong)', len(p) > 1000, f'{len(p)} kar')
    for kata in ('Hook', 'State of Art', 'Gap', 'Novelty', 'Findings',
                 'Critical Analysis', 'Diskusi Komparatif', 'Kaitan Teori',
                 'Limitasi', 'Rekomendasi Riset Lanjut', 'Implikasi'):
        cek(f'  11 elemen memuat "{kata}"', kata in p)
    cek('aturan infografis (grafik ke LAMPIRAN)', 'LAMPIRAN' in p.upper(), '')
    cek('aturan anti-halusinasi (JANGAN MENGARANG)',
        'JANGAN MENGARANG' in p.upper(), '')
    cek('abstrak 2 bahasa', 'ABSTRAK (ID)' in p and 'ABSTRACT (EN)' in p, '')
    cek('larangan ubah metode', 'JANGAN MENGUBAH METODE' in p.upper(), '')

    #  ── ⑦ SUSUN PESAN ──────────────────────────────────────────────────
    print('\n[7] SUSUN PESAN — identitas + peta + naskah')
    pesan = konversi.susun_pesan(
        naskah_ada, konversi.JENIS_KUANTITATIF, ident2,
        {'kerangka': [{'no': 1, 'judul': 'BAB I', 'panjang': 100, 'ringkas': 'x'}],
         'brief': {'judul': 'Uji'}})
    cek('pesan memuat identitas', 'Budi Santoso' in pesan, '')
    cek('pesan memuat jenis', 'Kuantitatif' in pesan, '')
    cek('pesan memuat peta naskah', 'PETA NASKAH' in pesan, '')
    cek('pesan memuat naskah', 'BAB I PENDAHULUAN' in pesan, '')
    cek('pesan minta JSON sah', 'JSON' in pesan, '')

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
