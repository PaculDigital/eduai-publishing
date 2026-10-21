#!/usr/bin/env python3
"""GERBANG JEV SEBAGAI MATA — konversi (07 Okt 2026).

WAJIB dari DALAM container:
    docker cp _gerbang_jev_mata.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_jev_mata.py

MENGUJI (TANPA panggil Jev sungguhan — pakai penyuntik palsu, hemat):
  [A] satpam.tanya_bebas() ADA & bentuknya benar
  [B] konversi.mata_jev() ADA & SELALU balik dict (tak pernah lempar galat)
  [C] Jev MATI → konversi TETAP JALAN (Jev tak boleh jadi penghalang)
  [D] Jev SETUJU / BEDA / RAGU → keputusan benar (ambang)
  [E] rangkum_mata() = LAPOR, bukan vonis ('salah'/'benar' DILARANG)
  [F] periksa_sebelum_konversi() memanggil Jev SETELAH pagar ①②③
  [G] Jev TIDAK memblokir: boleh=True walau Jev ragu/mati
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import konversi, satpam                                        # noqa: E402

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


NASKAH = """SKRIPSI
PENGARUH DIGITAL MARKETING TERHADAP KEBERLANJUTAN USAHA

OLEH :
ASIH SUSANTI PUTRI
NIM : 112210485
Email : asihsusantiputri@gmail.com

BAB I PENDAHULUAN
1.1 Latar Belakang
Digital marketing berkembang pesat di Indonesia.

BAB II TINJAUAN PUSTAKA
2.1 Digital Marketing
2.2 Kewirausahaan

BAB III METODE PENELITIAN
3.1 Desain Penelitian
3.2 Populasi dan Sampel

BAB IV HASIL DAN PEMBAHASAN
4.1 Hasil Uji Hipotesis
4.2 Pembahasan

BAB V KESIMPULAN
5.1 Kesimpulan
5.2 Saran

DAFTAR PUSTAKA
"""


def main() -> int:
    print('══ GERBANG JEV SEBAGAI MATA — KONVERSI ══')

    #  ── [A] tanya_bebas ADA ──────────────────────────────────────────
    print('\n[A] satpam.tanya_bebas()')
    cek('tanya_bebas ADA', hasattr(satpam, 'tanya_bebas'))
    import inspect
    sig = inspect.signature(satpam.tanya_bebas) if hasattr(satpam, 'tanya_bebas') else None
    cek('terima (teks, peta, pertanyaan)',
        sig is not None and len(sig.parameters) == 3,
        str(list(sig.parameters)) if sig else 'TIDAK ADA')
    #  fungsi ini TIDAK BOLEH melempar galat
    try:
        h = satpam.tanya_bebas('', [], {})
        cek('input kosong → balik None (tak lempar galat)', h is None, str(h))
        h2 = satpam.tanya_bebas(NASKAH, [], {})
        cek('pertanyaan kosong → balik None', h2 is None, str(h2))
    except Exception as e:                                    # noqa: BLE001
        cek('input kosong → tak lempar galat', False, f'{type(e).__name__}: {e}')

    #  ── [B] mata_jev SELALU balik dict ───────────────────────────────
    print('\n[B] konversi.mata_jev() — bentuk')
    cek('mata_jev ADA', hasattr(konversi, 'mata_jev'))
    cek('PERTANYAAN_PETA ADA', hasattr(konversi, 'PERTANYAAN_PETA'))
    if hasattr(konversi, 'PERTANYAAN_PETA'):
        p = konversi.PERTANYAAN_PETA
        #  ⚠️ SKEMA JEV TERTUTUP (terukur 07Okt26): HANYA 3 nama + 2 tipe ini
        #  yang SAH. Nama/tipe lain → 9router 503 "invalid_union".
        #  Asersi ini menangkap kalau ada yang menambah pertanyaan/tipe baru.
        cek('  HANYA 3 pertanyaan (tidak lebih)', len(p) == 3, str(list(p.keys())))
        for kunci in ('jumlah_bab', 'semua_romawi_sah', 'berurutan'):
            cek(f'  pertanyaan "{kunci}" ADA', kunci in p)
        tipe_sah = {'choice', 'noul'}
        for kunci, isi in p.items():
            cek(f'  "{kunci}" tipe SAH ({tipe_sah})',
                isi.get('type') in tipe_sah, str(isi.get('type')))
        cek('  jumlah_bab pakai criteria',
            'criteria' in (p.get('jumlah_bab') or {}), '')
        cek('  TIDAK ada tipe karangan (teks_bebas dll)',
            not any(isinstance(v, dict) and v.get('type') not in tipe_sah
                    for v in p.values()), '')

    #  ── [C] Jev MATI → konversi tetap jalan ──────────────────────────
    print('\n[C] JEV MATI → konversi TETAP JALAN')
    m = konversi.mata_jev(None, 1, NASKAH)
    cek('mata_jev balik dict', isinstance(m, dict), type(m).__name__)
    cek('punya kunci keputusan', 'keputusan' in m, str(list(m.keys())[:6]))
    cek('tanpa db → TIDAK lempar galat', True)
    print(f'     keputusan={m.get("keputusan")} alasan={str(m.get("alasan"))[:60]}')

    #  ── [D] SUNTIK jawaban Jev palsu → uji ambang ────────────────────
    print('\n[D] AMBANG keputusan (Jev palsu disuntik)')
    asli_tanya = satpam.tanya_bebas
    asli_peta = konversi.peta_bab

    def _suntik(choice, conf, n_bab_mesin=5):
        """Pasang Jev palsu + peta mesin palsu."""
        konversi.peta_bab = lambda db, fid, naskah: {
            'brief': {}, 'peta': [{'section_title': f'Bab {i}'} for i in range(n_bab_mesin)],
            'kerangka': []}
        satpam.tanya_bebas = lambda t, p, q: {
            'jumlah_bab': {'type': 'choice', 'choice': str(choice),
                           'confidence': conf},
            'semua_romawi_sah': {'type': 'noul', 'noul': 0.98},
            'berurutan': {'type': 'noul', 'noul': 0.96},
        }
        return konversi.mata_jev(None, 1, NASKAH)

    try:
        m_setuju = _suntik(5, 0.95)
        cek('Jev 5 bab == mesin 5 bab, conf 0,95 → SETUJU',
            m_setuju['keputusan'] == 'setuju', m_setuju['keputusan'])

        m_beda = _suntik(3, 0.95, n_bab_mesin=5)
        cek('Jev 3 bab != mesin 5 bab → BEDA',
            m_beda['keputusan'] == 'beda', m_beda['keputusan'])

        m_ragu = _suntik(5, 0.30)
        cek('conf 0,30 (< ambang tanya) → RAGU',
            m_ragu['keputusan'] == 'ragu', m_ragu['keputusan'])

        cek('jumlah_mesin terlapor', m_beda.get('jumlah_mesin') == 5,
            str(m_beda.get('jumlah_mesin')))
        #  ⚠️ Jev SKEMA TERTUTUP: TIDAK ADA 'bagian_wajib'/'bab_jev' lagi.
        #  Yang ada: jumlah_jev, romawi_sah, berurutan. (asersi lama dibuang)
        cek('romawi_sah terbaca (noul)', m_setuju.get('romawi_sah') is not None,
            str(m_setuju.get('romawi_sah')))
        cek('berurutan terbaca (noul)', m_setuju.get('berurutan') is not None,
            str(m_setuju.get('berurutan')))

        #  ── [E] rangkum_mata = LAPOR, bukan vonis ────────────────────
        print('\n[E] rangkum_mata() — LAPOR, bukan VONIS')
        for lbl, mm in (('setuju', m_setuju), ('beda', m_beda), ('ragu', m_ragu)):
            pesan = konversi.rangkum_mata(mm)
            cek(f'  {lbl}: pesan tidak kosong', bool(pesan), pesan[:60])
            rendah = pesan.lower()
            cek(f'  {lbl}: tidak memvonis (kata vonis DILARANG)',
                not any(v in rendah for v in ('salah', ' keliru', ' salah',
                                              'benar', ' benar ')),
                pesan[:70])
        pesan_beda = konversi.rangkum_mata(m_beda).lower()
        cek('  beda: menyebut KEDUA angka', '3' in pesan_beda and '5' in pesan_beda,
            pesan_beda[:70])
        cek('  beda: minta MANUSIA yang putuskan',
            'pilih' in pesan_beda or 'putus' in pesan_beda, pesan_beda[:70])
    finally:
        satpam.tanya_bebas = asli_tanya
        konversi.peta_bab = asli_peta

    #  ── [F] kode: Jev dipanggil SETELAH pagar ①②③ ───────────────────
    print('\n[F] URUTAN di periksa_sebelum_konversi()')
    kode = Path('/app/app/konversi.py').read_text(encoding='utf-8')
    i_pagar1 = kode.find('periksa_berkas_aman(nama_berkas')
    i_pagar2 = kode.find('kurang = lengkapi_identitas(ident)')
    i_pagar3 = kode.find('cek_kelengkapan(')
    i_jev = kode.find('mata_jev(db, fid, naskah)')
    cek('pagar① ada', i_pagar1 > 0)
    cek('pagar② ada', i_pagar2 > 0)
    cek('pagar③ ada', i_pagar3 > 0)
    cek('Jev dipanggil ADA', i_jev > 0, str(i_jev))
    cek('Jev SETELAH pagar①', i_pagar1 < i_jev, f'{i_pagar1} < {i_jev}')
    cek('Jev SETELAH pagar②  (naskah sudah beridentitas)',
        i_pagar2 < i_jev, f'{i_pagar2} < {i_jev}')
    cek('Jev SETELAH pagar③', i_pagar3 < i_jev, f'{i_pagar3} < {i_jev}')

    #  ── [G] Jev TIDAK memblokir ──────────────────────────────────────
    print('\n[G] Jev TIDAK boleh jadi PENGHALANG')
    #  ⚠️ Asersi LAMA hanya cari teks 'boleh=True, henti=False' → LOLOS walau
    #  Jev sudah dijadikan penghalang (suntikan: `keluar.update(boleh=False,
    #  henti=True)` DI ATAS baris Jev). Uji gigi membongkar lubang ini.
    #  Asersi BARU: periksa URUTAN + tidak ada `henti=True` yang menyertakan
    #  'Jev'/'mata' di badannya.
    i_jev = kode.find('mata_jev(db, fid, naskah)')
    i_boleh = kode.find('boleh=True, henti=False')
    cek('Jev dipanggil SEBELUM penutup boleh=True (Jev tak bisa membatalkan)',
        i_jev > 0 and i_boleh > i_jev, f'jev@{i_jev} boleh@{i_boleh}')

    import re as _re
    #  cari setiap blok `keluar.update(... henti=True ...)` lalu lihat 200 kar
    #  sebelumnya — kalau ada 'mata_jev'/'Jev'/'keputusan' → Jev jadi penghalang.
    tersangka = []
    for m in _re.finditer(r'henti=True', kode):
        awal = max(0, m.start() - 260)
        konteks = kode[awal:m.start()]
        if ('mata_jev' in konteks or 'mata[' in konteks
                or "'ragu'" in konteks or '"ragu"' in konteks):
            tersangka.append(konteks.strip().splitlines()[-1][:70])
    cek('tidak ada henti=True yang dipicu oleh Jev',
        not tersangka, str(tersangka[:2]))

    cek('mata_jev dibungkus try/except (tak boleh melempar)',
        'mata_jev(db, fid, naskah)' in kode and 'except Exception' in kode, '')

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
