#!/usr/bin/env python3
"""UJI 3 PERAN JEV — VERSI BENAR (07 Okt 2026). Rujukan tetap.

⚠️ INI VERSI YANG BENAR. Versi salah Wulan (criteria STRING/noul+criteria,
menuduh "Jev tidak stabil", mengubah ambang) sudah dipindah ke
`_arsip/pre-uji-jev-salah-07okt26/` — JANGAN dipakai.

ATURAN SKEMA (terukur dari galat Zod asli `/systemone`, 07 Okt 2026):
  · noul   → ⛔ TIDAK BOLEH ada `criteria`
  · choice → `criteria` = OBJEK {nama_opsi: deskripsi}
  · score  → `criteria` = ARRAY [tingkat0, tingkat1, …]  (2–10 tingkat)

ATURAN RESMI jev-1.13 yang dipatuhi:
  #1 Literal  → tulis kondisi PERSIS (jangan "kira-kira")
  #2 Hitungan → JANGAN minta Jev menghitung
  #5 Context  → state DIKURASI, jangan seluruh naskah
  + noul tanpa confidence → pakai |2p−1|

WAJIB dari DALAM container. Jalur: lewat jembatan (SATPAM), bukan JEV/*.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

JEMBATAN = os.getenv('JEMBATAN_JEV', 'http://172.17.0.1:8130/v1/chat/completions')
MODEL = 'SATPAM/typesafe/jev-1.13'
ASIH = Path('/app/uploads/8/3dbd8babe72c6098.docx')
AMBANG_ADA = 0.50       # di bawah ini → JANGAN klaim "ada"
AMBANG_YAKIN = 0.80     # keyakinan di bawah ini → "perlu diperiksa manusia"


def bersih(maks: int = 9000) -> str:
    """Potongan naskah BERSIH (buang sampah XML + karakter aneh)."""
    z = zipfile.ZipFile(str(ASIH))
    xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    t = re.sub(r'<[^>]+>', ' ', xml)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n', t)
    t = ''.join(c for c in t if c.isprintable() or c in '\n ')
    return t.strip()[:maks]


#  ── 3 PERAN, skema BENAR ────────────────────────────────────────────────
Q = {
    #  P1 · CHOICE → jenis naskah (criteria = OBJEK)
    'jenis_naskah': {
        'type': 'choice',
        'instructions': 'Tentukan jenis penelitian naskah akademik ini.',
        'criteria': {
            'kuantitatif': ('Memakai angka dan uji statistik: hipotesis, sampel, '
                            'populasi, kuesioner, regresi, uji-t, SPSS, signifikan.'),
            'kualitatif': ('Memakai wawancara/observasi mendalam: informan, '
                           'triangulasi, reduksi data, koding, tema, fenomena.'),
            'literatur_review': ('Menelaah pustaka/karya lain: tinjauan sistematis, '
                                 'analisis artikel, sintesis temuan, tanpa data lapangan.'),
            'lainnya': 'Tidak sesuai ketiga opsi di atas atau tidak dapat ditentukan.',
        },
    },
    #  P2 · NOUL → keberadaan bagian (⛔ TANPA criteria)
    'ada_abstrak': {
        'type': 'noul',
        'instructions': ('Apakah ada bagian yang BERJUDUL "ABSTRAK" atau '
                         '"ABSTRACT" di dalam naskah ini?'),
    },
    'ada_daftar_pustaka': {
        'type': 'noul',
        'instructions': ('Apakah ada bagian DAFTAR PUSTAKA atau DAFTAR RUJUKAN '
                         'yang memuat kumpulan rujukan buku/artikel?'),
    },
    'ada_metode': {
        'type': 'noul',
        'instructions': ('Apakah ada bagian yang MENGURAIKAN METODE penelitian '
                         '(jenis penelitian, populasi, sampel, teknik analisis)?'),
    },
    'ada_pembahasan': {
        'type': 'noul',
        'instructions': ('Apakah ada bagian PEMBAHASAN yang menafsirkan hasil '
                         'penelitian ini?'),
    },
    #  P3 · SCORE → taraf kelengkapan struktur (criteria = ARRAY)
    'kelengkapan_imrad': {
        'type': 'score',
        'instructions': ('Nilai kelengkapan STRUKTUR naskah sebagai calon artikel '
                         'jurnal IMRAD. Jangan menilai mutu tulisan — hanya '
                         'keberadaan bagian.'),
        'criteria': [
            'Nyaris tak ada bagian artikel (hanya latar belakang).',
            'Ada 1-2 bagian (mis. pendahuluan + metode), sisanya belum.',
            'Ada 3-4 bagian (pendahuluan, metode, hasil, pembahasan sebagian).',
            'Ada 5 bagian lengkap, tetapi abstrak atau pustaka belum rapi.',
            'Semua bagian lengkap: abstrak, pendahuluan, metode, hasil, '
            'pembahasan, kesimpulan, daftar pustaka.',
        ],
    },
}


def tanya(state: str, n_cuba: int = 3) -> dict | None:
    body = {'model': MODEL,
            'messages': [{'role': 'user',
                          'content': json.dumps({'state': state, 'questions': Q})}]}
    for cuba in range(n_cuba):
        req = urllib.request.Request(
            JEMBATAN, data=json.dumps(body).encode(),
            headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
            isi = (d.get('choices') or [{}])[0].get('message', {}).get('content', '')
            return json.loads(isi) if isi else None
        except urllib.error.HTTPError as e:
            if cuba < n_cuba - 1 and e.code in (400, 502, 503, 504):
                time.sleep(4)
                continue
            print(f'    [galat] HTTP {e.code}')
            return None
        except Exception as e:                                    # noqa: BLE001
            if cuba < n_cuba - 1:
                time.sleep(4)
                continue
            print(f'    [galat] {type(e).__name__}: {e}')
            return None
    return None


def main() -> int:
    print('══ UJI 3 PERAN JEV — VERSI BENAR ══')
    print(f'Jalur: {JEMBATAN}  (jembatan → /systemone)\n')
    if not ASIH.exists():
        print(f'✗ naskah tidak ada: {ASIH}')
        return 1
    state = bersih()
    print(f'state dikurasi = {len(state):,} kar  ·  5 pertanyaan 1 panggilan\n')

    t0 = time.time()
    jw = tanya(state)
    dt = time.time() - t0
    if not jw:
        print('✗ Jev tidak menjawab')
        return 1
    print(f'⏱  {dt:.1f} detik\n')

    j = jw.get('jenis_naskah') or {}
    print(f'P1 JENIS      : {j.get("choice")}  (keyakinan {j.get("confidence")})')
    print(f'                sebaran={j.get("probabilities")}')
    for k in ('ada_abstrak', 'ada_daftar_pustaka', 'ada_metode', 'ada_pembahasan'):
        v = (jw.get(k) or {}).get('noul')
        yakin = abs(2 * (v or 0) - 1)
        tanda = '✅ ADA' if (v or 0) >= AMBANG_ADA else '❌ TIDAK ADA'
        if yakin < AMBANG_YAKIN:
            tanda += '  ⚠️ RAGU — perlu diperiksa manusia'
        print(f'P2 {k:17}: {v}  (yakin {yakin:.2f})  {tanda}')
    s = jw.get('kelengkapan_imrad') or {}
    print(f'P3 IMRAD      : skor {s.get("score")}  conf {s.get("confidence")}')
    if (s.get('confidence') or 0) < AMBANG_YAKIN:
        print('                ⚠️ RAGU — jangan klaim, tanya manusia')
    print(f'                legend={s.get("legend")}')

    #  ── VERIFIKASI KE SUMBER ──
    z = zipfile.ZipFile(str(ASIH))
    teks = re.sub(r'<[^>]+>', ' ', z.read('word/document.xml').decode('utf-8', 'ignore'))
    print('\n══ VERIFIKASI KE SUMBER ══')
    for n, pola in (('abstrak', r'ABSTRAK|ABSTRACT'),
                    ('daftar pustaka', r'DAFTAR\s+PUSTAKA|DAFTAR\s+RUJUKAN'),
                    ('metode', r'\bMETODE\b|\bMETODOLOGI\b'),
                    ('pembahasan', r'PEMBAHASAN')):
        print(f'  {"ADA" if re.search(pola, teks, re.I) else "TIDAK ADA":10} {n}')

    Path('/tmp/uji_3peran_benar.json').write_text(
        json.dumps(jw, ensure_ascii=False, indent=2))
    print('\n(bukti: /tmp/uji_3peran_benar.json)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
