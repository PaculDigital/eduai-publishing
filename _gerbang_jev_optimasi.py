#!/usr/bin/env python3
"""GERBANG JEV OPTIMASI — PERIKSA MUTU ARTIKEL (07 Okt 2026).

WAJIB dari DALAM container:
    docker cp _gerbang_jev_optimasi.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_jev_optimasi.py

MENGUJI (Jev dipalsukan — hemat 9router):
  [A] ELEMEN_MUTU ada 11 + BAGIAN_WAJIB ada 7 (sumber jurnalkit/jemt_prompt.md)
  [B] LABEL_ELEMEN lengkap untuk semua kunci
  [C] SEMUA pertanyaan bertipe SAH ('noul'/'choice'/'score') — TIDAK ada tipe karangan
      (⚠️ jebakan: tipe teks_bebas → 9router 503 invalid_union)
  [D] periksa_mutu(): pisah KURANG / RAGU / ADA dengan ambang benar
  [E] Jev MATI → konversi TETAP JALAN (tak boleh jadi penghalang)
  [F] rangkum_mutu(): LAPOR bukan vonis ('Pasal ini BELUM ADA', bukan 'salah')
  [G] kode: Jev-mutu dipanggil SETELAH pagar ①②③ + dibungkus try/except
  [H] integrasi periksa_sebelum_konversi() mengisi 'mutu' + 'mutu_pesan'
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


def main() -> int:
    print('══ GERBANG JEV OPTIMASI — PERIKSA MUTU ARTIKEL ══')

    #  ── [A] jumlah pertanyaan ────────────────────────────────────────
    print('\n[A] ELEMEN MUTU & BAGIAN WAJIB')
    cek('ELEMEN_MUTU ADA', hasattr(konversi, 'ELEMEN_MUTU'))
    cek('BAGIAN_WAJIB_JEV ADA', hasattr(konversi, 'BAGIAN_WAJIB_JEV'))
    # ⚠️ JANGAN timpa BAGIAN_WAJIB milik mesin periksa_hasil()
    cek('BAGIAN_WAJIB mesin TETAP (tidak tertimpa)',
        konversi.BAGIAN_WAJIB == ('pendahuluan', 'metode', 'hasil_pembahasan',
                                  'kesimpulan'), str(konversi.BAGIAN_WAJIB))
    cek('ELEMEN_MUTU = 11 elemen mutu (JEMT)', len(konversi.ELEMEN_MUTU) == 11,
        f'{len(konversi.ELEMEN_MUTU)}')
    cek('BAGIAN_WAJIB_JEV = 7 bagian IMRAD', len(konversi.BAGIAN_WAJIB_JEV) == 7,
        f'{len(konversi.BAGIAN_WAJIB_JEV)}')
    for wajib in ('ada_novelty', 'ada_gap', 'ada_limitasi', 'ada_implikasi'):
        cek(f'  elemen "{wajib}" ADA', wajib in konversi.ELEMEN_MUTU)
    for w in ('ada_abstrak', 'ada_metode', 'ada_hasil', 'ada_pustaka'):
        cek(f'  bagian "{w}" ADA', w in konversi.BAGIAN_WAJIB_JEV)

    #  ── [B] LABEL lengkap ───────────────────────────────────────────
    print('\n[B] LABEL_ELEMEN')
    semua = set(konversi.ELEMEN_MUTU) | set(konversi.BAGIAN_WAJIB_JEV)
    kurang_label = [k for k in semua if k not in konversi.LABEL_ELEMEN]
    cek('semua kunci punya LABEL manusia', not kurang_label, str(kurang_label))
    bocor = [k for k, v in konversi.LABEL_ELEMEN.items()
             if 'ada_' in str(v) or 'noul' in str(v)]
    cek('label TIDAK membocorkan nama teknis', not bocor, str(bocor[:3]))

    #  ── [C] TIPE pertanyaan SAH (jebakan 9router) ───────────────────
    print('\n[C] TIPE pertanyaan — jebakan invalid_union')
    #  ⚠️ TIGA tipe SAH (07 Okt 2026, terukur ke /systemone langsung):
    #     'noul' (ya/tidak) · 'choice' (pilih 1) · 'score' (taraf skala).
    #     Klaim lama "hanya 2 tipe" KELIRU — `score` terbuang tanpa alasan.
    tipe_sah = {'noul', 'choice', 'score'}
    for nama_kumpulan, kumpulan in (('ELEMEN_MUTU', konversi.ELEMEN_MUTU),
                                    ('BAGIAN_WAJIB_JEV', konversi.BAGIAN_WAJIB_JEV),
                                    ('PERTANYAAN_PETA', konversi.PERTANYAAN_PETA)):
        salah = [k for k, v in kumpulan.items()
                 if not isinstance(v, dict) or v.get('type') not in tipe_sah]
        cek(f'  {nama_kumpulan}: semua tipe SAH', not salah, str(salah))
    #  khusus: jangan ada 'teks_bebas' di mana pun
    teks = Path('/app/app/konversi.py').read_text(encoding='utf-8')
    cek("tidak ada 'teks_bebas' di kode (penyebab 503)", 'teks_bebas' not in teks)

    #  ── [D] periksa_mutu() pisah KURANG/RAGU/ADA ─────────────────────
    print('\n[D] periksa_mutu() — ambang')
    cek('periksa_mutu ADA', hasattr(konversi, 'periksa_mutu'))
    asli_tanya = satpam.tanya_bebas
    asli_mutu = getattr(satpam, 'tanya_bebas_mutu', None)
    asli_peta = konversi.peta_bab

    def _suntik(nilai_map):
        #  periksa_mutu sekarang pakai tanya_bebas_mutu (bahan siap), bukan tanya_bebas
        satpam.tanya_bebas_mutu = lambda bahan, q: {
            k: {'type': 'noul', 'noul': nilai_map.get(k, 0.9)} for k in q}
        return konversi.periksa_mutu(None, 1, 'NASKAH UJI panjang cukup')

    try:
        #  semua tinggi → bersih
        h = _suntik({})
        cek('semua nilai 0,9 → keputusan "bersih"', h['keputusan'] == 'bersih',
            h['keputusan'])
        cek('  kurang kosong', not h['kurang'], str(h['kurang']))

        #  novelty rendah → kurang
        h2 = _suntik({'ada_novelty': 0.10})
        cek('novelty 0,10 → masuk KURANG', 'pernyataan kebaruan (novelty)' in h2['kurang'],
            str(h2['kurang']))
        cek('  keputusan "kurang"', h2['keputusan'] == 'kurang', h2['keputusan'])

        #  nilai tengah (0,40) → RAGU, bukan kurang dan bukan ada
        h3 = _suntik({'ada_gap': 0.40})
        cek('gap 0,40 → masuk RAGU (bukan kurang)',
            'pernyataan celah penelitian (gap)' in h3['ragu']
            and 'pernyataan celah penelitian (gap)' not in h3['kurang'],
            f'ragu={h3["ragu"]} kurang={h3["kurang"]}')

        #  kosong → ragu, jangan klaim apa pun
        h4 = _suntik({'ada_hook': None})
        cek('nilai None → masuk RAGU', 'pembukaan yang menarik (hook)' in h4['ragu'],
            str(h4['ragu']))

        cek('skor terhitung 0..1', 0.0 <= h['skor'] <= 1.0, str(h['skor']))
        cek('model asli dilaporkan', bool(h.get('model')), str(h.get('model')))
    finally:
        satpam.tanya_bebas = asli_tanya
        if hasattr(satpam, 'tanya_bebas_mutu'):
            satpam.tanya_bebas_mutu = asli_mutu
        konversi.peta_bab = asli_peta

    #  ── [E] Jev MATI → tetap jalan ──────────────────────────────────
    print('\n[E] JEV MATI → tidak jadi penghalang')
    satpam.tanya_bebas_mutu = lambda bahan, q: None
    try:
        hm = konversi.periksa_mutu(None, 1, 'NASKAH UJI cukup panjang')
        cek('Jev mati → balik dict', isinstance(hm, dict), type(hm).__name__)
        cek('Jev mati → keputusan "mati"', hm['keputusan'] == 'mati', hm['keputusan'])
        cek('Jev mati → TIDAK lempar galat', True)
        cek('Jev mati → kurang kosong (tidak menuduh)',
            not hm['kurang'], str(hm['kurang']))
    except Exception as e:                                    # noqa: BLE001
        cek('Jev mati → tidak lempar galat', False, f'{type(e).__name__}: {e}')
    finally:
        satpam.tanya_bebas_mutu = asli_tanya

    #  ── [F] rangkum_mutu = LAPOR bukan vonis ────────────────────────
    print('\n[F] rangkum_mutu() — LAPOR, bukan VONIS')
    cek('rangkum_mutu ADA', hasattr(konversi, 'rangkum_mutu'))
    p1 = konversi.rangkum_mutu({'ok': True, 'kurang': ['pernyataan kebaruan (novelty)'],
                                'ragu': []})
    cek('menyebut poin yang belum ada', 'BELUM ADA' in p1, p1[:60])
    cek('menyebut nama poinnya', 'novelty' in p1.lower(), p1[:60])
    cek('menawarkan pilihan (lanjut/lengkapi)',
        'lanjut' in p1.lower() and 'lengkapi' in p1.lower(), p1[:70])
    cek('menyebut Token Revisi (pintu jualan)', 'Token Revisi' in p1, p1[:80])
    rendah = p1.lower()
    cek('TIDAK memvonis (salah/buruk/tidak layak)',
        not any(v in rendah for v in ('salah', 'buruk', 'tidak layak')), p1[:70])
    p2 = konversi.rangkum_mutu({'ok': True, 'kurang': [], 'ragu': ['abstrak']})
    cek('ragu → minta diperiksa manusia', 'periksa' in p2.lower(), p2[:70])
    p3 = konversi.rangkum_mutu({'ok': True, 'kurang': [], 'ragu': []})
    cek('semua ada → pesan positif', 'sudah ada' in p3.lower(), p3[:60])
    cek('hasil mati → pesan kosong', konversi.rangkum_mutu({'ok': False}) == '')

    #  ── [G] URUTAN di kode ──────────────────────────────────────────
    print('\n[G] URUTAN: Jev-mutu SETELAH pagar ①②③')
    kode = Path('/app/app/konversi.py').read_text(encoding='utf-8')
    i2 = kode.find('kurang = lengkapi_identitas(ident)')
    i3 = kode.find('cek_kelengkapan(')
    i_mata = kode.find('mata_jev(db, fid, naskah)')
    i_mutu = kode.find('periksa_mutu(db, fid, naskah)')
    cek('Jev-mutu dipanggil ADA', i_mutu > 0, str(i_mutu))
    cek('Jev-mutu SETELAH pagar② (identitas)', i2 < i_mutu, f'{i2}<{i_mutu}')
    cek('Jev-mutu SETELAH pagar③ (kelengkapan)', i3 < i_mutu, f'{i3}<{i_mutu}')
    cek('Jev-mutu SETELAH Jev-mata', i_mata < i_mutu, f'{i_mata}<{i_mutu}')
    cek('Jev-mutu dibungkus try/except',
        'periksa_mutu(db, fid, naskah)' in kode and 'except Exception' in kode, '')
    #  tidak ada henti=True dipicu Jev
    import re as _re
    tersangka = []
    for m in _re.finditer(r'henti=True', kode):
        konteks = kode[max(0, m.start() - 260):m.start()]
        if any(x in konteks for x in ('periksa_mutu', 'mata_jev', 'mutu[')):
            tersangka.append(konteks.strip().splitlines()[-1][:70])
    cek('tidak ada henti=True dipicu Jev', not tersangka, str(tersangka[:2]))

    #  ── [H] integrasi ke periksa_sebelum_konversi ────────────────────
    print('\n[H] integrasi periksa_sebelum_konversi()')
    cek("kunci 'mutu' terisi", "keluar['mutu'] = periksa_mutu" in kode, '')
    cek("kunci 'mutu_pesan' terisi", "keluar['mutu_pesan'] = rangkum_mutu" in kode, '')

    #  ── [I] BAHAN MUTU memuat AWAL + AKHIR naskah ───────────────────
    #  ⚠️ AKAR 07Okt26: bahan peta bab TIDAK memuat abstrak & daftar pustaka
    #  (di luar bab) → Jev salah bilang "tidak ada abstrak". Asersi ini
    #  menangkap kalau bahan kembali ke versi peta-bab saja.
    print('\n[I] _bahan_mutu() — WAJIB memuat AWAL & AKHIR naskah')
    cek('_bahan_mutu ADA', hasattr(konversi, '_bahan_mutu'))
    if hasattr(konversi, '_bahan_mutu'):
        naskah_uji = ('ABSTRAK Skripsi ini meneliti pengaruh digital marketing. ' +
                      ('isi tengah ' * 3000) +
                      ' DAFTAR PUSTAKA Ahmad, B. (2024). Jurnal Ilmu.')
        bahan = konversi._bahan_mutu(naskah_uji)
        cek('bahan memuat ABSTRAK (awal naskah)', 'ABSTRAK' in bahan,
            f'{len(bahan)} kar')
        cek('bahan memuat DAFTAR PUSTAKA (akhir naskah)',
            'DAFTAR PUSTAKA' in bahan, f'{len(bahan)} kar')
        cek('bahan dipotong (ringan, < 20.000 kar)', len(bahan) < 20000,
            f'{len(bahan)}')
        cek('naskah kecil TIDAK dipotong',
            konversi._bahan_mutu('pendek saja') == 'pendek saja')
    #  TIDAK boleh kembali pakai _susun_state untuk mutu
    cek("periksa_mutu TIDAK pakai _susun_state (bahan peta bab)",
        '_susun_state(teks' not in kode.split('def periksa_mutu')[1].split('def ')[0]
        if 'def periksa_mutu' in kode else False, '')
    cek('satpam.tanya_bebas_mutu ADA (bahan siap)',
        'def tanya_bebas_mutu' in Path('/app/app/satpam.py').read_text(encoding='utf-8'))

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
