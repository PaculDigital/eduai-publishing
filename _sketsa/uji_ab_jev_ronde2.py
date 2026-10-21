"""UJI A/B RONDE 2 — naskah SULIT & panjang (21 Okt 2026).

RONDE 1 (naskah mudah, 1.960 kar) hasil: 13/13 jawaban SAMA, Δ noul rata
0,005. Artinya naskah mudah TIDAK membedakan kedua model. Ronde 2 sengaja
mencari BATAS: naskah panjang, bahasa kias, topik tersembunyi, jebakan
"mirip tapi beda" — dan 2 naskah sekaligus (buku + artikel jurnal).
"""
import json
import statistics
import subprocess
import sys
import time

MODEL_A = 'typesafe/jev-1.13'
MODEL_B = 'typesafe/jev-1.14'
JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
CONTAINER = 'eduai-app'

# ══════════════════════════════════════════════════════════════════════════
#  NASKAH A — buku umum, bahasa kias, topik tersirat (SULIT)
# ══════════════════════════════════════════════════════════════════════════
NASKAH_A = """BAB 4 KETAHANAN PANGAN DARI PEKARANGAN

Ada pelajaran yang tidak pernah masuk kurikulum, namun diwariskan setiap pagi
di ratusan pekarangan: bahwa tanah yang dirawat akan menjawab dengan caranya
sendiri. Ketika jagung ditanam di sela pagar, ia tidak hanya memberi tongkol.
Ia menjaga tanah tetap gembur, menahan air hujan yang jatuh terlalu deras, dan
memberi alasan bagi penghuninya untuk keluar rumah sebelum matahari tinggi.

Pemerintah desa pernah menganggap pekarangan sebagai urusan kecil. Program
bantuan benih lebih sering diarahkan ke lahan luas di luar kampung, dengan
alasan efisiensi dan skala ekonomi. Cara berpikir itu masuk akal di atas kertas.
Namun catatan panen tiga tahun terakhir memperlihatkan hal yang lain: saat
musim kemarau memanjang, keluarga yang menanam di pekarangan justru masih
memiliki sesuatu untuk dimasak, sementara sawah tadah hujan sudah mengering
sejak bulan kedua.

Gagasan bahwa pekarangan adalah jaring pengaman pangan sebenarnya bukan hal
baru. Ia pernah ditulis di laporan-laporan lama, lalu tenggelam ketika
pembangunan diarahkan pada komoditas ekspor. Yang berubah bukan tanahnya,
melainkan perhatian orang terhadap tanah itu.

Namun ada sisi yang jarang dibicarakan. Pekarangan juga bisa menjadi tempat
ketimpangan bekerja tanpa suara. Di rumah-rumah yang seluruh penghasilannya
bergantung pada satu orang, kebun kecil itu dikerjakan oleh perempuan setelah
pekerjaan utamanya selesai, dan hasilnya tidak pernah dihitung sebagai
pendapatan. Ketika panen dicatat, yang tercatat adalah nilai jual, bukan jam
kerja yang ditumpuk di belakangnya.

Kesimpulannya bukan bahwa pekarangan menyelesaikan masalah pangan. Lebih tepat
dikatakan bahwa pekarangan memberi ruang gerak ketika jalur lain tertutup,
dan bahwa ruang gerak itu tidak gratis.

BAB 5 KOPERASI YANG TIDAK TUMBUH

Koperasi Desa Makmur berdiri dengan modal patungan 84 kepala keluarga. Pada
tiga tahun pertama, simpanan anggota tumbuh stabil dan unit sembako menjadi
tempat warga berbelanja. Pengurus merasa arahnya benar.

Persoalan mulai muncul ketika koperasi memutuskan membuka unit simpan pinjam.
Keputusan itu diambil dalam rapat yang dihadiri 31 anggota dari 84. Pinjaman
pertama diberikan kepada kerabat pengurus, dengan alasan kebutuhan mendesak.
Tidak ada yang menolak saat itu, karena semua orang saling mengenal.

Setahun kemudian, tunggakan mencapai sepertiga dari total pinjaman beredar.
Rapat anggota memutuskan menghentikan sisa pinjaman baru. Koperasi kembali
menjadi toko sembako, tetapi kepercayaan anggota sudah berkurang. Beberapa
anggota berhenti menyetor simpanan wajib.

Bila dibaca sebagai cerita tentang kegagalan usaha, kisah ini terlalu
sederhana. Yang sebenarnya runtuh lebih dulu bukan modal, melainkan aturan
tentang siapa yang boleh memutuskan. Koperasi tidak pernah menyiapkan cara
untuk menolak permintaan orang yang dikenal.
"""

# ══════════════════════════════════════════════════════════════════════════
#  NASKAH B — artikel jurnal (bentuk berbeda, angka & istilah teknis)
# ══════════════════════════════════════════════════════════════════════════
NASKAH_B = """Pengaruh Literasi Digital terhadap Kinerja UMKM Kuliner di Kawasan Wisata

Abstrak. Penelitian ini menguji pengaruh literasi digital terhadap kinerja
usaha mikro, kecil, dan menengah sektor kuliner di kawasan wisata Pantai
Nirwana. Sampel berjumlah 118 pelaku usaha yang dipilih secara purposif.
Data dianalisis dengan regresi linear berganda menggunakan perangkat lunak
statistik. Hasil menunjukkan literasi digital berpengaruh positif dan
signifikan terhadap kinerja (p = 0,003). Variabel penggunaan media sosial
menyumbang paling besar (beta = 0,41).

Pendahuluan. Pandemi mengubah cara pelaku usaha kuliner berjualan. Pesanan
beralih ke pesan singkat dan aplikasi pesan, sementara pelanggan datang dari
luar daerah setelah unggahan foto makanan menyebar. Perubahan itu tidak
dialami sama rata. Sebagian pelaku usaha menyesuaikan diri dalam hitungan
minggu, sebagian lain belum mengubah apa pun hingga kini.

Penelitian sebelumnya tentang literasi digital cenderung memusatkan
perhatian pada pekerja kantoran. Kajian pada usaha kuliner berskala kecil di
kawasan wisata masih jarang, padahal ciri pasarnya berbeda: pelanggan bersifat
musiman dan keputusan pembelian sangat dipengaruhi ulasan daring.

Metode. Populasi penelitian adalah 340 pelaku usaha kuliner. Sampel diambil
secara purposif dengan kriteria telah beroperasi minimal dua tahun dan memiliki
akun media sosial aktif. Instrumen berupa kuesioner 24 butir dengan skala
Likert lima titik. Uji validitas menggunakan korelasi Product Moment dan uji
reliabilitas menggunakan Cronbach Alpha. Nilai alpha keseluruhan 0,87.
Uji asumsi klasik meliputi normalitas, multikolinearitas, dan
heteroskedastisitas; seluruh asumsi terpenuhi. Nilai VIF tertinggi 1,72.

Hasil dan Pembahasan. Literasi digital berpengaruh positif signifikan
(b = 0,38; p = 0,003). Penggunaan media sosial berpengaruh dominan
(b = 0,41; p = 0,001). Kemampuan mengelola ulasan daring tidak signifikan
(p = 0,182). Temuan ketiga ini berbeda dengan studi Widodo (2023) yang
menemukan pengaruh kuat ulasan daring pada usaha kafe di kota besar.
Perbedaan tersebut masuk akal bila ditinjau dari pola kunjungan: pelanggan
kawasan wisata datang sekali, sedangkan pelanggan kafe kota datang berulang.

Kesimpulan. Literasi digital berperan pada kinerja UMKM kuliner di kawasan
wisata, dengan media sosial sebagai jalur terkuat. Keterbatasan penelitian ini
adalah sampel purposif pada satu kawasan, sehingga hasil tidak dapat
digeneralisasi ke seluruh UMKM. Penelitian lanjutan disarankan memakai sampel
acak antarkawasan dan menambah variabel pengalaman usaha.
"""

PERTANYAAN_A = {
    # ── yang tersirat, bukan tertulis: butuh pemahaman
    "ada_kritik_program_pemerintah": {
        "type": "noul",
        "instructions": ("Apakah naskah mengkritik cara pemerintah desa "
                         "menempatkan prioritas program?"),
    },
    "ada_masalah_kesetaraan_gender": {
        "type": "noul",
        "instructions": ("Apakah naskah mempersoalkan beban kerja perempuan "
                         "yang tidak dihitung sebagai pendapatan?"),
    },
    "ada_sudut_pandang_optimistis": {
        "type": "noul",
        "instructions": ("Apakah naskah menyimpulkan bahwa pekarangan "
                         "menyelesaikan masalah pangan?"),
    },
    "ada_angka_tunggakan": {
        "type": "noul",
        "instructions": "Apakah naskah menyebut besaran tunggakan pinjaman?",
    },
    "ada_penyebab_koperasi_runtuh": {
        "type": "noul",
        "instructions": ("Apakah naskah menyebut aturan pengambilan keputusan "
                         "sebagai penyebab utama kegagalan koperasi?"),
    },
    # ── choice: butuh menyimpulkan, bukan mencari kata
    "inti_pesan_bab4": {
        "type": "choice",
        "instructions": "Apa inti pesan Bab 4?",
        "criteria": {
            "jaring_pengaman": "pekarangan sebagai cadangan pangan saat jalur lain tertutup",
            "produktivitas": "pekarangan meningkatkan hasil panen secara umum",
            "kegagalan": "pekarangan gagal menjadi sumber pangan",
            "tidak_jelas": "naskah tidak memberi kesimpulan",
        },
    },
    "sebab_kegagalan_koperasi": {
        "type": "choice",
        "instructions": "Apa yang disebut naskah sebagai penyebab kegagalan koperasi?",
        "criteria": {
            "aturan_keputusan": "tidak adanya aturan untuk menolak permintaan orang dikenal",
            "modal_kurang": "kekurangan modal awal",
            "persaingan": "kalah bersaing dengan toko lain",
            "tidak_disebut": "naskah tidak menjelaskannya",
        },
    },
    "nada_bab5": {
        "type": "choice",
        "instructions": "Bagaimana nada Bab 5 terhadap pengurus koperasi?",
        "criteria": {
            "memahami": "memahami kesulitan tanpa membenarkan kesalahan",
            "menyalahkan": "menyalahkan pengurus secara langsung",
            "memuji": "memuji kerja pengurus",
            "netral": "murni melaporkan tanpa penilaian",
        },
    },
    "bentuk_tulisan": {
        "type": "score",
        "instructions": ("Seberapa teknis penulisan naskah ini? Nol berarti "
                         "naratif tanpa istilah, lima berarti sangat teknis "
                         "dengan rumus dan angka statistik."),
        "criteria": ["nol", "satu", "dua", "tiga", "empat", "lima"],
    },
}

PERTANYAAN_B = {
    "ada_kolom_hasil": {
        "type": "noul",
        "instructions": "Apakah artikel memuat bagian hasil dan pembahasan?",
    },
    "ada_uji_validitas": {
        "type": "noul",
        "instructions": "Apakah artikel menyebut uji validitas instrumen?",
    },
    "ada_abstrak": {
        "type": "noul",
        "instructions": "Apakah artikel memuat abstrak?",
    },
    "ada_bahasa_inggris": {
        "type": "noul",
        "instructions": "Apakah artikel memuat abstrak dalam bahasa Inggris?",
    },
    "ada_pembanding_terdahulu": {
        "type": "noul",
        "instructions": ("Apakah artikel membandingkan temuannya dengan "
                         "penelitian lain yang hasilnya berbeda?"),
    },
    "ada_keterbatasan": {
        "type": "noul",
        "instructions": "Apakah artikel menyebut keterbatasan penelitian?",
    },
    "ada_rekomendasi": {
        "type": "noul",
        "instructions": "Apakah artikel memberi saran untuk penelitian lanjutan?",
    },
    "ada_rumus": {
        "type": "noul",
        "instructions": "Apakah artikel menampilkan rumus statistik secara tertulis?",
    },
    "jenis_penelitian": {
        "type": "choice",
        "instructions": "Jenis penelitian apa yang dipakai artikel?",
        "criteria": {
            "kuantitatif": "memakai angka dan uji statistik",
            "kualitatif": "memakai wawancara atau observasi",
            "campuran": "memadukan keduanya",
            "kajian_pustaka": "hanya menelaah pustaka tanpa data lapangan",
        },
    },
    "temuan_utama": {
        "type": "choice",
        "instructions": "Variabel apa yang paling besar pengaruhnya menurut artikel?",
        "criteria": {
            "media_sosial": "penggunaan media sosial",
            "literasi_digital": "literasi digital secara umum",
            "ulasan_daring": "kemampuan mengelola ulasan daring",
            "tidak_jelas": "artikel tidak menyebutkannya",
        },
    },
    "kesimpulan_ulasan": {
        "type": "choice",
        "instructions": "Apa yang ditemukan artikel tentang pengaruh ulasan daring?",
        "criteria": {
            "tidak_signifikan": "tidak berpengaruh signifikan",
            "paling_kuat": "berpengaruh paling kuat",
            "sama_dengan_widodo": "sama dengan temuan Widodo",
            "tidak_diuji": "tidak diuji dalam penelitian ini",
        },
    },
    "mutu_metode": {
        "type": "score",
        "instructions": ("Seberapa lengkap metode penelitian diuraikan? Nol "
                         "berarti tidak ada, lima berarti sangat rinci."),
        "criteria": ["nol", "satu", "dua", "tiga", "empat", "lima"],
    },
}


def panggil(model, naskah, pertanyaan, ulang=1):
    badan = {"model": model,
             "messages": [{"role": "user",
                           "content": json.dumps({"state": naskah,
                                                  "questions": pertanyaan})}],
             "max_tokens": 900}
    nama = f'{model.replace("/", "_")}'
    jalur = f'/tmp/ab2_{nama}.json'
    with open(jalur, 'w') as f:
        json.dump(badan, f)
    subprocess.run(['docker', 'cp', jalur, f'{CONTAINER}:/tmp/'], check=True,
                   capture_output=True)
    keluaran = []
    for _ in range(ulang):
        t0 = time.time()
        r = subprocess.run(
            ['docker', 'exec', CONTAINER, 'sh', '-c',
             f'curl -s -m 150 -X POST -H "Content-Type: application/json" '
             f'-d @/tmp/ab2_{nama}.json {JEMBATAN}'],
            capture_output=True, text=True)
        dtk = time.time() - t0
        try:
            d = json.loads(r.stdout)
            if 'choices' not in d:
                keluaran.append({'galat': str(d)[:250], 'detik': dtk})
                continue
            j = json.loads(d['choices'][0]['message']['content'])
            keluaran.append({'jawab': j, 'detik': dtk,
                             'model_asli': d.get('model'),
                             'usage': d.get('usage', {})})
        except Exception as e:
            keluaran.append({'galat': f'{type(e).__name__}: {r.stdout[:200]}',
                             'detik': dtk})
    return keluaran


def nilai(j):
    out = {}
    for nama, v in (j or {}).items():
        if not isinstance(v, dict):
            continue
        t = v.get('type')
        kunci = {'noul': 'noul', 'choice': 'choice', 'score': 'score'}.get(t)
        if kunci:
            out[nama] = (t, v.get(kunci))
    return out


def banding(judul, naskah, pertanyaan):
    print('\n' + '=' * 76)
    print(f'  {judul} — {len(naskah):,} kar · {len(pertanyaan)} pertanyaan')
    print('=' * 76)

    hasil = {}
    for model in (MODEL_A, MODEL_B):
        h = panggil(model, naskah, pertanyaan, ulang=1)[0]
        if 'galat' in h:
            print(f'  ⛔ {model}: {h["galat"][:150]}')
            hasil[model] = None
            continue
        u = h['usage']
        print(f'  {model:<22} {h["detik"]:>6.2f} dtk · token {u.get("input_tokens")} '
              f'· ${u.get("cost"):.7f} · {h["model_asli"]}')
        hasil[model] = h

    a, b = hasil.get(MODEL_A), hasil.get(MODEL_B)
    if not a or not b:
        return None

    va, vb = nilai(a['jawab']), nilai(b['jawab'])
    print(f'\n  {"pertanyaan":<30} {"tipe":<7} {"1.13":>11} {"1.14":>11}   beda')
    print('  ' + '-' * 72)
    sama = beda = 0
    d_noul, d_score, daftar = [], [], []
    for nama in pertanyaan:
        ta, na = va.get(nama, ('?', None))
        tb, nb = vb.get(nama, ('?', None))
        if ta == 'noul':
            d = abs((na or 0) - (nb or 0))
            d_noul.append(d)
            tandai = d >= 0.10
            print(f'  {nama:<30} {ta:<7} {na:>11.2f} {nb:>11.2f}   '
                  f'{"BEDA" if tandai else "sama"} Δ{d:.2f}')
        elif ta == 'score':
            d = abs((na or 0) - (nb or 0))
            d_score.append(d)
            tandai = d >= 1
            print(f'  {nama:<30} {ta:<7} {na:>11} {nb:>11}   '
                  f'{"BEDA" if tandai else "sama"} Δ{d:.2f}')
        else:
            tandai = na != nb
            print(f'  {nama:<30} {ta:<7} {str(na)[:11]:>11} {str(nb)[:11]:>11}   '
                  f'{"BEDA" if tandai else "sama"}')
        if tandai:
            beda += 1
            daftar.append((nama, na, nb))
        else:
            sama += 1

    print(f'\n  sama {sama}/{sama+beda} · beda {beda}/{sama+beda}', end='')
    if d_noul:
        print(f' · Δnoul rata {statistics.mean(d_noul):.3f} maks {max(d_noul):.2f}', end='')
    if d_score:
        print(f' · Δscore rata {statistics.mean(d_score):.2f}', end='')
    print()
    if daftar:
        print('  BERBEDA:')
        for n, x, y in daftar:
            print(f'    · {n}: {x} → {y}')
    return {'sama': sama, 'beda': beda, 'n': sama + beda,
            'd_noul': statistics.mean(d_noul) if d_noul else 0,
            'detik': {m: hasil[m]['detik'] for m in hasil if hasil[m]}}


def utama():
    print('=' * 76)
    print('  UJI A/B RONDE 2 — NASKAH SULIT (buku kias + artikel jurnal)')
    print('=' * 76)

    r1 = banding('NASKAH A — buku umum, bahasa kias', NASKAH_A, PERTANYAAN_A)
    r2 = banding('NASKAH B — artikel jurnal', NASKAH_B, PERTANYAAN_B)

    print('\n' + '=' * 76)
    print('  RINGKASAN RONDE 2')
    print('=' * 76)
    for nama, r in (('buku kias', r1), ('artikel jurnal', r2)):
        if r:
            print(f'  {nama:<16} sama {r["sama"]}/{r["n"]} ({100*r["sama"]//r["n"]}%) '
                  f'· Δnoul {r["d_noul"]:.3f}')

    # ── kestabilan 1.14 pada naskah sulit (5×)
    print('\n' + '=' * 76)
    print('  KESTABILAN NASKAH SULIT (5× panggilan)')
    print('=' * 76)
    for model in (MODEL_A, MODEL_B):
        ulang = panggil(model, NASKAH_A, PERTANYAAN_A, ulang=5)
        sah = [nilai(x['jawab']) for x in ulang if 'jawab' in x]
        if len(sah) < 2:
            print(f'  {model}: data kurang ({len(sah)})')
            continue
        goyang = []
        for nama in PERTANYAAN_A:
            vals = [s.get(nama, (None, None))[1] for s in sah]
            if len({str(v) for v in vals}) > 1:
                # ukur rentang
                ang = [v for v in vals if isinstance(v, (int, float))]
                rng = (max(ang) - min(ang)) if len(ang) > 1 else None
                goyang.append((nama, rng))
        print(f'  {model}: {len(goyang)}/{len(PERTANYAAN_A)} berubah')
        for nama, rng in goyang:
            print(f'    · {nama}' + (f' rentang {rng:.2f}' if rng is not None else ''))

    return 0


if __name__ == '__main__':
    sys.exit(utama())
