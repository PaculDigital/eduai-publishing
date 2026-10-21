#!/usr/bin/env python3
"""UJI AI SUNGGUHAN — apakah AI patuh G7e (3 LAPIS grafik + tidak mengarang).

Panggil jalur produksi yang SAMA (SYSTEM_REVISI + _panggil_9router).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402
from app import gambar as G                                 # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as S                                  # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


sumber = Path('/app/_naskah_bos_uji.docx')
teks = A._teks_dari_berkas(sumber, 'x.docx')
peta = S.petakan(teks) if hasattr(S, 'petakan') else None
blok_konteks = K.bangun_prompt(bagian_target='1.5', peta=peta)
print(f'  konteks bagian 1.5: {len(blok_konteks):,} kar')

KOMENTAR = ('Bu, pada bagian ini saya perlu grafik pertumbuhan GDP '
            '2015-2018 agar polanya terlihat. Datanya: 2015 = 30; '
            '2016 = 34; 2017 = 38; 2018 = 42 (satuan persen, sumber BPS).')

user_msg = (f'{blok_konteks}\n\n=== KOMENTAR YANG HARUS DIPENUHI ===\n'
            f'{KOMENTAR}\n')

print('  ── kirim ke AI (9router combo EduAi) ──')
jawab = ''
try:
    msg, info = asyncio.run(A._panggil_9router(user_msg, 300))
    jawab = msg
    print(f'  ✅ balasan {len(jawab):,} kar · model={info.get("model")}')
except Exception as e:                                        # noqa: BLE001
    print(f'  ❌ gagal: {type(e).__name__}: {e}')

if jawab:
    Path('/app/_uji_c/jawaban_ai.txt').write_text(jawab, encoding='utf-8')
    blokg = G.tangkap_data_grafik(jawab)
    nilai = G.nilai_kelayakan_grafik(jawab)
    bersih = G.buang_blok_grafik(jawab)

    print()
    print('════════ JAWABAN AI (utuh) ════════')
    print(jawab[:1600])
    print('════════════════════════════════════')
    print()
    print(f'  blok grafik: {len(blokg)}')
    if blokg:
        print(f'     jenis={blokg[0]["jenis"]} · judul={blokg[0]["judul"]!r} · '
              f'{len(blokg[0]["data"])} titik')
    print(f'  kelayakan  : layak={nilai["layak"]} · sebab={nilai["sebab"][:60]!r}')
    print(f'     pengantar={nilai["ada_kalimat_pengantar"]} · '
          f'penafsiran={nilai["ada_kalimat_penafsiran"]} · '
          f'panjang={nilai["panjang_kalimat"]} kar')
    print()
    print('  ── teks TANPA penanda mesin ──')
    print(f'  {bersih[:500]}')
    print()

    cek('AI keluarkan blok grafik', len(blokg) >= 1)
    cek('AI sertakan KALIMAT PENJELAS', nilai['panjang_kalimat'] >= 120,
        f'({nilai["panjang_kalimat"]})')
    cek('lulus penjaga 3 lapis', nilai['layak'] is True, nilai['sebab'][:60])
    cek('penanda mesin DIBUANG', 'DATA-GRAFIK' not in bersih)
    if blokg:
        angka = [v for _, v in blokg[0]['data']]
        cek('angka PERSIS yang user sebut', angka == [30.0, 34.0, 38.0, 42.0],
            f'(dapat {angka})')
    print()
    print('  ── MERAH: uji AI TANPA angka (harus TOLAK, jangan mengarang) ──')
    KOM2 = 'Bu, tolong buatkan grafik pertumbuhan ekonomi Indonesia.'
    try:
        msg2, _ = asyncio.run(A._panggil_9router(
            f'{blok_konteks}\n\n=== KOMENTAR YANG HARUS DIPENUHI ===\n{KOM2}\n',
            300))
        j2 = msg2
        Path('/app/_uji_c/jawaban_ai_tanpa_angka.txt').write_text(
            j2, encoding='utf-8')
        b2 = G.tangkap_data_grafik(j2)
        print(f'  jawaban {len(j2):,} kar · blok grafik: {len(b2)}')
        print(f'  kutipan: {j2[:400]}')
        cek('TIDAK mengarang angka (tidak ada blok grafik)', len(b2) == 0,
            f'(dapat {len(b2)} blok)')
    except Exception as e:                                    # noqa: BLE001
        print(f'  ❌ gagal: {e}')

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')