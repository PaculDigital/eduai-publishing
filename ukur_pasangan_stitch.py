"""Hitung pasangan stitch yang ditanya ke Jev — OFFLINE, nol panggilan.

Cara: stub modul berat (app.ai, app.models), ganti
satpam.tanya_bebas_mutu dengan pencatat yang mengembalikan jawaban
KOSONG (pasangan ambigu tidak tersambung), lalu jalankan
peta3_jev._susun_dari_bersih pada teks bersih naskah. Yang dicatat:
semua pertanyaan stitch (pass in-blok `_pecah_blok` + pass lintas
baris-kosong `_stitch_baris`) beserta kedua barisnya.

Tujuan: ukur berapa banyak pasangan yang kode TIDAK BISA putuskan
(`sambung_kode` -> None), dan pola teks apa yang mendominasi pasangan
itu — bahan untuk aturan deterministik baru.
"""
import json
import re
import sys
import types
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── stub modul berat SEBELUM impor peta3_jev ─────────────────────────────
_ai = types.ModuleType('app.ai')
_ai.SessionLocal = None
_ai._teks_dari_berkas = lambda *a, **k: ''
_ai.UPLOAD_DIR = Path('/tmp')
sys.modules['app.ai'] = _ai
_models = types.ModuleType('app.models')
_models.FileBerkas = object
sys.modules['app.models'] = _models

import app.satpam as _satpam  # noqa: E402
import app.sambung_kode as _sk  # noqa: E402

REKAM = []  # (asal, bahan, pertanyaan)


def _pencatat(bahan, pertanyaan, *a, **k):
    REKAM.append((bahan, dict(pertanyaan or {})))
    return {'__rekam__': {}}  # truthy supaya _tanya_jev_kuat tidak ulang


_satpam.tanya_bebas_mutu = _pencatat

import peta3_jev as P  # noqa: E402


def _ciri(a, b):
    """Ciri teks pasangan (a, b) untuk pengelompokan pola."""
    ciri = []
    if b[:1].islower():
        ciri.append('B-huruf-kecil')
    if b[:1].isupper():
        ciri.append('B-huruf-besar')
    if re.match(r'^\d', b):
        ciri.append('B-angka')
    if b.startswith('('):
        ciri.append('B-kurung')
    if a.endswith((':', ';')):
        ciri.append('A-titik-dua/titik-koma')
    if a.endswith((',', '-', '(')):
        ciri.append('A-koma/strip/kurung')
    if re.search(r'[.!?]["\')\]]*\s*$', a):
        ciri.append('A-akhir-kalimat')
    if len(a) <= 2:
        ciri.append('A-pendek<=2')
    if len(b) <= 2:
        ciri.append('B-pendek<=2')
    return ciri or ['(tanpa-ciri)']


def main():
    for fid in ('112', '115'):
        teks = (ROOT / 'ground_truth' / '_teks'
                / ('teks_bersih_%s.txt' % fid)).read_text(encoding='utf-8')
        REKAM.clear()
        d = P._susun_dari_bersih(teks)
        # ── pisahkan pertanyaan in-blok vs lintas-kosong dari bentuk soal:
        #    in-blok: "Does line Lxxxx pick up mid-sentence, continuing a
        #    sentence left unfinished at the end of line Lxxxx?"
        #    lintas-kosong: bentuk yang sama (instruksi identik) — bedakan
        #    dari bahan: in-blok state berisi "Lxxxx| teks" per baris asli,
        #    lintas-kosong state berisi "Lxxxx| teks" per BLOK. Keduanya
        #    tercatat di REKAM sesuai urutan panggil: _pecah_blok dulu,
        #    lalu _stitch_baris.
        pasang = []  # (a_teks, b_teks, instruksi)
        for bahan, tanya in REKAM:
            for _nama, q in (tanya or {}).items():
                ins = (q or {}).get('instructions') or ''
                m = re.findall(r'Line L\d+: "(.*?)"', ins)
                if len(m) == 2:
                    pasang.append((m[0], m[1], ins))
                elif (q or {}).get('type') == 'noul':
                    pasang.append(('?', '?', ins))
        print('=== fid=%s: pertanyaan stitch tercatat: %d (panggilan: %d)'
              % (fid, len(pasang), len(REKAM)))
        # ── simpan pasangan untuk analisis lanjut (offline, tanpa Jev) ──
        out = ROOT / ('pasangan_stitch_%s.json' % fid)
        out.write_text(json.dumps(
            [{'a': a, 'b': b} for a, b, _ in pasang],
            ensure_ascii=False, indent=1), encoding='utf-8')
        print('    pasangan disimpan:', out)
        print('    kandidat hasil susun (tanpa sambung Jev): %d, '
              'buang: %d, gabung: %d'
              % (len(d['kand']), len(d['buang']), len(d['gabung'])))
        # ── verifikasi: semua pasangan tercatat memang None di sambung_kode
        verdict = Counter()
        for a, b, _ in pasang:
            verdict[_sk.sambung_kode(a, b)] += 1
        print('    verdict sambung_kode atas pasangan tercatat:', dict(verdict))
        # ── pola ciri pasangan
        ciri = Counter()
        contoh = {}
        for a, b, _ in pasang:
            for c in _ciri(a, b):
                ciri[c] += 1
                contoh.setdefault(c, (a, b))
        for c, n in ciri.most_common():
            print('    %-24s : %4d  | mis. A=%r B=%r'
                  % (c, n, contoh[c][0][:60], contoh[c][1][:60]))
        # ── pasangan yang B-nya huruf kecil (kandidat aturan JOIN aman)
        kecil = [(a, b) for a, b, _ in pasang if b[:1].islower()]
        print('    B-huruf-kecil total: %d (%.1f%% dari pasangan)'
              % (len(kecil), 100.0 * len(kecil) / max(1, len(pasang))))
        for a, b in kecil[:8]:
            print('      A=%r  B=%r' % (a[:70], b[:70]))


if __name__ == '__main__':
    main()
