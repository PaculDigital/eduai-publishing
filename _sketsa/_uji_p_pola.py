"""UJI P — APAKAH JEV BISA KENALI POLA PENULISAN TETANGGA?

TUJUAN (perintah Bos 09 Okt): sebelum merancang "pola penulisan AI", UKUR dulu:
apakah Jev sanggup mengenali BENTUK PENULISAN sebuah bagian
(paragraf / paragraf+butir / butir / judul+isi / tabel) dengan akurat?

Kalau TIDAK sanggup → seluruh rencana "AI ikuti pola tetangga" RUNTUH.
Maka uji ini WAJIB jalan sebelum koding apa pun.

CARA:
1. Ambil bagian-bagian NYATA dari naskah Tesis 78 (fid=78) + Asih (fid=81)
   yang bentuknya SUDAH kita ketahui dari mata (kunci).
2. Kirim JENDELA 3 BARIS ke Jev (cara yang sudah terbukti), tanya 1 pertanyaan
   tipe CHOICE 5 pilihan: paragraf / paragraf_butir / butir / judul_isi / tabel.
3. Bandingkan dengan kunci mata → hitung akurasi.

JALAN: docker exec -w /app eduai-app python3 _uji_p_pola.py
"""
import json
import sys
import time

sys.path.insert(0, '/app')
import peta3_jev as P
from app import satpam

# ── 5 pola yang dinilai
POLA = {
    'paragraf': 'paragraf mengalir saja, tanpa daftar/butir',
    'paragraf_butir': 'ada kalimat pengantar lalu daftar butir (a./1./-) di dalamnya',
    'butir': 'daftar butir saja (a./b./1./2./-), tanpa kalimat pengantar',
    'judul_isi': 'judul bagian (mis. 2.1 Landasan Teori) diikuti isi di bawahnya',
    'tabel': 'isi/baris tabel (baris pendek berderet, judul kolom)',
}
TANYA = {'c1': {'type': 'choice',
                'instructions': 'Baris `c1.tengah` ada di dalam naskah akademik. '
                                'BENTUK PENULISAN baris tengah ini apa?',
                'criteria': dict(POLA)}}

# ── KUNCI MATA: bagian nyata yang bentuknya sudah diketahui
#   (dari peta fid=78 & fid=81 + pembacaan naskah)
KASUS = [
    # (fid, baris, kunci_pola, keterangan)
    (78, 358, 'judul_isi', '1.2 Rumusan Masalah (judul sub-bab)'),
    (78, 606, 'judul_isi', '1.3 Tujuan Penelitian (judul sub-bab)'),
    (78, 620, 'judul_isi', '1.4 Manfaat (judul sub-bab)'),
    (78, 638, 'judul_isi', 'sub-bab berikutnya'),
    (115, 2, 'judul_isi', '1.1 LATAR BELAKANG (judul sub-bab)'),
    (115, 877, 'paragraf_butir', '4. Threats (Ancaman) — butir dlm ancaman'),
    (115, 3486, 'tabel', '5 Adyatma — baris tabel'),
    (115, 7997, 'tabel', '6 Sidang Skripsi — baris tabel langkah'),
    (115, 8019, 'tabel', '4 Mbak April Konsumen — baris tabel informan'),
    (115, 555, 'paragraf', 'paragraf isi biasa'),
    (115, 4000, 'paragraf', 'paragraf isi biasa (tengah)'),
    (115, 6000, 'paragraf', 'paragraf isi biasa (jauh)'),
]

# ambil baris dari tiap naskah (pakai jalur RESMI peta3_jev)
BARIS_CACHE = {}
for fid in {k[0] for k in KASUS}:
    r = P.petakan(fid, None, None, putaran=1)
    BARIS_CACHE[fid] = r['baris']
    print('naskah fid=%d → %d baris' % (fid, len(r['baris'])))

print('=' * 78)
print('UJI P — JEV KENALI POLA PENULISAN? (%d kasus)' % len(KASUS))
print('=' * 78)

hasil = []
for fid, i, kunci, ket in KASUS:
    baris = BARIS_CACHE[fid]
    if i >= len(baris):
        print('L%06d (fid=%d) LEWAT — baris tak ada' % (i, fid))
        continue
    pak = {'sebelum': ' '.join(baris[i - 1].split())[:70],
           'tengah': ('L%06d| ' % i) + ' '.join(baris[i].split())[:70],
           'sesudah': ' '.join(baris[i + 1].split())[:70]}
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
    utama = max(set(vs), key=vs.count) if vs else None
    cc = [c for c in confs if c is not None]
    conf = round(sum(cc) / len(cc), 2) if cc else None
    benar = (utama == kunci)
    hasil.append({'fid': fid, 'i': i, 'kunci': kunci, 'pilih': pilih,
                  'utama': utama, 'conf': conf, 'benar': benar,
                  'keterangan': ket})
    print('\n[fid=%d L%06d] %s' % (fid, i, ket))
    print('   3 putaran : %s' % pilih)
    print('   putusan   : %-14s (conf %s)' % (str(utama), str(conf)))
    print('   kunci mata: %-14s → %s' % (kunci, '✅ BENAR' if benar else '❌ SALAH'))

benar = sum(1 for h in hasil if h['benar'])
print('\n' + '=' * 78)
print('RINGKASAN UJI P — %d/%d BENAR (%.0f%%)' % (benar, len(hasil),
                                                  100 * benar / len(hasil)))
print('=' * 78)
for h in hasil:
    print('  %s fid=%d L%06d  %-16s → %s' % ('✅' if h['benar'] else '❌',
          h['fid'], h['i'], h['kunci'], str(h['utama'])))
print('\nAMBANG KEPUTUSAN (disepakati sebelum uji):')
print('  ≥80%% benar → rencana "AI ikuti pola tetangga" JALAN')
print('  <80%% benar → CARI CARA LAIN (jangan paksakan)')
json.dump(hasil, open('/app/HASIL_UJI_P_POLA.json', 'w'), ensure_ascii=False, indent=1)
print('  ⇒ disimpan: /app/HASIL_UJI_P_POLA.json')
