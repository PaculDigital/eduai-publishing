"""UJI A/B JEV 1.13 vs 1.14 — naskah Indonesia nyata (21 Okt 2026).

MENGAPA: TypeSafe menyebut keunggulan terbesar 1.14 = MULTIBAHASA, tapi
TIDAK memberi satu angka pun. Ambang kita (satpam 0,80 · ragu 0,95) disetel
untuk 1.13 ⇒ wajib diukur ulang, bukan ditebak.

CARA: kirim naskah + pertanyaan yang SAMA ke dua model, bandingkan:
  · kesepakatan jawaban (choice) & selisih nilai (noul/score)
  · arah keyakinan (1.14 lebih tegas atau lebih ragu?)
  · waktu & biaya (dari usage Jev sendiri, bukan perkiraan)

Naskah uji = BENTUK NYATA yang dipakai app: bab buku berbahasa Indonesia,
termasuk kasus yang dulu TERBUKTI sulit (membedakan "memperdalam topik" vs
"topik baru" — lihat app/pipa.py:418).
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
#  NASKAH UJI — bahasa Indonesia, bentuk bab buku sungguhan
# ══════════════════════════════════════════════════════════════════════════
NASKAH = """BAB 1 PENDAHULUAN

Pengelolaan sampah organik di Desa Sukamaju masih menjadi persoalan yang belum
terselesaikan. Setiap rumah tangga menghasilkan rata-rata 2,3 kilogram sampah
per hari, dan sekitar 60 persen di antaranya adalah sisa makanan. Warga
terbiasa membuang sampah ke saluran irigasi karena tidak ada tempat
penampungan sementara. Akibatnya saluran tersumbat pada musim hujan dan
menimbulkan genangan di lahan pertanian.

Bank sampah hadir sejak tahun 2019 sebagai upaya warga sendiri. Pengurusnya
adalah ibu-ibu rumah tangga yang mengumpulkan sampah anorganik setiap minggu
lalu menjualnya ke pengepul. Namun bank sampah belum menyentuh sampah organik,
padahal jenis itu paling banyak dihasilkan rumah tangga.

Penelitian ini bertujuan mengukur seberapa besar kontribusi bank sampah
terhadap perubahan perilaku warga dalam memilah sampah. Pertanyaan penelitian
dirumuskan sebagai berikut: apakah keberadaan bank sampah berhubungan dengan
kebiasaan memilah sampah di tingkat rumah tangga?

BAB 2 TINJAUAN PUSTAKA

Suryanto (2021) menjelaskan bahwa bank sampah tidak sekadar tempat
pengumpulan, melainkan simpul perubahan sosial. Ia menemukan bahwa warga yang
terlibat aktif dalam bank sampah cenderung memilah sampah tanpa perlu diminta.
Temuan itu sejalan dengan Hidayat (2020) yang menekankan peran insentif
ekonomi sebagai pemicu awal.

Wulandari (2022) memberi catatan kritis. Menurutnya, keberhasilan bank sampah
sangat bergantung pada kehadiran pengurus yang berdedikasi. Begitu pengurus
berhenti, kegiatan sering ikut berhenti. Ia menyebut hal ini sebagai
kerentanan struktural pada lembaga yang bergantung pada satu orang.

BAB 3 METODE PENELITIAN

Penelitian ini menggunakan pendekatan kuantitatif dengan desain survei.
Responden diambil secara acak dari 240 kepala keluarga di tiga dusun. Data
dikumpulkan melalui kuesioner tertutup selama empat minggu. Analisis
dilakukan dengan regresi linear sederhana, dengan taraf signifikansi 5 persen.
"""

# ══════════════════════════════════════════════════════════════════════════
#  PERTANYAAN — campuran 3 tipe, termasuk jebakan yang dulu sulit
# ══════════════════════════════════════════════════════════════════════════
PERTANYAAN = {
    # ── KEBERADAAN (noul) — dasar, harusnya mudah
    "ada_tujuan": {
        "type": "noul",
        "instructions": "Apakah naskah ini menyatakan tujuan penelitian secara eksplisit?",
    },
    "ada_sitasi": {
        "type": "noul",
        "instructions": "Apakah naskah ini memuat sitasi ke penulis lain?",
    },
    "sitasi_lengkap_tahun": {
        "type": "noul",
        "instructions": "Apakah setiap sitasi dalam naskah disertai tahun terbit?",
    },
    # ── JEBAKAN 1: dua sitasi yang saling berlawanan sudut pandang
    "ada_pandangan_berlawanan": {
        "type": "noul",
        "instructions": ("Apakah naskah memuat dua pandangan penulis yang saling "
                         "berlawanan atau saling mengoreksi?"),
    },
    # ── JEBAKAN 2: hal yang TIDAK ada di naskah (uji kejujuran)
    "ada_data_eksperimen": {
        "type": "noul",
        "instructions": "Apakah naskah memuat hasil eksperimen laboratorium?",
    },
    "ada_uji_validitas": {
        "type": "noul",
        "instructions": "Apakah naskah menyebut uji validitas atau reliabilitas instrumen?",
    },
    # ── CHOICE: butuh pemahaman isi, bukan cocok kata
    "metode": {
        "type": "choice",
        "instructions": "Pendekatan penelitian apa yang dipakai naskah ini?",
        "criteria": {
            "kuantitatif": "memakai angka, survei, atau uji statistik",
            "kualitatif": "memakai wawancara mendalam, observasi, atau studi kasus",
            "campuran": "memadukan keduanya",
            "tidak_jelas": "naskah tidak menyebut pendekatan penelitian",
        },
    },
    "sumber_insentif": {
        "type": "choice",
        "instructions": "Menurut naskah, apa pemicu awal warga mau memilah sampah?",
        "criteria": {
            "insentif_ekonomi": "keuntungan uang atau ekonomi",
            "kesadaran_sendiri": "kesadaran tanpa imbalan",
            "aturan_desa": "aturan atau sanksi dari pemerintah desa",
            "tekanan_sosial": "tekanan atau ajakan tetangga",
        },
    },
    "kerentanan": {
        "type": "choice",
        "instructions": "Apa kelemahan bank sampah menurut catatan kritis dalam naskah?",
        "criteria": {
            "bergantung_pengurus": "bergantung pada satu atau beberapa pengurus",
            "tidak_ada_dana": "kekurangan dana operasional",
            "kurang_warga": "kurangnya partisipasi warga",
            "tidak_disebut": "naskah tidak menyebut kelemahannya",
        },
    },
    "hambatan_awal": {
        "type": "choice",
        "instructions": "Apa yang disebut naskah sebagai penyebab saluran irigasi tersumbat?",
        "criteria": {
            "sampah_sungai": "warga membuang sampah ke saluran",
            "endapan_lumpur": "endapan lumpur alami",
            "bangunan_sempit": "bangunan yang terlalu sempit",
            "tidak_disebut": "naskah tidak menjelaskannya",
        },
    },
    # ── SCORE: butuh hitungan
    "jumlah_bab": {
        "type": "score",
        "instructions": "Berapa jumlah bab dalam naskah ini?",
        "criteria": ["nol", "satu", "dua", "tiga", "empat", "lima"],
    },
    "kualitas_rujukan": {
        "type": "score",
        "instructions": ("Seberapa kuat bagian tinjauan pustaka naskah ini? "
                         "Nol berarti tidak ada rujukan, lima berarti rujukan "
                         "lengkap, beragam, dan saling dibandingkan."),
        "criteria": ["nol", "satu", "dua", "tiga", "empat", "lima"],
    },
    "kejelasan_metode": {
        "type": "score",
        "instructions": ("Seberapa jelas metode penelitian diuraikan dalam naskah? "
                         "Nol berarti tidak ada, lima berarti sangat rinci dan "
                         "bisa diulang orang lain."),
        "criteria": ["nol", "satu", "dua", "tiga", "empat", "lima"],
    },
}


def panggil(model: str, ulang: int = 1) -> dict:
    """Kirim SATU permintaan ke jembatan, balikkan jawaban + usage."""
    badan = {
        "model": model,
        "messages": [{"role": "user",
                      "content": json.dumps({"state": NASKAH,
                                             "questions": PERTANYAAN})}],
        "max_tokens": 800,
    }
    jalur = f'/tmp/ab_{model.replace("/", "_")}.json'
    with open(jalur, 'w') as f:
        json.dump(badan, f)
    subprocess.run(['docker', 'cp', jalur, f'{CONTAINER}:/tmp/'], check=True,
                   capture_output=True)
    semua = []
    for _ in range(ulang):
        t0 = time.time()
        r = subprocess.run(
            ['docker', 'exec', CONTAINER, 'sh', '-c',
             f'curl -s -m 120 -X POST -H "Content-Type: application/json" '
             f'-d @/tmp/ab_{model.replace("/", "_")}.json {JEMBATAN}'],
            capture_output=True, text=True)
        dtk = time.time() - t0
        try:
            d = json.loads(r.stdout)
        except Exception:
            semua.append({'galat': r.stdout[:300], 'detik': dtk})
            continue
        if 'choices' not in d:
            semua.append({'galat': str(d)[:300], 'detik': dtk})
            continue
        isi = d['choices'][0]['message']['content']
        try:
            jawab = json.loads(isi)
        except Exception:
            semua.append({'galat': f'JSON rusak: {isi[:200]}', 'detik': dtk})
            continue
        semua.append({'jawab': jawab, 'detik': dtk,
                      'model_asli': d.get('model'),
                      'usage': d.get('usage', {})})
    return semua


def nilai(j: dict) -> dict:
    """Ratakan jawaban jadi {nama: (tipe, nilai)}."""
    out = {}
    for nama, v in (j or {}).items():
        if not isinstance(v, dict):
            continue
        t = v.get('type')
        if t == 'noul':
            out[nama] = ('noul', v.get('noul'))
        elif t == 'choice':
            out[nama] = ('choice', v.get('choice'))
        elif t == 'score':
            out[nama] = ('score', v.get('score'))
    return out


def utama():
    print('=' * 74)
    print('  UJI A/B JEV — 1.13 vs 1.14 · naskah Indonesia')
    print(f'  naskah {len(NASKAH):,} kar · {len(PERTANYAAN)} pertanyaan')
    print('=' * 74)

    hasil = {}
    for model in (MODEL_A, MODEL_B):
        print(f'\n── {model} ──')
        jalan = panggil(model, ulang=1)
        h = jalan[0]
        if 'galat' in h:
            print(f'  ⛔ GAGAL: {h["galat"]}')
            hasil[model] = None
            continue
        u = h['usage']
        print(f'  model asli : {h["model_asli"]}')
        print(f'  waktu      : {h["detik"]:.2f} dtk')
        print(f'  token masuk: {u.get("input_tokens")} · biaya ${u.get("cost")}')
        hasil[model] = h

    a, b = hasil.get(MODEL_A), hasil.get(MODEL_B)
    if not a or not b:
        print('\n⛔ tidak bisa dibandingkan — ada yang gagal')
        return 2

    va, vb = nilai(a['jawab']), nilai(b['jawab'])
    print('\n' + '=' * 74)
    print('  PERBANDINGAN JAWABAN')
    print('=' * 74)
    print(f'  {"pertanyaan":<28} {"tipe":<7} {"1.13":>10} {"1.14":>10}   beda')
    print('  ' + '-' * 70)

    sama = beda = 0
    selisih_noul = []
    selisih_score = []
    daftar_beda = []
    for nama in PERTANYAAN:
        ta, na = va.get(nama, ('?', None))
        tb, nb = vb.get(nama, ('?', None))
        if ta == 'noul':
            d = abs((na or 0) - (nb or 0))
            selisih_noul.append(d)
            tanda = 'BEDA' if d >= 0.10 else 'sama'
            if tanda == 'BEDA':
                beda += 1
                daftar_beda.append((nama, ta, na, nb, d))
            else:
                sama += 1
            print(f'  {nama:<28} {ta:<7} {na:>10.2f} {nb:>10.2f}   {tanda} (Δ{d:.2f})')
        elif ta == 'score':
            d = abs((na or 0) - (nb or 0))
            selisih_score.append(d)
            tanda = 'BEDA' if d >= 1 else 'sama'
            if tanda == 'BEDA':
                beda += 1
                daftar_beda.append((nama, ta, na, nb, d))
            else:
                sama += 1
            print(f'  {nama:<28} {ta:<7} {str(na):>10} {str(nb):>10}   {tanda} (Δ{d})')
        else:
            cocok = (na == nb)
            if cocok:
                sama += 1
            else:
                beda += 1
                daftar_beda.append((nama, ta, na, nb, None))
            print(f'  {nama:<28} {ta:<7} {str(na)[:10]:>10} {str(nb)[:10]:>10}   '
                  f'{"sama" if cocok else "BEDA"}')

    total = sama + beda
    print('\n' + '=' * 74)
    print('  RINGKASAN')
    print('=' * 74)
    print(f'  jawaban sama : {sama}/{total}')
    print(f'  jawaban beda : {beda}/{total}')
    if selisih_noul:
        print(f'  Δ noul       : rata {statistics.mean(selisih_noul):.3f} · '
              f'maks {max(selisih_noul):.2f}')
    if selisih_score:
        print(f'  Δ score      : rata {statistics.mean(selisih_score):.2f} · '
              f'maks {max(selisih_score)}')

    if daftar_beda:
        print('\n  YANG BERBEDA:')
        for nama, t, na, nb, d in daftar_beda:
            print(f'    · {nama}: {na} → {nb}')

    # ── uji ulang: kestabilan jawaban 1.14 (3×)
    print('\n' + '=' * 74)
    print('  KESTABILAN (3× panggilan, model sama)')
    print('=' * 74)
    for model in (MODEL_A, MODEL_B):
        ulang = panggil(model, ulang=3)
        sah = [nilai(x['jawab']) for x in ulang if 'jawab' in x]
        if len(sah) < 2:
            print(f'  {model}: tidak cukup data')
            continue
        goyang = 0
        for nama in PERTANYAAN:
            vals = [s.get(nama, (None, None))[1] for s in sah]
            if len({str(v) for v in vals}) > 1:
                goyang += 1
        print(f'  {model}: {goyang}/{len(PERTANYAAN)} pertanyaan berubah antar-panggilan')

    # ── simpan bukti
    with open('/opt/data/bukti_jev_ab_21okt2026.json', 'w') as f:
        json.dump({'naskah_kar': len(NASKAH),
                   'pertanyaan': list(PERTANYAAN),
                   'hasil': {k: (v['jawab'] if v and 'jawab' in v else None)
                             for k, v in hasil.items()},
                   'usage': {k: (v['usage'] if v and 'usage' in v else None)
                             for k, v in hasil.items()},
                   'detik': {k: (v['detik'] if v and 'detik' in v else None)
                             for k, v in hasil.items()}},
                  f, indent=2, ensure_ascii=False)
    print('\n  bukti: /opt/data/bukti_jev_ab_21okt2026.json')
    return 0


if __name__ == '__main__':
    sys.exit(utama())
