"""UJI GERBANG PERIKSA KODE — memastikan gerbangnya sendiri tidak buta.

Kenapa uji ini ada (16Sep26): gerbang `scripts/periksa_kode.sh` dibuat untuk
menangkap "undefined name" yang dulu lolos ke produksi. Tapi gerbang yang
TIDAK PERNAH DIUJI bisa buta (positif palsu / negatif palsu) — dan gerbang
buta LEBIH BERBAHAYA daripada tidak ada gerbang, karena membuat kita percaya.

Uji ini menyuntikkan bug yang PERSIS sama dengan insiden 16Sep26, lalu
memastikan gerbang MENOLAK, lalu memastikan gerbang LULUS saat kode sehat.
"""
import shutil
import subprocess
import sys
from pathlib import Path

PROYEK = Path('/opt/data/services/eduai-publishing')
GATE = PROYEK / 'scripts' / 'periksa_kode.sh'
AI = PROYEK / 'app' / 'ai.py'
KUNCI = 'from . import tulis_docx\nfrom datetime import datetime, timezone\n'

LULUS = GAGAL = 0


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {catatan}' if catatan else ''))


def jalankan_gate():
    r = subprocess.run(['bash', str(GATE)], cwd=str(PROYEK),
                       capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr


def main():
    print('=' * 62)
    print('UJI GERBANG periksa_kode.sh — gerbangnya sendiri tidak buta?')
    print('=' * 62)

    cadangan = AI.parent / '_ai_uji.py.bak'
    shutil.copy2(AI, cadangan)

    try:
        # ── 1. Kode SEHAT → gerbang HARUS lulus ──────────────────────────
        print('\n[1] Kode sehat → gerbang LULUS (tidak positif palsu)')
        kode, keluar = jalankan_gate()
        cek('exit 0', kode == 0, f'exit={kode}')
        cek('tidak ada ✗ menolak', '⛔ PERIKSA KODE GAGAL' not in keluar)
        cek('melaporkan LULUS', 'PERIKSA KODE LULUS' in keluar)

        # ── 2. Bug PERSIS insiden 16Sep26 → gerbang HARUS menolak ────────
        print('\n[2] Bug 16Sep26 disuntik → gerbang MENOLAK')
        teks = AI.read_text(encoding='utf-8')
        if KUNCI not in teks:
            cek('prasyarat: import kunci ada di app/ai.py', False,
                'baris import tidak ketemu — uji dilewati')
        else:
            AI.write_text(teks.replace(KUNCI, ''), encoding='utf-8')
            kode2, keluar2 = jalankan_gate()
            cek('exit != 0 (menolak deploy)', kode2 != 0, f'exit={kode2}')
            cek('menyebut "nama TAK TERDEFINISI"',
                'TAK TERDEFINISI' in keluar2)
            cek('MENUNJUK tulis_docx', 'undefined name' in keluar2 and
                'tulis_docx' in keluar2)
            cek('MENUNJUK datetime', 'datetime' in keluar2)
            cek('MENUNJUK timezone', 'timezone' in keluar2)
            cek('pesan jelas JANGAN DEPLOY', 'JANGAN DEPLOY' in keluar2)
            cek('memeriksa SOURCE, bukan container lama',
                'dari SOURCE' in keluar2 or 'PARSE' in keluar2)

        # ── 3. Galat sintaks → gerbang HARUS menolak ─────────────────────
        print('\n[3] Galat sintaks → gerbang MENOLAK')
        AI.write_text(teks.rstrip() + '\ndef ini_salah_sintaks(:\n',
                      encoding='utf-8')
        kode3, keluar3 = jalankan_gate()
        cek('exit != 0', kode3 != 0, f'exit={kode3}')
        cek('menyebut sintaks', 'SINTAKS' in keluar3.upper())

    finally:
        # SELALU pulihkan, apa pun yang terjadi (jangan tinggalkan repo rusak)
        shutil.copy2(cadangan, AI)
        cadangan.unlink(missing_ok=True)

    # ── 4. Pasca-pulih: gerbang HARUS lulus lagi ─────────────────────────
    print('\n[4] Setelah dipulihkan → gerbang LULUS lagi')
    kode4, keluar4 = jalankan_gate()
    cek('exit 0', kode4 == 0, f'exit={kode4}')
    cek('app/ai.py UTUH (import kunci ada)', KUNCI in AI.read_text(encoding='utf-8'))

    print('\n' + '=' * 62)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 62)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
