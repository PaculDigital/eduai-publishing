"""UJI MODUL pola_penulisan.py — jalur RESMI (peta3_jev.petakan = peta Jev).

Jalan: docker exec -w /app eduai-app python3 _uji_pola.py
"""
import json
import sys

sys.path.insert(0, '/app')
import peta3_jev as P
from app import pola_penulisan as pp


def jalankan(fid, nama):
    print('=' * 74)
    print('NASKAH %s (fid=%d)' % (nama, fid))
    print('=' * 74)
    r = P.petakan(fid, None, None, putaran=1)
    peta = {'baris': r['baris'], 'label': r['label'],
            'gabung': r.get('gabung'), 'sistematika': r.get('sistematika')}

    # pagar: jalur resmi (bukan skrip host sendiri)
    n_tab = sum(1 for b in r['baris'] if '<w:tab' in b)
    print('baris=%d · label=%d · label "bab"=%d  · <w:tab>=%d %s' % (
        len(r['baris']), len(r['label']),
        sum(1 for l in r['label'].values() if l == 'bab'),
        n_tab, '✅ BERSIH' if n_tab == 0 else '❌ BOCOR'))

    # ── §2 profil per BAB
    profil = pp.profil_bab(peta)
    print('\n--- PROFIL PER BAB (%d BAB) ---' % len(profil))
    for p in profil:
        print('BAB baris %d-%d  «%s»' % (p['mulai'], p['akhir'], p['judul'][:44]))
        print('    skema=%-11s gaya=%-10s butir=%-10s tabel=%-5s next=%s' % (
            p['skema_nomor'], p['gaya_judul'], p['butir'],
            p['ada_tabel'], p['nomor_terakhir']))

    # ── §3 pola per baris: hitung sebaran
    sebaran = {}
    for i, lab in r['label'].items():
        po = pp.pola_baris(lab, r['baris'][i])
        sebaran[po] = sebaran.get(po, 0) + 1
    print('\n--- SEBARAN POLA (%d baris berlabel) ---' % len(r['label']))
    for k in sorted(sebaran):
        print('   %-13s %4d' % (k, sebaran[k]))
    total = sum(sebaran.values())
    tj = sebaran.get('tidak_jelas', 0)
    print('   ⇒ tidak_jelas: %d (%.1f%%) %s' % (
        tj, 100 * tj / max(total, 1),
        '✅ wajar' if tj <= 0.20 * total else '⚠️ KEBANYAKAN — laporkan'))

    # ── §3b cek tetangga pada beberapa titik
    print('\n--- UJI POLA BERTETANGGA (10 titik contoh) ---')
    contoh = [i for i in sorted(r['label']) if r['label'][i] in ('biasa', 'paragraf')][:10]
    for i in contoh:
        pr = pp.pola_untuk_titik(peta, i)
        tt = pp.pola_tetangga(peta, i)
        print('   L%06d lab=%-8s sendiri=%-11s tetangga=%-11s → %s' % (
            i, r['label'][i], pr, tt, pp.pola_untuk_titik(peta, i)))
    return {'profil': profil, 'sebaran': sebaran, 'total': total}


hasil = {}
for fid, nama in [(81, 'ASIH'), (115, 'WULANDARI')]:
    try:
        hasil[nama] = jalankan(fid, nama)
    except Exception as e:
        print('GAGAL fid=%d: %r' % (fid, e))
print('\nSELESAI.')
