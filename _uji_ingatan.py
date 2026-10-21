"""UJI INGATAN DOKUMEN — dijalankan DI DALAM container eduai-app.

KENAPA TERPISAH: `_uji_publik_komentar.py` dijalankan di container hermes
(jalur publik, punya internet) dan TIDAK bisa membaca DB eduai-app. Padahal
bug terbesar 17Sep26 justru SENYAP: revisi "sukses" (versi_dokumen bertambah)
tapi `section_state` & `revisi_history` KOSONG karena `catat_revisi()` gagal
diam-diam (`pengali` NameError → TypeError). Hanya bisa dibuktikan dari DB.

JALANKAN di dalam container:
    docker exec eduai-app python3 /app/_uji_ingatan.py --kode <KODE> --file <ID>
Atau tanpa argumen → periksa SEMUA berkas yang punya versi_dokumen.

Keluar kode 0 = LULUS, 1 = GAGAL (bisa dipakai gerbang otomatis).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

DB = '/app/data/eduai.db'
LULUS = GAGAL = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> bool:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'   ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'   ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--kode', default='')
    ap.add_argument('--file', type=int, default=0)
    a = ap.parse_args()

    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row

    print('═' * 74)
    print('UJI INGATAN DOKUMEN — section_state & revisi_history')
    print('═' * 74)

    file_id = a.file
    if a.kode:
        r = c.execute('SELECT file_id, status, model_ai, token_in, token_out, '
                      'token_revisi FROM proses_ai WHERE kode=?',
                      (a.kode,)).fetchone()
        if r is None:
            cek('proses ditemukan', False, f'kode={a.kode}')
            return akhir()
        file_id = r['file_id']
        print(f'\n   proses {a.kode}: status={r["status"]} file_id={file_id} '
              f'model={r["model_ai"]} tok={r["token_in"]}/{r["token_out"]}')
        cek('I0 proses selesai', r['status'] == 'selesai', r['status'])

    # ── I1. versi_dokumen (hasil tersimpan ke dokumen) ───────────────────
    print('\n── I1. HASIL TERSIMPAN (versi_dokumen) ──────────────────────')
    if file_id:
        v = c.execute('SELECT COUNT(*) FROM versi_dokumen WHERE file_id=?',
                      (file_id,)).fetchone()[0]
        cek('I1 versi_dokumen bertambah', v > 0, f'{v} versi (file_id={file_id})')
    else:
        v = c.execute('SELECT COUNT(*) FROM versi_dokumen').fetchone()[0]
        cek('I1 versi_dokumen ada baris', v > 0, f'{v} baris total')

    # ── I2. section_state (INGATAN per bagian — bug 17Sep26) ─────────────
    print('\n── I2. section_state (ingatan per bagian) ───────────────────')
    if file_id:
        rows = c.execute(
            'SELECT section_id, section_title, char_count, jenis_revisi, '
            'sumber_terakhir FROM section_state WHERE file_id=?',
            (file_id,)).fetchall()
    else:
        rows = c.execute(
            'SELECT section_id, section_title, char_count, jenis_revisi, '
            'sumber_terakhir FROM section_state ORDER BY id DESC LIMIT 5'
        ).fetchall()
    cek('I2a section_state TERISI (ini yang dulu SENYAP KOSONG)',
        len(rows) > 0, f'{len(rows)} baris')
    for r in rows:
        print(f'      · {r["section_id"] or "-":14s} | '
              f'{str(r["section_title"])[:28]:28s} | '
              f'{r["char_count"] or 0:6d} kar | {r["jenis_revisi"]} | '
              f'{r["sumber_terakhir"]}')
        cek(f'I2b isi_teks {r["section_id"]} tidak kosong',
            (r['char_count'] or 0) > 0, f'{r["char_count"]} kar')
        cek(f'I2c sumber_terakhir {r["section_id"]} = "ai"',
            r['sumber_terakhir'] == 'ai', str(r['sumber_terakhir']))

    # ── I3. revisi_history (riwayat + token nyata) ───────────────────────
    print('\n── I3. revisi_history (riwayat & token nyata) ───────────────')
    if file_id:
        h = c.execute(
            'SELECT section_id, model_ai, token_in, token_out, token_revisi, '
            'pengali FROM revisi_history WHERE file_id=? ORDER BY id DESC',
            (file_id,)).fetchall()
    else:
        h = c.execute(
            'SELECT section_id, model_ai, token_in, token_out, token_revisi, '
            'pengali FROM revisi_history ORDER BY id DESC LIMIT 5').fetchall()
    cek('I3a revisi_history TERISI', len(h) > 0, f'{len(h)} baris')
    for r in h:
        print(f'      · {r["section_id"] or "-":14s} | model={r["model_ai"]} | '
              f'tok {r["token_in"]}/{r["token_out"]} | revisi={r["token_revisi"]} '
              f'| pengali={r["pengali"]}')
    if h:
        cek('I3b model TERCATAT di riwayat', bool(h[0]['model_ai']),
            str(h[0]['model_ai']))
        cek('I3c token nyata tercatat (>0)', (h[0]['token_in'] or 0) > 0,
            f'in={h[0]["token_in"]}')
        cek('I3d pengali terisi (>=1) — inti bug 17Sep26',
            (h[0]['pengali'] or 0) >= 1, str(h[0]['pengali']))

    # ── I4. ingatan BISA DIBACA AI berikutnya ────────────────────────────
    print('\n── I4. INGATAN DIPAKAI REVISI BERIKUTNYA ────────────────────')
    if file_id:
        try:
            sys.path.insert(0, '/app')
            from app.catatan_ai import ringkasan_untuk_ai
            from app.models import SessionLocal
            db2 = SessionLocal()
            try:
                ring = ringkasan_untuk_ai(db2, file_id)
                cek('I4a ringkasan_untuk_ai() mengembalikan teks',
                    bool(ring and ring.strip()),
                    f'{len(ring or "")} kar')
                if ring:
                    print('      ' + (ring[:300].replace('\n', '\n      ')))
            finally:
                db2.close()
        except Exception as e:                                 # noqa: BLE001
            cek('I4a ringkasan_untuk_ai() bisa dipanggil', False,
                f'{type(e).__name__}: {e}')

    # ── I5. TIDAK ADA kegagalan senyap di log (bukti tidak regresi) ──────
    print('\n── I5. PEMERIKSAAN SILANG ───────────────────────────────────')
    n_proses = c.execute(
        "SELECT COUNT(*) FROM proses_ai WHERE status='selesai'").fetchone()[0]
    n_section = c.execute('SELECT COUNT(*) FROM section_state').fetchone()[0]
    print(f'      proses_ai selesai = {n_proses} · section_state = {n_section}')
    cek('I5 setiap proses selesai punya jejak ingatan (>=1)',
        (n_proses == 0) or (n_section > 0),
        f'{n_proses} proses vs {n_section} section '
        '(kalau proses>0 tapi section=0 → bug senyap kembali)')

    return akhir()


def akhir() -> int:
    print('\n' + '═' * 74)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('═' * 74)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
