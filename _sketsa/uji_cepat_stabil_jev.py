"""UJI CEPAT & STABIL — jev-1.14 vs jev-1.13, 10 panggilan per model.

PERTANYAAN BOS (21 Okt 2026): "Lebih cepat mana, dan lebih stabil mana?"

YANG DIUKUR (bukan kesan):
  · p50 / p95 LATENSI  → cepat
  · jumlah GAGAL        → andal
  · jumlah jawaban BERUBAH antar-ulang → stabil
  · Δ keyakinan rata-rata antar-ulang  → stabil (angka)

NASKAH: 3 naskah Indonesia (mudah / kias / jurnal) — sama seperti uji A/B,
supaya hasil bisa dibandingkan dengan temuan 21 Okt sebelumnya.

CATATAN JUJUR: `Byn/jev-1.14.0` TIDAK diuji — Bynara menjawab 502 di hulu
(tidak pernah memberi satu jawaban pun), jadi tidak ada angka yang bisa
dihitung. Jembatan ujinya sudah siap di 8132 kalau Byn hidup.
"""
import json
import statistics
import subprocess
import sys
import time

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
CONTAINER = 'eduai-app'
ULANG = 10

MODEL = {
    '1.13 (produksi)': 'SATPAM/typesafe/jev-1.13',
    '1.14 (kandidat)': 'typesafe/jev-1.14',
}

# ── naskah uji ────────────────────────────────────────────────────────────
NASKAH = {
    'mudah': """BAB 1 PENDAHULUAN

Pengelolaan sampah organik di Desa Sukamaju masih menjadi masalah utama. Warga
membuang sampah rumah tangga ke saluran air sehingga aliran tersumbat setiap
musim hujan. Pemerintah desa telah menyediakan dua bak sampah komunal, namun
kapasitasnya tidak sebanding dengan volume sampah harian.

BAB 2 TINJAUAN PUSTAKA

Sampah organik adalah sisa bahan yang berasal dari makhluk hidup dan mudah
terurai. Menurut Wardani (2021), pengomposan adalah proses penguraian bahan
organik oleh mikroorganisme dalam kondisi terkendali. Proses ini menghasilkan
pupuk yang dapat menyuburkan tanah.

BAB 3 METODE

Penelitian ini menggunakan pendekatan kualitatif deskriptif. Data dikumpulkan
melalui wawancara mendalam dengan dua belas informan dan observasi lapangan
selama tiga bulan. Analisis data menggunakan model Miles dan Huberman.""",

    'kias': """BAB 4 KETAHANAN PANGAN DARI PEKARANGAN

Ada pelajaran yang tidak pernah masuk kurikulum, namun diwariskan setiap pagi
di ratusan pekarangan: bahwa tanah yang dirawat akan menjawab dengan caranya
sendiri. Ketika jagung ditanam di sela pagar, ia tidak hanya memberi tongkol.
Ia menjaga tanah tetap gembur dan memberi alasan bagi penghuninya untuk keluar
rumah sebelum matahari tinggi.

Pemerintah desa pernah menganggap pekarangan sebagai urusan kecil. Program
bantuan benih lebih sering diarahkan ke lahan luas di luar kampung. Namun
catatan panen tiga tahun terakhir memperlihatkan hal lain: saat musim kemarau
memanjang, keluarga yang menanam di pekarangan justru masih memiliki sesuatu
untuk dimasak.

Namun ada sisi yang jarang dibicarakan. Pekarangan juga bisa menjadi tempat
ketimpangan bekerja tanpa suara. Kebun kecil itu dikerjakan perempuan setelah
pekerjaan utamanya selesai, dan hasilnya tidak pernah dihitung sebagai
pendapatan.""",

    'jurnal': """Pengaruh Literasi Digital terhadap Kinerja UMKM Kuliner

Abstrak. Penelitian ini menguji pengaruh literasi digital terhadap kinerja
usaha mikro, kecil, dan menengah sektor kuliner. Sampel berjumlah 118 pelaku
usaha yang dipilih secara purposif. Hasil menunjukkan literasi digital
berpengaruh positif dan signifikan (p = 0,003).

Metode. Instrumen berupa kuesioner 24 butir dengan skala Likert lima titik.
Uji validitas menggunakan korelasi Product Moment dan uji reliabilitas
menggunakan Cronbach Alpha dengan nilai 0,87. Uji asumsi klasik meliputi
normalitas, multikolinearitas, dan heteroskedastisitas.

Hasil dan Pembahasan. Literasi digital berpengaruh positif signifikan
(b = 0,38; p = 0,003). Penggunaan media sosial berpengaruh dominan
(b = 0,41; p = 0,001). Temuan ini berbeda dengan studi Widodo (2023).

Kesimpulan. Keterbatasan penelitian ini adalah sampel purposif pada satu
kawasan. Penelitian lanjutan disarankan memakai sampel acak antarkawasan.""",
}

PERTANYAAN = {
    'ada_bab': {'type': 'noul', 'instructions': 'Apakah naskah memuat penomoran bab?'},
    'ada_metode': {'type': 'noul', 'instructions': 'Apakah naskah menjelaskan cara penelitian dilakukan?'},
    'ada_kesimpulan': {'type': 'noul', 'instructions': 'Apakah naskah memberi kesimpulan?'},
    'ada_kritik': {'type': 'noul', 'instructions': 'Apakah naskah menyampaikan kritik terhadap suatu kebijakan atau keadaan?'},
    'ada_angka': {'type': 'noul', 'instructions': 'Apakah naskah menyebut angka statistik?'},
    'bentuk': {'type': 'choice',
               'instructions': 'Apa bentuk tulisan naskah ini?',
               'criteria': {'naratif': 'tuturan mengalir tanpa angka statistik',
                            'akademik': 'memakai istilah metodologi dan angka',
                            'berita': 'laporan peristiwa singkat',
                            'panduan': 'berisi langkah-langkah kerja'}},
    'nada': {'type': 'score',
             'instructions': 'Seberapa formal nada tulisan? Nol berarti santai, lima berarti sangat formal.',
             'criteria': ['nol', 'satu', 'dua', 'tiga', 'empat', 'lima']},
}


def panggil(model, naskah):
    payload = {'state': naskah, 'questions': PERTANYAAN}
    body = {'model': model,
            'messages': [{'role': 'user', 'content': json.dumps(payload)}],
            'max_tokens': 700}
    with open('/tmp/uji_cepat.json', 'w') as f:
        json.dump(body, f)
    subprocess.run(['docker', 'cp', '/tmp/uji_cepat.json',
                    f'{CONTAINER}:/tmp/uji_cepat.json'],
                   check=True, capture_output=True)
    t0 = time.time()
    r = subprocess.run(
        ['docker', 'exec', CONTAINER, 'sh', '-c',
         f'curl -s -m 120 -X POST -H "Content-Type: application/json" '
         f'-d @/tmp/uji_cepat.json {JEMBATAN}'],
        capture_output=True, text=True)
    dtk = time.time() - t0
    try:
        d = json.loads(r.stdout)
    except Exception:
        return {'galat': 'balasan bukan JSON', 'detik': dtk}
    if 'choices' not in d:
        return {'galat': str(d.get('error', {}).get('message', d))[:120],
                'detik': dtk}
    try:
        j = json.loads(d['choices'][0]['message']['content'])
    except Exception:
        return {'galat': 'content bukan JSON', 'detik': dtk}
    return {'jawab': j, 'detik': dtk, 'model_asli': d.get('model'),
            'token': (d.get('usage') or {}).get('input_tokens')}


def nilai(j):
    out = {}
    for nama, v in (j or {}).items():
        if isinstance(v, dict):
            for t in ('noul', 'choice', 'score'):
                if t in v:
                    out[nama] = (t, v[t])
    return out


def ringkas(daftar):
    """Hitung p50/p95 dari daftar detik (hanya yang SUKSES)."""
    if not daftar:
        return None, None
    s = sorted(daftar)
    n = len(s)
    p50 = statistics.median(s)
    idx = min(int(round(0.95 * (n - 1))), n - 1)
    return p50, s[idx]


def utama():
    print('=' * 78)
    print(f'  UJI CEPAT & STABIL — {ULANG} panggilan per model · 3 naskah')
    print('=' * 78)

    hasil = {m: {'detik': [], 'gagal': 0, 'n': 0, 'goyang': {},
                 'd_noul': [], 'model_asli': set(), 'token': set()}
             for m in MODEL}

    for nama_naskah, naskah in NASKAH.items():
        print(f'\n── naskah: {nama_naskah} ({len(naskah):,} kar)')
        for label, model in MODEL.items():
            kumpulan = []
            for i in range(ULANG):
                h = panggil(model, naskah)
                hasil[label]['n'] += 1
                if 'galat' in h:
                    hasil[label]['gagal'] += 1
                    print(f'   {label} #{i+1}: GAGAL — {h["galat"]}')
                    continue
                hasil[label]['detik'].append(h['detik'])
                hasil[label]['model_asli'].add(h.get('model_asli'))
                if h.get('token'):
                    hasil[label]['token'].add(h['token'])
                kumpulan.append(nilai(h['jawab']))

            # goyangan: berapa pertanyaan yang jawabannya berubah antar-ulang
            for nama in PERTANYAAN:
                vals = [k.get(nama, (None, None))[1] for k in kumpulan]
                unik = {str(v) for v in vals}
                if len(unik) > 1:
                    hasil[label]['goyang'][(nama_naskah, nama)] = len(unik)
                    ang = [v for v in vals if isinstance(v, (int, float))]
                    if len(ang) > 1:
                        hasil[label]['d_noul'].append(max(ang) - min(ang))

    print('\n' + '=' * 78)
    print('  HASIL')
    print('=' * 78)
    print(f'  {"model":<18} {"sukses":>7} {"gagal":>6} {"p50":>8} {"p95":>8} '
          f'{"goyang":>8} {"Δnoul":>7}')
    print('  ' + '-' * 70)
    for label in MODEL:
        h = hasil[label]
        p50, p95 = ringkas(h['detik'])
        goyang = len(h['goyang'])
        dn = statistics.mean(h['d_noul']) if h['d_noul'] else 0.0
        sukses = len(h['detik'])
        print(f'  {label:<18} {sukses:>7} {h["gagal"]:>6} '
              f'{(f"{p50:.2f}dtk" if p50 else "-"):>8} '
              f'{(f"{p95:.2f}dtk" if p95 else "-"):>8} '
              f'{goyang:>8} {dn:>7.3f}')

    print('\n  Model asli yang menjawab:')
    for label in MODEL:
        print(f'    {label}: {sorted(hasil[label]["model_asli"])}')
    print('  Token input (harus sama antar model kalau naskah sama):')
    for label in MODEL:
        print(f'    {label}: {sorted(hasil[label]["token"])}')

    print('\n  Pertanyaan yang GOYAH:')
    ada = False
    for label in MODEL:
        for (nk, nama), n_unik in sorted(hasil[label]['goyang'].items()):
            print(f'    {label} · {nk} · {nama} → {n_unik} nilai berbeda')
            ada = True
    if not ada:
        print('    (tidak ada — semua jawaban konsisten)')

    print('\n  Byn/jev-1.14.0: TIDAK DIUJI — Bynara 502 di hulu (jembatan uji '
          'siap di 8132).')
    return 0


if __name__ == '__main__':
    sys.exit(utama())
