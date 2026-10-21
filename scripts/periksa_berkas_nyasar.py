"""periksa_berkas_nyasar.py — deteksi berkas KEMBAR/nyasar di container eduai-app.

KENAPA INI ADA (pelajaran 24Sep26, TERUKUR):
  Wulan berulang kali `docker cp app/state.py eduai-app:/app/state.py`
  sedangkan container menjalankan **/app/app/state.py** (paket `app`).
  Akibat menipu: perbaikan kode BENAR, tapi hasil fungsi TIDAK berubah —
  seolah logikanya salah. Wulan menuduh logikanya 2x sebelum sadar
  salah tempat salin.

CARA PAKAI:
    python3 scripts/periksa_berkas_nyasar.py            # periksa container hidup
    python3 scripts/periksa_berkas_nyasar.py --perbaiki # hapus berkas nyasar

LEWATI (exit 0) kalau:
  - container tidak jalan (bukan kegagalan, hanya tidak bisa diperiksa)
  - berkas nyasar tidak ditemukan (sehat)

GAGAL (exit 1) kalau ada berkas .py di /app/ yang seharusnya di /app/app/
atau sebaliknya (kembar dengan md5 BERBEDA = paling berbahaya).
"""
import subprocess
import sys

KONTAINER = 'eduai-app'
# berkas yang HANYA boleh ada di /app/app/ (modul paket)
MODUL = ('state.py', 'ai.py', 'brief.py', 'sorotan.py', 'konteks.py', 'parser.py',
         'config.py', 'main.py', 'models.py', 'jenis.py', 'proses.py')


def jalankan(cmd: str) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return (r.stdout or '') + (r.stderr or '')
    except Exception as e:                                    # noqa: BLE001
        return f'__GAGAL__ {e}'


def main() -> int:
    perbaiki = '--perbaiki' in sys.argv

    hidup = jalankan(f'docker inspect -f "{{{{.State.Running}}}}" {KONTAINER}').strip()
    if hidup != 'true':
        print(f'LEWAT: kontainer {KONTAINER} tidak jalan (bukan kegagalan).')
        return 0

    # 1) berkas modul yang NYASAR di /app/ (bukan /app/app/)
    nyasar = []
    for nama in MODUL:
        ada = jalankan(f'docker exec {KONTAINER} sh -c "test -f /app/{nama} && echo YA"')
        if 'YA' in ada:
            nyasar.append(nama)

    # 2) berkas kembar (ada di dua tempat) — hitung md5 dua-duanya
    kembar = {}
    for nama in MODUL:
        a = jalankan(f'docker exec {KONTAINER} md5sum /app/app/{nama}').split()
        b = jalankan(f'docker exec {KONTAINER} md5sum /app/{nama}').split()
        ma = a[0] if a and len(a[0]) == 32 else None
        mb = b[0] if b and len(b[0]) == 32 else None
        if ma and mb:
            kembar[nama] = (ma, mb)

    # 3) bukti berkas yang BENAR-BENAR dipakai (sumber tunggal kebenaran)
    print('=' * 78)
    print('PERIKSA BERKAS NYASAR / KEMBAR — kontainer', KONTAINER)
    print('=' * 78)

    gagal = 0
    print('\n1) Berkas yang benar-benar DIMUAT python (import nyata):')
    for nama, modul in (('state.py', 'app.state'), ('ai.py', 'app.ai'),
                        ('konteks.py', 'app.konteks'), ('parser.py', 'app.parser')):
        out = jalankan(
            f"docker exec -w /app {KONTAINER} python3 -c "
            f"\"import sys; sys.path.insert(0,'/app'); import {modul} as m; print(m.__file__)\"")
        jalur = out.strip().splitlines()[-1] if out.strip() else '?'
        tanda = '✅' if jalur.startswith('/app/app/') else '⚠️'
        print(f'   {tanda} {nama:<12} → {jalur}')
        if not jalur.startswith('/app/app/'):
            gagal += 1

    print('\n2) Berkas NYASAR di /app/ (seharusnya di /app/app/):')
    if not nyasar:
        print('   ✅ tidak ada — bersih')
    else:
        for nama in nyasar:
            print(f'   ❌ /app/{nama}  ← HARUS DIHAPUS (menipu: seolah kode baru)')
            gagal += 1

    print('\n3) Berkas KEMBAR tapi ISI BERBEDA (paling berbahaya):')
    beda = 0
    for nama, (ma, mb) in kembar.items():
        if ma != mb:
            print(f'   🔴 /app/{nama} ({mb[:8]}) ≠ /app/app/{nama} ({ma[:8]})')
            beda += 1
    if not beda:
        print('   ✅ tidak ada kembar berbeda' if kembar else '   ✅ tidak ada kembar')
    gagal += beda

    if perbaiki and nyasar:
        print('\n4) PERBAIKAN — menghapus berkas nyasar:')
        for nama in nyasar:
            jalankan(f'docker exec {KONTAINER} rm -f /app/{nama}')
            print(f'   dihapus: /app/{nama}')

    print('\n' + '=' * 78)
    if gagal:
        print(f'HASIL: {gagal} MASALAH — jangan percaya hasil uji sebelum bersih!')
        print('  Ingat: container pakai /app/app/… — salin ke sana.')
        print(f'  Perbaiki: python3 scripts/periksa_berkas_nyasar.py --perbaiki')
        return 1
    print('HASIL: BERSIH — berkas modul hanya di /app/app/, tidak ada nyasar/kembar.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
