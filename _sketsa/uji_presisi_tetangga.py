"""UJI KUALITAS: `enable_thinking:false` — output PRESISI & TETANGGA terjaga?

Naskah 8 paragraf; komentar menyebar di P2 (2 komentar), P5, P7.
P1/P3/P4/P6/P8 = paragraf TANPA komentar = "tetangga" yang wajib utuh.

DIUKUR OTOMATIS (bukan penilaian Wulan):
  balas      : semua komentar dapat balasan [K? + GANTI-JADI]
  kutip_sah  : KUTIP-ASLI ada PERSIS di naskah
  kutip_tepat: KUTIP-ASLI == kalimat sasaran yang dikomentari
  meluap     : ada kutip dari paragraf TANPA komentar  (=> tetangga dirusak)
  blkg_sama  : kalimat LAIN dalam paragraf sasaran ikut terkutip (=> melebar)

Dikirim dua versi dgn ID uji unik agar dua-duanya MELEWATI cache provider.
"""
import json, os, time, urllib.error, urllib.request

BASE = os.environ['EDUAI_FALLBACK_BASE'].rstrip('/')
KEY = os.environ['EDUAI_FALLBACK_KEY']
import sys
sys.path.insert(0, '.')
from app.ai import SYSTEM_REVISI, _urai_jawaban  # noqa: E402

# ── naskah uji: 8 paragraf ─────────────────────────────────────────
P = [
    # P1 (bersih)
    'Populasi dalam penelitian ini adalah seluruh mahasiswa program studi '
    'manajemen angkatan 2021 sampai 2023 yang berjumlah 1.240 orang. '
    'Peneliti mengambil sampel sebanyak 300 responden dengan teknik '
    'proportionate stratified random sampling agar setiap angkatan '
    'terwakili secara seimbang. Pendekatan kuantitatif dipilih karena '
    'penelitian ini bertujuan menguji hubungan antarvariabel secara '
    'kuantitatif.',
    # P2 (2 komentar: K1 kalimat 1, K3 kalimat 3)
    'Metode penelitian ini menggunakan pendekatan kuantitatif dengan '
    'jenis penelitian survei. Data primer dikumpulkan melalui kuesioner '
    'daring yang disebar selama tiga minggu kepada responden yang telah '
    'ditetapkan. Penelitian ini bertujuan untuk bertujuan untuk menguji '
    'pengaruh kualitas produk dan harga terhadap keputusan pembelian '
    'konsumen di wilayah Jawa Barat. Instrumen telah diuji validitas '
    'dalamnya dengan korelasi antarbutir dan uji reliabilitas Cronbach '
    'alpha sebesar 0,91.',
    # P3 (bersih)
    'Teknik analisis yang digunakan adalah regresi linear berganda dengan '
    'bantuan program SPSS versi 26. Sebelum pengujian hipotesis, data '
    'dijalankan melalui uji asumsi klasik meliputi uji normalitas, '
    'linieritas, heteroskedastisitas, dan multikolinearitas. Hasil uji '
    'menunjukkan seluruh asumsi terpenuhi sehingga model layak digunakan '
    'untuk pengujian hipotesis.',
    # P4 (bersih)
    'Berdasarkan hasil analisis, koefisien determinasi sebesar 0,612 '
    'artinya 61,2 persen keputusan pembelian dijelaskan oleh kualitas '
    'produk dan harga, sedangkan sisanya dipengaruhi faktor lain di luar '
    'model. Nilai t hitung kualitas produk sebesar 5,84 dengan signifikansi '
    '0,000 yang lebih kecil dari 0,05, sehingga hipotesis pertama diterima.',
    # P5 (1 komentar: K2 kalimat 2)
    'Kualitas produk merupakan variabel yang memberikan kontribusi '
    'terbesar terhadap keputusan pembelian konsumen. Dalam konteks '
    'penelitian ini, kualitas produk yang diartikan sebagai kesesuaian '
    'produk dengan harapan konsumen tersebut memberikan pengaruh yang '
    'sangat berarti dan sangat signifikan terhadap keputusan pembelian '
    'konsumen yang dilakukan. Harga berpengaruh positif dengan koefisien '
    '0,31.',
    # P6 (bersih)
    'Penelitian ini memiliki keterbatasan pada penggunaan data yang hanya '
    'diambil dari satu wilayah, sehingga generalisasi hasil perlu '
    'kehati-hatian. Penelitian selanjutnya disarankan menambah variabel '
    'promosi dan persepsi nilai untuk memperluas model. Peneliti juga '
    'dapat menggunakan metode longitudinal agar dinamika perilaku '
    'konsumen terekam lebih baik.',
    # P7 (1 komentar: K4 kalimat 1 — paragraf bersih, uji gaya)
    'Sesuai dengan hal tersebut, maka berdasarkan teori yang telah '
    'dirumuskan sebelumnya di dalam bab ini dapat ditarik kesimpulan '
    'bahwa kualitas produk dan harga sama-sama berpengaruh terhadap '
    'keputusan pembelian. Kerangka teori yang telah dibangun menjadi '
    'dasar penyusunan hipotesis pada bab selanjutnya.',
    # P8 (bersih)
    'Hipotesis penelitian ini disusun berdasarkan teori dan hasil '
    'penelitian terdahulu yang relevan. Hipotesis pertama menyatakan '
    'bahwa kualitas produk berpengaruh positif terhadap keputusan '
    'pembelian. Hipotesis kedua menyatakan bahwa harga berpengaruh '
    'positif terhadap keputusan pembelian konsumen.',
]
NAASKAH = '\n\n'.join(P)

KOMENTAR = [
    ('K1', 1, 0, 'Kalimat pembuka paragraf 2 terlalu umum, sebutkan teknik samplingnya.'),
    ('K3', 1, 2, 'Ada pengulangan kata "bertujuan untuk" yang ganda.'),
    ('K2', 4, 1, 'Kalimat kedua terlalu berbelit dan mengulang subjek.'),
    ('K4', 6, 0, 'Gaya kalimat terlalu kaku, rapikan bahasanya.'),
]

#  kalimat sasaran tiap komentar (untuk penilaian keakratan)
SASARAN = {
    'K1': P[1].split('. ')[0] + '.',
    'K3': 'Penelitian ini bertujuan untuk bertujuan untuk menguji pengaruh '
          'kualitas produk dan harga terhadap keputusan pembelian konsumen '
          'di wilayah Jawa Barat.',
    'K2': 'Dalam konteks penelitian ini, kualitas produk yang diartikan '
          'sebagai kesesuaian produk dengan harapan konsumen tersebut '
          'memberikan pengaruh yang sangat berarti dan sangat signifikan '
          'terhadap keputusan pembelian konsumen yang dilakukan.',
    'K4': 'Sesuai dengan hal tersebut, maka berdasarkan teori yang telah '
          'dirumuskan sebelumnya di dalam bab ini dapat ditarik kesimpulan '
          'bahwa kualitas produk dan harga sama-sama berpengaruh terhadap '
          'keputusan pembelian.',
}
PARAGRAF_KOMENTAR = {1, 4, 6}   # index paragraf yang boleh tersentuh


def tugas(uid):
    isi_k = '\n'.join(f'[{k}] {teks}' for k, _, _, teks in KOMENTAR)
    return ('NASKAH:\n' + NAASKAH +
            '\n\nKOMENTAR PEMBIMBING:\n' + isi_k +
            '\n\nBalas HANYA dengan pasangan penanda untuk SETIAP komentar:\n'
            '[K?-KUTIP-ASLI] <kalimat asli persis dari naskah>\n'
            '[K?-GANTI-JADI] <penggantinya>\n\n'
            f'ID-internal-ukuran: {uid}')


def kirim(uid, tambahan, timeout=420):
    p = {'model': 'glm-5.3-flash', 'max_tokens': 16000, 'temperature': 0.2,
         'messages': [{'role': 'system', 'content': SYSTEM_REVISI},
                      {'role': 'user', 'content': tugas(uid)}]}
    p.update(tambahan)
    req = urllib.request.Request(
        BASE + '/chat/completions', data=json.dumps(p).encode(),
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            teks = r.read().decode('utf-8', 'ignore')
    except Exception as e:                                   # noqa: BLE001
        return {'galat': type(e).__name__ + ': ' + str(e)[:250]}, ''
    dt = time.monotonic() - t0
    try:
        konten, info = _urai_jawaban(teks, 'glm-5.3-flash')
        lolos, alasan = True, 'lolos'
    except Exception as e:                                   # noqa: BLE001
        return {'dt': round(dt, 1), 'lolos': False,
                'alasan': str(e)[:200]}, ''
    return {'dt': round(dt, 1), 'lolos': True, 'alasan': alasan,
            'reasoning': info.get('reasoning'), 'finish': info.get('finish'),
            'token_out': info.get('token_out')}, konten


def nilai(konten):
    """Penilaian OTOMATIS presisi + tetangga."""
    import re
    hasil = {'balas': [], 'kutip_sah': {}, 'kutip_tepat': {},
             'meluap': [], 'blkg_sama': {}}
    #  ambil tiap pasang penanda
    for k, pidx, kidx, _ in KOMENTAR:
        m = re.search(r'\[\s*' + k + r'-KUTIP-ASLI\s*\]\s*(.+?)\s*'
                      r'\[\s*' + k + r'-GANTI-JADI\s*\]', konten, re.S)
        ada_ganti = bool(re.search(r'\[\s*' + k + r'-GANTI-JADI\s*\]\s*\S',
                                   konten))
        hasil['balas'].append((k, bool(m) and ada_ganti))
        if not m:
            hasil['kutip_sah'][k] = False
            hasil['kutip_tepat'][k] = False
            continue
        kutip = ' '.join(m.group(1).split())
        sah = kutip in ' '.join(NAASKAH.split())
        hasil['kutip_sah'][k] = sah
        #  apakah kutip == kalimat sasaran (presisi)
        tepat = kutip == ' '.join(SASARAN[k].split())
        hasil['kutip_tepat'][k] = tepat
        #  apakah kutip mengambil paragraf lain (meluap ke tetangga)
        for pi, par in enumerate(P):
            if pi in PARAGRAF_KOMENTAR:
                continue
            if kutip[:60] in ' '.join(par.split()):
                hasil['meluap'].append((k, f'P{pi+1}'))
        #  apakah kalimat LAIN di paragraf sasaran ikut terkutip
        kalimat_par = [' '.join(x.split()) for x in P[pidx].split('. ')
                       if len(x) > 40]
        lain = [i for i, km in enumerate(kalimat_par)
                if km[:50] in kutip and i != kidx and kutip.count('.') > 1]
        hasil['blkg_sama'][k] = lain
    return hasil


hasil = {}
for tag, uid, extra in (
        ('ON (pola app)', 'ON-a91c', {}),
        ('OFF (enable_thinking)', 'OFF-b47e', {'enable_thinking': False})):
    print(f'\n══ {tag} ══', flush=True)
    dasar, konten = kirim(uid, extra)
    penilaian = nilai(konten) if konten else {}
    balas_ok = sum(1 for _, ok in penilaian.get('balas', []) if ok)
    ring = {**dasar,
            'balas': f'{balas_ok}/4',
            'kutip_sah': penilaian.get('kutip_sah'),
            'kutip_tepat': penilaian.get('kutip_tepat'),
            'meluap_tetangga': penilaian.get('meluap'),
            'blkg_ikut_terkutip': penilaian.get('blkg_sama'),
            'isi': konten}
    hasil[tag] = ring
    print(json.dumps({k: v for k, v in ring.items() if k != 'isi'},
                     ensure_ascii=False, indent=1), flush=True)

with open('/tmp/uji_presisi_tetangga.json', 'w') as fh:
    json.dump(hasil, fh, ensure_ascii=False, indent=1)
print('\narsip: /tmp/uji_presisi_tetangga.json', flush=True)
