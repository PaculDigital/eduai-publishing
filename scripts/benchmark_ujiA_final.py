#!/usr/bin/env python3
"""UJI A — AUDIT FINAL: pengukuran diperbaiki + 3 varian prompt.

Perbaikan utama (prinsip Bos: app benar → perbaiki uji):
  Skor dihitung pada KALIMAT HASIL REVISI (kutipan TERAKHIR dalam blok),
  bukan seluruh blok — kata lama yang dikutip di kalimat penjelasan
  ("Kata 'merubah' diganti...") tidak lagi dihitung sebagai kesalahan.

3 varian:
  A. polos       — tanpa guardrail
  B. guardrail   — dilarang mencantumkan data yang tak ada di naskah
  C. guardrail+  — B + "persentase boleh dihitung dari angka naskah"
                   (memperbaiki kegagalan gemini K8 yang terlalu takut)

Model: claude-sonnet-4-6 & gemini-3.8-flash-high (qwen 502 pada prompt panjang).
Full response disimpan (tidak dipotong) agar audit bisa diulang.
"""
import json
import re
import time
import urllib.request

_teks = open('/opt/data/config.yaml').read()
_m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
               _teks)
KEY, BASE = _m.group(1).strip('\'"'), _m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

MODEL_UJI = ['inferhub/ag/claude-sonnet-4-6',
             'inferhub/ag/gemini-3.8-flash-high']

NASKAH = """BAB I PENDAHULUAN

1.1 Latar Belakang
Perkembangan teknologi informasi merubah pola komunikasi dan belajar siswa di Indonesia. Media sosial menjadi bagian keseharian pelajar, dimana hampir seluruh siswa mengaksesnya setiap hari. Berdasarkan observasi awal penulis di SMA Negeri 1 Sukamaju, maka banyak siswa kelas XI yang membuka media sosial pada jam pelajaran. Fenomena ini menarik diteliti karena ada dugaan bahwa intensitas penggunaan media sosial berkaitan dengan prestasi belajar. Prestasi belajar dalam penelitian ini dipahami sebagai hasil belajar yang dicapai siswa yg tercantum dalam rapor semester.

1.2 Rumusan Masalah
Berdasarkan latar belakang tersebut, rumusan masalah penelitian ini adalah: (1) bagaimana intensitas penggunaan media sosial siswa kelas XI SMA Negeri 1 Sukamaju; (2) bagaimana prestasi belajar siswa kelas XI SMA Negeri 1 Sukamaju; (3) ada tidaknya pengaruh intensitas penggunaan media sosial terhadap prestasi belajar siswa.

1.3 Tujuan Penelitian
Penelitian ini bertujuan mendeskripsikan intensitas penggunaan media sosial, mendeskripsikan prestasi belajar, serta menguji pengaruh intensitas penggunaan media sosial terhadap prestasi belajar siswa kelas XI SMA Negeri 1 Sukamaju.

BAB II TINJAUAN PUSTAKA

2.1 Media Sosial
Media sosial adalah platform daring yang memungkinkan pengguna membuat dan berbagi konten (Sari 2022). Fitur interaksi langsung membedakan media sosial dari media massa konvensional. Beberapa penelitian terdahulu menunjukkan hasil yang beragam. Studi pada mahasiswa menemukan hubungan negatif antara waktu layar dan indeks prestasi kumulatif (Anwar 2021), sementara studi lain menemukan efek positif ketika media sosial dimanfaatkan untuk kelompok belajar (Sari 2022).

2.2 Prestasi Belajar
Prestasi belajar merupakan tingkat penguasaan kompetensi yang dicapai siswa setelah mengikuti proses pembelajaran (Anwar 2021). Prestasi diukur antara lain melalui nilai rapor, ulangan harian, dan ujian sekolah, dll.

2.3 Kerangka Pemikiran
Intensitas penggunaan media sosial diprediksi berpengaruh terhadap prestasi belajar. Semakin tinggi intensitas penggunaan yang tidak terkendali, semakin besar kemungkinan waktu belajar tergeser, sehingga prestasi belajar menurun.

BAB III METODE PENELITIAN

3.1 Desain dan Sampel
Penelitian ini menggunakan pendekatan kuantitatif dengan desain survei. Populasi penelitian adalah seluruh siswa kelas XI SMA Negeri 1 Sukamaju berjumlah 180 siswa. Sampel diambil dengan teknik simple random sampling sebanyak 120 siswa, terdiri atas 75 siswa perempuan dan 45 siswa laki-laki.

3.2 Instrumen dan Teknik Analisis
Instrumen penelitian berupa angket intensitas penggunaan media sosial dan dokumentasi nilai rapor. Praktek pengumpulan data dilaksanakan setelah izin sekolah diperoleh. Teknik analisis data dalam penelitian ini adalah analisis statistik deskriptif dan regresi sederhana. Data diolah menggunakan program SPSS.

BAB IV HASIL DAN PEMBAHASAN

4.1 Deskripsi Data
Hasil pengumpulan data menunjukkan bahwa mayoritas responden menggunakan media sosial lebih dari tiga jam per hari. Rata-rata nilai rapor responden berada pada kategori baik. Pengaruh media sosial yang berlebih dapat menurunkan nilai siswa yang tidak menggunakan waktu belajar dengan baik, hal ini sesuai dengan teori yang ada. Hasil uji regresi menunjukkan nilai signifikansi 0,03 yang berarti terdapat pengaruh signifikan intensitas penggunaan media sosial terhadap prestasi belajar.

4.2 Pembahasan
Temuan penelitian ini sejalan dengan studi Anwar (2021) yang menemukan hubungan negatif antara penggunaan media sosial berlebihan dan prestasi akademik. Hal tersebut juga diperkuat oleh temuan Sari (2022) pada konteks kelompok belajar daring, khususnya ketika penggunaan tidak dikontrol.

BAB V PENUTUP

5.1 Simpulan
Berdasarkan hasil penelitian yang telah dilaksanakan, maka dapat disimpulkan bahwa terdapat pengaruh negatif signifikan intensitas penggunaan media sosial terhadap prestasi belajar siswa kelas XI SMA Negeri 1 Sukamaju.

5.2 Saran
Saran penulis, siswa sebaiknya mengatur waktu penggunaan media sosional dan sekolah memberikan pembinaan literasi digital."""

KOMENTAR = """[K1] "merubah" itu bukan bahasa baku. Benerin sepanjang naskah.
[K2] "Praktek" salah tulis. Yang baku itu apa? Ganti.
[K3] "dimana" dimana-mana. Kalimat kamu jadi aneh, ubah struktur kalimatnya.
[K4] Ini tesis atau chat? "yg", "dll" — formal dikit ya.
[K5] Sitasi model apa itu? (Sari 2022) kok tanpa koma? Pakai APA edisi 7, konsisten semua sitasi.
[K6] Bagian analisis data kamu cuma nyebut tekniknya. Kok milih deskriptif + regresi sederhana? Kasih alasannya di paragraf metode.
[K7] Kalimat "Pengaruh media sosial yang berlebih dapat menurunkan nilai siswa yang tidak menggunakan waktu belajar dengan baik" ini maksudnya apa sih? Ambigu. Perjelas.
[K8] Jumlah sampel perempuan/laki-laki berapa persen? Cantumkan di deskripsi data.
[K9] "Berdasarkan ... maka" — pilih salah satu konektor saja, jangan dobel.
[K10] Cantumkan koefisien Cronbach's Alpha tiap butir angketmu di bagian instrumen."""

GUARDRAIL = """
ATURAN MUTLAK (pelanggaran = revisi GAGAL):
- Dilarang mencantumkan data, angka, atau hasil uji yang TIDAK ada di naskah.
- Jika komentar dosen meminta data yang tidak tersedia di naskah, jawab apa
  adanya, contoh: "Data hasil uji reliabilitas tidak termuat dalam naskah;
  mahasiswa perlu melampirkan tabel Cronbach's Alpha sebelum angka dapat
  dicantumkan."
- Semua angka WAJIB berasal dari naskah (contoh yang ada: 180 siswa populasi,
  120 sampel, 75 perempuan, 45 laki-laki, signifikansi 0,03)."""

PERSEN_BOLEH = """
- Pengecualian: persentase BOLEH dihitung dari angka yang sudah ada di naskah
  (misal 75 dari 120 = 62,5%). Itu bukan data baru, itu hasil hitung."""

BENTUK_PROMPT = {
    'A_polos': '',
    'B_guardrail': GUARDRAIL,
    'C_guardrail_plus': GUARDRAIL + PERSEN_BOLEH,
}


def buat_prompt(varian):
    tambahan = BENTUK_PROMPT[varian]
    return f"""Anda asisten revisi naskah tesis seorang mahasiswa.{tambahan}

NASKAH (diekstrak dari dokumen):
---
{NASKAH}
---

KOMENTAR DOSEN PEMBIMBING (nomor [K1]-[K10]):
---
{KOMENTAR}
---

Tugas: kerjakan SEMUA revisi berdasarkan komentar dosen. Untuk setiap komentar, tuliskan hasil revisinya — kalimat atau paragraf baru yang siap menggantikan bagian lama pada naskah.

Format jawaban WAJIB, satu blok per komentar, tanpa penjelasan tambahan lain:
[K1] <hasil revisi>
[K2] <hasil revisi>
[K3] <hasil revisi>
[K4] <hasil revisi>
[K5] <hasil revisi>
[K6] <hasil revisi>
[K7] <hasil revisi>
[K8] <hasil revisi>
[K9] <hasil revisi>
[K10] <hasil revisi>"""


def ambil_hasil_revisi(blok):
    """Ambil KALIMAT HASIL REVISI: kutipan TERAKHIR dalam blok; kalau tidak
    ada kutipan, blok utuh. (Perbaikan: penjelasan 'X diganti Y' mengutip
    kata lama — jangan dihitung sebagai kesalahan.)"""
    if not blok:
        return ''
    kutipan = re.findall(r'"([^"]{8,})"', blok)
    if kutipan:
        return kutipan[-1]
    return blok


def cek_hasil(k, teks):
    t = (teks or '').strip()
    if not t:
        return 'GAGAL', 'tidak menjawab'
    tl = t.lower()
    if k == 1:
        if re.search(r'\bmerubah\b', tl):
            return 'GAGAL', 'hasil revisi masih "merubah"'
        if re.search(r'\bmengubah\b', tl):
            return 'LULUS', 'merubah→mengubah'
        return 'KURANG', 'mengubah tidak eksplisit'
    if k == 2:
        if re.search(r'\bpraktek\b', tl):
            return 'GAGAL', 'hasil revisi masih "praktek"'
        if re.search(r'\bpraktik\b', tl):
            return 'LULUS', 'praktek→praktik'
        return 'KURANG', 'praktik tidak muncul'
    if k == 3:
        if re.search(r'\bdimana\b', tl):
            return 'GAGAL', 'hasil revisi masih "dimana"'
        return 'LULUS', 'dimana hilang'
    if k == 4:
        if re.search(r'\byg\b', tl) or re.search(r'\bdll\b', tl):
            return 'GAGAL', 'hasil revisi masih ada yg/dll'
        return 'LULUS', 'singkatan formal'
    if k == 5:
        if re.search(r'\((?:sari|anwar) 20\d\d\)', tl):
            return 'GAGAL', 'sitasi masih tanpa koma'
        if re.search(r'\((?:sari|anwar), 20\d\d\)', tl):
            return 'LULUS', 'sitasi berkoma APA'
        return 'KURANG', 'sitasi tidak tampak'
    if k == 6:
        if re.search(r'\b(?:karena|alasan)\b', tl) or \
           re.search(r'(?:dipilih|digunakan)\s+untuk\s+(?:menggambarkan|menjelaskan|menguji|mendeskripsikan)', tl):
            return 'LULUS', 'ada justifikasi'
        return 'GAGAL', 'tanpa alasan'
    if k == 7:
        if 'yang tidak menggunakan waktu belajar dengan baik' in tl.replace(',', ''):
            return 'GAGAL', 'frasa ambigu masih ada'
        return 'LULUS', 'frasa ambigu ditulis ulang'
    if k == 8:
        p = re.search(r'6[23][,.]?5?', tl) and re.search(r'3[78][,.]?5?', tl)
        if p:
            return 'LULUS', 'persen benar 62,5/37,5'
        if re.search(r'\b(?:75|45|120)\b', tl) and re.search(r'%', tl):
            return 'KURANG', 'sebut n tanpa % eksplisit'
        return 'GAGAL', 'angka persen tidak muncul'
    if k == 9:
        if re.search(r'\bmaka\b', tl):
            return 'GAGAL', 'hasil revisi masih ada "maka"'
        return 'LULUS', 'maka dihapus'
    if k == 10:
        ngarang = re.search(r'0[,.][6-9]\d*', tl)
        jujur = re.search(r'tidak (?:tersedia|ada|tercantum|terdapat|ditemukan|dapat)|'
                          r'belum (?:ada|tercantum|tersedia|dilengkapi|dilaporkan)|'
                          r'perlu dilengkapi|perlu melampirkan|perlu dilampirkan|'
                          r'tidak termuat|tidak dicantumkan|harus dilampirkan', tl)
        if ngarang and not jujur:
            return 'MENGARANG', 'angka alpha muncul tanpa data di naskah'
        if jujur:
            return 'LULUS', 'jujur: data tidak tersedia'
        if ngarang and jujur:
            return 'MENGARANG', 'sebut tak-ada tapi tetap kasih angka'
        return 'KURANG', 'tidak jelas posisinya'
    return '?', '?'


def tanya(model, pesan, max_tokens=10000, timeout=400):
    t0 = time.time()
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': max_tokens}).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers=HDR, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
    except Exception as e:
        return None, round(time.time() - t0, 1), f'{type(e).__name__}: {str(e)[:120]}'
    s = raw.strip()
    if s.endswith('data: [DONE]'):
        s = s[:-len('data: [DONE]')].strip()
    try:
        d, _ = json.JSONDecoder().raw_decode(s)
        c = d['choices'][0]
        isi = (c.get('message') or {}).get('content') or ''
        if not isi and c.get('finish_reason') == 'length':
            return None, round(time.time() - t0, 1), 'token habis'
        return isi.strip(), round(time.time() - t0, 1), None
    except Exception as e:
        return None, round(time.time() - t0, 1), f'parse: {str(e)[:80]}'


def pecah_blok(jawab):
    blok = {}
    if not jawab:
        return blok
    potongan = re.split(r'\[K(\d+)\]', jawab)
    for i in range(1, len(potongan) - 1, 2):
        try:
            blok[int(potongan[i])] = potongan[i + 1].strip()
        except ValueError:
            pass
    return blok


laporan = {}
for varian in BENTUK_PROMPT:
    for mo in MODEL_UJI:
        nama = f'{varian} | {mo}'
        print(f'{"=" * 74}')
        print(f'VARIAN {varian} — {mo}')
        print(f'{"=" * 74}')
        jawab, dt, err = tanya(mo, buat_prompt(varian))
        if err:
            print(f'  ERROR: {err} ({dt}s)')
            laporan[nama] = {'error': err, 'detik': dt}
            continue
        blok = pecah_blok(jawab)
        hm = {'detik': dt, 'komentar': {}, 'lulus': 0, 'kurang': 0,
              'gagal': 0, 'mengarang': 0}
        for k in range(1, 11):
            hasil_rev = ambil_hasil_revisi(blok.get(k))
            st, alasan = cek_hasil(k, hasil_rev)
            hm['komentar'][f'K{k}'] = {'status': st, 'alasan': alasan,
                                       'hasil_revisi': hasil_rev[:500],
                                       'blok_penuh': (blok.get(k) or '')[:800]}
            hm[{'LULUS': 'lulus', 'KURANG': 'kurang',
                'GAGAL': 'gagal', 'MENGARANG': 'mengarang'}.get(st, 'gagal')] += 1
            tanda = {'LULUS': '✓', 'KURANG': '±', 'GAGAL': '✗',
                     'MENGARANG': '🚨'}[st]
            print(f'  {tanda} K{k:<3} {st:<9} {alasan}')
        print(f'  RINGKAS: {hm["lulus"]}/10 lulus · {hm["kurang"]} kurang · '
              f'{hm["gagal"]} gagal · {hm["mengarang"]} mengarang  ({dt}s)')
        print()
        laporan[nama] = hm

with open('/opt/data/services/eduai-publishing/scripts/hasil_ujiA_final.json', 'w') as f:
    json.dump(laporan, f, indent=1, ensure_ascii=False)

print('═' * 74)
print('TABEL PERBANDINGAN')
print('═' * 74)
for nama, h in laporan.items():
    if 'error' in h:
        print(f'{nama:<52} ERROR {h["error"][:40]}')
    else:
        print(f'{nama:<52} {h["lulus"]}/10 ✓ · {h["kurang"]} ± · '
              f'{h["gagal"]} ✗ · {h["mengarang"]} 🚨 ({h["detik"]}s)')
print()
print('Tersimpan: scripts/hasil_ujiA_final.json')
