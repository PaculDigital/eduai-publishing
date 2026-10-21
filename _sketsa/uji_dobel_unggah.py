"""UJI APAKAH DOBEL-UNGGAH JUGA TERJADI TANPA CAMPUR TANGAN ALAT UJI.

KENAPA: dari L2 kita dapat 2 berkas identik (file 47 & 48). TAPI Wulan
    MEMICU event `change` manual — padahal `DOM.setFileInputFiles` sudah
    memicunya sendiri. Jadi separuh sebab = ulah alat uji.
    Uji ini MEMBUKTIKAN dengan 3 perlakuan:
      A. setFileInputFiles SAJA (tanpa picu change)  → apakah 1 berkas?
      B. picu change PALING BANYAK 2× (meniru klik dobel) → apakah 2 berkas?
      C. apakah backend menolak dobel? (uji langsung 2 POST identik)
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402

HASIL = pathlib.Path('/opt/data/services/eduai-publishing/_sketsa/e2e_bukti')


def berkas_uji(s: Sesi) -> int:
    """Berapa baris `.berkas-baris` / tautan unduh terlihat (hitungan layar)."""
    return s.js("document.querySelectorAll('a[href*=\"/unduh/\"]').length") or 0


def main() -> int:
    s = Sesi()
    try:
        s.ke(f'{BASE}/naskah', 5)
        awal = berkas_uji(s)
        info(f'berkas di layar SEBELUM: {awal}')

        # ── A. setFileInputFiles SAJA (TANPA picu change) ────────────────
        print('\n── A. unggah NORMAL (tanpa picu change manual) ──────────')
        root = s.tab.cmd('DOM.getDocument', {'depth': -1})
        rid = root['result']['root']['nodeId']
        nid = s.tab.cmd('DOM.querySelector',
                        {'nodeId': rid, 'selector': 'input#pilih'}
                        )['result']['nodeId']
        s.tab.cmd('DOM.setFileInputFiles', {'files': ['/tmp/naskah_bos.docx'],
                                            'nodeId': nid})
        print('     setFileInputFiles dipanggil (TANPA picu change)')
        time.sleep(25)
        sesudah = berkas_uji(s)
        info(f'berkas di layar SESUDAH-A: {sesudah} (selisih {sesudah - awal})')
        cek('A. unggah normal = 1 berkas (tidak dobel)',
            (sesudah - awal) == 1, f'selisih={sesudah - awal}')
        s.potret('DOBEL_A_sesudah')

        print()
        print('  KESIMPULAN SEMENTARA: kalau selisih=1 → dobel murni ulah alat uji')
        print('  (Wulan memicu `change` 2×). Kalau selisih=2 → BUG sungguhan.')
    finally:
        s.tutup()
    return 0


if __name__ == '__main__':
    sys.exit(main())
