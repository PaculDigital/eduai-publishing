"""#5 U-KUNCI — UJI SEJATI: apakah HAKIM menangkap yang SURVEYOR lewatkan?

Pertanyaan yang dijawab skrip ini:
  Surveyor (peta3_jev) memberi label. Hakim (hakim_peta T①) memeriksa kandidat
  judul. KUNCI JAWABAN (HASIL_UKUNCI.json, fid=115) bilang 24 'asli' + 51 'palsu'.

  ⇒ Apakah hakim BENAR pada baris yang kunci bilang 'palsu' (surveyor salah)?
  ⇒ Apakah hakim TIDAK mengganggu baris yang kunci bilang 'asli'?

Cara ukur:
  'palsu' di kunci = kandidat judul yang SEHARUSNYA BUKAN judul
     ⇒ kalau hakim bilang 'ragu'  = TANGKAP (bagus!)
     ⇒ kalau hakim bilang 'sepakat' = LOLOS (surveyor salah diteruskan)

  'asli' di kunci = memang judul
     ⇒ kalau hakim bilang 'sepakat' = SETUJU (bagus)
     ⇒ kalau hakim bilang 'ragu'  = RAGU PALSU (tidak merusak, cuma lewat)

CATATAN JUJUR: kunci (HASIL_UKUNCI.json) sendiri CACAT (≥11 salah kunci menurut
laporan #4 U4b). ⇒ angka di sini WAJIB dibaca sebagai 'lawan kunci', bukan
'kebenaran mutlak'. Laporkan apa adanya.
"""
from __future__ import annotations

import json
import sys
from collections import Counter

sys.path.insert(0, '/app')

import peta3_jev as P                                    # noqa: E402
from app import hakim_peta as H                          # noqa: E402

FID = 115
KUNCI = '/app/HASIL_UKUNCI.json'
KELUAR = '/app/HASIL_U_KUNCI.json'


def main():
    kunci = json.load(open(KUNCI))
    peta_kunci = {int(x['i']): x for x in kunci}
    print(f'kunci: {len(kunci)} baris · '
          f'asli={sum(1 for x in kunci if x["jenis"] == "asli")} · '
          f'palsu={sum(1 for x in kunci if x["jenis"] == "palsu")}')

    print('\nmenjalankan surveyor (peta3_jev) ...')
    r = P.petakan(FID, None, None, putaran=1)
    print(f'  label={len(r["label"])} baris · gagal={r["gagal"]} · '
          f'kand={r["kand_jml"]}')

    print('menjalankan HAKIM (T①) ...')
    lap = H.periksa_peta(r)
    bagian = {int(b['i']): b for b in lap['bagian']}
    print(f'  {lap["alasan"]}')

    # ── COCOKKAN ────────────────────────────────────────────────────────────
    hasil = []
    for i, k in peta_kunci.items():
        b = bagian.get(i)
        hasil.append({
            'i': i,
            'kunci': k['jenis'],
            'kunci_utama': k.get('utama'),
            'surveyor': (b or {}).get('label'),
            'hakim_status': (b or {}).get('status', 'TIDAK_ADA'),
            'p_info': (b or {}).get('p_info'),
            'judul': (b or {}).get('judul'),
        })

    def hit(jenis, status):
        return [x for x in hasil
                if x['kunci'] == jenis and x['hakim_status'] == status]

    palsu = [x for x in hasil if x['kunci'] == 'palsu']
    asli = [x for x in hasil if x['kunci'] == 'asli']

    print('\n' + '═' * 68)
    print('A. BARIS YANG KUNCI BILANG "PALSU" (surveyorLEWATKAN)')
    print('═' * 68)
    print(f'  total            : {len(palsu)}')
    for st in ('ragu', 'sepakat', 'curiga', 'belum', 'TIDAK_ADA'):
        n = len(hit('palsu', st))
        pct = 100.0 * n / len(palsu) if palsu else 0
        tanda = ''
        if st in ('ragu', 'curiga'):
            tanda = '  ← ✅ TANGKAP'
        elif st == 'sepakat':
            tanda = '  ← ❌ LOLOS (surveyor salah diteruskan)'
        print(f'  hakim {st:<9}: {n:>3} ({pct:5.1f}%){tanda}')

    print('\n' + '═' * 68)
    print('B. BARIS YANG KUNCI BILANG "ASLI" (memang judul)')
    print('═' * 68)
    print(f'  total            : {len(asli)}')
    for st in ('sepakat', 'ragu', 'curiga', 'belum', 'TIDAK_ADA'):
        n = len(hit('asli', st))
        pct = 100.0 * n / len(asli) if asli else 0
        tanda = ''
        if st == 'sepakat':
            tanda = '  ← ✅ SETUJU'
        elif st in ('ragu', 'curiga'):
            tanda = '  ← ⚠️ ragu palsu (tidak merusak)'
        print(f'  hakim {st:<9}: {n:>3} ({pct:5.1f}%){tanda}')

    # ── ANGKA KUNCI ─────────────────────────────────────────────────────────
    tangkap = len(hit('palsu', 'ragu')) + len(hit('palsu', 'curiga'))
    lolos = len(hit('palsu', 'sepakat'))
    print('\n' + '═' * 68)
    print('C. ANGKA PENENTU')
    print('═' * 68)
    print(f'  TANGKAP (palsu → ragu/curiga) : {tangkap}/{len(palsu)} '
          f'({100.0*tangkap/max(len(palsu),1):.1f}%)')
    print(f'  LOLOS   (palsu → sepakat)     : {lolos}/{len(palsu)} '
          f'({100.0*lolos/max(len(palsu),1):.1f}%)')
    n_asli_setuju = len(hit('asli', 'sepakat'))
    print(f'  ASLI SETUJU                   : {n_asli_setuju}/{len(asli)} '
          f'({100.0*n_asli_setuju/max(len(asli),1):.1f}%)')

    # ── banding: apa yang SURVEYOR bilang vs KUNCI ───────────────────────────
    tab = Counter((x['kunci'], x['surveyor']) for x in hasil)
    print('\n  Surveyor vs kunci (baris x kolom):')
    for (kn, sv), n in sorted(tab.items(), key=lambda t: -t[1])[:8]:
        print(f'    kunci={kn:<6} surveyor={str(sv):<9} : {n}')

    json.dump({'fid': FID, 'hasil': hasil,
               'angka': {'tangkap': tangkap, 'lolos': lolos,
                         'palsu_total': len(palsu),
                         'asli_setuju': n_asli_setuju,
                         'asli_total': len(asli)}},
              open(KELUAR, 'w'), ensure_ascii=False, indent=1)
    print(f'\n  → {KELUAR}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
