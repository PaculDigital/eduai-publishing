#!/usr/bin/env python3
"""UJI NASKAH SKRIPSI ASLI — mesin konversi atas naskah NYATA (07 Okt 2026).

WAJIB dari DALAM container:
    docker cp _uji_naskah_asli.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _uji_naskah_asli.py

MENGUJI MESIN (tanpa panggil AI — hemat token) atas 4 naskah NYATA:
  · SKRIPSI S1 UNHAS olahraga   (tanpa email → harusnya DIBLOKIR)
  · SKRIPSI S1 UNMUL            (template kosong → harusnya DIBLOKIR)
  · TESIS S2 UNHAS manajemen    (punya nama, cek deteksi jenis)
  · SKRIPSI UNHAS + identitas buatan (untuk uji jalur LOLOS)

Yang diperiksa: PAGAR ① berkas aman · PAGAR ② nama+email · PAGAR ③ kelengkapan
· DETEKSI JENIS · TEKS TERBACA (bukan kosong).
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

from app import konversi                                              # noqa: E402

LULUS = 0
GAGAL = 0
LADANG = Path('/app/_arsip/contoh-dokumen')


def cek(nama, benar, bukti=''):
    global LULUS, GAGAL
    if benar:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def teks_docx(jalur: Path) -> str:
    """Baca teks mentah .docx (tanpa parser app — supaya uji ini mandiri)."""
    try:
        with zipfile.ZipFile(jalur) as z:
            x = z.read('word/document.xml').decode('utf-8', 'ignore')
    except Exception as e:                                    # noqa: BLE001
        return f'[GAGAL BACA: {e}]'
    t = re.sub(r'</w:p>', '\n', x)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    return t


def uji_satu(nama: str, jalur: Path, harap: dict) -> None:
    print(f'\n── {nama} ──')
    if not jalur.is_file():
        cek(f'{nama}: berkas ADA', False, str(jalur))
        return
    cek(f'{nama}: berkas ADA', True)
    print(f'     ukuran: {jalur.stat().st_size/1024:.1f} KB')

    #  PAGAR ①
    aman, pesan = konversi.periksa_berkas_aman(jalur.name, jalur)
    print(f'     [①] berkas aman: {aman} {pesan[:70]}')
    cek(f'{nama}: PAGAR① berkas aman (docx asli)',
        aman == harap.get('aman', True), pesan[:80])

    t = teks_docx(jalur)
    cek(f'{nama}: teks terbaca (>500 kar)', len(t) > 500, f'{len(t)} kar')

    #  PAGAR ②
    ident = konversi.cari_identitas(t)
    kurang = konversi.lengkapi_identitas(ident)
    print(f'     [②] nama={ident["nama"]!r} email={ident["email"]!r}')
    if harap.get('ada_identitas'):
        cek(f'{nama}: identitas TERBACA', not kurang, str(kurang))
    else:
        cek(f'{nama}: identitas KURANG → akan DIBLOKIR', bool(kurang), str(ident))

    #  JENIS
    j = konversi.deteksi_jenis(t)
    print(f'     [④] jenis={j["jenis"]} yakin={j["yakin"]} skor={j["skor"]}')
    if harap.get('jenis'):
        cek(f'{nama}: jenis = {harap["jenis"]}', j['jenis'] == harap['jenis'],
            j['jenis'])
    cek(f'{nama}: alasan jenis ADA', len(j['alasan']) > 0, '')

    #  KELENGKAPAN — pakai peta bab dari MESIN ASLI (state.petakan).
    #  ⚠️ JEBAKAN 07Okt26: uji pertama Wulan pakai `state.petakan` tanpa argumen
    #  yang benar → peta KOSONG → "kurang" palsu (semua bab dianggap hilang).
    #  Nama fungsi asli = state.petakan(teks) → dict {'bab_besar': [...]}.
    peta = []
    try:
        from app import state
        hasil_peta = state.petakan(t)
        #  ⚠️ state.petakan() balik LIST (bukan dict) — dikira dict di uji pertama.
        peta = hasil_peta if isinstance(hasil_peta, list) else (
            (hasil_peta or {}).get('bab_besar') or [])
        print(f'     peta bab: {len(peta)} bab terdeteksi')
    except Exception as e:                                    # noqa: BLE001
        print(f'     ⚠️ peta bab gagal: {e}')
    kel = konversi.cek_kelengkapan({'teks': t}, peta)
    print(f'     [③] kurang: {kel["kurang"]}')
    print(f'         kategori peta: {kel.get("kategori")}')
    cek(f'{nama}: cek kelengkapan jalan', isinstance(kel.get('kurang'), list), '')
    if peta:
        cek(f'{nama}: peta bab TIDAK kosong (naskah nyata terbaca)',
            len(peta) >= 3, f'{len(peta)} bab')
        #  ⚠️ Asersi ANTI-SALAH-TUDUH: naskah skripsi NYATA pasti punya
        #  pendahuluan+metode+kesimpulan. Kalau pagar bilang KURANG → pagar SALAH.
        cek(f'{nama}: pagar TIDAK salah menuduh (bab inti ada)',
            not (set(kel['kurang']) & {'latar_belakang', 'metode', 'kesimpulan'}),
            str(kel['kurang']))


def main() -> int:
    print('══ UJI NASKAH SKRIPSI ASLI — MESIN KONVERSI ══')

    uji_satu('SKRIPSI S1 UNHAS (olahraga-menstruasi)',
             LADANG / 'skripsi-s1' / 'SKRIPSI-S1-unhas-olahraga-menstruasi.docx',
             {'aman': True, 'ada_identitas': False, 'jenis': konversi.JENIS_KUANTITATIF})

    uji_satu('SKRIPSI S1 UNMUL (fazrigading)',
             LADANG / 'skripsi-s1' / 'SKRIPSI-S1-unmul-fazrigading.docx',
             {'aman': True, 'ada_identitas': False})

    uji_satu('TESIS S2 UNHAS (digital marketing)',
             LADANG / 'tesis-s2' / 'TESIS-S2-unhas-manajemen-digital-marketing.docx',
             {'aman': True, 'ada_identitas': False})

    #  ── JALUR LOLOS: naskah nyata + identitas disisipkan
    print('\n── SKRIPSI UNHAS + identitas disisipkan (uji jalur LOLOS) ──')
    asli = teks_docx(LADANG / 'skripsi-s1' / 'SKRIPSI-S1-unhas-olahraga-menstruasi.docx')
    disisip = ('SKRIPSI\nOleh: Annisa Al-Maghfirah\nEmail: annisa.maghfirah@unhas.ac.id\n\n'
               + asli)
    ident = konversi.cari_identitas(disisip)
    kurang = konversi.lengkapi_identitas(ident)
    print(f'     [②] nama={ident["nama"]!r} email={ident["email"]!r}')
    cek('naskah + identitas → LOLOS pagar②', not kurang, str(kurang))

    j = konversi.deteksi_jenis(disisip)
    print(f'     [④] jenis={j["jenis"]} yakin={j["yakin"]} skor={j["skor"]}')
    cek('jenis terdeteksi (bukan default buta)', j['yakin'] >= 0.30, str(j['yakin']))

    #  susun pesan (tanpa kirim ke AI)
    pesan = konversi.susun_pesan(disisip, j['jenis'], ident,
                                 {'kerangka': [], 'brief': {}})
    cek('susun_pesan jalan atas naskah nyata', len(pesan) > 500, f'{len(pesan)} kar')
    cek('  pesan memuat identitas', 'Annisa' in pesan, '')
    cek('  pesan memuat naskah', 'MENSTRUASI' in pesan.upper(), '')

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
