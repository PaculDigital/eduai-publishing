"""U1 — UJI ADVERSARIAL: apakah surveyor & hakim BUTA DI TITIK YANG SAMA?

TUJUAN (nit Bos 09 Okt): bukan menyuntik kesalahan acak, tapi memakai KASUS NYATA
dari kegagalan yang SUDAH terjadi. Yang ditakuti = blind spot BERKORELASI
(keduanya lewatkan kasus yang sama) — itu cuma ketahuan lewat kasus nyata.

6 KASUS ADVERSARIAL (dari catatan terukur):
  A1 nomor halaman "30" jadi BAB palsu          (Wulandari-PDF)
  A2 nomor halaman "65" jadi BAB palsu          (Wulandari-PDF)
  A3 typo "BAB VI" (setelah BAB III) — harus SETIA (jangan diperbaiki!)
  A4 butir daftar "f. Pelayanan pelanggan" jadi sub-bab
  A5 L000356 "PENDAHULUAN" dianggap sub-bab     (Tesis 78)
  A6 L000608 "1. Apakah…" dianggap sub-bab      (Tesis 78)

CARA: tiap kasus dibentuk sebagai paket JENDELA BARIS (cara yang terbukti),
lalu ditanya ke Jev dengan pertanyaan SAMA yang dipakai surveyor & hakim.
Bandingkan: apakah surveyor (label) dan hakim (p) sama-sama salah di kasus itu?

JALAN: docker exec -w /app eduai-app python3 _u1_adversarial.py
"""
import json
import sys
import time

sys.path.insert(0, '/app')
from app import satpam

KASUS = [
    # (kode, judul, [baris_atas, baris_tengah, baris_bawah], harapan)
    ('A1', 'nomor halaman "30" jadi BAB palsu',
     ['Maka dari itu penulis menyimpulkan', '30', 'BAB III METODOLOGI'],
     'biasa'),
    ('A2', 'nomor halaman "65" jadi BAB palsu',
     ['sehingga dapat ditarik kesimpulan', '65', '4.1 Gambaran Umum'],
     'biasa'),
    ('A3', 'typo "BAB VI" (setelah BAB III) — harus SETIA',
     ['PENDAHULUAN', 'BAB VI HASIL PENELITIAN DAN PEMBAHASAN', '4.1 Gambaran Umum'],
     'bab'),
    ('A4', 'butir daftar "f. Pelayanan pelanggan" jadi sub-bab',
     ['e. Keterbatasan promosi offline.', 'f. Pelayanan pelanggan', '4.3.2.2 Faktor Eksternal'],
     'biasa'),
    ('A5', '"PENDAHULUAN" (judul bab) dianggap sub-bab',
     ['BAB I', 'PENDAHULUAN', 'Indonesia merupakan salah satu negara'],
     'bab'),
    ('A6', 'butir "1. Apakah…" dianggap sub-bab',
     ['1.2 Rumusan Masalah', '1. Apakah analisis SWOT dapat digunakan?', '2. Bagaimana hasilnya?'],
     'biasa'),
]

KRIT = {'bab': 'judul bab besar (BAB I, BAB II, …)',
        'subbab': 'judul sub-bab (mis. 1.1 Latar Belakang, 2.1.1 Pengertian)',
        'paragraf': 'kalimat/paragraf isi naskah',
        'biasa': 'bukan judul apa pun (fragmen, nomor halaman, butir daftar)'}
TANYA = {'c1': {'type': 'choice',
                'instructions': 'Baris `c1.tengah` ada di dalam naskah akademik. '
                                'Baris tengah ini perannya apa?',
                'criteria': dict(KRIT)}}
KUNCI_JUDUL = {'bab', 'subbab'}       # jawaban yang dianggap "dianggap judul"
HARAP_JUDUL = {'A3', 'A5'}            # kasus yang MEMANG judul

print('=' * 78)
print('U1 — UJI ADVERSARIAL (6 kasus NYATA dari kegagalan yang sudah terjadi)')
print('=' * 78)
hasil = []
for kode, judul, baris3, harap in KASUS:
    pak = {'sebelum': baris3[0], 'tengah': 'L000000| ' + baris3[1], 'sesudah': baris3[2]}
    bahan = json.dumps({'c1': pak}, ensure_ascii=False)
    pilih, confs = [], []
    for k in range(3):
        jw = satpam.tanya_bebas_mutu(bahan, TANYA) or {}
        blok = jw.get('c1') or {}
        v = blok.get('choice')
        if isinstance(v, dict):
            v = v.get('id') or v.get('label')
        c = blok.get('confidence')
        pilih.append(v)
        confs.append(float(c) if c is not None else None)
        time.sleep(0.4)
    vs = [x for x in pilih if x]
    dari = {}
    for x in vs:
        dari[x] = dari.get(x, 0) + 1
    utama = max(dari, key=dari.get) if dari else None
    cs = [c for c in confs if c is not None]
    conf = round(sum(cs) / len(cs), 2) if cs else None
    dianggap_judul = utama in KUNCI_JUDUL
    seharusnya_judul = kode in HARAP_JUDUL
    benar = (dianggap_judul == seharusnya_judul)
    hasil.append({'kode': kode, 'judul': judul, 'pilih': pilih, 'utama': utama,
                  'conf': conf, 'benar': benar,
                  'seharusnya_judul': seharusnya_judul, 'dianggap_judul': dianggap_judul})
    print('\n[%s] %s' % (kode, judul))
    print('    pilihan 3 putaran : %s' % pilih)
    print('    putusan           : %-8s (conf %s)' % (str(utama), str(conf)))
    print('    seharusnya        : %s' % ('JUDUL' if seharusnya_judul else 'BUKAN judul'))
    print('    ⇒ %s' % ('✅ BENAR' if benar else '❌ SALAH (BLIND SPOT)'))

benar = sum(1 for h in hasil if h['benar'])
print('\n' + '=' * 78)
print('RINGKASAN U1 — %d/%d BENAR' % (benar, len(hasil)))
print('=' * 78)
for h in hasil:
    tanda = '✅' if h['benar'] else '❌'
    print('  %s %s  %-40s → %s' % (tanda, h['kode'], h['judul'][:40], h['utama']))
gagal = [h for h in hasil if not h['benar']]
if gagal:
    print('\n🚨 BLIND SPOT DITEMUKAN di: %s' % ', '.join(h['kode'] for h in gagal))
    print('   ⇒ Jev salah di kasus yang MASIH ADA di naskah nyata.')
else:
    print('\n  ⇒ Jev TIDAK buta di 6 kasus nyata ini.')
json.dump(hasil, open('/app/HASIL_U1_ADVERSARIAL.json', 'w'), ensure_ascii=False, indent=1)
print('  ⇒ disimpan: /app/HASIL_U1_ADVERSARIAL.json')
