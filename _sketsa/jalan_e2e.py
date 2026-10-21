"""UJI E2E LAYAR — MAHASISWA ↔ PEMBIMBING (AI NYATA, NASKAH NYATA).

JALANKAN DI HOST:  python3 _sketsa/jalan_e2e.py

URUTAN (persis alur manusia di layar):
  L1  MAHASISWA  login lewat /masuk  → /naskah
  L2  MAHASISWA  unggah naskah BOS (63.797 kar) lewat form asli
  L3  MAHASISWA  bagikan tautan pembimbing (/pembimbing/bagikan)
  L4  PEMBIMBING buka /tinjau/<token> (TANPA login)
  L5  PEMBIMBING sorot + tulis komentar
  L6  PEMBIMBING aktifkan komentar
  L7  MAHASISWA  lihat komentar → klik EduAi → REVISI AI NYATA
  L8  MONITOR    proses jalan (tahap, waktu, token, model)
  L9  MAHASISWA  cek saldo Token Revisi (sebelum vs sesudah)
  L10 MAHASISWA  uji TOMBOL (Terapkan / Tolak / Riwayat / Lewati)
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import (BASE, KELUARAN, LULUS, GAGAL, Sesi, cek,  # noqa
                           info, isi_form, klik)


def baca(s, expr, tunggu=0.0):
    return s.js(expr, tunggu)


def main() -> int:
    print('=' * 78)
    print('UJI E2E LAYAR — MAHASISWA ↔ PEMBIMBING (AI NYATA · NASKAH BOS)')
    print('=' * 78)
    s = Sesi()
    try:
        # ══ L1. LOGIN MAHASISWA ══════════════════════════════════════════
        print('\n── L1. MAHASISWA LOGIN (layar /masuk) ────────────────────')
        s.ke(f'{BASE}/masuk', 4)
        r = baca(s, "document.body.innerText.slice(0,120)")
        cek('L1a halaman masuk terbuka',
            'Masuk' in str(r) or 'masuk' in str(r), str(r)[:70])
        info('isi form: ' + isi_form(s, 'email', 'uji-berbayar-e2e@test.local'))
        info('isi sandi: ' + isi_form(s, 'password', 'UjiBayar123!'))
        s.potret('L1_form_masuk')
        klik(s, 'form button[type="submit"]', 5)
        url = baca(s, 'location.pathname')
        cek('L1b login berhasil → /naskah', url == '/naskah', f'path={url}')
        judul = baca(s, "document.querySelector('h1,h2')?.innerText || ''")
        info(f'halaman: {judul!r}')

        # ══ L2. UNGGAH NASKAH BOS ════════════════════════════════════════
        print('\n── L2. MAHASISWA UNGGAH NASKAH BOS (63.797 kar) ──────────')
        n = baca(s, "document.querySelectorAll('.file-baris,.berkas').length")
        info(f'berkas sebelum unggah: {n}')
        s.potret('L2a_sebelum_unggah')
        #  Unggah lewat CARA ASLI BROWSER: DOM.setFileInputFiles ke
        #  `input#pilih[name=berkas]`, lalu picu event 'change' supaya
        #  JS halaman (`pilih.addEventListener('change', …)`) jalan sendiri
        #  → form terkirim ke /unggah seperti mahasiswa sungguhan.
        naskah = '/tmp/naskah_bos.docx'
        doc = baca(s, "(function(){var i=document.querySelector('input#pilih');"
                      "return i ? 'ada' : 'tidak ada';})()")
        cek('L2a input unggah ada di layar', doc == 'ada', str(doc))
        #  nodeId untuk DOM.setFileInputFiles
        root = s.tab.cmd('DOM.getDocument', {'depth': -1})
        rid = root.get('result', {}).get('root', {}).get('nodeId')
        q = s.tab.cmd('DOM.querySelector',
                      {'nodeId': rid, 'selector': 'input#pilih'})
        nid = q.get('result', {}).get('nodeId')
        info(f'nodeId input = {nid}')
        if nid:
            r = s.tab.cmd('DOM.setFileInputFiles',
                          {'files': [naskah], 'nodeId': nid})
            info(f'setFileInputFiles: {json.dumps(r)[:90]}')
            #  picu 'change' (yang memanggil kirim())
            s.js("document.querySelector('input#pilih')"
                 ".dispatchEvent(new Event('change',{bubbles:true}))")
            info('event change dipicu — menunggu unggah selesai')
            for i in range(30):            # tunggu maks 150 dtk
                time.sleep(5)
                info_ = baca(s, "document.body.innerText")
                if 'Berkas Tersimpan' in str(info_):
                    break
            s.potret('L2b_sesudah_unggah')
        else:
            cek('L2b unggah terkirim', False, 'nodeId tidak ketemu')
    finally:
        print(f'\n       (tab dibiarkan terbuka untuk langkah berikutnya: {s.tid})')
        #  JANGAN tutup — dipakai langkah berikutnya
    print('=' * 78)
    print(f'SEMENTARA: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 78)
    return 0


if __name__ == '__main__':
    sys.exit(main())
