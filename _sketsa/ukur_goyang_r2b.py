"""Ukur ronde 2 bagian 2 (offline, 0 Jev).

A. Pasangan stitch B-diawali-dash / butir / A-angka-telanjang:
   distribusi p Jev + laju gabung di run opt3 tersimpan.
B. Arah benar flip label antar-run menurut label kebenaran dasar
   (cocokkan teks kandidat ke TSV lewat ukur_skor_teks).
C. Garis flip paragraf<->biasa: ciri teks (awal kalimat baku?
   panjang? berakhir titik?) vs label benar.
"""
import json
import re
import sys
from collections import Counter, defaultdict

ROOT = '/home/hatch/workspace/jev-v5'
sys.path.insert(0, ROOT)
from ukur_skor_teks import muat_tsv, cari_indeks, norm  # noqa: E402

d = json.load(open(ROOT + '/hasil_sesudah_opt_114.json', encoding='utf-8'))
POLA_AKHIR = re.compile(r'[.!?:;\u2026]["\')\]]*$')


def ambang(a):
    return 0.5 if POLA_AKHIR.search((a or '').strip()) else 0.2


def ekstrak_stitch(run):
    out = {}
    for e in run.get('stitch_log') or []:
        for qid, q in (e.get('pertanyaan') or {}).items():
            m = re.search(r'Line L\d+: "(.*)"\. Line L\d+: "(.*)"\.$',
                          q.get('instructions') or '', re.S)
            if not m:
                continue
            j = (e.get('jawaban') or {}).get(qid) or {}
            p = j.get('noul')
            if isinstance(p, (int, float)):
                out[(norm(m.group(1)), norm(m.group(2)))] = float(p)
    return out


print('=== A. POLA STITCH KHUSUS (run1+run2 digabung per fid) ===')
for fid in ('112', '115'):
    s = {}
    for r in d['run'][fid]:
        s.update(ekstrak_stitch(r))
    def kelompok(nama, pred):
        ps = [(k, p) for k, p in s.items() if pred(k)]
        gabung = sum(1 for (a, b), p in ps if p >= ambang(a))
        ps_sorted = sorted(p for _, p in ps)
        med = ps_sorted[len(ps_sorted)//2] if ps_sorted else None
        print('  fid=%s %-28s n=%3d gabung-Jev=%3d (%.0f%%) p-med=%.2f p-min=%.2f p-maks=%.2f'
              % (fid, nama, len(ps), gabung,
                 100.0 * gabung / max(1, len(ps)), med if med is not None else -1,
                 min(ps_sorted) if ps_sorted else -1,
                 max(ps_sorted) if ps_sorted else -1))
        return ps
    print(' fid=%s' % fid)
    kelompok('B diawali "- "', lambda k: k[1].startswith('- '))
    kelompok('B diawali "-"/"–"/"•"', lambda k: k[1][:1] in ('-', '–', '•'))
    kelompok('B butir a)/1. dst', lambda k: bool(re.match(r'^[a-z0-9]{1,3}[.)]\s', k[1])))
    kelompok('A angka telanjang', lambda k: bool(re.match(r'^\d{1,3}$', k[0])))
    kelompok('A angka telanjang + B pendek',
             lambda k: bool(re.match(r'^\d{1,3}$', k[0])) and len(k[1].split()) <= 4)
    kelompok('B kurung-buka', lambda k: k[1].startswith('('))
    kelompok('B 1-2 kata', lambda k: len(k[1].split()) <= 2)
    kelompok('B nama+koma', lambda k: bool(re.match(r'^[A-Z][a-z]+,', k[1])))

print()
print('=== B. ARAH BENAR FLIP (TSV) ===')
for fid in ('81', '112', '115'):
    rows = muat_tsv(fid)
    benar = {}
    for row in rows:
        benar.setdefault(norm(row['teks']), row['benar'])
    r1, r2 = d['run'][fid]
    def labmap(r):
        m = {}
        for i, t in r['kand']:
            m.setdefault(norm(t), r['label'].get(str(i)))
        return m
    l1, l2 = labmap(r1), labmap(r2)
    arah = Counter()
    contoh = defaultdict(list)
    for t in set(l1) & set(l2):
        if l1[t] != l2[t] and t in benar:
            if l1[t] == benar[t]:
                arah['run1-benar'] += 1
            elif l2[t] == benar[t]:
                arah['run2-benar'] += 1
            else:
                arah['keduanya-salah'] += 1
                if len(contoh['keduanya-salah']) < 5:
                    contoh['keduanya-salah'].append(
                        (benar[t], l1[t], l2[t], t[:60]))
    print('fid=%s flip-dengan-label-benar: %s' % (fid, dict(arah)))
    for c in contoh['keduanya-salah']:
        print('   benar=%s run1=%s run2=%s %r' % c)

print()
print('=== C. CIRI GARIS FLIP paragraf<->biasa (112+115, vs label benar) ===')
for fid in ('112', '115'):
    rows = muat_tsv(fid)
    benar = {}
    for row in rows:
        benar.setdefault(norm(row['teks']), row['benar'])
    r1, r2 = d['run'][fid]
    def labmap(r):
        m = {}
        for i, t in r['kand']:
            m.setdefault(norm(t), r['label'].get(str(i)))
        return m
    l1, l2 = labmap(r1), labmap(r2)
    ciri = Counter()
    for t in set(l1) & set(l2):
        if {l1[t], l2[t]} == {'paragraf', 'biasa'} and t in benar:
            b = benar[t]
            panjang = len(t.split())
            awal = t[:1]
            akhir_titik = t.endswith('.')
            mulai_kalimat_baku = bool(re.match(
                r'^(Penelitian ini|Dalam penelitian|Adapun|Pada bab|Bab ini|'
                r'Menurut|Berdasarkan|Hasil|Data|Metode|Teknik|Analisis)',
                t))
            ciri[('benar=' + b,
                  'panjang<=8' if panjang <= 8 else 'panjang>8',
                  'akhir-titik' if akhir_titik else 'tanpa-titik',
                  'awal-baku' if mulai_kalimat_baku else 'awal-lain')] += 1
    for k, c in sorted(ciri.items(), key=lambda kv: -kv[1]):
        print(' fid=%s %s : %d' % (fid, k, c))
