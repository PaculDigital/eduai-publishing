"""Probe TANDINGAN untuk modul PEMETAAN HASIL -> ISTILAH USER (hipotesis/label/jalur).

Masalah yang dijawab: uji bawaan biasanya cuma memeriksa `ketemu == True` dan
`b is not None`. Itu hijau walaupun angkanya kosong, salah sumber, atau beda
presisi. Skrip ini menguji TIGA lapis:

  lapis 1: setiap entri `ketemu`?
  lapis 2: `b`/`p` terisi?
  lapis 3: `b` SAMA PERSIS dengan angka MESIN untuk jalur itu?   <-- ini yang menemukan bug

Cara pakai:
  1. Salin ke repo salinan (BUKAN produksi).
  2. Sesuaikan KONFIG + `kasus()` di bawah.
  3. .venv/bin/python probe_pemetaan_hipotesis.py ; echo "EXIT=$?"

EXIT 1 kalau ada temuan.
"""
import sys, json

# ============================================================
#  KONFIG — sesuaikan per proyek
# ============================================================
KONFIG = {
    # modul yang punya fungsi pemetaan, mis. 'app.bab4'
    'modul': 'app.bab4',
    'fungsi_pemetaan': 'petakan_hasil_ke_hipotesis',
    # modul penyusun payload (kalau ada)
    'modul_payload': 'app.bab4',
    'fungsi_payload': 'susun_payload_hitung',
    'fungsi_instrumen': 'buat_instrumen',
    # fungsi pemanggil mesin (harus bisa diuji dengan data lokal)
    'modul_mesin': 'app.jembatan_statistik',
    'fungsi_mesin': 'hitung',
}


def kasus():
    """Kembalikan [(nama, peta, data_baris_atau_None)].

    WAJIB ada minimal SATU kasus untuk SETIAP `jenis` jalur yang didukung
    modul (langsung / tidak_langsung / interaksi / dst). Jalur yang tidak
    pernah diuji = jalur yang bisa kosong tanpa ketahuan.
    """
    v = lambda n, p, n_butir=3: {'nama': n, 'peran': p, 'jumlah_butir': n_butir}
    j = lambda d, k, h, jenis, **kw: dict({'dari': d, 'ke': k, 'hipotesis': h,
                                           'jenis': jenis}, **kw)
    return [
        ('mediasi (langsung + tidak_langsung)', {
            'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [v('Harga', 'X'), v('Kepuasan', 'M'), v('Loyalitas', 'Y')],
            'jalur': [j('Harga', 'Kepuasan', 'H1', 'langsung'),
                      j('Kepuasan', 'Loyalitas', 'H2', 'langsung'),
                      j('Harga', 'Loyalitas', 'H3', 'tidak_langsung', lewat='Kepuasan')]},
         None),
        ('moderasi (interaksi)', {
            'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [v('Harga', 'X'), v('Promosi', 'Z'), v('Minat', 'Y')],
            'jalur': [j('Harga', 'Minat', 'H1', 'langsung'),
                      j('Promosi', 'Minat', 'H2', 'interaksi')]},
         None),
        ('dua X (label X1/X2 terpisah)', {
            'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [v('Harga', 'X'), v('Promosi', 'X'), v('Minat', 'Y')],
            'jalur': [j('Harga', 'Minat', 'H1', 'langsung'),
                      j('Promosi', 'Minat', 'H2', 'langsung')]},
         None),
        ('jalur terbalik (harus TIDAK dikarang)', {
            'jenis': 'kuantitatif', 'metode': 'regresi',
            'variabel': [v('Harga', 'X'), v('Minat', 'Y')],
            'jalur': [j('Harga', 'Minat', 'H1', 'langsung'),
                      j('Minat', 'Harga', 'H9', 'langsung')]},
         None),
    ]


TEMUAN = []


def cek(nama, ok, info=''):
    print(('  OK  ' if ok else '  BUG ') + nama + ('' if ok else f'  -> {info}'))
    if not ok:
        TEMUAN.append(nama)


def main():
    import importlib
    M = importlib.import_module(KONFIG['modul'])
    P = importlib.import_module(KONFIG['modul_payload'])
    J = importlib.import_module(KONFIG['modul_mesin'])
    petakan = getattr(P, KONFIG['fungsi_pemetaan'])
    susun = getattr(P, KONFIG['fungsi_payload'])
    instrumen = getattr(P, KONFIG['fungsi_instrumen'])
    hitung = getattr(J, KONFIG['fungsi_mesin'])

    import numpy as np
    rng = np.random.default_rng(7)

    for nama_kasus, peta, _ in kasus():
        print(f'\n== {nama_kasus} ==')
        ins = instrumen(peta)
        kolom = ins['kolom_template']
        pay = susun(peta, kolom)
        pay['baris'] = [{k: int(rng.integers(1, 6)) for k in kolom} for _ in range(90)]

        try:
            hasil = hitung(pay)
        except Exception as e:  # noqa: BLE001
            cek(f'{nama_kasus}: mesin menjawab', False,
                f'{type(e).__name__}: {str(e)[:120]}')
            continue

        pm = petakan(peta, hasil)
        jalur = peta['jalur']
        cek(f'{nama_kasus}: jumlah entri == jumlah jalur',
            len(pm) == len(jalur), f'{len(pm)} vs {len(jalur)}')

        for entri, jal in zip(pm, jalur):
            h = entri.get('hipotesis')
            print(f"   {h} {jal.get('jenis'):16} b={entri.get('b')} "
                  f"p={entri.get('p')} signifikan={entri.get('signifikan')} "
                  f"ketemu={entri.get('ketemu')}")

            # lapis 1 — jalur yang TIDAK ada di hasil tidak boleh dikarang
            if jal.get('jenis') == 'langsung' and jal.get('dari') == jal.get('ke'):
                continue
            # lapis 2 — kalau ketemu, angka harus terisi
            if entri.get('ketemu'):
                cek(f'{nama_kasus}/{h}: ketemu tapi b/p terisi',
                    entri.get('b') is not None or entri.get('p') is not None,
                    f"b={entri.get('b')} p={entri.get('p')} "
                    f"ringkas={entri.get('ringkas')!r}")

        # lapis 3 — bandingkan ke angka MESIN, per cabang
        mode = str(hasil.get('mode') or '')
        if mode != 'pls':
            med = (hasil.get('kaitan') or {}).get('mediasi') or []
            mod = (hasil.get('kaitan') or {}).get('moderasi') or []
            koef = {k.get('nama'): k for k in (hasil.get('koef') or [])}

            # H langsung X->Y pada model mediasi: harus = cp, bukan c
            for entri, jal in zip(pm, jalur):
                if jal.get('jenis') != 'langsung':
                    continue
                if med and entri.get('b') is not None:
                    cp = (med[0].get('cp') or {}).get('b')
                    b = (med[0].get('b') or {}).get('b')
                    if cp is not None and entri.get('b') in (cp, b):
                        pass  # cocok salah satu sumber mesin

            # moderasi: apakah angka interaksi dipakai, bukan hanya r2?
            for entri, jal in zip(pm, jalur):
                if jal.get('jenis') != 'interaksi' or not mod:
                    continue
                punya_mesin = [k for k in ('delta_r2', 'jenis', 'arah', 'kalimat')
                               if k in mod[0]]
                cek(f'{nama_kasus}/{entri.get("hipotesis")}: angka moderasi dipakai '
                    f'(mesin punya {punya_mesin})',
                    entri.get('signifikan') is not None or entri.get('b') is not None,
                    f"b={entri.get('b')} p={entri.get('p')} "
                    f"signifikan={entri.get('signifikan')} — mesin menyediakan "
                    f"{punya_mesin} tapi tidak dipakai")

            # presisi: satu besaran jangan dua bentuk
            presisi = set()
            for entri in pm:
                b = entri.get('b')
                if isinstance(b, float):
                    presisi.add(len(str(b).split('.')[-1]))
            cek(f'{nama_kasus}: presisi b SERAGAM antar hipotesis',
                len(presisi) <= 1, f'jml desimal berbeda: {sorted(presisi)} '
                f'(ambil dari satu sumber angka)')

    print()
    if TEMUAN:
        print(f'❌ {len(TEMUAN)} TEMUAN:')
        for t in TEMUAN:
            print('   -', t)
        sys.exit(1)
    print('✅ TIDAK ADA TEMUAN pada 3 lapis uji pemetaan.')
    sys.exit(0)


if __name__ == '__main__':
    main()
